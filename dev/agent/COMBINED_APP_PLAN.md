# Combined application integration proposal

Date: 2026-11-03
Status: Initial integration implemented after subsequent user decisions. See the
completion log and root README for actual delivery and verification limits. No
corporate database changes or provider registrations have been performed.

## User-confirmed direction

- New private repository: `selenao-bit/gallup-again`.
- Actual login and account creation were subsequently deferred by the user.
  Use explicit, impersonable synthetic persona selection for this version.
- Existing PostgreSQL corporate dataset is the shared source.
- Focus on employee and manager experiences. HR/company screens and AI evaluation
  statistics are deferred.
- Preserve Selena's five current tabs, including the preparation controls within
  Team engagement. Do not restore the removed review-preparation or My voice tabs.
- Combine Lucas's manager preparation foundation with suitable Kevin dashboard
  and access-control patterns.
- North Stars, orchestration details and the report template still need definition.
- Synthetic PostgreSQL email viewing approved: a persona sees only messages
  they sent or received. Direct-report dashboard access does not grant inbox access.
  Real mailbox connections and email sending remain outside this slice.
- User subsequently approved separate application-owned storage for account
  mappings, sessions and audit activity. Exact storage location/schema and any
  migration execution remain to be designed; no corporate schema changes implied.

## Sources inspected

- Lucas: separate clone of `Lukeryan360/Capstone_Project`; README, repository rules,
  relevant identity/access and implementation contracts, architecture and roadmap,
  backend access policy, PostgreSQL repository and assistant code, SQL DDL.
- Kevin: separate clone of `kevinete4/manager-prep-assistant`; README and relevant
  specification, package manifests, dashboard service/UI and mock-session code.
- Selena: current employee demo README, app UI, data helpers and AI wrapper at
  `/Users/selenao/gallup_again_demo/gallup_again_employee_v2`.
- No `dev/personal/` contents inspected. No live database queried in this review.

## Proposed structure

Use Lucas's React/TypeScript and FastAPI application as the base, retaining its
read-only PostgreSQL boundary. Port Selena's employee presentation and shared
calculations into React and backend services. Reuse Kevin's useful dashboard,
provider and authorization patterns selectively; do not merge his SQLite models,
seed scripts or mock login into the shared corporate dataset.

Do not publish all three repositories wholesale. Prepare a reviewed application
file list that excludes private configuration, personal notes, local saved input,
IDE files, environments and unrelated data-generation material. Preserve source
provenance and inspect applicable licenses before copying code into the new repo.
Leave the original checkouts and the currently running employee demo intact.

## Employee experience

1. My work and goals: own goals, tasks, projects and training.
2. My reviews: existing review ratings/history on the established 1–5 scale and
   own self-assessments. Do not generate new performance ratings.
3. Team engagement (Q12): existing group/wave selection, charts, distributions,
   synthetic benchmark labels, discussion questions and AI discussion preparation.
   Preserve minimum-response and explicit suppression checks.
4. Ask my record: own permitted records, conversation state and source references.
5. What is and isn't used: permitted record counts and accurate exclusions.

Replace the employee picker with identity-derived scope. Managers may need both
their own employee workspace and their direct-report workspace; confirm that
dual access is desired before finalizing navigation.

## Manager experience

- Current direct-report list, scoped on the server using `employees.supervisor_id`.
- Selected employee header and evidence overview based on verified records.
- Recent completed goals/training and task context adapted from Kevin's compact
  dashboard pattern. Do not fabricate feedback/recognition to fill his feed.
- Start the Conversation: on-demand questions, bounded retrieval, structured
  answers, source labels, data gaps and employee scope pinned by backend code.
- Prepare with AI: editable, cited draft based on the selected employee and
  period; proposed sections are context, accomplishments, goal/work progress,
  development and support, discussion questions, proposed follow-up, and sources
  and gaps. Follow-up is discussion material, not a persisted action tracker.
