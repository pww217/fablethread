#!/usr/bin/env bash
# All data, including system prompts — one-liner replacement for curl + jq
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" "$@"
