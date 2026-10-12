# project-init

**A Claude Code skill that sets up a new project.** You create an empty folder and open it in VS Code,
then run the skill. It gives the new project its starting files: `CLAUDE.md` and path-scoped
rules, docs, README, tool configs and starting folders. Then it commits, creates a GitHub
repository, and pushes.

This repository is the skill's source. Everything the skill needs is inside `skills/project-init/`.

## Contents

- [What it does](#what-it-does)
- [What a new project gets, and why](#what-a-new-project-gets-and-why)
  - [Every project](#every-project)
  - [With the `python` module](#with-the-python-module)
  - [With the `javascript` module](#with-the-javascript-module)
  - [With other modules](#with-other-modules)
- [Stack](#stack)
- [File structure](#file-structure)
- [To use the skill to start a new project](#to-use-the-skill-to-start-a-new-project)
  - [1. Install the skill](#1-install-the-skill)
  - [2. Set up GitHub](#2-set-up-github)
  - [3. Set up conda](#3-set-up-conda)
- [To work on this repository](#to-work-on-this-repository)
- [How to run](#how-to-run)
  - [Start a new project with the skill](#start-a-new-project-with-the-skill)
  - [The scripts alone](#the-scripts-alone)
- [How to test](#how-to-test)
  - [The test suite](#the-test-suite)
  - [Lint and type checks](#lint-and-type-checks)
  - [Checked in real Claude Code sessions](#checked-in-real-claude-code-sessions)

## What it does

1. `scripts/init_project.py` checks the folder, git, the `gh` login and conda (and changes nothing
   if a check fails), runs `git init`, calls the builder, creates a conda environment with the
   project's name (Python 3.12) and, for a Python project, installs the Python tools into it and
   pins them, then commits, turns on the pre-commit hook, runs `gh repo create`, and pushes.
2. `scripts/build_instance.py` splits the master `assets/CLAUDE_GOLDEN.md` into a `CLAUDE.md` of about
   190 lines that always loads, plus `.claude/rules/*.md` files that load only when Claude touches
   matching files. It copies or fills in the other files from `assets/`. Rules a tool can enforce
   (ruff, mypy, ESLint, `tsc`, permissions) are in the configs, not in prose.
3. `SKILL.md` tells Claude how to run it: what to ask, the command, how to handle failures.

## What a new project gets, and why

The skill writes files, sets up git and GitHub, and creates a conda environment named after the
project (Python 3.12). For a project with the `python` module it also installs the Python tools
(pytest, pytest-cov, mypy, ruff, python-dotenv) into that environment and pins the versions pip
actually installed in `requirements.txt`, so the hooks work from the first commit. It installs
nothing else: the JavaScript tools are installed with `npm install` afterwards, from the pinned
`package.json`.

The idea behind the files: Claude follows written rules most of the time, but not always, and every
line of `CLAUDE.md` costs context in every session. So each rule a tool can check goes into that
tool's config, where it is enforced on every run, and `CLAUDE.md` keeps only what no tool can check.

### Every project

| File | What it is | Why |
| --- | --- | --- |
| `CLAUDE.md` | The rules Claude always loads: workflow, project facts, how to work. About 190 lines. | Claude Code reads it at the start of every session. Anthropic advises keeping it under 200 lines: a longer file uses more context and is followed less reliably. |
| `.claude/rules/*.md` | The other rules, one file per topic, each with `paths:` globs. Which files you get depends on the modules. | A rule file loads only when Claude touches a matching file, so the Python rules cost nothing while Claude edits CSS. |
| `.claude/settings.json` | Claude Code permissions. Allowed without asking: git status, diff, log, add, commit, push, `check.py` and `cleanup.py`. Asks first: editing `CLAUDE.md`, the spec and this file; editing the check configs (`ruff.toml`, `mypy.ini`, `pytest.ini`, `package.json`, `tsconfig.json`, `eslint.config.js`, `.prettierrc.json`, `.stylelintrc.json`) and the hook files (`.githooks/`, `scripts/check.py`, `scripts/run-check.sh`), so a check cannot be loosened to make it pass; installing packages; deleting folders; killing processes. Denied: force push, `git reset --hard`, `git clean`, `git restore`, deleting Docker volumes, and skipping the git hooks (`--no-verify`, `commit -n`, `core.hooksPath`). Each rule is written twice, as `Bash(...)` and `PowerShell(...)`. Also the edit hook: after every `Edit` or `Write`, it runs `scripts/check.py --edited` on that file. | Routine steps run without prompts, and commands that destroy work cannot run at all, even in bypass mode. A rule here is enforced; a rule in `CLAUDE.md` is only advice. On Windows, Claude Code may run commands with its PowerShell tool, which `Bash(...)` rules do not cover. The edit hook makes Claude fix lint errors as it writes, not at the end. |
| `scripts/check.py`, `scripts/run-check.sh` | The checks: `ruff check`, `ruff format --check` and `mypy` (with `ruff.toml`); `npm run lint`, `typecheck`, `format:check` (Prettier) and `lint:css` (Stylelint) with `package.json`, each once there are files for it to check; and the tests: pytest with the 80% branch-coverage floor once `tests/` holds a `test_*.py`, `npm test` once it holds a `*.test.js`. With `--edited` it checks one file: ruff, ESLint, Stylelint and Prettier fix what they can, and the rest goes back to Claude. `run-check.sh` finds the project's conda Python (the active environment, or `envs/<name>` under conda's folder) and runs `check.py` with it. | One command runs every check the extensions show in the editor, and both hooks use it. `python` alone is not reliable in hooks: on Windows it can be the Microsoft Store stub, and Claude Code's shell may not have the environment active. |
| `.githooks/pre-commit` | Runs `scripts/run-check.sh`. A failing check or test refuses the commit. `init_project.py` turns it on with `git config core.hooksPath .githooks` after the first commit; after a fresh clone, the new README says to run that once. | Lint errors, type errors and failing tests cannot reach the history, from Claude or from you. The workflow already tells Claude to run the tests before a commit; the hook makes sure, for every commit. If a tool is missing (before `npm install`, for example), it refuses the commit and names the tool. |
| `.gitattributes` | LF line endings for every text file, on every machine. | The hook scripts fail under `sh` with CRLF endings, which git on Windows (`core.autocrlf=true`) would otherwise give them. |
| `docs/workflow.md`, `inbox.md`, `spec.md`, `design.md`, `plan.md` | The working loop (copied) and its four documents (filled in with the name and purpose). | Ideas go to the inbox, then the spec and design, then a plan, one milestone at a time. Claude works from these files instead of from memory of past sessions. |
| `README.md` | Filled in with the name, purpose, stack, folder table, setup, run and test commands. | Every project starts with a README that says how to set it up and run it. |
| `.gitignore` | Ignores secrets (`config/.env`), data, models, logs, caches, `node_modules`, local settings. | Secrets and large or generated files never reach GitHub. |
| `config/.env.example` | The list of settings, with secrets left empty. | Copied to `config/.env`, which is never committed, so settings live in one place and secrets stay out of the code. |
| `.vscode/settings.json` | Format on save, UTF-8, LF line endings, ruff for Python, Prettier and ESLint fixes for JavaScript, mypy with `mypy.ini`, pytest in `tests/`. The default terminal is cmd, and each new terminal runs `conda activate <project name>`. | The editor applies the same checks as the command line while you type, and every terminal starts in the project's environment, so nothing is installed into `base` by mistake. |
| `.vscode/extensions.json` | Recommends extensions for the modules you chose: Python, Ruff and Mypy with `python`; ESLint and Prettier with `javascript`; Prettier and Stylelint with `html-css` or `ui-design`. Error Lens and SonarLint for every project. Built by `build_instance.py`, not copied. | VS Code offers to install them when the project opens; nothing installs them without your click. A project gets only the extensions its files use. |
| `scripts/cleanup.py` | Deletes caches and generated files (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, coverage, logs). Never source, data or environments. `--dry-run` lists only. | One safe command Claude may run without asking. |
| `src/`, `tests/unit/`, `tests/e2e/` | Empty starting folders (each holds a `.gitkeep`). | Every project has the same layout, which the rules and configs assume. |

### With the `python` module

| File | What it is | Why |
| --- | --- | --- |
| `ruff.toml` | Linter and formatter config: line length 100, docstrings, type annotations, import order, naming, security checks, no `print` outside `scripts/`, pathlib, and limits on complexity (8), arguments (4) and statements per function (15). | Ruff checks style, common bugs and code smells in well under a second, so Claude can run it after every change. The limits keep functions small. |
| `mypy.ini` | Type checker config: `strict = True` on `src/`. | Strict typing finds wrong types and missing `None` checks before the code runs, and typed code is easier for Claude to change safely. |
| `pytest.ini` | Test config: tests live in `tests/`, async tests run without decorators. The test command requires 80% branch coverage. | Tests prove a change works. The coverage floor stops untested code from growing. |
| `requirements.txt` | pytest, pytest-cov, mypy, ruff and python-dotenv, each pinned with `==`. With `--no-conda`, or if the install fails, only a comment naming them. | The skill installs the latest versions into the new environment and pins what pip installed, so it never guesses a version, and a clone gets the same tools. |

### With the `javascript` module

| File | What it is | Why |
| --- | --- | --- |
| `package.json` | Dev-only tools, pinned: ESLint, TypeScript, Node types, Prettier, Stylelint. Scripts: `typecheck`, `lint`, `lint:css`, `format:check`, `test`. Also with `html-css` and `ui-design`. | The app itself has no dependencies and no build step. These tools only check the code. |
| `.prettierrc.json`, `.stylelintrc.json` | Prettier formats JavaScript, CSS and HTML at line length 100 (as ruff does). Stylelint checks CSS with its standard rules. Also with `html-css` and `ui-design`. | The formatting and CSS the editor extensions show are checked by the hooks too, so they cannot drift. |
| `tsconfig.json` | Type-checks plain JavaScript (`checkJs`, `strict`) without compiling. | Type errors are found in `.js` files without switching to TypeScript. |
| `eslint.config.js` | ESLint rules: the same size limits as ruff, `const` over `let`, `===`, no `console` outside `log.js`, no `fetch` outside `api.js`, no `innerHTML`. | It enforces the JavaScript rules from `CLAUDE.md`, including the ones that keep unsafe HTML out. |

### With other modules

Most modules add only a rules file under `.claude/rules/`. Some also add folders: `data` adds
`data/`, `llm` adds `models/` and `prompts/`, `static-site` adds `content/` and `site/`, and the
`html-css` and `ui-design` modules add `tests/e2e/ui/`. `docker` adds `.dockerignore`, which keeps
secrets, data, models, caches, tests and docs out of the image.

## Stack

Python 3.12 (this repository's conda environment, `project-init`). The scripts use only the standard library. They were
checked with ruff 0.17.0 and mypy 2.4.0 using the configs in `assets/`.

## File structure

```text
skills/project-init/            the skill. Install by copying this folder.
  SKILL.md                      what Claude reads: steps, questions, failure handling
  scripts/
    init_project.py             folder, git, GitHub: the entry point
    build_instance.py           builds the files; holds the section-to-file map and path globs
  assets/                       everything a new project receives, laid out as in a project
    CLAUDE_GOLDEN.md            the master, in tagged sections. Never copied.
    CLAUDE_GOLDEN.md.646        the master before the cut to the line budget. Reference only.
    docs/                       workflow.md (copied); inbox, spec, design, plan (filled in)
    scripts/cleanup.py          cache cleaner (copied)
    scripts/check.py            the checks both hooks run (copied)
    scripts/run-check.sh        finds the project's Python, runs check.py (filled in)
    .githooks/pre-commit        the git hook (copied)
    README.md, requirements.txt, config/.env.example    (filled in or copied)
    ruff.toml, mypy.ini, pytest.ini                     Python checks
    package.json, tsconfig.json, eslint.config.js       JavaScript checks
    .gitignore, .gitattributes, .dockerignore, .claude/settings.json, .vscode/
tests/                          the test suite (not installed with the skill)
  fake_gh.py, fake_conda.py     stand in for the GitHub CLI and conda; never touch the real ones
  helpers.py, conftest.py       the sandbox: project folder, bare remote, isolated git config
  test_assets.py                the assets match what the builder expects
  test_build_instance.py        what the builder writes and leaves alone
  test_init_project.py          init end to end, and every refusal
  test_checks.py                check.py and both hooks, with the real ruff, mypy and pytest
pytest.ini                      points pytest at tests/ and the skill's scripts
CLAUDE.md, TODO.md              instructions for working on this repository; open items
```

`assets/CLAUDE_GOLDEN.md.646` is the master as it was before it was cut from 646 lines to 525, so
that the always-loaded `CLAUDE.md` would fit under 200 lines. The name records its line count. It
is kept so you can see the full wording of rules that were shortened or dropped, and bring one back.
Nothing reads it: `build_instance.py` reads only `CLAUDE_GOLDEN.md`, and new projects never get it.
Do not edit it.

## To use the skill to start a new project

Do these once per machine.

### 1. Install the skill

1. Copy `skills/project-init` to `%USERPROFILE%\.claude\skills\project-init`.
2. Delete the old `%USERPROFILE%\.claude\skills\project-docs-init`. This skill replaces it.
3. After every change to the skill, copy it again.

### 2. Set up GitHub

1. Install the GitHub CLI:

   ```bat
   winget install GitHub.cli
   ```

2. Open a new terminal. The old one does not see the new PATH.
3. Log in:

   ```bat
   gh auth login
   ```

4. Check that git has `user.name` and `user.email` set.

If winget fails with `0x8a15000f` (data required by the source is missing):

1. In an administrator terminal, run:

   ```bat
   winget source reset --force
   ```

2. Install again (step 1).

### 3. Set up conda

1. Install Miniconda.
2. Set it up for cmd, once, so that `conda activate` works in the VS Code terminal:

   ```bat
   conda init cmd.exe
   ```

You do not create a conda environment for a new project. The skill creates it, named after that
project.

## To work on this repository

You need this only to change the skill or run its tests. `project-init` here is this repository's
own environment, not a new project's.

1. Create the environment, once:

   ```bat
   conda create -n project-init python=3.12
   ```

2. Activate it and install the tools, once:

   ```bat
   conda activate project-init
   pip install ruff==0.17.0 mypy pytest pytest-cov
   ```

3. After that, each time you work here, only activate it:

   ```bat
   conda activate project-init
   ```

## How to run

### Start a new project with the skill

Do "To use the skill to start a new project" above once. Then, for each new project:

1. **Create an empty folder** for the project, for example `C:\alkashef\GitHub\my-app`, and open it
   in VS Code (File > Open Folder). The folder may hold only `.git`, `.claude` and `.vscode`. A
   repository with commits is refused, because the skill is for new projects.
2. **Open Claude Code in that folder** (the VS Code extension, or `claude` in the VS Code terminal).
3. **Run the skill.** Type `/project-init`, or just say "start a new project".
4. **Answer its questions.** It proposes a default for each:
   - *Project name*: the GitHub repository name and the conda environment name. Default: the
     folder name.
   - *Purpose*: one line. It goes into `CLAUDE.md`, the spec, the README and the repository
     description.
   - *Modules*: what the project has. It proposes some from your purpose. Default: `python`.
   - *Visibility*: private unless you say public.

   | Module | Add when the project has |
   | --- | --- |
   | `python`, `javascript` | Python code, JavaScript or TypeScript |
   | `html-css`, `ui-design` | a browser front end, a user interface |
   | `http-apis`, `cli`, `mcp` | an HTTP API, a command-line interface, an MCP server or host |
   | `data`, `llm` | data files or a store, LLM calls or local models |
   | `logging`, `long-running`, `validation` | logging, async jobs, user-input validation |
   | `static-site`, `docker` | a Markdown-to-HTML site, Docker |

5. **Wait for it to finish.** It checks everything first and changes nothing if a check fails.
   Then it runs `git init`, builds the files, creates the conda environment and installs the
   Python tools (about a minute), makes the first commit (the whole scaffold), turns on the
   pre-commit hook, creates the GitHub repository, and pushes `main`. It ends by printing the
   repository URL and the environment.
6. **Start a new Claude Code session in the same folder** (a new conversation). `CLAUDE.md`, the
   rules, the permissions and the edit hook were created after the first session began, so only
   a new one loads them. If Claude Code asks whether you trust the folder, say yes: until you do,
   it ignores the project's `allow` rules (the `ask` and `deny` rules still apply).
7. **Finish the setup** (the skill's report lists these):
   - JavaScript, HTML or CSS: open a new VS Code terminal and run `npm install`. Until then, the
     pre-commit hook refuses every commit that has web files to check, and says so. (The Python
     tools are already installed.)
   - Check that the tools are found. In a new VS Code terminal (cmd, with the project's
     environment active), run:

     ```bat
     python scripts/check.py
     ```

     It should print `All checks passed.` If it names a tool, that tool is not installed yet.
   - Install the recommended VS Code extensions. VS Code may not offer them, because
     `.vscode/extensions.json` appeared after the folder was opened: in the Extensions view, search
     `@recommended` and choose *Install Workspace Recommended Extensions*.
   - Check the **Project** section of `CLAUDE.md` and the layout table in `docs/design.md`.
   - Write your first ideas in `docs/inbox.md`, then tell Claude to go through the inbox. From
     there the loop is in `docs/workflow.md`: inbox, spec and design, plan, one milestone at a time.

If it stops with an error, nothing was deleted. The usual causes: `gh` is missing or not logged in
(`winget install GitHub.cli`, then `gh auth login`); the folder holds other files; the repository
name is taken (rerun with `--name`, or tell the skill another name); git has no `user.name` or
`user.email`; conda is not installed (install Miniconda, or rerun with `--no-conda`). If conda
or pip fails partway (no network, for example), the project is still committed and pushed, and
the error says the commands to run by hand.

### The scripts alone

From `skills/project-init/`:

```bash
python scripts/init_project.py --with python http-apis --purpose "Does X"   # in the new folder
python scripts/build_instance.py <folder> --with python --dry-run           # list only
```

`--with` modules: `logging`, `llm`, `long-running`, `validation`, `python`, `javascript`,
`html-css`, `ui-design`, `http-apis`, `data`, `cli`, `static-site`, `mcp`, `docker`. Existing files
are never overwritten unless `build_instance.py` gets `--force`.

**Changing what new projects get.** Edit `assets/`. For the rules, edit `assets/CLAUDE_GOLDEN.md`,
keep its section tags, and keep the always-loaded set (`always_loaded()` in `build_instance.py`)
under 200 lines once built.

**The line budget.** The built `CLAUDE.md` must have fewer than 200 lines, counting every line,
blank lines included. It is about 190 now. The test suite checks this on a build with every module.

- *Why every line:* Anthropic's advice to keep `CLAUDE.md` under 200 lines counts the file as it
  is. Skipping blank lines would let the file pass the test at well over 200 real lines.
- *Why only `CLAUDE.md`:* it loads in every session. A rules file loads only when Claude touches a
  matching file, so it has no limit. Keep rules files short anyway: several can load at once (a
  `.js` file loads both `javascript.md` and `ui-design.md`).
- *If the test fails:* shorten a section, or move one out of `always_loaded()` into a rules file
  in `rule_files()`. Do not raise the limit.

## How to test

### The test suite

From the repository root:

```bash
conda run -n project-init python -m pytest
```

It runs in about 30 seconds and needs only git. Each test works in its own temporary folder, with
its own git config, a fake `gh` (`tests/fake_gh.py`) that answers the three calls the skill makes
and adds a local bare repository as `origin`, so every push is a real git push, and a fake conda
(`tests/fake_conda.py`) that lists and "creates" environments without touching conda. Your own git
config, GitHub account and conda environments are never touched.

- `test_assets.py`: every asset the builder lists exists; every section of `CLAUDE_GOLDEN.md` goes
  into `CLAUDE.md` or a rules file; every `Bash(...)` permission rule has a `PowerShell(...)` twin;
  the edit hook is set up; and editing a check config or a hook file asks first.
- `test_build_instance.py`: which files each build writes, no `{{placeholders}}` left, rules files
  start with `paths:`, `--dry-run` writes nothing, a second run keeps existing files, `--force`
  overwrites, an unknown module is refused, the recommended extensions follow the modules (a
  Python-only project gets no ESLint, Prettier or Stylelint), and `CLAUDE.md` has fewer than 200
  lines (see "The line budget").
- `test_init_project.py`: a run commits once on `main` and pushes; the repository is created
  private (or `--public`) with the purpose; `--no-github`, `--remote-url`, an existing empty
  repository and an existing `origin` work without calling `gh`; a failed push says how to finish;
  the conda environment is created with the project's name, kept if it exists, skipped with
  `--no-conda`, and a failed create says how to finish; a Python project gets its tools installed
  and pinned in the first commit, other projects get none, and a failed install says how to
  finish; and each of ten refusals stops with its message and changes nothing in the folder.
- `test_checks.py`: init turns on the pre-commit hook and marks the hook scripts executable; the
  scripts have LF endings; `check.py` passes on a new project and fails on a lint error; after an
  edit it fixes the file and sends the rest back as a `block` decision, and ignores other files; a
  missing tool is named; the tests run once there are some, and a failing one fails the check; and a
  real `git commit` is refused by the hook, then accepted once fixed.
- The built `.vscode/settings.json` makes cmd the default terminal with `conda activate <name>`.

### Lint and type checks

Use the configs that new projects get, in `assets/`. Run the checks for
`assets/scripts/cleanup.py` from inside `assets/`, where it sits as it will in a new project. From
anywhere else, the `scripts/**` exception for `print` does not match it. The same goes for
`assets/scripts/check.py`, whose `S603` exception (it runs the check tools) is in `ruff.toml`. One
line in `init_project.py` carries `# noqa: S603` (it exists to run git and gh).

```bash
# from skills/project-init/
conda run -n project-init ruff check --config assets/ruff.toml scripts
conda run -n project-init ruff format --check --config assets/ruff.toml scripts assets/scripts
conda run -n project-init mypy --config-file assets/mypy.ini scripts assets/scripts
# from skills/project-init/assets/
conda run -n project-init ruff check --config ruff.toml scripts
# from the repository root (bash; MYPYPATH lets mypy find the scripts the tests import)
conda run -n project-init ruff check --config skills/project-init/assets/ruff.toml tests
MYPYPATH="skills/project-init/scripts;tests" conda run -n project-init mypy --config-file skills/project-init/assets/mypy.ini tests
```

### Checked in real Claude Code sessions

Run once by hand with headless `claude -p` sessions in a project built by the skill (not part of
the suite):

- `CLAUDE.md` loads at the start of a session. `.claude/rules/python.md` loads only after Claude
  reads a `.py` file, and not after it reads `README.md`.
- The deny rules block `git clean`, `git reset --hard` and `git push --force`, even in bypass mode.
  Before the `PowerShell(...)` twins were added they blocked nothing, because these sessions ran
  commands with the PowerShell tool.
- An `ask` rule (`pip install`) blocks the command when no one can answer the prompt.
- An `Edit` ask rule holds even in accept-edits mode: asked to raise `line-length` in `ruff.toml`,
  Claude's edit waited for a permission no one gave, and the file stayed as it was.
- A reworded command gets past a deny rule: `git -C . clean -n` ran. Deny rules match the command
  text, so they stop mistakes, not a determined workaround.
- The edit hook: Claude wrote `import os` / `x=1` to `src/sample.py`. The hook removed the import,
  formatted the rest, and Claude got "Missing docstring in public module" as hook feedback. The
  first version reported through exit code 2, and Claude saw nothing: Claude Code ran the hook in
  PowerShell, which turned the exit code into 1 (a non-blocking error, not shown to Claude). Hence
  the JSON `block` decision.
- The pre-commit hook, with no conda environment active: it found the project's environment
  under Miniconda's folder, refused a commit with a lint error, and accepted it once fixed.
- The web checks, in a `javascript` + `html-css` project after a real `npm install` of the pinned
  tools: on an empty project they pass; with `var`, `==`, an unformatted page and an empty CSS
  block, ESLint, Prettier and Stylelint each fail. After an edit, ESLint and Stylelint fixed what
  they could, Prettier formatted the file, and only `==` and the empty block went back to Claude.

Also run once by hand: the skill with the real conda, in a scratch folder. It created the
environment in about 30 seconds, and `conda activate <name>` in cmd then found its Python 3.12.

Also run once by hand: the installed skill against the real `gh` 2.102.0, in a scratch folder. It
created the private repository `project-init-smoke-test` with the purpose as its description,
pushed one commit to `main` (the same commit as the local one, 32 files and folders on GitHub),
and created the conda environment. A second run with the same name in another empty folder was
refused (`already exists`) and left that folder empty.
