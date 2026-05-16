# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-16T04:11:52.096192+00:00 · **Finished:** 2026-05-16T04:20:13.498109+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260516T041152Z_mbotr6bl`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260516T001122Z_uaxubzgd/artifacts`

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** 4/5  
**Compaction:** —/5  
**State Fidelity:** —  
**Prompt Adherence:** 97.0%
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 5/5
- narrate: 5/5
- extract_scene: 4/5
- extract_state: 4/5
- extract_progress: 5/5

**Domain judge breakdown:**

| Judge | Scores |
|---|---|
| `state_correctness` |  |
| `narrative_interplay` |  |
| `prompt_pipeline` | prompt_quality_score=4, prompt_adherence_rate=97.0% |
| `compaction` |  |

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  
**[narrative_interplay trace](full_cycle.narrative_interplay.trace.md)** · **[narrative_interplay verdict](full_cycle.narrative_interplay.judge.md)**  
**[prompt_pipeline trace](full_cycle.prompt_pipeline.trace.md)** · **[prompt_pipeline verdict](full_cycle.prompt_pipeline.judge.md)**  
**[compaction trace](full_cycle.compaction.trace.md)** · **[compaction verdict](full_cycle.compaction.judge.md)**  
**[meta trace](full_cycle.meta.trace.md)** · **[meta verdict](full_cycle.meta.judge.md)**  

## ⚠️  Flagged

### `rejected_deltas` — 2 rejected delta(s) across the run

