---

# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive (Inferred) | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-----------------------------------|-------------|---------------------------|------|
| 1 | N/A (No roll) | N/A | Pressure/Threat Pressure | Yes | "You have a lot of nerve showing your face here" | None |
| 2 | N/A (No roll) | N/A | Breathe/Pressure Release | Yes | "The debt is settled... weary respect." | None |
| 3 | N/A (No roll) | N/A | Tension/New Thread | Yes | "Fine. It's a short enough distance..." | None |
| 4 | N/A (No roll) | N/A | Pressure/Threat Pressure | Yes | "The heavy weight of the Wax-sealed ledger settles against your hip" | None |
| 5 | Partial | Complication | Pressure | Yes | "Best you keep walking before those questions start costing you more than just time." | None |
| 6 | Partial | Complication | Pressure/Overwhelm (Escalation) | **No** | Narration shows immediate physical violence/gripping, but prose tone is somewhat detached from the sudden escalation. "Caron's debt is settled... Take it and find something better to do." vs Bald Tough pinning coins. The disconnect is minor; tone matches the *failure* of the bribe, but misses the visceral shift in NPC behavior described in state. | TONE_MISMATCH (Subtle) |
| 7 | N/A (No roll/Empty Input?) | N/A | Pressure/Escalation | **Yes** | "Not so fast, messenger... You don't get to just hand it over and walk away like a saint." | None |
| 8 | Partial | Complication | Pressure/Complication | Yes | "Trying to run, messenger?... His grip is bruising..." | None |
| 9 | N/A (No roll) | N/A | Pressure/Escalation | **Yes** | "Talking to the stones now... Losing your wits along with your sense?" | None |
| 10 | Fail | Setback/Complication | Overwhelm/Pressure | Yes | "Get your hands off me... His eyes aren't scanning for a drink or a meal; they are tracking..." | None |
| 11 | Fail | Complication/Setback | Pressure/Escalation | **No** | Narration describes tackling Matthew, but the input was "Matthew's bodyguard draws a knife! I tackle him". The narration ignores the *bodyguard* aspect and focuses on Matthew. It also fails to reflect the *failure* of the tackle clearly in the prose tone (it says "sprawling clumsily" which is good, but misses the specific threat of Caitlin until later). | DIRECTIVE_IGNORED (Input ignored) |
| 12 | Fail | Complication/Setback | Pressure/Overwhelm | Yes | "Your boots slip... heavy wooden door... remains stubbornly barred." | None |
| 13 | N/A (No roll) | N/A | Breathe/Resolution | Yes | "The frantic tension of the Crossed Keys fades into a dull, rhythmic ache..." | None |

**Momentum Arc Assessment:** The momentum arc feels **appropriate**. It starts neutral, escalates through confrontation and failure (-1 to -3), hits floor relief (breathing room beat at T9/T12 state diffs show `pending_gm_beat` type changes or presence), and ends in a recovery phase. The progression from Town -> Road -> Inn Porch -> Tavern Interior -> Docks provides a coherent spatial arc that mirrors the narrative tension.

### 1A.5 — PacingContext.directive Analysis

| Turn | PacingContext.directive (Inferred) | Honored? | Flag |
|------|-----------------------------------|----------|------|
| 1-4 | Pressure/Tension | Yes | None |
| 5-9 | Pressure/Escalation | Yes | None |
| 10-12 | Overwhelm/Pressure (High Tension) | Yes | None |
| 13 | Breathe/Resolve | Yes | None |

