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

**Critical:**
- **Condition Orphaning** (Turns: 2, 3, 4, 6, 10, 11, 12) — Tag: `wrong_pipeline`. Fix: Ensure `_apply_thread_updates` or the dice resolution step in Step 0 reads from `state.pc.conditions` and calculates `cond_mod` correctly. The condition is added to state but ignored by the ruling pipeline.
- **Momentum State Drift** (Turns: 3, 4, 5) — Tag: `engine_bug`. Fix: Debug `_apply_delta()` or momentum update logic in Step 0/1 tail. The band-derived delta is not being applied to the PC's momentum field correctly, leading to divergent state values.
- **Floor Relief Override Failure** (Turns: 6, 12) — Tag: `engine_bug`. Fix: Investigate `_check_floor_relief` logic. When `beat_locked=True` and storyteller emits a pressure-type beat, the engine should override it with `breathing_room`. It is currently failing to do so.

**Major:**
- **Location Change Application Failure** (Turns: 4, 8) — Tag: `schema_drift`. Fix: Verify that `location_change` deltas from Scene Extract are being merged into `state.location` by the validator/apply pipeline. The extraction identifies the change, but the state remains at the previous location ID/name in subsequent diffs.
- **Storytell Actions Extraction Miss** (Turns: 3, 5, 10) — Tag: `extraction_miss`. Fix: Debug Storytell LLM output parsing for the `actions` field. It is returning empty lists despite valid JSON structure elsewhere.

**Minor:**
- **Consecutive Pressure Counter Mismatch** (Turns: 3, 9) — Tag: `engine_bug`. Fix: Align the counter increment logic with the actual beat types emitted by Storytell. Complication/Pressure beats should consistently increment the counter; null or non-pressure beats should reset it.

### Issues

**Critical:**
- **Condition Orphaning** (Turns: 2, 3, 4, 6, 10, 11, 12) — Tag: `wrong_pipeline`. Fix: Ensure `_apply_thread_updates` or the dice resolution step in Step 0 reads from `state.pc.conditions` and calculates `cond_mod` correctly. The condition is added to state but ignored by the ruling pipeline.
- **Momentum State Drift** (Turns: 3, 4, 5) — Tag: `engine_bug`. Fix: Debug `_apply_delta()` or momentum update logic in Step 0/1 tail. The band-derived delta is not being applied to the PC's momentum field correctly, leading to divergent state values.
- **Floor Relief Override Failure** (Turns: 6, 12) — Tag: `engine_bug`. Fix: Investigate `_check_floor_relief` logic. When `beat_locked=True` and storyteller emits a pressure-type beat, the engine should override it with `breathing_room`. It is currently failing to do so.

**Major:**
- **Location Change Application Failure** (Turns: 4, 8) — Tag: `schema_drift`. Fix: Verify that `location_change` deltas from Scene Extract are being merged into `state.location` by the validator/apply pipeline. The extraction identifies the change, but the state remains at the previous location ID/name in subsequent diffs.
- **Storytell Actions Extraction Miss** (Turns: 3, 5, 10) — Tag: `extraction_miss`. Fix: Debug Storytell LLM output parsing for the `actions` field. It is returning empty lists despite valid JSON structure elsewhere.

**Minor:**
- **Consecutive Pressure Counter Mismatch** (Turns: 3, 9) — Tag: `engine_bug`. Fix: Align the counter increment logic with the actual beat types emitted by Storytell. Complication/Pressure beats should consistently increment the counter; null or non-pressure beats should reset it.


## narrative_interplay

### Actionable Issues

- **NPC Identity Continuity Failure** (Turns: T4, T8) — Tag: `npc_ghost`. Silas Thorne is introduced as an Assay Clerk blocking a doorway, then reappears in Turn 8 as the General Store clerk tallying supplies. The engine's compendium/narrator pipeline failed to track NPC role/location consistency across location changes or treated them as separate entities incorrectly. Fix: Ensure `compendium_npc_update` tracks unique identities and prevents role/location drift unless explicitly justified by narrative logic (which it wasn't here).

- **Phantom Thread in Narration** (Turns: T2-T9) — Tag: `phantom_thread`. The thread `deliver_the_ledger` is updated with progress ("Learned of missing caravan rumors", "Purchased supplies") but the narration never mentions Halden, the ledger, or the obligation to deliver it. Fix: Inject thread summaries into narrator context more aggressively or require storyteller to explicitly weave thread goals into action outcomes.

- **Declarative Input Handling** (Turns: T6, T7) — Tag: `intent_redirect`. Player inputs "The sheriff gives me..." and "I find a locked tin box" are treated as attempts requiring rolls/checks rather than stated facts or successful actions. This contradicts the player's agency when they state outcomes directly. Fix: Improve Step 0 Ruling to recognize declarative statements of fact vs. attempts, or allow "impossible" checks for contradictions rather than randomizing success/fail on declared successes.

