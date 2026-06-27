# Convergence Proactive — Pacing Engine Reform

## Purpose

Replace the 5-component reactive convergence score with 7 components (6 boolean + 1 integer floor) that prevent RISING→CLIMAX deadlock, and replace the hard 4-turn CLIMAX→RESOLUTION cap with a signal-gated exit (early exit on thread resolution, extension on sustained pressure, hard cap at 6 turns). Also remove dead `avoidance_keywords` config field and `dice_weight` convergence component.

## Problem Statement

`compute_convergence_score()` in `_pacing.py:86-142` computes a 5-component score that is entirely reactive. Each component depends on state that can remain 0 indefinitely under stealth/avoidance-heavy play styles. The phase machine requires `convergence_score >= 2` for `RISING → CLIMAX`, but when all 5 components are 0, there is no recovery mechanism — convergence deadlocks.

Separately, **CLIMAX → RESOLUTION** is a pure turn-count timeout (default 4 turns). No engine signal can exit early or extend.

## Design Reference

`docs/design/convergence-proactive-design.md` (status: reviewed, second pass 2026-06-25)

## Constraints

- **Zero behavioral change to unchanged paths.** SETUP→RISING (3-turn TTL), RESOLUTION→BREATHER (1 turn), BREATHER→RISING (3-turn TTL) remain identical.
- **`avoidance_keywords` removal is safe** — `rg` confirms only `config.py` references it (field at 146, deserialization at 280). No templates, routes, or YAML consumers.
- **`dice_weight` removal is safe** — only referenced in `_pacing.py` (lines 133-140) and `narrate.py` (lines 256-261). Both being rewritten.
- **Tests temporarily disabled** per AGENTS.md lint workflow rules. Run `make check` (lint + typecheck) as a final step after all phases complete.

## Firm Decisions

