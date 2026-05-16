#!/usr/bin/env bash
# Get prompts + outputs for a specific stream on a turn
set -euo pipefail

TURN="${1:?Usage: get-props.sh <turn> <stream>}"
STREAM="${2:?Usage: get-props.sh <turn> <stream>}"

case "$STREAM" in
  rules|narrate|scene|state|progress) ;;
  *) echo "Unknown stream: $STREAM (use: rules|narrate|scene|state|progress)" >&2; exit 1 ;;
esac

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "=== Turn $TURN — $STREAM ==="
echo ""
echo "--- SYSTEM ---"
echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.system"
echo ""
echo "--- USER ---"
echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.user"
echo ""
echo "--- OUTPUT ---"
echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.output"
