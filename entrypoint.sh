#!/bin/sh
# Runs main.py once a day at RUN_AT (default 00:00, in the container's TZ).
#
# Any command passed to the container replaces the scheduler, so a manual
# one-shot is still just: docker compose run --rm pricechecker python main.py
set -eu

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

RUN_AT="${RUN_AT:-00:00}"
RUN_ON_START="${RUN_ON_START:-false}"

log() {
    echo "[pricechecker] $(date '+%Y-%m-%d %H:%M:%S %Z') $*"
}

runOnce() {
    log "running check"
    if python main.py; then
        log "check finished"
    else
        log "check failed with status $?"
    fi
}

if ! date -d "today $RUN_AT" >/dev/null 2>&1; then
    log "invalid RUN_AT '$RUN_AT', expected HH:MM"
    exit 1
fi

if [ "$RUN_ON_START" = "true" ]; then
    runOnce
fi

while true; do
    now=$(date +%s)
    next=$(date -d "today $RUN_AT" +%s)
    if [ "$next" -le "$now" ]; then
        next=$(date -d "tomorrow $RUN_AT" +%s)
    fi
    log "next check at $(date -d "@$next" '+%Y-%m-%d %H:%M:%S %Z')"
    sleep $((next - now))
    runOnce
done
