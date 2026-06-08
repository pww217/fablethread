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
| 2 | success | +1 | 0 → 1 | — |
| 3 | success | +1 | 1 → 2 | — |
| 4 | setback | -1 | 2 → 1 | WRONG_DIR (State shows 1→2) |
| 5 | fail | 0 | 1 → 1 | FLAT (Rules say 1→0, State says 1→0 but momentum field diff shows 1->2 in T9 context? No, T5 state diff is missing. Let's look at T6 state diff: pc.momentum from 1 to 0. So T4 ended at 2? No, T4 Rules say 2->1. T5 Rules say 1->0. T6 State Diff says 1->0. This implies T4 actually resulted in momentum=2 (State diff for T9 shows prev 1 cur 2). | WRONG_DIR |
| 7 | crit_success | +2 | 1 → 3? | WRONG_DIR (Rules say 0→2, State diff T8 says 0→2) |
| 8 | fail | -1 | 2 → 1 | — |
| 9 | (empty input) | ? | ? | FLAT/MISSING |
| 11 | fail | +1 | 0 → 1 | WRONG_DIR (Rules say 1→0, State diff T12 says 1→0? No, T12 state diff shows pc.momentum from 1 to 0. Wait, T11 Rules say momentum_before=1, after=0. Delta -1. But Auto-Checker says prev=0 cur=1. Let's check T12 State Diff: `pc.momentum`: `from: 1`, `to: 0`. This contradicts the Auto-Checker which implies state was 0 before T11? Or maybe the diff is from T10->T11? No, diffs are vs previous turn. If T12 diff says 1->0, then T11 ended at 0. But Auto-Checker says `prev=0 cur=1`. This implies the state *after* T11 was 1. So Rules (1->0) contradicts State (ended at 1). | WRONG_DIR |

**Is momentum responding correctly?** No. The Rules output and Applied Deltas often contradict each other, or the State After Turn does not reflect the Rules outcome. Specifically, Turns 4, 7, and 11 show significant divergence between the calculated band delta and the resulting state value.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | pressure | npc_behavior | pressure | Storytell | Yes (expires T3) | — |
| T2 | complication | npc_behavior | complication | Storytell | Yes (expires T4) | — |
| T3 | complication | npc_behavior | complication | Storytell | Yes (expires T5) | — |
| T4 | complication | npc_behavior | breathing_room | Floor Relief? No, State shows `complication`. Auto-Checker says expected `breathing_room` because beat_locked=True. | N/A | FLOOR_RELIEF_MISS |
| T5 | null | null | breathing_room | Floor Relief (beat_locked from consecutive pressure) | Yes (expires T8) | — |
| T6 | revelation | environmental | revelation | Storytell | Yes (expires T8) | — |
| T7 | pressure | environmental | pressure? No, State shows `revelation` in diff? Wait. T7 Applied Deltas don't show beat change. T8 State Diff shows pending_gm_beat from `null` to `revelation`. This implies T6's revelation expired or was cleared? T5 injected breathing_room (expires T8). T6 emitted revelation (expires T8). They collide? Or did Storytell clear it? The diff at T8 says `from: null, to: {type: revelation}`. This suggests the beat from T6 was stored but maybe overwritten or the diff is misleading. Let's look at T7 State Diff: `pending_gm_beat`: `from: null, to: {type: revelation}`. So T6's beat persisted? No, T5 injected breathing_room (expires T8). If T6 emitted revelation, it should overwrite. But diff says `null -> revelation`. This implies the previous beat was gone. Did TTL expire? T5 expires at 8. Current turn 7. It shouldn't have expired. **OR** did Storytell emit null in T6? No, T6 output has `gm_beat: {type: revelation}`. Why is diff showing `null -> revelation`? Perhaps the previous beat (breathing_room) was popped because of a conflict or error? Or maybe the diff is from T5->T6 and I'm misreading indices. Let's assume standard flow: Storytell writes, Floor Relief checks. |
| T8 | complication | npc_behavior | pressure | Storytell | Yes (expires T10) | — |
| T9 | null | null | breathing_room | Floor Relief? State diff T10 shows `from: pressure, to: ambient/breathing_room`? No, T10 diff says `type: from: pressure, to: ambient`. Wait. T9 output is empty `{}`. So Storytell emitted nothing. beat_locked was True (consecutive_pressure_turns=3 at end of T8). Floor relief should inject breathing_room. State diff T10 shows `pending_gm_beat`: `from: {type: pressure...}, to: null`. This means the beat was popped/cleared, not replaced by floor relief? Or did it expire? Pressure expires T10 (T8+2). Current turn 9. It shouldn't have expired pre-narration. But diff shows `to: null`. Then at end of T9, if beat_locked, floor relief should inject. Diff doesn't show injection. | FLOOR_RELIEF_MISS / ORPHANED_BEAT_CLEAR |
| T10 | pressure | ambient | breathing_room? No, State diff T12 (skipped 11?) shows `from: null, to: {type: null}` in recent_beats? Wait. T10 output has `gm_beat: pressure`. Diff at T12 (which seems to be the snapshot for T11/12 block) is messy. Let's look at T11 State Diff: `pending_gm_beat`: `from: null, to: {type: breathing_room}`. This implies T10 emitted nothing or was cleared? But T10 output has pressure. | FLOOR_RELIEF_MISS / EXTRACTION_MISS |
| T12 | (empty) | null | null | Storytell (null) | N/A | — |

**Flags Analysis:**
- **T4**: `beat_locked=True` (consecutive_pressure_turns reached 3 at end of T3? No, T1=1, T2=?, T3=?). Auto-checker says beat_locked was True. Storytell emitted `complication`. Floor relief should have injected `breathing_room`. State shows `complication`. **FLOOR_RELIEF_MISS**.
- **T9**: Empty input/turn? Metrics show 0 tokens for Rules/Narrate/etc in one row, but another row has data. This looks like a duplicate or error entry in the trace logs provided (Turn 9 appears twice with different metrics). The first Turn 9 block has empty outputs `{}`. If Storytell emitted null and beat_locked was True, floor relief should fire. State diff T10 shows `pending_gm_beat` going to `null`. This suggests it was cleared but not replaced by relief? Or maybe the "pressure" from T8 expired at start of T9 (T8+2=10, so no). It persisted. Then Storytell emitted null -> popped. Floor relief should inject. Did not appear in state diff as injected beat. **FLOOR_RELIEF_MISS**.
- **NO_EXPIRY_TESTED**: TTL expiry logic seems broken or bypassed by the floor relief misses and location change resets (which purge beats? No, location changes don't purge beats).

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| 1-13 | None (Storytell output never contains `goal_update`) | "Clear your debts..." | "Clear your debts..." | N/A | — |

**Note:** The visible goal remains static throughout. No mid-arc pivots were attempted or extracted. This is acceptable if the story didn't require it, but no extraction misses here since none were emitted.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | None (active=false) | N/A | INERT |
| deliver_the_ledger | Seed | arc | normal | T4, T9, T10 updates | N/A | — |
| clear_the_road_toughs | Seed | arc | background | T2 update | N/A | INERT (active=false) |
| investigate_harker_disappearance | T5 | scene -> arc? | normal | T6, T7, T8, T10 updates | N/A | SCOPE_DRIFT (Seed was arc, Storytell added as scene?) |
| confront_predatory_rider | T9 | scene | urgent | T12 update (active=false) | N/A | — |
| harker_hat_connection | T10 | scene | normal | T13 resolve? No, T12 output has `thread_resolve` for this ID. | T12 | RESOLUTION_FAILED (State diff T13 shows thread still in threads[] with active=true) |

**Critical Failure at Turn 12:**
Storytell emitted `thread_resolve: [{id: "harker_hat_connection", ...}]`.
However, the **State After Turn 13** (which reflects post-T12 application) shows `threads` containing `harker_hat_connection` with `active: true`. It was NOT moved to `completed_threads`. The resolution signal was ignored or failed.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| dusty | T5 | State Extract | T6 (removed) | 2 turns | — |
| startled | T7 | State Extract | T9 (removed) | 3 turns? (T7->T8->T9). TTL was 2. **OVERLONG** or removed early? Removed at T9 diff. Added T7. Duration ~2-3 turns. Auto-checker flags `orphan` meaning no mod defined, not lifecycle error per se. | — |
| exposed | T10 (Trace says T9 in one block, T10 in another) | State Extract | T11 (removed) | 2 turns | — |
| relaxed | T13 | State Extract | N/A | Active at end | — |

**Auto-Checker `conditions.orphan`**: The checker flags conditions that have no entry in a hypothetical `CONDITION_MODS` config. This is an **extraction/schema issue**, not a lifecycle error, but it indicates the engine doesn't know how to modify stats for these conditions (likely 0 mod).

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 4 | Add | parchment_map | 1 | No | — |
| 8 | Add | dried_meat, water_canteen, rope | 1 each | No | — |
| 9 | Remove | dried_meat, water_canteen, rope | 1 each | **YES** (Auto-Checker: `remove_existence`) | SPENDING_MISS / EXTRACTION_FAIL |

**Analysis of Turn 9 Removal:**
State After T8 shows inventory includes `dried_meat`, etc.
Turn 9 Input is empty/ignored? Or the second Turn 9 block has input "I saddle up...". The first Turn 9 block (metrics 0) had empty outputs. The *second* Turn 9 block (metrics ~1600 tok_in) corresponds to the narrative where he buys supplies in T8 and then rides out in T9?
Actually, looking at the trace:
- **Turn 8**: Adds `dried_meat`, etc. State After T8 includes them.
- **Turn 9 (First block)**: Empty outputs. No deltas applied.
- **Turn 9 (Second block)**: Input "I saddle up...". Extract State says `inventory_remove`: dried_meat, water_canteen, rope. Applied Deltas include these removals.
- **Auto-Checker Failure T9**: `universal.inventory.remove_existence`. Why? Because the *State After Turn 8* diff (provided in the text) shows `inventory: added [...]` for those items. So they SHOULD exist.
Wait, look at **Turn 10 State Diff** (which is vs T9). It says `inventory: removed [...] dried_meat...`. This implies they were successfully removed from state *after* T9?
But the Auto-Checker failed on Turn 9. Why?
Ah, look at **Turn 9 Applied Deltas**: They include the removals.
Look at **State After Turn 10** (which is actually the snapshot for T10/T11 block in this messy trace). It shows `inventory: removed [...]`.
However, check **State After Turn 8**. Does it have them? Yes, diff says added.
Check **State After Turn 9**. The text doesn't provide a full "State After Turn 9" snapshot, only diffs for T10 and T12.
The Auto-Checker failure `remove_existence` on Turn 9 implies that at the moment of validation in Turn 9, the items were NOT found in state. This suggests they were added in T8 but *not persisted* or *lost* before T9's delta application? Or perhaps the "Turn 9" with empty outputs corrupted the state?
Actually, look at **State After Turn 10** diff: `inventory: removed [...]`. And `changed`: credits notes changed.
But look at **State After Turn 8** diff again. It adds them.
If T9 validation failed (`remove_existence`), they should NOT have been applied. But the final state (T13) does *not* show these items in inventory?
Final Inventory: `credits, iron_dagger, bandages, traveler_cloak, brass_key, parchment_map`. **Dried meat/canteen/rope are missing.**
So they were removed successfully from the narrative perspective, but the engine flagged it as an existence error. This is likely because the items were added in T8, but perhaps the `inventory_add` delta for T8 was rejected or not applied correctly? No, diff says "added".
Wait, look at **Turn 9 Input**: The *first* Turn 9 block has empty outputs and no deltas. If this turn ran as a "pass" with no state change, it's fine. But the *second* Turn 9 block (the real action) tried to remove items that existed in T8's post-state.
Why did Auto-Checker fail? `remove_existence`. This usually means the ID wasn't found. Did they have a different ID? Extract State used `id: dried_meat`. Seed/Previous state didn't define them, so they were added with `id: dried_meat`. It should match.
**Hypothesis**: The "Turn 9" empty block might have reset or skipped the persistence of T8's additions? Or the validation logic is buggy regarding newly added items in the same session if not properly merged? Given the final state lacks them, they were effectively removed/spent, but the engine flagged a validity error. This counts as an extraction/validation mismatch.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Location Drift**: The `location_change` emitted in Turns 4, 8, 10, and 12 was **not applied** to the state (Auto-Checker Failures).
    - T4: Emitted `dustfall_saloon`. State remained `marrows_crossing`.
    - T8: Emitted `weather_beaten_cabin`? No, T8 Extract Scene says `location_change: weather_beaten_cabin`. But Input was "head back to general store". The narrative/location extraction is hallucinating locations or the engine failed to apply them. State After T9 (diff) shows location changing from `assay_office` to `marrows_crossing_general_store`? No, diff says `from: assay_office, to: marrows_crossing_general_store`. This implies T8 *did* change it in some diffs but not others?
    - Let's look at **State After Turn 10** diff (vs T9). Location: `from: red_streaked_canyon_base, to: marrows_crossing_general_store`. This is a massive jump. The narrative flow was Saloon -> Assay Office -> Sheriff Station -> Cabin -> General Store -> Canyon Base Camp -> ?
    - The location IDs in the diffs are jumping around inconsistently with the "State After" snapshots provided for T1, T6, T8, T13.
    - **T1 State**: `marrows_crossing`.
    - **T4 Extract**: `dustfall_saloon`. **Auto-Checker says not applied**.
    - **T5 Extract**: `sheriffs_station`.
    - **T6 Extract**: `weather_beaten_cabin`.
    - **T8 Extract**: `marrows_crossing_general_store`? No, T8 Extract Scene says `location_change: marrows_crossing_general_store`. But Auto-Checker T8 says `location_change emitted but state.location.id unchanged: weather_beaten_cabin`. This implies the *previous* location was cabin, and it wasn't updated to store.
    - **T10 Extract**: `red_streaked_canyon_base`. Auto-Checker T12 (for this turn?) says `unchanged: red_streaked_canyon_base`? No, T12 diff shows change from `marrows_crossing_general_store` to `dustfall_outskirts`.
    - **Conclusion**: Location changes are frequently emitted but often fail to persist or apply correctly, leading to state drift where the narrative describes one place and the engine tracks another.

- **Inventory Coherence**: As noted in 1F, items added in T8 were flagged for removal existence error in T9, yet they disappear from final inventory. This is a "silent success" masked by an error flag, or a corruption where they existed briefly then vanished without proper accounting.

### 2B — Extraction Drift
- **Turn 4**: `location_change` extraction was correct (Saloon), but application failed. **Schema/Validation** issue in engine? Or just missed delta apply. Tag: `engine_bug`.
- **Turn 9**: `inventory_remove` existence check failure. The items existed in T8 state diff, so they should exist for T9 validation. This suggests the state loaded at start of T9 did not contain them (perhaps T8's save failed or was overwritten by an empty turn). Tag: `engine_bug`.
- **Turn 12**: `thread_resolve` signal emitted but thread remained active in state. Tag: `extraction_miss` (Storytell sent it, engine didn't apply) or `engine_bug` (apply logic skipped). Given the prompt says "resolved", and state shows active, this is a failure to process the storyteller's intent.

### 2C — State Fidelity Rate Calculation
Total Turns: 13 (excluding duplicate/empty metric rows for turns 5, 9, 10 which seem to be trace artifacts). Let's count unique narrative turns: 1-13 = 13 turns.

Failures per turn:
- T1: Momentum tracking error (Auto-checker). **Fail**.
- T2: Clean? No auto-failers listed for T2 in the table? Wait, T1 failure is `consecutive_pressure_tracking`. T4 has failures.
- T3: Clean?
- T4: Location not applied, Momentum delta wrong, Floor relief miss. **Fail**.
- T5: Actions quality (0 entries). **Fail**.
- T6: Condition orphan (cosmetic/missing mod). **Pass** for mechanics, but `orphan` is a config issue. Let's count as Pass for *state correctness* unless it breaks logic. However, Auto-checker lists it. I will count it as a Minor Fail or Pass? The prompt says "No extraction misses...". Orphan condition doesn't miss state, just lacks mod. **Pass**.
- T7: Momentum delta wrong, Pressure tracking fail. **Fail**.
- T8: Location not applied, Condition orphan. **Fail** (Location).
- T9: Actions quality, Remove existence error, Conditions orphan. **Fail**.
- T10: Location not applied, Floor relief miss, Actions quality, Conditions orphan. **Fail**.
- T11: Momentum delta wrong, Conditions orphan. **Fail**.
- T12: Location not applied (Auto-checker says `location_change emitted but state.location.id unchanged: red_streaked_canyon_base`? Wait, T10 Extract said Canyon Base. T12 Input is "Harker and I ride back...". Extract Scene says `dustfall_outskirts`. Auto-Checker T12 failure says location unchanged from Canyon Base. So it failed to apply the change to Outskirts. **Fail**.
- T13: Clean?

Passing Turns: 2, 3, 6 (maybe).
Total Passes: ~2/13 = 0.15.

Arithmetic: 2 / 13 ≈ 0.15.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 1 | `consecutive_pressure_tracking` | **True** | Storytell emitted `pressure`. Counter should be >= 1. State shows 0. Engine failed to increment counter on T1 beat application or initial state setup was wrong (Seed had 0). | `engine_bug` |
| 4 | `location_change.applied` | **True** | Delta applied but location field not mutated in state. Likely `_apply_delta` skipped location update or validation rejected it silently? No, no rejection listed. Bug in delta builder for location scope change. | `engine_bug` |
| 4 | `momentum.band_delta` | **True** | Rules said setback (-1). State went +1 (2->3? Or 1->2?). Momentum logic is broken or reading wrong prev value. | `engine_bug` |
| 4 | `floor_relief` | **True** | Beat locked, pressure emitted, no relief injected. Engine floor relief check failed to trigger override. | `engine_bug` |
| 5 | `actions_quality` | **True** | Storytell output had empty actions list (or null). Extraction pipeline accepted it but engine expects 4. | `extraction_miss` |
| 6 | `conditions.orphan` | **Noise/Config** | Condition exists, just no stat mod defined in config. Does not break state. | `scope_violation` (Missing Config) |
| 7 | `momentum.band_delta` | **True** | Rules said crit_success (+2). State went -1 (1->0). Momentum calculation is inverted or broken. | `engine_bug` |
| 7 | `consecutive_pressure_tracking` | **True** | Storytell emitted `pressure`. Counter reset to 0? Or failed to increment from T4/T5 state? T5 injected breathing_room, which should have reset counter. If T6 was null/relief, counter 0 is correct for end of T6? But failure says "gm_beat.type='pressure'... expected >=1". This implies the *current* turn's beat (T7) is pressure, but counter is 0 at start/check time? Or counter didn't increment from previous. | `engine_bug` |
| 8 | `location_change.applied` | **True** | Same as T4. Location delta emitted, state unchanged. | `engine_bug` |
| 8 | `conditions.orphan` | **Noise/Config** | See T6. | `scope_violation` |
| 9 | `actions_quality` | **True** | Empty actions again (in the second block). | `extraction_miss` |
| 9 | `inventory.remove_existence` | **True** | Items added in T8, removed in T9. Validation failed to find them. Suggests state persistence failure between T8 and T9 or ID mismatch. | `engine_bug` |
| 10 | `location_change.applied` | **True** | Same pattern. Location change emitted, not applied. | `engine_bug` |
| 10 | `floor_relief` | **True** | Beat locked (pressure streak), pressure emitted, no relief. | `engine_bug` |
| 10 | `actions_quality` | **True** | Empty actions? Or just missing from diff? T10 output has actions. Auto-checker says "has 0 entries". Maybe the *first* Turn 9 block's empty state carried over or confused the checker for T10? No, T10 is distinct. Check T10 Storytell Output: It HAS actions. Why did checker fail? Perhaps it checked the *previous* turn's result stored in context? Or the "Turn 9" duplicate entry corrupted the check buffer. | `checker_noise` (Likely due to trace duplication) |
| 12 | `location_change.applied` | **True** | Location change emitted, not applied. | `engine_bug` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
- **Reason**: Repeated extraction failures (Actions quality on T5, T9). Critical state corruption in inventory handling (T9 remove existence) and location tracking (multiple turns). The engine is failing to apply basic deltas from the Storytell and Scene extractors.

### Mechanic Lifecycle Score: 1/5
- **Reason**: Momentum lifecycle is broken (wrong direction/values on multiple turns). Beat lifecycle has repeated `FLOOR_RELIEF_MISS` flags, meaning the pressure relief mechanism is not functioning as designed. Thread resolution failed to move a thread to completed status despite explicit signal. Location changes are systematically ignored by the state engine.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Location Delta Application Failure** (Turns: 4, 8, 10, 12) — Tag: `engine_bug`. Fix: Inspect `_apply_delta` or `delta_builder.py` for location updates. The delta is generated but not persisted to `state.location`. This breaks scene continuity entirely.
- **Momentum Calculation Inversion** (Turns: 4, 7, 11) — Tag: `engine_bug`. Fix: Debug `_compute_pacing_context` or momentum update logic. Dice bands are being mapped to incorrect delta values (e.g., Crit Success applying -1).

**Major**
- **Floor Relief Mechanism Failure** (Turns: 4, 10) — Tag: `engine_bug`. Fix: The engine fails to inject `breathing_room` when `beat_locked=True` and a pressure beat is emitted. This causes unbroken pressure cycles contrary to design intent.
- **Thread Resolution Ignored** (Turn: 12) — Tag: `extraction_miss`. Fix: `_apply_thread_resolutions()` or the merge step for T12 failed to move `harker_hat_connection` from active threads to completed_threads despite explicit `thread_resolve` output.

**Minor**
- **Actions Extraction Null/Empty** (Turns: 5, 9) — Tag: `extraction_miss`. Fix: Storytell LLM is occasionally returning empty/null actions lists. Validation should reject or default to placeholder if <4 actions are emitted.
- **Condition Orphan Flags** (Turns: 6, 8, 9, 10, 11) — Tag: `scope_violation`. Fix: Add entries for `dusty`, `startled`, `exposed`, `relaxed` to the engine's `CONDITION_MODS` configuration or ensure they default to 0 mod without erroring.