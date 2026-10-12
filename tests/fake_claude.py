"""A stand-in for `claude -p`, used by the milestone runner tests. It never calls a model.

`claude.cmd` (written by the tests, first on PATH) runs this file. It reads the runner's prompt on
stdin, finds the milestone number and title, and acts by FAKE_CLAUDE_STATE:

    (unset)    finishes it: deletes its row and block from docs/plan.md, commits, and pushes
    "blocked"  writes a blocker to docs/blocked.md and commits nothing
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


def finish(number: int, title: str) -> int:
    """Do what a finished milestone does: update the plan, commit, and push."""
    plan = Path("docs/plan.md")
    plan.write_text(without_milestone(plan.read_text("utf-8"), number), encoding="utf-8")
    git = shutil.which("git") or "git"
    for args in (["add", "docs/plan.md"], ["commit", "-m", f"M{number}: {title}"], ["push"]):
        # S603 is ignored on purpose: this fake runs only git, with arguments the test controls.
        result = subprocess.run([git, *args], check=False)  # noqa: S603
        if result.returncode != 0:
            return result.returncode
    sys.stdout.write(f"- **TLDR: M{number} is done.**\n")
    return 0


def main() -> int:
    """Log the call, then act on the milestone named in the prompt."""
    log_call(sys.argv[1:])
    prompt = sys.stdin.read()
    match = re.search(r"milestone M(\d+) \((.*?)\) from docs/plan\.md", prompt)
    if match is None:
        sys.stderr.write("fake claude: no milestone in the prompt\n")
        return 1
    state = os.environ.get("FAKE_CLAUDE_STATE", "")
    if state == "blocked":
        blocker = f"# Blocked: M{match[1]} ({match[2]})\n\nNeeds a decision: which database?\n"
        Path("docs/blocked.md").write_text(blocker, "utf-8")
        return 0
    if state == "idle":
        return 0
    return finish(int(match[1]), match[2])


if __name__ == "__main__":
    raise SystemExit(main())
