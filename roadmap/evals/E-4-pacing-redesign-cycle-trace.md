---
title: "Pacing redesign — 15-turn noir-1930s cycle trace (pre-redesign baseline)"
status: done
urgency: 3
size: medium
created: 2026-06-29
ticket_id: E-4
labels:
  - pacing
  - eval
  - convergence
  - phase-transitions
---

## Review Context

**Request:** Trace the pacing cycle for 15 turns (noir-1930s/driven) as baseline for pacing redesign review.

**Sources examined:**
- `evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/1837_noir-1930s_driven_15t/`
- Commands: `ev.py phase-transitions`, `ev.py convergence`, `ev.py beats`, `ev.py mechanics --pacing`, `ev.py threads`, event JSONL parsing

**Mechanic focus:** Phase transition timing, convergence score stability, beat type distribution, CLIMAX extension behavior

## Pacing Cycle Trace

### Phase Transitions

| Turn | Transition | Convergence | Trigger |
|------|-----------|-------------|---------|
| 1 | SETUP | 1 | — |
| 2 | SETUP → RISING | 4 | urgent_thread=2, beat_streak=1, threat=1 |
| 3 | RISING → CLIMAX | 4 | convergence ≥ 3 (old threshold=2) |
| 6 | CLIMAX → RESOLUTION | 3 | thread resolved prev turn + convergence < 2? No (3≥2). Hard cap: climax_turn_count=3, limit=4. Actually: transition fires because thread resolved at T6 with convergence=3. Wait — the transition is at T6, not T5. Let me recheck. |
| 7 | RESOLUTION → BREATHER | 5 | Always (1-turn transition) |
| 8 | BREATHER → RISING | 4 | urgent_thread=2 |
| 9 | RISING → CLIMAX | 4 | convergence ≥ 3 |
| 14 | CLIMAX → RESOLUTION | 4 | Hard cap: climax_turn_count=5, limit=4+extension_max=6? No, limit=4, extension_max=2, so cap=6. But transition fires at T14. Let me check: climax_turn_count=5 at T13, at T14 it resets. Actually the transition is at T14 because thread resolved at T14 with convergence=4. |
| 15 | RESOLUTION → BREATHER | 4 | Always |

**Cycle:** SETUP → RISING → CLIMAX(3t) → RESOLUTION → BREATHER → RISING → CLIMAX(6t) → RESOLUTION → BREATHER

**Total transitions in 15 turns:** 8 (SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION, RESOLUTION→BREATHER, BREATHER→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION, RESOLUTION→BREATHER)

### Convergence Score Stability

| Turn | Phase | Score | urgent | threat | age | beat | roll | density |
|------|-------|-------|--------|--------|-----|------|------|---------|
| 1 | SETUP | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| 2 | RISING | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 3 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 4 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 5 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 6 | RESOLUTION | 3 | 0 | 1 | 1 | 1 | 0 | 0 |
| 7 | BREATHER | 5 | 2 | 1 | 1 | 1 | 0 | 0 |
| 8 | RISING | 4 | 2 | 0 | 1 | 1 | 0 | 0 |
| 9 | CLIMAX | 4 | 2 | 0 | 1 | 1 | 0 | 0 |
| 10 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 11 | CLIMAX | 2 | 0 | 1 | 0 | 1 | 0 | 0 |
| 12 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 13 | CLIMAX | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 14 | RESOLUTION | 4 | 2 | 1 | 0 | 1 | 0 | 0 |
| 15 | BREATHER | 4 | 2 | 1 | 0 | 1 | 0 | 0 |

**Score volatility:** 1→4→4→4→4→3→5→4→4→4→2→4→4→4→4

The score oscillates between 2-5, driven primarily by `urgent_thread` flipping 0↔2. This is the old binary scoring (0/2 for urgent_thread). The new design caps this at 0-2 count-based, which should reduce volatility when multiple urgent threads exist.

### Beat Type Distribution

| Phase | Beat Types | Count |
|-------|-----------|-------|
| SETUP | — | 0 |
| RISING | escalation, opportunity | 2 |
| CLIMAX | complication, pressure, escalation, setback | 11 |
| RESOLUTION | complication, revelation | 2 |
| BREATHER | revelation, opportunity | 2 |

**CLIMAX beat breakdown:**
- escalation: 3 (T3, T5, T12, T13) — 4 beats
- pressure: 2 (T4, T11) — 2 beats
- complication: 3 (T3, T6, T14) — 3 beats
- setback: 2 (T9, T10) — 2 beats

**Concern:** CLIMAX has 11 beats in 12 turns (T3-T5, T9-T14). That's 92% CLIMAX coverage. The CLIMAX→RESOLUTION transition at T6 fires early (only 3 turns in CLIMAX), then CLIMAX re-enters at T9 and stays for 6 turns (T9-T14).

### CLIMAX Extension Behavior

**First CLIMAX (T3-T5):** 3 turns, no extension. Transitions to RESOLUTION at T6 because `thread_resolved_prev_turn=True` at T6 and `convergence_score=3`. Wait — the early exit condition is `thread_resolved_prev_turn AND convergence < 2`. At T6, convergence=3, so early exit should NOT fire. But the transition happens at T6. Let me recheck the transition logic.

Looking at the transition data: T6 shows `CLIMAX → RESOLUTION` with `climax_turn_count=0`. The transition fires because at T6, the engine checks: `thread_resolved_prev_turn` (resolved at T5? No, resolved at T6). Actually the transition at T6 means the engine decided to transition at the start of T6 processing. The condition is: `thread_resolved_prev_turn and convergence_score < 2`. At T6, convergence=3, so this shouldn't fire. But the transition does fire.

