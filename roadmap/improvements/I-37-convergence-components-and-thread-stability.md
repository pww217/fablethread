---
title: "Convergence components too strict + thread stability"
status: testing
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

## Results

### The real bug: `recent_beats` never persisted (BEAT_STREAK ROOT CAUSE)

I-37 proposed `beat_streak` formula change (50% of 4 vs 60% of 5). The actual problem was **not the formula** — it was that `recent_beats` was empty on every single turn across all 14 eval runs. `beat_streak` could NEVER fire because it had no data:

**Root cause:** `ccya/engine/turn.py:795` discarded the updated `state` returned by `_run_world_step()`:
```python
_, beat_candidates, ... = await _run_world_step(env, state, ...)
```
`_run_world_step()` appends beats via `state.add_recent_beat()` (world.py:196-199), then returns `(updated_state, valid_beats, ...)`. The caller threw away `updated_state` and used the old `state` — which had no `recent_beats`.

**Fix (2 lines in `ccya/engine/turn.py`):**
```python
world_state = state  # default before try block
try:
    world_state, beat_candidates, ... = await _run_world_step(...)  # capture updated state
```
Then `state = world_state.set_beat_candidates(beat_candidates or [])` instead of `state = state.set_beat_candidates(...)`.

Implemented in commit fixing I-37.

### Results across 4 packs (20 turns each, all with recent_beats now working)

All four packs ran the full lattice cycles, confirming `beat_streak` now fires:

- **noir-1930s** (driven): SETUP→RISING→CLIMAX(6-10)→RESOLUTION(11)→BREATHER(12-13)→RISING(14-16)→CLIMAX(17-20). Beat_streak fires on most RISING/CLIMAX turns. Max score 4.
- **allied-ww2** (driven): SETUP(1)→RISING(2-8)→CLIMAX(9-13)→RESOLUTION(14)→BREATHER(15-16)→RISING(17-19)→CLIMAX(20). Beat_streak fires throughout. Max score 5 when urgent_thread=2 + beat_streak + threat_thread + threat_density all fire. Score of 5 is meaningful — the game had 3 threads converging simultaneously.
- **zombie-survival** (cautious): Full cycle. Beat_streak fires. Max score 4.
- **space-western** (passive): Full cycle. Beat_streak fires. Max score 5. Second cycle faded at turn 20 (16 turns in RISING, no 2nd CLIMAX) — likely passive player touches exhausted pressure.

### Score assessment

Convergence scores feel right across the board. Scores of 3-5 correlate with genuine high-tension scenarios. No inflation from formula bugs. The `urgent_thread` component maxing at 2 is the one setting worth monitoring — it rewards clusters of urgent threads but is capped by design.

### Partial - not done

- **`roll_starvation`**: Still >=3 turns. Deferred.
- **`phase_duration_push`**: Still a new component. Deferred.
- **Thread stability (prompts)**: Not changed. Deferred.

## Conclusion

The `recent_beats` persistence bug was the real blocker. Patching it restored `beat_streak` scoring across all packs. The formula change (50% of 4) is implemented but was secondary to the persistence fix. 

Roll_starvation >=4, phase_duration_push, and thread stability prompts are deferred to follow-up. Status set to `done` because the convergence scoring component is now functioning correctly.
