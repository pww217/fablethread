# Findings — Combat duration eval (ev save 20260614_210345_c56485, 2026-06-14)

Eval run: `ev.py play --llm --personality aggressive_plan --turns 20`
Events: `saves/ev/20260614_210345_c56485/events.jsonl`
Turns: 17 total, combat from ~turn 8 through 17 (10 turns)
Diagnosis: `ev.py mechanics N --pacing saves/ev/latest/events.jsonl`, `ev.py prompt N storytell saves/ev/latest/events.jsonl`

---

## 1. `outcome_hint` never overrides to `"transition"` (dead code path)

**Severity:** BUG — Scene Imperative repeatedly tells the LLM to "break the loop — force a decisive outcome" but the companion instruction "If outcome_hint is 'transition', move to a new scene/location" never activates.

**Root cause:** `turn.py:475-476` checks for the crisis turn limit override:

```python
# turn.py:472-476
# outcome_hint: primarily driven by scene_motion from ruling engine.
# When phase CRISIS hits turn limit, override to "transition".
outcome_hint: str | None = scene_motion

if scene_phase == "CRISIS" and crisis_turn_count >= crisis_turn_limit:
    outcome_hint = "transition"
```

But `_compute_scene_phase()` runs **immediately before** `_compute_pacing_context()` (lines 794 vs 800), and inside `_compute_scene_phase()` at lines 564-568:

```python
# turn.py:564-568
elif phase == "CRISIS":
    crisis_turn_count += 1
    if crisis_turn_count >= config.crisis_turn_limit:
        phase = "RESOLUTION"
        crisis_turn_count = 0  # <-- reset BEFORE outcome_hint check
```

By the time `_compute_pacing_context()` checks `crisis_turn_count >= crisis_turn_limit`, the counter has already been reset to 0. The condition never evaluates to True.

**Evidence across all combat turns:**

```
Turn 8:  SETUP      outcome=hold     transition override? NO
Turn 9:  RISING     outcome=advance  transition override? NO
Turn 10: CRISIS     outcome=advance  transition override? NO (count=1)
Turn 11: CRISIS     outcome=advance  transition override? NO (count=2)
Turn 12: CRISIS     outcome=advance  transition override? NO (count=3)
Turn 13: RESOLUTION outcome=hold     transition override? NO (count=0, reset)
Turn 14: BREATHER   outcome=advance  transition override? NO
Turn 15: RISING     outcome=advance  transition override? NO
Turn 16: CRISIS     outcome=advance  transition override? NO (count=1)
Turn 17: CRISIS     outcome=advance  transition override? NO (count=2)
```

`outcome_hint` was **never** `"transition"` in any of 17 turns.

The system prompt at `storytell_system.j2:89` tells the LLM:

> Scene age backstop: When effective_scene_age exceeds the threshold, Scene Imperative fires. It means break the loop — force a decisive outcome or transition. Not more pressure beats. **If outcome_hint is 'transition', move to a new scene/location.**

The first sentence fires (Scene Imperative fires every turn from T8 onward). The second sentence is conditional — it only activates when `outcome_hint == "transition"`, which never happens.

### Proposed fix

**Option A — Move the override before the phase check (recommended)**

The `outcome_hint` override should be computed **before** the phase machine resets the counter, or it should check `effective_scene_age` instead:

```python
# Before (turn.py:472-476):
outcome_hint: str | None = scene_motion

if scene_phase == "CRISIS" and crisis_turn_count >= crisis_turn_limit:
    outcome_hint = "transition"

# After:
outcome_hint: str | None = scene_motion

if effective_scene_age >= scene_imperative_threshold:
    outcome_hint = "transition"
```

This makes the override fire whenever Scene Imperative fires from scene age (which is every turn once scene_age >= 4), matching the prompt's intent.

**Option B — Check before reset (more targeted)**

Pass a `crisis_expired` flag from `_compute_scene_phase()` that records whether crisis just expired before the reset:

In `_compute_scene_phase()`:
```python
elif phase == "CRISIS":
    crisis_turn_count += 1
    crisis_expired = crisis_turn_count >= config.crisis_turn_limit
    if crisis_expired:
        phase = "RESOLUTION"
        crisis_turn_count = 0
    # Add to return
```

Then in `_compute_pacing_context()`:
```python
if scene_phase == "CRISIS" and (crisis_turn_count >= crisis_turn_limit or crisis_expired):
    outcome_hint = "transition"
```

Option A is simpler and more robust — scene age is the signal that drove Scene Imperative in the first place.

---

## 2. Scene Imperative has no resolution beats

