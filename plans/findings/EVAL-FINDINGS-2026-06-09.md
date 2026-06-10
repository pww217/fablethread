# EVAL Findings — 2026-06-09

> Saves examined: `the-outer-rim--after-unification` (32 turns), `cordyceps-year-twenty` (27 turns)
> Focus: Narrative mechanics — beats, pacing, pressures, momentum, impossible actions, event data integrity, checker correctness
> Method: Cross-reference save event data against architecture docs and source

---

## Category 1: Event Data Completeness

Fields that should exist in stored event data but are missing or have broken structure.

---

### Bug 8: `extraction_context` missing from event schema (High)

**Files:**
- Event schema (all save files)
- `ccya/ev/checkers/location_change.py` — requires `extraction_context.location_this_turn`
- `ccya/ev/checkers/inventory.py` — requires `extraction_context.inventory_this_turn`
- `ccya/ev/checkers/conditions.py` — requires `extraction_context.conditions_this_turn`
- `ccya/ev/checkers/npc_presence.py` — requires `extraction_context`
- `ccya/ev/checkers/pacing.py` — requires `extraction_context`
- `ccya/ev/checkers/directive_tone.py` — requires `extraction_context.scene_tags_this_turn`
- `ccya/ev/checkers/state_fidelity.py` — requires `extraction_context`

**Detail:**
The `extraction_context` field is referenced by 7 checkers via `requires_fields` but does not exist in any event in either save. The event data stores extraction results under `extraction` (with sub-keys `scene`, `state`, `storytell`), but the high-level `extraction_context` dict with fields like `inventory_this_turn`, `conditions_this_turn`, `location_this_turn`, `scene_tags_this_turn` was never added to the event.

The `requires_fields` check (`checkers/__init__.py:74-85`) requires EACH field to be found in at least one event. Since `extraction_context` doesn't exist in ANY event, all 7 checkers fail immediately:

```
required field 'extraction_context' not found in any event for checker 'npc_presence'
required field 'extraction_context.inventory_this_turn' not found in any event for checker 'inventory_integrity'
required field 'extraction_context.conditions_this_turn' not found in any event for checker 'conditions_lifecycle'
...
```

**Evidence (all saves):**
- `extraction_context` is absent from EVERY event in all examined saves
- `extraction` field exists with keys `scene`, `state`, `storytell` — but none is the expected context dict

**Impact:**
7 checkers are completely non-functional. They cannot validate anything because they fail at the field-checking stage.

**Fix:**
- **Option A (quick):** Remove `extraction_context` from `requires_fields` in all affected checkers. The checkers' internal logic should guard against missing data via `ev.get("extraction_context", {})` or similar.
- **Option B (correct):** Add `extraction_context` enrichment to the event at `turn.py:1445` or as a post-processing step. Populate it with the inventory/conditions/location/scene-tag state from the extraction results.

---

### Bug 1: `impossible` not stored in event `ruling` dict (High)

**File:** `ccya/engine/turn.py:1375-1384`

**Detail:**
The `ruling_event` dict serializes only a subset of `RulesOutcome` fields. The `impossible` field is dropped even though `RulesOutcome.impossible` is a valid model field that serializes correctly in isolation:

```python
# Lines 1375-1384 — missing "impossible" and "reason"
ruling_event = {
    "intent_verb": _outcome.intent_verb,
    "intent": _outcome.intent,
    "rolled": _outcome.rolled,
    "total_ms": ruling_metrics.get("total_ms"),
    "tokens_in": ruling_metrics.get("tokens_in", 0),
    "tokens_out": ruling_metrics.get("tokens_out", 0),
    "outcome_summary": outcome_summary,
}
```

For non-rolled turns where `impossible=True`, the ruling applies a momentum penalty (`apply_momentum(state, "fail")` called at line 722), but the event records `ruling.rolled=False`, `ruling.band=None`, and `ruling.impossible=None` (field absent). The only observable signal is `momentum_delta` at the top level, which is indistinguishable from a data error.

**Evidence (outer-rim save):**

