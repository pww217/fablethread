---
title: "[User-Reported] Seed Initialization Systemic Failures"
status: new
created: 2026-06-24
labels:
  - engine
  - seed
  - arc
  - sanitizer
---
## Problem

Multiple interconnected failures in seed/initialization pipeline:

1. **No choices on initial turn 0** — Player gets no actionable options at game start
2. **Arc origin overlaps PC bio** — `arc_origin` should be independently invented lore (unrelated to player), then tied to player motivations at the end. Currently it's conflated with player backstory.
3. **Seed turn summary broken** — Initial turn summary generation fails
4. **Sanitizer not running** — Likely due to arc changes breaking the sanitizer trigger/conditions

## Root Cause Estimate

Seed initialization at `ccya/engine/seed.py` / `init_state.py` sets up initial state but arc generation, choice generation, and sanitizer registration are not properly wired. The arc_origin prompt likely pulls from PC bio instead of generating independent lore first.

## Impact

- Game starts with no player agency (no choices)
- Arc feels generic/derivative instead of distinct world lore
- Sanitizer failures compound state drift over time
- First impression severely degraded

## Suggested Fix

1. Separate arc_origin generation: first invent standalone arc lore, then append player tie-in
2. Ensure choice generation runs on turn 0 (not deferred to turn 1)
3. Verify sanitizer registration triggers on arc state changes
4. Add seed turn summary generation to initialization pipeline