"""
find_unreferenced.py

Lists candidate dead code in a git repository: Python functions, classes and module-level
names, JavaScript functions and exports, CSS classes and custom properties, and keys of
.env.example files that nothing else in the repository names.
Does NOT delete anything, and does NOT prove that a name is dead: every line it prints is a
candidate to check by hand (dynamic calls, decorators, string-built names).

Run: python find_unreferenced.py [ROOT] [--all]
  ROOT   the repository folder (default: the current folder)
  --all  also list decorated Python functions (route handlers, fixtures, CLI commands)
"""

import ast
import io
import re
import subprocess
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_CODE_SUFFIXES: tuple[str, ...] = (".py", ".js", ".mjs", ".ts", ".html", ".css", ".ps1", ".sh", ".toml", ".cfg", ".ini", ".json", ".yml", ".yaml")
_DOC_SUFFIXES: tuple[str, ...] = (".md", ".rst", ".txt")
_TEST_PARTS: tuple[str, ...] = ("tests", "test", "__tests__")
_JS_DEF = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s*\*?\s*(\w+)|(?:const|let|var|class)\s+(\w+))", re.M)
_CSS_CLASS = re.compile(r"\.(-?[A-Za-z_][\w-]*)")
_CSS_PROP = re.compile(r"(?<![\w-])(--[\w-]+)\s*:")
_ENV_KEY = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=", re.M)
_PLAIN_WORD = re.compile(r"\w+")
_HYPHEN_WORD = re.compile(r"-*\w[\w-]*")


@dataclass(frozen=True)
class Definition:
    """One defined name: its kind, its name, and where it is defined."""

    kind: str
    name: str
    path: Path
    line: int


@dataclass(frozen=True)
class Corpus:
    """The text of the repository, split into code, tests and docs."""

    code: dict[Path, str]
    tests: dict[Path, str]
    docs: dict[Path, str]


@dataclass(frozen=True)
class WordCounts:
    """How often each word appears in a group of files, counted two ways."""

    plain: Counter[str]
    hyphenated: Counter[str]


def _word_counts(texts: dict[Path, str]) -> WordCounts:
    """
    Count the words of a group of files once, so each look-up is fast.

    Args:
        texts: The files and their text.

    Returns:
        The counts of plain words (letters, digits, _) and of words that may hold hyphens.
    """
    plain: Counter[str] = Counter()
    hyphenated: Counter[str] = Counter()
    for path, text in texts.items():
        plain.update(_python_words(text) if path.suffix == ".py" else _PLAIN_WORD.findall(text))
        hyphenated.update(_HYPHEN_WORD.findall(text))
    return WordCounts(plain, hyphenated)


def _python_words(text: str) -> list[str]:
    """
    List the names a Python file uses, leaving out comments and docstrings.

    Args:
        text: The text of the file.

    Returns:
        Every name token, plus the words of string literals that hold no space (such as
        "name" in getattr(obj, "name")); on a tokenize error, every word of the text.
    """
    words: list[str] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.NAME:
                words.append(token.string)
            elif token.type == tokenize.STRING and not any(c.isspace() for c in token.string):
                words += _PLAIN_WORD.findall(token.string)
    except (tokenize.TokenError, SyntaxError):
        return _PLAIN_WORD.findall(text)
    return words


def _repo_files(root: Path) -> list[Path]:
    """
    List the files git tracks or would track (untracked but not ignored).

    Args:
        root: The repository folder.

    Returns:
        The files, as absolute paths.

    Raises:
        subprocess.CalledProcessError: If root is not a git repository.
    """
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / line for line in out.splitlines() if (root / line).is_file()]


def _is_test(path: Path, root: Path) -> bool:
    """
    Tell whether a file belongs to the tests.

    Args:
        path: The file.
        root: The repository folder.

    Returns:
        True for files under a tests folder or named test_*.
    """
    rel = path.relative_to(root)
    return any(part in _TEST_PARTS for part in rel.parts[:-1]) or rel.name.startswith("test_") or ".test." in rel.name


