# Design guide

## Apply ADD with bounded depth

Use architectural drivers to choose the next design issue. A driver matters when different answers change structure, contracts, technology, or operating cost.
For a small local utility, one design cycle can settle the architecture. Decompose further only when a component contains a real unresolved risk.
Do not imitate a large enterprise design process for a small application.

Use these prompts internally:

| Concern | Question |
| --- | --- |
| Functional driver | Which critical task requires this component or interface? |
| Quality driver | Under which conditions must the system meet which measurable result? |
| Constraint | Which existing rule, platform, integration, or resource limits the options? |
| Risk | Which uncertain claim could invalidate the recommended design? |

Read rather than re-interview when the spec already answers the question.
If the spec says only "fast," ask about a concrete task and acceptable waiting time. Submit the resulting requirement change for approval.

## Make alternatives useful

Compare genuinely different approaches to the same problem. Give each feasible option its strongest case.
Compare only criteria tied to drivers. Avoid numeric scores without a defensible measurement or agreed weighting.
Do not invent rejected options merely to justify a favorite technology.
Explain the chosen option's cost and limitation as clearly as its benefit.

For example, file storage and a database differ in concurrent writes, queries, recovery, and operations.
The recommendation depends on actual requirements. A one-user script does not automatically need a server or database.

## Define boundaries

Give each component a clear responsibility, state ownership, and external contract.
State allowed dependency directions so an implementation session can locate the owner of a change.
Keep domain rules independent of replaceable external systems where this reduces risk.
Reuse project patterns that already work. Add a boundary when it hides meaningful complexity, not merely to increase the number of layers.

For a UI, define navigation, interaction states, and workflow contracts when they affect implementation.
Use a separate visual design process for typography, detailed layouts, or aesthetic exploration when requested.

## Walk behavior through the design

Trace at least one critical workflow from entry point to result. Identify where validation, authorization, persistence, and external calls happen.
Examine relevant failures, such as duplicate submissions, interrupted writes, unavailable services, stale data, or invalid AI output.
Choose recovery behavior already supported by the spec. Propose a requirement change if the expected behavior is missing.
Use a sequence or state diagram only when prose leaves an important ambiguity.

## Choose evidence proportional to risk

| Claim | Appropriate evidence |
| --- | --- |
| A framework supports a feature | Official documentation for the intended version |
| Components obey an import boundary | Proposed automated dependency check or existing check results |
| A critical operation meets a latency target | Representative benchmark with workload and environment |
| Data remains recoverable after interruption | Failure scenario and a planned or executed recovery test |
| An integration can access required data | Official access requirements and, when authorized, a feasibility experiment |

Document planned evidence as planned. An architecture diagram or passing lint does not demonstrate runtime quality.
Propose an experiment with a question, pass criterion, owner, and expected effort when documentation cannot settle a blocking claim.
Do not execute it without authorization. Mark its result unknown until evidence exists.

Request expert review for a specific unresolved technical judgment when its consequences justify that review.
Avoid using expert review as a substitute for producing a concrete proposal.

## Sources and adaptation

Use the following original sources as the method's basis. The workflow and templates in this skill are a custom adaptation.

- [SEI: ADD 3.0](https://www.sei.cmu.edu/library/add-30-rethinking-drivers-and-decisions-in-the-design-process/): drivers, patterns, tactics, frameworks, and iterative architectural decisions.
- [SEI: ADD method collection](https://www.sei.cmu.edu/library/attribute-driven-design-method-collection/): design from significant functional requirements, quality requirements, and constraints.
- [George Fairbanks: Risk-driven model](https://www.georgefairbanks.com/software-architecture/risk-driven-model/): choose design effort and techniques according to technical risk.
- [arc42 method](https://arc42.org/method/): connect requirements, structures, crosscutting concepts, communication, implementation, and evaluation.
- [Michael Nygard: Architecture decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions): preserve decision context and consequences. Adapt record storage to project-init's current-state documents and Git history.
