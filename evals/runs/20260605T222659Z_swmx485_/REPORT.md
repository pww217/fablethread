# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-05T22:26:59.772473+00:00 · **Finished:** 2026-06-05T22:33:30.469012+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260605T222659Z_swmx485_`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260605T202442Z_havr6lvx/artifacts`

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**State Fidelity:** 0.0%  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  


## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | crit_success | +2 | 0 → 2 | — |
| 6 | success | +1 | 2 → 3 | WRONG_DIR (Design: success=+1, but table shows delta from Rules output as `momentum_delta`: 1. Wait, design says success=+1. Turn 5 was crit_success (+2). Turn 6 was success (+1). Momentum went 0->2->3. This is correct direction.) | — |
| 8 | crit_success | +2 (Design) / 0 (Actual) | 3 → 3 | FLAT (Rules output says `momentum_delta: 0` for a Crit Success band, which contradicts the momentum delta table in Engine Constants where crit_success=+2. The engine applied 0 change.) | WRONG_DIR (Logic Error) |
| 9 | success | +1 (Design) / 0 (Actual) | 3 → 3 | FLAT (Rules output says `momentum_delta: 0` for a Success band, contradicting design where success=+1. Momentum capped at max 3 anyway, so delta is clamped to 0.) | — |
| 10 | success | +1 (Design) / 0 (Actual) | 3 → 3 | FLAT (Same as T9, momentum at cap.) | — |

**Is momentum responding correctly?** No. Turns 8 and 9 show `momentum_delta: 0` in the Rules output for bands that should yield positive deltas (+2 and +1 respectively). While T9/T10 are capped at max(3), T8 (Momentum was 3, so delta clamped to 0) is technically correct application of cap, but the *reported* delta from the ruling engine is wrong if it claims a roll occurred. However, looking closely at Turn 5: Momentum went 0->2 (Correct). Turn 6: 2->3 (Correct). The issue is that for Turns 8-10, the Rules output explicitly lists `momentum_delta: 0` despite high rolls. This suggests the Python momentum clamping logic is working (capping at 3), but the *extraction* or *reporting* of the delta in the Rules JSON might be misleading if it doesn't reflect the cap. More critically, **Turn 8** shows a Crit Success (+2 design) resulting in `momentum_delta: 0`. Since momentum was already 3, this is correct application. However, **Turn 9** and **10** also show 0 delta for Success bands while at max momentum. This is consistent behavior (clamping). The flag `WRONG_DIR` on T8 is incorrect; it's just capped. I will mark them as `FLAT` due to cap or correct application.

*Correction*: In Turn 5, Momentum went from 0 to 2. In Turn 6, from 2 to 3. In Turn 8, from 3 to 3 (Delta 0). This is mechanically sound clamping. No `WRONG_DIR`.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T4 | complication | npc_behavior | complication (expires T6) | Storytell | Yes | — |
| T5 | null | null | null | Storytell (Null-Clear) | N/A | — |
| T6 | revelation | npc_behavior | revelation (expires T8) | Storytell | Yes | — |
| T7 | null | null | null | Storytell (Null-Clear) | N/A | — |
| T8 | revelation | player_discovery | revelation (expires T10) | Storytell | Yes | — |
| T9 | null | null | null | Storytell (Null-Clear) | N/A | — |
| T10 | revelation | npc_behavior | revelation (expires T12) | Storytell | Yes | — |
| T11 | null | null | null | Storytell (Null-Clear) | N/A | — |
| T12 | complication | npc_behavior | complication (expires T14) | Storytell | Yes | — |
| T13 | null | null | null | Storytell (Null-Clear) | N/A | — |

**Note:** Floor relief was never triggered (`beat_locked` never reached threshold or momentum floor). `NO_EXPIRY_TESTED` is false because beats were emitted and expired/cleared correctly. No orphaned beats detected in state snapshots.

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| 1-13 | None (null) | "Clear your debts..." | "Clear your debts..." | N/A | — |

