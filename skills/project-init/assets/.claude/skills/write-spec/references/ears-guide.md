# EARS and IDs

Use the existing EARS convention. Otherwise, apply the patterns below.
Use the business vocabulary and the actual system name.

| Pattern | Structure |
| --- | --- |
| Always active | The system shall [required response]. |
| Event | When [trigger], the system shall [required response]. |
| State | While [state], the system shall [required response]. |
| Optional feature | Where [feature is included], the system shall [required response]. |
| Unwanted behavior | If [unwanted condition], then the system shall [required response]. |

Combine a precondition and trigger only when both constrain the required response.
Write one behavior per requirement so its acceptance can be examined independently.
Do not add a trigger to a requirement that is always active.
Do not invent conditions or thresholds to complete a pattern.

Example of an agreed business rule, using invented data:

- `PAY-007`: When an accounts clerk records a payment against an invoice, the
  system shall reduce the outstanding balance of the invoice by the recorded amount.
- `EX-012`: Given an outstanding balance of 1,000 and a payment of 400, expect
  an outstanding balance of 600.

The example does not settle currency conversion, overpayments, refunds, or
authorization.
 Examine those concerns if they are relevant to the approved scope.
Do not generate rules for them merely because this example mentions payments.


Keep existing requirement IDs. Allocate a new ID after the highest number ever
used in its namespace. Examine available version history when the spec omits retired IDs.
If the previous range remains unknown, resolve the ID allocation before assigning a new ID.
 Preserve withdrawn rows so the allocator does not reuse them.
For a spec without an ID convention, use `AREA-NNN` and `NFR-NNN`.
Change wording without changing the ID when the underlying requirement continues.
Mark a retired requirement `Withdrawn`. Do not renumber surviving requirements.

Source: [Official EARS guide by Alistair Mavin](https://alistairmavin.com/ears/).
EARS controls wording. It does not establish the business value of a requirement.
