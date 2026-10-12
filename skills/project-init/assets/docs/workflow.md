# Workflow

The same in every project. Project-specific rules are in `CLAUDE.md`.

## The files

| File | Role | Who edits |
| --- | --- | --- |
| `docs/inbox.md` | Raw ideas, issues, questions, in the user's words | User |
| `docs/spec.md` | What to build: requirements with IDs | AI, with user approval |
| `docs/design.md` | How to build it: architecture, data, rules, decisions | AI |
| `docs/plan.md` | What is left: only unfinished milestones, with their questions and approvals | AI; the user adds approvals |

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
5. **Blocked.** If a milestone needs something it may not do on its own (a spec change, a user decision, a new dependency, an action `CLAUDE.md` forbids), stop it. In `plan.md`, set its Status to `blocked` and add a **Blocked** entry to its block (template below). Leave every other file as it was, commit `plan.md` alone with the message `M<n>: blocked`, and push. Ask in chat too if the user is present.
6. **Approval.** The user answers in the milestone's block: an **Approval** entry with the decision, and Status `approved`. Then the user commits `plan.md` and the milestone runs again. The approval permits exactly what it says, even an action the rules otherwise forbid (such as editing a spec row), and nothing more. To refuse, the user rewrites or deletes the milestone instead.

## Rules

- Never edit `spec.md` without the user's approval, given in chat or in an **Approval** entry.
- If the spec and the design disagree, the spec wins: stop and ask.
- Stay in scope. When in doubt, ask; do not fill gaps silently.
- Never report tests as passed unless they ran. Show failing output.

## Running milestones unattended

`python scripts/milestones-runner.py [--start N] [--end N]`, run by the user from a terminal with
the project's conda environment active, works through the table in order. Each milestone runs in
its own `claude -p` session with the model and effort of its row, following steps 4 to 6. The
runner stops at a `blocked` row, at a milestone that becomes blocked (and prints its question), or
at one that did not finish (its row is still in the table, git is not clean, or a commit was not
pushed). After you approve and commit, run it again: it continues with the approved milestone.
Logs and timings go to `.claude/logs/`. It needs a clean git tree and a branch that pushes to a
remote.

## Milestone templates

A row of the table "Milestones at a glance". Model: `haiku`, `sonnet` or `opus`. Effort: `low`,
`medium`, `high`, `xhigh` or `max`. Status: `open`, then `blocked` and `approved` if it needs the
user (steps 5 and 6).

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

The entries a blocked milestone adds to the end of its block: **Blocked** by the AI (step 5), then
**Approval** by the user (step 6).

```markdown
- **Blocked:** <One sentence: what the milestone needs, and why it may not do it.>
  - <Each fact behind the stop, with its source: a spec row, a plan block, a rule, file and line.>
  - Nothing else was changed. To continue, approve one of these:
    1. <The narrowest permission that lets the milestone go on.>
    2. <Another way, if there is one.>
- **Approval:** <The user's decision, in the user's words.>
```
