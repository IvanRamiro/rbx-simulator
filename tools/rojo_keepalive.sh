#!/bin/zsh
# Serves the project with Rojo and starts it again whenever it stops.
# Rojo 7.7.1 crashes when a folder under src is deleted while it serves, and then Studio quietly stops syncing.
# Run this from the project folder instead of `rojo serve`:
#     ./tools/rojo_keepalive.sh
# Stop it with Ctrl+C (twice if Rojo is mid-start). Its output also goes to ~/Library/Logs/rojo-qi-aura.log.
cd "${0:A:h}/.." || exit 1
LOG="$HOME/Library/Logs/rojo-qi-aura.log"
PORT=34872

if /usr/sbin/lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Rojo is already serving on port $PORT. Stop that one first (Ctrl+C in its terminal), then run this again."
    exit 1
fi

trap 'echo; echo "Stopped."; exit 0' INT TERM
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') starting rojo serve" | tee -a "$LOG"
    rojo serve default.project.json 2>&1 | tee -a "$LOG"
    echo "$(date '+%Y-%m-%d %H:%M:%S') Rojo stopped; starting it again in 2 seconds (Ctrl+C to quit)" | tee -a "$LOG"
    sleep 2
done
