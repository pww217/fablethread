# Plan 2: Phase Engine and Directive Rewrite

## Purpose

Implement the scene phase state machine, phase-driven directive computation, and beat constraint derivation in `turn.py`. This is the core behavioral change — everything after this reads `scene_phase` as the primary pacing signal.

## Problem Statement

The pacing system has no explicit scene state. Directive computation infers urgency from three broken signals (`momentum`, `narrative_velocity`, `consecutive_pressure_turns`) that produce wrong behavior — Breathe fires during active raids, Pressure/Overwhelm never fire, and beat diversity is structurally impossible without beat history context. The fix is a single authoritative `scene_phase` field computed from thread urgency, `tension_delta`, and scene age, consumed by a simplified directive stack.

## Constraints

- Pipeline order unchanged: ruling → narrate → extract_scene → extract_state → storytell.
- Phase engine runs after ruling (needs `tension_delta` from `intent`) and before directive computation (needs `scene_phase`).
- Old fields (`momentum`, `narrative_velocity`, `beat_locked`, `gate`, `consecutive_pressure_turns`) remain in `PacingContext` and event logging until Plan 4 deletes them. This plan adds new fields alongside them — no deletions.
- Scene phase state is stored in `state["scene"]` dict alongside existing fields like `turn_entered`.
- `location_change` is detected from the scene extraction result (already exists in the pipeline).

## Non-goals

- No prompt template changes — all `.j2` updates are Plan 3.
- No deletion of old fields — that's Plan 4.
- No changes to `extraction.py` beyond adding `scene_phase` and `allowed_beat_types` to the storytell context dict.
- No changes to EV tools, server routes, or UI templates.
- No changes to `config.yaml` — new fields have defaults.
- No thread hygiene improvements — assumes existing thread system.

## Solution

Add `_compute_scene_phase()` as a new function in `turn.py` implementing the 5-state machine (SETUP → RISING → CRISIS → RESOLUTION → BREATHER) with hard configurable thresholds. Call it in `_narrate_setup()` after ruling and age computation, before `_compute_pacing_context()`. Rewrite `_compute_narration_directive()` to consume `scene_phase`, `tension_delta`, and `thread_urgency_count` instead of the old signals. Add `allowed_beat_types` and `enforce_relief` derivation functions. Update beat lifecycle to track `consecutive_pressure_beats` (beat-based, not directive-based). Wire `scene_phase` through to the storytell context in `extraction.py`.

## Firm decisions

1. **Phase transitions use hard `>=` thresholds** against three inputs: `thread_urgency_count` (primary), `tension_delta` (accelerant), `effective_scene_age` (backstop). No weighted sums.
2. **`location_change` → SETUP always, never RESOLUTION.** RESOLUTION is entered only via `crisis_turn_count >= crisis_turn_limit`.
3. **`tension_delta` is an accelerant, not a decider.** Thread urgency overrides — an urgent thread during `de-escalates` does not suppress CRISIS.
4. **`enforce_relief` replaces `beat_locked`'s floor-relief role.** Fires during CRISIS when `consecutive_pressure_beats >= 3`. Does NOT append `"; Resolve a Threat"` — that behavior is deleted as part of Plan 4.
5. **`consecutive_pressure_beats` replaces `consecutive_pressure_turns`.** New counter tracks beat-type streaks (reads `pending_gm_beat.type`), not directive-type streaks. Semantics differ — this is not a rename.
6. **Beat history append already exists** at `turn.py:1156-1167`. The write/pop lifecycle already matches the design spec. Plan 2 only changes the pressure counter logic (lines 1053-1061).
7. **`scene_phase` is stored in `state["scene"]`** — the scene dict already holds `turn_entered` and other per-scene fields.

## Risks, Ambiguities, and Blockers

