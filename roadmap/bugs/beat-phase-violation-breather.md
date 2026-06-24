---
title: Beat Phase Violations — Invalid Beat Types in BREATHER Phase
status: new
urgency: 3
size: small
created: 2026-06-24
labels:
  - engine
  - pacing
  - beats
---
## Problem

The storyteller generates beat types that are invalid for the current scene phase. The phase engine allows certain beat types per phase, but the storyteller ignores the constraints.

**Evidence (the-outer-rim save):**

BEAT_PHASE_MAP (from `beat_phase_validity` checker):
- BREATHER allows: `breathing_room`, `callback`
- BREATHER disallows: `pressure`, `complication`, `revelation`, `escalation`, `twist`, `setback`, `opportunity`

Violations found:
1. **T13 (BREATHER):** Beat type = `revelation` (driver=motivation, npc="Scarred Leader reveals they are guarding a shipment of unregistered mining gear.")
   - `revelation` is not in BREATHER's allowed set
2. **T14 (BREATHER):** Beat type = `opportunity` (driver=motivation, directive="Scene Pressure")
   - `opportunity` is not in BREATHER's allowed set
   - Also, directive "Scene Pressure" violates BREATHER's expected directive (should be neutral/hold, not pressure)

**Other turns with suspect beats (non-violating but noteworthy):**
- T3 (RISING): No beat at all
- T5 (RISING): No beat at all
- T9 (CLIMAX): No beat at all — CLIMAX should always have a beat

## Reproduction

```bash
ev.py turn 13 --save-dir saves/the-outer-rim--after-unification-2026-06-24 | grep -A5 "gm_beat"
ev.py turn 14 --save-dir saves/the-outer-rim--after-unification-2026-06-24 | grep -A5 "gm_beat"
```

## Root Cause Estimate

The storyteller prompt (`storytell_system.j2`) lists allowed beat types per phase but does not enforce the constraints at the engine level. The `beat_phase_validity` checker exists but is a post-hoc validation — it does not prevent the violation. The phase context in the prompt includes `scene_phase` but the storyteller can still generate out-of-phase beats.

The null beats in CLIMAX (T9) are especially problematic — CLIMAX should consistently generate beats to drive tension.

## Impact

- BREATHER phases feel like RISING/CLIMAX because storyteller generates escalation-level beats
- Invalid beats undermine the pacing system's phase differentiation
- The beat system's phase constraints are aspirational, not enforced

## Suggested Fix

- Add engine-level enforcement in `apply_gm_beat` (or similar) that rejects beats incompatible with the current `scene_phase`
- When rejected, fall back to a default beat for the phase (e.g., BREATHER → `breathing_room`)
- Log the rejection so the storyteller can (in future turns) learn from the feedback
- Ensure CLIMAX always has a beat — transform null beats into `pressure` in CLIMAX
