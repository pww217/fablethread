---
title: 25-turn eval round
status: new
urgency: 3
size: large
created: 2026-07-13
ticket_id: E-14
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

Full eval round targeting:
- Bug B-46: smoothed convergence not persisted (new fix)
- All existing testing items
- Post-i28 stability across persona pairs x 25 turns

## Plan

Full eval: 5 persona x 5 genre Latin square x 25 turns

## Execution Log

- 2026-07-13: Stage 1 — smoothed_convergence persisted to state.meta after narrate
- 2026-07-13: Fixed `beat_narrative_chain` checker to read from `post_turn_pending_beat` (was reading cleared `last_turn_state.meta.pending_gm_beat`)
- 2026-07-13: 5 runs completed (noir:driven, space-western:speedrunner, golden-piracy:completionist, zombie-survival:cautious, allied-ww2:aggressive)

## Run Groups

| Run | Group | Checkers | Notes |
|-----|-------|----------|-------|
| noir:driven | 2238_noir-1930s_25t | 43/43 PASS (100%) | All checkers pass |
| space-western:speedrunner | 2328_space-western_25t | 41/43 PASS (95.3%) | thread_culling, ruling_reason_quality |
| golden-piracy:completionist | 2340_golden-piracy_25t | 42/43 PASS (97.7%) | thread_culling |
| zombie-survival:cautious | 2340_zombie-survival_25t | 42/43 PASS (97.7%) | thread_culling |
| allied-ww2:aggressive | 2340_allied-ww2_25t | 39/43 PASS (90.7%) | thread_culling, sanitizer_lifecycle, ruling_reason_quality, extraction_retry_rates |

## Findings

### Fixed / Verified

**B-46 smoothed_convergence persisted:** All 3 convergence checkers pass across all 5 runs:
- convergence_ema: 5/5 PASS
- convergence_recompute: PASS  
- convergence_threshold_context: PASS
- beat_narrative_chain: Fixed to read from `post_turn_pending_beat`, Beats: 2/2 PASS

### Ongoing Issues

1. **thread_culling (5/5 FAIL):** Systematic failure. When dormant count >= 3, culling should move oldest dormant threads to completed_threads with resolution_state=abandoned. Hallucinated events produce bad referenced thread IDs in state that aren't cleaned up.
2. **ruling_reason_quality (2/5 FAIL):** space-western and allied-ww2 — ruling_reason quality below threshold in certain turns
3. **sanitizer_lifecycle (1/5 FAIL):** allied-ww2 — resolved_threads references unknown IDs (cleanup issue)
4. **extraction_retry_rates (1/5 FAIL):** latest run — RecordResult validation error during extraction
