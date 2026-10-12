---
name: deadcode
description: Use when the user asks to find or remove dead code, unused functions, classes, files, scripts, dependencies, settings, CSS or variables, a finished one-time feature (an import, a migration), or leftover legacy code, or asks to make the docs stop naming removed or obsolete things.
argument-hint: "[area or path to focus on]"
---

# Dead code removal

Dead code is anything that no live path reaches. Find candidates with a tool, prove each
one by hand, ask the user about every product decision, remove test-first, then make the
docs match. The project's instructions (CLAUDE.md, AGENTS.md) win over this skill.

## Steps

1. **Read the rules.** From the project instructions, note the test gates (tests, type
   checker, linters, doc checks), the cleanup script, the limits on destructive actions,
   which docs need approval to change, and the commit workflow. Run `git status`: start
   from a clean tree.
2. **Clean.** Run the project's cleanup script in its dry-run mode, read the list, then run
   it for real. Leave alone anything outside the repository and any user data; report it.
3. **Scan.** Run the candidate finder (the folder of this skill is given when it loads):
   `python <skill-folder>/find_unreferenced.py <repo> [--all]`. It lists unused and
   tests-only names. Then check by hand what it cannot see (table below).
4. **Prove each candidate.** Search the whole repository (code, tests, scripts, HTML,
   config, docs) for the name. A name is dead only if no live path uses it:
   - Used only by tests: dead. Delete the tests with it, unless they guard live behavior.
   - Used only by other dead code: dead. Repeat the scan after each removal until nothing
     new shows up.
   - Possibly called dynamically: decorators and routes, entry points, `getattr`, names
     in strings, plugin registries, event names, CSS classes built from strings
     (`` `md-${kind}` ``). Read the caller before you decide.
5. **Sort into three lists.** *Dead*: delete. *Keep*: write down why (for example a
   public protocol method, a test seam, used by mockups). *Ask*: anything that is a product
   decision. Ask all *Ask* items in one batch, each with a recommendation:
   - a whole feature, importer, migration or script the user may still run by hand;
   - a requirement or spec row that would have to be withdrawn;
   - a dependency to remove;
   - large untracked folders (models, data, exports) and anything outside the repository.
6. **Remove test-first.** Add guard tests that fail now: the module cannot be imported,
   the route returns 404, no doc names a removed file, every link in the docs resolves.
   Watch them fail. Delete the code and its tests. If a removed module held a helper that
   live tests still use, move it to the shared test fakes. Run the gates.
7. **Sweep the docs.** Search README, design, plan, the instruction files, the dependency
   list and the env example for every removed name, path and setting key. Fix only what
   is now wrong. Keep history (changelogs, progress logs) as history. Regenerate any
   generated table of contents.
8. **Verify.** Run every gate in full, run the cleanup script again (gates leave caches),
   run `git diff --check`, and keep the line endings the files had.
9. **Commit and report**, following the project workflow. Report: what was removed, what
   was kept on purpose and why, open questions, and what the user must delete outside the
   repository.

## What to scan

| Kind | How to find it |
| --- | --- |
| Functions, classes, module names | `find_unreferenced.py`; then grep each name |
| Whole files and modules | No import of the module; no mention in scripts or config |
| Scripts | No mention in README, docs, CI or other scripts; one-time jobs already run |
| CSS classes and custom properties | `find_unreferenced.py`; grep HTML and JS, including string-built names |
| Settings and env keys | Key in `.env.example` and the config module but read nowhere |
| Dependencies | Each line of the dependency list: grep its import name in code and scripts |
| Exports | Exported but used only in its own module: make it private, do not delete it |
| Parameters and fields | Passed everywhere but never read; read but always the same value |
| Comments and docstrings | Name code, files or rules that are gone |
| Untracked folders | Large folders the code no longer reads (models, caches, old data) |

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Trusting the finder | It only finds candidates. Route handlers, hooks and string-built names look unused. |
| Grepping only the source folder | Search tests, scripts, HTML, config and docs too. |
| Stopping after one pass | A removal exposes new dead code. Scan again until nothing new shows up. |
| Deleting a feature the spec still requires | That is the user's decision. Ask, and withdraw the spec row only with approval. |
| Deleting a test that guards live behavior | Delete only the tests of the removed code. |
| A guard test that passes on its first run | Prove it: run it against the old version (`git show HEAD:<path>`). |
| Bulk edits through shell heredocs | Heredocs can eat backslashes and quotes. Write edit scripts to a file, then run the file. |
| Rewriting the line endings of docs | Read bytes, edit, and write back with the original line endings. |
| Deleting outside the repository or user data | List it in the report for the user to delete. |
