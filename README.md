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
  Email is excluded from AI context and manager access to a report's inbox.
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

The November 3 read-only check found **no email messages and no Q12 survey waves
or results** in the configured database. The prior employee demo's CSV fixtures
have not been imported. Those populated journeys therefore remain unverified.
No corporate schema changes, data regeneration or persistent app tables were
introduced. Peer feedback and private manager notes remain excluded. Manager
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
validates source IDs against retrieved records. Live calls have not been verified.
The original Streamlit Azure configuration is not automatically transferred.
Only allowlisted, bounded record fields are sent; context includes at most 100
work records with text fields truncated to 1,200 characters, plus reportable Q12
items for engagement preparation. No model can select a different employee or SQL.
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
