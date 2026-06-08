# ccya Eval — Narrative & Mechanic Interplay Judge

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| T2 | crit_success | "" | "Breathe" (likely, based on velocity/threads) | Yes | "Water's a copper; news costs more than that..." | |
| T3 | fail | "" | "Pressure" (consecutive pressure counter was 1→0 in diff? No, T2 had no beat. T1 had revelation. T3 beat=pressure.) | Partial | "I don't talk about the dead... Harker was a fool." | DIRECTIVE_IGNORED |
| T4 | success | "" | "Pressure" (consecutive pressure 0→1) | Yes | "We aren't seeing walk-ins today... move along." | |
| T5 | partial | "" | "Pressure" (consecutive pressure 1→2) | Yes | "Keep your nose out of his business." | |

**Band Progression:** The run oscillates between success/fail/partial without a clear low→build→peak arc. Momentum stays mostly flat (0→2→1→2→2→0). This is appropriate for an investigation where progress is incremental, but the tone rarely shifts from "suspenseful" to "relieved" or "triumphant."

### 1A.5 — PacingContext Analysis

**Narration → outcome_hint:**
| Turn | PacingContext.outcome_hint | Honored? | Flag |
|------|----------------------------|----------|------|
| T2 | hold (likely) | Yes | |
| T3 | advance (impossible/fail often triggers advance or holds tension) | Yes | |

