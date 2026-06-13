# Pacing / Beat System Design

> **NOTE:** This document was superseded by `docs/design/major-narrative-mechanic-overhaul.md` (Scene Phase & Pacing Redesign). The momentum system, beat_locked, pacing_gate, and related fields described here were removed in Plan 4. This document is preserved for historical reference only.

## Purpose

> **Superseded by:** `docs/design/major-narrative-mechanic-overhaul.md`

Design authority for plans that overhauled the pacing computation and GM beat lifecycle. Covers: directive computation, consecutive_pressure counter signal, beat_locked trigger, floor relief mechanism, beat diversity tracking, beat history in prompt, pending_gm_beat null-clear, beat diversity enforcement, Scene Imperative behavioral weight, and Breathe directive sensitivity. All of these were implemented and the old system was removed in Plan 4.

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
last_gm_beat_type = (storyteller_result.gm_beat.type
                     if storyteller_result and storyteller_result.gm_beat
                     else None)
if last_gm_beat_type in ("pressure", "escalation", "complication"):
```

`storyteller_result` is in scope at the counter update site (turn.py:1183-1192) — it was unpacked from `_extract_result` earlier in the same function. The intermediate variable `last_gm_beat_type` makes the data source explicit.

**Null behavior:** When `storyteller_result.gm_beat` is `None` (null beat turn), `last_gm_beat_type` is `None` and does not match any pressure type, so the counter resets to `0`. This is correct — a null beat means nothing notable happened, which is effectively relief, and should not accumulate toward beat_locked.

**Effect:** After 3 consecutive pressure-type beats, `consecutive_pressure_turns >= 3` triggers beat_locked, which enables floor relief.

**Momentum floor fallback** retained: `momentum <= -3` still triggers beat_locked independently (belt-and-suspenders).

#### 2. Replace `not pending_gm_beat` guard with a pressure-type check

Change `turn.py:1090` from:
```
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
```
to:
```
if _pc.beat_locked:
    _current_beat = state.get("meta", {}).get("pending_gm_beat")
    if _current_beat is None or _current_beat.get("type") in ("pressure", "escalation", "complication"):
```

**Rationale:** The old guard blocked floor relief whenever storytell generated any beat (80%+ of turns), making it structurally unreachable. But unconditional override (always inject breathing_room when beat_locked) is too aggressive — it overwrites legitimate non-pressure beats the storyteller independently produced (revelation, opportunity, breathing_room). The replacement guard only overrides when:
- No beat exists (null turn — stale beat cleared by change #3), OR
- The current beat is a pressure type (storyteller is stuck in a pressure loop)

When the storyteller already produced a non-pressure beat, let it stand — the diversity/relief goal is already being met.

**Timing note:** By the time floor relief runs (line 1089), `pending_gm_beat` reflects the current turn's storyteller output (set at line 1005). Change #3's null-clear (at line 1006) has already run, so null turns leave `pending_gm_beat` absent. The check correctly distinguishes "storyteller already provided relief" from "storyteller is stuck in pressure mode."

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

**Pre-condition — `## GM Beat` section must render:** Before implementing this beat history rendering, verify that the `## GM Beat` section currently renders in the storytell user prompt. Finding 1.8 (CONSOLIDATED-EV-FINDINGS.md) confirmed that the section was entirely absent across the entire cordyceps-v2 26-turn run — the beat type, current pressures, and pending_beat were never rendered to the storyteller. If the `## GM Beat` section does not currently render, restoring it is a prerequisite and should be treated as a separate step preceding this beat history addition. Without this verification, the history context is injected into a prompt that may be missing its surrounding beat guidance entirely.

#### 5. Give Scene Imperative behavioral weight (storytell only)

**Context — outcome_hint is already "advance" when SI fires.**

In `_compute_pacing_context` (turn.py:510-527), `outcome_hint` is set to `"advance"` when `effective_age >= 3`. Scene Imperative fires when `effective_age >= 5`, so outcome_hint is always already `"advance"` on SI turns. The narrator already receives _"Narrate through to the resolution. Do not linger on preparation or setup. Something significant happens this turn."_ (narrate_user.j2:101). If that instruction hasn't produced behavioral change, the problem is at the LLM level, not prompt wording.

