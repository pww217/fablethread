#!/usr/bin/env bash
# Get a single prompt (system or user) for a stream on a turn
set -euo pipefail

TURN="${1:?Usage: get-prompt.sh <turn> <stream> <system|user|output>}"
STREAM="${2:?Usage: get-prompt.sh <turn> <stream> <system|user|output>}"
PART="${3:?Usage: get-prompt.sh <turn> <stream> <system|user|output>}"

case "$STREAM" in
  rules|narrate|scene|state|progress) ;;
  *) echo "Unknown stream: $STREAM" >&2; exit 1 ;;
esac

case "$PART" in
  system|user|output) ;;
  *) echo "Unknown part: $PART (use: system|user|output)" >&2; exit 1 ;;
esac

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "--- Turn $TURN — $STREAM $PART ---"
echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.$PART"
