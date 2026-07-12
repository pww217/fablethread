# GM Beat Overhaul Design

## Purpose

This document is the design authority for plans implementing the GM beat overhaul. It covers the new beat model (effect-driven, NPC-first), removal of `surface_as`, two-section storytell output, and NPC context injection from scene to storytell via extraction context.

## Problem Statement

The current GM beat system has three structural weaknesses:

1. **Beats are type-driven, not narrative-driven.** The storyteller selects from a constrained enum of beat types (`pressure`, `complication`, `escalation`, etc.) guided by the pacing engine. This produces mechanically correct but narratively shallow beats — the storyteller optimizes for type compliance rather than scene logic.

2. **`surface_as` is dead weight.** The field is rendered in prompts, validated (or rather, not validated), checked by an eval checker, and warned about in system prompts — but it has zero mechanical effect. It exists purely as a rendering hint that the narrator is told not to use. Every byte spent on `surface_as` is wasted.

3. **The storyteller has too much NPC context, not the right kind.** The storyteller receives `npc_roster` (built from compendium at `storytell.py:63`) which includes bios, personalities, presence metadata, notes, position, last_seen_location, departed_reason. This is token-heavy and includes NPCs irrelevant to the current beat. The storyteller needs a lighter, curated view — relevant NPCs with only the psychological fields that matter for beat generation.

## Constraints

- **No new pipeline steps.** Beat generation stays inside the existing storytell stream. A future split is anticipated but not designed.
- **No async / background execution.** Single LLM call per turn.
- **Storytell context must not grow meaningfully.** `npc_context` replaces `npc_roster` for beat generation (cuts personalities, bios, presence metadata). Not additive. `npc_context` is built by the scene extractor (Step 2a), flows through `_ExtractionContext` (same-turn passer), and is received by storytell. Scene decides which NPCs are relevant based on narration + NPC fields alone, passes structured context to storytell.
- **Prompt must not conflate the two cognitive modes.** Structural separation in both input framing and output fields is the primary mitigation.
- **No beat type → thread ID mechanical coupling.** The connection to threads should be inferrable from `effect`.
- **Direct swap.** Per project AGENTS.md: no backwards compatibility. Delete unused fields, routes, config keys, models.
- **`surface_as` removal must be clean.** Checker, validator, and prompt warnings all go.

## Non-goals

- Async / background beat generation
- Separate pipeline step for beat generation
- Per-NPC beat emission (one beat per turn, as now)
- Dice-outcome-gated beats
- Beat anchored to specific thread ID
- Changes to beat TTL or lifecycle mechanics (2-turn TTL stays)
- Changes to narrator prompt structure beyond replacing `type`+`surface_as` with `effect`
- Full NPC context in storytell (bio, archetype, full presence model)
- Deriving beat types from `effect` text for pacing calculations

## Decision Table

