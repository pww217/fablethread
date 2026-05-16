# Domain Judge Scores

```yaml
prompt_pipeline:
  pipeline_scores:
    extract_progress: 4
    extract_scene: 4
    extract_state: 3
    narrate: 5
    rules: 5
  prompt_adherence_rate: 0.94
  prompt_quality_score: 4

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **<Description>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: The State Extract pipeline is emitting `inventory_remove` for items that no longer exist (credits). The extractor must check the current state inventory before emitting removal deltas, or the validator must provide better feedback to the extractor to prevent this loop.
- **<Description>** (turns: 10, 12) — Tag: `schema_drift`. Fix: Location changes are being emitted by the extractor but not applied to the state. Investigate the `_apply_delta` logic for location changes and the validation rules.

**Major**
- **<Description>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: The Progress Extract pipeline is failing to generate the required 4 suggested actions. Update the prompt to enforce this output.
- **<Description>** (turns: 3, 4, 5, 6, 7, 9, 10) — Tag: `wrong_pipeline`. Fix: The Narrate pipeline is not receiving the pressure directive from the Scene Pressure mechanic. Ensure the `narrate_user.j2` template includes the pressure directive variable.
- **<Description>** (turns: 11-13) — Tag: `scope_violation`. Fix: Arc engagement is stuck at -1. The `tick_arc` logic is not recovering engagement after the player's actions (T11-T13) should have provided some drift signals. Review the engagement scoring logic.

**Minor**
- **<Description>** (turns: 3, 4, 6, 7, 8, 9, 10, 11, 12, 13) — Tag: `checker_noise`. Fix: Update the `npc_mention.extracted` checker to ignore common nouns and location names (e.g., "Crossed", "Leather") that are not NPC names.
- **<Description>** (turns: 5-13) — Tag: `stale_context`. Fix: The `bruised_ribs` condition is never removed despite the player's actions. Either the condition TTL is too long or the narrative never resolves it. Consider adding a mechanic to auto-resolve conditions after a certain number of turns or upon specific actions.

### Issues

**Critical**
- **<Description>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: The State Extract pipeline is emitting `inventory_remove` for items that no longer exist (credits). The extractor must check the current state inventory before emitting removal deltas, or the validator must provide better feedback to the extractor to prevent this loop.
- **<Description>** (turns: 10, 12) — Tag: `schema_drift`. Fix: Location changes are being emitted by the extractor but not applied to the state. Investigate the `_apply_delta` logic for location changes and the validation rules.

**Major**
- **<Description>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: The Progress Extract pipeline is failing to generate the required 4 suggested actions. Update the prompt to enforce this output.
- **<Description>** (turns: 3, 4, 5, 6, 7, 9, 10) — Tag: `wrong_pipeline`. Fix: The Narrate pipeline is not receiving the pressure directive from the Scene Pressure mechanic. Ensure the `narrate_user.j2` template includes the pressure directive variable.
- **<Description>** (turns: 11-13) — Tag: `scope_violation`. Fix: Arc engagement is stuck at -1. The `tick_arc` logic is not recovering engagement after the player's actions (T11-T13) should have provided some drift signals. Review the engagement scoring logic.

**Minor**
- **<Description>** (turns: 3, 4, 6, 7, 8, 9, 10, 11, 12, 13) — Tag: `checker_noise`. Fix: Update the `npc_mention.extracted` checker to ignore common nouns and location names (e.g., "Crossed", "Leather") that are not NPC names.
- **<Description>** (turns: 5-13) — Tag: `stale_context`. Fix: The `bruised_ribs` condition is never removed despite the player's actions. Either the condition TTL is too long or the narrative never resolves it. Consider adding a mechanic to auto-resolve conditions after a certain number of turns or upon specific actions.


## narrative_interplay

### Actionable Issues

- **Phantom Arc Threads** (turns: 4-8) — Tag: `phantom_thread`. Fix: Ensure the progress extractor's thread signals are reflected in the narration. If a thread is marked active, the narrator should reference the mystery or opportunity it represents. If marked failed, the narrator should show the failure.
- **Phantom Conditions** (turns: 1-10, 10-11) — Tag: `phantom_thread`. Fix: Either remove conditions that are not narratively relevant or ensure the narrator references them. `low_morale` and `exhausted` should either be removed or described in the prose.
- **Inert Scene Pressures** (turns: 4-9) — Tag: `inert_mechanic`. Fix: Scene pressures should create observable story consequences. If `inn_entrance_blockade` is active, the narration should reflect the difficulty of passing or the threat of the figures.
- **Late Pressure Removal** (turns: 4-9) — Tag: `state_mismatch`. Fix: Remove pressures when the narration shows the threat is resolved, not several turns later.

### Issues

- **Phantom Arc Threads** (turns: 4-8) — Tag: `phantom_thread`. Fix: Ensure the progress extractor's thread signals are reflected in the narration. If a thread is marked active, the narrator should reference the mystery or opportunity it represents. If marked failed, the narrator should show the failure.
- **Phantom Conditions** (turns: 1-10, 10-11) — Tag: `phantom_thread`. Fix: Either remove conditions that are not narratively relevant or ensure the narrator references them. `low_morale` and `exhausted` should either be removed or described in the prose.
- **Inert Scene Pressures** (turns: 4-9) — Tag: `inert_mechanic`. Fix: Scene pressures should create observable story consequences. If `inn_entrance_blockade` is active, the narration should reflect the difficulty of passing or the threat of the figures.
- **Late Pressure Removal** (turns: 4-9) — Tag: `state_mismatch`. Fix: Remove pressures when the narration shows the threat is resolved, not several turns later.


## prompt_pipeline

### Actionable Issues

- **<Extract State fails to validate inventory IDs before removal>** (pipeline: extract_state, turns: 6, 13) — Tag: `<instruction_ignored>`. Fix: Add a "Zero-Tolerance" rule: "Before emitting `inventory_remove`, verify the ID exists in the `## inventory` section. If it does not exist, DO NOT emit the remove."
- **<Extract Scene removes NPCs incorrectly when they are just out of view>** (pipeline: extract_scene, turns: 10, 13) — Tag: `<bad_prompt>`. Fix: Clarify `npc_remove` rule: "Emit `npc_remove` ONLY if the NPC physically leaves the location, dies, or is explicitly dismissed. Do NOT remove NPCs just because the player moved to a different area within the same location or the NPC is no longer the focus."
- **<Extract Progress emits invalid pressure IDs>** (pipeline: extract_progress, turns: 13) — Tag: `<bad_prompt>`. Fix: Add rule: "Only emit IDs in `scene_pressure_remove` that are present in the `## Current Pressures` list. Do not invent or guess IDs."
- **<Narration directive ignored by Progress Extractor>** (pipeline: extract_progress, turns: 5-13) — Tag: `<wasted_tokens>`. Fix: Add instruction to the Progress Extractor prompt: "Use the `narration_directive` to inform your `gm_beat` and `scene_pressure` decisions. For example, if the directive is 'Pressure', consider adding a `scene_pressure_add` or `gm_beat` of type 'pressure'."

