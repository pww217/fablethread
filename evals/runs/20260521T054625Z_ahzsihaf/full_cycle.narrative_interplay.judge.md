---

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| T1 | N/A (No Roll) | N/A | "" | Yes | "You look like you've had a rough trot on the road" | None |
| T2 | N/A (No Roll) | N/A | "" | Yes | "It’s done. The debt is settled." | None |
| T3 | N/A (No Roll) | N/A | "" | Yes | "Two hundred it is... make sure it stays dry." | None |
| T4 | N/A (No Roll) | N/A | "" | Yes | "The walk back toward the Crossed Keys is quiet" | None |
| T5 | Success | Honor the dice (Success) | Pressure/Complication? | Partial | "We aren't here for the stew, kid... waiting for a delivery." | DIRECTIVE_IGNORED (Narration shows success in *getting info*, but state implies standoff continues without resolution of the immediate threat. The band was Success, implying the player got what they wanted—knowledge—but the narrative frames it as an escalation rather than a successful interrogation.) |
| T6 | Partial | Honor the dice (Partial) | Pressure/Complication? | Yes | "Caron’s coin is paid... But we aren't working for Caron." | None |
| T7 | N/A (No Roll) | N/A | Pressure | Yes | "Scarred Tough shifts his weight, his shoulder slamming hard against yours" | None |
| T8 | Success | Honor the dice (Success) | Complication? | Partial | "The door groans, clicking open just a few inches... Scarred Tough's heavy arm tightening like a vice" | DIRECTIVE_IGNORED (Band was Success. Narration shows success in unlocking, but the *cost* is immediate physical restraint which feels more like a Fail/Setback outcome than a standard Success with minor complication.) |
| T9 | N/A (No Roll) | N/A | Pressure? | Yes | "The stone remains indifferent... mocking and derision." | None |
| T10 | Success | Honor the dice (Success) | Complication? | Partial | "Matthew Estrada doesn't flinch... 'Accusations are heavy things to carry'" | DIRECTIVE_IGNORED (Band was Success. Player demanded answers. Narration shows evasion and escalation, not a successful revelation.) |
| T11 | Partial | Honor the dice (Partial) | Complication? | Yes | "Successfully snatched a heavy pouch... but your precious ledger slid across the floor toward the thugs." | None |
| T12 | Partial | Honor the dice (Partial) | Complication? | Yes | "Successfully retrieved the ledger and escaped into the docks, but the stolen pouch snagged on a crate" | None |

**Momentum Arc Assessment:** The momentum arc is **inappropriate**. It oscillates wildly without clear cause-and-effect from the *narrative* consequences of the rolls.
- T5 (Success) → Momentum 1 (Expected +1). Narrative: Thugs still blocking, just talking more.
- T6 (Partial) → Momentum 1 (Expected 0). Narrative: Bribe rejected, pinned. This feels like a Fail/Setback in tone, not Partial.
- T8 (Success) → Momentum 2 (Expected +1). Narrative: Locked door but pinned tighter.
- T10 (Success) → Momentum 3 (Expected +1). Narrative: Confrontation escalated, thugs entered room. This feels like a Fail/Setback in terms of *safety*, though the player "won" the interaction socially? The momentum gain is disconnected from the narrative tension which increased drastically.
- T11 (Partial) → Momentum 3 (Expected 0). Narrative: Lost ledger temporarily.
- T12 (Partial) → Momentum 3 (Expected 0). Narrative: Escaped, lost pouch.

The band progression feels **too fast** in terms of narrative escalation relative to mechanical success. The player is rolling well but the situation gets progressively worse or more dangerous, creating a "Sisyphean" feel where Success doesn't yield relief.

### 1A.5 — PacingContext.directive Analysis

