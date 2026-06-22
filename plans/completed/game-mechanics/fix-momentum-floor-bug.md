# Fix: `beat_locked` / Momentum Floor Desync

## Status
`open`

## Objective
`_compute_pacing_context()` reads `momentum` from its parameter, which is passed from `(state.get("pc") or {}).get("momentum", 0)` **before** `apply_delta()` runs. This means `beat_locked` is computed against pre-apply momentum — if the delta contains a momentum decrease that pushes the PC to the floor, `beat_locked` evaluates to `False` this turn and only fires on the *next* turn. The eval assert catches the resulting state where `pacing_context.beat_locked=False` is stored in the event even though post-apply momentum is at floor.

## Non-goals
- Does not touch the `MOMENTUM_DELTA` eval assert or `check_momentum_band_delta` — those are correct.
- Does not change how `apply_momentum()` works — that function is called during `_ruling_phase()` and mutates `state` in place, which means the momentum value **is already correct by the time `_narrate_setup` runs**. The bug is not in ruling phase momentum application; it's in the delta-apply ordering.

***

## Implementation — Phase 01: Fix pacing context momentum read order

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/eval/engine_mirror.py` (to confirm `MOMENTUM_FLOOR` value matches `config.momentum_floor`)

### Detailed steps

#### Step 1.1 — Confirm the actual flow

**File:** `ccya/engine/turn.py`

**What:** Trace the momentum value through the call sequence. In `run_turn`:
1. `_ruling_phase(ctx)` → calls `apply_momentum(state, band)` which mutates `state["pc"]["momentum"]` in place. ✅ Correct — momentum is updated here.
2. `_narrate_setup(ctx)` → calls `_compute_pacing_context(..., momentum=(state.get("pc") or {}).get("momentum", 0), ...)`. This reads from the already-mutated state. ✅ So momentum **is** post-ruling at this point.
3. `pacing_ctx` (`_pc`) is computed in `_narrate_setup` and stored on `ctx.pacing_ctx`.
4. Later, `apply_delta(state, delta)` runs — but `delta` from extraction does **not** contain a momentum field (momentum is applied in-place by `apply_momentum`, not via delta). ✅

**Why this matters:** The momentum value in `_compute_pacing_context` should already be correct. The actual bug may be that `consecutive_pressure_turns` read from state in `_narrate_setup` is *also* stale — it's read *before* the consecutive counter is updated (which happens after `apply_delta`, near the bottom of `run_turn`). If the counter hits threshold exactly this turn, `beat_locked` won't fire until next turn.

**Validation:** Before changing anything, add a debug log immediately before and after the `consecutive_pressure_turns` update block to confirm the counter value at `_narrate_setup` time vs. after update.

***

#### Step 1.2 — Fix: move consecutive pressure counter update before `_narrate_setup`

**File:** `ccya/engine/turn.py`

**What:** The `consecutive_pressure_turns` block currently lives *after* `apply_delta` near the bottom of `run_turn`, inside the `if _extract_result is not None and _pc is not None:` block. This is correct for storing the *result* of this turn's beat, but the counter that governs this turn's `beat_locked` decision was read from `state["meta"]["consecutive_pressure_turns"]` at `_narrate_setup` time — before extraction even ran. That value reflects beats up to and including the *prior* turn, which is actually correct for the forward-looking pacing decision.

**The real fix:** The `beat_locked` check in `_compute_pacing_context` uses `>= config.consecutive_pressure_threshold`. If the threshold is (say) 3, and the counter is at 2 going into this turn, `beat_locked` correctly fires only after 3 consecutive turns are confirmed — which requires knowing this turn's beat type, which isn't known until extraction. This is a chicken-and-egg problem that can't be fully resolved without splitting the computation.

**Resolution:** Accept the one-turn lag for `consecutive_pressure_turns` (it's a secondary signal). The primary fix is to verify the `momentum <= config.momentum_floor` branch fires correctly, since that *can* be known before extraction.

**Code Snippet — add assertion log in `_compute_pacing_context`:**
```python
def _compute_pacing_context(
    deescalate: float,
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    momentum: int,
    config: "EngineConfig",
    consecutive_pressure_turns: int = 0,
    scene_motion: str = "hold",
    impossible: bool = False,
) -> PacingContext:
    # ... existing directive computation ...

    beat_locked = False
    _at_floor = momentum <= config.momentum_floor
    _at_pressure_threshold = consecutive_pressure_turns >= config.consecutive_pressure_threshold
    if _at_floor or _at_pressure_threshold:
        beat_locked = True
        directive_parts = [directive] if directive else []
        directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""

    _log.debug(
        "pacing_context.beat_locked=%s momentum=%d floor=%d consecutive=%d threshold=%d",
        beat_locked, momentum, config.momentum_floor,
        consecutive_pressure_turns, config.consecutive_pressure_threshold,
        extra={"turn": ages.get("scene_age", 0), "trace_id": "", "pack": "", "kind": "pacing"},
    )
    # ... rest unchanged ...
