# Checker Library Reference

## Overview

Each checker is an individual mechanical invariant registered with
`@register_checker`. Deterministic checkers run without an LLM.
LLM checkers use the configured checker model.

Checkers are organized by domain:

- **Momentum & beats**: `momentum_lifecycle`, `gm_beat_lifecycle`
- **Inventory & conditions**: `location_change`, `inventory_integrity`, `conditions_lifecycle`
- **Threads & arcs**: `thread_lifecycle`, `arc_goal_updates`
- **NPCs**: `npc_presence`
- **Pacing**: `pacing_directives`, `action_quality`
- **Sanitizer**: `sanitizer_lifecycle`
- **LLM-based**: `directive_tone_match`, `beat_narrative_chain`, `state_fidelity`
- **Scenario assertions**: `turn_assert` (called programmatically by eval runner, not in default registry)

## Eval Rubric

When inspecting a game, check one area at a time rather than running all checkers at once. See [RUBRIC.md](RUBRIC.md) for the prioritized checklist with what to look for, commands, and red flags per mechanic area.

## Checkers

### momentum_lifecycle

- **Type:** deterministic
- **Fields:** `ruling.band`, `momentum_before`, `momentum_after`, `applied`
- **What it checks:** Momentum delta matches roll band mapping, values stay within [MOMENTUM_MIN, MOMENTUM_MAX], floor relief respects constraints
- **CLI:** `ev.py check TURN momentum_lifecycle`
- **Caveats:** Skips turns where no roll occurred (`ruling.rolled == false`). At momentum -2 or below, success/crit_success give +2/+3 instead of the standard band delta. Reports a failure if momentum stays at floor (-3) for 3+ consecutive turns without relief.

### gm_beat_lifecycle

- **Type:** deterministic
- **Fields:** `state_snapshot`, `momentum_before`, `momentum_after`, `ruling`, `narrate_prompt`
- **What it checks:** Pending GM beat is consumed across turns, beat lifecycle is respected, floor relief injected when beat_locked, binding block present on rolled turns, beat_locked dual-trigger fires at momentum floor
- **CLI:** `ev.py check TURN gm_beat_lifecycle`
- **Caveats:** Checks that `pending_gm_beat` from one turn is consumed or updated in the next. Verifies that when storyteller emits a GM beat, the state's `pending_gm_beat` matches its type. When `beat_locked` is true and storyteller did not emit a non-pressure beat, floor relief must inject `breathing_room`.

### location_change

- **Type:** deterministic
- **Fields:** `applied.location_change`, `extraction_context.location_this_turn`
- **What it checks:** When a location change is emitted, the post-turn location ID differs from the previous turn's location ID
- **CLI:** `ev.py check TURN location_change`
- **Caveats:** Only checks turns where `applied.location_change` is present. First turn is skipped (no previous location to compare).

### inventory_integrity

- **Type:** deterministic
- **Fields:** `applied.inventory_add`, `applied.inventory_remove`, `extraction_context.inventory_this_turn`
- **What it checks:** No negative inventory amounts, no overdraw (removing from zero-quantity items), no removal of non-existent items
- **CLI:** `ev.py check TURN inventory_integrity`
- **Caveats:** Checks state_snapshot inventory for negative amounts. Compares previous turn's inventory against current turn's removals to detect overdraw and removal of items that didn't exist.

### conditions_lifecycle

- **Type:** deterministic
- **Fields:** `applied.pc_condition_add`, `applied.pc_condition_remove`, `extraction_context.conditions_this_turn`
- **What it checks:** Conditions present in ruling reason, no duplicate condition IDs, condition count respects cap
- **CLI:** `ev.py check TURN conditions_lifecycle`
- **Caveats:** Checks that condition IDs appear in the ruling's reason text (lowercase comparison). Dedup check is case-insensitive. Cap check compares against `PC_CONDITIONS_MAX` (5).

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
- **Fields:** `extraction_context`, `applied.compendium_npc_update`
- **What it checks:** All NPC presence values in compendium are valid (`present`, `nearby`, `known`, `departed`, `archived`). Departed NPCs have required `departed_reason` and `departed_summary` fields.
- **CLI:** `ev.py check TURN npc_presence`
- **Caveats:** Only checks state_snapshot compendium entries, not extraction output.

### pacing_directives

- **Type:** deterministic
- **Fields:** `ruling`, `narrate_prompt`, `extraction_context`
- **What it checks:** Consecutive pressure tracking matches beat type, outcome_hint rendered in narrator prompt, directive rendered in storyteller prompt, removed directives not present, beat type variety maintained, surface_as consistency across consecutive same-type beats
- **CLI:** `ev.py check TURN pacing_directives`
- **Caveats:** Consecutive pressure counter must increment on pressure/escalation/complication beats and reset on others. Removed directives: "location pressure", "location imperative", "combat fatigue". Beat type variety warns if a single type exceeds 60% of all beats (requires 3+ beats). Surface_as consistency checks that consecutive same-type beats don't flip between "ambient" and "environmental" without a directive change.

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
- **Fields:** `narrate`, `extraction_context`, `applied.inventory_add`, `applied.inventory_remove`, `applied.pc_condition_add`, `applied.pc_condition_remove`
- **What it checks:** State extraction matches what narration describes — no missing or unsupported changes
- **CLI:** `ev.py check TURN state_fidelity --llm`
- **Caveats:** Uses the configured checker model. Evaluates first event only. Narration must explicitly mention or strongly imply each state change. Missing changes described in narration are failures. Extra changes not supported by narration are also failures.

### turn_assert

- **Type:** deterministic
- **Fields:** None (takes assertions as parameter)
- **What it checks:** Validates per-turn structured assertions from YAML scenarios (stream/field/expected/min_amount)
- **CLI:** Called programmatically by `ev.py eval run`, not in default registry
- **Caveats:** Supports streams: `ruling`, `extract.state`, `extraction_context`. Assertions specify a field dotpath, expected value, and optional min_amount threshold. Score is ratio of passed assertions to total.

## Running Checkers

### Single turn, specific checkers

```bash
ev.py check 5 momentum_lifecycle gm_beat_lifecycle
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
