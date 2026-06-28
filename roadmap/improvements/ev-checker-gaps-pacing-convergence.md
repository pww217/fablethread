---
title: "EV checkers: heavy gaps in pacing/convergence checker coverage"
status: done
urgency: 3
size: large
created: 2026-06-27
completed: 2026-06-27
labels:
  - ev
  - checkers
  - pacing
  - convergence
---

## Status

Done. All 17 checkers implemented, registered, tested, and checker bugs fixed.

## Implementation

Files: `ccya/ev/checkers/pacing_convergence.py` (6 checkers), `ccya/ev/checkers/threads.py` (6 additions), `ccya/ev/checkers/state_lifecycle.py` (5 checkers).

Registration: added `pacing_convergence`, `state_lifecycle` imports to `ccya/ev/checkers/__init__.py`.

## Test results

### outer-rim save (10 events, turns 1-9)

40/42 PASS (95.2%). 2 failures:

| Checker | Result | Notes |
|---|---|---|
| `phase_transition_signals` | FAIL | CLIMAX→RESOLUTION at turn 6 without required signal-gated exit (legitimate engine bug) |
| `convergence_recompute` | FAIL | Stored data has legacy component values (`urgent_thread: 1` vs `+2`) plus real bugs (turn 1 has `urgent_thread: 0` despite urgent thread present; turn 3 has `scene_age: 0` when scene entered at turn 1) |

### golden-age save (2 events, turns 1-2)

40/42 PASS (95.2%). 2 failures:

| Checker | Result | Notes |
|---|---|---|
| `convergence_recompute` | FAIL | Legacy component values (`urgent_thread: 0` on turn 1 despite urgent thread present) |

## Checker bugs fixed

| Checker | Bug | Fix |
|---|---|---|
| `thread_urgency_decay` | Used threshold 4, engine uses 8 (`turn_state.py:116`) | Changed to `cfg.thread_urgency_max_age` |
| `thread_cooldown` | Read `last_thread_created_turn` from current turn's state (already has `thread_add` applied) | Read from previous turn's state; skip first turn |
| `convergence_components` | Used class default `convergence_threshold=3`, runtime default is 2 (`config.py:293`) | Override to 2 when class default matches |
| `convergence_recompute` | Flagged legacy `urgent_thread: 1` vs recomputed `2` as mismatch | Allow legacy +1 for urgent_thread (old engine used +1, now uses +2) |

## Remaining legitimate bugs

- `phase_transition_signals`: CLIMAX→RESOLUTION at turn 6 without required signal-gated exit (thread resolved on turn 5)
- `convergence_recompute`: Stored convergence components have real bugs across both saves — component values don't match recomputed values for multiple components, not just legacy urgent_thread

## Context

The checker library has good coverage for extraction integrity (threads, inventory, conditions, NPCs, arcs) and some pacing basics (phase transitions, climax counting, breather enforcement, beat phase validity, convergence components). However, the **complex mechanics that drive scene rhythm** have significant gaps:

| Mechanic | Existing checker | Gap |
|---|---|---|
| Phase transitions | `phase_transition` | Only validates state machine edges + climax outcome_hint. Misses: SETUP→RISING triggers, CLIMAX signal-gated exit, RESOLUTION→BREATHER, `turns_in_phase` |
| Convergence score | `convergence_components` | Validates stored components sum, doesn't independently recompute from raw state, misses: +2 weight for urgent_thread, beat_streak carry-over, roll_starvation formula, dormant exclusion |
| Stall floor | None | `consecutive_low_convergence` increment/reset, `stall_floor` formula |
| Curtain call | None | `curtain_call: "active"` / `"forced"` on CLIMAX turns |
| Spiral detection | None | `detect_spiral()` consecutive/ratio thresholds |
| Directive-beat alignment | `beat_phase_validity` | Only checks phase constraints. Misses: Scene Imperative filtering, spiral pressure exclusion |
| CLIMAX exit signals | None | Early exit (resolved + convergence < 2), extension (convergence ≥ 3 + urgent), hard cap |
| Beat diversity | None | World generating homogeneous candidates |
| Beat candidates population | None | World failure detection (empty candidates) |
| Thread urgency decay | None | Auto-dormant, stepwise urgency decay |
| Thread cap eviction | None | Cap enforcement on thread_add |
| Thread culling | None | Dormant → abandoned transition |
| Thread creation cooldown | None | Cooldown gate enforcement |
| Thread completion threshold | None | Auto-resolve at ≥3 progress entries |
| Progress dedup | None | ≥70% overlap rejection |
| Condition TTL | None | TTL decrement, removal at 0 |
| World state TTL | None | `expires_turn` enforcement |
| NPC presence decay | None | Location-change auto-demotion |

