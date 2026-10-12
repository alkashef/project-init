"""scripts/milestones-runner.py, as a new project gets it: its parts, and whole runs.

The whole runs use a fake `claude` (tests/fake_claude.py) that finishes, blocks, or skips each
milestone, in a project set up by init_project.py, with the real git hooks.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from helpers import Sandbox, build, logged_calls, run, shim

FAKE_CLAUDE = Path(__file__).resolve().with_name("fake_claude.py")
PLAN = """# Plan — project-init

**Next milestone number: M3**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M1** First | Does one thing | sonnet | low | open |
| **M2** Second | Does another | haiku | medium | open |

## Milestones

### M1 — First

- **Refs:** R1.

### M2 — Second

- **Refs:** R2.
"""


def load_runner(project: Path) -> ModuleType:
    """Import the runner a built project got."""
    path = project / "scripts" / "milestones-runner.py"
    spec = importlib.util.spec_from_file_location("milestones_runner", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["milestones_runner"] = module  # dataclasses look their module up while defined
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def built(tmp_path: Path) -> Path:
    """A project built with the python module, named my-app."""
    build(tmp_path / "my-app", "--with", "python")
    return tmp_path / "my-app"


@pytest.fixture
def planned(sandbox: Sandbox) -> Sandbox:
    """A pushed project named after this repository's environment, with two planned milestones.

    The runner refuses to start outside the project's environment; the tests run in this
    repository's environment, `project-init`, so the project takes that name.
    """
    result = sandbox.init("--name", "project-init", "--with", "python", "--no-conda")
    assert result.returncode == 0, result.stderr
    shim(sandbox.fake_bin, "claude", FAKE_CLAUDE)
    root = sandbox.folder.parent
    sandbox.env.update(
        {
            "FAKE_CLAUDE_LOG": str(root / "claude.log"),
            # The pre-commit hook finds Python through the active environment.
            "CONDA_DEFAULT_ENV": "project-init",
            "CONDA_PREFIX": sys.prefix,
        }
    )
    (sandbox.folder / "docs" / "plan.md").write_text(PLAN, encoding="utf-8")
    sandbox.git("commit", "-am", "Plan M1 and M2")
    sandbox.git("push")
    return sandbox


def run_runner(sandbox: Sandbox) -> tuple[int, str]:
    """Run the project's milestone runner and return its exit code and output."""
    command = [sys.executable, "scripts/milestones-runner.py"]
    result = run(command, sandbox.folder, sandbox.env)
    return result.returncode, result.stdout + result.stderr


def plan_rows(runner: ModuleType, project: Path) -> list[object]:
    """Return the rows of the project's plan table, as the runner reads them."""
    lines = (project / "docs" / "plan.md").read_text(encoding="utf-8").splitlines()
    rows: list[object] = runner.parse_plan_rows(lines)
    return rows


def test_new_plan_has_the_table_the_runner_reads(built: Path) -> None:
    runner = load_runner(built)
    assert "## Milestones at a glance" in (built / "docs" / "plan.md").read_text("utf-8")
    assert plan_rows(runner, built) == []


def test_workflow_row_template_is_a_row_the_runner_reads(built: Path) -> None:
    runner = load_runner(built)
    workflow = (built / "docs" / "workflow.md").read_text(encoding="utf-8")
    [template] = [line for line in workflow.splitlines() if line.startswith("| **M<n>**")]
    filled = template.replace("<n>", "7").replace("<title>", "Login")
    filled = filled.replace("<model>", "sonnet").replace("<effort>", "high")
    assert runner.parse_row(filled) == runner.Row(7, "Login", "sonnet", "high", "open")


def test_new_gitignore_has_the_runner_entries(built: Path) -> None:
    runner = load_runner(built)
    lines = (built / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert runner.missing_ignore_entries(lines) == []


def test_runner_checks_the_project_environment(built: Path) -> None:
    runner = load_runner(built)
    assert runner.in_project_env("C:/miniconda3/envs/my-app")
    assert not runner.in_project_env("C:/miniconda3/envs/other")


def test_unusable_model_or_effort_is_named(built: Path) -> None:
    runner = load_runner(built)
    assert "Model 'gpt'" in runner.row_problem(runner.Row(1, "A", "gpt", "low", "open"))
    assert "Effort 'huge'" in runner.row_problem(runner.Row(1, "A", "opus", "huge", "open"))
    assert runner.row_problem(runner.Row(1, "A", "opus", "max", "open")) is None


def test_prompt_names_the_milestone_and_its_commit(built: Path) -> None:
    runner = load_runner(built)
    prompt = runner.build_prompt(runner.Row(3, "Login", "sonnet", "low", "open"))
    assert "milestone M3 (Login) from docs/plan.md" in prompt
    assert "`M3: Login`" in prompt
    assert "<n>" not in prompt


def test_gitignore_entries_start_on_a_new_line(built: Path, tmp_path: Path) -> None:
    runner = load_runner(built)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("node_modules/", encoding="utf-8")
    assert runner.add_ignore_entries(gitignore)
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert lines == ["node_modules/", ".claude/logs/", ".claude/blocked.md"]
    assert not runner.add_ignore_entries(gitignore)


def test_runner_finishes_every_open_milestone(planned: Sandbox) -> None:
    code, output = run_runner(planned)
    assert code == 0, output
    assert "Range M1 to M2 is done." in output
    assert planned.git("log", "-2", "--format=%s").splitlines() == ["M2: Second", "M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    calls = logged_calls(planned.folder.parent / "claude.log")
    models = [(call[call.index("--model") + 1], call[call.index("--effort") + 1]) for call in calls]
    assert models == [("sonnet", "low"), ("haiku", "medium")]
    timings = (planned.folder / ".claude" / "logs" / "timings.csv").read_text("utf-8")
    assert len(timings.splitlines()) == 3


def test_runner_stops_at_a_blocked_milestone(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    code, output = run_runner(planned)
    assert code == 1
    assert "M1 is blocked:" in output
    assert "which database?" in output
    assert len(logged_calls(planned.folder.parent / "claude.log")) == 1


def test_runner_stops_when_a_milestone_does_not_finish(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "idle"
    code, output = run_runner(planned)
    assert code == 1
    assert "M1 stopped: its row is still in the plan table" in output


def test_runner_refuses_a_dirty_tree(planned: Sandbox) -> None:
    (planned.folder / "notes.txt").write_text("x", encoding="utf-8")
    code, output = run_runner(planned)
    assert code == 1
    assert "git status is not clean" in output
    assert logged_calls(planned.folder.parent / "claude.log") == []
