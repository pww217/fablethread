#!/usr/bin/env bash
# Get prompts + outputs + connectors for a turn
set -euo pipefail

TURN="${1:?Usage: get-props-connector.sh <turn>}"

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

for STREAM in rules narrate scene state progress; do
  echo "--- $STREAM ---"
  echo ""
  echo "--- USER ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.user"
  echo ""
  echo "--- OUTPUT ---"
  echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) | .prompts.$STREAM.output"
  echo ""
done

echo "--- Connectors ---"
echo "$DATA" | jq -r ".turns[] | select(.turn == $TURN) |
  .connectors[] |
  \"before_stage: \(.before_stage)\" +
  (
    if .segments and (.segments | length) > 0 then
      (
        .segments[] |
        \"  from=\(.from) label=\(.label)\" +
        (
          .lines[] |
          \"    \(.k) = \(.v)\"
        )
      )
    else
      \"  (none)\"
    end
  )
"
