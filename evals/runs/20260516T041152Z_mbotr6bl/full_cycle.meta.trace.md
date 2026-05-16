# Domain Judge Scores

```yaml
prompt_pipeline:
  pipeline_scores:
    extract_progress: 5
    extract_scene: 4
    extract_state: 4
    narrate: 5
    rules: 5
  prompt_adherence_rate: 0.97
  prompt_quality_score: 4

```

# Judge Summaries

## state_correctness

### Actionable Issues

- **<inventory_remove validation fails on depleted stock>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: Add pre-validation in state extract prompt or engine validator to check `current_amount >= requested_remove_amount` before emitting delta.
- **<progress extract omits actions array>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Enforce exactly 4 actions in progress extraction system prompt; add fallback template if LLM omits the field.
- **<scene pressure not passed to narrator prompt>** (turns: 4, 5, 6, 7, 9) — Tag: `scope_violation`. Fix: Ensure `state.scene.scene_pressure` is merged into `_narrate_messages()` context before streaming, and directive generation is triggered when urgency ≥ immediate.
- **<location change emitted but state ID not updated>** (turns: 4, 10, 12) — Tag: `engine_bug`. Fix: Debug `apply_delta()` location merge logic; force `state.location.id = delta.location_change.id` regardless of description/name matches.
- **<scene extract misses NPC names from prose>** (turns: 1, 3, 4, 5, 10, 11) — Tag: `schema_drift`. Fix: Update scene extract few-shot examples to explicitly map all proper nouns in narration to `npc_add/update` deltas, or add a post-extraction entity normalization step.

### Issues

- **<inventory_remove validation fails on depleted stock>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: Add pre-validation in state extract prompt or engine validator to check `current_amount >= requested_remove_amount` before emitting delta.
- **<progress extract omits actions array>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Enforce exactly 4 actions in progress extraction system prompt; add fallback template if LLM omits the field.
- **<scene pressure not passed to narrator prompt>** (turns: 4, 5, 6, 7, 9) — Tag: `scope_violation`. Fix: Ensure `state.scene.scene_pressure` is merged into `_narrate_messages()` context before streaming, and directive generation is triggered when urgency ≥ immediate.
- **<location change emitted but state ID not updated>** (turns: 4, 10, 12) — Tag: `engine_bug`. Fix: Debug `apply_delta()` location merge logic; force `state.location.id = delta.location_change.id` regardless of description/name matches.
- **<scene extract misses NPC names from prose>** (turns: 1, 3, 4, 5, 10, 11) — Tag: `schema_drift`. Fix: Update scene extract few-shot examples to explicitly map all proper nouns in narration to `npc_add/update` deltas, or add a post-extraction entity normalization step.


## narrative_interplay

### Actionable Issues

- **<Critical> Narration completely ignored player input in T7. Input stated negotiating with Halden at a table, but prose described a sudden ambush by toughs. This breaks player agency and intent fidelity.** (turns: 7) — Tag: `intent_redirect` — Fix: Enforce strict input-action binding in the narrator prompt. Add a validation step that cross-references `intent_verb`/`target` with the first sentence of generated prose before streaming.
- **<Major> Band/Narrative mismatch in T11. Rules output `band: fail`, but narration explicitly states "Your clumsy tackle succeeds in knocking Matthew off-balance" and finds an insignia. A fail band should describe the action not succeeding or incurring a direct cost.** (turns: 11) — Tag: `tone_mismatch` — Fix: Update the narrator few-shot examples to strictly map `fail` to action failure/complication, and `partial` to success-with-cost. Add a post-generation band-check filter.
- **<Minor> Pacing fatigue from 8 consecutive immediate-pressure turns (T5-T12). The engine rarely inserts breathing turns or ambient beats during sustained combat/escape sequences.** (turns: 5-12) — Tag: `inert_mechanic` — Fix: Adjust the `beat_disposition` logic to prefer `breathing_room` or `ambient` beats during prolonged high-tension chains, or force a location change/interlude turn when `consecutive_floor_count` exceeds 3.
- **<Minor> T9 Partial band underdelivered narrative success. Band was `partial` (success + complication), but prose focused heavily on failure (slam, lockout) with only a minor positive (thugs retreating).** (turns: 9) — Tag: `tone_mismatch` — Fix: Calibrate the narrator's weighting of `partial` outcomes to ensure the "success" component is narratively prominent, not just a footnote.

