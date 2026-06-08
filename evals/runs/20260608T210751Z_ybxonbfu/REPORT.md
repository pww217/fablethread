# Eval Report — `baseline`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-08T21:07:51.154584+00:00 · **Finished:** 2026-06-08T21:14:20.965952+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T210751Z_ybxonbfu`  
**Track:** baseline  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T200711Z_jah59imd/artifacts`
**Scoring philosophy:** aggregate quality (baseline)  

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**State Fidelity:** —  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking`

**[state_correctness trace](baseline.state_correctness.trace.md)** · **[state_correctness verdict](baseline.state_correctness.judge.md)**  


## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| T1   | partial/flat | 0         | 0 → 0             | FLAT |
| T2   | setback     | -1        | 0 → -1            | —    |
| T4   | fail        | -1        | -1 → -2           | —    |
| T5   | crit_fail/fail | -2      | -1 → -3           | WRONG_DIR (band says fail, delta says -2) |
| T6   | partial/success | +1     | -3 → -2           | WRONG_DIR (floor at -3 should cap or trigger relief) |

**Momentum Analysis:** Momentum responds to dice rolls but violates floor constraints. At `momentum=-3` (T5/T6), the engine fails to enforce `config.momentum_floor`, allowing a +1 delta on T6 despite being at the absolute minimum. The band-to-delta mapping also drifts (`fail` yielding `-2` instead of `-1`).

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1             | opportunity | npc_behavior | opportunity       | Storytell   | Yes (expires T3) | —    |
| T2             | pressure    | npc_behavior | pressure          | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T4             | complication| npc_behavior | complication      | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T5             | complication| npc_behavior | complication      | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T6 (diff 5)    | pressure    | npc_behavior | pressure          | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T7 (diff 6)    | breathing_room | environmental | breathing_room  | Floor Relief| Yes (expires T10)| —    |

**Beat Analysis:** Floor relief consistently fails to inject `breathing_room` when `beat_locked=True` and storyteller emits pressure/complication beats. The counter increments on pressure types but the override logic is bypassed, creating a pressure loop until an explicit breathing_room finally fires at T7. TTL expiry checks run correctly; no orphaned beats detected.

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| T5   | None (empty block)  | Clear your debts... | Investigate Harker's disappearance and settle your debts. | Yes      | SILENT_CHANGE |

**Goal Analysis:** `visible_goal` changes at the end of Turn 5 without a corresponding `goal_update` string in any storyteller extraction output. This indicates either stale delta application from an unlogged turn or direct state mutation bypassing the pipeline.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| deliver_the_ledger | Seed | arc | normal | T2, T4, T5, T8, T9 | — | INERT (silent progress drifts: advancement→shift mix) |
| investigate_harker_disappearance | T7 | arc | normal | T10, T11, T13 | — | — |
| canyon_ambush | T9 | scene | urgent | T10 | T10 | RESOLUTION_FAILED (resolved in storyteller but state diff shows added to completed_threads with `last_updated_turn: null` mismatch) |
| unlock_the_tin_box | T5? | arc | normal | None | — | SILENT_CHANGE (appears in state without thread_add/thread_update emission trace) |

**Thread Analysis:** Scene-scoped threads purge correctly on location change. Arc threads persist but suffer from progress kind drift (`advancement` vs `shift`) and silent creation of `unlock_the_tin_box`. Resolution tracking for `canyon_ambush` shows metadata misalignment in the diff.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| heat_exhaustion | T1 | narrative | T2/T3 | ~2 turns | ORPHANED (no CONDITION_MODS entry per auto-checker) |
| rattled | T5 | narrative | T6 | ~1 turn | ORPHANED |
| chilled | T9 | environmental | T10 | ~1 turn | ORPHANED |

