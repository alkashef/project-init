---
name: project-init
description: Set up the current folder as a new project from the golden templates and push it to GitHub. Run it in a new, empty project folder that is open in VS Code. Builds CLAUDE.md, the path-scoped rules, docs/ (workflow, inbox, spec, design, plan), README, tool configs and starting folders, then commits, creates the GitHub repository, pushes, and creates a conda environment with the project's name. Use whenever the user wants to start, init, bootstrap or scaffold a new project or repo, or says "new project", even if they do not mention GitHub or the docs. Not for adding files to an existing project.
---

# Project init

The user creates the project folder and opens it in VS Code first. This skill sets up that folder
(the current working directory). It is self-contained:

- `scripts/init_project.py` runs the steps below. `scripts/build_instance.py` builds the files.
- `assets/` holds everything a new project receives, laid out as it is in a project, plus the
  master `CLAUDE_GOLDEN.md` that the builder splits into `CLAUDE.md` and `.claude/rules/`.

To change what new projects get, edit `assets/`, not this file.

## Steps

1. **Ask**, in one message, and propose a default for each. Start by showing the folder you will
   set up (the current working directory). If it is not the project folder, stop and tell the user
   to open the right one.
   - **Project name.** It becomes the GitHub repository name, the conda environment name, and the
     README title. Default: the folder name. Letters, digits, `.`, `_`, `-`.
   - **Purpose.** One line. It fills CLAUDE.md, the spec, the README, and the repository description.
   - **Modules.** Propose the ones the purpose implies and let the user adjust. Default: `python`.
   - **Visibility.** Private by default. Use `--public` only if the user says so.

   | Module | Add when the project has | Adds |
   | --- | --- | --- |
   | `python` | Python code | ruff, mypy, pytest configs, `requirements.txt`, Python rules |
   | `javascript` | JavaScript or TypeScript | `package.json`, `tsconfig.json`, `eslint.config.js` |
   | `html-css`, `ui-design` | a browser front end, a user interface | HTML/CSS and UI rules, `tests/e2e/ui/` |
   | `http-apis` | an HTTP API | API rules |
   | `data` | data files or a data store | data rules, `data/` |
   | `cli` | a command-line interface | CLI rules |
   | `llm` | LLM calls or local models | LLM rules, `models/`, `prompts/` |
   | `logging`, `long-running`, `validation` | logging, async jobs, user input | those rules |
   | `static-site` | a Markdown-to-HTML site | static-site rules, `content/`, `site/` |
   | `mcp`, `docker` | an MCP server or host, Docker | those rules, `.dockerignore` |

2. **Run the script** from the project folder with the PowerShell tool. It checks everything first
   and changes nothing if a check fails:

   ```powershell
   python "<this skill's folder>\scripts\init_project.py" --name <name> --with <modules> --purpose "<purpose>"
   ```

   Plain `python` on this machine can be the Microsoft Store stub. If it fails, use
   `C:\Users\aa186095\AppData\Local\miniconda3\python.exe`. Options: `--public`, `--no-github`
   (local repository only), `--remote-url <url>` (push to a repository that already exists),
   `--no-conda` (no conda environment).

   The script: (1) checks the name, that the folder is empty (apart from `.git`, `.claude`,
   `.vscode`), git and its identity, the `gh` login, that no GitHub repository has that name, and
   that conda is installed; (2) runs `git init -b main` unless the folder is already a repository
   with no commits; (3) runs `build_instance.py`, which keeps any file that already exists;
   (4) commits, then turns on the pre-commit hook (`git config core.hooksPath .githooks`);
   (5) runs `gh repo create` unless `origin` already exists, then pushes `main`;
   (6) runs `conda create -n <name> python=3.12` unless that environment already exists. The first
   commit holds the whole scaffold, so the push is never empty. `.vscode/settings.json` makes cmd
   the default VS Code terminal, and each new terminal runs `conda activate <name>`.

3. **If it fails**, show the error as printed and give the fix. Do not delete anything.
   - `gh` is missing or not logged in: ask the user to run `winget install GitHub.cli` and then
     `gh auth login`. Do not install it yourself.
   - The folder holds other files, or the repository already has commits: this skill is for a
     new project. Ask the user to use an empty folder.
   - The push failed after the repository was created: the project is committed locally. Fix the
     cause, then run `git push -u origin main` in the project folder.
   - conda is missing: ask the user to install Miniconda, or rerun with `--no-conda`.
   - `conda create` failed: the project is set up and pushed. Give the user the command the error
     prints.
   - Anything else: the script says what to change. Rerun with the corrected input.

4. **Report**: the repository URL and the next steps:
   - **Start a new Claude Code session in this folder.** `CLAUDE.md`, the rules, and
     `.claude/settings.json` (permissions and the edit hook) were created after this session
     started, so they load only in a new one. If Claude Code asks whether to trust the folder,
     say yes: until then it ignores the `allow` rules.
   - Open a new VS Code terminal: it is cmd, with the project's conda environment active. If it
     says `conda` is not recognized, run `conda init cmd.exe` once and open a new terminal.
   - Python: in that terminal, install `pytest`, `pytest-cov`, `mypy`, `ruff` and
     `python-dotenv`, and pin their versions in `requirements.txt`. The scaffold leaves it empty on
     purpose, because it does not invent versions. JavaScript: run `npm install`. Then run
     `python scripts/check.py` in that terminal: it prints `All checks passed.` once the tools
     are found.
   - Install the recommended VS Code extensions: VS Code may not offer them, because the file
     appeared after the folder was opened. Extensions view, search `@recommended`.
   - The checks are enforced: after each edit, a Claude Code hook runs ruff or ESLint on the file
     and sends what is left back to Claude, and the git pre-commit hook refuses a commit unless
     every check passes. Until the tools above are installed, it refuses every commit and names
     what is missing.
   - Write the first ideas in `docs/inbox.md`, then follow `docs/workflow.md`.
   - Review the **Project** section of the new `CLAUDE.md` and the layout table in `docs/design.md`.

Do not edit the generated files or make more commits in this skill. Setting up the project is done
when the script succeeds.
