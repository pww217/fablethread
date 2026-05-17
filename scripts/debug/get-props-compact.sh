#!/usr/bin/env bash
# Get prompts + outputs for a specific stream on a turn, skipping system prompts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" compact "$@"
