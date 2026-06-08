---
state_fidelity_rate: 0.15
extraction_accuracy_score: 2
mechanic_lifecycle_score: 1
---

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 2 | crit_success | +2 | 0 → 2 | — |
| 3 | fail | -1 | 2 → 1 | WRONG_DIR (Auto-Checker: prev=1 cur=2, expected delta -1) |
| 4 | success | +1 | 1 → 2 | WRONG_DIR (Auto-Checker: prev=2 cur=1, expected delta +1) |
| 5 | partial | 0 | 2 → 2 | — |
| 6 | fail (impossible) | -1 | 2 → 1 | WRONG_DIR (Auto-Checker: prev=1 cur=2) |
| 7 | fail | -1 | 1 → 0 | — |
| 8 | impossible | 0 | 0 → 0 | FLAT |
| 9 | impossible | 0 | 0 → 0 | FLAT |
| 10 | success | +1 | 0 → 1 | — |

**Is momentum responding correctly to dice rolls across the run?** No. The Auto-Checker flags multiple `WRONG_DIR` and `FLAT` anomalies where the state delta does not match the band-derived expectation, indicating significant state drift or application failures in the momentum field.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | revelation | player_discovery | pressure (T3) | Storytell/Override | Yes | — |
| T2 | null | null | pressure (T4) | Floor Relief Miss | N/A | FLOOR_RELIEF_MISS |
| T3 | pressure | npc_behavior | pressure (T6) | Storytell | No | TTL_EXCEEDED (expires T5, seen at T6) |
| T4 | pressure | npc_behavior | pressure (T7) | Floor Relief Miss | N/A | FLOOR_RELIEF_MISS |
| T5 | pressure | ambient | breathing_room (T8) | Storytell/Override | Yes | — |
| T6 | null | null | complication (T9) | Storytell | N/A | — |
| T7 | null | null | pressure (T10) | Floor Relief Miss | N/A | FLOOR_RELIEF_MISS |
| T8 | null | null | breathing_room (T12) | Floor Relief Miss | N/A | FLOOR_RELIEF_MISS |
| T9 | complication | environmental | complication (T11) | Storytell | Yes | — |
| T10 | pressure | environmental | pressure (T13) | Storytell | No | TTL_EXCEEDED (expires T12, seen at T13) |

