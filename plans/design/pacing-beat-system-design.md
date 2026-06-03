# Pacing / Beat System Design

## Purpose

Design authority for plans that overhaul the pacing computation and GM beat lifecycle. Covers: directive computation, consecutive_pressure counter signal, beat_locked trigger, floor relief mechanism, beat diversity tracking, beat history in prompt, pending_gm_beat null-clear, beat diversity enforcement, Scene Imperative behavioral weight, and Breathe directive sensitivity.

## Problem Statement

The pacing/beat system has three interlocking failures producing zero useful output across 51 combined turns. First, `beat_locked` — the floor relief trigger — is structurally unreachable because its `consecutive_pressure_turns` counter tracks ruling directives ("Pressure"/"Overwhelm") that never fire, not the actual pressure-type beats the storyteller generates. Second, even if `beat_locked` fired, floor relief beats are blocked by a `not pending_gm_beat` condition that is almost never satisfied (storyteller emits a beat on 80%+ of turns, and null turns leave stale beats un-cleared). Third, beat diversity is nonexistent because the storyteller prompt has no beat history — the LLM generates beats blind to what it emitted in prior turns, making the ~50 lines of diversity guidance instructions untestable. The result is a system that generates pressure-type beats ~50% of the time, never varies surface type, and never delivers breathing_room relief, twists, callbacks, setbacks, or escalations.

## Constraints

- Pipeline order is fixed: narrator runs first, then extraction. The 1-turn beat lag cannot be eliminated without reordering the entire pipeline, which is too expensive for this change.
- The 5-call pipeline structure (ruling → narrate → extract_scene → extract_state → storytell) is unchanged.
- The beat type vocabulary (9 types) is unchanged — only the frequency distribution changes.
- The floor relief concept (forced breathing_room when momentum is critically low) is sound — only the trigger mechanism is broken.
- Backwards compatibility is not required. Prompt format changes are acceptable.

## Non-goals

- Thread system overhaul — separate design doc (arc-thread-system-design.md).
- NPC continuity / last_seen enhancements — separate concern.
- Conditions system — to be removed via a separate change.
- Scene-scoped thread purge on location change — works correctly, unchanged.
- Pacing gate (`block_escalate`/`allow`) for thread_add — works correctly, unchanged.

## Current State — What Exists

### Directive computation (`_compute_narration_directive`, turn.py:430-473)

Priority order:
1. **Breathe** — `narrative_velocity < -0.3` (de-escalation). Wins unconditionally.
2. **Scene Imperative** — `effective_scene_age >= scene_imperative_threshold` (default 5).
3. **Overwhelm** — 3+ urgent scene-scoped threads (never fires in either game — thread urgency is low).
4. **Pressure** — 1-2 urgent scene-scoped threads.
5. **Tension** — background urgency threads only.
6. **Scene Pressure** — non-contradicting secondary when `effective_age >= scene_pressure_threshold` (default 3).

Observed directive distribution across 51 turns: empty (27), Breathe (11), Scene Imperative (7), Scene Pressure (7), Tension (0 on its own — rolled into empty), Pressure (0), Overwhelm (0).

### beat_locked trigger (`_compute_pacing_context`, turn.py:502-508)

Triggered when either:
- `consecutive_pressure_turns >= consecutive_pressure_threshold` (default 3) — **never fired in either game**
- `momentum <= momentum_floor` (default -3) — **never fired in either game (minimum momentum observed: -1)**

When beat_locked fires, it appends "; Resolve a Threat" to the directive and sets `beat_locked = True`.

### consecutive_pressure_turns counter (turn.py:1183-1192)

Updated at the end of each turn:
- Increments by 1 when `directive in ("Pressure", "Overwhelm")` AND no thread_updates present.
- Resets to 0 otherwise.

The counter was `0` at every turn in both games because the directive was never "Pressure" or "Overwhelm".

### Floor relief (turn.py:1090-1096)

