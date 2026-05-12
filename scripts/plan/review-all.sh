#!/usr/bin/env bash
# scripts/plan/review-all.sh — review every plan in plans/review/ sequentially
# Usage:
#   ./scripts/plan/review-all.sh
#
# Each plan gets a 10-minute timeout. If it times out, it's marked FAILED
# and the next plan continues. After successful review, the reviewed plan
# file is written to plans/<slug>-reviewed.md. The original plan is left
# in plans/review/ for manual review.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

REVIEW_DIR="plans/review"
REVIEW_SCRIPT="${SCRIPT_DIR}/review.sh"

die() {
  printf '[%s] FATAL: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >&2
  exit 1
}

[[ -d "$REVIEW_DIR" ]] || die "Review directory not found: $REVIEW_DIR"
[[ -x "$REVIEW_SCRIPT" ]] || die "Review script not found or not executable: $REVIEW_SCRIPT"

# Collect plan basenames (exclude already-reviewed files)
PLANS=()
for f in "${REVIEW_DIR}"/*.md; do
  [[ -f "$f" ]] || continue
  [[ "$f" == *-review.md ]] && continue
  PLANS+=("$(basename "$f")")
done

if [[ ${#PLANS[@]} -eq 0 ]]; then
  echo "No plans found in ${REVIEW_DIR}/"
  exit 0
fi

echo "================================================"
echo "  Reviewing ${#PLANS[@]} plan(s) sequentially"
echo "  Using: ${REVIEW_SCRIPT}"
echo "================================================"
echo ""

PASS=0
FAIL=0

for PLAN_NAME in "${PLANS[@]}"; do
  if "$REVIEW_SCRIPT" --plan "$PLAN_NAME"; then
    ((PASS+=1))
  else
    ((FAIL+=1))
  fi
  echo ""
done

echo "================================================"
echo "  Done. ${#PLANS[@]} plan(s) processed."
echo "  Passed: ${PASS}  |  Failed: ${FAIL}"
echo "================================================"
