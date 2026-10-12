"""Run the project's checks: ruff and mypy for Python, ESLint and tsc for JavaScript.

Two hooks run it, and so can you:
    python scripts/check.py            # every check. The git pre-commit hook runs this.
    python scripts/check.py --edited   # one edited file, with a Claude Code hook's JSON on stdin

The Python checks run when `ruff.toml` exists, the JavaScript checks when `package.json` exists.
mypy runs once `src/` holds Python; ESLint and tsc once `src/` or `tests/` holds JavaScript. Tests
are not run here: they belong to the workflow (`docs/workflow.md`).

The full run exits 2 if anything fails, so that git refuses the commit. With --edited, ruff or
ESLint fixes what it can in that one file, and the rest goes back to Claude as a JSON `block`
decision on stdout (exit 0). Claude Code may run hooks in PowerShell, which turns every failing
exit code into 1, so an exit code alone would not reach Claude. A tool that is not installed fails
the full run, but is skipped after an edit.
"""

import argparse
import json
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILED = 2
JS_SUFFIXES = {".js", ".mjs", ".cjs", ".ts"}


def run(command: list[str]) -> tuple[int, str]:
    """Run a command in the project root. Return its exit code and its output."""
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def python_tool(*args: str) -> list[str]:
    """Return the command that runs a Python tool from this environment."""
    return [sys.executable, "-m", *args]


def has_files(folders: list[str], suffixes: set[str]) -> bool:
    """Return True if any of the folders holds a file with one of the suffixes."""
    return any(p.suffix in suffixes for folder in folders for p in (ROOT / folder).rglob("*"))


def python_checks() -> list[list[str]]:
    """Return the Python checks: lint and format always, types once `src/` holds Python."""
    if not (ROOT / "ruff.toml").is_file():
        return []
    checks = [python_tool("ruff", "check", "."), python_tool("ruff", "format", "--check", ".")]
    if has_files(["src"], {".py"}):
        checks.append(python_tool("mypy"))
    return checks


def javascript_checks() -> list[list[str]]:
    """Return the JavaScript checks, once `src/` or `tests/` holds JavaScript."""
    if not (ROOT / "package.json").is_file() or not has_files(["src", "tests"], JS_SUFFIXES):
        return []
    npm = shutil.which("npm") or "npm"
    return [[npm, "run", "lint"], [npm, "run", "typecheck"]]


def why_not_runnable(command: list[str]) -> str:
    """Return why a check cannot run (its tool is not installed), or '' if it can."""
    if command[1:2] == ["-m"]:
        if find_spec(command[2]) is None:
            return f"`{command[2]}` is not installed in this environment. See the README's Setup."
        return ""
    if shutil.which(command[0]) is None:
        return f"`{Path(command[0]).name}` is not installed."
    if not (ROOT / "node_modules").is_dir():
        return "The JavaScript tools are not installed. Run `npm install`."
    return ""


def label(command: list[str]) -> str:
    """Return a short name for a check, such as `ruff check .` or `npm run lint`."""
    words = command[2:] if command[1:2] == ["-m"] else [Path(command[0]).stem, *command[1:]]
    return " ".join(words)


def check_all() -> int:
    """Run every check that applies and print each failure. Return 0 or FAILED."""
    failures: list[str] = []
    for command in python_checks() + javascript_checks():
        problem = why_not_runnable(command)
        if not problem:
            code, output = run(command)
            problem = output if code else ""
        if problem:
            failures.append(f"`{label(command)}` failed:\n{problem}")
    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        return FAILED
    print("All checks passed.")
    return 0


def edited_file(hook_input: str) -> Path | None:
    """Return the file a Claude Code hook says was edited, if it is a file in this project."""
    tool_input = json.loads(hook_input or "{}").get("tool_input", {})
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    path = (ROOT / raw).resolve()
    return path if raw and path.is_relative_to(ROOT) and path.is_file() else None


def fix_commands(path: Path) -> list[list[str]]:
    """Return the commands that fix one file and report what they cannot fix.

    Python is formatted before the fixes (so line breaks do not count as errors) and after them
    (so a removed import leaves no blank line behind).
    """
    relative = str(path.relative_to(ROOT))
    if path.suffix == ".py" and (ROOT / "ruff.toml").is_file():
        formatting = python_tool("ruff", "format", relative)
        fixes = python_tool("ruff", "check", "--fix", "--output-format=concise", relative)
        return [formatting, fixes, formatting]
    eslint = shutil.which("eslint", path=str(ROOT / "node_modules" / ".bin"))
    if path.suffix in JS_SUFFIXES and eslint:
        return [[eslint, "--fix", relative]]
    return []


def check_edited(hook_input: str) -> int:
    """Fix and check the file named in the hook input. Print what is left as a block decision."""
    path = edited_file(hook_input)
    commands = fix_commands(path) if path else []
    if any(why_not_runnable(command) for command in commands):
        return 0
    results = [run(command) for command in commands]
    problems = list(dict.fromkeys(output for code, output in results if code))
    if problems:
        reason = f"Checks failed for {path}. Fix these:\n" + "\n".join(problems)
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="Run the project's checks.")
    parser.add_argument(
        "--edited", action="store_true", help="check one file named by a hook's JSON on stdin"
    )
    return parser.parse_args()


def main() -> int:
    """Run the full checks, or the checks for one edited file."""
    if parse_args().edited:
        return check_edited(sys.stdin.buffer.read().decode("utf-8"))
    return check_all()


if __name__ == "__main__":
    raise SystemExit(main())
