#!/usr/bin/env zsh
# qa-cycle.zsh — run eval, then generate a remediation plan via opencode
# Usage: ./qa-cycle.zsh [--fast]

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ── Date stamp ──────────────────────────────────────────────────────────────
DATE_SLUG="$(date +%b-%d | tr '[:upper:]' '[:lower:]')"   # e.g. may-10
PLAN_PATH="docs/plans/eval-remediation-${DATE_SLUG}.md"

# ── Step 1: Run eval ─────────────────────────────────────────────────────────
if [[ "${1:-}" == "--fast" ]]; then
  echo "→ Running eval (fast / temp=0)…"
  make eval-fast
else
  echo "→ Running eval (standard)…"
  make eval
fi

# ── Locate the latest REPORT.md ──────────────────────────────────────────────
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

# ── Step 2: Generate remediation plan via opencode ───────────────────────────
echo "→ Generating remediation plan → ${PLAN_PATH}…"

opencode \
  --model "mlx-community/Qwen3-35B-A22B-4bit" \
  --prompt "$(cat <<'PROMPT'
You are a planning agent for the ccya interactive narrative game engine.
Your ONLY deliverable is a remediation plan document written to the path I specify.
You do not implement code. You do not run tests. You write plans only.

Before writing anything, read these files in this order:
1. AGENTS.md — rules, module boundaries, prompt rules, dead-code policy. This is law.
2. docs/plans/TODO.md — know what is already open before adding anything.
3. The REPORT.md file I am about to give you.

Then write a remediation plan to: PLAN_PATH_PLACEHOLDER

The plan must follow the exact format in AGENTS.md (Status, Part of, Dependencies,
Objective, Non-goals, Affected files table, Firm decisions, Implementation phases,
Tests, REPOMAP updates, Risks, Ambiguities, TODO.md update).

PHASING RULES — organize phases by shared context, not by feature:
  Phase 1: Prompt-only changes (system/user prompt edits) — no code touched.
    These are the most sensitive changes. Each prompt change must name: the pipeline,
    the exact passage being changed, what it currently says, what it should say, and
    why. Do not consolidate prompts of different pipelines into one step.
    Prompt changes must be conservative — preserve intent, tighten language, cut
    redundancy, fix contradictions. Never rewrite a prompt's purpose.
  Phase 2: Eval harness changes (judge.py, report.py, universal_asserts.py).
    Only fields or asserts referenced in Section 6 or Section 11 of the report.
  Phase 3: Engine/state/extraction changes — only if Section 11 has Critical or Major
    issues tagged [Engine]. If there are none, omit this phase entirely.
  Phase 4: Documentation updates (REPOMAP, TODO.md, any plan cross-references).

CONTENT RULES:
- Every issue in Section 11 of REPORT.md tagged Critical or Major must appear in
  the plan with a concrete step. Minor issues may be batched or deferred.
- Each step must include: File, What, Why, and a Validation check.
- For prompt changes: include the exact Before/After text. No pseudocode.
- For assert changes: include the complete Python snippet. No pseudocode.
- Flag every ambiguity that would block execution.
- Do not invent field names or function signatures — read REPOMAP if unsure.
- State Fidelity Rate and Prompt Adherence Rate from the report front matter must
  each appear in the Objective section so an executor knows the baseline.

After writing the plan, append a one-line entry to docs/plans/TODO.md under the
appropriate priority section (P1 for Critical issues, P2 for Major, P3 for Minor).

Do not summarize findings. Do not restate the report. Write the plan.
PROMPT
)" \
  --file "$REPORT" \
  --output "$PLAN_PATH"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "✓ QA cycle complete."
echo "  Report:  ${REPORT}"
echo "  Plan:    ${PLAN_PATH}"
echo ""
echo "Review the plan, then implement phases in order."
echo "Prompt changes (Phase 1) require your explicit approval before any code phase."