**The narrator cannot receive directive-specific guidance.** The narrate prompt only receives `pacing_context.outcome_hint` — it has no access to the directive string. Adding "when the pacing directive is Scene Imperative" to narrate prompts is inoperable.

**Proposed:** Add Scene Imperative guidance only to `storytell_system.j2` (which does receive the directive):

- "Scene Imperative means this scene has been active too long without meaningful progression. Your primary directive is to **advance the story** — generate choices that move the narrative forward, introduce new information, or force a decision point."

No narrate prompt changes — the existing outcome_hint "advance" guidance already covers this. If the narrator ignores it, the fix belongs elsewhere (investigation needed).

#### 6. Refine Breathe trigger to distinguish stealth from relief

Current: `narrative_velocity < -0.3` triggers Breathe unconditionally.

Proposed: Add a secondary check — if urgent scene-scoped threads exist, do not trigger Breathe even if velocity is low. Urgent threads mean the player is lying low in an active tense situation, not genuinely de-escalating. When those threads resolve, velocity drops are genuine relief.

In `_compute_narration_directive` (turn.py:440):
```
if narrative_velocity < -0.3:
    urgent_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "") == "urgent")
    if urgent_count > 0:
        pass  # skip Breathe — low velocity is tactical avoidance, not genuine relief
    else:
        return "Breathe"
```

This is simpler than the original proposal (which required beat history and an `has_recent_pressure_beats` function). It has zero dependency on beat history — the `scope_scene_threads` list already exists in `_compute_narration_directive`'s scope. It directly addresses the root conflation: `narrative_velocity` cannot distinguish tactical avoidance from genuine relief, but thread urgency can.

**Rationale for removing the beat history check:** If urgent threads exist, tension is unresolved regardless of recent beat types — the player hasn't escaped the situation. If urgent threads are absent, the player has resolved the threat (or it never existed) and low velocity is genuine relief. Beat history adds no signal beyond what thread urgency already provides for this guard.

**Edge case — player has been avoiding urgent threads for 5+ turns:** Breathe is suppressed throughout, which is correct — the tension isn't resolved until the player deals with the threat. Once the thread resolves (de-escalated or completed), urgent threads disappear from `scope_scene_threads` and Breathe fires normally on the next low-velocity turn.

### Alternatives Considered and Rejected

- **Reordering the pipeline to eliminate the 1-turn beat lag:** Rejected. The 5-call pipeline is deeply coupled at the async streaming level. Reordering would touch every phase boundary for a marginal improvement (the beat is used for atmosphere, not plot logic — staleness is acceptable).
- **Auto-clear pending_gm_beat on every turn start:** Rejected. The 1-turn lag means the narrator reads the beat during its turn. Clearing at turn start would mean the narrator never sees the beat. The correct clear point is after extraction (when storytell produces its output).
- **Hard cap on pressure-type beats in code:** Rejected. The storyteller should retain creative freedom. The counter and prompt guidance are sufficient to shape distribution. Code enforcement would create arbitrary narrative restrictions.
- **Eliminate null beats entirely:** Rejected. The 1-in-4 null cadence is a deliberate design choice for pacing variety. The problem is not null beats — it's that null beats don't clear state.
- **Replace floor relief with a different mechanism:** Rejected. The floor relief concept (forced breathing_room) is sound. The trigger and gate conditions are broken. Fix the trigger, don't replace the mechanism.

## Decision Table

