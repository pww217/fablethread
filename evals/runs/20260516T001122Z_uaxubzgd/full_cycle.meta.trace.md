# Domain Judge Scores

```yaml
{}

```

# Judge Summaries

## state_correctness

### Actionable Issues

- **Inventory validation and extraction consistency** (turns: 4, 5, 6, 7, 9, 12) — Tag: `extraction_miss`. Fix: Implement pre-validation in the state manager to reject removals exceeding current balance or referencing non-existent IDs. Update the state extraction prompt to strictly cross-reference the current inventory snapshot before emitting deltas.
- **Progress extraction pipeline failure** (turns: 1-13) — Tag: `extraction_miss`. Fix: Debug the progress extraction LLM call; ensure the prompt mandates `actions` generation or adjust the auto-checker threshold to account for narrative-heavy turns.
- **Scene pressure directive leakage** (turns: 8, 9, 10) — Tag: `scope_violation`. Fix: Engine must inject active `scene_pressure` directives (especially `immediate` urgency) into the Narrate User Prompt to ensure the narrator acknowledges and reacts to escalating threats.
- **Location change application lag** (turns: 4, 12) — Tag: `engine_bug`. Fix: Verify the location delta application logic in the state manager; ensure `location_change` emissions correctly overwrite `state.location.id` and trigger necessary NPC/scene updates.

### Issues

- **Inventory validation and extraction consistency** (turns: 4, 5, 6, 7, 9, 12) — Tag: `extraction_miss`. Fix: Implement pre-validation in the state manager to reject removals exceeding current balance or referencing non-existent IDs. Update the state extraction prompt to strictly cross-reference the current inventory snapshot before emitting deltas.
- **Progress extraction pipeline failure** (turns: 1-13) — Tag: `extraction_miss`. Fix: Debug the progress extraction LLM call; ensure the prompt mandates `actions` generation or adjust the auto-checker threshold to account for narrative-heavy turns.
- **Scene pressure directive leakage** (turns: 8, 9, 10) — Tag: `scope_violation`. Fix: Engine must inject active `scene_pressure` directives (especially `immediate` urgency) into the Narrate User Prompt to ensure the narrator acknowledges and reacts to escalating threats.
- **Location change application lag** (turns: 4, 12) — Tag: `engine_bug`. Fix: Verify the location delta application logic in the state manager; ensure `location_change` emissions correctly overwrite `state.location.id` and trigger necessary NPC/scene updates.


## narrative_interplay

### Actionable Issues

- **<Momentum band stuck at -3 from T6 to T16 despite narrative recoveries and partial successes. The engine fails to shift the band or allow narrative breathing room.>** (turns: 6-16) — Tag: `inert_mechanic`. Fix: Implement momentum recovery thresholds or narrative beat triggers that explicitly shift the band when the player achieves tactical goals (e.g., securing the ledger, escaping the breach).
- **<Thread `settle_the_debt` remains active with progress 0 in state after T2, despite narration explicitly resolving the debt ("The debt is dead").>** (turns: 2) — Tag: `state_mismatch`. Fix: Update thread state to `complete` or increment progress immediately upon narrative resolution extraction.
- **<GM beat turns (T7, T11, T12) produce zero narration while forcing state/location changes. This creates a jarring mechanical/narrative split.>** (turns: 7, 11, 12) — Tag: `directive_ignored`. Fix: Ensure GM beats surface as ambient descriptions or event narrations that acknowledge the state change (e.g., "The heavy oak door finally gives way...").
- **<Condition `shoulder_bruise` is added twice in the trace (T7 and T9), indicating a deduplication failure in the state extractor.>** (turns: 7, 9) — Tag: `inert_mechanic`. Fix: Add state validation to prevent duplicate condition IDs from being applied.

### Issues

