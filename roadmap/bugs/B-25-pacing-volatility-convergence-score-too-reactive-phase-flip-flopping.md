---
title: "Pacing volatility — convergence score too reactive, phase flip-flopping"
status: canceled
urgency: 2
size: medium
created: 2026-06-29
ticket_id: B-25
labels: [pacing, convergence, engine]
---

## Status

**Canceled** — volatility symptom resolved by F-28 (hysteresis + phase minimums).

E-7 evaluation across 5 runs shows 1-5 phase transitions in 15 turns, well below the "10+ phase changes" symptom.

## Related finding (not fixed)

**Too stable when threads don't build:** Golden-piracy stayed RISING for 10 turns (T3-T12). Root cause: seed threads (`navy_patrols`, `guild_bounty`) stayed dormant entire run, never contributing to convergence. This is a thread system issue (seed threads not being surfaced), not a pacing volatility issue. See E-7 thread audit findings.

## Description

Convergence score is too reactive, causing excessive phase transitions (10+ phase changes in 15 turns). No rolling average, no hysteresis, no minimum turns per phase. Phase constraint enforcement is also missing — ruling picks beats without checking phase alignment.

## Symptoms

- 10+ phase changes in 15 turns during eval runs
- Convergence score fluctuates wildly based on single-turn events
- No smoothing or stabilization mechanism
- Ruling step selects beats without checking phase alignment constraints

## Root Causes

### Convergence score too reactive
- `compute_convergence_score()` is entirely reactive — every component depends on current state
- Single turn events can swing the score by the full threshold (2 points)
- No rolling average, no decay, no hysteresis band
- Related to B-5 (convergence starvation) — opposite problem: too volatile instead of too static

### No minimum turns per phase
- Game can flip between phases every turn
- No stabilization period to let narrative catch up
- Players experience whiplash from phase to phase

### Phase constraint enforcement missing
- Ruling step selects beats from `beat_candidates` without checking `allowed_beat_types`
- World step enforces diversity rules but ruling step doesn't respect phase alignment
- `derive_allowed_beat_types` computes constraints but they may not be enforced in ruling

## Fix Needed

### Short-term
- Add rolling average to convergence score (e.g., average of last 3 turns)
- Add hysteresis band: require convergence to be above threshold by margin before transitioning
- Add minimum turns per phase (e.g., 3 turns minimum before allowing phase change)

### Long-term
- Enforce phase alignment in ruling step — filter beat_candidates by `allowed_beat_types`
- Consider narrative-aware phase transitions (B-5 Option C)
- Coordinate with I-4 (too many hard rolls) — hard rolls may contribute to volatility

## Related

- B-5: Convergence starvation — pacing engine (done, but volatility is separate issue)
- I-4: Balancing difficulty — too many hard rolls
- World step diversity rules already exist but ruling step doesn't enforce phase alignment

## Files to Review

- `ccya/engine/_pacing.py` — `compute_convergence_score()`, phase transition logic
- `ccya/engine/ruling.py` — beat selection, phase alignment checks
- `ccya/engine/world.py` — `derive_allowed_beat_types`, beat diversity enforcement
- `ccya/config.py` — convergence threshold and phase config