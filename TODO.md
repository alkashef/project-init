# To do

1. **Check the `code-chef` skill** in `skills/`.
   - Decide: keep it in this repo, move it to its own repo, or delete it. The README says they are not part of this project.
   - `code-chef/SKILL.md` looks malformed: after its frontmatter, a ` ```md ` block holds a second frontmatter with a different `description`. Only the first one would load.
   - Neither is installed in `%USERPROFILE%\.claude\skills\`.

1. **Check the `deadcode` skill** in `skills/`.
   - Decide: keep it in this repo, move it to its own repo, or delete it. The README says they are not part of this project.
   - `deadcode/find_unreferenced.py` is a script: lint and type-check it like the others.
   - Neither is installed in `%USERPROFILE%\.claude\skills\`.

1. **Re-run the checks in that environment:** `ruff check`, `ruff format --check` and `mypy`
   (strict) on the scripts, using the configs in `skills/project-init/assets/`. Then fix the
   README's mypy version (it says 2.3.1).

1. **Add an automated test suite** for `build_instance.py` and `init_project.py`. The 63 checks
   so far were run by hand against a fake `gh`.

1. **Verify what was never tested:**
   - a run against the real `gh` (install it, `gh auth login`);
   - the permission rules in `assets/.claude/settings.json` (`/permissions` in a new project);
   - that path-scoped rule files in `.claude/rules/` load when Claude touches matching files.

1. **Install the skill:** copy `skills/project-init` to `%USERPROFILE%\.claude\skills\`, and delete
   the old `project-docs-init` skill, which is still installed.
