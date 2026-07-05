---
title: "Band outcomes don't drive narration — beats override success/fail results"
status: implemented
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

### Convergence Deep Dive — Root Cause Found (2026-07-04)

**Problem:** Convergence score hits 3+ but phase stays in SETUP across all 6 eval runs (noir-1930s, space-western, golden-piracy, zombie-survival, allied-ww2).

**Correction (2026-07-04):** Root cause #6 (thread data source mismatch) is **WRONG**. Tracing `narrate.py:176-211`:

- Line 180: `_raw_thread_dicts = [t.model_dump() for t in state.long_term_objective.threads]`
- Line 197-204: `compute_convergence_score(..., active_threads=_raw_thread_dicts, ...)`
- Line 211: `_compute_scene_phase(state, ...)`

Both read from `state.long_term_objective.threads` at narrate time. The event data divergence in `convergence_threads` vs LTO threads is post-save, not narrate-time.

### Real Root Cause: Phase transitions never persist

`_compute_scene_phase` returns a new `Scene` object at `narrate.py:211`, but nowhere in the codebase writes `new_scene` back to `state.scene`. The result is only used locally:

1. Line 212: `scene_phase = new_scene.scene_phase` — reads new phase
2. Line 216-225: `_compute_pacing_context(scene_phase=scene_phase, ...)` — uses new phase for directive computation
3. Line 227-229: stores convergence data in `_pc` (PacingContext)

The `_pc` is passed to event logging (`turn.py:607-624`) but `turn.py:611` reads `state.scene.scene_phase` (the OLD input value), not `new_scene.scene_phase`.

**Verified:** `turns_in_phase` in events always reflects `state.scene.turns_in_phase` which is never updated by the phase engine. The phase engine is a dead computation — it computes transitions every turn but they're discarded.

### Phase 3 Results (25-turn runs)

#### zombie-survival:cautious (25 turns)
- **Convergence:** Wildly oscillating — hits 3+ at turns 8-10, 12-13, 15, 17-19 then drops back. Phase stays SETUP entire run.
- **Band distribution:** 87.5% bad (87.5% fail, 12.5% success) — EXTREMELY negative. Player trapped.
- **Conditions at end:** 7 (very harsh)
- **Turn 5:** DELTA_VALIDATION_FAILED error

#### allied-ww2:aggressive (25 turns)
- **Convergence:** Hits 3+ at turn 9 then drops to 1 (turns 16-25). Phase stays SETUP.
- **Band distribution:** 42.9% bad (14.3% crit_fail, 28.6% fail, 14.3% partial, 42.9% success).
- **Conditions at end:** 3 (moderate)

### Updated Root Causes

### 7. Phase engine always reads seed state

`_compute_scene_phase` at line 223 reads `scene = state.scene` and line 228 computes `turns_in_phase = scene.turns_in_phase + 1`. Since `state.scene` is never updated (see #8), `scene.turns_in_phase` is always 0 (seed value). So `turns_in_phase = 0 + 1 = 1` every turn. The condition `turns_in_phase >= 3` never fires because the counter never accumulates.

### 8. Phase transitions never persist — ROOT CAUSE

`_compute_scene_phase` at `narrate.py:211` returns a new `Scene` object with the computed phase, but the result is never written to `state.scene`. Only `new_scene.scene_phase` is read at line 212 for directive computation. The event log at `turn.py:611` reads `state.scene.scene_phase` (the old input value), not the computed output.

**Impact:** The entire 5-state phase machine (SETUP→RISING→CLIMAX→RESOLUTION→BREATHER→RISING) is non-functional. Phase transitions are computed every turn but discarded. The scene always stays in its seed phase (SETUP for all 6 eval runs).

### Phase 3 Results (25-turn runs)

#### zombie-survival:cautious (25 turns)
- **Convergence:** Wildly oscillating — hits 3+ at turns 8-10, 12-13, 15, 17-19 then drops back. Phase stays SETUP entire run.
- **Band distribution:** 87.5% bad (87.5% fail, 12.5% success) — EXTREMELY negative. Player trapped.
- **Conditions at end:** 7 (very harsh)
- **Turn 5:** DELTA_VALIDATION_FAILED error

#### allied-ww2:aggressive (25 turns)
- **Convergence:** Hits 3+ at turn 9 then drops to 1 (turns 16-25). Phase stays SETUP.
- **Band distribution:** 42.9% bad (14.3% crit_fail, 28.6% fail, 14.3% partial, 42.9% success).
- **Conditions at end:** 3 (moderate)

### Updated Root Causes

### 7. `turns_in_phase` resets on location change

`delta_builder.py:223` sets `_stamp_turn = state.meta.turn + 1` when a location change occurs, updating `scene.turn_entered` to the current turn. `_compute_scene_phase:228` computes `turns_in_phase = scene.turns_in_phase + 1` using the preserved `scene.turn_entered`, so `turns_in_phase` resets to 0. Observed in noir-1930s: `turn_entered` changed 0→6→9→15 across three location changes. This is by design (tracking location entry), not a phase code bug, but it means `turns_in_phase` resets whenever the player changes location, making age-based transitions harder to reach.

### 8. SETUP→RISING transition has no convergence fallback — REAL ROOT CAUSE

The SETUP→RISING transition (line 238-241) uses `thread_urgency_count > 0 or turns_in_phase >= 3`. It does NOT use convergence score. This means even when convergence hits 3+ (indicating the system "wants" to advance), the phase stays in SETUP because neither condition fires. The convergence score is only used for RISING→CLIMAX, not SETUP→RISING.

**Why convergence can hit 3+ without urgent threads:** `compute_convergence_score` has 5 components (urgent_thread, threat_thread, beat_streak, roll_starvation, threat_density). Score 3+ can come from `threat_thread(1) + beat_streak(1) + roll_starvation(1) = 3` with `urgent_count=0`. The SETUP→RISING transition only checks `thread_urgency_count > 0`, ignoring these other convergence signals entirely.

#### Fix Applied (2026-07-05)

Added convergence fallback to SETUP→RISING transition in `_pacing.py:241`:

```python
if thread_urgency_count > 0 or turns_in_phase >= 3 or (convergence_score >= 2 and turns_in_phase >= 2):
```

Three exit paths from SETUP:
1. `thread_urgency_count > 0` — urgent thread pushes out (existing)
2. `turns_in_phase >= 3` — time-based fallback (existing)
3. `convergence_score >= 2 and turns_in_phase >= 2` — convergence-based exit (new)

Uses threshold 2 (default `convergence_enter_threshold`), lower than CLIMAX's 3. The `turns_in_phase >= 2` minimum prevents instant exit on turn 0.

## Phase 2 Results — Post-Persistence-Fix (2026-07-05)

### Fix Applied (2026-07-05)
Phase persistence bug fixed: `_compute_scene_phase` result now written to `state.scene` via `set_scene` method. Phase transitions now persist across turns.

### noir-1930s:driven (2342, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3 (fix confirmed)
- **Band distribution:** PASS (checker) — no skew detected
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known — scene_age and roll_starvation components mismatch)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose (I-25 prose leak fix not working or re-introduced — see I-26)

