# Workflow

The same in every project. Project-specific rules are in `CLAUDE.md`.

## The files

| File | Role | Who edits |
| --- | --- | --- |
| `docs/inbox.md` | Raw ideas, issues, questions, in the user's words | User |
| `docs/spec.md` | What to build: requirements with IDs | AI, with user approval |
| `docs/design.md` | How to build it: architecture, data, rules, decisions | AI |
| `docs/plan.md` | What is left: only unfinished milestones | AI |

Each fact lives in one file. Finished work is recorded by git history, not by the docs.

## The loop

1. **Inbox.** The user adds a line to `inbox.md`. No format is needed.
2. **Spec and design.** On request, the AI goes through the inbox with the user and asks only what it cannot decide. It proposes spec changes; the user approves them. Then it updates `design.md`. A line leaves the inbox once it is in the spec or dropped.
3. **Plan.** The AI turns the spec and design changes into milestones in `plan.md`: for each, a row in the table "Milestones at a glance" and a block under "Milestones" (templates below). Number them from the counter at the top of `plan.md`, then advance the counter.
4. **Execute.** Work one milestone at a time, in order:
   1. Write the tests. Name each after the spec ID it verifies.
   2. Run them; the new tests must fail.
   3. Implement the smallest change that passes.
   4. Run the tests and the checks named in `CLAUDE.md` (type check, lint). If any fail, go back to step 3.
   5. Update docs the change made inaccurate (README, design).
   6. Delete the milestone's row and block from `plan.md`.
   7. Commit only the files this milestone changed, with the message `M<n>: <title>`, then push. Do not start the next milestone until the push succeeds.

## Rules

- Never edit `spec.md` without the user's approval.
- If the spec and the design disagree, the spec wins: stop and ask.
- Stay in scope. When in doubt, ask; do not fill gaps silently.
- Never report tests as passed unless they ran. Show failing output.

## Running milestones unattended

`python scripts/milestones-runner.py [--start N] [--end N]`, run by the user from a terminal with
the project's conda environment active, works through the table in order. Each milestone runs in
its own `claude -p` session with the model and effort of its row, following step 4. The runner
stops at the first milestone that did not finish (its row is still in the table, git is not clean,
or a commit was not pushed) or that wrote `.claude/blocked.md`. Logs and timings go to
`.claude/logs/`. It needs a clean git tree and a branch that pushes to a remote.

## Milestone templates

A row of the table "Milestones at a glance". Model: `haiku`, `sonnet` or `opus`. Effort: `low`,
`medium`, `high`, `xhigh` or `max`. Status: `open`.

```markdown
| **M<n>** <title> | <one line: what it delivers> | <model> | <effort> | open |
```

A block under "Milestones":

```markdown
### M<n> — <title>

- **Refs:** <spec IDs>, <design sections>.
- **Owner:** <module or file that owns the change>.
- **Tests first:** <test names, one per spec ID>.
- **Build:** <the smallest change that passes them>.
- **Gate:** <what must be true before commit>.
```