| Decision | What | Why |
|---|---|---|
| Beat types kept for pacing | `type` field stays on the beat model. The storyteller still emits a `type` constrained by `BEAT_PHASE_MAP`. | Pacing engine (convergence scoring, phase transitions, `derive_allowed_beat_types`) depends on `type`. Rewriting it is out of scope. |
| `effect` is the primary creative field | `effect: str` on the beat model. Required — the LLM must emit a short, concrete sentence describing what is about to happen. Narrator prompt uses it directly. | Replaces `surface_as` as the narrator's creative guidance. Short and concrete ("npc fears exposure, moves to block", "weather event disrupts"). Gives narrator flexibility — not a category label. Required in all cases (even environmental beats). |
| `surface_as` removed entirely | Field deleted from `GMBeat` model. All references in prompts, checkers, validators go. | Zero mechanical effect. Dead code. |
| Two-section storytell output | Flat JSON. No `record` wrapper. Structural separation is purely in the prompt (instructions tell the LLM to think in two sections). `gm_beat` field name is kept (not renamed to `beat`). | Keeps the extraction pipeline unchanged. The cognitive separation is in the prompt, not the schema. Keeping `gm_beat` avoids renaming downstream references. |
| `npc_id` + `driver` on beat | Optional fields on the beat. Required when an NPC is the source. `driver` is one of `motivation | fear | leverage`. | Tells the narrator exactly whose psychology is driving the action. Useful for evals and future tooling. |
| NPC context built by scene, flows through extraction_ctx to storytell | Scene extracts relevant NPC psychological fields based on narration + NPC fields alone (no arc/thread context). Passes structured list with npc_id + field type + effect string to storytell via `_ExtractionContext` (same-turn passer). Storytell picks which fields to use based on threads/arc/context that scene does not have. Replaces the full `npc_roster` for beat generation. | Scene is the authority on NPCs — it passes its interpretation of what NPC fields mean right now. Storytell adds arc/thread context on top. Storytell gets a slimmed-down npc_roster (name, title, maybe bio) instead of the full thing. Keeps token cost minimal. Use existing templating patterns (sections/, conditional formatting) to limit template sprawl. |
| Narrator receives `effect` only | Narrator prompt shows `effect` instead of `type` + `surface_as`. | Simplifies the narrator's creative guidance. `effect` is a concrete sentence — no need for category labels. |
| Null effect with non-null npc_id → retriable error | If `effect` is empty but `npc_id` is non-null, log a warning and retry the storyteller call with a retry hint. If the retry also fails, coerce the entire beat to null. | An NPC-driven beat without effect is incoherent. The storyteller needs to explain what the NPC is doing. The retry hint tells the LLM specifically what went wrong. |
| Driver/npc_id mismatch → no coercion | If `driver` is set but `npc_id` is missing/invalid, leave it. The storytell has already made its best judgment. Don't reject the whole beat. | Graceful degradation. The `effect` is still valid creative guidance. No need to second-guess the storytell. |
| Single temperature, single LLM call | One call, one temperature. Record keeper and beat section use the same temperature. | Defer to a future phase if needed. Two calls double token cost and latency. |
| No effect validation (other than non-empty) | No max length, no structural validation on `effect`. Trust the LLM. | Simpler code. If the LLM emits garbage, it's a prompt quality issue, not a validation issue. |
| Keep `gm_beat` field name | `gm_beat` stays on `StorytellerResult`. Not renamed to `beat`. | Less work. Avoids renaming downstream references in checkers, pipeline, state tools. |

## Open Questions

- **[OPEN: Null beat frequency in practice]** Will the LLM actually emit null with reasonable frequency, or will prompt instruction alone be insufficient? Recent-beat history is already available and will be used as guidance. May need an explicit nudge ("you have emitted a beat for 4 consecutive turns").
- **[OPEN: Scenes with no present NPCs]** Rare but possible. Environmental fallback is acceptable. Or just null beats. Unlikely to persist more than 1-2 turns.
- **[OPEN: Temperature for beat section]** The record-keeper pass is analytic; the beat pass is generative. Single temperature is the default decision, but this may need revisiting in a future phase.

## Current State — What Exists

### GMBeat Model

**File:** `ccya/models/extraction.py:181-219`

```python
class GMBeat(BaseModel):
    type: Literal["complication", "revelation", "opportunity", "breathing_room",
                  "pressure", "twist", "setback", "escalation", "callback"] | None = None
    surface_as: Literal["ambient", "event", "npc_behavior", "environmental",
                        "player_discovery", "item"] = "ambient"
    beat_expires_turn: int | None = None
```

`type` is validated via `_coerce_gm_beat_type` (nulls unrecognized strings). `surface_as` is **not validated** — accepts any string the LLM emits.

### Beat Lifecycle

Beats are stored in `state.meta.pending_gm_beat` (a dict, not a StateDelta field). This is a deliberate exception — the beat bypasses the StateDelta/validation pipeline and is written directly by `turn.py`.

```
storytell (Step 2c) → writes new beat → pending_gm_beat
  ↓
narrate (Step 1, next turn) → reads pending_gm_beat → expiry check → passes to prompt
  ↓
storytell (Step 2c, next turn) → storyteller sees pending beat → generates new beat
  ↓
turn.py → new beat replaces pending; null type pops the key
```

Expiry: `beat_expires_turn = turn_no + 2` (2-turn TTL). Auto-nulled by narrate pre-check.

### Prompt Injection

**Narrator prompt** (`narrate_system.j2:11`): Beat is priority-ordered below player input. Integrated as "environmental pressure, NPC attitude, or scene atmosphere."

**Narrator user prompt** (`narrate_user.j2:86-88`): Renders `type` and `surface_as` as creative guidance. Tells narrator not to recite metadata.