*Note: PacingContext directives are not explicitly provided in the trace, but inferred from state changes and beat types. The narration consistently matches these inferred directives.*

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T5 (State Diff) | Pressure | T6 | Yes | Bald Tough pins coins, Scarred Tough flanks. "Caron didn't hire us to watch for Caron's debts." | None |
| T6 (Storyteller Output) | Pressure | T7 | Yes | Thugs demand info about ledger recipient. "The ledger stays with us... tell us exactly who's waiting." | None |
| T8 (State Diff) | Complication | T9 | **No** | State shows `pending_gm_beat` type change to `breathing_room`? No, T8 state diff shows `type: complication`. Narration in T9 reflects the *failure* of the bribe and mockery. The beat was "complication" (silhouette/window). This is reflected in T9 narration ("The silhouette at the second-story window leans further out"). | None |
| T10 (Storyteller Output) | Breathing Room? No, Storyteller says `breathing_room` but State Diff shows `type: complication`. | T11 | **No** | Storyteller output for T10 says `gm_beat: { type: breathing_room }`. However, the narration in T11 is high-tension combat (Tackle fail). The "Breathing Room" beat was *not* honored. Instead, a complication/escalation occurred. | NO_EFFECT / WRONG_EFFECT |
| T12 (Storyteller Output) | Breathing Room | T13 | Yes | Narration describes escaping to docks, wrapping wounds, quiet atmosphere. "The frantic tension... fades into a dull, rhythmic ache." | None |

**Assessment:** Beats are creating meaningful story pivots in most cases. The **T10 Breathing Room beat failure** is significant: the engine/storyteller signaled relief, but the narration continued high-tension combat, disconnecting the mechanic from the prose consequence. This suggests a misalignment between Progress Extract and Narrate on that turn.

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| settle_the_debt | Seed | Arc | Yes | Resolved in T2. Narration reflects payment and ledger closing. | None |
| deliver_the_ledger | Seed | Arc | Partially | Advanced in T3, T4, T13. However, the *delivery* itself is never narrated as a completed action; it remains an active tension until T13 where Aren leaves town without delivering it. The thread state advances but narrative resolution is pending/abandoned? No, just delayed. | None |
| clear_the_road_toughs | Seed | Arc | Yes | Advanced in T5-T9. Resolved by escaping the inn (T12/T13). Narration reflects leaving them behind. | None |

**Assessment:** Thread lifecycle is coherent. `settle_the_debt` resolves cleanly. `clear_the_road_toughs` resolves via escape. `deliver_the_ledger` remains active, which matches the narrative state (Aren has not delivered it).

### 1C.5 — Thread Expiration Evaluation

| Thread ID | Added (Tn) | Resolved/TTL (Tm) | Scope | Location Changed? | Narration Justified? | Flag |
|-----------|------------|-------------------|-------|-------------------|---------------------|------|
| settle_the_debt | Seed | T2 | Arc | N/A | Yes. Payment made, ledger marked. | None |
| clear_the_road_toughs | Seed | T13 (Implicitly resolved by escape) | Arc | Yes (Tavern -> Docks) | Yes. Aren leaves the scene of confrontation. | None |

**Assessment:** Thread expiration is justified by narration and location changes.

### 1D — Condition→Narrative Callback
For each active condition per turn: was it referenced in narration or did it affect a roll directive?

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T1-T7 (Seed) / T8 (Replaced by pain_spike?) | Yes. "ache in your ribs" (T2), "bruised face" (T3), "favor one side" (T3). Replaced/updated in T8 state diff? No, `pain_spike` added, `bruised_ribs` removed in T12? Wait, T12 State Extract shows `pc_condition_remove: [bruised_ribs]`. But T7 Narration mentions "bruised ribs". | Yes. Likely contributed to difficulty or narrative cost. | None |
| low_morale | Seed / Removed T2 | Yes (Implicitly). "hollow, restless ache" (T3). Removed in T2 state extract? No, removed in T2 State Extract. Narration reflects relief/shift. | N/A | None |
| pain_spike | T8-T12 | Yes. "sharp gasp of pain" (T8), "jars your bones... sharp pain through your ribs" (T11). Removed in T13? No, removed in T13 State Extract (`pc_condition_remove: [pain_spike]`). Narration reflects healing/resting. | Yes. Affected T11 roll outcome/failure description. | None |
| exhausted | T12-T13 | Yes. "hollow and physically drained" (T13). Added in T12 State Extract? No, added in T13 State Extract (`pc_condition_add: [exhausted]`). Narration reflects this state clearly. | N/A | None |

