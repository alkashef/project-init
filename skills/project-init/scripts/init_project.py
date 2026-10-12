"""Set up the current folder as a new project: scaffold, git, GitHub, and a conda environment.

Run it from a new, empty project folder (the folder open in VS Code). Nothing is changed until
every check passes. Then, in order: `git init` (unless the folder is already a repository with no
commits), build the scaffold with build_instance.py (CLAUDE.md, rules, docs, configs, starting
folders), commit, create the GitHub repository (unless `origin` already exists), push, and create
a conda environment with the project's name (unless one exists). The scaffold files come from the
skill's `assets/` folder (next to this `scripts/` folder).

Usage:
    python init_project.py --with python http-apis --purpose "Does X"
    python init_project.py --no-github            # local repository only
    python init_project.py --remote-url URL       # push to a repository that exists
Options: --name (default: the folder name), --folder (default: the current folder), --public (the
default is private), --no-conda (no conda environment).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Plan:
    """What the checks found: the tools to use and the state of the folder."""

    git: str
    gh: str | None
    has_repo: bool
    has_origin: bool
    conda: str | None
    has_env: bool


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output. The caller checks the return code."""
    # S603 is ignored here on purpose: this script exists to run git and gh. Every argument is a
    # separate list item (the name is checked by check_name), and no command goes through a shell.
    return subprocess.run(  # noqa: S603
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_ok(command: list[str], cwd: Path | None = None) -> str:
    """Run a command and return its stdout. Exit with the command's own error text on failure."""
    result = run(command, cwd)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"error: `{' '.join(command)}` failed:\n{detail}")
    return result.stdout.strip()


def find_tool(name: str, hint: str) -> str:
    """Return the full path of a tool on PATH, or exit with how to install it."""
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"error: `{name}` is not installed. {hint}")
    return path


