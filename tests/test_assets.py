"""The skill's assets agree with what build_instance.py expects to find in them."""

import json
import re
from pathlib import Path

import build_instance as bi


def golden_ids() -> set[str]:
    """Return the IDs of every section in the golden master."""
    return {s.section_id for s in bi.read_sections(bi.assets_dir() / "CLAUDE_GOLDEN.md")}


def placed_ids() -> set[str]:
    """Return the IDs of every section the builder puts in CLAUDE.md or a rules file."""
    in_rules = {i for _, ids in bi.rule_files().values() for i in ids}
    return set(bi.always_loaded()) | in_rules


def test_every_listed_asset_exists() -> None:
    listed = [f for files in bi.template_files().values() for f in files]
    listed += bi.rendered_templates()
    missing = [f for f in listed if not (bi.assets_dir() / f).is_file()]
    assert missing == []


def test_every_named_section_is_in_the_golden_master() -> None:
    named = placed_ids() | set(bi.optional_flags().values())
    assert named - golden_ids() == set()


def test_every_golden_section_goes_somewhere() -> None:
    assert golden_ids() - placed_ids() == set()


def test_every_bash_rule_has_a_powershell_twin() -> None:
    # On Windows, Claude Code may run commands with its PowerShell tool, which Bash(...) rules
    # do not cover. A headless session ran `git reset --hard` until each rule got a twin.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    for kind, rules in settings["permissions"].items():
        bash = {r[len("Bash(") :] for r in rules if r.startswith("Bash(")}
        powershell = {r[len("PowerShell(") :] for r in rules if r.startswith("PowerShell(")}
        assert bash - powershell == set(), kind


def test_every_edit_is_checked_by_a_hook() -> None:
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    [entry] = settings["hooks"]["PostToolUse"]
    assert set(entry["matcher"].split("|")) >= {"Edit", "Write"}
    assert entry["hooks"][0]["command"].endswith('/scripts/run-check.sh" --edited')


def test_check_configs_and_hooks_ask_before_an_edit() -> None:
    # The hooks enforce these files; loosening one is the easy way to make a check pass.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    protected = [
        "ruff.toml",
        "mypy.ini",
        "pytest.ini",
        "package.json",
        "tsconfig.json",
        "eslint.config.js",
        ".prettierrc.json",
        ".stylelintrc.json",
        ".githooks/**",
        "scripts/check.py",
        "scripts/run-check.sh",
    ]
    ask = settings["permissions"]["ask"]
    assert [f for f in protected if f"Edit(/{f})" not in ask] == []


def test_every_section_id_is_unique() -> None:
    sections = bi.read_sections(bi.assets_dir() / "CLAUDE_GOLDEN.md")
    assert len(sections) == len(golden_ids())


def project_skills() -> list[Path]:
    """Return the folder of each skill that new projects receive."""
    return sorted(p for p in (bi.assets_dir() / ".claude" / "skills").iterdir() if p.is_dir())


def test_project_skills_are_the_two_slash_commands() -> None:
    assert [p.name for p in project_skills()] == ["write-design", "write-spec"]


def test_every_project_skill_names_itself_after_its_folder() -> None:
    for folder in project_skills():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith(f"---\nname: {folder.name}\ndescription:"), folder.name


def test_every_project_skill_link_resolves() -> None:
    for folder in project_skills():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)#:]+)\)", text)
        assert links, folder.name
        assert [link for link in links if not (folder / link).is_file()] == []


def test_the_workflow_and_the_skills_hand_off_to_each_other() -> None:
    docs = bi.assets_dir() / "docs"
    skills = bi.assets_dir() / ".claude" / "skills"
    workflow = (docs / "workflow.md").read_text(encoding="utf-8")
    assert "/write-spec" in workflow
    assert "/write-design" in workflow
    assert "/write-design" in (skills / "write-spec" / "SKILL.md").read_text(encoding="utf-8")
    assert "/write-spec" in (skills / "write-design" / "SKILL.md").read_text(encoding="utf-8")


def test_no_asset_mentions_the_inbox() -> None:
    # The inbox was replaced by /write-spec.
    sources = [bi.assets_dir() / "CLAUDE_GOLDEN.md", *(bi.assets_dir() / "docs").glob("*.md")]
    assert [p.name for p in sources if "inbox" in p.read_text(encoding="utf-8")] == []
