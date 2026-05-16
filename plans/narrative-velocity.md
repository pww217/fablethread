# narrative_velocity: Priority-Keyed Pacing Directive Consolidation

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Compute narrative_velocity | Add `momentum_ceiling` to `EngineConfig`; add `_compute_narrative_velocity`; rewrite `_compute_narration_directive` with priority stack; wire into `run_turn` |
| 02 | Propagate through call sites | Remove `deescalate` and `momentum` from `_narrate_messages` and `_extract_progress_messages` signatures; thread `narrative_velocity` instead |
| 03 | Fold location_age into pressure | Add `location_pressure_at` / `location_imperative_at` to `EngineConfig`; add `_inject_location_pressure`; retire parallel location branch |
| 04 | Prompt template cleanup | Update `narrate_user.j2` and `extract_progress_user.j2` to consume `narrative_velocity`; commit atomically with Phase 02 |
| 05 | Tests | Consolidate unit tests; add parametrized directive matrix; update integration fixtures |

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
- `ccya/engine/turn.py` — `_compute_narration_directive`, `_compute_ages`, `run_turn`, `run_turn_retry` (the deescalate computation block in each)
- `ccya/engine/config.py` — full `EngineConfig` dataclass and `build_engine_config`

### Detailed steps

#### Step 1.1 — Add `momentum_ceiling` to `EngineConfig`

**File:** `ccya/engine/config.py`

**What:** Add `momentum_ceiling: int = 3` to the `EngineConfig` dataclass immediately after `momentum_floor: int = -3`. Add the corresponding mapping in `build_engine_config` under the `game` section.

**Why:** `momentum_ceiling` does not exist in the current dataclass — confirmed by reading `config.py`. `_compute_narrative_velocity` (Step 1.2) requires it. Adding it here before referencing it in `turn.py` ensures `make check` passes throughout.

**Code Snippet** (dataclass addition, after `momentum_floor`):
```python
    momentum_floor: int = -3
    momentum_ceiling: int = 3          # NEW — upper bound for momentum normalization
    momentum_floor_relief_turns: int = 2
```

**Code Snippet** (`build_engine_config` addition, under `game` section):
```python
        momentum_floor=int(game.get("momentum_floor", -3)),
        momentum_ceiling=int(game.get("momentum_ceiling", 3)),   # NEW
        momentum_floor_relief_turns=int(game.get("momentum_floor_relief_turns", 2)),
```

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.momentum_ceiling == 3; print('ok')`

---

#### Step 1.2 — Add `_compute_narrative_velocity` to `turn.py`

**File:** `ccya/engine/turn.py`

**What:** New pure function. Converts `deescalate`, current `momentum`, and `avoidance` into a single float in `[-1.0, 1.0]`. Negative = de-escalate / breathe. Positive = escalate. Zero = neutral.

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
      3. Momentum outside floor/ceiling normalizes toward ±0.5.
      5. Default: 0.0 (neutral, let pressure/beat directives govern).
    """
    if deescalate > 0:
        return -deescalate  # already in (0, 1.0] from run_turn; negate for direction

    if avoidance:
        return -0.4

    span = momentum_ceiling - momentum_floor
    if span <= 0:
        return 0.0
    midpoint = (momentum_ceiling + momentum_floor) / 2.0
    normalized = (momentum - midpoint) / (span / 2.0)
    # Scale down — momentum alone shouldn't dominate; caps at ±0.5
    return max(-0.5, min(0.5, normalized * 0.5))
```

**Validation:** `python -c "from ccya.engine.turn import _compute_narrative_velocity; assert _compute_narrative_velocity(0.6, 0, False) == -0.6; assert _compute_narrative_velocity(0.0, 0, True) == -0.4; assert _compute_narrative_velocity(0.0, 0, False) == 0.0; print('ok')`

---

#### Step 1.3 — Rewrite `_compute_narration_directive` with a priority stack

**File:** `ccya/engine/turn.py`

**What:** Replace the current additive semicolon-join approach with an ordered priority stack. The function returns the *single highest-priority directive label*, optionally followed by secondary labels only when they do not contradict the primary. Contradiction rule: if `velocity < -0.3` (breathe/de-escalate), return `"Breathe"` immediately with no secondaries.