## Proposed new checkers

### Pacing/convergence (highest priority)

**1. `phase_transition_signals`** — deterministic
- Reads: `pacing_context`, `last_turn_state.arc.threads`, `state.meta.consecutive_low_convergence`
- Verifies:
  - SETUP→RISING fires when: urgent thread appears OR `turns_in_phase >= 3`
  - CLIMAX→RESOLUTION: early exit when `completed_threads.resolved_turn == turn_no - 1` AND `convergence_score < 2`
  - CLIMAX extension: stays when `convergence_score >= 3` AND has_urgent_active_thread, caps at `climax_turn_limit + extension_max`
  - RESOLUTION→BREATHER: always fires (1-turn transition)
  - BREATHER→RISING: fires when urgent thread OR `breather_turn_count >= breather_max_turns`
  - `turns_in_phase` increments by 1 each turn, resets on phase change

**2. `convergence_recompute`** — deterministic
- Reads: `last_turn_state.arc.threads`, `pacing_context`, `state.scene`, `state.meta.recent_beats`, `ruling`
- Independently recomputes all 6 convergence components from raw state:
  - `urgent_thread`: +2 if any non-dormant urgent thread (NOT +1)
  - `threat_thread`: +1 if any non-dormant threat-type thread
  - `scene_age`: +1 if `scene_age >= scene_pressure_threshold`
  - `beat_streak`: +1 if ≥60% pressure beats in recent window with carry-over for null types
  - `roll_starvation`: +1 if `turns_since_last_roll >= roll_starvation_threshold`
  - `threat_density`: +1 if active threat count >= `threat_density_threshold`
- Compares recomputed sum against stored `convergence_score - stall_floor`

**3. `stall_floor_computation`** — deterministic
- Reads: `state.meta.consecutive_low_convergence`, `pacing_context.convergence_score`, `pacing_context.convergence_components.stall_floor`, `state.scene.scene_phase`
- Verifies:
  - `consecutive_low_convergence` increments when total_score < threshold, resets on reaching threshold or cancel/retry
  - `stall_floor = min(1 + ((clc - 3) // 3), stall_floor_max)` when `clc >= 3`, else 0
  - `consecutive_low_convergence` persists across BREATHER→RISING cycles

**4. `curtain_call`** — deterministic
- Reads: `pacing_context`, `state.scene.curtain_call`, `state.scene.climax_turn_count`
- Verifies:
  - CLIMAX turn 1: `curtain_call == "active"`
  - CLIMAX turn ≥ `climax_turn_limit - 1`: `curtain_call == "forced"`
  - Non-CLIMAX: `curtain_call == ""`

**5. `spiral_detection`** — deterministic
- Reads: `ruling`, `state.meta.spiral_detected` (or `pacing_context.spiral_detected`)
- Verifies:
  - `spiral_detected` is True when: ≥3 consecutive hard+ rolls OR ≥3 of last 5 rolls are hard+
  - `spiral_detected` is False when: neither condition met

**6. `directive_beat_alignment`** — deterministic
- Reads: `ruling.selected_beat`, `state.meta.beat_candidates`, `pacing_context`, `state.scene.scene_phase`
- Verifies:
  - When `directive == "Scene Imperative"`: selected beat type is in `["revelation", "hazard", "callback", "opportunity", "setback", "breathing_room"]`
  - When `spiral_detected == True`: selected beat type is NOT in pressure bucket (`pressure`, `complication`, `escalation`, `setback`)
  - Selected beat type is in `derive_allowed_beat_types()` output (phase + directive + spiral)

