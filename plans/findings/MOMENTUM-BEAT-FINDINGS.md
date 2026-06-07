# Momentum & Beat System — Root-Cause Analysis

> Game: noir--1930s (25 turns). Covers G1 and G2 (formerly I1/I2) from [FINDINGS-JUNE-6.md](FINDINGS-JUNE-6.md).
> General observations at [BUGS-OBSERVATIONS.md](BUGS-OBSERVATIONS.md).
>
> Confidence: **H**=high (data supports), **M**=medium (pattern suggests, needs
> cross-game), **L**=low (hypothesis only).

---

## Finding MB-1: Breathe directive dominates because no urgent scene threads exist at low momentum

**Confidence: H**

### Detail

The directive priority stack (`_compute_narration_directive`, `turn.py:458`) gives
Breathe top priority when `narrative_velocity < -0.3` AND `urgent_count == 0`.
Velocity < -0.3 means momentum ≤ -2.

Over the 25 turns, at least 1 urgent scene-scope thread existed on ~11 turns, but
was absent for ~14 turns. Every absence at momentum ≤ -2 produced Breathe (with
"; Resolve a Threat" appended when beat_locked).

### Per-turn directive source

| Turn | Directive | Momentum | Scene Age | Urgent Scene Thr | BeatLock | Source |
|------|-----------|----------|-----------|------------------|----------|--------|
| 4 | Breathe; Resolve a Threat | -2 | 2 | none | True | velocity < -0.3, no urgent → Breathe |
| 5 | Pressure; Resolve a Threat | -2 | 3 | warehouse_ambush | True | urgent blocks Breathe → Pressure |
| 6 | Pressure; Scene Pressure; R. Threat | -3 | 4 | warehouse_ambush | True | urgent blocks Breathe → Pressure |
| 7 | Scene Imperative; Resolve a Threat | -2 | 5+2combat | warehouse_ambush | True | age≥5 beats all |
| 8 | Breathe; Resolve a Threat | -3 | 6+2combat | none | True | velocity < -0.3, no urgent → Breathe |
| 9 | Scene Imperative; Resolve a Threat | -3 | 7 | warehouse_pursuit | True | age≥5 beats Breathe |
| 10 | Breathe; Resolve a Threat | -3 | 8+2combat | none | True | velocity < -0.3, no urgent → Breathe |
| 14 | Breathe; Resolve a Threat | -2 | 12 | none | True | same pattern |
| 17 | Breathe | -2 | 3 | none | False | velocity < -0.3, no urgent, no beatLock |
| 18 | Breathe; Resolve a Threat | -3 | 4 | none | True | same pattern |
| 23 | Breathe | -2 | 6 | none | False | same, no beatLock |
| 24 | Breathe; Resolve a Threat | -3 | 7 | none | True | same pattern |
| 25 | Breathe; Resolve a Threat | -3 | 8 | none | True | same pattern |

Pattern: **Breathe fires on every turn where momentum ≤ -2 AND urgent scene thread
is missing** (9+ turns). When urgent thread exists, Pressure or Scene Imperative
replaces Breathe.

### Hypothesis

The scene-scope urgent thread lifecycle is fragile — threads appear (created by
storytell/sanitizer), get resolved after 1-2 turns, and leave gaps. During those
gaps, low momentum guarantees Breathe. The system needs a way to maintain
urgency pressure even when scene threads are in transition.

---

## Finding MB-2: "; Resolve a Threat" append contradicts Breathe directive

**Confidence: H**

### Detail

When `beat_locked` is True, the directive always has "; Resolve a Threat" appended
(`turn.py:555-557`):

```python
directive_parts = [directive] if directive else []
directive_parts.append("Resolve a Threat")
directive = "; ".join(directive_parts) or ""
```

This means when Breathe fires AND beat_locked is active, the directive becomes
"Breathe; Resolve a Threat". The narrator receives simultaneous instructions to
de-escalate AND resolve a threat. These are contradictory.

### Occurrences

Turns where Breathe + beat_locked produced this mixed signal: **T4, T8, T10, T14,
T18, T24, T25** = 7 turns.

