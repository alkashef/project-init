"""Run the milestones of docs/plan.md one after another, each in its own unattended claude session.

Each milestone of the table "Milestones at a glance" runs in a fresh `claude -p` session with the
model and effort its row names, following the loop of docs/workflow.md. Before the first one, the
runner checks the conda environment, a clean git tree, an upstream branch and .gitignore. After
each one, it checks that the milestone's row left the plan, that git is clean and that everything
was pushed. It stops at a row whose Status is `blocked` and at a milestone that sets it, printing
the milestone's block with its question; the user adds an Approval entry, sets the Status to
`approved`, commits, and runs again. It also stops at a milestone that did not finish. It shows a
live status line, logs each session to .claude/logs/M<n>.log, appends a timing to
.claude/logs/timings.csv, and ends with a summary table.

Does NOT edit the plan, the code or git: the claude session does that. The git pre-commit hook
still runs every check and test on each milestone's commit.

Run, after `conda activate {{PROJECT_NAME}}`:
    python scripts/milestones-runner.py [--start N] [--end N]
"""

import argparse
import csv
import ctypes
import io
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Final, NoReturn, Self

# The rules of a run (docs/workflow.md).
ENV_NAME: Final = "{{PROJECT_NAME}}"
VALID_MODELS: Final = ("haiku", "sonnet", "opus")
VALID_EFFORTS: Final = ("low", "medium", "high", "xhigh", "max")
IGNORE_ENTRIES: Final = (".claude/logs/",)
TAIL_LINES: Final = 30
REFRESH_SECONDS: Final = 1.0
OUTCOME_DONE: Final = "done"
OUTCOME_FAILED: Final = "failed"
OUTCOME_BLOCKED: Final = "blocked"
STATUS_BLOCKED: Final = "blocked"  # in the Status column: the milestone waits for an approval


@dataclass(frozen=True)
class BarStyle:
    """How a progress bar looks: its width in characters and its filled and empty characters."""

    width: int
    fill: str
    empty: str


# The live status line keeps within 79 columns, so an 80-column console does not wrap it.
LIVE_BAR: Final = BarStyle(10, "█", "░")
RANGE_BAR: Final = BarStyle(40, "|", "_")


@dataclass(frozen=True)
class Row:
    """One row of the table "Milestones at a glance" (model, effort and status in lower case)."""

    id: int
    title: str
    model: str
    effort: str
    status: str


@dataclass(frozen=True)
class Result:
    """How one milestone of this run ended (outcome: done, failed or blocked)."""

    id: int
    title: str
    model: str
    effort: str
    started_at: str
    seconds: float
    outcome: str


@dataclass(frozen=True)
class Progress:
    """Everything the live status line shows, at one moment."""

    done: int
    total: int
    row_id: int
    model: str
    effort: str
    milestone_seconds: float
    total_seconds: float
    finished_seconds: tuple[float, ...]


@dataclass(frozen=True)
class Options:
    """The command-line arguments. A start or end of None means the whole table."""

    start: int | None
    end: int | None


@dataclass(frozen=True)
class Paths:
    """The files the runner reads and writes, below the repository root."""

    root: Path

    @property
    def plan(self) -> Path:
        """docs/plan.md."""
        return self.root / "docs" / "plan.md"

    @property
    def log_dir(self) -> Path:
        """.claude/logs, with one log per milestone."""
        return self.root / ".claude" / "logs"

    @property
    def gitignore(self) -> Path:
        """.gitignore."""
        return self.root / ".gitignore"

    @property
    def timings(self) -> Path:
        """.claude/logs/timings.csv."""
        return self.log_dir / "timings.csv"


@dataclass(frozen=True)
class ClaudeRun:
    """The output lines and the exit code of one `claude -p` run."""

    lines: list[str]
    exit_code: int


@dataclass(frozen=True)
class Verdict:
    """The judgement of a finished run: its outcome and, for a failure, the reason."""

    outcome: str
    reason: str


class RunStoppedError(Exception):
    """The run must stop. main() prints the message and the detail lines, then the summary."""

    def __init__(self, message: str, details: Sequence[str] = (), color: str = "red") -> None:
        """Keep the first line, the lines under it, and the color of the first line."""
        super().__init__(message)
        self.message = message
        self.details = tuple(details)
        self.color = color


