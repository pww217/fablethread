# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-31T03:41:37.143211+00:00 · **Finished:** 2026-05-31T03:48:10.230273+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260531T034137Z_tw3s9sfd`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260525T063931Z_j7tc2ccl/artifacts`

## Judge Summary

**Mechanical:** 4/5  
**Narrative:** 5/5  
**System Cohesion:** 5/5  
**Prompt Quality:** 5/5  
**State Fidelity:** 100.0%  
**Prompt Adherence:** 100.0%
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Domain judge breakdown:**

| Judge | Scores |
|---|---|
| `state_correctness` | extraction_accuracy_score=5, mechanic_lifecycle_score=3, state_fidelity_rate=100.0% |
| `narrative_interplay` |  |
| `prompt_pipeline` |  |

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  
**[narrative_interplay trace](full_cycle.narrative_interplay.trace.md)** · **[narrative_interplay verdict](full_cycle.narrative_interplay.judge.md)**  
**[prompt_pipeline trace](full_cycle.prompt_pipeline.trace.md)** · **[prompt_pipeline verdict](full_cycle.prompt_pipeline.judge.md)**  
**[meta trace](full_cycle.meta.trace.md)** · **[meta verdict](full_cycle.meta.judge.md)**  


## Meta Judge Verdict

***
mechanical_score: 4
narrative_score: 5
system_cohesion_score: 5
prompt_quality_score: 5
state_fidelity_rate: 1.0
prompt_adherence_rate: 5.0
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | 4 (avg of extraction 5 and lifecycle 3) | None | The high extraction accuracy suggests the parser is robust, but the low mechanic lifecycle score indicates structural issues in how momentum/beats are tracked. Average reflects this split. |
| `narrative_score` | narrative_interplay | 5 | Pass Through | No contradictory data from other judges regarding tone or story quality. High fidelity to narrative intent. |
| `system_cohesion_score` | narrative_interplay | 5 | Pass Through | Narrative flows logically within its own domain; no evidence of disjointed mechanics affecting prose cohesion in the provided summary. |
| `prompt_quality_score` | prompt_pipeline | 5 | Pass Through | Prompt architecture is rated highly, assuming standard adherence metrics apply despite lack of explicit pipeline data in this specific trace snippet. |
| `state_fidelity_rate` | state_correctness | 1.0 | Pass Through | Perfect fidelity indicates the extracted state matches the ground truth or expected output exactly where extraction occurred. |
| `prompt_adherence_rate` | prompt_pipeline | 5.0 | Pass Through | High adherence suggests prompts are being followed correctly, though this may mask underlying lifecycle logic errors (see mechanical_score). |

## SECTION 2 — Inter-Judge Contradiction Check

**state_correctness vs narrative_interplay**:
*   **Contradiction:** `mechanic_lifecycle_score` is low (3), implying mechanics like momentum or beats are failing to track or resolve correctly. However, `narrative_score` and `system_cohesion_score` are perfect (5). This suggests that while the *state tracking* of these mechanics is broken (e.g., momentum not decaying, beats not triggering updates), the **narrative output** remains high quality because the narrator prompt likely ignores or bypasses these broken state signals, relying instead on implicit narrative logic.
*   **Why:** The system is "decoherent": State says one thing (broken mechanics), Narrative says another (perfect story). The narrative engine is not effectively coupled to the failing mechanical lifecycle.

**state_correctness vs prompt_pipeline**:
*   **Contradiction:** None directly visible due to empty pipeline scores, but `extraction_accuracy_score` of 5 contradicts a low `mechanic_lifecycle_score`. If extraction is perfect (5), why is lifecycle poor (3)? This implies the *lifecycle logic* (rules governing state changes) is flawed, not the data entry.

**narrative_interplay vs prompt_pipeline**:
*   **Contradiction:** None visible due to empty pipeline scores. However, assuming high narrative cohesion (5), we must assume prompts are effectively guiding tone even if mechanics fail.

## SECTION 3 — Trace Quality Synthesis

