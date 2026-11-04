# User-provided GW Azure endpoint

Date: 2026-11-04

Implemented: Saved the user-provided resource root
`https://gw-sb-11.openai.azure.com/` in private Azure configuration, selected Azure
mode, and moved the already-saved GW key from the direct-provider variable to
`GW_AZURE_OPENAI_KEY`. The credential value was preserved and not displayed.
Restarted only the confirmed owned combined-app launcher.

Verified: Settings parse/normalization and private credential preservation passed.
Authenticated GET `/openai/v1/models` returned HTTP 200 using the Azure key.
The result was a broad 480-model catalog, not a verified deployment listing;
no inference model/deployment was selected from it. No employee records were sent
to Azure in this task. No database writes or source code changes.

Not verified: Azure inference and sourced responses; no deployment name is saved.
The previously provided default in the old employee wrapper is not deployment
verification. No Git commit or push. Existing handoff ZIP remains an earlier
source snapshot and intentionally contains no private configuration.

Runtime checks: both local liveness endpoints returned OK and the backend was
restarted in Azure mode. Persona loading returned 503 because PostgreSQL
connections now time out (`ConnectionTimeout`), independently of Azure metadata
authentication. No database settings or records were changed. Restoring that
existing connection is also required for a sourced chatbot smoke check.

Follow-up decisions: User has withdrawn the Claude suggestion. Continue GW/Azure.
Need the actual deployment name from GW configuration before bounded live checks.

## Recommended Next Steps

Save the user-confirmed deployment name privately, restart the owned backend and
run the existing bounded employee/manager email+Q12 live citation smoke script.
