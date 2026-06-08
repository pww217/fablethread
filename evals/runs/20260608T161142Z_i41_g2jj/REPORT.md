# Eval Report — `baseline`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-08T16:11:42.303161+00:00 · **Finished:** 2026-06-08T16:17:35.158347+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T161142Z_i41_g2jj`  
**Track:** baseline  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T071015Z_pc3119x2/artifacts`
**Scoring philosophy:** aggregate quality (baseline)  

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**State Fidelity:** 100.0%  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**[state_correctness trace](baseline.state_correctness.trace.md)** · **[state_correctness verdict](baseline.state_correctness.judge.md)**  


## Judge Verdict — `state_correctness`

state_fidelity_rate: 0.6666666666666666
extraction_accuracy_score: 2
mechanic_lifecycle_score: 1

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**288 passed, 22 failed**

> **Legend:** `[PASS]` = assertion passed · `[FAIL]` = assertion failed  
| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | [PASS] | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | [PASS] | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | [PASS] | (first turn) |
| 1 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 1 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 1 | `universal.inventory.no_overdraw` | [PASS] | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 1 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 1 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 1 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 1 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 1 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 1 | `universal.inventory.remove_existence` | [PASS] | (first turn) |
| 1 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 1 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 1 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 2 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 2 | `universal.location_change.applied` | [PASS] | (no change) |
| 2 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 2 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 2 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=1 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 2 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 2 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 2 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 2 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['dusty_throat'] |
| 2 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 3 | `ruling.rolled` | [PASS] | rolled=False |
| 3 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 3 | `universal.location_change.applied` | [PASS] | (no change) |
| 3 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 3 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 3 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 3 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 3 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 3 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 3 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 3 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 3 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 4 | `ruling.rolled` | [PASS] | rolled=True |
| 4 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 4 | `universal.location_change.applied` | [PASS] | (no change) |
| 4 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 4 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | [PASS] | band=crit_success delta=2 (expected +2, engine may clamp) |
| 4 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 4 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='revelation' (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 4 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 4 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 4 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 4 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['dusty_throat'] |
| 4 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 4 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 5 | `ruling.rolled` | [PASS] | rolled=True |
| 5 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 5 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> assay_office |
| 5 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 5 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | [PASS] | band=crit_success delta=1 (expected +2, engine may clamp) |
| 5 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | [PASS] | directive 'Scene Pressure' rendered in storytell prompt |
| 5 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='revelation', counter=0 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 5 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 5 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 5 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 5 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 5 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 5 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 5 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 5 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 6 | `ruling.rolled` | [FAIL] | rolled=True |
| 6 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 6 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> sheriffs_office |
| 6 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 6 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | [PASS] | band=fail delta=-1 (expected -1, engine may clamp) |
| 6 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 6 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 6 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='complication' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 6 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=3, floor=-3) |
| 6 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 6 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 6 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 6 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 6 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | [FAIL] | beats are 67% 'revelation' (threshold: 60%): {'revelation': 2, 'complication': 1} |
| 6 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 7 | `ruling.rolled` | [FAIL] | rolled=False |
| 7 | `extract.state.inventory_add` | [FAIL] | inventory_add[torn_map] not found |
| 7 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=escalation |
| 7 | `universal.location_change.applied` | [PASS] | (no change) |
| 7 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 7 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 7 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 7 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 7 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 7 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=3 (expected 0) |
| 7 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 7 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 7 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 7 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 7 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 7 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 7 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 8 | `extract.state.inventory_remove` | [FAIL] | inventory_remove[credits] not found |
| 8 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 8 | `universal.location_change.applied` | [PASS] | (no change) |
| 8 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 8 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 8 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 8 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=1 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 8 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 8 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 8 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 8 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 9 | `ruling.rolled` | [FAIL] | rolled=True |
| 9 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 9 | `universal.location_change.applied` | [PASS] | (no change) |
| 9 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 9 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | [PASS] | band=success delta=1 (expected +1, engine may clamp) |
| 9 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 9 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 9 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='escalation', counter=2 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 9 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 9 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 9 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 9 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 9 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['rattled'] |
| 9 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 10 | `ruling.rolled` | [FAIL] | rolled=False |
| 10 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=escalation |
| 10 | `universal.location_change.applied` | [PASS] | sheriffs_office -> general_store |
| 10 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 10 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 10 | `universal.inventory.no_overdraw` | [PASS] | checked 1 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 10 | `universal.storytell.directive_rendered` | [PASS] | directive 'Scene Pressure; Resolve a Threat' rendered in storytell prompt |
| 10 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=3 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=2, floor=-3) |
| 10 | `universal.pacing.floor_relief` | [PASS] | beat_locked=True, storytell_type='pressure' → floor relief injected breathing_room |
| 10 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 10 | `universal.inventory.remove_existence` | [PASS] | checked 1 removes |
| 10 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 10 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 10 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | [FAIL] | beats are 67% 'pressure' (threshold: 60%): {'pressure': 2, 'escalation': 1} |
| 10 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 11 | `extract.state.pc_condition_remove` | [FAIL] | pc_condition_remove[bruised_ribs] not found |
| 11 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 11 | `universal.location_change.applied` | [PASS] | sheriffs_office -> red_canyon_cliffs |
| 11 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 11 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 11 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 11 | `universal.storytell.directive_rendered` | [PASS] | directive 'Pressure' rendered in storytell prompt |
| 11 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 11 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 11 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 11 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 11 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 11 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 11 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 11 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['threatened'] |
| 11 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 11 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 12 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 12 | `universal.location_change.applied` | [PASS] | (no change) |
| 12 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 12 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | [PASS] | band=success delta=1 (expected +1, engine may clamp) |
| 12 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 12 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 12 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 12 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 12 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 12 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 12 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 12 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 13 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 13 | `universal.location_change.applied` | [PASS] | (no change) |
| 13 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 13 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 13 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 13 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 13 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 13 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type=None (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 13 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=3, floor=-3) |
| 13 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 13 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 13 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 13 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 13 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 13 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 13 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 13 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |

## Universal Assert Results

> **Legend:** `[SYSTEM]` = system integrity failure (red severity) · `[PACING]` = pacing/perfection concern (yellow severity)  
| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.state.inventory_add` | [SYSTEM] | 1 | 1 | T7 |
| `extract.state.inventory_remove` | [SYSTEM] | 1 | 1 | T8 |
| `extract.state.pc_condition_remove` | [SYSTEM] | 1 | 1 | T11 |
| `ruling.rolled` | [SYSTEM] | 4 | 8 | T6 |
| `universal.beat_type.surface_as_consistency` | [PACING] | 0 | 13 | — |
| `universal.beat_type.variety` | [PACING] | 2 | 13 | T6 |
| `universal.conditions.orphan` | [SYSTEM] | 4 | 13 | T2 |
| `universal.directives.no_removed` | [PACING] | 0 | 13 | — |
| `universal.goal_update.applied` | [PACING] | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.no_overdraw` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.remove_existence` | [SYSTEM] | 0 | 13 | — |
| `universal.location_change.applied` | [SYSTEM] | 0 | 13 | — |
| `universal.momentum.band_delta` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.binding_present` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | [SYSTEM] | 0 | 13 | — |
| `universal.npc_states.no_removed` | [PACING] | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | [PACING] | 0 | 13 | — |
| `universal.pacing.consecutive_pressure_tracking` | [SYSTEM] | 6 | 13 | T1 |
| `universal.pacing.floor_no_relief` | [PACING] | 0 | 13 | — |
| `universal.pacing.floor_relief` | [PACING] | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | [SYSTEM] | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | [SYSTEM] | 0 | 13 | — |
| `universal.storytell.actions_quality` | [SYSTEM] | 3 | 13 | T3 |
| `universal.storytell.directive_rendered` | [PACING] | 0 | 13 | — |
| `universal.thread_add.applied` | [SYSTEM] | 0 | 13 | — |
| `universal.thread_update.valid_id` | [SYSTEM] | 0 | 13 | — |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `canyon_exploration_danger` | T9 | T10 | 2 |  |
| `clear_the_road_toughs` | T0 | T0 | 1 |  |
| `deliver_the_ledger` | T0 | T11 | 12 | ⚠️ >8 turns |
| `investigate_harker_disappearance` | T7 | T12 | 6 |  |
| `settle_the_debt` | T0 | T9 | 10 | ⚠️ >8 turns |
| `street_confrontation` | T8 | T8 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `assay_office` | 1 |  |
| `dustfall_outskirts` | 0 |  |
| `dustfall_saloon` | 3 |  |
| `general_store` | 1 |  |
| `marrows_crossing` | 1 |  |
| `red_canyon_cliffs` | 3 |  |
| `sheriffs_office` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `dusty_throat` | T1 | T2 | 2 |  |
| `exhausted` | T9 | T12 | 4 |  |
| `rattled` | T6 | T6 | 1 |  |
| `threatened` | T8 | T8 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | I ride into Dustfall and tie my horse at the liv… | 1117 (+0) | 3266 (+0) | 2841 (-70) | 1587 (-70) | 2701 (-48) | 0 | 0 | 31.12 |
| 2 | I step up to the bar and ask for a glass of wate… | 1278 (-77) | 3477 (-133) | 3093 (-104) | 1683 (-2) | 3051 (-158) | 0 | 0 | 21.96 |
| 3 |  | — | — | 0 (-3256) | 0 (-1654) | 0 (-3251) | 0 | 0 | 21.82 |
| 3 | I lean on the bar and ask what happened to Old M… | 1356 (+1) | 3676 (-74) | 3214 (+5) | 1704 (+63) | 3158 (-134) | 0 | 0 | 25.35 |
| 4 | I head over to the assay office to see if Harker… | 1358 (+28) | 3721 (-52) | 3220 (-92) | 1684 (-49) | 3287 (-206) | 0 | 0 | 31.78 |
| 5 | I walk to the sheriff's office and ask if he's f… | 1372 | 3807 | 3269 | 1721 | 3428 | 0 | 0 | 23.82 |
| 5 |  | — | — | 0 (-3452) | 0 (-1709) | 0 (-3480) | 0 | 0 | 23.83 |
| 6 | The sheriff gives me Harker's cabin key. I walk … | 1372 (-6) | 3915 (-137) | 3340 (-55) | 1709 (+47) | 3474 (-153) | 0 | 0 | 29.14 |
| 7 | I look through Harker's desk and find a locked t… | 1377 (+25) | 3986 (-10) | 3331 (-6) | 1725 (+24) | 3555 (-88) | 0 | 0 | 27.77 |
| 8 | I head back to the general store to buy supplies… | 1365 | 3957 | 3340 | 1747 | 3627 | 0 | 0 | 37.51 |
| 9 | I saddle up and ride out to Red Canyon. The trai… | 1429 (+61) | 4124 (-9) | 3325 (-46) | 1762 (-11) | 3654 (+23) | 0 | 0 | 27.13 |
| 10 | I find a camp at the base of the canyon wall. Tw… | 1368 (-15) | 4127 (-26) | 3307 (-114) | 1785 (+77) | 3662 (-74) | 0 | 0 | 26.23 |
| 10 |  | — | — | 0 | 0 | 0 | 0 | 0 | 25.31 |
| 11 | The men surrender. I find Harker tied up in a ne… | 1394 (+5) | 4173 (-73) | 3370 (-12) | 1810 (+118) | 3735 (-25) | 0 | 0 | 0.00 |
| 12 | Harker and I ride back to Dustfall together. He'… | 1440 (+92) | 4134 (-51) | 3365 (+17) | 1748 (+77) | 3676 (-48) | 0 | 0 | 0.00 |
| 13 | I walk Harker to the doc's office and then head … | 1384 (+38) | 4107 (-49) | 3360 (-29) | 1813 (+99) | 3670 (-98) | 0 | 0 | 0.00 |
|  | TOTALS | 17610 | 50470 | 42375 | 22478 | 44678 | 0 | 0 | 352.77 |

**Total turns:** 16 · **Total duration:** 352.77s · **Avg/turn:** 22.05s
**Total tokens in:** 177,611 · **Total tokens out:** 10,554 · **Total LLM time:** 333.4s
**Total retries:** 0 · **Total parse failures:** 0

