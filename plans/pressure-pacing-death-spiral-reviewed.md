# Pressure Pacing and Death Spiral Elimination (TTL/Avoidance/Floor)

## Status
`open`

## Objective
The pressure lifecycle has three compounding failures that produce unescapable death spirals. First, `immediate` pressures have no automatic TTL — once escalated from `building` (which happens at age 4), they persist indefinitely until the extractor explicitly removes them. The extractor routinely fails to remove them after combat, meaning a fight from T3 can still show as active at T14. Second, when momentum reaches the floor (-3), the engine applies no mechanical relief — the only response is a vague narrator directive that is frequently ignored (the directive wire bug is addressed in narration-pacing-fixes.md, but even a correctly-wired directive is advisory, not binding). Third, player de-escalation actions (retreat, rest, disengage) have no mechanical reward — avoidance does not age pressures down, and the engine does not distinguish "player choosing to flee" from "player doing nothing." Together these make recovery from a bad run nearly impossible. This plan adds: a TTL for immediate pressures, a momentum-floor relief mechanism, and an avoidance-based pressure age decay.

## Non-goals
- Does not change dice resolution or band logic in `rules.py`.
- Does not touch the narrator prompts directly (handled in narration-pacing-fixes.md).
- Does not add new Pydantic fields beyond what is needed for TTL tracking (immediate pressures already have `max_turns`; we populate it on escalation).
- Does not change how pressures are added by the extractor — only how they age and expire.
- Does not change `_purge_scene_pressures` location-change behavior.

## Firm decisions

1. `immediate` pressures get a default TTL of **8 turns** from the turn they became immediate (not from `turn_added`). This is set as `max_turns = turn_became_immediate + 8` at escalation time. 8 is long enough to be meaningful but short enough to prevent permanent stale pressures. Configurable via `scene_pressure_immediate_ttl`.
2. At momentum floor (-3), if the player has been at floor for ≥ 2 consecutive turns with no `crit_success` or `success` band, the engine injects a `breathing_room` GM beat into `pending_gm_beat`. This is a mechanical injection, not a narrator suggestion — the beat fires next turn regardless.
3. De-escalation detection: if player input contains any token from a configurable keyword list (`retreat`, `run`, `flee`, `hide`, `rest`, `escape`, `back away`, `disengage`, `withdraw`, `surrender`, `concede`), the turn is flagged `avoidance=True`. On `avoidance=True`, each non-immediate pressure has its effective age incremented by 1 extra turn (simulating time passing while the player creates distance). Immediate pressures are not decayed by avoidance — you can't rest your way out of someone actively stabbing you.
4. Consecutive floor tracking uses a minimal counter in `state["meta"]["consecutive_floor_count"]` rather than scanning event history (events lack momentum snapshots). This is the only new state field added by this plan.
5. All three thresholds are configurable and must have sensible defaults that make the game feel fair without trivializing threat.

## Implementation — Phase 1: Immediate Pressure TTL

### Context files to load
- `ccya/engine/pressure.py`
- `ccya/engine/config.py`
- `config.yaml`

### Overview
When a pressure escalates from `building` to `immediate`, stamp it with a `turn_became_immediate` field and set `max_turns` to `turn_became_immediate + scene_pressure_immediate_ttl`. The existing `max_turns` expiry logic in `_expire_scene_pressures` then handles removal automatically with no further changes needed.

### Detailed steps

#### Step 1.1 — Add config key

**File:** `ccya/engine/config.py`

**What:** Add `scene_pressure_immediate_ttl: int = 8` to `EngineConfig`.

**Why:** Makes the TTL tunable without code changes.

**Code Snippet:**
```python
scene_pressure_immediate_ttl: int = 8
```

**Validation:** `from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.scene_pressure_immediate_ttl == 8`

***

#### Step 1.2 — Add config default to config.yaml

**File:** `config.yaml`

**What:** Under the `game:` section, add:
```yaml
scene_pressure_immediate_ttl: 8
```

**Why:** Keeps config.yaml in sync with the EngineConfig default.

**Validation:** Load config from yaml, confirm field present.

***

#### Step 1.3 — Stamp TTL on escalation in _expire_scene_pressures

