# Pacing Redesign — EMA Smoothing, Hysteresis, Phase Minimums, Spiral Removal

## Problem Statement

The pacing system produces 10+ phase transitions in 15 turns (noir-1930s/driven 15t eval). The convergence score is 6 independent boolean components with no smoothing — a single urgent thread flips the score by 2 points. The same threshold triggers both RISING→CLIMAX and CLIMAX→RESOLUTION transitions with no hysteresis gap. Phase minimums are tracked (`turns_in_phase`) but never enforced before transition checks. Spiral detection creates a harmful feedback loop: death spiral → fewer pressure beats → lower convergence → harder to reach CLIMAX.

**Symptoms:**
- 10 phase transitions in 15 turns (SETUP→SETUP→RISING→CLIMAX→CLIMAX→RESOLUTION→BREATHER→RISING→CLIMAX→CLIMAX→CLIMAX→RESOLUTION→BREATHER→BREATHER→RISING)
- Peak action (gunfire, tackles, reinforcements) assigned RESOLUTION/BREATHER
- Convergence score oscillates: 4→1→4→5→4→2→0→0→1
- Beat phase violations: escalation during RESOLUTION, opportunity during RISING
- Spiral detection starves convergence when player is struggling

## Target State

The pacing system uses an exponential moving average for convergence, hysteresis thresholds for phase transitions, configurable minimum turns per phase, and removes spiral detection entirely. Pack configuration uses direct pacing knobs (`convergence_alpha`, `RISING_min`, `CLIMAX_min`, `BREATHER_min`) instead of an archetype abstraction.

## Decisions

### 1. Convergence Scoring

**Exponential moving average** applied to raw scores before threshold comparison.

- One persisted float on `state.meta.smoothed_convergence`, initialized to raw score on first turn, then updated as `alpha * raw + (1 - alpha) * prev_smoothed`
- Alpha is pack-configurable (`convergence_alpha`, default 0.4), allowing aggressive packs to make the signal more responsive
- Smoothing happens in `_narrate_setup()` (the caller of `compute_convergence_score()`), not inside the function
- Function contract unchanged: `compute_convergence_score()` still returns `(raw_score, components_dict)`
- Smoothed score flows into `_compute_scene_phase()` and `PacingContext.convergence_score`

**`urgent_thread` component becomes count-capped:**
- Current: binary `+2` if any urgent thread exists
- New: `min(urgent_count, 2)` contributing 0/1/2
- This makes the score more compositional — multiple signals need to agree for maximum contribution, reducing volatility from thread urgency swings

**Component weights after change:**

| Component | Current | New |
|-----------|---------|-----|
| urgent_thread | 0/2 | 0/1/2 (capped at 2) |
| threat_thread | 0/1 | 0/1 (unchanged) |
| scene_age | 0/1 | 0/1 (unchanged) |
| beat_streak | 0/1 | 0/1 (unchanged) |
| roll_starvation | 0/1 | 0/1 (unchanged) |
| threat_density | 0/1 | 0/1 (unchanged) |
| **Total raw** | **0-7** | **0-7** |

**Stall floor removed.** The EMA already handles consecutive low-score recovery — the `consecutive_low_convergence` counter and `stall_floor_max` config are redundant smoothing mechanisms. Removing `stall_floor`, `consecutive_low_convergence`, and `stall_floor_max`.

### 2. Hysteresis

**`convergence_threshold` replaced by two keys:**
- `convergence_enter_threshold` (default 3) — threshold for entering RISING→CLIMAX
- `convergence_exit_threshold` (default 1) — threshold for CLIMAX→RESOLUTION early exit
- Gap of 2 between enter and exit prevents flip-flopping

**Interaction with smoothed score:**
- All threshold comparisons use the smoothed score, not raw
- The `_compute_pacing_context()` outcome_hint gate (line 227 in `_pacing.py`) uses `convergence_enter_threshold` — if smoothed score meets the enter threshold, the narrator is instructed to transition

### 3. Phase Minimums

