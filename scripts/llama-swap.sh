#!/usr/bin/env bash
# scripts/llama-swap.sh
#
# Check if llama-swap is already listening on :8080; start it if not.
# Config and logs live in ~/.llm/ — independent of any single app.
#
# Usage:
#   bash scripts/llama-swap.sh    # from ccya/ root
#   make llama-swap               # same via Makefile

set -euo pipefail

CFG="$HOME/.llm/llama-swap.yaml"
LOG="$HOME/.llm/logs/llama-swap.log"
HOST=127.0.0.1
PORT=8080

if nc -z "$HOST" "$PORT" 2>/dev/null; then
    echo "  llama-swap  already serving on ${HOST}:${PORT}"
    exit 0
fi

if [ ! -f "$CFG" ]; then
    echo "  llama-swap  ERROR: config not found at $CFG" >&2
    exit 1
fi

mkdir -p "$HOME/.llm/logs"
echo "  llama-swap  starting → ${HOST}:${PORT}"
echo "  llama-swap  config  → ${CFG}"
echo "  llama-swap  log     → ${LOG}"

nohup llama-swap --config "$CFG" --listen "${HOST}:${PORT}" >> "$LOG" 2>&1 &
SWAP_PID=$!
echo "  llama-swap  pid=${SWAP_PID}"

TIMEOUT=30
ELAPSED=0
INTERVAL=2

while ! nc -z "$HOST" "$PORT" 2>/dev/null; do
    if ! kill -0 "$SWAP_PID" 2>/dev/null; then
        echo "  llama-swap  ERROR: process exited unexpectedly — tail ${LOG}" >&2
        tail -20 "$LOG" >&2
        exit 1
    fi
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "  llama-swap  ERROR: timed out after ${TIMEOUT}s — tail ${LOG}" >&2
        tail -20 "$LOG" >&2
        exit 1
    fi
    printf "  llama-swap  waiting... %ds\r" "$ELAPSED"
    sleep "$INTERVAL"
    ELAPSED=$(( ELAPSED + INTERVAL ))
done

echo "  llama-swap  ready (${ELAPSED}s)                    "
