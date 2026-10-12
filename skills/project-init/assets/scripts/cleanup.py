"""Delete caches and generated artifacts from the repository, by name, wherever they sit.

Does NOT delete source, tests, docs, config, input data, or dependencies (virtual
environments, node_modules).

Usage:
    python scripts/cleanup.py             # delete
    python scripts/cleanup.py --dry-run   # list only

Edit `default_patterns()` and `skipped_dirs()` for the project.
"""

import argparse
import fnmatch
import os
import shutil
from pathlib import Path


def default_patterns() -> list[str]:
    """Return the name patterns of the caches and artifacts to delete."""
    return [
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "htmlcov",
        "*.egg-info",
        "logs",
    ]


def skipped_dirs() -> set[str]:
    """Return the folders that are never entered."""
    return {".git", ".venv", "venv", "env", "node_modules", "data"}


def matches(name: str, patterns: list[str]) -> bool:
    """Return True if the name matches any pattern."""
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def find_targets(root: Path, patterns: list[str], skip: set[str]) -> list[Path]:
    """Return every file or folder under root whose name matches a pattern.

    Args:
        root: The repository root.
        patterns: Name patterns to delete.
        skip: Folder names that are never entered.

    Returns:
        The matching paths. Matched folders are not searched further.
    """
    found: list[Path] = []
    for folder, dirs, files in os.walk(root):
        matched = [d for d in dirs if matches(d, patterns)]
        found += [Path(folder) / d for d in matched]
        found += [Path(folder) / f for f in files if matches(f, patterns)]
        dirs[:] = [d for d in dirs if d not in skip and d not in matched]
    return found


def delete(path: Path) -> None:
    """Delete a file, a symlink, or a folder tree."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="Delete caches and generated artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="list what would be deleted")
    return parser.parse_args()


def main() -> None:
    """Find the caches and delete them, or only list them with --dry-run."""
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    targets = find_targets(root, default_patterns(), skipped_dirs())
    for path in targets:
        print(path.relative_to(root))
        if not args.dry_run:
            delete(path)
    verb = "found" if args.dry_run else "deleted"
    print(f"{len(targets)} item(s) {verb}.")


if __name__ == "__main__":
    main()
