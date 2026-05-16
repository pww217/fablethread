# narrative_velocity: Priority-Keyed Pacing Directive Consolidation

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Compute narrative_velocity | Replace `deescalate` float + `momentum` heuristic with a signed scalar; add priority-stack logic to `_compute_narration_directive` |
| 02 | Propagate through call sites | Remove `deescalate` from `_narrate_messages` and `_extract_progress_messages` signatures; thread `narrative_velocity` instead |
| 03 | Fold location_age into pressure | Retire standalone `Location Pressure` / `Location Imperative` directives; express staleness as a synthetic scene pressure entry |
| 04 | Prompt template cleanup | Update `narrate_user.j2` and `extract_progress_user.j2` to consume `narrative_velocity` and the unified pressure list |
| 05 | Tests | Unit tests for `_compute_narration_directive` covering priority, contradiction suppression, and velocity sign; integration test fixture update |

---

## Objective

`_compute_narration_directive` currently builds a semicolon-joined string of up to four independent labels (`Breathe`, `Pressure`, `Location Imperative`, `Resolve a Threat`, etc.) with no priority resolution. Contradictory directives like `"Breathe; Location Imperative"` can be emitted simultaneously, leaving the LLM to arbitrate — which it does inconsistently. Additionally, `deescalate` (a float) and `momentum` (an int read from state) answer the same question from different angles: *how fast should things move right now?* This plan collapses both into a single signed `narrative_velocity` scalar, imposes a strict priority stack on the directive builder so the highest-priority signal always wins, and folds `location_age` thresholds into the scene pressure list rather than maintaining a parallel code path.

## Non-goals

- This plan does not touch `scene_pressure` lifecycle (add/remove/escalate logic in `pressure.py`) — that is a separate consolidation.
- This plan does not merge `pending_gm_beat` with scene pressure — that is a higher-risk structural change deferred to a later plan.
- This plan does not change the `momentum` integer stored in `state["pc"]["momentum"]` — velocity is a derived narration signal only, not a state field.
- This plan does not alter `apply_momentum` in `state.py`.
- This plan does not modify extraction stream 1 (scene) or stream 2 (state).

---

## Implementation — Phase 01: Compute narrative_velocity

### Files to pull for context
- `ccya/engine/turn.py` — `_compute_narration_directive`, `_compute_ages`, `run_turn` (the deescalate computation block)
- `ccya/engine/config.py` — `EngineConfig` fields: `avoidance_keywords`, `scene_pressure_deescalate_on_success`, `momentum_floor`, `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at`

### Detailed steps

#### Step 1.1 — Add `_compute_narrative_velocity` to `turn.py`

**File:** `ccya/engine/turn.py`

**What:** New pure function that converts `deescalate`, current `momentum`, and `avoidance` into a single float in `[-1.0, 1.0]`. Negative = de-escalate / breathe. Positive = escalate. Zero = neutral.

**Why:** Single source of truth for pacing direction. Downstream code (narrate and extract) only needs one number, not two separate signals with overlapping semantics.

**Code Snippet**
```python
def _compute_narrative_velocity(
    deescalate: float,
    momentum: int,
    avoidance: bool,
    momentum_floor: int = -3,
    momentum_ceiling: int = 3,
) -> float:
    """Compute a signed pacing scalar in [-1.0, 1.0].

    Negative values signal de-escalation (breathe, slow down).
    Positive values signal escalation (pressure, urgency).
    Zero is neutral.

    Priority:
      1. Explicit de-escalation from a successful check beats everything.
      2. Avoidance keyword in player input nudges negative.
      3. Momentum floor (consecutive failures) nudges negative (player needs relief).
      4. Momentum ceiling (consecutive successes) nudges positive (earned escalation).
      5. Default: 0.0 (neutral, let pressure/beat directives govern).
    """
    if deescalate > 0:
        return -deescalate  # already in (0, 1.0] from turn.py; negate for direction

    if avoidance:
        return -0.4

    span = momentum_ceiling - momentum_floor
    if span <= 0:
        return 0.0
    # Normalize momentum to [-1, 1] relative to its range midpoint
    midpoint = (momentum_ceiling + momentum_floor) / 2.0
    normalized = (momentum - midpoint) / (span / 2.0)
    # Scale down — momentum alone shouldn't dominate; caps at ±0.5
    return max(-0.5, min(0.5, normalized * 0.5))
```

