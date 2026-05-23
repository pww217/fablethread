# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| 5 | Success | None | "" | Yes | "We're just here for the festival... debts are being respected." | |
| 6 | No Roll | Deceive (Fail implied by context) | "" | N/A | Thugs ignore bribe, eye ledger. | `DIRECTIVE_IGNORED` |
| 8 | Success | None | "" | Yes | "The door yields... quiet storage room." | |
| 9 | Setback | Pressure Beat | "" | Yes | "One coin for a secret? ... peel this door off its hinges" | |
| 10 | Setback | Pressure Beat | "" | Yes | "If you're looking for answers, find them somewhere that isn't about to become a butcher's shop." | |
| 11 | Crit Fail | Chaos/Pressure | "" | Yes | "chaotic mess of splintering wood and shattering pottery" | |
| 12 | Success | Escape | "" | Yes | "burst through the back door... sprint toward the docks" | |

**Band Progression Assessment:** The momentum arc is coherent. It starts neutral (0), builds to positive peak (+2) after successful stealth/delivery, then crashes (-2) due to a critical failure in combat/chaos, and recovers slightly (-1) via escape. This feels appropriate for a "reluctant courier" caught in over their head.

### 1A.5 — PacingContext.directive Analysis

No explicit `PacingContext` directives (like "Breathe", "Escalate") were present in the provided trace outputs, so this section is marked N/A based on available data. The narrative tone naturally escalated with momentum changes without needing explicit directive flags from a pacing context module.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T9 (Pressure) | Pressure | T9, T10, T11 | Yes | Scarred Tough breaks down door (T9), bursts out (T10/11). | |

**Assessment:** The GM beat created in Turn 9 ("Scarred Tough begins actively attempting to break down the storage room door") was honored perfectly. It drove the tension through T10 and resolved with a breach in T11, forcing the player's escape action in T12. This is high-quality mechanical storytelling.

### 1B.5 — Beat Generation Quality with Directive Context

N/A (No PacingContext directives present). However, the beat type `pressure` was appropriate for the escalating confrontation at the inn door and storage room.

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| settle_the_debt | N/A (Seed) | Arc | Yes | Resolved in T2. | |
| deliver_the_ledger | N/A (Seed) | Arc | Yes | Resolved in T7/T12. | |
| clear_the_road_toughs | N/A (Seed) | Arc | Partially | Active but unresolved by end of trace. | `INERT_THREAD` (Partial) |

**Note:** The thread `clear_the_road_toughs` was advanced in T5, T6, and T13, but never resolved or removed from the active list despite the player escaping. While not "inert" as it drove action, it remains an open loop at the end of the trace.

### 1C.5 — Thread Expiration Evaluation

| Thread ID | Added (Tn) | Resolved/TTL (Tm) | Scope | Location Changed? | Narration Justified? | Flag |
|-----------|------------|-------------------|-------|-------------------|---------------------|------|
| settle_the_debt | Seed | T2 | Arc | N/A | Yes. Payment made, ledger marked. | |
| deliver_the_ledger | Seed | T7 (Resolved) / T12 (Escaped with it?) | Arc | No | `FALSE_EXPIRATION`/`STATE_MISMATCH`. Thread resolved in T7 when handed to Halden, but Player *took* the ledger back in T12? **Correction:** In T7, Narration says "You pull out the heavy ledger... and lay it on the table." Storyteller resolves thread. BUT in T12, Input is "I grab the ledger from my coat". This implies the player took it *back* or never gave it up? Or did they take a different one? The narration in T7 says Halden takes it ("weight of the errand finally passing from your shoulders to his"). Yet T12 input assumes possession. **Major Disconnect.** |

**Flag:** `STATE_MISMATCH` on Thread `deliver_the_ledger`.
*   **T7 Storyteller:** Resolves thread, implies handover complete.
*   **T12 Narration/Input:** Player grabs ledger from coat and runs.
*   **Analysis:** The engine allowed the player to possess an item they had just surrendered and resolved a thread for, without any narrative justification (e.g., "You realize you grabbed the wrong ledger," or "Halden hands it back in panic"). This breaks causality.

### 1D — Condition→Narrative Callback
| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T1, T3, T4 | Yes (T1: "bruised ribs protest", T3: "ache with sharp throb") | No | |
| low_morale | Seed-T2 | N/A (Removed in T2) | N/A | `PHANTOM` (Never referenced in prose before removal). |

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| clear_the_road_toughs | T5-T13 | Arc | Yes (Thugs present, confrontations occur) | Advanced multiple times. | `SILENT_COMPLETE` (Not complete, but thread logic seems stuck). |

