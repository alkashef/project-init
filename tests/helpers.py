"""Helpers for the tests: running the skill's scripts, git, and the fake gh and conda."""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "project-init" / "scripts"
FAKE_GH = Path(__file__).resolve().with_name("fake_gh.py")
FAKE_CONDA = Path(__file__).resolve().with_name("fake_conda.py")
REAL_TOOLS = ("gh.exe", "gh.cmd", "gh", "conda.exe", "conda.bat", "conda.cmd")
IDENTITY = "[user]\n\tname = Test User\n\temail = test@example.com\n"


def run(
    command: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output. The caller checks the return code."""
    # S603 is ignored on purpose: the tests run only git and the skill's own scripts.
    return subprocess.run(  # noqa: S603
        command,
        cwd=cwd,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_path() -> str:
    """Return the full path of git. The tests cannot run without it."""
    path = shutil.which("git")
    if path is None:
        raise RuntimeError("git is not installed")
    return path


def path_without_real_tools() -> list[str]:
    """Return the PATH folders, minus any that hold a real gh or conda, so only fakes are found.

    The rest of PATH stays: git needs its own folders (a push to a local remote runs `sh`).
    """
    folders = os.environ.get("PATH", "").split(os.pathsep)
    return [f for f in folders if f and not any((Path(f) / n).exists() for n in REAL_TOOLS)]


def build(target: Path, *options: str) -> subprocess.CompletedProcess[str]:
    """Run build_instance.py on the target folder."""
    return run([sys.executable, str(SCRIPTS / "build_instance.py"), str(target), *options])


def shim(folder: Path, name: str, script: Path) -> Path:
    """Write a `.cmd` file that runs a fake tool's script, and return its path."""
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}.cmd"
    path.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    return path


def logged_calls(log: Path) -> list[list[str]]:
    """Return the arguments of every call a fake tool logged, in order."""
    if not log.exists():
        return []
    calls: list[list[str]] = [json.loads(line) for line in log.read_text("utf-8").splitlines()]
    return calls


def text_files(root: Path) -> dict[str, str]:
    """Return every file under root (relative POSIX path to text), outside .git."""
    files = (p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in files}


@dataclass
class Sandbox:
    """A project folder, a bare repository as its remote, an isolated git, fake gh and conda."""

    folder: Path
    remote: Path
    fake_bin: Path
    env: dict[str, str]

    def init(self, *options: str) -> subprocess.CompletedProcess[str]:
        """Run init_project.py in the project folder."""
        script = str(SCRIPTS / "init_project.py")
        return run([sys.executable, script, *options], self.folder, self.env)

    def git(self, *args: str) -> str:
        """Run git in the project folder and return its output. Fail the test if git fails."""
        result = run([git_path(), *args], self.folder, self.env)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    def remote_head(self) -> str:
        """Return the commit that `main` points to in the remote, or '' if it has none."""
        result = run([git_path(), "--git-dir", str(self.remote), "rev-parse", "main"], env=self.env)
        return result.stdout.strip() if result.returncode == 0 else ""

    def gh_calls(self) -> list[list[str]]:
        """Return the arguments of every call made to the fake gh, in order."""
        return logged_calls(Path(self.env["FAKE_GH_LOG"]))

    def conda_calls(self) -> list[list[str]]:
        """Return the arguments of every call made to the fake conda, in order."""
        return logged_calls(Path(self.env["FAKE_CONDA_LOG"]))

    def remove_gh(self) -> None:
        """Take the fake gh off PATH, as if gh were not installed."""
        self.env["PATH"] = os.pathsep.join(
            p for p in self.env["PATH"].split(os.pathsep) if Path(p) != self.fake_bin
        )

    def remove_conda(self) -> None:
        """Hide the fake conda and Miniconda's default places, as if conda were not installed."""
        del self.env["CONDA_EXE"]
        nowhere = str(self.folder.parent / "no-home")
        self.env.update({"LOCALAPPDATA": nowhere, "USERPROFILE": nowhere})

    def forget_identity(self) -> None:
        """Empty the git config, as if git had no user.name or user.email."""
        Path(self.env["GIT_CONFIG_GLOBAL"]).write_text("", encoding="utf-8")

    def snapshot(self) -> dict[str, tuple[int, int]]:
        """Return every path in the folder (including .git) with its size and change time."""
        return {
            p.relative_to(self.folder).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in self.folder.rglob("*")
        }


def make_sandbox(root: Path) -> Sandbox:
    """Create a sandbox under root: an empty `demo` folder, a bare remote, fake gh and conda."""
    folder, remote, fake_bin = root / "demo", root / "remote.git", root / "bin"
    folder.mkdir()
    shim(fake_bin, "gh", FAKE_GH)
    # conda is found through CONDA_EXE, so it stays off PATH: remove_conda() can then hide it.
    conda = shim(root / "conda-bin", "conda", FAKE_CONDA)
    (root / "gitconfig").write_text(IDENTITY, encoding="utf-8")
    env = dict(os.environ)
    env.update(
        {
            "PATH": os.pathsep.join([str(fake_bin), *path_without_real_tools()]),
            "GIT_CONFIG_GLOBAL": str(root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "FAKE_GH_LOG": str(root / "gh.log"),
            "FAKE_GH_REMOTE": str(remote),
            "CONDA_EXE": str(conda),
            "FAKE_CONDA_LOG": str(root / "conda.log"),
        }
    )
    assert run([git_path(), "init", "--bare", "-b", "main", str(remote)], env=env).returncode == 0
    return Sandbox(folder, remote, fake_bin, env)