def check_name(name: str) -> None:
    """Exit unless the name is safe as a repository name, a conda environment name, and a title."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", name):
        raise SystemExit(
            f"error: the project name '{name}' may hold only letters, digits, '.', '_' and '-', "
            "and must start with a letter or a digit. Pass a valid one with --name."
        )


def check_folder(folder: Path) -> None:
    """Exit unless the folder exists and is empty, apart from .git, .claude, and .vscode."""
    if not folder.is_dir():
        raise SystemExit(f"error: {folder} is not a folder.")
    extra = sorted(p.name for p in folder.iterdir() if p.name not in {".git", ".claude", ".vscode"})
    if extra:
        raise SystemExit(
            f"error: {folder} already holds {', '.join(extra[:5])}. "
            "This skill is for a new, empty project folder."
        )


def check_git_identity(git: str) -> None:
    """Exit unless git knows who is committing."""
    for key in ("user.name", "user.email"):
        if not run([git, "config", key]).stdout.strip():
            raise SystemExit(f'error: git has no {key}. Run: git config --global {key} "<value>"')


def check_repo(git: str, folder: Path) -> bool:
    """Return True if the folder is already a repository. Exit if that repository has commits."""
    if not (folder / ".git").exists():
        return False
    if run([git, "rev-parse", "--verify", "HEAD"], folder).returncode == 0:
        raise SystemExit(f"error: {folder} already has commits. This skill is for a new project.")
    return True


def check_github(gh: str, name: str) -> None:
    """Exit unless gh is logged in and the account has no repository with this name."""
    who = run([gh, "api", "user", "--jq", ".login"])
    if who.returncode != 0:
        raise SystemExit(
            f"error: gh cannot read the account: {who.stderr.strip()}\nRun: gh auth login"
        )
    owner = who.stdout.strip()
    if run([gh, "repo", "view", f"{owner}/{name}"]).returncode == 0:
        raise SystemExit(f"error: github.com/{owner}/{name} already exists. Pick another name.")


def github_tool(name: str) -> str:
    """Return the gh path after checking the login and that the repository name is free."""
    hint = "Install it with `winget install GitHub.cli`, then run `gh auth login`."
    gh = find_tool("gh", hint)
    check_github(gh, name)
    return gh


def find_conda() -> str:
    """Return the conda executable: $CONDA_EXE, conda on PATH, or Miniconda's default place."""
    candidates = [os.environ.get("CONDA_EXE", ""), shutil.which("conda") or ""]
    for home in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("USERPROFILE", "")):
        if home:
            candidates.append(str(Path(home) / "miniconda3" / "Scripts" / "conda.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit(
        "error: conda is not installed. Install Miniconda, or pass --no-conda to skip the "
        "project's conda environment."
    )


def conda_env_exists(conda: str, name: str) -> bool:
    """Return True if conda already has an environment with this name."""
    envs: list[str] = json.loads(run_ok([conda, "env", "list", "--json"]))["envs"]
    return any(Path(env).name == name for env in envs)


def create_env(conda: str, name: str) -> None:
    """Create the project's conda environment. On failure, say how to finish by hand."""
    command = [conda, "create", "-n", name, "python=3.12", "-y"]
    result = run(command)
    if result.returncode != 0:
        raise SystemExit(
            f"error: conda could not create the environment:\n{result.stderr.strip()}\n"
            "The project is set up and committed. Run "
            f"`conda create -n {name} python=3.12` yourself."
        )


def build_command(folder: Path, args: argparse.Namespace) -> list[str]:
    """Return the command that builds the scaffold."""
    builder = Path(__file__).resolve().with_name("build_instance.py")
    command = [sys.executable, str(builder), str(folder)]
    if args.flags:
        command += ["--with", *args.flags]
    options = {
        "--name": args.name,
        "--purpose": args.purpose,
        "--stack": args.stack,
        "--test-command": args.test_command,
        "--run-command": args.run_command,
    }
    for option, value in options.items():
        if value:
            command += [option, value]
    return command


def preflight(args: argparse.Namespace, folder: Path) -> Plan:
    """Check everything before changing anything. Return what was found."""
    check_name(args.name)
    check_folder(folder)
    git = find_tool("git", "Install Git for Windows.")
    check_git_identity(git)
    has_repo = check_repo(git, folder)
    has_origin = has_repo and run([git, "remote", "get-url", "origin"], folder).returncode == 0
    if has_origin and args.remote_url:
        raise SystemExit("error: this repository already has an `origin`. Drop --remote-url.")
    run_ok([*build_command(folder, args), "--dry-run"])
    needs_gh = not (args.no_github or args.remote_url or has_origin)
    gh = github_tool(args.name) if needs_gh else None
    conda = None if args.no_conda else find_conda()
    has_env = conda is not None and conda_env_exists(conda, args.name)
    return Plan(git, gh, has_repo, has_origin, conda, has_env)


def create_project(args: argparse.Namespace, folder: Path, plan: Plan) -> list[str]:
    """Start the repository, build the scaffold, and commit it. Return the builder's report."""
    if plan.has_repo:
        run_ok([plan.git, "symbolic-ref", "HEAD", "refs/heads/main"], folder)
    else:
        run_ok([plan.git, "init", "-b", "main"], folder)
    report = run_ok(build_command(folder, args))
    run_ok([plan.git, "add", "-A"], folder)
    run_ok([plan.git, "commit", "-m", "Initial scaffold from project-init"], folder)
    return report.splitlines()


def push(git: str, folder: Path) -> None:
    """Push main to origin. On failure, say how to finish by hand."""
    result = run([git, "push", "-u", "origin", "main"], folder)
    if result.returncode != 0:
        raise SystemExit(
            f"error: the push failed:\n{result.stderr.strip()}\n"
            "The project is committed locally. Fix the cause, then run "
            f"`git push -u origin main` in {folder}."
        )


def publish(args: argparse.Namespace, folder: Path, plan: Plan) -> str:
    """Add the remote (creating the GitHub repository unless one exists) and push.

    Returns:
        The remote URL, or an empty string when the project stays local.
    """
    if args.no_github:
        return ""
    if plan.gh:
        command = [plan.gh, "repo", "create", args.name, "--source", ".", "--remote", "origin"]
        command.append("--public" if args.public else "--private")
        if args.purpose:
            command += ["--description", args.purpose]
        run_ok(command, folder)
    elif args.remote_url:
        run_ok([plan.git, "remote", "add", "origin", args.remote_url], folder)
    push(plan.git, folder)
    return run_ok([plan.git, "remote", "get-url", "origin"], folder)


def set_up_env(name: str, plan: Plan) -> str:
    """Create the conda environment unless it exists or was skipped. Return what happened."""
    if plan.conda is None:
        return "skipped (--no-conda)"
    if plan.has_env:
        return f"{name} (already existed, kept as it was)"
    create_env(plan.conda, name)
    return f"{name} (created, Python 3.12)"


def add_remote_options(parser: argparse.ArgumentParser) -> None:
    """Add the options that say where the project is pushed."""
    parser.add_argument("--public", action="store_true", help="make the repository public")
    remote = parser.add_mutually_exclusive_group()
    remote.add_argument("--no-github", action="store_true", help="keep the project local")
    remote.add_argument("--remote-url", default="", help="push to this existing repository")


def parse_args() -> argparse.Namespace:
    """Read the command-line options. The name defaults to the folder name."""
    parser = argparse.ArgumentParser(description="Set up this folder as a new project.")
    parser.add_argument("--name", default="", help="project and repository name (default: folder)")
    parser.add_argument("--folder", type=Path, default=Path.cwd(), help="default: current folder")
    parser.add_argument("--with", dest="flags", nargs="*", default=[], help="optional modules")
    parser.add_argument("--purpose", default="", help="one line: what the project does")
    parser.add_argument("--stack", default="", help="overrides the stack line")
    parser.add_argument("--test-command", default="", help="overrides the test command")
    parser.add_argument("--run-command", default="", help="overrides the run command")
    add_remote_options(parser)
    parser.add_argument("--no-conda", action="store_true", help="no conda environment")
    args = parser.parse_args()
    args.folder = args.folder.resolve()
    args.name = args.name or args.folder.name
    return args


def main() -> int:
    """Set up the project and print what was done."""
    args = parse_args()
    plan = preflight(args, args.folder)
    report = create_project(args, args.folder, plan)
    url = publish(args, args.folder, plan)
    env = set_up_env(args.name, plan)
    skipped = [line for line in report if line.startswith("skipped")]
    print(f"Set up {args.folder}: {len(report) - len(skipped)} files and folders, committed.")
    if skipped:
        print(f"{len(skipped)} already existed and were kept as they were.")
    print(f"Remote: {url or 'none (local git only)'}")
    print(f"Conda environment: {env}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
