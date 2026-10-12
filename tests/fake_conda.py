"""A stand-in for conda, used by the init_project.py tests. It never creates an environment.

`conda.cmd` (written by the tests, and named in CONDA_EXE) runs this file. It answers the calls
init_project.py makes:

    conda env list --json                        the names in FAKE_CONDA_ENVS (os.pathsep-separated)
    conda create -n NAME ...                     fails when FAKE_CONDA_STATE is "fail"
    conda run -n NAME python -m pip install ...  fails when FAKE_PIP_STATE is "fail"
    conda run -n NAME python -m pip list ...     every tool at version 1.2.3, as JSON

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


def pip(args: list[str]) -> int:
    """Answer `conda run -n NAME python -m pip ...`: install, or list what is installed."""
    if args[:1] == ["install"]:
        if os.environ.get("FAKE_PIP_STATE") == "fail":
            sys.stderr.write("ERROR: No matching distribution found for ruff\n")
            return 1
        return 0
    names = ["pip", "pytest", "pytest_cov", "mypy", "ruff", "python-dotenv"]
    sys.stdout.write(json.dumps([{"name": n, "version": "1.2.3"} for n in names]) + "\n")
    return 0


def main() -> int:
    """Log the call, then answer it like conda would."""
    args = sys.argv[1:]
    log_call(args)
    if args[:3] == ["env", "list", "--json"]:
        return env_list()
    if args[:1] == ["create"]:
        return create()
    if args[:1] == ["run"] and args[3:6] == ["python", "-m", "pip"]:
        return pip(args[6:])
    sys.stderr.write(f"fake conda: unexpected call: {args}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