```

**Validation:** Run eval scenario with a forced momentum-at-floor turn. Confirm the debug log shows `beat_locked=True` with the correct momentum value. Confirm `pacing_context.beat_locked` in the stored event matches.

***

#### Step 1.3 — Fix eval assert comment to reflect actual timing contract

**File:** `ccya/eval/universal_asserts.py`

**What:** Add a clarifying docstring to `check_momentum_floor_no_relief` and `check_beat_locked_dual_trigger` (if it exists) explaining that `pacing_context.beat_locked` in the event reflects pre-extraction momentum (post-ruling), and the consecutive counter reflects N-1 turns. This prevents future confusion about whether a failing assert is an engine bug or an eval timing artifact.

**Code Snippet:**
```python
def check_momentum_floor_no_relief(
    event: dict[str, Any],
    prev_event: dict[str, Any] | None,
    event_window: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Momentum at floor for >= 3 consecutive turns without a success band is a pacing failure.

    Timing note: pacing_context.beat_locked is computed in _narrate_setup using post-ruling,
    pre-extraction momentum. The consecutive_pressure_turns counter lags by one turn (it reflects
    beats through the prior turn). A one-turn lag on the counter signal is expected and not a bug.
    """
    # ... existing body unchanged ...
```

**Validation:** No behavior change — doc only. Confirm tests still pass.

***

### Tests to write or update

**File:** `tests/test_pacing.py` (create if absent) or existing pacing test file.

```python
def test_beat_locked_fires_at_momentum_floor():
    """beat_locked must be True when momentum == MOMENTUM_FLOOR."""
    from ccya.engine.turn import _compute_pacing_context, PacingContext
    from ccya.engine.config import EngineConfig
    config = EngineConfig()
    ctx = _compute_pacing_context(
        deescalate=0.0,
        narrative_velocity=0.0,
        scope_scene_threads=[],
        ages={"scene_age": 0, "effective_scene_age": 0},
        momentum=config.momentum_floor,  # exactly at floor
        config=config,
        consecutive_pressure_turns=0,
    )
    assert ctx.beat_locked is True

def test_beat_locked_false_above_floor():
    """beat_locked must be False when momentum is above floor and pressure counter is below threshold."""
    from ccya.engine.turn import _compute_pacing_context
    from ccya.engine.config import EngineConfig
    config = EngineConfig()
    ctx = _compute_pacing_context(
        deescalate=0.0,
        narrative_velocity=0.0,
        scope_scene_threads=[],
        ages={"scene_age": 0, "effective_scene_age": 0},
        momentum=config.momentum_floor + 1,
        config=config,
        consecutive_pressure_turns=config.consecutive_pressure_threshold - 1,
    )
    assert ctx.beat_locked is False

def test_beat_locked_fires_at_pressure_threshold():
    """beat_locked must be True when consecutive_pressure_turns >= threshold."""
    from ccya.engine.turn import _compute_pacing_context
    from ccya.engine.config import EngineConfig
    config = EngineConfig()
    ctx = _compute_pacing_context(
        deescalate=0.0,
        narrative_velocity=0.0,
        scope_scene_threads=[],
        ages={"scene_age": 0, "effective_scene_age": 0},
        momentum=config.momentum_floor + 2,  # above floor
        config=config,
        consecutive_pressure_turns=config.consecutive_pressure_threshold,
    )
    assert ctx.beat_locked is True
```

### Risks

1. **`config.momentum_floor` may differ from `MOMENTUM_MIN` in `engine_mirror.py`.** If `EngineConfig.momentum_floor` has a different default than the eval mirror constant, the assert and the engine disagree on what "floor" means. Verify both before merging.
2. **The bug may be a non-issue in production** if `apply_momentum` is always called in `_ruling_phase` before `_narrate_setup`. Confirm by adding a `assert state["pc"]["momentum"] == ctx._momentum_before` check in a test — if momentum hasn't moved yet at narrate setup time, the read is stale. The code review above suggests it has already moved by then, meaning the floor branch should fire correctly and the eval failure was actually catching a real consecutive-counter lag, not a momentum read bug.

## Ambiguities requiring resolution before execution

1. **Is `MOMENTUM_MIN` in `engine_mirror.py` kept in sync with `EngineConfig.momentum_floor`?** Options: A) They're the same value, the assert is correct. B) They've drifted, meaning the assert fires false positives. Need to check both files before touching anything.

2. **Did the eval failure come from the `momentum <=` branch or the `consecutive_pressure_turns >=` branch?** The fix differs: A) If it's the momentum branch, there may be a genuine read-order bug that needs to be traced more carefully. B) If it's the consecutive counter, the one-turn lag is structural and the right fix is adding the timing note to the assert docstring, not changing engine logic.