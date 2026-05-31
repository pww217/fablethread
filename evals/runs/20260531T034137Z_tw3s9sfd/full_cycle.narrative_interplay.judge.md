# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| T1 | N/A | N/A | "" | Yes | "Aren Voss approached Caron..." | |
| T2 | N/A | N/A | "" | Yes | "The Debt Is Settled" tagline. | |
| T3 | N/A | N/A | "" | Yes | "A Negotiated Errand." | |
| T4 | N/A | N/A | "" | Yes | "A Gauntlet of Shadows." | |
| T5 | Crit Success | Advance | "Tension" (likely, low urgency) | Partial | Narration resolves tension immediately despite "Tension" directive suggesting lingering. | `DIRECTIVE_IGNORED` |
| T6 | Fail | Setback | "Pressure" (urgent thread added in T4/T5 context implied) | Yes | "A Bribe Refused." Toughs refuse bribe, maintain blockade. | |
| T7 | N/A | N/A | "" | Yes | "Secrets and Sudden Intrusions." Matthew enters. | |
| T8 | Success | Advance | "Pressure" (urgent thread `estrada_suspicion` added) | Yes | "Eyes Locked in the Gloom." Estrada pivots to PC. | |
| T9 | N/A | N/A | "" | Yes | "The Exit Is Blocked." Wall bribe fails, Estrada closes in. | |
| T10 | Success | Advance | "Pressure" (urgent threads active) | Yes | "A Soldier's Cold Command." Estrada threatens with baton. | |
| T11 | Partial | Setback | "Overwhelm" or "Pressure" (multiple urgent threads: `estrada_interrogation`, `sensitive_cargo_mystery`) | Yes | "A Desperate Theft." PC steals cylinder but gets slammed into wall. | |
| T12 | Fail | Setback | "Pressure"/"Overwhelm" (urgent chase thread) | Yes | "A Desperate Flight to the Docks." PC escapes inn but is pursued. | |
| T13 | N/A | N/A | "" | Yes | "The Hunt Closes In." Search party fans out. | |

**Band Progression Assessment:** The run lacks explicit dice rolls for most turns (T1-T4, T7, T9), resulting in no band progression data from Rules output. However, the narrative momentum is high-tension throughout. When rolls occur (T5 Crit, T6 Fail, T8 Success, T10 Success, T11 Partial, T12 Fail), they drive significant plot pivots. The arc feels appropriate: low tension in town square → escalating confrontation at inn → chaotic theft → desperate chase.

### 1A.5 — PacingContext Analysis (Two Signals)

**Narration → outcome_hint:**
| Turn | PacingContext.outcome_hint | Honored? | Flag |
|------|----------------------------|----------|------|
| T5 | "advance" (implied by Crit Success/Resolution of toughs) | Yes | |
| T6 | "hold"/"advance" (Fail, but standoff continues) | Partial | `DIRECTIVE_IGNORED_BY_NARRATOR` |

*Note: Without explicit PacingContext logs in the trace, I am inferring from Rules Outcome and Narration. In T5, Crit Success should advance/resolve; it did resolve the immediate blockade. In T6, Fail usually implies a setback or hold; narration held the standoff but added pressure.*

**Progress Extractor → directive:**
| Turn | PacingContext.directive | Thread Action Aligned? | Flag |
|------|-------------------------|------------------------|------|
| T5 | "Tension" (likely) | Yes. Added `high_end_cargo_arrival` (arc). | |
| T6 | "Pressure" | Yes. Added `wasted_bribe` (scene), escalated `the_inn_gauntlet`. | |
| T7 | "" | Yes. No new threads, but added `sensitive_cargo_mystery` (arc) due to discovery. | |
| T8 | "Pressure" | Yes. Added `estrada_suspicion` (scene). | |
| T9 | "" | Yes. Added `trapped_at_the_inn` (scene). | |
| T10 | "Pressure" | Yes. Added `estrada_interrogation` (scene). | |
| T11 | "Overwhelm"/"Pressure" | Yes. Added `stolen_cylinder_heist` (scene). | |
| T12 | "Overwhelm" | Yes. Added `dockside_chase` (scene), removed old scene threads on location change. | |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T4 | opportunity (environmental) | T5 | Yes | "Bald Tough... lets out a sudden, sharp bark of a laugh... stepping aside." | |
| T5 | opportunity (npc_behavior) | T6 | No | Narration shows toughs refusing bribe and maintaining blockade. Beat was "opportunity," but narration showed complication/refusal. | `WRONG_EFFECT` |
| T6 | complication (npc_behavior) | T7 | Yes | Halden whispers about sensitive cargo; Matthew enters violently. | |
| T8 | pressure (npc_behavior) | T9 | Yes | Estrada closes distance, blocks path. | |
| T9 | pressure (npc_behavior) | T10 | Yes | Estrada threatens with baton, demands answers. | |
| T10 | pressure (event) | T11 | Yes | Bar shelves shatter; PC tackled and slammed into wall. | |
| T12 | pressure (event) | T13 | Yes | Search party fans out, lanterns sweep crates. | |