- **Condition Phantoming** (Turns: T1-T2) — Tag: `phantom_mechanic`. Condition `heat_exhaustion` is added in Turn 1 extraction but never mentioned in narration or applied as a mechanical modifier to subsequent rolls (T2 charisma roll had no cond_mod). Fix: Ensure conditions are either narratively referenced or mechanically applied; if neither, they shouldn't be generated.

### Issues

- **NPC Identity Continuity Failure** (Turns: T4, T8) — Tag: `npc_ghost`. Silas Thorne is introduced as an Assay Clerk blocking a doorway, then reappears in Turn 8 as the General Store clerk tallying supplies. The engine's compendium/narrator pipeline failed to track NPC role/location consistency across location changes or treated them as separate entities incorrectly. Fix: Ensure `compendium_npc_update` tracks unique identities and prevents role/location drift unless explicitly justified by narrative logic (which it wasn't here).

- **Phantom Thread in Narration** (Turns: T2-T9) — Tag: `phantom_thread`. The thread `deliver_the_ledger` is updated with progress ("Learned of missing caravan rumors", "Purchased supplies") but the narration never mentions Halden, the ledger, or the obligation to deliver it. Fix: Inject thread summaries into narrator context more aggressively or require storyteller to explicitly weave thread goals into action outcomes.

- **Declarative Input Handling** (Turns: T6, T7) — Tag: `intent_redirect`. Player inputs "The sheriff gives me..." and "I find a locked tin box" are treated as attempts requiring rolls/checks rather than stated facts or successful actions. This contradicts the player's agency when they state outcomes directly. Fix: Improve Step 0 Ruling to recognize declarative statements of fact vs. attempts, or allow "impossible" checks for contradictions rather than randomizing success/fail on declared successes.

- **Condition Phantoming** (Turns: T1-T2) — Tag: `phantom_mechanic`. Condition `heat_exhaustion` is added in Turn 1 extraction but never mentioned in narration or applied as a mechanical modifier to subsequent rolls (T2 charisma roll had no cond_mod). Fix: Ensure conditions are either narratively referenced or mechanically applied; if neither, they shouldn't be generated.


## prompt_pipeline

### Actionable Issues

### Critical
- **Rules Pipeline Schema Mismatch** (pipeline: Rules, turns: T1-T13) — Tag: `schema_drift`. Fix: Update the System Prompt's JSON Schema example to exactly match the Pydantic model for `IntentEnvelope`, including all required fields and valid enum values for `intent_verb` (add "transition" or map it explicitly). Ensure the LLM output passes validation.

### Major
- **NPC Data Redundancy** (pipeline: Narrate, Scene, Storytell, turns: T1-T13) — Tag: `wasted_tokens`. Fix: Prune the `## Characters` section in all three user prompts to exclude detailed bios/motivations/fear/leverage. Pass only Name, Title, and Presence status. Inject full bio data dynamically for first appearances or specific interactions.
- **Scene Extractor Duplicate Entries** (pipeline: Scene, turns: T6) — Tag: `instruction_ignored`. Fix: Add explicit instruction to merge updates for existing NPC IDs within the same turn's output array rather than creating duplicate objects.

### Minor
- **Storytell Premature Activation** (pipeline: Storytell, turns: T2) — Tag: `bad_prompt`. Fix: Clarify thread update rules with examples showing that "learning information" does not trigger a thread update unless it directly impacts the thread's urgency or active status via player action.
- **Rules Prompt Ambiguity** (pipeline: Rules, turns: T1-T13) — Tag: `bad_prompt`. Fix: Replace "appropriate unlisted word" with explicit mapping rules for meta-actions like "transition", "inspect", etc., to prevent LLM hallucination of non-standard verbs.

### Issues

### Critical
- **Rules Pipeline Schema Mismatch** (pipeline: Rules, turns: T1-T13) — Tag: `schema_drift`. Fix: Update the System Prompt's JSON Schema example to exactly match the Pydantic model for `IntentEnvelope`, including all required fields and valid enum values for `intent_verb` (add "transition" or map it explicitly). Ensure the LLM output passes validation.

### Major
- **NPC Data Redundancy** (pipeline: Narrate, Scene, Storytell, turns: T1-T13) — Tag: `wasted_tokens`. Fix: Prune the `## Characters` section in all three user prompts to exclude detailed bios/motivations/fear/leverage. Pass only Name, Title, and Presence status. Inject full bio data dynamically for first appearances or specific interactions.
- **Scene Extractor Duplicate Entries** (pipeline: Scene, turns: T6) — Tag: `instruction_ignored`. Fix: Add explicit instruction to merge updates for existing NPC IDs within the same turn's output array rather than creating duplicate objects.

### Minor
- **Storytell Premature Activation** (pipeline: Storytell, turns: T2) — Tag: `bad_prompt`. Fix: Clarify thread update rules with examples showing that "learning information" does not trigger a thread update unless it directly impacts the thread's urgency or active status via player action.
- **Rules Prompt Ambiguity** (pipeline: Rules, turns: T1-T13) — Tag: `bad_prompt`. Fix: Replace "appropriate unlisted word" with explicit mapping rules for meta-actions like "transition", "inspect", etc., to prevent LLM hallucination of non-standard verbs.