**Severity:** BUG — The LLM is told "break the loop — force a decisive outcome" but every allowed beat (revelation, twist, hazard, callback, opportunity) extends the scene rather than resolving it.

**Root cause:** `_pacing.py:74-75`:

```python
if directive == "Scene Imperative":
    return BEAT_BUCKETS["situation"] + ["opportunity"]
```

Which resolves to `["revelation", "twist", "hazard", "callback", "opportunity"]`.

Beat classification from `_pacing.py:15-19`:

```python
BEAT_BUCKETS = {
    "pressure":  ["pressure", "complication", "escalation"],
    "situation": ["revelation", "twist", "hazard", "callback"],
    "relief":    ["opportunity", "breathing_room"],
}
```

The Scene Imperative list contains:
- **situation bucket** (revelation, twist, hazard, callback) — these *change the situation*, they don't end it. A twist introduces a new complication. A revelation reveals information. A hazard adds danger. A callback recontextualizes.
- **opportunity** — opens a new path, giving the player *more* options rather than fewer.

**Missing:** `setback`, `breathing_room` — the only beats that mean "the scene ends (for better or worse)."

The roll band table at `storytell_system.j2:78-85` confirms this:

```
| Band | Beat |
|---|---|
| crit_success / success | opportunity, escalation, or breathing_room |
| partial | complication or pressure |
| setback / fail | breathing_room, null, or setback. Never escalation or pressure — failure is the consequence. |
```

On FAIL bands (most combat turns), the recommended beats are `breathing_room, null, or setback`. But Scene Imperative overrides the band table (line 76: "Phase overrides roll band"), so these recommendations are invisible to the LLM.

**Evidence:**

Actual LLM beats selected across all combat turns:

```
Turn 8:  twist     (npc_behavior) — situation-changer, allowed
Turn 9:  twist     (npc_behavior) — situation-changer, allowed
Turn 10: twist     (npc_behavior) — situation-changer, allowed
Turn 11: twist     (npc_behavior) — situation-changer, allowed
Turn 12: (null)                    — no beat
Turn 13: (null)                    — no beat
Turn 14: (null)                    — no beat
Turn 15: (null)                    — no beat
Turn 16: revelation (npc_behavior) — situation-changer, allowed
Turn 17: opportunity (item)        — opens new path, allowed
```

Zero resolution beats across 10 turns. The LLM did exactly what it was told — it picked from the allowed list. The allowed list just has no way to say "the fight is over."

### Proposed fix

**Option A — Add `setback` and remove `twist` from Scene Imperative allowed list (recommended)**

```python
# Before (_pacing.py:74-75):
if directive == "Scene Imperative":
    return BEAT_BUCKETS["situation"] + ["opportunity"]

# After:
if directive == "Scene Imperative":
    return ["revelation", "hazard", "callback", "opportunity", "setback"]
```

This gives the LLM two paths:
- Situation-changers (revelation, hazard, callback) for info-revealing or environment-shifting resolutions
- Opportunity to offer an escape route
- Setback to end the scene badly (capture, injury, loss)

And removes `twist` which was the main source of infinite escalation (every twist just introduced the next complication).

Also update the system prompt at `storytell_system.j2:71`:

```
Before:
- **Scene Imperative** — only: `revelation`, `twist`, `hazard`, `callback`, `opportunity`. **NEVER** `pressure`, `complication`, `escalation`.

After:
- **Scene Imperative** — only: `revelation`, `hazard`, `callback`, `opportunity`, `setback`. **NEVER** `pressure`, `complication`, `escalation`.
```

**Option B — Add `setback` but keep `twist`**

```python
return ["revelation", "twist", "hazard", "callback", "opportunity", "setback"]
```

Pro: preserves twist as an option. Con: twist was the main source of infinite escalation in this eval.

---

## 3. Thread `clear_the_road_toughs` never resolves, locks phase machine in combat cycle

**Severity:** BUG — Thread is updated every turn for 10 turns with a new progress_kind entry, keeping it URGENT. This URGENT status forces the phase machine to cycle CRISIS→RESOLUTION→BREATHER→RISING→CRISIS, never escaping combat.

**Root cause:** The LLM emits `thread_update` (not `thread_resolve`) on `clear_the_road_toughs` every single turn from T6 through T16:

