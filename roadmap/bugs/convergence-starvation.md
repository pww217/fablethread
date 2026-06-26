---
title: "Convergence Starvation — Pacing Engine"
status: up-next  # design reviewed 2026-06-25, no fatal blockers — ready for planning
urgency: 2
size: large
created: 2026-06-22
design: docs/design/convergence-proactive-design.md
labels:
  - pacing
  - convergence
  - engine
  - phase-transitions
---

## Validation

**Validated: confirmed root cause.**

### Root Cause Confirmed

`compute_convergence_score()` in `_pacing.py:86-142` computes a 5-component score that is **entirely reactive** — every component depends on current state, nothing injects pressure proactively:

1. `any_urgent` (+1): Any non-dormant thread with urgency="urgent"
2. `any_threat` (+1): Any non-dormant thread with type="threat"
3. `scene_age` (+1): Scene age >= scene_pressure_threshold (default 3)
4. `beat_streak` (+1): ≥60% of last 5 beats are pressure types
5. `dice_weight` (+1): any_urgent AND rolled AND band in crit_fail/fail

Phase transition at `_pacing.py:262`: `RISING → CLIMAX` requires `convergence_score >= config.convergence_threshold` (default 2). If all 5 components are 0, convergence stays at 0 forever — no mechanism to recover.

### Contributing Factors Confirmed

1. **Stealth-heavy play style** — ruling system classifies idle observation/unimpeded movement as "no check required" → no rolls → no dice_weight component. This is by design (`routes.py` ruling system).
2. **No rolls → no beat streak** — null beats (34-57%) mean no beats to streak. Beat driver is always "motivation" (not pressure types).
3. **Thread urgency skewed** — most threads are "normal" urgency, not "urgent". `any_urgent` component stays 0.
4. **Fresh scene** — `scene_age < scene_pressure_threshold` when just entered RISING.

### Assessment

This is a real architectural gap. The convergence system has no proactive pressure injection. All 4 suggested fixes (proactive injection, floor, narrative transitions, urgency escalation) are valid approaches. Proactive pressure injection (Option A) is recommended as it addresses the root cause directly.

---

When all 5 convergence components are 0, there is no mechanism to recover. The phase machine waits for `convergence >= convergence_threshold` (default 2) to transition RISING→CLIMAX, but if convergence is 0, it can never reach the threshold. This creates "convergence dead spots" where the game state is completely static.

**Evidence (Eval Cycle 2, noir opportunist):** T20-T22 have convergence score = 0 across all 5 components:
- No urgent threads (all background)
- No threat threads
- Scene age = 0 (just entered BREATHER→RISING)
- No beat streak (null beats in T20-T22)
- No dice weight (no rolls in T20-T22)

The opportunist persona's stealth-heavy play style starves convergence. The player chooses stealth actions that the ruling system classifies as "no check required" (idle observation, unimpeded movement, etc.), which means no rolls, no dice_weight component, and no pressure beats.

## Root Cause Analysis

### Convergence score is entirely reactive

`compute_convergence_score()` in `_pacing.py:86-142` computes a 5-component score:

1. **any_urgent** (+1): Any non-dormant thread with urgency="urgent"
2. **any_threat** (+1): Any non-dormant thread with type="threat"
3. **scene_age** (+1): Scene age >= scene_pressure_threshold (default 3)
4. **beat_streak** (+1): ≥60% of last 5 beats are pressure types
5. **dice_weight** (+1): any_urgent AND rolled AND band in crit_fail/fail

The score responds to what's happening in the current scene, but has **no proactive mechanism to inject pressure when the scene goes quiet**.

### Contributing factors

1. **Stealth-heavy play style.** The opportunist persona chooses stealth actions that the ruling system classifies as "no check required" (idle observation, unimpeded movement, etc.). No rolls → no dice_weight component.

2. **No rolls → no beat streak.** The beat streak component requires beats to exist, but null beats (34-57%) mean there are no beats to streak. Beat driver is always "motivation" (not pressure types), so even when beats exist, they don't contribute to the streak.

3. **Thread urgency distribution skewed.** Most threads are "normal" urgency, not "urgent". The convergence score depends on `any_urgent` component (+1), but most threads are "normal" urgency.

4. **Thread type distribution skewed.** Most threads are "threat" type, but the convergence score depends on `any_threat` component (+1). If there are no threat threads, this component is 0.

5. **Fresh scene.** If the scene is fresh (just entered RISING), scene_age < scene_pressure_threshold, so this component is 0.

### Previous root causes (likely fixed)

- **Overly passive NPCs.** NPCs were not getting their personalities correctly due to a misconfiguration. This has been fixed in recent commits.
- **NPC personality assignment.** NPCs were not getting their personalities correctly. This has been fixed.

The convergence starvation may have been caused by these NPC issues in the past. Worth verifying if convergence starvation persists after those fixes.

## Suggested Fixes

### Option A: Proactive pressure injection (recommended)

Add a mechanism to inject pressure when convergence has been low for N turns:

- If convergence < threshold for 3+ turns, inject a "pressure beat" or "complication"
- If convergence < threshold for 5+ turns, escalate the most relevant thread to "urgent"
- If convergence < threshold for 7+ turns, transition to a new phase based on narrative context

This is the most robust fix because it addresses the root cause: the convergence score is entirely reactive with no proactive mechanism.

### Option B: Convergence floor

Add a minimum convergence score that prevents convergence from dropping to 0:

- If convergence < 1, set it to 1
- If convergence < 2, add a "floor" component that increments based on how long convergence has been low

This is a simpler fix but may feel artificial. The floor should be narrative-driven, not purely mechanical.

### Option C: Narrative-based phase transitions

Allow the phase machine to transition based on narrative context, not just convergence score:

- If the player has been in stealth for 5 turns, transition to a new phase based on narrative context
- If the player has avoided rolls for 5 turns, transition to a new phase based on narrative context
- If convergence < threshold for N turns, allow a "narrative transition" that doesn't require convergence

This is a more fundamental change to the phase machine but may produce better narrative outcomes.

### Option D: Thread urgency escalation

Add a mechanism to escalate thread urgency when convergence is low:

- If convergence < threshold for 3+ turns, escalate the most relevant thread to "urgent"
- If convergence < threshold for 5+ turns, escalate all non-dormant threads to "urgent"

This is a targeted fix that addresses the `any_urgent` component specifically.

## Implementation Notes

- The convergence threshold was lowered from 3 to 2 in commit `eed5878` to help with starvation, but it hasn't helped much. The threshold change alone isn't sufficient when all 5 components are 0.
- The ruling system's "routine" path (no check) is for: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce, information gathering, actions already attempted in this scene without new stakes, taking cover, reloading, healing, using a prepared item as intended. This is by design — the ruling system's "impossible" and "routine" paths skip rolls for low-risk actions.
- The spiral detection (`detect_spiral()`) detects death spirals (consecutive hard rolls or high ratio of hard rolls). This feeds into `derive_allowed_beat_types` which removes pressure beats when spiral is detected, but it doesn't directly affect convergence. A player in a death spiral gets fewer pressure beats, which reduces beat_streak, which reduces convergence — creating a feedback loop where bad rolls make it harder to reach CLIMAX.

## Priority

High. This is the biggest gap in the current designs. The arc redesign and seed redesign don't address pacing engine convergence. Without a fix, stealth-heavy play styles will consistently starve convergence, creating dead spots in the game.
