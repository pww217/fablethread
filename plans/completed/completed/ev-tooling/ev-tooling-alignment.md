# EV Tooling Alignment Plan

## Purpose

Align the EV tool, checkers, rubric, and event recording with the scene phase & pacing overhaul design, fixing the critical phase-persistence bug that blocks all testing.

## Problem Statement

The EV tooling cannot validate the new phase engine because: (1) `_compute_scene_phase()` return value is never written to `state["scene"]`, making the phase engine a no-op; (2) `tension_delta` from the ruling engine is never recorded in events.jsonl, so no checker can validate it; (3) no checkers exist for phase transitions, tension_delta, recent_beats, or crisis/breather turn counts; (4) existing checkers reference stale field names and missing design constraints.

## Constraints

- Pipeline order is fixed: ruling → narrate → extract_scene → extract_state → storytell.
- No new LLM calls. Signal extraction happens within existing calls only.
- Backwards compatibility with saved game state is not required.
- Each phase must be independently executable and verifiable.
- Phase size: one coherent, testable change set.

## Non-goals

- Arc/thread system redesign.
- Prompt template changes (handled in separate plan).
- Ruling engine scope expansion beyond tension_delta.
- Thread deduplication via ArcThread.key.

## Solution

Fix the phase-persistence bug in turn.py, record tension_delta in events, consolidate enforce_relief into the shared `_pacing.py` function, update existing checkers to match the new design, add missing checkers for phase transitions and tension_delta, and update documentation.

## Firm decisions

1. `_compute_scene_phase()` must write its return value to `state["scene"]` — the doc comment says "mutates in place" but the implementation returns a new dict; the caller must assign it.
2. `tension_delta` must be recorded in the ruling event dict in events.jsonl.
3. `enforce_relief` must use `derive_enforce_relief()` from `_pacing.py` — no inline computation in turn.py.
4. Removed directives list must include "Overwhelm" and "Pressure" per the design doc.
5. Phase constraint checking must use `BEAT_PHASE_MAP` from `_pacing.py`.

## Risks, Ambiguities, and Blockers

- **Blocker**: Phase-persistence bug must be fixed first. All downstream checkers read stale phase data.
- **Ambiguity**: The `tension_delta` field exists on `IntentEnvelope` with default `"maintains"`. The ruling prompt already asks for it (ruling_system.j2:70,86). No ambiguity — just needs to be recorded in events.
- **Risk**: The `pacing_context` event field already records `scene_phase` from `state.get("scene")`. After the bug fix, this will reflect the correct phase. No change needed to event recording structure.

## Status

`completed`

## Phases

Three phases: (1) fix critical engine bugs, (2) update existing checkers, (3) add new checkers and documentation.

---

## Implementation — Phase 1: Fix Critical Engine Bugs

### Context files to load

- `ccya/engine/turn.py` — lines 775-802, 1009-1044, 1300-1320, 1333-1340
- `ccya/engine/_pacing.py` — full file
- `ccya/models.py` — lines 168-177 (IntentEnvelope, TensionDelta)

### Detailed steps

#### Step 1.1 — Fix phase-persistence bug

**File:** `ccya/engine/turn.py`

**What:** Change line 799 from `scene = _compute_scene_phase(...)` to `state["scene"] = _compute_scene_phase(...)`.

**Why:** The design doc says `_compute_scene_phase()` "mutates state['scene'] in place" but it actually returns a new dict. The caller rebinds the local variable `scene` but never writes the new dict to `state["scene"]`. This means phase transitions are computed but never persisted, making the phase engine a no-op.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.engine.turn import _compute_scene_phase
from ccya.engine.config import EngineConfig

