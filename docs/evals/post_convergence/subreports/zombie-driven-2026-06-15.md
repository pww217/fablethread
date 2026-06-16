# Evaluation Report: Zombie Survival (Driven Persona)

**Session:** `saves/ev/20260615_225837_35b68a`
**Pack:** zombie-survival | **Personality:** driven | **Turns:** 20
**Checkers:** 20/23 PASS (87.0%) | **Average score:** 0.87

---

## 1. Phase Engine

**Verdict: FAIL**

The game was stuck in SETUP for all 20 turns. No phase transitions occurred. The convergence engine never detected sufficient pressure to escalate to RISING, meaning the pacing system failed to build narrative tension over time.

Phase trajectory: `SETUP` x20 (every turn)

---

## 2. Convergence Score

**Verdict: FAIL**

Convergence scores ranged 0–2 across 20 turns. Never reached the >=3 threshold needed for RISING entry.

```
Turn | Thread | Depth | Age | Beat | Dice | Score
  1  |   0    |   0   |  0  |  0   |  0   |   0
  2  |   0    |   0   |  0  |  1   |  0   |   1
  4  |   0    |   0   |  1  |  1   |  0   |   2
  6  |   0    |   0   |  1  |  1   |  0   |   2
 20  |   0    |   0   |  1  |  1   |  0   |   2
```

All 20 turns: thread_weight=0, urgency_depth=0, dice_weight=0. The only occasional contributors were beat_streak (+1) and scene_age (+1). Score never exceeded 2.

**Root cause:** The scoring components (thread_weight, urgency_depth, dice_weight) all require urgent threads or dice failures with urgent threads. The driven persona's passive inputs never created urgent threads, and the ruling pipeline never assigned stakes to repetitive compliance actions.

---

## 3. Curtain Call

**Verdict: N/A**

No CLIMAX turns occurred, so curtain call was never activated.

---

## 4. GM Beat Lifecycle

**Verdict: FAIL**

23 beats generated across 20 turns. Beat type distribution:

| Type | Count | % |
|------|-------|---|
| revelation | 10 | 43% |
| pressure | 6 | 26% |
| setback | 2 | 9% |
| complication | 1 | 4% |
| opportunity | 1 | 4% |

Two consecutive streaks of 3+ same-type beats:
- `revelation` x3: turns 7, 8, 9
- `revelation` x3: turns 14, 15, 16

The `beat_phase_validity` checker flagged T19 where `pressure` was not allowed in SETUP phase (allowed: breathing_room, callback, hazard, opportunity, revelation, setback).

Beat variety was poor — revelations dominated (43%), indicating the storyteller was stuck in a "reveal information" loop rather than creating dynamic tension.

---

## 5. Thread Lifecycle & Arc Goals

**Verdict: PASS (barely)**

- Created: 4
- Resolved: 2 (50%)
- Hallucinated: 0
- Pending: 2

Thread progression was minimal — most showed tiny incremental updates (0.50->0.53->0.56 pattern) that triggered dedup rejections. Several thread updates were skipped by the sanitizer as invalid:

```
thread_sanitizer: skipping invalid thread_update resource_scarcity_coverup
thread_sanitizer: skipping invalid new_thread militia_interrogation_tension
thread_sanitizer: skipping invalid thread_update stolen_dispatch_contents
thread_sanitizer: skipping invalid new_thread militia_intake_interrogation
```

No goal changes detected across 20 turns. The arc goal remained: "Secure the necessary wiring for the water pump without alerting the Council to the true extent of the grid's failure."

---

## 6. Pacing Directives

**Verdict: FAIL**

The `pacing_directives` checker failed on T19 for the same beat type violation as above. Directives were rendered inconsistently:

- Scene Imperative: 8 turns
- Scene Pressure: 3 turns
- No directive: 9 turns

The directive tone didn't match the narrative arc because the game never progressed beyond SETUP.

---

## 7. Recent Beats History

**Verdict: PASS**

Recent beats list was properly maintained across all turns, capped at 5 entries with monotonically increasing turn numbers.

---

## 8. Inventory & Conditions

**Verdict: PASS (with major extraction quality concerns)**

Inventory integrity passed — no negative amounts, no overdraws. Final inventory:

```
Automated tracking beacon x1 (malfunctioning, internal component snapped, in jacket pocket)
Opened dispatch packet x1 (in jacket pocket)
```

However, 11 out of 20 turns had `extraction.state.empty` warnings, meaning the state extractor failed to detect any inventory or condition changes despite the player taking actions:

```
Turns with extraction.state.empty: 2, 4, 5, 6, 8, 9, 10, 12, 14, 15, 18, 19, 20
```

Conditions lifecycle passed — conditions were properly added and removed:

```
T1: +rattled
T2: -rattled
T3: +cornered
T4: -cornered
T11: +rattled
T12: -rattled
T17: +startled
T18: -startled
```

---

## 9. NPC Presence & Compendium

**Verdict: PASS**

4 NPCs tracked:

