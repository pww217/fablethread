# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-17T20:43:01.493174+00:00 · **Finished:** 2026-05-17T20:50:43.274247+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260517T204301Z_yzsa0gi4`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**Compaction:** —/5  
**State Fidelity:** 52.9%  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  

## ⚠️  Flagged

### `rejected_deltas` — 3 rejected delta(s) across the run

- turn 7: 2 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 2 turn(s) errored
- turn 7: engine_errors: [{"trace_id": "579fe0c0", "message": "Delta validation failed (2 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "8bb431aa", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | setback | -1 | 0 → -1 | — |
| 6 | success | +1 | -1 → 0 | — |
| 9 | fail | -1 | 0 → -1 | — |
| 11 | fail | -1 | -1 → -2 | — |
| 12 | setback | -1 | -2 → -3 | — |

**Assessment:** Momentum responds correctly to dice rolls across the run. All deltas match `momentum_delta` in Rules output and band definitions.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| T5 | complication | replace | Stored, expires T7 | Yes | — |
| T6 | breathing_room | replace | Stored, expires T8 | Yes | — |
| T9 | pressure | replace | Stored, expires T11 | Yes | — |
| T10 | complication | replace | Stored, expires T12 | Yes | — |

**Assessment:** Beats are generated and stored correctly. TTLs (turn_no + 2) are respected in the state snapshots provided. No orphaned beats detected in the visible trace.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|
| thug_extortion | T5 | immediate | No | T6 (remove) | 1 turn | — |
| thugs_closing_in | T9/10* | immediate | No | T12 (remove) | 3 turns | LATE_REMOVAL |

*\*Note: `thugs_closing_in` appears in Pressure Add at T9 and T10. The ID is consistent.*

**Assessment:** `thug_extortion` was removed correctly when the bribe succeeded. `thugs_closing_in` persisted until T12, which aligns with the player fleeing the scene (narrative resolution). No inert or overlong flags triggered for critical threats.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| bruised_ribs | T8 (Seed) | narrative | N/A | >5 turns | OVERLONG |
| low_morale | T10 (Seed) | narrative | T13 | 3 turns | — |

**Assessment:** `bruised_ribs` is present in the seed state and persists through Turn 13 without removal. This exceeds the 5-turn threshold for "active" conditions if not resolved, but since it's a persistent background condition from the seed, it may be intentional. However, strictly following the flag definition (active >5 turns), it triggers `OVERLONG`.

### 1E — Arc Thread Lifecycle Table

| Thread ID | Created (Tn) | State | Progress | Completed (Tm) | Flag |
|-----------|--------------|-------|----------|----------------|------|
| settle_the_debt | Seed | complete | 3 | T6 | — |
| deliver_the_ledger | Seed | complete | 3 | T12* | CAP_EXCEEDED / STALLED |

*\*Note: `deliver_the_ledger` shows as "complete" in the Turn 7 diff, but then reappears as "active" with progress 0 in subsequent diffs (Turns 8-13). This indicates a state corruption or duplicate thread issue.*

**Assessment:**
1. **CAP_EXCEEDED**: At T4, `deliver_the_ledger` and `clear_the_road_toughs` are added to active threads while `settle_the_debt` is still active (progress 2). The engine should have capped at 3, but here we see a transition where `settle_the_debt` was removed from active only after `deliver_the_ledger` became complete.
2. **STALLED**: `halden_might_have_more_lucrative` and `the_dark_labyrinthine_layout_of` remain in active threads with progress 0 for many turns (T4-T13), violating the spirit of thread advancement, though they are "active".

### 1G — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 3 | Add | credits | 200 | No | — |
| 4 | Add | credits | 1 | No | AMOUNT_MISMATCH (Narration implies advance, but delta is +1) |
| 6 | Remove | credits | 200 | No | — |
| 7 | Remove | merchant_seal / ledger | N/A | Yes | extraction_miss (Items not in inventory) |
| 9 | Remove | credits | 1 | No | — |
| 13 | Remove | credits | 1 | Yes | extraction_miss (Credits already at 0/low?) |

**Assessment:**
- **Turn 4**: Extracted +1 credit. Narrative says "advance". Seed had 500, T2 removed 500 (0 left), T3 added 200 (200 left). If advance was part of the 200, this is a double count or error. The delta shows `amount: 1`. This seems like an extraction miss for the full amount or a minor mismatch.
- **Turn 7**: Rejected deltas for `merchant_seal` and `ledger`. These items were never added to inventory in previous turns (Seed had `brass_key`, not ledger/seal). Extraction failed because it hallucinated items that didn't exist in state.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Turns 3-4**: Inventory coherence issue. T3 adds 200 credits. T4 adds 1 credit (advance?). Narrative implies receiving an advance *for* the job, likely part of or in addition to the 200. The delta `+1` is suspiciously small for a "deposit" on a 200-credit contract, suggesting extraction missed the bulk amount or misinterpreted "advance".
- **Turns 7**: Narrative says "slide the merchant seal across... hand him the ledger". State has neither item. Extraction attempted to remove non-existent items. This is a major coherence break between narrative intent and state reality.

### 2B — Extraction Drift
1. **Turn 4 (State Extract)**: `credits` +1 extracted. Likely should have been +0 (if part of T3) or the full advance amount if separate. Flag: `extraction_miss`.
2. **Turn 7 (State Extract)**: Attempted to remove `merchant_seal` and `ledger`. These items were never in inventory. The narrator introduced them, but they weren't tracked. Flag: `schema_drift` / `extraction_miss` (pipeline emitted deltas for non-existent keys).
3. **Turn 13 (State Extract)**: Attempted to remove 1 credit. State had 0 credits (Seed 500 - T2(500) + T3(200) - T4(1?) - T6(200) = ~-1? No, T4 was likely an error). Let's trace:
   - Start: 500
   - T2: Remove 500 → 0
   - T3: Add 200 → 200
   - T4: Add 1 → 201 (Assuming delta applied)
   - T6: Remove 200 → 1
   - T9: Remove 1 → 0
   - T13: Attempt to remove 1. Rejected because item doesn't exist (amount is 0). Flag: `validation_rejection`.

### 2C — State Fidelity Rate Calculation
Total Turns: 13 (Turns 1-13, excluding empty turns which are likely artifacts or skipped, but metrics show 17 entries including duplicates. Let's count unique player inputs/turns: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13 = 13 turns).

Turns with NO rejected deltas AND NO Auto-Checker failures (that indicate state drift) AND NO detected drift:
- T1: Clean.
- T2: Clean.
- T3: Auto-checker failure `npc_mention` (noise?), `actions_quality` (extraction miss?). Drift? No major state corruption, but actions missing is a pipeline fail. Let's count as Fail due to extraction quality.
- T4: Location change applied incorrectly (`universal.location_change.applied`). State drift. **Fail**.
- T5: Clean (except npc mention noise).
- T6: Actions quality fail. **Fail**.
- T7: Rejected deltas (inventory removal of non-existent items). **Fail**.
- T8: Clean.
- T9: Pressure directive failure, actions quality fail. **Fail**.
- T10: Location change applied incorrectly (`universal.location_change.applied`). State drift. **Fail**.
- T11: Clean (npc mention noise).
- T12: Location change applied incorrectly, npc mention, actions quality. **Fail**.
- T13: Rejected deltas (inventory removal). **Fail**.

Clean Turns: 1, 2, 5, 8, 11 = 5 turns.
Total Turns: 13.
Rate: 5/13 ≈ 0.384.

*Correction*: The prompt asks for `state_fidelity_rate` based on "no rejected deltas AND no Auto-Checker failures AND no detected drift".
Auto-checker failures like `npc_mention.extracted` are often noise if the NPC is in compendium, but here 'Crossed' (from Crossed Keys) might be a parser error. However, `location_change.applied` and `rejected deltas` are hard fails.

Let's re-evaluate "Clean":
- T1: No rejects, no critical checker failures. **Pass**.
- T2: No rejects, no critical checker failures. **Pass**.
- T3: Rejected? No. Checker? `actions_quality`. This is an extraction miss (0 actions). **Fail**.
- T4: Location change drift. **Fail**.
- T5: No rejects. Checker? `npc_mention` (likely noise if 'Crossed' isn't a named NPC, but it's in the location name). Let's assume minor noise. **Pass**? Or Fail due to potential context pollution? The checker says "narration mentions names not in npc_add/update or known". If 'Crossed' is part of 'Crossed Keys', this might be a false positive on the parser splitting words. But strictly, it's a failure flag. Let's count as **Fail** for safety, or **Pass** if we deem it noise. Given `universal.npc_mention` often flags partial matches, I will lean towards **Noise/Pass** unless it causes state drift. No state drift here.
- T6: Rejected? No. Checker? `actions_quality`. **Fail**.
- T7: Rejected deltas (inventory). **Fail**.
- T8: No rejects. Checker? None listed for T8 in the table provided? Wait, T9 has pressure directive failure. T8 is clean in checker list? Yes. **Pass**.
- T9: Pressure directive failure (narrate prompt issue), actions quality. **Fail**.
- T10: Location change drift. **Fail**.
- T11: No rejects. Checker? `npc_mention` ('Estrada', 'Matthew'). These are in compendium/present NPCs. This is likely a checker bug (false positive) if they were added/updated correctly. State looks consistent. **Pass** (Noise).
- T12: Location change drift, actions quality. **Fail**.
- T13: Rejected deltas (inventory). **Fail**.

Clean Turns: 1, 2, 5, 8, 11 = 5 turns.
Total: 13.
Rate: 5/13 ≈ 0.3846.

However, looking at the Metrics table, there are duplicate turn entries (e.g., Turn 3 appears twice). This suggests empty/no-op turns were logged. If we count those as "Turns", total is higher. But usually, fidelity is per *active* turn. I will stick to 13 active turns.

Let's look closer at T5/T9/T12 location changes.
T4: `location_change` emitted but state.location.id unchanged: merchant_road. (Drift)
T10: `location_change` emitted but state.location.id unchanged: river_docks. (Drift)
T12: `location_change` emitted but state.location.id unchanged: None. (Drift/No-op?)

The rate is low due to repeated location change application failures and inventory extraction errors on non-existent items.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 3,4,5,7,10,12,13 | `universal.npc_mention.extracted` | **Noise** (False Positive) | The checker likely splits "Crossed Keys" into "Crossed" and "Keys", or fails to match NPC names that are substrings of location names. 'Estrada'/'Matthew' in T11 were present NPCs, so this is a matching bug in the checker's known-NPC list comparison. | `engine_bug` (Checker logic) |
| 3,6,9,12 | `universal.progress.actions_quality` | **True Failure** | Progress Extractor failed to emit exactly 4 actions (emitted 0 or fewer). This is a consistent extraction failure in the LLM prompt/response for this pack. | `extraction_miss` |
| 4,10,12 | `universal.location_change.applied` | **True Failure** | Scene Extract emitted a location change, but the engine's apply logic did not update `state.location.id`. This suggests a validation failure or a bug in `_apply_delta()` ignoring empty/unchanged ID changes. | `engine_bug` (Apply logic) |
| 4,8,9 | `universal.narrate.pressure_directive_rendered` | **True Failure** | Scene pressures were active (immediate), but the narrator did not receive a Pressure/Overwhelm directive in its prompt context. This breaks the narrative-state alignment loop. | `wrong_pipeline` (Context building) |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2
**Reason:** Repeated extraction failures on inventory (Turns 7, 13 removing non-existent items; Turn 9/T13 rejecting valid removals due to state drift), consistent failure to generate actions (Turns 3,6,9,12), and location change application errors. The pipeline fails to accurately track item lifecycles when they are introduced narratively but not previously extracted/added.

### Mechanic Lifecycle Score: 3
**Reason:** Momentum and GM Beats function correctly. Scene Pressure lifecycle is mostly correct (though directive rendering failed). Arc threads show some stagnation (`halden_might_have_more_lucrative` stuck at progress 0 for many turns) but do not violate hard caps or expiry rules catastrophically. The main penalty comes from the location change mechanic failing to apply, which disrupts scene lifecycle tracking.

---

## SECTION 5 — Actionable Issues

**Critical**
- **<Description>** (Turns: 4, 10, 12) — Tag: `engine_bug`. Fix: Investigate `_apply_delta()` or Scene Extract validation to ensure that when a `location_change` is emitted with a new ID/name, it successfully overwrites the current location state. The checker indicates these are being ignored/dropped silently.

**Major**
- **<Description>** (Turns: 7, 13) — Tag: `extraction_miss`. Fix: Improve State Extract prompt to require existence checks or handle "new item" introductions via a specific `inventory_add` path before removal attempts. The extractor is trying to remove items that were never added because the narrator introduced them without a prior extraction step (or they were hallucinated).
- **<Description>** (Turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Debug Progress Extract LLM prompt/response for action generation. It consistently fails to output the required 4 actions in this pack context.

**Minor**
- **<Description>** (Turns: 4, 8, 9) — Tag: `wrong_pipeline`. Fix: Ensure `_compute_narration_directive()` outputs are correctly passed into the Narrator's prompt context when scene pressures exceed thresholds. The directive is computed but not rendered in the user prompt for narration.
- **<Description>** (Turns: All NPC mention failures) — Tag: `engine_bug` (Checker). Fix: Update Auto-Checker logic to handle substring matches or compound names (e.g., "Crossed Keys") correctly, reducing false positives on NPC mentions that are actually valid context.

## Auto-Checker

**240 passed, 25 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=1 |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 1 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 1 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=2 |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 2 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 2 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> town_square |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 3 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 3 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 4 | `universal.location_change.applied` | ✅ | (no change) |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 4 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 4 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 4 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `rules.rolled` | ❌ | rolled=False |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 5 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: merchant_road |
| 5 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 5 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 6 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 6 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 6 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 6 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 7 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 7 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 7 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `rules.rolled` | ❌ | rolled=False |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 8 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 8 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 8 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 2 removes |
| 9 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 9 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 9 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 9 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `rules.rolled` | ❌ | rolled=False |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 10 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 10 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 10 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 11 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `rules.rolled` | ✅ | rolled=False |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 12 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 12 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 12 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `rules.rolled` | ❌ | rolled=True |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 13 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: river_docks |
| 13 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 13 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 3 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `rules.rolled` | 🔴 | 7 | 12 | T2 |
| `universal.inventory.key_consumed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 2 | 13 | T5 |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.directive_rendered` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 3 | 13 | T5 |
| `universal.npc_mention.extracted` | 🔴 | 5 | 13 | T3 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.disposition_respected` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 3 | 13 | T4 |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Pressure Duration

| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `thug_extortion` | T5 | T5 | 1 |  |
| `thugs_breaching_door` | T11 | T11 | 1 |  |
| `thugs_closing_in` | T10 | T11 | 2 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_interior` | 2 |  |
| `marrows_crossing` | 2 |  |
| `merchant_road` | 6 | ⚠️ >4 turns |
| `river_docks` | 2 |  |
| `town_square` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T13 | 13 | ⚠️ >6 turns |
| `low_morale` | T1 | T12 | 12 | ⚠️ >6 turns |
| `winded` | T11 | T11 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1583 | 4023 | 2990 | 3588 | 4739 | 0 | 0 | 33.38 |
| 2 | I slide 500 credits across the table to Caron an… | 1583 | 4232 | 3308 | 3623 | 5084 | 0 | 0 | 28.68 |
| 3 | I find Halden by the town well and offer to carr… | 1594 | 4558 | 3330 | 3582 | 5102 | 0 | 0 | 38.83 |
| 3 |  | — | — | 0 | 0 | 0 | 0 | 0 | 28.03 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1527 | 4571 | 3215 | 3574 | 5085 | 0 | 0 | 34.04 |
| 5 | I walk up to the two toughs at the inn door and … | 1534 | 4907 | 3246 | 3628 | 5155 | 0 | 0 | 44.05 |
| 6 | I drop 200 credits on the ground between the tou… | 1615 | 4993 | 3338 | 3598 | 5244 | 0 | 0 | 33.42 |
| 6 |  | — | — | 0 | 0 | 0 | 0 | 0 | 28.74 |
| 7 | I sit across from Halden at his table, slide the… | 1589 | 4645 | 3300 | 3575 | 5108 | 0 | 0 | 43.74 |
| 8 | I pull out the brass key Halden gave me and try … | 1567 | 4936 | 3238 | 3560 | 5141 | 0 | 0 | 35.99 |
| 9 | I press my ear against the inn's stone wall and … | 1568 | 4974 | 3293 | 3638 | 5148 | 0 | 0 | 34.92 |
| 9 |  | — | — | 0 | 0 | 0 | 0 | 0 | 44.43 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1585 | 4866 | 3378 | 3611 | 5204 | 0 | 0 | 33.45 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1624 | 5303 | 3383 | 3607 | 5340 | 0 | 0 | 0.00 |
| 12 | I grab the ledger from my coat and sprint out th… | 1594 | 5409 | 3302 | 3600 | 5397 | 0 | 0 | 0.00 |
| 12 |  | — | — | 0 | 0 | 0 | 0 | 0 | 0.00 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1536 | 5053 | 3325 | 3672 | 5311 | 0 | 0 | 0.00 |
|  | TOTALS | 20499 | 62470 | 42646 | 46856 | 67058 | 0 | 0 | 461.71 |

**Total turns:** 17 · **Total duration:** 461.71s · **Avg/turn:** 27.16s
**Total tokens in:** 239,529 · **Total tokens out:** 12,324 · **Total LLM time:** 421.9s
**Total retries:** 0 · **Total parse failures:** 0

