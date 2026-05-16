#!/usr/bin/env bash
# Get prompts + outputs for ALL streams on a turn
set -euo pipefail

TURN="${1:?Usage: get-turn.sh <turn>}"

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

for STREAM in rules narrate scene state progress; do
  echo "--- BEGIN $STREAM PIPELINE ---"
  echo ""
  echo "--- SYSTEM ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.system"
  echo ""
  echo "--- USER ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.user"
  echo ""
  echo "--- OUTPUT ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.output"
  echo ""
  echo "--- END $STREAM PIPELINE ---"
  echo ""
done