| Turn | PacingContext.directive | Honored? | Flag |
|------|-------------------------|----------|------|
| T7 | Pressure (inferred from beat) | Yes | None |
| T8 | Complication (inferred from beat) | Partial | DIRECTIVE_IGNORED_BY_NARRATOR (Success band, but narrative feels like a setback due to pinning.) |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T6 (Pending) | Pressure | T7 | Yes | "Scarred Tough shifts his weight, his shoulder slamming hard against yours" | None |
| T8 (Pending) | Complication | T9? | No | Beat was "Bald/Scarred tighten perimeter". Narration in T9 is about bribing the wall. The beat expired or was ignored. | NO_EFFECT |

**Assessment:** Beats are creating **mechanical noise**. The pressure from T6 manifested, but the complication from T8 (tightening perimeter) did not manifest narratively until perhaps implicitly in T10 when they entered? But even then, it wasn't framed as a "beat" consequence. The beat system is disconnected from the immediate narrative flow.

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| the_ledger_delivery | T3 | Scene | Yes | No (Thread expired early/incorrectly?) | INERT_THREAD (The thread `the_ledger_conspiracy` was added in T6, but the original delivery task seems to have been abandoned or conflated.) |
| the_ledger_intercept | T5 | Scene | Yes | Resolved? | None |
| the_ledger_conspiracy | T6 | Arc | Yes | Completed (T9) | SILENT_COMPLETE (Thread marked complete in T9, but narration shows ongoing chase/conflict. The "conspiracy" is still active.) |

### 1C.5 — Thread Expiration Evaluation

| Thread ID | Added (Tn) | Resolved/TTL (Tm) | Scope | Location Changed? | Narration Justified? | Flag |
|-----------|------------|-------------------|-------|-------------------|---------------------|------|
| the_ledger_conspiracy | T6 | T9 (Completed) | Arc | Yes (Inn -> Docks) | No | FALSE_EXPIRATION (Thread marked complete while player is still being hunted by the same group.) |

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T3-T4 | Yes (T3: "making your bruised ribs ache") | No | None |
| low_morale | T1-T2 | Yes (Implied in T2 relief) | No | None |
| cornered | T6 | Yes (T7: "pinning you more firmly") | No | None |
| rattled | T7, T9? | Yes (T7: "rattles your teeth", T8 implied franticness) | No | None |
| disoriented | T10-T12? | Yes (T10: "head swim", T13: "trembling fingers") | No | None |
| wounded | T12+ | Yes (T13: "scrapes and bruises... throbbing ache") | No | None |

**Assessment:** Conditions are **well-referenced**. The engine successfully tracks physical state and the narrator reflects it.

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| the_ledger_conspiracy | T6-T9 | Arc | Yes (Thugs hunting ledger) | Completed at T9 | SILENT_COMPLETE (Narrative tension continues, but thread is marked done.) |

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Toughs:** Entered in T5. Present through T10. Removed from scene state in T12 when player flees to docks. Narration confirms their presence until the escape. **Coherent.**
- **Matthew Estrada:** Added in T10 (State says added, but he was present in T9 narration? No, T9 narration mentions "Bald Tough" and "Scarred Tough". Matthew appears in T10). Wait, looking at T10 Input: "I approach Matthew Estrada...". State adds him. Narration describes the tackle. **Coherent.**
- **Kenneth Calloway:** Added in T11 (State says added). Narration introduces him as the bodyguard who draws a knife. **Coherent.**
- **Soot-stained Boy:** Added in T13. Narration introduces him. **Coherent.**

### 2B — Player Intent Fidelity
- **T5:** Input: "Ask them what they're doing." Output: They explain they are waiting for a delivery. **Fidelity: Tight.**
- **T6:** Input: "Drop credits... go home." Output: Bribe rejected, pinned. **Fidelity: Tight (Mechanically failed).**
- **T8:** Input: "Unlock inn's front door with brass key." Output: Door opens, but player is pinned. **Fidelity: Loose.** The input was specific about the *key* and the *door*. The narration focuses heavily on the pinning, making the success feel pyrrhic in a way that contradicts the "Success" band slightly (see 1A).
- **T9:** Input: "Bribe the wall." Output: Wall ignores. **Fidelity: Tight.**
- **T10:** Input: "Grab wrist... demand identity." Output: Matthew refuses to answer, thugs enter. **Fidelity: Loose.** The player got *no* information (Success band usually implies getting what you want), but the narrative shows evasion and escalation.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:**
    - T1-T4: Low/Medium tension (Debt, Contract).
    - T5+: High tension (Thugs, Chase, Combat).
    - There is a sharp spike in tension at T5 that never resolves. The "breathing room" of the debt settlement was short-lived.
