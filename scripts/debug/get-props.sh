#!/usr/bin/env bash
# Wrapper for `ev.py props`. See ev.py --help.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" props "$@"