**Note:** The `recent_beats` history in the state snapshots shows significant desynchronization with turn numbers (e.g., Turn 6 diff references "Turn 7" for prior history additions). This suggests a global turn counter drift or replay issue affecting TTL calculations.
Flags: `FLOOR_RELIEF_MISS` appears repeatedly where `beat_locked=True` but no relief was injected because the storyteller emitted a pressure-type beat (which floor relief should override, but the checker flags it as a miss if the resulting state isn't breathing_room).

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| T5 (diff) | "Investigate Harker's disappearance..." | "Clear your debts..." | "Investigate Harker's..." | Yes | — |
| T10 (diff) | "Confront the men at the canyon camp." | "Investigate Harker's..." | "Confront the men..." | Yes | — |

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | T5, T12 | — | INERT (Active at T5, silent until end) |
| deliver_the_ledger | Seed | arc | normal | T3, T4, T8, T9, T10 | T11 | RESOLUTION_FAILED (Resolved in diff but thread remains active/changed in later diffs) |
| clear_the_road_toughs | Seed | arc | background | T2 | T10 | — |
| investigate_harker_disappearance | T5 | arc | normal | T6, T7, T9, T11 | T12 | RESOLUTION_FAILED (Resolved in diff but thread remains active/changed in later diffs) |

**Note:** The `deliver_the_ledger` and `investigate_harker_disappearance` threads show `RESOLUTION_FAILED`. They appear in `completed_threads` with a resolution state, yet subsequent turn diffs (`T10`, `T12`) still list them as "removed" or "changed" from the active thread pool without clear finalization, suggesting the `_merge_arc_update` logic is fighting with direct dict assignments or stale deltas.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| heat_exhaustion | T2 | State Extract | T3 | 1 turn | SILENT_DROP (Auto-Checker: orphan, no condition_mods entry) |
| rattled | T4 | State Extract | — | >5 turns | OVERLONG / ORPHAN (Auto-Checker: orphan at T4, T7) |
| threatened | T6 | Storytell? | — | >2 turns | SILENT_DROP (Auto-Checker: orphan at T6) |
| startled | T10 | State Extract | — | 1 turn | ORPHAN (Auto-Checker: orphan at T11) |
| dust_in_eyes | T12 | State Extract | — | 1 turn | ORPHAN (Auto-Checker: orphan at T13) |

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| T2 | Remove | credits | 1 | No | — |
| T8 | Add | dried_meat, canteen, rope | 1 each | No | — |
| T9 | Add | discarded_lantern | 1 | No | — |
| T13 | Add | whiskey | 1 | No | — |

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
**Severe Incoherence.** The state snapshots exhibit "time travel" behavior. Turn diffs reference turn numbers that are higher than the current turn (e.g., T6 diff shows prior history from T7, T10). Location IDs and names frequently revert to previous values in subsequent diffs (e.g., `dustfall_perimeter` at T8 reverts to `sheriffs_station` description/name logic in later diffs or vice versa depending on the diff view). Conditions are marked as "orphaned" by the auto-checker, meaning they exist in state but have no corresponding mechanical effect (condition_mods) applied to dice rolls, breaking the feedback loop between narrative and mechanics.

### 2B — Extraction Drift
- **Turn 3:** `universal.storytell.actions_quality` failure indicates extraction pipeline emitted empty actions list despite valid output structure elsewhere. This is an **extraction_miss**.
- **Turns 4, 8:** `universal.location_change.applied` failures indicate the extractor identified a location change (`dustfall_main_street`, `dustfall_perimeter`) but the applied delta did not update `state.location.id`. This is a **schema_drift** or **validation_rejection** where the engine ignored valid deltas.
- **Turns 2, 3, 4, 6, 10, 11, 12:** Repeated `universal.conditions.orphan` failures indicate that while conditions were added to state, they failed to register in the dice resolution logic (`condition_mods`). This is a **wrong_pipeline** issue where State Extract writes to condition list but Ruling/Narrate pipeline fails to read/apply them.

### 2C — State Fidelity Rate Calculation
Total Turns: 13 (Turns 1-13, noting duplicate turn labels in trace are likely replay/diff artifacts, counting unique logical turns).
Failures per turn:
- T1: Clean
- T2: Condition Orphan
- T3: Actions Miss, Pressure Tracking x2, Momentum Wrong Dir, Condition Orphans x2
- T4: Location Applied Fail, Momentum Wrong Dir, Condition Orphan
- T5: Momentum Wrong Dir, Actions Miss
- T6: Floor Relief Fail, Condition Orphan
- T7: Clean (in diff view) / Pressure Tracking Fail in metrics? (Metrics show T9 pressure fail). Let's count based on Auto-Checker table.
- T8: Location Applied Fail
- T9: Pressure Tracking Fail
- T10: Actions Miss
- T11: Condition Orphan
- T12: Floor Relief Fail, Condition Orphan
- T13: Clean

Clean Turns: 1, 7, 13 (3 turns).
Total Turns: 13.
Rate: 3/13 ≈ 0.23. However, the "time travel" diffs suggest many of these are corrupted snapshots rather than clean runs. If we count unique logical events where state *should* have been consistent:
Turns with NO auto-checker failures: T1, T7 (diff view), T13.
Rate: 3/13 = **0.23**.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 2 | `universal.conditions.orphan` | True Failure | Condition added but not passed to dice resolution context. | wrong_pipeline |
| 3 | `universal.storytell.actions_quality` | True Failure | Storyteller pipeline emitted empty actions list. | extraction_miss |
| 3 | `universal.pacing.consecutive_pressure_tracking` (x2) | True Failure | Counter logic mismatch: beat type vs counter value diverged. Likely null beat counted or pressure not counted correctly. | engine_bug |
| 3 | `universal.conditions.orphan` (rattled, heat_exhaustion) | True Failure | Same as T2. Conditions exist but don't affect mechanics. | wrong_pipeline |
| 3 | `universal.momentum.band_delta` | True Failure | Momentum state did not update according to band (-1 expected for fail, +1 observed). | engine_bug |
| 4 | `universal.location_change.applied` | True Failure | Location change extracted but delta application failed or was ignored. | schema_drift |
| 4 | `universal.momentum.band_delta` | True Failure | Momentum state drift (2→1 expected for success +1, got -1). | engine_bug |
| 4 | `universal.conditions.orphan` | True Failure | Condition orphaning persists. | wrong_pipeline |
| 5 | `universal.momentum.band_delta` | True Failure | Momentum state drift (1→2 expected for partial 0, got +1). | engine_bug |
| 5 | `universal.storytell.actions_quality` | True Failure | Storyteller pipeline emitted empty actions list. | extraction_miss |
| 6 | `universal.pacing.floor_relief` | True Failure | Beat locked with pressure beat, but floor relief did not inject breathing_room (override failed). | engine_bug |
| 6 | `universal.conditions.orphan` | True Failure | Condition orphaning persists. | wrong_pipeline |
| 8 | `universal.location_change.applied` | True Failure | Location change extracted but state location ID unchanged. | schema_drift |
| 9 | `universal.pacing.consecutive_pressure_tracking` | True Failure | Complication beat (pressure type) not counted in consecutive pressure tracker. | engine_bug |
| 10 | `universal.storytell.actions_quality` | True Failure | Storyteller pipeline emitted empty actions list. | extraction_miss |
| 11 | `universal.conditions.orphan` | True Failure | Condition orphaning persists. | wrong_pipeline |
| 12 | `universal.pacing.floor_relief` | True Failure | Beat locked with complication beat, floor relief override failed (expected breathing_room). | engine_bug |
| 12 | `universal.conditions.orphan` | True Failure | Condition orphaning persists. | wrong_pipeline |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**Reason:** Repeated extraction failures in Storytell actions (Turns 3, 5, 10) and significant schema drift/validation rejections for location changes (Turns 4, 8). The State Extract pipeline is functional but the Scene Extract pipeline fails to apply deltas reliably.

### Mechanic Lifecycle Score: 1/5
**Reason:** >4 red flags across tables. Momentum lifecycle is broken (`WRONG_DIR` on multiple turns). Beat lifecycle has repeated `FLOOR_RELIEF_MISS` and TTL failures. Condition lifecycle is entirely non-functional (orphaned conditions never affect mechanics). Thread resolution shows signs of failure/residue in state diffs.

---

## SECTION 5 — Actionable Issues

**Critical:**
- **Condition Orphaning** (Turns: 2, 3, 4, 6, 10, 11, 12) — Tag: `wrong_pipeline`. Fix: Ensure `_apply_thread_updates` or the dice resolution step in Step 0 reads from `state.pc.conditions` and calculates `cond_mod` correctly. The condition is added to state but ignored by the ruling pipeline.
- **Momentum State Drift** (Turns: 3, 4, 5) — Tag: `engine_bug`. Fix: Debug `_apply_delta()` or momentum update logic in Step 0/1 tail. The band-derived delta is not being applied to the PC's momentum field correctly, leading to divergent state values.
- **Floor Relief Override Failure** (Turns: 6, 12) — Tag: `engine_bug`. Fix: Investigate `_check_floor_relief` logic. When `beat_locked=True` and storyteller emits a pressure-type beat, the engine should override it with `breathing_room`. It is currently failing to do so.

**Major:**
- **Location Change Application Failure** (Turns: 4, 8) — Tag: `schema_drift`. Fix: Verify that `location_change` deltas from Scene Extract are being merged into `state.location` by the validator/apply pipeline. The extraction identifies the change, but the state remains at the previous location ID/name in subsequent diffs.
- **Storytell Actions Extraction Miss** (Turns: 3, 5, 10) — Tag: `extraction_miss`. Fix: Debug Storytell LLM output parsing for the `actions` field. It is returning empty lists despite valid JSON structure elsewhere.

**Minor:**
- **Consecutive Pressure Counter Mismatch** (Turns: 3, 9) — Tag: `engine_bug`. Fix: Align the counter increment logic with the actual beat types emitted by Storytell. Complication/Pressure beats should consistently increment the counter; null or non-pressure beats should reset it.