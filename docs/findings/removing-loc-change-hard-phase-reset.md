# Discovery: Location Change → Phase Reset

**Date:** 2026-06-17
**Status:** Discovery complete — ready for design

---

## Context

The phase engine tracks scene rhythm through 5 states (SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → RISING). Currently, **location change forces a phase reset to SETUP** (or BREATHER if the current phase was RESOLUTION).

This was originally a stopgap for pacing problems — a way to artificially lower urgency when players moved locations. Now that pacing works better, it's having the opposite effect: it **artificially deflates urgency** when players change location, which undermines pacing momentum.

The concern is that without this reset, players could string together high-tension scenes indefinitely by simply moving between locations. However, the scene imperative system (age-based: Scene Pressure at 3 turns, Scene Imperative at 4 turns) is designed to handle exactly this — it should be trusted to drive transitions.

---

## Current Behavior

### Phase Reset on Location Change

**Location change trigger** (`ccya/state/delta_builder.py:227-229`):
```python
_stamp_turn = state.get("meta", {}).get("turn", 0) + 1
state["scene"]["turn_entered"] = _stamp_turn
state["scene"]["location_entered_turn"] = _stamp_turn
```
On location change, `turn_entered` is set to `current_turn + 1`.

**Phase reset logic** (`ccya/engine/turn.py:525-531`):
```python
scene_entered = scene.get("turn_entered", 0)
location_change_this_turn = (scene_entered == current_turn)

if location_change_this_turn and phase != "RESOLUTION":
    return {**scene, "scene_phase": "SETUP", "climax_turn_count": 0, "breather_turn_count": 0}
```
When `turn_entered == current_turn` (i.e., location changed this turn), phase is forced to SETUP and all turn counters reset. RESOLUTION is a special case that goes to BREATHER instead.

### What Gets Reset

| Field | Reset value | Purpose |
|-------|-------------|---------|
| `scene_phase` | `"SETUP"` | Phase state machine |
| `climax_turn_count` | `0` | CLIMAX duration counter |
| `breather_turn_count` | `0` | BREATHER duration counter |

### What Persists

| Field | Behavior | Notes |
|-------|----------|-------|
| `scene_age` | **Resets to 0** | `scene_age = current_turn - turn_entered`. Driven by location change, not phase. |
| `turn_entered` | Set to `current_turn + 1` | Used to compute scene_age on next turn |
| `arc.threads[].urgency` | **Persists** | Thread urgency is independent of location |
| `urgency_set_turn` | **Persists** | Decay clock continues ticking |
| `convergence_score` | **Resets naturally** | Components (beat streak, scene age) reset because scene_age resets and beat history is per-scene |

### What scene_age Reset Causes

Scene age reset is **correct and intentional**. It's independent of phase:
- Scene age drives the **scene imperative system** (`_compute_narration_directive()`)
- Scene Pressure fires at age ≥3, Scene Imperative at age ≥4
- This is how the engine says "move this along" — it should not be tied to phase

So: scene_age resets on location change = **working as intended**. Do not change this.

---

## The Phase Machine (Full)

### Phase → Transition Conditions

```
SETUP     → RISING    : urgent thread appears
RISING    → CLIMAX    : convergence_score ≥ threshold (default 3)
CLIMAX    → RESOLUTION: climax_turn_count ≥ limit (default 4)
RESOLUTION→ BREATHER  : always (no location change check here)
BREATHER  → RISING    : urgent thread appears OR breather_turn_count ≥ max (default 3)
Any phase → SETUP     : location change (CURRENT BEHAVIOR — TO BE REMOVED)
RESOLUTION→ BREATHER  : location change (special case)
```

### Convergence Score Components

`compute_convergence_score()` in `ccya/engine/_pacing.py:85-131`:
1. Thread weight (+1 if ≥1 urgent thread)
2. Urgency depth (+1 if ≥2 urgent threads)
3. Scene age (+1 if age ≥ `scene_pressure_threshold`)
4. Beat streak (+1 if ≥60% pressure beats in last 5)
5. Dice weight (+1 if fail/crit_fail roll with urgent thread)

### Beat Type Constraints by Phase

`BEAT_PHASE_MAP` in `ccya/engine/_pacing.py:23-29`:
- **SETUP**: All beat types allowed (pressure, situation, relief)
- **RISING**: Pressure + situation only
- **CLIMAX**: Pressure only (complication, escalation, pressure)
- **RESOLUTION**: Relief + situation (breathing_room, callback, revelation)
- **BREATHER**: All beat types

These constraints are tied to phase. If phase persists on location change, beat type constraints persist.

### Urgency Decay

`ccya/engine/turn.py:217-241`:
- After `thread_urgency_max_age` turns (default 8) at same urgency level:
  - `urgent → normal`
  - `normal → background`
- This is independent of location change — decay continues regardless

---

## Files Involved

