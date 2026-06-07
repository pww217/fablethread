# ccya Eval — Narrative & Mechanic Interplay Judge

---

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| T2 | setback | "" | "Pressure" (implied by consecutive pressure logic in state, though directive empty in rules output) | Yes | "Water's a copper... ask the men by the entrance." | None |
| T4 | fail | "" | "Pressure" (consecutive_pressure_turns=3 at end of T3/T4 transition context) | No | Clerk is dismissive but helpful ("He wasn't here filing paperwork"). Not pressure. | DIRECTIVE_IGNORED |
| T5 | no_roll | "" | "Tension" or empty | Yes | Sheriff is cynical, provides info without threat. | None |
| T7 | success | "" | "Pressure" (consecutive_pressure_turns=1) | No | Discovery of map is positive; complication is minor shadow. Tone is suspenseful, not pressured. | DIRECTIVE_IGNORED |
| T8 | no_roll | "" | "Pressure" (consecutive_pressure_turns=2) | Yes | Thugs corner PC in store. High pressure. | None |
| T9 | no_roll | "" | "Pressure" (consecutive_pressure_turns=2→3) | No | PC is escaping/riding away. Scene motion is transition/advance, not sustained pressure. | DIRECTIVE_IGNORED |
| T10 | success | "" | "Pressure" (consecutive_pressure_turns=3) | Yes | Confrontation at campfire. High tension. | None |
| T12 | no_roll | "" | "Pressure" (consecutive_pressure_turns=1→2) | No | Escorting injured Harker is a relief/resolution beat, not pressure. | DIRECTIVE_IGNORED |

**Band Progression:** The momentum arc oscillates (-1 → -2 → -1 → 0). It feels appropriate for an investigation that hits dead ends then breakthroughs. However, the *directive* logic seems stuck in "Pressure" mode despite narrative relief (T4, T5, T7, T12), suggesting the `consecutive_pressure_turns` counter or directive computation is not resetting correctly when beats are non-pressure types, or the storyteller is ignoring the directive to de-escalate.

### 1A.5 — PacingContext Analysis (Two Signals)

**Narration → outcome_hint:**
| Turn | PacingContext.outcome_hint | Honored? | Flag |
|------|----------------------------|----------|------|
| T2 | advance (implied by scene motion to saloon interior) | Yes | None |
| T4 | transition (Assay Office) | Yes | None |
| T5 | transition (Sheriff Station) | Yes | None |
| T7 | hold (Cabin search) | Yes | None |
| T8 | transition (General Store) | No | DIRECTIVE_IGNORED_BY_NARRATOR |
| T9 | advance/transition (Red Canyon) | Yes | None |
| T10 | hold (Campfire confrontation) | Yes | None |
| T12 | transition (Back to Dustfall) | Yes | None |

*Note: Turn 8 narration describes entering the store and being cornered. The "advance" hint was likely honored by introducing the thugs.*

**Storytell → directive:**
| Turn | PacingContext.directive | Thread Action Aligned? | Flag |
|------|-------------------------|------------------------|------|
| T2 | Pressure (implied) | Added progress to `deliver_the_ledger`. No new threads. Aligned. | None |
| T4 | Pressure (implied) | Added progress. No new threads. Aligned. | None |
| T7 | Pressure (implied) | Added complication beat (`unknown_stalker`). Aligned with "Pressure" directive to add threat. | None |
| T8 | Pressure | Added `store_confrontation` thread. Aligned. | None |
| T9 | Pressure | Resolved store thread, added `canyon_ambush_threat`. Aligned. | None |
| T10 | Pressure | Updated ambush threat progress. Aligned. | None |
| T12 | Pressure (implied) | Resolved pursuit, updated main arc. Aligned. | None |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Source | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|--------|---------------|--------------------------|----------|------|
| T2 (T3 narration) | complication | Storytell | T3 | Yes | "Edda whispered... causing patrons to react with sudden tension." | None |
| T4 (T5 narration) | revelation | Storytell | T5 | No | Beat was `revelation` (surface: npc_behavior), but narration showed Sheriff dismissing PC. The "revelation" (no report filed) is info, not a narrative beat pivot in the prose style expected for a GM beat. Weak link. | NO_EFFECT |
| T7 (T8 narration) | complication | Storytell | T8 | Yes | Thugs enter store immediately. | None |
| T9 (T10 narration) | pressure | Storytell | T10 | Yes | "Silence of the canyon presses in... predatory." | None |
| T12 (T13 narration) | pressure | Storytell | T13 | No | Beat was `pressure` (surface: npc_behavior), but narration showed PC drinking whiskey calmly while *new* watchers appeared. The beat didn't drive the immediate action; it was background texture. | NO_EFFECT |

