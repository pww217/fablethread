#!/usr/bin/env bash
# scripts/mlx-serve.sh
#
# Check if mlx_lm.server is already listening; start it if not.
# Host, port, and model are read from config.yaml (llm.*).
# Cache/logging knobs come from config.yaml (mlx.*).
#
# Usage:
#   bash scripts/mlx-serve.sh          # from ccya/ root
#   make mlx-serve                     # same via Makefile
#
# Called automatically by `make run` and `make dev`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CFG="$REPO_DIR/config.yaml"
LOG="$REPO_DIR/logs/mlx-server.log"

# ---------------------------------------------------------------------------
# Read config (python3 is always available; avoids a yq/jq dependency)
# ---------------------------------------------------------------------------
_cfg() {
    python3 - "$CFG" "$1" <<'EOF'
import sys, yaml
from urllib.parse import urlparse

cfg = yaml.safe_load(open(sys.argv[1]))
key = sys.argv[2]

if key == "mlx.host":
    print(urlparse(cfg["llm"]["host"]).hostname)
elif key == "mlx.port":
    print(urlparse(cfg["llm"]["host"]).port)
elif key == "llm.model":
    print(cfg["llm"]["model"])
else:
    # dotted key lookup into mlx section
    parts = key.split(".")
    val = cfg
    for p in parts:
        val = val[p]
    print(val)
EOF
}

MLX_HOST=$(_cfg mlx.host)
MLX_PORT=$(_cfg mlx.port)
MLX_MODEL=$(_cfg llm.model)
MLX_MAX_TOKENS=$(_cfg mlx.max_tokens)
MLX_CACHE_SIZE=$(_cfg mlx.prompt_cache_size)
MLX_CACHE_BYTES=$(_cfg mlx.prompt_cache_bytes)
MLX_LOG_LEVEL=$(_cfg mlx.log_level)
MLX_ENV=$(_cfg mlx.env)
MLX_TEMPLATE_ARGS=$(_cfg mlx.chat_template_args)

# ---------------------------------------------------------------------------
# Check if already running
# ---------------------------------------------------------------------------
if nc -z "$MLX_HOST" "$MLX_PORT" 2>/dev/null; then
    echo "  mlx  already serving on ${MLX_HOST}:${MLX_PORT}"
    exit 0
fi

# ---------------------------------------------------------------------------
# Start server
# ---------------------------------------------------------------------------
echo "  mlx  starting ${MLX_MODEL}"
echo "  mlx  ${MLX_HOST}:${MLX_PORT}  max_tokens=${MLX_MAX_TOKENS}  cache=${MLX_CACHE_SIZE}×$(( MLX_CACHE_BYTES / 1073741824 ))GiB  log=${MLX_LOG_LEVEL}"
if [ -n "$MLX_TEMPLATE_ARGS" ]; then
    echo "  mlx  chat_template_args=${MLX_TEMPLATE_ARGS}"
fi
echo "  mlx  log → ${LOG}"

mkdir -p "$REPO_DIR/logs"

# Source the mlx virtualenv (mlxenv alias = source <env>/bin/activate)
# shellcheck disable=SC1091
source "$MLX_ENV/bin/activate"

# Build args array so we can conditionally include --chat-template-args
ARGS=(
    --model              "$MLX_MODEL"
    --host               "$MLX_HOST"
    --port               "$MLX_PORT"
    --max-tokens         "$MLX_MAX_TOKENS"
    --prompt-cache-size  "$MLX_CACHE_SIZE"
    --prompt-cache-bytes "$MLX_CACHE_BYTES"
    --log-level          "$MLX_LOG_LEVEL"
)
if [ -n "$MLX_TEMPLATE_ARGS" ]; then
    ARGS+=( --chat-template-args "$MLX_TEMPLATE_ARGS" )
fi

nohup mlx_lm.server "${ARGS[@]}" >> "$LOG" 2>&1 &

MLX_PID=$!
echo "  mlx  pid=${MLX_PID}"

# ---------------------------------------------------------------------------
# Poll until ready (max 120 s; model load time varies)
# ---------------------------------------------------------------------------
TIMEOUT=120
ELAPSED=0
INTERVAL=3

while ! nc -z "$MLX_HOST" "$MLX_PORT" 2>/dev/null; do
    if ! kill -0 "$MLX_PID" 2>/dev/null; then
        echo "  mlx  ERROR: server exited unexpectedly — tail ${LOG}" >&2
        tail -20 "$LOG" >&2
        exit 1
    fi
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "  mlx  ERROR: timed out after ${TIMEOUT}s — tail ${LOG}" >&2
        tail -20 "$LOG" >&2
        exit 1
    fi
    printf "  mlx  loading... %ds\r" "$ELAPSED"
    sleep "$INTERVAL"
    ELAPSED=$(( ELAPSED + INTERVAL ))
done

echo "  mlx  ready (${ELAPSED}s)                    "
