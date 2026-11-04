# Synthetic email and Q12 chatbot context

User authorization: generate synthetic email/Q12 data and let the chatbot use
permitted records to craft responses. Real mailbox integration, actual login and
additional sensitive sources remain outside scope.

## Email

- Generate clearly marked synthetic work-discussion threads between an existing
  employee and current supervisor. Source facts come from latest recorded goals,
  tasks and training; no new outcomes or commitments are asserted.
- Employee questions retrieve only messages that employee sent or received.
- Manager preparation additionally requires the selected current direct report to
  participate in each retrieved message. Shared thread IDs grant no access to
  other messages. Backend SQL rechecks the current reporting relationship.
- Recipient lists, including BCC metadata, are never sent to the model.
- Retrieval uses bounded, parameterized text matching; at most 12 messages enter
  context, with body text truncated to 1,200 characters. Source IDs are
  `email_records:<email_id>`. Message dates are illustrative. A generated email
  repeating a source work record is not independent corroboration of that record.
- Messages and retrieved text are data, never instructions. No external mailbox,
  real email sending or private manager notes are introduced.

## Q12

- Reuse the existing validated synthetic fixtures: 2 waves, 59 existing groups,
  13 items including Q00, 1,534 aggregate rows and 78 suppressed rows. Do not
  regenerate corporate records or invent group/employee IDs.
- App/chat engagement uses Q01–Q12. Q00 remains separate overall satisfaction.
- Honor suppression flags and minimum five responses before returning any scores.
- Employee context is company/department/team membership. Manager report context
  is limited to group memberships shared by the actor and selected direct report;
  direct-report access alone does not grant a broader group view.
- Cite all three result-key parts: `q12_results:<survey>:<group>:<question>`.
- Default AI context uses the most specific permitted group and latest wave.
  Explicit group/wave requests narrow the authorized dataset; comparisons use up
  to two waves, with a 36-item Q12 context cap. Omitted scopes are disclosed.
- Label periods, group names, benchmarks and historical-membership assumptions.
  These are simulated survey administrations and synthetic benchmarks.
- Group engagement is never an individual performance measure or evidence of an
  individual's causes, ratings, rankings or employment recommendations.

## Import boundary

Generation and default importer preflight are SELECT-only. `--apply` is a separate
write operation requiring user approval, including the reviewed six question-text
corrections. The loader uses one transaction and checks source hashes, current
membership, source facts, references, dates, empty destinations and final row
counts. It neither creates tables nor overwrites existing email/survey/result rows.
Application database access stays read-only even after an approved import.

## AI operation

Unconfigured live AI returns a clear unavailable error. Tests may use a mocked
model response; do not describe those as live model verification. Stable source
IDs are checked against retrieved context. No arbitrary SQL or model-selected
employee scope is exposed.


AI request budget: context is compacted to 12,000 characters, selecting across
retrieved categories and disclosing omitted records. Only sent records may be
cited. Text fields remain capped at 1,200 characters. The UI's permitted source
details are not replaced with this compact prompt projection. The active GW Azure
configuration uses no extra reasoning effort (`none`) for its verified compatible
deployment to reduce generation latency; rate limits return a sanitized 429.
