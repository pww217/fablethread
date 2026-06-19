# Semantic Thread Types Design

## Purpose

This document is the design authority for plans implementing semantic thread types, type-based pacing, and organic thread abandonment in the CCYA engine. It covers the arc/thread/beat/pacing subsystems.

## Problem Statement

The engine uses `urgency` (background/normal/urgent) as the primary pacing driver, conflating "what kind of tension" with "how pressing is it." This causes arcs to resolve every 1–6 turns instead of 8–15, breaking pacing. There is no semantic distinction between thread types, no mechanism for type changes mid-life, no explicit abandoned state handling, and the sanitizer lacks structured criteria for organic thread drop.

## Constraints

- Urgency and semantic type are orthogonal; both fields survive.
- No engine derivation or validation of thread type — storyteller assigns, sanitizer may correct.
- No engine enforcement of thread type → beat type relationship; prompt guidance only.
- No UI changes for semantic type rendering; prompt rendering only.
- No suppression flags for abandoned threads; re-emergence is fair game.
- No automatic thread removal; narrative-grounded abandonment only.
- No changes to `arc_categories` — they remain world-flavor, not tension classification.
- No staleness threshold — replaced by engine auto-dormant (4 turns no activity) + culling (>= 3 dormant).
- No solutions in this document; design decisions only.

## Non-goals

- No implementation steps (goes in plan docs).
- No code snippets beyond model shapes and type definitions.
- No changes to UI rendering (sidebar, turn review).
- No changes to `arc_categories` or their relationship to thread types.
- No engine-enforced thread type → beat type constraints.
- No automatic thread staleness or TTL-based removal.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Semantic thread types | Four types: threat, opportunity, complication, revelation. Stored on `ArcThread.type: Literal[...]`. | Answers "what kind of tension?" independently of urgency. Enables type-based pacing. |
| Urgency survives as modifier | `urgency: Literal["background", "normal", "urgent"]` remains on `ArcThread`. | Urgency answers "how pressing right now?" An opportunity can be urgent (closing soon). Orthogonal to type. |
| Storyteller assigns type | No engine derivation or validation. Storyteller sets type at creation, changes via `thread_update`. | Keeps narrative authority with the storyteller. Sanitizer may correct bad assignments in periodic pass. |
| Type changes mid-life | `type` field added to `ThreadUpdate`. A revelation becoming a threat (PC learns more) is valid and expected. | Reflects how tensions evolve in narrative; revelation threads naturally become threats/opportunities once the PC understands implications. |
| Seed generation enforces mixed types | `generate_seed_system.j2` instructs LLM to assign types and enforce at least one threat + at least one non-threat. Analogous to existing urgency cap at seed time. | Prevents homogenous starting states; ensures diverse tension landscape from turn 1. |
| Convergence score augmented, not replaced | Remove `thread_urgency_count` and `urgency_depth` components. Replace with: (1) active threat threads count, (2) urgent/closing opportunity threads count. Keep `scene_age`, `beat_streak`, `dice_weight` unchanged. | Threats naturally drive convergence; urgent opportunities can also contribute. Independent signals (scene age, beat streak, dice) remain. |
| Abandoned threads excluded from convergence | Abandoned threads do not count toward convergence calculations, regardless of when they were abandoned. | Abandoned threads have faded; they should not influence pacing pressure. |
| Thread type → beat type is prompt guidance | No engine enforcement. Parallel vocabulary documented in storyteller prompt: beats are what the narrator does with a tension; thread types describe the tension itself. | Keeps beat selection free-form; prevents mechanical coupling that reduces narrative flexibility. |
| arc_categories remain separate | No semantic type labels on `arc_categories`. They are world-flavor; thread types are tension classification. Relationship is emergent, not enforced. | Prevents conflating pack-level thematic buckets with runtime tension states. |
| abandoned is terminal state | `ThreadResolution.resolution_state` already includes `"abandoned"` (line 407). No schema change needed. Equal weight to `resolved` and `failed`. No suppression flag. | Abandoned means "tension faded given current circumstances" — not permanent suppression. Fair game for re-emergence. `completed_threads` TTL handles prompt visibility naturally. |
| Abandonment criteria are sanitizer judgment | No engine-enforced thresholds. Sanitizer prompt guidance includes explicit criteria (e.g., "no narrative mention in 5 turns + no activity in 3 turns") but sanitizer can override with narrative justification. | Sanitizer reads recent narration as evidence and is better positioned to judge narrative relevance than mechanical thresholds. |
| No UI changes for semantic types | No changes to `_state_left.html` or `tv.py`. Semantic types appear only in prompt rendering (storyteller/narrator prompts). | Keeps UI stable; semantic type is narrative metadata, not player-facing display. |
| Urgency tags in prompt rendering | `[URGENT]` only when `urgency == "urgent"`. No tag when `urgency == "normal"` (baseline). `[Background]` when `urgency == "background"` or `urgency == "dormant"`. No semantic type tags in rendering. | Keeps rendering minimal; urgency is the only field displayed in prompt thread list. |
| Dormant as fourth urgency value | `urgency: Literal["background", "normal", "urgent", "dormant"]` — dormant is lower than background, represents hidden tensions (secrets, foreshadowing). No separate field. | Simpler than separate field; fewer schema changes; dormant threads can represent hidden narrative elements the narrator can foreshadow. |
| Engine auto-dormant | Engine auto-demotes threads to dormant after 4 turns with no activity (progress/urgency change). Storyteller can override via `thread_update`. Sanitizer can also set dormant. | Replaces the staleness threshold (`thread_stale_threshold`). Gives engine hygiene control while preserving storyteller agency. |
| Culling mechanic | When >= 3 dormant threads, engine moves oldest (by `last_updated_turn`, not `added_turn`) to `completed_threads[]` with `resolution_state: "abandoned"`. Sanitizer can also cull proactively based on narrative evidence. | Hard cap prevents context bloat. Culling by `last_updated_turn` (not creation date) ensures the most neglected dormant thread is culled, not necessarily the oldest. |
| Storyteller can set dormant | Storyteller can set `urgency: "dormant"` via `thread_update`, same as they can set background/normal/urgent. | Preserves storyteller agency on when tensions go dormant. |
| Seed allows dormant | Seed generation can create dormant threads (hidden secrets, hidden opportunities, foreshadowing). No explicit prohibition. | Dormant threads represent hidden narrative elements the narrator can foreshadow or leave breadcrumbs for. |
| Backwards compat coercion | Unknown/invalid urgency values coerce to "background" (safest default). Dormant added to validator's valid set. | Prevents crashes from old data or LLM errors; dormant is now a valid value. |

