# Domain Judge Scores

```yaml
compaction:
  pipeline_scores: {}
narrative_interplay:
  pipeline_scores: {}
prompt_pipeline:
  pipeline_scores: {}
state_correctness:
  extraction_accuracy_score: 3
  mechanic_lifecycle_score: 4
  pipeline_scores: {}
  state_fidelity_rate: 1.0

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **Inventory Balance Corruption (Turns: 3, 4)** — Tag: `extraction_miss`. Fix: The Extract State pipeline failed to parse "200 credits" correctly, defaulting to 5 or a small integer. This caused the player's total credit count to drop from ~500 to 5 in one turn. Update extraction prompt to prioritize explicit numerical values for currency and ensure `inventory_update` merges with existing amounts rather than replacing them if not explicitly instructed.

**Major**
- **Phantom Item Lifecycle / Reconciliation Failure (Turns: 7, 12)** — Tag: `schema_drift`. Fix: The ledger was never added to inventory after T3 (where only credits were extracted). Consequently, the removal at T7 failed validation. At T12, it was re-added as a new item. This breaks continuity. Ensure that if an item is narratively held by the PC but missing from state extraction, the extractor either adds it or flags a warning for manual review rather than silently dropping it and requiring later reconciliation.

**Minor**
- **Auto-Checker False Positives on Adverbs (Turns: 2, 13)** — Tag: `engine_bug`. Fix: Update the NPC mention checker to exclude common adjectives/adverbs capitalized at sentence starts from entity recognition unless they match known compendium names or are followed by context clues indicating a proper noun.

### Issues

**Critical**
- **Inventory Balance Corruption (Turns: 3, 4)** — Tag: `extraction_miss`. Fix: The Extract State pipeline failed to parse "200 credits" correctly, defaulting to 5 or a small integer. This caused the player's total credit count to drop from ~500 to 5 in one turn. Update extraction prompt to prioritize explicit numerical values for currency and ensure `inventory_update` merges with existing amounts rather than replacing them if not explicitly instructed.

**Major**
- **Phantom Item Lifecycle / Reconciliation Failure (Turns: 7, 12)** — Tag: `schema_drift`. Fix: The ledger was never added to inventory after T3 (where only credits were extracted). Consequently, the removal at T7 failed validation. At T12, it was re-added as a new item. This breaks continuity. Ensure that if an item is narratively held by the PC but missing from state extraction, the extractor either adds it or flags a warning for manual review rather than silently dropping it and requiring later reconciliation.

**Minor**
- **Auto-Checker False Positives on Adverbs (Turns: 2, 13)** — Tag: `engine_bug`. Fix: Update the NPC mention checker to exclude common adjectives/adverbs capitalized at sentence starts from entity recognition unless they match known compendium names or are followed by context clues indicating a proper noun.


## narrative_interplay

### Actionable Issues

**Critical:**
- **Inventory/Thread Causality Break (Turns: 7, 12)** — Tag: `state_mismatch`. The ledger was handed to Halden and thread resolved in T7, but the player grabs it from their coat in T12. Fix: Ensure inventory state matches narrative handovers. If a thread resolves via item transfer, remove item from PC unless explicitly returned.
- **NPC Silently Relocated (Turns: 7, 12)** — Tag: `npc_ghost`. Halden disappears from the Inn and reappears at the Docks without narration or state update explaining his movement. Fix: Narrate Halden's departure in T8-T11 or explicitly move him to a new location with an event log entry.

**Major:**
- **Low Morale Phantom Condition (Turns: 2)** — Tag: `phantom`. The condition was removed from state but never referenced in prose before removal, making its mechanical impact invisible to the player. Fix: Reference conditions in narration when they are active or resolved if relevant.

**Minor:**
- **Thread Stagnation (Turns: 5-13)** — Tag: `inert_mechanic`. The thread `clear_the_road_toughs` was advanced but never closed, even after the player escaped town. Fix: Auto-resolve or demote threads when location changes significantly and threat is no longer present in current scene.

### Issues

**Critical:**
- **Inventory/Thread Causality Break (Turns: 7, 12)** — Tag: `state_mismatch`. The ledger was handed to Halden and thread resolved in T7, but the player grabs it from their coat in T12. Fix: Ensure inventory state matches narrative handovers. If a thread resolves via item transfer, remove item from PC unless explicitly returned.
- **NPC Silently Relocated (Turns: 7, 12)** — Tag: `npc_ghost`. Halden disappears from the Inn and reappears at the Docks without narration or state update explaining his movement. Fix: Narrate Halden's departure in T8-T11 or explicitly move him to a new location with an event log entry.

**Major:**
- **Low Morale Phantom Condition (Turns: 2)** — Tag: `phantom`. The condition was removed from state but never referenced in prose before removal, making its mechanical impact invisible to the player. Fix: Reference conditions in narration when they are active or resolved if relevant.

**Minor:**
- **Thread Stagnation (Turns: 5-13)** — Tag: `inert_mechanic`. The thread `clear_the_road_toughs` was advanced but never closed, even after the player escaped town. Fix: Auto-resolve or demote threads when location changes significantly and threat is no longer present in current scene.


## prompt_pipeline

### Actionable Issues

**Critical**
- <Scene Extractor fails to deduplicate existing NPCs, adding duplicates like 'scarred_tough' in T9 despite prior presence.> (pipeline: extract_scene, turns: [9]) — Tag: `<schema_drift>` Fix: Add a mandatory pre-submission check against the full compendium and previous turn's present_npcs list by name/title match.

**Major**
- <State Extractor removes phantom items not in inventory (T7) and fails to remove currency for implicit payments like dock boy bribe (T13).> (pipeline: extract_state, turns: [7, 13]) — Tag: `<instruction_ignored>` Fix: Strengthen "Match instruction" to reject removals of non-existent IDs. Add explicit rule that vague coin payments map to existing currency ID and trigger a remove delta.

**Minor**
- <Rules Pipeline uses 'negotiate' for pure movement actions (T1), which is semantically weak though valid.> (pipeline: rules, turns: [1]) — Tag: `<bad_prompt>` Fix: Allow `intent_verb` to be null or suggest a default like "approach" when no specific skill verb applies.
- <Progress Pipeline advances and resolves the same thread in one turn (T2).> (pipeline: extract_progress, turns: [2]) — Tag: `<instruction_ignored>` Fix: Clarify that `thread_advance` is for partial progress; use only `thread_resolve` if completed in a single step.

### Issues

**Critical**
- <Scene Extractor fails to deduplicate existing NPCs, adding duplicates like 'scarred_tough' in T9 despite prior presence.> (pipeline: extract_scene, turns: [9]) — Tag: `<schema_drift>` Fix: Add a mandatory pre-submission check against the full compendium and previous turn's present_npcs list by name/title match.

**Major**
- <State Extractor removes phantom items not in inventory (T7) and fails to remove currency for implicit payments like dock boy bribe (T13).> (pipeline: extract_state, turns: [7, 13]) — Tag: `<instruction_ignored>` Fix: Strengthen "Match instruction" to reject removals of non-existent IDs. Add explicit rule that vague coin payments map to existing currency ID and trigger a remove delta.

**Minor**
- <Rules Pipeline uses 'negotiate' for pure movement actions (T1), which is semantically weak though valid.> (pipeline: rules, turns: [1]) — Tag: `<bad_prompt>` Fix: Allow `intent_verb` to be null or suggest a default like "approach" when no specific skill verb applies.
- <Progress Pipeline advances and resolves the same thread in one turn (T2).> (pipeline: extract_progress, turns: [2]) — Tag: `<instruction_ignored>` Fix: Clarify that `thread_advance` is for partial progress; use only `thread_resolve` if completed in a single step.


## compaction