**Assessment:** Beats are creating consequences, but often lag or misalign in tone. T4's "revelation" beat failed to elevate the narrative tension as a revelation should (it was just info). T12's pressure beat was ignored by the calm whiskey drinking.

### 1B.3 — Surface Flag Consistency

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|
| complication | npc_behavior, environmental (T7) | No | SURFACE_DRIFT |
| pressure | ambient, npc_behavior, environmental | No | SURFACE_DRIFT |
| revelation | npc_behavior | Yes | None |

### 1B.5 — Beat Generation Quality with Directive Context

| Turn Beat Created | Beat Type | PacingContext.directive (Inferred) | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------------------|------------------------|------|
| T2 | complication | Pressure | Yes | None |
| T4 | revelation | Pressure | No | TYPE_MISMATCH |
| T7 | complication | Pressure | Yes | None |
| T8 | pressure | Pressure | Yes | None |
| T9 | pressure | Pressure | Yes | None |
| T12 | pressure | Pressure (implied) | Yes | None |

*Note: T4's revelation beat contradicts the "Pressure" directive which should favor complications or escalation.*

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| deliver_the_ledger | T1 (implicit start) | arc | Yes, progress tracked. | No (still active/inert) | INERT_THREAD |
| find_old_man_harker | T5 (via update/create) | arc | Yes, resolved in T12/T13 context. | Partially Complete | None |
| store_confrontation | T8 | scene | Resolved by fleeing to canyon. | Complete | None |
| canyon_ambush_threat | T9 | scene | Resolved by freeing Harker. | Complete | None |

### 1C.5 — Thread Resolution Evaluation

| Thread ID | Added (Tn) | Resolved (Tm) | Scope | Narration Justified? | Flag |
|-----------|------------|---------------|-------|---------------------|------|
| store_confrontation | T8 | T9 | scene | Yes, PC fled to canyon. | None |
| canyon_ambush_threat | T9 | T12 (via state diff) | scene | Yes, Harker freed. | LATE_RESOLUTION |

*Note: `canyon_ambush_threat` was resolved in the state of Turn 12/13 context but narratively resolved at the end of Turn 11. The resolution appeared in T12's state diff as "completed_threads" added, which is late.*

### 1C.7 — goal_update → Narrative Effect

| Turn | goal_update Text | visible_goal After | Narration Shift? | Thread Focus Aligned? | Flag |
|------|------------------|--------------------|-----------------|------------------------|------|
| T5 (via state diff) | "The PC is currently in Dustfall investigating the disappearance of Old Man Harker." | Investigating Harker's disappearance. | Yes, focus shifted from ledger to Harker. | None |

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| heat_exhaustion | T1-T2 | No (implied by "weary posture") | No | PHANTOM |
| rattled | T3, T7-T11 | Yes ("tension in the room", "unsettled") | No | None |
| threatened | T8-T9 | No (removed before narration of T9) | No | PHANTOM |
| startled | T7-T8 | No (removed before narration of T8) | No | PHANTOM |
| watched | T12-T13 | Yes ("watching you") | No | None |

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| deliver_the_ledger | T1-T12+ | arc | No (never mentioned by name) | Yes, progress updated. | PHANTOM_THREAD |
| find_old_man_harker | T5-T13 | arc | Implicitly via Harker rescue. | Yes. | None |

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Toughs (Bald/Scarred):** Entered at T8 (General Store). Narration described them entering. Consistent.
- **Sheriff Vance:** Introduced at T5. Present in narration. Consistent.
- **Assay Clerk:** Introduced at T4. Present in narration. Consistent.
- **Amy Holly:** Introduced at T8. Present in narration. Consistent.
- **Old Man Harker:** Rescued at T11. Present in narration at T12/T13. Consistent.

