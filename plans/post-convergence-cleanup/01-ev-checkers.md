# Post-Convergence Cleanup — Phase 1: EV Checkers

## Purpose

Update all EV checkers to match the convergence scoring engine changes: CRISIS→CLIMAX rename, `tension_delta` field removal, `derive_enforce_relief`/`consecutive_pressure_beats` removal, `crisis_turn_count`→`climax_turn_count`, and new `convergence_score` field validation. Plans 1 and 2 must be complete (engine changes merged).

## Firm decisions

- `tension_delta` checker: deleted entirely (field no longer exists in event data).
- `tension_monotonicity` checker: deleted entirely (field no longer exists in event data).
- `crisis_turn_counting` checker: renamed to `climax_turn_counting`, all CRISIS→CLIMAX references updated.
- `gm_beat` checker: remove enforce_relief check, remove `derive_enforce_relief` import.
- `beat_phase_validity` checker: remove `breathing_room` bypass comment (no longer an enforce_relief override).
- `pacing` checker: remove `consecutive_pressure` counter check (field `post_extraction_consecutive_pressure_beats` no longer emitted).
- `phase_transition` checker: rename CRISIS→CLIMAX, update `crisis_turn_count`→`climax_turn_count`.
- `phase_persistence` checker: update valid_phases set.
- `breather_enforcement` checker: unchanged (BREATHER unchanged).
- `__init__.py` checker registry: update imports to new names, remove deleted checkers.

## Status

`open`

## Dependencies

- Plans 1 and 2 complete (engine changes merged, event dict no longer emits removed fields).

## Implementation — Phase 1: EV Checkers

### Context files to load

- `ccya/ev/checkers/__init__.py` — checker registry (line 124)
- `ccya/ev/checkers/tension_delta.py` — full file (71 lines) — DELETE
- `ccya/ev/checkers/tension_monotonicity.py` — full file (82 lines) — DELETE
- `ccya/ev/checkers/crisis_turn_counting.py` — full file (80 lines) — RENAME + UPDATE
- `ccya/ev/checkers/gm_beat.py` — full file (100 lines) — REMOVE enforce_relief
- `ccya/ev/checkers/beat_phase_validity.py` — full file (58 lines) — REMOVE enforce_relief comment
- `ccya/ev/checkers/pacing.py` — full file (249 lines) — REMOVE consecutive_pressure check
- `ccya/ev/checkers/phase_transition.py` — full file (78 lines) — RENAME CRISIS + crisis_turn_count
- `ccya/ev/checkers/phase_persistence.py` — update valid_phases

### Detailed steps

#### Step 1.1 — Delete tension_delta checker

**File:** `ccya/ev/checkers/tension_delta.py`

**What:** Delete the entire file. The `tension_delta` field no longer exists in `IntentEnvelope` or the event dict.

**Why:** Field removed from model and pipeline. Checker would always fail (field missing) or produce vacuous results.

**Validation:** File no longer exists on disk.

#### Step 1.2 — Delete tension_monotonicity checker

**File:** `ccya/ev/checkers/tension_monotonicity.py`

**What:** Delete the entire file. Same reasoning as tension_delta — field no longer exists.

**Why:** All checks reference `tension_delta` and `CRISIS` phase — both renamed or removed.

**Validation:** File no longer exists on disk.

#### Step 1.3 — Rename and update crisis_turn_counting → climax_turn_counting

**File:** `ccya/ev/checkers/crisis_turn_counting.py`

**What:**
- Rename file to `climax_turn_counting.py`.
- Rename checker id from `"crisis_turn_counting"` to `"climax_turn_counting"`.
- Rename all CRISIS→CLIMAX, `crisis_turn_count`→`climax_turn_count`, `crisis_count`→`climax_count` in variable names.
- Update description and all detail strings.
- Update import in the checker registry (`__init__.py`).

**Why:** Phase rename + state key rename.

**Validation:** `cp ccya/ev/checkers/crisis_turn_counting.py ccya/ev/checkers/climax_turn_counting.py; rm ccya/ev/checkers/crisis_turn_counting.py` then update the content.

#### Step 1.4 — Remove enforce_relief check from gm_beat checker

**File:** `ccya/ev/checkers/gm_beat.py`

**What:**
- Remove `from ccya.engine._pacing import derive_enforce_relief` import (line 8).
- Remove `from ccya.engine.config import EngineConfig` import (line 9) — only used by enforce_relief check.
- Remove the enforce_relief check block (lines 62-77).
- Update function description.