**Validation:** `python -c "from ccya.engine.turn import _compute_narrative_velocity; assert _compute_narrative_velocity(0.6, 0, False) == -0.6; assert _compute_narrative_velocity(0.0, 0, True) == -0.4; print('ok')`

---

#### Step 1.2 — Rewrite `_compute_narration_directive` with a priority stack

**File:** `ccya/engine/turn.py`

**What:** Replace the current additive semicolon-join approach with an ordered priority stack. The function returns the *single highest-priority directive label*, optionally followed by secondary labels only when they do not contradict the primary. Contradiction rule: if `velocity < 0` (breathe/de-escalate), suppress all movement/escalation directives regardless of pressure counts.

**Why:** Fixes the `"Breathe; Location Imperative"` contradiction class. LLM receives one clear instruction, not a list of conflicting ones.

**Code Snippet**
```python
def _compute_narration_directive(
    narrative_velocity: float,
    scene_pressure: list[dict[str, Any]],
    ages: dict[str, int],
    threat_ages: list[dict[str, Any]],
    threat_pressure_at: int = 3,
    threat_imperative_at: int = 5,
    building_threat_imperative_at: int = 4,
) -> str:
    """Compute the narration directive string using a priority stack.

    Returns the highest-priority directive. Secondary directives are appended
    only when they do not contradict the primary (i.e., no escalation labels
    when velocity is negative).

    Priority order (highest to lowest):
      1. Breathe       — explicit de-escalation (velocity < -0.3)
      2. Overwhelm     — 3+ immediate pressures
      3. Resolve a Threat — aged-out threat pressure
      4. Pressure      — 1–2 immediate pressures
      5. Tension       — building pressures only
      6. Combat Fatigue — combat_age >= 3 (appended, non-contradicting only)
    """
    primary: str = ""
    secondary: list[str] = []
    escalating = narrative_velocity >= 0

    # Priority 1: breathe (de-escalation wins unconditionally)
    if narrative_velocity < -0.3:
        primary = "Breathe"
        # Do not append escalation secondaries — return immediately
        return primary

    # Priority 2: overwhelm (3+ immediate pressures)
    immediate_count = sum(1 for p in scene_pressure if p.get("urgency") == "immediate")
    if immediate_count >= 3:
        primary = "Overwhelm"

    # Priority 3: aged-out threat (resolve a threat)
    if not primary and threat_ages:
        old_building = [
            t for t in threat_ages
            if t.get("urgency") == "building" and t.get("age", 0) >= building_threat_imperative_at
        ]
        old_background = [
            t for t in threat_ages
            if t.get("urgency") == "background" and t.get("age", 0) >= threat_imperative_at
        ]
        old_immediate = [
            t for t in threat_ages
            if t.get("urgency") == "immediate" and t.get("age", 0) >= 3
        ]
        if old_building or old_background or old_immediate:
            primary = "Resolve a Threat"

    # Priority 4: pressure (1–2 immediate)
    if not primary and immediate_count > 0:
        primary = "Pressure"

    # Priority 5: tension (building only)
    if not primary:
        building_count = sum(1 for p in scene_pressure if p.get("urgency") == "building")
        if building_count > 0:
            primary = "Tension"

    # Priority 6: threat pressure (background aging toward imperative)
    if not primary and threat_ages:
        background_pressure = [
            t for t in threat_ages
            if t.get("urgency") == "background"
            and threat_pressure_at <= t.get("age", 0) < threat_imperative_at
        ]
        if background_pressure:
            primary = "Threat Pressure"

    # Secondary: combat fatigue (non-contradicting append)
    if ages.get("combat_age", 0) >= 3:
        secondary.append("Combat Fatigue")

    parts = [primary] if primary else []
    parts.extend(secondary)
    return "; ".join(parts)
```

