# Verify GW sandbox deployment

Date: 2026-11-04

Implemented: Tested the user-provided `gw-sb-11` as a deployment candidate; Azure
returned HTTP 404 `DeploymentNotFound`. It is the resource name. Then tested the
existing employee demo's configured default candidate `gpt-5.4-mini` on the same
user-provided resource. Azure accepted it and produced a completed visible response.
Saved this verified deployment privately as `GW_AZURE_MODEL` and restarted only
the confirmed owned combined-app launcher.

Verified: A minimal live Azure response and a separate live `responses.parse`
request using the actual `WorkspaceAnswer` schema both completed successfully.
The latter used the existing client/API version and 2,200-token output cap.
Only connection-test text was sent; no employee records or keys were printed.
No application source code, database records or schema changed. No Git commit/push.

Not verified: A source-backed chatbot response through the running app. The existing
PostgreSQL TCP target still returns `TimeoutError`, so permitted employee records
cannot currently be retrieved. Do not represent the connection/schema probes as
email/Q12 answer verification. Earlier functional tests/data checks remain dated
evidence rather than a claim that the database is currently reachable.

Follow-up decisions: Restore the existing PostgreSQL server/network connection;
no connection credentials, endpoints or firewall settings were changed here.

## Recommended Next Steps

After PostgreSQL is reachable, run `scripts/check_integration.py`, then the bounded
employee/manager email+Q12 live citation smoke checks. Do not regenerate or reload
the already-imported records to troubleshoot a network timeout.
