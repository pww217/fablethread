#!/usr/bin/env bash
# Get state diffs for a turn
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" deltas "$@"