**Why:** Fixes the `"Breathe; Location Imperative"` contradiction class. LLM receives one clear instruction, not a list of conflicting ones. The `ages` parameter is retained for `combat_age` (secondary append) but the `location_age` branch is removed — that is handled by Phase 03 via synthetic pressure injection.

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
      6. Threat Pressure — background threat aging toward imperative
      Secondary (non-contradicting append):
      7. Combat Fatigue — combat_age >= 3
    """
    # Priority 1: breathe (de-escalation wins unconditionally)
    if narrative_velocity < -0.3:
        return "Breathe"

    secondary: list[str] = []

    # Priority 2: overwhelm (3+ immediate pressures)
    immediate_count = sum(1 for p in scene_pressure if p.get("urgency") == "immediate")
    if immediate_count >= 3:
        primary = "Overwhelm"
    else:
        primary = ""

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

**Validation:**
```python
from ccya.engine.turn import _compute_narration_directive

assert _compute_narration_directive(-0.6, [{"urgency": "immediate"}]*3, {}, []) == "Breathe"
assert _compute_narration_directive(0.0, [{"urgency": "immediate"}]*3, {}, []) == "Overwhelm"
assert _compute_narration_directive(0.0, [{"urgency": "immediate"}], {"combat_age": 3}, []) == "Pressure; Combat Fatigue"
assert _compute_narration_directive(0.0, [], {}, []) == ""
```

---

#### Step 1.4 — Wire `_compute_narrative_velocity` into `run_turn` and `run_turn_retry`

**File:** `ccya/engine/turn.py`

**What:** In `run_turn`, replace the inline `deescalate` computation block and the `_compute_narration_directive` call with the two new functions. In `run_turn_retry`, replace its existing directive computation with the same pattern (with `deescalate=0.0` and `avoidance=False`). Do not remove the `deescalate` local variable yet — it is still passed to `_narrate_messages` and `_run_extraction_pipeline` until Phase 02 lands.

**Code Snippet** (in `run_turn`, after `apply_momentum` and before `_narrate_messages`):
```python
# Compute unified pacing scalar
narrative_velocity = _compute_narrative_velocity(
    deescalate=deescalate,
    momentum=(state.get("pc") or {}).get("momentum", 0),
    avoidance=avoidance,
    momentum_floor=config.momentum_floor,
    momentum_ceiling=config.momentum_ceiling,
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

**Code Snippet** (in `run_turn_retry`):
```python
narrative_velocity = _compute_narrative_velocity(
    deescalate=0.0,
    momentum=(state.get("pc") or {}).get("momentum", 0),
    avoidance=False,
    momentum_floor=config.momentum_floor,
    momentum_ceiling=config.momentum_ceiling,
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

**Validation:** `make check` passes. `make test` — all existing tests pass.

---

### Tests to write or update

**File:** `tests/test_pacing.py` (create if not present)

```python
from ccya.engine.turn import _compute_narrative_velocity, _compute_narration_directive

def test_velocity_deescalate_dominates():
    assert _compute_narrative_velocity(0.6, 3, False) == -0.6

def test_velocity_avoidance():
    assert _compute_narrative_velocity(0.0, 0, True) == -0.4

def test_velocity_neutral():
    assert _compute_narrative_velocity(0.0, 0, False) == 0.0

def test_velocity_high_momentum_positive():
    assert _compute_narrative_velocity(0.0, 3, False) > 0

def test_breathe_suppresses_overwhelm():
    result = _compute_narration_directive(-0.6, [{"urgency": "immediate"}]*3, {}, [])
    assert result == "Breathe"

def test_overwhelm_wins():
    result = _compute_narration_directive(0.0, [{"urgency": "immediate"}]*3, {}, [])
    assert result == "Overwhelm"

def test_combat_fatigue_appended():
    result = _compute_narration_directive(0.0, [{"urgency": "immediate"}], {"combat_age": 4}, [])
    assert result == "Pressure; Combat Fatigue"

def test_empty_returns_empty_string():
    result = _compute_narration_directive(0.0, [], {}, [])
    assert result == ""
```

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — add `_compute_narrative_velocity`; update `_compute_narration_directive` signature.

### Risks
1. The old `_compute_narration_directive` signature accepted `ages` and `location_age` as the primary location branch — after Step 1.3, `location_age` is only used for the `combat_age` secondary. Phase 03 must follow to wire in the synthetic pressure; between Phase 01 and Phase 03 landing, location staleness will be undetected. This is acceptable since Phase 03 is a fast follow.
2. `deescalate` is still passed downstream until Phase 02 — do not remove it in `run_turn` until Phase 02 is committed.

---

## Implementation — Phase 02 + 04: Propagate through call sites (commit atomically with Phase 04)

**Critical:** Phase 02 renames `deescalate` → `narrative_velocity` in Python signatures. Phase 04 renames it in Jinja templates. A runtime `UndefinedError` will occur if either lands without the other. **These two phases must be committed in a single atomic commit.**

### Files to pull for context
- `ccya/engine/narrate.py` — `_narrate_messages` full signature and `user_ctx` dict
- `ccya/engine/extraction.py` — `_extract_progress_messages` and `_run_extraction_pipeline` signatures
- `ccya/engine/turn.py` — `_narrate_messages(...)` and `_run_extraction_pipeline(...)` call sites in both `run_turn` and `run_turn_retry`
- `ccya/prompts/narrate_user.j2` — all references to `deescalate` and `momentum` (template variables)
- `ccya/prompts/extract_progress_user.j2` — all references to `deescalate`

### Detailed steps

#### Step 2.1 — Remove `deescalate` and `momentum` from `_narrate_messages`

**File:** `ccya/engine/narrate.py`

**What:** Replace `deescalate: float = 0.0` with `narrative_velocity: float = 0.0`. Remove `momentum: int = 0` from the signature entirely — it is no longer needed as a separate input since it is subsumed into `narrative_velocity`. Update `user_ctx` to use `"narrative_velocity": narrative_velocity` and remove the `"momentum": momentum` key.

**Why:** Confirmed by reading `narrate.py`: both `deescalate` and `momentum` exist as separate params and both are placed into `user_ctx`. After this change the template receives one pacing signal instead of two.

**Code Snippet** (full updated signature — copy this exactly, do not use the old version as a base):
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
    pending_gm_beat: dict[str, Any] | None = None,
    narrative_velocity: float = 0.0,       # replaces deescalate; momentum removed
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
```

In `user_ctx`, replace:
```python
    "momentum": momentum,
    "deescalate": deescalate,
```
with:
```python
    "narrative_velocity": narrative_velocity,
```

**Validation:** `grep -n "deescalate\|\"momentum\"" ccya/engine/narrate.py` — zero matches.

---

#### Step 2.2 — Remove `deescalate` from `_extract_progress_messages` and `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_progress_messages`, replace `deescalate: float = 0.0` with `narrative_velocity: float = 0.0` and update the Jinja context key. In `_run_extraction_pipeline`, same rename and thread through.

**Code Snippet** (`_extract_progress_messages` — parameter and context key only; leave all other params unchanged):
```python
# Parameter:
    narrative_velocity: float = 0.0,   # replaces deescalate

# In the _render call context dict:
    "narrative_velocity": narrative_velocity,   # was "deescalate": deescalate
```

**Code Snippet** (`_run_extraction_pipeline` — parameter and pass-through only):
```python
# Parameter:
    narrative_velocity: float = 0.0,   # replaces deescalate

# In _extract_progress_messages call:
    narrative_velocity=narrative_velocity,   # was deescalate=deescalate
```

**Validation:** `grep -n "deescalate" ccya/engine/extraction.py` — zero matches.

---

#### Step 2.3 — Update `run_turn` and `run_turn_retry` call sites

**File:** `ccya/engine/turn.py`

**What:** Update both `_narrate_messages(...)` calls and both `_run_extraction_pipeline(...)` calls to pass `narrative_velocity=narrative_velocity` instead of `deescalate=deescalate`. Remove `momentum=...` from the `_narrate_messages` call. Remove the standalone `deescalate` variable after confirming no remaining references.

**Validation:** `grep -n "deescalate" ccya/engine/turn.py` — zero matches. `make check` passes.

---

#### Step 4.1 — Update `narrate_user.j2` (commit with Phase 02)

**File:** `ccya/prompts/narrate_user.j2`

**What:** Before touching the file, run `grep -n "deescalate\|momentum" ccya/prompts/narrate_user.j2` to find every reference. Replace all `deescalate` references with `narrative_velocity`. Replace any `momentum` template variable references with `narrative_velocity` comparisons (e.g., `{% if deescalate > 0 %}` → `{% if narrative_velocity < -0.3 %}`). Remove any standalone `{{ momentum }}` output.

**Validation:** Render the template in isolation:
```python
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader("ccya/prompts"))
out = env.get_template("narrate_user.j2").render(
    narrative_velocity=0.0, state={}, pc={}, user_input="test",
    chronicle_tail="", recent_turns=[], rules_outcome=None,
    npc_name_pool={}, recently_left=[], pending_gm_beat=None,
    meta={"turn": 1}, scene={}, ages={}, known_npcs=[], present_npcs=[],
    compendium_bios=[], pc_allegiance=None, scene_pressure=[],
    world_factions=[], world_locations=[], threat_ages=[],
    threat_pressure_at=3, threat_imperative_at=5,
    building_threat_imperative_at=4, npc_roster=[], prior_history=[],
)
assert out  # non-empty, no UndefinedError
```

---

#### Step 4.2 — Update `extract_progress_user.j2` (commit with Phase 02)

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Run `grep -n "deescalate" ccya/prompts/extract_progress_user.j2`. Replace all matches with `narrative_velocity`. Conditions that were `{% if deescalate > 0 %}` become `{% if narrative_velocity < -0.3 %}`.

**Validation:** Same pattern as Step 4.1 — render with a mock context containing `narrative_velocity` and confirm no `UndefinedError`.

---

### Tests to write or update
- Run `make test` — no import errors on the renamed parameters.
- Add smoke-render test in `tests/test_templates.py`:
```python
def test_narrate_user_j2_no_deescalate():
    """Template renders without UndefinedError when narrative_velocity replaces deescalate."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    env = Environment(loader=FileSystemLoader("ccya/prompts"), undefined=StrictUndefined)
    # StrictUndefined will raise if any variable is missing — this catches regressions
    ctx = {
        "narrative_velocity": 0.0, "state": {}, "pc": {}, "user_input": "test",
        "chronicle_tail": "", "recent_turns": [], "rules_outcome": None,
        "npc_name_pool": {}, "recently_left": [], "pending_gm_beat": None,
        "meta": {"turn": 1}, "scene": {}, "ages": {}, "known_npcs": [],
        "present_npcs": [], "compendium_bios": [], "pc_allegiance": None,
        "scene_pressure": [], "world_factions": [], "world_locations": [],
        "threat_ages": [], "threat_pressure_at": 3, "threat_imperative_at": 5,
        "building_threat_imperative_at": 4, "npc_roster": [], "prior_history": [],
    }
    out = env.get_template("narrate_user.j2").render(**ctx)
    assert out
