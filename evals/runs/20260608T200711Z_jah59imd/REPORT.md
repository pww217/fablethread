# Eval Report — `baseline`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-08T20:07:11.772561+00:00 · **Finished:** 2026-06-08T20:13:36.992827+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T200711Z_jah59imd`  
**Track:** baseline  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T071015Z_pc3119x2/artifacts`
**Scoring philosophy:** aggregate quality (baseline)  

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**State Fidelity:** 31.0%  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking`

**[state_correctness trace](baseline.state_correctness.trace.md)** · **[state_correctness verdict](baseline.state_correctness.judge.md)**  


## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table
| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 1 | — | 0 | 0 → 0 | — |
| 2 | — | 0 | 0 → 0 | — |
| 3 | success | +1 | 0 → 1 | — |
| 4 | — | 0 | 1 → 1 | — |
| 5 | — | 0 | 1 → 1 | — |
| 6 | fail | -1 | 1 → 0 | — |
| 7 | — | 0 | 0 → 0 | — |
| 8 | fail | -1 | 0 → -1 | — |
| 9 | — | 0 | -1 → -1 | — |
| 10 | fail | -1 | -1 → -2 | — |
| 11 | — | 0 | -2 → -2 | — |
| 12 | — | 0 | -2 → -3 | FLAT |
| 13 | — | 0 | -3 → -3 | FLAT |

Momentum responds correctly to dice rolls across the run. Band-to-delta mapping matches engine constants. Flat flags on T12/T13 reflect no roll, not a directional error.

### 1B — GM Beat Lifecycle Table
| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | pressure | npc_behavior | pressure | storytell | Yes | — |
| T2 | complication | npc_behavior | complication | storytell | Yes | — |
| T3 | revelation | ambient | revelation | storytell | Yes | — |
| T4 | opportunity | npc_behavior | opportunity | storytell | Yes | — |
| T5 | pressure | npc_behavior | revelation | storytell | Yes | STATE_DRIFT |
| T6 | complication | environmental | complication | storytell | Yes | — |
| T7 | complication | environmental | complication | storytell | Yes | — |
| T8 | pressure | event | complication | storytell | Yes | STATE_DRIFT |
| T9 | null | null | breathing_room | floor_relief? | N/A | FLOOR_RELIEF_MISS |
| T10 | pressure | npc_behavior | null | storytell | Expired | — |
| T11 | complication | npc_behavior | pressure | storytell | Yes | STATE_DRIFT |
| T12 | escalation | npc_behavior | escalation | storytell | Yes | FLOOR_RELIEF_MISS |
| T13 | complication | npc_behavior | escalation | storytell | Yes | FLOOR_RELIEF_MISS |

Beat TTL (turn_no + 2) is respected when stored. Floor relief fails to override pressure/escalation beats on T12/T13 despite `beat_locked=True`. State drift occurs in pending_gm_beat.type across multiple turns.

### 1C — Arc Goal Update Table
| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| T1-T5 | None | Clear your debts... | Clear your debts... | Yes | — |
| T6-T8 | None | Clear your debts... | Investigate Harker's... | No | SILENT_CHANGE |
| T9 | None | Investigate Harker's... | Confront the travelers... | No | SILENT_CHANGE |
| T10-13 | None | Confront the travelers... | Confront the travelers... | Yes | — |

`visible_goal` shifts at T6 and T9 without corresponding `goal_update` emission in storyteller output. Direct dict assignment bypasses extraction signal, breaking traceability. Flagged as `SILENT_CHANGE`.

### 1D — Unified Thread Lifecycle Table
| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | 0 | Never | INERT |
| deliver_the_ledger | Seed | arc | normal | T3, T4, T5 | Never | UNRESOLVED_AT_END |
| clear_the_road_toughs | Seed | arc | background | T1, T2, T7, T9 | Never | UNRESOLVED_AT_END |
| investigate_harker_disappearance | T6 (implicit) | arc | normal | T3-T5, T8, T10, T11 | T12 | — |
| unrest_in_marrow_crossing | T8 | scene | urgent | T9 | Never | INERT |
| confrontation_at_overlook | T11 | scene | urgent | T12 | T13 | — |

`investigate_harker_disappearance` and `confrontation_at_overlook` resolve correctly to `completed_threads`. Two arc threads remain inactive without resolution signals. Scene thread `unrest_in_marrow_crossing` deactivates but lacks explicit purge signal.