**File:** `ccya/engine/pressure.py`

**What:** In the escalation branch inside `_expire_scene_pressures`, when setting `p["urgency"] = "immediate"`, also set `p["turn_became_immediate"] = current_turn` and `p["max_turns"] = turn_added_val + age + immediate_ttl`.

**Why:** The existing `max_turns` check at the top of the loop (`if max_turns is not None and age >= max_turns`) will then handle expiry automatically. No new expiry path needed.

**Code Snippet:**
```python
# In the building→immediate escalation branch (both the TTL=4 path and the configurable path):
p["urgency"] = "immediate"
p["turn_became_immediate"] = current_turn
# Only set max_turns if not already set (extractor may have set one).
if p.get("max_turns") is None:
    immediate_ttl = config.scene_pressure_immediate_ttl if config else 8
    turn_added_val = p.get("turn_added") or current_turn
    p["max_turns"] = turn_added_val + age + immediate_ttl
_log.info(
    "pressure: escalated %r to immediate, max_turns=%s",
    pid, p.get("max_turns"),
    extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "pressure"},
)
```

**Validation:** Write a unit test fixture with a `building` pressure at age 4. Run `_expire_scene_pressures`. Assert `urgency == "immediate"` and `max_turns` is set. Run again at `current_turn = turn_added + 4 + 8`. Assert pressure is in `delta.scene_pressure_remove`.

***

## Implementation — Phase 2: Avoidance-Based Pressure Decay

### Context files to load
- `ccya/engine/pressure.py`
- `ccya/engine/turn.py`
- `ccya/engine/config.py`

### Overview
Detect de-escalation intent in the player's raw input. Pass an `avoidance` boolean through the turn pipeline to `_expire_scene_pressures`. When `avoidance=True`, increment the effective age of non-immediate pressures by an extra turn so they expire sooner.

### Detailed steps

#### Step 2.1 — Add avoidance config keys

**File:** `ccya/engine/config.py`

**What:** Add:
```python
avoidance_keywords: list[str] = ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"]
avoidance_decay_per_turn: int = 1
```

**Validation:** `EngineConfig().avoidance_keywords` contains `"retreat"`.

***

#### Step 2.2 — Detect avoidance in turn.py

**File:** `ccya/engine/turn.py`

**What:** After reading `player_input`, compute:
```python
_avoidance_kw = config.avoidance_keywords
_input_lower = (player_input or "").lower()
avoidance = any(kw in _input_lower for kw in _avoidance_kw)
```
Log `avoidance=True` at `DEBUG` level with `kind="pacing"` if triggered.

**Why:** Centralizes the detection; the flag then flows to the pressure pipeline.

**Validation:** Unit test: input `"I retreat into the alley"` → `avoidance=True`. Input `"I attack the guard"` → `avoidance=False`.

***

#### Step 2.3 — Pass avoidance to _expire_scene_pressures

**File:** `ccya/engine/pressure.py`

**What:** Add `avoidance: bool = False` parameter to `_expire_scene_pressures`. In the age calculation for non-immediate pressures, add `avoidance_bonus = config.avoidance_decay_per_turn if (config and avoidance) else 0` and compute `effective_age = age + avoidance_bonus`. Use `effective_age` in all TTL/escalation checks instead of `age`.

**Why:** When the player retreats, ambient/building threats age faster — the world "catches up" while the player creates distance, but immediate threats (someone physically chasing you) are unaffected.

**Code Snippet:**
```python
def _expire_scene_pressures(
    state: dict[str, Any], delta: StateDelta, config: EngineConfig | None = None, avoidance: bool = False
) -> None:
    ...
    avoidance_bonus = (config.avoidance_decay_per_turn if config else 1) if avoidance else 0
    ...
    urgency = p.get("urgency", "background")
    effective_age = age + (avoidance_bonus if urgency != "immediate" else 0)
    # Use effective_age in all TTL/escalation checks below
```

**Validation:** Test fixture: `building` pressure at age 2, `avoidance=True`, `avoidance_decay_per_turn=2`. effective_age should be 4 → pressure escalates to immediate (same as age 4 without avoidance). Confirms decay math is correct.