**Validation:** Verify the following assertions pass:
```python
from ccya.engine.turn import _compute_narration_directive

# Breathe suppresses everything
assert _compute_narration_directive(-0.6, [{"urgency": "immediate"}, {"urgency": "immediate"}, {"urgency": "immediate"}], {}, []) == "Breathe"

# Overwhelm wins over Resolve a Threat
threat = [{"urgency": "building", "age": 5}]
assert _compute_narration_directive(0.0, [{"urgency": "immediate"}]*3, {}, threat) == "Overwhelm"

# Pressure + combat fatigue
assert _compute_narration_directive(0.0, [{"urgency": "immediate"}], {"combat_age": 3}, []) == "Pressure; Combat Fatigue"

# Empty — no directive
assert _compute_narration_directive(0.0, [], {}, []) == ""
```

---

#### Step 1.3 — Wire `_compute_narrative_velocity` into `run_turn`

**File:** `ccya/engine/turn.py`

**What:** Replace the inline `deescalate` computation block and the two separate `_compute_narration_directive` calls (in `run_turn` and `run_turn_retry`) with calls to `_compute_narrative_velocity` followed by `_compute_narration_directive` with the new signature.

**Why:** Single call site, consistent derivation. `run_turn_retry` currently hardcodes `deescalate=0.0` — this stays correct since velocity defaults to neutral on retry.

**Code Snippet** (replace in `run_turn`, after `apply_momentum` and before `narration_directive =`):
```python
# Compute unified pacing scalar
narrative_velocity = _compute_narrative_velocity(
    deescalate=deescalate,
    momentum=(state.get("pc") or {}).get("momentum", 0),
    avoidance=avoidance,
    momentum_floor=config.momentum_floor,
    momentum_ceiling=config.momentum_ceiling,  # add this field to EngineConfig if absent
)

narration_directive = _compute_narration_directive(
    narrative_velocity=narrative_velocity,
    scene_pressure=(state.get("scene") or {}).get("scene_pressure") or [],
    ages=ages,
    threat_ages=threat_ages,
    threat_pressure_at=config.threat_pressure_at,
    threat_imperative_at=config.threat_imperative_at,
    building_threat_imperative_at=config.building_threat_imperative_at,
)
```

In `run_turn_retry`, replace the existing `narration_directive =` block with:
```python
narrative_velocity = _compute_narrative_velocity(
    deescalate=0.0,
    momentum=(state.get("pc") or {}).get("momentum", 0),
    avoidance=False,
    momentum_floor=config.momentum_floor,
    momentum_ceiling=getattr(config, "momentum_ceiling", 3),
)
narration_directive = _compute_narration_directive(
    narrative_velocity=narrative_velocity,
    scene_pressure=(state.get("scene") or {}).get("scene_pressure") or [],
    ages=ages,
    threat_ages=threat_ages,
    threat_pressure_at=config.threat_pressure_at,
    threat_imperative_at=config.threat_imperative_at,
    building_threat_imperative_at=config.building_threat_imperative_at,
)
```

**Validation:** `make check` passes. Run `make test` — all existing pacing tests pass.

---

### Tests to write or update

**File:** `tests/test_pacing.py` (create if not present)

```python
# test_compute_narrative_velocity
def test_velocity_deescalate_dominates():
    v = _compute_narrative_velocity(deescalate=0.6, momentum=3, avoidance=False)
    assert v == -0.6

def test_velocity_avoidance():
    v = _compute_narrative_velocity(deescalate=0.0, momentum=0, avoidance=True)
    assert v == -0.4

def test_velocity_neutral():
    v = _compute_narrative_velocity(deescalate=0.0, momentum=0, avoidance=False)
    assert v == 0.0

def test_velocity_high_momentum_positive():
    v = _compute_narrative_velocity(deescalate=0.0, momentum=3, avoidance=False)
    assert v > 0

# test_compute_narration_directive
def test_breathe_suppresses_overwhelm():
    result = _compute_narration_directive(
        narrative_velocity=-0.6,
        scene_pressure=[{"urgency": "immediate"}] * 3,
        ages={}, threat_ages=[],
    )
    assert result == "Breathe"

def test_overwhelm_wins_over_pressure():
    result = _compute_narration_directive(
        narrative_velocity=0.0,
        scene_pressure=[{"urgency": "immediate"}] * 3,
        ages={}, threat_ages=[],
    )
    assert result == "Overwhelm"

def test_no_contradicting_secondaries_when_breathe():
    result = _compute_narration_directive(
        narrative_velocity=-0.5,
        scene_pressure=[],
        ages={"combat_age": 5},
        threat_ages=[{"urgency": "building", "age": 6}],
    )
    assert "Location" not in result
    assert "Resolve" not in result

def test_combat_fatigue_appended():
    result = _compute_narration_directive(
        narrative_velocity=0.0,
        scene_pressure=[{"urgency": "immediate"}],
        ages={"combat_age": 4},
        threat_ages=[],
    )
    assert result == "Pressure; Combat Fatigue"

def test_empty_returns_empty_string():
    result = _compute_narration_directive(
        narrative_velocity=0.0,
        scene_pressure=[],
        ages={},
        threat_ages=[],
    )
    assert result == ""
```

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — update `_compute_narration_directive` signature entry; add `_compute_narrative_velocity`.

