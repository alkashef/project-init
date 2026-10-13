# Technology choices

## Recommend a stack from the constraints

Read the current stack, manifests, environment rules, deployment target, and approved integrations first.
Do not assume Python, TypeScript, React, cloud hosting, an LLM, or a database because these are familiar.
Treat existing technologies as constraints until a replacement has a concrete benefit that outweighs migration and maintenance costs.
Prefer the standard library when it satisfies the requirements. Explain the capability that requires each new major library.

Recommend the applicable languages, runtime, frameworks, database, major libraries, and test tools.
If a category is unnecessary, state why briefly instead of inventing a technology for it.
Connect consequential choices to requirement IDs or project constraints and a `DEC-NNN`.

## Check current facts

Use official documentation, release notes, package metadata, or license text for consequential technology claims.
Check the exact capability, platform support, compatible runtime versions, maintenance status, and license where these affect the decision.
For paid services, check current pricing and limits when they affect the proposed design. State workload assumptions behind cost estimates.
Record source URLs and the date checked. Do not treat model recall as current evidence.
If browsing is unavailable, label the candidate and capability claim unverified. Do not claim an implementation-ready choice when the uncertainty could change the stack.

## Separate recommendations from installed dependencies

In design, name the chosen technologies, their roles, reasons, and relevant compatibility constraints.
Record a required major version or support policy only when architecture depends on it.
Keep exact installed direct versions in the manifest, requirements file, or lockfile according to project rules.
Resolve and pin exact versions when adding the dependency, with the required approval. Never install a package merely to complete design.
In project-init, `requirements.txt` or `package.json` owns the installed direct dependency list. Do not add unused packages to those files.

Identify existing, approved, proposed, and unverified technologies clearly.
A proposed library remains proposed until the user grants any required dependency approval.
An architecture approval permits a dependency only when that library and permission are explicit in the approved scope.

## Explain choices to non-programmers

Give one primary recommendation. Explain its effect on cost, setup, maintenance, privacy, or an important workflow.
Describe a meaningful alternative and the condition that would favor it.
Ask for the underlying constraint rather than a brand preference.

Example: "I recommend local storage because the approved scope has one user on one machine. Shared access would change this choice."

If shared access is not established, ask whether users need simultaneous access before finalizing persistence.
Do not infer shared access merely from the number of employees in the organization.

## Design tools and quality checks

Reuse the project's check tools where adequate. Identify a browser test tool when UI workflow requirements need browser tests.
Define test boundaries and fakes for external services. Keep live services and private data out of automated tests unless the project explicitly permits them.
Treat coverage and lint as implementation checks. Define separate evidence for requirement behavior and important quality attributes.