**All phases get a `turns_in_phase >= min_turns` gate before convergence check.**

**Direct pack config values (no archetype abstraction):**
- `RISING_min` (default 3) — minimum turns in RISING before RISING→CLIMAX transition is checked
- `CLIMAX_min` (default 3) — minimum turns in CLIMAX before CLIMAX→RESOLUTION transition is checked
- `BREATHER_min` (default 2) — minimum turns in BREATHER before BREATHER→RISING transition is checked
- SETUP and RESOLUTION stay at 1 always (transition phases, not sustained states) — not configurable

**Ceiling values remain on `EngineConfig` for internal use:**
- `climax_turn_limit` (default 4) — max turns in CLIMAX before forced RESOLUTION
- `breather_max_turns` (default 3) — max turns in BREATHER before forced RISING

Gap is always 1 between min and ceiling — tight but sufficient. One turn where the phase can exit naturally before the hard cap forces it.

**Old keys deprecated with warning:**
- `convergence_threshold` in pack config → use `convergence_enter_threshold` and `convergence_exit_threshold`
- `climax_turn_limit` and `breather_max_turns` in pack config → use `pacing_archetype` or remove (engine defaults to medium values)

### 4. Spiral Removal

**`detect_spiral()` deleted** — pacing should not balance difficulty. Spiral detection creates a harmful feedback loop: bad rolls → fewer pressure beats → lower convergence → harder to transition.

**Changes:**
- `spiral_detected` removed from `PacingContext`
- `derive_allowed_beat_types()` loses `spiral_detected` parameter; Scene Imperative override branch retained
- `spiral_consecutive_hard` and `spiral_hard_ratio` removed from `EngineConfig`
- `narrate.py`: remove import, remove `_spiral_detected` assignment, remove `_pc.spiral_detected` assignment

**Note:** Pressure beats will no longer be suppressed by spiral detection. This is acceptable because the EMA smoothing + hysteresis prevents the harmful oscillation that spiral detection was trying to address.

### 5. Guards (Already Done)

**`world.py` purge loop** now filters against `allowed_beat_types` post-Pydantic, logs `world.beat_phase_violation`.

**`ruling.py` re-validates** selected beat type, logs `ruling.beat_phase_violation`, treats violation as missing beat.

### 6. EV Checkers

**`gm_beat_lifecycle`:** No change needed. Already reads `last_turn_state.meta.pending_gm_beat` correctly.

**`beat_phase_validity`:** One-line fix — drop `spiral_detected=pacing_ctx.get("spiral_detected", False)` from `derive_allowed_beat_types()` call.

**`directive_beat_alignment`:** Drop `spiral_detected` parameter from `derive_allowed_beat_types()` call and remove spiral-specific assertion (lines 594-603).

**`spiral_detection`:** Remove entirely — no longer relevant.

**`pacing_directives`:** No signal fields to update (narrative signals removed).

## What's Unchanged

- `compute_convergence_score()` function contract (still returns `(int, dict[str, int])`)
- `BEAT_PHASE_MAP` and `BEAT_BUCKETS` constants
- `_compute_narration_directive()` — Scene Imperative / Scene Pressure logic unchanged
- `_compute_pacing_context()` — directive logic unchanged; outcome_hint gate uses `convergence_enter_threshold` instead of `convergence_threshold`; no longer sets `spiral_detected`
- `_compute_scene_phase()` — transition logic unchanged (except threshold comparisons and min_turns gate)
- `_compute_ages()` — scene age computation unchanged
- `_recent_turn_count()` — unchanged
- `recent_beats` tracking in `ruling.py` — unchanged
- `pending_gm_beat` lifecycle — unchanged
- `curtain_call` logic — unchanged

## Interface Changes

### `EngineConfig` (ccya/engine/config.py)

**Removed:**
- `convergence_threshold: int = 3`
- `spiral_consecutive_hard: int = 3`
- `spiral_hard_ratio: tuple[int, int] = (3, 5)`
- `stall_floor_max: int = 3`