### Issues

- **<Extract State fails to validate inventory IDs before removal>** (pipeline: extract_state, turns: 6, 13) — Tag: `<instruction_ignored>`. Fix: Add a "Zero-Tolerance" rule: "Before emitting `inventory_remove`, verify the ID exists in the `## inventory` section. If it does not exist, DO NOT emit the remove."
- **<Extract Scene removes NPCs incorrectly when they are just out of view>** (pipeline: extract_scene, turns: 10, 13) — Tag: `<bad_prompt>`. Fix: Clarify `npc_remove` rule: "Emit `npc_remove` ONLY if the NPC physically leaves the location, dies, or is explicitly dismissed. Do NOT remove NPCs just because the player moved to a different area within the same location or the NPC is no longer the focus."
- **<Extract Progress emits invalid pressure IDs>** (pipeline: extract_progress, turns: 13) — Tag: `<bad_prompt>`. Fix: Add rule: "Only emit IDs in `scene_pressure_remove` that are present in the `## Current Pressures` list. Do not invent or guess IDs."
- **<Narration directive ignored by Progress Extractor>** (pipeline: extract_progress, turns: 5-13) — Tag: `<wasted_tokens>`. Fix: Add instruction to the Progress Extractor prompt: "Use the `narration_directive` to inform your `gm_beat` and `scene_pressure` decisions. For example, if the directive is 'Pressure', consider adding a `scene_pressure_add` or `gm_beat` of type 'pressure'."


## compaction

### Actionable Issues

- **<Compaction at Turn 9 includes Turn 10 data>** (turn: 9) — Tag: `<sanitization_miss>`. Fix: Ensure the compactor only processes turns up to the current compaction turn (T9) and does not include future turns (T10) in the chronicle or recent_events.

### Issues

- **<Compaction at Turn 9 includes Turn 10 data>** (turn: 9) — Tag: `<sanitization_miss>`. Fix: Ensure the compactor only processes turns up to the current compaction turn (T9) and does not include future turns (T10) in the chronicle or recent_events.