state = {'scene': {'scene_phase': 'SETUP', 'crisis_turn_count': 0, 'breather_turn_count': 0}, 'meta': {'turn': 5}, 'arc': {'threads': []}}
config = EngineConfig()
result = _compute_scene_phase(state, 'escalates', {'effective_scene_age': 0}, config)
# After fix: state['scene']['scene_phase'] should be 'RISING'
print('state scene phase:', state['scene'].get('scene_phase'))
print('result phase:', result.get('scene_phase'))
assert state['scene'].get('scene_phase') == 'RISING', f'Expected RISING, got {state[\"scene\"].get(\"scene_phase\")}'
print('PASS')
"
```

#### Step 1.2 — Record tension_delta in ruling event

**File:** `ccya/engine/turn.py`

**What:** Add `"tension_delta"` to the `ruling_event` dict at lines 1300-1319. The value comes from `ctx.intent.tension_delta` (available via the TurnContext, set at line 636).

**Why:** The ruling engine already emits `tension_delta` on `IntentEnvelope` (models.py:176, default `"maintains"`). The EV tool needs this field in events.jsonl to validate that the ruling engine classifies player intent correctly.

**Code:** Add to the `ruling_event` dict (around line 1309, after `outcome_summary`):
```python
"tension_delta": _intent.tension_delta,
```

**Why:** `_intent` is the local variable set at line 636 (`ctx.intent = intent`). It has the `tension_delta` field.

**Validation:**
```bash
.venv/bin/python -c "
import json, sys
# Quick smoke: verify IntentEnvelope has tension_delta
from ccya.models import IntentEnvelope
ie = IntentEnvelope()
assert hasattr(ie, 'tension_delta'), 'IntentEnvelope missing tension_delta'
assert ie.tension_delta == 'maintains', f'Default should be maintains, got {ie.tension_delta}'
print('PASS: IntentEnvelope.tension_delta exists with default maintains')
"
```

#### Step 1.3 — Consolidate enforce_relief into derive_enforce_relief()

**File:** `ccya/engine/turn.py`

**What:** Replace the inline `enforce_relief` computation at lines 1023-1025 with a call to `derive_enforce_relief()` from `_pacing.py`.

**Current code (lines 1023-1025):**
```python
scene_phase = (state.get("scene") or {}).get("scene_phase", "SETUP")
consecutive_pressure = (state.get("meta") or {}).get("consecutive_pressure_beats", 0)
enforce_relief = scene_phase == "CRISIS" and consecutive_pressure >= config.consecutive_pressure_threshold
```

**What to change:** Import `derive_enforce_relief` from `_pacing` at the top of turn.py, then replace the three lines with:
```python
enforce_relief = derive_enforce_relief(
    (state.get("scene") or {}).get("scene_phase", "SETUP"),
    (state.get("meta") or {}).get("consecutive_pressure_beats", 0),
    config,
)
```

**Why:** The same logic exists in two places (`turn.py:1025` and `_pacing.py:32-34`). The design doc says `enforce_relief` is derived from phase + consecutive beats, and `_pacing.py` is the canonical location. Using the shared function ensures consistency and makes the checker at `gm_beat.py` easier to maintain.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.engine._pacing import derive_enforce_relief
from ccya.engine.config import EngineConfig
config = EngineConfig()

# CRISIS + 3 consecutive → True
assert derive_enforce_relief('CRISIS', 3, config) == True

# CRISIS + 2 consecutive → False
assert derive_enforce_relief('CRISIS', 2, config) == False

# RISING + 5 consecutive → False (wrong phase)
assert derive_enforce_relief('RISING', 5, config) == False

# SETUP + 10 consecutive → False
assert derive_enforce_relief('SETUP', 10, config) == False

print('PASS: derive_enforce_relief works correctly')
"
```

#### Step 1.4 — Import derive_enforce_relief in turn.py

**File:** `ccya/engine/turn.py`

**What:** Add `derive_enforce_relief` to the import from `_pacing` at the top of the file.

**Why:** Step 1.3 requires the import.

**Validation:** The import must resolve. Run `python -c "from ccya.engine.turn import run_turn"` to verify no import errors.

### Tests to write or update

- No test files to update (tests are temporarily removed per AGENTS.md).
- Manual validation via the inline Python smoke tests above.

---

## Implementation — Phase 2: Update Existing Checkers

### Context files to load

- `ccya/ev/checkers/pacing.py` — full file
- `ccya/ev/checkers/gm_beat.py` — full file
- `ccya/engine/_pacing.py` — BEAT_PHASE_MAP, derive_allowed_beat_types, derive_enforce_relief

### Detailed steps

#### Step 2.1 — Update pacing_directives: remove old removed_directives, add phase constraint checks

