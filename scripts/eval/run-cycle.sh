#!/usr/bin/env zsh
# qa-cycle.zsh — run eval, then generate a remediation plan via opencode
# Usage:
#   ./run-cycle.sh              — run eval (standard), then generate plan
#   ./run-cycle.sh --fast       — run eval (fast), then generate plan
#   ./run-cycle.sh <report>     — skip eval, use existing report
#   ./run-cycle.sh --fast <report> — skip eval, use existing report

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ── Date stamp ──────────────────────────────────────────────────────────────
DATE_SLUG="$(date +%b-%d | tr '[:upper:]' '[:lower:]')"   # e.g. may-10
PLAN_PATH="docs/plans/eval-remediation-${DATE_SLUG}.md"

# ── Step 1: Run eval or use existing report ──────────────────────────────────
# Usage:
#   ./run-cycle.sh              — run eval (standard), then generate plan
#   ./run-cycle.sh --fast       — run eval (fast), then generate plan
#   ./run-cycle.sh <report>     — skip eval, use existing report
#   ./run-cycle.sh --fast <report> — skip eval, use existing report

REPORT_ARG="${1:-}"
FAST_FLAG=""
if [[ "$REPORT_ARG" == "--fast" ]]; then
  FAST_FLAG="--fast"
  REPORT_ARG="${2:-}"
fi

if [[ -n "$REPORT_ARG" && -f "$REPORT_ARG" ]]; then
  REPORT="$(realpath "$REPORT_ARG")"
  echo "→ Using existing report: ${REPORT}"
elif [[ -n "$REPORT_ARG" ]]; then
  echo "ERROR: report file not found: ${REPORT_ARG}" >&2
  exit 1
else
  if [[ "$FAST_FLAG" == "--fast" ]]; then
    echo "→ Running eval (fast / temp=0)…"
    make eval-fast
  else
    echo "→ Running eval (standard)…"
    make eval
  fi

  # Eval writes to evals/runs/<timestamp>/REPORT.md
  LATEST_RUN="$(ls -td evals/runs/*/ 2>/dev/null | head -1)"
  if [[ -z "$LATEST_RUN" ]]; then
    echo "ERROR: no eval run directory found under evals/runs/" >&2
    exit 1
  fi
  REPORT="${LATEST_RUN}REPORT.md"
  if [[ ! -f "$REPORT" ]]; then
    echo "ERROR: REPORT.md not found at ${REPORT}" >&2
    exit 1
  fi
  echo "→ Using report: ${REPORT}"
fi

# ── Step 2: Generate remediation plan via opencode ───────────────────────────
echo "→ Generating remediation plan → ${PLAN_PATH}…"

PROMPT_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE"' EXIT

uv run python -c "
import sys, pathlib
prompt = pathlib.Path(sys.argv[1]).read_text()
report = pathlib.Path(sys.argv[2]).read_text()
plan_path = sys.argv[3]
prompt = prompt.replace('PLAN_PATH_PLACEHOLDER', plan_path)
prompt = prompt.replace('REPORT_PLACEHOLDER', report)
pathlib.Path(sys.argv[4]).write_text(prompt)
" \
  "$(dirname "$0")/prompt-template.txt" \
  "$REPORT" \
  "$PLAN_PATH" \
  "$PROMPT_FILE"

opencode run \
  -m "mlx/mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit" \
  < "$PROMPT_FILE" \
  > "$PLAN_PATH"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "✓ QA cycle complete."
echo "  Report:  ${REPORT}"
echo "  Plan:    ${PLAN_PATH}"
echo ""
echo "Review the plan, then implement phases in order."
echo "Prompt changes (Phase 1) require your explicit approval before any code phase."