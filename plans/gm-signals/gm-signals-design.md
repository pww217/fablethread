# GM Signal System Redesign

## Purpose

This document defines the target state for the pacing, arc thread, and GMB extender systems in `ccya`.
It is the design authority for all plans implementing changes described here.

---

## Current State — What Exists

### Pacing Signals: Three Redundant Age Trackers

`turn.py::_compute_ages()` produces three independent age counters written to `TurnContext._ages`:

- `scene_age` — turns in the current scene (since `scene.turn_entered`)
- `location_age` — turns at the current location (since `scene.location_entered_turn`)
- `combat_age` — turns since `scene.combat_started_turn` (set when scene tags contain `"combat"`)

These feed three distinct directives in `_compute_narration_directive()`:

- `Location Pressure` (location_age ≥ 3)
- `Location Imperative` (location_age ≥ 5)
- `Combat Fatigue` (combat_age ≥ 3, secondary append)

All three directives express the same semantic: *the story has stalled; move it forward.* They differ only in flavor. The narrator prompt in `narrate_system.j2` defines `Location Imperative` and `Location Pressure` as separate directives with separate instructions, adding token cost and LLM confusion when both conditions fire simultaneously.

### Pacing Signals: Beat-Locked Relief

`_compute_pacing_context()` sets `beat_locked = True` when `momentum <= config.momentum_floor` (-3). This fires a `"Resolve a Threat"` directive. However, `beat_locked` is documented as "Progress MUST emit breathing_room beat" — yet `pending_gm_beat` is zeroed unconditionally after narration in `run_turn`, before the storyteller has a chance to write and persist a new beat. The beat carryover across turns is broken by this unconditional clear.

There is no `consecutive_pressure_turns` counter. The engine cannot detect a player who has received three successive `Pressure` or `Overwhelm` directives without any thread advancement — a common sign the player is stuck.

### Band History: Not Tracked

`state["meta"]` has no rolling band log. Three consecutive `fail`/`crit_fail` rolls are indistinguishable from a successful turn at the engine level — momentum is a lagging aggregate, not a sequential signal.

### Arc Thread Creation: No Deduplication by Concept

`_apply_thread_signals()` checks thread creation against `existing_ids` (exact `id` string match). Two threads with semantically identical tensions but different IDs both pass the gate. The storyteller prompt in `storytell_system.j2` has no instruction to check for conceptual overlap with existing threads before emitting `thread_add`.

### Primary Thread: Not Designated

There is no mechanism to surface a single "most important active thread" to the narrator or storyteller. The narrator receives all active threads with equal weight.

### GMB Extenders: Mood

`Mood` is referenced in design discussion but is **absent from both `narrate_system.j2` and `storytell_system.j2`**. It does not appear in the narrator user prompt template context. It is inert.

### ARC_UPDATE: `thematic_question` and `pc_drive` Not Exposed

`_ALLOWED_NARRATOR_ARC_KEYS` in `turn.py` permits `thematic_question` and `pc_drive` updates, but the narrator system prompt's `<<<ARC_UPDATE_START>>>` JSON schema example only shows `discovered_truths` and `visible_goal`. The LLM does not know it can emit `thematic_question`.

### `recently_left` NPC Tracking

`scene.recently_left` and `scene.recently_left_turns` track NPCs that departed the scene. `npc_roster.py::build_npc_roster()` uses this to tag NPCs as `JUST_LEFT` in narrator context. The `narrate_system.j2` `## NPCs in scene` section has dedicated `JUST_LEFT` handling rules. The signal is low-value and adds state complexity.

### Problems with Current State

- `location_age`, `scene_age`, and `combat_age` encode the same "move on" intent in three different variables with overlapping directive strings — adding narrator prompt tokens with marginal semantic difference.
- `beat_locked` relief is conceptually correct but mechanically broken: the unconditional `pending_gm_beat = None` clear after narration destroys any carried beat before it reaches the next turn.
- No consecutive-pressure counter means the engine cannot distinguish a tense-but-progressing sequence from a stuck loop.
- No band history means three consecutive failures are invisible to the pacing system.
- Thread deduplication operates on ID strings only; semantic duplicates are not detected at creation time.
- `Mood` is a dead field — adds no signal.
- `thematic_question` is silently updatable in engine but the narrator is never told.
- `recently_left` + `JUST_LEFT` machinery adds state and prompt complexity for minimal storytelling value.