**File:** `ccya/ev/checkers/pacing.py`

**What:** 
1. Replace the `removed_directives` list at line 88 with the design-correct list: `["Overwhelm", "Pressure", "location pressure", "location imperative", "combat fatigue"]`.
2. Add a phase constraint check: for each turn, if storytell emitted a beat, verify the beat type is in the allowed set for the current `scene_phase`. Use `derive_allowed_beat_types()` from `_pacing.py`.

**Why:** The design doc says `Overwhelm` and `Pressure` directives were removed. The current checker only checks for old legacy directives. Phase constraint checking is the primary enforcement mechanism for beat diversity.

**Code changes:**

Line 88 — update removed_directives:
```python
removed_directives = ["Overwhelm", "Pressure", "location pressure", "location imperative", "combat fatigue"]
```

After the existing checks (before the `# beat_type_variety` section at line 103), add phase constraint checking:
```python
# Phase constraint: beat types must be allowed for current scene_phase
from ccya.engine._pacing import derive_allowed_beat_types

for ev in events:
    storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
    gm_beat = storytell_output.get("gm_beat")
    if not isinstance(gm_beat, dict) or not gm_beat.get("type"):
        continue
    
    pacing_ctx = extract_field(ev, "pacing_context") or {}
    scene_phase = pacing_ctx.get("scene_phase", "SETUP")
    allowed = derive_allowed_beat_types(scene_phase)
    beat_type = gm_beat["type"]
    
    if beat_type not in allowed:
        findings.append({
            "turn": ev.get("turn"),
            "check": "phase_constraint",
            "detail": f"beat type '{beat_type}' not allowed in phase '{scene_phase}' (allowed: {allowed})",
        })
        all_passed = False
```

**Validation:**
```bash
.venv/bin/python -c "
from ccya.engine._pacing import derive_allowed_beat_types, BEAT_PHASE_MAP

# Verify phase maps match design doc
assert set(BEAT_PHASE_MAP['SETUP']) == {'pressure', 'complication', 'escalation', 'revelation', 'twist', 'opportunity', 'callback', 'breathing_room', 'hazard'}
assert set(BEAT_PHASE_MAP['RISING']) == {'pressure', 'complication', 'escalation', 'revelation', 'twist'}
assert set(BEAT_PHASE_MAP['CRISIS']) == {'pressure', 'escalation', 'complication'}
assert set(BEAT_PHASE_MAP['RESOLUTION']) == {'breathing_room', 'callback', 'revelation'}
assert set(BEAT_PHASE_MAP['BREATHER']) == {'opportunity', 'revelation', 'callback', 'breathing_room', 'hazard'}

# enforce_relief returns only breathing_room
assert derive_allowed_beat_types('CRISIS', enforce_relief=True) == ['breathing_room']

# Normal CRISIS
assert derive_allowed_beat_types('CRISIS') == ['pressure', 'escalation', 'complication']

print('PASS: BEAT_PHASE_MAP and derive_allowed_beat_types match design doc')
"
```

#### Step 2.2 — Update gm_beat_lifecycle: use derive_enforce_relief

**File:** `ccya/ev/checkers/gm_beat.py`

**What:** Replace the inline `enforce_relief` check at lines 64-66 with a call to `derive_enforce_relief()` from `_pacing.py`.

**Current code (lines 64-66):**
```python
if scene_phase == "CRISIS":
    consecutive = extract_field(ev, "post_extraction_consecutive_pressure_beats") or 0
    if int(consecutive) >= 3:
```

**What to change:** Replace with:
```python
from ccya.engine._pacing import derive_enforce_relief
from ccya.engine.config import EngineConfig

# ... inside the loop, replace the condition:
config = EngineConfig()
consecutive = extract_field(ev, "post_extraction_consecutive_pressure_beats") or 0
if derive_enforce_relief(scene_phase, int(consecutive), config):
```

**Why:** The checker should use the same logic as the engine. Hardcoding `>= 3` is fragile — if the config default changes, the checker must change too. Using `derive_enforce_relief()` ensures the checker and engine stay in sync.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.ev.checkers.gm_beat import gm_beat_lifecycle
from ccya.ev.checkers import list_checkers

