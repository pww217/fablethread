# Plan: Arc/Thread Overhaul — Phase 1: Models

## Purpose

Update Pydantic model shapes in `ccya/models.py` to support always-append progress logs, remove dead `thematic_question` field, and add the `goal_update` output field for the storyteller.

## Problem Statement

`ArcThread.progress` is a single string that gets overwritten on every update, losing the investigative trail. `CampaignArc.thematic_question` has produced zero behavioral value across 77 combined turns — it consumes prompt context and model state with no observable output. The storyteller has no structured way to signal that the arc's visible goal has shifted without resolving the entire arc.

## Constraints

- Backwards compatibility is not required (design constraint #16).
- Existing saves must not crash on load — a Pydantic migration validator handles old `progress` format.
- The `_merge_arc_update` function applies `model_copy(update=...)` which will reject extra fields silently (Pydantic ignores unknown keys). Removing a field is safe.

## Non-goals

- No engine logic changes (Phase 2).
- No prompt template changes (Phase 3).
- No changes to `GMBeat`, `ThreadResolution`, `WorldStateFact`, or any model not listed below.

## Solution

Remove `thematic_question` from `CampaignArc` and `ArcResolution`. Change `ArcThread.progress` from `str` to `list[str]` with a migration validator, and add `last_updated_turn` field. Add `goal_update: str | None = None` to `StorytellerResult`.

## Firm decisions

1. `thematic_question` field is removed from both `CampaignArc` and `ArcResolution`. No behavioral value evidenced across 77 turns.
2. `goal_update` is a bare `str | None`, not a model class. Applied via direct dict assignment in the engine (Phase 2).
3. `ArcThread.progress` becomes `list[str] = []`. Every update appends; no boolean, no kind enum.
4. `ArcThread.last_updated_turn` is `int | None = None`, set by the engine on every mutation.
5. Migration for old saves: a `field_validator("progress", mode="wrap")` coerces old `"some string"` values to `["some string"]`.
6. `ArcResolution.thematic_question` is removed. The successor arc gets its thematic context from `visible_goal` and `goal_context` only.

## Risks, Ambiguities, and Blockers

- Old save files with `thematic_question` in the JSON will silently ignore the unknown key on load (Pydantic `model_validate`). No migration needed.
- Old save files with `progress` as a string will fail validation without the migration validator. The validator is required.

## Status

`completed`

## Phases

Single phase. This changes only `ccya/models.py`.

## Implementation — Phase 1: Models

### Context files to load

- `ccya/models.py` lines 29-48 (`ArcThread`, `CampaignArc`)
- `ccya/models.py` lines 352-366 (`ThreadUpdate`, `ArcResolution`)
- `ccya/models.py` lines 410-432 (`StorytellerResult`)
- `docs/design/arc-thread-system-design.md` section "New Model Shapes"

### Detailed steps

#### Step 1.1 — Remove `thematic_question` from `CampaignArc`

**File:** `ccya/models.py` lines 41-48

**What:** Delete line `thematic_question: str = ""` from the `CampaignArc` class body.

**Why:** Dead field across 77 turns. The successor arc's thematic framing is derived from `visible_goal` and `goal_context` alone.

**Validation:** `make check` passes. No reference to `CampaignArc.thematic_question` remains in any file that would break.

#### Step 1.2 — Change `ArcThread.progress` type and add new fields

**File:** `ccya/models.py` lines 29-38

**What:** Change `progress: str = ""` to `progress: list[str] = Field(default_factory=list)`. Add `last_updated_turn: int | None = None` as a new field. No `Field(...)` import needed — it's already imported.

New shape:
```
class ArcThread(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    active: bool = True
    urgency: Literal["background", "normal", "urgent"] = "normal"
    progress: list[str] = Field(default_factory=list)
    last_updated_turn: int | None = None
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
```

**Why:** Always-append progress list preserves the investigative trail. `last_updated_turn` enables urgency decay tracking without relying on external turn data.

**Validation:** `make check` passes.

#### Step 1.3 — Add progress migration validator to `ArcThread`

**File:** `ccya/models.py`, immediately after the `ArcThread` class body

**What:** Add a `field_validator("progress", mode="wrap")` that wraps old string values in a list:

```python
@field_validator("progress", mode="wrap")
@classmethod
def _coerce_progress(cls, v: Any, handler: Any) -> Any:
    if isinstance(v, str):
        return [v]
    return handler(v)
```

**Why:** Existing saves have `progress: "some string"` (a single str). Without this validator, `model_validate` will reject the type mismatch.

**Validation:** With `models.py` loaded, `ArcThread(progress="hello")` returns a `progress` list `["hello"]`, not a string.

#### Step 1.4 — Remove `thematic_question` from `ArcResolution`

**File:** `ccya/models.py` lines 360-366

**What:** Delete the line `thematic_question: str | None = None` from the `ArcResolution` class body.

**Why:** Field is dead. Successor arc's framing comes from `visible_goal` and `goal_context`.

**Validation:** `make check` passes.

#### Step 1.5 — Add `goal_update` field to `StorytellerResult`

**File:** `ccya/models.py` lines 410-432

**What:** Add `goal_update: str | None = None` as a new field on `StorytellerResult`. Placement: after `outcome_summary`, before `gm_beat`.

**Why:** The storyteller needs a way to update `visible_goal` mid-arc without triggering `arc_resolve`. A bare string field is minimal and sufficient. The engine applies it via direct dict assignment (Phase 2).

**Validation:** `make check` passes. A `StorytellerResult(goal_update="new goal")` round-trips correctly.

### Tests to write or update

No test files exist in the current repo. Run `make check` for validation.
