# Checker Library Reference

## Overview

Each checker is an individual mechanical invariant registered with
`@register_checker`. Deterministic checkers run without an LLM.
LLM checkers use the configured checker model.

Checkers are organized by domain:

- **Beats**: `gm_beat_lifecycle`
- **Inventory & conditions**: `location_change`, `inventory_integrity`, `conditions_lifecycle`
- **Threads & arcs**: `thread_lifecycle`, `arc_goal_updates`
- **NPCs**: `npc_presence`
- **Pacing**: `pacing_directives`, `action_quality`, `phase_transition`, `recent_beats`, `phase_persistence`, `scene_age_tracking`, `climax_turn_counting`, `breather_enforcement`, `roll_band_consistency`, `beat_phase_validity`
- **Threads & arcs**: `thread_lifecycle`, `arc_goal_updates`, `thread_resolution_validity`, `new_thread_validity`, `arc_resolution_validity`, `goal_update_validity`
- **NPCs**: `npc_presence`, `compendium_lifecycle`
- **Sanitizer**: `sanitizer_lifecycle`
- **LLM-based**: `directive_tone_match`, `beat_narrative_chain`, `state_fidelity`
- **Scenario assertions**: `turn_assert` (called programmatically by eval runner, not in default registry)

## Eval Rubric

When inspecting a game, check one area at a time rather than running all checkers at once. See [RUBRIC.md](RUBRIC.md) for the prioritized checklist with what to look for, commands, and red flags per mechanic area.

## Checkers

### gm_beat_lifecycle

- **Type:** deterministic
- **Fields:** `state_snapshot`, `ruling`, `narrate_prompt`
- **What it checks:** Pending GM beat is consumed across turns, beat lifecycle is respected, binding block present on rolled turns
- **CLI:** `ev.py check TURN gm_beat_lifecycle`
- **Caveats:** Checks that `pending_gm_beat` from one turn is consumed or updated in the next. Verifies that when storyteller emits a GM beat, the state's `pending_gm_beat` matches its type. Rolled turns must include the BINDING block in narrate user prompt.

### location_change

- **Type:** deterministic
- **Fields:** `applied.location_change`, `state_snapshot.location` (or `extraction.storytell.rendered_user` for pre-delta location)
- **What it checks:** When a location change is emitted, the post-turn location ID differs from the previous turn's location ID
- **CLI:** `ev.py check TURN location_change`
- **Caveats:** Only checks turns where `applied.location_change` is present. First turn is skipped (no previous location to compare). Note: `extraction_context` is NOT stored in events; checkers must use `state_snapshot` or parse the storyteller prompt.

### inventory_integrity

- **Type:** deterministic
- **Fields:** `applied.inventory_add`, `applied.inventory_remove`, `state_snapshot.inventory` (or `extraction.storytell.rendered_user` for pre-delta inventory)
- **What it checks:** No negative inventory amounts, no overdraw (removing from zero-quantity items), no removal of non-existent items
- **CLI:** `ev.py check TURN inventory_integrity`
- **Caveats:** Checks state_snapshot inventory for negative amounts. Compares previous turn's inventory against current turn's removals to detect overdraw and removal of items that didn't exist. Note: `extraction_context` is NOT stored in events.

### conditions_lifecycle

- **Type:** deterministic
- **Fields:** `applied.pc_condition_add`, `applied.pc_condition_remove`, `state_snapshot.pc.conditions` (or `extraction.storytell.rendered_user` for pre-delta conditions)
- **What it checks:** Conditions present in ruling reason, no duplicate condition IDs
- **CLI:** `ev.py check TURN conditions_lifecycle`
- **Caveats:** Checks that condition IDs appear in the ruling's reason text (lowercase comparison). Dedup check is case-insensitive. Note: `extraction_context` is NOT stored in events.

### thread_lifecycle

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** thread_add entries appear in state after the turn, thread_update IDs reference existing threads
- **CLI:** `ev.py check TURN thread_lifecycle`
- **Caveats:** Checks the next turn's state_snapshot to verify thread_add was applied. thread_update IDs are validated against the current turn's state.arc.threads.

### arc_goal_updates

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** When storyteller emits a goal_update string, it matches arc.visible_goal in state
- **CLI:** `ev.py check TURN arc_goal_updates`
- **Caveats:** Only checks turns where storyteller emitted a non-empty string goal_update. Skips null or non-string goal_update values.

### npc_presence

- **Type:** deterministic
- **Fields:** `state_snapshot.compendium.npcs`, `applied.compendium_npc_update`
- **What it checks:** All NPC presence values in compendium are valid (`present`, `nearby`, `known`, `departed`, `archived`). Departed NPCs have required `departed_reason` and `departed_summary` fields.
- **CLI:** `ev.py check TURN npc_presence`
- **Caveats:** Only checks state_snapshot compendium entries, not extraction output. Note: `extraction_context` is NOT stored in events.

### pacing_directives

