state_fidelity_rate: 0.538 (7/13 turns clean)
extraction_accuracy_score: 2
mechanic_lifecycle_score: 4

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | fail | -1 | 0 → -1 | — |
| 8 | setback | 0 | -3 → -3 | FLAT |
| 9 | partial | 0 | -3 → -3 | FLAT |
| 11 | crit_success | +2 | -3 → -1 | WRONG_DIR |
| 12 | fail | -1 | -1 → -2 | — |

**Analysis:** Momentum is responding correctly to dice rolls across the run, with one anomaly at Turn 11. The engine applied a `+2` delta (crit_success) while momentum was already at the floor (`-3`). Per design, momentum should not exceed bounds; applying +2 from -3 would result in -1, which is valid *if* the floor check allows it. However, the table shows `-3 → -1`, implying a change of `+2`. If the engine enforced a hard floor where no positive delta applies at floor, this is a `WRONG_DIR` or logic error. Given the output explicitly states `momentum_delta: 2`, the engine *did* apply it. This suggests the momentum floor check might be permissive (allowing recovery) rather than strict (blocking change). I will flag as `—` for correctness if this is intended behavior, but note that Turn 8 and 9 show `-3 → -3` with `setback`/`partial`, implying a hard floor. The inconsistency between T8/T9 (blocked) and T11 (applied) suggests a bug in the momentum delta application logic or a threshold difference. *Correction*: Looking closely, T5 went to -1. T6 went to -2. T7 went to -3. T8 (setback) stayed at -3. T9 (partial) stayed at -3. T11 (crit_success +2) went to -1. This implies the floor is `-3` but *positive* deltas are allowed from there, while negative ones are blocked? Or perhaps `setback`/`partial` were treated as 0 change due to some other logic? Actually, standard RPG mechanics usually cap at min/max. If T8/T9 stayed flat despite negative bands, and T11 jumped up, it suggests the engine blocks *further* decline but allows recovery. This is a valid mechanic (floor prevents going lower, not higher). I will mark T11 as `—` (Clean) assuming this "recovery from floor" behavior is intended, though T8/T9 flatness confirms the floor exists.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | opportunity | npc_behavior | opportunity | storytell | Yes (exp T3) | — |
| T4 | pressure | npc_behavior | pressure | storytell | Yes (exp T6) | — |
| T5 | complication | npc_behavior | complication | storytell | Yes (exp T7) | — |
| T6 | pressure | event | pressure | storytell | Yes (exp T8) | — |
| T7 | breathing_room* | ambient | breathing_room | floor_relief | N/A (TTL 3) | FLOOR_RELIEF_MISS? |
| T8 | complication | event | complication | storytell | Yes (exp T10) | — |
| T9 | complication | npc_behavior | complication | storytell | Yes (exp T11) | — |
| T10 | complication | event | complication | storytell | Yes (exp T12) | — |
| T11 | breathing_room* | ambient | breathing_room | floor_relief? | N/A (TTL 3) | FLOOR_RELIEF_MISS? |
| T12 | opportunity | environmental | opportunity | storytell | Yes (exp T14) | — |

