# Gallup Again — combined employee and manager demo

An initial integration of Selena's employee experience, Lucas's React/FastAPI
PostgreSQL foundation, and Kevin's compact manager dashboard patterns. Source
provenance is in [docs/SOURCES.md](docs/SOURCES.md).

## Current behavior

- Synthetic persona selection from Active PostgreSQL employees. An employee with
  eligible current direct reports also receives a manager workspace. **This is
  impersonable demo identity, not authentication.** Actual login is deferred.
- Five employee sections: My work and goals; My reviews; Team engagement (Q12);
  Ask my record; What is and isn't used. Managers can also view their own workspace.
- Own goals, task/project identifiers, training, reviews and self-assessments.
  Review ratings retain the fixed 1–5 scale.
- Own synthetic email viewer inside My work and goals. Only messages sent or
  received by the persona are returned, even within a shared thread. Other BCC
  recipients are hidden unless the persona sent the message. Bodies render as text.
  Email questions can use participation-scoped synthetic messages. Manager dashboard access does not grant a report's inbox; manager AI retrieves only messages involving both actor and selected report.
- Manager current-direct-report overview, task/training metrics, goal evidence,
  completed training milestones, cited on-demand conversation assistance and an
  editable/downloadable preparation outline. The outline is provisional; a final
  report template and North Stars have not been defined.
- Existing labeled task/training simulation remains in an expandable manager
  summary. General employee/manager questions require configured live OpenAI mode;
  no generated answer is substituted when unavailable.
- Q12 group membership, suppression, waves, item charts/distributions, synthetic
  benchmarks, discussion prompts and on-demand discussion preparation are wired
  to PostgreSQL. Missing/suppressed results are displayed honestly.

The approved November 3 update loaded **12,634 email messages and recipients,
2 Q12 waves and 1,534 aggregate results**, corrected six question statements,
and filled 40,202 missing narrative fields using labelled synthetic source context.
All imported records match the reviewed fixtures; all 2,500 employees participate
in generated email. Suppression is preserved. See
[database completeness and task rates](dev/agent/DATA_COMPLETENESS.md) for remaining
intentional NULLs and verification evidence. No corporate schema changes or
persistent app tables were introduced. Peer feedback and private manager notes remain excluded. Manager
preparation does not yet include reviews or self-assessments pending a field policy.
No HR/company administration, email sending, source editing, durable chat/audit,
account provisioning or real login is implemented.

## Setup

