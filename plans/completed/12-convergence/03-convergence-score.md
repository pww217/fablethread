# Convergence Scoring — Phase 3: Convergence Score + Phase Machine

**Status: completed** (2026-06-15)

## Purpose

Implement `compute_convergence_score()` and wire it into the RISING→CLIMAX transition. Replaces the old `crisis_urgency_threshold` and `tension_delta` checks with a composite 5-component score. Phase 2 must be complete (CRISIS→CLIMAX rename done, dead code removed, phase machine has no RISING→CLIMAX entry path yet).

## Firm decisions

- Score computed fresh each turn, never persisted (logged in event only).
- Five components, each worth +1, threshold 3 (configurable via `convergence_threshold`).
- Pending beat for current turn NOT included in streak calculation (pipeline ordering invariant).
- `current_outcome` parameter is `RulesOutcome | None` (not a list). Renamed from `recent_rolls` — it's the current turn's full outcome.
- Score computed before storytell runs each turn (in the narrate-setup block, same point where phase machine runs).
- RISING→CLIMAX transition: `if convergence_score >= config.convergence_threshold`.
- All other phase transitions unchanged.
- `outcome_hint = "transition"` override stays (Scene Imperative at `effective_scene_age >= scene_imperative_threshold`).
- Log convergence score components in event dict for EV tooling.

## Status

`open`

## Dependencies

- Phase 2 complete (phase machine functions cleaned up, config renamed, `climax_turn_count` state key exists).

## Implementation — Phase 3: Convergence Score + Phase Machine

### Context files to load

- `ccya/engine/_pacing.py` — create `compute_convergence_score()` after existing functions
- `ccya/engine/turn.py` — `_compute_scene_phase` (503-582), narrate-setup block (760-834), `_compute_pacing_context` (444-486), event dict (1365-1400)
- `ccya/engine/config.py` — verify `convergence_threshold` field exists (Phase 1)
- `ccya/models.py` — `RulesOutcome` (lines 179-194) — verify band field, rolled field
- `ccya/engine/extraction.py` — `_storytell_messages` (310-389) — verify how scene_phase and recent_beats are passed to prompts

### Detailed steps

#### Step 3.1 — Implement compute_convergence_score()

**File:** `ccya/engine/_pacing.py`

**What:** Add new function after `derive_allowed_beat_types()`:

```python
def compute_convergence_score(
    scene_phase: str,
    thread_urgency_count: int,
    scene_age: int,
    recent_beats: list[dict],
    current_outcome: RulesOutcome | None,
    config: EngineConfig,
) -> int:
```

Implementation rules:
1. **Thread weight (+1):** `thread_urgency_count >= 1`. Capped at 1.
2. **Urgency depth (+1):** `thread_urgency_count >= 2`. Additive — 2+ threads = +2 total.
3. **Scene age (+1):** `scene_age >= config.scene_pressure_threshold` (default 3).
4. **Beat streak (+1):** Of last 5 entries in `recent_beats`, count those whose `type` is in `BEAT_BUCKETS["pressure"]`. Streak threshold: if `len(recent_beats) < 5`, use `ceil(len(recent_beats) * 0.6)`. Else use 3. Pending beat (current turn) is never in `recent_beats`.
5. **Dice weight (+1):** `current_outcome` is not None and `current_outcome.rolled is True` and `current_outcome.band in ("crit_fail", "fail")` and `thread_urgency_count >= 1`.

Return sum (0-5). No negative scores.

**Import:** Add `from ccya.models import RulesOutcome` to `_pacing.py`. Add `from math import ceil`.

**Why:** Composite signal more robust than any single proxy. Five independent systems must agree before CLIMAX fires. Design invariant: score cannot reach threshold 3 without at least one urgent thread.

