#!/bin/bash
# Compatible with the Bash 3.2 supplied by macOS. Targets listeners by port.
set -u

fail() {
    printf '[stop] Error: %s\n' "$*" >&2
    exit 1
}

[ "$#" -eq 0 ] || fail 'Usage: scripts/stop.sh'
command -v lsof >/dev/null 2>&1 || fail 'Missing lsof; ensure it is on PATH.'

listener_pids() {
    local result status
    result="$(lsof -nP -iTCP:8000 -iTCP:5173 -sTCP:LISTEN -t)"
    status=$?
    # lsof returns 1 when no matching listeners exist.
    [ "$status" -le 1 ] || return "$status"
    if [ -n "$result" ]; then printf '%s\n' "$result" | sort -un; fi
}

signal_listeners() {
    local signal pid
    signal=$1
    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        printf '[stop] Sending %s to PID %s.\n' "$signal" "$pid"
        # A listener may exit between discovery and signaling.
        kill -"$signal" "$pid" 2>/dev/null || :
    done <<< "$pids"
}

pids="$(listener_pids)" || fail 'Could not inspect ports 8000 and 5173.'
if [ -z "$pids" ]; then
    printf '[stop] No listeners on ports 8000 or 5173; already stopped.\n'
    exit 0
fi

signal_listeners TERM
for ((attempt = 0; attempt < 5; attempt++)); do
    pids="$(listener_pids)" || fail 'Could not inspect ports 8000 and 5173.'
    [ -n "$pids" ] || break
    sleep 1
done

# Discover again so changed PIDs and multiple listeners are handled.
pids="$(listener_pids)" || fail 'Could not inspect ports 8000 and 5173.'
if [ -n "$pids" ]; then
    signal_listeners KILL
    sleep 1
fi
pids="$(listener_pids)" || fail 'Could not inspect ports 8000 and 5173.'
[ -z "$pids" ] || fail "Listeners remain (PIDs: $pids). Check process permissions or automatic restarts."
printf '[stop] Ports 8000 and 5173 are free.\n'
