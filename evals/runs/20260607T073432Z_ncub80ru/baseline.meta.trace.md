# Domain Judge Scores

```yaml
narrative_interplay:
  pipeline_scores: {}
prompt_pipeline:
  pipeline_scores: {}
state_correctness:
  extraction_accuracy_score: 2
  mechanic_lifecycle_score: 1
  pipeline_scores: {}
  state_fidelity_rate: 0.385

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **Location changes silently dropped from canonical state.** (Turns: 4, 8, 12) — Tag: `engine_bug`. Fix: Debug `_apply_delta` or validation pipeline to ensure `location_change` deltas are not being rejected by a false-positive constraint check. Verify that the extracted location ID matches an existing world location before applying.
- **Momentum delta sign inversion.** (Turns: 4, 5, 8, 9) — Tag: `engine_bug`. Fix: Audit `_apply_momentum_delta` in the ruling engine. The band-to-delta mapping is being applied with incorrect signs or reading from stale state snapshots during mutation.
- **GM Beat floor relief injection failure.** (Turns: 10 first block) — Tag: `engine_bug`. Fix: Ensure `_check_floor_relief` runs *after* Storytell beat assignment and correctly overrides pressure-type beats when `beat_locked=True`.

**Major**
- **Condition IDs not recognized by engine mod lookup.** (Turns: 2-13) — Tag: `schema_drift`. Fix: Either expand the engine's condition config to accept dynamic labels, or add validation in State Extract to restrict conditions to pre-defined IDs. Alternatively, make unknown conditions default to a generic "minor" modifier rather than orphaning them.
- **Consecutive pressure counter desynchronization.** (Turns: 1, 3, 4, 5, 7, 9, 10, 11) — Tag: `engine_bug`. Fix: Verify that the post-extraction pipeline correctly updates `meta.consecutive_pressure_turns` based on the *final* beat type (post-floor-relief), not just the storyteller's raw output.
- **Thread resolution failures.** (Turns: 9, 11) — Tag: `engine_bug`. Fix: Ensure `_apply_thread_resolutions` correctly moves threads to `completed_threads` and removes them from active list. The re-appearance of resolved threads suggests a state rollback or incomplete merge in the arc director.

**Minor**
- **Empty actions on blank input turns.** (Turns: 3, 5, 10) — Tag: `extraction_miss`. Fix: Update Storytell system prompt to explicitly instruct emitting placeholder/generic actions when narrative context is null/empty, rather than an empty array.

### Issues

**Critical**
- **Location changes silently dropped from canonical state.** (Turns: 4, 8, 12) — Tag: `engine_bug`. Fix: Debug `_apply_delta` or validation pipeline to ensure `location_change` deltas are not being rejected by a false-positive constraint check. Verify that the extracted location ID matches an existing world location before applying.
- **Momentum delta sign inversion.** (Turns: 4, 5, 8, 9) — Tag: `engine_bug`. Fix: Audit `_apply_momentum_delta` in the ruling engine. The band-to-delta mapping is being applied with incorrect signs or reading from stale state snapshots during mutation.
- **GM Beat floor relief injection failure.** (Turns: 10 first block) — Tag: `engine_bug`. Fix: Ensure `_check_floor_relief` runs *after* Storytell beat assignment and correctly overrides pressure-type beats when `beat_locked=True`.

**Major**
- **Condition IDs not recognized by engine mod lookup.** (Turns: 2-13) — Tag: `schema_drift`. Fix: Either expand the engine's condition config to accept dynamic labels, or add validation in State Extract to restrict conditions to pre-defined IDs. Alternatively, make unknown conditions default to a generic "minor" modifier rather than orphaning them.
- **Consecutive pressure counter desynchronization.** (Turns: 1, 3, 4, 5, 7, 9, 10, 11) — Tag: `engine_bug`. Fix: Verify that the post-extraction pipeline correctly updates `meta.consecutive_pressure_turns` based on the *final* beat type (post-floor-relief), not just the storyteller's raw output.
- **Thread resolution failures.** (Turns: 9, 11) — Tag: `engine_bug`. Fix: Ensure `_apply_thread_resolutions` correctly moves threads to `completed_threads` and removes them from active list. The re-appearance of resolved threads suggests a state rollback or incomplete merge in the arc director.

**Minor**
- **Empty actions on blank input turns.** (Turns: 3, 5, 10) — Tag: `extraction_miss`. Fix: Update Storytell system prompt to explicitly instruct emitting placeholder/generic actions when narrative context is null/empty, rather than an empty array.


## narrative_interplay

### Actionable Issues

- **Phantom Condition: heat_exhaustion** (Turns: T1-T2) — Tag: `<phantom_thread>` The condition was added but never referenced in prose or affected rolls. Fix: Ensure narrator references environmental conditions when they are active, or remove them if purely mechanical.
- **Directive-Narrative Disconnect: Pressure Directive on Calm Turns** (Turns: T4, T5, T12) — Tag: `<tone_mismatch>` The engine computed "Pressure" directives based on beat history, but the narration was informational/calm. Fix: Review `_compute_pacing_context` logic to ensure it resets when narrative velocity is low or de-escalation occurs naturally, rather than relying solely on consecutive pressure beats which may be misclassified by Storytell.
- **Beat Type Mismatch: Revelation as Pressure** (Turns: T4) — Tag: `<type_mismatch>` A "revelation" beat was generated under a "Pressure" directive context but failed to create narrative tension, acting instead as flat info delivery. Fix: Align Storytell prompt guidance so that "Revelation" beats are reserved for high-tension or plot-twist moments, not routine information gathering.
- **Inert Thread: deliver_the_ledger** (Turns: T1-T13) — Tag: `<inert_mechanic>` This thread was active and updated but never influenced narration or player choices directly. The Harker investigation completely overshadowed it. Fix: Either resolve this thread early when the PC shifts focus to Harker, or ensure its progress updates trigger narrative reminders of the original obligation.
- **Late Thread Resolution** (Turns: T12) — Tag: `<late_resolution>` `canyon_ambush_threat` was resolved narratively in Turn 11 but appeared in completed threads only in Turn 12's state diff, creating a lag in mechanical recognition of the story beat. Fix: Ensure thread resolution is applied and reflected in immediate next-turn context if possible, or accept that one-turn latency is acceptable for this engine version (but note it affects "System Cohesion").

### Issues

- **Phantom Condition: heat_exhaustion** (Turns: T1-T2) — Tag: `<phantom_thread>` The condition was added but never referenced in prose or affected rolls. Fix: Ensure narrator references environmental conditions when they are active, or remove them if purely mechanical.
- **Directive-Narrative Disconnect: Pressure Directive on Calm Turns** (Turns: T4, T5, T12) — Tag: `<tone_mismatch>` The engine computed "Pressure" directives based on beat history, but the narration was informational/calm. Fix: Review `_compute_pacing_context` logic to ensure it resets when narrative velocity is low or de-escalation occurs naturally, rather than relying solely on consecutive pressure beats which may be misclassified by Storytell.
- **Beat Type Mismatch: Revelation as Pressure** (Turns: T4) — Tag: `<type_mismatch>` A "revelation" beat was generated under a "Pressure" directive context but failed to create narrative tension, acting instead as flat info delivery. Fix: Align Storytell prompt guidance so that "Revelation" beats are reserved for high-tension or plot-twist moments, not routine information gathering.
- **Inert Thread: deliver_the_ledger** (Turns: T1-T13) — Tag: `<inert_mechanic>` This thread was active and updated but never influenced narration or player choices directly. The Harker investigation completely overshadowed it. Fix: Either resolve this thread early when the PC shifts focus to Harker, or ensure its progress updates trigger narrative reminders of the original obligation.
- **Late Thread Resolution** (Turns: T12) — Tag: `<late_resolution>` `canyon_ambush_threat` was resolved narratively in Turn 11 but appeared in completed threads only in Turn 12's state diff, creating a lag in mechanical recognition of the story beat. Fix: Ensure thread resolution is applied and reflected in immediate next-turn context if possible, or accept that one-turn latency is acceptable for this engine version (but note it affects "System Cohesion").


## prompt_pipeline

### Actionable Issues

- **Remove Last Turn Narrative from Rules User Prompt.** (pipeline: rules, turns: all) — Tag: `wasted_tokens`. Fix: Remove `last_turn_narrative` field from ruling user prompt template. Ruling only needs state and input for intent/impossibility checks.
- **Add Immediate Consumption Example to Extract State System Prompt.** (pipeline: extract_state, turns: 13) — Tag: `instruction_ignored`. Fix: Add example: *Narration: "I drink the potion." -> Output: `{}`* to clarify that single-use items consumed instantly do not enter inventory.
- **Remove Previous Turn Narration from Scene Extractor User Prompt.** (pipeline: extract_scene, turns: all) — Tag: `wasted_tokens`. Fix: Remove `previous_turn_narration` field. Scene extraction relies solely on current narration for tags/location changes.

### Issues

- **Remove Last Turn Narrative from Rules User Prompt.** (pipeline: rules, turns: all) — Tag: `wasted_tokens`. Fix: Remove `last_turn_narrative` field from ruling user prompt template. Ruling only needs state and input for intent/impossibility checks.
- **Add Immediate Consumption Example to Extract State System Prompt.** (pipeline: extract_state, turns: 13) — Tag: `instruction_ignored`. Fix: Add example: *Narration: "I drink the potion." -> Output: `{}`* to clarify that single-use items consumed instantly do not enter inventory.
- **Remove Previous Turn Narration from Scene Extractor User Prompt.** (pipeline: extract_scene, turns: all) — Tag: `wasted_tokens`. Fix: Remove `previous_turn_narration` field. Scene extraction relies solely on current narration for tags/location changes.

