# Chatbot latency and review chart

Date: 2026-11-04

Implemented:
- Added `frontend/src/ReviewChart.tsx` and integrated it into My reviews through
  `EmployeeWorkspace.tsx`. Connects chronological recorded overall ratings on the
  existing fixed 1–5 scale. Immediate SVG tooltips show period and score on mouse
  hover, keyboard focus or tap/click. Missing ratings are not fabricated or bridged.
- Added chart styles in `frontend/src/styles.css` and focused functional tests in
  `ReviewChart.test.tsx`.
- Extended `backend/app/config.py` to accept the model-supported explicit `none`
  reasoning setting. Verified the existing GW Azure `gpt-5.4-mini` deployment
  accepts it, then changed only this private setting in the combined app `.env`.
  Provider routing, employee authorization and citation validation remain active.
- Updated provider configuration tests, `.env.example`, README and context policy.
  `scripts/check_live_ai.py` now prints request durations without answer narratives,
  credentials or provider payloads. No dependencies added, data/schema writes,
  commits or pushes.

Verified:
- Same actor (69), same training question: low reasoning 6.27s total, including
  4.69s Azure generation, 0.58s persona lookup, 0.26s role lookup and 0.64s bundle.
  `none` comparison: 5.64s total, including 3.89s Azure generation, 0.56s persona,
  0.26s role and 0.83s bundle. Both returned four validated citations. Reasoning
  tokens changed from 49 to zero. These are single samples, not a latency guarantee.
- Restarted only the confirmed owned combined-app launcher. Current local app:
  http://localhost:5173 (launcher session 23217; backend PID 22415 at verification).
- Live source-backed requests through frontend proxy: employee email + Q12 5.61s,
  six cited sources; manager shared email + Q12 + training 5.62s, eleven cited
  sources. Both completed and all returned citation IDs matched supplied sources.
- Live employee review API: three records, periods 2026-Q1 through Q3, all three
  overall scores numeric and within 1–5; correct input format for the chart.
- 89 backend tests passed; 39 frontend tests passed; TypeScript and production
  build passed; git diff --check passed. Chart tests cover hover/focus tooltips,
  chronological connections, fixed scale, and missing-score gaps.

Not verified:
- Actual visual browser rendering/hover: Chrome tab creation failed in available
  browser automation. Component interaction tests passed, but this is not visual QA.
- Broad model answer-quality or latency benchmarks were not run. Sandbox/network
  load can still affect timing; no quota/billing settings were changed.

Follow-up decisions: None required for this change. Actual login and report-template
selection remain previously deferred work, outside this task.

Reference: official OpenAI model documentation confirms `none` reasoning support:
https://developers.openai.com/api/docs/models/gpt-5.4-mini

Working app location: /private/tmp/gallup-again. Original repository receives only
this task log; the original employee demo was not changed.
