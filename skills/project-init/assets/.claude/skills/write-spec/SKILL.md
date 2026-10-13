---
name: write-spec
description: >-
  Interview users to build or revise a software requirements specification from
  their business goals and tasks. Use for vague app ideas, requirements
  discovery, user interviews, specification gaps, or requests to build a spec.
  Use usage-centered elicitation, one question at a time, EARS syntax, stable
  requirement IDs, and concrete acceptance examples. Preserve existing approved
  requirements. Do not use for implementation, architecture, or a clear small fix.
---

# Write Spec

Build the spec from the work users need to accomplish. Connect required behavior
to business goals, evidence, and expected results. Keep design and implementation
outside this skill.

Use the approach described by Karl Wiegers and Joy Beatty. Apply the adaptations
in [the interview guide](references/interview-guide.md). Read that guide before
the first interview. Read [the EARS guide](references/ears-guide.md) when writing
requirements. Use [the spec template](assets/spec-template.md) only when the
project has no existing spec format.

## Start from the available context

1. Read the request, prior answers, and relevant supplied documents.
2. Read project instructions and the existing spec, workflow, and glossary.
3. Identify whether this is a new spec, a resumed interview, or a proposed amendment.
4. Use the existing spec path. Otherwise, use `docs/spec.md` in the stated project.
5. If no project or destination is known, interview in chat. Resolve the destination before saving.

Use files and observation to establish facts. Reserve user questions for intent,
priorities, domain rules, trade-offs, and facts the available evidence cannot establish.
Do not inspect unrelated user data. Request a relevant, redacted example when needed.

Preserve the project's ID convention, EARS syntax, and approval rules. For an
approved spec, propose a requirement change before applying it. Do not treat
permission to draft a spec as approval of its requirements.

## Run an adaptive interview

Ask one focused question per message, then wait. Use plain language and the user's
terms. Start from the largest uncertainty that could change the scope or acceptance
criteria. Skip questions that the context already answers.

Prefer open questions for discovery. Offer choices when the user needs help with
a concrete decision. Label a proposed answer as a recommendation. Do not attach
a guessed answer to every question or steer toward a conventional feature list.

Work through the following concerns as they become relevant. Do not recite them
as a questionnaire or require every concern for every app.

### Business purpose and scope

Establish the problem, affected people, current workaround, and desired improvement.
Distinguish the operator, beneficiary, buyer, and approver when their needs differ.
Identify the smallest useful scope, exclusions, constraints, and evidence of success.
Confirm the purpose before exploring detailed features.

### User tasks and scenarios

Identify what each relevant user needs to accomplish. Reconstruct a specific recent
instance when possible. Capture the trigger, starting conditions, actions, information,
decisions, other people or systems, and observable result.

Distinguish current behavior from desired behavior. A legacy process is evidence
about today's work. It is not automatically a requirement for the new app.
Use the scenarios to derive required behavior. Do not ask the user to choose
programming languages, databases, or frameworks unless a binding constraint requires it.

### Rules, exceptions, and data

Explore alternative success paths and consequential failures. Ask what should happen
for invalid or missing input, duplicates, conflicting changes, unavailable dependencies,
and interrupted work when relevant. Establish the responsible role and expected result.

Clarify domain terms, data relationships, ownership, validation, retention, and permissions.
Record the required effect of a failure. Leave its technical mechanism to design.

### Measurable quality needs

Explore performance, reliability, recovery, privacy, security, usability, accessibility,
compatibility, and operational constraints when relevant. Tie each target to a user
task, workload, or business constraint. Never invent a threshold to replace an adjective.
Treat an unknown target as an open question with a way to resolve it.

### Acceptance examples and confirmation

For each consequential rule, capture a concrete input or situation and its expected result.
Include a representative success case and a relevant exception or boundary case.
Ask the user or appropriate domain owner to review the expected results.

Restate a small, coherent part when enough evidence exists. Ask what is wrong or missing.
Record corrections and continue from unresolved concerns. Do not restart settled discussion.

## Build the spec incrementally

Write only within the authorized destination and approval scope. Keep a working draft
current so the interview can resume. Label it `Draft` until the applicable approval occurs.
Store open questions and material assumptions in that same spec. Do not create another
requirements document or copy requirements into the design or plan.

For each requirement:

- Write one required behavior in EARS syntax, with a stable ID and a priority.
- State its business reason and identify its source or supporting evidence.
- Link the relevant scenario and acceptance examples by ID.
- Distinguish a confirmed requirement from an inference or proposed requirement.

Separate business outcomes from software acceptance. A response-time test can establish
latency. It cannot establish that the app improves business decisions.
Record how the business outcome will be evaluated after use, when relevant.

Reuse the project's ID convention. If none exists, use `AREA-NNN` and `NFR-NNN`.
Allocate after the highest number previously used in the relevant namespace.
Keep an ID when its requirement changes. Mark retired requirements `Withdrawn`.
Never renumber, recycle IDs, or delete withdrawn requirements to close numbering gaps.
Use `SCN-NNN` for scenarios and `EX-NNN` for examples if no convention exists.

For amendments, show the proposed delta and its impact on existing scenarios and requirements.
Apply the delta only under the project's approval rules. Flag downstream design or test
impacts without changing those artifacts as part of this interview.

## Review and finish

Review substance before wording:

- Trace each requirement to a user task, business rule, quality need, or binding constraint.
- Check that scenarios cover the agreed scope, including relevant roles and failure paths.
- Check terminology, consistency, unique IDs, and unresolved conflicts.
- Check that acceptance examples have domain-reviewed expected results.
- Identify material unknowns that would change scope, behavior, or acceptance.

Resolve material unknowns or explicitly defer them with an owner and a revisit condition.
Do not describe a deferred question as answered. Identify what it blocks.

Stop the interview when the next stage has enough confirmed information and no
unresolved decision would materially change it. Do not use a numerical confidence
score, fixed question quota, or the presence of template headings as the completion test.

Present the spec for human review, with its main decisions and remaining open items.
Record approval only when the user gives it for the actual contents. Do not repeat
confirmation requests for decisions already approved. Report a draft honestly if approval
is absent. Do not start architecture, planning, coding, or dependency installation.
After approval, tell the user the next step is `/write-design`.