**Note:** The goal never changed. No `goal_update` was emitted by Storytell in any turn. This is valid if the arc hasn't pivoted, but it means the `visible_goal` field is static throughout the trace.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | T1, T2 | T2 | — |
| deliver_the_ledger | Seed | arc | normal | T3, T7 | None | UNRESOLVED_AT_END |
| clear_the_road_toughs | Seed | arc | background | T4, T5, T6 | T6 | — |
| road_instability | T3 | arc | normal | None (only added) | None | INERT (No updates after add? Wait. T3 adds it. No thread_update for this ID in T4-T13.) | INERT |
| ledger_pursuit | T7 | arc | urgent | T8, T9, T10, T12, T13 | None | UNRESOLVED_AT_END |
| cellar_secret | T8 | scene | normal | T9 | T10 (Abandoned) | — |
| dockside_confrontation | T12 | scene | urgent | None (only added) | None | INERT |

**Flags Explanation:**
- `INERT`: `road_instability` and `dockside_confrontation` were added but never received a `thread_update` to change urgency/progress in subsequent turns. This is allowed by design ("Storyteller-managed"), but indicates low engagement from the Storytell pipeline for these specific threads.
- `UNRESOLVED_AT_END`: Active at end of trace.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| wounded | T13 | narrative (Storytell/State Extract?) | None | Active > 0 turns | — |

**Note:** The condition `wounded` was added in Turn 13 via the State Extract output (`pc_condition_add`). It has a TTL of 3 turns. No resolution yet.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 6 | Remove | credits | 200 | Yes (Auto-Checker) | AMOUNT_MISMATCH / EXISTENCE_FAIL |
| 7 | Remove | merchant_seal | 1 | Yes (Auto-Checker) | SPENDING_MISS (Item never existed in inventory) |
| 7 | Remove | ledger | 1 | Yes (Auto-Checker) | SPENDING_MISS (Item never existed in inventory) |
| 9 | Remove | credits | 1 | Yes (Auto-Checker) | AMOUNT_MISMATCH / EXISTENCE_FAIL |
| 13 | Remove | credits | 1 | Yes (Auto-Checker) | AMOUNT_MISMATCH / EXISTENCE_FAIL |

**Note:** The Auto-Checker flags `universal.inventory.remove_existence` on Turns 6, 7, 9, and 13. This indicates the State Extract pipeline is emitting removals for items that are either not in inventory or have insufficient quantity (specifically `credits`). In Turn 2, 500 credits were removed. Starting balance was 500. Balance became 0.
- T6: Remove 200 credits from 0? -> Fail.
- T9: Remove 1 credit from 0? -> Fail.
- T13: Remove 1 credit from 0? -> Fail.

The engine's `apply_delta` likely rejected these or failed to apply them, but the *extraction* is hallucinating inventory changes that contradict state history.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
**Critical Incoherence:** Inventory balance for `credits`.
- Start: 500.
- T2: Removed 500. Balance: 0.
- T6: Extracted remove 200. Auto-checker flagged existence failure. If applied, balance would be -200 (invalid) or rejected. State snapshot after T13 shows `credits` is **not present** in the inventory list at all? Let's check T13 State After Turn Inventory:
    ```json
    "inventory": [
      { ... "id": "iron_dagger" },
      { ... "id": "bandages" },
      { ... "id": "traveler_cloak" },
      { ... "id": "brass_key" },
      { ... "id": "parchment_cylinder" }
    ]
    ```
    The `credits` item is completely missing from the final inventory. This implies it was removed in T2 and never re-added, which is correct for a 0-balance removal if the engine deletes empty stacks. However, subsequent extraction attempts to remove more credits (T6, T9, T13) are **extraction failures**. The State Extract pipeline failed to recognize that `credits` were already exhausted/removed.

