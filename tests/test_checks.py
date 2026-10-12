"""The checks a new project gets: scripts/check.py, the Claude Code edit hook, the pre-commit hook.

These run the real ruff and mypy from this repository's environment against a built project.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import build_instance as bi
import pytest
from helpers import Sandbox, build, git_path, run

BAD = "import os\n"  # an unused import, and no module docstring
GOOD = '"""A module."""\n'


@pytest.fixture
def project(sandbox: Sandbox) -> Sandbox:
    """A Python project set up by init_project.py, kept local, with no conda environment."""
    result = sandbox.init("--with", "python", "--no-github", "--no-conda")
    assert result.returncode == 0, result.stderr
    return sandbox


def check(folder: Path, *args: str, stdin: str | None = None) -> tuple[int, str]:
    """Run the project's scripts/check.py with this environment's Python (it has ruff and mypy)."""
    result = run([sys.executable, str(folder / "scripts" / "check.py"), *args], folder, stdin=stdin)
    return result.returncode, result.stdout + result.stderr


def edited(path: Path) -> str:
    """Return the JSON a Claude Code PostToolUse hook gets after an edit to this file."""
    return json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(path)}})


def load_check() -> ModuleType:
    """Import the check.py that new projects get."""
    spec = importlib.util.spec_from_file_location("check", bi.assets_dir() / "scripts/check.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_init_turns_on_the_pre_commit_hook(project: Sandbox) -> None:
    assert project.git("config", "core.hooksPath") == ".githooks"
    for script in [".githooks/pre-commit", "scripts/run-check.sh"]:
        assert project.git("ls-files", "-s", script).startswith("100755"), script


def test_shell_scripts_have_lf_endings(tmp_path: Path) -> None:
    build(tmp_path / "my-app")
    for script in [".githooks/pre-commit", "scripts/run-check.sh"]:
        assert b"\r" not in (tmp_path / "my-app" / script).read_bytes(), script
    assert 'name="my-app"' in (tmp_path / "my-app" / "scripts/run-check.sh").read_text("utf-8")


def test_checks_pass_on_a_new_project(project: Sandbox) -> None:
    code, output = check(project.folder)
    assert code == 0, output


def test_checks_fail_on_a_lint_error(project: Sandbox) -> None:
    (project.folder / "src" / "bad.py").write_text(BAD, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "bad.py" in output


def test_edited_file_is_fixed_and_the_rest_reported(project: Sandbox) -> None:
    path = project.folder / "src" / "ugly.py"
    path.write_text("import os\nx=1\n", encoding="utf-8")
    code, output = check(project.folder, "--edited", stdin=edited(path))
    # Claude Code shows the reason of a `block` decision to Claude.
    assert code == 0
    decision = json.loads(output)
    assert decision["decision"] == "block"
    assert "Missing docstring in public module" in decision["reason"]
    assert path.read_text(encoding="utf-8") == "x = 1\n"


def test_clean_edit_and_other_files_pass(project: Sandbox) -> None:
    clean = project.folder / "src" / "clean.py"
    clean.write_text(GOOD, encoding="utf-8")
    for path in [clean, project.folder / "README.md", project.folder.parent / "elsewhere.py"]:
        assert check(project.folder, "--edited", stdin=edited(path)) == (0, ""), path


def test_missing_tool_is_named() -> None:
    reason = load_check().why_not_runnable([sys.executable, "-m", "no_such_tool"])
    assert "`no-such-tool` not installed" in reason


def write_tested_module(folder: Path, expected: int) -> None:
    """Write src/calc.py and a test of it that passes when `expected` is 3."""
    (folder / "src" / "__init__.py").write_text('"""Source."""\n', encoding="utf-8")
    calc = (
        '"""Arithmetic."""\n\n\ndef add(a: int, b: int) -> int:\n    """Add."""\n    return a + b\n'
    )
    (folder / "src" / "calc.py").write_text(calc, encoding="utf-8")
    test = (
        "from src.calc import add\n\n\n"
        f"def test_add() -> None:\n    assert add(1, 2) == {expected}\n"
    )
    (folder / "tests" / "unit" / "test_calc.py").write_text(test, encoding="utf-8")


def test_checks_run_the_tests_once_there_are_some(project: Sandbox) -> None:
    write_tested_module(project.folder, 3)
    code, output = check(project.folder)
    assert code == 0, output
    write_tested_module(project.folder, 4)
    code, output = check(project.folder)
    assert code == 2
    assert "`pytest -q --cov=src --cov-branch --cov-fail-under=80` failed" in output
    assert "test_add" in output


def test_pre_commit_hook_refuses_a_failing_commit(project: Sandbox) -> None:
    # The hook finds Python through the active conda environment, as in a VS Code terminal.
    env = {**project.env, "CONDA_DEFAULT_ENV": "demo", "CONDA_PREFIX": sys.prefix}
    (project.folder / "src" / "bad.py").write_text(BAD, encoding="utf-8")
    project.git("add", "-A")
    refused = run([git_path(), "commit", "-m", "bad"], project.folder, env)
    assert refused.returncode != 0
    assert "ruff check" in refused.stderr
    (project.folder / "src" / "bad.py").write_text(GOOD, encoding="utf-8")
    project.git("add", "-A")
    accepted = run([git_path(), "commit", "-m", "good"], project.folder, env)
    assert accepted.returncode == 0, accepted.stderr
