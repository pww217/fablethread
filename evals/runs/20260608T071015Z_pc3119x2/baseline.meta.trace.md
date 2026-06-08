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
  state_fidelity_rate: 0.15

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **Location Delta Application Failure** (Turns: 4, 8, 10, 12) — Tag: `engine_bug`. Fix: Inspect `_apply_delta` or `delta_builder.py` for location updates. The delta is generated but not persisted to `state.location`. This breaks scene continuity entirely.
- **Momentum Calculation Inversion** (Turns: 4, 7, 11) — Tag: `engine_bug`. Fix: Debug `_compute_pacing_context` or momentum update logic. Dice bands are being mapped to incorrect delta values (e.g., Crit Success applying -1).

**Major**
- **Floor Relief Mechanism Failure** (Turns: 4, 10) — Tag: `engine_bug`. Fix: The engine fails to inject `breathing_room` when `beat_locked=True` and a pressure beat is emitted. This causes unbroken pressure cycles contrary to design intent.
- **Thread Resolution Ignored** (Turn: 12) — Tag: `extraction_miss`. Fix: `_apply_thread_resolutions()` or the merge step for T12 failed to move `harker_hat_connection` from active threads to completed_threads despite explicit `thread_resolve` output.

**Minor**
- **Actions Extraction Null/Empty** (Turns: 5, 9) — Tag: `extraction_miss`. Fix: Storytell LLM is occasionally returning empty/null actions lists. Validation should reject or default to placeholder if <4 actions are emitted.
- **Condition Orphan Flags** (Turns: 6, 8, 9, 10, 11) — Tag: `scope_violation`. Fix: Add entries for `dusty`, `startled`, `exposed`, `relaxed` to the engine's `CONDITION_MODS` configuration or ensure they default to 0 mod without erroring.

### Issues

**Critical**
- **Location Delta Application Failure** (Turns: 4, 8, 10, 12) — Tag: `engine_bug`. Fix: Inspect `_apply_delta` or `delta_builder.py` for location updates. The delta is generated but not persisted to `state.location`. This breaks scene continuity entirely.
- **Momentum Calculation Inversion** (Turns: 4, 7, 11) — Tag: `engine_bug`. Fix: Debug `_compute_pacing_context` or momentum update logic. Dice bands are being mapped to incorrect delta values (e.g., Crit Success applying -1).

**Major**
- **Floor Relief Mechanism Failure** (Turns: 4, 10) — Tag: `engine_bug`. Fix: The engine fails to inject `breathing_room` when `beat_locked=True` and a pressure beat is emitted. This causes unbroken pressure cycles contrary to design intent.
- **Thread Resolution Ignored** (Turn: 12) — Tag: `extraction_miss`. Fix: `_apply_thread_resolutions()` or the merge step for T12 failed to move `harker_hat_connection` from active threads to completed_threads despite explicit `thread_resolve` output.

**Minor**
- **Actions Extraction Null/Empty** (Turns: 5, 9) — Tag: `extraction_miss`. Fix: Storytell LLM is occasionally returning empty/null actions lists. Validation should reject or default to placeholder if <4 actions are emitted.
- **Condition Orphan Flags** (Turns: 6, 8, 9, 10, 11) — Tag: `scope_violation`. Fix: Add entries for `dusty`, `startled`, `exposed`, `relaxed` to the engine's `CONDITION_MODS` configuration or ensure they default to 0 mod without erroring.


## narrative_interplay

### Actionable Issues

