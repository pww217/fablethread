---
title: "Convergence components too strict + thread stability"
status: up next
urgency: 2
size: medium
created: 2026-07-09
ticket_id: I-37
labels:
  - engine
  - pacing
  - threads
---

## Problem

Convergence score rarely reaches threshold 3 during RISING, so RISING→CLIMAX transitions depend on thread luck rather than natural pacing. Three components are too picky for what the system actually produces:

1. `beat_streak`: 60% of 5 recent beats must be tension. Diversity constraints prevent clustering — 5-beat window dilutes the signal.
2. `roll_starvation`: fires at 3 turns without rolls, but rolls happen every turn in normal play. Gap of 3 is too easy to hit and too quick to matter.
3. No time-based signal: phases can run indefinitely without a "this is getting stale" push.

Additionally, thread type stability is broken (types flip-flop constantly) and urgency lacks hysteresis (promotes/demotes every turn based on momentary prose).

## Changes

### Component changes

| Component | Current | Proposed | Why |
|-----------|---------|----------|-----|
| `beat_streak` | 60% of 5 | 50% of 4 | Tighter window, easier to hit. 2/4 beats is still meaningful. |
| `roll_starvation` | >=3 turns | >=4 turns | Catch genuine action pauses, not turn-to-turn noise. |
| `phase_duration_push` | none | +1 at +3 turns past RISING_min, +2 at +6 | Natural time pressure signal. |

### Thread stability (prompt fixes)

**`sanitize_thread.j2`** — Add type stability rule:
> Once a type is assigned, keep it unless the thread's fundamental nature has changed (not just the current narrative moment). A thread that is a `threat` stays a `threat` even when the immediate danger subsides. Only change type if the thread's core identity shifts (e.g., a `threat` becomes an `opportunity` because the player discovers a way to use it).

**`record_system.j2`** — Add urgency stability guidance:
> **Escalate to urgent when:** The threat has been imminent for 2+ turns (not just this turn). A single moment of danger is not enough — urgency should reflect sustained pressure, not momentary prose.

### Files to change

- `ccya/engine/_pacing.py` — `compute_convergence_score()`: beat_streak threshold, roll_starvation threshold, add phase_duration_push
- `ccya/prompts/sanitize_thread.j2` — type stability rule
- `ccya/prompts/record_system.j2` — urgency hysteresis guidance

### Validation

- Run convergence checker on existing eval runs to verify score changes
- Run 25-turn evals on all 3 packs to verify RISING→CLIMAX fires more reliably
- Check thread type stability: count type changes per thread across the run
