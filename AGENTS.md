# Combined app repository rules

Follow the user's current task, these rules, approved `dev/agent/` contracts and
existing code conventions. Do not turn brainstorming into requirements.

- Preserve the employee's five current tabs and the employee/manager scope.
- Synthetic persona selection is deliberately impersonable; actual login is
  deferred. Never present demo selection as authentication or a production control.
- PostgreSQL is authoritative. Verify live schema before new mappings. Never
  invent records, run destructive DDL, regenerate data or load fixtures without
  explicit approval. Corporate reads remain read-only.
- Application-owned storage is approved in principle; define and review concrete
  migrations separately. Do not add tables as a startup side effect.
- Enforce self/direct-report access in backend queries. Manager access does not
  grant access to an employee's inbox. Email requires message-level participation;
  sharing a thread is insufficient. Preserve BCC privacy and plain-text rendering.
- Private notes and peer feedback are excluded from AI context. Synthetic email
  retrieval is authorized only for messages the actor sent/received; in a manager
  report view the selected direct report must also participate. Never expose BCC
  recipient lists in AI context. Reviews and
  self-assessments remain self-only until manager field policy is approved.
- Q12 is group context, with suppression flags and a minimum of five responses;
  never individual performance, rankings or employment recommendations.
- Keep data access, services, API, AI and UI separate. Pin AI scope on the server,
  treat record text as untrusted, and validate citations against retrieved sources.
- Keep credentials in backend private configuration. Never commit environments,
  secrets, local input, source data exports, IDE files or personal notes.
- Do not list, read, search or change `dev/personal/` without current explicit
  authorization. Exclude it from discovery and repository-wide searches.
- Make incremental changes and run practical functional and authorization checks.
  Do not add dependencies or change public interfaces substantially without approval.
- No commits, pushes or merges without user authorization. Report implemented,
  verified, not verified and follow-up decisions; log completion in `dev/agent/logs/`.