**Why:** `derive_enforce_relief` function deleted. `consecutive_pressure_beats` no longer emitted in event dict.

**Validation:** `grep -n 'enforce_relief\|derive_enforce_relief\|consecutive' ccya/ev/checkers/gm_beat.py` should return 0 matches.

#### Step 1.5 — Update beat_phase_validity checker

**File:** `ccya/ev/checkers/beat_phase_validity.py`

**What:**
- Remove the `breathing_room` bypass comment at line 30: `# breathing_room is an enforce_relief override, not a storyteller choice — always allowed`.
- Remove the bypass at lines 31-32 that skips `breathing_room` checks.
- (Optional but correct: `breathing_room` is now in the Scene Imperative allowed list, and still in `BEAT_PHASE_MAP["RESOLUTION"]` and `BEAT_PHASE_MAP["BREATHER"]`. It should be checked normally like any other beat.)

**Why:** `enforce_relief` mechanism removed. `breathing_room` should be validated against the phase's allowed list like any other beat. Platforms where `breathing_room` is legitimately allowed (RESOLUTION, BREATHER, Scene Imperative) will pass; platforms where it's not allowed (BASE CLIMAX) will correctly fail.

**Validation:** `grep -n 'enforce_relief\|breathing_room always' ccya/ev/checkers/beat_phase_validity.py` should return 0 (after removing the bypass).

#### Step 1.6 — Remove consecutive_pressure check from pacing checker

**File:** `ccya/ev/checkers/pacing.py`

**What:**
- Remove the import of `PRESSURE_BEAT_TYPES` from `ccya.engine.turn` (line 10) — only used by the consecutive_pressure check.
- Remove the consecutive_pressure tracking block (lines 25-52, approximately).
- The `gm_beat_type` extraction earlier in the loop can be kept if needed for other checks, but the `counter` extraction and `is_pressure` check should be removed.

**Why:** `post_extraction_consecutive_pressure_beats` no longer emitted in event dict.

**Validation:** `grep -n 'consecutive_pressure\|PRESSURE_BEAT_TYPES' ccya/ev/checkers/pacing.py` should return 0.

#### Step 1.7 — Update phase_transition checker

**File:** `ccya/ev/checkers/phase_transition.py`

**What:**
- Rename CRISIS→CLIMAX in `VALID_TRANSITIONS` (lines 11-17):
  ```python
  VALID_TRANSITIONS = {
      ("SETUP", "RISING"),
      ("RISING", "CLIMAX"),
      ("CLIMAX", "RESOLUTION"),
      ("RESOLUTION", "BREATHER"),
      ("BREATHER", "RISING"),
  }
  ```
- Rename `crisis_count`→`climax_count` (line 34).
- Update the outcome_hint consistency check (lines 37-45): change phase check from `"CRISIS"` to `"CLIMAX"`, update detail string.
- Remove `crisis_turn_count` reference (no longer needed for outcome_hint — Scene Imperative is now age-based only, not CLIMAX turn-limit-based).

**Why:** Phase rename + outcome_hint no longer driven by CLIMAX turn count.

**Validation:** `grep -n 'CRISIS\|crisis_' ccya/ev/checkers/phase_transition.py` should return 0 (after rename).

#### Step 1.8 — Update phase_persistence checker

**File:** `ccya/ev/checkers/phase_persistence.py`

**What:** Change `valid_phases` at line 36:
```python
valid_phases = {"SETUP", "RISING", "CLIMAX", "RESOLUTION", "BREATHER"}
```

**Why:** Phase rename.

**Validation:** `.venv/bin/python -c "from ccya.ev.checkers.phase_persistence import phase_persistence; pass"` — no import error.

#### Step 1.9 — Update checker registry in __init__.py

**File:** `ccya/ev/checkers/__init__.py`

**What:**
- Remove `tension_delta` and `tension_monotonicity` from the import line (line 124).
- Change `crisis_turn_counting` to `climax_turn_counting` in the import line.

**Why:** Checker file deletions and renames.

**Validation:** `.venv/bin/python -c "from ccya.ev.checkers import list_checkers; names = list_checkers(); assert 'tension_delta' not in names; assert 'tension_monotonicity' not in names; assert 'climax_turn_counting' in names"`

### Tests to write or update

No tests exist. Run `make check` after all Plan 3 phases complete.