class Stopwatch:
    """Counts the seconds since it was made."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Start counting now. A test passes its own clock."""
        self._clock = clock
        self._start = clock()

    def elapsed(self) -> float:
        """Return the seconds counted so far."""
        return self._clock() - self._start


@dataclass
class RunState:
    """What this run has done so far: the milestones to run, the total timer and the results."""

    total: int
    stopwatch: Stopwatch
    results: list[Result] = field(default_factory=list)

    def progress(self, row: Row, milestone: Stopwatch) -> Progress:
        """Return the numbers for the live status line while `row` runs."""
        return Progress(
            done=len(self.results),
            total=self.total,
            row_id=row.id,
            model=row.model,
            effort=row.effort,
            milestone_seconds=milestone.elapsed(),
            total_seconds=self.stopwatch.elapsed(),
            finished_seconds=tuple(result.seconds for result in self.results),
        )


@dataclass(frozen=True)
class Console:
    """Prints to the terminal: ANSI colors when use_color is True, plain text when it is False."""

    use_color: bool

    def paint(self, text: str, color: str) -> str:
        """Return the text in "green", "yellow" or "red"; unchanged when colors are off."""
        if not self.use_color:
            return text
        code = {"green": "32", "yellow": "33", "red": "31"}[color]
        return f"\x1b[{code}m{text}\x1b[0m"

    def say(self, text: str = "", color: str | None = None) -> None:
        """Print one permanent line."""
        print(text if color is None else self.paint(text, color), flush=True)

    def overwrite(self, text: str, color: str) -> None:
        """Replace the current terminal line with the text, cut to the width of the terminal."""
        width = shutil.get_terminal_size().columns - 1
        sys.stdout.write(self._erase(width) + self.paint(text[:width], color))
        sys.stdout.flush()

    def clear_line(self) -> None:
        """Erase the current terminal line and put the cursor at its start."""
        sys.stdout.write(self._erase(shutil.get_terminal_size().columns - 1))
        sys.stdout.flush()

    def _erase(self, width: int) -> str:
        """Return the characters that clear the current line."""
        if self.use_color:
            return "\r\x1b[2K"
        return "\r" + " " * width + "\r"


PLAIN_CONSOLE: Final = Console(use_color=False)


@dataclass(frozen=True)
class Session:
    """Everything one run needs: the files, the terminal, the state and the range."""

    paths: Paths
    console: Console
    state: RunState
    first: int
    last: int


class LiveStatus:
    """Redraws one status line every second from a thread. Use it in a `with` block."""

    def __init__(self, console: Console, render: Callable[[], str]) -> None:
        """Keep the console and the function that returns the text of the line."""
        self._console = console
        self._render = render
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self) -> Self:
        """Start the thread."""
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the thread, also after an error, and erase the line."""
        self._stop.set()
        self._thread.join()
        self._console.clear_line()

    def _loop(self) -> None:
        """Draw, then wait one second or until stop; repeat."""
        while True:
            self._console.overwrite(self._render(), "yellow")
            if self._stop.wait(REFRESH_SECONDS):
                return


# --- reading the plan ----------------------------------------------------------------------------


def _split_lines(text: str) -> list[str]:
    """Split on CRLF, LF or CR only (str.splitlines also splits on form feeds and more)."""
    return re.split(r"\r\n|\r|\n", text)


def _read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file (a byte order mark is dropped)."""
    return _split_lines(path.read_text(encoding="utf-8-sig"))


def parse_row(line: str) -> Row | None:
    """Read one table row: | **M<n>** Title | Description | Model | Effort | Status |.

    Args:
        line: One line of the plan.

    Returns:
        The row, or None when the line is not a milestone row.
    """
    match = re.match(
        r"^\|\s*\*\*M(?P<id>\d+)\*\*\s*(?P<title>[^|]*?)\s*\|\s*(?P<text>.*)\|\s*(?P<model>[^|]*?)\s*"
        r"\|\s*(?P<effort>[^|]*?)\s*\|\s*(?P<status>[^|]*?)\s*\|\s*$",
        line,
        re.IGNORECASE,
    )
    if match is None:
        return None
    return Row(
        id=int(match["id"]),
        title=match["title"].replace("**", "").strip(),
        model=match["model"].strip().lower(),
        effort=match["effort"].strip().lower(),
        status=match["status"].strip().lower(),
    )


