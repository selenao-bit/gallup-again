# Initial combined employee/manager application

Date: 2026-11-03

## Implemented

New private repository `selenao-bit/gallup-again`, with a separate working folder
at `/private/tmp/gallup-again`. Adapted Lucas's React/FastAPI application, Selena's
five employee sections and Q12 constants, and Kevin's dashboard patterns. Added
shared employee-record services, source-backed manager evidence, synthetic persona
selection, participation-only email viewing, cited AI endpoints and an editable
preparation outline. Provenance, setup and current limitations are documented.

Actual login/account creation is deferred by the user's latest direction. Each
Active synthetic employee is selectable; eligible current reporting edges enable
the additional manager workspace. This is impersonable demo identity. Private
manager notes and peer feedback remain excluded. Emails are self-only and excluded
from AI; manager preparation omits reviews/self-assessments pending field policy.
The provisional report outline does not define North Stars or automated decisions.

No source repository checkout, corporate record or schema was changed. No Q12 or
email data was imported/generated. No persistent operational tables were created.
Separate application storage is approved in principle but unnecessary for this slice.

## Verified

- Backend: 57 tests passed, including self-scope pinning, manager denial, disabled
  routes, message-level participation across shared threads, BCC privacy, model
  source-ID validation, bounded text and honest unconfigured-AI failures.
- Frontend: 32 tests passed, including five employee sections, manager navigation,
  subject/persona clearing, empty inbox/Q12 and honest unavailable-AI behavior.
- TypeScript check and production build passed; Python dependency check passed.
- Read-only live schema/population check confirmed mapped source columns.
- Read-only API smoke passed against PostgreSQL: 2,408 Active personas; sampled
  employee had 12 goals, 0 tasks, 8 training rows, 12 reviews and 12 self-assessments;
  sampled manager had 10 eligible direct reports. Self and role/subject denial
  checks passed. Live email messages and Q12 survey waves/results were empty.
- Local launcher started both loopback services on ports 8000 and 5173. The final
  backend mapping changes were loaded by restarting only the owned launcher.
- Private repository creation and approved GitHub owner were verified via API.

## Not verified

Live model calls/API credentials, populated PostgreSQL Q12/email journeys, manual
browser rendering and the final report format. Browser automation could not open
the app due to tool errors; automated React rendering and compilation passed.
No public deployment or genuine login is claimed. The original Streamlit demo
continues independently and its Azure credentials have not been transferred.

## Follow-up decisions

Whether to prepare/import the existing Q12 fixtures, which existing source can
supply synthetic email messages, approved AI provider/configuration, final report
sections, and future manager access to additional record categories. Do not infer
permission to generate/load records from approval of an email viewer.

## Recommended Next Steps

Proposed task: Restore populated Q12 in the shared database through a reviewed,
additive fixture import. Objective: preserve the prior employee engagement journey
using PostgreSQL. Prerequisite: explicit approval for import preparation/execution
and validation against existing group/question IDs. This recommendation does not
authorize importing, regenerating or overwriting data.