- **Prerequisite: Plan 1 must execute first.** Plan 1 adds `tension_delta` to `IntentEnvelope`, `TensionDelta` type alias, and `crisis_urgency_threshold`/`crisis_turn_limit`/`breather_max_turns` to `EngineConfig`. Plan 2 depends on all of these.
- **[QUESTION: relationship between `tension_delta` and `scene_motion`]** The design doc does not address how these two ruling-engine fields interact. `scene_motion` ("hold"|"advance"|"transition") measures scene-level motion intent. `tension_delta` ("escalates"|"maintains"|"de-escalates") measures action-level tension. They are orthogonal — `tension_delta` feeds phase transitions; `scene_motion` feeds `outcome_hint`. No conflict, but the interaction when both fire simultaneously (e.g., `scene_motion=advance` + `tension_delta=de-escalates`) is not discussed. Proposed: phase transition logic ignores `scene_motion` entirely. `scene_motion` continues to drive `outcome_hint` as before. This is consistent with the design doc's statement that "thread urgency can override `tension_delta`" — phase is driven by thread state + tension + age, not by `scene_motion`.
- **Thread signal quality degrades over time** — known risk. Phase transitions driven by `thread_urgency_count` will be noisy if urgency tags go stale. `effective_scene_age` backstop provides a floor.
- **Ruling engine misclassifies intent** — "I hide" during a firefight yields `tension_delta=de-escalates` even though tension is high. Mitigated: `tension_delta` is an accelerant, not a decider. Thread urgency can override.

## Status

`completed`

## Phases

Single phase — all changes to `turn.py` and `extraction.py` are tightly coupled (phase engine → directive rewrite → beat lifecycle → storytell context). Splitting would create a non-functional intermediate state.

## Implementation — Phase 2: Phase Engine and Directive Rewrite

### Context files to load

- `ccya/engine/turn.py` — Full file (1571 lines). Key sections: `_compute_narration_directive` (445), `_compute_pacing_context` (511), `_compute_ages` (587), `_narrate_setup` (762), `run_turn` (844), beat lifecycle (1024-1061), event logging (1340-1371), `PacingContext` dataclass (99)
- `ccya/engine/_pacing.py` — new file (created in Step 2.2): `BEAT_PHASE_MAP`, `derive_allowed_beat_types()`, `derive_enforce_relief()`
- `ccya/engine/extraction.py` — `_storytell_messages` (214), `_run_extraction_pipeline` (397)
- `ccya/models.py` — `ArcThread` urgency field (line 40), `TensionDelta` type alias (added by Plan 1), `IntentEnvelope` (line 167)
- `ccya/engine/config.py` — EngineConfig fields (new ones from Plan 1 + existing scene_*_threshold)
- `ccya/engine/ruling.py` — `tension_delta` on IntentEnvelope (added by Plan 1)

### Detailed steps

#### Step 2.1 — Add `_compute_scene_phase()` function

**File:** `ccya/engine/turn.py` — insert after `_compute_ages()` (after line 598), before `_recent_turn_count()` (line 602)

**What:** New function implementing the 5-state phase machine. Signature:

```python
def _compute_scene_phase(
    state: dict[str, Any],
    tension_delta: TensionDelta,
    ages: dict[str, int],
    config: EngineConfig,
) -> dict[str, Any]:
```

Inputs read from `state["scene"]` (current phase, crisis_turn_count, breather_turn_count) and `state["arc"]["threads"]` (thread urgency counts). Returns an updated `state["scene"]` dict with new `scene_phase`, `crisis_turn_count`, `breather_turn_count`.

Transition logic:

| Current | Condition | Next |
|---|---|---|
| SETUP | `thread_urgency > 0` (or `tension_delta=escalates` + `thread_urgency >= 1` as accelerant) | RISING |
| RISING | `thread_urgency >= crisis_urgency_threshold` OR (`thread_urgency >= 1` AND `tension_delta=escalates`) OR `effective_scene_age >= scene_pressure_threshold` | CRISIS |
| CRISIS | `crisis_turn_count >= crisis_turn_limit` [Python-enforced] | RESOLUTION |
| RESOLUTION | `location_change_this_turn` | SETUP |
| RESOLUTION | no `location_change_this_turn` | BREATHER |
| BREATHER | `thread_urgency > 0` OR `breather_turn_count >= breather_max_turns` | RISING |
| BREATHER | `location_change_this_turn` | SETUP |
| any | `location_change_this_turn` (except RESOLUTION which splits above) | SETUP |