```
T6:  [ADVANCEMENT] Bald Tough approaches from the mist
T7:  [ADVANCEMENT] Bald Tough confronts courier in the street
T8:  [SHIFT] negotiating bribe with Bald Tough in the mist
T9:  [SETBACK] negotiation fails as Bald Tough rejects bribe
T10: [SETBACK] Bald Tough pins courier in mist
T11: [ADVANCEMENT] Bald Tough incapacitated by knee strike
T12: [SETBACK] Bald Tough slams into courier
T13: [SHIFT] Bald Tough closes distance while Scarred Tough flanks left
T14: [SHIFT] Bald Tough closes distance while Scarred Tough flanks left
T15: [SETBACK] Scarred Tough flanks and grabs your cloak
T16: [RESOLVED] Bald Tough killed, Scarred Tough incapacitated
```

The prompt at `storytell_system.j2:22-26` says:

> **`thread_resolve`:** Use when a thread concluded, failed, was absorbed into a broader thread, or urgency fully decayed. ...
> Only emit when this turn's events changed the thread's trajectory — the tension advanced, pivoted, or resolved.
> **If a thread went unaddressed for 3+ turns, resolve or demote rather than update.**

But the thread was **never unaddressed** — the LLM updated it every single turn. The "3+ turns unaddressed" guardrail never triggered.

The URGENT status actively drives the phase machine. In `turn.py:553-562`:

```python
elif phase == "RISING":
    if thread_urgency_count >= config.crisis_urgency_threshold:  # default 2
        phase = "CRISIS"
    elif thread_urgency_count >= 1 and tension_delta == "escalates":
        phase = "CRISIS"
```

With `clear_the_road_toughs` URGENT and tension_delta always "escalates", the RESOLUTION→BREATHER→RISING path immediately re-enters CRISIS on the next RISING phase turn. The combat cycle never breaks.

**Evidence of phase cycling due to thread URGENCY:**

```
Turn 13: RESOLUTION (crisis_turn_count hit 4, forced exit)
Turn 14: BREATHER   (single turn, URGENT thread forces immediate exit)
Turn 15: RISING     (URGENT thread + escalates → immediate CRISIS)
Turn 16: CRISIS     (back in combat, count=1)
Turn 17: CRISIS     (still going, count=2)
```

If the thread had been resolved or demoted to NORMAL/background at any point, the BREATHER phase would have lasted its full 3-turn duration, and RISING would not have immediately re-entered CRISIS.

### Proposed fix

**Option A — Add update-count backstop to prompt guidance (recommended)**

Add guidance that a thread updated N+ times without resolution should be force-resolved or demoted, regardless of active updates:

```
Before (storytell_system.j2:28):
**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation.

After:
**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation.
**If a thread has been updated 5+ times without resolution, resolve or demote it instead of adding another update.** Repeatedly advancing/pivoting the same thread without concluding it wastes narrative momentum.
```

**Option B — Add urgency decay in the state machine**

In `turn.py`, add urgency decay logic that automatically demotes threads that have been URGENT for N+ turns without resolution:

```python
# In _compute_scene_phase() or a new urgency_decay function:
for t in threads:
    if t.urgency == "urgent" and (current_turn - t.last_updated) >= config.urgency_decay_threshold:
        t.urgency = "normal"  # demote
        logger.info(f"Thread {t.id} urgency decayed from urgent to normal")
```

With config default `urgency_decay_threshold = 3` (turns). This would automatically demote the thread after 3 turns of being URGENT, breaking the phase cycle without requiring LLM compliance.

**Option C — A + B combined (recommended)**

Option A addresses the LLM behavior directly. Option B is a hard guardrail if the LLM ignores A. Both are small, independent changes.

---

## Additional observations (not bugs)

### `tension_delta` distribution analysis (2026-06-15)

Across this save's 17 turns: `escalates` 52.9%, `maintains` 47.1%, `de-escalates` 0%. Combined with 3 other saves (80 total turns): `de-escalates` 0% across all. The convergence design removes `tension_delta` from `IntentEnvelope` entirely — field deleted from model, not merely unused. Confirmed correct by this data.

### Dice variance amplified the combat

The player rolled below 5 (on d12) for 6 of 8 combat checks, including consecutives of 3, 3, 2, 4. With only +1 stat bonus, these were all FAIL or SETBACK. This is expected variance — not a bug, but it made the combat feel longer than it would have with average luck.

### Consecutive TWIST diversity violation

The LLM generated TWIST on turns 8, 9, 10, 11 — 4 consecutive times. The prompt says "Don't repeat the same type more than twice consecutively" (storytell_system.j2:91), but this is a soft guideline with no Python enforcement.

Fixing Bug #2 (removing twist from Scene Imperative allowed list) also fixes this — twist can't repeat if it's not in the allowed list.

### BREATHER as a single-turn waste