| Decision | What | Why |
|---|---|---|
| consecutive_pressure re-keyed to beat types | Counter tracks `storyteller_result.gm_beat.type` (null → reset to 0), not directive | Directives never fire; beat types are the actual signal |
| Floor relief guard changed to pressure-type check | Only overrides when current beat is None or pressure-type | Lets non-pressure storyteller beats stand; only injects breathing_room when storyteller is still in pressure loop |
| pending_gm_beat cleared on null storytell | Pop pending_gm_beat when gm_beat is None | Stale beats should not persist through intentional null |
| Beat history passed to storyteller | New `recent_beats: list[dict]` in meta + prompt rendering | Enables LLM to follow diversity guidance with actual data |
| Scene Imperative gains storytell prompt guidance | New behavioral instruction in storytell_system.j2 only; outcome_hint already "advance" on SI turns | Narrator can't read directive — outcome_hint "advance" already covers narrate; storytell gets specific SI instruction |
| Breathe trigger refined with thread urgency | Secondary check: if urgent threads exist, skip Breathe regardless of velocity | Velocity conflates tactical avoidance with relief; thread urgency is the correct signal |
| Momentum floor fallback retained | `momentum <= -3` remains beat_locked trigger | Belt-and-suspenders for edge cases where momentum crashes without pressure beats |
| Null beat cadence unchanged | 1-in-4 null guidance preserved | Null beats are healthy; only the state-clear problem needs fixing |
| Pipeline order unchanged | Narrate → extraction → storytell preserved | Reordering is too expensive for marginal benefit |

## Failure Modes and Risks

