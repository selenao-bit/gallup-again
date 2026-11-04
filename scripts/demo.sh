#!/bin/bash
# Sprint-only opt-in. Existing standard launcher remains unchanged.
set -eu
SPRINT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export DEMO_IDENTITY_ENABLED=true
export ASSISTANT_MODE="${ASSISTANT_MODE:-simulated}"
exec "$SPRINT_ROOT/scripts/start.sh" "$@"
