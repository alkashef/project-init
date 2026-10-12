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
3. **Plan.** The AI turns the spec and design changes into milestones in `plan.md` (template below). Number them from the counter at the top of `plan.md`, then advance the counter.
4. **Execute.** Work one milestone at a time, in order:
   1. Write the tests. Name each after the spec ID it verifies.
   2. Run them; the new tests must fail.
   3. Implement the smallest change that passes.
   4. Run the tests and the checks named in `CLAUDE.md` (type check, lint). If any fail, go back to step 3.
   5. Update docs the change made inaccurate (README, design).
   6. Delete the milestone block from `plan.md`.
   7. Commit only the files this milestone changed, with the message `M<n>: <title>`, then push. Do not start the next milestone until the push succeeds.

## Rules

- Never edit `spec.md` without the user's approval.
- If the spec and the design disagree, the spec wins: stop and ask.
- Stay in scope. When in doubt, ask; do not fill gaps silently.
- Never report tests as passed unless they ran. Show failing output.

## Milestone template

```markdown
### M<n> — <title>

- **Run with:** <model> · <effort>.
- **Refs:** <spec IDs>, <design sections>.
- **Owner:** <module or file that owns the change>.
- **Tests first:** <test names, one per spec ID>.
- **Build:** <the smallest change that passes them>.
- **Gate:** <what must be true before commit>.
```
