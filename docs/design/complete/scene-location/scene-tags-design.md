# Scene Tags Design

## Purpose

Design document for re-adding `scene_tags` to the scene extraction pipeline. Covers the data model, extraction prompt, state mutation, and downstream consumers. Intended for implementers and reviewers.

Reference: "This document is the design authority for plans implementing scene tags."

## Problem Statement

`scene_tags` was removed from `SceneExtractResult` in a prior refactor. The field was replaced by inference from narration + scene_phase + threads. However, two downstream consumers still reference `state["scene"]["tags"]`:

1. **Combat acceleration** (`turn.py:705-709`): `effective_scene_age += 2` when `"combat"` is in tags. Currently dead code — `state.scene.tags` is initialized to `[]` in `state/io.py:101` and never populated, so the combat boost never fires.
2. **Convergence score** (`_pacing.py:compute_convergence_score`): Currently uses 5 components (urgent thread, threat, scene age, beat streak, dice weight). No tag-based component exists.

The user wants combat acceleration revived and convergence score potentially extended with tag-based signals. Everything else (beat filtering, GM beat surface_as, ruling difficulty) can be inferred from narration + context and does not need tags.

## Constraints

- Tags must be extracted by the LLM from narration via `extract_scene` — no manual tagging in the UI or API.
- Tags must be a flat list of strings — no hierarchy, no nesting.
- The extraction prompt must constrain tag vocabulary to prevent drift (bounded tag set).
- No new API endpoints or UI fields — tags flow through the existing extraction pipeline only.
- Backward compat: `state.scene.tags` already exists as `[]` in the state schema. New code must not break existing state files.

## Non-goals

- Tag-based beat filtering (e.g., `"dungeon"` → no `breathing_room`). The phase map already constrains beats; the LLM can infer scene type from narration.
- Tag-based ruling difficulty modifiers. The `_VERB_CATEGORY` in `rules.py` already maps verbs to combat/social/exploration/movement.
- Tag-based GM beat surface_as constraints. The LLM can infer from narration.
- Tag-based location rules (e.g., `"dungeon"` → narration must include hazards). The location description already provides this context.
- UI display of tags in the sidebar. The TV already shows `scene_phase` and `scene_tagline`.
- Tag migration — no migration of existing saves. New tag data only flows from new extractions.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Tag vocabulary | Bounded set: `combat`, `social`, `exploration`, `dungeon`, `travel`, `social_gathering`, `investigation`, `combat_ambient` | Prevents LLM drift. The bounded set maps to existing `_VERB_CATEGORY` categories and common scene types. |
| Tag extraction | LLM extracts tags from narration in `extract_scene` step via `SceneExtractResult.scene_tags` | Single source of truth. No manual tagging, no separate extraction step. |
| Tag storage | `state.scene.tags: list[str]` initialized to `[]` in `state/io.py` | Already exists in state schema. No migration needed. |
| Combat acceleration | `effective_scene_age += 2` when `"combat"` in tags (turn.py:705-709) | Revives dead code path. Combat scenes escalate pressure faster. |
| Convergence score | New component 6: `"combat"` tag + any urgent thread → +1 | Combat with urgent threads should converge to CLIMAX faster. |
| Tag display in dev tools | `ev/state_tools.py:_render_scene_section` already renders tags if present | No code change needed — already reads `scene.get("tags")`. |
| Tag display in play output | `ev/play.py` already reads `state.scene.tags` in scene dict | No code change needed — already present in play output. |
| Tag display in diff output | `ev/output.py` already has `"scene.tags"` → `"Scene Tags"` label | No code change needed — already present in diff output. |

## Open Questions

- `[OPEN: Should tag vocabulary include "combat_ambient" (combat-related but not active combat) or just "combat"?]`
- `[OPEN: Should the convergence score tag component require BOTH combat tag AND urgent thread, or just combat tag alone?]`
- `[OPEN: Should tag extraction be constrained to at most 3 tags per turn to prevent tag bloat?]`

