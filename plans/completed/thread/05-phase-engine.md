# Phase 5 — Phase engine: convergence score + SETUP TTL

## Purpose

Update `compute_convergence_score()` with new components (any_urgent_thread + active_threat_threads) and add SETUP TTL + `turns_in_phase` tracking to `_compute_scene_phase()`.

## Problem Statement

Convergence score currently only counts urgent thread quantity (components 1 and 2), conflating urgency with type. SETUP phase has no time limit, causing stagnation when the player takes no urgent action.

## Constraints

- Component 1 (any_urgent_thread >= 1) restores the reliable baseline behavior of old component 1.
- Component 2 (active_threat_threads >= 1) adds type-based specificity. Threads with `type == None` still contribute via component 1.
- Dormant threads excluded from all convergence components.
- SETUP → RISING fires on urgent thread OR `turns_in_phase >= 3`, whichever comes first.

## Non-goals

- No changes to components 3-5 (scene_age, beat_streak, dice_weight).
- No changes to auto-dormant, culling, sanitizer, or prompts — covered in other phases.

## Solution

Update `compute_convergence_score()` to accept thread list (or derived counts) instead of `thread_urgency_count`. Add `turns_in_phase` tracking to `_compute_scene_phase()` and use it in the SETUP transition condition.

## Firm decisions

1. Component 1: `any_urgent_thread >= 1` — any thread with `urgency == "urgent"` and `dormant == False`.
2. Component 2: `active_threat_threads >= 1` — threads with `type == "threat"` and `dormant == False`.
3. Component 2 degrades gracefully: if no threads have types, it never fires.
4. SETUP → RISING transition: `thread_urgency_count > 0` OR `turns_in_phase >= 3`.

## Risks, Ambiguities, and Blockers

- **Function signature change:** `compute_convergence_score()` currently takes `thread_urgency_count: int`. Component 2 requires knowing thread types. Two approaches: (a) pass thread data (raw list or counts) and compute both components inside the function; or (b) compute both counts in the caller (`_compute_scene_phase()`) and pass both. Approach (a) is simpler — pass the raw thread list and iterate once.
- **`_compute_scene_phase()` is in `turn.py:503-568`**, not in `_pacing.py`. The convergence score function `compute_convergence_score()` at `_pacing.py:85-131` is called with `thread_urgency_count` from `_compute_scene_phase()`.

## Status

`completed`

## Implementation — Phase 5: Phase engine

### Context files to load

- `ccya/engine/_pacing.py:85-131` — `compute_convergence_score()`
- `ccya/engine/turn.py:503-568` — `_compute_scene_phase()`
- `ccya/engine/config.py:158` — `convergence_threshold` config field

### Detailed steps

#### Step 5.1 — Update `compute_convergence_score()` signature and components

**File:** `ccya/engine/_pacing.py:85-131`

**What:** Change function signature from `thread_urgency_count: int` to `active_threads: list[dict[str, Any]]` (raw thread dict list from state). Replace components 1 and 2:

```python
# Component 1: any urgent thread (+1)
any_urgent = any(
    t.get("urgency") == "urgent" and not t.get("dormant", False)
    for t in active_threads
)
if any_urgent:
    score += 1

# Component 2: active threat (+1)
any_threat = any(
    t.get("type") == "threat" and not t.get("dormant", False)
    for t in active_threads
)
if any_threat:
    score += 1
```

Keep components 3 and 4 unchanged. Update component 5 to use `any_urgent` instead of the removed `thread_urgency_count`.

Update component 5 (lines 123-129) from:
```python
if (
    current_outcome is not None
    and current_outcome.rolled
    and current_outcome.band in ("crit_fail", "fail")
    and thread_urgency_count >= 1
):
    score += 1
```
to:
```python
if (
    any_urgent
    and current_outcome is not None
    and current_outcome.rolled
    and current_outcome.band in ("crit_fail", "fail")
):
    score += 1
```

Remove `thread_urgency_count` parameter. Update docstring.

**Why:** Components 1 and 2 now use dormant-aware type-based logic. Component 5's old `thread_urgency_count >= 1` is semantically identical to `any_urgent` after the new component 1 — reuse the variable. Dormant and abandoned threads excluded from all components.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/_pacing.py').read()); print('syntax OK')"`

#### Step 5.2 — Update caller of `compute_convergence_score()` in main pipeline

**File:** `ccya/engine/turn.py:763-785`

**What:** The convergence score is computed in the MAIN turn pipeline (lines 763-785), NOT in `_compute_scene_phase()`. The function `_compute_scene_phase()` at line 503 receives `convergence_score` as a parameter — it does not compute it.

Change lines 763-785 to pass the raw thread dict list instead of the scalar `thread_urgency_count`:

```python
# Count urgent threads for SETUP transition (still needed by _compute_scene_phase)
_raw_thread_dicts = [t for t in (state.get("arc") or {}).get("threads") or [] if isinstance(t, dict)]

# Compute convergence score before phase machine — passes raw thread list
convergence_score = compute_convergence_score(
    scene_phase=scene_phase,
    active_threads=_raw_thread_dicts,      # was: thread_urgency_count
    scene_age=ctx._ages.get("scene_age", 0),
    recent_beats=state.get("meta", {}).get("recent_beats", []),
    current_outcome=ctx.outcome,
    config=config,
)
```

Remove the `thread_urgency_count` computation (lines 765-770) since it was only used for the convergence score call. The SETUP TTL check in `_compute_scene_phase()` computes its OWN urgency count internally (lines 528-532).

**Why:** Caller must pass the raw thread list so `compute_convergence_score()` can compute both components (any_urgent_thread + active_threat_threads). The old scalar `thread_urgency_count` is insufficient.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/turn.py').read()); print('syntax OK')"`

#### Step 5.3 — Add `turns_in_phase` tracking to `_compute_scene_phase()`

**File:** `ccya/engine/turn.py:503-568`

**What:** Add scene initialization:
```python
scene.setdefault("turns_in_phase", 0)
```

Increment `turns_in_phase` at the start of the function (before the phase transitions):
```python
turns_in_phase = scene.get("turns_in_phase", 0) + 1
```

Add `"turns_in_phase": turns_in_phase` to the return dict (line 568) so the counter persists across turns.

Reset to 0 on every phase transition (SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION, RESOLUTION→BREATHER, BREATHER→RISING).

Update the SETUP→RISING condition:
```python
if phase == "SETUP":
    if thread_urgency_count > 0 or turns_in_phase >= 3:
        phase = "RISING"
        turns_in_phase = 0
```

**Why:** SETUP stagflation prevented. 3-turn TTL ensures RISING even without player urgency.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/turn.py').read()); print('syntax OK')"`

#### Step 5.4 — Remove `thread_stale_threshold` from config

**File:** `ccya/engine/config.py:165,284`

**What:** Remove the `thread_stale_threshold: int = 3` field from `EngineConfig` (line 165) AND remove its reference in `from_game_dict()` (line 284).

```python
# Remove line 165 entirely:
#   thread_stale_threshold: int = 3

# Remove from from_game_dict at line 284:
#   thread_stale_threshold=int(game.get("thread_stale_threshold", 3)),
```

**Why:** Replaced by engine auto-dormant (Phase 3). No code references it after Phase 3. Must remove from both the field definition and the game-dict deserializer to prevent `__init__` errors.

**Validation:** `make check` — confirm no references to `thread_stale_threshold` remain.

### Tests to write or update

No tests currently. Run `make check` for type/lint.

## Status

completed