**Storyteller system prompt** (`storytell_system.j2:76-94`): Defines beat schema with `type` + `surface_as`. Constrained by `allowed_beat_types` from pacing engine. Diversity guidance: vary `type` and `surface_as`.

**Storyteller user prompt** (`storytell_user.j2:42-58`): Shows pending beat context (type, surface, expiry) and recent beat history.

### Pacing System Integration

**File:** `ccya/engine/_pacing.py`

- `BEAT_PHASE_MAP` (line 24-30): Maps scene phases to allowed beat types.
- `BEAT_BUCKETS` (line 18-22): Groups types into pressure/situation/relief buckets.
- `derive_allowed_beat_types()` (line 61-83): Returns constrained type list based on phase, directive, spiral detection.
- `compute_convergence_score()` (line 86-142): Beat streak component checks if ≥60% of recent beats are pressure-bucket types.
- `_compute_scene_phase()` (line 222-294): 5-phase state machine (SETUP→RISING→CLIMAX→RESOLUTION→BREATHER→RISING).

### NPC Fields

**File:** `ccya/models/extraction.py:24-26` (CompendiumNpcUpdate)

```python
motivation: str | None   # what NPC fundamentally wants
fear: str | None          # what NPC is most afraid of
leverage: str | None      # what NPC can offer/threaten/withhold
```

Rendered in `_npc_roster.j2:10` for present NPCs. Used in narrator system prompt (`narrate_system.j2:65-71`) as behavioral guidance. **NOT used by the storyteller.**

### Threading

Flat `ArcThread` model with `dormant`/`urgency`/`type` fields. No parent/child hierarchy.

### surface_as — Current State

Defined as a Literal with 6 values but **not validated**. Rendered in prompts but has **no mechanical effect**. The checker in `ccya/ev/checkers/pacing.py:128-159` checks consecutive same-type beats don't flip `surface_as` without directive change.

### Problems with Current State

1. **`surface_as` is dead code.** Defined, rendered in 3 prompt templates, warned about in system prompts, checked by an eval checker — but has zero mechanical effect. Every byte spent on it is wasted.

2. **Storyteller lacks NPC context.** The storyteller cannot generate NPC-driven beats because it doesn't receive motivation/fear/leverage. This is the primary gap — the discovery findings identify NPC action as the primary beat driver.

3. **Beats are type-driven, not narrative-driven.** The storyteller optimizes for type compliance (constrained by pacing engine) rather than scene logic. `effect` would fix this by making the storyteller describe what's happening rather than selecting from a category list.

4. **Two cognitive modes conflated.** The storyteller prompt asks it to be both a record-keeper (thread signals, facts, actions) and a game-master (beat generation) in a single output. This creates cognitive conflation. The two-section output structure (`record` + `gm_beat` in the prompt) is the primary mitigation.

## Proposed Solution

### Core Changes

#### 1. New GMBeat Model

```python
class GMBeat(BaseModel):
    type: Literal[
        "complication",
        "revelation",
        "opportunity",
        "breathing_room",
        "pressure",
        "twist",
        "setback",
        "escalation",
        "callback",
    ] | None = None
    effect: str = ""
    npc_id: str | None = None
    driver: Literal["motivation", "fear", "leverage"] | None = None
    beat_expires_turn: int | None = None
```

Changes from current:
- **Removed:** `surface_as`
- **Added:** `effect` (required — short concrete sentence), `npc_id` (optional), `driver` (optional)
- **Kept:** `type` (for pacing engine), `beat_expires_turn` (unchanged)

#### 2. Two-Section Storytell Output

The storyteller output is a flat JSON object. No `record` wrapper. The structural separation is purely in the prompt (instructions tell the LLM to think in two sections: record-keeper mode and game-master mode). The `gm_beat` field name is kept (not renamed to `beat`) to avoid renaming downstream references.

```python
class StorytellerResult(BaseModel):
    # record section (existing fields, unchanged)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    goal_update: str | None = None
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = Field(default_factory=list)
    arc_resolve: ArcResolution | None = None
    chapter_end: bool = False
    # beat section (new fields)
    gm_beat: GMBeat | None = None          # kept as gm_beat, not renamed to beat
```

The record keeper fields are unchanged. The structural separation is in the prompt (how the storyteller is instructed to think about the output), not in the output schema. This avoids changing the extraction pipeline.