- **Type:** deterministic
- **Fields:** `ruling`, `narrate_prompt`, `extraction.storytell.rendered_user`
- **What it checks:** outcome_hint rendered in narrator prompt, directive rendered in storyteller prompt, removed directives not present, beat type variety maintained, surface_as consistency across consecutive same-type beats
- **CLI:** `ev.py check TURN pacing_directives`
- **Caveats:** Removed directives: "Overwhelm", "Pressure", "location pressure", "location imperative", "combat fatigue". Beat type variety warns if a single type exceeds 60% of all beats (requires 3+ beats). Surface_as consistency checks that consecutive same-type beats don't flip between "ambient" and "environmental" without a directive change. Phase constraint check verifies beat types are allowed for the current scene_phase per BEAT_PHASE_MAP. Uses regex word boundaries to avoid false positives from word variants (e.g., "overwhelmed" matching "Overwhelm").

### phase_transition

- **Type:** deterministic
- **Fields:** `pacing_context`
- **What it checks:** Phase engine transitions follow the state machine (SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION, RESOLUTION→BREATHER, BREATHER→RISING), climax_turn_count monotonicity, outcome_hint consistency during climax limit
- **CLI:** `ev.py check TURN phase_transition`
- **Caveats:** CLIMAX turn count must increment by 1 within CLIMAX phase. When climax_turn_count >= 4 (default limit), outcome_hint must be "transition".

### recent_beats

- **Type:** deterministic
- **Fields:** `state_snapshot`
- **What it checks:** recent_beats exists in state, capped at 5 entries, entry structure (turn/type/surface_as), monotonic turn numbers
- **CLI:** `ev.py check TURN recent_beats`
- **Caveats:** Default cap is 5 entries per config.recent_beats_max. Each entry must have turn, type, and surface_as fields.

### phase_persistence

- **Type:** deterministic
- **Fields:** `scene_phase`
- **What it checks:** scene_phase field present and valid on every turn (regression guard for phase-persistence bug)
- **CLI:** `ev.py check TURN phase_persistence`
- **Caveats:** Validates that scene_phase is one of SETUP/RISING/CLIMAX/RESOLUTION/BREATHER on every turn. The original bug caused phase to never be written to state, resetting every turn.

### scene_age_tracking

- **Type:** deterministic
- **Fields:** `state_snapshot`
- **What it checks:** scene_age increments by 1 each turn, resets to 0 on location change
- **CLI:** `ev.py check TURN scene_age_tracking`
- **Caveats:** scene_age = current_turn - location_entered_turn. First turn and location change turns are skipped (age is 0).

### climax_turn_counting

- **Type:** deterministic
- **Fields:** `pacing_context`
- **What it checks:** climax_turn_count increments by 1 within CLIMAX phase, resets to 0 on phase exit, starts at 1 when entering CLIMAX
- **CLI:** `ev.py check TURN climax_turn_counting`
- **Caveats:** climax_turn_count should be 0 when not in CLIMAX phase. Entering CLIMAX should set it to 1.

### breather_enforcement

- **Type:** deterministic
- **Fields:** `pacing_context`
- **What it checks:** breather auto-transitions to RISING after breather_max_turns (default 3), breather_turn_count increments correctly
- **CLI:** `ev.py check TURN breather_enforcement`
- **Caveats:** breather_turn_count should be 0 when not in BREATHER phase. Entering BREATHER should set it to 1. When breather_turn_count >= 3, next phase should be RISING.

### roll_band_consistency

- **Type:** deterministic
- **Fields:** `ruling`
- **What it checks:** band matches dice roll using rules engine, skill/difficulty are valid
- **CLI:** `ev.py check TURN roll_band_consistency`
- **Caveats:** Recomputes band from raw_total + stat_mod + diff_mod using `rules.compute_band()`. Validates skill is in VALID_SKILLS and difficulty is in DIFFICULTY_MOD.

### thread_resolution_validity

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** thread_resolve entries have valid id/resolution_state/outcome, referenced threads exist in state
- **CLI:** `ev.py check TURN thread_resolution_validity`
- **Caveats:** resolution_state must be one of "resolved", "failed", "abandoned". Thread IDs must exist in arc.threads or arc.completed_threads.

### new_thread_validity

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** thread_add entries have id/description/visible_goal, no duplicate thread ids
- **CLI:** `ev.py check TURN new_thread_validity`
- **Caveats:** id must be non-empty string. description and visible_goal must be non-empty strings. No duplicate thread ids in state after add.

### compendium_lifecycle

- **Type:** deterministic
- **Fields:** `applied.compendium_npc_update`, `state_snapshot`
- **What it checks:** NPCs added via compendium_npc_update appear in state.compendium.npcs after the turn
- **CLI:** `ev.py check TURN compendium_lifecycle`
- **Caveats:** Validates that every NPC id in applied.compendium_npc_update exists in state.compendium.npcs. Catches state application bugs.

### beat_phase_validity

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `pacing_context`
- **What it checks:** gm_beat.type is allowed for the current phase
- **CLI:** `ev.py check TURN beat_phase_validity`
- **Caveats:** Validates beat types against BEAT_PHASE_MAP. SETUP allows [pressure, complication, revelation]. RISING allows [pressure, complication, escalation, twist]. CLIMAX allows [pressure, complication, escalation, setback]. RESOLUTION allows [callback, breathing_room]. BREATHER allows [breathing_room, callback].

