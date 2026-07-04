---
title: "Band outcomes don't drive narration — beats override success/fail results"
status: testing
urgency: 2
size: large
created: 2026-07-04
ticket_id: I-25
labels:
  - engine
  - pacing
---

## Problem

When the player rolls success or crit_success on an escape/extraction attempt, the narrator fails to deliver narrative relief. The band says "you succeed" but the beat pool (phase-constrained escalation types) and outcome_hint (scene_motion from ruling LLM) push the scene deeper into tension instead of forward.

### Concrete example (cordyceps-year-twenty-2026-07-04)

- **Turn 4:** SUCCESS (roll 10). Player intent: "I'll give you a couple of my rations for passage." Narration: scout takes rations but 2 more scouts appear from rooftops, perimeter tightens. Player is *worse off* than before the roll.
- **Turn 5:** CRIT_SUCCESS (roll 12). Player intent: "Signal Michael Rosales to prepare for a sudden sprint." Narration: leader's headset malfunctions, player gets a "window" and dives behind a van. Still in the opening scene. No narrative relief.

The band result is authoritative per `narrate_user.j2:84`, but the narrator has no clear mechanism to reconcile band with beat and outcome_hint when they conflict.

## Root Causes

### 1. Band directives are generic, not intent-aware

`ccya/rules.py:53-61` — success and crit_success directives are one-liners:
```
success: "Clean success — you do what you intended."
crit_success: "Best possible outcome — something unexpected goes in your favour."
```

No guidance on *how* to fulfill the intent. No connection to the player's stated action (which the narrator has in the prompt). Compare to fail/setback/partial which get specific, actionable directives tied to intent verb category (combat/social/exploration/movement).

### 2. Beat is given equal authority to band in the system prompt

`narrate_system.j2:72`:
```
Override rule: The outcome hint, pending GM beat, and curtain call are authoritative scene signals.
```

The beat is called "creative guidance" in the user prompt (`narrate_user.j2:93`) but "authoritative" in the system prompt. The system prompt wins with the LLM.

### 3. Beat pool has no band awareness

`ccya/engine/_pacing.py:18-30` — `BEAT_PHASE_MAP` constrains beats by scene phase only. SETUP/RISING phases get pressure/complication/escalation/revelation/twist beats regardless of band result. On a crit_success, the beat pool is identical to a fail — all escalation types.

### 4. outcome_hint is decoupled from band

`_compute_pacing_context` in `_pacing.py:157-197` computes `outcome_hint` from the ruling engine's `scene_motion`, with two hard overrides:
- Scene Imperative (scene_age >= 5): forced to "transition"
- Convergence hard gate (score >= threshold during RISING/CLIMAX): forced to "transition"

The ruling engine's `scene_motion` is decided by the ruling LLM, not by the band. So the narrator gets a success directive + hold outcome_hint + escalation beat — three conflicting signals with no priority hierarchy.

### 5. No authority hierarchy for narrator inputs

The narrator receives: band (BINDING), rules_outcome directive, beat, outcome_hint, scene phase, curtain call. There's no explicit ranking of these inputs when they conflict. The "player input > GM beat > outcome hint" priority in `narrate_system.j2:11` only covers player input, not the band.

## Proposed Changes

### A. Strengthen band directives in `ccya/rules.py`

Make directives intent-fulfillment biased and explicit about how success should manifest:

```python
success: [
    "You do what you intended. Fulfill the player's stated goal directly.",
    "Note any minor consequence if the fiction demands it.",
],
crit_success: [
    "You do what you intended, fully and decisively. The outcome serves as a clear turning point.",
    "Succeed outstandingly; gain a meaningful additional benefit that advances the scene.",
],
```

For partial, also strengthen: add explicit "you get what you wanted" signal so it's clear partial = win-with-cost, not loss-with-glimmer.

### B. Add authority hierarchy to `narrate_system.j2`

Add a new section in the system prompt establishing priority order:

```
## Narration Priority (BINDING)

When scene signals conflict, resolve in this order:

1. **Band result + rules_outcome directive** — highest authority. Dictates whether the player's intent is fulfilled, compromised, or denied.
2. **Outcome hint (advance/hold/transition)** — dictates scene motion. On success/crit_success with player intent to exit, bias toward advance/transition.
3. **Beat** — creative guidance only. Use as environmental texture. Discard or reframe if it contradicts the band.
4. **Scene phase** — constraint on beat types, not a driver of scene direction.

**Critical:** On success/crit_success, the player's intent MUST be fulfilled. If the beat contradicts this, treat the beat as flavor/texture only — do not let it override the band.
```

