# ccya Eval — Narrative & Mechanic Interplay Judge

---

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|
| 2 | success | "" | "Pressure" (implied by beat history, though not explicitly in Rules output, Storytell emitted pressure) | Yes | "News? Most folks... are looking to forget what they saw." | |
| 3 | success | "" | "Pressure" (consecutive beats) | Yes | "They say he was seen near the Crossed Keys right before those riders started circling." | |
| 4 | setback | "" | "Tension" / "Scene Pressure" | No | Silas blocks door, hostile. Tone is high tension, not just background pressure. | `DIRECTIVE_IGNORED` (if directive was low) or `TONE_MISMATCH` (if directive was Tension but outcome was Hostile Block). *Note: Rules output doesn't show Directive field in parsed JSON for turns 2-4, only outcome_summary. Assuming default/empty based on success/setback bands without urgent threads.* |
| 5 | fail | "" | "Breathe" (beat_locked from consecutive pressure reset? No, counter was 3 at T4 end, so beat_locked likely true at start of T5). *Correction: Counter resets to 0 at T5 because Storytell emitted `breathing_room` at T4.* So Directive is likely empty or "Tension". | Yes | "No report on my desk yet... we don't waste ink on ghosts." (Calm, dismissive) | |
| 6 | fail | "" | "Pressure" / "Complication" (Storytell emitted `revelation` at T5? No, T5 Storytell had no beat. T4 had `breathing_room`. So counter was 0 entering T5. T5 had no beat from Storytell? Wait, T5 Storytell output is empty JSON `{}` in the trace provided for Turn 5 (the second one). This implies a null turn or error handling resulted in no mechanics firing properly.) | N/A | *Narration describes finding Harker's hat.* | `DIRECTIVE_IGNORED` (Mechanics failed to drive narrative) |
| 7 | crit_success | "" | "Pressure" (Storytell emitted `pressure`) | Yes | "something heavy is being dragged slowly across the grit-coated floorboards toward your back." | |
| 8 | fail | "" | "Complication" (Storytell emitted `complication`) | No | Narration describes buying supplies calmly. Beat was `complication` with `npc_behavior`. Narrative ignores the complication entirely, treating it as a normal transaction until riders arrive *after* the beat should have manifested. | `DIRECTIVE_IGNORED` |
| 9 | fail (implied) | "" | "Pressure" / "Overwhelm"? | Yes | Victor Drax blocks exit, predatory stance. High tension matches pressure/complication. | |

**Band Progression:** The run oscillates wildly due to state corruption (see Section 5). Narratively, it feels disjointed because the location and NPC context jump randomly. Momentum arc is broken by the engine's internal clock/state errors.

### 1A.5 — PacingContext Analysis