### Issues

- **<Critical> Narration completely ignored player input in T7. Input stated negotiating with Halden at a table, but prose described a sudden ambush by toughs. This breaks player agency and intent fidelity.** (turns: 7) — Tag: `intent_redirect` — Fix: Enforce strict input-action binding in the narrator prompt. Add a validation step that cross-references `intent_verb`/`target` with the first sentence of generated prose before streaming.
- **<Major> Band/Narrative mismatch in T11. Rules output `band: fail`, but narration explicitly states "Your clumsy tackle succeeds in knocking Matthew off-balance" and finds an insignia. A fail band should describe the action not succeeding or incurring a direct cost.** (turns: 11) — Tag: `tone_mismatch` — Fix: Update the narrator few-shot examples to strictly map `fail` to action failure/complication, and `partial` to success-with-cost. Add a post-generation band-check filter.
- **<Minor> Pacing fatigue from 8 consecutive immediate-pressure turns (T5-T12). The engine rarely inserts breathing turns or ambient beats during sustained combat/escape sequences.** (turns: 5-12) — Tag: `inert_mechanic` — Fix: Adjust the `beat_disposition` logic to prefer `breathing_room` or `ambient` beats during prolonged high-tension chains, or force a location change/interlude turn when `consecutive_floor_count` exceeds 3.
- **<Minor> T9 Partial band underdelivered narrative success. Band was `partial` (success + complication), but prose focused heavily on failure (slam, lockout) with only a minor positive (thugs retreating).** (turns: 9) — Tag: `tone_mismatch` — Fix: Calibrate the narrator's weighting of `partial` outcomes to ensure the "success" component is narratively prominent, not just a footnote.


## prompt_pipeline

### Actionable Issues

- **<State Extractor invents inventory removals>** (pipeline: Extract State, turns: 13) — Tag: `<instruction_ignored>`. Fix: Add a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.`
- **<Scene Extractor incorrectly removes present NPCs>** (pipeline: Extract Scene, turns: 11) — Tag: `<instruction_ignored>`. Fix: Strengthen the NPC removal rule with a negative constraint: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus. Only remove if narration explicitly states departure, death, or ejection.`
- **<Prompt Redundancy in Scene/State inputs>** (pipeline: Extract Scene/State, turns: all) — Tag: `<wasted_tokens>`. Fix: Replace full location descriptions and NPC bios in extractor prompts with IDs and short tags. The LLM already has full state in the system prompt or previous turns; extractors only need IDs to map narration to state.
- **<Progress Extractor pressure removal logic>** (pipeline: Extract Progress, turns: 11-13) — Tag: `<schema_drift>`. Fix: Clarify that `scene_pressure_remove` should only be emitted when a threat is narratively resolved, not just when it's no longer the focus. Add a rule: `Only emit scene_pressure_remove if the narration explicitly states the threat is neutralized, fled, or resolved.`

### Issues

- **<State Extractor invents inventory removals>** (pipeline: Extract State, turns: 13) — Tag: `<instruction_ignored>`. Fix: Add a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.`
- **<Scene Extractor incorrectly removes present NPCs>** (pipeline: Extract Scene, turns: 11) — Tag: `<instruction_ignored>`. Fix: Strengthen the NPC removal rule with a negative constraint: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus. Only remove if narration explicitly states departure, death, or ejection.`
- **<Prompt Redundancy in Scene/State inputs>** (pipeline: Extract Scene/State, turns: all) — Tag: `<wasted_tokens>`. Fix: Replace full location descriptions and NPC bios in extractor prompts with IDs and short tags. The LLM already has full state in the system prompt or previous turns; extractors only need IDs to map narration to state.
- **<Progress Extractor pressure removal logic>** (pipeline: Extract Progress, turns: 11-13) — Tag: `<schema_drift>`. Fix: Clarify that `scene_pressure_remove` should only be emitted when a threat is narratively resolved, not just when it's no longer the focus. Add a rule: `Only emit scene_pressure_remove if the narration explicitly states the threat is neutralized, fled, or resolved.`


## compaction

### Actionable Issues

- *(none)*

### Issues

- *(none)*