Details:
- `location_change_this_turn` is a `bool` parameter — the caller passes it from the extraction result (available post-narrate, but phase computation happens pre-narrate). **The phase engine runs before narrate, so `location_change` is not yet known during phase computation.** This means the phase engine operates on the *prior turn's* state for `location_change` detection. The design doc acknowledges this: "location_change routes directly to SETUP" — this happens on the turn *after* the extraction detects it. The scene dict already stores `turn_entered` (repomap.md:331). Phase transition on location change is detected by checking `state["scene"].get("turn_entered") == current_turn` — if the scene was entered this turn, force phase to SETUP regardless of current phase. This is more reliable than `scene_age == 0` which conflates first-turn-of-session with location-change.
- `crisis_turn_count` increments each turn the phase is CRISIS. Resets to 0 on each fresh entry into CRISIS.
- `breather_turn_count` increments each turn the phase is BREATHER. Resets to 0 on each entry into BREATHER. Bounce-back (BREATHER → RISING → BREATHER) starts fresh.
- `effective_scene_age` is set in `_ruling_phase()` at line 727 (after `_compute_ages()` returns, adds combat boost to `scene_age`).

**Validation:** Unit-test the state machine in isolation. Call `_compute_scene_phase()` with known inputs and assert correct phase + counters. All 10 transition edges must be exercised.

#### Step 2.2 — Create shared pacing helpers module

**File:** `ccya/engine/_pacing.py` — new file

**What:** New module with the beat constraint map and two helper functions:

```python
BEAT_PHASE_MAP: dict[str, list[str]] = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room", "hazard"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CRISIS":      ["pressure", "escalation", "complication"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room", "hazard"],
}

def derive_allowed_beat_types(scene_phase: str, *, enforce_relief: bool = False) -> list[str]:
    if scene_phase == "CRISIS" and enforce_relief:
        return ["breathing_room"]
    return BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))


def derive_enforce_relief(scene_phase: str, consecutive_pressure_beats: int, config: "EngineConfig") -> bool:
    return scene_phase == "CRISIS" and consecutive_pressure_beats >= config.consecutive_pressure_threshold
```

**Why:** These encapsulate the beat constraint table in Python. Placed in a shared module so both `turn.py` (phase engine, directive computation) and `extraction.py` (storytell context) can import them without circular imports. `allowed_beat_types` is passed to storytell as prompt context. `enforce_relief` overrides CRISIS beat constraints to force only `breathing_room` beats.

**Validation:** Assert `derive_allowed_beat_types("CRISIS", enforce_relief=True) == ["breathing_room"]`. Assert `derive_allowed_beat_types("RISING")` excludes `breathing_room` and `opportunity`.

#### Step 2.3 — Update `_narrate_setup()` to compute phase before pacing context

**File:** `ccya/engine/turn.py` — lines 762-841

**What:** In `_narrate_setup()`, after computing `ctx._ages` (~line 816) and before calling `_compute_pacing_context()` (~line 819):

1. Derive `tension_delta` from `ctx.intent.tension_delta` (default `"maintains"` if intent is None)
2. Read current `scene_phase` from `state.get("scene", {})` — default to `"SETUP"` if missing
3. Call `_compute_scene_phase(state, tension_delta, ctx._ages, config)` — this mutates `state["scene"]` in place
4. Compute `allowed_beat_types` from the new phase
5. Compute `enforce_relief` from the new phase and the meta counter

**Why:** Phase must be computed before directive computation, which happens inside `_compute_pacing_context()`. Both phase and directive depend on the same inputs (thread urgency, age, tension) so ordering is deterministic.