Note: This is already the current model shape — `StorytellerResult` has flat fields with `gm_beat: GMBeat | None`. The "two sections" is purely instructional text in the system prompt telling the LLM to think in two cognitive modes.

#### 3. New Storytell Prompt

The storyteller system prompt (`storytell_system.j2`) is rewritten to include:

**System prompt additions:**

```
## Output Structure

Your output is a single JSON object with two sections:

1. `record` — thread signals, facts, actions, outcome_summary, arc updates. This is the analytical section.
2. `gm_beat` — one beat to shape the next turn, or `null`. This is the creative section.

These are separate fields in the JSON. Do not conflate them.

## GM Beat

`gm_beat`: one beat to shape the next turn, or `null`. Emit as:

```json
{
  "gm_beat": {
    "type": "complication",
    "effect": "The guard captain recognizes the PC from a previous encounter and demands to know why they're back.",
    "npc_id": "guard_captain_voss",
    "driver": "motivation"
  }
}
```

- `type`: one of the `allowed_beat_types` listed below. Constrained by the pacing engine.
- `effect`: a short, concrete sentence describing what is about to happen. Must be narratively specific — name NPCs, reference locations, tie to active threads. NOT a category label. NOT "ambient tension." If you cannot write a concrete sentence, emit `null` for the entire `gm_beat`.
- `npc_id`: the ID of the NPC driving this beat. Required when `driver` is set.
- `driver`: one of `motivation`, `fear`, `leverage`. Required when `npc_id` is set. Tells the narrator whose psychology is driving the action.

**Priority: NPC action first.** Check present NPCs (see NPC Context below). If an NPC has an obvious move given the current situation, that becomes the beat. Environmental/atmospheric beats are fallbacks only, and even then must be anchored to an active thread or NPC situation.

**Null beats are allowed.** Only emit `null` if no NPC has a motivated move and no thread has a natural next action. Given LLM tendencies to always comply, use this permission sparingly.

**Roll band** (when directive is Tension or absent):
- **crit_success / success** → prefer a beat that rewards the player or reveals info
- **partial** → prefer a beat that creates tension or adds an obstacle
- **setback / fail** → prefer a beat that gives room to recover
- **No roll** → prefer a neutral or discovery-oriented beat

**Diversity:** Don't repeat the same beat `type` more than twice consecutively. Use `recent_beats` (below) as guidance.

## NPC Context

Present NPCs are listed below. For each, you have: name, title, motivation, fear, leverage, bond. Use this to generate NPC-driven beats. This is your primary beat source.

## Beat Types

**For this turn, only the types in the `allowed_beat_types` list are valid. `gm_beat.type` MUST be one of those types.**
```

**User prompt additions:**

The user prompt (`storytell_user.j2`) adds an NPC Context section before the existing GM Beat section:

```
## NPC Context
{% for npc in npc_context %}
- **{{ npc.name }}** ({{ npc.title }}) — wants: {{ npc.motivation or "unknown" }} | fears: {{ npc.fear or "unknown" }} | leverage: {{ npc.leverage or "unknown" }} | bond: {{ npc.bond or "none" }}
{% endfor %}

## GM Beat
{% if pending_beat and pending_beat.type %}
Type: **{{ pending_beat.type | replace('_', ' ') | upper }}**
Expires: Turn {{ pending_beat.beat_expires_turn }}

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.
{% else %}
No beat currently carried over from the previous turn. Choose freely.
{% endif %}
{% if recent_beats %}
## Recent Beats
{% for b in recent_beats %}T{{ b.turn }}: {% if b.type %}{{ b.type | replace('_', ' ') | upper }}{% else %}No beat emitted this turn{% endif %}

{% endfor %}
{% endif %}
```

Note: `surface_as` is removed from the pending beat display and recent beats display. `recent_beats` is kept and used as diversity guidance.

#### 4. NPC Context Injection

The storyteller prompt receives two variables:

1. **`npc_context`** — A list of dicts built by the **scene extractor** (Step 2a), flowing through `_ExtractionContext` (the same-turn passer), received by storytell. Each entry has `npc_id`, a field type key (`fear`, `motivation`, `leverage`, or `bond`), and an effect string describing what that field means right now.

