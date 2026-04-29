#!/usr/bin/env bash
# Recommended Ollama server env for Apple Silicon (single-user, long context).
# Run from repo: `make ollama-launch` or: `bash scripts/ollama-launch.sh`
set -euo pipefail

export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-1}"
export OLLAMA_KV_CACHE_TYPE="${OLLAMA_KV_CACHE_TYPE:-q8_0}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-1}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"
export OLLAMA_MLX="${OLLAMA_MLX:-1}"
# export OLLAMA_DEBUG=1   # uncomment for layer offload / KV logs

exec ollama serve "$@"
