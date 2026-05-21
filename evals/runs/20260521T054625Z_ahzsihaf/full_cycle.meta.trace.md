# Domain Judge Scores

```yaml
compaction:
  pipeline_scores: {}
narrative_interplay:
  pipeline_scores: {}
prompt_pipeline:
  pipeline_scores: {}
state_correctness:
  extraction_accuracy_score: 2
  mechanic_lifecycle_score: 2
  pipeline_scores: {}
  state_fidelity_rate: 0.0

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **Condition Schema Drift at Turn 1** (turns: [1]) — Tag: `schema_drift`. Fix: The Extract State pipeline is injecting conditions with incorrect `added_turn` values (future dates). Ensure the extractor initializes conditions relative to the *current* turn or respects the seed state's empty condition array.
- **Location ID Update Failure** (turns: [4, 10, 12]) — Tag: `engine_bug`. Fix: The engine is rejecting location deltas where the narrative implies a move. Check the validation logic for `location_change` payloads; ensure that if `description` changes and NPCs are removed/added appropriately, the `id` field is accepted or correctly inferred from context.

**Major**
- **Progress Actions Extraction Misses** (turns: [3, 6, 9, 12]) — Tag: `extraction_miss`. Fix: The Extract Progress prompt needs reinforcement to always generate at least 4 suggested actions based on the immediate narrative conflict or choice point.

**Minor**
- **NPC Mention False Positives** (turns: [1, 3, 4, 5, 7, 8, 9, 10, 13]) — Tag: `stale_context`. Fix: Update the Auto-Checker's NPC mention logic to ignore common words and focus on proper nouns defined in the compendium.

### Issues

**Critical**
- **Condition Schema Drift at Turn 1** (turns: [1]) — Tag: `schema_drift`. Fix: The Extract State pipeline is injecting conditions with incorrect `added_turn` values (future dates). Ensure the extractor initializes conditions relative to the *current* turn or respects the seed state's empty condition array.
- **Location ID Update Failure** (turns: [4, 10, 12]) — Tag: `engine_bug`. Fix: The engine is rejecting location deltas where the narrative implies a move. Check the validation logic for `location_change` payloads; ensure that if `description` changes and NPCs are removed/added appropriately, the `id` field is accepted or correctly inferred from context.

**Major**
- **Progress Actions Extraction Misses** (turns: [3, 6, 9, 12]) — Tag: `extraction_miss`. Fix: The Extract Progress prompt needs reinforcement to always generate at least 4 suggested actions based on the immediate narrative conflict or choice point.

**Minor**
- **NPC Mention False Positives** (turns: [1, 3, 4, 5, 7, 8, 9, 10, 13]) — Tag: `stale_context`. Fix: Update the Auto-Checker's NPC mention logic to ignore common words and focus on proper nouns defined in the compendium.


## narrative_interplay

### Actionable Issues

**Critical**
- **<Thread Expiration Logic>** (turns: T9) — Tag: `false_expiration`. The thread `the_ledger_conspiracy` is marked complete at Turn 9, but the narrative continues with the same antagonists hunting the player through Turns 10-13. Fix: Ensure arc threads only resolve when the *narrative tension* associated with them is actually resolved (e.g., thugs defeated or escaped permanently), not just on progress thresholds.
- **<Momentum Band/Narration Mismatch>** (turns: T8, T10) — Tag: `directive_ignored`. The Rules System outputs "Success" bands for Turns 8 and 10, but the Narration describes outcomes that are mechanically equivalent to Setbacks or Fails (player is pinned/restrained in T8; player gets no info and faces new threats in T10). Fix: Align the Narrative outcome with the Band. If the band is Success, the player must achieve their *primary* intent (unlocking door / getting answer), even if complications exist. Do not negate the success entirely.

**Major**
- **<GM Beat Integration>** (turns: T8) — Tag: `no_effect`. A "Complication" beat was generated in Turn 8 ("tighten perimeter") but did not appear in the narration of subsequent turns. Fix: Ensure pending GM beats are surfaced in the next available narrative turn or explicitly acknowledged by NPCs/Environment.
- **<Intent Fidelity>** (turns: T10) — Tag: `intent_redirect`. Player intent was "Demand identity". Narration outcome was evasion and escalation. While this is a valid *complication*, it violates the spirit of the "Success" band which implies the player's action worked. Fix: If the band is Success, Matthew should reveal *something* (even if partial/misleading) or the band should be Partial/Fail to reflect the resistance.

**Minor**
- **<Condition Tracking>** (turns: T7-T9) — Tag: `phantom`. The "rattled" condition was added in T7 and removed in T8/9, but the narration's description of "frantic movements" spans multiple turns without clear mechanical justification for the removal. Fix: Ensure conditions persist as long as their narrative descriptor is relevant.

### Issues

**Critical**
- **<Thread Expiration Logic>** (turns: T9) — Tag: `false_expiration`. The thread `the_ledger_conspiracy` is marked complete at Turn 9, but the narrative continues with the same antagonists hunting the player through Turns 10-13. Fix: Ensure arc threads only resolve when the *narrative tension* associated with them is actually resolved (e.g., thugs defeated or escaped permanently), not just on progress thresholds.
- **<Momentum Band/Narration Mismatch>** (turns: T8, T10) — Tag: `directive_ignored`. The Rules System outputs "Success" bands for Turns 8 and 10, but the Narration describes outcomes that are mechanically equivalent to Setbacks or Fails (player is pinned/restrained in T8; player gets no info and faces new threats in T10). Fix: Align the Narrative outcome with the Band. If the band is Success, the player must achieve their *primary* intent (unlocking door / getting answer), even if complications exist. Do not negate the success entirely.

**Major**
- **<GM Beat Integration>** (turns: T8) — Tag: `no_effect`. A "Complication" beat was generated in Turn 8 ("tighten perimeter") but did not appear in the narration of subsequent turns. Fix: Ensure pending GM beats are surfaced in the next available narrative turn or explicitly acknowledged by NPCs/Environment.
- **<Intent Fidelity>** (turns: T10) — Tag: `intent_redirect`. Player intent was "Demand identity". Narration outcome was evasion and escalation. While this is a valid *complication*, it violates the spirit of the "Success" band which implies the player's action worked. Fix: If the band is Success, Matthew should reveal *something* (even if partial/misleading) or the band should be Partial/Fail to reflect the resistance.

**Minor**
- **<Condition Tracking>** (turns: T7-T9) — Tag: `phantom`. The "rattled" condition was added in T7 and removed in T8/9, but the narration's description of "frantic movements" spans multiple turns without clear mechanical justification for the removal. Fix: Ensure conditions persist as long as their narrative descriptor is relevant.


## prompt_pipeline

### Actionable Issues

### Critical
- **<Extract State incorrectly removes reusable items upon use>** (pipeline: Extract State, turns: [8]) — Tag: `instruction_ignored`. Fix: Add explicit guidance that *using* an item does not equal *removing* it unless the narration states consumption/loss. Example: "Unlocking a door with a key retains the key."

### Major
- **<Extract Scene removes NPCs incorrectly during location transitions>** (pipeline: Extract Scene, turns: [10]) — Tag: `instruction_ignored`. Fix: Clarify that if an NPC is present in the previous turn's scene and narrated as moving to the new space (not leaving), they should remain in `present_npcs` or be updated, not removed.
- **<Extract Progress duplicates recent events across turns>** (pipeline: Extract Progress, turns: [13]) — Tag: `instruction_ignored`. Fix: Instruct the LLM to check the input's `recent_events` array for existing IDs/text before emitting new additions.

### Minor
- **<World Pack Style block wasted in Extractors>** (pipeline: All Extractors) — Tag: `wasted_tokens`. Fix: Remove `World Pack Style` from user prompts of Scene, State, and Progress pipelines. It is only relevant to Narrate.

### Issues

### Critical
- **<Extract State incorrectly removes reusable items upon use>** (pipeline: Extract State, turns: [8]) — Tag: `instruction_ignored`. Fix: Add explicit guidance that *using* an item does not equal *removing* it unless the narration states consumption/loss. Example: "Unlocking a door with a key retains the key."

### Major
- **<Extract Scene removes NPCs incorrectly during location transitions>** (pipeline: Extract Scene, turns: [10]) — Tag: `instruction_ignored`. Fix: Clarify that if an NPC is present in the previous turn's scene and narrated as moving to the new space (not leaving), they should remain in `present_npcs` or be updated, not removed.
- **<Extract Progress duplicates recent events across turns>** (pipeline: Extract Progress, turns: [13]) — Tag: `instruction_ignored`. Fix: Instruct the LLM to check the input's `recent_events` array for existing IDs/text before emitting new additions.

### Minor
- **<World Pack Style block wasted in Extractors>** (pipeline: All Extractors) — Tag: `wasted_tokens`. Fix: Remove `World Pack Style` from user prompts of Scene, State, and Progress pipelines. It is only relevant to Narrate.


## compaction

### Actionable Issues

- **(none)**

### Issues

- **(none)**