### C. Remove beat from override rule in `narrate_system.j2`

Change line 72 from:
```
Override rule: The outcome hint, pending GM beat, and curtain call are authoritative scene signals.
```
To:
```
Override rule: The outcome hint and curtain call are authoritative scene signals. The GM beat is creative guidance — use it as texture, not direction.
```

### D. Negative bands should always offer exit routes

On fail/setback/partial: always provide at least one viable path forward — move, change scene, change situation. Never trap the player with no forward motion. This works with the outcome_hint/transition signals: if a transition is available, the failure should enable it rather than block it.

### E. Connect band to outcome_hint in `_pacing.py` (follow-up)

Out of scope for this ticket. Requires plumbing `intent_verb` through `turn_context.py` → `_pacing.py`. Worth doing but deferred to a follow-up ticket.

### F. Phase-aware beat selection (optional, later)

When band is success/crit_success, prefer relief-type beats (opportunity, breathing_room) over pressure-type beats when the phase allows. This doesn't change the phase map — just biases beat selection downstream.

## Files to Touch

- `ccya/rules.py` — band directives (A) + partial directive (D)
- `ccya/prompts/narrate_system.j2` — authority hierarchy section (B), remove beat from override rule (C)
- `ccya/engine/_pacing.py` — out of scope (follow-up)

## Decisions Made

1. **E (intent_verb → outcome_hint)** — Deferred. Requires plumbing `intent_verb` through `turn_context.py` → `_pacing.py`. Follow-up ticket.
2. **F (phase-aware beat selection)** — Deferred. Separate concern, marked optional.
3. **B (authority hierarchy)** — Goes in `narrate_system.j2` (system prompt), not `narrate_user.j2`. System prompt is where rules/priorities live; user prompt is for dynamic content.
4. **Partial directive** — Should also be strengthened with explicit "you get what you wanted" signal so it's clear partial = win-with-cost, not loss-with-glimmer.
5. **D (negative bands exit routes)** — Added as a new section: failures must always provide at least one viable path forward.

## Done When

- A crit_success on an escape attempt produces clear narrative relief and scene motion toward exit
- The narrator explicitly fulfills the player's stated intent on success, with beat as texture not direction
- No conflict between band and beat produces a worse outcome than the pre-roll state on a success roll

## Evaluation Findings (2026-07-04)

### space-western run (15 turns, gemma-4-26b-a4b-it)

**Pacing stuck in SETUP:**
- All 15 turns show `scene_phase: SETUP`
- `convergence_score` ranges 1-4 (never reaches climax threshold)
- `climax_turn_count: 0` throughout
- No scene transitions occurred despite multiple success/crit_success rolls
- This confirms the ticket's core problem: positive bands don't produce narrative relief or scene motion

**Outcome hints vs band conflicts:**
- Turn 3: SUCCESS band, outcome_hint `advance`, but scene stayed in SETUP
- Turn 7: CRIT_SUCCESS band, outcome_hint `advance`, but scene stayed in SETUP
- Outcome hints sometimes match band (T3 advance), sometimes conflict (T7 advance but no relief)
- Narration consistently escalates tension despite positive rolls
- Beat pool (pressure/complication/escalation) is identical for success and fail — no band awareness

**Roll distribution (8 rolls examined):**
- crit_fail: 37.5% (3/8)
- fail: 12.5% (1/8)
- setback: 12.5% (1/8)
- partial: 12.5% (1/8)
- success: 12.5% (1/8)
- crit_success: 12.5% (1/8)
- Heavy skew toward negative bands (50% crit_fail + fail)
- Only 2 positive rolls out of 8, neither produced narrative relief

**Conclusion:** The ticket's proposed fixes (A: strengthen band directives, B: authority hierarchy, C: remove beat from override rule) are validated. The narrator has no mechanism to reconcile success band + escalation beat + hold outcome_hint. Pacing never advances because negative bands dominate and positive bands don't produce relief.

### Pacing Analysis (2026-07-04)

**Scene stuck in SETUP — convergence score cannot accumulate (FIXED):**
Three changes made (pacing.py + config.py):
1. Removed scene_age from `compute_convergence_score` (used by narration directive, not convergence)
2. Lowered `convergence_enter_threshold` from 3 to 2 (score would be 2 at minimum, triggering transitions)
3. Fixed beat_streak counting (pacing.py:103-108) — was tracking `last_non_null_type` and only counting pressure beats that appear AFTER a pressure-type was seen. Now counts total pressure-type beats in window vs threshold (60% majority)