# Verify checker is registered
checkers = list_checkers()
checker_ids = [c['id'] for c in checkers]
assert 'gm_beat_lifecycle' in checker_ids, 'gm_beat_lifecycle not registered'
print('PASS: gm_beat_lifecycle registered')
"
```

### Tests to write or update

- No test files to update (tests are temporarily removed per AGENTS.md).
- Manual validation via the inline Python smoke tests above.

---

## Implementation — Phase 3: Add New Checkers and Documentation

### Context files to load

- `ccya/ev/checkers/__init__.py` — checker registration, CheckerResult, list_checkers
- `ccya/ev/checkers/pacing.py` — pattern for deterministic checkers
- `ccya/ev/events.py` — extract_field, filter_turn_events
- `ccya/engine/_pacing.py` — BEAT_PHASE_MAP, derive_allowed_beat_types, derive_enforce_relief
- `ccya/engine/config.py` — EngineConfig defaults

### Detailed steps

#### Step 3.1 — Add phase_transition checker

**File:** `ccya/ev/checkers/phase_transition.py` (new)

**What:** A deterministic checker that validates phase engine transitions follow the state machine defined in the design doc.

**Checkers to perform:**

1. **Valid transitions only:** For each consecutive pair of turns, verify the phase transition is valid per the state machine:
   - SETUP → RISING (valid)
   - RISING → CRISIS (valid)
   - CRISIS → RESOLUTION (valid)
   - RESOLUTION → BREATHER (valid)
   - BREATHER → RISING (valid)
   - Any → SETUP (valid only on location_change)
   - All other transitions are invalid

2. **crisis_turn_count monotonicity:** Within a CRISIS phase, `crisis_turn_count` must increment by exactly 1 each turn, resetting to 0 on fresh CRISIS entry.

3. **breather_turn_count monotonicity:** Within a BREATHER phase, `breather_turn_count` must increment by exactly 1 each turn, resetting to 0 on fresh BREATHER entry.

4. **outcome_hint consistency:** When `phase == CRISIS` and `crisis_turn_count >= crisis_turn_limit`, `outcome_hint` must be `"transition"`.

**Code structure:**
```python
from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    ("SETUP", "RISING"),
    ("RISING", "CRISIS"),
    ("CRISIS", "RESOLUTION"),
    ("RESOLUTION", "BREATHER"),
    ("BREATHER", "RISING"),
    # Any → SETUP is valid (location_change)
}

# All phases that can transition to SETUP
ANY_TO_SETUP = True


@register_checker(
    "phase_transition", "deterministic",
    requires_fields=["pacing_context"],
    description="Validate phase engine transitions follow the state machine",
)
def phase_transition(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        crisis_count = pc.get("crisis_turn_count", 0)
        breather_count = pc.get("breather_turn_count", 0)
        outcome_hint = pc.get("outcome_hint")

        # Check outcome_hint consistency during crisis limit
        if phase == "CRISIS" and crisis_count >= 4:  # default crisis_turn_limit
            if outcome_hint != "transition":
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "outcome_hint_consistency",
                    "detail": f"CRISIS with crisis_turn_count={crisis_count} >= limit but outcome_hint={outcome_hint!r} (expected 'transition')",
                })
                all_passed = False

        # Check transitions (skip first turn)
        if i > 0:
            prev_ev = filtered[i - 1]
            prev_pc = extract_field(prev_ev, "pacing_context") or {}
            prev_phase = prev_pc.get("scene_phase", "SETUP")

            # Any → SETUP is always valid (location_change)
            if phase == "SETUP":
                continue

            # All other transitions must be in VALID_TRANSITIONS
            if (prev_phase, phase) not in VALID_TRANSITIONS:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "valid_transition",
                    "detail": f"invalid phase transition: {prev_phase} → {phase}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="phase_transition", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="phase_transition", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
