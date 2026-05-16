#!/usr/bin/env bash
# Get beats, pressures, arcs, connectors (the mechanical pipeline)
set -euo pipefail

TURN="${1:?Usage: get-mechanics.sh <turn>}"

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "=== Turn $TURN — Mechanics ==="
echo ""

echo "--- Rules Intent ---"
echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0].rules_intent"
echo ""

echo "--- GM Beat ---"
USER=$(echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0].prompts.progress.user // empty")
if [ -n "$USER" ]; then
  BEAT=$(echo "$USER" | awk '
    /^## gm_beat$/ { found=1; next }
    found && /^## (deescalate|Current Pressures|last_turn_narration|rules_stakes|gm_beat|pending_beat)$/ { found=0 }
    found && NF
  ')
  if [ -n "$BEAT" ]; then
    echo "$BEAT"
  else
    echo "(empty)"
  fi
else
  echo "(no prompts — compaction entry)"
fi
echo ""

echo "--- Deescalate ---"
if [ -n "$USER" ]; then
  DEESC=$(echo "$USER" | awk '
    /^## deescalate$/ { found=1; next }
    found && /^## (Current Pressures|last_turn_narration)$/ { found=0 }
    found && NF
  ')
  if [ -n "$DEESC" ]; then
    echo "$DEESC"
  else
    echo "(empty)"
  fi
fi
echo ""

echo "--- Current Pressures ---"
if [ -n "$USER" ]; then
  PRESS=$(echo "$USER" | awk '
    /^## Current Pressures$/ { found=1; next }
    found && /^## (last_turn_narration|gm_beat)$/ { found=0 }
    found && NF
  ')
  if [ -n "$PRESS" ]; then
    echo "$PRESS"
  else
    echo "(empty)"
  fi
fi
echo ""

echo "--- Rules Stakes ---"
if [ -n "$USER" ]; then
  STAKES=$(echo "$USER" | awk '
    /^## rules_stakes$/ { found=1; next }
    found && /^## (gm_beat|last_turn_narration)$/ { found=0 }
    found && NF
  ')
  if [ -n "$STAKES" ]; then
    echo "$STAKES"
  else
    echo "(empty)"
  fi
fi
echo ""

echo "--- Campaign Arc (from narrate) ---"
NARRATE=$(echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0].prompts.narrate.user // empty")
if [ -n "$NARRATE" ]; then
  ARC=$(echo "$NARRATE" | awk '
    /^### Campaign Arc$/ { found=1; next }
    found && /^### Characters$/ { found=0 }
    found && NF
  ')
  if [ -n "$ARC" ]; then
    echo "$ARC"
  else
    echo "(empty)"
  fi
else
  echo "(no prompts — compaction entry)"
fi
echo ""

echo "--- State Deltas ---"
echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0] |
  .state_diff[] |
  \"  [\(.from_stream)] \(.domain).\(.field) = \(.value)\"" 2>/dev/null || echo "  (none)"
echo ""

echo "--- Connectors ---"
echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0] |
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
  )" 2>/dev/null || echo "  (none)"
echo ""

echo "--- Summary ---"
echo "$DATA" | jq -r "[.turns[] | select(.turn == $TURN) | select(.streams | length > 0)][0] |
  \"  streams: \(.streams | keys | join(\", \"))
  has_rejections: \(.has_rejections)
  has_retries: \(.has_retries)
  has_errors: \(.has_errors)
  total_tt: \(.total_tt // \"N/A\")
  tokens_in: \(.total_tokens_in_display // \"N/A\")
  tokens_out: \(.total_tokens_out_display // \"N/A\")\""