**Condition Analysis:** All added conditions lack `CONDITION_MODS` entries in the ruling/pacing math, meaning they do not affect dice rolls or momentum as designed. TTL tracking is disrupted by shuffled state diffs, but nominal durations align with extraction claims.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| T2   | Remove | credits | 1             | No        | —    |
| T4   | Update | iron_dagger | notes only | No      | —    |
| T8   | Add    | dried_meat, water_canteen, hemp_rope | 2/1/1 | No | — |
| T13  | Add    | whiskey_glass | 1           | No        | SPENDING_MISS (credits not deducted despite purchase narrative) |

**Inventory Analysis:** Extraction accurately captures additions and updates. Notable miss: `whiskey_glass` added at T13 without a corresponding credit deduction, violating the economy loop implied by the input/narrative.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory, conditions, threads, and location diverge significantly across turns due to trace shuffling and extraction gaps:
- **Location/Time Drift:** `meta.turn` regresses (`from: 7, to: 5` at T6 diff; `from: 13, to: 10` at T11 diff). Location IDs flip backwards (`outskirts_cabin → sheriff_station`). This breaks chronological causality for scene-scoped thread purging and beat expiry.
- **Condition/Rule Disconnect:** Conditions added via extraction never enter the ruling math (`CONDITION_MODS` missing), breaking the intended stat/difficulty interaction loop.
- **Goal/Thread Misalignment:** `visible_goal` shifts without storyteller emission; `unlock_the_tin_box` appears in state without pipeline trace, suggesting stale delta merge or out-of-band mutation.

### 2B — Extraction Drift
| Turn | Responsible Pipeline | Field That Drifted | Failure Type |
|------|---------------------|--------------------|--------------|
| T3   | Storytell           | `actions` (0 entries) | extraction_miss |
| T5   | Storytell/Ruling    | `actions` (0), `beat_locked` logic | schema_drift / engine_bug |
| T6   | Scene Extract       | `location_change.id` not applied to state | validation_rejection |
| T7-9 | Pacing Engine       | `pending_gm_beat.type` remains pressure/complication despite beat_locked=True | engine_bug (floor relief bypass) |
| T13  | State Extract       | Inventory add without credit remove | extraction_miss |

### 2C — State Fidelity Rate Calculation
Total logical turns evaluated: 13.
Turns with no rejected deltas AND no Auto-Checker failures AND no detected drift: T1, T4 (partial), T12 → **2/13**.
`state_fidelity_rate = 0.15`

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True failure or checker noise? | Root Cause | Remediation Tag |
|------|-----------|-------------------------------|------------|-----------------|
| T2   | `universal.conditions.orphan` | True failure | Condition added to state but never registered in ruling/pacing math (`CONDITION_MODS`). Pipeline omission. | extraction_miss |
| T3   | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Empty user input yielded `{}` storyteller output; LLM skipped action generation. | extraction_miss |
| T3   | `universal.pacing.consecutive_pressure_tracking` | True failure | Storyteller emitted null/empty beat, but counter incremented to 1. Logic reads stale state or miscounts. | engine_bug |
| T5   | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Same as T3. | extraction_miss |
| T5   | `universal.pacing.consecutive_pressure_tracking` | True failure | Counter stuck at 1 despite beat type mismatch. TTL expiry not resetting counter correctly. | engine_bug |
| T5   | `universal.pacing.beat_locked_dual_trigger` | True failure | Momentum hit floor (-3) but `beat_locked=False`. Floor check logic missing or gated incorrectly. | engine_bug |
| T6   | `universal.location_change.applied` | True failure | Scene extract emitted location delta, but validator/apply skipped it (likely ID mismatch or schema drift). | validation_rejection |
| T6   | `universal.conditions.orphan` | True failure | Same as T2. Condition lifecycle decoupled from ruling engine. | extraction_miss |
| T7   | `universal.pacing.floor_relief` | True failure | `beat_locked=True`, storytell emitted pressure, but floor relief did not override to breathing_room. Override logic bypassed. | engine_bug |
| T8   | `universal.pacing.floor_relief` | True failure | Same as T7. Complication beat persisted despite locked state. | engine_bug |
| T9   | `universal.pacing.floor_relief` | True failure | Same as T7/T8. Pressure loop continues unchecked. | engine_bug |
| T10  | `universal.conditions.orphan` | True failure | Same systemic condition orphaning. | extraction_miss |
| T10  | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Empty input → no actions emitted. | extraction_miss |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**Reason:** Repeated extraction failures on critical fields (`actions` missing on multiple turns, `location_change` not applied despite emission). Condition lifecycle extraction succeeds but fails to wire into downstream math. State drift from shuffled diffs and silent goal/thread mutations further degrade accuracy. Major extraction misses cap at 2 per rubric.

