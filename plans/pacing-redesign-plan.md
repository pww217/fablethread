# Pacing Redesign — Implementation Plan

**Design Reference:** [docs/design/pacing-redesign-design.md](../design/pacing-redesign-design.md)
**Roadmap:** [roadmap/features/F-28-pacing-redesign-convergence-smoothing-hysteresis-phase-minimums-spiral-removal.md](../roadmap/features/F-28-pacing-redesign-convergence-smoothing-hysteresis-phase-minimums-spiral-removal.md)
**Ticket:** F-28

## Summary

Three phases to replace the volatile convergence-based pacing system with EMA smoothing, hysteresis thresholds, configurable phase minimums, and spiral detection removal. Phase 1 removes spiral detection (no dependencies). Phase 2 overhauls convergence scoring (EMA + urgent_thread cap + stall floor removal). Phase 3 adds hysteresis and phase minimums (depends on Phase 2 for config changes). Each phase is independently executable and verifiable.

---

## Phase 1: Spiral Removal

**Scope:** Remove `detect_spiral()`, `spiral_detected` from all data structures, and all spiral-related config/checkers/UI.

### 01-1. Remove `detect_spiral()` from `_pacing.py`

- **File:** `ccya/engine/_pacing.py`
- **What:** Delete the `detect_spiral()` function (lines 33-58).
- **Why:** Spiral detection is being removed entirely per design.
- **Validation:** `_pacing.py` no longer contains `detect_spiral`; imports in other files will fail until updated (expected).

### 01-2. Remove `spiral_detected` from `PacingContext`

- **File:** `ccya/engine/turn_context.py`
- **What:** Delete `spiral_detected: bool = False` from `PacingContext` dataclass (line 47).
- **Why:** Spiral detection removed; no narrative signals needed.
- **Validation:** `PacingContext` has no `spiral_detected` field; mypy will flag usage sites.

### 01-3. Remove `_spiral_detected` from `TurnContext`

- **File:** `ccya/engine/turn_context.py`
- **What:** Delete `_spiral_detected: bool = False` from `TurnContext` dataclass (line 37).
- **Why:** Spiral detection removed; no internal tracking needed.
- **Validation:** `TurnContext` has no `_spiral_detected` field.

### 01-4. Remove spiral detection from `_narrate_setup()` in `narrate.py`

- **File:** `ccya/engine/narrate.py`
- **What:**
  - Remove `detect_spiral` from imports (line 15).
  - Remove `consecutive_low_convergence` tracking block (lines 216-230).
  - Remove `stall_floor` computation (lines 225-228).
  - Remove `total_convergence_score = _convergence_score + stall_floor` (line 230).
  - Remove spiral detection call and assignments (lines 251-257).
  - Change `total_convergence_score = _convergence_score` (raw score, no stall floor).
  - Add EMA smoothing logic after `compute_convergence_score()` call:
    1. Read `state.meta.smoothed_convergence` (exists if not first turn).
    2. If not exists (first turn), set `smoothed_convergence = raw_score`.
    3. If exists, compute `smoothed_convergence = config.convergence_alpha * raw_score + (1 - config.convergence_alpha) * prev_smoothed`.
    4. Store back to `state.meta.smoothed_convergence`.
  - Use `smoothed_convergence` for all threshold comparisons and phase transitions going forward.
- **Why:** Spiral detection and stall floor removed; EMA smoothing replaces both.
- **Validation:** `_narrate_setup()` no longer references `detect_spiral`, `stall_floor`, or `consecutive_low_convergence`; uses `smoothed_convergence` for phase transition logic.

### 01-5. Remove `spiral_detected` parameter from `derive_allowed_beat_types()`

- **File:** `ccya/engine/_pacing.py`
- **What:** Change signature from `def derive_allowed_beat_types(scene_phase, *, directive="", spiral_detected=False)` to `def derive_allowed_beat_types(scene_phase, *, directive="")`. Remove the spiral branch in the function body (lines 79-81). Retain the Scene Imperative directive branch (lines 74-75) and fallback (lines 77-83).
- **Why:** Spiral detection removed; spiral branch no longer needed.
- **Validation:** Function signature has no `spiral_detected`; calling with `spiral_detected=` will raise TypeError.

### 01-6. Update `derive_allowed_beat_types()` call sites

- **Files:** `ccya/engine/world.py` (line 52), `ccya/engine/turn.py` (line 426), `ccya/server/tv.py` (lines 283-288)
- **What:**
  - `world.py:52`: Drop `spiral_detected=pacing_context.spiral_detected if pacing_context else False`.
  - `turn.py:426`: Drop `spiral_detected=_pc.spiral_detected if _pc else False`.
  - `tv.py:283-288`: Remove the `spiral_detected` display block from `_tv_state_diff()`.
