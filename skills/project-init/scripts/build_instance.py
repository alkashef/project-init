"""Build a project instance from the golden CLAUDE.md master (`assets/CLAUDE_GOLDEN.md`).

Writes CLAUDE.md (the always-loaded sections), `.claude/rules/*.md` (the path-scoped sections),
README.md, the docs, the starting folders, and every other file the project receives, all from
the skill's `assets/` folder. Does NOT edit the master. Never overwrites an existing file unless
--force is given. The project name is the name of the TARGET folder unless --name is given.

Usage:
    python build_instance.py TARGET --with python http-apis validation --purpose "Does X"
    python build_instance.py TARGET --with python --dry-run
"""

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Section:
    """One `##` section of the golden file: its ID, title, and body lines."""

    section_id: str
    title: str
    body: list[str]


def assets_dir() -> Path:
    """Return the skill's assets/ folder (this script is in the skill's scripts/ folder)."""
    return Path(__file__).resolve().parent.parent / "assets"


def always_loaded() -> list[str]:
    """Return the IDs of the sections that go into CLAUDE.md."""
    return ["C1", "A1", "A2", "A3", "A6", "A7", "A9", "A10", "A11", "A15", "A16", "A17"]


def rule_files() -> dict[str, tuple[list[str], list[str]]]:
    """Map each rules file to its path globs and the section IDs it holds."""
    return {
        "code-quality": (
            ["src/**", "tests/**", "scripts/**", "main.py"],
            ["A5", "A8", "A12", "A13", "A18", "A19"],
        ),
        "llm": (["prompts/**", "src/**/llm*"], ["A14"]),
        "python": (["**/*.py"], ["B1"]),
        "javascript": (["**/*.js", "**/*.mjs", "**/*.ts"], ["B2"]),
        "html-css": (["**/*.html", "**/*.css"], ["B3"]),
        "ui-design": (["**/*.html", "**/*.css", "**/*.js"], ["B3a"]),
        "http-apis": (["src/api/**"], ["B4"]),
        "data": (["data/**", "src/store/**"], ["B5"]),
        "cli": (["main.py"], ["B6"]),
        "static-site": (["content/**", "site/**", "scripts/build-site.js"], ["B7"]),
        "mcp": (["src/mcp/**"], ["B8"]),
        "docker": (["Dockerfile", "compose.yaml", ".dockerignore"], ["B9"]),
    }


def optional_flags() -> dict[str, str]:
    """Map each --with flag to the section it turns on."""
    return {
        "logging": "A13",
        "llm": "A14",
        "long-running": "A18",
        "validation": "A19",
        "python": "B1",
        "javascript": "B2",
        "html-css": "B3",
        "ui-design": "B3a",
        "http-apis": "B4",
        "data": "B5",
        "cli": "B6",
        "static-site": "B7",
        "mcp": "B8",
        "docker": "B9",
    }


def template_files() -> dict[str, list[str]]:
    """Map a flag ('always' or a --with flag) to the asset files it copies as they are."""
    return {
        "always": [
            ".claude/settings.json",
            ".gitignore",
            ".vscode/extensions.json",
            "config/.env.example",
            "docs/workflow.md",
            "scripts/cleanup.py",
        ],
        "python": ["ruff.toml", "mypy.ini", "pytest.ini", "requirements.txt"],
        "javascript": ["package.json", "tsconfig.json", "eslint.config.js"],
        "docker": [".dockerignore"],
    }


def rendered_templates() -> list[str]:
    """Return the asset files that get their {{placeholders}} filled (README, docs, VS Code)."""
    return [
        "README.md",
        "docs/inbox.md",
        "docs/spec.md",
        "docs/design.md",
        "docs/plan.md",
        ".vscode/settings.json",
    ]


def always_folders() -> dict[str, str]:
    """Map each folder every project starts with to what it holds."""
    return {
        "src/": "All source code.",
        "tests/": "`unit/` and `e2e/` tests.",
        "docs/": "Workflow, inbox, spec, design, and plan.",
        "config/": "`.env` (never committed) and `.env.example`.",
        "scripts/": "`cleanup.py` and setup scripts.",
        ".claude/": "Claude Code settings.",
        ".vscode/": "Shared editor settings.",
    }