1. **Early-exit signal sources from state, not in-flight storyteller_result.** `thread_resolved_prev_turn = any(ct for ct in state["arc"]["completed_threads"] if ct.get("resolved_turn") == turn_no - 1)`. One-turn delay consistent with existing RISING→CLIMAX pattern.
2. **`has_urgent_active_thread` filters dormant threads explicitly.** Do NOT copy existing `_pacing.py:249-253` `thread_urgency_count` pattern (which does not filter dormant).
3. **`stall_floor` is global across BREATHER→RISING cycles.** Counter not reset on new RISING phase. Resets on reaching threshold (= RISING→CLIMAX) or on cancel/retry.
4. **`compute_convergence_score` returns `(score, components_dict)`** to eliminate the narrate.py mirror (design suggestion #1). Removes ~30 lines of duplicated logic and the entire class of mirror-drift bugs.
5. **`beat_streak` repair:** When a beat entry has `type=None`, carry over the type from the chronologically previous non-null entry in the window.
6. **Prompt template changes:** Strengthen `curtain_call` in narrator prompt (CLIMAX prose resolution nudge) and add light storyteller nudge for `thread_resolve` emission. No other prompt templates touched.

## Risks, Ambiguities, and Blockers

All resolved in design doc review (second pass, 2026-06-25). No open blockers.

## Status

`completed`

---

# Phases: 7 phases — config, core convergence, phase machine, state tracking, narrate refactor, prompts, doc updates

---

## Implementation — Phase 1: EngineConfig changes (add fields, remove dead code)

### Context files to load
- `ccya/engine/config.py` (EngineConfig dataclass lines 101-194, build_engine_config lines 205-311)

### Detailed steps

#### Step 1.1 — Remove `avoidance_keywords` from EngineConfig dataclass

**File:** `ccya/engine/config.py`

**What:** Delete line 147:
```python
avoidance_keywords: list[str] = field(default_factory=lambda: ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])
```

**Why:** Dead code — defined, populated from config, never consumed anywhere. Zero runtime references outside config.

**Validation:** Verify no external usage:
```bash
grep -rn 'avoidance_keywords' --include='*.py' ccya/ | grep -v '__pycache__' | grep -v 'config.py'
# Expected: no matches
```

#### Step 1.2 — Remove `avoidance_keywords` from `build_engine_config` deserialization

**File:** `ccya/engine/config.py`

**What:** Delete line 282:
```python
avoidance_keywords=[str(kw) for kw in game.get("avoidance_keywords", ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])],
```

**Why:** Matches the dataclass field removal above. No YAML consumers exist.

#### Step 1.3 — Add new config fields to EngineConfig dataclass

**File:** `ccya/engine/config.py`

**What:** Add these fields to `EngineConfig` (group with existing pacing thresholds around lines 157-163):
```python
# New convergence components
roll_starvation_threshold: int = 3    # turns without a roll before +1
threat_density_threshold: int = 3     # active threat threads before +1
stall_floor_max: int = 3              # cap on stall floor extra score
# CLIMAX extension
extension_max: int = 2               # max additional CLIMAX turns beyond climax_turn_limit
```

**Why:** Required by new convergence components (roll_starvation, threat_density, stall_floor) and CLIMAX extension logic.

#### Step 1.4 — Add deserialization for new config fields in `build_engine_config`

**File:** `ccya/engine/config.py`

**What:** Add to the `EngineConfig(...)` constructor call (group with existing pacing thresholds around lines 287-291):
```python
roll_starvation_threshold=int(game.get("roll_starvation_threshold", 3)),
threat_density_threshold=int(game.get("threat_density_threshold", 3)),
stall_floor_max=int(game.get("stall_floor_max", 3)),
extension_max=int(game.get("extension_max", 2)),
```

**Why:** Makes new config keys configurable via YAML. Falls back to design defaults.

---

## Implementation — Phase 2: Core convergence score — `compute_convergence_score()` in `_pacing.py`

### Context files to load
- `ccya/engine/_pacing.py` (compute_convergence_score lines 86-142, BEAT_BUCKETS lines 18-22)

### Detailed steps

#### Step 2.1 — Update `compute_convergence_score` signature

**File:** `ccya/engine/_pacing.py`

**What:** Change the function signature from:
```python
def compute_convergence_score(
    scene_phase: str,
    active_threads: list[dict[str, Any]],
    scene_age: int,
    recent_beats: list[dict[str, Any]],
    current_outcome: RulesOutcome | None,
    config: EngineConfig,
) -> int:
```
to:
```python
def compute_convergence_score(
    scene_phase: str,
    active_threads: list[dict[str, Any]],
    scene_age: int,
    recent_beats: list[dict[str, Any]],
    current_outcome: RulesOutcome | None,
    config: EngineConfig,
    turn_no: int,
    recent_rolls: list[dict[str, Any]],
) -> tuple[int, dict[str, int]]:
```

**Why:** `turn_no` required for `roll_starvation` component (computes `turns_since_last_roll`). `recent_rolls` required for `roll_starvation` component (computes `turns_since_last_roll = turn_no - recent_rolls[0]["turn"]`). Return type changes to `(score, components_dict)` to eliminate narrate.py mirror (design suggestion #1).

#### Step 2.2 — Rewrite function body: remove dice_weight, add 3 new components, repair beat_streak

**File:** `ccya/engine/_pacing.py`

**What:** Replace the entire function body (lines 101-141) with 6-component logic (stall_floor computed externally):

1. **Components 1-3 (UNCHANGED):** `any_urgent`, `any_threat`, `scene_age` — copy verbatim from current implementation.
2. **Component 4 (REPAIRED beat_streak):** Replace current beat_streak logic (lines 124-131) with carry-over logic:
    ```python
    pressure_types = set(BEAT_BUCKETS["pressure"])
    last_non_null_type = None
    pressure_count = 0
    for b in window:
        bt = b.get("type")
        if bt is not None:
            last_non_null_type = bt
        if last_non_null_type in pressure_types:
            pressure_count += 1
    threshold = ceil(n * 0.6) if n < 5 else 3
    if pressure_count >= threshold:
        score += 1
    ```
3. **Component 5 (NEW roll_starvation):**
    ```python
    turns_since_last_roll = turn_no - recent_rolls[0]["turn"] if recent_rolls else None
    if turns_since_last_roll is not None and turns_since_last_roll >= config.roll_starvation_threshold:
        score += 1
    ```
4. **Component 6 (NEW threat_density):**
    ```python
    active_threat_count = sum(1 for t in active_threads if t.get("type") == "threat" and not t.get("dormant", False))
    if active_threat_count >= config.threat_density_threshold:
        score += 1
    ```
5. **stall_floor is NOT computed here.** The design says: "State tracking: `meta.consecutive_low_convergence` (int, default 0), incremented in `narrate.py:_narrate_setup()` immediately after `compute_convergence_score()` returns, reset to 0 when `convergence_score >= convergence_threshold`." So stall_floor is computed at the call site in narrate.py, not inside `compute_convergence_score`. The function returns `score` (components 1-6) and `components_dict`. The caller computes stall_floor separately and adds it to the total.

6. **Remove dice_weight entirely** — delete lines 133-140.

7. **Return `(score, components_dict)`** where `components_dict` has keys: `urgent_thread`, `threat_thread`, `scene_age`, `beat_streak`, `roll_starvation`, `threat_density`. `stall_floor` is added by caller.

**Why:** Implements all 6 boolean components inside the core function. Removes dead `dice_weight`. Returns dict to eliminate narrate.py mirror.

#### Step 2.3 — Update docstring

**File:** `ccya/engine/_pacing.py`

**What:** Update docstring from "5-component" to "6-component" (stall_floor is computed externally). Fix threshold default from 3 to 2 (source default is `config.convergence_threshold` which defaults to 2).

**Before:**
```
"""Compute a 5-component convergence score for RISING→CLIMAX transition.
...
Threshold is config.convergence_threshold (default 3).
```

**After:**
```
"""Compute a 6-component convergence score for RISING→CLIMAX transition.
...
Threshold is config.convergence_threshold (default 2).
```

**Why:** Design notes (minor notes section) flag these docstring inaccuracies.

#### Step 2.4 — Update call site in `narrate.py`

**File:** `ccya/engine/narrate.py`

**What:** Update the call at lines 200-207 from:
```python
convergence_score = compute_convergence_score(
    scene_phase=scene_phase,
    active_threads=_raw_thread_dicts,
    scene_age=ctx._ages.get("scene_age", 0),
    recent_beats=state.get("meta", {}).get("recent_beats", []),
    current_outcome=ctx.outcome,
    config=config,
)
```
to:
```python
_convergence_score, _convergence_components = compute_convergence_score(
    scene_phase=scene_phase,
    active_threads=_raw_thread_dicts,
    scene_age=ctx._ages.get("scene_age", 0),
    recent_beats=state.get("meta", {}).get("recent_beats", []),
    current_outcome=ctx.outcome,
    config=config,
    turn_no=turn_no,
    recent_rolls=state.get("meta", {}).get("recent_rolls", []),
)
```

**Why:** New signature requires `turn_no` and `recent_rolls`. `turn_no` is already computed at line 153. `recent_rolls` is available from state.

---

## Implementation — Phase 3: Phase machine — `_compute_scene_phase()` in `_pacing.py`

### Context files to load
- `ccya/engine/_pacing.py` (_compute_scene_phase lines 222-294)

### Detailed steps

#### Step 3.1 — Update CLIMAX→RESOLUTION transition logic

**File:** `ccya/engine/_pacing.py`

**What:** Replace the CLIMAX block (lines 267-272) from:
```python
elif phase == "CLIMAX":
    climax_turn_count += 1
    if climax_turn_count >= config.climax_turn_limit:
        phase = "RESOLUTION"
        climax_turn_count = 0
        turns_in_phase = 0
```
to:
```python
elif phase == "CLIMAX":
    climax_turn_count += 1
    # Early exit — evaluated EVERY CLIMAX turn (not just at the limit).
    # Signal sourced from state (end-of-prior-turn), not in-flight storyteller_result.
    thread_resolved_prev_turn = any(
        ct for ct in (state.get("arc") or {}).get("completed_threads", [])
        if ct.get("resolved_turn") == turn_no - 1
    )
    if thread_resolved_prev_turn and total_convergence_score < 2:
        phase = "RESOLUTION"
        climax_turn_count = 0
        turns_in_phase = 0
    # Hard cap + extension — only evaluated at/after the limit
    elif climax_turn_count >= config.climax_turn_limit:
        # has_urgent_active_thread: explicit dormant filter (do NOT copy existing thread_urgency_count pattern)
        has_urgent_active_thread = any(
            t for t in (state.get("arc") or {}).get("threads") or []
            if isinstance(t, dict) and t.get("urgency") == "urgent" and not t.get("dormant", False)
        )
        if total_convergence_score >= 3 and has_urgent_active_thread:
            if climax_turn_count >= config.climax_turn_limit + config.extension_max:
                phase = "RESOLUTION"
                climax_turn_count = 0
                turns_in_phase = 0
            # else stay in CLIMAX (extension active)
        else:
            phase = "RESOLUTION"
            climax_turn_count = 0
            turns_in_phase = 0
    # else: stay in CLIMAX (below limit, no early-exit signal)
```

**Why:** Implements signal-gated CLIMAX→RESOLUTION exit per design. Early exit on thread resolution + low convergence. Extension on sustained pressure (convergence >= 3 + urgent active thread). Hard cap at `climax_turn_limit + extension_max` (6 turns).

**Note:** `turn_no` must be available in `_compute_scene_phase`. Currently the function signature is `_compute_scene_phase(state, ages, config, convergence_score)`. We need to add `turn_no: int` and rename `convergence_score` to `total_convergence_score` (see Step 3.2). The call site at `narrate.py:210` already has `turn_no` in scope.

#### Step 3.2 — Update `_compute_scene_phase` signature

**File:** `ccya/engine/_pacing.py`

**What:** Change signature from:
```python
def _compute_scene_phase(
    state: dict[str, Any],
    ages: dict[str, int],
    config: EngineConfig,
    convergence_score: int = 0,
) -> dict[str, Any]:
```
to:
```python
def _compute_scene_phase(
    state: dict[str, Any],
    ages: dict[str, int],
    config: EngineConfig,
    total_convergence_score: int = 0,
    turn_no: int = 0,
) -> dict[str, Any]:
```

**Why:** `turn_no` required for `thread_resolved_prev_turn` check (`resolved_turn == turn_no - 1`). Renamed `convergence_score` to `total_convergence_score` to distinguish from `_convergence_score` (components 1-6) computed in narrate.py before passing to this function.

#### Step 3.3 — Update call site in `narrate.py`

**File:** `ccya/engine/narrate.py`

**What:** Update call at line 210 from:
```python
state["scene"] = _compute_scene_phase(state, ctx._ages, config, convergence_score)
```
to:
```python
state["scene"] = _compute_scene_phase(state, ctx._ages, config, total_convergence_score, turn_no)
```

**Why:** New `turn_no` parameter required, and pass `total_convergence_score` (which includes stall_floor) instead of `convergence_score` (components 1-6 only).

#### Step 3.4 — Update docstring

**File:** `ccya/engine/_pacing.py`

**What:** Update docstring from "5-state machine" reference (no change needed — still 5 states) but update any references to "4-turn hard cap" to reflect signal-gated exit with hard cap at 6.

---

## Implementation — Phase 4: State tracking — `consecutive_low_convergence` in `narrate.py`

### Context files to load
- `ccya/engine/narrate.py` (lines 199-262, where convergence is computed and components mirrored)

### Detailed steps

#### Step 4.1 — Add stall_floor computation and consecutive_low_convergence tracking

**File:** `ccya/engine/narrate.py`

**What:** After the `compute_convergence_score` call (after line 207 in updated code), add:
```python
# Stall floor + consecutive_low_convergence tracking
meta = state.setdefault("meta", {})
clc = meta.get("consecutive_low_convergence", 0)
if _convergence_score < config.convergence_threshold:
    clc += 1
    meta["consecutive_low_convergence"] = clc
else:
    clc = 0
    meta.pop("consecutive_low_convergence", None)

# Compute stall_floor from clc
stall_floor = 0
if clc >= 3:
    stall_floor = min(1 + ((clc - 3) // 3), config.stall_floor_max)

# Add stall_floor to components dict and total score
_convergence_components["stall_floor"] = stall_floor
total_convergence_score = _convergence_score + stall_floor
```

Then use `total_convergence_score` where `convergence_score` was used for phase transition (line 210 already computed phase, but we need to pass `total_convergence_score` to `_compute_scene_phase` instead of `convergence_score`).

The updated flow in narrate.py should be:
```python
# Compute convergence (components 1-6)
_convergence_score, _convergence_components = compute_convergence_score(...)

# Stall floor + consecutive_low_convergence tracking
meta = state.setdefault("meta", {})
clc = meta.get("consecutive_low_convergence", 0)
if _convergence_score < config.convergence_threshold:
    clc += 1
    meta["consecutive_low_convergence"] = clc
else:
    clc = 0
    meta.pop("consecutive_low_convergence", None)

stall_floor = 0
if clc >= 3:
    stall_floor = min(1 + ((clc - 3) // 3), config.stall_floor_max)
_convergence_components["stall_floor"] = stall_floor

total_convergence_score = _convergence_score + stall_floor

# Compute phase (use total score)
state["scene"] = _compute_scene_phase(state, ctx._ages, config, total_convergence_score, turn_no)
```

**Why:** Implements stall_floor as a 7th component computed externally (per design). Tracks `consecutive_low_convergence` globally across BREATHER→RISING cycles. Resets on reaching threshold or on cancel/retry.

#### Step 4.2 — Update `PacingContext` convergence fields

**File:** `ccya/engine/narrate.py`

**What:** Update lines 232-262 (the convergence component mirror) to use `_convergence_components` directly instead of recomputing:
```python
# PacingContext convergence fields — use returned components dict directly
# (no mirror — eliminates duplicate logic and mirror-drift bugs)
_pc.convergence_score = total_convergence_score
_pc.convergence_components = _convergence_components
```

Delete the entire block at lines 234-262 (the 5-component mirror with `urgent_thread`, `threat_thread`, `scene_age`, `beat_streak`, `dice_weight`).

**Why:** `compute_convergence_score` now returns `components_dict`. No need to mirror. Eliminates ~28 lines of duplicated logic and the entire class of mirror-drift bugs (design suggestion #1).

#### Step 4.3 — Update `PacingContext` docstring

**File:** `ccya/engine/turn_context.py`

**What:** Update line 47 from:
```python
convergence_score: int = 0  # 5-component score for RISING→CLIMAX transition
```
to:
```python
convergence_score: int = 0  # convergence score for RISING→CLIMAX transition (6 components + stall_floor)
```

**Why:** Design notes flag this docstring inaccuracy.

---

## Implementation — Phase 5: Prompt templates — curtain_call strengthening

### Context files to load
- `ccya/prompts/narrate_user.j2` (curtain_call section at lines 43-45)
- `ccya/prompts/` directory for storyteller template location

### Detailed steps

#### Step 5.1 — Locate storyteller prompt template

**File:** `ccya/prompts/record_system.j2` (storyteller extraction template)

**What:** The storyteller template is `record_system.j2`. It contains `thread_resolve` guidance at lines 44-46 and curtain_call guidance at lines 76-80.

**Why:** Need to add light nudge for storyteller to emit `thread_resolve` in CLIMAX/RESOLUTION phases.

#### Step 5.2 — Strengthen curtain_call in narrator prompt

**File:** `ccya/prompts/narrate_user.j2`

**What:** The curtain_call is already rendered at lines 43-45 as `## Curtain Call: {{ curtain_call | upper }}`. Update to add guidance text that activates when `curtain_call` is `active` or `forced`:
```jinja2
{% if curtain_call and curtain_call != "" %}
## Curtain Call: {{ curtain_call | upper }}
{% if curtain_call == "active" %}
The main pressure thread should reach its conclusion this turn. Bring the climax home.
{% elif curtain_call == "forced" %}
FORCED: You must resolve the main pressure thread this turn. End the climax now.
{% endif %}
{% endif %}
```

**Why:** Strengthens existing `curtain_call` signal so narrator reliably resolves the climax thread in prose (design Templates section).

#### Step 5.3 — Add storyteller nudge for thread_resolve

**File:** `ccya/prompts/record_system.j2`

**What:** Add light guidance near `thread_resolve` emission instructions (around line 44, where `thread_resolve` guidance begins):
```
In CLIMAX or RESOLUTION phases, if the narrator has resolved the main pressure thread in the prose, record it as `thread_resolve` rather than `thread_update`. This helps the engine recognize natural endpoints.
```

**Why:** Secondary nudge ensures storyteller records thread resolutions the narrator made in prose (design Templates section).

---

## Implementation — Phase 6: Cancel/retry reset for `consecutive_low_convergence`

### Context files to load
- `ccya/engine/narrate.py` (`_narrate_setup` lines 149-281)
- `ccya/engine/turn.py` (cancel checks in `run_turn`)

### Detailed steps

#### Step 6.1 — Reset `consecutive_low_convergence` on cancel/retry

**File:** `ccya/engine/narrate.py`

**What:** At the start of `_narrate_setup`, before any convergence logic runs, add:
```python
# Reset consecutive_low_convergence on cancel/retry (design: resets on cancel/retry)
if is_cancel_requested(str(ctx.save_dir)):
    state.setdefault("meta", {}).pop("consecutive_low_convergence", None)
    return  # or continue after existing cancel check
```

Place this right after `state = ctx.state` and `config = ctx.config` (after line 151-152), before `turn_no` computation and before any convergence/stall_floor logic. This ensures `consecutive_low_convergence` is cleared before any new turn reads it, and is a single location where state is already available.

**Why:** Design says stall_floor counter "is also reset on cancel/retry." Placing at start of `_narrate_setup` is the cleanest single location — state is already available, no signature changes needed, and it runs before any convergence logic that would read `consecutive_low_convergence`.

**Validation:** Verify the reset happens before `_narrate_setup` reads `consecutive_low_convergence` (which happens after `compute_convergence_score` call).

---

## Implementation — Phase 7: Doc updates (AGENTS.md mandatory)

### Context files to load
- `docs/repomap.md` (module index, entry points)
- `docs/architecture/` (pipeline docs, data shapes)
- `ccya/engine/_pacing.py` (updated signatures)
- `ccya/engine/config.py` (updated EngineConfig)
- `ccya/engine/narrate.py` (updated call sites)

### Detailed steps

#### Step 7.1 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:** Update the following entries:
- `compute_convergence_score` signature: add `turn_no: int, recent_rolls: list[dict[str, Any]]` parameters, change return type from `int` to `tuple[int, dict[str, int]]`
- `_compute_scene_phase` signature: add `turn_no: int` parameter
- `EngineConfig` fields: remove `avoidance_keywords`, add `roll_starvation_threshold`, `threat_density_threshold`, `stall_floor_max`, `extension_max`
- `PacingContext` docstring: update from "5-component" to "convergence score (6 components + stall_floor)"

**Why:** AGENTS.md requires repomap updates for any function signature or config field changes.

#### Step 7.2 — Update `docs/architecture/` pipeline docs

**File:** `docs/architecture/` (relevant subdocs — `step2c-record.md`, `step2d-world.md`, `pacing-systems.md`, `state-models.md`, `OVERVIEW.md`)

**What:** Update documentation to reflect:
- 7-component convergence score (6 boolean + 1 integer floor)
- `stall_floor` computed externally from `consecutive_low_convergence`
- `consecutive_low_convergence` state field in `meta` (global across BREATHER→RISING, resets on threshold/cancel/retry)
- `roll_starvation` component sourced from `recent_rolls`
- `threat_density` component with dormant filter
- CLIMAX→RESOLUTION signal-gated exit (early exit on thread resolution, extension on sustained pressure, hard cap at 6)
- `turn_no` and `recent_rolls` as new parameters to `compute_convergence_score`

**Why:** AGENTS.md requires architecture doc updates for config keys, function signatures, and state model changes.

#### Step 7.3 — Update `docs/architecture/state-models.md` (or relevant state doc)

**File:** `docs/architecture/state-models.md` (or relevant state documentation)

**What:** Add `meta.consecutive_low_convergence` to the state model table:
| Field | Scope | Type | Owner |
|-------|-------|------|-------|
| `meta.consecutive_low_convergence` | Add | `int`, default 0 | `narrate.py` — updated every turn after convergence computed; reset on threshold reached or cancel/retry |

**Why:** New state field requires state model documentation.

---

## Tests to write or update

None — test suite is temporarily disabled per AGENTS.md lint workflow rules.

Run `make check` (lint + typecheck) as a final step after all 7 phases are complete, per AGENTS.md instructions.