***

## Implementation — Phase 3: Momentum Floor Relief Injection

### Context files to load
- `ccya/engine/turn.py`
- `ccya/engine/config.py`

### Overview
After applying the state delta each turn, check if momentum is at floor (-3) and has been for ≥ 2 consecutive turns without a success band. If so, inject `breathing_room` into `pending_gm_beat`. This is engine-level — it fires unconditionally regardless of narrator compliance.

### Detailed steps

#### Step 3.1 — Add momentum floor config keys

**File:** `ccya/engine/config.py`

**What:** Add two fields:
```python
momentum_floor: int = -3
momentum_floor_relief_turns: int = 2
```

**Why:** `momentum_floor` makes the floor value configurable (currently hardcoded as `-3` in `ccya/state/momentum.py`'s `MOMENTUM_MIN`). `momentum_floor_relief_turns` controls how many consecutive turns at floor trigger relief.

**Validation:** `EngineConfig().momentum_floor == -3` and `EngineConfig().momentum_floor_relief_turns == 2`.

**Wiring:** In `build_engine_config()`, add:
```python
momentum_floor=int(game.get("momentum_floor", -3)),
momentum_floor_relief_turns=int(game.get("momentum_floor_relief_turns", 2)),
```

**config.yaml:** Add under `game:` section:
```yaml
momentum_floor: -3
momentum_floor_relief_turns: 2
```

***

#### Step 3.2 — Add floor-tracking helper in turn.py

**File:** `ccya/engine/turn.py`

**What:** Add a helper function `_check_floor_relief(state, config, band: str) -> None` that tracks consecutive floor turns via a counter in `state["meta"]["consecutive_floor_count"]` and injects `breathing_room` when the threshold is reached.

**Why:** Events in `events.jsonl` do not contain `state_snapshot` with momentum values, so the original approach of scanning event history is not feasible. A simple integer counter in `state["meta"]` is the minimal viable approach.

**Code Snippet:**
```python
def _check_floor_relief(
    state: dict[str, Any], config: EngineConfig, band: str
) -> None:
    """Check momentum floor and inject breathing_room beat if relief conditions met.

    Tracks consecutive floor turns via state["meta"]["consecutive_floor_count"].
    Resets counter on any non-floor momentum or success/crit_success band.
    """
    floor = config.momentum_floor
    relief_threshold = config.momentum_floor_relief_turns
    cur_momentum = (state.get("pc") or {}).get("momentum", 0)
    meta = state.setdefault("meta", {})

    if cur_momentum != floor:
        meta["consecutive_floor_count"] = 0
        return

    count = int(meta.get("consecutive_floor_count", 0)) + 1
    meta["consecutive_floor_count"] = count

    if (
        count >= relief_threshold
        and band not in ("success", "crit_success")
        and meta.get("pending_gm_beat") is None
    ):
        meta["pending_gm_beat"] = {
            "type": "breathing_room",
            "surface_as": "ambient",
            "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
        }
        _log.info(
            "pacing: injecting breathing_room beat (floor=%d, consecutive=%d)",
            cur_momentum, count,
            extra={"turn": (state.get("meta") or {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "pacing"},
        )
```

**Validation:** Unit test: call with momentum=-3, band="fail", count reaches threshold → assert `pending_gm_beat` is set. Call with band="success" → assert counter resets and no injection.

***

#### Step 3.3 — Call _check_floor_relief after delta application

**File:** `ccya/engine/turn.py`

**What:** In `run_turn()`, after `apply_delta()` succeeds and before `save_state()`, call `_check_floor_relief(state, config, outcome.band)`. This is in the block after line 673 (the `apply_delta` call), within the `else` branch where delta was accepted.

Also add the import at the top of `turn.py`:
```python
from ccya.engine.pressure import _expire_scene_pressures, _purge_scene_pressures, _check_floor_relief
```

**Code Snippet (placement in run_turn, after apply_delta):**
```python
# After: state, recent_events_evicted = apply_delta(...)
# Add floor relief check
_check_floor_relief(state, config, outcome.band if outcome.rolled else "")
```

**Why:** This is the binding mechanical guarantee. The injection happens after momentum is updated by `apply_momentum` (which runs during `apply_delta`), and the `pending_gm_beat` is persisted via `save_state` so it is available for the next turn's narration. The beat is read at the top of the next `run_turn` call (line 413).

**Validation:** Run a fixture with 3 consecutive turns at momentum=-3 with no success band. Assert `state["meta"]["pending_gm_beat"]["type"] == "breathing_room"` after turn 3. Assert it does NOT inject if last turn was a `success` band.

***

### Tests to write or update
- `tests/test_pressure.py`: `test_immediate_ttl_set_on_escalation` — building pressure age 4 → assert max_turns set.
- `tests/test_pressure.py`: `test_immediate_expires_after_ttl` — immediate pressure at max_turns → assert in delta.scene_pressure_remove.
- `tests/test_pressure.py`: `test_avoidance_decay_building` — building age 2, avoidance=True, decay=2 → effective_age 4, escalates.
- `tests/test_pressure.py`: `test_avoidance_no_effect_on_immediate` — immediate pressure, avoidance=True → effective_age unchanged.
- `tests/test_pressure.py`: `test_floor_relief_injection` — mock state with momentum=-3, call `_check_floor_relief` 2+ times with non-success band → assert `pending_gm_beat` injected.
- `tests/test_pressure.py`: `test_floor_relief_not_injected_after_success` — floor momentum with success band → assert no injection, counter resets.
- `tests/test_pressure.py`: `test_floor_relief_no_injection_with_existing_beat` — floor momentum with existing `pending_gm_beat` → assert no overwrite.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: `_expire_scene_pressures` — add `avoidance: bool = False` param; document `turn_became_immediate` stamp and immediate TTL behavior.
- `docs/REPOMAP/engine.md`: `_purge_scene_pressures` — no change.
- `docs/REPOMAP/engine.md`: `pressure.py` — add `_check_floor_relief` helper; document momentum-floor `breathing_room` injection.
- `docs/REPOMAP/engine.md`: `EngineConfig` — add three new keys: `scene_pressure_immediate_ttl`, `momentum_floor`, `momentum_floor_relief_turns`, `avoidance_keywords`, `avoidance_decay_per_turn`.

### Risks
1. **`max_turns` field conflict** — if a pressure was added with an explicit `max_turns` by the extractor, Phase 1.3 overwrites it on escalation. Mitigation: only set `max_turns` if it is currently `None` at the point of escalation (i.e., `if p.get("max_turns") is None`). **Fixed in plan.**
2. **Avoidance keyword false positives** — "hide" could appear in "I hide behind the pillar" (legitimate avoidance) or "I hide the coin in my pocket" (not avoidance). At decay=1 extra turn, the cost of a false positive is trivial. Acceptable.
3. **Momentum floor injection fighting existing pending_gm_beat** — if a high-priority beat is already pending (e.g., a boss encounter), overwriting it with `breathing_room` is wrong. Mitigation: `_check_floor_relief` checks `meta.get("pending_gm_beat") is None` before injecting. **Fixed in plan.**
4. **Consecutive floor tracking via events is infeasible** — events in `events.jsonl` do not contain `state_snapshot` with momentum values. Resolved by using a counter in `state["meta"]["consecutive_floor_count"]` instead. **Fixed in plan.**

## Ambiguities resolved
1. **Event log for floor tracking:** Events in `events.jsonl` do not contain `state_snapshot` with momentum. Resolved: use a counter in `state["meta"]["consecutive_floor_count"]` instead of scanning events. (See Step 3.2 fix.)
2. **`config.momentum_floor`:** Did not exist. Resolved: added `momentum_floor: int = -3` to `EngineConfig` and wiring in `build_engine_config()`. (See Step 3.1 fix.)
3. **`state.meta` access pattern:** `state` is `dict[str, Any]`, `state["meta"]` is a nested dict. Attribute access like `state.meta.momentum` would raise AttributeError. Resolved: use `state["pc"]["momentum"]` for momentum and `state.setdefault("meta", {})["pending_gm_beat"]` for beat injection. (See Step 3.2/3.3 fixes.)
