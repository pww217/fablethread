

```yaml
state_fidelity_rate: 0.31
extraction_accuracy_score: 3
mechanic_lifecycle_score: 2
```

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