**Assessment:** Conditions are consistently referenced in narration and affect the tone/cost of actions. The transition from `bruised_ribs` to `pain_spike` is handled well narratively (grip causing spike).

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| settle_the_debt | T1-T2 | Arc | Yes. "Mark it cleared." (T2). | Resolved. | None |
| deliver_the_ledger | T3-T13 | Arc | Partially. The ledger is present ("Wax-sealed ledger settles against your hip"), but the *thread* of delivering it isn't explicitly narrated as a goal in every turn, just implied by possession. | Advanced. | PHANTOM_THREAD (Subtle) |
| clear_the_road_toughs | T5-T13 | Arc | Yes. Confrontation and escape described. | Resolved/Abandoned via location change. | None |

**Assessment:** `deliver_the_ledger` is a **Phantom Thread** in terms of explicit narrative focus. While the item exists, the *thread* (the obligation to deliver it) doesn't drive specific narration beats as much as the immediate threats do. It's present but silent until T13 where Aren leaves town without delivering it. This is acceptable for an active thread, but less "chained" than the others.

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Caron:** Present T1-T2. Removed in T3 Scene Extract. Narration reflects leaving him behind (T3). **Coherent.**
- **Halden:** Present T3-T4. Removed in T5 Scene Extract? No, Halden is not present in T5 scene. He was at the well. Aren leaves him to go to the inn. **Coherent.**
- **Bald/Scarred Toughs:** Added T5 (State Diff). Present T5-T10. Removed from `present_npcs` in T11 State Diff? No, they are removed in T12 Scene Extract? Wait, T11 Narration mentions them leaving? "The thugs have lost their grip on you as you moved from the porch into the tavern." (T12 Recent Events). They exit when Aren enters the tavern. **Coherent.**
- **Matthew Estrada:** Added T10 State Diff? No, present in T10 Narration. Present T10-T13. Removed in T14 Scene Extract? Trace ends at T13. He is still present in T13 narration context (left behind). **Coherent.**
- **Caitlin Kelly:** Added T11 State Diff. Present T11-T13. Left behind when Aren escapes to docks. **Coherent.**
- **Dock Boy:** Added T14 Scene Extract? No, added in T13 Scene Extract (`npc_add: [dock_boy]`). Narration reflects interaction and departure. **Coherent.**

**Ghost NPCs:** None detected. All present NPCs are mentioned or their absence is explained by location change.

### 2B — Player Intent Fidelity
- **T1:** Sit with Caron, talk debt. Honored.
- **T2:** Pay 500 credits. Honored.
- **T3:** Find Halden, offer delivery for 200. Honored.
- **T4:** Leave town, head to inn. Honored.
- **T5:** Ask toughs what they're doing. Honored (though they respond with threats).
- **T6:** Drop credits, say Caron's debt is paid. Honored (Bald Tough pins coins, rejects bribe).
- **T7:** *Input Missing in Trace?* Input field is empty `""`. Narration describes thugs escalating and demanding info about ledger recipient. This seems to be a continuation of T6/T5 context. The engine likely generated narration based on state/beat rather than specific input. **Loose** (due to missing input).
- **T8:** Use brass key to unlock door. Honored (Key fails, door barred).
- **T9:** Whisper "I have credits" and offer coin to wall. Honored (Mocked by toughs).
- **T10:** Grab Matthew's wrist, demand identity. Honored (Matthew reacts violently).
- **T11:** *Input:* "Matthew's bodyguard draws a knife! I tackle him..." Narration describes tackling Matthew, but ignores the "bodyguard" premise and focuses on Matthew as the primary opponent. It also fails to mention Caitlin drawing her knife in the narration until later? No, T11 Narration says: "From the shadows... Caitlin Kelly... draws a long, thin knife." So it *does* reflect the bodyguard/Caitlin element implicitly by having her draw. However, the input said "Matthew's bodyguard", implying Matthew is NOT the one drawing, but his guard is. The narration has Matthew reaching for his blade AND Caitlin drawing hers. This is a **Loose** interpretation of the specific "bodyguard" detail, merging it into general combat escalation.
- **T12:** Grab ledger, sprint out back door, shout to Halden. Honored (Fails due to barred door).
- **T13:** Find quiet corner at dock, wrap wounds, write note to Caron, pay dock boy. Honored perfectly.