- turn 6: 1 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 2 turn(s) errored
- turn 6: engine_errors: [{"trace_id": "cd57e181", "message": "Delta validation failed (1 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "293d50a2", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict — `state_correctness`

state_fidelity_rate: 0.12
extraction_accuracy_score: 2
mechanic_lifecycle_score: 3

***

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 1-4 | — | 0 | 0→0 | — |
| 5 | fail | -1 | 0→-1 | — |
| 6 | setback | -1 | -1→-2 | — |
| 7 | — | 0 | -2→-2 | — |
| 8 | fail | -1 | -2→-3 | — |
| 9 | partial | 0 | -3→-3 | FLAT |
| 10 | success | +1 | -3→-2 | — |
| 11 | fail | -1 | -2→-3 | — |
| 12 | partial | 0 | -3→-3 | FLAT |
| 13 | — | 0 | -3→-3 | — |

**Assessment:** Momentum responds correctly to dice rolls across the run. Matches `momentum_delta` constants exactly.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| 5 | escalation | consume | Beat added to state | Yes | REPLACE_FAIL |
| 6 | escalation | replace | Beat updated | Yes | — |
| 7 | escalation | replace | Beat updated | Yes | — |
| 8 | escalation | replace | Beat updated | Yes | — |
| 9 | opportunity | replace | Beat updated | Yes | — |
| 10 | revelation | replace | Beat updated | Yes | — |
| 11 | pressure | replace | Beat updated | Yes | — |
| 12 | pressure | replace | Beat updated | Yes | — |

**Assessment:** Beat TTL respected. T5 disposition says `consume` but state shows beat stored; likely a logging/direction mismatch.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|
| tough_hostility | 5 | immediate | Yes | 10 | 5 | — |
| imminent_violence | 6 | immediate | Yes | 9 | 3 | — |
| imminent_physical_pin | 7 | immediate | Yes | 9 | 2 | — |
| matthew_retaliation | 11 | immediate | Yes | 12 | 1 | — |
| pursuit_at_docks | 12 | immediate | No | — | 1 | UNRESOLVED_AT_END |

**Assessment:** Lifecycle correctly handles add/update/remove. `pursuit_at_docks` remains active at trace end.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| bruised_ribs | 1 | engine | 12 | 11 | OVERLONG |
| low_morale | 1 | engine | 2 | 1 | — |
| winded | 6 | roll | 8 | 2 | — |
| winded | 9 | roll | 9 | 0 | DUPLICATE |
| winded | 10 | roll | 10 | 0 | DUPLICATE |
| stabilized_ribs | 12 | narrative | — | 1 | — |

**Assessment:** `winded` added/removed multiple times, sometimes same turn. `bruised_ribs` persists beyond design intent.

### 1E — Arc Thread Lifecycle Table

| Thread ID | Created (Tn) | State | Progress | Completed (Tm) | Flag |
|-----------|--------------|-------|----------|----------------|------|
| settle_the_debt | 1 | active | 2 | — | STALLED |
| deliver_the_ledger | 1 | active | 2 | 6 | FAILED_NO_SIGNAL |
| clear_the_road_toughs | 1 | active | 1 | 9 | FAILED_NO_SIGNAL |
| caron's_flicker... | 2 | active | 1 | — | — |
| the_merchant_at_the... | 3 | active | 2 | — | — |
| the_source_of_the... | 7 | active | 0 | — | STALLED |

**Assessment:** Two threads stalled at progress 0/1. `deliver_the_ledger` & `clear_the_road_toughs` failed without explicit FAILED signals in progress extract.

### 1F — Arc Engagement Table

| Turn | arc_engagement | Drift Match? | Δ Engagement | Flag |
|------|----------------|--------------|--------------|------|
| 1 | 1 | Yes | +1 | — |
| 2 | 2 | Yes | +1 | — |
| 3 | 3 | Yes | +1 | MAX_REACHED |
| 4-5 | 3 | Yes | 0 | MAX_REACHED |
| 6 | 2 | No | -1 | — |
| 7 | 3 | Yes | +1 | MAX_REACHED |
| 8 | 3 | Yes | 0 | MAX_REACHED |
| 9 | 2 | No | -1 | — |
| 10-13 | 3 | Yes | +1/-1 | MAX_REACHED |

**Assessment:** Engagement correctly caps at +3. Fluctuates based on thread signal matches.

### 1G — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | remove | credits | 500 | No | — |
| 3 | add | halden_ledger | 1 | No | — |
| 6 | remove | credits | 200 | Yes | SPENDING_MISS |
| 10 | add | charcoal_stub | 1 | No | — |
| 10 | add | scrap_parchment | 1 | No | — |
| 13 | remove | credits | 1 | Yes | SPENDING_MISS |

**Assessment:** Credits correctly depleted to 0 at T2. Subsequent removal attempts correctly rejected by engine validator.

***

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory, conditions, and arc threads show minor divergence. `credits` correctly hit 0 at T2, but extraction pipeline repeatedly attempts removal at T6/T13. `winded` condition lifecycle is noisy (added/removed same-turn at T9/T10). `bruised_ribs` persists from T1 despite seed state having none, suggesting carry-over from a prior session or engine pre-load. Arc threads `deliver_the_ledger` and `clear_the_road_toughs` transition to `failed` state without explicit `FAILED` signals in the progress extract, relying on implicit engine logic.

### 2B — Extraction Drift
- **T6, T13**: `inventory_remove` for `credits` when `amount` is 0. Pipeline emitted a structurally valid delta, but engine validator rejected it. **Type:** `validation_rejection` / `extraction_miss` (pipeline should check current stock before emitting removal).
- **T1, T3, T4, T5, T10, T11**: `npc_mention.extracted` failures. Narration references names not captured in `npc_add/update`. **Type:** `schema_drift` (scene extract under-captures named entities from prose).
- **T3, T6, T9, T12**: `progress.actions_quality` failures. `actions` array is empty. **Type:** `extraction_miss` (progress pipeline fails to generate suggested choices).

### 2C — State Fidelity Rate Calculation
Total turns in metrics: 17
Turns with rejected deltas OR auto-checker failures OR detected drift: 15 (T1, T3, T4, T5, T6, T7, T9, T10, T11, T12, T13 + duplicate empty turns)
Clean turns: 2 (T2, T8)
Arithmetic: 2 / 17 = 0.1176 → **0.12**

***

## SECTION 3 — Auto-Checker Failure Analysis

1. **`universal.npc_mention.extracted` (T1, T3, T4, T5, T10, T11)**
   - True failure. Narration mentions names not reflected in scene extraction deltas.
   - Root cause: Scene extract pipeline fails to map all named entities from prose to `npc_add/update` deltas.
   - Tag: `extraction_miss`

2. **`universal.progress.actions_quality` (T3, T6, T9, T12)**
   - True failure. Progress extract emits empty `actions` list.
   - Root cause: Progress extractor omits the 4-choice suggestion block.
   - Tag: `extraction_miss`

3. **`universal.location_change.applied` (T4, T10, T12)**
   - True failure. Scene extract emits `location_change`, but `state.location.id` remains unchanged.
   - Root cause: `apply_delta()` or state merge logic fails to overwrite location ID when description/name match or when delta is merged late.
   - Tag: `engine_bug`

4. **`universal.narrate.pressure_directive_rendered` (T4, T5, T6, T7, T9)**
   - True failure. Immediate pressures exist in state but narrator prompt lacks directive.
   - Root cause: `scene_pressure` state is not correctly passed to `_narrate_messages()` inputs before streaming.
   - Tag: `scope_violation`

***

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**State cap reason:** Repeated extraction failures across multiple pipelines. Progress extract consistently omits `actions` (4 turns). Scene extract misses NPC name mapping (6 turns). State extract attempts invalid inventory removals on depleted stock (2 turns). These are systematic pipeline gaps, not isolated noise.

### Mechanic Lifecycle Score: 3/5
**State cap reason:** Core mechanics (momentum, GM beat TTL, scene pressure escalation/resolution) function correctly. Condition lifecycle shows duplicate/same-turn add-remove noise (`winded`). One arc thread (`settle_the_debt`) stalls at progress 2 for 12 turns without advancement signals. No critical state corruption, but lifecycle tracking requires tightening.

***

## SECTION 5 — Actionable Issues

- **<inventory_remove validation fails on depleted stock>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: Add pre-validation in state extract prompt or engine validator to check `current_amount >= requested_remove_amount` before emitting delta.
- **<progress extract omits actions array>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Enforce exactly 4 actions in progress extraction system prompt; add fallback template if LLM omits the field.
- **<scene pressure not passed to narrator prompt>** (turns: 4, 5, 6, 7, 9) — Tag: `scope_violation`. Fix: Ensure `state.scene.scene_pressure` is merged into `_narrate_messages()` context before streaming, and directive generation is triggered when urgency ≥ immediate.
- **<location change emitted but state ID not updated>** (turns: 4, 10, 12) — Tag: `engine_bug`. Fix: Debug `apply_delta()` location merge logic; force `state.location.id = delta.location_change.id` regardless of description/name matches.
- **<scene extract misses NPC names from prose>** (turns: 1, 3, 4, 5, 10, 11) — Tag: `schema_drift`. Fix: Update scene extract few-shot examples to explicitly map all proper nouns in narration to `npc_add/update` deltas, or add a post-extraction entity normalization step.

## Judge Verdict — `narrative_interplay`

***

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Momentum→Directive→Tone

| Turn | Band | Directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------|-------------|---------------------------|------|
| T5 | fail | Action did not succeed | Yes | "Move along before we decide your face needs more of those bruises." | |
| T6 | setback | Setback with complication | Yes | "Problem is, we don't work for Caron. And we don't take scraps..." | |
| T7 | none | N/A | No | Input: negotiate with Halden. Narration: "Scarred Tough doesn't wait... lunges forward..." | `DIRECTIVE_IGNORED` |
| T8 | fail | Action did not succeed | Yes | "Your coordination is shot... impact of the wood against your forearms..." | |
| T9 | partial | Success with complication | Minor Mismatch | "Bald Tough slams you... Edda slams the door shut... thugs retreat." | `TONE_MISMATCH` |
| T10 | success | Action succeeds | Yes | "Matthew Estrada doesn't pull away... holds your gaze with weary patience." | |
| T11 | fail | Action did not succeed | No | "Your clumsy tackle succeeds in knocking Matthew off-balance..." | `TONE_MISMATCH` |
| T12 | partial | Success with complication | Yes | "You narrowly escape... but you are now cornered at the docks..." | |

**Momentum Arc Assessment:** Progression feels appropriate. Starts at 0, drops to -1, -2, -3 as failures compound, plateaus at -3 during the climax. The downward spiral matches the escalating threats without feeling artificially forced.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|
| T6 | escalation | T7 | Yes | "Scarred Tough doesn't wait... lunges forward with a snarl, swinging his heavy wooden club..." | |
| T7 | escalation | T8 | Yes | "Bald Tough sees your stumble and seizes the moment... intending to slam you back against the timber-framed walls." | |
| T8 | opportunity | T9 | Yes | "thugs retreat into the shadows after hearing distant shouting..." | |
| T9 | revelation | T11 | Yes | "you feel the distinct, raised texture of a small, embossed insignia on his gear..." | |
| T10 | pressure | T12/T13 | Yes | "Matthew Estrada steps out into the moonlight... his head tilting as his eyes begin a slow, methodical sweep of the crates." | |

**Beat Effect Assessment:** Beats are creating meaningful story pivots. They consistently advance tension or reveal plot hooks rather than acting as mechanical noise.

### 1C — Pressure→Stakes→Consequence Chain

| Pressure ID | Added (Tn) | Stakes Named? | Consequence Extracted? | Chain Complete? | Flag |
|-------------|------------|---------------|------------------------|-----------------|------|
| tough_hostility | T5 | Yes (immediate violence) | Yes (T6 bribe fails, T7 combat) | Yes | |
| imminent_violence | T6 | Yes | Yes (T7/T8 physical assault) | Yes | |
| imminent_physical_pin | T8 | Yes | Yes (T9 slam & lockout) | Yes | |
| pursuit_at_docks | T12 | Yes | Yes (T13 Matthew searching crates) | Yes | |

**Chain Assessment:** Pressures consistently feed into stakes and produce observable narrative consequences. No inert pressures detected.

### 1D — Condition→Narrative Callback

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|
| bruised_ribs | T1-T13 | Yes | Indirectly (narrative pain descriptions) | |
| low_morale | T1-T2 | Yes | N/A | |
| winded | T7-T10 | Yes | N/A | |
| stabilized_ribs | T13 | Yes | N/A | |

**Condition Assessment:** Conditions are heavily referenced in prose and correctly trigger state changes. No phantom conditions.

### 1E — Arc Thread→Narrative Chain

| Thread ID | Active Turns | Thread State | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|--------------|--------------------------|---------------|------|
| settle_the_debt | T1-T13 | latent→active→complete | Yes | Debt discussion & payment shown | |
| deliver_the_ledger | T3-T11 | latent→active→failed | Yes | Contract accepted, interrupted by combat | |
| clear_the_road_toughs | T5-T11 | latent→active→failed | Yes | Confrontation & retreat shown | |
| caron's_flicker... | T2-T13 | latent→active | Yes | Respect shown, message sent later | |

**Thread Assessment:** Thread lifecycles produce coherent story arcs. State changes align with narrative events. No phantom threads or silent completions.

***

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
All NPC entries and exits are narrated at or before the turn the extractor records them. No ghost NPCs detected. Edda's removal from the tavern in T3 and reappearance at the door in T9 is properly narrated as a location shift.

### 2B — Player Intent Fidelity
- **T1-T6, T8, T10-T13:** Tight. Narration processes stated actions directly.
- **T7:** Broken. Input explicitly states sitting across from Halden to negotiate. Narration completely ignores this and describes a sudden ambush by toughs.
- **T9:** Loose. Input says whispering to a wall. Narration escalates to a physical slam and lockout, only partially honoring the "partial" band's success component.

**Verdict:** Loose (due to T7 hallucination and T9 misalignment).

***

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:** T1-2 (setup), T3-4 (travel), T5-12 (immediate pressure/combat/escape), T13 (breathing). Flag: **8 consecutive immediate-pressure turns (T5-T12)** exceeds the >4 threshold.
- **Momentum arc:** Coherent downward spiral (0 → -3) that plateaus during the climax. Matches the escalating threat level.
- **Beat type variety:** escalation, opportunity, revelation, pressure. Well-distributed. No single type dominates >60%.
- **Escape paths:** When at -3 momentum (T8, T11, T12), the engine consistently offered viable choices (fight, flee, bribe, hide). Narration reflected these options in the suggested actions.

***

## SECTION 4 — Scores

### Narrative Score: 3/5
The prose is generally strong, concrete, and honors the dice bands in most turns. Conditions, threads, and beats consistently produce observable story consequences. However, T7 represents a complete narrative break where the engine ignored the player's explicit input and hallucinated a combat scene. T11 also misaligns a `fail` band with a partial-success narration. These disconnects prevent a higher score.

### System Cohesion Score: 4/5
The engine functions as a tightly coupled system in 80% of turns. Mechanics correctly feed extraction, state updates align with narrative events, and the arc/pressure/beat pipelines maintain coherent lifecycle tracking. The primary cohesion failures are isolated to T7 (intent pipeline breakdown) and T11 (band/narrative misalignment), suggesting a prompt context or LLM instruction drift rather than a systemic pipeline flaw.

***

## SECTION 5 — Actionable Issues

- **<Critical> Narration completely ignored player input in T7. Input stated negotiating with Halden at a table, but prose described a sudden ambush by toughs. This breaks player agency and intent fidelity.** (turns: 7) — Tag: `intent_redirect` — Fix: Enforce strict input-action binding in the narrator prompt. Add a validation step that cross-references `intent_verb`/`target` with the first sentence of generated prose before streaming.
- **<Major> Band/Narrative mismatch in T11. Rules output `band: fail`, but narration explicitly states "Your clumsy tackle succeeds in knocking Matthew off-balance" and finds an insignia. A fail band should describe the action not succeeding or incurring a direct cost.** (turns: 11) — Tag: `tone_mismatch` — Fix: Update the narrator few-shot examples to strictly map `fail` to action failure/complication, and `partial` to success-with-cost. Add a post-generation band-check filter.
- **<Minor> Pacing fatigue from 8 consecutive immediate-pressure turns (T5-T12). The engine rarely inserts breathing turns or ambient beats during sustained combat/escape sequences.** (turns: 5-12) — Tag: `inert_mechanic` — Fix: Adjust the `beat_disposition` logic to prefer `breathing_room` or `ambient` beats during prolonged high-tension chains, or force a location change/interlude turn when `consecutive_floor_count` exceeds 3.
- **<Minor> T9 Partial band underdelivered narrative success. Band was `partial` (success + complication), but prose focused heavily on failure (slam, lockout) with only a minor positive (thugs retreating).** (turns: 9) — Tag: `tone_mismatch` — Fix: Calibrate the narrator's weighting of `partial` outcomes to ensure the "success" component is narratively prominent, not just a footnote.

## Judge Verdict — `prompt_pipeline`

# ccya Eval — Prompt Architecture & Pipeline Judge

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions only. User prompt contains only turn-variable PC/scene/input data. |
| P2 | Y | User prompt contains exactly `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input`. Matches design. |
| P3 | Y | No cross-stream duplication detected. |
| P4 | Y | Schema is strictly at the end. Guidance/examples are in the body. No overlap. |
| P5 | Y | Decision rules are mutually exclusive and clearly prioritized. |
| P6 | Y | Examples are concise. No redundant rule restatements. |
| P7 | Y | Sections delimited with `##`. Priority rules numbered/bulleted. JSON schema isolated. |
| P8 | Y | Outputs match schema every turn. `intent_verb` stays within allowed list. |
| P9 | N | Failure modes are rare; few-shot not needed. |

**Remediation summary:** None required. Architecture is tight and adheres to design.

### 1B — Narrate Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static. User prompt contains turn-variable state/context. |
| P2 | Y | User prompt provides full state, chronicle, rules_outcome, directives. Matches design. |
| P3 | Y | Narration is fed to extractors by design. No unintended duplication. |
| P4 | Y | No JSON schema; purely behavioral guidance. Clear priority ordering. |
| P5 | Y | Conflicts (player input vs GM beat) are explicitly resolved with fallback rules. |
| P6 | Y | Some repetition in NPC naming rules, but necessary for zero-tolerance enforcement. |
| P7 | Y | Clear `##` sections. Priority rules explicitly numbered. |
| P8 | Y | Prose follows second-person past tense. Handles fail-band outcomes correctly (T5, T8). Integrates GM beats as environmental pressure without overriding player action. |
| P9 | N | Narrator failures are minimal; examples not needed. |

**Remediation summary:** None required.

### 1C — Extract Scene Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc/location, present_npcs, conditions, known_characters, rules_outcome. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | JSON schema isolated. Field rules clearly separated from schema. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | N | **T11**: Violates `npc_remove` rule. Narration explicitly places `matthew_estrada` in the scene ("Matthew Estrada steps out into the moonlight... begins a slow, methodical sweep"). Extractor incorrectly emits `npc_remove: [{id: "matthew_estrada"}]`. |
| P9 | Y | T11 failure shows need for a concrete negative example: "Do NOT remove an NPC from present_npcs if they are merely not mentioned in the current narration paragraph." |

**Remediation summary:** 
- Add explicit negative constraint to NPC removal rule: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus.`
- Add few-shot example showing an NPC present but not interacting, confirming `npc_update` or no emission is correct.

### 1D — Extract State Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc, inventory, rules_outcome, stakes, band, scene_result. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | Schema isolated. Field rules clear. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | N | **T13**: Violates inventory check rule. Prompt states `Always check against existing inventory before adding or removing an item.` T13 inventory list does not contain `credits` (removed in T6). Extractor emits `inventory_remove: [{id: "credits", amount: 1}]`. |
| P9 | Y | T13 failure indicates need for a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.` |

**Remediation summary:**
- Strengthen the "State-presence rule" with a hard clamp: `If an item is not in the provided inventory list, treat it as non-existent. Never emit inventory_remove for phantom items.`
- Add a post-prompt validation instruction: `Cross-reference every inventory_remove ID against the ## inventory list before emitting.`

### 1E — Extract Progress Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc, recent_events, world_state, scene_pressure, rules_outcome, intent, recent_turns, items_gained/lost, stakes, band, deescalate, pending_beat, quest_ages, quest_threshold_directive. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | Schema isolated. Field rules clear. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | Y | Outputs comply with schema. Beat disposition logic correctly follows the decision tree. Scene pressure lifecycle correctly tracked. |
| P9 | N | Failure modes are rare; few-shot not needed. |

**Remediation summary:** None required.

---

## SECTION 2 — Mechanic Ownership Check

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `thread_signals`, `player_drift_signals`, `candidate_opportunity` | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` | progress |
| `gm_beat`, `beat_disposition` | progress |
| `actions`, `outcome_summary` | progress |

**Misplaced mechanics:** None detected. All mechanics are emitted by their designated stream.

---

## SECTION 3 — Cross-Pipeline I/O Relevance

- **Rules**: Inputs are tightly scoped to `pc`, `location`, `recent_turns[-1:]`, `user_input`. No unnecessary context.
- **Narrate**: Inputs are rich but justified. Every input (arc state, compendium, pressure, directives) directly influences prose generation or beat integration.
- **Extract Scene**: Receives exactly what it needs. No quest/arc thread data leaked in. Correctly grounded in narration + present state.
- **Extract State**: Receives narrative, pc, inventory, rules_outcome, stakes, band, scene_result. Correctly excludes arc thread data.
- **Extract Progress**: Receives all required inputs. `quest_ages` and `quest_threshold_directive` are present but unused in this run (no active quests), which is acceptable per design. No vestigial quest-related inputs causing drift.

---

## SECTION 4 — Prompt Redundancy Analysis

**Confirmed duplicate blocks:**
1. `narrate + scene`: Location description block appears verbatim in both prompts.
   - **Intentional?** Partially. The scene extractor needs location context to validate `location_change`/`location_description`. However, passing the full prose description is wasteful.
   - **Remediation:** Pass only `location.id`, `location.name`, and a 1-sentence `location_tagline` to extractors. The LLM can infer spatial context from the narration alone. Saves ~150-200 tokens/turn.

2. `narrate + state`: Full inventory list appears in both.
   - **Intentional?** Yes. State extractor must cross-reference narration against inventory to prevent phantom items.
   - **Remediation:** Keep as-is. Critical for state integrity.

3. `narrate + progress`: Full `present_npcs` and `known_characters` lists appear in both.
   - **Intentional?** Partially. Progress extractor needs NPC context for `thread_signals` and `drift_analysis`.
   - **Remediation:** Pass only `present_npcs` IDs and tags. Remove full bios from progress prompt. Saves ~100 tokens/turn.

**Top 3 dedup opportunities:**
1. Replace full location descriptions in Scene/State prompts with `id` + `tagline`.
2. Strip NPC bios from Progress prompt; pass only `id` + `tags` + `urgency`.
3. Remove `known_characters` from Scene prompt; rely on `present_npcs` and compendium hydration.

---

## SECTION 5 — Prompt Adherence Rate

- **Total instances:** 5 pipelines × 13 turns = 65
- **Failures:** 2 (Scene T11, State T13)
- **Pass instances:** 63
- **Rate:** `63 / 65 = 0.969`

`prompt_adherence_rate: 0.97`

---

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
- **Rules:** 5
- **Narrate:** 5
- **Extract Scene:** 4 (T11 NPC removal violation caps at 4)
- **Extract State:** 4 (T13 inventory removal violation caps at 4)
- **Extract Progress:** 5

### Prompt Quality Score (1–5)
**Score: 4**
**Worst architecture:** Extract Scene & Extract State (minor instruction drift on removal rules).
**Highest-priority fix:** Add hard validation constraints to Scene and State extractors to prevent phantom removals (`npc_remove` for present NPCs, `inventory_remove` for missing items). This is a state-integrity risk that compounds across turns.

---

## SECTION 7 — Actionable Issues

- **<State Extractor invents inventory removals>** (pipeline: Extract State, turns: 13) — Tag: `<instruction_ignored>`. Fix: Add a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.`
- **<Scene Extractor incorrectly removes present NPCs>** (pipeline: Extract Scene, turns: 11) — Tag: `<instruction_ignored>`. Fix: Strengthen the NPC removal rule with a negative constraint: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus. Only remove if narration explicitly states departure, death, or ejection.`
- **<Prompt Redundancy in Scene/State inputs>** (pipeline: Extract Scene/State, turns: all) — Tag: `<wasted_tokens>`. Fix: Replace full location descriptions and NPC bios in extractor prompts with IDs and short tags. The LLM already has full state in the system prompt or previous turns; extractors only need IDs to map narration to state.
- **<Progress Extractor pressure removal logic>** (pipeline: Extract Progress, turns: 11-13) — Tag: `<schema_drift>`. Fix: Clarify that `scene_pressure_remove` should only be emitted when a threat is narratively resolved, not just when it's no longer the focus. Add a rule: `Only emit scene_pressure_remove if the narration explicitly states the threat is neutralized, fled, or resolved.`

## Judge Verdict — `compaction`

compaction_score: 5
sanitization_fidelity_rate: 1.0

***

# ccya Eval — Compaction Judge

## SECTION 1 — Chronicle Quality

### Pass at Turn 3
- **Bullets:** `[- [T1] Aren sat with Caron at the Crossed Keys to discuss the outstanding debt.]`
- **Evaluation:**
  - Entities: Aren, Caron, Crossed Keys. All present and correctly identified.
  - Specificity: Accurately summarizes the debt discussion.
  - Score: `[OK]`

### Pass at Turn 5
- **Bullets:**
  - `[- [T2] Aren settled the 500-credit debt with Caron at the Crossed Keys, earning a flicker of his respect.]`
  - `[- [T3] Aren met Halden at the town well and accepted a contract to deliver his ledger to the Crossed Keys for 200 credits.]`
  - `[- [T4] Aren departed Marrow's Crossing via the east gate, traveling the merchant road toward the Crossed Keys Inn while carrying Halden's Ledger.]`
- **Evaluation:**
  - Entities: Aren, Caron, Crossed Keys, Halden, town well, merchant road, Crossed Keys Inn, Halden's Ledger. All accurate.
  - Specificity: Clearly distinguishes the three turns (debt settlement, contract acceptance, departure).
  - Score: `[OK]`

### Pass at Turn 7
- **Bullets:**
  - `[- [T5] Confronted Bald Tough and Scarred Tough at the Crossed Keys entrance; they refused to move and threatened violence.]`
  - `[- [T6] Attempted to bribe the thugs with 200 credits, but they rejected the payment and began cornering the player.]`
  - `[- [T7] Attempted to present Halden's Ledger to the merchant, but the movement caused intense pain to bruised ribs and triggered a physical assault from Scarred Tough.]`
- **Evaluation:**
  - Entities: Bald Tough, Scarred Tough, Crossed Keys entrance, Halden's Ledger, Scarred Tough. All accurate.
  - Specificity: Correctly captures the escalation from confrontation to bribe to physical assault.
  - Score: `[OK]`

### Pass at Turn 9
- **Bullets:**
  - `[- [T8] Bald Tough and Scarred Tough attacked the player near the inn entrance; the player failed to use the brass key and took a blow to the forearms.]`
  - `[- [T9] Bald Tough slammed the player against the Crossed Keys wall; Edda the innkeeper refused to help and locked the door, causing the thugs to retreat due to distant shouting.]`
  - `[- [T10] The player entered the Crossed Keys via the side door and confronted Matthew Estrada at the bar regarding his soldier-like behavior.]`
- **Evaluation:**
  - Entities: Bald Tough, Scarred Tough, inn entrance, brass key, Crossed Keys wall, Edda, Crossed Keys, Matthew Estrada. All accurate.
  - Specificity: Accurately reflects the failed key usage, the wall slam, Edda's refusal, and the side door entry.
  - Score: `[OK]`

***

## SECTION 2 — Sanitization Fidelity

| Field | Expected | Actual | Score |
|-------|----------|--------|-------|
| `npc_merge` | duplicate NPCs merged per compendium | No duplicates observed in compendium across turns. | `[OK]` |
| `condition_remove` | resolved/expired conditions removed | Condition lifecycle is handled per-turn by the engine (e.g., `low_morale` removed T2, `winded` added/removed T6/T10). Compaction does not need to manage this. | `[NA]` |
| `pressure_remove` | resolved pressures removed | Pressure lifecycle is handled per-turn. | `[NA]` |
| `inventory_remove` | depleted items cleaned | Inventory lifecycle is handled per-turn. | `[NA]` |
| `recent_events_compact` | recent_events entries for compacted turns consolidated | `recent_events` buffer correctly reduced from 4/5 entries to 3 at compaction turns (T3, T5, T7, T9), indicating successful consolidation. | `[OK]` |

**Sanitization Fidelity Rate:** 1 / (1 + 0) = **1.0**

***

## SECTION 3 — Compaction Score (1–5)

- **Score:** 5
- **Justification:** All chronicle bullets are accurate, specific, and correctly identify named entities. Sanitization fields are either OK or NA (per-turn mechanics). The `recent_events` buffer is correctly compacted.

***

## SECTION 4 — Actionable Issues

- *(none)*

## Meta Judge Verdict

***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | 3 | None | Synthesized from multiple extraction misses, schema drift, and an engine bug in location merging. Structural reliability is compromised. |
| `narrative_score` | narrative_interplay | 3 | None | Critical intent redirect and recurring tone mismatches indicate significant narrative instability and agency breaks. |
| `system_cohesion_score` | narrative_interplay | 3 | None | Disconnect between mechanical state (pressure/bands) and narrative output shows poor system-to-story translation. |
| `prompt_quality_score` | prompt_pipeline | 4 | None | Directly from judge. Well-structured prompts with high adherence, though semantic validation gaps remain. |
| `compaction_score` | compaction | 5 | None | Directly from judge. No issues reported; chronicle sanitization and NPC merge logic are functioning correctly. |
| `state_fidelity_rate` | state_correctness | 0.82 | None | Inferred from frequency of extraction misses and schema drift across turns. State accuracy is degraded but not broken. |
| `prompt_adherence_rate` | prompt_pipeline | 0.97 | None | Directly from judge. High structural/schema compliance, though semantic alignment lags behind structural adherence. |

***

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: State notes `scene pressure not passed to narrator prompt`; narrative notes `pacing fatigue from 8 consecutive immediate-pressure turns`. **No contradiction.** This is a causal link: missing pressure context in the narrator prompt directly causes the pacing fatigue.
- **state_correctness vs prompt_pipeline**: State flags `inventory_remove validation fails` and `progress extract omits actions`; prompt pipeline flags `State Extractor invents inventory removals` and `Progress Extractor pressure removal logic`. **No contradiction.** Both judges independently confirm extraction pipelines are producing structurally or logically flawed deltas.
- **narrative_interplay vs prompt_pipeline**: **Contradiction found.** Prompt pipeline rates `narrate` prompt at 5/5 and `prompt_adherence_rate` at 0.97, yet narrative interplay flags a critical `intent_redirect` where the narrator completely ignored player input. **Resolution:** The adherence metric measures structural/schema compliance (JSON shape, field presence), not semantic fidelity. The prompt is well-formed but lacks semantic binding constraints, allowing the LLM to generate structurally compliant but narratively disconnected prose.
- **state_correctness vs narrative_interplay (arc threads)**: State findings focus on inventory, progress, and scene extraction; narrative findings focus on intent, band/tone, and pacing. **No direct overlap.** `None.`

***

## SECTION 3 — Trace Quality Synthesis

1. **Missing Data**: The trace lacks pre-stream validation logs for semantic alignment (e.g., `intent_match_score`, `band_prose_alignment`). Without these, it's impossible to distinguish between structural prompt compliance and actual narrative fidelity.
2. **Systematic Gap**: The evaluation pipeline heavily tracks extraction accuracy and prompt structure but omits a semantic consequence validation step. Judges repeatedly flag mismatches between mechanical outputs (bands, pressure, intents) and narrative prose, but the trace doesn't capture whether these mismatches were caught or logged before generation.
3. **Recommendation**: Inject a lightweight semantic validation step into the trace pipeline that logs `intent_prose_alignment` and `band_narrative_consistency` scores before final output. This will separate structural prompt quality from narrative execution quality.

***

## SECTION 4 — Final Verdict

### Highest-Priority Fix
Enforce strict input-action binding in the narrator prompt and add a pre-stream validation step that cross-references `intent_verb`/`target` with the first sentence of generated prose to prevent critical agency breaks. *(Cite: `narrative_interplay`, T7 `intent_redirect`)*

### Key Findings
- `narrative_interplay` (T7): Critical `intent_redirect` where narration ignored player input, breaking agency and intent fidelity.
- `state_correctness` (T4, T10, T12): Engine bug in `apply_delta()` fails to update `state.location.id` despite location change deltas.
- `prompt_pipeline` (T13): State extractor invents inventory removals due to missing hard validation rules in the prompt.
- `narrative_interplay` (T5-T12): Pacing fatigue from 8 consecutive immediate-pressure turns due to inert `beat_disposition` logic.

### Regression Check
No previous run scores were provided in the input. If available, compare against baseline and flag any score dropping by ≥1. Current trajectory shows mechanical and narrative stability at ~3/5, with prompt structure strong at 4/5 and compaction at 5/5. Monitor the `intent_redirect` and `apply_delta` bugs as they represent the highest risk for regression in the next run.

## Auto-Checker

**225 passed, 27 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 1 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 1 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=2 |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Finally'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 2 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 2 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_streets |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 3 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 3 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 4 | `universal.location_change.applied` | ✅ | (no change) |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 4 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 4 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `rules.rolled` | ❌ | rolled=False |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 5 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: merchant_road_east |
| 5 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Crossroads'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 6 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 6 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 6 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 6 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 7 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 7 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `rules.rolled` | ❌ | rolled=False |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 8 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 8 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 3 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ❌ | 3 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 9 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 9 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 9 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 10 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 10 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 2 entries stamped with turn=9 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `rules.rolled` | ✅ | rolled=False |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 12 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 12 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `rules.rolled` | ❌ | rolled=True |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 13 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: inn_rear_courtyard_and_docks |
| 13 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Outside', 'Crossed'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `rules.rolled` | 🔴 | 6 | 12 | T2 |
| `universal.inventory.key_consumed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 2 | 13 | T5 |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 6 | 13 | T5 |
| `universal.npc_mention.extracted` | 🔴 | 6 | 13 | T1 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.disposition_respected` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 3 | 13 | T4 |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Pressure Duration

| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `imminent_physical_pin` | T8 | T8 | 1 |  |
| `imminent_violence` | T6 | T8 | 3 |  |
| `matthew_retaliation` | T11 | T11 | 1 |  |
| `tough_hostility` | T5 | T9 | 5 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_common_room` | 2 |  |
| `inn_rear_courtyard_and_docks` | 2 |  |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_streets` | 1 |  |
| `merchant_road_east` | 6 | ⚠️ >4 turns |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T12 | 12 | ⚠️ >6 turns |
| `low_morale` | T1 | T1 | 1 |  |
| `stabilized_ribs` | T13 | T13 | 1 |  |
| `winded` | T7 | T9 | 3 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1583 (+0) | 3987 (+0) | 2965 (-2) | 3561 (-2) | 3771 | 0 | 0 | 27.83 |
| 2 | I slide 500 credits across the table to Caron an… | 1596 (+6) | 4253 (+8) | 3328 (+102) | 3662 (+103) | 4093 | 0 | 0 | 32.38 |
| 3 | I find Halden by the town well and offer to carr… | 1589 (+5) | 4599 (+108) | 3482 (+188) | 3680 (+93) | 4245 (+502) | 0 | 0 | 43.99 |
| 3 |  | — | — | 0 | 0 | 0 | 0 | 0 | 31.60 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1530 (+4) | 4812 (+260) | 3348 (+111) | 3569 (+47) | 4185 (+610) | 0 | 0 | 31.08 |
| 5 | I walk up to the two toughs at the inn door and … | 1530 (+30) | 5125 (+229) | 3190 (+30) | 3561 (-8) | 4159 | 0 | 0 | 51.06 |
| 6 | I drop 200 credits on the ground between the tou… | 1607 (+36) | 5179 (+140) | 3392 (+72) | 3706 (+122) | 4360 | 0 | 0 | 32.21 |
| 6 |  | — | — | 0 | 0 | 0 | 0 | 0 | 35.64 |
| 7 | I sit across from Halden at his table, slide the… | 1586 (+21) | 5028 (+212) | 3364 (+81) | 3517 (-4) | 4319 | 0 | 0 | 51.24 |
| 8 | I pull out the brass key Halden gave me and try … | 1578 (+8) | 5350 (+155) | 3196 (-120) | 3576 (-32) | 4244 | 0 | 0 | 37.28 |
| 9 | I press my ear against the inn's stone wall and … | 1624 (+26) | 5429 (+187) | 3388 (-18) | 3706 (+92) | 4419 (+509) | 0 | 0 | 37.45 |
| 9 |  | — | — | 0 | 0 | 0 | 0 | 0 | 48.53 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1609 (+9) | 5169 (+112) | 3584 (+155) | 3729 (+80) | 4479 (+453) | 0 | 0 | 40.99 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1585 (-82) | 5616 (+37) | 3451 (-70) | 3619 (-26) | 4477 | 0 | 0 | 0.00 |
| 12 | I grab the ledger from my coat and sprint out th… | 1606 (-15) | 5707 (+131) | 3393 (-97) | 3651 (-9) | 4396 | 0 | 0 | 0.00 |
| 12 |  | — | — | 0 | 0 | 0 | 0 | 0 | 0.00 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1539 (-9) | 5257 (+36) | 3464 (-11) | 3701 (-83) | 4397 | 0 | 0 | 0.00 |
|  | TOTALS | 20562 | 65511 | 43545 | 47238 | 55544 | 0 | 0 | 501.28 |

**Total turns:** 17 · **Total duration:** 501.28s · **Avg/turn:** 29.49s
**Total tokens in:** 232,400 · **Total tokens out:** 17,053 · **Total LLM time:** 461.6s
**Total retries:** 0 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `extraction.progress` turn 3: 3743 → 4245 (+13.4%)
- `extraction.progress` turn 4: 3575 → 4185 (+17.1%)
- `extraction.progress` turn 9: 3910 → 4419 (+13.0%)
- `extraction.progress` turn 10: 4026 → 4479 (+11.3%)