| Turn | Player Action | impossible | momentum delta | ruling.rolled | ruling.band |
|------|--------------|------------|---------------|---------------|-------------|
| 23 | "Deliver the supplies" | true | -1 (3→2) | false | None |
| 24 | "Land and deliver supplies" | true | -1 (2→1) | false | None |
| 28 | "...grab some weapons. I want a grenade" | true | -1 (0→-1) | false | None |

**Evidence (cordyceps save):**

| Turn | Player Action | impossible | momentum delta | ruling.rolled | ruling.band |
|------|--------------|------------|---------------|---------------|-------------|
| 13 | "Dress my head wounds and take an amphetamine" | true | -1 (-1→-2) | false | None |
| 19 | "Stick my screwdriver through his eye, take his gun..." | true | 0 (-3→-3, floor cap) | false | None |

Turn 19 is especially invisible — impossible action at momentum floor, momentum delta is 0 (capped), so there's no way to know an impossible action was attempted.

**Impact:**
- Cannot distinguish "no action / no roll" from "impossible action, -1 momentum" without reading raw LLM output from `ruling_prompt.output`
- Momentum checkers (`momentum_lifecycle`) and debug tooling cannot validate impossible-action momentum deltas
- When momentum is at floor, impossible-action attempts become completely invisible (momentum delta = 0)

**Fix:**
Add `"impossible"` and `"reason"` to the `ruling_event` dict. Also add `"band"` for non-rolled rulings (set to `_outcome.band` which is `"fail"` for impossible actions):

```python
ruling_event = {
    "intent_verb": _outcome.intent_verb,
    "intent": _outcome.intent,
    "rolled": _outcome.rolled,
    "impossible": _outcome.impossible,   # ← add
    "reason": _outcome.reason,            # ← add
    "band": _outcome.band,               # ← add (present even for non-rolled)
    ...
}
```

---

### Bug 9: `sanitizer_lifecycle` checker requires `threads_removed` which doesn't exist in event schema (High)

**File:** `ccya/ev/checkers/sanitizer.py:13-14`

**Detail:**
The `sanitizer_lifecycle` checker requires `threads_removed` as a required field, but no sanitizer event in either save has a `threads_removed` key. The actual schema uses `threads_resolved` and `threads_added` but not `threads_removed`.

Sanitizer event keys from both saves:
```
['changes_detail', 'goal_changed', 'kind', 'ms',
 'threads_added', 'threads_resolved', 'threads_updated',
 'tokens_in', 'tokens_out', 'trace_id', 'turn']
```

**Evidence (both saves):**
```
required field 'threads_removed' not found in any event for checker 'sanitizer_lifecycle'
```

**Impact:**
`sanitizer_lifecycle` checker is completely non-functional on all saves.

**Fix:**
Remove `threads_removed` from `requires_fields`, or rename to `threads_resolved` if the checker should check resolution events. Also verify the checker's internal logic still works with the actual schema.

---

### Bug 10: Duplicate NPC entries in `applied.compendium_npc_update` (Low)

**Location:** Event schema — `applied.compendium_npc_update` is a list that can contain duplicate NPC IDs.

**Evidence (cordyceps save, turn 26):**
```
compendium_npc_update entries:
  [0] id=scavenger_traveler_1, notes=fumbling with medical kit — terrified
  [1] id=scavenger_traveler_1, notes=stepping back in pure terror
  [2] id=elena_vance, notes=hands up and motionless — loathing you
```

The `scavenger_traveler_1` NPC appears twice with different notes. The compendium merge logic processes list entries sequentially — the second update silently overwrites the first, losing the "fumbling with medical kit" note.

**Impact:**
Minor data loss on NPC notes. Could cause confusion when reviewing NPC state changes.

**Fix:**
Either:
- Deduplicate `compendium_npc_update` before processing (keep last entry per ID)
- Or fix the storyteller extraction to not emit duplicate NPC updates (harder, LLM-side)

---

### Bug 11: Key NPC never extracted from narration — scene extraction prompt blind spot (Medium)

**Files:**
- `ccya/prompts/sections/extract_scene_system.j2` — scene extraction system prompt
- `ccya/state/npcs.py:97-188` — `apply_npc_scene_management()` NPC creation logic