def parse_plan_rows(lines: Sequence[str]) -> list[Row]:
    """Return the rows of the table "Milestones at a glance", in the order of the file.

    Args:
        lines: The lines of docs/plan.md.

    Returns:
        The rows between that heading and the next heading of level 1 to 3.
    """
    rows: list[Row] = []
    in_table = False
    for line in lines:
        if re.match(r"^## Milestones at a glance", line, re.IGNORECASE):
            in_table = True
        elif in_table and re.match(r"^#{1,3} ", line):
            break
        elif in_table:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    return rows


def plan_has_row(lines: Sequence[str], milestone_id: int) -> bool:
    """Tell whether the table "Milestones at a glance" still has a row for the milestone.

    A finished milestone leaves the table: its commit deletes its block and its row
    (docs/workflow.md).

    Args:
        lines: The lines of docs/plan.md.
        milestone_id: The milestone number.

    Returns:
        True when the table has the row of that milestone.
    """
    return any(row.id == milestone_id for row in parse_plan_rows(lines))


def plan_row(lines: Sequence[str], milestone_id: int) -> Row | None:
    """Return the milestone's row of the table "Milestones at a glance", or None if it left."""
    return next((row for row in parse_plan_rows(lines) if row.id == milestone_id), None)


def milestone_block(lines: Sequence[str], milestone_id: int) -> list[str]:
    """Return the lines of the milestone's `### M<n>` block, up to the next heading."""
    block: list[str] = []
    inside = False
    for line in lines:
        if re.match(r"^#{1,3} ", line):
            inside = re.match(rf"^### M{milestone_id}\b", line) is not None
        if inside:
            block.append(line)
    return block


def rows_in_range(rows: Sequence[Row], first: int, last: int) -> list[Row]:
    """Return the rows numbered first to last, in table order (not numeric order)."""
    return [row for row in rows if first <= row.id <= last]


def next_open_row(rows: Sequence[Row]) -> Row | None:
    """Return the first row, in table order, whose status is not "done"."""
    return next((row for row in rows if row.status != "done"), None)


def resolve_range(rows: Sequence[Row], start: int | None, end: int | None) -> tuple[int, int]:
    """Return the first and last milestone number; a missing start or end means the whole table."""
    ids = [row.id for row in rows]
    return (
        min(ids, default=0) if start is None else start,
        max(ids, default=0) if end is None else end,
    )


def range_problem(first: int, last: int) -> str | None:
    """Return why the range is refused (a start after the end), or None."""
    if first > last:
        return f"--start ({first}) is greater than --end ({last})."
    return None


def row_problem(row: Row) -> str | None:
    """Return why the model or effort of the row cannot be used, or None."""
    if not row.model or not row.effort:
        return f"M{row.id} has no Model or no Effort in the table."
    if row.model not in VALID_MODELS:
        return f"M{row.id}: Model '{row.model}' is not one of {', '.join(VALID_MODELS)}."
    if row.effort not in VALID_EFFORTS:
        return f"M{row.id}: Effort '{row.effort}' is not one of {', '.join(VALID_EFFORTS)}."
    return None


def build_prompt(row: Row) -> str:
    """Return the text sent to claude for one milestone."""
    text = " ".join(
        (
            "Implement only milestone M<n> (<title>) from docs/plan.md.",
            "Follow its block, the loop in docs/workflow.md (steps 4 to 6) and CLAUDE.md.",
            "This is an unattended run: nobody can answer questions.",
            "Rules:",
            "(a) never edit docs/spec.md, unless the block's Approval entry says to;",
            "(b) in docs/plan.md, when the gate passes, delete the block of M<n> and its row in",
            'the table "Milestones at a glance", and edit nothing else in the plan;',
            "(c) do that edit before the commit so the commit includes it;",
            "(d) commit only the files this milestone changed, with the message `M<n>: <title>`,",
            "then run git push;",
            "(e) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
            "(f) a spec and a design that disagree, any need for a user decision, or any action",
            "that CLAUDE.md 'Git and destructive actions' forbids, which no Approval entry in the",
            "block permits: stop the milestone. Set its Status in the table to `blocked`, add a",
            "Blocked entry with the reason and the exact question to its block (template in",
            "docs/workflow.md), change no other file, commit docs/plan.md alone with the message",
            "`M<n>: blocked`, and run git push;",
            "(g) an Approval entry in the block is the user's decision: it permits exactly what it",
            "says, even an action these rules or CLAUDE.md otherwise forbid, and nothing more;",
            "(h) end with the report in CLAUDE.md 'Communication and reporting'.",
        )
    )
    return text.replace("<n>", str(row.id)).replace("<title>", row.title)