### Core Implementation
| File | Lines | What |
|------|-------|------|
| `ccya/engine/turn.py` | 525-531 | Location change → SETUP reset |
| `ccya/engine/turn.py` | 492-561 | `_compute_scene_phase()` phase machine |
| `ccya/engine/turn.py` | 415-438 | `_compute_narration_directive()` (scene imperatives) |
| `ccya/engine/turn.py` | 478-489 | `_compute_ages()` (scene_age) |
| `ccya/engine/turn.py` | 217-241 | Urgency decay |
| `ccya/state/delta_builder.py` | 213-229 | Location change detection + `turn_entered` stamping |

### Pacing Infrastructure
| File | Lines | What |
|------|-------|------|
| `ccya/engine/_pacing.py` | 23-29 | `BEAT_PHASE_MAP` beat constraints |
| `ccya/engine/_pacing.py` | 85-131 | `compute_convergence_score()` |
| `ccya/engine/_pacing.py` | 60-82 | `derive_allowed_beat_types()` |
| `ccya/engine/thread_sanitizer.py` | 20-80+ | LLM-driven urgency escalation |

### Config
| File | Line | Field | Default |
|------|------|-------|---------|
| `ccya/engine/config.py` | 153 | `scene_pressure_threshold` | 3 |
| `ccya/engine/config.py` | 154 | `scene_imperative_threshold` | 4 |
| `ccya/engine/config.py` | 156 | `climax_turn_limit` | 4 |
| `ccya/engine/config.py` | 157 | `breather_max_turns` | 3 |
| `ccya/engine/config.py` | 158 | `convergence_threshold` | 3 |
| `ccya/engine/config.py` | 174 | `thread_urgency_max_age` | 8 |

### Prompts
| File | What |
|------|------|
| `ccya/prompts/narrate_user.j2` | Uses `scene_phase`, `pacing_context.outcome_hint` |
| `ccya/prompts/storytell_user.j2` | Uses `scene_phase`, `allowed_beat_types`, `directive` |
| `ccya/prompts/sections/_thread_list.j2` | Renders thread urgency |

### Checkers
| File | What |
|------|------|
| `ccya/ev/checkers/phase_transition.py` | Validates phase state machine |
| `ccya/ev/checkers/scene_age_tracking.py` | Validates scene_age resets on location change |
| `ccya/ev/checkers/beat_phase_validity.py` | Validates beat types against phase |
| `ccya/ev/checkers/climax_turn_counting.py` | Validates climax_turn_count |

---

## Desired Future Behavior

**Decision: Phase persists across location changes.**

When a player changes location:
1. `scene_age` resets to 0 (unchanged — correct)
2. `turn_entered` stamps to `current_turn + 1` (unchanged — correct)
3. **`scene_phase` persists** — no forced SETUP/BREATHER
4. **`climax_turn_count` persists** — keeps counting
5. **`breather_turn_count` persists** — keeps counting
6. **Beat type constraints persist** — tied to phase
7. **Thread urgency persists** — unchanged
8. **Urgency decay continues** — unchanged

### Why This Works

- **Scene imperatives handle pacing**: Scene Pressure (age 3) and Scene Imperative (age 4) are age-based and independent of phase. They fire regardless of location and will drive transitions.
- **Urgency decay prevents infinite escalation**: After 8 turns at `urgent`, threads decay to `normal`. This prevents players from maintaining CLIMAX indefinitely by keeping threads urgent.
- **Climax/Breather counters are time-based fallbacks**: If CLIMAX runs too long, `climax_turn_count` hits the limit and forces RESOLUTION. Same for BREATHER with `breather_max_turns`.
- **Beat type constraints remain phase-bound**: A CLIMAX in a new location still restricts beats to pressure types. A SETUP still allows all beats.

### What Changes

The location-change-to-SETUP logic in `_compute_scene_phase()` is removed:

```python
# REMOVE this block:
if location_change_this_turn and phase != "RESOLUTION":
    return {**scene, "scene_phase": "SETUP", "climax_turn_count": 0, "breather_turn_count": 0}
```

**RESOLUTION handling**: RESOLUTION already flows naturally to BREATHER in exactly 1 turn (no time limit, just a single-beat transition). The current code has a special case where location change in RESOLUTION also forces BREATHER immediately — but this is unnecessary since RESOLUTION→BREATHER would happen next turn anyway. Remove the `phase != "RESOLUTION"` condition entirely, so **all phases persist across location change**: SETUP persists, RISING persists, CLIMAX persists, RESOLUTION persists (and naturally becomes BREATHER next turn).

### Checkers That Need Updates

- `ccya/ev/checkers/phase_transition.py` — will need to remove the "any→SETUP on location change" validation
- `ccya/ev/checkers/scene_age_tracking.py` — scene_age reset is unchanged, should pass
- `ccya/ev/checkers/climax_turn_counting.py` — climax_turn_count persistence should be validated instead of reset

---

## Open Questions

~~1. **RESOLUTION special case**: Currently RESOLUTION→BREATHER on location change (not SETUP). Should RESOLUTION also persist across location changes?~~ **Resolved**: RESOLUTION persists. It naturally becomes BREATHER in 1 turn anyway, so no special handling needed.

~~2. **Beat type constraint on location change**~~ **Resolved**: Stay tied to phase.

~~3. **Is there ever a case where you WANT location to affect phase?**~~ **Resolved**: No legitimate use case. Scene imperatives and urgency decay handle pacing.