#!/usr/bin/env bash
# Get JSON outputs from all streams on a turn
set -euo pipefail

TURN="${1:?Usage: get-outputs.sh <turn>}"

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

for STREAM in rules narrate scene state progress; do
  echo "--- $STREAM output ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.output" | jq '.' 2>/dev/null || echo "(empty)"
  echo ""
done
