---
name: ev-run
description: Iterative eval: graduated scope, phase-gated, sequential, eval tickets as long-term memory
---

Purpose: Execute an iterative, phase-gated evaluation with graduated scope. Each phase targets a different severity threshold. Skip phases that find no matching issues.

**The eval ticket is your track and long-term memory.** Eval tickets serve as the source of truth across compactions — record what's been done, what's next, what evidence exists. Create ONE `E-` ticket per eval session (not per bug). Include eval group path, phase report links, all findings, fixes applied (with commit separators), and reproduction context in the ticket body. Update the ticket continuously: after every phase, every fix, every review. Any agent that picks up the ticket should be able to resume from wherever you left off.

**Sequential work:** One phase at a time. One issue at a time when investigating bugs. Do not pull multiple phases or issues into context simultaneously. Work through rubric sections one at a time, writing findings to the ticket as long-term memory after each section. **No parallel runs:** Never run multiple `ev.py play` instances in parallel — each game reads/writes shared directories (save dirs, events, reports). Running two turns simultaneously from the same game can corrupt state or produce ambiguous checker output. Always run game pairs sequentially, even within a phase that tests multiple pack/persona combinations.

**Critical constraints:**
1. Write findings into the ticket as you discover them — do not buffer findings until the end.
2. Work through rubric sections one at a time. Write findings to the ticket before moving to the next section. The context window cannot hold all checkers + all findings.
3. The Executive Summary is written LAST, after all rubric sections are complete.
4. **Checkers are bellwethers, not verdicts.** A passed checker means something *might* be healthy. A failed checker means something *might* be unhealthy. Neither is proof. Always pair checker results with subjective examination — pull live data from runs and examine it directly.
5. **Use `ev-review` for deep dives.** When examining testing-phase tickets, recent commits, or anything that warrants deeper examination, load the `ev-review` skill. Do not rely on checkers alone for mechanical assessment.
6. **Exit criteria is completeness, not checker pass.** The eval is done when you have conducted a thorough subjective evaluation of all areas that need focus (testing-phase tickets, recent changes). Not when all checkers pass.

## Prerequisites

- `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
- Set bash timeout to at least 25 × 60000 = 1,500,000ms for full phase 3
- Read `evals/ev-tooling/templates/report.md.j2` — understand the structure before you start
- Read architectural docs: `docs/architecture/OVERVIEW.md`, `docs/architecture/pacing-systems.md`, `docs/architecture/step0-ruling.md`, `docs/architecture/step2a-scene.md`, `docs/architecture/step2b-state.md`, `docs/architecture/step2c-record.md`, `docs/architecture/delta-validate.md`, `docs/architecture/state-models.md`, `docs/architecture/cross-module-contracts.md`
- Find the prior eval group: locate the newest full eval group in `evals/runs/` before the current one

## Persona Pairings

| Scenario | Persona |
|---|---|
| `noir-1930s` | `driven` |
| `space-western` | `speedrunner` |
| `golden-piracy` | `completionist` |
| `zombie-survival` | `cautious` |
| `allied-ww2` | `aggressive` |

Available personas: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `opportunist`, `completionist`, `speedrunner`, `custom`. Defined in `ccya/ev/persona.py`.

## Graduated Scope

Start small, expand as stability increases. Phase 2 is the most important — this is where nuanced bugs and regressions surface that Phase 1 misses and Phase 3 doesn't focus on.

| Phase | Games | Turns | Purpose |
|-------|-------|-------|---------|
| 1 | 1 | 5 | Critical/game-breaking bugs |
| 2 | 3 | 15 | Nuanced bugs, regressions, intermediate issues |
| 3 | 5 | 25 | Balance, long-term mechanics, nuanced patterns |

## Phase Gating Thresholds

| Transition | Condition |
|------------|-----------|
| Phase 1 → Phase 2 | No critical bugs found, OR critical bugs fixed |
| Phase 2 → Phase 3 | No intermediate bugs found, OR intermediate bugs fixed, AND engine is stable |
| Skip Phase 3 | Critical bugs found that need refactor, OR intermediate bugs found that need refactor |
| Skip Phase 2 | User explicitly requests, OR Phase 1 found no critical issues and user wants intermediate check |

## Phase 1: 1 game, 5 turns — Critical/game-breaking bugs

**Threshold:** Critical failures, game-breaking bugs, obvious quality-degrading issues that would make the game unplayable or severely broken.

**Execution:**
```bash
# Start with noir:driven (balanced pair). If critical issues found, run 2-3 more pairs to confirm pattern.
.venv/bin/python scripts/debug/ev.py play --llm --turns 5 \
   --pack noir-1930s --persona driven --auto-report
