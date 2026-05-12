#!/usr/bin/env bash
# scripts/plan/review.sh — review plan(s) for implementation accuracy
# Usage:
#   ./scripts/plan/review.sh              — review all plans in plans/review/
#   ./scripts/plan/review.sh --plan <slug|filename> — review a specific plan
#   ./scripts/plan/review.sh --list       — list plans in plans/review/
#
# After successful review, the review output is written to plans/review/<slug>-review.md.
# The original plan is left untouched in plans/review/.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

REVIEW_DIR="plans/review"
DEST_DIR="plans"
PROMPT_TEMPLATE="${SCRIPT_DIR}/prompt-template.txt"
TIMEOUT_SECS=600

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.bun/bin:$HOME/.local/bin:$HOME/bin:${PATH:-}"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  printf '[%s] %s\n' "$(timestamp)" "$*"
}

die() {
  log "FATAL: $*" >&2
  exit 1
}

resolve_timeout_bin() {
  if command -v timeout >/dev/null 2>&1; then
    command -v timeout
    return 0
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    command -v gtimeout
    return 0
  fi
  return 1
}

resolve_opencode_bin() {
  if [[ -n "${OPENCODE_BIN:-}" && -x "${OPENCODE_BIN}" ]]; then
    printf '%s\n' "$OPENCODE_BIN"
    return 0
  fi
  if command -v opencode >/dev/null 2>&1; then
    command -v opencode
    return 0
  fi
  [[ -x "/opt/homebrew/bin/opencode" ]] && { printf '%s\n' "/opt/homebrew/bin/opencode"; return 0; }
  [[ -x "/usr/local/bin/opencode" ]] && { printf '%s\n' "/usr/local/bin/opencode"; return 0; }
  [[ -x "$HOME/.bun/bin/opencode" ]] && { printf '%s\n' "$HOME/.bun/bin/opencode"; return 0; }
  [[ -x "$HOME/.local/bin/opencode" ]] && { printf '%s\n' "$HOME/.local/bin/opencode"; return 0; }
  return 1
}

TIMEOUT_BIN="$(resolve_timeout_bin)" || die "Neither 'timeout' nor 'gtimeout' found. Install GNU coreutils or set TIMEOUT_BIN."
OPENCODE_BIN="$(resolve_opencode_bin)" || die "'opencode' not found. PATH=$PATH"

[[ -d "$REVIEW_DIR" ]] || die "Review directory not found: $REVIEW_DIR"
[[ -d "$DEST_DIR" ]] || die "Destination directory not found: $DEST_DIR"
[[ -f "$PROMPT_TEMPLATE" ]] || die "Prompt template not found: $PROMPT_TEMPLATE"

MODE="all"
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)
      MODE="list"
      shift
      ;;
    --plan)
      [[ -n "${2:-}" ]] || die "--plan requires a value"
      MODE="one"
      TARGET="$2"
      shift 2
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

if [[ "$MODE" == "list" ]]; then
  echo "Plans in ${REVIEW_DIR}/:"
  FOUND=0
  for f in "${REVIEW_DIR}"/*.md; do
    [[ -f "$f" ]] || continue
    [[ "$f" == *-review.md ]] && continue
    echo "  $(basename "$f")"
    FOUND=1
  done
  [[ $FOUND -eq 1 ]] || echo "  (none)"
  exit 0
fi

PLANS=()
if [[ "$MODE" == "one" ]]; then
  if [[ -f "${REVIEW_DIR}/${TARGET}" ]]; then
    PLANS+=("${REVIEW_DIR}/${TARGET}")
  elif [[ -f "${REVIEW_DIR}/${TARGET}.md" ]]; then
    PLANS+=("${REVIEW_DIR}/${TARGET}.md")
  else
    die "plan not found: ${TARGET}"
  fi
else
  for f in "${REVIEW_DIR}"/*.md; do
    [[ -f "$f" ]] || continue
    [[ "$f" == *-review.md ]] && continue
    PLANS+=("$f")
  done
fi

if [[ ${#PLANS[@]} -eq 0 ]]; then
  echo "No plans found in ${REVIEW_DIR}/"
  exit 0
fi

echo "================================================"
echo "  Reviewing ${#PLANS[@]} plan(s) sequentially"
echo "  Timeout: $((TIMEOUT_SECS / 60))m per plan"
echo "  opencode: ${OPENCODE_BIN}"
echo "  timeout:  ${TIMEOUT_BIN}"
echo "================================================"
echo ""

PASS=0
FAIL=0

for PLAN_PATH in "${PLANS[@]}"; do
  PLAN_BASENAME="$(basename "$PLAN_PATH")"
  TMP_PROMPT="$(mktemp)"
  TMP_OUTPUT="$(mktemp)"
  TMP_LOG="$(mktemp)"

  log "→ Reviewing: ${PLAN_BASENAME}"

  if ! python3 - "$PROMPT_TEMPLATE" "$PLAN_PATH" > "$TMP_PROMPT" <<'PY'
import sys
template = open(sys.argv[1], "r", encoding="utf-8").read()
content = open(sys.argv[2], "r", encoding="utf-8").read()
sys.stdout.write(template.replace("PLAN_PLACEHOLDER", content))
PY
  then
    log "✗ FAILED: could not build prompt for ${PLAN_BASENAME}"
    rm -f "$TMP_PROMPT" "$TMP_OUTPUT" "$TMP_LOG"
    ((FAIL+=1))
    echo ""
    continue
  fi

  log "  Running review"
  REVIEW_PATH="${DEST_DIR}/${PLAN_BASENAME%.md}-reviewed.md"
  if "$TIMEOUT_BIN" "$TIMEOUT_SECS" "$OPENCODE_BIN" run \
      -m mlx/mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit \
      < "$TMP_PROMPT" > "$REVIEW_PATH"; then
    log "✓ Review written to: ${REVIEW_PATH}"
    ((PASS+=1))
  else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 124 ]]; then
      log "✗ TIMED OUT after ${TIMEOUT_SECS}s"
    else
      log "✗ FAILED: opencode exited with code ${EXIT_CODE}"
    fi
    ((FAIL+=1))
  fi
  echo ""
done

echo "================================================"
echo "  Done. ${#PLANS[@]} plan(s) processed."
echo "  Passed: ${PASS}  |  Failed: ${FAIL}"
echo "================================================"