Runs after `apply_delta`:
```
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
    meta["pending_gm_beat"] = {"type": "breathing_room", "surface_as": "ambient", "beat_expires_turn": turn + 3}
```

Two conditions: beat_locked must be True AND pending_gm_beat must be None. The second condition blocks floor relief because storytell generates a beat on ~80% of turns.

### pending_gm_beat lifecycle

- Set by storyteller's `gm_beat` output (if non-null).
- Set by floor relief (if beat_locked fires).
- Cleared by TTL expiry (`turn_no > beat_expires_turn`).
- Cleared by overwrite with a new beat.
- **NOT cleared on null storytell output.** When storytell returns `null`, the old beat persists. Observed in both games: a `revelation` beat generated at zombie T1 survived as pending_gm_beat through T4.
- Narrator reads `pending_gm_beat` from state and integrates it into narration. This is always the previous turn's beat (1-turn architectural lag).

### Beat diversity in prompt (storytell_system.j2:135-187)

The prompt contains:
- Crisis-aware diversity: on 3+ consecutive pressure beats, at least 1 in 3 must be non-pressure.
- Major pivot moment guidance: must consider revelation, twist, callback, opportunity.
- Per-type guidance for each non-pressure beat type.
- Band-aligned selection: directive takes precedence, otherwise map roll result to beat type.
- Surface distribution rule: vary surface_as across 3+ turn sequences.
- Per-surface-type examples.

**Critical gap:** No beat history is passed to the storyteller. The LLM cannot follow diversity guidance because it has no data about what beats it generated in prior turns. The guidance is structurally untestable by the LLM.

### Scene Imperative (directive: "Scene Imperative")

Computed when `effective_scene_age >= 5` (default). Fires reliably in both games when scenes stall. But it has no observable effect on narrative behavior — the storyteller and narrator don't change their output patterns during Imperative turns. The directive is computed but carries no behavioral weight in the prompt.

## Problems with Current State

1. **beat_locked is structurally unreachable.** The `consecutive_pressure_turns` counter tracks directives that never fire (Pressure/Overwhelm: 0/51 turns). The actual pressure-type beats (generated ~50% of the time by storytell) are invisible to the counter. `momentum <= -3` is also unreachable (observed minimum: -1).

2. **Floor relief has a 3-way blocker.** (a) beat_locked never fires. (b) Even if it did, `pending_gm_beat` is almost never None because storytell generates a beat on 80%+ of turns. (c) Even on null turns, old beats persist — no clear-on-null logic. The breathing_room floor relief is unreachable.