### Risks
1. `momentum_ceiling` may not exist on `EngineConfig` — check `config.py` before referencing; add with default `3` if absent.
2. The `deescalate` variable is still computed in `run_turn` for backward logging purposes — do not remove it before Phase 02 confirms all downstream consumers have been migrated.

---

## Implementation — Phase 02: Propagate through call sites

### Files to pull for context
- `ccya/engine/turn.py` — both `run_turn` and `run_turn_retry`, specifically the `_narrate_messages(...)` and `_run_extraction_pipeline(...)` call sites
- `ccya/engine/narrate.py` — `_narrate_messages` signature
- `ccya/engine/extraction.py` — `_extract_progress_messages` signature and `_run_extraction_pipeline` signature

### Detailed steps

#### Step 2.1 — Remove `deescalate` from `_narrate_messages`

**File:** `ccya/engine/narrate.py`

**What:** Replace the `deescalate: float = 0.0` parameter with `narrative_velocity: float = 0.0`. Update `user_ctx` dict key from `"deescalate"` to `"narrative_velocity"`.

**Why:** The template receives `deescalate` today; Phase 04 will update the template to use `narrative_velocity`. Keeping both during the transition causes confusion — rename here and update template in Phase 04 atomically.

**Code Snippet**
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    narrator_rules: list[str] = [],
    world_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    narrative_velocity: float = 0.0,   # replaces deescalate
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    compendium_bios: list[dict[str, Any]] = [],
    pc_allegiance: str | None = None,
    scene_pressure: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    threat_ages: list[dict[str, Any]] | None = None,
    threat_pressure_at: int = 3,
    threat_imperative_at: int = 5,
    building_threat_imperative_at: int = 4,
    npc_roster: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        # ... all existing keys unchanged except:
        "narrative_velocity": narrative_velocity,   # was "deescalate": deescalate
        # ... rest of keys
    }
```

**Validation:** `grep -rn "deescalate" ccya/engine/narrate.py` returns no matches after this change.

---

#### Step 2.2 — Remove `deescalate` from `_extract_progress_messages` and `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_progress_messages`, replace `deescalate: float = 0.0` with `narrative_velocity: float = 0.0` and update the Jinja context dict key. In `_run_extraction_pipeline`, replace `deescalate: float = 0.0` with `narrative_velocity: float = 0.0` and thread it through to the `_extract_progress_messages` call.

**Code Snippet** (`_extract_progress_messages` signature change):
```python
def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    state_result: "StateExtractResult",
    extraction_ctx: "_ExtractionContext",
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    narrative_velocity: float = 0.0,   # replaces deescalate
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    stakes: str = "",
    band: str = "",
    narration_directive: str = "",
) -> list[dict[str, str]]:
    ...
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            ...
            "narrative_velocity": narrative_velocity,   # was "deescalate"
            ...
        },
    )
```

**Code Snippet** (`_run_extraction_pipeline` signature change):
```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    narrative_velocity: float = 0.0,   # replaces deescalate
    recent_turns: list[dict[str, Any]] | None = None,
    narration_directive: str = "",
) -> ...:
    ...
    progress_msgs = _extract_progress_messages(
        ...
        narrative_velocity=narrative_velocity,   # was deescalate=deescalate
        ...
    )