### 2B — Player Intent Fidelity
- **T1 (Transition to Saloon):** Honored.
- **T2 (Ask Bartender for News):** Honored. Edda provides info about thugs.
- **T4 (Assay Office):** Honored. Clerk gives info.
- **T5 (Sheriff Station):** Honored. Sheriff confirms no report.
- **T7 (Pry Box/Open Map):** Honored. Finds map, startled by shadow.
- **T8 (Buy Supplies):** Honored. Buys items, interrupted by thugs.
- **T9 (Ride to Canyon):** Honored. Travels to canyon.
- **T10 (Confront Thugs at Campfire):** Honored. Confronts them.
- **T12 (Escort Harker Back):** Honored. Returns to town.
- **T13 (Deliver Harker/Drink Whiskey):** Honored.

**Verdict:** Tight. The engine faithfully processes player actions and locations.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:** T2 (Med), T4 (Low/Med), T5 (Low), T7 (Med/Complication), T8 (High), T9 (Med), T10 (High), T12 (Med/Low).
    - Flag: >3 consecutive high-pressure beats in `recent_beats` history at end of run, but narrative tension varies. The *mechanic* counter (`consecutive_pressure_turns`) stays high because the storyteller keeps emitting pressure/complication beats even when narration is calm (T4, T5, T12).
- **Momentum arc:** Oscillates between -2 and 0. No clear peak or resolution of the main debt goal. The Harker rescue provides a local peak/resolution but doesn't shift momentum significantly.
- **Beat type variety:** Pressure/Complication dominate. Revelation (T4) was misused. Breathing Room appeared in T6/T10 history but not utilized effectively to reset tone.
- **recent_beats effectiveness:** The beat diversity guidance seems ineffective; the storyteller defaults to pressure/complication repeatedly, ignoring the "at least one in three should be non-pressure" rule evident in early turns (T4 revelation was an attempt, T6 breathing room existed).

---

## SECTION 4 — Scores

### Narrative Score: 3
The narration is competent and follows player intent tightly. However, mechanical disconnects exist: conditions like `heat_exhaustion` are phantom; beats like "revelation" fail to elevate narrative tone when they should; and the persistent "Pressure" directive despite calm scenes creates a tonal dissonance where mechanics say "danger!" but prose says "calm info gathering."

### System Cohesion Score: 2
The engine components talk, but not effectively. The **PacingContext** computation (Python) calculates pressure based on consecutive beats, but the Storytell LLM ignores de-escalation directives or fails to generate appropriate relief beats when directed. The **Beat Lifecycle** works (beats are stored and consumed), but the *alignment* between beat type/directive and narrative consequence is broken in ~40% of cases. Conditions are often phantom. Threads like `deliver_the_ledger` become inert background noise, never driving narration despite being active in state.

---

## SECTION 5 — Actionable Issues

- **Phantom Condition: heat_exhaustion** (Turns: T1-T2) — Tag: `<phantom_thread>` The condition was added but never referenced in prose or affected rolls. Fix: Ensure narrator references environmental conditions when they are active, or remove them if purely mechanical.
- **Directive-Narrative Disconnect: Pressure Directive on Calm Turns** (Turns: T4, T5, T12) — Tag: `<tone_mismatch>` The engine computed "Pressure" directives based on beat history, but the narration was informational/calm. Fix: Review `_compute_pacing_context` logic to ensure it resets when narrative velocity is low or de-escalation occurs naturally, rather than relying solely on consecutive pressure beats which may be misclassified by Storytell.
- **Beat Type Mismatch: Revelation as Pressure** (Turns: T4) — Tag: `<type_mismatch>` A "revelation" beat was generated under a "Pressure" directive context but failed to create narrative tension, acting instead as flat info delivery. Fix: Align Storytell prompt guidance so that "Revelation" beats are reserved for high-tension or plot-twist moments, not routine information gathering.
- **Inert Thread: deliver_the_ledger** (Turns: T1-T13) — Tag: `<inert_mechanic>` This thread was active and updated but never influenced narration or player choices directly. The Harker investigation completely overshadowed it. Fix: Either resolve this thread early when the PC shifts focus to Harker, or ensure its progress updates trigger narrative reminders of the original obligation.
- **Late Thread Resolution** (Turns: T12) — Tag: `<late_resolution>` `canyon_ambush_threat` was resolved narratively in Turn 11 but appeared in completed threads only in Turn 12's state diff, creating a lag in mechanical recognition of the story beat. Fix: Ensure thread resolution is applied and reflected in immediate next-turn context if possible, or accept that one-turn latency is acceptable for this engine version (but note it affects "System Cohesion").