# --- arguments, environment and git --------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> Options:
    """Read the command line.

    Args:
        argv: The arguments; None means sys.argv.

    Returns:
        The options. Without --start and --end the whole table is run.
    """
    parser = argparse.ArgumentParser(
        description="Run the milestones of docs/plan.md, one claude session each."
    )
    parser.add_argument(
        "--start", type=int, default=None, help="first milestone number (default: the first row)"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="last milestone number (default: the last row)"
    )
    args = parser.parse_args(argv)
    return Options(start=args.start, end=args.end)


def in_project_env(prefix: str) -> bool:
    """Tell whether a Python prefix (sys.prefix) is the project's conda environment."""
    return Path(prefix).name.lower() == ENV_NAME.lower()


def missing_ignore_entries(existing: Sequence[str]) -> list[str]:
    """Return the entries of IGNORE_ENTRIES that are not a line of .gitignore (case-insensitive)."""
    known = {line.lower() for line in existing}
    return [entry for entry in IGNORE_ENTRIES if entry.lower() not in known]


def add_ignore_entries(gitignore: Path) -> bool:
    """Append the missing entries to .gitignore.

    Args:
        gitignore: The path of .gitignore.

    Returns:
        True when it had to add a line.
    """
    text = gitignore.read_text(encoding="utf-8-sig") if gitignore.exists() else ""
    missing = missing_ignore_entries(_split_lines(text))
    if not missing:
        return False
    # Start on a new line, so the first entry does not join a last line without a line end.
    start = "\n" if text and not text.endswith(("\n", "\r")) else ""
    with gitignore.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(start + "\n".join(missing) + "\n")
    return True


