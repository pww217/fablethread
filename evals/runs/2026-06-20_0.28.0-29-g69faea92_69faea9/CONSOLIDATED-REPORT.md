# Consolidated Eval Report — 2026-06-20 (Post-Fix)

**Commit:** `69faea9` (v0.28.0-29-g69faea92, dirty)
**Date:** 2026-06-20
**Packs:** 5 (space-western, allied-ww2, noir-1930s, golden-piracy, zombie-survival)
**Turns:** 30 per pack (150 total)
**Checkers:** 23 deterministic + 3 LLM-based (26 total)
**Flags:** `--no-sanitize --temp 0.7 --eval --personality custom --rubric`

---

## Fixes Applied Since Previous Eval (e399818)

### 1. Inventory Checker ID Resolution (ccya/ev/checkers/inventory.py)
- Now uses `resolve_inventory_remove_target()` to resolve raw storyteller IDs against canonical state IDs
- Eliminates false positives for `lead_rounds`, `garand_rounds`, `large_caliber_rounds`

### 2. Warning Storage (ccya/ev/warnings.py, ccya/engine/extraction/pipeline.py, ccya/engine/seed.py)
- Added `thread_dedup` and `compendium_dedup` columns to warnings table
- Compendium NPC dedup redirects now stored in `extraction_event["compendium_dedup_redirects"]`
- Seed soft-check warnings now stored in `envelope.seed_state.meta["_seed_soft_warnings"]`

### 3. Prompt Fixes (ccya/prompts/extract_scene_system.j2, ccya/prompts/storytell_system.j2)

#### location_change vs location_description (extract_scene_system.j2)
- Added explicit warning: scene extractor was emitting `location_change` when narration describes different atmosphere but PC is in same place
- **Fixes:** allied-ww2 T24 (location_change emitted but location.id unchanged)

