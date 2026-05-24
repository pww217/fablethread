# Domain Judge Scores

```yaml
compaction:
  pipeline_scores: {}
narrative_interplay:
  pipeline_scores: {}
prompt_pipeline:
  pipeline_scores: {}
  prompt_adherence_rate: 0.97
state_correctness:
  extraction_accuracy_score: 3
  mechanic_lifecycle_score: 1
  pipeline_scores: {}
  state_fidelity_rate: 0.69

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **Narrator Binding Failure** (turns: [5,6,8,10,11,12]) — Tag: `wrong_pipeline`. Fix: Ensure `_run_extraction_pipeline()` or `_narrate_messages()` always injects the `rules_outcome` BINDING block into the user prompt when `rolled=true`. This is a systematic pipeline wiring error.
- **Thread Progress Stagnation** (turns: [3,4,5,6,13]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` must increment progress on matched IDs from `thread_advance`. Currently, it seems to only update `last_seen_turn` but not `progress`, or the delta application is failing silently.

**Major**
- **Inventory Spending Hallucination** (turns: [7,9,13]) — Tag: `extraction_miss`. Fix: State Extractor prompt needs stronger negative constraints against removing inventory items that are not present in the current state snapshot provided as context. Add a validation step pre-extraction or post-prompt to list available inventory IDs.
- **Actions Generation Failure** (turns: [3,6,9,12]) — Tag: `extraction_miss`. Fix: Storyteller prompt needs explicit instruction to always output exactly 4 actions, even if generic. Check for empty array rejection in validator and retry or default generation.

