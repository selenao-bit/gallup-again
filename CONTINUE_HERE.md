# Continue Gallup Again

Updated: November 4, 2026. This source snapshot contains the combined employee and
manager demo, synthetic email/Q12 retrieval, GW Azure integration, task completion
metrics, connected review chart with hover scores, and the Ask my record loading fix.

Read [AGENTS.md](AGENTS.md), [README.md](README.md), and
[the current handoff](docs/CLAUDE_HANDOFF.md) before changing code. Read only the
relevant development contracts and task logs. Never inspect dev/personal without
current explicit authorization.

## Current behavior

- Five employee tabs and the manager direct-report workspace are preserved.
- PostgreSQL is authoritative; approved synthetic email/Q12 records are already
  loaded. Do not regenerate/reload them or execute database/schema.sql as setup.
- Live AI uses the verified existing GW Azure gpt-5.4-mini deployment. Credentials,
  endpoint and database connection are configured privately; no working .env is
  included in this repository. Configure your own authorized settings from
  .env.example. Never put server credentials in frontend configuration.
- Backend scope and source-ID validation remain enforced. Emails require
  message-level participation; Q12 is suppressed group context, never an individual
  performance measure. Manager reviews/self-assessments remain excluded.
- The chart connects recorded ratings on a fixed 1–5 scale and exposes hover/focus
  scores. Chat uses a fresh request controller after the StrictMode loading fix.

## Verification

Latest upload checks: 89 backend tests; 41 frontend tests; TypeScript and production
build; Python dependency check. Earlier bounded live employee/manager requests
returned source-cited email/Q12 answers. Safari Ask my record displayed a live cited
training answer after its loading fix. These are targeted checks, not exhaustive
model-quality or latency benchmarks.

Run from the repository root:

```sh
.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -q
npm test
npm run build
.venv/bin/python -m pip check
./scripts/demo.sh --no-browser
```

Follow README setup for a fresh clone. Startup does not create corporate tables,
load records or provision accounts. Avoid duplicate local servers.

## Deferred decisions

Actual login, durable chats/drafts/audit, final report template and North Stars,
HR/company-wide screens, and stable hosting remain unfinished. Synthetic persona
selection is not authentication. Each chat question is currently independent.

There is no active public link. Public tunnel creation requires explicit approval
for exposing synthetic record views and Azure chatbot use; that approval is pending.
A GitHub source upload does not publish a running website or change those permissions.

The working app has been under /private/tmp/gallup-again. Treat temporary storage as
a working location, not a durable backup. Do not confuse the original Capstone or
employee Streamlit checkout with this combined app.

## Proposed work

See dev/agent/logs/TASK-COMPLETION-RECOMMENDATIONS-001.md for advisory priorities.
They are proposals, not implementation authorization. Ask the user for their next
bounded task; preserve current features, data and privacy boundaries.