## Open Questions

- Should the convergence score components for type-based signals be weighted differently (e.g., threat threads count more than opportunity threads, or do they contribute equally when urgent)?
- Should the staleness threshold (`thread_stale_threshold: 3`) be removed entirely, or kept as a fallback if engine auto-dormant is not implemented? (Answer: staleness threshold replaced by engine auto-dormant after 4 turns with no activity — settled above.)
- Should the culling threshold (>= 3 dormant) be configurable via `EngineConfig`, or hardcoded? (Answer: hardcoded, no config field needed — settled above.)
- Should the engine auto-dormant mechanism also apply to threads with `active=false` (latent threads), or only to threads with `active=true`? (Answer: only to threads with `active=true` — dormant threads are still "in the story world" but not currently active, same as latent threads but with clearer semantics — settled above.)

## Current State — What Exists

### ArcThread Model (`ccya/models.py:35-48`)

Fields: `id`, `summary`, `active`, `urgency`, `progress`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`, `urgency_set_turn`. No `type` field. No semantic classification.

### ThreadUpdate Model (`ccya/models.py:412-417`)

Fields: `id`, `active`, `urgency`, `progress`, `progress_kind`. No `type` field. No mechanism for type changes.

### ThreadResolution Model (`ccya/models.py:404-409`)

Fields: `id`, `resolution_state` (Literal["resolved", "failed", "abandoned"]), `outcome`, `promote_to_world_state`. Already supports `abandoned` state. No type-related fields.

### CampaignArc Model (`ccya/models.py:64-71`)

Fields: `visible_goal`, `goal_context`, `threads`, `completed_threads`, `resolution`, `last_thread_created_turn`. No type-related fields. No abandoned thread metadata.

### Convergence Score (`ccya/engine/_pacing.py:85-131`)

5-component score: (1) `thread_urgency_count >= 1`, (2) `thread_urgency_count >= 2`, (3) `scene_age >= config.scene_pressure_threshold`, (4) `beat_streak` (pressure ratio in 5-turn window), (5) `dice_weight` (crit_fail/fail + urgent thread). Urgency-based components (1) and (2) drive thread pressure. No type-based components.

### Thread Update Application (`ccya/engine/turn.py:112-211`)

`_apply_thread_updates()` processes `thread_update` from storyteller. Applies `active`, `urgency`, `progress` fields. No `type` handling. Auto-latent demotion based on staleness threshold (`thread_stale_threshold: 3`). No type change logic. No dormant handling. No culling mechanism.

### Thread Resolution Application (`ccya/engine/turn.py:334-`)

`_apply_thread_resolutions()` processes `thread_resolve` from storyteller. Moves threads from `threads[]` to `completed_threads[]` with `resolution_state` and `outcome`. No special handling for `abandoned` vs `resolved`/`failed`. No suppression flags.

### Sanitizer (`ccya/engine/thread_sanitizer.py`)

`sanitize_threads()` runs every `config.sanitize_every` turns (default 5). Reads recent narration, calls LLM with `sanitize_thread.j2` prompt. Parses JSON response, validates against `ThreadUpdate`, `ThreadResolution`, `ArcThread` models. Applies changes via `_apply_sanitization()`. No type correction logic. No explicit abandonment criteria in prompt.

### Seed Generation (`ccya/engine/seed.py:359-396`)

`_enforce_thread_limits()` enforces: max 2 active threads, non-active threads never urgent, urgency_set_turn tracking. No type enforcement. No mixed type guidance.

### Prompt Rendering (`ccya/prompts/sections/_thread_list.j2`)

Renders thread list with urgency tag: `[URGENT]` when urgent, no tag when normal, `[Background]` when background. No type rendering. No semantic type display.

### ArcThreadSummary (`ccya/prompts/context.py:77-85`)

Simplified thread data for prompts: `id`, `summary`, `urgency`, `progress`, `active`, `last_updated_turn`. No `type` field. No semantic type in prompt context.

### GMBeat Model (`ccya/models.py:428-466`)

Beat types: complication, revelation, opportunity, breathing_room, pressure, twist, setback, escalation, callback. No explicit relationship to thread semantic types. No engine-enforced mapping.

### arc_categories (`ccya/pack.py:155`)

Pack-level thematic buckets (e.g., `power_struggle`, `resource_scarcity`). No semantic type labels. No relationship to thread types enforced.

### Problems with Current State

- **No semantic thread types**: All threads are classified only by urgency. No distinction between threat, opportunity, complication, or revelation.
- **Urgency as primary pacing driver**: Convergence score relies on `thread_urgency_count` and `urgency_depth`, conflating "what kind of tension" with "how pressing."
- **No type change mechanism**: `ThreadUpdate` lacks `type` field. No way for storyteller to change a thread's semantic type mid-life.
- **No seed type enforcement**: Seed generation has no mixed type guidance. No minimum threat/non-threat requirements.
- **Abandoned state exists but lacks criteria**: `ThreadResolution.resolution_state` includes `"abandoned"` but sanitizer prompt has no explicit abandonment criteria. No structured guidance for when to abandon.
- **No type-based convergence**: Convergence score has no components for active threats or urgent opportunities.
- **Arc categories conflated with tension types**: No explicit separation between pack-level themes (arc_categories) and runtime tension classification (thread types).
- **Sanitizer lacks type correction**: No mechanism for sanitizer to correct bad thread type assignments.
- **Prompt rendering lacks type**: `_thread_list.j2` and `ArcThreadSummary` do not include semantic type. No type guidance in storyteller/narrator prompts.
- **No dormant urgency value**: No fourth urgency level for dormant threads (hidden tensions, secrets, foreshadowing). No mechanism to represent "low-priority but still in the story world" tensions.
- **Staleness threshold creates latent threads**: `thread_stale_threshold` (3 turns) creates `active=false` threads that are semantically identical to `active=true, urgency=background` threads. No clear distinction between "latent" and "background."
- **No culling mechanism**: No hard cap on dormant/latent threads, allowing context bloat when tensions accumulate without activity.
- **No engine auto-dormant**: No mechanism to automatically demote inactive threads to dormant, relying entirely on staleness threshold which creates the latent/active ambiguity.

## Proposed Solution

### Core Changes

**1. Add `type` field to `ArcThread` model**

New field: `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None`

- Optional field (backwards compatible with existing threads that have no type).
- Assigned by storyteller at creation, changeable via `thread_update`.
- No engine derivation or validation.

**2. Add `type` field to `ThreadUpdate` model**

New field: `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None`

- Allows storyteller to change thread type mid-life via `thread_update`.
- Engine applies type change alongside other `thread_update` fields (active, urgency, progress).

**3. Add `type` field to `ArcThreadSummary` model**

New field: `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None`

- No rendering changes (type not displayed in prompts).
- Type available in context for storyteller/narrator prompts if needed for narrative guidance.

**4. Add `type` handling to `_apply_thread_updates()` in `turn.py`**

Add to existing update loop (line ~154-185):
- If `update.type is not None`, apply `updates["type"] = update.type`.
- No validation; engine trusts storyteller assignment.

**5. Add `type` handling to `_apply_sanitization()` in `thread_sanitizer.py`**

Add to existing update loop (line ~372-380):
- If `tu.get("type") is not None`, apply type change to thread.
- No validation; sanitizer can correct bad assignments.

**6. Add dormant to validator's valid urgency set in `_validate_parsed()` in `thread_sanitizer.py`**

Add "dormant" to the validator's valid urgency set (line ~239):
- If `urgency` is "dormant", accept it as valid (same as background/normal/urgent).
- No coercion; dormant is now a legitimate urgency value.

**7. Replace urgency-based convergence components with type-based equivalents**

In `compute_convergence_score()` (`_pacing.py:85-131`):
- Remove component 1 (`thread_urgency_count >= 1`) and component 2 (`thread_urgency_count >= 2`).
- Replace with:
  - Component 1: `active_threat_threads >= 1` (counts threads with `type == "threat"` and `active == True`).
  - Component 2: `urgent_opportunity_threads >= 1` (counts threads with `type == "opportunity"` and `urgency == "urgent"`).
- Keep components 3, 4, 5 unchanged (`scene_age`, `beat_streak`, `dice_weight`).
- Abandoned threads do not count toward convergence (they are moved to `completed_threads[]` and excluded from active thread lists).
- Dormant threads do not count toward convergence (they are not active/pressing).

**8. Add engine auto-dormant mechanism to `turn.py`**

Replace the staleness threshold (`thread_stale_threshold`) with engine auto-dormant:
- After 4 turns with no activity (no progress, no urgency change, no type change), engine auto-demotes thread to `urgency: "dormant"`.
- Only applies to threads with `active == True` (dormant threads are still "in the story world" but not currently active).
- Storyteller can override via `thread_update` (set urgency back to background/normal/urgent).
- Sanitizer can also set dormant via `thread_updates` in its periodic pass.

**9. Add engine culling mechanism to `turn.py`**

Hard cap on dormant threads:
- When >= 3 dormant threads exist, engine moves oldest (by `last_updated_turn`, not `added_turn`) to `completed_threads[]` with `resolution_state: "abandoned"` and `outcome: "Thread faded from relevance — no narrative activity in N turns."`
- Culling by `last_updated_turn` (not creation date) ensures the most neglected dormant thread is culled, not necessarily the oldest.
- Sanitizer can also cull proactively based on narrative evidence (in addition to the engine's mechanical cull).

**10. Update seed generation prompt (`generate_seed_system.j2`)**

Add thread type rules (after existing "Thread rules" section, line ~137):
- Instruct LLM to assign `type` to each thread.
- Enforce: at least one thread with `type == "threat"`, at least one thread with `type != "threat"` (opportunity/complication/revelation).
- Allow dormant threads (hidden secrets, hidden opportunities, foreshadowing). No explicit prohibition.
- Analogous to existing urgency cap enforcement in `_enforce_thread_limits()`.

**11. Update sanitizer prompt (`sanitize_thread.j2`)**

Add explicit abandonment criteria (in "Instructions" section, line ~36):
- "If a thread has no narrative mention in 5+ turns AND no activity (progress/urgency change) in 3+ turns, consider resolving as abandoned."
- "Abandonment requires narrative justification — do not abandon threads that are still relevant to the current situation."
- Add type correction guidance: "If a thread's assigned type no longer matches its narrative role, update the type field."
- Add dormant guidance: "If a thread has no activity in 4+ turns, consider setting urgency to 'dormant'."
- Add culling guidance: "If there are >= 3 dormant threads, consider resolving the oldest (by last_updated_turn) as abandoned."

**12. Update prompt rendering (`_thread_list.j2`)**

Update urgency tag rendering:
- `[URGENT]` only when `urgency == "urgent"`.
- No tag when `urgency == "normal"` (baseline).
- `[Background]` when `urgency == "background"` or `urgency == "dormant"` (dormant renders the same as background).
- No semantic type tags in rendering (type is narrative metadata, not displayed).

### Alternatives Considered and Rejected

| Alternative | Why Rejected | Trade-off |
|---|---|---|
| Engine derives thread type from beat history | Adds complexity, reduces storyteller agency, creates coupling between beat selection and thread classification | Storyteller has better narrative context for type assignment |
| Engine enforces thread type → beat type mapping | Reduces narrative flexibility, creates mechanical coupling, limits beat selection freedom | Prompt guidance preserves the parallel vocabulary without enforcement |
| Automatic thread removal based on staleness | Breaks narrative continuity, removes storyteller agency, creates "silent deletion" | Narrative-grounded abandonment (sanitizer judgment) preserves agency |
| Suppression flags for abandoned threads | Prevents legitimate re-emergence, adds metadata complexity, creates "zombie" threads | No suppression flag; `completed_threads` TTL handles visibility naturally |
| Semantic type tags in UI rendering | Adds UI complexity, type is narrative metadata not player-facing, breaks existing UI stability | Prompt rendering only; UI remains unchanged |
| arc_categories get semantic type labels | Conflates pack-level themes with runtime tension states, creates redundant classification | Arc categories remain world-flavor; thread types remain tension classification |
| Hard engine thresholds for abandonment | Sanitizer is better positioned to judge narrative relevance; mechanical thresholds are brittle | Explicit criteria in prompt guidance, but sanitizer can override with narrative justification |
| Separate `status` field for dormant (vs. fourth urgency value) | More schema changes, more complexity, creates redundancy with `active` field | Fourth urgency value is simpler; dormant is "lower urgency" not a separate status |
| Cull by `added_turn` (oldest creation date) | Punishes threads that were recently updated, not the most neglected | Cull by `last_updated_turn` (most neglected) is more fair and narrative-grounded |
| No engine auto-dormant (sanitizer only) | Removes engine hygiene control, relies entirely on periodic sanitizer passes | Engine auto-dormant provides immediate hygiene; sanitizer can also cull proactively |
| No engine culling (sanitizer only) | No hard cap, dormant threads accumulate indefinitely | Engine culling provides safety net; sanitizer can also cull proactively |
| Seed forbids dormant threads | Prevents hidden secrets/opportunities, reduces narrative depth | Dormant threads represent hidden narrative elements the narrator can foreshadow |
| Storyteller cannot set dormant | Removes storyteller agency on when tensions go dormant | Storyteller can set dormant via `thread_update`, same as other urgency values |

## Failure Modes and Risks

- **Storyteller never assigns types**: If storyteller ignores the type field, the design degrades gracefully — convergence score falls back to treating all threads equally (no type-based components trigger), urgency-based pacing is lost but not broken.
- **Sanitizer over-corrects types**: Sanitizer may change thread types without narrative justification. Mitigation: prompt guidance emphasizes narrative evidence, not mechanical thresholds.
- **Seed generation ignores type constraints**: LLM may generate homogenous starting states (e.g., all threats). Mitigation: `_enforce_thread_limits()` can add type enforcement analogous to existing urgency cap enforcement.
- **Abandoned threads re-emerge unexpectedly**: No suppression flag means abandoned threads can be re-created by storyteller. This is by design — narrative justification is the only gate.
- **Convergence score degrades without types**: If no threads have types assigned, convergence score components 1 and 2 never trigger, making it harder to reach CLIMAX phase. Mitigation: prompt guidance in storyteller prompt emphasizes type assignment.
- **Type changes mid-life create confusion**: A revelation becoming a threat may confuse the storyteller if they expect types to be stable. Mitigation: prompt guidance explicitly states type changes are expected and valid.
- **Engine auto-dormant too aggressive**: 4 turns with no activity may be too short for some tensions (e.g., political situations that resolve slowly). Mitigation: storyteller can override via `thread_update` (set urgency back to background/normal/urgent).
- **Culling removes threads too early**: >= 3 dormant may be too high a threshold, causing context bloat before culling kicks in. Mitigation: sanitizer can also cull proactively based on narrative evidence, providing a safety net below the engine's hard cap.
- **Dormant threads accumulate**: If storyteller never sets threads to dormant, they stay active with background urgency indefinitely, wasting context. Mitigation: engine auto-dormant after 4 turns with no activity provides hygiene control.
- **Dormant threads re-emerge unexpectedly**: No suppression flag means dormant threads can be reactivated by storyteller at any time. This is by design — narrative justification is the only gate.
- **Backwards compat crashes**: Old data with unknown urgency values (from LLM errors or legacy saves) may crash on load. Mitigation: unknown urgency values coerce to "background" (safest default). Dormant added to validator's valid set.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `thread_urgency_count` component | `compute_convergence_score()` | Replaced by `active_threat_threads` component |
| `urgency_depth` component | `compute_convergence_score()` | Replaced by `urgent_opportunity_threads` component |
| No explicit abandonment criteria | `sanitize_thread.j2` | Added explicit criteria (5 turns no mention + 3 turns no activity) |
| No type correction guidance | `sanitize_thread.j2` | Added type correction guidance |
| No type enforcement | `generate_seed_system.j2` | Added mixed type requirements (at least one threat, at least one non-threat) |
| No type handling | `_apply_thread_updates()` | Added type field handling |
| No type handling | `_apply_sanitization()` | Added type field handling |
| No type field | `ArcThreadSummary` | Added type field (no rendering changes) |
| No dormant urgency value | `ArcThread`, `ThreadUpdate`, `ArcThreadSummary` | Added "dormant" to urgency Literal |
| No auto-dormant mechanism | Engine (turn.py) | Added auto-dormant after 4 turns with no activity |
| No culling mechanism | Engine (turn.py) | Added culling when >= 3 dormant, by last_updated_turn |
| No staleness threshold | `config.thread_stale_threshold` | Replaced by engine auto-dormant (4 turns no activity) |
| No dormant handling | `_apply_thread_updates()` | Added dormant urgency handling |
| No dormant handling | `_apply_sanitization()` | Added dormant urgency handling |
| No dormant handling | `_validate_parsed()` | Added dormant to validator's valid urgency set |

## What Is Unchanged

- `ThreadResolution.resolution_state` (resolved/failed/abandoned) — already supports abandoned, no schema change needed.
- `GMBeat` model and beat types — no engine-enforced relationship to thread types, prompt guidance only.
- `arc_categories` on `ScenarioBrief` — remain world-flavor, no semantic type labels added.
- `scene_age`, `beat_streak`, `dice_weight` convergence components — unchanged, measure independent signals.
- UI rendering (`_state_left.html`, `tv.py`) — no changes for semantic type display.
- `completed_threads` TTL handling — abandoned threads handled naturally by existing TTL, no suppression flags.
- Thread cap eviction (`thread_max_active`) — unchanged, operates on active count not type.
- Urgency decay (`thread_urgency_max_age`) — unchanged, urgent→normal→background after N turns.
- `_merge_arc_update()` in `delta_builder.py` — no changes, merges arc state as-is.
- `_apply_arc_resolve()` in `turn.py` — no changes, arc resolution logic unchanged.
- `_apply_thread_resolutions()` in `turn.py` — no changes, abandoned state already handled as terminal.
- `BEAT_BUCKETS`, `BEAT_PHASE_MAP` in `_pacing.py` — unchanged, beat constraint map not affected by thread types.
- `detect_spiral()`, `derive_allowed_beat_types()` in `_pacing.py` — unchanged, spiral detection and beat derivation not affected by thread types.
- `sanitize_every`, `sanitize_temperature` config fields — unchanged, sanitizer frequency and temperature not affected by thread types.
- `thread_memory_ttl`, `arc_memory_ttl` config fields — unchanged, completed thread visibility TTL not affected by thread types.

## New Model Shapes

### ArcThread (updated)

```python
class ArcThread(BaseModel):
    id: str
    summary: str
    active: bool = True
    urgency: Literal["background", "normal", "urgent", "dormant"] = "normal"
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: list[ProgressEntry] = Field(default_factory=list)
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
    last_updated_turn: int | None = None
    added_turn: int | None = None
    urgency_set_turn: int | None = None