- **Why:** Function no longer accepts `spiral_detected`; UI no longer displays it.
- **Validation:** No `spiral_detected=` keyword argument in any `derive_allowed_beat_types()` call; tv.py no longer references `spiral_detected`.

### 01-7. Remove spiral from event logging in `turn.py`

- **File:** `ccya/engine/turn.py`
- **What:** Remove `"spiral_detected": _pc.spiral_detected if _pc else False` from the `pacing_context` dict in the event (line 413).
- **Why:** Spiral detection removed from PacingContext.
- **Validation:** Event `pacing_context` no longer contains `spiral_detected`.

### 01-8. Remove spiral config fields from `EngineConfig`

- **File:** `ccya/engine/config.py`
- **What:** Delete `spiral_consecutive_hard: int = 3` and `spiral_hard_ratio: tuple[int, int] = (3, 5)` from `EngineConfig` dataclass (lines 178-179).
- **Why:** Spiral detection removed; config fields unused.
- **Validation:** `EngineConfig` has no spiral fields; mypy will flag usage.

### 01-9. Remove `spiral_detection` checker

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:** Delete the entire `spiral_detection` checker function (lines 457-529).
- **Why:** Spiral detection removed; checker no longer relevant.
- **Validation:** `pacing_convergence.py` no longer contains `spiral_detection`; `@register_checker("spiral_detection", ...)` removed.

### 01-10. Remove spiral from `directive_beat_alignment` checker

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:**
  - Drop `spiral_detected=pacing_ctx.get("spiral_detected", False)` from `derive_allowed_beat_types()` call (line 571).
  - Remove spiral-specific assertion block (lines 594-603).
- **Why:** Spiral detection removed; checker no longer validates spiral behavior.
- **Validation:** `directive_beat_alignment` no longer references `spiral_detected`.

### 01-11. Remove spiral from `beat_phase_validity` checker

- **File:** `ccya/ev/checkers/beat_phase_validity.py`
- **What:** Drop `spiral_detected=pacing_ctx.get("spiral_detected", False)` from `derive_allowed_beat_types()` call (line 49).
- **Why:** Spiral detection removed; checker no longer validates spiral behavior.
- **Validation:** `beat_phase_validity` no longer references `spiral_detected`.

### 01-12. Update documentation

- **Files:** `docs/architecture/pacing-systems.md`, `docs/repomap.md`
- **What:**
  - Remove all references to `spiral_detected`, `detect_spiral()`, `spiral_consecutive_hard`, `spiral_hard_ratio` from pacing-systems.md.
  - Update code locations table in pacing-systems.md (remove spiral-related entries).
  - Update repomap.md pacing system description.
- **Why:** Stale docs are bugs per AGENTS.md.
- **Validation:** No mentions of "spiral" remain in architecture docs or repomap.

---

## Phase 2: Convergence Scoring Overhaul (EMA + Urgent Thread Cap + Stall Floor Removal)

**Scope:** Implement EMA smoothing on convergence score, change urgent_thread component from binary 0/2 to count-capped 0/1/2, remove stall floor and consecutive_low_convergence tracking, add new config fields.

### 02-1. Add new config fields to `EngineConfig`

- **File:** `ccya/engine/config.py`
- **What:**
  - **Remove:** `convergence_threshold: int = 3` (line 162), `stall_floor_max: int = 3` (line 166).
  - **Add:** `convergence_enter_threshold: int = 3`, `convergence_exit_threshold: int = 1`, `convergence_alpha: float = 0.4`, `RISING_min: int = 3`, `CLIMAX_min: int = 3`, `BREATHER_min: int = 2`.
  - **Kept (internal use only):** `climax_turn_limit: int = 4`, `breather_max_turns: int = 3`.
- **Why:** New pacing system uses hysteresis thresholds, EMA alpha, and configurable phase minimums.
- **Validation:** `EngineConfig` has new fields with correct defaults; old fields removed.

### 02-2. Update `build_engine_config()` for new config keys

- **File:** `ccya/engine/config.py`
- **What:**
  - Read `convergence_alpha`, `convergence_enter_threshold`, `convergence_exit_threshold` from pack config (with defaults 0.4, 3, 1).
  - Read `RISING_min`, `CLIMAX_min`, `BREATHER_min` from pack config (with defaults 3, 3, 2).
  - Add deprecation warnings for old keys: `convergence_threshold`, `climax_turn_limit`, `breather_max_turns` in pack config.
  - Remove `convergence_threshold` and `stall_floor_max` from the EngineConfig constructor call.
- **Why:** Pack config needs to support new fields; old keys need migration warnings.
- **Validation:** `build_engine_config()` reads new keys; emits warnings for old keys; constructs EngineConfig with new fields.

### 02-3. Change `urgent_thread` component from binary to count-capped