```

**Validation:** `grep -rn "deescalate" ccya/engine/extraction.py` returns no matches.

---

#### Step 2.3 — Update `run_turn` and `run_turn_retry` call sites

**File:** `ccya/engine/turn.py`

**What:** In both `run_turn` and `run_turn_retry`, update the `_narrate_messages(...)` and `_run_extraction_pipeline(...)` calls to pass `narrative_velocity=narrative_velocity` instead of `deescalate=deescalate`. Remove the standalone `deescalate` variable after confirming no remaining references.

**Validation:** `grep -rn "deescalate" ccya/engine/turn.py` returns no matches. `make check` passes.

---

### Tests to write or update
- Ensure `tests/test_pacing.py` (from Phase 01) passes unchanged — no new tests needed here.
- Run `make test` — confirm no import errors on the renamed parameter.

### Risks
1. The `deescalate` key may be referenced in `narrate_user.j2` or `extract_progress_user.j2` — Phase 04 handles template updates. If Phase 02 lands before Phase 04, the templates will receive `narrative_velocity` but reference `deescalate`, causing a Jinja `UndefinedError`. **Do not commit Phase 02 without Phase 04, or add a backward-compat alias in the template context temporarily.**

---

## Implementation — Phase 03: Fold location_age into pressure

### Files to pull for context
- `ccya/engine/turn.py` — `_compute_ages`, `_compute_narration_directive` (post-Phase-01 version), `_compute_threat_ages`
- `ccya/engine/config.py` — `EngineConfig`: confirm `location_pressure_at` and `location_imperative_at` threshold fields exist or add them

### Detailed steps

#### Step 3.1 — Add location staleness as a synthetic pressure entry

**File:** `ccya/engine/turn.py`

**What:** New function `_inject_location_pressure` that, given `ages` and config thresholds, returns a synthetic scene pressure dict to append to the pressure list before `_compute_narration_directive` is called. This means `Location Pressure` and `Location Imperative` are no longer separate directive labels — they become urgency-tagged pressures processed by the same path as all other pressures.

**Why:** Eliminates the parallel `location_age` branch in the directive builder. Location staleness is conceptually identical to scene pressure — it is a reason to move things along. One path, consistent behavior.

**Code Snippet**
```python
_LOCATION_PRESSURE_ID = "_engine_location_stale"

def _inject_location_pressure(
    ages: dict[str, int],
    existing_pressure: list[dict[str, Any]],
    location_pressure_at: int = 3,
    location_imperative_at: int = 5,
) -> list[dict[str, Any]]:
    """Return a new pressure list with a synthetic location staleness entry appended if warranted.

    Does not mutate the input list. Returns a new list.
    The synthetic entry uses id='_engine_location_stale' and is never persisted to state.
    """
    location_age = ages.get("location_age", 0)
    if location_age <= location_pressure_at:
        # Not stale yet — strip any existing synthetic entry and return
        return [p for p in existing_pressure if p.get("id") != _LOCATION_PRESSURE_ID]

    urgency = "immediate" if location_age > location_imperative_at else "building"
    synthetic = {
        "id": _LOCATION_PRESSURE_ID,
        "text": "The scene has lingered here too long — move it along.",
        "urgency": urgency,
        "turn_added": 0,  # 0 signals engine-generated; _compute_threat_ages skips turn_added==0
    }
    filtered = [p for p in existing_pressure if p.get("id") != _LOCATION_PRESSURE_ID]
    return filtered + [synthetic]
```

#### Step 3.2 — Wire `_inject_location_pressure` into `run_turn` and `run_turn_retry`

**File:** `ccya/engine/turn.py`

**What:** Before the `narration_directive = _compute_narration_directive(...)` call in both `run_turn` and `run_turn_retry`, call `_inject_location_pressure` to produce an augmented pressure list. Pass this augmented list to `_compute_narration_directive` and `_narrate_messages` instead of the raw `scene_pressure`.

**Code Snippet** (insert before `narration_directive =` in both functions):
```python
_raw_scene_pressure = (state.get("scene") or {}).get("scene_pressure") or []
_effective_pressure = _inject_location_pressure(
    ages=ages,
    existing_pressure=_raw_scene_pressure,
    location_pressure_at=getattr(config, "location_pressure_at", 3),
    location_imperative_at=getattr(config, "location_imperative_at", 5),
)