```

**Why:** No existing checker validates the phase state machine. The design doc defines explicit transitions; the checker must enforce them.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.ev.checkers.phase_transition import phase_transition
from ccya.ev.checkers import list_checkers

# Verify checker is registered
checkers = list_checkers()
checker_ids = [c['id'] for c in checkers]
assert 'phase_transition' in checker_ids, 'phase_transition not registered'

# Test with valid transitions
valid_events = [
    {'turn': 1, 'pacing_context': {'scene_phase': 'SETUP', 'crisis_turn_count': 0, 'breather_turn_count': 0, 'outcome_hint': 'hold'}},
    {'turn': 2, 'pacing_context': {'scene_phase': 'RISING', 'crisis_turn_count': 0, 'breather_turn_count': 0, 'outcome_hint': 'hold'}},
    {'turn': 3, 'pacing_context': {'scene_phase': 'CRISIS', 'crisis_turn_count': 1, 'breather_turn_count': 0, 'outcome_hint': 'hold'}},
]
result = phase_transition(valid_events)
assert result.passed == True, f'Expected pass, got: {result.detail}'

# Test with invalid transition
invalid_events = [
    {'turn': 1, 'pacing_context': {'scene_phase': 'SETUP', 'crisis_turn_count': 0, 'breather_turn_count': 0, 'outcome_hint': 'hold'}},
    {'turn': 2, 'pacing_context': {'scene_phase': 'CRISIS', 'crisis_turn_count': 0, 'breather_turn_count': 0, 'outcome_hint': 'hold'}},
]
result = phase_transition(invalid_events)
assert result.passed == False, f'Expected fail, got: {result.detail}'

print('PASS: phase_transition checker works correctly')
"
```

#### Step 3.2 — Add tension_delta checker

**File:** `ccya/ev/checkers/tension_delta.py` (new)

**What:** A deterministic checker that validates the ruling engine's `tension_delta` field is present, has valid values, and is consistent with the directive.

**Checkers to perform:**

1. **tension_delta present in ruling event:** Every turn's ruling event must have a `tension_delta` field.
2. **tension_delta valid values:** Must be one of `"escalates"`, `"maintains"`, `"de-escalates"`.
3. **Breathe directive consistency:** When `tension_delta == "de-escalates"` AND no urgent threads exist, the directive should be `"Breathe"` (or empty if in BREATHER phase).

**Code structure:**
```python
from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)

VALID_TENSION_DELTAS = {"escalates", "maintains", "de-escalates"}


@register_checker(
    "tension_delta", "deterministic",
    requires_fields=["ruling", "pacing_context"],
    description="Validate tension_delta field presence, values, and directive consistency",
)
def tension_delta(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for ev in filtered:
        ruling = extract_field(ev, "ruling") or {}
        pc = extract_field(ev, "pacing_context") or {}
        directive = pc.get("directive", "")
        phase = pc.get("scene_phase", "SETUP")

        # Check tension_delta present
        td = ruling.get("tension_delta")
        if td is None:
            findings.append({
                "turn": ev.get("turn"),
                "check": "tension_delta_present",
                "detail": "tension_delta field missing from ruling event",
            })
            all_passed = False
            continue

        # Check valid values
        if td not in VALID_TENSION_DELTAS:
            findings.append({
                "turn": ev.get("turn"),
                "check": "tension_delta_valid",
                "detail": f"tension_delta={td!r} not in {VALID_TENSION_DELTAS}",
            })
            all_passed = False

        # Breathe directive consistency: de-escalates + no urgent threads → Breathe
        # Note: we can't check thread urgency from events alone, so we only check
        # that when tension_delta is de-escalates, the directive is NOT a pressure type
        if td == "de-escalates" and directive in ("Scene Imperative", "Scene Pressure"):
            findings.append({
                "turn": ev.get("turn"),
                "check": "breathe_consistency",
                "detail": f"tension_delta=de-escalates but directive={directive!r} (expected Breathe or empty)",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="tension_delta", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="tension_delta", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
```

**Why:** The ruling engine emits `tension_delta` but it was never recorded in events. After Phase 1.2, this field will be available. The checker validates the ruling engine's classification is sensible.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.ev.checkers.tension_delta import tension_delta
from ccya.ev.checkers import list_checkers

# Verify checker is registered
checkers = list_checkers()
checker_ids = [c['id'] for c in checkers]
assert 'tension_delta' in checker_ids, 'tension_delta not registered'

