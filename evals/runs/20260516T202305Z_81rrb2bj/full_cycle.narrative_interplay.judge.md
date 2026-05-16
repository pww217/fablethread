narrative_score: 3
system_cohesion_score: 2
***

# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + Narration Directive → Tone

| Turn | Band | Rules Directive | Narration Directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|---------------------|-------------|---------------------------|------|
| 5 | fail | Complication | N/A | Yes | "The broad man reaches out, intending to shove you back" | |
| 6 | setback | Complication | N/A | Yes | "He lunges forward... sending you stumbling backward" | |
| 8 | partial | Success w/ Complication | N/A | Yes | "The key turns... but the Lean Thug strikes... snatching the ledger" | |
| 10 | success | Success | N/A | Yes | "Matthew Estrada doesn't flinch... just stares at you" | |
| 11 | setback | Complication | N/A | Yes | "The silent guard recovers... attempts to pin your arms" | |

**Band Progression Assessment:**
The band progression is appropriate. The run moves from low-stakes negotiation (T1-3) to high-stakes physical confrontation (T5-11). The momentum arc is coherent: it starts at 0, drops to -1 (T5), -2 (T6), stays at -2 (T8, T11), then briefly recovers to -1 (T10) before dropping back to -2 (T11). This reflects the player's struggle against escalating threats.

### 1A.5 — Narration Directive Analysis

No explicit `narration_directive` fields were present in the provided trace for any turn. The engine appears to rely on the `band` and `stakes` for tone guidance, which is standard.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T5 | escalation | T6 | Yes | "The Scarred Tough grabs your collar to drag you toward the mud." | |
| T6 | complication | T7 | Yes | "The Lean Thug snatches the ledger from your hands before it can reach the door." | |
| T7 | complication | T8 | Yes | "The Lean Thug clutches the ledger tightly and prepares to bolt into the shadows with the prize." | |
| T8 | environmental | T9 | Yes | "The sudden darkness makes it impossible to track the Lean Thug's exact direction of escape." | |
| T11 | complication | T12 | Yes | "The silent guard recovers from the stumble and attempts to pin your arms..." | |
| T12 | environmental | T13 | Yes | "The rain begins to fall heavily, turning the alleyway into a treacherous, slippery gauntlet..." | |
| T13 | pressure | T14 | N/A | Beat expires or is replaced before narration in T14 (not provided). | |

**Beat Quality Assessment:**
Beats are creating meaningful story pivots. The escalation from the Scarred Tough's grab to the Lean Thug's theft to the environmental pressure of the rain creates a coherent chain of escalating danger.

### 1C — Pressure→Stakes→Consequence Chain

| Pressure ID | Added (Tn) | Stakes Named? | Consequence Extracted? | Chain Complete? | Flag |
|-------------|------------|---------------|------------------------|-----------------|------|
| inn_entrance_blockade | T4 | N/A | N/A | No | INERT_PRESSURE |
| physical_confrontation_imminent | T5 | N/A | N/A | No | INERT_PRESSURE |
| total_darkness | T9 | N/A | N/A | No | INERT_PRESSURE |
| rising_tide_flood | T13 | N/A | N/A | No | INERT_PRESSURE |

**Analysis:**
Scene pressures are added but never seem to feed into the `stakes` field in the Rules output (which is empty for most turns) or create explicit mechanical consequences in the narration beyond the immediate beat. The pressures exist in state but do not drive the narrative forward in a way that feels mechanically integrated. They are inert.

### 1C.5 — Pressure Removal Evaluation

| Pressure ID | Added (Tn) | Resolved (Tm) | Turns to Remove | Narration Justified? | Correct? | Flag |
|-------------|------------|---------------|-----------------|---------------------|----------|------|
| inn_entrance_blockade | T4 | T9 | 5 | No | No | LATE_REMOVAL |
| physical_confrontation_imminent | T5 | T8 | 3 | Yes | Yes | |
| total_darkness | T9 | T10 | 1 | Yes | Yes | |
| rising_tide_flood | T13 | N/A | N/A | N/A | N/A | |

**Analysis:**
`inn_entrance_blockade` was removed in T9, but the narration in T8 already showed the thugs retreating. The pressure persisted for 5 turns after being added, which is too long. The removal was justified by the narration in T8, but the state didn't update until T9.

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T1-T13 | Yes | No | |
| low_morale | T1-T10 | No | No | PHANTOM |
| winded | T5-T6, T8-T9, T11-T12 | Yes | No | |
| exhausted | T10-T11 | No | No | PHANTOM |

**Analysis:**
`low_morale` and `exhausted` are added to state but never referenced in the narration. They are phantom conditions. `bruised_ribs` is consistently referenced. `winded` is referenced.

### 1E — Arc Thread→Narrative Chain

