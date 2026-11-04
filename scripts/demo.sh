#!/bin/bash
# Enable synthetic personas; preserve private .env and process AI configuration.
set -eu
SPRINT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export DEMO_IDENTITY_ENABLED=true
# Settings defaults to simulated only when neither process nor .env config selects a mode.
exec "$SPRINT_ROOT/scripts/start.sh" "$@"
