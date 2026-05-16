#!/usr/bin/env bash
# Get a summary of all turns
set -euo pipefail

DATA=$(curl -s http://127.0.0.1:8765/turn_viewer/data)

echo "=== Turn Viewer Summary ==="
echo ""

echo "$DATA" | jq -r '.turns[] |
  "Turn \(.turn): streams=\(.streams | keys | join(", ")) user=\(.user_input // "" | .[0:60])
    tokens: in=\(.total_tokens_in_display) out=\(.total_tokens_out_display) tt=\(.total_tt)
    rules_intent: \(.rules_intent.intent // "" | .[0:80])
    deltas: \(.state_diff | length)
    connectors: \(.connectors | length)"
' 2>/dev/null || echo "(server not running or no data)"
