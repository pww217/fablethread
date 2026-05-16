# Fix location turn stamp off-by-one

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Stamp turn_entered and location_entered_turn with post-increment value | Pass the already-computed turn_no into apply_delta so the stamps use the correct turn |

## Objective
When `apply_delta` processes a `location_change`, it stamps `state["scene"]["turn_entered"]` and `state["scene"]["location_entered_turn"]` using `state["meta"]["turn"]`. However, `state["meta"]["turn"]` is incremented *after* `apply_delta` returns in both `run_turn` and `run_turn_retry`. This means both fields are written with `current_turn - 1` — the turn the player was at the *previous* location — not the turn the location change actually occurred.

Consequence: `_compute_ages` reads both fields and subtracts from the current (post-increment) turn to compute `location_age` and `scene_age`. Because the fields are already 1 behind, both ages read 1 higher than reality on the first turn at a new location. The narrator fires Location Pressure after only 2 actual turns instead of 3, and Location Imperative after 4 turns instead of 5.

The fix is to thread `turn_no` (already computed in `run_turn` as `state["meta"]["turn"] + 1` before any mutations) through `apply_delta` so it can stamp the correct value. Because `apply_delta` is also called from the compactor and from tests, the new parameter must be optional with a sensible default fallback.

## Non-goals
- No changes to `_compute_ages` logic.
- No changes to `scene_age` computation or `turn_entered` semantics beyond the stamp.
- No changes to how the narrator uses `location_age`.
- No state migration — the off-by-one affects only location-change turns, and the correction will take effect naturally from the next location change.
- No changes to `run_turn_retry` beyond passing `turn_no` (it already has the same variable).

---

## Implementation — Phase 01: Stamp turn_entered and location_entered_turn with post-increment value

### Files to pull for context
- `ccya/state/delta.py` — `apply_delta` signature and the `location_change` block
- `ccya/engine/turn.py` — both `run_turn` and `run_turn_retry` call sites for `apply_delta`
- `ccya/engine/compactor.py` — any `apply_delta` call there (check if it exists)
- `ccya/state/__init__.py` — re-exports; verify `apply_delta` signature is re-exported

### Detailed steps

#### Step 1.1 — Add current_turn_no parameter to apply_delta

**File:** `ccya/state/delta.py`

**What:** Add an optional keyword argument `current_turn_no: int | None = None` to `apply_delta`. In the `location_change` block, prefer `current_turn_no` over `state.get("meta", {}).get("turn", 0)` for stamping `turn_entered` and `location_entered_turn`.

**Why:** `apply_delta` cannot see `turn_no` directly — it only sees the state dict, which holds the pre-increment turn. The caller (`run_turn`) already has the correct value as `turn_no` before calling `apply_delta`.

**Code Snippet**

Signature change:
```python
def apply_delta(
    state: dict[str, Any],
    delta: StateDelta,
    *,
    recent_events_max: int = 20,
    current_turn_no: int | None = None,
) -> tuple[dict[str, Any], bool]:
```

Inside the `location_change` block, replace:
```python
    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": _strip_non_ascii(delta.location_change.name),
            "description": delta.location_change.description,
        }
        state.setdefault("scene", {})["present_npcs"] = []
        state.setdefault("scene", {})["recently_left"] = []
        state.setdefault("scene", {})["recently_left_turns"] = 0
        state["scene"]["turn_entered"] = state.get("meta", {}).get("turn", 0)
        state["scene"]["location_entered_turn"] = state.get("meta", {}).get("turn", 0)
```
With:
```python
    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": _strip_non_ascii(delta.location_change.name),
            "description": delta.location_change.description,
        }
        state.setdefault("scene", {})["present_npcs"] = []
        state.setdefault("scene", {})["recently_left"] = []
        state.setdefault("scene", {})["recently_left_turns"] = 0
        _stamp_turn = current_turn_no if current_turn_no is not None else state.get("meta", {}).get("turn", 0)
        state["scene"]["turn_entered"] = _stamp_turn
        state["scene"]["location_entered_turn"] = _stamp_turn
```

**Validation:** Confirm `apply_delta` still works with no `current_turn_no` argument (used by compactor and tests) and falls back to the existing behavior.

#### Step 1.2 — Pass turn_no to apply_delta in run_turn

**File:** `ccya/engine/turn.py`

**What:** In `run_turn`, the `apply_delta` call is:
```python
                state, recent_events_evicted = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
```
Change to:
```python
                state, recent_events_evicted = apply_delta(
                    state, delta,
                    recent_events_max=config.recent_events_max,
                    current_turn_no=turn_no,
                )
```

**Why:** `turn_no` is computed at the start of `run_turn` as `state["meta"]["turn"] + 1` and is the correct post-increment value.

**Validation:** After this change, if a location change occurs on turn 5, `state["scene"]["location_entered_turn"]` must equal `5`, not `4`. Verify with a test.

#### Step 1.3 — Pass turn_no to apply_delta in run_turn_retry

**File:** `ccya/engine/turn.py`

**What:** Same change in the `run_turn_retry` copy of the `apply_delta` call.

```python
                state, recent_events_evicted = apply_delta(
                    state, delta,
                    recent_events_max=config.recent_events_max,
                    current_turn_no=turn_no,
                )
```

**Validation:** Same as Step 1.2.

### Tests to write or update

**File:** `tests/test_state_delta.py` (create if it does not exist; check for existing delta tests first)

```python
def test_apply_delta_location_stamp_uses_current_turn_no() -> None:
    """location_entered_turn must reflect current_turn_no, not the pre-increment meta.turn."""
    from ccya.models import LocationRef, StateDelta
    from ccya.state.delta import apply_delta

    state: dict = {
        "meta": {"turn": 4},  # pre-increment value
        "inventory": [],
        "pc": {"conditions": []},
        "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
        "compendium": {"npcs": {}},
    }
    delta = StateDelta(
        location_change=LocationRef(id="tavern", name="The Tavern", description="A dim room.")
    )
    new_state, _ = apply_delta(state, delta, current_turn_no=5)
    assert new_state["scene"]["location_entered_turn"] == 5
    assert new_state["scene"]["turn_entered"] == 5


def test_apply_delta_location_stamp_fallback_without_current_turn_no() -> None:
    """Without current_turn_no, stamp falls back to meta.turn (existing behavior)."""
    from ccya.models import LocationRef, StateDelta
    from ccya.state.delta import apply_delta

    state: dict = {
        "meta": {"turn": 4},
        "inventory": [],
        "pc": {"conditions": []},
        "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
        "compendium": {"npcs": {}},
    }
    delta = StateDelta(
        location_change=LocationRef(id="tavern", name="The Tavern", description="A dim room.")
    )
    new_state, _ = apply_delta(state, delta)
    assert new_state["scene"]["location_entered_turn"] == 4
```

### REPOMAP and architecture updates
`docs/REPOMAP/state.md` — update `apply_delta` entry: note the optional `current_turn_no: int | None = None` parameter and document that callers should pass the post-increment turn number when available so `turn_entered` and `location_entered_turn` are stamped correctly.

### Risks
1. Tests that call `apply_delta` directly with a location change and check `location_entered_turn` will now see a different value if they pass `current_turn_no`. Existing tests that don't pass it will continue to use the fallback and should be unaffected.
2. The compactor calls `_apply_sanitization`, not `apply_delta` directly for pressure/condition/NPC changes — verify it does not call `apply_delta` with location changes. If it does, it should be updated to pass the current turn.

## Ambiguities requiring resolution before execution
None.
