# Convergence Scoring — Phase 2: CRISIS→CLIMAX Rename + Dead Code Removal

**Status: completed** (2026-06-15)

## Purpose

Mechanical rename of all CRISIS→CLIMAX references across the codebase, and removal of dead machinery (`derive_enforce_relief`, `consecutive_pressure_beats`, `enforce_relief` parameter, `tension_delta` from phase machine, Breathe directive). Phase 1 must be complete (config field names exist, model fields are gone).

## Firm decisions

- `state["scene"]["crisis_turn_count"]` → `state["scene"]["climax_turn_count"]` everywhere.
- `BEAT_PHASE_MAP["CRISIS"]` → `BEAT_PHASE_MAP["CLIMAX"]`.
- `derive_enforce_relief()` deleted — no replacement.
- `enforce_relief` parameter removed from `derive_allowed_beat_types()`.
- `consecutive_pressure_beats` counter removed. No replacement — `recent_beats` streak in convergence score replaces.
- `tension_delta` parameter removed from `_compute_scene_phase`, `_compute_narration_directive`, `_compute_pacing_context`.
- Breathe directive priority branch removed from `_compute_narration_directive` (dead code — 0% de-escalates).
- `tension_delta` removed from ruling_event dict and pacing_context logging.
- Prompt references: all CRISIS→CLIMAX, twist→setback in Scene Imperative list (but Curtain Call guidance deferred to Phase 4).
- `TensionDelta` type alias removed from `ccya/models.py` (deferred from Phase 1 — its last consumer `turn.py` is updated in this phase).
- `TensionDelta` import removed from `ccya/engine/turn.py` (type alias deleted in this phase).

## Status

`completed`

## Dependencies

- Phase 1 complete (EngineConfig fields exist, IntentEnvelope.tension_delta gone).

## Implementation — Phase 2: Rename + Dead Code Removal

### Context files to load

- `ccya/engine/_pacing.py` — full file (94 lines)
- `ccya/engine/turn.py` — `PRESSURE_BEAT_TYPES` import context (line 27), `_compute_narration_directive` (405-441), `_compute_pacing_context` (444-486), `_compute_scene_phase` (503-582), narrate-setup block (760-834), post-extraction block (1020-1067), event dict (1365-1400), `derive_enforce_relief` imports
- `ccya/engine/extraction.py` — import (line 19), storytell message builder (373-382), any other `derive_enforce_relief` or `enforce_relief` references
- `ccya/prompts/ruling_system.j2` — Scene Phase schema reference (lines 61, 76, 92)
- `ccya/prompts/storytell_system.j2` — Scene Imperative beat list (line 71), CRISIS phase reference (any)
- `ccya/prompts/storytell_user.j2` — (check for CRISIS references)
- `ccya/prompts/sections/` — any CRISIS references in subtemplates

### Detailed steps

#### Step 2.1 — CRISIS→CLIMAX rename in BEAT_PHASE_MAP

**File:** `ccya/engine/_pacing.py`

**What:** Rename the key in `BEAT_PHASE_MAP` at line 24:
```python
"CLIMAX":      ["pressure", "escalation", "complication"],
```

**Why:** Phase name rename throughout.

**Validation:** `.venv/bin/python -c "from ccya.engine._pacing import BEAT_PHASE_MAP; assert 'CLIMAX' in BEAT_PHASE_MAP; assert 'CRISIS' not in BEAT_PHASE_MAP"`

#### Step 2.2 — CRISIS→CLIMAX rename in state keys and variables

**File:** `ccya/engine/turn.py`

**What:**
- In `_compute_scene_phase` (line 503): rename all `crisis_turn_count` → `climax_turn_count`. Includes:
  - `scene.setdefault("crisis_turn_count", 0)` → `scene.setdefault("climax_turn_count", 0)` (line 522)
  - `crisis_turn_count = scene.get("crisis_turn_count", 0)` → `climax_turn_count = scene.get("climax_turn_count", 0)` (line 526)
  - Return dict key `"crisis_turn_count"` → `"climax_turn_count"` (line 582)
  - All internal `crisis_turn_count` variable names (lines 556, 558, 562)
- In narrate-setup block (lines 771-796): rename all `crisis_turn_count` → `climax_turn_count`
- In `_compute_narration_directive` (line 409): `crisis_turn_count` → `climax_turn_count`
- In `_compute_pacing_context` (line 448): `crisis_turn_count` → `climax_turn_count`, `crisis_turn_limit` → `climax_turn_limit`
- In event dict pacing_context sub-dict (line 1380): rename `"crisis_turn_count"` → `"climax_turn_count"`

**Why:** Consistent naming across all phase-machine-related code.

**Validation:** `grep -n 'crisis_turn' ccya/engine/turn.py` should return 0 matches (after rename).

#### Step 2.3 — Remove derive_enforce_relief and enforce_relief parameter

**File:** `ccya/engine/_pacing.py`

**What:**
- Delete `derive_enforce_relief()` function at lines 92-94.
- Remove `enforce_relief: bool = False` parameter from `derive_allowed_beat_types()` at line 63.
- Remove the `if scene_phase == "CRISIS" and enforce_relief:` priority branch at lines 80-81.

**Why:** Dead code (fired 0/49 turns). Convergence score's beat streak component replaces its function.