```

### Risks
1. `narrate_user.j2` or `extract_progress_user.j2` may reference `momentum` or `deescalate` in multiple Jinja blocks — grep first, replace all, do not assume a single occurrence.
2. `StrictUndefined` in the smoke test will catch any missed template variable. If the render fails, find the missing key and add it to the context or fix the template.

---

## Implementation — Phase 03: Fold location_age into pressure

### Files to pull for context
- `ccya/engine/turn.py` — `_compute_ages`, `_compute_narration_directive` (post-Phase-01 version), `run_turn`, `run_turn_retry`
- `ccya/engine/config.py` — `EngineConfig` dataclass (post-Phase-01 version with `momentum_ceiling`)

### Detailed steps

#### Step 3.0 — Add `location_pressure_at` and `location_imperative_at` to `EngineConfig`

**File:** `ccya/engine/config.py`

**What:** Add two new fields after the `scene_pressure_*` block:
```python
    # Location staleness thresholds (turns since last location change)
    location_pressure_at: int = 3   # building pressure at this age
    location_imperative_at: int = 5  # immediate pressure at this age
```

Add corresponding entries in `build_engine_config` under the `game` section:
```python
        location_pressure_at=int(game.get("location_pressure_at", 3)),
        location_imperative_at=int(game.get("location_imperative_at", 5)),
