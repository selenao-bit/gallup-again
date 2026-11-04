#!/bin/bash
# Compatible with the Bash 3.2 supplied by macOS. No installation or DB probes.
set -u

backend_pid=''
frontend_pid=''

finish() {
    status=$?
    trap - EXIT
    if [ -n "$backend_pid$frontend_pid" ]; then cleanup; fi
    if [ "$status" -ne 0 ] && [ "$status" -ne 130 ] &&
       [ "$status" -ne 143 ] && [ "$status" -ne 129 ] &&
       [ "${LOCAL_LAUNCHER_PAUSE_ON_ERROR:-0}" = 1 ] && [ -t 0 ]; then
        printf '\nLauncher stopped (exit %s). Press Return to close.\n' "$status"
        read -r _
    fi
    exit "$status"
}
trap finish EXIT

fail() {
    printf '[launcher] Error: %s\n' "$*" >&2
    exit 1
}

OPEN_BROWSER=1
case "${1:-}" in
    '') ;;
    --no-browser) OPEN_BROWSER=0 ;;
    *) fail 'Usage: scripts/start.sh [--no-browser]' ;;
esac
[ "$#" -le 1 ] || fail 'Usage: scripts/start.sh [--no-browser]'

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
cd "$PROJECT_ROOT" || exit 1
PYTHON="$PROJECT_ROOT/.venv/bin/python"
APP_URL='http://127.0.0.1:5173'

# Finder may have a minimal PATH. Use installed Homebrew tools if needed.
for directory in /opt/homebrew/bin /usr/local/bin; do
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        PATH="$PATH:$directory"
    fi
done
export PATH

for executable in node npm curl lsof; do
    command -v "$executable" >/dev/null 2>&1 ||
        fail "Missing $executable. See README.md for prerequisites; ensure it is on PATH."
done
[ -x "$PYTHON" ] || fail 'Missing executable .venv/bin/python. See README.md for the existing root environment setup.'
[ -x node_modules/.bin/vite ] ||
    fail 'Missing frontend dependencies. Run npm ci at the repository root; see README.md.'

# Check imports without loading application configuration or printing secrets.
env -u PYTHONPATH "$PYTHON" -c '
import sys
if sys.version_info < (3, 11):
    sys.exit(1)
import fastapi, pydantic, sqlalchemy, psycopg, uvicorn, dotenv, openai
' >/dev/null 2>&1 || fail 'Python 3.11+ and backend dependencies are required in .venv. See README.md.'

for port in 8000 5173; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        fail "Port $port is already occupied. Stop that service yourself or use the manual startup instructions. No services were started."
    fi
done

group_alive() {
    kill -0 -- "-$1" 2>/dev/null
}

cleanup() {
    trap '' INT TERM HUP
    printf '\n[launcher] Stopping services started by this launcher...\n'
    for pid in "$backend_pid" "$frontend_pid"; do
        [ -z "$pid" ] || kill -TERM -- "-$pid" 2>/dev/null || :
    done
    # npm has a Vite child: stop the entire owned group, even if npm exits first.
    for ((attempt = 0; attempt < 5; attempt++)); do
        alive=0
        for pid in "$backend_pid" "$frontend_pid"; do
            if [ -n "$pid" ] && group_alive "$pid"; then alive=1; fi
        done
        [ "$alive" -eq 1 ] || break
        sleep 1
    done
    for pid in "$backend_pid" "$frontend_pid"; do
        [ -z "$pid" ] || kill -KILL -- "-$pid" 2>/dev/null || :
    done
    [ -z "$backend_pid" ] || wait "$backend_pid" 2>/dev/null || :
    [ -z "$frontend_pid" ] || wait "$frontend_pid" 2>/dev/null || :
    printf '[launcher] Services stopped.\n'
}
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

# Bash job control gives each service its own process group. Cleanup never
# signals the caller's group or searches for unrelated processes by name/port.
set -m
printf '[backend] Starting Uvicorn at http://127.0.0.1:8000\n'
env -u PYTHONPATH "$PYTHON" -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 &
backend_pid=$!
printf '[frontend] Starting npm run dev at %s\n' "$APP_URL"
(
    cd "$PROJECT_ROOT" || exit 1
    exec npm run dev -- --clearScreen false
) &
frontend_pid=$!
# Return foreground commands (including polling sleeps) to the launcher's group
# so a terminal Ctrl+C reaches our trap, rather than just interrupting sleep.
set +m

check_services() {
    for service in backend frontend; do
        if [ "$service" = backend ]; then pid=$backend_pid; else pid=$frontend_pid; fi
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid"
            status=$?
            fail "$service exited unexpectedly (exit $status). Review its output above; see README.md for setup and configuration."
        fi
    done
}

printf '[launcher] Waiting for backend and frontend (up to 60 seconds). Ctrl+C stops both.\n'
ready=0
startup_deadline=$((SECONDS + 60))
while [ "$SECONDS" -lt "$startup_deadline" ]; do
    check_services
    if curl --noproxy '*' --silent --fail --max-time 1 http://127.0.0.1:8000/health >/dev/null 2>&1 &&
       curl --noproxy '*' --silent --fail --max-time 1 "$APP_URL/" >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
[ "$ready" -eq 1 ] || fail 'Startup timed out. Review server output and README.md.'
check_services
printf '\n[launcher] Application ready: %s\n[launcher] Keep this terminal open. Press Ctrl+C to stop both services.\n' "$APP_URL"
if [ "$OPEN_BROWSER" -eq 1 ]; then
    if command -v open >/dev/null 2>&1; then
        open "$APP_URL" || printf '[launcher] Could not open the browser. Open %s manually.\n' "$APP_URL" >&2
    else
        printf '[launcher] Open %s in your browser.\n' "$APP_URL"
    fi
fi

while :; do
    check_services
    sleep 1
done