- **<Description>** (turns: 6, 8) — Tag: `intent_redirect`. Fix: Ruling step misclassifies "Sheriff gives key" as `sneak`/impossible grab instead of accepting the gift or rolling for persuasion. The engine must respect declarative actions unless truly impossible.
- **<Description>** (turns: 8, 9) — Tag: `npc_ghost`. Fix: Silas Vance appears in two different locations with conflicting titles (Assay Clerk vs General Store Clerk). Victor Drax disappears without resolution while the thread is silently deleted from state. Ensure NPC lifecycle and location tracking are consistent.
- **<Description>** (turns: 5, 10) — Tag: `inert_mechanic`. Fix: Storytell output is empty JSON `{}` for these turns, yet time/location advances in subsequent diffs. This indicates a pipeline crash or silent failure where mechanics do not drive narrative consequence.
- **<Description>** (turns: 9, 10) — Tag: `false_resolution`. Fix: Thread `confront_predatory_rider` is removed from arc state but no narration resolves the confrontation with Victor Drax. The player was left in limbo between a store and a canyon camp without narrative closure for that threat.

### Issues

- **<Description>** (turns: 6, 8) — Tag: `intent_redirect`. Fix: Ruling step misclassifies "Sheriff gives key" as `sneak`/impossible grab instead of accepting the gift or rolling for persuasion. The engine must respect declarative actions unless truly impossible.
- **<Description>** (turns: 8, 9) — Tag: `npc_ghost`. Fix: Silas Vance appears in two different locations with conflicting titles (Assay Clerk vs General Store Clerk). Victor Drax disappears without resolution while the thread is silently deleted from state. Ensure NPC lifecycle and location tracking are consistent.
- **<Description>** (turns: 5, 10) — Tag: `inert_mechanic`. Fix: Storytell output is empty JSON `{}` for these turns, yet time/location advances in subsequent diffs. This indicates a pipeline crash or silent failure where mechanics do not drive narrative consequence.
- **<Description>** (turns: 9, 10) — Tag: `false_resolution`. Fix: Thread `confront_predatory_rider` is removed from arc state but no narration resolves the confrontation with Victor Drax. The player was left in limbo between a store and a canyon camp without narrative closure for that threat.


## prompt_pipeline

### Actionable Issues

### Critical
- **<description>** (pipeline: Rules/Narrate/Scene/State/Storytell, turns: T1-T13) — Tag: `wasted_tokens`. Fix: Pass summarized recent turns to non-narrate pipelines instead of full narration. *Outcome:* Reduce token waste by ~400 tokens/turn across 3 streams (Scene, State, Storytell).

### Major
- **<description>** (pipeline: Extract Scene, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Bio Examples into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Extract State, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Condition Heuristics into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Storyteller, turns: T1-T12) — Tag: `bad_prompt`. Fix: Merge Beat Alignment Tables into a single decision matrix. *Outcome:* Reduce prompt size by ~150 tokens without losing guidance quality.

### Minor
- **<description>** (pipeline: Extract Scene/State/Storytell, turns: T1-T12) — Tag: `cross_pipeline_redundancy`. Fix: Remove unnecessary inputs (`state.pc`, `conditions` for Scene; `player_intent` for State; `rules_outcome` for Storytell). *Outcome:* Reduce token waste by ~50 tokens/turn per stream.

### Issues

### Critical
- **<description>** (pipeline: Rules/Narrate/Scene/State/Storytell, turns: T1-T13) — Tag: `wasted_tokens`. Fix: Pass summarized recent turns to non-narrate pipelines instead of full narration. *Outcome:* Reduce token waste by ~400 tokens/turn across 3 streams (Scene, State, Storytell).

### Major
- **<description>** (pipeline: Extract Scene, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Bio Examples into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Extract State, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Condition Heuristics into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Storyteller, turns: T1-T12) — Tag: `bad_prompt`. Fix: Merge Beat Alignment Tables into a single decision matrix. *Outcome:* Reduce prompt size by ~150 tokens without losing guidance quality.

### Minor
- **<description>** (pipeline: Extract Scene/State/Storytell, turns: T1-T12) — Tag: `cross_pipeline_redundancy`. Fix: Remove unnecessary inputs (`state.pc`, `conditions` for Scene; `player_intent` for State; `rules_outcome` for Storytell). *Outcome:* Reduce token waste by ~50 tokens/turn per stream.