```

**Why:** Confirmed absent from `config.py`. Formalizing them removes the need for `getattr()` defensive patterns in `turn.py` and makes the thresholds configurable per-game.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.location_pressure_at == 3; assert c.location_imperative_at == 5; print('ok')`

---

#### Step 3.1 — Add `_inject_location_pressure` to `turn.py`

**File:** `ccya/engine/turn.py`

**What:** New pure function. Given `ages` and config thresholds, returns a new pressure list with a synthetic location staleness entry appended if warranted. Does not mutate the input. The synthetic entry uses `id="_engine_location_stale"` and `turn_added=0` (engine-generated; never persisted to state; `_compute_threat_ages` must skip `turn_added==0`).

**Code Snippet**
```python
_LOCATION_PRESSURE_ID = "_engine_location_stale"

def _inject_location_pressure(
    ages: dict[str, int],
    existing_pressure: list[dict[str, Any]],
    location_pressure_at: int = 3,
    location_imperative_at: int = 5,
) -> list[dict[str, Any]]:
    """Return a new pressure list with a synthetic location staleness entry if warranted.

    Does not mutate the input list. Returns a new list.
    The synthetic entry is never persisted to state (turn_added=0 signals engine-generated).
    """
    location_age = ages.get("location_age", 0)
    filtered = [p for p in existing_pressure if p.get("id") != _LOCATION_PRESSURE_ID]
    if location_age <= location_pressure_at:
        return filtered

    urgency = "immediate" if location_age > location_imperative_at else "building"
    synthetic = {
        "id": _LOCATION_PRESSURE_ID,
        "text": "The scene has lingered here too long — move it along.",
        "urgency": urgency,
        "turn_added": 0,
    }
    return filtered + [synthetic]
```