def _run(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository and return its result, or stop the run if it cannot start."""
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise _error(f"`{args[0]}` could not run: {exc}") from exc


def git_is_clean(root: Path) -> bool:
    """Tell whether `git status --porcelain` succeeds and lists nothing."""
    done = _run(["git", "status", "--porcelain"], root)
    return done.returncode == 0 and not done.stdout.strip()


def git_has_upstream(root: Path) -> bool:
    """Tell whether the current branch has an upstream, so that git push works."""
    done = _run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
    return done.returncode == 0


def git_has_unpushed(root: Path) -> bool:
    """Tell whether HEAD has commits that are not on the upstream (True when git cannot tell)."""
    done = _run(["git", "rev-list", "--count", "@{u}..HEAD"], root)
    return done.returncode != 0 or int(done.stdout.strip() or "0") > 0


def _error(message: str) -> RunStoppedError:
    """Build the stop for a plain error: "ERROR: <message>" in red."""
    return RunStoppedError(f"ERROR: {message}")


def check_range(first: int, last: int) -> None:
    """Refuse a range whose start is after its end.

    Args:
        first: The first milestone number.
        last: The last milestone number.

    Raises:
        RunStoppedError: If the range is refused.
    """
    problem = range_problem(first, last)
    if problem is not None:
        raise _error(problem)


def preflight(paths: Paths) -> None:
    """Check the environment before the first milestone.

    Args:
        paths: The repository files.

    Raises:
        RunStoppedError: If the conda env is wrong, git is not clean, the branch has no
            upstream, or .gitignore had to be changed.
    """
    if not in_project_env(sys.prefix):
        raise _error(
            f"Python runs from '{sys.prefix}', not from the conda env '{ENV_NAME}'. "
            f"Run 'conda activate {ENV_NAME}' first."
        )
    if not git_is_clean(paths.root):
        raise _error("git status is not clean. Commit or stash your changes first.")
    if not git_has_upstream(paths.root):
        raise _error(
            "The current branch has no upstream, so git push cannot work. "
            "Set one with: git push -u origin <branch>"
        )
    if add_ignore_entries(paths.gitignore):
        raise _error(
            f".gitignore was missing {', '.join(IGNORE_ENTRIES)}; the lines are added now. "
            "Commit .gitignore, then run again."
        )


# --- time and display ----------------------------------------------------------------------------


def format_duration(seconds: float) -> str:
    """Return mm:ss, or h:mm:ss from one hour on (the seconds are cut, not rounded)."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def bar_text(done: int, total: int, style: BarStyle) -> str:
    """Return a bar of `style.width` characters, filled by the share done/total (rounded down)."""
    filled = min(style.width * done // total, style.width) if total > 0 else 0
    return style.fill * filled + style.empty * (style.width - filled)


def percent(done: int, total: int) -> int:
    """Return 100 * done / total, rounded (0 when total is 0)."""
    return round(100 * done / total) if total > 0 else 0


def eta_text(finished_seconds: Sequence[float], left: int) -> str:
    """Return "ETA mm:ss": the average time of the finished milestones times the milestones left."""
    if not finished_seconds:
        return "ETA --"
    average = sum(finished_seconds) / len(finished_seconds)
    return f"ETA {format_duration(average * left)}"


def status_text(progress: Progress) -> str:
    """Return the live status line (without colors) for one moment of the run."""
    bar = bar_text(progress.done, progress.total, LIVE_BAR)
    return " | ".join(
        (
            f"{bar} {percent(progress.done, progress.total)}% {progress.done}/{progress.total}",
            f"M{progress.row_id} {progress.model}/{progress.effort}",
            f"this {format_duration(progress.milestone_seconds)}",
            f"total {format_duration(progress.total_seconds)}",
            eta_text(progress.finished_seconds, progress.total - progress.done),
        )
    )


def outcome_color(outcome: str) -> str:
    """Return green for done, yellow for blocked and red for failed."""
    return {OUTCOME_DONE: "green", OUTCOME_BLOCKED: "yellow"}.get(outcome, "red")


def result_line(result: Result) -> str:
    """Return the permanent line of a finished milestone."""
    return " | ".join(
        (
            f"M{result.id} {result.title}",
            result.model,
            result.effort,
            format_duration(result.seconds),
            result.outcome,
        )
    )


def _table_lines(results: Sequence[Result], console: Console) -> list[str]:
    """Return the aligned table of this run's milestones, each row in the color of its outcome."""
    header = ("ID", "Model", "Effort", "Duration", "Result")
    cells = [
        (f"M{r.id}", r.model, r.effort, format_duration(r.seconds), r.outcome) for r in results
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *cells, strict=True)]
    lines = [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in (header, *cells)
    ]
    return [lines[0]] + [
        console.paint(line, outcome_color(r.outcome))
        for line, r in zip(lines[1:], results, strict=True)
    ]


def summary_lines(
    results: Sequence[Result], total_seconds: float, console: Console = PLAIN_CONSOLE
) -> list[str]:
    """Return the summary of the run: a table, the total time, the average and the slowest one.

    Args:
        results: The milestones that ran, in order.
        total_seconds: The total time of the run.
        console: Paints the rows of the table (the default adds no colors).

    Returns:
        The lines to print; an empty list when no milestone ran.
    """
    if not results:
        return []
    slowest = max(results, key=lambda result: result.seconds)
    average = sum(result.seconds for result in results) / len(results)
    return [
        "Summary",
        *_table_lines(results, console),
        f"Total time: {format_duration(total_seconds)}",
        f"Average: {format_duration(average)}",
        f"Slowest: M{slowest.id} ({format_duration(slowest.seconds)})",
    ]


def print_summary(console: Console, state: RunState) -> None:
    """Print the summary of the run, if any milestone ran."""
    lines = summary_lines(state.results, state.stopwatch.elapsed(), console)
    if lines:
        console.say()
        for line in lines:
            console.say(line)


def enable_ansi() -> bool:
    """Turn on ANSI colors in the console.

    Returns:
        True when colors work; False when output is not a terminal or Windows refuses.
    """
    if not sys.stdout.isatty():
        return False
    if sys.platform != "win32":
        return True
    stdout_handle, virtual_terminal = -11, 0x0004
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(stdout_handle)
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | virtual_terminal))
    except (AttributeError, OSError):
        return False


