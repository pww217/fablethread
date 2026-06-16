# Eval Report: Space Western (space-western)
**Date:** 2026-06-16 | **Turns:** 20 | **Personality:** driven
**Save:** `saves/ev/20260616_021437_7fe5b3/`
**Checker pass rate:** 87.0% (20/23) — avg score 0.87

## Failures
- `thread_lifecycle`: FAIL
- `thread_resolution_validity`: FAIL
- `arc_resolution_validity`: FAIL

## Narrative Mechanics Assessment

### Scene/Location Imperatives — WORKING
Scene taglines show excellent environmental escalation: `Willieburgh Shaft Four — firefight in the dark` → `Willieburgh Shaft Four — firefight in dust` → `Willieburgh Shaft Four — dust-choked tunnel, melee struggle` → `Willieburgh Shaft Four — collapsing corridor, trapped by debris` → `Willieburgh Shaft Four — narrow ledge, trapped below` → `Willieburgh Shaft Four — ledge standoff, falling shale` → `Observation deck entrance — narrow corridor, tense standoff` → `Terminal Room — flickering screens, seismic warnings` → `Terminal Room — rhythmic tremors, imminent collapse` → `Terminal Room — ceiling collapse, saboteur breach` → `Terminal Room — choking dust, saboteur advancing` → `Terminal Room — buried under rubble` → `Terminal Room — choked with silt and rubble` → `Terminal Room — heavy silence near ventilation grate`. Location transitions are continuous and well-paced.

### Combat — WORKING
Combat is tight and tactical. The firefight → collapse → escape → saboteur breach → grapple → buried under rubble arc is narratively coherent. Conditions track: `startled` → `unsteady` → `choking` → `off_balance` → `dust_in_eyes` → `suffocating`/`stunned` → `exposed`. The Space Western has the best condition tracking of all packs.

### Thread Management — BROKEN
`thread_updates.dedup` on `militia_encroachment` (T2), `corporate_audit`/`resource_scarcity` (T6), `structural_instability_shaft` (T16,T17), `militia_confrontation` (T19). `thread_same_turn_conflict` on `melee_skirmish_willieburgh` (T5). `thread_resolutions` reference unknown IDs: `structural_instability_shaft` (T5,T18), `ventilation_shaft_breach` (T19), `structural_collapse_evacuation` (T20).

### State Extraction — FIXED (2026-06-16)
`extraction.state.empty` on 7/20 turns (2,3,7,8,10,12,14,19).

Fix: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run on 2026-06-16 confirmed fix works.

### Storyteller Parse — BROKEN
Turn 12: `storytell parse failed` — `arc_resolve.resolution`, `arc_resolve.visible_goal`, `arc_resolve.goal_context` all missing.

### Best-Performing Pack
This pack has the highest checker pass rate (87.0%) and is one of only two packs where `pacing_directives` passes fully. `arc_goal_updates` and `goal_update_validity` both PASS — the only packs where goal updates work correctly.

### Other Bugs
- `TypeError` in logging: `thread_same_turn_conflict` uses `%d` format for `trace_id` — crashes logging formatter
- `generate_seed soft-check`: Opening narrative 356 words (expected 530-930) — shortest of all packs
- Many `skill: ?` in rulings