### Mechanic Lifecycle Score: 1/5
**Reason:** Floor relief mechanism consistently fails across T7-T9 despite `beat_locked=True` and pressure-type beats, breaking the intended de-escalation loop. Momentum floor constraints are violated (`momentum=-3 → -2`). Consecutive pressure tracking desynchronizes from beat types. Goal updates occur silently without storyteller emission. >4 red flags across tables; core pacing/arc governance is non-functional in this trace.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Floor relief override bypassed on `beat_locked=True`** (turns: T7, T8, T9) — Tag: `engine_bug`. Fix: Ensure `_check_floor_relief()` runs post-delta apply unconditionally when `beat_locked=True` and pending beat is pressure/complication/null. Verify gate logic does not block relief injection.
- **Momentum floor constraint ignored** (turns: T5, T6) — Tag: `engine_bug`. Fix: Clamp momentum deltas to `[momentum_min, momentum_max]` during `_apply_delta()` or ruling resolution; prevent +1 delta at `-3`.

**Major**
- **Conditions orphaned from ruling/pacing math** (turns: T2, T6, T10) — Tag: `extraction_miss`. Fix: Wire extracted conditions into `RulesOutcome.cond_mod` calculation during Step 0. Ensure `_apply_delta()` registers new conditions in a lookup table for future rulings.
- **Location change emission not applied to state** (turns: T6) — Tag: `validation_rejection`. Fix: Debug delta builder ID matching; ensure scene extract location IDs map correctly to state schema before validation rejection.

**Minor**
- **Actions extraction drops on empty/whitespace inputs** (turns: T3, T5, T10) — Tag: `extraction_miss`. Fix: Add fallback prompt guard in storyteller system template to always emit 4 actions even when user input is null or whitespace.
- **Silent arc goal/thread mutations without pipeline trace** (turns: T5, T7) — Tag: `stale_context`. Fix: Audit delta merge logic; ensure all state changes route through explicit extraction outputs rather than background batch processing or stale snapshot application.

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**285 passed, 25 failed**