## Current State — What Exists

### Scene Extraction Pipeline

```mermaid
graph LR
    A[Turn narration] --> B[extract_scene LLM]
    B --> C[SceneExtractResult]
    C --> D[delta_builder.apply]
    D --> E[state.scene]
    E --> F[turn.py: _compute_ages]
    F --> G[effective_scene_age]
    G --> H[_compute_narration_directive]
    H --> I[Scene Pressure / Scene Imperative]
```

### SceneExtractResult (models.py:316)

```python
class SceneExtractResult(BaseModel):
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(default_factory=list, max_length=12)
```

No `scene_tags` field. The field was removed in a prior refactor.

### State Schema (state/io.py:100)

```python
"scene": {
    "tags": [],
    "world_state": [],
    "tagline": "",
    "turn_entered": 0,
}
```

`tags` is initialized to `[]` but never written to. Always empty.

### Combat Acceleration (turn.py:705-709)

```python
_scene_age = ctx._ages.get("scene_age", 0)
_tags: list[str] = (state.get("scene") or {}).get("tags") or []
if "combat" in _tags:
    _scene_age += 2
ctx._ages["effective_scene_age"] = _scene_age
```

Dead code — `state.scene.tags` is always `[]`.

### Convergence Score (_pacing.py:85-139)

5 components, each +1:
1. Any urgent thread
2. Active threat
3. Scene age ≥ scene_pressure_threshold
4. Beat streak (pressure beats in recent window)
5. Dice weight (urgent + fail/crit_fail)

No tag-based component.

### Dev Tooling

- `ev/state_tools.py:_render_scene_section` — already renders tags if present
- `ev/play.py` — already includes `state.scene.tags` in output
- `ev/output.py` — already has `"scene.tags"` → `"Scene Tags"` label
- `ev/state_tools.py:cmd_effective_age` — shows effective_scene_age over time

### Problems with Current State

1. **Combat acceleration is dead code.** The check at `turn.py:705-709` can never fire because `state.scene.tags` is never populated. The combat tag boost (+2 to effective_scene_age) is unreachable.
2. **No tag extraction.** The LLM has no opportunity to tag scenes during extraction. The bounded tag vocabulary was removed with `scene_tags` from `SceneExtractResult`.
3. **Convergence score lacks combat signal.** Combat scenes with urgent threads should converge to CLIMAX faster, but the 5-component score has no tag-based component.
4. **State schema has orphan field.** `state.scene.tags` exists in the schema but is never written. It's a zombie field — initialized to `[]`, read in multiple places, never populated.

## Proposed Solution

### Core Changes

**1. Add `scene_tags` to `SceneExtractResult`**

```python
class SceneExtractResult(BaseModel):
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(default_factory=list, max_length=12)
    scene_tags: list[str] = Field(default_factory=list, max_length=3)
```

Bounded tag vocabulary enforced in the extraction prompt (not in Pydantic — Pydantic accepts any strings, the prompt constrains the LLM).

**2. Update extract_scene_system.j2 prompt**

Add tag extraction instructions to the Scene Extractor system prompt. Constrain to bounded set: `combat`, `social`, `exploration`, `dungeon`, `travel`, `social_gathering`, `investigation`, `combat_ambient`. At most 3 tags per turn.

**3. Combat acceleration revival (turn.py:705-709)**

No code change needed — the check already exists. Only the extraction prompt needs to populate tags.

**4. Convergence score tag component (_pacing.py:compute_convergence_score)**

Add component 6: `"combat"` tag + any urgent thread → +1 to convergence score. This makes combat scenes with urgent threads converge to CLIMAX faster.

### Alternatives Considered and Rejected

**Alternative 1: Derive combat from narration via LLM in ruling step**
- Why rejected: Adds an extra LLM call per turn. The extract_scene step already processes narration — tag extraction there is free (no additional LLM call).

**Alternative 2: Derive combat from scene_phase == "CLIMAX"**
- Why rejected: CLIMAX is a convergence event, not a combat indicator. Social scenes can also reach CLIMAX. The tag is more precise.