**Validation:** Trace through with a SETUP state and 0 urgent threads — phase stays SETUP. Trace with 1 urgent thread — phase transitions to RISING.

#### Step 2.4 — Rewrite `_compute_narration_directive()`

**File:** `ccya/engine/turn.py` — lines 445-508

**What:** Replace the entire function. New signature and logic:

```python
def _compute_narration_directive(
    scene_phase: str,
    tension_delta: TensionDelta,
    thread_urgency_count: int,
    crisis_turn_count: int,
    crisis_turn_limit: int,
    effective_scene_age: int,
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 4,
) -> str:
```

Priority stack (new):

```
1. Breathe     — tension_delta == "de-escalates" AND thread_urgency_count == 0
2. Scene Imperative — (scene_phase == CRISIS AND crisis_turn_count >= crisis_turn_limit)
                       OR effective_scene_age >= scene_imperative_threshold
3. Scene Pressure   — effective_scene_age >= scene_pressure_threshold
4. (empty)     — default
```

Removed: `Overwhelm`, `Pressure`, `Tension` directives. Their jobs are handled by phase. Removed: `"; Resolve a Threat"` append — that was tied to `beat_locked` which is being replaced by `enforce_relief`.

**Why:** Four-level priority stack is simpler than the old six-level, driven by clean signals (phase + tension_delta + age) instead of broken counters. `Overwhelm`/`Pressure`/`Tension` are redundant when phase already signals RISING/CRISIS.

**Validation:** Assert directive is empty (no tension, no age, no urgent threads). Assert "Breathe" when `tension_delta="de-escalates"` and `thread_urgency_count=0`. Assert "Scene Imperative" when `scene_phase="CRISIS"` and `crisis_turn_count >= crisis_turn_limit`.

#### Step 2.5 — Rewrite `_compute_pacing_context()`

**File:** `ccya/engine/turn.py` — lines 511-584

**What:** Replace the function body. New signature:

```python
def _compute_pacing_context(
    scene_phase: str,
    tension_delta: TensionDelta,
    thread_urgency_count: int,
    crisis_turn_count: int,
    crisis_turn_limit: int,
    effective_scene_age: int,
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 4,
) -> PacingContext:
```

New logic:
1. Call `_compute_narration_directive()` with the new signal set (no momentum, no velocity, no consecutive_pressure_turns).
2. `beat_locked` is replaced by `enforce_relief` for floor-relief purposes, but `beat_locked` field stays on `PacingContext` until Plan 4. Set to `False` for now (the old trigger conditions no longer exist).
3. `gate` field stays on `PacingContext` until Plan 4. Set to `"allow"` for now (the old deescalate-gate logic is removed).
4. `outcome_hint` logic remains unchanged — still driven by `scene_motion` from intent + existing fallbacks. Add: when `scene_phase == "CRISIS" AND crisis_turn_count >= crisis_turn_limit`, override `outcome_hint = "transition"`.
5. `narrative_velocity` parameter removed from signature. `PacingContext` field remains until Plan 4.

**Why:** `PacingContext` is the integration point between the phase engine and the narrator/storyteller. It must emit the new signals while keeping old fields alive (Plan 4 removes them). The old parameters (deescalate, narrative_velocity, momentum, consecutive_pressure_turns) are no longer needed.

**Validation:** Assert `PacingContext.directive` matches new directive output. Assert `outcome_hint="transition"` when phase CRISIS hits turn limit.

#### Step 2.6 — Update `_narrate_setup()` wiring

**File:** `ccya/engine/turn.py` — lines 816-826

**What:** Update the call to `_compute_pacing_context()` in `_narrate_setup()` to pass the new parameters:

