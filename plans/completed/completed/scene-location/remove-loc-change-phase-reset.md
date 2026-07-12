# Remove Location Change → Phase Reset

## Purpose

Stop forcing scene phase to SETUP (or BREATHER from RESOLUTION) when the player changes location. Phase now persists across location changes. Scene age still resets on location change (unchanged).

## Problem Statement

Location change was being used as a hard stop to reset pacing phases. This was originally a workaround for pacing problems but now has the opposite effect — it artificially deflates urgency when players change location. The scene imperative system (age-based Scene Pressure/Imperative) and urgency decay are sufficient to handle pacing without location-based phase resets.

## Constraints

- Scene age reset behavior is unchanged — it must continue to reset to 0 on location change
- Urgency decay is unchanged — continues regardless of location
- Beat type constraints remain tied to phase
- No changes to config fields

## Non-goals

- No new config options
- No changes to urgency decay logic
- No changes to scene_age reset behavior
- No changes to how threads are managed on location change

## Solution

Remove the two-phase-forcing blocks in `_compute_scene_phase()` that checked for location change and forced SETUP (or BREATHER for RESOLUTION). The phase machine now runs normally each turn regardless of location, allowing phase to persist. Update the checker that allowed any→SETUP as always-valid, since that transition no longer exists from location change. Update docs.

## Firm Decisions

1. Phase (SETUP/RISING/CLIMAX/RESOLUTION/BREATHER) persists across location changes — no forced reset
2. `scene_age` continues to reset to 0 on location change — unchanged, correct
3. `climax_turn_count` and `breather_turn_count` persist — not reset on location change
4. Beat type constraints stay tied to phase — unchanged
5. Thread urgency persists — unchanged
6. Urgency decay continues unchanged — 8-turn timer on same urgency level
7. RESOLUTION naturally becomes BREATHER in 1 turn — no special location change handling needed

## Risks, Ambiguities, and Blockers

None identified.

## Status

`open`

## Phases

Single phase: core engine change + checker fix + doc update

---

## Implementation — Phase 1: Remove location-change phase reset

### Context files to load

- `ccya/engine/turn.py` lines 492–561 (`_compute_scene_phase`)
- `ccya/ev/checkers/phase_transition.py` lines 1–78
- `docs/architecture/pacing-systems.md` lines 35–50

### Detailed steps

#### Step 1.1 — Remove location-change-to-SETUP block from `_compute_scene_phase`

**File:** `ccya/engine/turn.py`

**What:** Remove lines 525–531 (the `location_change_this_turn` check that forces phase to SETUP). Also remove the `scene_entered` and `location_change_this_turn` variable declarations on lines 526–527 since they are no longer used after this block is removed.

**Why:** Phase must no longer reset on location change.

**Validation:** `rg "location_change_this_turn" ccya/engine/turn.py` returns no matches after edit.

#### Step 1.2 — Update the docstring of `_compute_scene_phase`

**File:** `ccya/engine/turn.py`

**What:** Update the docstring (lines 498–503) to remove "RESOLUTION→SETUP/BREATHER" and "any→SETUP (location change)" references. The new transitions summary should read:

```python
"""Compute the scene phase using the 5-state machine.

Transitions: SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION,
RESOLUTION→BREATHER, BREATHER→RISING.

Mutates state["scene"] in place. Returns the updated scene dict.
"""
```

**Why:** The docstring must reflect the actual behavior.

**Validation:** `rg "any.*SETUP|location.change" ccya/engine/turn.py | rg "_compute_scene_phase"` returns no matches after edit.

#### Step 1.3 — Remove the "any→SETUP always valid" skip in phase_transition checker

**File:** `ccya/ev/checkers/phase_transition.py`

**What:** Remove lines 57–59:
```python
# Any → SETUP is always valid (location_change)
if phase == "SETUP":
    continue
```

This skip allowed any→SETUP transitions to pass without validation. Since location change no longer forces SETUP, this skip is no longer correct. The "same phase persists" check on lines 54–55 already handles the valid case where phase stays SETUP across turns. Any other → SETUP transition that is not in `VALID_TRANSITIONS` will now correctly fail.

**Why:** This skip was masking the location-change→SETUP transition. With that removed, the skip must also be removed so that transitions are validated correctly.

**Validation:** `rg "any.*SETUP|location_change" ccya/ev/checkers/phase_transition.py` returns no matches after edit.

#### Step 1.4 — Update phase transition table in pacing-systems.md

**File:** `docs/architecture/pacing-systems.md`

**What:** In the phase transitions table (lines 38–45), remove these two rows:
- `| Any (non-RESOLUTION) | SETUP | Location change (scene_entered == current_turn) |`
- `| RESOLUTION | BREATHER | Always (location change doesn't redirect RESOLUTION) |`

Replace with a single row:
- `| RESOLUTION | BREATHER | Always (1-turn transition) |`

**Why:** The removed rows described the old location-change behavior. The new row clarifies that RESOLUTION→BREATHER is always a natural 1-turn transition.

**Validation:** `rg "Location change" docs/architecture/pacing-systems.md` returns no matches after edit.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).
