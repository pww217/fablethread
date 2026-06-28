---
name: ev-run
description: Iterative eval: 1-5 turns (critical), 10 turns (intermediate), 20-25 turns (balance); phase-gated, skips if no issues found
---

Purpose: Execute an iterative, phase-gated evaluation. Each phase targets a different severity threshold. Skip phases that find no matching issues.

**Critical constraints:**
1. Write findings into the report as you discover them — do not buffer findings until the end.
2. Work through rubric sections one at a time. Write findings to the report file before moving to the next section. The context window cannot hold all checkers + all findings.
3. The Executive Summary is written LAST, after all rubric sections are complete.

## Prerequisites

- Server running on `localhost:8765`
- LLM backend on `localhost:8080` with `mlx-community/gemma-4-26b-a4b-it-mxfp8`
- `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
- Set bash timeout to at least 25 × 60000 = 1,500,000ms for full phase 3

## Before Running

1. **Read the template:** `docs/ev/consolidated-report-template.md` — understand the structure before you start.
2. **Read architectural docs:**
   - `docs/architecture/OVERVIEW.md`
   - `docs/architecture/pacing-systems.md`
   - `docs/architecture/step0-ruling.md`
   - `docs/architecture/step2a-scene.md`
   - `docs/architecture/step2b-state.md`
   - `docs/architecture/step2c-storytell.md`
   - `docs/architecture/delta-validate.md`
   - `docs/architecture/state-models.md`
   - `docs/architecture/cross-module-contracts.md`
3. **Find the prior eval group:** locate the newest full eval group in `evals/runs/` before the current one.

## Persona Pairings

| Scenario | Persona |
|---|---|
| `noir-1930s` | `driven` |
| `space-western` | `speedrunner` |
| `golden-piracy` | `completionist` |
| `zombie-survival` | `cautious` |
| `allied-ww2` | `aggressive` |

Available personas: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `opportunist`, `completionist`, `speedrunner`, `custom`. Defined in `ccya/ev/personality.py`.

## Phase 1: 1-5 turns — Critical/game-breaking issues

**Threshold:** Critical failures, game-breaking bugs, obvious quality-degrading issues that would make the game unplayable or severely broken.

**Execution:**
```bash
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist zombie-survival:cautious allied-ww2:aggressive"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 5 \
    --pack "$pack" --personality "$persona" --auto-report
done
```

**Analysis:**
- Run full rubric checkers against all 5 runs
- Write findings to `evals/runs/<group>/PHASE-1.md`
- If no issues match the critical threshold: output "Phase 1: No critical issues found. Skipping to Phase 2." and move on.
- If critical issues found: continue to Phase 2.

## Phase 2: 10 turns — Intermediate issues

**Threshold:** Intermediate degradations, pacing issues, extraction misses that matter, mechanical inconsistencies that affect gameplay but don't break it.

**Execution:**
```bash
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist zombie-survival:cautious allied-ww2:aggressive"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 10 \
    --pack "$pack" --personality "$persona" --auto-report
done
```

**Analysis:**
- Run full rubric checkers against all 5 runs
- Write findings to `evals/runs/<group>/PHASE-2.md`
- If no issues match the intermediate threshold: output "Phase 2: No intermediate issues found. Skipping to Phase 3." and move on.
- If intermediate issues found: continue to Phase 3.

## Phase 3: 20-25 turns — Balance and long-term mechanics

**Threshold:** Balance issues, long-term mechanical assessment, nuanced issues that only appear over extended play, edge cases in pacing/convergence/state management.

**Execution:**
```bash
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist zombie-survival:cautious allied-ww2:aggressive"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 25 \
    --pack "$pack" --personality "$persona" --auto-report
done
```

**Analysis:**
- Run full rubric checkers against all 5 runs
- Write findings to `evals/runs/<group>/PHASE-3.md`
- This phase always runs if Phase 1 or 2 found issues, or if user explicitly requests full eval.

## Validating Items

Scan `roadmap/bugs/*.md` for `status: validating`. For each:
- Run targeted checkers against relevant runs
- Assess: confirmed fixed / regressed / inconclusive
- Update the bug file directly:
  - Confirmed fixed → `status: done`, `completed: YYYY-MM-DD`
  - Regressed or still broken → `status: up-next`
  - Inconclusive → leave as `validating`
- After updating all bug files, call the `ticket` skill to validate changes, then run `make roadmap`

## Changes Since Last Eval

```bash
git log --oneline <prior_sha>..<current_sha> -- ccya/
```

Focus on engine/prompt areas. Report a brief summary.

## Rubric Sections — SEQUENTIALLY, ONE AT A TIME

Work through sections **one at a time**. Do not run all checkers for all sections and then write findings. The context window will not hold everything. You must write findings back to the report file as long-term memory after each section.

**The loop:**
1. Pick ONE rubric section (e.g., "Ruling Engine")
2. Run all targeted `ev.py` commands for that section across all runs in the current phase
3. Parse output, assess findings
4. **Write findings into the report file immediately** — this is your long-term memory
5. Only then move to the next rubric section

If you are interrupted or lose context, resume by re-reading the report file (which contains your previous findings) and continue from where you stopped.

## Checker Scores

Compile pass/fail table across all rubric areas and all runs in the current phase.

## Executive Summary (LAST)

After all rubric sections are complete, write a concise (5-10 item) summary at the top of the report:
- Largest failures
- Major fix progressions
- Anything that can be said concisely but matters

Do not start with this. Do not let it distract from systematic rubric review.

## New Tickets

For any new issues found that fit the eval type:
- Call the `ticket` skill to create new `E-` tickets
- Include reproduction context, relevant checker output, and phase information

## Output Location

Write phase reports and consolidated report at:
```
evals/runs/<group>/PHASE-1.md
evals/runs/<group>/PHASE-2.md
evals/runs/<group>/PHASE-3.md
evals/runs/<group>/REPORT.md
```

Where `<group>` is the directory created by the runs (format: `YYYY-MM-DD_{tag}_{sha:8}`).

## Reference Docs

- `docs/ev/consolidated-report-template.md` — report skeleton
- `docs/ev/COMMANDS.md` — full command reference
- `docs/ev/EVAL-RUNS.md` — eval run storage & workflow
- `docs/ev/CHECKERS.md` — checker library
- `docs/ev/RUBRIC.md` — eval rubric checklist (detailed mechanics)