---

## Target State — What It Becomes

### Core Changes

#### 1. Unified `scene_age` — Single Staleness Signal

Replace `location_age`, `combat_age`, and `scene_age` with a single `scene_age` integer in `state["scene"]`. `scene_age` is computed as turns elapsed since `scene.turn_entered`. It increments every turn regardless of location or combat status.

Weighted staleness threshold: the age threshold for the "move forward" directive is reduced when the scene has combat tags (combat presses faster). The weight is a multiplier applied to the raw `scene_age` before threshold comparison, not a separate counter.

**Reset condition:** `scene_age` resets when `scene.turn_entered` is updated — i.e., when the scene extractor emits a `location_change`. Intra-scene pivots (new NPC arrives, confrontation changes character) do NOT reset `scene_age`. Scene age is location-scoped.

**Directive replacement:** `Location Pressure`, `Location Imperative`, and `Combat Fatigue` are removed. A single new directive `Scene Imperative` replaces all three at the high threshold. An intermediate `Scene Pressure` replaces `Location Pressure`. These two directives subsume all three legacy directives.

**Narrator prompt impact:** Remove the `Location Pressure`, `Location Imperative`, and `Combat Fatigue` directive definitions from `narrate_system.j2`. Add `Scene Pressure` and `Scene Imperative` definitions. Estimated net reduction: ~80 tokens.

#### 2. `pending_gm_beat` Carryover Fix

Remove the unconditional `state["meta"]["pending_gm_beat"] = None` line from `run_turn` post-narration. The only beat lifecycle management is:

- **Written:** after storytell extraction, if `StorytellerResult.gm_beat` is non-null, write to `state["meta"]["pending_gm_beat"]` with `beat_expires_turn = turn_no + 2`.
- **Consumed (read-gated):** `_narrate_setup()` reads `pending_gm_beat` and passes it to the narrator only if `turn_no <= beat_expires_turn`.
- **Cleared:** only when a new beat is written (replaces), or when `turn_no > beat_expires_turn` at read-gate time.

The beat now persists across turns until it expires or is replaced, as designed.

#### 3. Consecutive Pressure Counter + Band History

**`state["meta"]["recent_bands"]`:** A list of the last N band strings (default N=3, configurable as `EngineConfig.recent_bands_window`). Appended after `_ruling_phase()` resolves `outcome.band`, before `_compute_pacing_context()` runs.

**`state["meta"]["consecutive_pressure_turns"]`:** Integer counter. Incremented each turn when `directive` resolves to `Pressure` or `Overwhelm` AND `thread_advance` from the prior turn's storyteller result was empty. Reset to 0 whenever the directive is not `Pressure`/`Overwhelm`, or when any thread was advanced.

**Relief trigger:** `beat_locked` fires when `consecutive_pressure_turns >= config.consecutive_pressure_threshold` (default 3) OR when the last N bands in `recent_bands` are all in `{"fail", "crit_fail"}`. The `momentum <= momentum_floor` trigger is removed.

`beat_locked` continues to set directive to a breathing_room-favoring value (existing behavior in storytell guidance).

#### 4. Arc Thread Canonical Key Deduplication

`ArcThread` gains a new optional field `key: str | None` (default `None`). The `key` is a 2–4 token snake_case canonical concept label (e.g. `"lira_betrayal"`, `"hull_breach"`). It is emitted by the storyteller in `thread_add`.

At thread creation in `run_turn`, before accepting `thread_add`:
1. Existing `id` collision check (unchanged).
2. New: if `thread_add.key` is non-null, check against `{t.key for t in arc.threads if t.key}`. If collision: reject `thread_add`, log `WARNING thread_add.key_collision`.

The storyteller prompt gains one instruction: before emitting `thread_add`, check active and latent thread summaries for conceptual overlap; if overlap exists, emit `null` instead.

`key` is not required (nullable) to preserve backwards compatibility with existing saved arc threads that have no key. The check only fires when the incoming `thread_add` provides one.

#### 5. `thematic_question` in Narrator ARC_UPDATE

The narrator system prompt's `<<<ARC_UPDATE_START>>>` JSON schema example is updated to include `thematic_question` as an allowed key. The rule remains: only emit when the turn's narration has materially shifted the story's emotional register.

The `_ALLOWED_NARRATOR_ARC_KEYS` set in `turn.py` already includes `thematic_question`; no engine change needed.