| Thread ID | Active Turns | Thread State | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|--------------|--------------------------|---------------|------|
| settle_the_debt | T1-T3 | complete | Yes | Yes | |
| deliver_the_ledger | T3-T10 | complete | Yes | Yes | |
| clear_the_road_toughs | T4-T6 | failed | Yes | Yes | |
| the_ledger_itself_may_contain | T3-T8 | failed | No | Yes | SILENT_COMPLETE |
| the_identity_of_the_shadowy | T4-T8 | active | No | Yes | PHANTOM_THREAD |
| the_lean_man's_mention_of | T5-T8 | active | No | Yes | PHANTOM_THREAD |
| the_lean_thug's_sudden_interest | T7-T8 | active | No | Yes | PHANTOM_THREAD |
| the_brass_key_found_in | T11-T13 | latent | No | No | |
| the_river_docks_offer_a | T12-T13 | latent | No | No | |
| the_dock_boy_might_return | T13-T13 | latent | No | No | |

**Analysis:**
Several threads are marked as active or failed but never referenced in the narration. `the_ledger_itself_may_contain` was marked failed but the narration never addressed the ledger's contents specifically as a failed thread. `the_identity_of_the_shadowy`, `the_lean_man's_mention_of`, and `the_lean_thug's_sudden_interest` are active threads that are never mentioned in the prose. They are phantom threads.

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Caron:** Entered T1, left T3. Narration describes him leaving. OK.
- **Halden:** Entered T3, left T4. Narration describes him leaving. OK.
- **Shadowy Figures:** Entered T4, left T8. Narration describes them retreating. OK.
- **Benjamin Calloway:** Entered T8, left T10. Narration describes him leaving. OK.
- **Matthew Estrada:** Entered T10, left T12. Narration describes him being tackled. OK.
- **Silent Guard:** Entered T11, left T12. Narration describes him pursuing. OK.
- **Dock Boy:** Entered T13, left T13. Narration describes him leaving. OK.

No ghost NPCs or unexplained re-entries.

### 2B — Player Intent Fidelity
- **T1:** Player sits with Caron. Narration honors this.
- **T2:** Player pays debt. Narration honors this.
- **T3:** Player negotiates with Halden. Narration honors this.
- **T4:** Player heads to inn. Narration honors this.
- **T5:** Player confronts toughs. Narration honors this.
- **T6:** Player bribes toughs. Narration honors this.
- **T7:** Player thrusts ledger. Narration honors this.
- **T8:** Player uses key. Narration honors this.
- **T9:** Player bribes wall. Narration honors this (fails).
- **T10:** Player confronts Matthew. Narration honors this.
- **T11:** Player tackles guard. Narration honors this.
- **T12:** Player escapes. Narration honors this.
- **T13:** Player tends wounds/sends message. Narration honors this.

Verdict: **tight**.

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:** T1-T3 are low tension. T4-T13 are high tension. This is a long stretch of immediate pressure (10 turns).
- **Momentum arc:** Coherent decline from 0 to -2, with a brief recovery.
- **Beat type variety:** Mostly escalation and complication. Some environmental. OK.
- **Escape paths:** The player was given viable choices (bribe, fight, flee, investigate). The narration always presented the consequences of those choices.

## SECTION 4 — Scores

### Narrative Score (1–5)
**3/5**
The narration is competent and honors player intent. However, the tone is consistently grim and the pacing is relentless, which can feel monotonous. The narration does a good job of describing the physical consequences of the mechanics (bruised ribs, winded), but it fails to integrate the arc threads and conditions into the prose, making them feel like hidden mechanics rather than part of the story.

### System Cohesion Score (1–5)
**2/5**
The engine has significant cohesion failures:
1. **Phantom Threads:** Multiple arc threads are active or failed but never mentioned in the narration. This breaks the feedback loop between the arc system and the narrative.
2. **Phantom Conditions:** Conditions like `low_morale` and `exhausted` are added to state but never referenced in the narration or affecting rolls.
3. **Inert Pressures:** Scene pressures are added but never seem to influence the narrative or mechanics beyond being removed later.
4. **Late Pressure Removal:** `inn_entrance_blockade` persisted for 5 turns after the threat was narratively resolved.

The engine is behaving as isolated components: the narrator writes good prose, the extractor creates state, but the state (threads, conditions, pressures) does not feed back into the narrator or the player's experience effectively.

## SECTION 5 — Actionable Issues

- **Phantom Arc Threads** (turns: 4-8) — Tag: `phantom_thread`. Fix: Ensure the progress extractor's thread signals are reflected in the narration. If a thread is marked active, the narrator should reference the mystery or opportunity it represents. If marked failed, the narrator should show the failure.
- **Phantom Conditions** (turns: 1-10, 10-11) — Tag: `phantom_thread`. Fix: Either remove conditions that are not narratively relevant or ensure the narrator references them. `low_morale` and `exhausted` should either be removed or described in the prose.
- **Inert Scene Pressures** (turns: 4-9) — Tag: `inert_mechanic`. Fix: Scene pressures should create observable story consequences. If `inn_entrance_blockade` is active, the narration should reflect the difficulty of passing or the threat of the figures.
- **Late Pressure Removal** (turns: 4-9) — Tag: `state_mismatch`. Fix: Remove pressures when the narration shows the threat is resolved, not several turns later.