```
vincent_owens: Vincent Owens — Former neighbor and current militia scout
unknown_scout: Unknown Scout
militia_guards: Two militia guards
militia_courier: Militia Courier
```

No NPC ghosting detected. Compendium lifecycle passed — all NPC updates were properly tracked. NPC presence was consistent.

---

## 10. Location & Scene Transitions

**Verdict: FAIL**

The `location_change` checker failed on T12 where a location_change was emitted but the post-turn location ID was unchanged (barretthaven_main_thoroughfare). Known bug TICK-26: `applied.location_change` doesn't exist in events — field is `applied.location_description`.

Location transitions:

```
farm_outskirts -> barretthaven_main_thoroughfare -> intake_office_interior
```

Scene tags evolved from "tension near maintenance terminal" to "dim light, boxed in."

---

## 11. Sanitizer Lifecycle

**Verdict: PASS**

All sanitizer checks passed. Thread IDs matched between storyteller and sanitizer where applicable.

---

## 12. Warning Signals

**Verdict: FAIL**

```
extraction.state.empty: 11 turns (2, 4, 5, 6, 8, 9, 10, 12, 14, 15, 18, 19, 20)
thread_sanitizer invalid: 5 warnings
thread_updates.dedup: 6 rejections
```

No retry errors or rejected items. The extraction.empty pattern is the dominant issue — the state extractor consistently failed to detect changes even when inventory/items clearly changed in the narrative.

---

## 13. Prompt Size Analysis

**Verdict: PASS**

Token counts showed a slight decreasing trend across all stages (Total in: -165.7/turn), which is unusual — context should accumulate. This suggests context trimming is working aggressively or the prompt template is being optimized.

```
Total tokens: 14,257-15,969 in, 673-1,039 out
Average turn time: 28.3 seconds
```

---

## 14. Roll Distribution

```
Fail:      5 (55.6%)
Success:   2 (22.2%)
Partial:   1 (11.1%)
Crit:      1 (11.1%)
```

Heavy failure rate (55.6%) combined with the driven persona should have created escalation pressure, but the engine didn't convert these failures into phase progression.

---

## Root Cause Analysis

**The convergence scoring has a latent bug: it doesn't account for sustained scene pressure through beat patterns alone.**

The scoring components (thread_weight, urgency_depth, dice_weight) all require urgent threads or dice failures with urgent threads. The driven persona's passive inputs never created urgent threads, and the ruling pipeline never assigned stakes to the repetitive compliance actions.

**Circular dependency chain:**

1. The driven persona produced passive, repetitive inputs (reaching, withdrawing, showing hands)
2. The ruling pipeline classified ~60% of turns as `routine` or `trivial` — no dice, no stakes
3. The thread system had 4 threads but they were `advancement`/`shielding` kind, not `urgent` kind — thread_weight stayed 0
4. Scene_age stayed 0 because the scene never transitioned out of SETUP
5. With thread_weight=0, urgency_depth=0, scene_age=0, dice_weight=0, only beat_streak and scene_age could contribute (max +1 each)
6. Score maxed out at 2, never reaching the >=3 threshold for RISING
7. No phase escalation -> no new scene context -> no fresh thread urgency -> score stays low -> loop

**Player input pattern (the loop):**

```
T1:  I approach the maintenance terminal and begin prying open the casing...
T2:  I slowly pull the pliers away... keeping my hands visible...
T3:  I reach slowly for my belt to retrieve the Copper Coil...
T4:  I slowly pull my hand away... raise my palms in a non-threatening gesture.
T5:  Slowly reach for my belt to unbuckle it, keeping my hands visible...
T6:  I slowly reach for the heavy pliers and hold them up...
T7:  I walk toward the settlement perimeter without resisting, keeping my hands visible...
T8:  I walk toward the intake office, keeping my hands visible...
```

"Keeping my hands visible" appears 5 times. "Slowly" appears 6 times. The inputs are passive compliance loops.

**Ruling classifications confirm the loop:**

```
T2: routine (non-confrontational movement)
T3: routine (retrieving item)
T4: trivial (non-threatening gesture)
T5: routine (complying with a command)
T6: trivial (routine gesture of de-escalation)
T7: routine movement
T8: routine movement
T11: trivial (routine compliance)
T13: routine movement
```

**Your own game worked because you played actively** — making decisions that forced rulings with stakes, creating urgent threads, triggering dice failures with consequences. The driven persona's automated behavior was too passive to break out of the SETUP trap.

---

## Recommendations

1. **Convergence scoring needs a sustained pressure component** — beat_streak should contribute more when pressure beats accumulate over multiple turns, even without urgent threads.

2. **The ruling pipeline should auto-escalate** when it consistently classifies actions as routine/trivial (indicating the player is stalling). A threshold of 3+ consecutive routine classifications could trigger a stakes override.

3. **The driven persona needs tuning** — its automated behavior is too passive. It should be more likely to take decisive actions that create stakes.

4. **Extraction pipeline needs investigation** — 55% of turns had empty state extraction, meaning the game state was largely invisible to downstream systems.