Use Python 3.11+ (verified here with 3.13.9), Node 24.19+ within 24.x and npm
11.17+ within 11.x. Existing locked dependencies are retained from Lucas's app.
Run from this repository root:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm ci
cp .env.example .env  # only when .env does not already exist
```

Set `DATABASE_URL` privately in `.env` to the existing authorized PostgreSQL
connection. The backend uses read-only transactions. Never execute
`database/schema.sql` as setup: it contains destructive historical DDL and is a
reference only. Do not load fixtures or seed a database as part of startup.

```sh
./scripts/demo.sh
```

Open http://127.0.0.1:5173. Keep the launcher running. The app binds to loopback;
there is no deployed public app. Start and stop only the processes you own.
The original Streamlit demo can continue independently on port 8501.

For general AI questions, set `ASSISTANT_MODE=openai`, `OPENAI_API_KEY` and an
account-accessible `OPENAI_MODEL` in private backend configuration, then restart.
The existing adapter uses the OpenAI Responses API with structured output and
validates source IDs against retrieved records. Live employee and manager email/Q12 citation smoke checks passed on November 4, 2026.
The configured provider is now the GW Azure sandbox; private configuration is never copied into source.
Only allowlisted, bounded record fields are sent; context includes at most 60
work records, 12 matching synthetic emails and 36 reportable Q12 items, with text
fields truncated to 1,200 characters and a total 12,000-character context budget. No model can select a different employee or SQL.
Do not put API keys or database credentials in frontend environment variables.

## Verification

```sh
.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -q
npm test
npm run build
.venv/bin/python -m pip check
# Explicit read-only check against the configured existing PostgreSQL database:
.venv/bin/python scripts/check_integration.py
```

Unit/integration tests use mocks and isolated test databases, not corporate writes.
The live smoke reads existing records and verifies self/direct-report boundaries.
See [the integration plan](dev/agent/COMBINED_APP_PLAN.md) for design dependencies;
its initial planning status is historical and the completion log records this slice.


## Synthetic email/Q12 generation and context update

The current local update adds question-specific email and Q12 retrieval. See
[the context policy](dev/agent/DATA_CONTEXT_POLICY.md) for exact access rules.
Generated emails are two-message synthetic employee/supervisor discussions tied
 to existing work records; they do not assert new outcomes or commitments.
Local generated data stays in ignored `local-fixtures/`, separate from source code.

```sh
# SELECT-only generation; refuses to replace differing local outputs:
.venv/bin/python scripts/generate_email_fixtures.py
# SELECT-only validation of prepared local email and Q12 fixtures:
.venv/bin/python scripts/import_demo_fixtures.py
```

Q12 inputs must be copied from the reviewed existing fixtures into
`local-fixtures/q12/`, together with `review-preflight.json` from the reviewed
Q12 import package. No automatic generation or loading occurs at startup.
The importer has an explicit `--apply` option for separately approved execution;
that option writes six reviewed question-text corrections plus aggregate/email
rows, checks all destination tables are empty, and uses one transaction.
Do not execute it until that database change is approved.

Generation produced 12,634 marked synthetic messages in 6,317 threads. The user
approved importing these records and the 2-wave/1,534-row Q12 fixtures; the import
and exact read-back checks passed. Do not rerun the importer: it intentionally
refuses nonempty destinations. Live AI verification still requires a private API key.
The API and UI use data from PostgreSQL, not the generated CSV files directly.

Azure mode is selected privately, using the verified gpt-5.4-mini deployment. The
demo launcher respects that setting; Azure keys never fall back to direct OpenAI. Never paste API keys into
chat or put them in frontend settings. No fallback answer is passed off as live AI.


## Task completion for every employee

Employee and manager views use the same all-time backend calculation, over all
scoped task records. A numeric rate appears where eligible tasks exist; no-task
and cancelled-only cases have explicit explanations instead of blank values or
false zeros. Stored review-quarter percentages retain their original definition.
User-approved narrative enrichment fills real text gaps but preserves meaningful
NULLs such as suppressed scores and unfinished completion dates. Details and
read-only audit commands are in [DATA_COMPLETENESS.md](dev/agent/DATA_COMPLETENESS.md).


## Live AI status — November 4, 2026

GW/Azure is active with the verified `gpt-5.4-mini` deployment. Both a minimal
response and structured parsing passed; full employee and manager requests through
the running app now return live answers citing permitted email and Q12 records.
The database connection was reachable again during the final checks; no VM,
firewall, database settings or records were changed to restore it.

The original all-groups/all-waves Q12 prompt hit the shared sandbox rate limit.
Default retrieval now selects the most specific permitted group and latest wave.
Explicit group/wave requests and comparisons are honored within the same access
scope. Comparisons include at most two waves and AI Q12 context at most 36 items.
A 12,000-character compact context budget gives each retrieved source category a
turn, discloses omitted records and validates citations only against records
actually sent. Large full UI source details remain available within existing scope.

Azure reasoning effort is set privately to `none` for the verified `gpt-5.4-mini`
deployment to reduce chatbot generation time. The model supports this setting
([official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini)).
`AZURE_OPENAI_REASONING_EFFORT` is optional for compatible reasoning models;
it is not sent to direct OpenAI automatically. Rate-limit responses now return a
clear HTTP 429 without exposing provider payloads. The shared sandbox can still
rate-limit requests; no billing/quota settings were changed.

Latest upload verification: 89 backend tests, 41 frontend tests, TypeScript,
production build and Python dependency checks passed. Live employee
answer: email + Q12 citations. Live manager answer: shared email + Q12 + training
citations. These are functional smoke checks, not a broad answer-quality benchmark.
The user withdrew the Claude suggestion; no Claude integration is pending.

## Latest UI fixes and continuation

My reviews connects chronological recorded ratings on the fixed 1–5 scale and
shows the period and score on hover or keyboard focus. Ask my record now creates
a fresh request controller per submission, fixing the indefinite loading state
caused by React StrictMode cleanup. A live cited training answer was verified in
Safari; generation can still take several seconds.

For current context and remaining decisions, read [CONTINUE_HERE.md](CONTINUE_HERE.md)
and [the Claude handoff](docs/CLAUDE_HANDOFF.md). Historical task logs retain their
original verification dates. This repository contains source, not a hosted app;
private configuration and PostgreSQL records are not included.

Current code remains local and newer than the private GitHub baseline. No commit
or push was performed. Current logs describe the exact tests and limits.
