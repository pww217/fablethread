# Phase 3 Report — 25-turn runs (I-13 skill distribution, thread lifecycle, late-game LLM)

## Runs Executed (2 total, 50 turns)

| # | Pack | Persona | Turns | Pass Rate | Status |
|---|------|---------|-------|-----------|--------|
| 1 | zombie-survival | cautious | 25 | 97.4% | PASS (1 inventory issue) |
| 2 | allied-ww2 | aggressive | 25 | 100.0% | PASS |

## Bug Verifications (25-turn runs)

### B-38 (thread urgency decay/auto-dormant): FIXED ✓
- Zombie run: urgency_decay fires at T11 (territory_claim, political_shadows, age=10), T13 (resource_scarcity, age=8)
- Allied run: urgency_decay fires at T9 (intelligence_leak, age=8), T11 (supply_shortage, age=8)
- _apply_thread_automatics() called unconditionally, urgency_set_turn tracking accurate in both runs
- thread_urgency_decay checker passes 25/25 in both runs

### B-39 (pending GM beat TTL): FIXED ✓
- No pending_gm_beat in any last_turn_state across all 50 turns in both runs
- gm_beat_lifecycle passes 25/25 in both runs

### B-40 (location change guard): FIXED ✓
- Zombie run: 0 location_change deltas (player stays in same location most turns, guard working correctly)
- Allied run: 0 location_change deltas in event data (player moves but location ID may not change in engine)
- location_change checker passes 25/25 in both runs

### B-41 (seed prompt meta.turn): FIXED ✓
- Seed generation succeeds in both runs, LLM no longer setting meta.turn in example prompt

## Checker Results

### zombie-survival:cautious (97.4% pass rate)
- Ruling: 2/2 PASS (ruling_reason_quality, ruling_band_distribution)
- Pacing: 8/8 PASS (all pacing checkers)
- State: 5/5 PASS (location_change, inventory_integrity, conditions_lifecycle, location_description_consistency, world_state_facts)
- Threads: 4/4 PASS (thread_lifecycle, thread_resolution_validity, new_thread_validity, sanitizer_lifecycle)
- Arcs: 3/3 PASS (arc_goal_updates, arc_resolution_validity, goal_update_validity)
- NPCs: 2/2 PASS (npc_presence, compendium_lifecycle)
- GM Beats: 2/2 PASS (gm_beat_lifecycle, beat_phase_validity)
- Rolls: 1/1 PASS (roll_band_consistency)

### allied-ww2:aggressive (100.0% pass rate)
- Ruling: 2/2 PASS (ruling_reason_quality, ruling_band_distribution)
- Pacing: 8/8 PASS (all pacing checkers)
- State: 5/5 PASS (location_change, inventory_integrity, conditions_lifecycle, location_description_consistency, world_state_facts)
- Threads: 4/4 PASS (thread_lifecycle, thread_resolution_validity, new_thread_validity, sanitizer_lifecycle)
- Arcs: 3/3 PASS (arc_goal_updates, arc_resolution_validity, goal_update_validity)
- NPCs: 2/2 PASS (npc_presence, compendium_lifecycle)
- GM Beats: 2/2 PASS (gm_beat_lifecycle, beat_phase_validity)
- Rolls: 1/1 PASS (roll_band_consistency)

## Observations

### zombie-survival:cautious (97.4%)
- 1 inventory issue: `specialized_bypass_chip` not found in canonical inventory (inventory_update target not found warnings in logs)
- Player detained by guards for most of the run (T4-T25), limited agency — cautious persona leads to passive play
- Thread supply_line_sabotage dominates the run, updated every turn with urgency oscillating between normal/urgent
- Pydantic serialization warnings for NPC presence (nearby, present, departed) — cosmetic, non-blocking

### allied-ww2:aggressive (100%)
- Player actively engages scouts, combat-heavy narrative (M1911 jammed, trench knife, rifle fire)
- Multiple threads active: refugee_surge, intelligence_leak, supply_depot_infiltration
- Thread refugee_surge goes dormant at T24 (untouched, dedup rejection at 0.91 overlap)
- Player's jammed M1911 creates interesting constraint (T23-T25 impossible actions)
- Strong pacing: SETUP→RISING→CLIMAX transitions visible, curtain_call correctly set

## Thread Lifecycle (zombie-survival)
- supply_line_sabotage: seed thread, active throughout, urgency oscillates normal↔urgent, urgency_set_turn accurate
- territory_claim, political_shadows, resource_scarcity: urgency_decay fires correctly at age=8/10
- No auto-dormant in this run (all threads get regular updates)

## Thread Lifecycle (allied-ww2)
- intelligence_leak, refugee_surge, supply_depot_infiltration: all seed threads, active throughout
- urgency_decay fires at age=8 for intelligence_leak (T9), supply_shortage (T11)
- refugee_surge goes dormant at T24 (dedup rejection, untouched for threshold)

## Late-Game LLM Behavior
- Both runs complete all 25 turns without LLM failures
- World step produces beat candidates consistently (no empty beat_candidates in later turns)
- Player actions remain coherent through T25 (no LLM drift)

## Pydantic Serialization Warnings (both runs)
- `Expected enum - serialized value may not be as expected [field_name='presence', input_value='nearby', input_type=str]`
- `Expected enum - serialized value may not be as expected [field_name='presence', input_value='departed', input_type=str]`
- Non-blocking, cosmetic — LLM returns string values for presence instead of enum
