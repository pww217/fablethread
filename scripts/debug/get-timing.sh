#!/usr/bin/env bash
# Get tokens + timing info for all turns
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" timing "$@"
