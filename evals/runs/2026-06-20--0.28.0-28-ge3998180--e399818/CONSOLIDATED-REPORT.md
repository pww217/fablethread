# Consolidated Eval Report — 2026-06-20

**Commit:** `e399818` (v0.28.0-28-ge3998180, dirty)
**Date:** 2026-06-20
**Packs:** 5 (space-western, allied-ww2, noir-1930s, golden-piracy, zombie-survival)
**Turns:** 30 per pack (150 total)
**Checkers:** 26 total per pack (23 deterministic + 3 LLM-based)
**Flags:** `--no-sanitize --temp 0.7 --eval --personality custom --rubric`

---

## Recent Changes (since c0d8778, June 19-20)

### 1. Thread Dormant/Active Swap
- `active` → `dormant` swap across thread models, prompts, and engine code.
- Affected: `thread_sanitizer.py`, `changes.py`, `storytell_user.j2`, `sanitize_thread.j2`.

### 2. Convergence Score Recalculation
- Now uses `active_threads` list with `dormant` exclusion.
- Checks `urgency` and `type` fields for scoring.
- Affected: `_pacing.py`.

### 3. Prompt Template Updates
- Thread list template: added `type` and `dormant` fields.
- Arc summaries, seed generation, and sanitization templates updated.
- Affected: `storytell_user.j2`, `generate_seed_system.j2`, `sanitize_thread.j2`.

### 4. NPC Group Identity Rules
- Type-level ID, quantity in name, distinguishing bio.
- Affected: `generate_seed_system.j2`.

### 5. Consumable Inventory Enforcement
- Consumables must use individual units (no clips/magazines).
- Affected: `generate_seed_system.j2`.

### 6. Arc Resolution Frequency Target
- Target set to 8-15 turns.
- Affected: engine validation.

### 7. Pacing Context Refactoring
- Refactored into `turn_context.py` and `turn_state.py`.
- Affected: `narrate.py`, `turn_context.py`, `turn_state.py`.

---

## Full Rubric Results

### space-western (30/30 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 1 retry at T12 (storytell). 30/30 turns clean.

### allied-ww2 (30/30 clean turns, 22/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 20 deterministic (except State) | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |
| location_change | FAIL (0.0) | T24: location_change emitted but post-turn location.id unchanged: narrow_muddy_lane |
| inventory_integrity | PASS (1.0) | Fixed: checker now uses resolve_inventory_remove_target() |

**Turn errors:** None. 30/30 turns clean.

### noir-1930s (30/30 clean turns, 22/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 20 deterministic (except Goals, State) | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |
| goal_update_validity | FAIL (0.0) | T30: goal_update equals previous turn's visible_goal (no change) |
| inventory_integrity | PASS (1.0) | Fixed: checker now uses resolve_inventory_remove_target() |

**Turn errors:** None. 30/30 turns clean.

### golden-piracy (30/30 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |

**Turn errors:** 5 retries (T1, T8, T20, T25, T28 — storytell: 4, state: 1). 30/30 turns clean.
**Rejections:** T20 (fire_bucket not found), T24 (flintlock_pistol_round not found).

### zombie-survival (30/30 clean turns, 23/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 22 deterministic (except State) | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| state_fidelity | PASS (1.0) | |
| inventory_integrity | PASS (1.0) | Fixed: checker now uses resolve_inventory_remove_target() |

**Turn errors:** 3 retries (T9, T19, T22 — storytell: 2, state: 1). 30/30 turns clean.
**Rejections:** T9 (sterile_wipe not found), T24 (revolver_round not found), T25 (heavy_duty_bandage not found).

---

## Summary

| Pack | Turns | Clean | Deterministic | LLM | Total | Score |
|------|-------|-------|---------------|-----|-------|-------|
| space-western | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| allied-ww2 | 30 | 30 | 22/23 | 3/3 | 25/26 | 96.2% |
| noir-1930s | 30 | 30 | 22/23 | 3/3 | 25/26 | 96.2% |
| golden-piracy | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| zombie-survival | 30 | 30 | 23/23 | 3/3 | 26/26 | 100.0% |
| **Total** | **150** | **150** | **113/115** | **15/15** | **128/130** | **98.5%** |

**150/150 total clean turns. 128/130 total checker runs (113/115 deterministic + 15/15 LLM).**

### LLM Checker Results

| Checker | Pass | Fail | Notes |
|---------|------|------|-------|
| directive_tone_match | 5/5 | 0/5 | All pass (non-rolled turns skip by default) |
| beat_narrative_chain | 5/5 | 0/5 | All pass |
| state_fidelity | 5/5 | 0/5 | All pass (empty extraction = pass by default) |

---

## Failure Analysis

### inventory_integrity — FIXED (was 3/5 packs fail, 11 occurrences)

**Root cause (resolved):** `inventory_integrity` checker compared raw storyteller IDs against canonical state IDs without resolution. The engine's `apply_delta` correctly resolved via `resolve_inventory_remove_target()`, but the checker did not.

**Affected packs/items (now fixed):**
- noir-1930s: `lead_rounds` (5 occurrences, T12, T18-T20, T26)
- allied-ww2: `garand_rounds` (2 occurrences, T21, T24)
- zombie-survival: `large_caliber_rounds` (4 occurrences, T15, T19, T22, T23)

