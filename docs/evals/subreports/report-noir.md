# Eval Report: Noir (noir-1930s)
**Date:** 2026-06-16 | **Turns:** 20 | **Personality:** driven
**Save:** `saves/ev/20260616_012543_acf362/`
**Checker pass rate:** 87.0% (20/23) — avg score 0.87

## Failures
- `pacing_directives`: 6/7 FAIL
- `beat_phase_validity`: 2/3 FAIL
- `goal_update_validity`: 1/2 FAIL

## Narrative Mechanics Assessment

### Scene/Location Imperatives — WORKING
Scene taglines evolve well across turns: `Loganmouth Precinct — heavy tension` → `cramped stationhouse, tense standoff` → `Pier 14 — thick fog, desolate docks` → `Pier 14 — standoff in the mist` → `Pier 14 — heavy fog, armed confrontation` → `Pier 14 — tightening circle, iron pipe lunging` → `Loganmouth Precinct — holding cells, tense interrogation` → `Interrogation room — harsh light, metal table`. Location transitions are continuous and logical.

### Combat — WORKING
Combat escalation is strong. Turns 6-14 show a clear combat arc: approach → standoff → intimidation → shooting → weapon loss → capture. Conditions track well: `adrenaline_spike` → `focused` → `threatened` → `deafened` → `startled` → `injured_ribs` → `winded` → `focused` → `rattled` → `shackled`. The combat feels narratively coherent.

### Thread Management — BROKEN
`press_leverage` thread appears on every turn with progress values like 1.00, 0.91, 0.80 — all rejected as dedup overlaps. The thread never progresses past initial creation. This is a systemic issue: the storyteller creates a thread but never meaningfully updates or resolves it.

### State Extraction — FIXED (2026-06-16)
`extraction.state.empty` fires on 8/20 turns (2,3,5,6,9,12,16,18). Root cause: check only looked at `inventory_add` + `pc_condition_add`, missing `inventory_update`/`inventory_remove`/`pc_condition_remove`. Validator also missing `inventory_update`. Prompt lacked spatial reasoning guidance — LLM treated "draw revolver" as an inventory change.

Fix: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run on 2026-06-16 confirmed fix works — LLM now correctly outputs `inventory_change_reason: "none"` when there are no inventory changes.

### Storyteller Parse — BROKEN
Turn 12: `storytell parse failed` — `arc_resolve.resolution`, `arc_resolve.visible_goal`, `arc_resolve.goal_context` all missing. The storyteller returns an empty `arc_resolve: {}` object.

### Rulings — BUG
Many turns show `skill: ?` in the ruling output (turns 1,2,3,4,9,15,19,20). The skill assignment is not being populated for certain rulings.

### Other
- `generate_seed soft-check`: Opening narrative 422 words (expected 530-930) — too short
- `Fallback message stripped from narration` — not observed in this run
