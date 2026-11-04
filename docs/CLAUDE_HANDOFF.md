# Gallup Again — handoff for Claude

Prepared for Selena, November 4, 2026. This describes the current local demo. It
contains no API keys, connection credentials or employee-record exports.

## What I am building

I am combining my employee demo with Kevin's and Lucas's manager demos into an
employee performance analytics and manager conversation-preparation app. Help me
continue incrementally, preserve working features, and ask before consequential
architecture or data changes.

## Where the current work is

- Combined working app on this Mac: `/private/tmp/gallup-again`.
- Original project: `/Users/selenao/PycharmProjects/Capstone_Project`.
- Private combined GitHub repository: https://github.com/selenao-bit/gallup-again
- Source repositories: https://github.com/Lukeryan360/Capstone_Project and
  https://github.com/kevinete4/manager-prep-assistant
- Current local demo: http://localhost:5173 ; backend: http://127.0.0.1:8000 .
- A separate compiled frontend preview is running at http://localhost:5180 .
- This source snapshot includes the latest combined features and chatbot fixes.
  Check GitHub commit history and local git status for any subsequent changes.
- `/private/tmp` is temporary storage; do not assume it is a durable backup.
- No public link is active. Opening a public Cloudflare tunnel was blocked by
  automatic approval review because the demo has no real login and would expose
  synthetic records and chatbot use to anyone with the URL. Explicit approval
  for that exposure is still pending; do not treat this handoff as that approval.

A cloud-hosted chat cannot reach this Mac's localhost by following the URL alone.
Use these notes and screenshots, or give a local coding tool access to the combined
working directory. Do not upload `.env`, credentials or whole unreviewed folders.

## Technology and current behavior

React/TypeScript with Vite, FastAPI/Pydantic, and PostgreSQL. The backend mediates
all database and model access. Live AI uses the existing GW Azure OpenAI sandbox
with the verified `gpt-5.4-mini` deployment; credentials live in private backend
configuration. The optional reasoning setting is `none` for this compatible model.
There is no Claude API integration requested; Claude is being used as a collaborator.

Employee tabs to preserve:
1. My work and goals: goals, tasks/projects, training and permitted synthetic inbox.
2. My reviews: recorded overall ratings, history and own self-assessments.
3. Team engagement (Q12): group results, charts, suppression and preparation controls.
4. Ask my record: on-demand source-cited answers about permitted records.
5. What is and isn't used: coverage and exclusions.

The separate My voice and Prepare my conversation tabs were deliberately removed.
Keep the preparation controls inside Team engagement.

Managers retain their own employee workspace and a direct-report workspace with
progress/evidence views, Start the Conversation and an editable provisional draft.
The final report template is still undefined. HR/company-wide experiences, genuine
login, North Stars and detailed evaluation/benchmark pages are deferred.

Synthetic persona selection is deliberately impersonable and is NOT authentication.
Do not describe this demo as production-ready access control.

## Data and AI boundaries

PostgreSQL is authoritative. Synthetic email and Q12 fixtures were loaded with
explicit approval, six truncated Q12 statements corrected, and approved missing
narratives filled. Do not regenerate/reload those records to troubleshoot a bug.
Some NULLs are meaningful (unfinished dates, suppressed scores, no applicable rate).
Task completion uses Complete / non-Cancelled assigned tasks, including Suspended;
no assigned/eligible tasks displays an explanation rather than a fabricated zero.

Backend queries enforce self/direct-report boundaries. Manager access does not
create general inbox access: each retrieved email must include the actor, and a
selected-report context must also include that report. Never expose BCC lists to AI.
Manager preparation excludes reviews/self-assessments, private notes and peer
feedback under the current policy. Q12 is permitted group context, never individual
performance; honor suppression and the minimum five responses.

Retrieval is bounded and citations are validated against sources actually sent to
the model. Context has a 12,000-character budget. Do not cache stale authorization,
show fabricated responses/citations, add employment recommendations or let model
arguments choose employee scope.

## Latest fixes and evidence

- Review chart now connects chronological recorded ratings on the existing 1–5
  scale. Hover/focus shows the period and score. Missing scores are not invented.
  Files: `frontend/src/ReviewChart.tsx`, its tests, EmployeeWorkspace and styles.
- Ask my record previously reused an AbortController cancelled by React StrictMode
  effect cleanup. Submission then cancelled immediately and skipped clearing its
  loading state, making the wait indefinite.
- Fixed Conversation in `frontend/src/EmployeeWorkspace.tsx`: fresh controller per
  submission, ref tracks active request, unmount aborts it, duplicate submits are
  guarded. Regression in `EmployeeWorkspace.test.tsx` failed before the fix and
  passes afterward; error recovery and leaving the section are also checked.
- Latest frontend verification: 41 tests pass, TypeScript and production build pass,
  git diff --check passes. Live Safari Ask my record returned a cited training
  answer and restored the submit button.
- Latest upload checks: 89 backend tests and 41 frontend tests passed, together
  with the TypeScript check, production build and Python dependency check.
- Earlier bounded live employee/manager email + Q12 checks took about 5.6 seconds
  each with validated citations. A later goal question took 6.91 seconds. These are
  samples, not a universal speed guarantee. The UI bug and normal AI generation
  time are separate issues. Every persona/question was not exercised.

## How to continue safely

Read combined `AGENTS.md` first, then only relevant `dev/agent/` specifications,
current code, tests and task logs. Later task logs describe implemented state more
accurately than superseded brainstorming/proposals.

Never list/read/search `dev/personal/` without Selena's explicit current permission.
Exclude it from discovery. Do not reveal secrets, change corporate schema/data,
introduce persistent tables, install substantial dependencies or commit/push without
the required user authorization. Keep source provenance and existing features.

Practical commands from `/private/tmp/gallup-again`:
- `npm test`
- `npm run build`
- `.venv/bin/python -m pytest backend/tests -q`
- `scripts/demo.sh --no-browser` starts local servers only when the required ports
  are free; do not launch a duplicate or stop services you do not own.

Relevant recent logs in the combined app:
- `dev/agent/logs/TASK-ASK-MY-RECORD-LOADING-001.md`
- `dev/agent/logs/TASK-CHAT-LATENCY-REVIEW-CHART-001.md`
- `dev/agent/DATA_CONTEXT_POLICY.md`

No new feature request is implied by this handoff. Ask Selena what she wants next.