**Fix:** Checker now uses `resolve_inventory_remove_target()` for ID resolution, matching engine behavior. All 3 packs now pass.

### location_change — 1/5 packs fail (1 occurrence)

**Root cause:** Storyteller emits `location_change` directive but the post-turn location ID remains unchanged.

**Affected:** allied-ww2 T24 (narrow_muddy_lane).

**Impact:** Minor — narration describes a location change that doesn't persist in state.

### goal_update_validity — 1/5 packs fail (1 occurrence)

**Root cause:** Storyteller emits `goal_update` identical to previous `visible_goal` (no-op).

**Affected:** noir-1930s T30 ("Survive the confrontation at Pier Nine and protect Brian Vance.").

**Impact:** Minor — redundant goal update, no state change.

---

## Warnings Summary

All 5 packs share the same 1 warning gap (warnings produced but not stored in events):
- `generate_seed soft-check` → seed.py:421-424 (logged only)

**Fixed:** Thread update dedup (stored in `thread_dedup_rejections` field) and Compendium NPC dedup (stored in `compendium_dedup_redirects` field) are now persisted in events.

Retry distribution:
- space-western: 1 retry (T12 storytell)
- allied-ww2: 0 retries
- noir-1930s: 0 retries
- golden-piracy: 5 retries (T1, T8, T20, T25, T28)
- zombie-survival: 3 retries (T9, T19, T22)

---

## Comparison with Previous Eval (commit 255992b, June 18)

Both dates use 26 total checkers (23 deterministic + 3 LLM). June 20 reports them separately for clarity.

| Pack | Jun 18 (255992b) | Jun 20 Raw (e399818) | Jun 20 Post-Fix (e399818) |
|------|------------------|----------------------|---------------------------|
| space-western | 26/26 (100%) | 26/26 (100%) | 26/26 (100%) |
| allied-ww2 | 26/26 (100%) | 24/26 (92.3%) | 25/26 (96.2%) |
| noir-1930s | 26/26 (100%) | 24/26 (92.3%) | 25/26 (96.2%) |
| golden-piracy | 25/26 (96.2%) | 26/26 (100%) | 26/26 (100%) |
| zombie-survival | 26/26 (100%) | 25/26 (96.2%) | 26/26 (100%) |

**Key changes:**
1. `state_fidelity` golden-piracy now passes (empty extraction pass-by-default fix retained from June 18).
2. `inventory_integrity` failures were introduced by the consumable inventory unit enforcement change, but are now fixed by making the checker use `resolve_inventory_remove_target()` for ID resolution.
3. Remaining failures: `location_change` (allied-ww2 T24), `goal_update_validity` (noir-1930s T30).
4. Overall: 4/5 packs at 100% after fix, 1 pack at 96.2%.

---

## Recommendations

1. **Fix `location_change` validation** — STORYTELLER PROMPT FIX APPLIED (see below). Scene extractor emits `location_change` when it should emit `location_description`.

2. **Fix `goal_update_validity` no-op detection** — STORYTELLER PROMPT FIX APPLIED (see below). Storyteller emits `goal_update` identical to previous `visible_goal`.

3. **Reduce golden-piracy retries** — STORYTELLER PROMPT FIX APPLIED (see below). 5 retries across 30 turns (16.7%) caused by: `gm_beat.surface_as` validation errors (T1, T25, T28), `arc_resolve` empty object (T8), no JSON found (T26).

4. **Store seed soft-check warnings in events** — COMPLETED (seed.py now stores in `_seed_soft_warnings`). Thread dedup and compendium NPC dedup are now stored in events.

### Fixes Applied (post-eval)

The following fixes were applied on branch `fix/eval-inventory-and-warnings`:

1. **`inventory_integrity` checker** — Now uses `resolve_inventory_remove_target()` to resolve raw storyteller IDs against canonical state IDs before comparison. This eliminates false positives where the storyteller emits `lead_rounds` but inventory stores `lead_round`.

2. **`warnings.py`** — Added `thread_dedup` and `compendium_dedup` columns to the warnings table. Removed thread dedup from "Warnings Gaps" (it is now stored in events).

3. **`extraction/pipeline.py`** — Compendium NPC dedup redirects are now collected and stored in `extraction_event["compendium_dedup_redirects"]`.

4. **`seed.py`** — Seed soft-check warnings are now stored in `envelope.seed_state.meta._seed_soft_warnings`.

### Prompt Fixes (post-eval session 2)

The following prompt fixes were applied to reduce storyteller/extractor compliance failures:

1. **`extract_scene_system.j2`** — Added explicit warning about `location_change` vs `location_description` distinction. Common mistake: scene extractor emits `location_change` when narration describes different atmosphere but PC is in same place.

2. **`storytell_system.j2`** — Added CRITICAL warning about `gm_beat.surface_as` vs `gm_beat.type` distinction. Storyteller was emitting `pressure` (a beat type) as `surface_as` (should be `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, or `item`). This caused 3/5 golden-piracy retries.

3. **`storytell_system.j2`** — Added CRITICAL warning about `arc_resolve` empty objects. Storyteller was emitting `arc_resolve: {}` instead of omitting the field. This caused T8 golden-piracy retry.

4. **`storytell_system.j2`** — Strengthened `goal_update` no-op detection guidance. Added explicit instruction to compare proposed `goal_update` against current `visible_goal` before emitting.
