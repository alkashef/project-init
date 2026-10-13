# Interview Guide

## Method and sources

Use usage-centered requirements elicitation as the core method. Derive system
requirements from user tasks and business goals. Examine events and responses,
data concepts, and quality attributes. These concerns come from Wiegers and Beatty.

- [Karl Wiegers and Joy Beatty: Requirements Elicitation](https://www.informit.com/articles/article.aspx?p=3172445)
- [Karl Wiegers: Exploring User Requirements with Use Cases](https://processimpact.com/courses/usecasedesc.html)

Use the following sources for specific supporting techniques:

- [Teresa Torres: Story-based customer interviews](https://www.producttalk.org/customer-interviews/)
- [Matt Wynne and Cucumber: Example Mapping](https://cucumber.io/docs/bdd/example-mapping/)
- [Alistair Mavin: EARS](https://alistairmavin.com/ears/)

Treat this skill as an adaptation for an AI interviewer. Do not claim that its
entire workflow is a certified method or a verbatim reproduction of these sources.
Do not present simulated users or AI reviewers as evidence from actual users.

## Choose the next question

Maintain a short map of unresolved concerns in working context. Track business
purpose, user tasks, rules, exceptions, data, quality, scope, and acceptance evidence.
Prioritize an unknown by how much its answer could change the work and the cost
of a wrong assumption. Do not convert this map into a score for spec quality.

For sparse context, ask for the real situation that motivates the app.
For rich context, summarize what the evidence supports and ask about one material gap.
For conflicting answers, identify the conflict and ask who can decide it.

Use focused questions such as these when the corresponding concern is unresolved:

| Concern | Example question |
| --- | --- |
| Real work | What happened the last time you needed to do this? |
| Business value | What would improve if this task worked better? |
| User goal | What must this person accomplish before the task is complete? |
| Rule | What makes a request eligible for approval? |
| Exception | What should happen if another person changes the record first? |
| Data | Which information determines whether these are the same customer? |
| Quality | How long can this person wait before the task is disrupted? |
| Acceptance | For this specific input, what result would you accept? |

Ask only one of these at a time. Adapt the wording to the user's context.

## Capture enough scenario detail

For a user task, identify the actor and goal, trigger, preconditions, main success
path, alternate paths, failure paths, and postconditions. Capture business decisions
and required information. Avoid screen layouts and implementation mechanisms.

For an existing process, ask for a representative document or observed example
when an answer depends on details that people routinely omit. Preserve confidentiality.
For a new process, label the scenario as proposed and confirm the desired behavior.

## Keep evidence distinct from decisions

Record a source as precisely as the available context allows: a user statement,
named domain owner, document section, or observed behavior. Do not invent a citation.
Record an agent inference as an inference, even when it seems conventional.

Distinguish what happens today, what someone requests, and what the authorized
decision-maker approves. A source can support a fact without approving a future behavior.
If stakeholders disagree, record both positions and the responsible decision-maker.

## Derive rules with examples

Use examples to expose ambiguity before formalizing a requirement.
Capture the situation, relevant input, business rule, and expected result.
Record unresolved questions instead of choosing an answer to make the example complete.
Use invented or redacted data. The domain owner must review the expected result.

For example, suppose a user requests a late-payment alert. Clarify who receives it,
what establishes the due date, and when a payment counts as received. Investigate
partial payments, disputed invoices, and time boundaries when they affect the rule.
Do not choose a grace period or notification channel without supporting context.

The examples become candidate acceptance tests. Their execution belongs downstream.
User approval establishes the intended outcome within the agreed scope. It does
not prove that the implementation meets that outcome or that the product delivers value.

## Detect a weak spec

Challenge features with no stated purpose, quality adjectives with no acceptance
condition, and assumptions presented as facts. Challenge requirements that describe
technical solutions when the underlying behavior remains unclear.

Do not seek theoretical completeness. Examine omitted concerns when they could
change acceptance, safety, scope, or operational use. Respect a user request to stop.
Leave a usable draft that identifies the material unresolved decisions and their effects.
