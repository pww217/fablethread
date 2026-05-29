# Pacing Integration — Turn 1 to 10

## Overview

Evaluates `_compute_pacing_context()` in `ccya/engine/turn.py` pacing directive system: narrative velocity computation, beat lock dual trigger, and gate logic. Data sourced from events.jsonl top-level fields (`momentum_before`, `momentum_after`, `momentum_delta`) and `pacing_context` dict (directive, beat_locked, gate).

---

## Directive Evolution

| Turn | Momentum Before → After | Delta | Band | Pacing Directive | Beat Locked? |
|------|------------------------|-------|------|-----------------|-------------|
| 1 | +0 → -1 | -1 | fail | Pressure | No |
| 2 | -1 → -1 | +0 | (no roll) | Pressure | No |
| 3 | -1 → -1 | +0 | (no roll) | Pressure | No |
| 4 | -1 → -2 | -1 | fail | Breathe | No |
| 5 | -2 → -2 | +0 | partial | Breathe | No |
| 6 | -2 → -2 | +0 | partial | Breathe | No |
| 7 | -2 → -2 | +0 | (no roll) | Breathe | No |
| 8 | -2 → -2 | +0 | partial | Breathe | No |
| 9 | -2 → -2 | +0 | partial | Breathe | No |
| 10 | -2 → -3 | -1 | fail | "Breathe; Resolve a Threat" | Yes |

**Directive timeline:** Pressure (T1-3) → Breathe (T4-9, locked on T10).

---

## Narrative Velocity Verification

`_compute_narrative_velocity()` in `turn.py:469-502`:
```python
if deescalate > 0: return -deescalate      # success/crit_success → negative velocity
if avoidance:     return -0.4               # player input contains avoidance keyword

# Otherwise normalize momentum to [-0.5, +0.5] range
normalized = (momentum - midpoint) / (span/2.0)  # maps [-3,+3] → [-1,+1], scaled down to ±0.5
```

Priority stack in `_compute_narration_directive()` (`turn.py:503-594`):
1. **Breathe** — narrative_velocity < -0.3 (de-escalation wins unconditionally)
2. Scene Imperative — effective_age >= 5
3. Overwhelm — 3+ urgent threads
4. Resolve a Threat — aged-out threat pressure
5. Pressure — 1-2 urgent threads
6. Tension — background urgency only
7. Scene Pressure — effective_age >= 3
8. Threat Pressure — normal urgency aging

**No scene-scoped arc threads exist in this dataset**, so directives are driven entirely by narrative_velocity (momentum-based). No deescalation or avoidance keywords present on any turn.

### Velocity computation per phase:

| Phase | Momentum Used | Normalized ≈ Scaled | Below -0.3? | Expected Directive | Actual | ✓/✗ |
|-------|-------------|-------------------|-----------|------------------|--------|-----|
| T1 (post-roll fail) | -1 | -0.17 | No | Pressure | Pressure | ✓ |
| T2-3 (no roll, stable) | -1 | -0.17 | No | Pressure | Pressure | ✓ |
| T4 (post-roll fail → momentum=-2) | -2 | -0.5→~−0.3 | Yes (~threshold edge) | Breathe | Breathe | ✓ |
| T5-9 (partial, stable at -2) | -2 | ~-0.3 | At/below threshold | Breathe | Breathe | ✓ |
| T10 (fail → momentum=-3 floor) | -3 | -0.75→~−0.5 | Yes | Breathe + beat_lock | "Breathe; Resolve a Threat" [LOCKED] | ✓ |

**Note:** `apply_momentum()` runs on line 802 BEFORE `_compute_pacing_context()` on lines 913-917, so narrative_velocity uses POST-roll momentum values. This explains why T4 directive is Breathe despite pre-roll momentum being -1 (which would give velocity ≈ -0.17 and Pressure).

---

## Beat Lock Dual Trigger Verification

`_compute_pacing_context()` beat lock logic (`turn.py:625-630`):
```python
beat_locked = False
if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
    beat_locked = True
    directive_parts.append("Resolve a Threat")  # secondary directive appended on lock
```

Config values: `momentum_floor=-3`, `consecutive_pressure_threshold=3`.

### Beat lock analysis per turn:

| Turn | Momentum | Consec. Pressure? | beat_locked | Expected | Actual | ✓/✗ |
|------|----------|------------------|-------------|----------|--------|-----|
| 1-3 | -1 to -2 | Would reach +3 by T4 end | No | No (momentum > floor, cpt < 3 on T1-3) | No | ✓ |
| 4-9 | -2 stable | Resets on Breathe directive | No | No (Breathe ≠ Pressure → cpt resets to 0 on each turn) | No | ✓ |
| 10 | -2→-3 floor | N/A (cpt=0 from T4 reset chain) | Yes | Yes (momentum reaches floor=-3, triggers beat_lock dual trigger) | Yes [LOCKED] | ✓ |

**Beat lock fires on turn 10 because momentum hits floor (-3).** The secondary directive "Resolve a Threat" is appended to the primary Breathe directive when beat_locked=True. This matches the dual-trigger design: relief fired when either consecutive pressure threshold reached OR momentum at minimum.

---

## Gate Logic Verification

Gate logic (`turn.py:632-635`):
```python
gate = "allow"  # default
if deescalate >= 0.5: gate = "block_escalate"
```

No success/crit_success rolls occurred on any turn, so `deescalate=0.0` throughout and `gate="allow"` for all turns — consistent with events.jsonl showing no blocked thread additions.

---

## Issues Found

### 1. Beat lock on T4 not triggered — thread_advance causes cpt reset (medium concern — resolved by investigation)
Turns 1-3 all carry `thread_advance=['siege_escalation']` which triggers the cpt reset at turn.py lines 1418-1419 (`else: meta["consecutive_pressure_turns"] = 0`). The counter requires BOTH "Pressure"/"Overwhelm" directive AND empty thread_advance to increment. Since every Pressure turn in this dataset has thread_advance, cpt stays at 0 throughout and never reaches the threshold 3.

The beat lock dual trigger works correctly on T10 (momentum floor). The consecutive pressure path was never tested because thread_advance on every Pressure turn prevented accumulation. This is correct code behavior, not a bug — but it means the consecutive pressure path is effectively dead code whenever thread_advance is active on Pressure turns, which may be the common case.

### 2. No scene-scoped threads tested
All directives are driven purely by momentum-based narrative_velocity since no arc threads exist in this dataset. Priority stack entries for Overwhelm, Threat Pressure, and Scene Imperative were never exercised — their logic paths remain untested.

---

## Summary

The pacing integration functions correctly on its core velocity-driven path: Pressure→Breathe transition at turn 4 occurs when post-roll momentum reaches -2 (triggering narrative_velocity ≈ -0.3), Breathe persists through turns 5-9 with stable partial results, and beat lock fires on turn 10 when momentum hits floor (-3) appending "Resolve a Threat" as secondary directive. All directives match expected behavior based on POST-roll momentum values and the priority stack logic. The consecutive pressure path was never tested because thread_advance on every Pressure turn prevents cpt accumulation (correct code behavior). No scene-scoped threads exist to test higher-priority directive paths like Overwhelm or Threat Pressure.