**Alternative 3: No tag vocabulary — let LLM invent tags**
- Why rejected: Tag drift. Without a bounded set, the LLM will invent synonyms (`"combat"`, `"fighting"`, `"battle"`, `"combat-scene"`) that break the `"combat" in tags` check. A bounded set prevents this.

**Alternative 4: Tag-based beat filtering in derive_allowed_beat_types**
- Why rejected: The phase map already constrains beats per phase. The LLM can infer scene type from narration + location + threads. Adding tag-based filtering would be complex plumbing for marginal gain.

## Failure Modes and Risks

1. **LLM tag drift.** The LLM might invent tags outside the bounded set. Mitigation: the bounded set in the prompt is small (8 tags), and the prompt explicitly says "choose from this list." Pydantic does not enforce the set — the prompt is the only guard.
2. **Tag bloat.** The LLM might tag every scene with `"exploration"` or `"social"`. Mitigation: max 3 tags per turn in the prompt. The convergence score tag component requires `"combat"` specifically, so non-combat tags don't affect convergence.
3. **Backward compat with existing saves.** `state.scene.tags` is already `[]` in the schema. New code reads it as `[]` for old saves — no breakage. New extractions populate it.
4. **Convergence score changes alter pacing.** Adding a tag-based component to convergence score will make combat scenes converge to CLIMAX faster. This is the intended behavior, but it changes the pacing curve. Packs that tuned convergence_threshold=3 may need adjustment.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| (none) | — | No removals. Only additions. |

## What Is Unchanged

- `SceneExtractResult` fields except the addition of `scene_tags`
- `extract_scene_user.j2` — no changes needed
- `state/io.py` — `scene.tags` already initialized to `[]`
- `delta_builder.py` — no changes needed (tags flow through existing state mutation)
- `_compute_narration_directive` — no changes needed (uses effective_scene_age which is already computed)
- `_compute_pacing_context` — no changes needed (uses directive from _compute_narration_directive)
- `derive_allowed_beat_types` — no changes needed (phase + directive + spiral only)
- `BEAT_PHASE_MAP` — no changes needed
- `BEAT_BUCKETS` — no changes needed
- `rules.py` — no changes needed (_VERB_CATEGORY already maps verbs to categories)
- `storytell_user.j2` — no changes needed (pacing_context already rendered)
- `narrate_user.j2` — no changes needed
- `ev/state_tools.py` — already renders tags if present
- `ev/play.py` — already includes tags in output
- `ev/output.py` — already has `"scene.tags"` label
- `config.py` — no new config fields needed (combat acceleration is hardcoded +2)
- `routes.py` — no changes needed (tags not exposed via API settings endpoint)

## New Model Shapes

### SceneExtractResult (updated)

```python
class SceneExtractResult(BaseModel):
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(default_factory=list, max_length=12)
    scene_tags: list[str] = Field(default_factory=list, max_length=3)
```

### Bounded Tag Vocabulary (prompt-enforced, not Pydantic-enforced)

```
combat
social
exploration
dungeon
travel
social_gathering
investigation
combat_ambient
```

## Context for Implementing LLMs

- `ccya/models.py:316` — SceneExtractResult model. Add `scene_tags` field.
- `ccya/prompts/extract_scene_system.j2` — Scene Extractor system prompt. Add tag extraction instructions with bounded vocabulary.
- `ccya/state/io.py:100` — State initialization. `scene.tags` already initialized to `[]`.
- `ccya/engine/turn.py:705-709` — Combat acceleration. Dead code path — no changes needed, just verify it works when tags are populated.
- `ccya/engine/_pacing.py:85-139` — Convergence score. Add tag-based component 6.
- `ccya/ev/state_tools.py:1083` — `_render_scene_section`. Already renders tags.
- `ccya/ev/play.py:117` — Play output. Already includes tags.
- `ccya/ev/output.py:202` — Diff output. Already has `"scene.tags"` label.