#### 6. Remove `recently_left` and `JUST_LEFT`

`scene.recently_left` and `scene.recently_left_turns` are removed from state. `npc_roster.py::build_npc_roster()` no longer emits `JUST_LEFT`-tagged NPC entries. The `## NPCs in scene` section in `narrate_system.j2` that describes `JUST_LEFT` behavior is removed. The `JUST_LEFT` presence tag enum value is removed from any type definitions.

#### 7. Drop Mood

No `Mood` field is added anywhere. No design action.

---

## Decision Table

| Decision | What | Why |
|---|---|---|
| Collapse age trackers | Replace `location_age`, `combat_age`, `scene_age` with single `scene_age`; replace 3 directives with 2 | One source of truth per concept; reduces narrator prompt tokens and LLM confusion |
| Scene age resets on location change only | `scene_age` tied to `scene.turn_entered`; intra-scene pivots do not reset | Location change is the only unambiguous signal that stale-scene pressure is resolved |
| Combat weight via threshold reduction | Combat presence lowers the effective staleness threshold, not a separate counter | Avoids re-introducing a second age variable |
| Remove unconditional `pending_gm_beat = None` | Beat clears only at write (replace) or expiry read-gate | Fixes carryover bug; aligns with documented intent |
| `consecutive_pressure_turns` in `state["meta"]` | Persisted across turns, reset on thread advance or non-pressure directive | Momentum is lagging aggregate; sequential pressure needs a sequential counter |
| Relief trigger: consecutive pressure OR all-fail bands | `beat_locked` when `consecutive_pressure_turns >= threshold` OR all recent bands are fail/crit_fail | Detects stuck player by two independent orthogonal signals |
| Remove `momentum <= momentum_floor` relief trigger | Replaced by the above | Momentum floor is a coarse signal; covered better by the two new signals |
| `ArcThread.key` nullable | key checked only when emitted; null skips dedup check | Preserves existing saved states; no migration required |
| Remove `recently_left` entirely | Drop field, decay counter, roster tag, and narrator prompt section | Low-value signal; narrator prompt complexity not justified |
| Drop Mood | Not added anywhere | Not present in any LLM prompt; no signal value confirmed |
| `thematic_question` in narrator ARC_UPDATE schema | Prompt schema example updated; engine already accepts it | Closes gap between engine capability and narrator knowledge |
| Primary thread: deferred | Not implemented in this design | Deferred; value unclear without a concrete consumer |
| Player engagement pattern: deferred | Not implemented in this design | Output / consumer use case not defined |

---

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `location_age` | `turn.py::_compute_ages()`, `TurnContext._ages` dict key | Subsumed by `scene_age` |
| `combat_age` | `turn.py::_compute_ages()`, `TurnContext._ages` dict key | Subsumed by weighted `scene_age` threshold |
| `Location Pressure` directive | `_compute_narration_directive()`, `narrate_system.j2` | Replaced by `Scene Pressure` |
| `Location Imperative` directive | `_compute_narration_directive()`, `narrate_system.j2` | Replaced by `Scene Imperative` |
| `Combat Fatigue` directive | `_compute_narration_directive()`, `narrate_system.j2` | Subsumed into weighted scene_age threshold |
| Unconditional `pending_gm_beat = None` clear | `turn.py::run_turn()` post-narration block | Beat lifecycle handled by write/expiry only |
| `momentum <= momentum_floor` relief trigger | `_compute_pacing_context()` `beat_locked` condition | Replaced by `consecutive_pressure_turns` + band history |
| `scene.recently_left` | `state.yaml` schema, `state/io.py`, `npc_roster.py` | Deleted with no replacement |
| `scene.recently_left_turns` | `state.yaml` schema, `state/io.py` | Deleted with no replacement |
| `JUST_LEFT` presence tag | NPC roster tag enum, `narrate_system.j2` NPCs section | Deleted with no replacement |
| `Mood` GMB extender | Never existed in any file | No action needed; confirmed inert |

---

## What Is Unchanged

