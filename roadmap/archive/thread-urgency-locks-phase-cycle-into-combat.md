---
title: "[Scene] Thread urgency locks phase cycle into combat spiral"
status: done
urgency: 2
size: medium
created: 2026-06-15
labels:
  - Improvement
  - World Building
---

## Detail

URGENT threads lock the phase machine into a CRISIS→RESOLUTION→BREATHER→RISING→CRISIS cycle. When a thread stays URGENT across many turns (e.g., `clear_the_road_toughs` updated 9 times over 10 turns), RESOLUTION exits to a single-turn BREATHER (line 578: `thread_urgency_count > 0` triggers immediate exit), and RISING immediately re-enters CRISIS (line 554-558: `thread_urgency_count >= 2`). The scene never escapes combat.

This is a design tension, not a pure bug. Threads provide narrative input to the phase machine — without them, the cycle becomes a predictable 4-turn loop (SETUP→RISING→CRISIS→RESOLUTION) with no connection to fiction. But the current coupling creates spiral lockups where a single thread can keep a scene stuck for 10+ turns.

## Tradeoffs

### Option A: Dissociate threads from pacing

Remove thread urgency from phase transitions. The cycle becomes a fixed 4-turn loop (SETUP→RISING→CRISIS→RESOLUTION→BREATHER→RISING...).

* **Pro:** No spiral lockups, predictable pacing
* **Con:** Loses narrative input — phase cycle no longer responds to story state, becomes mechanical

### Option B: Force-down urgency on Scene Imperative

When Scene Imperative fires (scene is stale), demote URGENT threads to NORMAL.

* **Pro:** Breaks the cycle mechanically, no LLM compliance needed
* **Con:** Narrative whiplash — "Scene Imperative says this is urgent, but thread just demoted"

### Option C: Prompt guidance (soft guardrail)

Tell the LLM to resolve or demote threads updated 5+ times without resolution.

* **Pro:** Preserves narrative input, LLM-controlled
* **Con:** Eval shows LLM ignores it — thread was updated every single turn anyway

### Option D: Hybrid — one-turn grace on Scene Imperative

When Scene Imperative fires, skip BREATHER's immediate exit on URGENT threads for one turn. Give the LLM one turn of breathing room to actually end the scene (now that outcome_hint="transition" is firing from bug #1 fix).

* **Pro:** Less whiplash than full demotion, gives transition signal time to take effect
* **Con:** Still some thread coupling, doesn't fully solve spiral

## Open questions

1. Is thread urgency the right signal for phase transitions, or should it be based on scene tags (e.g., "combat") + scene age?
2. If we keep thread coupling, should urgency decay automatically after N turns (configurable threshold)?
3. Does fixing bug #1 (outcome_hint="transition" firing) naturally solve this — if the LLM gets a strong "move to a new scene" signal, it resolves threads itself?

## Related

* TICK- (bug #1): outcome_hint never becomes "transition" — fixed
* `docs/findings/combat-duration-eval-2026-06-14.md` — eval evidence