> **Legend:** `[PASS]` = assertion passed · `[FAIL]` = assertion failed  
| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | [PASS] | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | [PASS] | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | [PASS] | (first turn) |
| 1 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 1 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 1 | `universal.inventory.no_overdraw` | [PASS] | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 1 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='opportunity', counter=0 |
| 1 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 1 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 1 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 1 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 1 | `universal.inventory.remove_existence` | [PASS] | (first turn) |
| 1 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 1 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 1 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 2 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=opportunity |
| 2 | `universal.location_change.applied` | [PASS] | (no change) |
| 2 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 2 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 2 | `universal.inventory.no_overdraw` | [PASS] | checked 1 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='opportunity', counter=0 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 2 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 2 | `universal.inventory.remove_existence` | [PASS] | checked 1 removes |
| 2 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 2 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['heat_exhaustion'] |
| 2 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 3 | `ruling.rolled` | [PASS] | rolled=False |
| 3 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 3 | `universal.location_change.applied` | [PASS] | (no change) |
| 3 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 3 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 3 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 3 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 3 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=1 (expected 0) |
| 3 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=-1, floor=-3) |
| 3 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 3 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 3 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 3 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 4 | `ruling.rolled` | [PASS] | rolled=True |
| 4 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=opportunity |
| 4 | `universal.location_change.applied` | [PASS] | (no change) |
| 4 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 4 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | [PASS] | band=setback delta=-1 (expected -1, engine may clamp) |
| 4 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 4 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 4 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 4 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 4 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['heat_exhaustion'] |
| 4 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 4 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 5 | `ruling.rolled` | [FAIL] | rolled=False |
| 5 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 5 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> assay_office |
| 5 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 5 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 5 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | [PASS] | directive 'Scene Pressure' rendered in storytell prompt |
| 5 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=2 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=-1, floor=-3) |
| 5 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 5 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 5 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 5 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 5 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 5 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 5 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 5 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 6 | `ruling.rolled` | [FAIL] | rolled=True |
| 6 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 6 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> sheriffs_station |
| 6 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 6 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | [PASS] | band=fail delta=-1 (expected -1, engine may clamp) |
| 6 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 6 | `universal.storytell.directive_rendered` | [PASS] | directive 'Breathe' rendered in storytell prompt |
| 6 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 6 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=-1, floor=-3) |
| 6 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 6 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 6 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 6 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 6 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 6 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 7 | `ruling.rolled` | [FAIL] | rolled=False |
| 7 | `extract.state.inventory_add` | [FAIL] | inventory_add[torn_map] not found |
| 7 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 7 | `universal.location_change.applied` | [PASS] | (no change) |
| 7 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 7 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 7 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 7 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 7 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 7 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=1 (expected 0) |
| 7 | `universal.pacing.beat_locked_dual_trigger` | [FAIL] | momentum=-3 at floor -3, but beat_locked=False — engine should have fired floor relief |
| 7 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 7 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=1 |
| 7 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 7 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 7 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 7 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 7 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 8 | `extract.state.inventory_remove` | [FAIL] | inventory_remove[credits] not found |
| 8 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 8 | `universal.location_change.applied` | [FAIL] | location_change emitted but post-turn location.id unchanged: outskirts_cabin |
| 8 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 8 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 8 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | [PASS] | directive 'Breathe' rendered in storytell prompt |
| 8 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='breathing_room', counter=0 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=-2, floor=-3) |
| 8 | `universal.pacing.floor_relief` | [PASS] | beat_locked=True, storytell emitted non-pressure beat 'breathing_room' — floor relief did not override |
| 8 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 8 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['rattled'] |
| 8 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 9 | `ruling.rolled` | [FAIL] | rolled=True |
| 9 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 9 | `universal.location_change.applied` | [PASS] | (no change) |
| 9 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 9 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | [PASS] | band=fail delta=0 (expected -1, engine may clamp) |
| 9 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 9 | `universal.storytell.directive_rendered` | [PASS] | directive 'Breathe' rendered in storytell prompt |
| 9 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=-3, floor=-3) |
| 9 | `universal.pacing.floor_relief` | [FAIL] | beat_locked=True, storytell_type='pressure' but pending_gm_beat.type='pressure' (expected 'breathing_room') |
| 9 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=1 |
| 9 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 9 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 9 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 9 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 9 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 10 | `ruling.rolled` | [FAIL] | rolled=False |
| 10 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 10 | `universal.location_change.applied` | [PASS] | outskirts_cabin -> general_store |
| 10 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 10 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 10 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 10 | `universal.storytell.directive_rendered` | [PASS] | directive 'Breathe' rendered in storytell prompt |
| 10 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=2 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=-3, floor=-3) |
| 10 | `universal.pacing.floor_relief` | [FAIL] | beat_locked=True, storytell_type='complication' but pending_gm_beat.type='complication' (expected 'breathing_room') |
| 10 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=2 |
| 10 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 10 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 10 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 10 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 10 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | [PASS] | beat variety OK: {'breathing_room': 1, 'pressure': 1, 'complication': 1} |
| 10 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 11 | `extract.state.pc_condition_remove` | [FAIL] | pc_condition_remove[bruised_ribs] not found |
| 11 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 11 | `universal.location_change.applied` | [PASS] | outskirts_cabin -> red_canyon |
| 11 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 11 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 11 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 11 | `universal.storytell.directive_rendered` | [PASS] | directive 'Breathe' rendered in storytell prompt |
| 11 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=3 |
| 11 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=-3, floor=-3) |
| 11 | `universal.pacing.floor_relief` | [FAIL] | beat_locked=True, storytell_type='pressure' but pending_gm_beat.type='pressure' (expected 'breathing_room') |
| 11 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 11 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | [FAIL] | momentum at floor for 3 consecutive turns |
| 11 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 11 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 11 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 11 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 11 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | [FAIL] | beats are 67% 'pressure' (threshold: 60%): {'pressure': 2, 'complication': 1} |
| 11 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 12 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 12 | `universal.location_change.applied` | [PASS] | (no change) |
| 12 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 12 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | [PASS] | band=success delta=2 (expected +2, engine may clamp) |
| 12 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | [PASS] | directive 'Pressure; Resolve a Threat' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 12 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=-3, floor=-3) |
| 12 | `universal.pacing.floor_relief` | [PASS] | beat_locked=True, storytell_type=None → floor relief injected breathing_room |
| 12 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | [FAIL] | momentum at floor for 3 consecutive turns |
| 12 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 12 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['chilled'] |
| 12 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 12 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 13 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 13 | `universal.location_change.applied` | [PASS] | (no change) |
| 13 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 13 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 13 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 13 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 13 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 13 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=-1, floor=-3) |
| 13 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 13 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 13 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 13 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 13 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 13 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 13 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 13 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |

