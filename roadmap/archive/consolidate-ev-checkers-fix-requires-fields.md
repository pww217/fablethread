---
title: "Consolidate EV checkers — fix requires_fields, logic bugs, runner issues"
status: done
urgency: 2
size: medium
created: 2026-06-12
labels:
  - Bug
  - Tooling
---

## Scope

Consolidated from TICK-6, TICK-7, TICK-8, TICK-9, TICK-25, TICK-26. All EV checkers have field/schema mismatches or runner bugs.

## Consolidated Issues

### TICK-6: momentum_lifecycle checker

* Bug: reads state_snapshot.pc.momentum (post-turn) instead of momentum_before (start-of-turn) — off-by-one, causes false negatives
* Bug: 'break' exits after first floor streak >= 3, missing later episodes

### TICK-7: gm_beat_lifecycle checker

* Bug: expects breathing_room on ALL beat_locked turns, but engine only injects floor relief when beat_locked from consecutive_pressure, NOT when triggered by momentum floor
* Fix: add triggered_by_momentum check at line 75 matching engine logic

### TICK-8: sanitizer_lifecycle checker

* Bug: checker runner runs checkers per-turn via find_turn() which only returns 'turn'-kind events. Sanitizer events are 'sanitizer'-kind, so checker never sees them
* Fix: separate sanitizer_lifecycle from per-turn --all runs, or change runner to pass ALL events to checkers with needs_non_turn_events=True

### TICK-9: pacing_directives checker

* Bug: requires 'extraction_context' in requires_fields, but this field DOES NOT EXIST in event schema. Data is at 'extraction.state' and 'extraction.storytell'
* Fix: remove 'extraction_context' from requires_fields, remove dead fallback code (lines 31-33)

### TICK-25: checkers reference non-existent extraction_context field

* inventory_integrity: requires extraction_context.inventory_this_turn — data is in state_snapshot.inventory / applied.inventory_add/remove/update
* conditions_lifecycle: requires extraction_context.conditions_this_turn — remove from requires_fields AND remove conditions_cap check block
* npc_presence: requires extraction_context — not used in logic, remove
* pacing_directives: see TICK-9 above

### TICK-26: location_change checker uses non-existent field names

* requires_fields includes 'applied.location_change' — event has 'applied.location_description'
* Checker logic reads applied.get('location_change') — returns None
* Fix: update requires_fields, rewrite logic to work with actual event schema

## Validation

All 6 checkers fail against real pipeline output. Confirmed across eval sessions 20260611_214133_be94dd, 20260611_215527_7bde5a, 20260611_221346_1d2f79, 20260611_225430_140eeb, 20260611_231041_87b14d
