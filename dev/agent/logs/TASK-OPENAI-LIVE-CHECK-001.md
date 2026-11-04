# Saved-key activation and live smoke attempt

Date: 2026-11-03

Implemented: Restarted the owned combined-app launcher to read the user-saved
private key. Added `scripts/check_live_ai.py` for two bounded end-to-end requests
through the frontend proxy, requiring actual email and Q12 citations. No key is
read or printed by the smoke script. No application code or database changes.

Verified: The configured mode is direct OpenAI and model is `gpt-4.1-mini`. A key
is present, matches the saved `.env` value, has no surrounding whitespace and has
no process-environment override. Key contents, prefixes and lengths were not
printed. The first employee request returned app HTTP 503. A minimal provider
diagnostic returned `AuthenticationError`, HTTP 401, code `invalid_api_key`.
Only sanitized error class/status/code/type were inspected. Official OpenAI error
guidance was checked: https://developers.openai.com/api/docs/guides/error-codes.

Not verified: Successful live response/citations. The first smoke request failed
before model generation, so the manager request was not sent. No fallback answer
or live success claimed. No repeat verification suite was needed because app
behavior was not edited. No Git commit/push; private configuration untouched.

Follow-up decisions: Asked whether the credential came from OpenAI Platform or
the GW/Azure sandbox. Direct OpenAI rejected the saved credential. Do not assume
the provider or replace/generate a credential automatically. User must privately
provide a valid credential for the selected provider; Azure additionally needs
its endpoint/deployment configuration if that is the intended service.

## Recommended Next Steps

Resolve the credential's provider, configure that connection privately, and rerun
the bounded live smoke checks. Keep keys out of source, logs and chat.
