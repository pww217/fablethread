---
title: "Generate world beats only on phase transitions, not every turn"
status: idea
urgency: 2
size: large
created: 2026-06-30
ticket_id: I-22
labels:
  - engine
  - world-step
  - thematic-repetition
---

## Problem

The world step generates beat candidates every turn. This causes two issues:

1. **Thematic repetition.** The LLM sees the same `recent_beats` context repeatedly across turns within a phase. Even with noun bans and diversity rules, it falls back to the same patterns (e.g., "heavy footsteps", "heavy breathing", "flashlight beam" appearing dozens of times).

2. **Unnecessary LLM calls.** Generating beats every turn wastes compute when the phase hasn't changed. A 25-turn session makes ~25 world LLM calls when ~5-8 would suffice.

The noun-ban band-aid (`world.py:45-57`, `world_user.j2:34-37`) doesn't work well — the LLM works around it by using banned words as modifiers ("heavy iron rod", "heavy timber") or the extraction catches adjectives instead of nouns.

## Status Update (2026-06-30)

**Thematic repetition RESOLVED by band-aid removal.** Examined 4 fresh 25-turn runs at commit `12332bab` (post-band-aid-removal):
- Golden-piracy: No noun-verb pair repeats across 25 turns
- Space-western: No noun-verb pair repeats across 25 turns
- Noir-1930s: No noun-verb pair repeats across 25 turns

The banned_nouns band-aid was ineffective (LLM worked around it). Removing it entirely + keeping recent_beats tracking resolved the issue. The LLM generates genuinely different beats each turn without explicit noun bans.

**I-22 is now a compute optimization, not a thematic repetition fix.** The proposal to run world step only on phase transitions is still valid for reducing LLM calls (~25 → ~5-8 per session), but thematic repetition is no longer a blocker.

## Alternatives considered

### Keep current approach (every turn)
- Thematic repetition resolved by band-aid removal
- LLM calls are wasteful but acceptable
- Simpler implementation

### Hybrid: beats on phase transitions + every N turns
- Generate beats on phase transitions AND every 3 turns within a phase
- Gives periodic beat refresh without the repetition problem
- More complex, partially retains the original problem
- Lower priority now that thematic repetition is resolved

### Keep current approach, fix noun ban
- The noun ban band-aid doesn't work — LLM works around it
- Would require a much more sophisticated extraction and enforcement
- Unlikely to be effective

## Proposed Solution

Run the world step only when `scene.scene_phase` changes, not every turn.

### Behavior

```
Turn 1 (SETUP):
  - World step runs → generates beat candidates
  - Ruling picks a beat
  - Narration happens

Turn 2 (SETUP):
  - Phase unchanged → SKIP world step
  - beat_candidates = [] (empty)
  - Ruling has no beats to pick from
  - Narration uses last beat + player input

Turn 3 (SETUP):
  - Phase unchanged → SKIP world step
  - Same as turn 2

Turn 4 (RISING): ← PHASE TRANSITION
  - World step runs → generates fresh beat candidates
  - LLM sees accumulated recent_beats but only once per phase
  - Ruling picks a beat
  - Narration happens
```

### Key design decisions

1. **Empty beat_candidates:** The ruling and narrate prompts already handle "no GM beat" — they narrate from player input + outcome hint. No changes needed there.

2. **Beat history tracking:** Still append selected beats to `recent_beats` for diversity tracking. The LLM only generates when the phase changes, so it sees fresh context each time.

3. **Phase transition detection:** Compare current `scene.scene_phase` with previous turn's `scene.scene_phase`. If different → run world step. If same → skip.

4. **First turn of a phase:** Always generates beats (even SETUP turn 1). This ensures every phase starts with fresh beat candidates.

## Implementation

### Files to modify

- `ccya/engine/turn.py` — add phase transition check before `_run_world_step`
- `ccya/engine/world.py` — no changes needed (already handles empty recent_beats)
- `ccya/engine/state.py` or wherever `scene_phase` is tracked — may need to store previous turn's phase

### Pseudocode

```python
# In turn.py, before _run_world_step call:
prev_phase = prev_state.get("scene", {}).get("scene_phase", "SETUP")
curr_phase = state.get("scene", {}).get("scene_phase", "SETUP")

if prev_phase != curr_phase or turn_no == 1:
    # Phase transition or first turn — run world step
    beat_candidates, ... = await _run_world_step(...)
else:
    # Same phase — skip world step
    beat_candidates = []
```

## Alternatives considered

### Hybrid: beats on phase transitions + every N turns
- Generate beats on phase transitions AND every 3 turns within a phase
- Gives periodic beat refresh without the repetition problem
- More complex, partially retains the original problem

### Keep current approach, fix noun ban
- The noun ban band-aid doesn't work — LLM works around it
- Would require a much more sophisticated extraction and enforcement
- Unlikely to be effective

## Success criteria

- Thematic repetition visibly reduced in 25-turn sessions (subjective examination)
- World LLM calls reduced from ~25 per session to ~5-8
- No regression in beat quality or pacing
- Phases feel distinct rather than one long scene

## Related

- `I-12` — world step not blending NPC psychological hints
- `I-3` — prompt choices tied to arcs/threads
- `B-24` — extraction reliability (resolved)
- `I-13` — skill distribution imbalance (improved)
