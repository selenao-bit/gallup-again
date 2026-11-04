#!/bin/bash
# Finder opens .command files in Terminal. Exec forwards signals directly.
PROJECT_ROOT="$(cd -- "$(dirname -- "$0")" && pwd)" || exit 1
export LOCAL_LAUNCHER_PAUSE_ON_ERROR=1
exec /bin/bash "$PROJECT_ROOT/scripts/start.sh" "$@"