### 1E — Condition Lifecycle Table
| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| unsettled | T3 | narrative | T4 | 2 turns | — |
| fatigued | T5 | narrative | Never | >8 turns | OVERLONG, ORPHAN |
| dust_in_eyes | T6 | narrative | T9 | 3 turns | — |
| startled | T7 | narrative | T9 | 2 turns | — |
| rattled | T10 | narrative | T13 | 3 turns | — |
| cornered | T11 | narrative | Never | >2 turns | ACTIVE |

`fatigued` lacks a `CONDITION_MODS` registry entry, persists beyond TTL tracking, and is flagged by auto-checkers as orphan. Other conditions follow expected add/remove cycles.

### 1F — Inventory Evolution Table
| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| T1 | Add | horse | 1 | No | — |
| T2 | Remove | credits | 1 | No | — |
| T6 | Add | iron_key | 1 | No | STATE_DRIFT |
| T8 | Add | dried_meat, water_canteen, hempen_rope | 1 each | No | AMOUNT_MISMATCH |
| T9 | Remove | dried_meat, water_canteen, hempen_rope | 1 each | No | STATE_DRIFT |
| T12 | Add | stolen_hat | 1 | No | — |
| T13 | Add | whiskey | 1 | No | — |

Items added in T8 extract delta are removed in subsequent state diffs without narrative cause or extraction signal. `iron_key` shows duplicate add/remove cycles across diffs. Flagged as `STATE_DRIFT` and `AMOUNT_MISMATCH`.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory, conditions, threads, and NPCs show consistent drift patterns rather than hard breaks:
- **Conditions**: `fatigued` persists indefinitely without TTL decay or mod lookup `(Turns 5–13, pc.conditions)`. Auto-checkers flag orphan status repeatedly.
- **Threads**: `deliver_the_ledger` and `clear_the_road_toughs` remain in `arc.threads[]` with `active: false` but lack resolution signals or auto-latent demotion logs `(Turn 9, arc.threads[])`.
- **NPC Compendium**: Presence/location fields jump between turns without narrative triggers (e.g., `bartender_dustfall` location shifts from saloon to assay office in diffs `(Turn 4, compendium.npcs.bartender_dustfall.last_seen)`).

### 2B — Extraction Drift
- **T5, T8, T11**: Storyteller emits `gm_beat.type=X`, but state reflects `Y` `(state.meta.pending_gm_beat.type)`. Pipeline emitted correct signal; engine merge or diff generation overwrote it. Tag: `schema_drift`.
- **T9 (empty input block)**: Extract pipelines return `{}`. Actions quality drops to 0, beat type becomes null, but consecutive pressure counter stays at 2 `(Turn 9, state.meta.consecutive_pressure_turns)`. Extraction failure cascades into pacing sync bug. Tag: `extraction_miss` → `engine_bug`.
- **T6, T9**: Location change emitted in extract delta but post-turn snapshot retains old ID `(state.location.id)`. Delta validation passes, apply mutates state, diff generation reads stale cache or fails to persist before checkpoint. Tag: `validation_rejection` (soft).