**Storytell → directive:**
| Turn | PacingContext.directive | Thread Action Aligned? | Flag |
|------|-------------------------|------------------------|------|
| T2 | Breathe/Empty | No new threads added. | |
| T3 | Pressure | `deliver_the_ledger` updated, no new thread. | THREAD_DIRECTIVE_IGNORED (Pressure usually warrants a beat or thread push) |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Source | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|--------|---------------|--------------------------|----------|------|
| T1 (T2) | revelation | Storytell | T2 | Yes | "Edda stops her rhythmic wiping... guarded intensity." | |
| T3 (T4) | pressure | Storytell | T4 | Yes | Silas blocks doorway, suspicious. | |
| T5 (T6) | pressure | Storytell | T6 | No | Narration describes Elena refusing key, but no specific "pressure" beat text is highlighted as a distinct event; it's just the refusal itself. | NO_EFFECT (Subtle) |
| T7 (T8) | breathing_room | Floor Relief? (Consecutive pressure was 3 at end of T6? Diff shows 0→2 in T5, then 2→0 in T6 diff? Wait. T5 diff: `consecutive_pressure_turns` 1→2. T6 diff: `consecutive_pressure_turns` 2→0 (reset by breathing_room?). T7 beat is null in extraction but state shows pressure? No, T8 applied deltas show no beat change from T7's null? Let's look at T8 State After Turn: `pending_gm_beat` is null. T9 State After Turn: `recent_beats` has T6 breathing_room. |
| T9 (T10) | complication | Storytell | T10 | Yes | Rockfall disrupts camp. | |

**Assessment:** Beats are generally reflected, but the "pressure" beats often just manifest as standard NPC refusal rather than a distinct narrative pivot or escalation event. The `breathing_room` beat in T6/T7 seems to have been injected by floor relief (consecutive pressure hit 3? No, diff shows reset).

### 1B.5 — Beat Generation Quality with Directive Context

| Turn Beat Created | Beat Type | PacingContext.directive | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------|------------------------|------|
| T2 (from T1) | revelation | Breathe/Empty | Yes (Revelation fits low pressure/investigation start) | |
| T4 (from T3) | pressure | Pressure | Yes | |
| T6 (from T5) | pressure | Pressure | Yes | |
| T8 (from T7) | null/null? | ? | N/A | |

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| deliver_the_ledger | Seed | arc | Yes, updated every turn. | Abandoned at T10/11 due to Harker rescue. | |
| clear_the_road_toughs | Seed | arc | No, never mentioned in narration after seed? Wait, T3 update says "Approaching the inn entrance". Narration doesn't mention toughs. | Inert Thread (Narrative disconnect) | INERT_THREAD |
| investigate_harker_disappearance | T5 | arc | Yes, drives turns 6-12. | Resolved at T12. | |

### 1C.5 — Thread Resolution Evaluation

| Thread ID | Added (Tn) | Resolved (Tm) | Scope | Narration Justified? | Flag |
|-----------|------------|---------------|-------|---------------------|------|
| deliver_the_ledger | Seed | T10/11 | arc | Yes, Harker rescue eclipses it. | |
| clear_the_road_toughs | Seed | T10 | arc | No, never narratively addressed, just abandoned because PC left town. | FALSE_RESOLUTION (Narrative didn't show resolution) |

### 1C.7 — goal_update → Narrative Effect

| Turn | goal_update Text | visible_goal After | Narration Shift? | Thread Focus Aligned? | Flag |
|------|------------------|--------------------|-----------------|------------------------|------|
| T5 (State Diff shows change) | "Investigate Harker's disappearance..." | Investigate Harker... | Yes, shifts focus from ledger to Harker. | `deliver_the_ledger` progress continues but `investigate_harker_disappearance` added. | |

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| heat_exhaustion | T1-T2 | No explicit mention of "heat exhaustion" debuff, but environment is hot. | N/A (No roll) | PHANTOM (Condition added in T1 extraction, never mentioned or mechanically referenced in prose/rolls) |
| rattled | T3-T4 | "Heavy silence... unsettling." | N/A | OK |
| threatened | T5-T6 | "Watched and cautioned." | N/A | OK |
| startled | T9-T10 | "Sudden tremor... disoriented." | Yes (Cond mod 0, but mentioned) | OK |

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| deliver_the_ledger | T2-T9 | arc | No, never explicitly mentioned as "delivering ledger" or "Halden's ledger" in prose. Only implied by location choices. | Yes (Progress updated) | PHANTOM_THREAD (Narrative doesn't reflect the specific thread summary) |
| investigate_harker_disappearance | T5-T12 | arc | Yes, drives all actions from T6 onwards. | Yes | OK |

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Silas Thorne:** Introduced in T4 as Assay Clerk. Reappears in T8 as General Store clerk? This is a continuity error (Ghost NPC / Identity Swap). Silas was an assay clerk, now he's tallying supplies at the general store. The narrator calls him "Silas Thorne" again but gives him a different role/location context without explanation.
- **Edda:** Introduced in T2 as Innkeeper/Bartender. Consistent.
- **Elena Vance:** Introduced in T5 as Sheriff's Deputy. Consistent.

### 2B — Player Intent Fidelity
- **T1:** "Ride into Dustfall... head for saloon." Narration: Arrives at saloon, notes silence/shadow. **Tight.**
- **T3:** "Ask what happened to Old Man Harker." Narration: Edda refuses, gives vague info about his death/debts. **Loose** (Player asked for fate, got refusal + rumor).
- **T6:** "Sheriff gives me key... walk to cabin." Narration: Sheriff *denies* key ("I told you once"). Player input was declarative/factual ("The sheriff gives me"), but the engine treated it as an action that failed because the state didn't support it (or the ruling LLM interpreted it as a request). This is **Intent Redirect** — the player stated a fact, the engine narrated a refusal.
- **T7:** "Look through desk... find locked tin box." Narration: Finds nothing ("finds no secret compartment"). Player input was declarative success ("I find"), engine rolled fail and denied it. This is a common LLM RPG issue where declarative inputs are treated as attempts rather than facts, especially when the ruling step classifies them as checks. **Broken** (if intent was "search" it's fine, but if player stated result, it should be honored or ruled impossible).

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:** Mostly high tension/suspense throughout. Only T2 and T8 feel like "breathing" moments (transaction/information gathering), but even T2 has Edda's guarded intensity.
- **Momentum arc:** Flat oscillation. No clear climax or resolution until the very end (Harker rescue).
- **Beat type variety:** Low. Mostly `pressure`, one `revelation`, one `complication`. Lack of `opportunity` or `twist`.
- **Intent verb variety:** High (`transition`, `persuade`, `sneak`, `negotiate`). Good coverage.
- **Skill coverage:** Charisma (T2, T3, T10), Wits (T4, T5), Strength (T7). Dexterity missing? No dexterity rolls seen.

---

## SECTION 4 — Scores

### Narrative Score: 3/5
The prose is competent and atmospheric ("bruised purple light," "scarred wood"). However, there are significant mechanical-narrative disconnects: Silas Thorne's identity swap (Assay Clerk → General Store Clerk), the phantom `deliver_the_ledger` thread never mentioned in prose, and the handling of declarative player inputs as failed checks (T6, T7) creates frustration rather than engagement.

### System Cohesion Score: 2/5
The engine fails to maintain NPC continuity (Silas Thorne). The thread system is largely decorative (`deliver_the_ledger` progress updates are invisible in narration). Conditions like `heat_exhaustion` are added but never referenced or mechanically impactful in the prose, making them phantom mechanics.

---

## SECTION 5 — Actionable Issues

- **NPC Identity Continuity Failure** (Turns: T4, T8) — Tag: `npc_ghost`. Silas Thorne is introduced as an Assay Clerk blocking a doorway, then reappears in Turn 8 as the General Store clerk tallying supplies. The engine's compendium/narrator pipeline failed to track NPC role/location consistency across location changes or treated them as separate entities incorrectly. Fix: Ensure `compendium_npc_update` tracks unique identities and prevents role/location drift unless explicitly justified by narrative logic (which it wasn't here).

- **Phantom Thread in Narration** (Turns: T2-T9) — Tag: `phantom_thread`. The thread `deliver_the_ledger` is updated with progress ("Learned of missing caravan rumors", "Purchased supplies") but the narration never mentions Halden, the ledger, or the obligation to deliver it. Fix: Inject thread summaries into narrator context more aggressively or require storyteller to explicitly weave thread goals into action outcomes.

- **Declarative Input Handling** (Turns: T6, T7) — Tag: `intent_redirect`. Player inputs "The sheriff gives me..." and "I find a locked tin box" are treated as attempts requiring rolls/checks rather than stated facts or successful actions. This contradicts the player's agency when they state outcomes directly. Fix: Improve Step 0 Ruling to recognize declarative statements of fact vs. attempts, or allow "impossible" checks for contradictions rather than randomizing success/fail on declared successes.

- **Condition Phantoming** (Turns: T1-T2) — Tag: `phantom_mechanic`. Condition `heat_exhaustion` is added in Turn 1 extraction but never mentioned in narration or applied as a mechanical modifier to subsequent rolls (T2 charisma roll had no cond_mod). Fix: Ensure conditions are either narratively referenced or mechanically applied; if neither, they shouldn't be generated.