**NPC Presence Coherence:**
- T8: `cellar_dweller` added as present in cellar.
- T10: `cellar_dweller` marked `known`. Thread resolved (abandoned).
- T13: `cellar_dweller` is not mentioned in compendium updates, but thread is abandoned. This is coherent; the scene changed to docks, so cellar NPC recedes to background/known status or drops from active tracking if scope=scene and location changed? Wait, `cellar_secret` was scope=scene. Location changed T8 (Cellar) -> T12 (Docks). Scene-scoped threads should be purged on location change.
    - Design: "Scene-scope threads... Purged on location change".
    - T8 to T9: Cellar to Cellar? No, T8 is Cellar. T9 input is in cellar ("press ear against wall"). State After T9 shows Location ID `crossed_keys_cellar`. So thread persists.
    - T10: Input confronts Matthew (Taproom?). State After T10 shows Location Description "The taproom...". Did location ID change? The diff for T10 doesn't show a `location_change` in Applied Deltas, but the description changed from Cellar to Taproom. If the engine treats this as a new scene/location implicitly or if the ID didn't update, thread persistence is ambiguous. However, Thread Resolve fired on T10 explicitly (`cellar_secret` resolved/abandoned). So it was handled correctly via explicit resolution rather than auto-purge.

### 2B — Extraction Drift
**Primary Failure Source:** **State Extract (Step 2b)** and **Storytell (Step 2c) Inventory Logic**.

1.  **Turns 6, 9, 13: `credits` Removal Hallucination.**
    -   State after T2 had 0 credits (or removed the item).
    -   Storytell/State Extract continued to emit `inventory_remove` for `credits`.
    -   Auto-Checker confirmed these items did not exist or were invalid.
    -   **Root Cause:** Extraction pipeline failed to check current inventory state before emitting deltas, or hallucinated narrative justification for spending credits that weren't there.

2.  **Turn 7: Non-existent Items (`merchant_seal`, `ledger`).**
    -   State Extract emitted removals for `merchant_seal` and `ledger`.
    -   These items were never in the inventory (Seed had `brass_key`, `iron_dagger`, etc.). The narrative mentions "sliding the merchant seal" and "handing him the ledger", but the engine's inventory model did not track these as acquireable/owned items previously.
    -   **Root Cause:** State Extract failed to validate existence of removed items against current state before emitting delta.

3.  **Turns 2, 4: NPC Mention Extraction Noise.**
    -   Auto-Checker flagged `universal.npc_mention.extracted` for names like 'Slowly' (T2) and 'Marrow' (T4). These are likely false positives from the checker parsing narrative text or improper tokenization of proper nouns vs adverbs. 'Marrow' is part of the location name "Marrow's Crossing", which might be flagged if not mapped to `location_id`.

### 2C — State Fidelity Rate Calculation
-   Total Turns: 13
-   Clean Turns (No rejected deltas AND No Auto-Checker failures):
    -   T1: Clean.
    -   T2: Fail (`thread_update.valid_id` noise? `npc_mention` noise). Let's count as noisy but not state-breaking. However, strict adherence to "No Auto-Checker failures" excludes it.
    -   T3: Fail (`npc_mention`).
    -   T4: Fail (`npc_mention`).
    -   T5: Clean? No auto-checker failures listed for T5.
    -   T6: Fail (Inventory existence).
    -   T7: Fail (Inventory existence).
    -   T8: Clean? No auto-checker failures listed.
    -   T9: Fail (Inventory existence).
    -   T10: Clean? No auto-checker failures listed.
    -   T11: Clean? No auto-checker failures listed.
    -   T12: Fail (`npc_mention`).
    -   T13: Fail (Inventory existence).

-   Clean Turns: 1, 5, 8, 10, 11 = 5 turns.
-   Dirty Turns: 2, 3, 4, 6, 7, 9, 12, 13 = 8 turns.
-   Rate: 5 / 13 ≈ **0.38**.

*Correction on "Clean":* The prompt asks for `state_fidelity_rate`. If I use the strict definition (No rejected deltas AND No Auto-Checker failures), many turns fail due to minor noise (`npc_mention`). However, the inventory errors are critical state drifts.
Let's look at the specific instruction: "Count: turns where (no rejected deltas AND no Auto-Checker failures AND no detected drift) / total turns."