#### gm_beat.surface_as vs gm_beat.type (storytell_system.j2)
- Added CRITICAL warning: storyteller was emitting `pressure` (a beat type) as `surface_as` (should be `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, or `item`)
- **Fixes:** golden-piracy T1, T25, T28 retries (EXTRACTION_COERCION_FAILED validation errors)

#### arc_resolve empty object (storytell_system.j2)
- Added CRITICAL warning: storyteller was emitting `arc_resolve: {}` instead of omitting the field
- **Fixes:** golden-piracy T8 retry (missing field validation errors)

#### goal_update no-op detection (storytell_system.j2)
- Strengthened guidance: added explicit instruction to compare proposed `goal_update` against current `visible_goal` before emitting
- **Fixes:** noir-1930s T30 (goal_update equals previous visible_goal)

---

## Full Rubric Results

### space-western (30/30 clean turns, 23/23 deterministic PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 3 retries (T20, T28, T29 — storytell: 2, state: 1). 30/30 turns clean.

### allied-ww2 (30/30 clean turns, 23/23 deterministic PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 1 retry (T5 — storytell). 30/30 turns clean.

### noir-1930s (30/30 clean turns, 23/23 deterministic PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 1 retry (T23 — storytell). 30/30 turns clean.

### golden-piracy (30/30 clean turns, 23/23 deterministic PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 1 retry (T15 — storytell). 30/30 turns clean.

### zombie-survival (30/30 clean turns, 23/23 deterministic PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 0 retries. 30/30 turns clean.

---

## Summary

| Pack | Turns | Clean | Deterministic | LLM | Total | Score |
|------|-------|-------|---------------|-----|-------|-------|
| space-western | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| allied-ww2 | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| noir-1930s | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| golden-piracy | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| zombie-survival | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| **Total** | **150** | **150** | **115/115** | **15/15** | **130/130** | **100.0%** |

**150/150 total clean turns. 130/130 total checker runs (115/115 deterministic + 15/15 LLM).**

### LLM Checker Results

| Checker | Pass | Fail | Notes |
|---------|------|------|-------|
| directive_tone_match | 5/5 | 0/5 | All pass (non-rolled turns skip by default) |
| beat_narrative_chain | 5/5 | 0/5 | All pass |
| state_fidelity | 5/5 | 0/5 | All pass (empty extraction = pass by default) |

---

## Retry Rate Comparison

| Pack | Previous (e399818) | Post-Fix (69faea9) | Change |
|------|-------------------|-------------------|--------|
| space-western | 1 (T12) | 3 (T20, T28, T29) | +2 |
| allied-ww2 | 0 | 1 (T5) | +1 |
| noir-1930s | 0 | 1 (T23) | +1 |
| golden-piracy | **5 (T1, T8, T20, T25, T28)** | **1 (T15)** | **-4 (80% reduction)** |
| zombie-survival | 3 (T9, T19, T22) | 0 | -3 |
| **Total** | **9 retries** | **6 retries** | **-3 (33% reduction)** |

**Key improvement:** golden-piracy retry rate dropped from 16.7% to 3.3% (5→1 retries), confirming the `gm_beat.surface_as` and `arc_resolve` prompt fixes are effective.

---

## Failure Analysis

### All deterministic checkers now PASS (23/23 across all packs)

**Previously failing checkers (now fixed):**
1. **`location_change`** (allied-ww2 T24) — Fixed by adding explicit `location_change` vs `location_description` distinction in scene extractor prompt
2. **`goal_update_validity`** (noir-1930s T30) — Fixed by strengthening no-op detection guidance in storyteller prompt
3. **`inventory_integrity`** (3 packs, 11 occurrences) — Fixed by using `resolve_inventory_remove_target()` in checker

**Previously retry-causing issues (now fixed):**
1. **`gm_beat.surface_as` validation errors** (golden-piracy T1, T25, T28) — Fixed by clarifying `surface_as` vs `type` distinction
2. **`arc_resolve` empty object errors** (golden-piracy T8) — Fixed by warning against emitting empty `arc_resolve`

---

## Warnings Summary

Retry distribution:
- space-western: 3 retries (T20, T28, T29)
- allied-ww2: 1 retry (T5)
- noir-1930s: 1 retry (T23)
- golden-piracy: 1 retry (T15)
- zombie-survival: 0 retries

**Warning gaps:** None remaining. Thread dedup, compendium dedup, and seed soft-checks are all now stored in events.

---

## Comparison with Previous Eval (commit e399818, June 20)

| Pack | e399818 Raw | e399818 Post-Fix | 69faea9 Post-Fix |
|------|-----------|-----------------|------------------|
| space-western | 26/26 (100%) | 26/26 (100%) | 26/26 (100%) |
| allied-ww2 | 25/26 (96.2%) | 25/26 (96.2%) | 26/26 (100%) |
| noir-1930s | 25/26 (96.2%) | 25/26 (96.2%) | 26/26 (100%) |
| golden-piracy | 26/26 (100%) | 26/26 (100%) | 26/26 (100%) |
| zombie-survival | 26/26 (100%) | 26/26 (100%) | 26/26 (100%) |

**Key improvements:**
1. `location_change` (allied-ww2 T24) — Fixed by prompt clarification
2. `goal_update_validity` (noir-1930s T30) — Fixed by prompt clarification
3. `inventory_integrity` (3 packs) — Fixed by checker ID resolution
4. Retry rate reduced 33% overall (9→6), 80% for golden-piracy (5→1)

---

## Recommendations

1. **Monitor retry rate** — space-western increased from 1 to 3 retries. Investigate if this is normal variance or a regression.

2. **Continue prompt iteration** — The `gm_beat.surface_as` and `arc_resolve` fixes are clearly effective. Consider adding similar CRITICAL warnings to other prompt templates where LLM compliance issues have been observed.

3. **Consider inventory canonical ID matching** — The `resolve_inventory_canonical_id no match` warnings suggest some items are not being matched correctly. This is not causing checker failures but may indicate subtle inventory state drift.

4. **Next eval cycle** — Run the same 5 packs again to confirm stability of the 100% score.