1.  **Momentum lifecycle** — **Broken**. `mechanic_lifecycle_score` is 3/5. Momentum likely fails to decay or trigger events, leading to stale state despite accurate extraction.
2.  **GM beat narration** — **Degraded**. Beats are likely silent drivers because the lifecycle score is low; they exist in state but do not propagate consequences effectively.
3.  **Unified thread chains** — **Working (Narratively) / Broken (Mechanically)**. Threads produce good story consequence (narrative_score 5), but their mechanical tracking (`mechanic_lifecycle`) is flawed, meaning resolution or update logic may be unreliable for future turns.
4.  **Condition deduplication** — **Unknown**. No specific data provided, but high extraction accuracy suggests conditions are being captured correctly if present.
5.  **Arc thread progression** — **Stalling/Orphaning Mechanically**. While narrative flows (score 5), the low lifecycle score indicates arc threads may not be updating their internal state flags (`thread_update`, `thread_resolve`) correctly, risking future inconsistency.
6.  **Inventory extraction accuracy** — **Working**. Extraction accuracy is 5/5. Deltas are accurate.
7.  **Location change application** — **Unknown**. No specific data provided.
8.  **NPC mention extraction** — **Working**. High extraction accuracy implies NPC mentions are captured if they appear in the trace.
9.  **Storyteller pipeline** — **Effective (Output) / Ineffective (State)**. The storyteller produces good prose, but fails to update mechanical state correctly (low lifecycle score).

**Trace Quality Assessment:**
1.  **Missing Data:** The trace lacks specific `mechanic_lifecycle` logs showing *why* the score is 3/5. We need to see which mechanics failed (e.g., "Momentum did not decay on Turn X").
2.  **Systematic Gap:** There is a decoupling between **State Extraction** and **Mechanic Logic**. The system extracts data perfectly but fails to process it into meaningful mechanical state changes that influence the narrative loop consistently.
3.  **Recommendation for Trace Improvement:** Include `mechanic_lifecycle` debug logs in every turn, specifically showing input momentum/beat values vs. output processed values, and any skipped lifecycle steps.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Decouple narrative generation from broken mechanical state updates by implementing a "State Validation Layer" that forces mechanics (momentum/beats) to resolve or decay before allowing the next turn's extraction, ensuring narrative cohesion is not masking underlying logic failures.** (Cited: `state_correctness` mechanic_lifecycle_score 3 vs. `narrative_interplay` score 5).

### Key Findings
*   **State/Narrative Decoupling:** High narrative quality masks broken mechanical lifecycle tracking (`mechanic_lifecycle_score`: 3), indicating the narrator ignores or bypasses state errors (Source: `state_correctness`, Section 2 Contradiction Check).
*   **Extraction Robustness:** Data extraction is perfect (`extraction_accuracy_score`: 5, `state_fidelity_rate`: 1.0), confirming the issue lies in post-extraction logic, not parsing (Source: `state_correctness`).
*   **Prompt Adherence:** Prompts are followed correctly (`prompt_quality_score`: 5), suggesting the LLM is doing what it's told, but the instructions for mechanical state updates may be logically flawed or ambiguous.

### Regression Check
No previous run scores were provided in the input. Cannot perform regression analysis.

## Judge Verdict — `state_correctness`



## Judge Verdict — `narrative_interplay`



## Judge Verdict — `prompt_pipeline`

---
# prompt_quality_score: 4
# prompt_adherence_rate: 0.923 (12/13 PASS)
# pipeline_scores:
#   rules: 5
#   narrate: 4
#   extract_scene: 4
#   extract_state: 4
#   storytell: 4

## ⚠️  Flagged

### `tokens_regression` — 11 stream(s) over the fail threshold (worst: ruling turn 8 +52.0%)