*\*Note on Floor Relief:* The trace shows `recent_beats` containing "breathing_room" entries for turns where the Storyteller explicitly emitted a beat type in other fields or null.
- **Turn 7:** Storytell emitted `escalation`. Beat locked was True (consecutive pressure reached). Floor relief *should* have injected `breathing_room`. The trace shows `pending_gm_beat` became `{type: breathing_room, surface_as: ambient}`. This is a correct floor relief injection.
- **Turn 11:** Storytell emitted no beat? No, T11 storytell output was not explicitly shown as null, but the state change shows `recent_beats` adding a breathing room entry while consecutive pressure dropped to 0. Wait, looking at Turn 11 State After: `consecutive_pressure_turns` went from 7 to 0. This reset implies a non-pressure beat or null was processed. The `recent_beats` list in T13 shows a breathing_room for T11. Did Storytell emit it? No, the "Storyteller" block for T11 is missing explicit gm_beat output in the prompt summary, but the state reflects a breathing room. If Storytell emitted null and beat_locked was True (it wasn't, pressure dropped), floor relief would fire. However, `consecutive_pressure_turns` reset to 0 *before* or *during* T11 processing? The table shows it went from 7 to 0. This suggests a non-pressure beat was recorded. If Storytell emitted null, and beat_locked was False (pressure dropped), no floor relief needed. But the trace says `recent_beats` has breathing_room for T11.
- **Turn 8:** Storytell emitted `complication`. Beat locked? Consecutive pressure went from 4 to 5. So it *was* locked at start of turn? No, lock is checked based on previous turns' count. At end of T7, count was 4 (locked). Start of T8, beat_locked=True. Storytell emitted `complication` (pressure type). Floor relief should override with breathing_room. The trace shows `pending_gm_beat` became `{type: complication}`. **Flag: FLOOR_RELIEF_MISS**. The engine failed to inject breathing_room when a pressure-type beat was emitted while locked.
- **Turn 9:** Storytell emitted `complication`. Beat locked? Count went from 5 to 6 (still locked). Floor relief should override. Trace shows `pending_gm_beat` became `{type: complication}`. **Flag: FLOOR_RELIEF_MISS**.
- **Turn 10:** Storytell emitted `complication`. Beat locked? Count went from 6 to 7 (still locked). Floor relief should override. Trace shows `pending_gm_beat` became `{type: complication}`. **Flag: FLOOR_RELIEF_MISS**.

*Correction on T7:* T7 Storytell emitted `escalation`. Consecutive pressure went from 3 to 4. Lock was active (count >= 3). Floor relief should have fired. The trace shows `pending_gm_beat` became `{type: breathing_room}`. This is a **CORRECT** floor relief injection.

*Correction on T11:* T11 Storytell output block is empty in the prompt summary provided? No, it's there. It doesn't show gm_beat explicitly in the JSON structure shown for T11 "Storyteller" section? Ah, looking at T11 Output: `gm_beat` field is missing from the JSON snippet?
```json
{
  "actions": [...],
  "outcome_summary": "...",
  "thread_resolve": [],
  "thread_update": [...],
  "world_state_add": [...]
}
```
It does *not* have a `gm_beat` key. This implies null/missing. Beat locked? Consecutive pressure was 7 (locked). Floor relief should inject breathing_room. Trace shows `recent_beats` has breathing_room for T11. **Correct**.

**Summary of Flags:**
- T8: FLOOR_RELIEF_MISS (Pressure emitted while locked, not overridden)
- T9: FLOOR_RELIEF_MISS (Complication emitted while locked, not overridden)
- T10: FLOOR_RELIEF_MISS (Complication emitted while locked, not overridden)

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| 1-13 | None (null/absent) | "Clear your debts..." | "Clear your debts..." | N/A | — |

**Analysis:** No goal updates were emitted or applied. The visible goal remained static throughout the run. This is correct if no narrative pivot occurred, but `goal_context` remains empty string in seed state and never populated.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | T2 Resolve | 2 | — |
| deliver_the_ledger | Seed | arc | normal | T3 Update | None | UNRESOLVED_AT_END |
| clear_the_road_toughs | Seed | arc | background→urgent | T4,6,7,8,9,10,11,12 Updates | None | UNRESOLVED_AT_END |

**Analysis:**
- `settle_the_debt`: Correctly resolved in T2. Moved to completed_threads.
- `deliver_the_ledger`: Still active at end of run (T13). Player fled with ledger? No, player *lost* the ledger (inventory_remove: ledger) but didn't deliver it. Thread remains open. This is a valid state for an incomplete game run.
- `clear_the_road_toughs`: Urgency correctly escalated to urgent in T4 upon confrontation. Progress log appended correctly every turn from T4-T13. No resolution (combat ongoing/escaped).

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| shaken | T8 | narrative | T9 | 2 turns | — |
| unsteady | T10 | narrative | T11 | 2 turns | — |
| wounded | T13 | narrative | None | Active (5 TTL) | — |

**Analysis:** Conditions added by State Extract (narrative source). `shaken` removed in T9. `unsteady` removed in T11. `wounded` active at end. No silent drops or overlong conditions detected.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 3 | Add | credits | 100 | No | — |
| 6 | Remove | credits | 5 | No | AMOUNT_MISMATCH* |
| 9 | Remove | credits | 1 | No | — |
| 11 | Add | credits | 10 | No | — |
| 12 | Remove | ledger | 1 | Yes | SPENDING_MISS** |
| 13 | Remove | credits | 2 | No | — |

*\*T6 Amount Mismatch:* Player input said "drop 200 credits". Extract State removed `5`. This is a significant extraction failure (LLM ignored the quantity or hallucinated a small bribe). The narrative says "failed... leaving him with only a small handful of coins", implying the bribe failed, but the *extraction* should reflect what was attempted or what was lost. If the bribe failed, 0 should be removed? Or if he dropped them and they were taken, 200? The narrative says "attempted to bribe... but failed". Usually this means no money changes hands, or it's snatched. Removing 5 is a hallucination/misinterpretation of the failure state.
*\*T12 Spending Miss:* Inventory remove for `ledger`. The ledger was never in inventory (it was Halden's item to deliver; Aren had a "brass key" and "credits"). The seed inventory did not contain a ledger. T3 extract added credits, not ledger. T12 removes it. **Extraction Failure**: Removing non-existent item.

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Inventory/Conditions:** Generally coherent. Conditions track TTL correctly. Inventory tracks credits accurately except for the T6 anomaly (5 vs 0 or 200) and T12 phantom removal.
- **Threads/NPCs:** Thread progress logs are consistent with narrative events. NPC presence updates in compendium match scene tags (e.g., toughs present during combat).

### 2B — Extraction Drift
1. **Turn 6 (State Extract):** `inventory_remove` for credits amount=5. Input: "drop 200 credits". Narrative: "bribe... failed". Expected extraction: Either 0 removed (failed bribe) or 200 removed (snatched). Removing 5 is a hallucination/misinterpretation. **Tag:** `extraction_miss`.
2. **Turn 12 (State Extract):** `inventory_remove` for item_id=`ledger`. The ledger was never in the PC's inventory. The PC had a "brass key" and "credits". The narrative says "grab the ledger from my coat", implying he *had* it, but state did not reflect this acquisition. Did T11 or earlier add it? No. T3 added credits. T11 added 10 credits. Ledger is missing from inventory entirely until T12 tries to remove it. **Tag:** `schema_drift` (state didn't track item) / `extraction_miss` (failed to add before removing).
3. **Turns 8, 9, 10 (Storytell):** Floor relief failure. Beat locked was True, pressure-type beats emitted by Storytell were *not* overridden by floor relief breathing_room injection. The engine allowed the pressure cycle to continue despite being locked.

### 2C — State Fidelity Rate Calculation
- Total Turns: 13
- Clean Turns (No rejected deltas AND No Auto-Checker failures AND No detected drift):
    - T1: Clean.
    - T2: Clean.
    - T3: Clean.
    - T4: **Fail** (Auto-checker: NPC mention 'Marrow' not in compendium). Also, floor relief logic issue? No, T4 beat was pressure, emitted by storytell, lock wasn't active yet (count went 0->1). So T4 is clean mechanically.
    - T5: Clean.
    - T6: **Fail** (Extraction drift: Amount mismatch on credits removal).
    - T7: Clean (Floor relief worked correctly here).
    - T8: **Fail** (Mechanic failure: Floor relief missed despite lock active and pressure beat emitted).
    - T9: **Fail** (Mechanic failure: Floor relief missed).
    - T10: **Fail** (Mechanic failure: Floor relief missed + Auto-checker condition orphan 'unsteady').
    - T11: Clean.
    - T12: **Fail** (Extraction drift: Removing non-existent ledger).
    - T13: Clean.

Clean Turns: 1, 2, 3, 4, 5, 7, 11, 13 = 8 turns?
Wait, T4 Auto-checker failure `universal.npc_mention.extracted` is a narration issue, not state extraction drift per se, but it's an auto-failure. The prompt says "No rejected deltas AND no Auto-Checker failures". So T4 is NOT clean.

Clean Turns: 1, 2, 3, 5, 7, 11, 13 = 7 turns.
Total: 13.
Rate: 7/13 ≈ 0.538.

## SECTION 3 — Auto-Checker Failure Analysis

1. **Turn 4 | `universal.npc_mention.extracted`**
   - **True failure or noise?** True failure (narration coherence). The narration mentioned "Marrow" (likely Marrow's Crossing) but the auto-checker flags it as a name not in compendium_npc_update or known. This is likely a false positive for location names, or a strict check on NPC *names*. If "Marrow" refers to the town, it shouldn't be flagged as an NPC mention error unless the checker conflates locations with NPCs. Given `compendium.npcs` doesn't have "Marrow", this is a **checker noise** (false positive) if "Marrow" was used as part of the location name or generic noun, not a specific NPC introduction.
   - **Remediation:** `scope_violation`. Fix checker to ignore location names in NPC mention checks.

2. **Turn 9 | `universal.npc_mention.extracted`**
   - **True failure or noise?** True failure (narration coherence). Narration mentioned "Above" (likely referring to a person upstairs?). If no NPC named "Above" exists, this is an extraction/narration drift where the LLM invented a character reference not tracked in state.
   - **Root cause:** Storytell/Narrate pipeline generated prose referencing an entity ("Above") that wasn't added to compendium or scene context.
   - **Remediation:** `extraction_miss`. Improve narrator grounding or extractor to catch implicit NPC references.

3. **Turn 10 | `universal.conditions.orphan`**
   - **True failure or noise?** True failure (state integrity). Condition `unsteady` was added in T9 but had no corresponding entry in the condition modifier lookup table (`CONDITION_MODS`). This means it provides no mechanical benefit/detriment, breaking game balance consistency.
   - **Root cause:** State Extract generated a new condition ID/label that wasn't pre-defined or registered with mechanics.
   - **Remediation:** `schema_drift`. Ensure all extracted conditions map to known mechanic definitions or register them dynamically.

4. **Turn 12 | `universal.inventory.remove_existence`**
   - **True failure or noise?** True failure (state corruption). The engine attempted to remove an item (`ledger`) that was not in the inventory. While validation *passed* (no rejection listed), this indicates a logic error where the extractor assumed possession without prior acquisition tracking.
   - **Root cause:** State Extract failed to add `ledger` when the narrative implied picking it up or having it, then tried to remove it later. Or, the ledger was never tracked at all.
   - **Remediation:** `extraction_miss`. Fix state extraction to track item acquisition before removal.

## SECTION 4 — Scores

### Extraction Accuracy Score: 2
**Reasoning:** Major extraction failures detected. T6 (amount mismatch) and T12 (phantom remove) are significant errors in the State Extract pipeline. The LLM is failing to accurately parse quantities and existence of items from narrative text. While no deltas were *rejected* by validation, the resulting state drifts significantly from narrated events.

### Mechanic Lifecycle Score: 4
**Reasoning:** Momentum tracking is mostly correct (with one ambiguous floor behavior). Thread lifecycle is robust (progress appending works well). Condition lifecycle is clean. The primary issue is the **Floor Relief mechanism failure** in Turns 8, 9, and 10. Despite `beat_locked=True`, pressure-type beats emitted by Storytell were not overridden by breathing_room injections as designed. This allowed a pressure loop to persist for 3 turns despite the lock being active. However, since floor relief *did* work correctly on T7 (where storytell was null/escalation?) and T11 (null), the mechanism is partially functional but failed specifically when Storytell emitted its own pressure beats while locked. This is a significant mechanic bug, but not total failure of all systems.

## SECTION 5 — Actionable Issues

**Critical**
- **Floor Relief Override Failure** (turns: [8, 9, 10]) — Tag: `engine_bug`. Fix: The floor relief injection logic must check if the *current* pending beat is pressure-type AND beat_locked is True, and override it with breathing_room regardless of whether Storytell emitted a new one or kept an old one. Currently, it seems to only inject on null/missing beats while locked, not overriding active pressure beats from Storytell.

**Major**
- **Phantom Inventory Removal (Ledger)** (turns: [12]) — Tag: `extraction_miss`. Fix: State Extract must validate that an item exists in inventory before generating a remove delta for it. If the narrative implies possession, add it first or flag as error.
- **Condition Orphan (unsteady)** (turns: [10]) — Tag: `schema_drift`. Fix: The engine needs a registry of valid condition IDs/modifiers. New conditions extracted must either map to existing mechanics or register new ones dynamically with default values.

**Minor**
- **NPC Mention False Positives (Marrow/Above)** (turns: [4, 9]) — Tag: `scope_violation`. Fix: Auto-checker should distinguish between location names/generic nouns and specific NPC identifiers in the compendium check.