Turn 1: No AC fails. Clean.
Turn 2: AC Fail (`npc_mention`, `thread_update`). Drift? Thread update ID was valid in state, but checker flagged it? The thread `settle_the_debt` existed. This is likely a false positive or strict ID matching issue. But strictly, it's an AC failure.
Turn 3: AC Fail (`npc_mention`).
Turn 4: AC Fail (`npc_mention`).
Turn 5: No AC fails. Clean.
Turn 6: AC Fail (Inventory). State Drift confirmed.
Turn 7: AC Fail (Inventory). State Drift confirmed.
Turn 8: No AC fails. Clean.
Turn 9: AC Fail (Inventory). State Drift confirmed.
Turn 10: No AC fails. Clean.
Turn 11: No AC fails. Clean.
Turn 12: AC Fail (`npc_mention`).
Turn 13: AC Fail (Inventory). State Drift confirmed.

Clean Turns: 1, 5, 8, 10, 11 = 5/13.
Rate: **0.38**.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 2 | `universal.npc_mention.extracted` ('Slowly') | **Noise**. 'Slowly' is likely an adverb parsed as a name by the checker's regex/NLP. | Checker false positive on narrative prose parsing. | `checker_noise` |
| 2 | `universal.thread_update.valid_id` (`settle_the_debt`) | **True Failure (Logic)**. The thread ID exists in state, but the update might have been processed before existence check or checker has stale view? Actually, T1 added progress to it. T2 resolved it. If the checker runs on pre-apply state, it should exist. This is likely a race condition in the checker or a false positive if the thread was already moved to completed_threads by the time the update arrived (order of operations). | Pipeline ordering / Checker timing. | `scope_violation` |
| 3 | `universal.npc_mention.extracted` ('Marrow') | **Noise**. 'Marrow' is part of location name "Marrow's Crossing". Checker failed to distinguish Location vs NPC. | Checker schema mismatch (Location names not excluded from NPC check). | `checker_noise` |
| 4 | `universal.npc_mention.extracted` ('Marrow') | **Noise**. Same as T3. | Checker schema mismatch. | `checker_noise` |
| 6 | `universal.inventory.remove_existence` (`credits`) | **True Failure**. Credits were exhausted in T2 (500 removed). Extraction emitted another removal of 200. State would have gone negative or rejected. | **Extraction Miss**: State Extract failed to validate current inventory balance before emitting delta. | `extraction_miss` |
| 6 | `universal.thread_update.valid_id` (`clear_the_road_toughs`) | **True Failure (Logic)**. Similar to T2. Thread existed, but update might have conflicted with resolution or checker timing. | Pipeline ordering / Checker timing. | `scope_violation` |
| 7 | `universal.inventory.remove_existence` (`merchant_seal`, `ledger`) | **True Failure**. These items were never in inventory. Extraction hallucinated their existence to support narrative "handing over" actions. | **Extraction Miss**: State Extract failed to validate item existence against state before emitting delta. | `extraction_miss` |
| 9 | `universal.inventory.remove_existence` (`credits`) | **True Failure**. Credits still exhausted from T2. Extraction emitted removal of 1. | **Extraction Miss**: Same root cause as T6. | `extraction_miss` |
| 12 | `universal.npc_mention.extracted` ('Ahead') | **Noise**. 'Ahead' is likely an adverb/preposition parsed incorrectly by the checker. | Checker false positive on narrative prose parsing. | `checker_noise` |
| 13 | `universal.inventory.remove_existence` (`credits`) | **True Failure**. Credits still exhausted from T2. Extraction emitted removal of 1 (for dock boy). Narrative says "pay the dock boy", but inventory didn't support it. | **Extraction Miss**: Same root cause as T6/T9. | `extraction_miss` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 1
**Reason:** Repeated extraction failures on Inventory (Turns 6, 7, 9, 13). The State Extract pipeline consistently emits removal deltas for items that do not exist or have insufficient quantity. This is a critical failure in the delta generation logic, leading to state corruption attempts (negative inventory) or silent rejections that break narrative consistency (player pays but no deduction shown/valid). Major extraction failures cap at 2; these are systemic and repeated across multiple turns involving different items (`credits`, `ledger`).