2. **`npc_roster`** — Slimmed down. Only `id`, `name`, `title`, and optionally `bio`. No bios, personalities, presence metadata, notes, position, last_seen_location, departed_reason. This is a significant reduction from the current npc_roster.

Scene decides which NPCs are relevant based on narration + NPC fields alone (no arc/thread context). It passes structured context to storytell. Storytell then picks which fields to use based on threads/arc/context that scene does not have. This division of labor is better because:

- Scene is the authority on NPCs — it passes its interpretation of what NPC fields mean right now
- Storytell adds arc/thread context on top to make the final selection
- Avoids duplicate filtering logic between scene and storytell
- Keeps token cost minimal — only relevant fields are passed

**Data flow:**
```
Scene (2a) → SceneExtractResult.npc_context (new field)
  ↓
_build_extraction_context() → copies npc_context to _ExtractionContext.npc_context
  ↓
Storytell (2c) → reads npc_context from _ExtractionContext → passes to prompt
```

The `npc_context` is built in `ccya/engine/extraction/scene.py` from the compendium. This is a new function (e.g., `build_npc_context()`) that extracts relevant NPC psychological fields. The format is:

```python
[
    {"npc_id": "guard_captain_voss", "fear": "does not want the ledger contents revealed; moves to block"},
    {"npc_id": "merchant_halden", "motivation": "wants to maintain trade relationships with the player"},
]
```

Each entry has `npc_id` and exactly one psychological field. The value is scene's interpretation of what that field means right now (the "effect"). Multiple entries are allowed. The storytell prompt renders this as a section before the beat instructions.

**npc_roster slimming:** The current `build_npc_roster()` returns dicts with id, name, title, bio, presence, motivation, fear, leverage, bond, notes, last_presence_turn, last_seen_location, departed_reason, personality_label, personality_traits, personality_speech_hint. For storytell, we only need id, name, title, and optionally bio. This is a significant reduction.

A new Jinja2 section template (`sections/_npc_context.j2`) is created for rendering the NPC Context in the storyteller user prompt. This uses existing templating patterns (conditional formatting, sections/) to limit template sprawl. The template should follow the same style as `_npc_roster.j2` for consistency.

**Model changes:**
- `SceneExtractResult` gains `npc_context: list[dict[str, Any]] = Field(default_factory=list)`
- `_ExtractionContext` gains `npc_context: list[dict[str, Any]] = field(default_factory=list)`
- `_build_extraction_context()` copies `scene_result.npc_context` to `ctx.npc_context`
- `storytell.py` passes `extraction_ctx.npc_context` to the storytell user prompt template
- `storytell.py` passes slimmed-down `npc_roster` (id, name, title, bio only) instead of full roster

#### 5. Narrator Prompt Simplification

The narrator user prompt (`narrate_user.j2`) changes from:

```
**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — surface as `{{ pending_beat.surface_as | default('ambient') }}`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

To:

```
{% if pending_beat and pending_beat.effect -%}
**GM Beat:** {{ pending_beat.effect }}
{%- endif %}
```

The narrator system prompt (`narrate_system.j2:11`) is updated to reference `effect` instead of `type` + `surface_as`. The narrator does not receive `npc_id` or `driver` — those are for evals and future tooling.

#### 6. Driver/npc_id Validation

In `turn.py` (where beats are written to `pending_gm_beat`), add validation:

```python
if _new_beat and _new_beat.npc_id and not _new_beat.effect:
    # NPC-driven beat without effect is incoherent — retry
    _log.warning("turn beat: npc_id '%s' set but effect is empty, retrying storyteller", _new_beat.npc_id)
    # Mark for retry (caller handles retry logic)
    _retry_needed = True

