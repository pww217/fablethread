---
title: "Phase 3 eval: 5 games × 25 turns — engine stability verification, NPC presence tracking, beat mechanics"
status: done
type: eval
urgency: 3
size: medium
created: 2026-06-29
ticket_id: E-3
labels: [phase-3, engine-stability, npc-presence, beat-mechanics]
---

# E-3: Phase 3 eval — 5 games × 25 turns

## Eval Group

**Path:** `evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/`
**Date:** 2026-06-29
**SHA:** e6b746b

## Phase Reports

- [PHASE-3.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/PHASE-3.md)
- [REPORT.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/REPORT.md)

## Games Run

| # | Pack | Persona | Pass Rate | Individual Report |
|---|------|---------|-----------|-------------------|
| 1 | noir-1930s | driven | 90.5% | [2014_noir-1930s_driven_25t/report.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2014_noir-1930s_driven_25t/report.md) |
| 2 | space-western | speedrunner | 95.2% | [2020_space-western_speedrunner_25t/report.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2020_space-western_speedrunner_25t/report.md) |
| 3 | golden-piracy | completionist | 85.7% | [2026_golden-piracy_completionist_25t/report.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2026_golden-piracy_completionist_25t/report.md) |
| 4 | zombie-survival | cautious | 92.9% | [2032_zombie-survival_cautious_25t/report.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2032_zombie-survival_cautious_25t/report.md) |
| 5 | allied-ww2 | aggressive | 88.1% | [2038_allied-ww2_aggressive_25t/report.md](evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2038_allied-ww2_aggressive_25t/report.md) |

**Average pass rate: 90.5%**

## Findings

### Engine Stability
- All 5 games completed to 25 turns without crashes
- No game-breaking bugs found
- Average pass rate 90.5% is acceptable for Phase 3
- No regressions vs previous full eval (SHA 0d8013d5)

### NPC Presence & Compendium
- All 5 games pass `npc_presence` and `compendium_lifecycle` checkers
- NPCs properly transition between present/nearby/known/departed
- Location change auto-demotion to `nearby` working
- Re-promotion when NPCs follow player working
- I-11 implementation verified: NPC profiles rendered correctly to World prompt

### `npcs` Field in Beats
- Schema fix applied to `world_system.j2` but LLM not populating the field
- No functional impact yet — `npcs` field not used in ruling/narration phases

### Beat Mechanics
- World step generates 2-3 beats with `type` + `effect` correctly populated
- Beat diversity maintained (no consecutive repeats of same type)
- Phase alignment enforced via `allowed_beat_types`
- Beat selection bias: index 0 selected ~60% of time (known limitation)

### Console Warnings (Non-Fatal)
1. `condition unknown turns_remaining type: NoneType` — `tremors` and `hunted` conditions missing `turns_remaining` field handling
2. `resolve_inventory_canonical_id no match` — LLM-generated item IDs don't match canonical IDs
3. `thread_updates.dedup` — Working correctly, just logging
4. `extract_state parse failed` — LLM output validation issues when condition changes present (2 games, retry succeeded)

### Failing Checkers
- **ruling_reason_quality:** 3/5 games failed — Rulings with `skill: ?` and `diff: ?` fail checker
- **sanitizer_lifecycle:** 3/5 games failed — Sanitizer events reference unknown thread IDs
- **location_change:** 1/5 games failed — noir-1930s/driven

## What Was Done
- Ran Phase 3: 5 games at 25 turns (all pairs)
- Verified NPC presence tracking working correctly across all games
- Verified I-11 implementation (NPC profiles from compendium) working correctly
- Verified beat mechanics healthy
- Engine stability confirmed — no regressions

## What's Next
1. Review F-4 (charisma bias in rulings) — ruling_reason_quality failures may be related
2. Consider adding `npcs` field usage in ruling/narration phases
3. Fix `turns_remaining` field for `tremors` and `hunted` conditions
4. Improve inventory item ID canonicalization