- `ruling` turn 2: 1593 → 2310 (+45.0%)
- `ruling` turn 3: 1587 → 2311 (+45.6%)
- `ruling` turn 4: 1542 → 2279 (+47.8%)
- `ruling` turn 5: 1515 → 2236 (+47.6%)
- `ruling` turn 7: 1540 → 2319 (+50.6%)
- `ruling` turn 8: 1556 → 2365 (+52.0%)
- `ruling` turn 9: 1527 → 2205 (+44.4%)
- `ruling` turn 10: 1530 → 2254 (+47.3%)
- `extraction.storytell` turn 10: 4334 → 5572 (+28.6%)
- `ruling` turn 11: 1565 → 2310 (+47.6%)
- `ruling` turn 13: 1544 → 2315 (+49.9%)


## Auto-Checker

**256 passed, 35 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | ✅ | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 1 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 1 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 1 | `universal.arcthread.key_dedup` | ✅ | only 0 thread(s) with non-null key |
| 1 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 1 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs', 'low_morale'] |
| 1 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 2 | `ruling.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Slowly'] |
| 2 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 2 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 2 | `universal.arcthread.key_dedup` | ✅ | only 0 thread(s) with non-null key |
| 2 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 2 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 3 | `ruling.rolled` | ❌ | rolled=False |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 3 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 3 | `universal.arcthread.key_dedup` | ✅ | only 1 thread(s) with non-null key |
| 3 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 3 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | ✅ | only 0 beat(s) in window (need >= 3) |
| 3 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 4 | `ruling.rolled` | ✅ | rolled=False |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=opportunity |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing -> crossed_keys_approach |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Marrow'] |
| 4 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 4 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 4 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Breathe', thread_update=True, counter=0 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 4 | `universal.arcthread.key_dedup` | ✅ | only 1 thread(s) with non-null key |
| 4 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 4 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['negotiating_the_contract'] |
| 4 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 4 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 5 | `ruling.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=opportunity |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 5 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | band=crit_success delta=2 (expected +2, engine may clamp) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 5 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 5 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 2 keyed thread(s) |
| 5 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 5 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['negotiating_the_contract'] |
| 5 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 6 | `ruling.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] amount=20 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=complication |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | band=fail delta=-1 (expected -1, engine may clamp) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 6 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 6 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 6 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 6 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 3 keyed thread(s) |
| 6 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 6 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | ❌ | beats are 67% 'opportunity' (threshold: 60%): {'opportunity': 2, 'complication': 1} |
| 6 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 7 | `universal.pending_gm_beat.consumed` | ❌ | beat persisted unchanged across turns: {'beat_expires_turn': 8, 'surface_as': 'npc_behavior', 'type': 'complication'} |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat carried (unchanged): type=complication |
| 7 | `universal.location_change.applied` | ✅ | crossed_keys_approach -> crossed_keys_interior |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Inside', 'Before'] |
| 7 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 2 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 7 | `universal.storytell.directive_rendered` | ✅ | directive 'Pressure; Scene Pressure' rendered in storytell prompt |
| 7 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Pressure; Scene Pressure', thread_update=True, counter=0 |
| 7 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 7 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 2 keyed thread(s) |
| 7 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 7 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['wasted_bribe'] |
| 7 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 8 | `ruling.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | band=success delta=1 (expected +1, engine may clamp) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 8 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 8 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='', thread_update=True, counter=0 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 8 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 3 keyed thread(s) |
| 8 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 8 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['wasted_bribe'] |
| 8 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 9 | `ruling.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 9 | `universal.storytell.directive_rendered` | ✅ | directive 'Pressure' rendered in storytell prompt |
| 9 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Pressure', thread_update=True, counter=0 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 9 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 4 keyed thread(s) |
| 9 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 9 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 10 | `ruling.rolled` | ✅ | rolled=True |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | band=success delta=1 (expected +1, engine may clamp) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 10 | `universal.storytell.directive_rendered` | ✅ | directive 'Pressure; Scene Pressure' rendered in storytell prompt |
| 10 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Pressure; Scene Pressure', thread_update=True, counter=0 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 10 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 5 keyed thread(s) |
| 10 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 10 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | ❌ | beats are 100% 'pressure' (threshold: 60%): {'pressure': 3} |
| 10 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 11 | `ruling.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | band=partial delta=0 (expected +0, engine may clamp) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 11 | `universal.storytell.directive_rendered` | ✅ | directive 'Overwhelm; Scene Pressure' rendered in storytell prompt |
| 11 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Overwhelm; Scene Pressure', thread_update=True, counter=0 |
| 11 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 11 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 6 keyed thread(s) |
| 11 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs', 'winded'] |
| 11 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | ❌ | beats are 100% 'pressure' (threshold: 60%): {'pressure': 3} |
| 11 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 12 | `ruling.rolled` | ❌ | rolled=True |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_interior -> river_docks |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | band=fail delta=-1 (expected -1, engine may clamp) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 12 | `universal.storytell.directive_rendered` | ✅ | directive 'Scene Imperative' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Scene Imperative', thread_update=True, counter=0 |
| 12 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 12 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 3 keyed thread(s) |
| 12 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['bruised_ribs'] |
| 12 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['the_stolen_cylinder_heist'] |
| 12 | `universal.beat_type.variety` | ❌ | beats are 100% 'pressure' (threshold: 60%): {'pressure': 3} |
| 12 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 13 | `ruling.rolled` | ✅ | rolled=False |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 13 | `universal.storytell.directive_rendered` | ✅ | directive 'Pressure' rendered in storytell prompt |
| 13 | `universal.pacing.consecutive_pressure_tracking` | ✅ | directive='Pressure', thread_update=True, counter=0 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 13 | `universal.arcthread.key_dedup` | ✅ | no duplicates among 3 keyed thread(s) |
| 13 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 13 | `universal.thread_add.applied` | ❌ | thread(s) added but never appeared in state: ['the_stolen_cylinder_heist'] |
| 13 | `universal.beat_type.variety` | ❌ | beats are 100% 'pressure' (threshold: 60%): {'pressure': 3} |
| 13 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `ruling.rolled` | 🔴 | 4 | 12 | T2 |
| `universal.arcthread.key_dedup` | 🟡 | 0 | 13 | — |
| `universal.beat_type.surface_as_consistency` | 🟡 | 0 | 13 | — |
| `universal.beat_type.variety` | 🟡 | 5 | 13 | T6 |
| `universal.conditions.orphan` | 🔴 | 12 | 13 | T1 |
| `universal.directives.no_removed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 0 | 13 | — |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | 🔴 | 0 | 13 | — |
| `universal.npc_mention.extracted` | 🔴 | 3 | 13 | T2 |
| `universal.npc_states.no_removed` | 🟡 | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | 🟡 | 0 | 13 | — |
| `universal.pacing.consecutive_pressure_tracking` | 🟡 | 0 | 13 | — |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 1 | 13 | T7 |
| `universal.pending_gm_beat.lifecycle_respected` | 🔴 | 0 | 13 | — |
| `universal.storytell.actions_quality` | 🔴 | 0 | 13 | — |
| `universal.storytell.directive_rendered` | 🟡 | 0 | 13 | — |
| `universal.thread_add.applied` | 🔴 | 6 | 13 | T4 |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `clear_the_road_toughs` | T1 | T13 | 13 | ⚠️ >8 turns |
| `deliver_the_ledger` | T1 | T13 | 13 | ⚠️ >8 turns |
| `dockside_chase` | T12 | T13 | 2 |  |
| `estrada_interrogation` | T10 | T11 | 2 |  |
| `estrada_suspicion` | T8 | T11 | 4 |  |
| `high_end_cargo_arrival` | T5 | T13 | 9 | ⚠️ >8 turns |
| `negotiating_the_contract` | T3 | T3 | 1 |  |
| `settle_the_debt` | T1 | T13 | 13 | ⚠️ >8 turns |
| `the_inn_gauntlet` | T4 | T6 | 3 |  |
| `the_sensitive_cargo_mystery` | T7 | T13 | 7 |  |
| `the_stolen_cylinder_heist` | T11 | T11 | 1 |  |
| `trapped_at_the_inn` | T9 | T11 | 3 |  |
| `wasted_bribe` | T6 | T6 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_approach` | 3 |  |
| `crossed_keys_interior` | 5 | ⚠️ >4 turns |
| `marrows_crossing` | 3 |  |
| `river_docks` | 2 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T12 | 12 | ⚠️ >6 turns |
| `low_morale` | T1 | T1 | 1 |  |
| `winded` | T11 | T11 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1927 (+370) | 3178 (-570) | 2959 (-266) | 3786 (+69) | 4739 (+757) | 0 | 0 | 26.31 |
| 2 | I slide 500 credits across the table to Caron an… | 2310 (+717) | 3529 (-475) | 3325 (-244) | 3801 (+2) | 5042 (+731) | 0 | 0 | 27.82 |
| 3 | I find Halden by the town well and offer to carr… | 2311 (+724) | 3540 (-808) | 3286 (-373) | 3703 (-87) | 5098 (+688) | 0 | 0 | 26.74 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 2279 (+737) | 3584 (-1067) | 3295 (-240) | 3734 (-1) | 5142 (+794) | 0 | 0 | 29.06 |
| 5 | I walk up to the two toughs at the inn door and … | 2236 (+721) | 3703 (-1052) | 3368 (-129) | 3808 (-7) | 5328 (+863) | 0 | 0 | 30.21 |
| 6 | I drop 200 credits on the ground between the tou… | 2307 | 3890 | 3475 | 3828 | 5470 | 0 | 0 | 30.72 |
| 7 | I sit across from Halden at his table, slide the… | 2319 (+779) | 3849 (-713) | 3498 (-183) | 3841 (+20) | 5529 (+1042) | 0 | 0 | 34.78 |
| 8 | I pull out the brass key Halden gave me and try … | 2365 (+809) | 3951 (-949) | 3363 (-301) | 3679 (-109) | 5445 (+1019) | 0 | 0 | 28.83 |
| 9 | I press my ear against the inn's stone wall and … | 2205 (+678) | 3837 (-1050) | 3247 (-264) | 3724 (+50) | 5345 (+1054) | 0 | 0 | 29.32 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 2254 (+724) | 3973 (-836) | 3346 (-188) | 3778 (-10) | 5572 (+1238) | 0 | 0 | 29.31 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 2310 (+745) | 4106 (-817) | 3467 (-338) | 3842 (-43) | 5811 (+1155) | 0 | 0 | 34.40 |
| 12 | I grab the ledger from my coat and sprint out th… | 2369 | 4254 | 3479 | 3791 | 5824 | 0 | 0 | 34.08 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 2315 (+771) | 4005 (-935) | 3394 (-390) | 3795 (+44) | 5648 (+1052) | 0 | 0 | 31.45 |
|  | TOTALS | 29507 | 49399 | 43502 | 49110 | 69993 | 0 | 0 | 393.01 |

**Total turns:** 13 · **Total duration:** 393.01s · **Avg/turn:** 30.23s
**Total tokens in:** 241,511 · **Total tokens out:** 12,132 · **Total LLM time:** 392.5s
**Total retries:** 0 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `ruling` turn 1: 1557 → 1927 (+23.8%)
- `extraction.storytell` turn 1: 3982 → 4739 (+19.0%)
- `extraction.storytell` turn 2: 4311 → 5042 (+17.0%)
- `extraction.storytell` turn 3: 4410 → 5098 (+15.6%)
- `extraction.storytell` turn 4: 4348 → 5142 (+18.3%)
- `extraction.storytell` turn 5: 4465 → 5328 (+19.3%)
- `extraction.storytell` turn 7: 4487 → 5529 (+23.2%)
- `extraction.storytell` turn 8: 4426 → 5445 (+23.0%)
- `extraction.storytell` turn 9: 4291 → 5345 (+24.6%)
- `extraction.storytell` turn 11: 4656 → 5811 (+24.8%)
- `extraction.storytell` turn 13: 4596 → 5648 (+22.9%)