3. **No null-clear mechanism for pending_gm_beat.** When storytell returns null, the old `pending_gm_beat` persists. Clearance paths are TTL expiry (rarely fires before replacement) or overwrite by a new beat (doesn't happen on null turns). Result: stale beats persist through null turns.

4. **Beat diversity is untestable.** The storyteller prompt has ~50 lines of diversity guidance but zero beat history data. The LLM generates each turn's beat independently, blind to prior turns. Evidence: 4 of 9 beat types used across 51 turns; surface_as is 64%+ `npc_behavior` in both games.

5. **Scene Imperative is a label with no behavioral impact.** The directive fires correctly when scenes stall, but neither storytell_system.j2 nor narrate_system.j2 give it actionable guidance. The narrator doesn't advance the story faster; the storyteller doesn't escalate stakes.

6. **Breathe fires on false velocity signals.** `narrative_velocity < -0.3` triggers Breathe, but the velocity calculation conflates mechanical stealth/passivity with actual tension relief. Breathe fired during active tension sequences in both games (hiding from guards, police raids) because the player chose cautious actions, lowering velocity without resolving tension.

7. **Architectural 1-turn beat lag.** The narrator reads the previous turn's beat. This is by design but means the narrator's beat context is always stale, especially during null-turn sequences where a 2-3 turn old beat continues to shape narration.

## Proposed Solution

### Core Changes

#### 1. Re-key consecutive_pressure counter to beat types, not directives

Change the counter at `turn.py:1189` from:
```
if (directive in ("Pressure", "Overwhelm")) and not thread_updates:
```
to tracking the actual storyteller beat type:
```
if last_gm_beat_type in ("pressure", "escalation", "complication"):
```

This aligns the counter with what the storyteller actually generates rather than with ruling directives that never fire.

**Effect:** After 3 consecutive pressure-type beats, `consecutive_pressure_turns >= 3` triggers beat_locked, which enables floor relief.

**Momentum floor fallback** retained: `momentum <= -3` still triggers beat_locked independently (belt-and-suspenders).

#### 2. Remove the `not pending_gm_beat` condition from floor relief

Change `turn.py:1090` from:
```
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
```
to:
```
if _pc.beat_locked:
```

**Rationale:** The `not pending_gm_beat` condition was intended to prevent overwriting an active beat, but in practice it blocks relief because storytell always generates a beat. Floor relief should override — if the system determines the player needs relief, it should take priority over whatever beat the storyteller generated.

**Mitigation:** The system injects the floor relief beat. If the storyteller generated a different beat, the floor relief beat replaces it. This is correct behavior: the system's pacing determination trumps the storyteller's independent beat choice when the player is in momentum crisis.

#### 3. Clear pending_gm_beat on null storytell output

Immediately after the existing gm_beat apply block (after `turn.py` line 1005, which sets `pending_gm_beat` when `_new_beat` is non-null), add an else branch:
```
if _new_beat and _new_beat.type:
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
else:
    state.get("meta", {}).pop("pending_gm_beat", None)
```

**IMPORTANT — placement:** This must go at ~line 1006 (the else branch of the existing `if _new_beat and _new_beat.type:` at line 1000), NOT in the floor relief section at line 1089. Floor relief at line 1090 checks `pending_gm_beat` — the null-clear must run before that check or it will be silently inoperable.

**Rationale:** When the storyteller intentionally emits null, it means no beat is warranted. The old beat should not persist. This is the most targeted fix — it clears stale beats specifically when null is emitted, leaving normal beat overwrites unaffected.

**Secondary effect:** Combined with change #2, this means floor relief can fire on the turn after a null beat (pending_gm_beat is clear, beat_locked can trigger).

#### 4. Pass beat history to storyteller prompt

Add a `last_n_beats` (configurable, default 5) field to the prompt context passed to `storytell_system.j2`.

Format: an ordered list of the most recent N beats with type, surface_as, and turn number:
```
Previous beats:
  T32: pressure (npc_behavior)
  T31: complication (event)
  T30: null
  T29: pressure (npc_behavior)
  T28: opportunity (player_discovery)
```

**Where to store:** State already contains enough data to reconstruct beat history. The `pending_gm_beat` in meta only stores the current beat. Add a `recent_beats: list[dict]` to `meta` — append the storyteller's gm_beat each turn (including null entries as `{"type": null, "surface_as": null}`), capped at N entries.

**Prompt change:** In `storytell_system.j2`, render the beat history before the GM Beat guidance section. Add instruction: "Use this history to vary your beat types — avoid repeating the same type more than twice in a sequence. At least one in three beats should be a non-pressure type."

#### 5. Give Scene Imperative behavioral weight

Add to `storytell_system.j2`:
- "Scene Imperative means this scene has been active too long without meaningful progression. Your primary directive is to **advance the story** — generate choices that move the narrative forward, introduce new information, or force a decision point."

Add to `narrate_system.j2`:
- "When the pacing directive is Scene Imperative, keep narration lean and move the scene forward. Avoid atmospheric or ambient descriptions — prioritize action and dialogue that advances the plot."

#### 6. Refine Breathe trigger to distinguish stealth from relief

Current: `narrative_velocity < -0.3` triggers Breathe unconditionally.

Proposed: Add a secondary check — if the scene has active urgent threads AND recent pressure-type beats, do not trigger Breathe even if velocity is low. Instead, output "Tension" or "" (let the beat system handle it).

In `_compute_narration_directive`:
```
if narrative_velocity < -0.3:
    if has_active_pressure(scene_threads) and has_recent_pressure_beats(meta, window=3):
        pass  # skip Breathe — player is lying low, tension hasn't resolved
    else:
        return "Breathe"
```

`has_active_pressure` checks for urgent scene-scoped threads. `has_recent_pressure_beats` checks the last 3 beats for pressure-type entries.

This prevents Breathe from firing when the player is actively in a tense situation but choosing cautious actions.

### Alternatives Considered and Rejected

- **Reordering the pipeline to eliminate the 1-turn beat lag:** Rejected. The 5-call pipeline is deeply coupled at the async streaming level. Reordering would touch every phase boundary for a marginal improvement (the beat is used for atmosphere, not plot logic — staleness is acceptable).
- **Auto-clear pending_gm_beat on every turn start:** Rejected. The 1-turn lag means the narrator reads the beat during its turn. Clearing at turn start would mean the narrator never sees the beat. The correct clear point is after extraction (when storytell produces its output).
- **Hard cap on pressure-type beats in code:** Rejected. The storyteller should retain creative freedom. The counter and prompt guidance are sufficient to shape distribution. Code enforcement would create arbitrary narrative restrictions.
- **Eliminate null beats entirely:** Rejected. The 1-in-4 null cadence is a deliberate design choice for pacing variety. The problem is not null beats — it's that null beats don't clear state.
- **Replace floor relief with a different mechanism:** Rejected. The floor relief concept (forced breathing_room) is sound. The trigger and gate conditions are broken. Fix the trigger, don't replace the mechanism.

## Decision Table

| Decision | What | Why |
|---|---|---|
| consecutive_pressure re-keyed to beat types | Counter tracks last_gm_beat.type, not directive | Directives never fire; beat types are the actual signal |
| `not pending_gm_beat` removed from floor relief | Floor relief overrides active beat | Pacing determination trumps storyteller's independent choice in crisis |
| pending_gm_beat cleared on null storytell | Pop pending_gm_beat when gm_beat is None | Stale beats should not persist through intentional null |
| Beat history passed to storyteller | New `recent_beats: list[dict]` in meta + prompt rendering | Enables LLM to follow diversity guidance with actual data |
| Scene Imperative gains prompt guidance | New behavioral instructions in storytell_system.j2 and narrate_system.j2 | Turns a dead label into actionable directive |
| Breathe trigger refined with pressure context | Secondary check for recent pressure beats + urgent threads | Prevents Breathe during active tension when player is lying low |
| Momentum floor fallback retained | `momentum <= -3` remains beat_locked trigger | Belt-and-suspenders for edge cases where momentum crashes without pressure beats |
| Null beat cadence unchanged | 1-in-4 null guidance preserved | Null beats are healthy; only the state-clear problem needs fixing |
| Pipeline order unchanged | Narrate → extraction → storytell preserved | Reordering is too expensive for marginal benefit |

## Failure Modes and Risks

- **Floor relief overrides legitimate storyteller beats.** If beat_locked fires and overwrites a carefully chosen storyteller beat, narrative quality may drop. Mitigation: beat_locked threshold should be conservative (3+ consecutive pressure beats is already a strong signal). The momentum floor trigger adds a safety net for rare cases.
- **Beat history makes prompt too long.** 5 beats × ~40 chars each = ~200 tokens. Acceptable overhead. If beats expand, cap at 3 or summarize older entries. Monitor prompt length in logging.
- **Breathe refinement may be too conservative.** If `has_recent_pressure_beats` blocks Breathe even when tension has genuinely resolved, the player gets no relief. Mitigation: `has_active_pressure` (urgent threads) is the stronger signal — if no urgent threads exist, Breathe fires normally even if there were recent pressure beats.
- **consecutive_pressure counter may spike incorrectly.** If the storyteller generates `complication` beats routinely (which map to pressure-type), the counter might hit 3 every 4 turns. Mitigation: monitor counter distribution after deploy. If it triggers too frequently, add a decay (counter decrements on non-pressure beats rather than resetting to 0).
- **Null-clear may surprise the narrator.** The narrator reads pending_gm_beat during its call. If the beat was cleared at the end of the previous turn (because that turn's storytell was null), the narrator may have no beat to work with on a turn where one was expected. Mitigation: verify that the clear happens after storytell processes in the arc director, which is already after narrate. The timing is correct — narrate reads the pre-clear state.

## Open Questions

- `[OPEN: beat history window size?]` Should `recent_beats` keep 3, 5, or 10 entries? 5 aligns with the "at least 1 in 3" diversity rule (enough to detect 3-turn patterns). But a larger window allows the LLM to spot longer-range repetition. Recommend 5 as default, configurable.
- `[OPEN: should beat history include surface_as?]` The surface diversity problem is severe (64%+ `npc_behavior`). Including `surface_as` in history would let the LLM vary surface types. But it doubles the history size. Recommend including `surface_as` for at least the last 3 beats.
- `[OPEN: consecutive_pressure decay vs. reset?]` Current behavior resets to 0 on any non-matching turn. This means one `breathing_room` beat fully resets the counter, and the storyteller needs 3 more pressure beats to trigger locked again. A decay (decrement by 1 instead of reset) would be more sensitive but might make it too hard to escape the locked state. Recommend starting with reset (simpler, matches current behavior) and monitor.

## What Is Removed

Nothing. This design rewires trigger conditions and adds data flow. No existing fields or functions are removed.

## What Is Unchanged

- Pipeline order (ruling → narrate → extract_scene → extract_state → storytell)
- Beat type vocabulary (9 types unchanged)
- Beat model shape (`GMBeat.type` and `surface_as`)
- Floor relief concept (forced breathing_room on critical momentum)
- Pacing gate (`block_escalate`/`allow`) for thread_add
- Momentum field and computation
- narrative_velocity computation
- Scene-scoped thread purge on location change
- 1-turn beat lag (architectural, not fixable without pipeline reorder)

## New Model Shapes

### Meta.recent_beats (new field)

```
meta["recent_beats"]: list[dict]  # max 5 entries, oldest first
  Each entry:
    turn: int
    type: str | None  # beat type or null
    surface_as: str | None  # surface type or null
```

Appended to at the end of each turn (after storytell processes). Capped at N entries. Null beats are included as `{"type": null, "surface_as": null}`.

## Context for Implementing LLMs

- `ccya/engine/turn.py` lines 476-546 — `_compute_pacing_context`. The beat_locked trigger (line 502-508) and outcome_hint (line 511-528) logic. The counter change goes here or at the update site (line 1183-1192).
- `ccya/engine/turn.py` lines 1089-1096 — Floor relief injection. The `not pending_gm_beat` condition removal goes here. The null-clear does NOT go here — it must be at line ~1006 (after the existing gm_beat apply block, before floor relief checks).
- `ccya/engine/turn.py` lines 1183-1192 — consecutive_pressure counter update. The re-key from directive to beat type goes here.
- `ccya/engine/turn.py` lines 430-473 — `_compute_narration_directive`. The Breathe trigger refinement goes here (adding secondary pressure check).
- `ccya/prompts/storytell_system.j2` — Beat diversity guidance (lines 135-187). Beat history rendering and Scene Imperative guidance go here.
- `ccya/prompts/narrate_system.j2` — Lines 3-17 contain pending_gm_beat integration. Scene Imperative narration guidance goes here.
- `ccya/prompts/sections/` — New `_beat_history.j2` section (or inline in storytell_system.j2) for rendering recent_beats.
- `plans/findings/CONSOLIDATED-EV-FINDINGS.md` — Category 1 (GM Beat System) and Category 3 (Pacing Computation) contain the empirical evidence for every change in this design.