**Validation:** `.venv/bin/python -c "from ccya.engine._pacing import derive_enforce_relief"` should raise ImportError.

#### Step 2.4 — Remove derive_enforce_relief import and call from turn.py

**File:** `ccya/engine/turn.py`

**What:**
- Remove `derive_enforce_relief` from the import at line 27.
- Remove the `consecutive_pressure_beats` counter tracking block at lines 1042-1050.
- Remove the floor relief injection block at lines 1052-1067.
- In the event dict (lines 1384-1399): remove `"post_extraction_consecutive_pressure_beats"` key, remove `enforce_relief` parameter from `derive_allowed_beat_types` call, remove `"enforce_relief"` key.

**Why:** All dead code. `recent_beats` streak (Phase 3) replaces pressure beat tracking.

**Validation:** `grep -n 'derive_enforce_relief\|enforce_relief\|consecutive_pressure_beats\|consecutive_pressure' ccya/engine/turn.py` should return 0 matches.

#### Step 2.5 — Remove derive_enforce_relief import and call from extraction.py

**File:** `ccya/engine/extraction.py`

**What:**
- Remove `derive_enforce_relief` from the import at line 19.
- In `_storytell_messages()` (lines 373-382): change the `derive_allowed_beat_types()` call to remove `enforce_relief` parameter:
```python
"allowed_beat_types": derive_allowed_beat_types(
    scene.get("scene_phase", "SETUP"),
    directive=pacing_context.directive if pacing_context else "",
    spiral_detected=pacing_context.spiral_detected if pacing_context else False,
),
```

**Why:** `enforce_relief` parameter removed from `derive_allowed_beat_types()`.

**Validation:** `grep -rn 'enforce_relief' ccya/engine/` should return 0 matches.

#### Step 2.6 — Remove tension_delta from phase machine functions

**File:** `ccya/engine/turn.py`

**What:**
- Remove `tension_delta` from `_compute_narration_directive` signature and usage (lines 407, 429-430). Remove the Breathe priority branch entirely (lines 428-430).
- Remove `tension_delta` from `_compute_pacing_context` signature and call (lines 446, 462).
- Remove `tension_delta` from `_compute_scene_phase` signature (line 505) and both checks: SETUP→RISING tension_delta check (lines 550-551), RISING→CRISIS tension_delta check (lines 557-558). The RISING→CLIMAX transition will be replaced by convergence score in Phase 3 — for now, leave RISING without any CRISIS/CLIMAX entry path (Phase 3 adds it back via convergence score).
- In the narrate-setup block (lines 771, 794, 800-809): remove `tension_delta` variable and all references.
- Remove `TensionDelta` from the import at line 47 (`from ccya.models import ... TensionDelta`).
- Remove `TensionDelta` type alias from `ccya/models.py` at line 18 (deferred from Phase 1 — now safe since turn.py no longer imports it).
- Remove `tension_delta` from ruling_event dict (line 1350).

**Why:** `tension_delta` is dead signal. Breathe directive removed per user resolution. Phase machine will use convergence score for RISING→CLIMAX entry.

**Validation:** `.venv/bin/python -c "from ccya.engine.turn import _compute_scene_phase; help(_compute_scene_phase)"` — check signature has no `tension_delta` param.

#### Step 2.7 — CRISIS→CLIMAX rename in prompts

**Files:**
- `ccya/prompts/ruling_system.j2` — rewrites to CLIMAX at lines 61-63
- `ccya/prompts/storytell_system.j2` — any CRISIS references
- `ccya/prompts/storytell_user.j2` — check for CRISIS (should show phase dynamically, not hardcoded)
- `ccya/prompts/sections/` — glob and grep for CRISIS

**What:**
- Replace all CRISIS→CLIMAX references in prompt text (not variable names — those come from state keys which are already renamed).
- In `storytell_system.j2` line 72: remove the Breathe directive entry from the "Directive overrides" table (Breathe directive removed in this phase).
- In `storytell_system.j2` line 38: change "avoid Breathe turns" to "avoid prolonged climactic turns" or similar (Breathe no longer exists as a directive concept).

**Why:** Phase rename. Breathe directive removed entirely.

**Validation:** `grep -rn 'CRISIS' ccya/prompts/` should return 0 matches. `grep -rn '"Breathe"\|"Breathe"\|Breathe' ccya/prompts/` — after changes, only prose references to "breathe" as a verb should remain.

#### Step 2.8 — Remove Breathe from derive_allowed_beat_types

**File:** `ccya/engine/_pacing.py`

**What:** Remove the Breathe directive priority branch at lines 77-78 (or let it become unreachable — the directive string won't be "Breathe" anymore since no code sets it). Actually, since we removed the Breathe trigger in `_compute_narration_directive`, the directive string can never be "Breathe", so the branch is dead but harmless. Optionally remove the branch for cleanliness.

**Why:** Breathe directive removed entirely.

**Validation:** `grep -n 'Breathe' ccya/engine/turn.py` should return 0 matches (outside comments). `grep -n '"Breathe"\|"Breathe"' ccya/prompts/` — Breathe directive reference in storytell_system.j2:72 directive table should be removed.

### Tests to write or update

No tests exist. Run `make check` at Phase 4 completion (will fail on these changes until Phase 3 restores the phase machine entry path).