def flag_folders() -> dict[str, dict[str, str]]:
    """Map a --with flag to the extra folders it adds, with what each holds."""
    return {
        "data": {"data/": "Input and runtime data."},
        "llm": {
            "models/": "Downloaded model weights (never committed).",
            "prompts/": "LLM prompt files.",
        },
        "static-site": {
            "content/": "Markdown source. Authors edit only this.",
            "site/": "Generated output. Never edited by hand.",
        },
    }


def folder_rows(flags: list[str]) -> dict[str, str]:
    """Return every folder the project starts with, mapped to what it holds."""
    rows = dict(always_folders())
    for flag in flags:
        rows.update(flag_folders().get(flag, {}))
    return rows


def folder_table(flags: list[str]) -> str:
    """Render the starting folders as a Markdown table."""
    lines = ["| Path | Holds |", "| --- | --- |"]
    lines += [f"| `{path}` | {holds} |" for path, holds in folder_rows(flags).items()]
    return "\n".join(lines)


def empty_dirs(flags: list[str]) -> list[str]:
    """Return the folders that start empty (each gets a `.gitkeep` so git keeps it)."""
    folders = ["src", "tests/unit", "tests/e2e"]
    if "ui-design" in flags or "html-css" in flags:
        folders.append("tests/e2e/ui")
    folders += [path.rstrip("/") for flag in flags for path in flag_folders().get(flag, {})]
    return folders


def python_fills(name: str) -> dict[str, str]:
    """Return the Project and README values that follow from using Python."""
    setup = (
        f"```bash\nconda create -n {name} python=3.12\nconda activate {name}\n"
        "pip install -r requirements.txt\n```\n\n"
        "Copy `config/.env.example` to `config/.env` and fill in the values.\n\n"
        "External dependencies (LLM server, models, API keys): none yet. Explain here how to set "
        "up and check each one before the first run."
    )
    return {
        "{{STACK}}": f"Python 3.12, conda environment `{name}`, pytest, ruff, mypy",
        "{{TEST_COMMAND}}": "python -m pytest --cov=src --cov-branch --cov-fail-under=80",
        "{{RUN_COMMAND}}": "python main.py",
        "{{SETUP}}": setup,
    }


def default_fills(name: str, flags: list[str]) -> dict[str, str]:
    """Return a value for every placeholder: known ones from the name and flags, else TBD."""
    fills = {
        "{{PROJECT_NAME}}": name,
        "{{PURPOSE}}": "TBD",
        "{{STACK}}": "TBD",
        "{{TEST_COMMAND}}": "TBD",
        "{{RUN_COMMAND}}": "TBD",
        "{{SETUP}}": "TBD",
        "{{PROJECT_RULES}}": "none yet",
        "{{DIRECTORY_STRUCTURE}}": folder_table(flags),
    }
    if "python" in flags:
        fills.update(python_fills(name))
    return fills