**Added:**
- `convergence_enter_threshold: int = 3`
- `convergence_exit_threshold: int = 1`
- `convergence_alpha: float = 0.4`
- `RISING_min: int = 3`
- `CLIMAX_min: int = 3`
- `BREATHER_min: int = 2`

**Kept (internal use only, not set from pack config):**
- `climax_turn_limit: int` — remains for CLIMAX hard cap logic
- `breather_max_turns: int` — remains for BREATHER hard cap logic

### `PacingContext` (ccya/engine/turn_context.py)

**Removed:**
- `spiral_detected: bool = False`

**No new fields added** — narrative signals removed (entry/exit signals don't carry enough weight to change LLM behavior reliably).

### `state.meta` (runtime state)

**Added:**
- `smoothed_convergence: float` — EMA value, initialized to raw score on first turn, updated each turn

**Removed:**
- `consecutive_low_convergence: int` — replaced by EMA behavior
- `stall_floor` (stored in convergence_components) — removed entirely

### `derive_allowed_beat_types()` (ccya/engine/_pacing.py)

**Changed signature:**
```python
# Before
def derive_allowed_beat_types(
    scene_phase: str,
    *,
    directive: str = "",
    spiral_detected: bool = False,
) -> list[str]:

# After
def derive_allowed_beat_types(
    scene_phase: str,
    *,
    directive: str = "",
) -> list[str]:
```

**Call sites to update:**
- `world.py:49-53` — drop `spiral_detected=...`
- `turn.py:423-427` — drop `spiral_detected=...` (event logging)
- `ruling.py:260` — drop `spiral_detected=...` (beat validation)
- `ccya/ev/checkers/beat_phase_validity.py:46-50` — drop `spiral_detected=...`
- `ccya/ev/checkers/pacing_convergence.py:568-572` — drop `spiral_detected=...`
- `ccya/server/tv.py:283-287` — remove spiral_detected display in turn viewer UI

### `_compute_scene_phase()` (ccya/engine/_pacing.py)

**Changed:**
- Uses `config.convergence_enter_threshold` instead of `config.convergence_threshold` for RISING→CLIMAX transition (line 299)
- Uses `config.convergence_exit_threshold` for CLIMAX→RESOLUTION early exit (line 312)
- Adds min_turns gate before convergence check: `turns_in_phase >= config.RISING_min` for RISING→CLIMAX, `turns_in_phase >= config.CLIMAX_min` for CLIMAX→RESOLUTION
- Signature unchanged

### `_compute_pacing_context()` (ccya/engine/_pacing.py)

**Changed:**
- Uses `config.convergence_enter_threshold` instead of `config.convergence_threshold` for outcome_hint gate (line 227)
- No longer sets `spiral_detected`
- No longer computes phase signals (removed)

### `_narrate_setup()` (ccya/engine/narrate.py)

**Changed:**
- EMA smoothing logic added after `compute_convergence_score()` call:
  1. Read `state.meta.smoothed_convergence` (exists if not first turn)
  2. If not exists (first turn), set `smoothed_convergence = raw_score`
  3. If exists, compute `smoothed_convergence = config.convergence_alpha * raw_score + (1 - config.convergence_alpha) * prev_smoothed`
  4. Store back to `state.meta.smoothed_convergence`
  5. Use `smoothed_convergence` for all threshold comparisons and phase transitions
- `consecutive_low_convergence` tracking removed (replaced by EMA behavior)
- Spiral detection removed (import, assignment, `_pc.spiral_detected` assignment)

### `build_engine_config()` (ccya/engine/config.py)

**Changed:**
- Reads `convergence_alpha`, `convergence_enter_threshold`, `convergence_exit_threshold` from pack config (with defaults)
- Reads `RISING_min`, `CLIMAX_min`, `BREATHER_min` from pack config (with defaults)
- Deprecation warning for old keys (`convergence_threshold`, `climax_turn_limit`, `breather_max_turns` in pack config)

## Open Questions

None. All decisions are firm.
