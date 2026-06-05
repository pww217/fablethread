---
state_fidelity_rate: 0.0
extraction_accuracy_score: 1
mechanic_lifecycle_score: 2
---

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