**Assessment:** Beats are generally effective story pivots. The T5 beat (`opportunity`) was narratively contradicted by the T6 outcome (refusal), suggesting a disconnect between the "Opportunity" tag and the actual NPC reaction to the bribe attempt. However, this might be interpreted as a "false opportunity," which is valid storytelling, but mechanically it flags as `WRONG_EFFECT`.

### 1B.3 — Surface Flag Consistency

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|
| opportunity | environmental (T4), npc_behavior (T5) | No | `SURFACE_DRIFT` |
| complication | npc_behavior (T6) | Yes | |
| pressure | npc_behavior (T8, T9), event (T10, T12) | Partial | `SURFACE_DRIFT` |

*Note: Surface drift is present but often justified by context. "Opportunity" as environmental vs NPC behavior is a significant shift in how the beat is presented.*

### 1B.5 — Beat Generation Quality with Directive Context

| Turn Beat Created | Beat Type | PacingContext.directive (Inferred) | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------------------|------------------------|------|
| T4 | opportunity | "" | Yes | |
| T5 | opportunity | "Tension" | Partial | `TYPE_MISMATCH` |
| T6 | complication | "Pressure" | Yes | |
| T8 | pressure | "Pressure" | Yes | |
| T9 | pressure | "" | Yes | |
| T10 | pressure | "Pressure" | Yes | |
| T11 | pressure | "Overwhelm"/"Pressure" | Yes | |
| T12 | pressure | "Overwhelm" | Yes | |

*Flag: In T5, a "Tension" directive (low urgency) resulted in an "Opportunity" beat. While not strictly wrong, it accelerated the plot more than "Tension" typically implies.*

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| settle_the_debt | Seed | arc | Yes | Resolved in T2. | |
| deliver_the_ledger | Seed | arc | Yes | Urgency escalated, ongoing. | |
| clear_the_road_toughs | Seed | arc | Partial | Upgraded to `the_inn_gauntlet` (T4). | |
| negotiating_the_contract | T3 | scene | No | Removed in T4 on location change without narrative resolution? Narration didn't resolve the negotiation; it jumped to travel. | `INERT_THREAD` / `MISSING_RESOLUTION` |
| the_inn_gauntlet | T4 | scene | Yes | Resolved by moving inside (T7). | |
| high_end_cargo_arrival | T5 | arc | Yes | Ongoing, evolved into `sensitive_cargo_mystery`. | |
| wasted_bribe | T6 | scene | Yes | Removed in T7 on location change. Narration didn't explicitly resolve it, but the bribe was a past event. | |
| estrada_suspicion | T8 | scene | Yes | Resolved by confrontation (T10). | |
| trapped_at_the_inn | T9 | scene | Yes | Resolved by escape (T12). | |
| stolen_cylinder_heist | T11 | scene | Yes | Removed in T12 on location change. Narration shows PC fleeing with it. | |
| dockside_chase | T12 | scene | Ongoing | Active in T13. | |

*Flag: `negotiating_the_contract` was added in T3 and removed in T4 due to location change (`crossed_keys_approach`). The narration for T4 describes traveling *to* the inn, but doesn't show the negotiation concluding with Halden. It jumps straight to encountering toughs. This is a missing narrative resolution.*

### 1C.5 — Thread Resolution Evaluation