### 2C — State Fidelity Rate Calculation
Total turns evaluated: 13  
Turns with no rejected deltas AND no Auto-Checker failures AND no detected drift: T1, T2, T3, T4 = 4  
Arithmetic: 4 / 13 = **0.307** → `state_fidelity_rate: 0.31`

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True/Noise? | Root Cause | Remediation Tag |
|------|-----------|-------------|------------|-----------------|
| 4 | universal.conditions.orphan (`unsettled`) | True failure | Condition added via narrative extraction lacks `CONDITION_MODS` registry entry; engine skips mod lookup. | `extraction_miss` |
| 5 | universal.storytell.actions_quality (0) | True failure | Empty user input triggers null storyteller output pipeline; actions field omitted entirely. | `extraction_miss` |
| 5 | universal.pacing.consecutive_pressure_tracking | True failure | Storyteller emits null beat type, but state counter retains stale value=2 instead of resetting to 0. | `engine_bug` |
| 5 | universal.conditions.orphan (`fatigued`, `dust_in_eyes`) | True failure | Same registry gap as T4; narrative-derived IDs bypass condition mod schema validation. | `extraction_miss` |
| 6 | universal.location_change.applied | True failure | Extract delta emits location change, but post-turn snapshot id remains old value. Apply mutation or diff read fails silently. | `engine_bug` |
| 7 | universal.conditions.orphan (`fatigued`, `dust_in_eyes`) | True failure | Persistent registry gap; conditions persist without TTL/mod enforcement. | `extraction_miss` |
| 8 | universal.storytell.actions_quality (0) | True failure | Null input block drops actions extraction signal entirely. | `extraction_miss` |
| 8 | universal.pacing.consecutive_pressure_tracking | True failure | Storyteller emits pressure, but state counter=0. Counter sync lags or resets incorrectly on null-turn artifacts. | `engine_bug` |
| 8 | universal.conditions.orphan (`fatigued`, etc.) | True failure | Registry gap persists across turns. | `extraction_miss` |
| 9 | universal.storytell.actions_quality (0) | True failure | Null input block; extraction pipeline returns empty dict, actions omitted. | `extraction_miss` |
| 9 | universal.pacing.consecutive_pressure_tracking | True failure | Beat type=None in state, counter stuck at 2. Reset logic missing for null storyteller outputs. | `engine_bug` |
| 9 | universal.conditions.orphan (`fatigued`, etc.) | True failure | Registry gap persists. | `extraction_miss` |
| 9 | universal.location_change.applied | True failure | Extract delta emits location change, state id unchanged. Apply/diff mismatch. | `engine_bug` |
| 10 | universal.conditions.orphan (`fatigued`) | True failure | Registry gap persists. | `extraction_miss` |
| 10 | universal.storytell.actions_quality (0) | True failure | Null input block; actions signal dropped. | `extraction_miss` |
| 11 | universal.conditions.orphan (`fatigued`, `rattled`) | True failure | Registry gap persists. | `extraction_miss` |
| 12 | universal.pacing.floor_relief | True failure | `beat_locked=True`, storytell emits escalation, but pending_gm_beat stays escalation instead of injecting breathing_room. Override logic bypassed or condition check fails. | `engine_bug` |
| 12 | universal.conditions.orphan (`fatigued`, etc.) | True failure | Registry gap persists. | `extraction_miss` |
| 13 | universal.storytell.actions_quality (0) | True failure | Null input block; actions signal dropped. | `extraction_miss` |
| 13 | universal.pacing.floor_relief | True failure | Same as T12: beat_locked=True, storytell emits complication, pending stays complication. Floor relief injection fails to trigger or override. | `engine_bug` |
| 13 | universal.conditions.orphan (`fatigued`, etc.) | True failure | Registry gap persists. | `extraction_miss` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 3/5
Extraction pipelines consistently produce valid JSON structures when inputs are populated, but fail to emit actions on null/empty turns (T5, T8, T9, T10, T13). Condition extraction lacks registry fallbacks, causing orphan flags. State drift in `pending_gm_beat.type` and location diffs indicates schema merge/diff generation gaps rather than pure LLM hallucination. No critical state corruption; core inventory/condition lifecycle remains traceable despite noise.

### Mechanic Lifecycle Score: 2/5
Red flags exceed threshold (>4 across tables). GM beat floor relief consistently fails to override pressure/escalation beats on T12/T13 despite `beat_locked=True`, breaking de-escalation design intent. Pacing consecutive-pressure counter desyncs on null storyteller outputs, retaining stale values instead of resetting. Two arc threads remain inert without resolution or auto-latent demotion signals. Condition TTL tracking is broken for narrative-derived IDs (`fatigued`). Mechanics function but exhibit repeated sync failures and missing override paths.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Floor relief injection fails to override pressure/escalation beats when `beat_locked=True`** (turns: 12, 13) — Tag: `engine_bug`. Fix: Patch `_check_floor_relief()` in `engine/turn.py` to evaluate storyteller-emitted beat type against the locked state and force-inject a `breathing_room` beat with TTL=3 when conditions are met (consecutive pressure threshold reached, not momentum floor).
- **Pacing consecutive-pressure counter desyncs on null storyteller outputs** (turns: 5, 8, 9) — Tag: `engine_bug`. Fix: Ensure post-extraction step resets `state.meta.consecutive_pressure_turns` to 0 whenever `storyteller_result.gm_beat.type` is None/null or extraction returns empty dict.

