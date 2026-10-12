# To do

1. **Check the `code-chef` skill** in `skills/`.
   - Decide: keep it in this repo, move it to its own repo, or delete it. The README says they are not part of this project.
   - `code-chef/SKILL.md` looks malformed: after its frontmatter, a ` ```md ` block holds a second frontmatter with a different `description`. Only the first one would load.
   - Neither is installed in `%USERPROFILE%\.claude\skills\`.

1. **Check the `deadcode` skill** in `skills/`.
   - Decide: keep it in this repo, move it to its own repo, or delete it. The README says they are not part of this project.
   - `deadcode/find_unreferenced.py` is a script: lint and type-check it like the others.
   - Neither is installed in `%USERPROFILE%\.claude\skills\`.
