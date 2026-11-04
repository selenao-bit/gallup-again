# Ask my record stuck loading

Date: 2026-11-04

Implemented:
- Fixed `frontend/src/EmployeeWorkspace.tsx` Conversation request lifecycle. A
  component-wide AbortController was cancelled by React StrictMode's development
  effect cleanup, then reused on submission. The cancelled request skipped both
  error and busy-state updates, leaving Reading permitted records indefinitely.
- Each submission now owns a fresh AbortController held in a ref. Cleanup cancels
  the active request on unmount; a ref guard prevents duplicate submissions. This
  shared Conversation fix also applies to manager and engagement preparation.
- Added two focused tests in `frontend/src/EmployeeWorkspace.test.tsx`; also run the
  existing error test under StrictMode and assert that the submit button recovers.

Verified:
- A new StrictMode success regression test failed against the original code with
  the disabled Reading permitted records button still present. After the fix it
  passes. Error recovery and cancellation when leaving the section pass too.
- All 41 frontend tests, TypeScript check and production build passed.
  git diff --check passed. No backend changes were required.
- Safari's existing localhost:5173 app, selected synthetic employee Michael Haney:
  clicked the training starter question, submitted Prepare with AI, observed the
  loading state change to a source-cited live answer and the submit button recover.
  Saved screenshot /private/tmp/ask-my-record-fixed.png with the answer visible.
- One bounded direct baseline goal question for actor 69 returned a validated
  answer in 6.91s (5.22s Azure generation, four citations). This confirms that normal
  model generation still takes seconds, separately from the indefinite UI bug.

Not verified:
- Every persona/question and all browsers were not exercised. The Safari result
  and StrictMode regression are targeted evidence, not a universal latency promise.
- Backend test suite was not rerun for this frontend-only fix; previous 89-test
  result remains dated evidence. No data, schema, secrets or AI settings changed.

Follow-up decisions: None required. Changes run through the existing frontend
server's hot reload; a page refresh obtains a fresh app state if needed. No commit
or push. Working app is /private/tmp/gallup-again; original repository only receives
this log.
