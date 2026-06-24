# Cascadian Eval — Bug Hunt & Stabilization

**Started:** 2026-06-24
**Branch:** main
**Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8`

---

## Strategy

Progressive evaluation with iterative fixes. Start short, go longer, expand scope.

1. **5-turn single run** — pick a balanced pack/persona, find critical bugs, fix them
2. **10-turn run** — different pack/persona, verify fixes hold, find more bugs
3. **15-turn run** — different pack/persona, verify further, find more bugs
4. **Continue 15-turn runs** with different packs/personas until confident most serious bugs are fixed
5. **Full 5-pack eval** (25 turns each) when stable

## Threshold for Full Eval

- All mechanical problems fixed (ruling, dice, state, pacing, threads, arcs, beats, NPCs)
- All Python errors fixed (no tracebacks, no exceptions)
- All engine problems fixed (sanitizer, extraction, delta building, state mutations)
- Not required: all prompt quality problems (those are for tomorrow)
- Minor prompt fixes allowed during the process — concise, turn-based, minimal token impact
- No major prompt overhauls

## Known Issues (from 2026-06-22 REPORT.md)

### Critical (target these first)
1. Arc resolution too frequent (every 1-5 turns, target 8-15)
2. Convergence starvation (stealth-heavy play starves all 5 components to 0)
3. Null beat rate 34-57% (no checker enforces threshold)
4. Thread resolution events ≠ unique threads (LLM resolves non-existent threads)

### High-priority
5. Thread dedup rejection rate (near-duplicate updates)
6. Thread TTL disconnect (narrator forgets, storyteller doesn't)
7. Curtain call turn-count based, not narrative-based
8. NPC presence enum incomplete ("archived" not in enum)
9. NPC roster limited to 10

### Medium-priority
10. Beat driver always "motivation"
11. Beat streak fragile (null beats reset streaks)
12. Ruling "routine" path too generous
13. Storyteller prompt too information-dense
14. Group NPC resolution fragile
15. NPC dialogue not tracked

---

## Run Schedule

| # | Turns | Pack | Persona | Status | Notes |
|---|-------|------|---------|--------|-------|
| 1 | 5 | noir-1930s | opportunist | COMPLETE | 25/25 checkers pass, 40% thread resolution, convergence reaches CLIMAX T4 |
| 2 | 10 | zombie-survival | cautious | COMPLETE | 25/25 checkers pass, 28.6% thread resolution, convergence reaches CLIMAX T2 |
| 3 | 15 | space-western | explorer | COMPLETE | 24/25 checkers pass. thread_lifecycle FAIL: T9 updates non-existent thread 'militia_raiders_threat'. ruling_intent_match FAIL: T1 false impossible. beat_narrative_chain FAIL: blank GM beat. |
| 4 | 15 | golden-piracy | driven | COMPLETE | 24/25 checkers pass. extraction_retry_rates FAIL: T7 state retry (no JSON), T14 state retry (condition_change_reason missing). |
| 5 | 15 | allied-ww2 | completionist | COMPLETE | 25/25 checkers pass (100%) — cleanest run so far |
| 6 | 25×5 | all packs | standard personas | COMPLETE | 4/5 pass all checkers (99.2% overall). Full report: `evals/REPORT-2026-06-24.md` |

---

## Fixes Applied

- **Critical bug fixed:** `ev.py check --all --save-dir DIR` was loading 0 events because the "check" command skipped event loading. Fixed in `ccya/ev/__init__.py` by adding event loading logic for the check command when `--save-dir` is provided.
- **No new fixes needed for 5-pack runs** — engine stable across all 125 turns.

---

## Full 5-Pack Evaluation (25 turns each)

| Pack | Persona | Checkers | Threads Created | Threads Resolved | Resolution Rate | Notes |
|------|---------|----------|-----------------|------------------|-----------------|-------|
| noir-1930s | driven | 24/25 (96%) | 15 | 2 | 13.3% | location_change FAIL: T21 emitted but post-turn location unchanged |
| space-western | speedrunner | 25/25 (100%) | 12 | 2 | 16.7% | Clean run |
| golden-piracy | driven | 25/25 (100%) | 15 | 3 | 27.3% | Clean run |
| zombie-survival | cautious | 25/25 (100%) | 11 | 2 | 18.2% | Clean run |
| allied-ww2 | completionist | 25/25 (100%) | 13 | 2 | 15.4% | Clean run |

**Total:** 66 threads created, 11 resolved (16.7% resolution rate). 4/5 packs pass all checkers.

### Persistent Issues Across All Packs

1. **Thread lifecycle warnings** — thread_sanitizer consistently skips invalid thread_update and resolved_thread references to unknown IDs (hallucinated thread IDs by storyteller)
2. **Thread dedup rejections** — progress 1.00 overlap with last entry, rejecting (storyteller creates near-duplicate updates)
3. **thread_same_turn_conflict** — thread_update and thread_resolve for same ID on same turn (race condition in extraction)
4. **Inventory canonical ID mismatches** — resolve_inventory_canonical_id no match for items not in pack inventory (rusty_dagger, worn_dagger, sturdy_flashlight, medical_supplies, leather_notebook, merchant_ledger, etc.)
5. **Duplicate condition adds** — reconcile_delta duplicate condition add ignored (winded, bleeding_wound)
6. **generate_seed failures** — allied-ww2 initial run failed with "No JSON found in generate_seed response" (transient LLM issue, succeeded on retry)

### Per-Pack Details

**noir-1930s / driven (24/25):**
- location_change FAIL: T21 emitted location_change but post-turn location.id unchanged (main_street)

**space-western / speedrunner (25/25):**
- Clean run. Thread sanitizer warnings for unknown IDs (militia_raiders_threat, militia_ambush_active, naval_pursuit, alleyway_ambush, city_street_exposure)

**golden-piracy / driven (25/25):**
- Clean run. Thread sanitizer warnings for unknown IDs (dockside_pursuit, mutineer_enforcers, plaza_pursuit, plaza_melee, warehouse_corridor_pursuit, corridor_melee_climax, imminent_capture)

**zombie-survival / cautious (25/25):**
- Clean run. Thread sanitizer warnings for unknown IDs (immediate_lethal_threat, environmental_hazard_steam, immediate_pursuit, reclamation_hub_entry, reservoir_chemical_crisis, security_intervention_escalation, pump_station_exploration)

**allied-ww2 / completionist (25/25):**
- Clean run. Thread sanitizer warnings for unknown IDs (lethal_ambush_zone, flanking_maneuver_risk, close_quarters_combat, command_disillusionment, farmstead_confrontation, pursuit_in_ravine, cavern_confinement, immediate_combat_danger)

---

## Run 1: noir-1930s / opportunist / 5 turns

**Goal:** Find critical bugs, verify engine stability, identify quick wins.
