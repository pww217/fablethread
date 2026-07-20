---
title: "Convergence score uses raw instead of smoothed across all phase transitions"
status: done
urgency: 2
size: medium
created: 2026-07-19
ticket_id: B-51
labels: [pacing, convergence, smoothing]
design:
plan:
pr:
  url:
  branch:
---

## Description

The convergence score EMA smoothing is computed and persisted to `state.meta.smoothed_convergence`, but **all phase transitions use raw convergence instead of smoothed**. The smoothed value is effectively wasted — it's computed, stored, but never consumed by the phase engine or any decision logic.

**Resolved by I-42** (2026-07-20): All phase transitions now use smoothed convergence.

## Root Cause

In `ccya/engine/narrate.py`:

- **Line 197:** `_convergence_score` = raw 5-component sum from `compute_convergence_score()`
- **Line 207-208:** `smoothed_convergence` = EMA of raw score
- **Line 211:** `_compute_scene_phase(..., _convergence_score, ...)` — passes **raw** to phase engine
- **Line 224:** `convergence_score=int(smoothed_convergence)` — sets smoothed in PacingContext
- **Line 227:** `_pc.convergence_score = _convergence_score` — **overwrites with raw**

So `PacingContext.convergence_score` always contains raw, smoothed is only used for the outcome_hint hard gate in `_compute_pacing_context()`.

## Affected Phase Transitions (all use raw, should use smoothed)

### 1. SETUP→RISING (`_pacing.py:246`)

```python
if thread_urgency_count > 0 or turns_in_phase >= 3 or (total_convergence_score >= 2 and turns_in_phase >= 2):
```

Uses `total_convergence_score` (raw). With raw, a single spike of 2+ can flip to RISING immediately. Smoothed would require sustained pressure.

### 2. RISING→CLIMAX (`_pacing.py:252`)

```python
if total_convergence_score >= config.convergence_enter_threshold and turns_in_phase >= config.RISING_min:
```

Uses raw. A single turn with convergence >= 2 can trigger CLIMAX entry. Smoothed would prevent premature entry from transient spikes.

### 3. CLIMAX→RESOLUTION early exit (`_pacing.py:266`)

```python
if thread_resolved_prev_turn and total_convergence_score < config.convergence_exit_threshold and turns_in_phase >= config.CLIMAX_min:
```

Uses raw. If convergence drops to 1 on a single turn, CLIMAX exits immediately. Smoothed would require sustained pressure loss.

### 4. CLIMAX extension (`_pacing.py:278`)

```python
if total_convergence_score >= 3 and has_urgent_active_thread:
```

Uses raw. Extension requires raw >= 3, which is hard to sustain. Smoothed would allow extension when average pressure is high even if a single turn dips.

### 5. BREATHER→RISING (`_pacing.py:300`)

```python
if (thread_urgency_count > 0 or breather_turn_count >= config.breather_max_turns) and turns_in_phase >= config.BREATHER_min:
```

Doesn't directly use convergence, but the **design intent** for BREATHER was to use smoothed convergence for a clean break (I-42.2). Raw would be too jumpy for re-engagement decisions.

### 6. Convergence hard gate in `_compute_pacing_context()` (`_pacing.py:186`)

```python
if config and convergence_score >= config.convergence_enter_threshold and scene_phase in ("SETUP", "RISING"):
    outcome_hint = "transition"
```

Uses `convergence_score` from PacingContext, which is raw (overwritten at narrate.py:227). This gate should use smoothed to prevent transient spikes from forcing transitions.

## Concrete Effects

1. **Phase transitions are too reactive.** Raw convergence spikes cause immediate phase flips. The system oscillates between phases instead of providing stable pacing.
2. **CLIMAX entries are premature.** A single turn with convergence >= 2 can flip SETUP→RISING→CLIMAX. With smoothing, sustained pressure is required.
3. **CLIMAX exits are premature.** A single turn with convergence < 2 exits CLIMAX. With smoothing, sustained pressure loss is required.
4. **CLIMAX extension is too strict.** Requires raw >= 3, which is hard to sustain. Smoothed would allow extension when average pressure is high.
5. **BREATHER clean break is broken.** Design intent (I-42.2) was to use smoothed for BREATHER to prevent immediate re-engagement. Raw is too jumpy.
6. **Convergence hard gate is too reactive.** Forces "transition" outcome hint on transient spikes. Should use smoothed.

## Evidence from Eval Runs

From I-42 findings:
- noir-1930s: 22 turns in RISING before reaching CLIMAX at T25 (1 turn) — dampening loop from sanitizer downgrades
- zombie-survival: CLIMAX duration 1 turn (second CLIMAX)
- golden-piracy: CLIMAX 7 turns, then rapid exit
- Space-western: CLIMAX 10 turns (longest), but still volatile

The dampening loop (I-42.3) is partially caused by this — raw convergence drops to 0-1 after BREATHER, requiring a full rebuild. Smoothed would provide continuity.

## Fix

Pass `smoothed_convergence` to `_compute_scene_phase()` instead of raw `_convergence_score` for all phase transition logic. The smoothed value is already computed and persisted — it just needs to be used.

Files changed:
- `ccya/engine/narrate.py:211` — pass `smoothed_convergence` instead of raw `_convergence_score`
- `ccya/engine/narrate.py:227` — use `int(smoothed_convergence)` instead of raw `_convergence_score`
- `ccya/engine/_pacing.py:_compute_scene_phase()` — parameter type changed from `int` to `float` to accept smoothed value

## Related Tickets

- **B-46** (done): Smoothed convergence not persisted — this is fixed, smoothed is now persisted
- **I-42.2**: BREATHER uses smoothed convergence — design intent was smoothed for clean break, but code uses raw
- **I-42.3**: BREATHER amplifies dampening — partially caused by raw convergence requiring full rebuild after BREATHER
- **I-42.1**: Convergence limited dynamic range — smoothing would help mitigate the impact of compressed range

## References

- `ccya/engine/narrate.py:197-227` — convergence computation and passing
- `ccya/engine/_pacing.py:212-324` — `_compute_scene_phase()` with all phase transitions
- `ccya/engine/_pacing.py:157-197` — `_compute_pacing_context()` with convergence hard gate
- `roadmap/improvements/convergence-formula-phase-transitions.md` — I-42 findings