**Validation:**
```python
from ccya.engine.turn import _inject_location_pressure, _LOCATION_PRESSURE_ID

result = _inject_location_pressure({"location_age": 2}, [])
assert not any(p["id"] == _LOCATION_PRESSURE_ID for p in result)

result = _inject_location_pressure({"location_age": 4}, [], location_pressure_at=3, location_imperative_at=5)
assert next(p for p in result if p["id"] == _LOCATION_PRESSURE_ID)["urgency"] == "building"

result = _inject_location_pressure({"location_age": 6}, [], location_pressure_at=3, location_imperative_at=5)
assert next(p for p in result if p["id"] == _LOCATION_PRESSURE_ID)["urgency"] == "immediate"
```

---

#### Step 3.2 — Wire `_inject_location_pressure` into `run_turn` and `run_turn_retry`

**File:** `ccya/engine/turn.py`

**What:** Before `_compute_narration_directive` in both `run_turn` and `run_turn_retry`, insert the augmentation call. Pass `_effective_pressure` to both `_compute_narration_directive` and `_narrate_messages` instead of the raw pressure list.

**Code Snippet** (insert before `narration_directive =` in both functions):
```python
_raw_scene_pressure = (state.get("scene") or {}).get("scene_pressure") or []
_effective_pressure = _inject_location_pressure(
    ages=ages,
    existing_pressure=_raw_scene_pressure,
    location_pressure_at=config.location_pressure_at,
    location_imperative_at=config.location_imperative_at,
)

narration_directive = _compute_narration_directive(
    narrative_velocity=narrative_velocity,
    scene_pressure=_effective_pressure,
    ages=ages,
    threat_ages=threat_ages,
    threat_pressure_at=config.threat_pressure_at,
    threat_imperative_at=config.threat_imperative_at,
    building_threat_imperative_at=config.building_threat_imperative_at,
)
```

Pass `scene_pressure=_effective_pressure` to `_narrate_messages(...)` as well.

---

#### Step 3.3 — Verify `_compute_threat_ages` skips `turn_added == 0`

**File:** `ccya/engine/turn.py`

**What:** Read `_compute_threat_ages` and confirm it guards against `turn_added == 0` before computing age. If the guard is absent, add:
```python
if entry.get("turn_added", 0) == 0:
    continue  # engine-generated synthetic entry — skip aging
```

**Why:** The synthetic location entry must not accumulate age and trigger `Resolve a Threat` via the threat aging path.

**Validation:** Add a test asserting that a pressure entry with `turn_added=0` does not appear in `_compute_threat_ages` output.

---

#### Step 3.4 — Remove `location_age` branch from `_compute_narration_directive`

**File:** `ccya/engine/turn.py`

**What:** After Phase 03 wiring is confirmed working, delete any remaining `location_age` checks from `_compute_narration_directive`. The function's `ages` parameter is now only consumed by the `combat_age` secondary append.

**Validation:** `grep -n "location_age" ccya/engine/turn.py` — zero hits in `_compute_narration_directive`. `make check` passes.

---

### Tests to write or update

**File:** `tests/test_pacing.py`

