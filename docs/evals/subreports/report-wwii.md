# Eval Report: WWII (allied-ww2)
**Date:** 2026-06-16 | **Turns:** 20 | **Personality:** driven
**Save:** `saves/ev/20260616_014846_89f5a7/`
**Checker pass rate:** 78.3% (18/23) — avg score 0.78

## Failures
- `thread_lifecycle`: FAIL
- `arc_goal_updates`: FAIL
- `thread_resolution_validity`: FAIL
- `arc_resolution_validity`: FAIL
- `goal_update_validity`: FAIL

## Narrative Mechanics Assessment

### Scene/Location Imperatives — WORKING
Scene taglines show good tactical progression: `Triage perimeter — muddy outskirts, forest edge` → `Forest edge — underbrush, sentries alerted` → `Secondary supply depot — lanterns flickering, soldiers alerted` → `Secondary Supply Depot — firefight in the clearing` → `Secondary Supply Depot — firefight under lanterns` → `Secondary Supply Depot — firefight in smoke` → `Secondary Supply Depot — exposed in mud, under heavy fire`. Location transitions are continuous.

### Combat — WORKING
Combat is the strongest element in this pack. The firefight arc from stealth approach → detected → firefight → cover → flanking → heavy engagement plays out well. Conditions track: `pinned`/`startled` → `blinded`/`exhausted` → `startled` → `dust_in_eyes` → `rattled` → `prone` → `wounded_arm`/`trembling_hands` → `pinned`. The combat feels tactically coherent.

### Thread Management — BROKEN
`thread_updates.dedup` on `supply_line_collapse` (turns 2,6,7,8) and `wounded_neglect` (turns 10,14,15,16,18,19,20). All progress at 1.00 — never meaningfully updated. `thread_same_turn_conflict` on `supply_line_collapse` (turn 8). `thread_resolutions` reference unknown IDs: `depot_firefight_climax` (T10), `storehouse_siege` (T14), `exposed_position` (T16).

### State Extraction — FIXED (2026-06-16)
`extraction.state.empty` on 6/20 turns (1,3,6,9,11,19).

Fix: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run on 2026-06-16 confirmed fix works.

### Storyteller Parse — BROKEN
Turn 13: `extract_state parse failed` — `inventory_change_reason` is `NoneType`. The state extractor returns `None` for `inventory_change_reason` when inventory changes are present.

### Pacing — BEST OF ALL PACKS
`pacing_directives` passes 7/7 — the only pack where pacing directives fully work. This is the best-performing pack for narrative pacing.

### Other Bugs
- `TypeError` in logging: `thread_same_turn_conflict` uses `%d` format for `trace_id` — crashes logging formatter
- `generate_seed soft-check`: Opening narrative 387 words (expected 530-930) — too short
- Many `skill: ?` in rulings
