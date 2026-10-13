---
name: write-design
description: Turn an approved software spec into a practical technical design through a lightweight adaptation of Attribute-Driven Design 3.0. Use for architecture, technology stack selection, design reviews, or changes to docs/design.md in a Spec, Design, Plan workflow. Recommend languages, frameworks, and major libraries. Preserve requirement IDs and stable DEC IDs. Support users without programming experience through one question at a time. Do not use for initial requirements discovery, visual styling alone, implementation planning, or coding.
---

# Write Design

Build a design that explains how the approved requirements will work. Apply ADD 3.0 with depth proportional to technical risk.
Treat this as an adaptation of ADD, not the official method or a guarantee of technical quality.

## Establish the baseline

- Read project instructions, applicable rules, `docs/workflow.md`, `docs/spec.md`, and the current `docs/design.md`.
- Read existing code, manifests, and tests when available. Distinguish an implemented fact from a proposed design.
- Use the project's paths and conventions. Default to `docs/design.md` when none exist.
- Identify whether the request creates, resumes, reviews, or amends a design. Preserve unrelated decisions and user edits.
- Confirm approval from the available record or the user's instruction. If the spec is unapproved, analyze it provisionally and resolve approval before finalizing design.
- If requirements are absent, ask for the spec or use `/write-spec` first. Do not invent business behavior to make architecture possible.

Read [the design guide](references/design-guide.md) when choosing drivers, boundaries, or validation methods.
Read [the technology guide](references/technology-guide.md) before recommending a stack or new dependency.
Use [the design template](assets/design-template.md) only for a new document. Preserve an existing format.

## Keep each fact in its proper file

Keep requirements and EARS statements in `spec.md`. Cite their IDs in design instead of copying their text.
Keep architecture, technical rules, data structures, interfaces, settings, and decisions in `design.md`.
Keep milestones, task order, and implementation approvals in `plan.md` under the local workflow.
Keep installed direct dependencies and exact pins in the existing dependency files. Do not duplicate the installed inventory in design.

When a design requires a changed requirement, propose the exact spec change for approval. Do not silently edit the spec.
Treat the spec as authoritative when design and spec conflict. Analyze unaffected parts while the conflict awaits resolution.
Follow local rules for an active blocked milestone. Do not start a milestone or create a plan merely to finish design.

## Select the drivers

Find the requirements and constraints that most affect structure or technology. Cite existing IDs and the source of project constraints.
Consider critical workflows, data ownership, performance, availability, security, privacy, deployment, cost, and maintainability only where relevant.
Use measurable quality scenarios from the spec. If a missing target could change the design, ask one business question to resolve it.
Do not invent traffic volumes, uptime targets, budgets, retention periods, or regulatory obligations.
Label estimates and assumptions. Record who must resolve each material unknown and whether it blocks design or later implementation.

## Develop the design

For each major design issue, apply this cycle internally:

1. Select the driver or risk to address.
2. Compare the recommended approach with a meaningful feasible alternative.
3. Define responsibilities, data ownership, interfaces, and allowed dependencies.
4. Walk a critical workflow and its failure paths through the design.
5. Assess the result against the driver and identify the remaining uncertainty.

Repeat only where another decision or unresolved risk warrants more detail. Avoid alternatives for trivial choices.
Prefer the smallest structure that satisfies the drivers and project rules. Add distributed services, queues, or abstraction layers only with a concrete reason.
In an existing project, examine the cost of reuse, migration, and operating both designs before proposing a replacement.
Record enough detail for separate implementation sessions to make consistent choices. Do not specify every private function.

## Work with the user

Infer expertise from the conversation. Ask at most one question per message and give one procedural step at a time.
Explain consequences in business terms. Recommend the technical choice yourself rather than asking a non-programmer to choose a library by name.
Ask only for facts, priorities, permissions, or trade-offs that the available evidence cannot resolve.
For a consequential choice, state the recommendation, relevant alternatives, business effect, and the exact decision needed.
Do not ask for approval again when the user already approved that choice and scope.
Distinguish business approval from technical review. Identify the specific decision that needs an experienced software reviewer when the evidence exceeds your ability to assess it.
Do not require a technical reviewer for every routine choice or claim that an AI review proves correctness.

## Write the design

Preserve the project's headings. For project-init, retain Decisions, Architecture, Data model, and Interfaces.
Add compact subsections for drivers, technology choices, important flows, and unresolved risks only when needed.
Cover these concerns where they apply:

- Components, layers, responsibilities, import rules, and the directory structure.
- Languages, runtime, frameworks, database, major libraries, and verification tools.
- Data types, identities, ownership, relationships, integrity, persistence, and migration boundaries.
- Public contracts, authorization boundaries, validation, errors, and recovery behavior.
- Deployment, external data flows, secrets, settings, and operational failure handling.

For an AI feature, define the provider or local runtime, outgoing data, output validation, failure handling, and test boundaries. Respect project rules.
Choose diagrams only when they clarify boundaries, dependencies, or runtime behavior. Use the least detail that helps implementation.
Keep directory entries and technical settings concrete. Reference requirement IDs for user-visible rules and limits.

## Record decisions and evidence

Give every significant design decision a stable `DEC-NNN`, or the existing project convention.
Never renumber or reuse IDs. Find the highest allocated ID in the current document and available Git history before assigning a new one.
If history is unavailable, resolve the allocation boundary before finalizing new IDs. Provisional labels must not enter the approved design.
Record context, requirement references, choice, rationale, alternatives, consequences, and a validation method. Use compact tables or nearby details.
Under project-init, keep one current decision per topic. Remove a replaced decision from the current document and give its replacement a new ID.
Keep replacement history in Git. If another project uses superseded records, preserve that convention instead.
Separate observed results, documented capabilities, estimates, assumptions, and planned checks. Cite sources for consequential claims.
Never mark a test, benchmark, compatibility check, or prototype as successful unless it actually ran.

## Finish at the design boundary

Check that the design addresses the architectural drivers, respects the spec, and gives significant decisions real alternatives and validation methods.
Check references, unique IDs, technology evidence, data flows, interface failures, and consistency with project rules.
Check that material unknowns have an owner and a blocking condition. Do not call an unresolved stack choice final.
Present the concrete design before requesting any approval required by project rules. Allow review in chat or a draft without replacing approved content prematurely.
Record only approval actually given, in the location the workflow permits. Technical review and user approval are separate facts.
Save authorized design edits and follow applicable document checks and Git rules. Report the result and any remaining blocker briefly.
Stop after design. Do not install dependencies, create application code, run experiments, or build milestones unless separately authorized.
After approval, tell the user the next step is `/write-plan`.
