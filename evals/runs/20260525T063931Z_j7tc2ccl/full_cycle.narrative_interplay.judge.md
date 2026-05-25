---

# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| 1 | N/A (No Roll) | N/A | "" | N/A | "You pull a stool out..." | None |
| 2 | N/A (No Roll) | N/A | "" | N/A | "The principal is settled, Aren," | None |
| 3 | N/A (No Roll) | N/A | "" | N/A | "Two hundred credits to move a single book?" | None |
| 4 | N/A (No Roll) | N/A | "" | N/A | "You turn your back on the central well..." | None |
| 5 | Partial | Complication/Success with cost | Pressure? (Inferred from Toughs presence) | Yes | "Move along, and maybe we won't have to make your night any more difficult" | None |
| 6 | Success | Action succeeds cleanly | Tension/Pressure? (Inferred from Bribe context) | Yes | "Seems our client's business just got a lot more interesting." | None |
| 7 | N/A (No Roll) | N/A | "" | N/A | "Since you've gone through such trouble... perhaps there's another bit of business" | None |
| 8 | N/A (No Roll) | N/A | "" | Yes | "That's for a very specific lock, runner," he calls out. | None |
| 9 | N/A (No Roll) | N/A | "" | Yes | "Credits won't make the stone listen, boy..." | None |
| 10 | Crit Success | Action succeeds with maximum effect | Pressure/Opportunity? (Inferred from Matthew's calmness) | Partial | "You've got a grip like a cornered rat... find a corner and eat your meal" | TONE_MISMATCH (Crit success narrative is dismissive/threatening rather than empowering; however, the *mechanic* of momentum +3 suggests high agency. The prose reflects Matthew's dominance despite Aren's success in gripping him.) |
| 11 | Fail | Action fails completely | Pressure/Complication? (Inferred from Knife threat) | Yes | "Sit down, boy, or you'll find out how quickly a man can bleed out" | None |
| 12 | Setback | Partial success with cost | Overwhelm/Escalate? (Inferred from Chase context) | Yes | "You narrowly escaped... but you are now being pursued" | None |

**Momentum Arc Assessment:**
The momentum arc is **appropriate**. It starts at 0, rises to 3 on a Crit Success (T10), drops slightly on Fail/Setback (T11-12). The narrative tone generally matches the mechanical outcome: T5/T6 build tension and resolve it via bribery; T10 provides high agency but immediate consequence (Matthew's counter-threat); T11 is a hard fail resulting in near-death pressure.

### 1A.5 — PacingContext.directive Analysis

*Note: Specific `PacingContext` structs were not provided in the trace, so directives are inferred from narrative tone and beat generation.*

| Turn | Inferred Directive | Honored? | Flag |
|------|--------------------|----------|------|
| 1-4 | "" (Setup) | Yes | None |
| 5 | Pressure/Threat | Yes | None |
| 6 | Tension Release/Breathe | Yes | None |
| 7 | Opportunity/Tension | Yes | None |
| 8 | Revelation/Opportunity | Yes | None |
| 9 | Breathe/Entry Granted | Yes | None |
| 10 | Pressure/Escalate | Yes | None |
| 11 | Overwhelm/Pressure | Yes | None |
| 12 | Escalate/Chase | Yes | None |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T5 (Storyteller) | Pressure (npc_behavior) | T6 | Yes | Bald Tough accepts bribe, Scarred Tough eyes ledger. The pressure of the standoff resolves into a transactional tension. | None |
| T6 (Storyteller) | Opportunity (npc_behavior) | T7 | Partial | Halden offers new job. This is an opportunity beat reflected in narrative ("perhaps there's another bit of business"). | None |
| T8 (Storyteller) | Opportunity (npc_behavior) | T9 | Yes | Edda opens door, offering shelter/stew. This is the "opportunity" for entry/refuge. | None |
| T10 (Storyteller) | Revelation (npc_behavior) | T11 | No | Beat type was `revelation` but narrative shows immediate **pressure** (knife at throat). The revelation about Matthew's shipment is ignored in favor of the physical threat from Daniel. | WRONG_EFFECT |
| T11 (Storyteller) | Pressure (npc_behavior) | T12 | Yes | Pursuit begins immediately after failing to tackle Daniel. | None |
| T12 (Storyteller) | Pressure (npc_behavior) | T13 | Yes | Pursuit closes in ("heavy, rhythmic thud of pursuit... growing louder"). | None |

**Assessment:** Beats generally create meaningful pivots. The mismatch at T10 is minor—the revelation about the shipment *is* revealed in dialogue, but the narrative consequence (pressure) overrides it mechanically. This is acceptable as "complication" often supersedes "revelation" in high-tension scenes.

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| settle_the_debt | Seed | Arc | Yes (Resolved in T2) | Yes | None |
| deliver_the_ledger | Seed | Arc | Partially (Delivered to Halden, but narrative shifts focus) | Incomplete/Abandoned? | INERT_THREAD (The seed thread `deliver_the_ledger` was never explicitly advanced/resolved by ID; instead a new thread `halden_new_contract` was created. The original ledger delivery obligation seems to have been fulfilled narratively but not tracked mechanically via the specific seed thread ID.) |
| clear_the_road_toughs | Seed | Arc | Yes (Resolved via Bribe in T6) | Yes | None |
| halden_ledger_delivery | T3 | Scene | Resolved in T7 | Yes | None |
| the_inn_vigil | T5 | Scene | Expired/Abandoned? (Toughs bribed, threat neutralized) | Incomplete | INERT_THREAD (Thread added but never advanced or resolved; likely expired silently.) |
| halden_new_contract | T7 | Arc | Advanced in T8, T10, Resolved in T13? (Progress 3 -> Completed) | Yes | None |

**Note on `deliver_the_ledger`:** The seed thread ID was `deliver_the_ledger`. In T3, the storyteller added a *new* thread `halden_ledger_delivery` and advanced it. It did not advance the original seed thread. This is a **mechanic disconnect**: the engine created redundant threads instead of advancing the existing arc thread.

### 1C.5 — Thread Expiration Evaluation

| Thread ID | Added (Tn) | Resolved/TTL (Tm) | Scope | Location Changed? | Narration Justified? | Flag |
|-----------|------------|-------------------|-------|-------------------|---------------------|------|
| the_inn_vigil | T5 | N/A (Still active in state?) | Scene | Yes (Moved to Docks T12) | No explicit expiration event seen. Likely expired due to location change or age. | MISSING_EXPIRATION (Thread `the_inn_vigil` was added at T5, but no resolution/expiration is visible in the provided trace for T6-T13. It should have been removed when the toughs were bribed or upon leaving the inn.) |

### 1D — Condition→Narrative Callback
| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T1-T9 (Removed?) / T13+ | Yes ("bruised ribs protest", "stinging pain") | No explicit roll modifier shown, but narrative reflects it. | None |
| low_morale | Seed - T4 | Removed in T4 State Extract. Narration mentions "hollow emptiness". | N/A | None |
| winded | T10-T12 (Removed?) | Yes ("gasping for breath", "winded") | No explicit roll modifier shown. | None |

**Assessment:** Conditions are well-referenced in narration. `bruised_ribs` is a persistent narrative driver.

### 1E — Unified Thread→Narrative Chain
| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| halden_new_contract | T7-T13 | Arc | Yes ("new job opportunity", "secretive business") | Advanced/Completed | None |

**Assessment:** The `halden_new_contract` thread is the primary driver of narrative progression in turns 7-10. It successfully chains mechanics to story.

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
| NPC | Entry/Exit Turn | Narration Match? | Flag |
|-----|-----------------|------------------|------|
| Caron | T1 (Present) - T3 (Removed) | Yes. Present in T1/T2, removed from scene in T3 when Aren leaves tavern. | None |
| Halden | Seed - T7 (Moved to Inn) | Yes. Present at well in T3, moves to inn in T7. Removed from present_npcs in T9? No, he is still "Watching" in T10/T11. He seems to stay with Aren or follow him? Actually, in T9 Aren enters the inn and Halden is *inside*. This implies Halden followed Aren or was already there. Narration says "Halden's tapping continues... from behind the door." This is coherent. | None |
| Edda (Innkeeper) | Seed - T9 (Present in Inn) | Yes. Outside in Seed, enters scene at T9 when she opens the door. | None |
| Toughs | T5 (Added) - T6 (Removed/Changed status) | Yes. Appear at T5, bribed and step aside in T6. Removed from present_npcs? They are removed in T7 State Diff? No, they remain as "Greedy" until T9? Actually, T9 State shows them removed? Let's check T9 Applied Deltas: `npc_remove` is empty. But T10 State Diff shows them changed/removed? The trace is messy on exact removal turn for toughs, but narrative clearly has them step aside in T6 and not mentioned again until they are gone. | None |
| Matthew Estrada | Seed (Compendium) - T9/T10 (Present?) | Yes. Appears at bar in T9/T10 interaction. | None |
| Daniel Calloway | T11 (Added) | Yes. Draws knife immediately upon Aren's tackle attempt. | None |
| Hooded Figure | T12 (Added) | Yes. Observed from crates during chase. | None |
| Shivering Boy | T13 (Added) | Yes. Hired to deliver note. | None |

**Ghost NPCs:** No obvious ghost NPCs. All present_npcs in state diffs are referenced in narration or recent events.

### 2B — Player Intent Fidelity
| Turn | Input Action | Narration Processed? | Flag |
|------|--------------|----------------------|------|
| 1 | Sit with Caron, talk debt. | Yes. Sits down, conversation ensues. | None |
| 2 | Pay 500 credits. | Yes. Coins slid across table, ledger struck through. | None |
| 3 | Offer to carry ledger for 200 creds. | Yes. Negotiation with Halden occurs. | None |
| 4 | Leave town via east gate. | Yes. Walks out east gate, heads to inn. | None |
| 5 | Confront toughs at door. | Yes. Approaches them, they block path. | None |
| 6 | Bribe toughs with 200 credits. | Yes. Drops coins, toughs accept and step aside. | None |
| 7 | Deliver ledger to Halden. | Yes. Hands over ledger at inn table. | None |
| 8 | Try brass key on front door. | Yes. Tries lock, it fails/grinds. | None |
| 9 | Bribe wall/door for entry. | Yes. Whispers to stone, Edda opens door. | None |
| 10 | Grab Matthew's wrist, demand identity. | Yes. Lunges at bar, grabs wrist, demands info. | None |
| 11 | Tackle bodyguard (Daniel), search coat. | Partially. Input says "Tackle him... and search". Narration: Tackles *Matthew* by mistake? Or tackles Daniel? Narrative says "You lunge at Matthew Estrada... collide with bar." Then Daniel draws knife. The player intended to tackle the *bodyguard*, but tackled Matthew instead (or failed). This is a **Narrative Redirect** based on mechanical failure/ambiguity. | INTENT_REDIRECT (Player targeted bodyguard, narrative had them miss and hit bar/Matthew) |
| 12 | Sprint out back door with ledger. | Yes. Grabs ledger, bolts through kitchen. | None |
| 13 | Bandage wounds, write note to Caron, pay boy. | Yes. Bands ribs in crates, writes note, pays boy. | None |

**Verdict:** **Loose**. Most intents are honored precisely. T11 is a notable redirect: the player specified "Matthew's bodyguard" as the target of the tackle/search, but the narration had them lunge at Matthew (or miss entirely) and fail to search anyone. This suggests the Ruling/Intent step may have misclassified the target or the Narrator ignored the specific target in favor of a generic failure animation.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:**
    - Breathing/Low: T1, T2 (Debt talk), T4 (Travel).
    - Medium/Pressure: T3 (Negotiation), T5 (Standoff), T7 (New Job hint), T8/T9 (Entry struggle).
    - High/Escalate: T6 (Bribe resolution), T10 (Confrontation/Crit Success), T11 (Fail/Knife threat), T12/13 (Chase/Pursuit).
- **Momentum arc:** Discernible arc. Starts low, builds through debt clearance and contract acceptance, spikes at the inn confrontation (T10 Crit -> Momentum 3), crashes on Fail (T11 -> Momentum 2), stays high tension during chase (T12 Setback -> Momentum 1).
- **Beat type variety:** Pressure, Opportunity, Revelation. Good variety. No single type dominates >60%.
- **Escape paths:** When in bad situations (T5 standoff, T11 knife threat), viable choices were offered via actions list and narrative framing (bribe at T5, back away/defend at T11).

---

## SECTION 4 — Scores

### Narrative Score: 4
The prose is strong, adhering to the "plain language" style guide. Mechanics generally produce good fiction. The main deduction is for the **Thread Redundancy** (creating new threads instead of advancing existing ones) and the slight **Intent Redirect** at T11 where the player's specific target was ignored in favor of a generic failure narrative.

### System Cohesion Score: 3
The engine behaves as a system, but with notable friction points:
1.  **Thread Lifecycle Failure:** The engine failed to advance the seed thread `deliver_the_ledger` and instead created a duplicate/parallel thread `halden_ledger_delivery`. This indicates a failure in `_apply_thread_signals()` or the Progress Extractor's mapping logic to match existing arc threads by summary/tags rather than ID.
2.  **Thread Expiration:** The `the_inn_vigil` thread appears to have been left inert/missing expiration handling after the toughs were dealt with and location changed.
3.  **Beat/Narrative Mismatch:** T10's "Revelation" beat was narratively overridden by "Pressure," showing a slight disconnect between Beat Type and Narrative Consequence priority.

---

## SECTION 5 — Actionable Issues

**Critical**
- **<Description>** (turns: 3, 7) — Tag: `inert_mechanic`. The seed thread `deliver_the_ledger` was never advanced or resolved by ID. Instead, a new thread `halden_ledger_delivery` was created. This creates duplicate arc tracking and leaves the original goal context orphaned. **Fix:** Ensure Progress Extractor matches existing ArcThread IDs by summary/tag overlap before creating new threads, or explicitly resolve/advance existing ones.

**Major**
- **<Description>** (turns: 5) — Tag: `phantom_thread`. The thread `the_inn_vigil` was added but never advanced or resolved in the visible trace, despite the threat being neutralized by bribery and location changing. It likely expired silently without narrative consequence. **Fix:** Ensure scene-scoped threads are explicitly removed/advanced when their associated NPCs leave or threats resolve.
- **<Description>** (turns: 10) — Tag: `wrong_effect`. GM Beat type was "Revelation" but the narrative immediately shifted to "Pressure" (knife threat). While narratively coherent, it indicates the beat disposition logic may be ignoring its own type in favor of immediate scene tension. **Fix:** Align beat type with narrative consequence or ensure Revelation beats are surfaced as dialogue discoveries rather than ignored for combat pressure.

**Minor**
- **<Description>** (turns: 11) — Tag: `intent_redirect`. Player input specified tackling the "bodyguard," but narration described lunging at Matthew Estrada and failing to search anyone. This disconnect between player intent and narrative outcome reduces agency. **Fix:** Improve Ruling/Intent classification to correctly identify target NPCs, or ensure Narrator respects specific targets in failure outcomes (e.g., "You lunge for Daniel but miss...").