**Verdict:** Tight / Loose. Mostly tight, with minor looseness on T7 (missing input) and T11 (interpretation of "bodyguard").

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:**
    - High Pressure: T5-T12 (Confrontation, Bribe Fail, Escape Fail).
    - Breathing/Resolution: T1-T4 (Setup), T13 (Recovery).
    - Consecutive high-pressure turns: 8 (T5-T12). This is **>4 consecutive high-pressure turns**. Flag.
- **Momentum arc:** Discernible arc from Neutral -> Escalation -> Floor (-3) -> Recovery. Coherent.
- **Beat type variety:** Pressure, Complication, Breathing Room. Variety is good. No >60% same type.
- **Escape paths:** When in bad situation (T12, momentum -3), Aren escapes to the docks. This was a viable choice reflected in narration and state change.

---

## SECTION 4 — Scores

### Narrative Score: 4/5
The prose is strong, consistent with the pack style, and honors most mechanics well. Conditions and inventory changes are reflected. The main deduction is for the **T10 Breathing Room beat mismatch** (mechanic signaled relief, narration continued combat) and the **consecutive high-pressure stretch** which felt slightly monotonous in tone despite escalating stakes.

### System Cohesion Score: 3/5
The engine generally works as a system, but there are notable disconnects:
1. **T10 Beat Mismatch:** Progress Extract signaled `breathing_room`, but Narrate produced high-tension combat. This breaks the mechanic→narrative chain.
2. **T7 Missing Input:** The trace shows an empty input for T7, yet narration proceeded as if there was a specific action (thugs demanding info). This suggests either a pipeline failure or a reliance on stale state/beat that wasn't clearly driven by user intent.
3. **Thread Phantoming:** `deliver_the_ledger` thread is active but rarely drives explicit narrative beats compared to immediate threats, making it feel somewhat inert mechanically until the end.

---

## SECTION 5 — Actionable Issues

- **Critical: Beat-Narration Mismatch on T10** (turns: 10) — Tag: `directive_ignored`. The Progress Extractor emitted a `breathing_room` beat, but the Narrator produced high-tension combat prose. This indicates a failure in how the Narrator consumes or prioritizes pending beats vs. current scene state/roll outcomes. Fix: Ensure Narrator prompt explicitly instructs to honor `pending_gm_beat.type` if it contradicts immediate roll outcome tone, or fix Progress Extractor logic for beat generation during high-tension states.
- **Major: Missing Input Handling on T7** (turns: 7) — Tag: `intent_redirect`. The input field is empty in the trace, but narration reflects a specific escalation ("Not so fast..."). This suggests the engine may be hallucinating intent or relying on stale context when no valid user input is provided. Fix: Validate non-empty user input before proceeding to Narrate step; if missing, default to "What happens next?" style prompt or error out.
- **Minor: Consecutive High-Tension Fatigue** (turns: 5-12) — Tag: `tone_mismatch`. While mechanically correct for the situation, 8 consecutive turns of pressure without a mechanical "Breathe" directive (despite T9/T12 having breathing room beats in state diffs? No, T9 beat was Pressure, T12 was Breathing Room but came *after* the fail) creates narrative fatigue. Fix: Consider injecting `breathing_room` or `resolution` directives more frequently during extended confrontations to allow for tactical pauses.
- **Minor: Phantom Thread Focus** (turns: 3-13) — Tag: `phantom_thread`. The `deliver_the_ledger` thread is active but rarely referenced in narration compared to immediate threats. Fix: Instruct Narrator to periodically reference the primary arc goal (`visible_goal`) or specific threads when no immediate combat threat dominates, even if just as internal monologue or NPC reminder.