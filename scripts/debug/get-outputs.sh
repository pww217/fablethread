#!/usr/bin/env bash
# Get JSON outputs from all streams on a turn
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" outputs "$@"