def start_console() -> Console:
    """Switch standard output to UTF-8 and return a Console with colors if they work."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    return Console(use_color=enable_ansi())


# --- running a milestone -------------------------------------------------------------------------


def run_claude(paths: Paths, row: Row) -> ClaudeRun:
    """Run one milestone in `claude -p` and save the full output to .claude/logs/M<n>.log.

    Args:
        paths: The repository files.
        row: The milestone; its model and effort go to claude.

    Returns:
        The output lines (standard output and error together) and the exit code.

    Raises:
        RunStoppedError: If the claude program cannot be found or started.
    """
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    program = shutil.which("claude") or "claude"
    command = [
        program,
        "-p",
        "--model",
        row.model,
        "--effort",
        row.effort,
        "--permission-mode",
        "bypassPermissions",
    ]
    try:
        done = subprocess.run(
            command,
            cwd=paths.root,
            input=build_prompt(row),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise _error(f"claude could not run: {exc}") from exc
    text = done.stdout.rstrip("\r\n")
    lines = _split_lines(text) if text else []
    (paths.log_dir / f"M{row.id}.log").write_text(
        "".join(f"{line}\n" for line in lines), encoding="utf-8"
    )
    return ClaudeRun(lines, done.returncode)


def failure_reason(paths: Paths, row: Row, run: ClaudeRun) -> str | None:
    """Return why a run that finished or blocked its milestone does not count, or None."""
    after = plan_row(_read_lines(paths.plan), row.id)
    if after is not None and after.status != STATUS_BLOCKED:
        return (
            "its row is still in the plan table and not blocked, so the commit that finishes "
            f"it was not made (claude exit code {run.exit_code})."
        )
    if not git_is_clean(paths.root):
        return "git status is not clean."
    if git_has_unpushed(paths.root):
        return "there are commits that were not pushed."
    return None


def judge(paths: Paths, row: Row, run: ClaudeRun) -> Verdict:
    """Return done (its row left the plan), blocked (its row says so) or failed (with why)."""
    reason = failure_reason(paths, row, run)
    if reason is not None:
        return Verdict(OUTCOME_FAILED, reason)
    if plan_has_row(_read_lines(paths.plan), row.id):
        return Verdict(OUTCOME_BLOCKED, "")
    return Verdict(OUTCOME_DONE, "")


def waiting_for_approval(paths: Paths, row: Row) -> RunStoppedError:
    """Build the stop for a blocked milestone: what to do, then its block with the question."""
    message = (
        f"M{row.id} waits for your approval. In docs/plan.md, add an Approval entry to its "
        "block, set its Status to `approved`, commit, and run again:"
    )
    return RunStoppedError(message, milestone_block(_read_lines(paths.plan), row.id), "yellow")


def stop_for(paths: Paths, row: Row, verdict: Verdict, run: ClaudeRun) -> NoReturn:
    """Stop the run because the milestone did not finish.

    Raises:
        RunStoppedError: Always. It carries the blocked milestone's question, or the reason and
            the last lines of output.
    """
    if verdict.outcome == OUTCOME_BLOCKED:
        raise waiting_for_approval(paths, row)
    intro = f"Last {TAIL_LINES} lines of output (full log: .claude/logs/M{row.id}.log):"
    tail = [intro, *run.lines[-TAIL_LINES:]]
    raise RunStoppedError(f"M{row.id} stopped: {verdict.reason}", tail)


def append_timing(path: Path, result: Result) -> None:
    """Append a row (ID, model, effort, start, seconds, result) to the CSV; new: a header first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(["id", "model", "effort", "start", "seconds", "result"])
        writer.writerow(
            [
                f"M{result.id}",
                result.model,
                result.effort,
                result.started_at,
                f"{result.seconds:.1f}",
                result.outcome,
            ]
        )