### Mechanic Lifecycle Score: 2
**Reason:** 
- **Threads:** Two threads (`road_instability`, `dockside_confrontation`) became inert (no updates after creation). While not a crash, it indicates the Storytell pipeline is failing to maintain thread urgency/progress for new additions.
- **Beats:** Beat lifecycle was clean (Score 5 component), but Thread inertia drags down the overall mechanic health.
- **Conditions:** Condition `wounded` added correctly in T13 with TTL tracking, which is good.
- Overall, the inert threads and lack of thread engagement suggest a degradation in the Storytell pipeline's ability to manage long-term state beyond immediate resolutions.

---

## SECTION 5 — Actionable Issues

**Critical:**
- **<Description>** (turns: 6, 7, 9, 13) — Tag: `extraction_miss`. Fix: Update State Extract prompt and validation logic to strictly check `state.inventory` for existence and sufficient quantity before emitting `inventory_remove`. If an item is not in inventory or balance is insufficient, the extractor must emit null/empty delta rather than hallucinating a removal.

**Major:**
- **<Description>** (turns: 3, 4, 12) — Tag: `checker_noise`. Fix: Update Auto-Checker NPC extraction logic to exclude location names and common adverbs/prepositions from the "unknown name" check. 'Marrow' is a location root; 'Ahead', 'Slowly' are not NPCs.
- **<Description>** (turns: 2, 6) — Tag: `scope_violation`. Fix: Investigate why `thread_update.valid_id` fails for threads that clearly exist in the state snapshot provided to the checker. Ensure thread updates are processed/validated against the correct version of state (pre-apply vs post-apply).

