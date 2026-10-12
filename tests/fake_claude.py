"""A stand-in for `claude -p`, used by the milestone runner tests. It never calls a model.

`claude.cmd` (written by the tests, first on PATH) runs this file. It reads the runner's prompt on
stdin, finds the milestone number and title, and acts by FAKE_CLAUDE_STATE:

    (unset)    finishes it: deletes its row and block from docs/plan.md, commits, and pushes
    "blocked"  blocks it, unless its block has an Approval entry: sets its Status to `blocked`,
               adds a Blocked entry to its block, commits docs/plan.md alone, and pushes
    "idle"     does nothing

Every call's arguments are appended to FAKE_CLAUDE_LOG, one JSON list per line.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLAN = Path("docs/plan.md")
QUESTION = "- **Blocked:** Needs a decision: which database?"


def log_call(args: list[str]) -> None:
    """Append the arguments of this call to the log file."""
    with Path(os.environ["FAKE_CLAUDE_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")


def without_milestone(plan: str, number: int) -> str:
    """Return the plan without the milestone's table row and its `### M<n>` block."""
    kept: list[str] = []
    in_block = False
    for line in plan.splitlines():
        if line.startswith(("### ", "## ")):
            in_block = line.startswith(f"### M{number} ")
        if not in_block and not line.startswith(f"| **M{number}**"):
            kept.append(line)
    return "\n".join(kept) + "\n"


def with_question(plan: str, number: int) -> str:
    """Return the plan with the milestone's Status set to blocked and a Blocked entry added."""
    lines = plan.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"| **M{number}**"):
            lines[i] = re.sub(r"\|\s*\w+\s*\|\s*$", "| blocked |", line)
    heading = next(i for i, line in enumerate(lines) if line.startswith(f"### M{number} "))
    end = next((i for i in range(heading + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    while end > heading and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, QUESTION)
    return "\n".join(lines) + "\n"


def git(*args: str) -> int:
    """Run git and return its exit code."""
    # S603 is ignored on purpose: this fake runs only git, with arguments the test controls.
    return subprocess.run([shutil.which("git") or "git", *args], check=False).returncode  # noqa: S603


def commit_plan(text: str, message: str) -> int:
    """Write the plan, commit it alone with the message, and push."""
    PLAN.write_text(text, encoding="utf-8")
    for args in (["add", str(PLAN)], ["commit", "-m", message], ["push"]):
        code = git(*args)
        if code != 0:
            return code
    return 0


def act(state: str, number: int, title: str) -> int:
    """Block, finish, or skip the milestone, by the state the test set."""
    plan = PLAN.read_text(encoding="utf-8")
    approved = "**Approval:**" in plan
    if state == "idle":
        return 0
    if state == "blocked" and not approved:
        return commit_plan(with_question(plan, number), f"M{number}: blocked")
    code = commit_plan(without_milestone(plan, number), f"M{number}: {title}")
    sys.stdout.write(f"- **TLDR: M{number} is done.**\n")
    return code


def main() -> int:
    """Log the call, then act on the milestone named in the prompt."""
    log_call(sys.argv[1:])
    match = re.search(r"milestone M(\d+) \((.*?)\) from docs/plan\.md", sys.stdin.read())
    if match is None:
        sys.stderr.write("fake claude: no milestone in the prompt\n")
        return 1
    return act(os.environ.get("FAKE_CLAUDE_STATE", ""), int(match[1]), match[2])


if __name__ == "__main__":
    raise SystemExit(main())