**Validation:** Write a test script to `/tmp/test_convergence.py`:
```python
import sys; sys.path.insert(0, ".")
from ccya.engine._pacing import compute_convergence_score
from ccya.engine.config import EngineConfig
from ccya.models import RulesOutcome

cfg = EngineConfig()
# 0 urgent threads, age 0, no beats, no roll → score 0
assert compute_convergence_score("RISING", 0, 0, [], None, cfg) == 0
# 1 urgent, age 3, no beats, no roll → score 2 (thread + age)
assert compute_convergence_score("RISING", 1, 3, [], None, cfg) == 2
# 2 urgent, age 3, no beats, no roll → score 3 (thread + depth + age) → CLIMAX
assert compute_convergence_score("RISING", 2, 3, [], None, cfg) >= 3
# 1 urgent, age 3, 3 pressure beats in last 5 → score 3 (thread + age + streak)
beats = [{"type": "pressure"}] * 3
assert compute_convergence_score("RISING", 1, 3, beats, None, cfg) >= 3
# 1 urgent, age 0, no beats, fail roll → score 2 (thread + dice)
outcome = RulesOutcome(rolled=True, band="fail")
assert compute_convergence_score("RISING", 1, 0, [], outcome, cfg) == 2
print("ALL PASS")
```

#### Step 3.2 — Wire convergence score into phase machine

**File:** `ccya/engine/turn.py` — `_compute_scene_phase()` at line 503

**What:**
- Add `convergence_score: int` parameter to `_compute_scene_phase` signature.
- Replace the RISING→CLIMAX transition block (Phase 2 removed the old tension_delta checks, leaving an empty RISING branch):
```python
elif phase == "RISING":
    if convergence_score >= config.convergence_threshold:
        phase = "CLIMAX"
        climax_turn_count = 1
```
- Keep the CLIMAX→RESOLUTION, RESOLUTION→BREATHER/SETUP, BREATHER→RISING transitions unchanged.
- Keep the SETUP→RISING transition unchanged (uses `thread_urgency_count > 0`).

**Why:** Score-driven CLIMAX entry replaces old binary urgency + tension_delta checks.

**Validation:** After implementation, `make check` (will catch mypy issues).

#### Step 3.3 — Compute convergence score in narrate-setup block

**File:** `ccya/engine/turn.py` — narrate-setup block (lines 760-834)

**What:**
- After computing `thread_urgency_count` (lines 780-791) and `scene_age` from `ctx._ages`, compute convergence score using `compute_convergence_score()`.
- Import `compute_convergence_score` from `ccya.engine._pacing` at top of file (replace the removed `derive_enforce_relief` import).
- Wire as:
```python
from ccya.engine._pacing import compute_convergence_score

# ... after scene_age available ...
convergence_score = compute_convergence_score(
    scene_phase=scene_phase,
    thread_urgency_count=thread_urgency_count,
    scene_age=ctx._ages.get("scene_age", 0),
    recent_beats=state.get("meta", {}).get("recent_beats", []),
    current_outcome=ctx.outcome,
    config=config,
)
```
- Pass `convergence_score` to `_compute_scene_phase()` call (line 794).
- Store or log `convergence_score` — at minimum include in event dict.

**Why:** Score must be computed before phase machine runs each turn.

#### Step 3.4 — Log convergence score in event dict

**File:** `ccya/engine/turn.py` — event dict (lines 1365-1400)

**What:** Add `"convergence_score"` key to the `pacing_context` sub-dict. Also add component breakdown for EV debugging:
```python
"convergence_score": convergence_score,
```

**Why:** Enables EV checker tooling to validate convergence behavior post-implementation.

**Validation:** After running a turn (integration), check events.jsonl for the convergence_score field.

#### Step 3.5 — Remove Scene Imperative CRISIS turn-limit trigger

**File:** `ccya/engine/turn.py` — `_compute_narration_directive()` (lines 405-441)

**What:** Remove the CRISIS/CLIMAX turn-limit condition from the Scene Imperative trigger. After Phase 2, the remaining trigger is:
```python
if effective_scene_age >= scene_imperative_threshold:
    return "Scene Imperative"
```
The old `(scene_phase == "CRISIS" and crisis_turn_count >= crisis_turn_limit)` was already removed as part of the tension_delta cleanup. Confirm it's gone.

**Why:** Scene Imperative is now purely age-based. The CLIMAX hard cutoff at `climax_turn_limit` still forces RESOLUTION in the phase machine — Scene Imperative no longer needs to duplicate that signal.

**Validation:** `grep -n 'climax_turn_limit\|scene_phase.*CLIMAX' ccya/engine/turn.py` in `_compute_narration_directive` — should show no trigger based on phase.

### Tests to write or update

Write standalone convergence test (Step 3.1 validation). Run `make check` at Phase 4 completion.
