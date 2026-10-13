---
name: write-plan
description: Turn an approved spec and design into the milestone plan in docs/plan.md. A table at the top shows each milestone with its model, effort and status; a block per milestone gives its tests and how to build it. Use after the design is approved, or to add milestones when the spec or design changes. Do not use for requirements, architecture, or coding.
---

# Write Plan

Turn the approved spec and design into milestones that are built one at a time, in order. Write the
plan only. Do not write code, install dependencies, or start a milestone.

## Establish the baseline

- Read project instructions, `docs/workflow.md`, `docs/spec.md`, `docs/design.md`, and the current
  `docs/plan.md`. Read existing code, manifests, and tests when they exist.
- `docs/workflow.md` owns the row template, the block template, and the allowed model, effort, and
  status values. Follow it. Do not copy it into the plan.
- Check that the spec and the design are approved. If the spec says `Status: Draft` or the design
  has no approval, stop. Name the missing step: `/write-spec` or `/write-design`.
- Read [the milestone guide](references/milestone-guide.md) before cutting milestones.
- Number new milestones from the counter at the top of `plan.md`. Never renumber or reuse a number.

## Cut the milestones

1. List the requirements in `spec.md` and the decisions in `design.md` that the plan must deliver.
2. Cut thin slices. Each milestone delivers behavior that tests can prove, and fits one unattended
   session. Order them by dependency: foundations first.
3. Check coverage. Every requirement ID belongs to at least one milestone. List any that does not,
   and say why.
4. Write one block per milestone, in the workflow's template:
   - **Refs:** the spec IDs and the `DEC-NNN` it implements.
   - **Owner:** the module or file that owns the change.
   - **Tests first:** one test name per spec ID. Name each test after the ID it verifies.
   - **Build:** the smallest change that passes the tests, in terms the design already fixed.
   - **Gate:** what must be true before the commit.
5. Do not add a requirement, a decision, or a dependency that the spec and design do not have. If the
   plan needs one, stop and propose the spec or design change for approval.

## Choose the model and effort

Propose a model and an effort for each milestone, using the guide. The user may change any of them.
Use the aliases `haiku`, `sonnet`, and `opus` by default. Each alias means the latest model of that
family at the time of the run. Use a full model ID, for example `claude-sonnet-5-5`, only when the
user asks to pin a version.

## Show the table, then write the file

1. Show the milestones table in chat first: milestone, description, model, effort, status. Add a
   line for each uncovered requirement. Ask for the user's approval or changes.
2. After approval, write the rows under "Milestones at a glance" and the blocks under "Milestones".
   Set every Status to `open`. Advance the counter at the top.
3. Keep the table at the top of the file, directly under the counter, so the user sees every
   milestone and its status at a glance. The milestone runner reads this table: keep its columns and
   heading exactly.

## Update an existing plan

- Add new milestones after the last one. Do not renumber.
- Do not edit a milestone whose Status is `blocked` or `approved`, or any **Blocked** or **Approval**
  entry. If the change affects one, tell the user.
- For an `open` milestone that the new spec or design changes, show the proposed edit before making
  it.
- A finished milestone is not in the plan: its row and block are deleted in its commit.

## Finish

Check that every row has a block, every block has a row, every number is unique, and every ID in
Refs exists in the spec or the design. Report the milestones and any requirement left uncovered.
Tell the user the next step: run `python scripts/milestones-runner.py`, or ask Claude to work the
first milestone. Stop there.