def split_by_heading(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Group lines under each `## ` heading. Lines before the first heading are dropped."""
    groups: list[tuple[str, list[str]]] = []
    for line in lines:
        if line.startswith("## "):
            groups.append((line[3:].strip(), []))
        elif groups:
            groups[-1][1].append(line)
    return groups


def trim(lines: list[str]) -> list[str]:
    """Remove blank lines from both ends of a list of lines."""
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def to_section(title: str, body: list[str]) -> Section:
    """Build a Section: take the ID from the comment under the heading, then drop the comments."""
    match = re.search(r"<!--\s*([ABC]\d+a?)\.", "\n".join(body))
    section_id = match.group(1) if match else title
    kept = trim([line for line in body if not line.startswith("<!--")])
    return Section(section_id, title, kept)


def read_sections(golden: Path) -> list[Section]:
    """Split the golden file into sections, in file order.

    Args:
        golden: Path to the golden CLAUDE.md.

    Returns:
        One Section per `##` heading, without HTML comments.
    """
    lines = golden.read_text(encoding="utf-8").splitlines()
    return [to_section(title, body) for title, body in split_by_heading(lines)]


def select_sections(sections: list[Section], flags: list[str]) -> list[Section]:
    """Keep the sections that always apply plus the ones the flags turn on."""
    optional_ids = set(optional_flags().values())
    chosen = {optional_flags()[flag] for flag in flags}
    return [s for s in sections if s.section_id not in optional_ids or s.section_id in chosen]


def fill(text: str, fills: dict[str, str]) -> str:
    """Replace every {{placeholder}} that has a value."""
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def render_sections(sections: list[Section]) -> str:
    """Render sections as Markdown with `##` headings."""
    parts: list[str] = []
    for section in sections:
        parts.extend([f"## {section.title}", "", *section.body, ""])
    return "\n".join(parts).rstrip() + "\n"


def render_rule_file(globs: list[str], sections: list[Section]) -> str:
    """Render a path-scoped rules file with its `paths:` frontmatter."""
    paths = "\n".join(f'  - "{glob}"' for glob in globs)
    return f"---\npaths:\n{paths}\n---\n\n" + render_sections(sections)


def plan_outputs(
    assets: Path, target: Path, sections: list[Section], fills: dict[str, str]
) -> dict[Path, str]:
    """Return every generated file (path to text): CLAUDE.md, rules files, README, and docs."""
    by_id = {s.section_id: s for s in sections}
    core = [by_id[i] for i in always_loaded() if i in by_id]
    outputs = {target / "CLAUDE.md": fill("# CLAUDE.md\n\n" + render_sections(core), fills)}
    for name, (globs, ids) in rule_files().items():
        chosen = [by_id[i] for i in ids if i in by_id]
        if chosen:
            outputs[target / ".claude" / "rules" / f"{name}.md"] = render_rule_file(globs, chosen)
    for relative in rendered_templates():
        text = (assets / relative).read_text(encoding="utf-8")
        outputs[target / relative] = fill(text, fills)
    return outputs


def plan_copies(assets: Path, target: Path, flags: list[str]) -> dict[Path, Path]:
    """Return every file copied as it is (destination to source) from assets/."""
    copies: dict[Path, Path] = {}
    for key in ["always", *flags]:
        for relative in template_files().get(key, []):
            copies[target / relative] = assets / relative
    return copies


def write_text(path: Path, text: str, force: bool, dry_run: bool) -> str:
    """Write one file unless it exists (or this is a dry run). Return a status word."""
    if path.exists() and not force:
        return "skipped (exists)"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return "would write" if dry_run else "written"


def copy_file(source: Path, path: Path, force: bool, dry_run: bool) -> str:
    """Copy one file unless it exists (or this is a dry run). Return a status word."""
    if path.exists() and not force:
        return "skipped (exists)"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, path)
    return "would copy" if dry_run else "copied"


def make_empty_dir(path: Path, dry_run: bool) -> str:
    """Create a folder that holds only a `.gitkeep`, unless it already exists."""
    if path.exists():
        return "skipped (exists)"
    if not dry_run:
        path.mkdir(parents=True)
        (path / ".gitkeep").write_text("", encoding="utf-8")
    return "would create" if dry_run else "created"


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(
        description="Build a project instance from the golden CLAUDE.md."
    )
    parser.add_argument("target", type=Path, help="the project folder to write into")
    parser.add_argument(
        "--with", dest="flags", nargs="*", default=[], choices=sorted(optional_flags())
    )
    parser.add_argument("--name", default="", help="project name (default: the TARGET folder name)")
    parser.add_argument("--purpose", default="", help="fills {{PURPOSE}}")
    parser.add_argument("--stack", default="", help="fills {{STACK}}")
    parser.add_argument("--test-command", default="", help="fills {{TEST_COMMAND}}")
    parser.add_argument("--run-command", default="", help="fills {{RUN_COMMAND}}")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="list what would be written")
    return parser.parse_args()


def fills_from(args: argparse.Namespace) -> dict[str, str]:
    """Return the placeholder values: defaults, overridden by what the command line gave."""
    fills = default_fills(args.name or args.target.resolve().name, args.flags)
    given = {
        "{{PURPOSE}}": args.purpose,
        "{{STACK}}": args.stack,
        "{{TEST_COMMAND}}": args.test_command,
        "{{RUN_COMMAND}}": args.run_command,
    }
    fills.update({key: value for key, value in given.items() if value})
    return fills


def main() -> int:
    """Build the instance and print what happened to each file."""
    args = parse_args()
    assets = assets_dir()
    sections = select_sections(read_sections(assets / "CLAUDE_GOLDEN.md"), args.flags)
    outputs = plan_outputs(assets, args.target, sections, fills_from(args))
    copies = plan_copies(assets, args.target, args.flags)
    for path, text in outputs.items():
        print(f"{write_text(path, text, args.force, args.dry_run):18} {path}")
    for path, source in copies.items():
        print(f"{copy_file(source, path, args.force, args.dry_run):18} {path}")
    for folder in empty_dirs(args.flags):
        print(f"{make_empty_dir(args.target / folder, args.dry_run):18} {args.target / folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