```

**Analysis:**
- Run full rubric checkers against all runs (bellwethers only — verify with subjective examination)
- Write findings to the eval ticket immediately
- If critical issues found: run 2-3 more pairs to confirm pattern, then STOP. Fix the bugs before continuing. Do not proceed to Phase 2 while critical bugs are unfixed — signals will be confounded.
- If no critical issues: skip to Phase 2.

## Phase 2: 3 games, 10-15 turns — Nuanced bugs and regressions

**Threshold:** Intermediate degradations, pacing issues, extraction misses that matter, mechanical inconsistencies that affect gameplay but don't break it.

**Execution:**
```bash
# 3 persona pairs for wider sampling
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 15 \
    --pack "$pack" --persona "$persona" --auto-report
done
```

**Analysis:**
- Run full rubric checkers against all runs (bellwethers only — verify with subjective examination)
- Use `ev-review` for deep dives on any testing-phase tickets or recent changes
- Write findings to the eval ticket immediately
- If bugs found that require a refactor (not a simple fix): STOP. Do not proceed to Phase 3. Fix the refactor first, then resume.
- If no intermediate issues: skip to Phase 3.
- If engine is still unstable: stay in Phase 2 until stable.

## Phase 3: 5 games, 20 turns — Balance and long-term mechanics

**Threshold:** Balance issues, long-term mechanical assessment, nuanced issues that only appear over extended play, edge cases in pacing/convergence/state management.

**Execution:**
```bash
# All 5 persona pairs — only when engine is stable
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist zombie-survival:cautious allied-ww2:aggressive"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 25 \
    --pack "$pack" --persona "$persona" --auto-report
done
```

**Analysis:**
- Run full rubric checkers against all runs (bellwethers only — verify with subjective examination)
- Use `ev-review` for deep dives on any testing-phase tickets or recent changes
- Write findings to the eval ticket immediately
- This phase only runs when: critical bugs are fixed AND intermediate issues are resolved AND engine is stable.

## Testing Items Review

Scan ALL roadmap types for `status: testing`:
```bash
grep -rn "^status: testing" roadmap/bugs/ roadmap/improvements/ roadmap/features/ roadmap/evals/ 2>/dev/null
```

For each testing item (bugs, improvements, features, evals):
- Use `ev-review` for targeted deep-dive analysis (not just checkers)
- Run targeted checkers against relevant runs (bellwethers only)
- Assess: confirmed fixed / regressed / inconclusive via subjective examination
- Update the ticket file directly:
  - Confirmed fixed → `status: done`, `completed: YYYY-MM-DD`
  - Regressed or still broken → `status: up-next`
  - Inconclusive → leave as `testing`
- After updating all files, call the `ticket` skill to validate changes, then run `make roadmap`

## Changes Since Last Eval

A "full eval" is defined as an eval group with multiple runs totaling at least 40 turns. Find the prior full eval group in `evals/runs/` (the newest one before the current group). Extract the SHA from the group directory name:

```
evals/runs/2026-06-27_0.30.0-28-g0d8013d5_0d8013d/
                                               ^^^^^^^
                                               prior SHA
```

The format is `YYYY-MM-DD_{tag}_{sha:8}_{sha:8}` — the last 8-character hex string is the SHA.

```bash
# Compare commits between prior full eval and current
git log --oneline <prior_sha>..<current_sha> -- ccya/
```

Focus on engine/prompt areas. Report a brief summary.

## Rubric Sections — SEQUENTIALLY, ONE AT A TIME

Work through sections **one at a time**. Do not run all checkers for all sections and then write findings. The context window will not hold everything. You must write findings back to the ticket as long-term memory after each section.

**The loop:**
1. Pick ONE rubric section (e.g., "Ruling Engine")
2. Run all targeted `ev.py` commands for that section across all runs in the current phase
3. Parse output, assess findings
4. **Write findings into the ticket immediately** — this is your long-term memory
5. Only then move to the next rubric section

If you are interrupted or lose context, resume by re-reading the ticket (which contains your previous findings) and continue from where you stopped.

## Checkers Results

Compile pass/fail table across all rubric areas and all runs in the current phase. Remember: checkers are bellwethers, not verdicts. Include them for reference but base conclusions on subjective examination.

## Executive Summary (LAST)

After all rubric sections are complete, write a concise (5-10 item) summary at the top of the ticket:
- Largest failures
- Major fix progressions
- Anything that can be said concisely but matters

Do not start with this. Do not let it distract from systematic rubric review.

## New Tickets

Create ONE `E-` ticket per eval session (not per bug). Include:
- Eval group path and date in frontmatter
- Phase findings summary
- Links to phase reports (`PHASE-1.md`, etc.)
- All bugs/regressions found listed in the ticket body
- Reproduction context and relevant checker output
- What was done, what's next (for resuming across compactions)

The `E-` ticket serves as long-term memory — reference it on subsequent compactions.

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

- `evals/ev-tooling/templates/report.md.j2` — report skeleton
- `docs/ev/COMMANDS.md` — full command reference
- `docs/ev/EVAL-RUNS.md` — eval run storage & workflow
- `docs/ev/CHECKERS.md` — checker library
- `docs/ev/RUBRIC.md` — eval rubric checklist (detailed mechanics)
