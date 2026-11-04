# Restore source retrieval and verify live Azure answers

Date: 2026-11-04

## Implemented

The existing PostgreSQL TCP connection became reachable again when checked after
the user's update. No VM/container, firewall, database endpoint, credentials or
records were changed to restore it. Read-only integration and full-population
task-rate checks passed against the existing loaded dataset.

Initial full employee AI request failed. A sanitized diagnostic confirmed Azure
HTTP 429 `rate_limit_exceeded`: its prompt contained 76 sources / 52,453 characters
because all permitted Q12 groups and waves were included. No key or answer
narratives were printed. No quota/billing changes or provider substitutions.

Default AI Q12 selection now uses the most specific permitted group and latest
wave. Explicit group/wave requests and up-to-two-wave comparisons are preserved;
selection only narrows backend-authorized data. Suppression remains enforced first.
Q12 context is capped at 36 items and coverage/omissions are disclosed.

Added compact context packing with a 12,000-character budget. Categories take turns
in source selection; long fields are capped and duplicate Q12 prompt fields removed.
UI source details retain their original allowed projection. Citation validation
uses only the actually sent records, not omitted retrieved records. Oversized
metadata has a predictable error. Added sanitized 429 handling to both assistants.

Configured optional low reasoning effort for the existing Azure deployment,
matching the original employee demo. Direct OpenAI does not receive this option.
Restarted only the confirmed owned app launcher to load the tested change.

## Verified

- Read-only database integration: 2,408 Active personas, populated email and two
  Q12 waves, manager/employee restrictions and report data.
- All 2,500 task summaries: 1,307 numeric, 1,181 no assignments, 12 cancelled-only;
  representative employee APIs match the shared calculation.
- 85 backend tests passed, including group/wave selection, unauthorized selection,
  comparison behavior, context bounds/category turns/source IDs, explicit Azure
  reasoning options and sanitized rate-limit handling. Earlier same-day frontend
  checks: 36 tests and production build passed; this fix did not change UI code.
- Actual live employee request via frontend proxy passed: Azure answer with
  5 validated citations across email and Q12, 840 answer characters.
- Actual live manager request via frontend proxy passed: Azure answer with
  8 validated citations across shared email, Q12 and training, 1,207 characters.
- Both app requests used the configured GW Azure gpt-5.4-mini deployment, live
  records and `store=False`. No canned fallback or fake source was used.

## Not verified

Broad answer-quality/fairness evaluation, stress/load testing, manual visual QA or
long-term stability of external database availability/shared sandbox quotas. This
was functional integration work. No database writes, schema changes, Git commit
or push. Earlier handoff ZIP snapshots predate this fix.

## Follow-up decisions

No additional provider configuration is required for the verified paths. Existing
pending product choices remain separate: actual login, final report template and
whether to prepare extra task assignments. Shared sandbox rate limits can still
occur; the app now reports them clearly.

## Recommended Next Steps

Review the working employee and manager journeys in the browser. If the user
wants the current source published, request/obtain explicit commit/push scope;
the private GitHub main remains the older baseline.