# Driver/npc_id mismatch: let storytell handle it. No coercion.
# If driver is set but npc_id is missing/invalid, the storytell will have already
# made its best judgment. We don't need to second-guess it.
```

The retry logic is handled by the caller (the turn pipeline). A retriable error is logged and the storyteller call is retried once. The retry includes a simple hint: "Your previous attempt set npc_id without effect. Please provide a short, concrete sentence describing what this NPC is doing." If the retry also produces empty effect with non-null npc_id, the beat is coerced to null (no beat emitted).

Driver/npc_id mismatch is NOT coerced. If the storytell emits a driver that doesn't match the npc_id's actual fields, or a driver without an npc_id, the storytell has already made its best judgment. We don't need to second-guess it. The `effect` field is still valid creative guidance.

### Alternatives Considered and Rejected

1. **Derive beat types from `effect` text.** Rejected: adds complexity, risks losing pacing behavior, out of scope. `type` stays for pacing.

2. **Two separate LLM calls (record + beat).** Rejected: doubles token cost and latency. Single call with structural separation is the primary mitigation.

3. **Full NPC context in storytell (bio, archetype, presence model).** Rejected: token cost. Only motivation/fear/leverage/bond + name/title is needed for beat generation.

4. **Migration path for schema change.** Rejected: per project AGENTS.md, no backwards compatibility. Direct swap. Old state files are not carried forward.

5. **Rename `gm_beat` to `beat`.** Rejected: adds downstream work (checkers, pipeline, state tools) for no functional benefit. `gm_beat` stays.

6. **Make `effect` nullable.** Rejected: nullable fields cause the LLM to frequently omit them, triggering retries. Making it required forces the LLM to produce an effect or null the entire beat.

## Failure Modes and Risks

1. **LLM emits empty effect with non-null npc_id.** The storyteller may generate an NPC-driven beat but fail to write an effect sentence. Mitigation: retriable error in `turn.py`. The storyteller is retried once with a hint ("Your previous attempt set npc_id without effect. Please provide a short, concrete sentence describing what this NPC is doing."). If the retry also fails, the beat is coerced to null.

2. **LLM emits category-label-style effect.** The storyteller may emit something like "pressure building" instead of a concrete sentence. Mitigation: prompt instruction. No structural validation (per decision). This is a prompt quality issue.

3. **LLM emits invalid `driver` values.** The `driver` field is a Literal with 3 values. If the LLM emits something else, Pydantic validation will coerce it to null. This is acceptable — the `effect` is still valid.

4. **NPC context token cost.** Adding `npc_context` to the storyteller prompt increases context size. Mitigation: scene passes only relevant NPCs (not all present NPCs), only 2 fields per entry (npc_id + one psychological field with effect string). Storytell gets slimmed-down npc_roster (id, name, title, bio only). If token cost is a problem, reduce to npc_id only.

5. **Narrator prompt confusion.** The narrator receives `effect` instead of `type` + `surface_as`. If the narrator was relying on `type` for creative guidance, it may need prompt adjustment. Mitigation: the system prompt already tells the narrator to use the beat as "creative guidance" — `effect` is more specific creative guidance.

6. **Two-section output parsing.** If the LLM emits malformed JSON (e.g., two separate JSON objects instead of one), the extraction pipeline will fail. Mitigation: prompt instruction + validation. The prompt shows the exact schema.

7. **LLM emits `beat` instead of `gm_beat`.** If the LLM is trained on the old schema and emits `beat` instead of `gm_beat`, the extraction will fail. Mitigation: the prompt explicitly shows `gm_beat` as the field name. This is a known LLM compliance risk.

8. **LLM schema transition.** The LLM is trained on the current schema (`type` + `surface_as`). Removing `surface_as` and adding `effect` will cause extraction failures until the LLM adapts. Mitigation: system prompt updates. No backward compatibility — the LLM will need to learn the new schema. Expect one or two turns of degraded quality during transition.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `surface_as` field | `ccya/models/extraction.py` (GMBeat) | Deleted with no replacement. |
| `surface_as` validator | `ccya/models/extraction.py` | Not present (field was never validated), but any implicit validation goes. |
| `surface_as` checker | `ccya/ev/checkers/pacing.py:128-159` | Entire checker block removed. |
| `surface_as` reference | `ccya/ev/checkers/llm_checkers.py:133` | Removed from `beat_narrative_chain` checker. |
| `surface_as` rendering | `ccya/prompts/narrate_user.j2:88` | Replaced with `effect` rendering. |
| `surface_as` rendering | `ccya/prompts/storytell_user.j2:45` | Removed from pending beat display. |
| `surface_as` rendering | `ccya/prompts/storytell_system.j2:81-82` | Removed from beat schema instructions. |
| `surface_as` diversity guidance | `ccya/prompts/storytell_system.j2:94` | "Vary `surface_as` turn to turn" removed. |
| `gm_beat` field | `ccya/models/extraction.py` (StorytellerResult) | Kept as `gm_beat`. Not renamed. |
| `surface_as` in recent_beats | `ccya/engine/turn_state.py:475` | Removed from beat history snapshot. |
| `surface_as` validation | `ccya/ev/checkers/recent_beats.py:77-81` | Updated to validate `effect` instead of `surface_as`. |
| `npc_roster` in storyteller prompt | `ccya/engine/extraction/storytell.py` | Replaced by slimmed-down npc_roster (id, name, title, bio only) + `npc_context` (built by scene extractor, flows through _ExtractionContext, structured list of npc_id + psychological field + effect string). |

## What Is Unchanged

- **Beat TTL.** 2-turn TTL stays. `beat_expires_turn = turn_no + 2` unchanged.
- **Beat lifecycle.** `pending_gm_beat` storage in `state.meta`, expiry check in narrate, write in turn.py — all unchanged.
- **Beat types.** `type` field stays on the beat model. `BEAT_PHASE_MAP`, `BEAT_BUCKETS`, `derive_allowed_beat_types()`, `compute_convergence_score()`, `_compute_scene_phase()` — all unchanged.
- **Threading system.** `ArcThread` model, thread operations, thread reference in prompts — all unchanged.
- **NPC compendium model.** `CompendiumNpcUpdate` fields (motivation/fear/leverage) — unchanged. The storyteller prompt gains access to them via `npc_context` (replacing `npc_roster`).
- **Narrator system prompt.** NPC behavioral guidance (`narrate_system.j2:65-71`) — unchanged. The system prompt line 11 is updated to reference `effect` instead of `type` + `surface_as`. Only the user prompt rendering changes.
- **Beat history.** `recent_beats` snapshot in `turn_state.py` — structure stays the same, just without `surface_as`. New structure: `{"turn": N, "type": "...", "effect": "..."}`.
- **Storyteller prompt structure.** The overall storytell prompt (system + user) stays the same. Only the beat section changes. Net prompt growth ~15 lines — acceptable.
- **Scene extractor.** Gains `build_npc_context()` function in this overhaul (new, not a separate pipeline step). Scene extracts relevant NPC psychological fields based on narration + NPC fields alone (no arc/thread context), passes structured list to storytell via extraction_ctx.
- **SceneExtractResult.** Gains `npc_context` field. This is how npc_context flows from scene to storytell.
- **Storytell npc_roster.** Slimmed down to id, name, title, bio only. This is a significant reduction from the current full roster.
- **StateDelta.** Beat is intentionally absent from StateDelta (written directly to `state["meta"]["pending_gm_beat"]`). This stays.
- **Floor relief.** Beat history is still post-floor-relief. Unchanged.

## New Model Shapes

### GMBeat (updated)

```python
class GMBeat(BaseModel):
    type: Literal[
        "complication",
        "revelation",
        "opportunity",
        "breathing_room",
        "pressure",
        "twist",
        "setback",
        "escalation",
        "callback",
    ] | None = None
    effect: str = ""
    npc_id: str | None = None
    driver: Literal["motivation", "fear", "leverage"] | None = None
    beat_expires_turn: int | None = None