```python
from ccya.engine.turn import _inject_location_pressure, _LOCATION_PRESSURE_ID

def test_inject_location_pressure_not_stale():
    result = _inject_location_pressure({"location_age": 2}, [])
    assert not any(p["id"] == _LOCATION_PRESSURE_ID for p in result)

def test_inject_location_pressure_building():
    result = _inject_location_pressure({"location_age": 4}, [], location_pressure_at=3, location_imperative_at=5)
    entry = next(p for p in result if p["id"] == _LOCATION_PRESSURE_ID)
    assert entry["urgency"] == "building"

def test_inject_location_pressure_immediate():
    result = _inject_location_pressure({"location_age": 6}, [], location_pressure_at=3, location_imperative_at=5)
    entry = next(p for p in result if p["id"] == _LOCATION_PRESSURE_ID)
    assert entry["urgency"] == "immediate"

def test_inject_location_pressure_replaces_existing():
    existing = [{"id": _LOCATION_PRESSURE_ID, "urgency": "building", "text": "old", "turn_added": 0}]
    result = _inject_location_pressure({"location_age": 6}, existing, location_pressure_at=3, location_imperative_at=5)
    stale = [p for p in result if p["id"] == _LOCATION_PRESSURE_ID]
    assert len(stale) == 1 and stale[0]["urgency"] == "immediate"

def test_synthetic_pressure_not_aged_by_threat_ages():
    from ccya.engine.turn import _compute_threat_ages  # or wherever it lives
    synthetic = {"id": "_engine_location_stale", "urgency": "building", "turn_added": 0}
    # _compute_threat_ages must not include this entry
    result = _compute_threat_ages([synthetic], current_turn=5)
    assert not any(e.get("id") == "_engine_location_stale" for e in result)
```

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — add `_inject_location_pressure`, `_LOCATION_PRESSURE_ID`; add `location_pressure_at` / `location_imperative_at` to `EngineConfig` entry.

### Risks
1. `_compute_threat_ages` signature is unverified — executor must read it before Step 3.3 to confirm how entries are structured and whether a `turn_added == 0` guard already exists.
2. Between Phase 01 landing and Phase 03 landing, location staleness is undetected. Acceptable as a short gap; Phase 03 should follow Phase 01 immediately.

---

## Implementation — Phase 05: Tests

### Files to pull for context
- `tests/` — list all test files to confirm `test_pacing.py` doesn't already exist
- `tests/conftest.py` — check shared fixtures and FakeLLM patterns
- `docs/REPOMAP/testing.md` — integration fixture conventions

### Detailed steps

#### Step 5.1 — Consolidate pacing tests

**File:** `tests/test_pacing.py`

**What:** Collect all unit tests written inline in Phases 01–03 into a single file. Add a parametrized matrix test for `_compute_narration_directive`.

**Code Snippet**
```python
import pytest
from ccya.engine.turn import (
    _compute_narrative_velocity,
    _compute_narration_directive,
    _inject_location_pressure,
    _LOCATION_PRESSURE_ID,
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

**File:** `tests/fixtures/` (follow pattern from `docs/REPOMAP/testing.md`)

**What:** Ensure no fixture state or mock context references `deescalate` or passes `momentum` to `_narrate_messages`. Replace any such references with `narrative_velocity`. Verify `docs/testing/integration_test_plan.md` fixtures are consistent with the renamed parameters.

**Validation:** `make test` — all tests pass. `make check` — no type errors.

---

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`:
  - Add `_compute_narrative_velocity(deescalate, momentum, avoidance, momentum_floor, momentum_ceiling) -> float`
  - Update `_compute_narration_directive` to new signature
  - Add `_inject_location_pressure(ages, existing_pressure, location_pressure_at, location_imperative_at) -> list`
  - Add `_LOCATION_PRESSURE_ID: str` constant
  - Remove `deescalate` and `momentum` from `_narrate_messages` parameter list
  - Remove `deescalate` from `_run_extraction_pipeline` parameter list
  - Add `momentum_ceiling`, `location_pressure_at`, `location_imperative_at` to `EngineConfig` entry

### Risks
1. If `docs/REPOMAP/testing.md` specifies a fixture pattern different from what the integration test plan assumes, the executor must follow the REPOMAP pattern, not the integration plan.

---

## Ambiguities requiring resolution before execution

All three original ambiguities are now resolved:

1. **`momentum_ceiling`** — confirmed absent. Step 1.1 adds it to `EngineConfig` with default `3` before any reference in `turn.py`.

2. **`location_pressure_at` / `location_imperative_at`** — confirmed absent. Step 3.0 adds both to `EngineConfig` with defaults `3` and `5`. Direct field access used throughout; no `getattr()` defensive patterns needed.

3. **Phase 02 / Phase 04 atomicity** — resolved to Option A. Phases 02 and 04 are documented as a single combined phase and must be committed in one atomic commit. No backward-compat alias needed.

One new ambiguity identified during source review:

4. **`_compute_threat_ages` guard for `turn_added == 0`**: Step 3.3 requires verifying this guard exists before Phase 03 wiring. Executor must read `_compute_threat_ages` in `turn.py` before proceeding. Options: A) Guard exists — proceed. B) Guard absent — add it in Step 3.3 before wiring.
