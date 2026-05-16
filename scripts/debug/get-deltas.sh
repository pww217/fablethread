#!/usr/bin/env bash
# Get state diffs for a turn
set -euo pipefail

TURN="${1:?Usage: get-deltas.sh <turn>}"

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "=== Turn $TURN — State Deltas ==="
echo ""

echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) |
  .state_diff[] |
  \"[\(.from_stream)] \(.domain).\(.field) = \(.value)\"\
"

echo ""
echo "--- Rejections ---"
REJ=$(echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .rejections // [] | length")
if [ "$REJ" -gt 0 ]; then
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .rejections[] | \"  \(.domain).\(.field): \(.reason)\""
else
  echo "  (none)"
fi