def record_result(session: Session, result: Result) -> None:
    """Keep the result, add it to timings.csv (only a warning if that fails), and print its line."""
    session.state.results.append(result)
    try:
        append_timing(session.paths.timings, result)
    except OSError as exc:
        session.console.say(f"WARNING: could not write {session.paths.timings}: {exc}", "yellow")
    session.console.say(result_line(result), outcome_color(result.outcome))


def show_range_progress(session: Session, row: Row, run: ClaudeRun) -> None:
    """Print a bar of the milestones done in this run, and the last TLDR line of the output."""
    done, total = len(session.state.results), session.state.total
    bar = bar_text(done, total, RANGE_BAR)
    session.console.say(f"M{row.id}/M{session.last} [{bar}] {percent(done, total)}%", "green")
    tldr = next(
        (line for line in reversed(run.lines) if re.search("TLDR", line, re.IGNORECASE)), None
    )
    if tldr is not None:
        session.console.say(tldr)


def prepare_milestone(paths: Paths, row: Row) -> None:
    """Check what the milestone needs before claude starts.

    Raises:
        RunStoppedError: If it waits for an approval, or its model or effort cannot be used.
    """
    if row.status == STATUS_BLOCKED:
        raise waiting_for_approval(paths, row)
    problem = row_problem(row)
    if problem is not None:
        raise _error(problem)


def run_milestone(session: Session, row: Row) -> None:
    """Run one milestone with the live status line, time it, and check that it finished.

    Raises:
        RunStoppedError: If the milestone is blocked or did not finish.
    """
    session.console.say()
    session.console.say(f"Starting M{row.id} | {row.model} | {row.effort}")
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    watch = Stopwatch()
    with LiveStatus(session.console, lambda: status_text(session.state.progress(row, watch))):
        run = run_claude(session.paths, row)
    seconds = watch.elapsed()
    verdict = judge(session.paths, row, run)
    record_result(
        session,
        Result(row.id, row.title, row.model, row.effort, started_at, seconds, verdict.outcome),
    )
    if verdict.outcome != OUTCOME_DONE:
        stop_for(session.paths, row, verdict, run)
    show_range_progress(session, row, run)


def _range_rows(session: Session) -> list[Row]:
    """Return the rows of the range as the plan has them now (a milestone edits its own status)."""
    rows = parse_plan_rows(_read_lines(session.paths.plan))
    return rows_in_range(rows, session.first, session.last)


def run_all(options: Options, console: Console, paths: Paths, state: RunState) -> None:
    """Run every milestone of the range whose status is not done, in table order.

    Args:
        options: The command-line options.
        console: The terminal.
        paths: The repository files.
        state: Filled in as milestones finish; main() prints the summary from it.

    Raises:
        RunStoppedError: At the first problem. Nothing is retried.
    """
    rows = parse_plan_rows(_read_lines(paths.plan))
    first, last = resolve_range(rows, options.start, options.end)
    check_range(first, last)
    preflight(paths)
    state.total = sum(1 for row in rows_in_range(rows, first, last) if row.status != "done")
    session = Session(paths, console, state, first, last)
    while True:
        row = next_open_row(_range_rows(session))
        if row is None:
            console.say(f"Range M{first} to M{last} is done.", "green")
            return
        prepare_milestone(paths, row)
        run_milestone(session, row)


def run_guarded(options: Options, console: Console, paths: Paths, state: RunState) -> int:
    """Run the range; print a stop or an interrupt instead of a traceback. Return the exit code."""
    try:
        run_all(options, console, paths, state)
    except RunStoppedError as stop:
        console.say(stop.message, stop.color)
        for line in stop.details:
            console.say(line)
        return 1
    except KeyboardInterrupt:
        console.say("Interrupted.", "yellow")
        return 130
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the milestones and print the summary, also when the run stops early.

    Args:
        argv: The command-line arguments; None means sys.argv.

    Returns:
        0 when the range is done, 1 when a milestone stopped the run, 130 after Ctrl+C.
    """
    options = parse_args(argv)
    console = start_console()
    paths = Paths(Path(__file__).resolve().parent.parent)
    state = RunState(total=0, stopwatch=Stopwatch())
    try:
        return run_guarded(options, console, paths, state)
    finally:
        print_summary(console, state)  # also after an unexpected error


if __name__ == "__main__":
    sys.exit(main())
