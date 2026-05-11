#!/usr/bin/env bash
# scripts/plan/review.sh — review a plan for implementation accuracy
# Usage:
#   ./scripts/plan/review.sh              — review all plans in plans/review/
#   ./scripts/plan/review.sh <slug>       — review a specific plan (slug or filename)
#   ./scripts/plan/review.sh --list       — list plans in plans/review/
#
# Each plan gets a 10-minute timeout. If it times out, it's marked FAILED
# and the plan stays in plans/review/ for retry. After successful review,
# the plan is moved from plans/review/ to plans/

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

REVIEW_DIR="plans/review"
PROMPT_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE"' EXIT
TIMEOUT_SECS=600  # 10 minutes per plan

PROMPT_TEMPLATE="$(dirname "$0")/prompt-template.txt"

# ── List plans ────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--list" ]]; then
  echo "Plans in ${REVIEW_DIR}/:"
  for f in "${REVIEW_DIR}"/*.md; do
    [[ -f "$f" ]] || continue
    echo "  $(basename "$f")"
  done
  exit 0
fi

# ── Find plan(s) to review ────────────────────────────────────────────────────
TARGET="${1:-}"
PLANS=()

if [[ -z "$TARGET" ]]; then
  for f in "${REVIEW_DIR}"/*.md; do
    [[ -f "$f" ]] || continue
    PLANS+=("$f")
  done
else
  if [[ -f "${REVIEW_DIR}/${TARGET}" ]]; then
    PLANS+=("${REVIEW_DIR}/${TARGET}")
  elif [[ -f "${REVIEW_DIR}/${TARGET}.md" ]]; then
    PLANS+=("${REVIEW_DIR}/${TARGET}.md")
  else
    echo "ERROR: plan not found: ${TARGET}" >&2
    echo "Use --list to see available plans." >&2
    exit 1
  fi
fi

if [[ ${#PLANS[@]} -eq 0 ]]; then
  echo "No plans found in ${REVIEW_DIR}/"
  exit 0
fi

# ── Review each plan ──────────────────────────────────────────────────────────
for PLAN_PATH in "${PLANS[@]}"; do
  PLAN_BASENAME="$(basename "$PLAN_PATH")"
  PLAN_CONTENT="$(cat "$PLAN_PATH")"
  sed "s|PLAN_PLACEHOLDER|${PLAN_CONTENT}|g" "$PROMPT_TEMPLATE" > "$PROMPT_FILE"
  REVIEW_PATH="${REVIEW_DIR}/${PLAN_BASENAME%.md}-review.md"

  echo "→ Reviewing: ${PLAN_BASENAME}"

  if timeout "$TIMEOUT_SECS" opencode run \
      -m mlx/mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit \
      < "$PROMPT_FILE" > "$REVIEW_PATH" 2>&1; then
    echo "  → Review written to: ${REVIEW_PATH}"
    mv "$PLAN_PATH" "plans/"
    echo "  → Moved plan to: plans/${PLAN_BASENAME}"
  else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 124 ]]; then
      echo "  → FAILED: timed out after ${TIMEOUT_SECS}s (10m)"
    else
      echo "  → FAILED: opencode exited with code ${EXIT_CODE}"
    fi
    # Keep plan in plans/review/ for retry
  fi

  echo ""
done

echo "Done. ${#PLANS[@]} plan(s) reviewed."