```

### StorytellerResult (updated)

```python
class StorytellerResult(BaseModel):
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    goal_update: str | None = None
    gm_beat: GMBeat | None = None          # kept as gm_beat, not renamed to beat
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = Field(default_factory=list)
    arc_resolve: ArcResolution | None = None
    chapter_end: bool = False
```

### SceneExtractResult (updated)

```python
class SceneExtractResult(BaseModel):
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    npc_context: list[dict[str, Any]] = Field(
        default_factory=list
    )
    # npc_context format: [{"npc_id": "guard_captain_voss", "fear": "does not want the ledger contents revealed; moves to block"}, ...]
```

### _ExtractionContext (updated)

```python
@dataclass
class _ExtractionContext:
    comp_this_turn: dict[str, Any] = field(default_factory=dict)
    location_this_turn: dict[str, Any] = field(default_factory=dict)
    inventory_this_turn: list[dict[str, Any]] = field(default_factory=list)
    conditions_this_turn: list[dict[str, Any]] = field(default_factory=list)
    npc_context: list[dict[str, Any]] = field(default_factory=list)
    # npc_context flows from scene → extraction_ctx → storytell
```

## Context for Implementing LLMs

- **`ccya/models/extraction.py:181-219`** — GMBeat model definition. This is where `surface_as` is removed and `effect`/`npc_id`/`driver` are added.
- **`ccya/models/extraction.py:222-231`** — StorytellerResult model. `gm_beat` kept as-is (not renamed).
- **`ccya/models/extraction.py`** — SceneExtractResult. Add `npc_context: list[dict[str, Any]]` field.
- **`ccya/engine/extraction/context.py`** — _ExtractionContext. Add `npc_context` field. Update `_build_extraction_context()` to copy `scene_result.npc_context` to `ctx.npc_context`.
- **`ccya/engine/turn.py:256-265`** — Beat lifecycle: write/pop `pending_gm_beat`. Add driver/npc_id validation and null-effect-with-npc_id retry logic here.
- **`ccya/engine/turn.py:473-476`** — History event `gm_beat` dict. Replace `surface_as` with `effect`.
- **`ccya/engine/narrate.py:163-174`** — Pre-narration expiry check. Unchanged.
- **`ccya/engine/narrate.py:271`** — Pass beat to `_narrate_messages()`. Unchanged.
- **`ccya/engine/extraction/scene.py`** — New function `build_npc_context()` that extracts relevant NPC psychological fields from compendium. Scene decides relevance based on narration + NPC fields alone (no arc/thread context). Returns structured list: `[{"npc_id": "x", "fear": "string"}, ...]`.
- **`ccya/engine/extraction/storytell.py:87`** — Pass pending beat to storytell prompt. Receive pre-built `npc_context` variable from `extraction_ctx.npc_context`. Pass slimmed-down `npc_roster` (id, name, title, bio only) instead of full roster. Replace `npc_roster` with `npc_context` for beat generation.
- **`ccya/engine/extraction/pipeline.py:302-304`** — Comment about gm_beat being absent from StateDelta. No change needed (field name stays `gm_beat`).
- **`ccya/engine/turn_state.py:470-480`** — Beat history snapshot. Remove `surface_as` from snapshot. Add `effect` to snapshot.
- **`ccya/prompts/narrate_system.j2:11`** — Beat priority ordering. Update to reference `effect` instead of `type` + `surface_as`.
- **`ccya/prompts/narrate_user.j2:86-88`** — Beat rendering. Replace `type`+`surface_as` with `effect`.
- **`ccya/prompts/storytell_system.j2:76-94`** — Beat schema. Rewrite for two-section output with `effect`-first guidance. Remove `surface_as` references.
- **`ccya/prompts/storytell_user.j2:42-58`** — Pending beat context. Remove `surface_as` from display. Add NPC Context section.
- **`ccya/prompts/sections/_npc_context.j2`** — New template. Renders NPC Context for storytell (npc_id + psychological field).
- **`ccya/prompts/sections/_npc_roster.j2:10`** — NPC rendering. Unchanged (already renders motivation/fear/leverage for narrator).
- **`ccya/ev/checkers/pacing.py:128-159`** — surface_as checker. Remove entirely.
- **`ccya/ev/checkers/gm_beat.py`** — Beat lifecycle checker. Update to handle `effect` field. Field name stays `gm_beat`.
- **`ccya/ev/checkers/llm_checkers.py:133`** — `beat_narrative_chain` checker. Remove `surface_as` reference.
- **`ccya/ev/checkers/recent_beats.py:77-81`** — recent_beats checker. Update to validate `effect` instead of `surface_as`.

## Future Work

### NPC Rolls

Currently, when an NPC drives a beat (`npc_id` + `driver` set), the beat assumes the NPC's action succeeds. This is narratively shallow — NPCs should have success/failure on their actions, mirroring player dice.

Proposed flow:
```
scene extracts NPC motivation → passes to storytell → storytell rolls (or uses roll band) → beat reflects success/failure of NPC action
```

This would add a `roll_result` field to the beat (or derive it from the existing roll band) and make the `effect` sentence reflect the outcome. For example:

- **Success:** "The guard captain recognizes you from the last town and demands to know why you're back."
- **Failure:** "The guard captain reaches for his weapon but drops his keys — a moment of vulnerability you can exploit."

This adds a layer of uncertainty to NPC actions that makes beats feel more dynamic. NPCs aren't just "doing things," they're trying to achieve goals and may fail. This is a significant enhancement but adds complexity to the storytell prompt and extraction model. Defer to a future phase.