### Thread lifecycle (medium priority)

**7. `thread_urgency_decay`** — deterministic
- Reads: `last_turn_state.arc.threads`
- Verifies:
  - Threads untouched ≥4 turns (non-urgent) have `dormant == True`
  - Threads at same urgency ≥8 turns are demoted stepwise (urgent→normal→background)
  - No stepwise jumps (urgent→background directly)

**8. `thread_cap_eviction`** — deterministic
- Reads: `last_turn_state.arc.threads`, `extraction.record.thread_add`
- Verifies: when `thread_add` fires and active count > 5, oldest active thread has `dormant == True`

**9. `thread_culling`** — deterministic
- Reads: `last_turn_state.arc.threads`, `last_turn_state.arc.completed_threads`
- Verifies: when dormant count ≥3, oldest dormant threads appear in completed_threads with `resolution_state == "abandoned"`

**10. `thread_cooldown`** — deterministic
- Reads: `last_turn_state.arc.last_thread_created_turn`, `extraction.record.thread_add`
- Verifies: `thread_add` only fires when `turn - last_thread_created_turn >= cooldown`

**11. `thread_completion`** — deterministic
- Reads: `last_turn_state.arc.threads`, `last_turn_state.arc.completed_threads`
- Verifies: threads with ≥3 progress entries appear in completed_threads

**12. `progress_dedup`** — deterministic
- Reads: `extraction.record.thread_update[].progress`
- Verifies: consecutive progress entries on same thread differ by <70% overlap (simple diff ratio)

### State integrity (lower priority)

**13. `condition_ttl`** — deterministic
- Reads: `last_turn_state.pc.conditions`, `applied.pc_condition_add`
- Verifies: conditions not added this turn have decremented `turns_remaining`, no condition has `turns_remaining == 0`, permanent stays permanent

**14. `world_state_ttl`** — deterministic
- Reads: `last_turn_state.scene.world_state`
- Verifies: facts with `expires_turn <= current_turn` are not present, permanent facts persist

**15. `npc_presence_decay`** — deterministic
- Reads: `state.compendium.npcs`, `applied.location_change`
- Verifies: on location change, non-party NPCs get demoted

### World generation (lowest priority)

**16. `beat_diversity`** — deterministic
- Reads: `state.meta.beat_candidates`, `state.meta.recent_beats`
- Verifies: beat types in candidates don't all match the most recent beat type

**17. `beat_candidates_present`** — deterministic
- Reads: `state.meta.beat_candidates`
- Verifies: non-empty on turns where World should have run (every turn after turn 1)

## Implementation notes

- All proposed checkers are deterministic (no LLM calls needed for mechanical invariants)
- Most read `last_turn_state` + `pacing_context` + `extraction.record` — fields already available in events
- `stall_floor_computation` needs `state.meta.consecutive_low_convergence` which may need to be stored in events if not already
- `convergence_recompute` is the most complex — it needs access to raw `recent_beats`, `recent_rolls`, `active_threads` to independently verify the formula
- `spiral_detection` needs `recent_rolls` data in events

## Priority order

1. `convergence_recompute` — verifies the core scoring formula independently
2. `stall_floor_computation` — 7th component, drives CLIMAX transitions
3. `phase_transition_signals` — verifies all transition triggers, not just edges
4. `curtain_call` — CLIMAX soft-close mechanics
5. `directive_beat_alignment` — directive constraints on beats
6. `spiral_detection` — roll death spiral
7. `thread_urgency_decay` — core pacing mechanic
8. `thread_cap_eviction` — context bloat prevention
9. `thread_cooldown` — pacing control
10. `thread_culling` — dormant cleanup
11. `thread_completion` — auto-resolution
12. `progress_dedup` — LLM output quality
13. `condition_ttl` — state integrity
14. `world_state_ttl` — world state integrity
15. `npc_presence_decay` — NPC lifecycle
16. `beat_diversity` — World generation quality
17. `beat_candidates_present` — World failure detection