**Minor:**
- **<Description>** (turns: 3, 7) — Tag: `extraction_miss`. Fix: Improve Storytell pipeline's awareness of inventory contents when generating narrative actions or thread progress that implies item usage. The narrator extracted "handing ledger" but the engine didn't have it tracked as an inventory item to remove.

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**316 passed, 21 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | ✅ | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 1 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 1 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, floor=-3) |
| 1 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 1 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 1 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 1 | `universal.inventory.remove_existence` | ✅ | (first turn) |
| 1 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 1 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 1 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 2 | `ruling.rolled` | ❌ | rolled=False |
| 2 | `storytell.extract.thread_update` | ✅ | thread_update[settle_the_debt] found |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Slowly'] |
| 2 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, floor=-3) |
| 2 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `universal.inventory.remove_existence` | ✅ | checked 1 removes |
| 2 | `universal.thread_update.valid_id` | ❌ | thread_update references unknown thread ID(s): ['settle_the_debt'] |
| 2 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 2 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 3 | `ruling.rolled` | ❌ | rolled=False |
| 3 | `storytell.extract.thread_update` | ✅ | thread_update[deliver_the_ledger] found |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_well |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Marrow'] |
| 3 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 3 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, floor=-3) |
| 3 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 3 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 3 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 4 | `ruling.rolled` | ✅ | rolled=False |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=complication |
| 4 | `universal.location_change.applied` | ✅ | (no change) |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Marrow'] |
| 4 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'transition' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 4 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='complication', counter=1 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, floor=-3) |
| 4 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 4 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 4 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 4 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 5 | `ruling.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `storytell.extract.thread_update` | ✅ | thread_update[clear_the_road_toughs] found |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 5 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=2 (expected +2, engine may clamp) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=2, floor=-3) |
| 5 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 5 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 5 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 5 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 5 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 5 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 5 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 6 | `ruling.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=200 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=revelation |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=1 (expected +2, engine may clamp) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 6 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Pressure' rendered in storytell prompt |
| 6 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='revelation', counter=0 |
| 6 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 6 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `universal.inventory.remove_existence` | ❌ | removed non-existent item(s): ['credits'] |
| 6 | `universal.thread_update.valid_id` | ❌ | thread_update references unknown thread ID(s): ['clear_the_road_toughs'] |
| 6 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 6 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 6 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 7 | `storytell.extract.thread_resolve` | ❌ | thread_resolve[deliver_the_ledger] not found (resolved: []) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 2 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 7 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Pressure' rendered in storytell prompt |
| 7 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 7 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 7 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 7 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.inventory.remove_existence` | ❌ | removed non-existent item(s): ['merchant_seal', 'ledger'] |
| 7 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 7 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 7 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 8 | `ruling.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=revelation |
| 8 | `universal.location_change.applied` | ✅ | marrows_crossing_well -> crossed_keys_cellar |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=0 (expected +2, engine may clamp) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'transition' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Imperative' rendered in storytell prompt |
| 8 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='revelation', counter=0 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 8 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 8 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 8 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 9 | `ruling.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | band=success delta=0 (expected +1, engine may clamp) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 9 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 9 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 9 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 9 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `universal.inventory.remove_existence` | ❌ | removed non-existent item(s): ['credits'] |
| 9 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 9 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 9 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 10 | `ruling.rolled` | ✅ | rolled=True |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=revelation |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | band=success delta=0 (expected +1, engine may clamp) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 10 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 10 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='revelation', counter=0 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 10 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 10 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 10 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 10 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 10 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 10 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 11 | `ruling.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `extract.state.pc_condition_add` | ❌ | pc_condition_add[winded] not found |
| 11 | `extract.state.inventory_add` | ❌ | inventory_add[wax_sealed_cylinder] not found |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=0 (expected +2, engine may clamp) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 11 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Pressure' rendered in storytell prompt |
| 11 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 11 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 11 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 11 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 11 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 11 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 11 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 11 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 11 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 12 | `ruling.rolled` | ❌ | rolled=True |
| 12 | `extract.state.pc_condition_remove` | ❌ | pc_condition_remove[winded] not found |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=complication |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_cellar -> river_docks |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Ahead'] |
| 12 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=0 (expected +2, engine may clamp) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'transition' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Imperative' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='complication', counter=1 |
| 12 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 12 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 12 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 12 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 12 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 13 | `ruling.rolled` | ✅ | rolled=False |
| 13 | `extract.state.pc_condition_remove` | ❌ | pc_condition_remove[bruised_ribs] not found |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 13 | `universal.storytell.directive_rendered` | ✅ | directive 'Pressure' rendered in storytell prompt |
| 13 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=3, floor=-3) |
| 13 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 13 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `universal.inventory.remove_existence` | ❌ | removed non-existent item(s): ['credits'] |
| 13 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 13 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 13 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 13 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 13 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_add` | 🔴 | 1 | 1 | T11 |
| `extract.state.inventory_remove` | 🔴 | 1 | 2 | T8 |
| `extract.state.pc_condition_add` | 🔴 | 1 | 1 | T11 |
| `extract.state.pc_condition_remove` | 🔴 | 2 | 2 | T12 |
| `ruling.rolled` | 🔴 | 3 | 12 | T2 |
| `storytell.extract.thread_resolve` | 🔴 | 1 | 1 | T7 |
| `storytell.extract.thread_update` | 🔴 | 0 | 3 | — |
| `universal.beat_type.surface_as_consistency` | 🟡 | 0 | 13 | — |
| `universal.beat_type.variety` | 🟡 | 0 | 13 | — |
| `universal.conditions.orphan` | 🔴 | 0 | 13 | — |
| `universal.directives.no_removed` | 🟡 | 0 | 13 | — |
| `universal.goal_update.applied` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.inventory.remove_existence` | 🔴 | 4 | 13 | T6 |
| `universal.location_change.applied` | 🔴 | 0 | 13 | — |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | 🔴 | 0 | 13 | — |
| `universal.npc_mention.extracted` | 🔴 | 4 | 13 | T2 |
| `universal.npc_states.no_removed` | 🟡 | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | 🟡 | 0 | 13 | — |
| `universal.pacing.consecutive_pressure_tracking` | 🟡 | 0 | 13 | — |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pacing.floor_relief` | 🟡 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | 🔴 | 0 | 13 | — |
| `universal.storytell.actions_quality` | 🔴 | 0 | 13 | — |
| `universal.storytell.directive_rendered` | 🟡 | 0 | 13 | — |
| `universal.thread_add.applied` | 🔴 | 0 | 13 | — |
| `universal.thread_update.valid_id` | 🔴 | 2 | 13 | T2 |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `cellar_secret` | T8 | T9 | 2 |  |
| `clear_the_road_toughs` | T1 | T5 | 5 |  |
| `deliver_the_ledger` | T1 | T13 | 13 | ⚠️ >8 turns |
| `dockside_confrontation` | T12 | T13 | 2 |  |
| `ledger_pursuit` | T7 | T13 | 7 |  |
| `road_instability` | T3 | T13 | 11 | ⚠️ >8 turns |
| `settle_the_debt` | T1 | T1 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_cellar` | 4 |  |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_well` | 5 | ⚠️ >4 turns |
| `river_docks` | 2 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `wounded` | T13 | T13 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1923 (+0) | 3256 (+0) | 2894 (+35) | 3660 (+36) | 7090 (+60) | 0 | 0 | 33.17 |
| 2 | I slide 500 credits across the table to Caron an… | 2177 (+12) | 3554 (+56) | 3218 (+122) | 3692 (+45) | 7539 (+77) | 0 | 0 | 30.34 |
| 3 | I find Halden by the town well and offer to carr… | 2203 (+24) | 3623 (+94) | 3209 (+74) | 3628 (-19) | 7534 (+19) | 0 | 0 | 29.40 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 2176 (-49) | 3629 (-30) | 3123 (+3) | 3610 (+4) | 7595 (+8) | 0 | 0 | 26.93 |
| 5 | I walk up to the two toughs at the inn door and … | 2210 (+31) | 3791 (+22) | 3126 (+49) | 3605 (-1) | 7751 (+28) | 0 | 0 | 26.12 |
| 6 | I drop 200 credits on the ground between the tou… | 2201 (+23) | 3775 (+30) | 3166 (+58) | 3653 (+18) | 7794 (+36) | 0 | 0 | 30.63 |
| 7 | I sit across from Halden at his table, slide the… | 2239 (+29) | 3805 (-24) | 3194 (+79) | 3634 (+37) | 7800 (+22) | 0 | 0 | 29.45 |
| 8 | I pull out the brass key Halden gave me and try … | 2188 (+19) | 3881 (-1) | 3126 (+5) | 3617 (-33) | 7911 (-51) | 0 | 0 | 32.04 |
| 9 | I press my ear against the inn's stone wall and … | 2166 (-57) | 4012 (+33) | 3128 (-39) | 3572 (-97) | 7976 (-39) | 0 | 0 | 27.11 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 2130 (-88) | 3955 (-21) | 3132 (-10) | 3607 (-17) | 7954 (-69) | 0 | 0 | 30.55 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 2170 (-30) | 4112 (+62) | 3208 (+105) | 3628 (+5) | 8176 (+91) | 0 | 0 | 31.34 |
| 12 | I grab the ledger from my coat and sprint out th… | 2244 (+59) | 4213 (+101) | 3247 (+152) | 3650 (+34) | 8219 (+111) | 0 | 0 | 31.57 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 2190 (+50) | 4275 (+178) | 3266 (+162) | 3660 (+18) | 8375 (+110) | 0 | 0 | 31.97 |
|  | TOTALS | 28217 | 49881 | 41037 | 47216 | 101714 | 0 | 0 | 390.61 |

**Total turns:** 13 · **Total duration:** 390.61s · **Avg/turn:** 30.05s
**Total tokens in:** 268,065 · **Total tokens out:** 9,919 · **Total LLM time:** 390.0s
**Total retries:** 0 · **Total parse failures:** 0