- **File:** `ccya/engine/_pacing.py`
- **What:** In `compute_convergence_score()`, change component 1 (urgent_thread) from binary `+2 if any_urgent else 0` to count-capped `min(urgent_count, 2)`.
  - Before: `any_urgent = any(t.urgency == "urgent" and not dormant for t in active_threads)` → `score += 2 if any_urgent else 0`.
  - After: `urgent_count = sum(1 for t in active_threads if t.urgency == "urgent" and not dormant)` → `contribution = min(urgent_count, 2)` → `score += contribution`, `components["urgent_thread"] = contribution`.
- **Why:** Makes the score more compositional — multiple signals need to agree for maximum contribution, reducing volatility.
- **Validation:** `compute_convergence_score()` returns components where `urgent_thread` is 0, 1, or 2 (not just 0 or 2).

### 02-4. Add EMA smoothing in `_narrate_setup()`

- **File:** `ccya/engine/narrate.py`
- **What:** After `compute_convergence_score()` call (line 204-213), add EMA smoothing logic:
  1. Read `state.meta.smoothed_convergence` (exists if not first turn).
  2. If not exists (first turn), set `smoothed_convergence = raw_score`.
  3. If exists, compute `smoothed_convergence = config.convergence_alpha * raw_score + (1 - config.convergence_alpha) * prev_smoothed`.
  4. Store back to `state.meta.smoothed_convergence`.
  5. Use `smoothed_convergence` for all threshold comparisons and phase transitions going forward (replace `total_convergence_score` usage).
- **Why:** EMA smoothing prevents single-turn volatility from causing phase transitions.
- **Validation:** `state.meta.smoothed_convergence` is set on first turn and updated each subsequent turn; phase transition logic uses smoothed value.

### 02-5. Remove stall floor and consecutive_low_convergence from `_narrate_setup()`

- **File:** `ccya/engine/narrate.py`
- **What:**
  - Remove `consecutive_low_convergence` tracking block (lines 216-223).
  - Remove `stall_floor` computation (lines 225-228).
  - Remove `_convergence_components["stall_floor"] = stall_floor` (line 228).
  - Change `total_convergence_score = _convergence_score + stall_floor` to use `smoothed_convergence` instead (computed in 02-4).
  - Remove `state.setdefault("meta", {}).pop("consecutive_low_convergence", None)` on cancel/retry (line 154).
- **Why:** Stall floor and consecutive_low_convergence are redundant with EMA smoothing; removed per design.
- **Validation:** `_narrate_setup()` no longer references `stall_floor`, `consecutive_low_convergence`, or `clc`.

### 02-6. Update `convergence_recompute` checker for new urgent_thread scoring

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:** In `convergence_recompute()`, change component 1 from `components["urgent_thread"] = 2 if any_urgent else 0` to `components["urgent_thread"] = min(urgent_count, 2)` where `urgent_count = sum(1 for t in convergence_threads if t.urgency == "urgent" and not dormant)`.
- **Why:** Checker must match new scoring logic.
- **Validation:** `convergence_recompute` recomputes `urgent_thread` as 0/1/2 matching engine behavior.

### 02-7. Remove `stall_floor_computation` checker

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:** Delete the entire `stall_floor_computation` checker function (lines 313-384).
- **Why:** Stall floor removed; checker no longer relevant.
- **Validation:** `pacing_convergence.py` no longer contains `stall_floor_computation`.

### 02-8. Update `convergence_recompute` checker — remove stall_floor from score computation

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:** In `convergence_recompute()`, remove `stored_stall_floor = raw_components.get("stall_floor", 0)` and `expected_score = sum(components.values()) + stored_stall_floor`. Change to `expected_score = sum(components.values())`.
- **Why:** Stall floor removed from scoring; checker must not add it.
- **Validation:** `convergence_recompute` computes expected score as sum of 6 components only (no stall_floor).

### 02-9. Update documentation

- **Files:** `docs/architecture/pacing-systems.md`, `docs/repomap.md`, `AGENTS.md`
- **What:**
  - Update convergence score description in pacing-systems.md: 6 components (urgent_thread 0/1/2, no stall_floor), EMA smoothing explained.
  - Update config reference table: remove `convergence_threshold`, `stall_floor_max`; add `convergence_alpha`, `convergence_enter_threshold`, `convergence_exit_threshold`, `RISING_min`, `CLIMAX_min`, `BREATHER_min`.
  - Update repomap.md pacing system description.
- **Why:** Stale docs are bugs per AGENTS.md.
- **Validation:** Documentation reflects new scoring formula and config keys.

---

## Phase 3: Hysteresis + Phase Minimums

**Scope:** Replace single `convergence_threshold` with enter/exit thresholds, add min_turns gates before transition checks, update phase transition logic in `_compute_scene_phase()`.

