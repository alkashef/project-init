"""init_project.py end to end, against a fake gh and a local bare repository as the remote."""

from collections.abc import Callable
from pathlib import Path

import pytest
from helpers import Sandbox


def test_new_project_is_committed_and_pushed(sandbox: Sandbox) -> None:
    result = sandbox.init("--with", "python", "--purpose", "Counts sheep")
    assert result.returncode == 0, result.stderr
    assert sandbox.git("rev-list", "--count", "HEAD") == "1"
    assert sandbox.git("branch", "--show-current") == "main"
    assert sandbox.git("status", "--porcelain") == ""
    assert sandbox.remote_head() == sandbox.git("rev-parse", "HEAD")


def test_repository_is_created_private_with_the_purpose(sandbox: Sandbox) -> None:
    sandbox.init("--purpose", "Counts sheep")
    created = [call for call in sandbox.gh_calls() if call[:2] == ["repo", "create"]]
    expected = ["demo", "--source", ".", "--remote", "origin", "--private"]
    assert created == [["repo", "create", *expected, "--description", "Counts sheep"]]


def test_public_flag_creates_a_public_repository(sandbox: Sandbox) -> None:
    sandbox.init("--public")
    created = [call for call in sandbox.gh_calls() if call[:2] == ["repo", "create"]]
    assert "--public" in created[0]
    assert "--private" not in created[0]


def test_no_github_stays_local_without_gh(sandbox: Sandbox) -> None:
    sandbox.remove_gh()
    result = sandbox.init("--no-github")
    assert result.returncode == 0, result.stderr
    assert "none (local git only)" in result.stdout
    assert sandbox.git("remote") == ""
    assert sandbox.git("rev-list", "--count", "HEAD") == "1"


def test_remote_url_pushes_without_gh(sandbox: Sandbox) -> None:
    sandbox.remove_gh()
    result = sandbox.init("--remote-url", str(sandbox.remote))
    assert result.returncode == 0, result.stderr
    assert sandbox.git("remote", "get-url", "origin") == str(sandbox.remote)
    assert sandbox.remote_head() == sandbox.git("rev-parse", "HEAD")


def test_existing_empty_repository_is_used(sandbox: Sandbox) -> None:
    sandbox.git("init", "-b", "master")
    result = sandbox.init()
    assert result.returncode == 0, result.stderr
    assert sandbox.git("branch", "--show-current") == "main"
    assert sandbox.git("rev-list", "--count", "HEAD") == "1"


def test_existing_origin_is_pushed_to_without_gh(sandbox: Sandbox) -> None:
    sandbox.git("init")
    sandbox.git("remote", "add", "origin", str(sandbox.remote))
    result = sandbox.init()
    assert result.returncode == 0, result.stderr
    assert sandbox.gh_calls() == []
    assert sandbox.remote_head() == sandbox.git("rev-parse", "HEAD")


def test_existing_vscode_settings_are_kept(sandbox: Sandbox) -> None:
    (sandbox.folder / ".vscode").mkdir()
    (sandbox.folder / ".vscode" / "settings.json").write_text("{}", encoding="utf-8")
    result = sandbox.init()
    assert result.returncode == 0, result.stderr
    assert (sandbox.folder / ".vscode" / "settings.json").read_text(encoding="utf-8") == "{}"
    assert "1 already existed" in result.stdout


def test_failed_push_says_how_to_finish(sandbox: Sandbox, tmp_path: Path) -> None:
    sandbox.env["FAKE_GH_REMOTE"] = str(tmp_path / "missing.git")
    result = sandbox.init()
    assert result.returncode == 1
    assert "The project is committed locally" in result.stderr
    assert sandbox.git("rev-list", "--count", "HEAD") == "1"


def test_conda_environment_is_created_with_the_project_name(sandbox: Sandbox) -> None:
    result = sandbox.init()
    assert result.returncode == 0, result.stderr
    assert ["create", "-n", "demo", "python=3.12", "-y"] in sandbox.conda_calls()
    assert "Conda environment: demo (created" in result.stdout


def test_existing_conda_environment_is_kept(sandbox: Sandbox) -> None:
    sandbox.env["FAKE_CONDA_ENVS"] = "demo"
    result = sandbox.init()
    assert result.returncode == 0, result.stderr
    assert [call for call in sandbox.conda_calls() if call[0] == "create"] == []
    assert "already existed, kept" in result.stdout


def test_no_conda_needs_no_conda(sandbox: Sandbox) -> None:
    sandbox.remove_conda()
    result = sandbox.init("--no-conda")
    assert result.returncode == 0, result.stderr
    assert "Conda environment: skipped" in result.stdout


def test_failed_conda_create_says_how_to_finish(sandbox: Sandbox) -> None:
    sandbox.env["FAKE_CONDA_STATE"] = "fail"
    result = sandbox.init()
    assert result.returncode == 1
    assert "`conda create -n demo python=3.12`" in result.stderr
    assert sandbox.remote_head() == sandbox.git("rev-parse", "HEAD")


def nothing(_: Sandbox) -> None:
    """Leave the sandbox as it is."""


def holds_a_file(sandbox: Sandbox) -> None:
    """Put a file in the project folder."""
    (sandbox.folder / "notes.txt").write_text("x", encoding="utf-8")


def has_commits(sandbox: Sandbox) -> None:
    """Make the folder a repository with one commit (of a file in .claude, which is allowed)."""
    sandbox.git("init")
    (sandbox.folder / ".claude").mkdir()
    (sandbox.folder / ".claude" / "notes.md").write_text("x", encoding="utf-8")
    sandbox.git("add", "-A")
    sandbox.git("commit", "-m", "first")


def has_origin(sandbox: Sandbox) -> None:
    """Make the folder a repository with an `origin` remote."""
    sandbox.git("init")
    sandbox.git("remote", "add", "origin", str(sandbox.remote))


def gh_state(state: str) -> Callable[[Sandbox], None]:
    """Return a setup that makes the fake gh answer as logged out, or with the name taken."""

    def setup(sandbox: Sandbox) -> None:
        sandbox.env["FAKE_GH_STATE"] = state

    return setup


REFUSALS = [
    (holds_a_file, [], "already holds notes.txt"),
    (has_commits, [], "already has commits"),
    (nothing, ["--name", "bad name"], "may hold only letters"),
    (nothing, ["--with", "cobol"], "invalid choice: 'cobol'"),
    (Sandbox.forget_identity, [], "git has no user.name"),
    (Sandbox.remove_gh, [], "`gh` is not installed"),
    (gh_state("logged-out"), [], "gh auth login"),
    (gh_state("taken"), [], "github.com/tester/demo already exists"),
    (has_origin, ["--remote-url", "https://example.com/x.git"], "Drop --remote-url"),
    (Sandbox.remove_conda, [], "conda is not installed"),
]
REFUSAL_IDS = [
    "folder-not-empty",
    "has-commits",
    "bad-name",
    "unknown-module",
    "no-git-identity",
    "no-gh",
    "gh-logged-out",
    "name-taken",
    "origin-and-remote-url",
    "no-conda",
]


@pytest.mark.parametrize(("setup", "options", "message"), REFUSALS, ids=REFUSAL_IDS)
def test_refusal_changes_nothing(
    sandbox: Sandbox, setup: Callable[[Sandbox], None], options: list[str], message: str
) -> None:
    setup(sandbox)
    before = sandbox.snapshot()
    result = sandbox.init(*options)
    assert result.returncode == 1
    assert message in result.stderr
    assert sandbox.snapshot() == before
    assert [call for call in sandbox.gh_calls() if call[:2] == ["repo", "create"]] == []