- **Floor relief may trigger too often.** After re-key, consecutive_pressure hits 3 with ~12.5% probability in any 3-turn window (pressure ~50% of storyteller output). Over a 20-turn scene, beat_locked fires ~2-3 times. The pressure-type guard mitigates this — floor relief only overrides when the storyteller IS still generating pressure beats. If the storyteller independently varies output, no override occurs. The momentum floor fallback remains for extreme cases.
- **Beat history makes prompt too long.** 5 beats × ~40 chars each = ~200 tokens. Acceptable overhead. If beats expand, cap at 3 or summarize older entries. Monitor prompt length in logging.
- **Breathe refinement blocks relief during unresolved tension.** The revised check (urgent threads only, no beat history) suppresses Breathe whenever urgent scene-scoped threads exist, regardless of how many turns the player has been avoiding them. If the player is stuck in a loop (urgent thread persists for 10+ turns, velocity stays low), no Breathe directive is ever issued. Mitigation: the beat_locked + floor relief mechanism provides an alternative path to breathing_room when consecutive pressure turns hit the threshold. If the thread eventually resolves, urgent_count drops to 0 and Breathe fires on the next low-velocity turn.
- **consecutive_pressure counter may spike incorrectly.** If the storyteller generates `complication` beats routinely (which map to pressure-type), the counter might hit 3 every 4 turns. Mitigation: monitor counter distribution after deploy. If it triggers too frequently, add a decay (counter decrements on non-pressure beats rather than resetting to 0).
- **Null-clear may surprise the narrator.** The narrator reads pending_gm_beat during its call. If the beat was cleared at the end of the previous turn (because that turn's storytell was null), the narrator may have no beat to work with on a turn where one was expected. Mitigation: verify that the clear happens after storytell processes in the arc director, which is already after narrate. The timing is correct — narrate reads the pre-clear state.
- **Beat history cannot guarantee a stable distribution.** Finding 0.1 (CONSOLIDATED-EV-FINDINGS.md) shows that two runs of the same system with the same seed pack produced near-inverse beat profiles (v1: 61% complication+opportunity; v2: 54% revelation) — beat selection is dominated by LLM seed/model variance, not by any control mechanism in the pipeline. Beat history gives the LLM data to follow the diversity guidance, but model variance will still dominate beat selection more than prompt structure does. Beat history is expected to reduce the worst repetition patterns (e.g., 9 consecutive pressure beats) but should not be expected to produce a stable distribution across different models or seeds. Evaluation should focus on whether extreme runs (9+ same-type sequences) are eliminated, not on whether the overall distribution matches a target.

## Open Questions

- `[OPEN: beat history window size?]` Should `recent_beats` keep 3, 5, or 10 entries? 5 aligns with the "at least 1 in 3" diversity rule (enough to detect 3-turn patterns). But a larger window allows the LLM to spot longer-range repetition. Recommend 5 as default, configurable.
- `[OPEN: should beat history include surface_as?]` The surface diversity problem is severe (64%+ `npc_behavior`). Including `surface_as` in history would let the LLM vary surface types. But it doubles the history size. Recommend including `surface_as` for at least the last 3 beats.
- `[OPEN: consecutive_pressure decay vs. reset?]` Current behavior resets to 0 on any non-matching turn. This means one `breathing_room` beat fully resets the counter, and the storyteller needs 3 more pressure beats to trigger locked again. A decay (decrement by 1 instead of reset) would be more sensitive but might make it too hard to escape the locked state. Recommend starting with reset (simpler, matches current behavior) and monitor.
- `[OPEN: Breathe/beat decoupling unaddressed — Finding 1.10]` Finding 1.10 confirmed that during Breathe + block_escalate turns, the storyteller generated opportunity and revelation beats — zero breathing_room beats during any Breathe directive across all saves. This design fixes the Breathe trigger misfires (change #6) but does not address the decoupling between the pacing directive and the beat the storyteller independently selects. After this design, when the pacing system issues Breathe, the storyteller should ideally emit a breathing_room or opportunity beat, but nothing enforces or guides that alignment. If post-implementation data shows Breathe directives still producing non-breather beats, consider adding explicit beat-type guidance to the storytell prompt conditioned on the Breathe directive (similar to the Scene Imperative addition in change #5).

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

Appended to at the end of each turn, after floor relief injection (turn.py:~1096) and before the counter update (~1183). This ordering is critical:
1. Storytell output → `pending_gm_beat` set (line 1005)
2. Null-clear (change #3) — clears `pending_gm_beat` if null (line 1006)
3. Floor relief (change #2) — may override `pending_gm_beat` with breathing_room (line 1089)
4. **recent_beats append** — snapshot of `pending_gm_beat` after any override
5. Counter update (change #1 — line 1183)
6. Turn increment (line 1197)

Appending after floor relief ensures the beat history reflects what the narrator actually received, not what the storyteller originally generated (which may have been overridden by floor relief). Capped at N entries. Null beats are included as `{"type": null, "surface_as": null}` (only if pending_gm_beat was cleared by null-clear and not overridden by floor relief).

**Save/load initialization:** Pre-feature saves (v1 schema) won't have `recent_beats` in meta. The append code must use `meta.setdefault("recent_beats", [])` to handle missing keys gracefully. No explicit migration is required — the setdefault handles initialization on first write. Readers in the beat history prompt renderer should also use `.get("recent_beats", [])` for the same reason.

## Context for Implementing LLMs

- `ccya/engine/turn.py` lines 476-546 — `_compute_pacing_context`. The beat_locked trigger (line 502-508) and outcome_hint (line 511-528) logic. The counter change goes here or at the update site (line 1183-1192).
- `ccya/engine/turn.py` lines 1089-1096 — Floor relief injection. The `not pending_gm_beat` condition removal goes here. The null-clear does NOT go here — it must be at line ~1006 (after the existing gm_beat apply block, before floor relief checks).
- `ccya/engine/turn.py` lines 1183-1192 — consecutive_pressure counter update. The re-key from directive to beat type goes here.
- `ccya/engine/turn.py` lines ~1096-1183 — recent_beats append location (between floor relief and counter update). Use `meta.setdefault("recent_beats", []).append(...)`.
- `ccya/engine/turn.py` lines 430-473 — `_compute_narration_directive`. The Breathe trigger refinement goes here (adding secondary pressure check).
- `ccya/prompts/storytell_system.j2` — Beat diversity guidance (lines 135-187). Beat history rendering and Scene Imperative guidance go here.
- `ccya/prompts/narrate_system.j2` — Lines 3-17 contain pending_gm_beat integration. Scene Imperative guidance is NOT added here — the narrator cannot read the directive (see change #5).
- `ccya/prompts/sections/` — New `_beat_history.j2` section (or inline in storytell_system.j2) for rendering recent_beats.
- `plans/findings/CONSOLIDATED-EV-FINDINGS.md` — Category 1 (GM Beat System) and Category 3 (Pacing Computation) contain the empirical evidence for every change in this design.

### Wiring note: `narrate_frequency_penalty`

If the narration stream adds a `narrate_frequency_penalty` field to `EngineConfig` (default 0.3), `build_engine_config()` at `ccya/engine/config.py:183-213` must explicitly pull it from `llm.get("narrate_frequency_penalty", 0.3)`. The function uses keyword-only construction — an unlisted field silently takes its dataclass default and the YAML knob becomes cosmetic. The fix is a one-line addition in `build_engine_config` alongside the existing temperature wiring (line 188-191).