```

### ThreadUpdate (updated)

```python
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent", "dormant"] | None = None
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: str | None = None
    progress_kind: Literal["advancement", "setback", "shift"] | None = None
```

### ArcThreadSummary (updated)

```python
class ArcThreadSummary(BaseModel):
    id: str
    summary: str
    urgency: Literal["background", "normal", "urgent", "dormant"]
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: list[str] = Field(default_factory=list)
    active: bool
    last_updated_turn: int | None = None
```

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|------|------------------|----------------|
| `ccya/models.py:35-48` | ArcThread model | Add `type` field, add "dormant" to urgency Literal |
| `ccya/models.py:412-417` | ThreadUpdate model | Add `type` field, add "dormant" to urgency Literal |
| `ccya/models.py:404-409` | ThreadResolution model | No changes, already supports abandoned |
| `ccya/models.py:64-71` | CampaignArc model | No changes, threads already stored |
| `ccya/engine/_pacing.py:85-131` | compute_convergence_score() | Replace urgency-based components with type-based equivalents |
| `ccya/engine/turn.py:112-211` | _apply_thread_updates() | Add type handling, add dormant handling, remove staleness threshold |
| `ccya/engine/turn.py:334-` | _apply_thread_resolutions() | No changes, abandoned already handled |
| `ccya/engine/turn.py:1192-1291` | Arc director (turn processing) | Add engine auto-dormant mechanism, add culling mechanism |
| `ccya/engine/thread_sanitizer.py:205-290` | _validate_parsed() | Add type handling, add dormant to validator's valid urgency set |
| `ccya/engine/thread_sanitizer.py:356-400` | _apply_sanitization() | Add type handling, add dormant handling |
| `ccya/engine/seed.py:359-396` | _enforce_thread_limits() | No changes, type enforcement goes in prompt |
| `ccya/prompts/sections/_thread_list.j2` | Thread list rendering | Update urgency tag rendering (dormant = [Background]) |
| `ccya/prompts/generate_seed_system.j2:137-155` | Seed thread rules | Add type assignment, mixed type requirements, allow dormant |
| `ccya/prompts/sanitize_thread.j2:36-73` | Sanitizer instructions | Add explicit abandonment criteria, type correction, dormant, culling guidance |
| `ccya/prompts/context.py:77-85` | ArcThreadSummary | Add type field, add "dormant" to urgency Literal |
| `ccya/prompts/context.py:114-150` | ArcThreadBlock.from_state() | No changes, type field optional |
| `ccya/engine/config.py:160-178` | EngineConfig | No changes, config fields unchanged (thread_stale_threshold removed) |
| `ccya/state/delta_builder.py:52-67` | _merge_arc_update() | No changes, merges arc state as-is |
| `ccya/pack.py:155` | ScenarioBrief.arc_categories | No changes, arc_categories remain separate |
| `ccya/templates/_state_left.html:75-130` | Sidebar thread display | No changes, UI unchanged |
| `ccya/server/tv.py:235-265` | Turn review thread display | No changes, UI unchanged |
