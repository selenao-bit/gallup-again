# Synthetic email/Q12 data and chatbot context

Date: 2026-11-03

## Implemented

Added a SELECT-only deterministic email fixture generator and a separately gated
transactional importer. Generated 12,634 clearly marked synthetic messages and
12,634 recipient rows in 6,317 employee/supervisor threads for 2,499 employees
with eligible existing work sources. Messages reference actual latest goal/task/
training records; they do not assert new outcomes or commitments. The self-managed
root employee is not given a fictitious supervisor thread. Local data is ignored
under `local-fixtures/`. Reused the reviewed Q12 fixtures: 2 waves, 1,534 results,
78 suppressed rows; no corporate data regenerated.

Added question-specific retrieval shared by the employee and manager chatbot.
Email scope is message-level actor participation; manager preparation additionally
requires participation by the selected current direct report. SQL rechecks current
reporting edges. No recipient lists/BCC metadata enters model context. Q12 context
uses composite source IDs, reporting periods and permitted group memberships
shared by actor/subject; suppression is enforced before source construction.
General work questions do not automatically retrieve email/Q12. Text matching,
record counts and text lengths are bounded, with coverage gaps disclosed.

Updated AI context/prompt, employee starter questions and transparency wording,
repository policy, README, and `dev/agent/DATA_CONTEXT_POLICY.md`. The live adapter
remains the existing direct OpenAI integration pending provider selection. Actual
login remains deferred. No public interfaces or app dependencies were added.

## Verified

- 63 backend tests and 32 frontend tests passed; TypeScript/production build passed.
- New tests exercise deterministic email generation, references/date bounds,
  threaded replies, email scope across shared threads, reporting-line changes,
  source selection, composite Q12 citations and suppression exclusion.
- Two SELECT-only generator runs produced byte-identical local artifacts.
- Import preflight verified hashes, current membership, current source facts,
  participant accounts, dates, table emptiness, source references and Q12 arithmetic.
  Six known question-text corrections are still necessary for a future import.
- Live read-only email/Q12 query smoke passed; manager group results were a subset
  of the actor's own permitted groups. Empty destinations remained empty.
- Restarted only the owned combined-app launcher; proxy health returned OK at
  http://127.0.0.1:5173/api/health.

## Not verified

No database writes/imports performed; user approval of loading and the six existing
question-text corrections is pending. The prepared importer writes only with an
explicit `--apply`; it locks sources/destinations, refuses nonempty destinations,
rechecks sources, and imports both datasets plus corrections in one transaction.
Write permissions, triggers and populated app rendering remain unverified.

Neither OpenAI nor Azure credentials are configured for the combined app, so no
live model response was generated. Model/citation tests use mocks. No fallback
response is represented as live AI. No commits or pushes for this update.

## Follow-up decisions

Pending asynchronous questions: approve database loading plus six wording
corrections versus files-only; select Azure/GW versus direct OpenAI. Credentials
must be entered privately, never into chat or frontend settings. Do not infer
loading approval from elapsed time or from the generation request after asking
the explicit loading question.

## Recommended Next Steps

If approved, run the prepared atomic import, verify counts/suppression and rendered
source views, then configure the chosen AI service privately and make a bounded
live smoke request. These are required to finish end-to-end activation; no email
sending or expanded inbox scope is implied.