| Thread ID | Added (Tn) | Resolved (Tm) | Scope | Narration Justified? | Flag |
|-----------|------------|---------------|-------|---------------------|------|
| settle_the_debt | Seed | T2 | arc | Yes | |
| negotiating_the_contract | T3 | T4 | scene | No | `MISSING_RESOLUTION` |
| the_inn_gauntlet | T4 | T7 | scene | Partial (PC forced inside) | |
| trapped_at_the_inn | T9 | T12 | scene | Yes | |

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | Seed, T1-T13 | Yes (T1, T8, T9) | No | |
| low_morale | Seed, T1 | Removed in T2 | N/A | |
| winded | T10-T12 | Yes (T12 narration mentions "agony in your bruised ribs" and "breathless") | Yes (T12 Dex roll was a Fail) | |

*Note: `winded` condition was active during T12. The Narration for T12 explicitly references the pain ("sharp agony in your bruised ribs catches your breath"), which aligns with the mechanical penalty of a failed escape attempt.*

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| settle_the_debt | Seed-T2 | arc | Yes | Resolved T2. | |
| deliver_the_ledger | Seed-Ongoing | arc | Yes (Ledger delivery) | Urgency escalated T7, T13. | |
| high_end_cargo_arrival | T5-Ongoing | arc | Yes (Toughs guarding cargo) | Active. | |
| the_sensitive_cargo_mystery | T7-Ongoing | arc | Yes (Halden's whisper) | Urgency escalated T8, T10, T13. | |
| dockside_chase | T12-T13 | scene | Yes (Toughs pursuing) | Active. | |

*Flag: No phantom threads detected in final state.*

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit

- **Caron:** Present T1, exits implicitly after debt settlement. Narration confirms departure ("find somewhere more comfortable").
- **Halden:** Present T3 (well), T7 (inn interior). Narration consistent.
- **Toughs:** Present T4-T6 (entrance), T7+ (known/pursuing). Narration consistent with location change logic.
- **Matthew Estrada:** Enters T7. Narration describes entry ("strides into the room"). Consistent.
- **Dock Boy:** Added to compendium in T13 extraction, but narration says "You spot a young dock boy... toss him a few coins." The extractor added him as `presence: known` *after* he was bribed and vanished. This is a slight inconsistency: the NPC should likely be marked `absent` or removed from active compendium if they left immediately, but `known` is acceptable for a transient character.

### 2B — Player Intent Fidelity

- **T1:** "Walk over to Caron... sit down." → Narration describes walking and sitting. **Tight.**
- **T2:** "Slide 500 credits... mark debt cleared." → Narration describes sliding coins and marking ledger. **Tight.**
- **T3:** "Find Halden by town well... offer to carry ledger for 200." → Narration describes finding Halden at the well and offering terms. **Tight.**
- **T4:** "Leave Marrow's Crossing... head for Crossed Keys Inn." → Narration describes leaving through east gate and approaching inn. **Tight.**
- **T5:** "Walk up to toughs... ask what they're doing." → Narration describes marching up and demanding explanation. **Tight.**
- **T6:** "Drop 200 credits... tell them Caron's coin is paid." → Narration describes dropping coins in mud and speaking the line. **Tight.**
- **T7:** "Sit across from Halden... slide merchant seal... hand ledger." → Narration describes pushing past toughs, finding Halden, sliding items. **Tight.**
- **T8:** "Pull out brass key... try to unlock inn's front door with it." → *Flag:* Player said "front door," but narration says "side of the inn where a heavy wooden door stands slightly ajar, leading toward the kitchens." The extractor identified this as a side/kitchen door. This is a **Loose** interpretation/redirection by the Narrator/Extractor to fit game logic (front door was blocked).
- **T9:** "Press ear against wall... whisper 'I have credits'... offer single credit to wall." → Narration describes leaning on outer wall, whispering, and coin clattering. **Tight.**
- **T10:** "Approach Matthew Estrada at the bar... grab his wrist... demand who he is." → Narration describes lunging to bar, grabbing wrist, demanding identity. **Tight.**
- **T11:** "Matthew's bodyguard draws a knife! I tackle him into bar shelves and search his coat..." → *Flag:* Player assumes Matthew *is* the bodyguard or that a separate bodyguard drew a knife. Narration tackles *Matthew Estrada*. The player input was slightly ambiguous ("bodyguard"), but the engine interpreted it as tackling the main threat (Estrada). **Loose.**
- **T12:** "Grab ledger... sprint out back door toward river dock." → Narration describes grabbing parchment (ledger), bursting through kitchen door, reaching docks. **Tight.**
- **T13:** "Find quiet corner... wrap wounds with shirt... write note to Caron... pay dock boy." → Narration describes ducking behind crates, tearing shirt strip, writing message, bribing dock boy. **Tight.**

**Verdict: Tight/Loose mix due to T8/T11 interpretations.**

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:**
    - Breathing: T2 (Debt settled), T7 (Delivery, though suspenseful).
    - High-Tension: T4, T5, T6, T8, T9, T10, T11, T12, T13.
    - *Flag:* Only 2 breathing turns in 13. This is a **High-Pressure Run**. No consecutive pressure > 4 without a beat resolution, but the overall density is very high.

- **Momentum Arc:** Low (T1) → Build (T5 Crit) → Peak Conflict (T6-T10) → Escape/Chase (T12-T13). Coherent arc.

- **Beat Type Variety:**
    - Opportunity: 2
    - Complication: 1
    - Pressure: 4
    - *Flag:* >75% are "Pressure". Low variety in beat types, though narratively effective.

- **Intent Verb Variety:**
    - negotiate (T1, T2, T3)
    - travel (T4)
    - persuade (T5)
    - deceive (T6, T9)
    - sneak (T8, T11)
    - intimidate (T10)
    - escape (T12)
    - repair (T13)
    - *Flag:* Good variety. "Negotiate" is dominant early on, but shifts to action verbs later.

- **Skill Coverage:**
    - Charisma: T5, T6, T10
    - Dexterity: T8, T11, T12
    - *Flag:* Strength, Wits, Lore, Resolve never appeared in dice rolls. This is a significant gap for a 6-skill system, though the scenario naturally favored Cha/Dex actions (negotiation, stealth, combat).

- **Escape Paths:** In T9/T10, when trapped by Estrada, the narration offered "Dash past," "Reason with," "Grab Halden." Viable choices were presented. In T12, escape was successful but led to a chase. Good agency maintained under pressure.

---

## SECTION 4 — Scores

### Narrative Score: 4/5
The fiction is strong, responsive, and coherent. Mechanics (conditions, threads) are reflected in prose well. The only deductions are for the missing narrative resolution of `negotiating_the_contract` thread (T3→T4 jump) and the slight misinterpretation of "front door" vs "side door" in T8.

### System Cohesion Score: 4/5
The engine behaves as a cohesive system. State changes (inventory, conditions, threads) are accurately reflected in narration and subsequent turns. Thread lifecycle is managed correctly (location-based purging). The `negotiating_the_contract` thread removal without narrative resolution is a minor cohesion gap where the extractor removed a scene thread due to location change before the narrator could close it narratively.

---

## SECTION 5 — Actionable Issues

- **<Description>** Missing narrative resolution for `negotiating_the_contract` thread when player traveled from Well (T3) to Inn Entrance (T4). The engine purged the scene thread due to location change, but the narrator did not include a beat showing Halden accepting/rejecting the deal or Aren leaving him. This creates a "phantom" resolution where the mechanic says it's gone, but the story didn't show it happen. **(turns: 3-4)** — Tag: `MISSING_RESOLUTION`. Fix: Ensure Narrator receives context of purged scene threads to provide a closing beat before location transition completes.

- **<Description>** In T8, Player input "unlock inn's front door" was narrated as unlocking a "side/kitchen door." While logically sound for gameplay (front was blocked), it contradicts the player's specific intent and description of the object they were interacting with. **(turns: 8)** — Tag: `INTENT_REDIRECT`. Fix: Narrator should acknowledge the front door is blocked or clarify that only a side key works, rather than silently substituting the target.

- **<Description>** In T11, Player input "Matthew's bodyguard draws a knife" was interpreted as tackling Matthew Estrada directly. The player may have been referring to a separate NPC (Toughs were present). This ambiguity led to a tackle of the main antagonist instead of a generic thug. **(turns: 11)** — Tag: `INTENT_REDIRECT`. Fix: Clarify if "bodyguard" refers to Estrada or an additional entity in the ruling phase, or narrate both possibilities.

- **<Description>** Skill coverage is heavily skewed toward Charisma and Dexterity. Strength, Wits, Lore, and Resolve never appeared in dice rolls across 13 turns. While scenario-driven, this limits mechanical diversity. **(turns: 1-13)** — Tag: `INERT_MECHANIC`. Fix: Consider introducing a moment requiring Lore (analyzing the ledger/cylinder) or Strength/Resolve (physical struggle with Estrada/Toughs) to balance skill usage.