narration_directive = _compute_narration_directive(
    narrative_velocity=narrative_velocity,
    scene_pressure=_effective_pressure,   # augmented list
    ages=ages,
    threat_ages=threat_ages,
    ...
)
```

Then pass `scene_pressure=_effective_pressure` to `_narrate_messages(...)` as well.

#### Step 3.3 — Remove `location_age` branch from `_compute_narration_directive`

**File:** `ccya/engine/turn.py`

**What:** Delete the `if ages.get("location_age", 0) > 4` / `elif ages.get("location_age", 0) > 2` block from the (post-Phase-01) `_compute_narration_directive`. The function no longer needs to inspect `ages` at all for location — only `combat_age` remains as a secondary-append consumer.

**Why:** Location staleness now arrives as a pressure entry. The directive builder doesn't need two code paths for the same concept.

**Validation:** `grep -n "location_age" ccya/engine/turn.py` shows zero hits in `_compute_narration_directive`. `make check` passes.

---

### Tests to write or update

**File:** `tests/test_pacing.py`

```python
def test_inject_location_pressure_not_stale():
    result = _inject_location_pressure({"location_age": 2}, [])
    assert not any(p["id"] == "_engine_location_stale" for p in result)

def test_inject_location_pressure_building():
    result = _inject_location_pressure({"location_age": 4}, [], location_pressure_at=3, location_imperative_at=5)
    entry = next(p for p in result if p["id"] == "_engine_location_stale")
    assert entry["urgency"] == "building"

def test_inject_location_pressure_immediate():
    result = _inject_location_pressure({"location_age": 6}, [], location_pressure_at=3, location_imperative_at=5)
    entry = next(p for p in result if p["id"] == "_engine_location_stale")
    assert entry["urgency"] == "immediate"

def test_inject_location_pressure_replaces_existing():
    existing = [{"id": "_engine_location_stale", "urgency": "building", "text": "old", "turn_added": 0}]
    result = _inject_location_pressure({"location_age": 6}, existing, location_pressure_at=3, location_imperative_at=5)
    stale_entries = [p for p in result if p["id"] == "_engine_location_stale"]
    assert len(stale_entries) == 1
    assert stale_entries[0]["urgency"] == "immediate"
```

### Risks
1. `_compute_threat_ages` skips entries with `turn_added == 0` — verify this guard is present so the synthetic entry does not age into a `Resolve a Threat` directive.
2. If `EngineConfig` does not have `location_pressure_at` / `location_imperative_at` as fields, use `getattr(config, ..., default)` defensively and file a follow-up to add them formally.

---

## Implementation — Phase 04: Prompt template cleanup

### Files to pull for context
- `ccya/prompts/narrate_user.j2` — current usage of `deescalate`, `ages.location_age`, pacing directive block
- `ccya/prompts/extract_progress_user.j2` — current usage of `deescalate`, `narration_directive`

### Detailed steps

#### Step 4.1 — Update `narrate_user.j2`

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace all references to `deescalate` with `narrative_velocity`. Replace the `location_age` inline checks (if any) with logic that reads from `scene_pressure` (which now contains the synthetic location entry). The pacing directive block should key off `narration_directive` (already passed) and `narrative_velocity < 0` for breathe tone.

**Why:** Template must match the context dict from Phase 02. Any `{{ deescalate }}` reference will raise a Jinja `UndefinedError` at runtime after Phase 02 lands.

**Validation:** Render the template in isolation with a mock context containing `narrative_velocity=0.0` and no `deescalate` key. Confirm no `UndefinedError`.

#### Step 4.2 — Update `extract_progress_user.j2`

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Replace `deescalate` references with `narrative_velocity`. The template may use `deescalate > 0` as a condition to suppress pressure-add suggestions — replace with `narrative_velocity < -0.3`.

**Validation:** Same as 4.1 — render with mock context.

---

### Tests to write or update
- Add a smoke-render test in `tests/test_templates.py` (or equivalent) that builds the Jinja env, renders both templates with a minimal context dict containing `narrative_velocity` (no `deescalate`), and asserts no exception is raised and the output is non-empty.

### Risks
1. Templates may reference `deescalate` in multiple places — do a thorough `grep -n "deescalate"` before assuming a single replacement.
2. Template rendering is not covered by `make check` (it's runtime) — the smoke-render test in this phase is the only automated catch.

---

## Implementation — Phase 05: Tests

### Files to pull for context
- `tests/` — list all existing test files to identify the right location
- `tests/conftest.py` — check for shared fixtures (FakeLLM patterns, save_dir fixtures)
- `docs/REPOMAP/testing.md` — FakeLLM patterns for integration test fixtures

### Detailed steps

#### Step 5.1 — Consolidate pacing tests

**File:** `tests/test_pacing.py`

**What:** Collect all unit tests written in Phases 01–03 into a single file. Add a parametrized test covering the full `(velocity, pressure_list, ages, expected_primary_directive)` matrix for `_compute_narration_directive`.

**Code Snippet**
```python
import pytest
from ccya.engine.turn import (
    _compute_narrative_velocity,
    _compute_narration_directive,
    _inject_location_pressure,
)