```python
_pc = _compute_pacing_context(
    scene_phase=scene_phase,
    tension_delta=tension_delta,
    thread_urgency_count=thread_urgency_count,
    crisis_turn_count=crisis_turn_count,
    crisis_turn_limit=config.crisis_turn_limit,
    effective_scene_age=ctx._ages.get("effective_scene_age", 0),
    scene_pressure_threshold=config.scene_pressure_threshold,
    scene_imperative_threshold=config.scene_imperative_threshold,
)
```

Remove the old parameter wiring (deescalate, narrative_velocity, active_threads, ages, momentum, consecutive_pressure_turns, scene_motion, impossible) — `_compute_pacing_context` no longer accepts them.

**Why:** Clean separation. Phase engine computes scene_phase and thread counts; directive computation consumes them.

**Validation:** `make check` passes (lint + typecheck).

#### Step 2.7 — Update beat lifecycle: consecutive_pressure_beats counter

**File:** `ccya/engine/turn.py` — lines 1053-1061

**What:** Replace the `consecutive_pressure_turns` counter with `consecutive_pressure_beats` counter. Same logic structure but stored under a different key name in `state["meta"]`:

```python
# Consecutive pressure beats counter: tracks beat type streaks, not directive types
_current_beat = state.get("meta", {}).get("pending_gm_beat")
_beat_type = _current_beat.get("type") if _current_beat else None
meta = state.setdefault("meta", {})
current_pressure = meta.get("consecutive_pressure_beats", 0)
if _beat_type in PRESSURE_BEAT_TYPES:
    meta["consecutive_pressure_beats"] = current_pressure + 1
else:
    meta["consecutive_pressure_beats"] = 0
```

The old `consecutive_pressure_turns` key remains in state (Plan 4 deletes it). The new `consecutive_pressure_beats` key is the authoritative counter for `enforce_relief`. `PRESSURE_BEAT_TYPES` is an existing constant — verify its current definition at the top of turn.py.

**Why:** The new counter tracks beat-type streaks (from storytell output) rather than directive-type streaks (from pacing context). Semantics differ — the old counter never incremented because Pressure/Overwhelm directives never fired (0/51 turns). The new counter reads actual beat types emitted by the LLM.

**Validation:** Inject a `pending_gm_beat` with `type="pressure"` — assert `consecutive_pressure_beats` increments. Inject with `type="breathing_room"` — assert counter resets to 0.

#### Step 2.8 — Add scene_phase to end-of-turn event logging

**File:** `ccya/engine/turn.py` — lines 1361-1367 (pacing_context event dict)

**What:** Add `scene_phase`, `crisis_turn_count`, `breather_turn_count` to the `pacing_context` entry in the event dict. Also add a top-level `scene_phase` key alongside `narrative_velocity` for easy grepping in events:

```python
"pacing_context": {
    ...
    "scene_phase": state.get("scene", {}).get("scene_phase", "SETUP"),
    "crisis_turn_count": state.get("scene", {}).get("crisis_turn_count", 0),
    "breather_turn_count": state.get("scene", {}).get("breather_turn_count", 0),
},
"narrative_velocity": round(narrative_velocity, 2),
"scene_phase": state.get("scene", {}).get("scene_phase", "SETUP"),
```

**Why:** Events are the primary debugging surface. `scene_phase` must be queryable from events.jsonl for checker and ev.py inspection.

**Validation:** Run a turn, inspect events.jsonl `pacing_context` section — `scene_phase` is present and correct.

#### Step 2.9 — Ensure state["scene"] initialization

**File:** `ccya/engine/turn.py` — in `run_turn()` or `_compute_ages()` or `_narrate_setup()`

**What:** On first turn (or when `state["scene"]` lacks `scene_phase`), initialize the scene dict:

```python
scene = state.setdefault("scene", {})
scene.setdefault("scene_phase", "SETUP")
scene.setdefault("crisis_turn_count", 0)
scene.setdefault("breather_turn_count", 0)
```

Best location: `_narrate_setup()` at the point where scene state is first read (~line 804, before `_compute_pacing_context`), or `_compute_ages()` since it already reads `state["scene"]`.