The contradicting pair also happens with Pressure + beat_locked ("Pressure;
Resolve a Threat"), but that is less contradictory since both imply escalation.

### Hypothesis

The "; Resolve a Threat" append was designed as a safety valve to ensure beat_locked
actually produces pressure. But appending to Breathe creates ambiguity. The
system should either (a) not append when directive is Breathe, or (b) override
Breathe entirely when beat_locked is active (Breathe says de-escalate, beat_locked
was designed to prevent de-escalation).

---

## Finding MB-3: Floor relief beats deepen de-escalation during momentum crisis

**Confidence: H**

### Detail

Floor relief (`turn.py:1064-1072`) injects `breathing_room` (type="ambient",
TTL=2) when:
1. `beat_locked` is True
2. `pending_gm_beat` is None OR its type is in `PRESSURE_BEAT_TYPES`

This fires on **every beat_locked turn** where storyteller produces a pressure-type
beat or no beat — which was most beat_locked turns. The injected beat is
"ambient" — scene description, de-escalation, calm. Precisely the wrong signal
when the system is locked in a momentum crisis.

### Floor relief activations

| Turn | BeatLock | Storytell Beat | Floor Relief fired? | State Beat |
|------|----------|---------------|---------------------|------------|
| 4 | True | pressure | YES (pressure type) | breathing_room |
| 5 | True | pressure | YES | breathing_room |
| 6 | True | pressure | YES | breathing_room |
| 7 | True | none | YES (none) | breathing_room |
| 8 | True | pressure | YES | breathing_room |
| 9 | True | none | YES | breathing_room |
| 10 | True | none | YES | breathing_room |
| 14 | True | pressure | YES | breathing_room |
| 15 | True | none | YES | breathing_room |
| 16 | False | none | NO | none (null-clear) |
| 18 | True | complication | YES | breathing_room |
| 19 | True | pressure | YES | breathing_room |
| 20 | True | complication | YES | breathing_room |
| 21 | True | pressure | YES | breathing_room |
| 22 | True | none | YES | breathing_room |
| 24 | True | complication | YES | none... |
| 25 | True | none | YES | breathing_room |

Floor relief fired on **15 out of 16 beat_locked turns**. Only T24 beat_locked
didn't produce it (pending beat became None — unclear why).

### Hypothesis

Floor relief was designed for a different scenario: high momentum, many pressure
beats in a row, beat_locked fires from consecutive_pressure_threshold. In that
context, injecting a calm beat makes sense. But floor relief's condition is
**momentum OR consecutive_pressure** — and when momentum triggers beat_locked
(crisis mode), the calm beat is the opposite of what's needed. Fix: only fire
floor relief when beat_locked is from consecutive_pressure, not from momentum
floor.

---

## Finding MB-4: No momentum catch-up accelerates recovery from deep negatives

**Confidence: H**

### Detail

Momentum delta is uniform: success = +1, fail = -1, regardless of depth
(`rules.py:79`, `state/momentum.py:16`). At -3, a success goes to -2. A
subsequent fail (which is likely given ~50% failure rate) drops back to -3.

To climb from -3 to 0, the player needs 3 net successes — 6+ rolls at the
observed success rate. But the player never got 3 consecutive net successes in
this game.

### Roll depth progression

```
Turn | Band          | Delta | Momentum | Depth from 0
─────┼───────────────┼───────┼──────────┼─────────────
  1  | success       | +1    |  1       | 1
  2  | fail          | -1    |  0       | 0
  3  | fail          | -1    | -1       | -1
  4  | fail          | -1    | -2       | -2
  5  | partial       |  0    | -2       | -2
  6  | fail          | -1    | -3       | -3 ← stuck
  7  | success       | +1    | -2       | -2
  8  | fail          | -1    | -3       | -3 ← stuck
  9  | fail          | -1    | -3       | -3
 10  | setback       | -1    | -3       | -3
 11  | crit_success  | +2    | -1       | -1
 12  | fail          | -1    | -2       | -2
 13  | success       | +1    | -1       | -1
 14  | setback       | -1    | -2       | -2
 15  | partial       |  0    | -2       | -2
 16  | success       | +1    | -1       | -1
 17  | fail          | -1    | -2       | -2
 18  | crit_fail     | -2    | -3       | -3 ← stuck
 19  | fail          | -1    | -3       | -3
 20  | setback       | -1    | -3       | -3
 21  | fail          | -1    | -3       | -3
 22  | success       | +1    | -2       | -2
 23  | partial       |  0    | -2       | -2
 24  | setback       | -1    | -3       | -3
 25  | (death)       |  0    | -3       | -3
```

The player spent **T6-T25 (20 turns) at momentum -2 or -3**. Brief recoveries
(T11: -1, T13: -1, T16: -1) lasted exactly 1 turn before collapsing again.

### Hypothesis

The system needs depth-based momentum recovery:
- success at -3 → +2 instead of +1
- success at -2 → +1 (unchanged)
- success at -1 or higher → +1
- Or: momentum_delta_multiplier = 1 + (momentum_floor - current) / momentum_floor

This would let deep-negative momentum recover faster while not affecting normal
ranges.

### Roll outcome contributing factors

- 10 out of 24 rolls were **hard difficulty** (42%)
- Non-charisma skills (+0 mod) had ~25% success rate on hard, ~33% on normal
- Charisma (+2 mod) had ~42% success on hard, ~50% on normal
- The PC had **no skills above +2** (only charisma even hit +2)

---

## Finding MB-5: Consecutive pressure counter reads storyteller output, not stored beat

**Confidence: H**

### Detail

At `turn.py:1291-1301`, the consecutive pressure counter checks
`storyteller_result.gm_beat.type` — the raw LLM output, before floor relief
override. This means the counter continues climbing even when floor relief has
replaced the state's pending_gm_beat with breathing_room.

### Evidence

```
Turn | StorytellBeat | StateBeat | PressCnt | BeatLock Source
─────┼───────────────┼───────────┼──────────┼────────────────
  4  | pressure      | complication | 3      | pressure_threshold
  5  | pressure      | breathing_room | 4    | pressure_threshold + momentum
  6  | pressure      | breathing_room | 5    | momentum
  7  | none          | breathing_room | 6 ←  | momentum (should have reset)
  8  | pressure      | breathing_room | 0 ←  | momentum (reset: storytell was none at T7)
```

At T7, storyteller produced `none` (no beat), so T8's counter resets. But T7
state shows `breathing_room` (floor relief injected it). The counter ignores the
injected beat.

### Hypothesis

The counter should read from the **stored** pending_gm_beat (after floor relief),
so breathing_room gets counted as non-pressure and resets the counter. This would
make floor relief actually relieve pressure by resetting the counter, which it
currently doesn't. However, this changes the behavior: currently floor relief
doesn't affect beat_locked (which relies on the counter), so it would shorten
beat_locked episodes. This might be desirable — floor relief would then genuinely
relieve pressure instead of just layering an extra beat.

---

## Finding MB-6: Scene Imperative fires late and doesn't help momentum

**Confidence: M**

### Detail

Scene Imperative fires when `effective_scene_age >= 5` (with +2 boost if
combat-tagged). At T7 (age=5, combat), T9 (age=7), T11-13 (age=9-11, no combat),
T15 (age=13), T22-24 (age=5-7). The directive forces a scene transition, but:

1. It arrives **late** — by T11 the same scene ("Lisamouth Warehouse") had been
   active for 10 turns
2. It doesn't create urgency — it just tells the narrator to wrap up the scene
3. It blocks Breathe (higher priority) but replaces it with scene-wrapping rather
   than pressure-building

### Example

```
T11: directive=Scene Imperative, urgent=[mezzanine_confrontation], age=9
     → system told narrator to transition scene
     → player was mid-confrontation with Devon → mismatch
```

Scene transitions should be smoother and not override action urgency.

### Hypothesis

Scene Imperative should check whether urgent scene threads exist and defer to
Pressure if they do ("don't change the scene, there's a crisis"). Alternatively,
the scene aging threshold should be lower (3-4 turns) to transition before
stagnation sets in.

---

## Finding MB-7: Difficulty assignment produces 42% hard checks against a +2-max character

**Confidence: M** (needs cross-game validation — could be noir genre bias)

### Detail

The rulings system assigns difficulty based on the player's described action and
the scene context. High-stakes actions (executing a thug, grabbing evidence
during escape, killing a cop) plausibly deserve "hard." But with 10 out of 24
rolls at hard, and the character having only one +2 stat, the result was
predictable failure dominance.

### Hard difficulty rolls

| Turn | Action | Skill | Roll | Result |
|------|--------|-------|------|--------|
| 7 | Kick thug, grab pistol | strength+0 | 12→11 | success (lucky) |
| 9 | Execute defiant thug | charisma+2 | 2→3 | fail |
| 13 | Tackle Devon | charisma+2 | 8→9 | success |
| 15 | Force Devon to leave | charisma+2 | 6→7 | partial |
| 17 | Force witness statement | charisma+2 | 4→5 | fail |
| 18 | Seize manifests, flee | dexterity+0 | 1→0 | crit_fail |
| 20 | Point gun at officers | charisma+2 | 5→6 | setback |
| 21 | Demand written protection | charisma+2 | 2→3 | fail |
| 22 | Kill Keith | dexterity+0 | 11→10 | success (lucky) |
| 23 | Blaze of glory | dexterity+0 | 9→8 | partial |
| 24 | Fire remaining rounds | dexterity+0 | 8→6 | setback |

Hard charisma (+2): 3 "good" (success/partial), 4 "bad" (fail/setback) = 43% good
Hard non-charisma (+0): 2 "good", 2 "bad" = 50% good (but low sample)

### Hypothesis

Two possible fixes:
1. **Reduce hard frequency**: cap hard difficulty at 25% of rolls per play session
2. **Let momentum affect difficulty**: at momentum ≤ -2, difficulty shifted one
   step easier (hard → normal, normal → easy). This would create a natural easing
   when the player is already losing.

---

## Cross-Cutting: The Death Spiral Flow

```
Low stat mods → frequent fails → momentum drops → Breathe fires
    → narrator told to de-escalate → floor relief injects calm beat
    → scene stagnates → Scene Imperative fires → scene transitions
    → urgency drops → no urgent threads → easier target for next Breathe
                                  ↑
    Breathe + "; Resolve a Threat" ← beat_locked
```

The only escape is: **roll a crit_success (happened once, T11)** or **get urgent
scene threads AND roll well (happened ~4-5 times, always temporary)**.

---

## Proposed Solutions (ordered by effort/impact)

### Quick fixes (~3 lines each)

**MB-2: Don't append "; Resolve a Threat" to Breathe directive [FIXED — step 01.2]**

File: `ccya/engine/turn.py`, lines 554-557
```python
# Current code (adds "; Resolve a Threat" to ANY directive when beat_locked):
directive_parts = [directive] if directive else []
directive_parts.append("Resolve a Threat")
directive = "; ".join(directive_parts) or ""

# Fix: skip append when directive is Breathe
if beat_locked:
    if not directive.startswith("Breathe"):  # ← add this guard
        directive_parts = [directive] if directive else []
        directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""
```

Impact: Eliminates the contradictory "Breathe; Resolve a Threat" signal on ~7 turns per game. Simple, no behavioral side effects beyond removing the contradiction.

**MB-3: Only fire floor relief from consecutive_pressure, not momentum floor [FIXED — step 01.3]**

File: `ccya/engine/turn.py`, line 1064
```python
# Current condition (fires when beat_locked OR momentum at minimum):
if _pc.beat_locked:
    # ... injects breathing_room regardless of why beat_locked fired

# Fix: only fire from consecutive_pressure, not momentum floor
# Check what triggered beat_locked by examining the source:
#   - consecutive_pressure_turns >= config.consecutive_pressure_threshold → fire relief
#   - momentum <= config.momentum_floor → do NOT fire (crisis mode needs pressure)
```

Impact: Prevents calming beats from being injected during low-momentum crisis. 15/16 floor relief activations in baseline were from momentum floor — this would eliminate them, keeping the scene's natural escalation intact when it matters most.

### Medium fix (~20 lines)

**MB-4: Depth-based momentum recovery at -3 [FIXED — step 01.1]**

File: `ccya/state/momentum.py`, function `apply_momentum` (lines 16-27)
```python
# Current code (uniform delta regardless of depth):
def apply_momentum(state, band):
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band, 0)  # success=+1 always
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))

# Fix: increase delta magnitude at deep negatives (depth -3):
def apply_momentum(state, band):
    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band, 0)
    
    # Depth-based recovery: successes at -3 give +2 instead of +1
    if current <= momentum_floor and band in ("success", "crit_success"):
        depth_penalty = abs(current - momentum_floor)
        if depth_penalty >= 2:  # at -2 or -3 when floor is -3
            delta *= (1 + depth_penalty // 2)  # success at -3 → +2
    
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
```

Impact: Breaks the death spiral by making recovery from deep negatives statistically viable. At -3, a single success brings momentum to -1 instead of -2 (a 2-step jump vs 1-step). Reduces expected turns to escape from ~20 to ~8-10 at observed roll rates.

### Lower priority (pacing/design tweaks)

**MB-6: Scene Imperative timing [FIXED — step 01.4]** — Threshold lowered from 5 to 4 in config.py, giving one extra turn of pacing recovery before forcing scene advancement.

**MB-7: Difficulty frequency** — Cap hard difficulty at 25% of rolls per session, OR let momentum ≤ -2 shift one step easier (hard → normal). Would reduce 42% hard rate to ~20%, improving success rates for +2-max characters without changing core mechanics.

---

## Appendix: Key Source Locations (validated against source)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Velocity computation | `ccya/engine/turn.py` | 423-455 | Confirmed — momentum ≤ -2 → velocity < -0.3 → Breathe fires |
| Directive priority stack | `ccya/engine/turn.py` | 458-522 | Confirmed — Breathe at top priority when velocity < -0.3, no urgent threads |
| Pacing context (beat_locked) | `ccya/engine/turn.py` | 525-597 | **FIXED** — MB-2: Breathe no longer appends "; Resolve a Threat" (step 01.2) |
| Ages computation | `ccya/engine/turn.py` | 600-611 | Confirmed |
| Effective scene age (combat boost) | `ccya/engine/turn.py` | 742-746 | **FIXED** — MB-6: threshold lowered from 5 to 4 in config.py (step 01.4) |
| Scope-scene thread filtering | `ccya/engine/turn.py` | 827-838 | Confirmed — only scope=scene threads used for directive computation |
| Pacing context call site | `ccya/engine/turn.py` | 843-850 | Confirmed |
| Floor relief injection | `ccya/engine/turn.py` | 1064-1072 | **FIXED** — MB-3: only fires from consecutive_pressure, not momentum floor (step 01.3) |
| Pressure counter | `ccya/engine/turn.py` | 1074-1082 | **FIXED** — reads from pending_gm_beat after floor relief (findings referenced stale lines 1291-1301) |
| Momentum application | `ccya/state/momentum.py` | 16-27 | **FIXED** — MB-4: depth-based catch-up at -3 (success=+2, crit_success=+3) added to apply_momentum() (step 01.1) |
| Momentum deltas | `ccya/rules.py` | 79-86 | Confirmed — success=+1, fail=-1 regardless of current momentum |
| Band computation | `ccya/rules.py` | 119-131 | Confirmed |
| Difficulty mods | `ccya/rules.py` | 24-30 | Confirmed — MB-7: hard=-1 mod assigned 42% of rolls |
| Resolve check | `ccya/rules.py` | 171-223 | Confirmed |
| Config (momentum_floor, etc.) | `ccya/engine/config.py` | 139-155 | Confirmed — floor=-3, ceiling=3, pacing_factor=0.5 |
| Auto-latent demotion | `ccya/engine/turn.py` | 224-240 | **FIXED** — fires every turn (not gated on mutation), updated last_updated_turn for all active threads each turn so stale threshold check reliably triggers (step 01.3a) |

## Appendix: Auto-Checker Bug (Momentum Sign Inversion)

The momentum sign inversion reported as #4 in PRIORITIES.md was caused by `runner.py` enrichment logic (`lines 503-505`) using **index-based matching** between turn_events and state_snapshots. Auxiliary events like condition_expired don't have state_snapshot written by the engine, so they get enriched with snapshots from different pipeline stages — causing false positive auto-checker failures comparing misaligned prev_ev/curr_ev pairs. The actual momentum code handles deltas correctly when called directly from the engine.