**Minor**
- **GM Beat TTL Expiry** (turns: [9,10,11]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` or beat management logic must check `beat_expires_turn` against current turn number at the start of each turn and nullify if exceeded. It is currently persisting beats past TTL.
- **Auto-Checker False Positives** (turns: [2,4,13]) — Tag: `checker_noise`. Fix: Update NPC mention checker to exclude location names and generic capitalized words. Update location change checker to verify post-apply state correctly.

### Issues

**Critical**
- **Narrator Binding Failure** (turns: [5,6,8,10,11,12]) — Tag: `wrong_pipeline`. Fix: Ensure `_run_extraction_pipeline()` or `_narrate_messages()` always injects the `rules_outcome` BINDING block into the user prompt when `rolled=true`. This is a systematic pipeline wiring error.
- **Thread Progress Stagnation** (turns: [3,4,5,6,13]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` must increment progress on matched IDs from `thread_advance`. Currently, it seems to only update `last_seen_turn` but not `progress`, or the delta application is failing silently.

**Major**
- **Inventory Spending Hallucination** (turns: [7,9,13]) — Tag: `extraction_miss`. Fix: State Extractor prompt needs stronger negative constraints against removing inventory items that are not present in the current state snapshot provided as context. Add a validation step pre-extraction or post-prompt to list available inventory IDs.
- **Actions Generation Failure** (turns: [3,6,9,12]) — Tag: `extraction_miss`. Fix: Storyteller prompt needs explicit instruction to always output exactly 4 actions, even if generic. Check for empty array rejection in validator and retry or default generation.

**Minor**
- **GM Beat TTL Expiry** (turns: [9,10,11]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` or beat management logic must check `beat_expires_turn` against current turn number at the start of each turn and nullify if exceeded. It is currently persisting beats past TTL.
- **Auto-Checker False Positives** (turns: [2,4,13]) — Tag: `checker_noise`. Fix: Update NPC mention checker to exclude location names and generic capitalized words. Update location change checker to verify post-apply state correctly.


## narrative_interplay

### Actionable Issues

- **Critical: Beat-Narration Mismatch on T10** (turns: 10) — Tag: `directive_ignored`. The Progress Extractor emitted a `breathing_room` beat, but the Narrator produced high-tension combat prose. This indicates a failure in how the Narrator consumes or prioritizes pending beats vs. current scene state/roll outcomes. Fix: Ensure Narrator prompt explicitly instructs to honor `pending_gm_beat.type` if it contradicts immediate roll outcome tone, or fix Progress Extractor logic for beat generation during high-tension states.
- **Major: Missing Input Handling on T7** (turns: 7) — Tag: `intent_redirect`. The input field is empty in the trace, but narration reflects a specific escalation ("Not so fast..."). This suggests the engine may be hallucinating intent or relying on stale context when no valid user input is provided. Fix: Validate non-empty user input before proceeding to Narrate step; if missing, default to "What happens next?" style prompt or error out.
- **Minor: Consecutive High-Tension Fatigue** (turns: 5-12) — Tag: `tone_mismatch`. While mechanically correct for the situation, 8 consecutive turns of pressure without a mechanical "Breathe" directive (despite T9/T12 having breathing room beats in state diffs? No, T9 beat was Pressure, T12 was Breathing Room but came *after* the fail) creates narrative fatigue. Fix: Consider injecting `breathing_room` or `resolution` directives more frequently during extended confrontations to allow for tactical pauses.
- **Minor: Phantom Thread Focus** (turns: 3-13) — Tag: `phantom_thread`. The `deliver_the_ledger` thread is active but rarely referenced in narration compared to immediate threats. Fix: Instruct Narrator to periodically reference the primary arc goal (`visible_goal`) or specific threads when no immediate combat threat dominates, even if just as internal monologue or NPC reminder.

### Issues

- **Critical: Beat-Narration Mismatch on T10** (turns: 10) — Tag: `directive_ignored`. The Progress Extractor emitted a `breathing_room` beat, but the Narrator produced high-tension combat prose. This indicates a failure in how the Narrator consumes or prioritizes pending beats vs. current scene state/roll outcomes. Fix: Ensure Narrator prompt explicitly instructs to honor `pending_gm_beat.type` if it contradicts immediate roll outcome tone, or fix Progress Extractor logic for beat generation during high-tension states.
- **Major: Missing Input Handling on T7** (turns: 7) — Tag: `intent_redirect`. The input field is empty in the trace, but narration reflects a specific escalation ("Not so fast..."). This suggests the engine may be hallucinating intent or relying on stale context when no valid user input is provided. Fix: Validate non-empty user input before proceeding to Narrate step; if missing, default to "What happens next?" style prompt or error out.
- **Minor: Consecutive High-Tension Fatigue** (turns: 5-12) — Tag: `tone_mismatch`. While mechanically correct for the situation, 8 consecutive turns of pressure without a mechanical "Breathe" directive (despite T9/T12 having breathing room beats in state diffs? No, T9 beat was Pressure, T12 was Breathing Room but came *after* the fail) creates narrative fatigue. Fix: Consider injecting `breathing_room` or `resolution` directives more frequently during extended confrontations to allow for tactical pauses.
- **Minor: Phantom Thread Focus** (turns: 3-13) — Tag: `phantom_thread`. The `deliver_the_ledger` thread is active but rarely referenced in narration compared to immediate threats. Fix: Instruct Narrator to periodically reference the primary arc goal (`visible_goal`) or specific threads when no immediate combat threat dominates, even if just as internal monologue or NPC reminder.


## prompt_pipeline

### Actionable Issues

### Critical
- **<inventory_remove emitted for failed spending attempts>** (pipeline: extract_state, turns: [7, 9]) — Tag: `instruction_ignored`. Fix: Add explicit rule and negative examples stating that if an action fails before successful transfer of item/coin, NO inventory_remove should be emitted. Example: "Player drops coins but thugs pin them → no remove."

### Major
- **<NPCs removed due to absence in narration>** (pipeline: extract_scene, turns: [3]) — Tag: `instruction_ignored`. Fix: Clarify that `npc_remove` requires explicit narration of departure/death. Absence ≠ removal. Add example showing "NPC not mentioned = no change".
- **<GM Beat guidance too complex>** (pipeline: storytell, turns: [5-13]) — Tag: `wasted_tokens`. Fix: Simplify beat selection into a priority list or decision tree to reduce token waste and improve adherence.

### Minor
- **<Redundant static context in prompts>** (pipelines: scene, state, storytell) — Tag: `cross_pipeline_redundancy`. Fix: Compress PC bio and inventory lists for extractors; use summaries instead of full text where possible.

### Issues

### Critical
- **<inventory_remove emitted for failed spending attempts>** (pipeline: extract_state, turns: [7, 9]) — Tag: `instruction_ignored`. Fix: Add explicit rule and negative examples stating that if an action fails before successful transfer of item/coin, NO inventory_remove should be emitted. Example: "Player drops coins but thugs pin them → no remove."

### Major
- **<NPCs removed due to absence in narration>** (pipeline: extract_scene, turns: [3]) — Tag: `instruction_ignored`. Fix: Clarify that `npc_remove` requires explicit narration of departure/death. Absence ≠ removal. Add example showing "NPC not mentioned = no change".
- **<GM Beat guidance too complex>** (pipeline: storytell, turns: [5-13]) — Tag: `wasted_tokens`. Fix: Simplify beat selection into a priority list or decision tree to reduce token waste and improve adherence.

### Minor
- **<Redundant static context in prompts>** (pipelines: scene, state, storytell) — Tag: `cross_pipeline_redundancy`. Fix: Compress PC bio and inventory lists for extractors; use summaries instead of full text where possible.


## compaction