- **<Momentum band stuck at -3 from T6 to T16 despite narrative recoveries and partial successes. The engine fails to shift the band or allow narrative breathing room.>** (turns: 6-16) — Tag: `inert_mechanic`. Fix: Implement momentum recovery thresholds or narrative beat triggers that explicitly shift the band when the player achieves tactical goals (e.g., securing the ledger, escaping the breach).
- **<Thread `settle_the_debt` remains active with progress 0 in state after T2, despite narration explicitly resolving the debt ("The debt is dead").>** (turns: 2) — Tag: `state_mismatch`. Fix: Update thread state to `complete` or increment progress immediately upon narrative resolution extraction.
- **<GM beat turns (T7, T11, T12) produce zero narration while forcing state/location changes. This creates a jarring mechanical/narrative split.>** (turns: 7, 11, 12) — Tag: `directive_ignored`. Fix: Ensure GM beats surface as ambient descriptions or event narrations that acknowledge the state change (e.g., "The heavy oak door finally gives way...").
- **<Condition `shoulder_bruise` is added twice in the trace (T7 and T9), indicating a deduplication failure in the state extractor.>** (turns: 7, 9) — Tag: `inert_mechanic`. Fix: Add state validation to prevent duplicate condition IDs from being applied.


## prompt_pipeline

### Actionable Issues

- **<Extract Progress `drift_analysis` consistently omits `thread_id`, causing Pydantic validation failures on T3, T4, T9, T10>** (pipeline: extract_progress, turns: 3, 4, 9, 10) — Tag: `<schema_drift|instruction_ignored>`. Fix: Add a mandatory few-shot JSON example showing the exact `drift_analysis` entry structure with `thread_id` included. Expected outcome: Eliminates parse errors, restores 100% adherence.
- **<`present_npcs` and location description duplicated verbatim across 5 pipelines>** (pipeline: all, turns: 1–13) — Tag: `<cross_pipeline_redundancy|wasted_tokens>`. Fix: Pass `present_npcs` as a compacted JSON array or reference ID to Rules/Scene/State/Progress; pass location as ID + 1-sentence summary to extractors. Expected outcome: ~450 token reduction per turn without loss of functionality.
- **<Narrate T7 violates "Inventory is a hard constraint" by describing Halden's ledger despite it not being in the provided inventory list>** (pipeline: narrate, turns: 7) — Tag: `<instruction_ignored>`. Fix: Add a pre-narration verification step: "Before writing, cross-reference every item/NPC with the provided lists. If absent, narrate the attempt failing." Expected outcome: Prevents phantom item narration and state drift.

### Issues

- **<Extract Progress `drift_analysis` consistently omits `thread_id`, causing Pydantic validation failures on T3, T4, T9, T10>** (pipeline: extract_progress, turns: 3, 4, 9, 10) — Tag: `<schema_drift|instruction_ignored>`. Fix: Add a mandatory few-shot JSON example showing the exact `drift_analysis` entry structure with `thread_id` included. Expected outcome: Eliminates parse errors, restores 100% adherence.
- **<`present_npcs` and location description duplicated verbatim across 5 pipelines>** (pipeline: all, turns: 1–13) — Tag: `<cross_pipeline_redundancy|wasted_tokens>`. Fix: Pass `present_npcs` as a compacted JSON array or reference ID to Rules/Scene/State/Progress; pass location as ID + 1-sentence summary to extractors. Expected outcome: ~450 token reduction per turn without loss of functionality.
- **<Narrate T7 violates "Inventory is a hard constraint" by describing Halden's ledger despite it not being in the provided inventory list>** (pipeline: narrate, turns: 7) — Tag: `<instruction_ignored>`. Fix: Add a pre-narration verification step: "Before writing, cross-reference every item/NPC with the provided lists. If absent, narrate the attempt failing." Expected outcome: Prevents phantom item narration and state drift.


## compaction

### Actionable Issues

- None. The compactor successfully condensed the run into precise, entity-rich chronicle bullets with zero hallucinations, generic phrasing, or state conflicts. Sanitization logic was correctly bypassed as no duplicate NPCs, active pressures, or inventory/condition changes existed in the compacted windows.

### Issues

- None. The compactor successfully condensed the run into precise, entity-rich chronicle bullets with zero hallucinations, generic phrasing, or state conflicts. Sanitization logic was correctly bypassed as no duplicate NPCs, active pressures, or inventory/condition changes existed in the compacted windows.

