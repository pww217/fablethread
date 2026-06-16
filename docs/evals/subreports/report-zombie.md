# Eval Report: Zombie Survival (zombie-survival)
**Date:** 2026-06-16 | **Turns:** 20 | **Personality:** driven
**Save:** `saves/ev/20260616_013711_b79e75/`
**Checker pass rate:** 78.3% (18/23) — avg score 0.78

## Failures
- `thread_lifecycle`: FAIL
- `pacing_directives`: 6/7 FAIL
- `thread_resolution_validity`: FAIL
- `arc_resolution_validity`: FAIL
- `goal_update_validity`: 1/2 FAIL

## Narrative Mechanics Assessment

### Scene/Location Imperatives — WORKING
Scene taglines show good escalation: `Quarantine perimeter — gate failing, concrete collapsing` → `Quarantine perimeter — door buckling, mass breaching` → `Quarantine perimeter — seal breached, something enters` → `Secondary containment hallway — cramped, slick, and pursued` → `Inner Checkpoint — heavy doors sealed` → `Inner Checkpoint — door buckling, dust falling` → `Inner Checkpoint — breach collapsed, entity surging in`. Location transitions are continuous.

### Combat — WORKING
Combat is intense and narratively coherent. The entity breach → fight → retreat → barricade → breach again arc plays out well. Conditions track: `startled` → `blinded` → `startled` → `winded` → `dust_obscured` → `choking_dust` → `frightened` → `unsteady_footing` → `winded`. The combat escalation feels right for zombie survival.

### Thread Management — BROKEN
Multiple threads show `thread_updates.dedup` rejections: `containment_breach` (turns 2-4), `supply_shortage` (turns 6,12,15,16), `entity_incursion_combat` (turn 12), `sector_wide_chaos` (turns 18-20). All have progress values at or near 1.00 — meaning the storyteller creates threads but never meaningfully updates them.

Additionally: `thread_same_turn_conflict` — `thread_update` and `thread_resolve` for the same ID on turns 5 and 15. `thread_resolutions` references unknown IDs: `entity_breach_combat` (T5), `perimeter_breach_containment` (T6), `checkpoint_breach_containment` (T15), `entity_sector_infestation` (T16).

### State Extraction — FIXED (2026-06-16)
`extraction.state.empty` on 9/20 turns (2,3,4,6,8,9,11,14,20). Same systemic issue as noir.

Fix: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run on 2026-06-16 confirmed fix works.

### Delta Validation — BROKEN
Turns 17 and 20: `Delta validation failed (1 rejection(s))` + `Fallback narrative`. The state deltas fail validation, so the turn gets a fallback narrative instead of proper state application.

### Other Bugs
- `TypeError` in logging: `thread_same_turn_conflict` uses `%d` format for `trace_id` which is a string — crashes the logging formatter
- `inventory over-draw clamped`: `pistol_ammo` — requested 4 but stack is 2
- `generate_seed soft-check`: Opening narrative 404 words (expected 530-930) — too short
- `Fallback message stripped from narration` — observed on turns 17 and 20
