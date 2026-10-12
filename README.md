# project-init

A Claude Code skill that sets up a new project. You create an empty folder and open it in VS Code,
then run the skill. It gives the new project its starting files: `CLAUDE.md` and path-scoped
rules, docs, README, tool configs and starting folders. Then it commits, creates a GitHub
repository, and pushes.

This repository is the skill's source. Everything the skill needs is inside `skills/project-init/`.

## What it does

1. `scripts/init_project.py` checks the folder, git, and the `gh` login (and changes nothing if a
   check fails), runs `git init`, calls the builder, commits, runs `gh repo create`, and pushes.
2. `scripts/build_instance.py` splits the master `assets/CLAUDE_GOLDEN.md` into a `CLAUDE.md` of about
   190 lines that always loads, plus `.claude/rules/*.md` files that load only when Claude touches
   matching files. It copies or fills in the other files from `assets/`. Rules a tool can enforce
   (ruff, mypy, ESLint, `tsc`, permissions) are in the configs, not in prose.
3. `SKILL.md` tells Claude how to run it: what to ask, the command, how to handle failures.

## What a new project gets, and why

The skill installs nothing. It writes files and sets up git and GitHub. The tools those files
configure (ruff, mypy, pytest, ESLint, TypeScript) are installed by the user afterwards: the
skill's report lists them, and the new README's Setup says how.

The idea behind the files: Claude follows written rules most of the time, but not always, and every
line of `CLAUDE.md` costs context in every session. So each rule a tool can check goes into that
tool's config, where it is enforced on every run, and `CLAUDE.md` keeps only what no tool can check.

### Every project

| File | What it is | Why |
| --- | --- | --- |
| `CLAUDE.md` | The rules Claude always loads: workflow, project facts, how to work. About 190 lines. | Claude Code reads it at the start of every session. Anthropic advises keeping it under 200 lines: a longer file uses more context and is followed less reliably. |
| `.claude/rules/*.md` | The other rules, one file per topic, each with `paths:` globs. Which files you get depends on the modules. | A rule file loads only when Claude touches a matching file, so the Python rules cost nothing while Claude edits CSS. |
| `.claude/settings.json` | Claude Code permissions. Allowed without asking: git status, diff, log, add, commit, push, and `cleanup.py`. Asks first: editing `CLAUDE.md`, the spec and this file; installing packages; deleting folders; killing processes. Denied: force push, `git reset --hard`, `git clean`, `git restore`, and deleting Docker volumes. | Routine steps run without prompts, and commands that destroy work cannot run at all. A rule here is enforced; a rule in `CLAUDE.md` is only advice. |
| `docs/workflow.md`, `inbox.md`, `spec.md`, `design.md`, `plan.md` | The working loop (copied) and its four documents (filled in with the name and purpose). | Ideas go to the inbox, then the spec and design, then a plan, one milestone at a time. Claude works from these files instead of from memory of past sessions. |
| `README.md` | Filled in with the name, purpose, stack, folder table, setup, run and test commands. | Every project starts with a README that says how to set it up and run it. |
| `.gitignore` | Ignores secrets (`config/.env`), data, models, logs, caches, `node_modules`, local settings. | Secrets and large or generated files never reach GitHub. |
| `config/.env.example` | The list of settings, with secrets left empty. | Copied to `config/.env`, which is never committed, so settings live in one place and secrets stay out of the code. |
| `.vscode/settings.json` | Format on save, UTF-8, LF line endings, ruff for Python, Prettier and ESLint fixes for JavaScript, mypy with `mypy.ini`, pytest in `tests/`. | The editor applies the same checks as the command line while you type. |
| `.vscode/extensions.json` | Recommends Python, Ruff, Mypy, ESLint, Prettier, Stylelint, Error Lens and SonarLint. | VS Code offers to install them when the project opens. |
| `scripts/cleanup.py` | Deletes caches and generated files (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, coverage, logs). Never source, data or environments. `--dry-run` lists only. | One safe command Claude may run without asking. |
| `src/`, `tests/unit/`, `tests/e2e/` | Empty starting folders (each holds a `.gitkeep`). | Every project has the same layout, which the rules and configs assume. |

### With the `python` module

| File | What it is | Why |
| --- | --- | --- |
| `ruff.toml` | Linter and formatter config: line length 100, docstrings, type annotations, import order, naming, security checks, no `print` outside `scripts/`, pathlib, and limits on complexity (8), arguments (4) and statements per function (15). | Ruff checks style, common bugs and code smells in well under a second, so Claude can run it after every change. The limits keep functions small. |
| `mypy.ini` | Type checker config: `strict = True` on `src/`. | Strict typing finds wrong types and missing `None` checks before the code runs, and typed code is easier for Claude to change safely. |
| `pytest.ini` | Test config: tests live in `tests/`, async tests run without decorators. The test command requires 80% branch coverage. | Tests prove a change works. The coverage floor stops untested code from growing. |
| `requirements.txt` | Empty apart from a comment naming what to add: pytest, pytest-cov, mypy, ruff, python-dotenv. | Versions are pinned with `==` when the environment is created, from what was actually installed. The skill does not guess versions. |

### With the `javascript` module