- `_apply_thread_signals()` lifecycle (advance, expire, promote, complete) — unchanged
- `_apply_thread_resolutions()` — unchanged
- `_compute_narrative_velocity()` — unchanged
- `_compute_pacing_context()` structure — `beat_locked`, `gate`, `directive` fields unchanged; only the `beat_locked` condition changes
- `_ACTIVE_THREAD_CAP`, `_LATENT_THREAD_CAP`, `_EXPIRE_SILENT_TURNS`, `_PROMOTION_COOLDOWN_TURNS` constants — unchanged
- `PacingContext` dataclass fields — unchanged
- `ArcThread` lifecycle (active/latent/completed) — unchanged
- `arc.threads[]` unified model — unchanged
- `thread_advance`, `thread_resolve`, `thread_add` storyteller fields — unchanged except `thread_add` gains `key` field
- `_ALLOWED_NARRATOR_ARC_KEYS` set contents — unchanged (already includes `thematic_question`)
- `<<<ARC_UPDATE_START>>>` engine parsing logic in `_extract_narrator_arc_update()` — unchanged
- `beat_expires_turn` write logic — unchanged (still `turn_no + 2`)
- `narrate_system.j2` body (outside directive definitions and JUST_LEFT section) — unchanged
- `storytell_system.j2` body (outside one new `thread_add` dedup instruction) — unchanged
- `EngineConfig` existing fields — unchanged; two new fields added (`recent_bands_window`, `consecutive_pressure_threshold`)
- `scene.turn_entered` — unchanged; becomes the sole input to `scene_age`
- `scene.location_entered_turn` — unchanged but no longer used by `_compute_ages()`; [OPEN: remove from state or keep as dormant field? Recommend remove to stay clean.]
- `scene.combat_started_turn` — unchanged but no longer used by `_compute_ages()`; [OPEN: same question — recommend remove.]

---

## Migration Notes

No state migration function is required for most changes. The following fields must be handled by `_migrate_state()` in `state/io.py`:

- `scene.recently_left` — if present, drop silently on load.
- `scene.recently_left_turns` — if present, drop silently on load.
- `state["meta"]["consecutive_pressure_turns"]` — if absent, default to `0` on load.
- `state["meta"]["recent_bands"]` — if absent, default to `[]` on load.

No schema version bump is required; `_migrate_state()` handles missing/extra keys by convention.

---

## New Model Shapes

### EngineConfig additions

```python
recent_bands_window: int = 3
consecutive_pressure_threshold: int = 3
```

### ArcThread addition

```python
key: str | None = None  # 2–4 token canonical concept label; used for dedup at thread_add time
```

---

## Prompt Token Impact

| Template | Change | Estimated Token Delta |
|---|---|---|
| `narrate_system.j2` | Remove `Location Pressure`, `Location Imperative`, `Combat Fatigue` definitions; add `Scene Pressure`, `Scene Imperative` definitions; remove `JUST_LEFT` NPC handling block | −120 to −150 tokens |
| `narrate_system.j2` | Add `thematic_question` to `<<<ARC_UPDATE_START>>>` JSON example | +10 tokens |
| `storytell_system.j2` | Add one sentence to `thread_add` rules: check for conceptual overlap before emitting; emit `key` field | +20 tokens |
| Narrator user prompt (`_arc.j2` or equivalent) | No change to template; `scene_age` not surfaced directly to LLM | 0 |

Net: ~−90 to −120 tokens per turn across narrate + storytell prompts.

---

## Context for Implementing LLMs

- `ccya/engine/turn.py` — `_compute_ages()`, `_compute_pacing_context()`, `_compute_narration_directive()`, `_apply_thread_signals()`, `run_turn()` post-narration beat clear, `_ALLOWED_NARRATOR_ARC_KEYS`. Primary implementation file for all pacing and thread changes.
- `ccya/models.py` — `ArcThread` (add `key` field), `EngineConfig` (add `recent_bands_window`, `consecutive_pressure_threshold`), `PacingContext` (read `beat_locked` condition change). Read before touching any model.
- `ccya/state/io.py` — `_migrate_state()`. Add migration drops for `recently_left`, `recently_left_turns`; defaults for `consecutive_pressure_turns`, `recent_bands`.
- `ccya/engine/npc_roster.py` — `build_npc_roster()`. Remove `recently_left`/`JUST_LEFT` branch.
- `ccya/prompts/narrate_system.j2` — Remove 3 directives; add 2; remove `JUST_LEFT` section; update ARC_UPDATE schema.
- `ccya/prompts/storytell_system.j2` — Add `key` field to `thread_add` schema; add one dedup instruction.
- `docs/repomap.md` — Update scene thread lifecycle section, state shape section, EngineConfig field naming section after implementation.
