"""build_instance.py: what it writes, what it leaves alone, and the CLAUDE.md line budget."""

import json
from pathlib import Path

import build_instance as bi
import pytest
from helpers import build, text_files

ALL_MODULES = sorted(bi.optional_flags())
PYTHON_FILES = [
    "CLAUDE.md",
    ".claude/rules/code-quality.md",
    ".claude/rules/python.md",
    ".claude/settings.json",
    "README.md",
    "docs/spec.md",
    "ruff.toml",
    "mypy.ini",
    "pytest.ini",
    "requirements.txt",
    "scripts/cleanup.py",
    "src/.gitkeep",
    "tests/unit/.gitkeep",
]


def test_python_build_writes_the_python_files(tmp_path: Path) -> None:
    assert build(tmp_path, "--with", "python").returncode == 0
    assert [f for f in PYTHON_FILES if not (tmp_path / f).is_file()] == []


def test_python_build_leaves_out_other_modules(tmp_path: Path) -> None:
    build(tmp_path, "--with", "python")
    others = ["package.json", ".dockerignore", ".claude/rules/javascript.md", "data", "models"]
    assert [f for f in others if (tmp_path / f).exists()] == []


def test_full_build_writes_every_rules_file(full_build: Path) -> None:
    rules = {p.stem for p in (full_build / ".claude" / "rules").glob("*.md")}
    assert rules == set(bi.rule_files())


def test_rules_files_start_with_their_paths(full_build: Path) -> None:
    for path in (full_build / ".claude" / "rules").glob("*.md"):
        assert path.read_text(encoding="utf-8").startswith('---\npaths:\n  - "'), path.name


@pytest.mark.parametrize("modules", [[], ["python"], ALL_MODULES], ids=["none", "python", "all"])
def test_no_placeholder_is_left(tmp_path: Path, modules: list[str]) -> None:
    build(tmp_path, "--with", *modules)
    assert [name for name, text in text_files(tmp_path).items() if "{{" in text] == []


def test_name_and_purpose_reach_the_readme(tmp_path: Path) -> None:
    build(tmp_path / "my-app", "--with", "python", "--purpose", "Counts sheep")
    readme = (tmp_path / "my-app" / "README.md").read_text(encoding="utf-8")
    assert "my-app" in readme
    assert "Counts sheep" in readme
    assert "conda create -n my-app" in readme


def test_vscode_terminal_is_cmd_with_the_conda_environment(tmp_path: Path) -> None:
    build(tmp_path / "my-app")
    settings = json.loads((tmp_path / "my-app" / ".vscode" / "settings.json").read_text("utf-8"))
    default = settings["terminal.integrated.defaultProfile.windows"]
    profile = settings["terminal.integrated.profiles.windows"][default]
    assert profile["path"].endswith("cmd.exe")
    assert profile["args"] == ["/K", "conda activate my-app"]


def recommended(folder: Path) -> list[str]:
    """Return the extension IDs a built project's `.vscode/extensions.json` recommends."""
    text = (folder / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    return list(json.loads(text)["recommendations"])


def test_python_build_recommends_only_python_extensions(tmp_path: Path) -> None:
    build(tmp_path, "--with", "python")
    extensions = recommended(tmp_path)
    assert "charliermarsh.ruff" in extensions
    assert "usernamehw.errorlens" in extensions
    web = ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "stylelint.vscode-stylelint"]
    assert [e for e in web if e in extensions] == []


def test_web_build_recommends_web_extensions_once(tmp_path: Path) -> None:
    build(tmp_path, "--with", "javascript", "html-css", "ui-design")
    extensions = recommended(tmp_path)
    assert "dbaeumer.vscode-eslint" in extensions
    assert "stylelint.vscode-stylelint" in extensions
    assert "charliermarsh.ruff" not in extensions
    assert len(extensions) == len(set(extensions))


def test_every_extension_key_is_a_module() -> None:
    assert set(bi.extension_ids()) - {"always", *bi.optional_flags()} == set()


def test_claude_md_fits_the_line_budget(full_build: Path) -> None:
    # CLAUDE.md loads in every session, and Anthropic advises keeping it under 200 lines. Every
    # line counts, blank ones too, because that is what the advice measures. Only CLAUDE.md is
    # capped: the rules files load only when Claude touches a matching file.
    lines = len((full_build / "CLAUDE.md").read_text(encoding="utf-8").splitlines())
    assert lines < 200, f"CLAUDE.md has {lines} lines; the budget is under 200"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    result = build(tmp_path, "--with", *ALL_MODULES, "--dry-run")
    assert "would write" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_second_run_keeps_existing_files(tmp_path: Path) -> None:
    build(tmp_path, "--with", "python")
    (tmp_path / "README.md").write_text("mine", encoding="utf-8")
    result = build(tmp_path, "--with", "python")
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "mine"
    assert all(line.startswith("skipped") for line in result.stdout.splitlines())


def test_force_overwrites_existing_files(tmp_path: Path) -> None:
    build(tmp_path, "--with", "python")
    (tmp_path / "README.md").write_text("mine", encoding="utf-8")
    build(tmp_path, "--with", "python", "--force")
    assert (tmp_path / "README.md").read_text(encoding="utf-8") != "mine"


def test_unknown_module_is_refused(tmp_path: Path) -> None:
    result = build(tmp_path, "--with", "cobol")
    assert result.returncode == 2
    assert "invalid choice: 'cobol'" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_to_section_takes_the_id_from_the_comment() -> None:
    section = bi.to_section("Python", ["<!-- B1. Applies when: Python. -->", "", "Use ruff.", ""])
    assert section == bi.Section("B1", "Python", ["Use ruff."])


def test_select_sections_drops_optional_sections_not_chosen() -> None:
    sections = [bi.Section(i, i, []) for i in ["A1", "B1", "B2"]]
    assert [s.section_id for s in bi.select_sections(sections, ["python"])] == ["A1", "B1"]


def test_build_writes_the_project_skills(tmp_path: Path) -> None:
    build(tmp_path)
    for skill in ("write-spec", "write-design"):
        assert (tmp_path / ".claude" / "skills" / skill / "SKILL.md").is_file()
    assert not (tmp_path / ".claude" / "skills" / "write-spec" / "assets" / "icon.svg").exists()


def test_build_writes_a_draft_spec_and_no_inbox(tmp_path: Path) -> None:
    build(tmp_path / "my-app", "--purpose", "Counts sheep")
    docs = tmp_path / "my-app" / "docs"
    spec = (docs / "spec.md").read_text(encoding="utf-8")
    assert "# Spec — my-app\n\nStatus: Draft" in spec
    assert "Counts sheep" in spec
    assert not (docs / "inbox.md").exists()