### space-western:speedrunner (0002, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3, RISING→CLIMAX at turn 8 (convergence=3 triggered transition — fix confirmed)
- **Band distribution:** FAIL — 100% fail band (2 rolls, both fail on turns 4 and 9) — small sample but skewed
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose (see I-26)

### golden-piracy:completionist (0017, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3 (fix confirmed)
- **Band distribution:** PASS — 3 success, 1 fail (25% fail — within threshold)
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose (see I-26)

### Summary (post-fix)
- **Phase persistence fix CONFIRMED:** All three new runs show SETUP→RISING transitions (noir turn 3, space-western turn 3, golden-piracy turn 3)
- **Space-western shows RISING→CLIMAX at turn 8** (convergence=3 triggered transition) — phase machine is now functional
- **Band distribution varies by scenario:** noir (67% success, 33% crit_success), golden-piracy (75% success, 25% fail), space-western (100% fail — but only 2 rolls, small sample)
- **Directive-beat alignment passes on all runs** — beats align with directives
- **Opening prose leak CONFIRMED:** The `opening` field in `pc.situation` contains full prose text (I-25 prose leak fix not working or re-introduced — see I-26)

## Turn Metrics (All 3 New Runs — 9 turns each)

### Step Breakdown (averages, excluding 0ms duplicate turns)

| Step | noir avg | piracy avg | western avg | Combined avg |
|------|----------|------------|-------------|--------------|
| **ruling** | 5.3s (2,220/112 tok) | 5.3s (2,286/116) | 5.5s (2,290/112) | **5.4s (2,265/113)** |
| **narrate** | 9.9s (3,029/209, ft=1.0s) | 11.6s (3,109/266, ft=1.0s) | 12.2s (3,029/262, ft=1.0s) | **11.2s (3,056/246, ft=1.0s)** |
| **extract** | 20.6s (8,669/409, 3 streams) | 19.6s (8,969/409, 3 streams) | 19.6s (8,829/390, 3 streams) | **19.9s (8,822/403, 3 streams)** |
| **async (sanitize/world)** | 0ms (no timing tracked) | 0ms | 0ms | **0ms** |
| **total** | **35.7s** | **36.6s** | **38.6s** | **36.9s** |

### Key observations
- **Extract dominates** — 54% of total time (19.9s), not narrate (30%) or ruling (15%)
- **3 extraction streams per turn, 0 retries** — streams are scene, state, record (sanitize/world are async)
- **Low output tokens (100-400 per step)** — LLM is NOT generating long reasoning or prose. Time is spent on API latency processing ~8,800 input tokens per call with short structured output (JSON extraction, not prose)
- **First token ~1s** — narrate streaming starts consistently after ~1 second
- **Noir fastest** (35.7s), piracy (36.6s), western (38.6s) — small variance
- **Extract input grows** (7,800→9,500 tokens) — context accumulation across turns