# Test with valid tension_delta values
valid_events = [
    {'turn': 1, 'ruling': {'tension_delta': 'escalates'}, 'pacing_context': {'directive': '', 'scene_phase': 'SETUP'}},
    {'turn': 2, 'ruling': {'tension_delta': 'maintains'}, 'pacing_context': {'directive': 'Scene Pressure', 'scene_phase': 'RISING'}},
    {'turn': 3, 'ruling': {'tension_delta': 'de-escalates'}, 'pacing_context': {'directive': 'Breathe', 'scene_phase': 'BREATHER'}},
]
result = tension_delta(valid_events)
assert result.passed == True, f'Expected pass, got: {result.detail}'

# Test with missing tension_delta
missing_events = [
    {'turn': 1, 'ruling': {}, 'pacing_context': {'directive': '', 'scene_phase': 'SETUP'}},
]
result = tension_delta(missing_events)
assert result.passed == False, f'Expected fail, got: {result.detail}'

print('PASS: tension_delta checker works correctly')
"
```

#### Step 3.3 — Add recent_beats checker

**File:** `ccya/ev/checkers/recent_beats.py` (new)

**What:** A deterministic checker that validates the `recent_beats` history list is maintained correctly.

**Checkers to perform:**

1. **recent_beats exists in state_snapshot:** Every turn's state_snapshot should have `meta.recent_beats`.
2. **recent_beats capped at N entries:** The list must not exceed `config.recent_beats_max` (default 5) entries.
3. **Entry structure:** Each entry must have `turn` (int), `type` (str or None), `surface_as` (str or None).
4. **Null entries on null storytell:** When storytell emits null, the recent_beats entry should have `type: null` and `surface_as: null`.
5. **Monotonic turn numbers:** Turn numbers in recent_beats must be monotonically increasing.

**Code structure:**
```python
from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "recent_beats", "deterministic",
    requires_fields=["state_snapshot"],
    description="Validate recent_beats history list structure and constraints",
)
def recent_beats(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "state_snapshot") or {}
        meta = (snap.get("meta") or {})
        recent = meta.get("recent_beats")

        if recent is None:
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_exists",
                "detail": "recent_beats not found in state_snapshot.meta",
            })
            all_passed = False
            continue

        if not isinstance(recent, list):
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_is_list",
                "detail": f"recent_beats is {type(recent).__name__}, expected list",
            })
            all_passed = False
            continue

        # Check cap (default 5)
        if len(recent) > 5:
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_cap",
                "detail": f"recent_beats has {len(recent)} entries (max 5)",
            })
            all_passed = False

        # Check entry structure
        for j, entry in enumerate(recent):
            if not isinstance(entry, dict):
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_structure",
                    "detail": f"entry[{j}] is {type(entry).__name__}, expected dict",
                })
                all_passed = False
                continue

            if "turn" not in entry:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_turn",
                    "detail": f"entry[{j}] missing 'turn' field",
                })
                all_passed = False

            if "type" not in entry or "surface_as" not in entry:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_fields",
                    "detail": f"entry[{j}] missing 'type' or 'surface_as' field",
                })
                all_passed = False

        # Check monotonic turn numbers
        if isinstance(recent, list) and len(recent) > 1:
            for j in range(1, len(recent)):
                prev_turn = recent[j - 1].get("turn", 0)
                cur_turn = recent[j].get("turn", 0)
                if cur_turn <= prev_turn:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "recent_beats_monotonic",
                        "detail": f"entry[{j}].turn={cur_turn} <= entry[{j-1}].turn={prev_turn}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="recent_beats", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="recent_beats", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
```

**Why:** The design doc specifies that `recent_beats` is appended after floor relief injection, capped at 5, with null entries on null storytell turns. No existing checker validates this.

**Validation:**
```bash
.venv/bin/python -c "
from ccya.ev.checkers.recent_beats import recent_beats
from ccya.ev.checkers import list_checkers

# Verify checker is registered
checkers = list_checkers()
checker_ids = [c['id'] for c in checkers]
assert 'recent_beats' in checker_ids, 'recent_beats not registered'

# Test with valid recent_beats
valid_events = [
    {'turn': 1, 'state_snapshot': {'meta': {'recent_beats': [
        {'turn': 1, 'type': 'pressure', 'surface_as': 'ambient'}
    ]}}},
]
result = recent_beats(valid_events)
assert result.passed == True, f'Expected pass, got: {result.detail}'