**Detail:**
A character central to the entire arc — Elias (James Cannon's partner, the kidnapping victim driving the plot) — was never added to the compendium despite being mentioned by name across 10+ turns of narration. The seed narrative establishes Elias as the reason for the entire arc, but he was never included in the seed compendium. The scene extraction pipeline had every opportunity to create an NPC entry but never did.

**Root cause analysis:**
The scene extraction prompt (`extract_scene_system.j2`) tells the LLM to produce `compendium_npc_update` entries for NPCs that "enter the scene" or have "behavior changes" or "stance toward the player." It also constrains new NPCs with:
- "Limit new NPCs to at most 3 per turn"
- "Bio is mandatory for every NPC — even ambient presence"
- "NPC unchanged: Omit entirely"

Elias appears in 7+ turns of current narration, always as the **object/receiver** of action, never the subject:
- "searching for any sign of Elias" (turn 10)
- "no sign of Elias appears" (turn 12)
- "Elias for all of it" (turn 13 — quoted dialogue)
- "your partner huddled in the corner" (turn 13 — revealed)
- "You heave Elias toward the scout vehicle" (turn 14)
- "patch Elias up" (turn 15)
- "keep Elias quiet" (turn 16)

Meanwhile on turn 13, the LLM chose to spend its new-NPC budget on **Silas Vane** (a random raider described actively: "a tall man named Silas Vane trots toward the mangled raider truck, reaches for the latch") instead of Elias. The extraction prompt biases toward NPCs performing visible actions, not NPCs being acted upon.

The "bio is mandatory" constraint amplifies this: the LLM has concrete descriptive material for Silas ("Tall and imposing with a steady, practiced gait. A reliable enforcer...") but must infer a bio for Elias from context — and the prompt doesn't instruct it to do so.

**Impact:**
Characters central to the story remain invisible in the compendium if they're never the grammatical subject of narrative action. This corrupts any downstream system that depends on the compendium (NPC presence tracking, relationship maps, state diff reports).

**Extended evidence (cordyceps-06-09, turns 20-31):**
Even after the autoplay cascade generated 12 additional "Continue the story" turns (turns 20-31), Elias never appeared in the compendium. The NPC count stayed at 12 throughout, the same 12 extracted in turns 1-19: Blake Webb, Grease-Smeared Scavenger, Leo Vance, three dead motorcycle riders, Paul Wyatt, Raider Group, Scavengers Alcove, Silas Vane, Terror-Stricken Scavenger, Tyler Walker. All NPCs are active subjects or group descriptions. Elias — the driving plot element — remains invisible at turn 31.

**Fix:**
Two-part fix:

1. **Seed fix** (proper): Include all named seed-narrative characters in the seed pack's compendium, even if their presence is initially `known` or `archived`. Elias should have been in the starting compendium.

2. **Prompt fix** (belt-and-suspenders): Add to `extract_scene_system.j2`:
   > "If a named character enters the scene for the first time as the recipient of a major action (rescue, capture, healing, transport, medical aid), create an NPC entry for them with whatever information is available from context — including details from recent narration history if needed for the bio."

---

### Bug 12: `narrate` top-level field truncated to 4 characters (Low)

**File:** Event schema (all saves)

**Detail:**
Every turn event stores a top-level `narrate` field that contains exactly 4 characters (likely a digest or remnant), while the full narrative lives in `narrate_prompt.output` (1000-1700 chars). All 19 turn events in the cordyceps-06-09 save show this pattern.

**Evidence (cordyceps-06-09):**
```
Turn 1: narrate=4 chars, narrate_prompt.output=1378 chars
Turn 8: narrate=4 chars, narrate_prompt.output=1415 chars
Turn 19: narrate=4 chars, narrate_prompt.output=1075 chars
```

**Impact:**
Any tooling that reads `event["narrate"]` directly (e.g., state_fidelity checker, summary displays) gets junk instead of the actual narrative prose.

**Fix:**
Either populate `narrate` with the full `narrate_prompt.output` content, or remove the field entirely if it serves no purpose.

---

### Bug 13: `changes.threads` diverges from `applied.threads` (Low)

**File:** Event schema — `changes` vs `applied` fields

**Detail:**
The `changes` field consistently has thread data (1-3 entries per turn) while `applied.threads` is always empty (0 entries). Thread mutations are applied implicitly through the state mutation pipeline but never recorded in `applied`. This affects 16 of 19 turn events on cordyceps-06-09.

**Evidence (cordyceps-06-09):**
```
Turn 1: changes.threads=2, applied.threads=0
Turn 8: changes.threads=2, applied.threads=0
Turn 13: changes.threads=1, applied.threads=0
```

**Impact:**
Tooling that checks thread application consistency (e.g., thread_lifecycle checker, state diff viewers) gets incomplete data from `applied`.

**Fix:**
Either populate `applied.threads` with the resolved/updated thread data from the state pipeline, or remove the thread expectation from `applied` and document that thread state lives in `state_snapshot.arc.threads`.

---

### Bug 14: `narrative_velocity` field undocumented and unused (Low)

**File:** Event schema — `narrative_velocity` field appears in every event but is not referenced in any architecture doc, checker, or tool output.

**Detail:**
Every turn event stores a `narrative_velocity` float (range -1.0 to 0.5 on cordyceps-06-09) but the field:
- Is not documented in `scripts/debug/README.md`
- Is not checked by any checker plugin
- Is not displayed by `ev.py turn`, `ev.py mechanics`, or `ev.py summary`
- Is not mentioned in any architecture doc

**Evidence (cordyceps-06-09):**
```
Turn 1: narrative_velocity=0.17
Turn 4: narrative_velocity=-0.6
Turn 11: narrative_velocity=-1.0
Turn 18: narrative_velocity=-1.0
```

**Impact:**
Dead or orphaned field. May be useful for pacing analysis but cannot be inspected or validated without custom scripting.

**Fix:**
Either:
- Remove the field if it serves no pipeline purpose.
- Or document it and expose it via `ev.py mechanics --velocity` or similar.

---

### Bug 15: Autoplay momentum spiral on "Continue the story" (Medium)

**File:** `ccya/ev/play.py` — LLM autoplay mode

**Detail:**
When autoplay generates `"Continue the story"` as player input, the ruling engine correctly classifies it as `impossible=true` (-1 momentum). But the narrative prompt still produces a valid output, leading the autoplay to immediately generate another turn. This creates a cascade of impossible-action turns, rapidly draining momentum.

On cordyceps-06-09, this cascade ran for **12 consecutive turns** (20-31), dropping momentum from 3 to -3 and then stuck at floor for 7+ turns:

```
Turn 20: momentum 3→2 (-1, impossible)
Turn 21: momentum 2→1 (-1, impossible)
Turn 22: momentum 1→0 (-1, impossible, beat_locked=True, breathing_room injected by MB-3)
Turn 23: momentum 0→-1 (-1, impossible)
Turn 24: momentum -1→-2 (-1, impossible)
Turn 25: momentum -2→-3 (-1, impossible, beat_locked=True, hit floor)
Turn 26: momentum -3→-3 (0, floor cap, beat_locked=True)
...
Turn 31: momentum -3→-3 (0, floor cap, beat_locked=True, pressure=8)
```

**Cascade mechanics:**
- Turns 20-25: momentum drops by 1 each turn (impossible penalty), from 3 down to -3
- Turn 22: MB-3 floor relief injects breathing_room (triggered by consecutive pressure = 3, not momentum floor)
- Turn 25: momentum hits floor (-3). MB-3 skips floor relief (triggered_by_momentum = True). beat_locked stays True.
- Turns 25-31: momentum stuck at floor. beat_locked=True continuously. Storyteller outputs "escalation" every turn despite pending beat being something else. Consecutive pressure climbs to 8.
- No new NPCs created during the cascade (NPC count stays at 12).
- The storyteller overrides MB-3's breathing_room injection on turn 25+, outputting escalation regardless.

**Impact:**
Autoplay sessions can spiral into momentum death spirals if the LLM generates passive inputs. The engine correctly penalizes non-actions, but the autoplay loop doesn't detect this pattern and adjust behavior. Once at floor, the system has no mechanism to break out: MB-3 prevents floor relief (correctly) but the storyteller overrides any remaining relief signals with escalation, and beat_locked prevents scene progression.

**Fix:**
Add detection in `play.py` autoplay mode:
- If 2+ consecutive impossible-action turns are generated, inject a proactive input suggestion or pause for intervention.
- Consider a "momentum floor escape hatch" for beat_locked: after 3+ turns at floor with beat_locked, force a breathing_room regardless of triggered_by_momentum.

---

## Category 2: Checker Correctness

Checkers that produce wrong or confusing PASS/FAIL results.

---

### Bug 3: `momentum_lifecycle` `requires_fields` includes `ruling.band` — always fails on non-rolled turns (High)

**File:** `ccya/ev/checkers/momentum.py:18`

**Detail:**
The checker declares `requires_fields=["ruling.band", "momentum_before", "momentum_after", "applied"]`. The `requires_fields` check at `ccya/ev/checkers/__init__.py:74-85` requires the field to exist in **at least one event** in the filtered set. When running against a single turn, only that turn's event is passed.

The checker's own loop already correctly skips non-rolled turns with `if not ruling.get("rolled"): continue` at line 27, so the `requires_fields` check is redundant and actively harmful.

**Evidence (outer-rim save):**
```
$ ev.py check 23 momentum_lifecycle
required field 'ruling.band' not found in any event for checker 'momentum_lifecycle'
## momentum_lifecycle: FAIL (score: 0.0)
```
21 of 32 turns fail.

**Evidence (cordyceps save):**
```
$ ev.py check 13 momentum_lifecycle
required field 'ruling.band' not found in any event for checker 'momentum_lifecycle'
## momentum_lifecycle: FAIL (score: 0.0)
```
Turns 13, 19, 27 all fail (non-rolled). But rolled turns pass:
```
$ ev.py check 3 momentum_lifecycle
## momentum_lifecycle: PASS (score: 1.0)
```

**Impact:**
Checker is unusable on most turns. The only turns it works on are those with actual dice rolls.

**Fix:**
Remove `ruling.band` from `requires_fields`. The checker already has internal guards.

---

### Bug 6: `gm_beat_lifecycle` checker expects floor relief on ALL beat_locked turns (outdated after MB-3 fix) (High)

**File:** `ccya/ev/checkers/gm_beat.py:75-86`

**Detail:**
The MB-3 fix (step 01.3 in MOMENTUM-BEAT-FINDINGS, applied to `ccya/engine/turn.py:1091-1106`) changed floor relief to only fire when beat_locked is triggered by **consecutive pressure**, not by **momentum floor**. The guard at line 1098:

```python
if not triggered_by_momentum:
    # Inject floor relief
```

But the `gm_beat_lifecycle` checker at lines 75-86 still unconditionally expects `breathing_room` on every `beat_locked=True` turn where the storyteller didn't produce a non-pressure beat:

```python
if beat_locked:
    storytell_is_pressure = storytell_type in PRESSURE_BEAT_TYPES if storytell_type else False
    storytell_is_non_pressure = bool(storytell_type) and not storytell_is_pressure
    if not storytell_is_non_pressure:
        if cur_type != "breathing_room":
            # reports FAIL — expects breathing_room
```

**Evidence (outer-rim save):**
```
$ ev.py check 30 gm_beat_lifecycle
beat_locked=True, storytell_type='complication' but pending_gm_beat.type='complication' (expected 'breathing_room')
```
Turns 30, 31, 32 fail.

**Evidence (cordyceps save):**
```
$ ev.py check 3 gm_beat_lifecycle
beat_locked=True, storytell_type='complication' but pending_gm_beat.type='complication' (expected 'breathing_room')
$ ev.py check 19 gm_beat_lifecycle
beat_locked=True, storytell_type='pressure' but pending_gm_beat.type='pressure' (expected 'breathing_room')
$ ev.py check 4 gm_beat_lifecycle
## gm_beat_lifecycle: PASS (score: 1.0)
$ ev.py check 17 gm_beat_lifecycle
## gm_beat_lifecycle: PASS (score: 1.0)
```

**Extended evidence (cordyceps-06-09, turns 25-31):**
With the autoplay cascade hitting momentum floor, Bug 6 now triggers across 7 consecutive turns (25-31):
```
$ ev.py check 25 gm_beat_lifecycle
beat_locked=True, storytell_type='escalation' but pending_gm_beat.type='escalation' (expected 'breathing_room')
$ ev.py check 30 gm_beat_lifecycle
beat_locked=True, storytell_type='escalation' but pending_gm_beat.type='escalation' (expected 'breathing_room')
```
All turns from 25-31 fail with the same pattern: momentum at floor (-3), beat_locked=True, storyteller emits escalation, checker expects breathing_room. This confirms the MB-3 fix is correctly implemented at `turn.py:1091-1106` (preventing floor relief when triggered_by_momentum=True) but the checker hasn't been updated to match.

**Pattern:** checker only fails when beat_locked is from momentum floor AND storyteller emits a pressure-type beat. When storyteller emits a non-pressure beat (like "Breathe" on turn 17), the checker correctly skips the expectation.

**Impact:**
False FAILs on every save where momentum hits floor and storyteller emits pressure-type beats. Makes the checker unreliable for momentum-crisis scenarios.

**Fix:**
Add the same `triggered_by_momentum` guard that the engine uses. Only expect `breathing_room` when beat_locked is NOT from momentum floor:

```python
if beat_locked:
    snap = extract_field(ev, "state_snapshot") or {}
    pc_momentum = (snap.get("pc") or {}).get("momentum", 0)
    triggered_by_momentum = int(pc_momentum) <= MOMENTUM_FLOOR

    storytell_is_pressure = storytell_type in PRESSURE_BEAT_TYPES if storytell_type else False
    storytell_is_non_pressure = bool(storytell_type) and not storytell_is_pressure

    if not triggered_by_momentum and not storytell_is_non_pressure:
        if cur_type != "breathing_room":
            # Only expect breathing_room when triggered by consecutive pressure
```

---

### Bug 4: `momentum_lifecycle` floor streak detection uses start-of-turn momentum (off by one) (Medium)

**File:** `ccya/ev/checkers/momentum.py:74-88`

**Detail:**
The floor streak check reads momentum from `state_snapshot.pc.momentum`. But `state_snapshot` is pre-turn state (loaded from disk before `save_state`). This counts turns that **start** at the floor, not turns that **end** at the floor. The off-by-one pattern is rooted in Bug 7 (`state_snapshot` naming).

**Evidence (cordyceps save, turns 14-20):**
The floor episode: turns 14-15 hit floor, recover, then 17-20 sustained at floor.

With `momentum_after` (end-of-turn, correct):
- Turn 14: after=-3 → streak=1
- Turn 15: after=-1 → streak=0 (reset, recovered)
- Turn 17: after=-3 → streak=1
- Turn 18: after=-3 → streak=2
- Turn 19: after=-3 → streak=3 (**detected at turn 19**)
- Turn 20: after=-3 → streak=4

With `state_snapshot` (start-of-turn, current buggy code):
- Turn 14: start=-2 → streak=0
- Turn 15: start=-3 → streak=1
- Turn 16: start=-1 → streak=0
- Turn 17: start=-2 → streak=0
- Turn 18: start=-3 → streak=1
- Turn 19: start=-3 → streak=2
- Turn 20: start=-3 → streak=3 (**detected at turn 20**)

The off-by-one delays detection by exactly 1 turn and misses the initial floor hit.

**Impact:**
Floor no-relief detection misses legitimate streaks by one turn on the front end. The flag is supposed to alert when the player is stuck at minimum momentum for 3+ turns without relief.

**Fix:**
Use `momentum_after` from the enriched event field (which reflects end-of-turn state) instead of `state_snapshot`:

```python
momentum_after = extract_field(ev, "momentum_after")
if momentum_after is not None and int(momentum_after) <= MOMENTUM_FLOOR:
    floor_streak += 1
```

---

### Bug 5: `momentum_lifecycle` floor streak exits after first detection (Low)

**File:** `ccya/ev/checkers/momentum.py:88`

**Detail:**
The `break` on line 88 exits the event loop after finding the first `floor_streak >= 3`. If a game has multiple floor episodes separated by recovery, only the first is reported.

**Fix:**
Replace `break` with `continue` to track all floor episodes.

---

## Category 3: Field Naming & Clarity

Misleading field names that confuse debugging.

---

### Bug 2: `outcome_summary` in `ruling_event` is actually the storyteller's recap (Low)

**File:** `ccya/engine/turn.py:1383`

**Detail:**
The field `"outcome_summary"` in the ruling event stores `storytell_result.outcome_summary` (propagated from extraction pipeline at line 1457), not the ruling's outcome. The variable `outcome_summary` is initialized empty at line 1046 and set from the extraction result at line 1077.

For outer-rim turn 23's impossible-action ruling (reason: "No supplies or recipient mentioned in current scene"), the event's `ruling.outcome_summary` reads as "Jared and Emma arrive at Outpost Delta..." — a scene transition recap, not a ruling outcome.

For cordyceps turn 13's impossible-action ruling (reason: "No medical supplies or amphetamines in inventory."), the event's `ruling.outcome_summary` reads: "Victor fails to find medical supplies for his head wound as hungry workers breach the station stairs." — still the storyteller's scene description.

**Impact:**
Misleading for anyone reading the event — the field is namespaced under `ruling` but contains storyteller content.

**Fix:**
Rename to `storytell_outcome_summary` in the top-level event, or store both the ruling's actual outcome and the storyteller's recap separately.

---

### Bug 7: `state_snapshot` naming implies end-of-turn state but is pre-turn (Low)

**File:** `ccya/engine/turn.py:1445-1449`

**Detail:**
```python
event["state_snapshot"] = load_state(save_dir)   # line 1445
append_event(save_dir, event)                    # line 1446
register_persist(str(save_dir))                  # line 1448
save_state(save_dir, state)                      # line 1449
```

`load_state` runs before `save_state`, so `event["state_snapshot"]` contains the state from the **previous turn** (start of current turn). The comment at line 1447 confirms: `"Snapshot pre-turn state before overwriting"`. But the field name `state_snapshot` suggests a post-turn snapshot.

**Impact:**
Confusing for debugging. Drives the off-by-one error in Bug 4 (floor streak detection).

**Fix:**
Rename to `state_before_turn` for clarity, or swap the order to save then load. If swapping, check downstream consumers.

---

## Summary

### Category 1: Event Data Completeness

| # | Severity | File | Description |
|---|----------|------|-------------|
| 8 | High | Event schema — 7 checkers | `extraction_context` missing from event schema |
| 1 | High | `ccya/engine/turn.py:1375-1384` | `impossible` not stored in event `ruling` dict |
| 9 | High | `ccya/ev/checkers/sanitizer.py:13-14` | `threads_removed` doesn't exist in sanitizer events |
| 11 | Medium | `extract_scene_system.j2` prompt | Scene extraction misses passive/recipient NPCs |
| 10 | Low | Event schema — `compendium_npc_update` | Duplicate NPC entries cause silent overwrite |
| 12 | Low | Event schema — `narrate` field | Top-level `narrate` field truncated to 4 chars |
| 13 | Low | Event schema — `changes` vs `applied` | `changes.threads` has data but `applied.threads` always empty |
| 14 | Low | Event schema — `narrative_velocity` | Undocumented and unused field |
| 15 | Medium | `ccya/ev/play.py` — autoplay | Momentum spiral on consecutive "Continue the story" inputs |

### Category 2: Checker Correctness

| # | Severity | File | Description |
|---|----------|------|-------------|
| 3 | High | `ccya/ev/checkers/momentum.py:18` | `requires_fields` includes `ruling.band`, breaks on non-rolled turns |
| 6 | High | `ccya/ev/checkers/gm_beat.py:75-86` | Expects floor relief on ALL beat_locked turns (outdated after MB-3) |
| 4 | Medium | `ccya/ev/checkers/momentum.py:74-88` | Floor streak uses start-of-turn momentum (off by one) |
| 5 | Low | `ccya/ev/checkers/momentum.py:88` | Floor streak breaks after first detection |

### Category 3: Field Naming & Clarity

| # | Severity | File | Description |
|---|----------|------|-------------|
| 2 | Low | `ccya/engine/turn.py:1383` | `outcome_summary` is storyteller's recap, not ruling's |
| 7 | Low | `ccya/engine/turn.py:1445` | `state_snapshot` is pre-turn, not post-turn |

---

## How each bug was found (for reproducibility)

1. **Bug 1 — impossible not stored**: Ran `ev.py mechanics 23 --pacing --dice` on outer-rim → momentum delta -1 but no ruling. Dumped raw event JSON → `ruling.impossible: None`. Checked raw LLM ruling output → `"impossible": true`. Verified same pattern on cordyceps turns 13, 19.

2. **Bug 2 — outcome_summary misnamed**: Noticed ruling event `outcome_summary` for outer-rim turn 23 described a scene transition, not the ruling. Traced variable `outcome_summary` back through `turn.py`.

3. **Bug 3 — requires_fields kills checker**: Ran `ev.py check 13 momentum_lifecycle` on cordyceps → FAIL. Traced the `requires_fields` check at `checkers/__init__.py:74-85`. Confirmed non-rolled turns fail the check on both saves.

4-5. **Bugs 4, 5 — floor streak bugs**: Dumped cordyceps turn 14 event → `momentum_after: -3, state_snapshot.momentum: -2`. The discrepancy between post-turn momentum and `state_snapshot` revealed the off-by-one. Traced the streak loop to find the `break` bug.

6. **Bug 6 — gm_beat checker outdated after MB-3**: Ran `ev.py check --all --save-dir` on cordyceps turn 3 → `gm_beat_lifecycle` failed with "expected breathing_room but got complication". Read `gm_beat.py:75-86` against the MB-3 fix in `turn.py:1091-1106`. Confirmed same pattern on outer-rim turns 30-32. Extended evidence: cordyceps-06-09 turns 25-31 now also trigger this (momentum floor + escalation beats).

7. **Bug 7 — state_snapshot naming**: Traced `event["state_snapshot"]` at `turn.py:1445` → `load_state` before `save_state` at line 1449. State snapshot grows 8.5K (turn 1) → 18.8K (turn 31), about 2.2x over 31 turns.

8. **Bug 8 — extraction_context missing**: Ran `ev.py check 3 --all --save-dir` → 7 checkers failed with `extraction_context` missing. Verified the field doesn't exist in any event in either save by dumping event keys.

9. **Bug 9 — threads_removed missing**: Same `--all` run → `sanitizer_lifecycle` failed with `threads_removed` missing. Checked sanitizer event keys in both saves — no `threads_removed` key exists anywhere.

10. **Bug 10 — duplicate NPC entries**: Inspected `applied.compendium_npc_update` for cordyceps turn 26 while checking state diff data. Found `scavenger_traveler_1` appearing twice.

11. **Bug 11 — scene extraction misses passive NPCs**: While verifying Elias's compendium presence during cordyceps playthrough, searched all 19 events for "Elias" in extraction outputs — zero NPC entries found despite 7+ turns mentioning him by name. Traced extraction prompt `extract_scene_system.j2` to find bias toward active-subject NPCs. Confirmed LLM chose to extract Silas Vane (active) over Elias (passive) on the same turn. Extended evidence: through 31 turns and 12 additional "Continue the story" events, Elias never appeared in the compendium — 12 NPCs all active subjects or groups.

12. **Bug 12 — narrate field truncated**: Noticed `narrate` field in event dump was always 4 characters while full narrative was in `narrate_prompt.output`. Verified across all 19 turn events in cordyceps-06-09.

13. **Bug 13 — changes.threads vs applied.threads mismatch**: Dumped `changes.keys()` and `applied.keys()` for all turn events. Found `applied.threads` was always 0 entries while `changes.threads` had 1-3 entries per turn.

14. **Bug 14 — narrative_velocity undocumented**: Found `narrative_velocity` key in every event while dumping event keys. Searched docs, checkers, and tool output — zero references found.

15. **Bug 15 — autoplay momentum spiral**: While examining turn 20 and 21 events generated by autoplay, found consecutive `"Continue the story"` inputs both classified as impossible, draining momentum 3→2→1. Confirmed autoplay has no guard against this pattern. Extended evidence: the cascade ran for 12 turns (20-31), dropping momentum 3 → -3 and stuck at floor for 7+ turns with beat_locked=True, consecutive pressure=8, and no escape mechanism.