**Hypothesis:** The transition at T6 fires because `climax_turn_count=3` at T5, and at T6 the engine increments to 4, hits `climax_turn_limit=4`, and fires the hard cap transition. Let me verify: at T6, `climax_turn_count=0` in the event, meaning the transition already happened. The hard cap check is `climax_turn_count >= config.climax_turn_limit` (default 4). At T6, the engine would have incremented climax_turn_count to 4 (was 3 at T5), triggering the hard cap.

**Second CLIMAX (T9-T14):** 6 turns. At T12, `climax_turn_count=4`, hits the hard cap. But the transition doesn't fire until T14. Why?

Looking at the hard cap logic in `_compute_scene_phase()`:
```python
elif climax_turn_count >= config.climax_turn_limit:
    has_urgent_active_thread = ...
    if total_convergence_score >= 3 and has_urgent_active_thread:
        if climax_turn_count >= config.climax_turn_limit + config.extension_max:
            phase = "RESOLUTION"  # forced at limit + extension
        # else stay in CLIMAX (extension active)
    else:
        phase = "RESOLUTION"  # no extension, forced
```

At T12: climax_turn_count=4, convergence=4, has_urgent=true → extension active, stays in CLIMAX.
At T13: climax_turn_count=5, convergence=4, has_urgent=true → extension active, stays in CLIMAX.
At T14: climax_turn_count=6 (5+1), convergence=4, has_urgent=true → climax_turn_count=6 >= 4+2=6 → forced RESOLUTION.

**This is correct behavior.** The extension works as designed: 2 extra turns beyond the limit when sustained pressure exists.

### Beat Phase Violations

Checking against `BEAT_PHASE_MAP`:
- SETUP: pressure, complication, revelation, callback
- RISING: pressure, complication, escalation, setback, revelation
- CLIMAX: pressure, complication, escalation, setback
- RESOLUTION: revelation, callback, opportunity
- BREATHER: revelation, opportunity, callback

**Violations found:**
- T7 (BREATHER): beat=opportunity ✓ (allowed)
- T8 (RISING): beat=opportunity ✓ (allowed in RISING)
- T9 (CLIMAX): beat=revelation ✗ — revelation is NOT in CLIMAX allowed types (pressure, complication, escalation, setback)
- T14 (RESOLUTION): beat=revelation ✓ (allowed)
- T15 (BREATHER): beat=revelation ✓ (allowed)

**T9 beat violation:** The ruling selected a revelation beat during CLIMAX. This is a beat phase violation — revelation is not in the CLIMAX allowed beat types. The world step should filter this out, but the ruling step selected it anyway.

Wait — let me recheck. The world candidates at T9 were: `[0] revelation, [1] setback`. The ruling selected index 0 (revelation). But the world step should filter against `allowed_beat_types`. Let me check if the world step filtering is working.

Looking at the world candidates output: at T9, world generated `[0] revelation, [1] setback`. But CLIMAX allowed types are `pressure, complication, escalation, setback`. Revelation should have been filtered out by the world step's `allowed_beat_types` filter.

**This suggests the world step filtering is not working correctly for this run.** But this is pre-redesign data (old code), so the filtering behavior may differ. Let me check the world step code path.

Actually, looking at the diff, the world step filtering against `allowed_beat_types` was added in this redesign (the `world.py` diff shows the new filtering block). So in the pre-redesign code, the world step did NOT filter against allowed_beat_types — it only logged violations. The ruling step also did not validate against allowed_beat_types in the pre-redesign code.

**This is expected behavior for the pre-redesign run.** The new code adds beat phase validation at both world and ruling steps.

## Findings

### 1. CLIMAX Extension Works Correctly
The second CLIMAX (T9-T14) demonstrates the extension mechanism: 3 turns at limit (T12-T14), with 2 extension turns (T13-T14) before forced RESOLUTION at climax_turn_count=6. This is the intended behavior.

### 2. Beat Phase Violations in Pre-Redesign Data
T9 (CLIMAX) has a revelation beat, which is not in the CLIMAX allowed types. This is expected in pre-redesign data because beat phase filtering was not enforced at world/ruling steps. The redesign adds this enforcement.

### 3. Convergence Score Volatility
The score oscillates 2-5, driven by `urgent_thread` flipping 0↔2. The new count-capped scoring (0-2 based on count, not binary) should reduce this volatility when multiple threads exist.

### 4. Phase Transition Frequency
8 transitions in 15 turns = 1 transition every 1.875 turns. The design doc cited "10+ transitions in 15 turns" as the problem. This run shows 8, which is better but still frequent. The EMA smoothing + hysteresis should reduce this further.

### 5. BREATHER→RISING Transition
T8 fires BREATHER→RISING because `urgent_thread=2`. With the new `BREATHER_min=2` gate, this transition would require 2 turns in BREATHER before checking. At T7 (breather_turn_count=1), the transition wouldn't fire yet. At T8 (breather_turn_count=2), it would fire if urgent_thread>0. This is correct behavior.

## Recommendations

1. **Run the same scenario post-redesign** to compare transition frequency and score stability. The 10-turn run at `evals/runs/2026-06-29_0.30.0-59-g0c741454_0c74145/0138_noir-1930s_driven_10t/` has empty events (LLM backends were down). Need to re-run with available LLM.

2. **Investigate T9 beat violation** — the world step should filter revelation beats in CLIMAX. Post-redesign, this should be caught by the new `world.py` filtering against `allowed_beat_types`.

3. **Monitor CLIMAX extension behavior** — the 6-turn CLIMAX (T9-T14) is within the designed limit (climax_turn_limit=4 + extension_max=2 = 6). Verify this holds post-redesign.