def _load_corpus(root: Path, files: list[Path]) -> Corpus:
    """
    Read every text file of the repository into the code, test or doc group.

    Args:
        root: The repository folder.
        files: The files to read.

    Returns:
        The corpus; files that are not UTF-8 text are left out.
    """
    corpus = Corpus({}, {}, {})
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in _CODE_SUFFIXES + _DOC_SUFFIXES and not path.name.startswith(".env"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        group = corpus.docs if suffix in _DOC_SUFFIXES else corpus.tests if _is_test(path, root) else corpus.code
        group[path] = text
    return corpus


def _python_definitions(path: Path, text: str, include_decorated: bool) -> list[Definition]:
    """
    List the functions, classes and module-level names a Python file defines.

    Args:
        path: The file.
        text: Its text.
        include_decorated: Whether to list decorated functions too.

    Returns:
        The definitions; dunder names are left out.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found: list[Definition] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.decorator_list and not include_decorated and not isinstance(node, ast.ClassDef):
                continue
            found.append(Definition("py-" + type(node).__name__.replace("Def", "").lower(), node.name, path, node.lineno))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            found += [Definition("py-name", t.id, path, node.lineno) for t in targets if isinstance(t, ast.Name)]
    return [d for d in found if not (d.name.startswith("__") and d.name.endswith("__"))]


def _regex_definitions(kind: str, pattern: re.Pattern[str], path: Path, text: str) -> list[Definition]:
    """
    List the names a regular expression finds in a file, once per name.

    Args:
        kind: The label of the definitions.
        pattern: The expression; the first non-empty group is the name.
        path: The file.
        text: Its text.

    Returns:
        The definitions, with the line of the first match of each name.
    """
    seen: dict[str, Definition] = {}
    for match in pattern.finditer(text):
        name = next(group for group in match.groups() if group)
        if name not in seen:
            seen[name] = Definition(kind, name, path, text.count("\n", 0, match.start()) + 1)
    return list(seen.values())


def _definitions(corpus: Corpus, include_decorated: bool) -> list[Definition]:
    """
    List the definitions of every code file (not the tests: tests are users, not suppliers).

    Args:
        corpus: The repository text.
        include_decorated: Whether to list decorated Python functions.

    Returns:
        The definitions.
    """
    found: list[Definition] = []
    for path, text in corpus.code.items():
        suffix = path.suffix.lower()
        if suffix == ".py":
            found += _python_definitions(path, text, include_decorated)
        elif suffix in (".js", ".mjs", ".ts"):
            found += _regex_definitions("js", _JS_DEF, path, text)
        elif suffix == ".css":
            found += _regex_definitions("css-class", _CSS_CLASS, path, re.sub(r"/\*.*?\*/", "", text, flags=re.S))
            found += _regex_definitions("css-prop", _CSS_PROP, path, text)
        elif path.name.startswith(".env") and path.name.endswith("example"):
            found += _regex_definitions("env-key", _ENV_KEY, path, text)
    return found


def _count(name: str, counts: WordCounts) -> int:
    """
    Count the whole-word uses of a name.

    Args:
        name: The name; a name with a hyphen (CSS) is looked up among hyphenated words.
        counts: The word counts of a group of files.

    Returns:
        The number of uses.
    """
    return counts.hyphenated[name] if "-" in name else counts.plain[name]


def _status(definition: Definition, code: WordCounts, tests: WordCounts) -> str | None:
    """
    Classify one definition by where its name is used.

    Args:
        definition: The definition.
        code: The word counts of the code files.
        tests: The word counts of the test files.

    Returns:
        "unused", "tests-only", or None when code other than the definition uses the name.
    """
    if _count(definition.name, code) > 1:
        return None
    return "tests-only" if _count(definition.name, tests) else "unused"


def main(argv: list[str]) -> int:
    """
    Print the candidates, one per line: status, kind, name, file:line, and doc mentions.

    Args:
        argv: The command-line arguments without the program name.

    Returns:
        The exit code: 0.
    """
    root = Path(next((a for a in argv if not a.startswith("--")), ".")).resolve()
    corpus = _load_corpus(root, _repo_files(root))
    code, tests, docs_counts = (_word_counts(group) for group in (corpus.code, corpus.tests, corpus.docs))
    rows: list[str] = []
    for definition in _definitions(corpus, "--all" in argv):
        status = _status(definition, code, tests)
        if status:
            docs = _count(definition.name, docs_counts)
            where = f"{definition.path.relative_to(root).as_posix()}:{definition.line}"
            rows.append(f"{status:<10} {definition.kind:<12} {definition.name:<40} {where}" + (f"  (docs: {docs})" if docs else ""))
    print("\n".join(sorted(rows)) or "No candidates.")
    print(f"\n{len(rows)} candidates. Check each one by hand before deleting it.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
