"""A stand-in for the GitHub CLI, used by the init_project.py tests. It never contacts GitHub.

`gh.cmd` (written by the tests) runs this file. It answers the three calls init_project.py makes:

    gh api user --jq .login      prints "tester", or fails when FAKE_GH_STATE is "logged-out"
    gh repo view OWNER/NAME      fails ("not found"), or succeeds when FAKE_GH_STATE is "taken"
    gh repo create NAME ...      adds `origin` pointing at FAKE_GH_REMOTE (a local bare repository)

Every call is appended to FAKE_GH_LOG, one JSON list of arguments per line.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def log_call(args: list[str]) -> None:
    """Append the arguments of this call to the log file."""
    with Path(os.environ["FAKE_GH_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")


def api_user(state: str) -> int:
    """Answer `gh api user`: the login name, unless logged out."""
    if state == "logged-out":
        sys.stderr.write("To get started with GitHub CLI, please run:  gh auth login\n")
        return 4
    sys.stdout.write("tester\n")
    return 0


def repo_view(state: str) -> int:
    """Answer `gh repo view`: found only when the name is taken."""
    if state == "taken":
        sys.stdout.write("name:\ttester/taken\n")
        return 0
    sys.stderr.write("GraphQL: Could not resolve to a Repository with the name.\n")
    return 1


def repo_create() -> int:
    """Answer `gh repo create --source . --remote origin`: add the remote, as gh does."""
    git = shutil.which("git")
    if git is None:
        sys.stderr.write("fake gh: git not found\n")
        return 1
    remote = os.environ["FAKE_GH_REMOTE"]
    # S603 is ignored on purpose: this fake runs only git, with arguments the test controls.
    result = subprocess.run([git, "remote", "add", "origin", remote], check=False)  # noqa: S603
    sys.stdout.write(f"https://github.com/tester/{Path.cwd().name}\n")
    return result.returncode


def main() -> int:
    """Log the call, then answer it like gh would."""
    args = sys.argv[1:]
    log_call(args)
    state = os.environ.get("FAKE_GH_STATE", "ok")
    if args[:2] == ["api", "user"]:
        return api_user(state)
    if args[:2] == ["repo", "view"]:
        return repo_view(state)
    if args[:2] == ["repo", "create"]:
        return repo_create()
    sys.stderr.write(f"fake gh: unexpected call: {args}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