## Universal Assert Results

> **Legend:** `[SYSTEM]` = system integrity failure (red severity) · `[PACING]` = pacing/perfection concern (yellow severity)  
| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.state.inventory_add` | [SYSTEM] | 1 | 1 | T7 |
| `extract.state.inventory_remove` | [SYSTEM] | 1 | 1 | T8 |
| `extract.state.pc_condition_remove` | [SYSTEM] | 1 | 1 | T11 |
| `ruling.rolled` | [SYSTEM] | 5 | 8 | T5 |
| `universal.beat_type.surface_as_consistency` | [PACING] | 0 | 13 | — |
| `universal.beat_type.variety` | [PACING] | 1 | 13 | T11 |
| `universal.conditions.orphan` | [SYSTEM] | 4 | 13 | T2 |
| `universal.directives.no_removed` | [PACING] | 0 | 13 | — |
| `universal.goal_update.applied` | [PACING] | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.no_overdraw` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.remove_existence` | [SYSTEM] | 0 | 13 | — |
| `universal.location_change.applied` | [SYSTEM] | 1 | 13 | T8 |
| `universal.momentum.band_delta` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.binding_present` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | [SYSTEM] | 0 | 13 | — |
| `universal.npc_states.no_removed` | [PACING] | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | [PACING] | 1 | 13 | T7 |
| `universal.pacing.consecutive_pressure_tracking` | [PACING] | 2 | 13 | T3 |
| `universal.pacing.floor_no_relief` | [PACING] | 2 | 13 | T11 |
| `universal.pacing.floor_relief` | [PACING] | 3 | 13 | T9 |
| `universal.pending_gm_beat.consumed` | [SYSTEM] | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | [SYSTEM] | 0 | 13 | — |
| `universal.storytell.actions_quality` | [SYSTEM] | 3 | 13 | T3 |
| `universal.storytell.directive_rendered` | [PACING] | 0 | 13 | — |
| `universal.thread_add.applied` | [SYSTEM] | 0 | 13 | — |
| `universal.thread_update.valid_id` | [SYSTEM] | 0 | 13 | — |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `canyon_ambush` | T9 | T9 | 1 |  |
| `clear_the_road_toughs` | T0 | T12 | 13 | ⚠️ >8 turns |
| `deliver_the_ledger` | T0 | T12 | 13 | ⚠️ >8 turns |
| `investigate_harker_disappearance` | T7 | T12 | 6 |  |
| `settle_the_debt` | T0 | T12 | 13 | ⚠️ >8 turns |
| `unlock_the_tin_box` | T13 | T12 | 0 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `assay_office` | 1 |  |
| `dustfall_outskirts` | 0 |  |
| `dustfall_saloon` | 3 |  |
| `general_store` | 1 |  |
| `marrows_crossing` | 1 |  |
| `outskirts_cabin` | 1 |  |
| `red_canyon` | 3 |  |
| `sheriffs_station` | 1 |  |

