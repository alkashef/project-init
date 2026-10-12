"""A stand-in for conda, used by the init_project.py tests. It never creates an environment.

`conda.cmd` (written by the tests, and named in CONDA_EXE) runs this file. It answers the two
calls init_project.py makes:

    conda env list --json        lists the names in FAKE_CONDA_ENVS (separated by os.pathsep)
    conda create -n NAME ...     succeeds, or fails when FAKE_CONDA_STATE is "fail"

Every call is appended to FAKE_CONDA_LOG, one JSON list of arguments per line.
"""

import json
import os
import sys
from pathlib import Path


def log_call(args: list[str]) -> None:
    """Append the arguments of this call to the log file."""
    with Path(os.environ["FAKE_CONDA_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")


def env_list() -> int:
    """Answer `conda env list --json` with the base environment and the fake ones."""
    names = [n for n in os.environ.get("FAKE_CONDA_ENVS", "").split(os.pathsep) if n]
    root = Path("C:/fake/miniconda3")
    envs = [str(root)] + [str(root / "envs" / name) for name in names]
    sys.stdout.write(json.dumps({"envs": envs}) + "\n")
    return 0


def create() -> int:
    """Answer `conda create`: succeed, unless told to fail."""
    if os.environ.get("FAKE_CONDA_STATE") == "fail":
        sys.stderr.write("CondaHTTPError: HTTP 000 CONNECTION FAILED\n")
        return 1
    return 0


def main() -> int:
    """Log the call, then answer it like conda would."""
    args = sys.argv[1:]
    log_call(args)
    if args[:3] == ["env", "list", "--json"]:
        return env_list()
    if args[:1] == ["create"]:
        return create()
    sys.stderr.write(f"fake conda: unexpected call: {args}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