| File | What it is | Why |
| --- | --- | --- |
| `package.json` | Dev-only tools, pinned: ESLint, TypeScript, Node types. Scripts: `typecheck`, `lint`, `test`. | The app itself has no dependencies and no build step. These tools only check the code. |
| `tsconfig.json` | Type-checks plain JavaScript (`checkJs`, `strict`) without compiling. | Type errors are found in `.js` files without switching to TypeScript. |
| `eslint.config.js` | ESLint rules: the same size limits as ruff, `const` over `let`, `===`, no `console` outside `log.js`, no `fetch` outside `api.js`, no `innerHTML`. | It enforces the JavaScript rules from `CLAUDE.md`, including the ones that keep unsafe HTML out. |

### With other modules

Most modules add only a rules file under `.claude/rules/`. Some also add folders: `data` adds
`data/`, `llm` adds `models/` and `prompts/`, `static-site` adds `content/` and `site/`, and the
`html-css` and `ui-design` modules add `tests/e2e/ui/`. `docker` adds `.dockerignore`, which keeps
secrets, data, models, caches, tests and docs out of the image.

## Stack

Python 3.12 (conda environment `project-init`). The scripts use only the standard library. They were
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
    README.md, requirements.txt, config/.env.example    (filled in or copied)
    ruff.toml, mypy.ini, pytest.ini                     Python checks
    package.json, tsconfig.json, eslint.config.js       JavaScript checks
    .gitignore, .dockerignore, .claude/settings.json, .vscode/
skills/code-chef/, skills/deadcode/    other skills. Not part of this project.
```

`assets/CLAUDE_GOLDEN.md.646` is the master as it was before it was cut from 646 lines to 525, so
that the always-loaded `CLAUDE.md` would fit under 200 lines. The name records its line count. It
is kept so you can see the full wording of rules that were shortened or dropped, and bring one back.
Nothing reads it: `build_instance.py` reads only `CLAUDE_GOLDEN.md`, and new projects never get it.
Do not edit it.

## Setup

1. Create the conda environment once: `conda create -n project-init python=3.12`, then
   `conda activate project-init` and `pip install ruff==0.17.0 mypy pytest`. After that, only
   `conda activate project-init`.
2. Install the skill: copy `skills/project-init` to `%USERPROFILE%\.claude\skills\project-init`, and
   delete the old `%USERPROFILE%\.claude\skills\project-docs-init` it replaces. Copy again after
   every change.
3. For the GitHub step: `winget install GitHub.cli`, then `gh auth login`. Git needs `user.name`
   and `user.email`.

## How to run

### Start a new project with the skill

Do the Setup above once. Then, for each new project:

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
   Then it runs `git init`, builds the files, makes the first commit (the whole scaffold),
   creates the GitHub repository, and pushes `main`. It ends by printing the repository URL.
6. **Start a new Claude Code session in the same folder** (a new conversation). `CLAUDE.md`, the
   rules and the permissions were created after the first session began, so only a new one loads
   them.
7. **Finish the setup** (the skill's report lists these):
   - Python: create the conda environment named in `README.md` > Setup, install `pytest`,
     `pytest-cov`, `mypy`, `ruff` and `python-dotenv`, and pin their versions in `requirements.txt`.
   - Check the **Project** section of `CLAUDE.md` and the layout table in `docs/design.md`.
   - Write your first ideas in `docs/inbox.md`, then tell Claude to go through the inbox. From
     there the loop is in `docs/workflow.md`: inbox, spec and design, plan, one milestone at a time.

If it stops with an error, nothing was deleted. The usual causes: `gh` is missing or not logged in
(`winget install GitHub.cli`, then `gh auth login`); the folder holds other files; the repository
name is taken (rerun with `--name`, or tell the skill another name); git has no `user.name` or
`user.email`.

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

## How to test

There is no automated test suite in this repository yet. What was run, with scratch folders:

- `ruff check`, `ruff format --check` and `mypy` (strict) on the three scripts, with the configs in
  `assets/`. One line in `init_project.py` carries `# noqa: S603` (it exists to run git and gh).
  Run the checks for `assets/scripts/cleanup.py` from inside `assets/`, where it sits as it will in
  a new project. From anywhere else, the `scripts/**` exception for `print` does not match it:

  ```bash
  # from skills/project-init/
  conda run -n project-init ruff check --config assets/ruff.toml scripts
  conda run -n project-init ruff format --check --config assets/ruff.toml scripts assets/scripts
  conda run -n project-init mypy --config-file assets/mypy.ini scripts assets/scripts
  # from skills/project-init/assets/
  conda run -n project-init ruff check --config ruff.toml scripts
  ```

- `build_instance.py` into a scratch folder: full-stack and Python-only builds, `--dry-run`,
  a second run (skips existing files), and a rejected module name.
- `init_project.py` end to end against a fake `gh` and local bare repositories: 63 checks (empty
  folder, existing repo, cloned repo, `--public`, `--no-github`, `--remote-url`, and the refusals).

Not verified: the real `gh` (it was not installed), the permission rules in
`assets/.claude/settings.json` (check them with `/permissions`; deny rules match command text, so a
reworded command can bypass them), and when Claude Code loads a path-scoped rule file.
