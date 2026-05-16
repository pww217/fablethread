#!/usr/bin/env bash
# Get tokens + timing info for all turns
set -euo pipefail

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "=== Turn Viewer — Timing & Tokens ==="
echo ""

echo "$DATA" | jq -r '.turns[] |
  "Turn \(.turn):
    total_tt: \(.total_tt // "N/A")
    tokens_in: \(.total_tokens_in_display // "N/A")
    tokens_out: \(.total_tokens_out_display // "N/A")",
  (
    if .streams and (.streams | keys | length) > 0 then
      .streams | to_entries[] |
      "    \(.key): \(.value.tt)"
    else
      "    (no streams)"
    end
  )
'
