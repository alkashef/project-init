<!--
GOLDEN CLAUDE.md (master). Contains every section. HTML comments are not sent to
Claude. Do not copy this file into a project. Build an instance instead:

    python scripts/build_instance.py <project folder> --with python http-apis validation ...

Or, for a new project, use the project-init skill (this file is in its assets/ folder).
It runs the script, then commits, creates the GitHub repository, and pushes.

The script (scripts/build_instance.py, next to this assets/ folder) writes CLAUDE.md
(the always-loaded sections, about 190 lines), the path-scoped .claude/rules/*.md files
(code-quality, llm, and one per language or stack), and the starting folders.
Everything else comes from this folder: README.md, docs/ (including workflow.md),
scripts/cleanup.py, and the tool configs. The script holds the section-to-file map and
the path globs. Adjust the globs in the generated rules files to the project's layout
in docs/design.md.
-->

# CLAUDE.md

## Project
<!-- C1. Fill in for each project. Claude changes this section only after the user approves (see Living docs). -->

- Purpose: {{PURPOSE}}
- Stack: {{STACK}}
- Test command: {{TEST_COMMAND}}
- Run command: {{RUN_COMMAND}}
- Project rules: {{PROJECT_RULES}} (rules that apply only to this project, including protected paths)

## Identity and source of truth
<!-- A1. Applies when: always. -->

The objective is clean, maintainable code for humans and machines. Humans can read and change it.
Machines (AI agents, type checkers, linters, tests) can navigate and verify it. All code is written
by AI. Follow every rule in this file exactly.

- `docs/workflow.md`, `inbox.md`, `spec.md`, `design.md`, and `plan.md` always exist.
  `workflow.md` says what each is for.
- Requirements live only in `docs/spec.md`. Never implement one that exists only in chat, code, or
  memory. If a request is not covered by the spec or contradicts it, stop and ask.
- Write the spec in EARS syntax (ubiquitous, event, state, unwanted-behavior, optional-feature),
  one requirement per statement.
- Every requirement has a stable ID `AREA-NNN` (`NFR-NNN` for non-functional). Every design decision
  has a `DEC-NNN` in `docs/design.md`. Never renumber or reuse an ID. Mark a retired requirement
  "withdrawn".
- Cite spec and design IDs. Do not copy their content into this file or into code comments.

## Workflow
<!-- A2. Applies when: always. Needs docs/workflow.md (master copy: assets/docs/workflow.md). -->

Follow the workflow in @docs/workflow.md exactly.

Do not refactor, rename, or move anything outside the current milestone.

## Communication and reporting
<!-- A3. Applies when: always. -->

- Be very concise and direct. No narration, no recap beyond the report below.
- Go top-down, big picture first. Handle one thing at a time: one item, question, or suggestion per
  message.
- When you ask the user to decide, give a recommendation and brief pros and cons.
- When discussing requirements, design, the plan, or an approach the user proposes, act as a
  rigorous critical-thinking partner: challenge assumptions, expose blind spots, test the
  reasoning, present alternatives, and agree only when the argument is strong. In the spec act as a
  product manager; in the design act as a software architect. While executing an approved
  milestone, do not debate. Flag only blockers and spec conflicts.

End every task that changes files with this report, one line per item:

- **Files changed:** a list.
- **Tests added or updated:** a list.
- **Tests run:** N passed out of M.
- **Assumptions and open questions:** very concise.
- **TLDR: what I need to know if I read nothing else.** (last, whole line in bold)

## Code smells
<!-- A5. Applies when: always. Needs ruff.toml, mypy.ini, and eslint.config.js (see assets/). -->

Ruff, mypy, and ESLint enforce the limits below (`ruff.toml`, `mypy.ini`, `eslint.config.js`).
Never weaken their configuration, and never add `noqa`, `type: ignore`, or `eslint-disable` to make
a change pass. Fix the code.

Two hooks run `scripts/check.py`. After each edit, ruff or ESLint fixes the file and reports what is
left: fix it before moving on. Before each commit, every check and test runs, and a failure
refuses the commit. Never bypass the hooks (`--no-verify`, `core.hooksPath`). Editing the check configs or
the hook files asks the user first; ask only to change a rule on purpose, never to pass a check.

- Each function, class, and module does one thing. If its name needs two verbs, or describing it
  needs "and", split it. Keep functions near 20 lines (15 statements), 4 parameters, and complexity
  8. When a file passes about 300 lines, check it for a second responsibility and split it only if
  you find one.
- Prefer composition to inheritance. Group values that always travel together into one typed
  object. Inject long-lived collaborators through the constructor, not through every call.
- Do not write: duplicated logic (search for a helper first; extract on the second use); dead code;
  abstractions or design patterns the task does not need; pass-through wrappers or classes too small
  to justify themselves (the single owner of an external system is not one); mutable global state.
- Write code a beginner-to-intermediate programmer can read. Prefer plain constructs to clever ones.

## Architecture and layers
<!-- A6. Applies when: always. -->

- `docs/design.md` defines the layers and their import rules. Follow them. Before writing code,
  name the module that owns the change. Before creating a module, state its name, layer, and single
  responsibility.
- One module per concern. Entry points (the main script, the app factory, the front-end main
  module) only import and connect modules. They hold no logic.
- Business logic is pure: no HTTP, UI, or database imports. Transport and UI layers only translate
  and delegate.
- Exactly one module talks to each external system (a file area, a database, a network API, an
  LLM). A module exposes only what others need and never reaches into another module's internals.
- Pass anything that touches an external system (repository, API client, file writer, LLM client)
  into the code that uses it, so tests can use fakes. Do not use a dependency-injection framework.
- Changing a layer, a module boundary, the data model, the public API, or the tech stack needs the
  user's approval and a `DEC-NNN` in `docs/design.md`.

## Directory structure
<!-- A7. Applies when: always. A host that needs files at the repo root (for example GitHub Pages) lists the exception in docs/design.md. -->

| Path | Holds |
| --- | --- |
| `src/` | All source code. `docs/design.md` has the detailed layout. |
| `tests/` | `unit/`, `e2e/`, and `e2e/ui/`. |
| `docs/` | `workflow.md`, `inbox.md`, `spec.md`, `design.md`, `plan.md`, and reference material. |
| `config/` | `.env` (never committed) and `.env.example` (committed). |
| `data/` | Input and runtime data. |
| `content/`, `site/` | Static site: Markdown source (authors edit only this) and generated output (committed, never edited by hand). |
| `models/`, `prompts/` | Downloaded model weights (never committed; path from config) and LLM prompt files. |
| `scripts/` | Setup, download, and maintenance scripts: `cleanup.py`, `download_models.py`, `download_assets.py`. |
| `.vscode/`, `.claude/` | Shared editor settings and Claude Code settings. |
| Root | `CLAUDE.md`, `README.md`, `requirements.txt`, `.gitignore`, `main.py` (Python entry point), `Dockerfile`, `compose.yaml`, `.dockerignore` (Docker), and the tool configs: `ruff.toml`, `mypy.ini`, `pytest.ini` (Python), `package.json`, `tsconfig.json`, `eslint.config.js` (JavaScript). |

- All source code lives under `src/`, except the entry point `main.py`. Create a folder only when
  the layout in `docs/design.md` lists it, and update the layout in the same change.
- Never edit a generated file by hand. Regenerate it with the script that makes it.
- `scripts/cleanup.py` removes caches and generated artifacts by name (for example `__pycache__`,
  tool caches, logs). It never deletes source, tests, docs, config, input data, or dependencies.

## Naming and code documentation
<!-- A8. Applies when: always. Name formats and docstring syntax are in the language sections. -->

- Name things for their purpose, not for how they look or are built. Use one term per concept.
- Every module, class, and function has a docstring. Tests are exempt: their names carry the
  requirement ID.
  - Module: what it does, what it does not do (and which module does), and the requirement or
    decision IDs it implements.
  - Class: its single responsibility, stated explicitly, and the state it owns, if any.
  - Public function: a summary, then parameters, return value, and errors raised. A private or
    trivial function gets a one-line summary.
- Comment only where the behavior is not obvious. Do not narrate the code.
- Leave no TODO comments. Report out-of-scope findings under "Assumptions and open questions".

## Configuration and constants
<!-- A9. Applies when: the project has configurable values. Secrets: see Security and privacy. -->

- Settings live in `config/.env`, which is never committed. `config/.env.example` is committed and
  lists every key: non-secret keys carry their default, secret keys are empty. `config.py` is the
  only module that reads `config/.env` or the environment. A real environment variable overrides
  `config/.env`.
- Only the entry point imports `config`. It passes values down as arguments, grouped into small
  typed settings objects per component. The code has no defaults: a missing or invalid value fails
  clearly at startup.
- Never write a behavior-affecting value inline: URLs, ports, file paths, model names, thresholds,
  limits, timeouts. They come from config.
- Fixed vocabularies (statuses, sources, error codes) are enums, or named immutable constants where
  the language has no enums, in the module that owns them. No other module-level constants.
- To add a setting, in the same change: (1) add the key to `config/.env.example` (its default, or
  empty if secret); (2) add it to `config/.env`; (3) add a typed field in `config.py`; (4) add a row
  to the settings table in `docs/design.md`; (5) pass the value in from the entry point.

## Dependencies
<!-- A10. Applies when: the project uses third-party libraries. Environment commands are in the language sections. -->

- Prefer the standard library. Ask before adding any dependency, and say why the standard library is
  not enough. Install only into the project's isolated environment, never into the global
  interpreter or a base environment.
- The dependency file (`requirements.txt`; `package.json` for JavaScript) is the only list. Add a
  library in the same change that first imports it, never import an unlisted library, and remove it
  when its last import goes.
- List direct dependencies only, pinned to the version installed when added (`==` in
  `requirements.txt`, exact versions in `package.json`). Do not use `pip freeze`. Use only APIs that
  exist in the pinned version.

## Testing
<!-- A11. Applies when: the project has automated tests. Test tools and naming syntax are in the language sections. Needs pytest.ini (see assets/). -->

- Every requirement ID has a test at the lowest level that proves it. Every new public function in
  the business-logic layer also has a unit test.
- Every user workflow (an event-driven requirement, `When <trigger>, ...`) has an end-to-end test
  through the outermost non-browser entry point (HTTP API, CLI, or service), with fakes at the
  external boundaries. The UI is AI-built and never read by the user, so every UI workflow
  requirement also gets one headless-browser test in `tests/e2e/ui/`. `docs/design.md` chooses the
  browser tool, and the user approves it under Dependencies.
- Layout: `tests/unit/` (logic with fakes, one test file per source module) and `tests/e2e/`.
  Requirement coverage is the primary measure. Line and branch coverage on `src/` has a floor of 80%.
- Test public behavior, not private implementation: one behavior per test, and every test asserts
  something. Tests are deterministic (seed randomness; no real clock, network, or sleeps; exact
  outputs). They use temporary folders and invented data, and never touch real config, data, or user
  files, or need a live LLM or external server.
- Never weaken or edit an existing test, baseline, or fixture to make it pass. Change one only when
  its requirement changed, and say so in the report.

## Error handling
<!-- A12. Applies when: always. Exception syntax is in the language sections. -->

- Catch an exception only at an external boundary (file system, network, database, LLM,
  subprocess), and only to add context (what was being done, on which resource) and re-raise with
  the original error attached. Never catch to recover, fall back, continue, or swallow. Ruff and
  ESLint block bare and blind catches.
- Do not catch unexpected errors. The top level shows the raw error and the full stack trace, logs
  it, and stops. No friendly message, no retry.
- Invalid user input is not an error. Handle it as Input validation says. Error messages name what
  failed and the resource (path, endpoint, ID), never secrets or user content.
- If other users can reach the app, `docs/design.md` records a `DEC-NNN` that shows a short message
  and logs the trace instead.

## Logging
<!-- A13. Applies when: the project runs as an app or service. -->

- Use the language's logging library for diagnostics. Ruff and ESLint block `print` and `console`;
  a CLI may print its intended user output.
- Configure logging once, in the entry point, from settings. The log level and the log file path
  come from config. Log to the console and the file. Write plain text, one line per event, with
  timestamp, level, and module name.
- Log startup (with the settings in use, secrets excluded), key events, and failures. Levels:
  `INFO` for startup and key events, `DEBUG` for payloads and raw external responses, `WARNING` for
  rejected input, `ERROR` for failures.
- Never log secrets. Log user content only at `DEBUG`. Log an error once, at the top level. Do not
  log and re-raise at a boundary.

## LLMs and prompts
<!-- A14. Applies when: the project calls an LLM. The LLM client module, model names in config, raw responses at DEBUG, and no live LLM in tests are covered in Architecture, Configuration, Logging, and Testing. -->

- A project uses one provider, chosen in `docs/design.md`. Build no provider switch unless the spec
  requires one.
- Prompts live in files under `prompts/`, never as strings in code, and their paths come from
  config. The model ID (exact, not a moving alias), base URL, models folder path, and sampling and
  token limits also come from config.
- Treat LLM output as untrusted input: parse and validate it against a schema. On failure raise an
  error that includes the raw output. Do not repair it and do not retry.
- The LLM only produces data. It never executes tools, runs code, or decides transport or server
  behavior. Code runs the tools.
- API-hosted model: data leaves the machine, so send only the fields the prompt needs.
  `docs/design.md` states which data goes to which provider.
- Local model: the base URL points at localhost. Fail clearly when the server is not running or the
  model is not pulled. Download models only with `scripts/download_models.py`, never at run time.
  At run time the app is offline, with telemetry off. Weights live in `models/` and are never
  committed.

## Git and destructive actions
<!-- A15. Applies when: always. Commit and push timing is in docs/workflow.md. Needs .claude/settings.json (see assets/). -->

- Work on `main` unless told otherwise. Never commit `config/.env`, secrets, user data, model
  weights, exports, logs, or caches. Before the first commit, check that `.gitignore` covers them.
- `.claude/settings.json` blocks force-push, `reset --hard`, `git clean`, `git restore`, and Docker
  volume deletion. It asks before recursive deletes, installs, killing processes, and edits to the
  spec, `CLAUDE.md`, or the settings. Never work around a block with a different command.
- Delete recursively only a scratch folder you made in this milestone, and clear caches with
  `scripts/cleanup.py`. Never touch files outside this repo (except scratch folders you make and
  delete), the paths listed as protected under Project rules, or another program's process.
- If a task needs a forbidden action, or an approval you cannot get now (a new dependency, an
  architecture change, a spec change), stop that milestone. Write the reason and the exact question
  to `.claude/blocked.md`, and ask in chat if the user is present. The file is never committed. The
  user clears it.

## Security and privacy
<!-- A16. Applies when: always. -->

- Secrets (API keys, tokens, passwords, database IDs) live only in `config/.env` or the platform's
  secret store. They never appear in code, committed files, logs, error messages, reports, or
  browser-side code.
- User data stays on the machine. A flow of user data to an external service (an LLM API, Notion, a
  cloud store) must be listed in `docs/design.md` as a `DEC-NNN` and approved by the user. Servers
  listen on `127.0.0.1` unless the design says otherwise. Telemetry is off. At run time the app
  calls only the services the design lists.
- Never run, test, or debug against the user's real data. Copy it to a scratch folder, point the
  process at the copy through environment variables of that process only, and delete the copy
  afterwards. Reports give counts, never content. Never put real personal data in source, fixtures,
  or docs. Use invented data.

## Living docs
<!-- A17. Applies when: always. -->

- Update every doc a change makes inaccurate in the same change, and be specific: "Added
  `domain/review.py`: computes Needs Review", not "updated code". Each doc owns one kind of fact.
  Link to the owner; do not copy.

  | Change | Update |
  | --- | --- |
  | Behavior or a requirement | `docs/spec.md`, with the user's approval |
  | Architecture, data model, settings, directory layout, rules, thresholds | `docs/design.md` |
  | Setup, how to run, user-visible changes | `README.md` |
  | A library added or removed | `requirements.txt`, in the same change as the import |
  | New generated files, caches, secrets | `.gitignore` |

- `README.md` always has: What it does, Stack (with versions), File structure (top-level folders,
  one line each), Setup, How to run, How to test. Setup explains how to install dependencies,
  configure `config/.env`, and set up and check every external dependency (the LLM server, models,
  API keys) before the first run.
- Never edit `CLAUDE.md` without the user's approval. When a fact in it goes stale (stack, test
  command, run command) or a rule needs to change, flag it, propose the exact change, and edit only
  after approval.

## Long-running work
<!-- A18. Applies when: the project has tasks that can run long (network or LLM calls, large files, pipelines). -->

- Long-running work never blocks the UI or the request path. Use async I/O for waits, and keep
  blocking or CPU-heavy work off the main loop.
- Python: `async def` and `await` for I/O at the boundaries (API handlers, LLM and network
  clients). Pure business logic stays synchronous. Ruff flags blocking calls inside `async def`;
  run them with `asyncio.to_thread`. Async tests use `pytest-asyncio`.
- JavaScript: `async`/`await` with `fetch`. Move heavy computation to a Web Worker. Never freeze the
  main thread.
- An API request that can run long starts the task and returns `202` with a job ID at once. The
  task runs in the background as an async task. `GET /api/jobs/<id>` reports status and progress,
  and the UI polls it. One object created in `main.py` holds the job state.

## Input validation
<!-- A19. Applies when: the project accepts user input (forms, API requests, command-line arguments, uploaded files). -->

- Every user input passes through a validation component (a class or module) at the boundary,
  before any logic uses it. The validation rules live only there, never in handlers, views, or
  business logic.
- The component checks type, required fields, length or range, format, and allowed values. It
  reports every problem at once, naming the field and the rule, never the rejected value. Valid
  input leaves as a typed object. Invalid input is rejected with a clear message about what to fix;
  it is not an error.
- The server-side component is the authority. The browser may give fast feedback with native HTML
  constraint attributes (`required`, `type`, `min`, `max`, `pattern`), and a small validation-view
  module in JavaScript shows the server's field errors next to the fields. It does not copy the
  rules.
- Python: a Pydantic model for API bodies and a validator class for other inputs. Each rule has a
  test.

## Python
<!-- B1. Applies when: the project uses Python. Needs ruff.toml, mypy.ini, and pytest.ini (see assets/). -->

- Ruff (`ruff.toml`) and mypy (`mypy.ini`) enforce naming, type annotations, Google-style
  docstrings, absolute imports at the top of the file, `pathlib`, explicit file encodings,
  `raise ... from err`, and no `print`. Fix findings and never weaken the configuration.
- Test files are `test_<module>.py`. Test functions are `test_<requirement id>_<behavior>`, for
  example `test_tri_024_unsure_duplicate_creates_item`.
- Annotate every parameter, return value, and class attribute, using built-in generics and `|`. No
  `Any` unless a library forces it; then add a comment saying why.
- Use dataclasses for typed records. Settings are frozen dataclasses. Use f-strings, and `with` for
  resources. Do not write your own decorators, metaclasses, context managers, or descriptors.
  Library decorators such as `@dataclass` and `@pytest.fixture` are fine. Prefix internal names with
  `_`. Every folder under `src/` has an `__init__.py`, and imports read
  `from src.<module> import <name>`.
- A module may define `logger = logging.getLogger(__name__)`. It is the only module-level object
  besides enums.
- `main.py` at the repo root is the entry point. It loads config, sets up logging, creates the
  objects, and starts the app. It holds no logic. `config.py` loads `config/.env` with
  `python-dotenv`.
- Use the project's conda environment (its name and Python version are in the README Stack). Conda
  supplies Python only. Install packages with `pip install -r requirements.txt`, never
  `conda install`.
- Checks. Run all of them and fix every failure: `mypy src`, `ruff check .`,
  `ruff format --check .`, and `python -m pytest --cov=src --cov-branch --cov-fail-under=80`.
  `python scripts/check.py` runs all of them.
  `requirements.txt` lists `pytest`, `pytest-cov`, `mypy`, `ruff`, and `python-dotenv`, plus
  `pytest-asyncio` for async code.

## JavaScript and TypeScript
<!-- B2. Applies when: the project has JavaScript or TypeScript. Needs package.json, tsconfig.json, and eslint.config.js (see assets/). -->

- No front-end framework (React, Vue, Angular, and the like) and no UI library, unless
  `docs/design.md` chooses one. HTML, CSS, and JavaScript stay in separate files.
- Plain JavaScript as ES modules, typed with JSDoc and checked by the TypeScript compiler
  (`tsconfig.json` sets `checkJs` and `strict`). Start every file with `// @ts-check`. Write
  TypeScript source only if `docs/design.md` chooses a build toolchain. Write no `any`. The runtime
  has no dependencies and no build step. A dev-only `package.json` holds the check tools. Unit tests
  use `node --test`.
- ESLint (`eslint.config.js`) and `tsc` enforce the 20-line, 4-parameter, and complexity limits, the
  300-line file warning, typed parameters, `fetch` only in `api.js`, `console` only in `log.js`, no
  module-level `let`, and no `innerHTML`. Fix findings and never weaken the configuration.
- Naming: `kebab-case` files, `camelCase` functions and variables, `PascalCase` classes. Every
  function has JSDoc with `@param {Type}` and `@returns {Type}`, even when it is not exported.
  Describe a shared object shape once with `@typedef`. Every module starts with an `@module` block.
- Structure mirrors the Architecture rules. `main.js` only imports and connects modules. Logic
  modules (no DOM, no `fetch`) stay apart from view modules (each owns its own DOM) and `api.js`.
  Export only the public API. Modules talk through function calls or custom events, never by
  reaching into another module's DOM or state. Pass collaborators (the api module, storage, the
  clock) into the functions that use them, so tests can use fakes. Create state in `main.js` and
  pass it in.
- Behavior-affecting values (URLs, timeouts, limits) live in one `config.js` that exports a frozen
  object. Fixed vocabularies are frozen objects in the module that owns them.
- Errors: `try/catch` only in `api.js`, adding context and rethrowing with
  `new Error(message, { cause })`. Unexpected errors reach a top-level handler in `main.js` (the
  `error` and `unhandledrejection` events) that shows the raw error and stack trace on screen and
  logs it. One `log.js` wraps `console` with levels from config.
- JavaScript holds behavior only: no HTML markup strings and no styles. Clone `<template>` elements
  from the HTML or use `createElement`, and toggle CSS classes. Insert dynamic text with
  `textContent`. Never keep app data in `localStorage` or `sessionStorage`; the API is the only
  source of data. UI preferences may use `localStorage`.
- Checks. Run all of them and fix every failure: `npm run typecheck`, `npm run lint`, `npm test`,
  and the headless-browser tests (the command is in the README under How to test).
- The UI is built and maintained entirely by AI. Report front-end changes by their behavior in plain
  language, and prove correctness with the checks.

## HTML and CSS
<!-- B3. Applies when: the project has a browser front end. -->

- Stylelint (`.stylelintrc.json`) checks the CSS and Prettier (`.prettierrc.json`) formats the
  JavaScript, CSS, and HTML (`npm run lint:css`, `npm run format:check`). Fix findings and never
  weaken the configuration.
- Use semantic elements (`header`, `main`, `nav`, `aside`, `article`, `section`, `footer`). Every
  page has a clear `<title>` and one main heading.
- No `style=""` attributes and no `<style>` blocks. Pass computed values to CSS through custom
  properties set from JavaScript.
- No `onclick=""` or other inline handlers, and no `<script>` blocks, except the module entry in
  `index.html`. Attach behavior in JavaScript, using event delegation with `data-` attributes.
- HTML holds structure only. Markup that JavaScript needs lives in `<template>` elements in the
  HTML, not in JavaScript strings.
- Nothing loads from the network: no CDN, no Google Fonts. Store third-party files in the repo. A
  required external script is listed in `docs/design.md`.
- Colors, spacing, and fonts come only from custom properties in `theme.css`. Never write a color
  value in any other file.
- Keep shared sheets (`theme.css`, base, layout) and add one sheet per view or component only for
  styles specific to it. Every CSS file starts with a header comment that says what it styles and
  what it does not.
- Name CSS classes with BEM, `block__element--modifier`, and by purpose, not appearance
  (`sidebar__toggle`, not `blue-box`).
- Avoid duplicate rules, unused classes, excessive specificity, and layout hacks.
- Use meaningful link text and `alt` text on images. Keep text contrast readable. Do not rely on
  color alone to convey meaning.
- Mockups in `docs/` are a visual reference, not code to copy.

## UI design
<!-- B3a. Applies when: the project has a user interface. -->

- Quick: no unnecessary scripts, fonts, or images. Every action gives immediate feedback, and slow
  work shows a loading state.
- Responsive: the layout adapts from phone to wide desktop widths without horizontal scrolling, and
  content keeps a readable width on large screens.
- Minimal and uncluttered: show only what the current task needs, with one primary action per view,
  few colors, and generous whitespace. No decorative effects and no complex animation.
- Standard layout: header, navigation, main content, and footer, in the usual places. Use native
  HTML controls (`button`, `a`, `input`, `select`) instead of custom widgets.
- Every button and icon control has hover text (`title`) that explains what it does. Hover is not
  the only explanation: an icon-only control also has an `aria-label`, because touch screens have no
  hover.
- Prefer the system font stack. Add a custom font or an image only when `docs/design.md` requires
  it. Download it with `scripts/download_assets.py` into `src/assets/fonts/` or
  `src/assets/images/`, and commit the files. Never link to a font or an image online. The script
  records each source URL and license, and only assets whose license allows redistribution are used.

## HTTP APIs
<!-- B4. Applies when: the project exposes an HTTP API. -->

- Use FastAPI. Handlers are `async def`. The server serves the front end as static files and exposes
  a JSON API. No server-side HTML templating.
- A route handler calls one service function and returns the response. It holds no business logic.
  One router per domain.
- API paths are `kebab-case` plural nouns under `/api/`, for example `/api/triage-options`. Use GET
  to read, POST to create, PATCH to update, and DELETE to delete. A `/health` endpoint reports
  liveness.
- A Pydantic model validates every request body (see Input validation). Invalid input returns
  FastAPI's standard 422 `detail`, one entry per problem. Use 404 for a missing record and 409 for a
  conflict, both with a `detail` message.
- Authentication goes through one shared dependency or decorator, used by every protected endpoint.
  `docs/design.md` lists the public endpoints.
- Allowed CORS origins come from config. The default is none.
- End-to-end tests call the API through the framework's test client against temporary data. They do
  not start a server.

## Data and storage
<!-- B5. Applies when: the project reads or writes data files or a data store. -->

- `data/` holds input and runtime data. Code never lives in `data/`, and data never lives in `src/`.
- Raw input is read-only. Never modify or overwrite an input file. Generated output goes to a
  separate folder under `data/`, and a script can regenerate it. Caches are disposable.
- Exactly one module reads and writes each data store or file format. It parses and validates at
  that boundary and hands typed objects to the rest of the code. No other module parses raw fields.
- The data folder and file paths come from config. Tests use temporary folders.
- Document the data model in `docs/design.md`, and update it in the same change that changes the
  data.
- Use UUID strings for IDs and ISO 8601 UTC strings for timestamps.
- Before a change rewrites stored data in place (a migration, an import), copy the data to
  `<name>.before-<change>`. Never delete these backups.

## CLI apps
<!-- B6. Applies when: the project has a command-line interface. -->

- Parse arguments with `argparse` in `main.py`, then dispatch to functions. Each flag and step is
  documented in the README under How to run.
- Print only the intended user output (results and progress). Diagnostics go to the logger. A
  progress counter may rewrite one line with `\r` and show counts only.
- Exit with code 0 on success and a non-zero code on failure. Unexpected errors follow Error
  handling.

## Static-site builds (Node)
<!-- B7. Applies when: the project generates a static site from Markdown. -->

- Markdown in `content/` is the source of truth. Authors edit only `content/`.
- `site/` is generated output, committed for hosting. Never edit it by hand. Regenerate it with
  `node scripts/build-site.js`. The hand-written template, CSS, and JavaScript live in `src/`, and
  the build copies them into `site/`.
- The build script generates every page from one reusable template. It builds the navigation from
  the content (never hardcoded links), uses relative links only, and names each output file after
  the content file's slug.
- The build fails clearly when required metadata is missing, and it skips drafts.
- `marked` is a build-time dependency only. The generated site has no runtime dependency and renders
  no Markdown in the browser.
- The site works without JavaScript for basic reading and navigation.
- Static files only: no server-side routing, and no environment variables or secrets in browser
  code.
- The README explains how to add content, build, preview locally, and publish.

## MCP servers and hosts
<!-- B8. Applies when: the project is an MCP server or an MCP host. -->

- Use the official MCP Python SDK. A server exposes tools over MCP, never through ad-hoc REST. A
  host calls tools through an MCP client, never through custom endpoints.
- Transport: Streamable HTTP on `127.0.0.1`. Use stdio only when the client launches the server
  itself. Do not use SSE. The server URL and port come from config.
- Each tool has a typed input schema and a typed result. Tool behavior is deterministic: no LLM
  inside a server.
- A host checks that the target tool exists, and handles connection and tool-call failures with
  explicit errors. The model never executes a tool. The MCP client does (see LLMs and prompts).
- The MCP client and server calls are async (see Long-running work).
- End-to-end tests cover server startup, session initialization, tool discovery, tool invocation,
  and the side effects of each call.

## Docker
<!-- B9. Applies when: the project uses Docker. -->

- Docker runs the services the app depends on (a database, a vector store) and is used for
  deployment. During development the app runs from its conda environment.
- `.claude/settings.json` blocks `docker compose down -v` and volume and system prunes. Docker
  volumes are protected data. Never work around the block.
- Published ports bind to `127.0.0.1`, for example `127.0.0.1:8000:8000`. Pin the base image tag;
  never use `latest`. Turn off telemetry in containers (for example `DISABLE_TELEMETRY=true`).
- Never bake secrets or data into an image. They arrive at run time through environment variables
  and mounted volumes. `.dockerignore` excludes `.env`, `data/`, `models/`, and `.git`.