@pytest.mark.parametrize("velocity,pressure,ages,threat_ages,expected", [
    (-0.6, [{"urgency": "immediate"}]*3, {}, [], "Breathe"),
    (0.0, [{"urgency": "immediate"}]*3, {}, [], "Overwhelm"),
    (0.0, [{"urgency": "immediate"}], {}, [], "Pressure"),
    (0.0, [{"urgency": "building"}], {}, [], "Tension"),
    (0.0, [], {}, [{"urgency": "building", "age": 4, "id": "t1"}], "Resolve a Threat"),
    (0.0, [], {}, [{"urgency": "background", "age": 3, "id": "t2"}], "Threat Pressure"),
    (0.0, [], {}, [], ""),
    (0.0, [{"urgency": "immediate"}], {"combat_age": 4}, [], "Pressure; Combat Fatigue"),
])
def test_directive_matrix(velocity, pressure, ages, threat_ages, expected):
    result = _compute_narration_directive(
        narrative_velocity=velocity,
        scene_pressure=pressure,
        ages=ages,
        threat_ages=threat_ages,
    )
    assert result == expected
```

#### Step 5.2 — Update integration test fixtures

**File:** `tests/fixtures/` (or wherever mock response fixtures live per `docs/REPOMAP/testing.md`)

**What:** Ensure the integration test plan fixtures (from `docs/testing/integration_test_plan.md`) do not pass `deescalate` anywhere in mock turn construction. Replace any fixture state or mock context that references `deescalate` with `narrative_velocity`.

**Validation:** `make test` — all tests pass. `make check` — no type errors.

---

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`:
  - Add `_compute_narrative_velocity(deescalate, momentum, avoidance, momentum_floor, momentum_ceiling) -> float`
  - Update `_compute_narration_directive` signature to `(narrative_velocity, scene_pressure, ages, threat_ages, ...) -> str`
  - Add `_inject_location_pressure(ages, existing_pressure, location_pressure_at, location_imperative_at) -> list`
  - Remove `deescalate` from `_narrate_messages` and `_run_extraction_pipeline` parameter lists

### Risks
1. If `docs/REPOMAP/testing.md` specifies a different fixture pattern than assumed here, the fixture update in Step 5.2 must follow that pattern exactly.

---

## Ambiguities requiring resolution before execution

1. **`momentum_ceiling` on `EngineConfig`**: Does it exist? Options: A) It exists — use it directly. B) It does not — add `momentum_ceiling: int = 3` to `EngineConfig` in Phase 01 before referencing it.

2. **`location_pressure_at` / `location_imperative_at` on `EngineConfig`**: Same question as above. Options: A) They exist as named fields. B) They do not — the current code uses inline literals `> 4` and `> 2` in `_compute_narration_directive`. In that case, add them to `EngineConfig` with defaults `3` and `5` respectively.

3. **Phase 02 / Phase 04 atomicity**: The `deescalate` → `narrative_velocity` rename in Python signatures (Phase 02) and in Jinja templates (Phase 04) must either land in the same commit or Phase 04 must land first. Options: A) Commit both phases together. B) Add a temporary backward-compat alias (`"deescalate": narrative_velocity`) to the context dicts in Phase 02 and remove it when Phase 04 lands. Executor must choose before starting Phase 02.