- Never generate rankings or employment recommendations.

The proposed report sections and manager visibility into review/self-assessment
fields need confirmation. Private manager notes, peer feedback and email content
are not implicitly enabled by combining applications.

## Source limitations and verification gates

- Lucas's implemented assistant accepts a narrow set of task/training questions;
  it is not already a general RAG orchestrator. His live-model adapter exists but
  live operation is not established by reading code.
- Kevin's AI/chat and report button are unfinished. His mock session is not SSO.
- Kevin's role expectations, commitments, metrics, development plans and voice
  records have no established equivalent in the shared schema. Omit unsupported
  sections rather than infer fields or migrate his synthetic dataset.
- PostgreSQL DDL contains goals, reviews, self-assessments and Q12 definitions;
  this does not verify live schema compatibility or population. Existing Q12
  fixtures are not proof those rows are loaded into PostgreSQL.
- `recognition_logs` is empty in the reviewed DDL; do not treat it as an available
  recognition feed. Goal dates are not automatically completion timestamps.
- Complete a read-only live schema/population check before implementing mappings.
  Missing records must produce empty/unavailable states. Data loading or schema
  changes require separate explicit approval.
- Current persona mapping in Lucas's code differs from README examples. Genuine
  identity bindings must use verified employee IDs, not either sample mapping.

## Authentication proposal and dependencies

Use provider-validated OpenID Connect identities and backend-managed sessions.
Map approved provider identities to explicit corporate employee IDs and app roles
on the server. Stable issuer/subject identifiers identify accounts; email alone
must not permanently identify or automatically link accounts across providers.
Unknown accounts receive no corporate access. Recheck active status and current
direct-report edges on data requests. Demo headers and mock-login routes must not
bypass genuine authentication in the combined app.

Provider app registrations, allowed account/tenant policy and callback URLs are
required before a real end-to-end login can be verified. Keep client secrets
server-side. Provider credentials must be entered privately, not supplied in chat.
Decide local-only versus hosted first verification before fixing callback URLs.

Start with sign-in scopes. Reading/sending email requires separately approved
permissions and data-category policy; choosing Microsoft/Google does not grant
mailbox access.

Sessions, account bindings and audit records are application-owned operational
data. The user approved separate storage for these records after this proposal.
Define the location and concrete migration design before executing changes. Account
allowlist versus persistent provisioning, audit metadata, employee-visible prep
activity, session expiry/revocation and retention need a defined contract.

References: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect),
[Microsoft identity scopes](https://learn.microsoft.com/en-us/entra/identity-platform/scopes-oidc).

## Proposed implementation order after decisions

1. Establish the reviewed new repository baseline and approved identity/storage
   contract; preserve source provenance and existing working behavior.
2. Implement genuine login, explicit account bindings, session/logout and backend
   self/direct-report permissions. Verify denied, unmapped and expired sessions.
3. Port the five employee tabs onto verified PostgreSQL services, checking record
   scoping, review scale and Q12 disclosure rules.
4. Add manager overview and source-backed retrieval using the same services and
   scope enforcement, followed by cited chat and editable draft reports.
5. Verify employee/manager journeys, access denial, provider callbacks and AI smoke
   paths. Clearly distinguish mocked tests from live-provider/model verification.

This sequence is a proposal, not permission to start further roadmap phases.

## Decisions needed before dependent implementation

- Google first, Microsoft first, or both; Microsoft tenant/account restrictions.
- Approved people, stable account bindings, corporate IDs and role assignments.
- Concrete operational persistence design (separate storage approved in principle).
- First login verification target and provider registrations.
- Manager review/self-assessment visibility and Q12 permitted group scope.
- Report sections; defer North Stars until a concrete source and definition exist.
- AI provider configuration: employee demo currently uses Azure; Lucas's adapter
  uses direct OpenAI. Confirm the authorized shared provider before live calls.
