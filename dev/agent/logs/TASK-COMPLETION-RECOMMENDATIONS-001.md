# Completion recommendations (advisory)

Date: 2026-11-04

Implemented: No application changes. Reviewed original repository instructions,
relevant SPEC/ROADMAP sections, combined app README, handoff, current conversation
and record UI code, data-context policy and implemented-status logs. Recommendations
below are proposals, not permission to start new phases or migrations.

Verified from code/docs: Five employee tabs, manager preparation, source-cited AI,
review chart and synthetic email/Q12 integration exist. Current report is provisional;
actual login, durable application records, audit and public hosting remain incomplete.
Conversation answers are independent despite the displayed session history.

Recommended order:
1. Preserve the latest working code in a durable project directory and prepare a
   reviewed Git backup; actual commit/push needs user request.
2. Finish the report workflow: define review period and report sections; evidence
   summary, recorded progress, development/support, discussion and follow-up, with
   citations/gaps and editable downloadable output. Confirm manager field access.
3. Improve record presentation using category-specific cards, period/category
   filters, readable permitted email threads and citation-to-record navigation.
4. Make chat usable across a conversation with bounded history, scope checks on
   every turn, clear waiting/error/retry/cancel states and measured response times.
   Do not expose unvalidated streamed text as a completed cited answer.
5. Define and approve separate app-owned storage for drafts, notes, sessions and
   minimal access audit; no corporate schema changes or raw-source edits implied.
6. Add real sign-in and explicit account/employee mapping, then stable protected
   hosting; scope controls must be server-enforced. Public-tunnel approval remains
   pending and is not inferred from this advice request.
7. Finish with representative employee/manager journeys, accessibility/loading
   checks, source traceability/transparency and a repeatable capstone demo script.

A proposed first-release acceptance story: sign in as employee, inspect a selected
period, ask a cited question, then sign in as an authorized manager, prepare/edit/
export a sourced draft and return later to the saved version. Do not require new HR
analytics, rankings, real mailbox sync or extensive AI benchmarks for that slice.

Not verified: No new tests, live data probes, quality benchmarks, hosting/provider
selection or cost estimates. Earlier passing tests are historical evidence, not
rerun by this advisory review.

Follow-up decisions: Final report template/period rules and whether the immediate
target is a class demonstration or a hosted ongoing pilot. Prioritize one bounded
implementation next; persistent tables, login/provider setup, hosting, commits and
pushes each retain their existing approval boundaries.

References consulted:
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://developers.openai.com/api/docs/guides/latency-optimization