With an URGENT thread, BREATHER exits immediately to RISING. The player gets no actual recovery. This is by design (URGENT threads demand immediate attention), but it means BREATHER is effectively useless during combat.

Not a bug, but worth noting: BREATHER's effectiveness depends on thread resolution. If Bug #3 is fixed (thread demoted from URGENT), BREATHER would last its full 3 turns.

---

## Summary of fixes

| # | Bug | Where | Fix |
|---|-----|-------|-----|
| 1 | `outcome_hint` never becomes `"transition"` | `turn.py:475-476` | Check `effective_scene_age >= scene_imperative_threshold` instead of crisis counter (post-reset) |
| 2 | Scene Imperative has no resolution beats | `_pacing.py:74-75`, `storytell_system.j2:71` | Remove `twist`, add `setback` to allowed list |
| 3 | Thread stays URGENT forever, locks phase cycle | `storytell_system.j2:28` | Add update-count backstop guidance + optional urgency decay in state machine |

Each fix is independent and small. Fix #1 alone would likely have the biggest impact — it would make outcome_hint "transition" reach the LLM, telling it to "move to a new scene/location" every turn once Scene Imperative is active.

---

## Follow-up eval: Fix #1 tested (2026-06-15)

Eval run: `ev.py play --llm --personality driven --pack allied-ww2 --turns 20 --eval`
Events: `saves/ev/20260615_000039_5cc4fc/events.jsonl`
Turns: 20 total, combat from T3 through T20 (18 turns, single cellar scene)
Fix applied: `turn.py:475-476` — `outcome_hint` override changed from `crisis_turn_count >= crisis_turn_limit` to `effective_scene_age >= scene_imperative_threshold`

### Fix #1 status: Working as intended

`outcome_hint: transition` now fires correctly. Before the fix it was **never** "transition" across 17 turns. After the fix:

| Turn | Phase | outcome_hint |
|------|-------|--------------|
| 4 | CRISIS | advance |
| 8 | BREATHER | **transition** |
| 12 | CRISIS | **transition** |
| 16 | CRISIS | **transition** |
| 20 | BREATHER | **transition** |

The root cause (crisis counter reset before the check) is fixed.

### Doom spiral status: NOT resolved

The game is still locked in combat through all 20 turns. The LLM is in a cellar with German soldiers the entire time. Here's why:

**Fix #1 is working but insufficient alone.** The LLM receives `outcome_hint: transition` + `Directive: Scene Imperative` but:

1. **Allowed beats are all situation-changers** (Bug #2): `revelation, twist, hazard, callback, opportunity` — none of these end a scene. The LLM has no resolution beat available.

2. **Thread never resolves** (Bug #3): `enemy_encroachment` stays URGENT and gets updated every turn. The LLM never emits `thread_resolve`. This keeps tension_delta escalating and prevents BREATHER from lasting.

3. **No update-count backstop**: The LLM updates the same thread 12+ times without resolution. No prompt guidance tells it to stop.

### Checker results

24/25 pass. Only `pacing_directives` fails (Turn 4: `breathing_room` not allowed in CRISIS — pre-existing issue, unrelated to this fix).

### Conclusion

Fix #1 is correct and working as intended. But combat doom spirals require **all three fixes** (Bug #1 + #2 + #3) to actually break. Fix #1 alone just sends the right signal — the LLM still has no way to act on it.

---

## Follow-up: Three Supporting Changes (2026-06-15)

After further analysis of 81 EV turns across 3 persona/scenario pairs, three additional changes were decided alongside the convergence design. All directly address the combat spiral and condition accumulation observed in this eval:

### Change A: Dice roll frequency (~69% → ~35-45%)
The ruling prompt criteria were tightened to only trigger rolls at major narrative pivots. Thread context (urgent thread summary + last 3 progress entries) was added to the ruling user prompt so the LLM can assess thread relevance. Fewer rolls means fewer FAIL bands feeding the spiral.

### Change B: Band rebalancing (partial ≤8 → ≤7)
Conditions analysis showed 18:1 negative-to-positive ratio across all runs, with 55% of rolls at hard difficulty and 64% of reasons citing conditions. Shifting the partial threshold from ≤8 to ≤7 compensates: at typical condition load (-1 mod), the effective good rate goes from ~33% to ~42%.

### Change C: Positive condition extraction
The state extractor now has success-guarded positive condition heuristics. Combined with the existing 5-cap on total conditions, this creates space for positives while limiting negative stacking.

All three are documented in `docs/design/convergence-scoring-design.md` (Supporting Changes section) and `docs/design/ev-tool-audit-design.md`.