**Why:** New sessions have no `scene_phase` in state. Without initialization, all field accesses return `KeyError` or mistype as `None`.

**Validation:** Create a fresh `state = {"meta": {"turn": 0}}` and call the function — `scene` dict has all three fields with correct defaults.

#### Step 2.10 — Pass `scene_phase` and `allowed_beat_types` to storytell context

**File:** `ccya/engine/extraction.py` — `_storytell_messages()` (line 214)

**What:** Add two new keys to the storytell user context dict (~line 252):

```python
"scene_phase": scene.get("scene_phase", "SETUP"),
"allowed_beat_types": derive_allowed_beat_types(
    scene.get("scene_phase", "SETUP"),
    enforce_relief=derive_enforce_relief(
        scene.get("scene_phase", "SETUP"),
        state.get("meta", {}).get("consecutive_pressure_beats", 0),
        config,  # need config access for consecutive_pressure_threshold
    ),
),
```

Import from `ccya.engine._pacing` (created in Step 2.2): `from ccya.engine._pacing import derive_allowed_beat_types, derive_enforce_relief`.

`_storytell_messages()` does not currently receive `config`. Add it as a parameter (line 226) and pass it from `_run_extraction_pipeline()` line 524.

**Why:** The storyteller LLM needs `scene_phase` and `allowed_beat_types` to constrain its beat selection. Without these context variables, the prompt constraint table (Plan 3) is unreachable.

**Validation:** Render storytell messages, inspect user context — `scene_phase` and `allowed_beat_types` are present with correct values.

#### Step 2.11 — Remove old parameter passing

**File:** `ccya/engine/turn.py` — `_narrate_setup()` (lines 794-826)

**What:** Remove the call to `_compute_narrative_velocity()` (lines 795-802) and the old parameter wiring to `_compute_pacing_context()` (lines 820-826). The `narrative_velocity` variable is still needed for the `TurnResult` and event logging (Plan 4 removes it) — set it to `0.0` as a placeholder.

**Why:** Old signal computation (`momentum`, `avoidance`, `deescalate`) is no longer used by the directive system. Setting `narrative_velocity = 0.0` maintains the `TurnResult` field shape until Plan 4 deletes it entirely.

**Validation:** `make check` passes. Function signatures match at all call sites.

#### Step 2.12 — Update documentation

**Files:** `docs/repomap.md`, `docs/architecture/OVERVIEW.md`

**What:**
1. **repomap.md** — Update `ccya/engine/turn.py` entry to list new functions: `_compute_scene_phase()`, `_derive_allowed_beat_types()` (moved to `_pacing.py`), `_derive_enforce_relief()` (moved to `_pacing.py`). Update `_compute_narration_directive()` signature in the "Computation functions" section. Update `_compute_pacing_context()` signature. Add `ccya/engine/_pacing.py` to the module index.
2. **OVERVIEW.md** — Update the 5-call turn pipeline description to note phase engine runs between ruling and narrate. Update the PacingContext description to include `scene_phase` as the primary pacing signal.

**Why:** AGENTS.md mandates doc updates for any code change touching a module, config key, model field, prompt, or public API. This plan changes function signatures, adds new modules, and modifies the turn pipeline structure.

**Validation:** `grep '_compute_scene_phase\|_pacing\|derive_allowed_beat_types\|derive_enforce_relief' docs/repomap.md` returns hits. `grep 'scene_phase' docs/architecture/OVERVIEW.md` returns hits.

### Tests to write or update

No automated tests (tests are temporarily removed during refactor). Manual verification:

1. **State machine isolation test:** Run `_compute_scene_phase()` with 10 input combinations covering all transition edges. Log expected vs actual phase.
2. **Directive regression test:** Feed 6 input combinations to `_compute_narration_directive()` — assert correct directive string for each.
3. **Turn pipeline integration test:** Play 3 turns via ev.py, inspect events.jsonl for `scene_phase` progression.
