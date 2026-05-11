#!/usr/bin/env zsh
# scripts/plan/review-all.sh — review every plan in plans/review/ sequentially
# Usage:
#   ./scripts/plan/review-all.sh
#
# Each plan gets a 10-minute timeout. If it times out, it's marked FAILED
# and the next plan continues. After review, each plan is moved to plans/.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

REVIEW_DIR="plans/review"
PROMPT_TEMPLATE="$(dirname "$0")/prompt-template.txt"
TIMEOUT_SECS=600  # 10 minutes per plan

# ── Find plans ────────────────────────────────────────────────────────────────
PLANS=()
for f in "${REVIEW_DIR}"/*.md; do
  [[ -f "$f" ]] || continue
  PLANS+=("$f")
done

if [[ ${#PLANS[@]} -eq 0 ]]; then
  echo "No plans found in ${REVIEW_DIR}/"
  exit 0
fi

echo "Reviewing ${#PLANS[@]} plan(s) sequentially (up to 10m each)..."
echo ""

# ── Review each plan ──────────────────────────────────────────────────────────
for PLAN_PATH in "${PLANS[@]}"; do
  PLAN_BASENAME="$(basename "$PLAN_PATH")"
  PLAN_CONTENT="$(cat "$PLAN_PATH")"
  PROMPT_FILE="$(mktemp)"
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
      # Keep the plan in plans/review/ so it can be retried
    else
      echo "  → FAILED: opencode exited with code ${EXIT_CODE}"
      # Keep the plan in plans/review/ so it can be retried
    fi
  fi

  rm -f "$PROMPT_FILE"
  echo ""
done

echo "Done. ${#PLANS[@]} plan(s) reviewed."