### arc_resolution_validity

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** arc_resolve has resolution + visible_goal + goal_context, drop_threads reference existing threads
- **CLI:** `ev.py check TURN arc_resolution_validity`
- **Caveats:** resolution, visible_goal, and goal_context must be non-empty strings. drop_threads IDs must exist in arc.threads.

### goal_update_validity

- **Type:** deterministic
- **Fields:** `extraction.storytell`, `state_snapshot`
- **What it checks:** goal_update is non-empty string, must differ from previous visible_goal
- **CLI:** `ev.py check TURN goal_update_validity`
- **Caveats:** Skips turns where arc_resolve is also emitted (arc_resolve.visible_goal supersedes goal_update). Validates goal_update differs from next turn's arc.visible_goal.

### action_quality

- **Type:** deterministic
- **Fields:** `actions`, `ruling`
- **What it checks:** Actions list is non-empty, all actions are distinct
- **CLI:** `ev.py check TURN action_quality`
- **Caveats:** Simple count/distinct check. Reports failures for empty actions lists or duplicate entries.

### sanitizer_lifecycle

- **Type:** deterministic
- **Fields:** `threads_updated`, `threads_removed`, `threads_resolved`, `threads_added`, `goal_changed`, `changes_detail`
- **What it checks:** Sanitizer thread operations reference valid state threads, no goal_changed noops, orphan thread detection
- **CLI:** `ev.py check TURN sanitizer_lifecycle`
- **Caveats:** Requires non-turn events (`kind: "sanitizer"`) and state access (`--save-dir`). Returns inconclusive if no sanitizer events found. Checks that threads_updated/removed/resolved IDs exist in state.arc.threads, and threads_added IDs don't conflict. Orphan detection finds threads in state never referenced by any sanitizer event.

### directive_tone_match

- **Type:** llm
- **Fields:** `ruling.band`, `ruling.intent`, `narrate`
- **What it checks:** Narration tone aligns with ruling band (success→positive, fail→tense, crit_fail→severe)
- **CLI:** `ev.py check TURN directive_tone_match --llm`
- **Caveats:** Uses the configured checker model. Evaluates the first event only. Returns JSON with passed/score/reasoning/finding.

### beat_narrative_chain

- **Type:** llm
- **Fields:** `state_snapshot.meta.pending_gm_beat`, `narrate`
- **What it checks:** GM beat produces observable narrative consequence in current and next turn narration
- **CLI:** `ev.py check TURN beat_narrative_chain --llm`
- **Caveats:** Uses the configured checker model. Evaluates first event's pending beat type against its narration and next turn's narration if available. A "pressure" beat should create urgency, "complication" should introduce an obstacle, "escalation" should raise stakes.

### state_fidelity

- **Type:** llm
- **Fields:** `narrate`, `state_snapshot`, `applied.inventory_add`, `applied.inventory_remove`, `applied.pc_condition_add`, `applied.pc_condition_remove`
- **What it checks:** State extraction matches what narration describes — no missing or unsupported changes
- **CLI:** `ev.py check TURN state_fidelity --llm`
- **Caveats:** Uses the configured checker model. Evaluates first event only. Narration must explicitly mention or strongly imply each state change. Missing changes described in narration are failures. Extra changes not supported by narration are also failures. Note: `extraction_context` is NOT stored in events; the LLM checker receives state_snapshot as context instead.

### turn_assert

- **Type:** deterministic
- **Fields:** None (takes assertions as parameter)
- **What it checks:** Validates per-turn structured assertions from YAML scenarios (stream/field/expected/min_amount)
- **CLI:** Called programmatically by `ev.py eval run`, not in default registry
- **Caveats:** Supports streams: `ruling`, `extract.state`, `state_snapshot`. Assertions specify a field dotpath, expected value, and optional min_amount threshold. Score is ratio of passed assertions to total. Note: `extraction_context` stream is NOT available (field never stored in events).

## Running Checkers

### Single turn, specific checkers

```bash
ev.py check 5 gm_beat_lifecycle
```

### Single turn, all checkers

```bash
ev.py check 5 --all
```

### All turns, all checkers

```bash
ev.py check --all
```

### Include LLM checkers

```bash
ev.py check 5 --all --llm
```

### Override checker model

```bash
ev.py check 5 --all --checker-model "some-model"
```

### Specify save directory (needed for sanitizer_lifecycle)

```bash
ev.py check 5 --all --save-dir saves/another-game
```

## Checker Registry

The checker registry is maintained in `ccya/ev/checkers/__init__.py`. Each checker module is imported at the bottom of that file to register its checkers. To add a new checker:

1. Create a new module in `ccya/ev/checkers/`
2. Decorate the checker function with `@register_checker(id, type, requires_fields, description, ...)`
3. Import the module in `ccya/ev/checkers/__init__.py`