**Flag:** None critical for active threads, except the causality break noted in 1C.5 regarding ledger possession.

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
*   **Halden:** Present T3-T7. Removed from scene in T7 (Extraction says `npc_remove: [halden]`). Narration in T7 confirms handover. However, Halden reappears as an NPC to be shouted at in T12 ("shouting for Halden to hold on") and is present in the dock scene extraction (`npc_add: halden`).
    *   **Flag:** `NPC_GHOST` / `REENTRY_WITHOUT_NARRATION`. The player shouts for him, but there was no narrative beat explaining how he got from the inn table (T7) to the docks (T12). Did he flee? Was he kidnapped? The engine silently moved him.
*   **Scarred Tough:** Present T5-T9 in storage room. Removed from scene extraction in T10 (`npc_remove: [scarred_tough]`). Reappears as `tough_b` lunging into common room in T11. This is consistent with the "burst through door" beat, but the state management was messy (removed then added back implicitly).

### 2B — Player Intent Fidelity
*   **T7 vs T12 Ledger Issue:** As noted in 1C.5, the player's intent to grab the ledger from their coat in T12 contradicts the narrative resolution of that thread in T7 where Halden took it and the player's shoulders were "relieved." The engine failed to flag this possession conflict or narrate a retrieval.
*   **T9 Bribe:** Player offered 1 credit to a *wall*. Narration handled this absurdity well ("Is that all you've got, little mouse?"), treating it as a bizarre attempt to bribe someone behind the wall. Good fidelity to "Honor the dice/action."

**Verdict:** Loose. The ledger possession error is a significant break in causal logic.

---

## SECTION 3 — Pacing Assessment

*   **High-tension vs breathing turns:**
    *   T1-T2: Low/Med (Debt negotiation).
    *   T3-T4: Med (Contract/Travel).
    *   T5-T6: High (Confrontation/Bribe fail).
    *   T7: Low/Sanctuary (Delivery).
    *   T8: Med (Stealth discovery).
    *   T9-T12: Very High (Cornered, Chaos, Escape).
*   **Momentum Arc:** 0 → +1 → -1 → +1 → +2 → +1 → 0 → -2 → -1. This is a strong, dramatic arc. The crash at T11 feels earned due to the Crit Fail and previous pressure beats.
*   **Beat Type Variety:** Mostly `pressure` and implicit complications from failed rolls. Good variety in *types* of pressure (social vs physical).
*   **Escape Paths:** When momentum hit -2 (T11), the engine provided a clear escape path via Dexterity roll (Success) to T12. This is good design; even on a crash, there's an out if the player rolls well.

---

## SECTION 4 — Scores

### Narrative Score: 3/5
The prose quality and tone are excellent. The "Honor the dice" mechanic works beautifully (e.g., T11 Crit Fail resulting in chaotic clumsiness rather than just "you miss"). However, the **Ledger Causality Break** is a major flaw. The player surrendered an item, had it resolved as complete, and then spontaneously possessed it again without narrative explanation. This breaks immersion and logical consistency.

### System Cohesion Score: 2/5
The engine fails to maintain state integrity regarding inventory and thread resolution.
1.  **Inventory Leak:** Ledger was removed from PC inventory in T7 (implied by handover) but reappeared in PC inventory in T12 without any `inventory_add` event or narrative justification.
2.  **Thread State Mismatch:** The thread `deliver_the_ledger` resolved, yet the player acted as if they still held the object central to that thread.
3.  **NPC Silently Moved:** Halden moved from Inn Table (T7) to Docks (T12) with no intervening narration or state update explaining his movement.

The mechanics are not "decorative," but they are leaking and inconsistent, creating plot holes the narrator has to gloss over or ignore.

---

## SECTION 5 — Actionable Issues

**Critical:**
- **Inventory/Thread Causality Break (Turns: 7, 12)** — Tag: `state_mismatch`. The ledger was handed to Halden and thread resolved in T7, but the player grabs it from their coat in T12. Fix: Ensure inventory state matches narrative handovers. If a thread resolves via item transfer, remove item from PC unless explicitly returned.
- **NPC Silently Relocated (Turns: 7, 12)** — Tag: `npc_ghost`. Halden disappears from the Inn and reappears at the Docks without narration or state update explaining his movement. Fix: Narrate Halden's departure in T8-T11 or explicitly move him to a new location with an event log entry.

**Major:**
- **Low Morale Phantom Condition (Turns: 2)** — Tag: `phantom`. The condition was removed from state but never referenced in prose before removal, making its mechanical impact invisible to the player. Fix: Reference conditions in narration when they are active or resolved if relevant.

**Minor:**
- **Thread Stagnation (Turns: 5-13)** — Tag: `inert_mechanic`. The thread `clear_the_road_toughs` was advanced but never closed, even after the player escaped town. Fix: Auto-resolve or demote threads when location changes significantly and threat is no longer present in current scene.