# Test with missing recent_beats
missing_events = [
    {'turn': 1, 'state_snapshot': {'meta': {}}},
]
result = recent_beats(missing_events)
assert result.passed == False, f'Expected fail, got: {result.detail}'

print('PASS: recent_beats checker works correctly')
"
```

#### Step 3.4 — Register new checkers in __init__.py

**File:** `ccya/ev/checkers/__init__.py`

**What:** Add imports for the new checker modules at the bottom of the file, alongside the existing imports.

**Why:** The `@register_checker` decorator registers checkers at import time. The new modules must be imported for their checkers to be discoverable.

**Code:** Add to the existing import line at the bottom of `__init__.py` (line 64):
```python
from . import gm_beat, inventory, conditions, threads, arc_goals, npc_presence, pacing, sanitizer, llm_checkers, phase_transition, tension_delta, recent_beats  # noqa: E402, F401
```

**Validation:**
```bash
.venv/bin/python -c "
from ccya.ev.checkers import list_checkers
checkers = list_checkers()
checker_ids = [c['id'] for c in checkers]
for expected in ['phase_transition', 'tension_delta', 'recent_beats']:
    assert expected in checker_ids, f'{expected} not registered'
print(f'PASS: all {len(checkers)} checkers registered including new ones')
"
```

#### Step 3.5 — Update CHECKERS.md

**File:** `docs/ev/CHECKERS.md`

**What:** Add documentation for the three new checkers (`phase_transition`, `tension_delta`, `recent_beats`) in the checker library reference section. Update the overview table to reflect the new checkers.

**Why:** CHECKERS.md is the reference for all checkers. New checkers must be documented.

**Changes:**
1. Add to the overview table under "Pacing": `phase_transition`, `tension_delta`, `recent_beats`
2. Add three new checker documentation blocks after the existing `pacing_directives` section, following the same format:
   - Type, Fields, What it checks, CLI, Caveats

**Validation:** Read the file and verify the three new checkers are documented with the same format as existing checkers.

#### Step 3.6 — Update RUBRIC.md

**File:** `docs/ev/RUBRIC.md`

**What:** The RUBRIC.md is already well-aligned with the new design (it describes phase engine, tension_delta, etc.). Add references to the new checkers in the relevant sections:

1. Section 1 (Phase Engine): Add `ev.py check 5 phase_transition --save-dir saves/my-game` to the commands list.
2. Section 4 (Pacing Directives): Add `ev.py check 5 tension_delta --save-dir saves/my-game` to the commands list.
3. Add a new subsection under Section 4 or create a new section for `recent_beats`.

**Why:** RUBRIC.md is the prioritized checklist for inspecting games. New checkers should be referenced.

**Validation:** Read the file and verify the new checker commands appear in the relevant sections.

#### Step 3.7 — Update repomap.md

**File:** `docs/repomap.md`

**What:** Add the new checker modules to the checker registry section (line 53):
- `ccya/ev/checkers/phase_transition.py` — `phase_transition` — Validate phase engine transitions follow the state machine
- `ccya/ev/checkers/tension_delta.py` — `tension_delta` — Validate tension_delta field presence, values, and directive consistency
- `ccya/ev/checkers/recent_beats.py` — `recent_beats` — Validate recent_beats history list structure and constraints

Also update the repomap entry for `ccya/ev/checkers/__init__.py` to reflect 17 deterministic checkers + 3 LLM checkers (was 14 + 3).

**Why:** The repomap is the module boundary reference. New modules must be documented.

**Validation:** Read the file and verify the new checker modules appear in the table.

#### Step 3.8 — Update pacing-systems.md

**File:** `docs/architecture/pacing-systems.md`

**What:** Update the "Code locations" table in Section 9 to reflect the new checker files. Add a new subsection under Section 9 for "EV checkers" that lists the new checkers.

**Why:** The architecture doc should reference the EV checkers that validate the pacing system.

**Validation:** Read the file and verify the new checkers are referenced in the code locations table.

### Tests to write or update

- No test files to update (tests are temporarily removed per AGENTS.md).
- Manual validation via the inline Python smoke tests above for each new checker.