| Turn | PacingContext.outcome_hint | Honored? | Flag |
|------|----------------------------|----------|------|
| 2 | "advance" (implied by transition intent) | Yes | |
| 4 | "transition" (location change to Assay Office) | Yes | |
| 5 | "transition" (location change to Sheriff's Station) | Yes | |
| 6 | "transition" (location change to Cabin) | No | `DIRECTIVE_IGNORED_BY_NARRATOR` (Narration describes finding key from Sheriff, but Rules said impossible/no roll? Actually Rules says `rolled: false`, outcome summary mentions reaching cabin. Narration *does* describe entering the cabin, so it honors the transition.) -> Honored. |
| 8 | "hold" / "advance"? | Yes | |

**Storyteller → directive:**
The trace shows significant inconsistencies in Storytell outputs (empty JSONs for Turns 5 and 10). When Storytell *does* output, it often emits beats that don't match the narrative flow or are ignored.

| Turn | PacingContext.directive | Thread Action Aligned? | Flag |
|------|-------------------------|------------------------|------|
| 4 | "Tension" (likely) | Added `investigate_harker_disappearance`. Aligned with investigation theme. | |
| 7 | "Pressure" | Added no new thread, updated existing. Beat was `pressure` environmental. Narration reflected it (scraping sound). | |

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Source | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|--------|---------------|--------------------------|----------|------|
| T1 (for T2) | pressure | Storytell | 2 | Yes | "News? Most folks... looking to forget." (Bartender's reluctance/pressure). | |
| T2 (for T3) | complication | Storytell | 3 | Partially | Bartender shares secrets, but the *complication* aspect is weak. It feels more like information delivery than a compounding problem. | `WRONG_EFFECT` (Complication usually implies worsening situation, here it's just info). |
| T3 (for T4) | complication | Storytell | 4 | Yes | Silas blocks door, hostile. This is a clear complication to entering the office. | |
| T4 (for T5) | breathing_room | Floor Relief / Storytell? | 5 | No | Beat was `breathing_room`. Narration at Sheriff's station is calm/dismissive ("no report"). It *does* feel like relief compared to Silas's hostility, but it's subtle. | |
| T5 (for T6) | revelation | Storytell | 6 | Yes | "Harker's hat" discovery? No, that was T10. T6 narration describes entering the cabin and finding it dusty/cold. The `revelation` beat seems to have manifested as the *atmosphere* of the cabin (shadowed, grit-coated), which is a weak revelation. | `WRONG_EFFECT` (Revelation usually implies new info; here it's just setting). |
| T6 (for T7) | pressure | Storytell | 7 | Yes | Scraping sound behind PC. Clear environmental pressure. | |
| T7 (for T8) | complication | Storytell | 8 | No | Beat was `complication` with `npc_behavior`. Narration describes buying supplies calmly. The *riders* arrive at the end, but they are not described as a "complication" from an NPC behavior beat in the same way Silas blocked the door. It feels like a separate event. | `NO_EFFECT` (Beat type didn't drive the immediate interaction). |
| T8 (for T9) | pressure | Storytell | 9 | Yes | Victor Drax blocks exit, predatory stance. High tension/pressure. | |

**Beats creating meaningful pivots?** Mostly yes when they fire correctly. However, Turns 5 and 10 have empty Storytell outputs, breaking the chain. The `breathing_room` at T4/T5 transition was effective in lowering tone from Silas's hostility to Sheriff's indifference.

### 1B.3 — Surface Flag Consistency

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|
| pressure | `npc_behavior` (T2), `environmental` (T7) | No | `SURFACE_DRIFT` |
| complication | `npc_behavior` (T3, T8) | Yes | |
| breathing_room | `ambient` (T5?) | N/A | |

*Note: The trace shows inconsistent surface_as for 'pressure'. T2 was NPC behavior (bartender reluctance), T7 was environmental (scraping sound). This is acceptable variety, but the prompt asks if it's consistent with directive changes. Without seeing directives, we flag as drift.*

### 1B.5 — Beat Generation Quality with Directive Context

| Turn Beat Created | Beat Type | PacingContext.directive | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------|------------------------|------|
| T2 (for T3) | complication | "Pressure" (inferred from counter) | Yes | |
| T4 (for T5) | breathing_room | "Breathe" (likely, due to floor relief/reset) | Yes | |
| T6 (for T7) | pressure | "Tension" / Empty? | Yes | |

### 1C — Thread Tension Chain

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|
| `clear_the_road_toughs` | Seed | arc | Yes, progressed through saloon/inn rumors. | No (still active/inert) | `INERT_THREAD` (Never resolved or advanced significantly beyond "rumors"). |
| `investigate_harker_disappearance` | T4 | scene -> arc | Yes, led to cabin, map, finding Harker. | Partially (Found Harker, but fate unclear?) | |
| `confront_predatory_rider` | T8 | scene | No, thread added in T8/9 trace confusion, then removed in T10 state diff without narrative resolution of Victor Drax. | Yes (Removed) | `FALSE_RESOLUTION` (Thread removed from arc but no narration resolved the confrontation with Victor). |
| `harker_hat_connection` | T10 | scene | Resolved by finding Harker? Thread says "abandoned" because hat recovered without resolving fate. | No | `INERT_THREAD` (Resolved as abandoned, but narrative found Harker alive). |

### 1C.5 — Thread Resolution Evaluation

| Thread ID | Added (Tn) | Resolved (Tm) | Scope | Narration Justified? | Flag |
|-----------|------------|---------------|-------|---------------------|------|
| `confront_predatory_rider` | T8/9 | T10 (removed in state diff) | scene | No. Victor Drax was not resolved narratively; the engine just deleted the thread while jumping locations/times. | `FALSE_RESOLUTION` / `MISSING_RESOLUTION` |

### 1C.7 — goal_update → Narrative Effect

No explicit `goal_update` observed in Storytell outputs that changed `visible_goal`. The visible goal remained "Clear your debts..." throughout, which is consistent with the early-game state, but the narrative focus shifted entirely to Harker without updating the arc's primary driver.

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| `dusty` | T5-T6 | Yes ("fine dust... clings") | No | |
| `startled` | T7-T8 | Partially ("sudden noise... broken concentration" implied in T7 narration?) | No | `PHANTOM` (Condition added in T7, removed in T8. Narration mentions "heavy silence" and "scraping", but doesn't explicitly reference the *startled* state affecting PC actions). |
| `exposed` | T9-T12 | Yes ("biting chill... seep through clothing") | No | |

### 1E — Unified Thread→Narrative Chain

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|
| `investigate_harker_disappearance` | T4-T12 | arc | Yes (Cabin, Map, Harker) | Yes | |

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit

- **Silas Vance:** Introduced at Assay Office (T4). Reappears as General Store Clerk in T8. *Flag:* `NPC_GHOST` / `COHERENCE_ERROR`. Silas was an Assay Clerk, now a General Store Clerk? The bio changes from "ink-stained fingers... spectacles" to "wiry man with ink-stained fingers". It's the same NPC model reused incorrectly or hallucinated as two roles.
- **Victor Drax:** Introduced in T8 (General Store). Disappears after T9 without resolution, thread deleted in T10 state diff while PC is at Canyon Camp. *Flag:* `NPC_GHOST`.

### 2B — Player Intent Fidelity

- **T6 Input:** "The sheriff gives me Harker's cabin key."
    - **Narration:** "You reach toward the desk... Kaelen Vance doesn't move to assist you... 'I don't have any keys'..."
    - **Verdict:** `BROKEN`. The player stated a fact ("Sheriff gives me key"). The engine rejected it as impossible/improbable and narrated a refusal, *but* the Rules output said `rolled: false` (impossible check?). However, the narration contradicts the user's explicit action statement. In TRPG engines, if an action is declared, the GM usually accepts or rolls against it, but outright denying "The sheriff gives me..." without a roll or negotiation attempt is a violation of intent fidelity unless `impossible=true` was set (which Rules output didn't explicitly show for T6, just empty JSON). *Correction:* Looking at T6 Rules: `intent_verb: sneak`. This implies the engine misclassified "gives me key" as sneaking? Or perhaps the user input in T6 was interpreted as trying to take a key they don't have. The narration says "reach toward... hand outstretched to claim a key that isn't there." This suggests the engine thought the player *tried* to grab a non-existent key, rather than accepting the gift. This is an `INTENT_REDIRECT`.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing:** T1-T4 High (Saloon tension, Silas hostility). T5 Low (Sheriff indifference). T6 Med (Cabin atmosphere). T7 High (Scraping sound). T8 Med/High (Riders arrive). T9 Very High (Victor Drax confrontation).
- **Momentum arc:** Broken by state corruption. Momentum jumps from 2 to 1, then 0, then 2, then 1, then 0. No discernible arc due to turn numbering and location resets in the trace data.
- **Beat type variety:** Pressure, Complication, Breathing Room, Revelation. Good variety when firing.
- **Intent verb variety:** `transition`, `persuade`, `sneak`. Low variety. `Sneak` used for entering a cabin with a key and prying open a box? Misclassification by Ruling step.

---

## SECTION 4 — Scores

### Narrative Score: 2/5
The narration is competent prose, but it frequently ignores or contradicts player intent (T6) and mechanic beats (T8). The state corruption in the trace (Turns 5, 10 having empty outputs while advancing time/location) suggests severe mechanical failures that would result in disjointed storytelling for a player.

### System Cohesion Score: 2/5
The engine fails to maintain continuity between turns. Threads are deleted without narrative resolution (`confront_predatory_rider`). NPCs change roles (Silas). The "Empty JSON" outputs for Turns 5 and 10 indicate pipeline failures that break the mechanic→narrative chain entirely.

---

## SECTION 5 — Actionable Issues

- **<Description>** (turns: 6, 8) — Tag: `intent_redirect`. Fix: Ruling step misclassifies "Sheriff gives key" as `sneak`/impossible grab instead of accepting the gift or rolling for persuasion. The engine must respect declarative actions unless truly impossible.
- **<Description>** (turns: 8, 9) — Tag: `npc_ghost`. Fix: Silas Vance appears in two different locations with conflicting titles (Assay Clerk vs General Store Clerk). Victor Drax disappears without resolution while the thread is silently deleted from state. Ensure NPC lifecycle and location tracking are consistent.
- **<Description>** (turns: 5, 10) — Tag: `inert_mechanic`. Fix: Storytell output is empty JSON `{}` for these turns, yet time/location advances in subsequent diffs. This indicates a pipeline crash or silent failure where mechanics do not drive narrative consequence.
- **<Description>** (turns: 9, 10) — Tag: `false_resolution`. Fix: Thread `confront_predatory_rider` is removed from arc state but no narration resolves the confrontation with Victor Drax. The player was left in limbo between a store and a canyon camp without narrative closure for that threat.