### Momentum Floor Runs

| Run Start | Run End | Duration (turns) |
|---|---|---:|
| T7 | T4 | -2 |
| T6 | T12 | 7 |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `chilled` | T9 | T9 | 1 |  |
| `heat_exhaustion` | T1 | T2 | 2 |  |
| `rattled` | T5 | T5 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | I ride into Dustfall and tie my horse at the liv… | 1117 (+0) | 3266 (+0) | 2863 (+0) | 1609 (+0) | 2744 (+28) | 0 | 0 | 36.33 |
| 2 | I step up to the bar and ask for a glass of wate… | 1313 (+0) | 3517 (+4) | 3131 (+10) | 1683 (+9) | 3060 (-24) | 0 | 0 | 26.19 |
| 3 |  | — | — | 0 (-3234) | 0 (-1689) | 0 (-3239) | 0 | 0 | 26.66 |
| 3 | I lean on the bar and ask what happened to Old M… | 1356 (-19) | 3662 (-11) | 3204 (-29) | 1721 (+14) | 3224 (-51) | 0 | 0 | 28.36 |
| 4 | I head over to the assay office to see if Harker… | 1388 (+29) | 3678 (-81) | 3245 (-82) | 1701 (-31) | 3305 (-151) | 0 | 0 | 36.14 |
| 5 | I walk to the sheriff's office and ask if he's f… | 1384 | 3829 | 3283 | 1700 | 3477 | 0 | 0 | 28.35 |
| 5 |  | — | — | 0 (-3380) | 0 (-1705) | 0 (-3546) | 0 | 0 | 26.31 |
| 6 | The sheriff gives me Harker's cabin key. I walk … | 1373 (+19) | 3890 (-97) | 3336 (+58) | 1706 (-1) | 3462 (-101) | 0 | 0 | 28.88 |
| 7 | I look through Harker's desk and find a locked t… | 1369 | 4049 | 3379 | 1678 | 3595 | 0 | 0 | 28.59 |
| 8 | I head back to the general store to buy supplies… | 1363 (+50) | 4001 (+92) | 3394 (+84) | 1685 (-92) | 3636 (+11) | 0 | 0 | 41.17 |
| 9 | I saddle up and ride out to Red Canyon. The trai… | 1406 | 4090 | 3381 | 1722 | 3722 | 0 | 0 | 29.09 |
| 10 | I find a camp at the base of the canyon wall. Tw… | 1402 (-3) | 4245 (+116) | 3408 (+2) | 1768 (-62) | 3820 (+71) | 0 | 0 | 26.56 |
| 10 |  | — | — | 0 (-3426) | 0 (-1836) | 0 (-3791) | 0 | 0 | 27.06 |
| 11 | The men surrender. I find Harker tied up in a ne… | 1413 | 4308 | 3398 | 1728 | 3842 | 0 | 0 | 0.00 |
| 12 | Harker and I ride back to Dustfall together. He'… | 1384 (-47) | 4251 (+29) | 3381 (-48) | 1727 (-109) | 3815 (-37) | 0 | 0 | 0.00 |
| 13 | I walk Harker to the doc's office and then head … | 1391 (-25) | 4292 (+6) | 3387 (+13) | 1722 (-80) | 3866 (-13) | 0 | 0 | 0.00 |
|  | TOTALS | 17659 | 51078 | 42790 | 22150 | 45568 | 0 | 0 | 389.69 |

**Total turns:** 16 · **Total duration:** 389.69s · **Avg/turn:** 24.36s
**Total tokens in:** 179,245 · **Total tokens out:** 10,331 · **Total LLM time:** 367.4s
**Total retries:** 0 · **Total parse failures:** 0