### 03-1. Update `_compute_scene_phase()` with hysteresis and min_turns gates

- **File:** `ccya/engine/_pacing.py`
- **What:**
  - **RISING→CLIMAX (line 299):** Change `total_convergence_score >= config.convergence_threshold` to `smoothed_convergence >= config.convergence_enter_threshold AND turns_in_phase >= config.RISING_min`.
  - **CLIMAX→RESOLUTION early exit (line 312):** Change `total_convergence_score < 2` to `smoothed_convergence < config.convergence_exit_threshold AND turns_in_phase >= config.CLIMAX_min`.
  - **CLIMAX hard cap:** Keep existing logic but use `smoothed_convergence` instead of `total_convergence_score` for the convergence checks (lines 323, 323).
  - **BREATHER→RISING:** Add min_turns gate: `turns_in_phase >= config.BREATHER_min` in addition to existing urgent thread / breather_max_turns conditions.
  - Note: `smoothed_convergence` is passed into `_compute_scene_phase()` — update the function signature to accept it as a parameter (or read from state).
- **Why:** Hysteresis prevents flip-flopping; min_turns prevents premature transitions.
- **Validation:** Phase transitions respect enter/exit thresholds and minimum turn counts.

### 03-2. Update `_compute_pacing_context()` for new threshold names

- **File:** `ccya/engine/_pacing.py`
- **What:** Change `config.convergence_threshold` to `config.convergence_enter_threshold` in the outcome_hint gate (line 227).
- **Why:** Old config key removed; hysteresis uses enter threshold for forward transitions.
- **Validation:** `_compute_pacing_context()` uses `convergence_enter_threshold`.

### 03-3. Pass smoothed_convergence into `_compute_scene_phase()`

- **File:** `ccya/engine/_pacing.py`
- **What:** Update `_compute_scene_phase()` signature to accept `smoothed_convergence: float = 0` parameter. Update the caller in `_narrate_setup()` to pass `smoothed_convergence` instead of `total_convergence_score`.
- **Why:** Phase transition logic needs the smoothed value, not the raw total.
- **Validation:** `_compute_scene_phase()` receives and uses `smoothed_convergence` for all threshold comparisons.

### 03-4. Update `phase_transition_signals` checker for new transition logic

- **File:** `ccya/ev/checkers/pacing_convergence.py`
- **What:**
  - Update CLIMAX→RESOLUTION early exit check: use `convergence_exit_threshold` (default 1) instead of hardcoded `< 2`.
  - Update RISING→CLIMAX check: add min_turns gate (`turns_in_phase >= RISING_min`, default 3).
  - Update BREATHER→RISING check: add min_turns gate (`breather_turn_count >= BREATHER_min`, default 2).
  - Note: The checker reads `EngineConfig()` defaults; new config fields will be picked up automatically.
- **Why:** Checker must validate new transition logic.
- **Validation:** `phase_transition_signals` checker validates transitions against hysteresis thresholds and min_turns gates.

### 03-5. Update documentation

- **Files:** `docs/architecture/pacing-systems.md`, `docs/repomap.md`
- **What:**
  - Update phase transition table in pacing-systems.md with hysteresis thresholds and min_turns gates.
  - Update config reference table with new keys and defaults.
  - Update repomap.md pacing system description.
  - Update `_compute_scene_phase()` code locations table.
- **Why:** Stale docs are bugs per AGENTS.md.
- **Validation:** Documentation fully reflects hysteresis and min_turns behavior.

---

## Dependency Order

```
Phase 1 (spiral removal)
  └─ Phase 2 (convergence overhaul)
       └─ Phase 3 (hysteresis + phase minimums)
```

- Phase 1 has no dependencies.
- Phase 2 depends on Phase 1 (both modify `_narrate_setup()` in `narrate.py`; Phase 1 removes spiral/stall_floor, Phase 2 adds EMA).
- Phase 3 depends on Phase 2 (both modify `EngineConfig` and `_pacing.py`; Phase 2 adds new config fields, Phase 3 uses them).

---

## Documentation Updates (across all phases)

| Doc | Changes |
|-----|---------|
| `docs/architecture/pacing-systems.md` | Remove spiral references; update convergence score formula (6 components, urgent_thread 0/1/2, no stall_floor); add EMA smoothing explanation; update phase transition table with hysteresis/min_turns; update config reference table |
| `docs/repomap.md` | Update pacing system description; update code locations tables |
| `AGENTS.md` | No changes needed (build/lint commands unchanged) |

---

## Done when

- All 3 phases complete with clear verification steps.
- No references to `spiral_detected`, `detect_spiral`, `stall_floor`, `consecutive_low_convergence`, or `convergence_threshold` remain in source or docs.
- `make check` (lint + typecheck) passes.
- `docs/architecture/pacing-systems.md`, `docs/repomap.md` fully updated.