**Major**
- **Condition registry lacks fallback for narrative-derived IDs, causing orphan persistence and TTL bypass** (turns: 4–13) — Tag: `extraction_miss`. Fix: Add a default `CONDITION_MODS=0` lookup in the condition application pipeline or enforce strict schema validation during state extract to reject unregistered conditions with a warning instead of silent orphaning.
- **Location change delta emitted but post-turn snapshot retains stale ID** (turns: 6, 9) — Tag: `engine_bug`. Fix: Verify `_apply_delta()` correctly mutates `state.location` before diff generation and ensure atomic state write completes before checkpoint reads occur in the eval harness.

**Minor**
- **Actions quality drops to 0 on empty/null user input turns** (turns: 5, 8, 9, 10, 13) — Tag: `extraction_miss`. Fix: Update storyteller prompt handling for null inputs to emit placeholder/generic actions based on `recent_beats` and scene context, or ensure the extraction pipeline gracefully skips action emission without breaking downstream UI expectations.
- **Arc threads deactivate but lack explicit resolution signals** (turns: 2–9) — Tag: `scope_violation`. Fix: Ensure storyteller emits `thread_resolve` for inactive arc threads that reach narrative closure, or implement a post-turn cleanup pass to auto-resolve inert threads with state="superseded" matching the design spec.

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**283 passed, 27 failed**

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
| 1 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
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
| 2 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 2 | `universal.location_change.applied` | [PASS] | (no change) |
| 2 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 2 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 2 | `universal.inventory.no_overdraw` | [PASS] | checked 1 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=2 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 2 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 2 | `universal.inventory.remove_existence` | [PASS] | checked 1 removes |
| 2 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 2 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 2 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 3 | `ruling.rolled` | [FAIL] | rolled=True |
| 3 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 3 | `universal.location_change.applied` | [PASS] | (no change) |
| 3 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 3 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | [PASS] | band=success delta=1 (expected +1, engine may clamp) |
| 3 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 3 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='revelation', counter=0 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 3 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 3 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 3 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | [PASS] | beat variety OK: {'pressure': 1, 'complication': 1, 'revelation': 1} |
| 3 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 4 | `ruling.rolled` | [FAIL] | rolled=False |
| 4 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 4 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> assay_office |
| 4 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 4 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 4 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | [PASS] | directive 'Scene Pressure' rendered in storytell prompt |
| 4 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='opportunity', counter=0 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 4 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 4 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 4 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['unsettled'] |
| 4 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | [PASS] | beat variety OK: {'complication': 1, 'revelation': 1, 'opportunity': 1} |
| 4 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 5 | `ruling.rolled` | [FAIL] | rolled=False |
| 5 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=opportunity |
| 5 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> sheriffs_office |
| 5 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 5 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 5 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
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
| 5 | `universal.beat_type.variety` | [PASS] | beat variety OK: {'revelation': 1, 'opportunity': 1, 'pressure': 1} |
| 5 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 6 | `ruling.rolled` | [PASS] | rolled=False |
| 6 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 6 | `universal.location_change.applied` | [PASS] | (no change) |
| 6 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 6 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 6 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 6 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 6 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 6 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 6 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 6 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 6 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 6 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 6 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued', 'dust_in_eyes'] |
| 6 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 6 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 7 | `ruling.rolled` | [FAIL] | rolled=False |
| 7 | `extract.state.inventory_add` | [FAIL] | inventory_add[torn_map] not found |
| 7 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 7 | `universal.location_change.applied` | [FAIL] | location_change emitted but post-turn location.id unchanged: north_ridge_cabin |
| 7 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 7 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 7 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 7 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 7 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=2 |
| 7 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 7 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 7 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 7 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 7 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 7 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued'] |
| 7 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 8 | `extract.state.inventory_remove` | [FAIL] | inventory_remove[credits] not found |
| 8 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 8 | `universal.location_change.applied` | [PASS] | (no change) |
| 8 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 8 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | [PASS] | band=fail delta=-1 (expected -1, engine may clamp) |
| 8 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 8 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=3 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 8 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 8 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 8 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued', 'dust_in_eyes'] |
| 8 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 9 | `ruling.rolled` | [PASS] | rolled=False |
| 9 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 9 | `universal.location_change.applied` | [PASS] | (no change) |
| 9 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 9 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 9 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 9 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 9 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 9 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 9 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 9 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 9 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 9 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 9 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued'] |
| 9 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 10 | `ruling.rolled` | [FAIL] | rolled=False |
| 10 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 10 | `universal.location_change.applied` | [PASS] | red_canyon_plateau -> marrows_crossing_general_store |
| 10 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 10 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 10 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 10 | `universal.storytell.directive_rendered` | [PASS] | directive 'Resolve a Threat' rendered in storytell prompt |
| 10 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 10 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=0, floor=-3) |
| 10 | `universal.pacing.floor_relief` | [PASS] | beat_locked=True, storytell_type='pressure' → floor relief injected breathing_room |
| 10 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 10 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 10 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 10 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued', 'dust_in_eyes', 'startled'] |
| 10 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 10 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 11 | `extract.state.pc_condition_remove` | [FAIL] | pc_condition_remove[bruised_ribs] not found |
| 11 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 11 | `universal.location_change.applied` | [PASS] | (no change) |
| 11 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 11 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 11 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 11 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 11 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 11 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 11 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=-2, floor=-3) |
| 11 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 11 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 11 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 11 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 11 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 11 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued', 'rattled', 'cornered'] |
| 11 | `universal.thread_add.applied` | [FAIL] | thread(s) added but never appeared in state: ['unrest_in_marrow_crossing'] |
| 11 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 11 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 12 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 12 | `universal.location_change.applied` | [FAIL] | location_change emitted but post-turn location.id unchanged: red_canyon_plateau |
| 12 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 12 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 12 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | [PASS] | directive 'Pressure' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 12 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 12 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 12 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 12 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued', 'startled'] |
| 12 | `universal.thread_add.applied` | [FAIL] | thread(s) added but never appeared in state: ['unrest_in_marrow_crossing'] |
| 12 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 13 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 13 | `universal.location_change.applied` | [PASS] | (no change) |
| 13 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 13 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | [PASS] | band=fail delta=-1 (expected -1, engine may clamp) |
| 13 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 13 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 13 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 13 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 13 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 13 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 13 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 13 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['fatigued'] |
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
| `ruling.rolled` | [SYSTEM] | 5 | 8 | T3 |
| `universal.beat_type.surface_as_consistency` | [PACING] | 0 | 13 | — |
| `universal.beat_type.variety` | [PACING] | 0 | 13 | — |
| `universal.conditions.orphan` | [SYSTEM] | 9 | 13 | T4 |
| `universal.directives.no_removed` | [PACING] | 0 | 13 | — |
| `universal.goal_update.applied` | [PACING] | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.no_overdraw` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.remove_existence` | [SYSTEM] | 0 | 13 | — |
| `universal.location_change.applied` | [SYSTEM] | 2 | 13 | T7 |
| `universal.momentum.band_delta` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.binding_present` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | [SYSTEM] | 0 | 13 | — |
| `universal.npc_states.no_removed` | [PACING] | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | [PACING] | 0 | 13 | — |
| `universal.pacing.consecutive_pressure_tracking` | [PACING] | 3 | 13 | T6 |
| `universal.pacing.floor_no_relief` | [PACING] | 0 | 13 | — |
| `universal.pacing.floor_relief` | [PACING] | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | [SYSTEM] | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | [SYSTEM] | 0 | 13 | — |
| `universal.storytell.actions_quality` | [SYSTEM] | 3 | 13 | T6 |
| `universal.storytell.directive_rendered` | [PACING] | 0 | 13 | — |
| `universal.thread_add.applied` | [SYSTEM] | 2 | 13 | T11 |
| `universal.thread_update.valid_id` | [SYSTEM] | 0 | 13 | — |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `clear_the_road_toughs` | T0 | T12 | 13 | ⚠️ >8 turns |
| `confrontation_at_overlook` | T11 | T12 | 2 |  |
| `deliver_the_ledger` | T0 | T12 | 13 | ⚠️ >8 turns |
| `investigate_harker_disappearance` | T6 | T11 | 6 |  |
| `settle_the_debt` | T0 | T12 | 13 | ⚠️ >8 turns |
| `unrest_in_marrow_crossing` | T8 | T8 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `assay_office` | 1 |  |
| `dustfall_saloon` | 3 |  |
| `marrows_crossing` | 1 |  |
| `marrows_crossing_general_store` | 1 |  |
| `north_ridge_cabin` | 2 |  |
| `red_canyon_plateau` | 4 |  |
| `sheriffs_office` | 1 |  |

### Momentum Floor Runs

| Run Start | Run End | Duration (turns) |
|---|---|---:|
| T12 | T13 | 2 |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `cornered` | T11 | T11 | 1 |  |
| `dust_in_eyes` | T6 | T7 | 2 |  |
| `fatigued` | T6 | T12 | 7 | ⚠️ >6 turns |
| `rattled` | T11 | T12 | 2 |  |
| `startled` | T7 | T8 | 2 |  |
| `unsettled` | T3 | T3 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | I ride into Dustfall and tie my horse at the liv… | 1117 (+0) | 3266 (+0) | 2863 (-48) | 1609 (-48) | 2716 (-33) | 0 | 0 | 30.79 |
| 2 | I step up to the bar and ask for a glass of wate… | 1313 (-42) | 3513 (-97) | 3121 (-76) | 1674 (-11) | 3084 (-125) | 0 | 0 | 22.85 |
| 3 | I lean on the bar and ask what happened to Old M… | 1364 (-24) | 3683 (-51) | 3234 (-22) | 1689 (+35) | 3239 (-12) | 0 | 0 | 22.95 |
| 4 | I head over to the assay office to see if Harker… | 1375 (+20) | 3673 (-77) | 3233 (+24) | 1707 (+66) | 3275 (-17) | 0 | 0 | 26.21 |
| 5 | I walk to the sheriff's office and ask if he's f… | 1359 (+29) | 3759 (-14) | 3327 (+15) | 1732 (-1) | 3456 (-37) | 0 | 0 | 42.58 |
| 5 |  | — | — | 0 | 0 | 0 | 0 | 0 | 32.92 |
| 6 | The sheriff gives me Harker's cabin key. I walk … | 1405 (-7) | 3911 (-73) | 3380 (-72) | 1705 (-4) | 3546 (+66) | 0 | 0 | 28.64 |
| 7 | I look through Harker's desk and find a locked t… | 1354 (-24) | 3987 (-65) | 3278 (-117) | 1707 (+45) | 3563 (-64) | 0 | 0 | 32.16 |
| 8 |  | — | — | 0 (-3337) | 0 (-1701) | 0 (-3643) | 0 | 0 | 25.71 |
| 8 | I head back to the general store to buy supplies… | 1313 | 3909 | 3310 | 1777 | 3625 | 0 | 0 | 38.26 |
| 9 |  | — | — | 0 (-3371) | 0 (-1773) | 0 (-3631) | 0 | 0 | 26.78 |
| 9 | I saddle up and ride out to Red Canyon. The trai… | 1405 (+22) | 4129 (-24) | 3406 (-15) | 1830 (+122) | 3749 (+13) | 0 | 0 | 26.63 |
| 10 | I find a camp at the base of the canyon wall. Tw… | 1398 | 4168 | 3426 | 1836 | 3791 | 0 | 0 | 28.66 |
| 10 |  | — | — | 0 (-3382) | 0 (-1692) | 0 (-3760) | 0 | 0 | 0.00 |
| 11 | The men surrender. I find Harker tied up in a ne… | 1431 (+83) | 4222 (+37) | 3429 (+81) | 1836 (+165) | 3852 (+128) | 0 | 0 | 0.00 |
| 12 | Harker and I ride back to Dustfall together. He'… | 1416 (+70) | 4286 (+130) | 3374 (-15) | 1802 (+88) | 3879 (+111) | 0 | 0 | 0.00 |
| 13 |  | — | — | 0 | 0 | 0 | 0 | 0 | 0.00 |
| 13 | I walk Harker to the doc's office and then head … | 1384 | 4247 | 3360 | 1843 | 3819 | 0 | 0 | 0.00 |
|  | TOTALS | 17634 | 50753 | 42741 | 22747 | 45594 | 0 | 0 | 385.12 |

**Total turns:** 18 · **Total duration:** 385.12s · **Avg/turn:** 21.40s
**Total tokens in:** 179,469 · **Total tokens out:** 10,806 · **Total LLM time:** 363.4s
**Total retries:** 0 · **Total parse failures:** 0