- **Momentum arc:** Random oscillation / Upward spiral without release. Momentum hits 3 (Max) by T10 and stays there while the situation deteriorates (losing ledger, losing pouch, being hunted). This is a **broken** momentum loop where high momentum doesn't provide narrative leverage or safety.
- **Beat type variety:** Mostly "Pressure" and "Complication". No "Revelation" beats used effectively to advance plot beyond immediate threat.
- **Escape paths:** When in bad situations (T6, T8), the engine provided *mechanical* escape routes (unlocking door) but narratively constrained them with conditions (pinning). This creates a feeling of "railroading" rather than dynamic play.

---

## SECTION 4 — Scores

### Narrative Score: 3/5
The prose is competent and follows the style guide well (sensory details, second person). However, the *interplay* with mechanics drags it down. The "Success" bands often result in narrative outcomes that feel like failures or setbacks (T8, T10), creating cognitive dissonance for the player. The thread completion at T9 while the chase is ongoing breaks immersion.

### System Cohesion Score: 2/5
The engine fails to act as a unified system.
1. **Thread Lifecycle Failure:** `the_ledger_conspiracy` completes while the threat is still active and escalating (T9). This suggests the thread logic is based on arbitrary turn counts or progress thresholds rather than narrative resolution.
2. **Momentum Disconnect:** High momentum does not correlate with player agency or safety. The player rolls well but gets pinned/lost items anyway.
3. **Beat Ignorance:** GM beats (T8) are generated but do not appear in the narration, rendering them mechanical noise.

---

## SECTION 5 — Actionable Issues

**Critical**
- **<Thread Expiration Logic>** (turns: T9) — Tag: `false_expiration`. The thread `the_ledger_conspiracy` is marked complete at Turn 9, but the narrative continues with the same antagonists hunting the player through Turns 10-13. Fix: Ensure arc threads only resolve when the *narrative tension* associated with them is actually resolved (e.g., thugs defeated or escaped permanently), not just on progress thresholds.
- **<Momentum Band/Narration Mismatch>** (turns: T8, T10) — Tag: `directive_ignored`. The Rules System outputs "Success" bands for Turns 8 and 10, but the Narration describes outcomes that are mechanically equivalent to Setbacks or Fails (player is pinned/restrained in T8; player gets no info and faces new threats in T10). Fix: Align the Narrative outcome with the Band. If the band is Success, the player must achieve their *primary* intent (unlocking door / getting answer), even if complications exist. Do not negate the success entirely.

**Major**
- **<GM Beat Integration>** (turns: T8) — Tag: `no_effect`. A "Complication" beat was generated in Turn 8 ("tighten perimeter") but did not appear in the narration of subsequent turns. Fix: Ensure pending GM beats are surfaced in the next available narrative turn or explicitly acknowledged by NPCs/Environment.
- **<Intent Fidelity>** (turns: T10) — Tag: `intent_redirect`. Player intent was "Demand identity". Narration outcome was evasion and escalation. While this is a valid *complication*, it violates the spirit of the "Success" band which implies the player's action worked. Fix: If the band is Success, Matthew should reveal *something* (even if partial/misleading) or the band should be Partial/Fail to reflect the resistance.

**Minor**
- **<Condition Tracking>** (turns: T7-T9) — Tag: `phantom`. The "rattled" condition was added in T7 and removed in T8/9, but the narration's description of "frantic movements" spans multiple turns without clear mechanical justification for the removal. Fix: Ensure conditions persist as long as their narrative descriptor is relevant.