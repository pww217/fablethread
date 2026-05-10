# GM Beat Ownership Migration: Scene → Progress

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective

`gm_beat` is currently issued by the scene extractor (`SceneExtractResult`), which has
spatial and social context but no knowledge of story arc momentum, quest staleness, or
outcome trajectory. `ProgressExtractResult` has `outcome_summary`, quest updates, and
recent-event history — all of which are more meaningful signals for deciding *whether*
a beat is needed and *what kind* serves the story. This plan moves `gm_beat` ownership
to progress, extends `GMBeat.type` and `GMBeat.surface_as` with missing narrative
categories, converts the `deescalate` flag from `bool` to `float` so magnitude is
preserved through the pipeline, and adds beat expiry so stale pending beats do not
persist across turns where they were never consumed.

## Non-goals

- Does not change how `pending_gm_beat` is consumed by the narrator (`narrate_user.j2`
  or `narrate_system.j2`) — only the producer changes.
- Does not change the directive-shaping logic in `rules.py` (`build_directive`).
- Does not add new Jinja2 template variables beyond renaming the producer and adding
  `deescalate`/`quest_ages` to the progress extraction template.
- Does not touch compaction, chronicle, or any persistence path other than
  `meta.pending_gm_beat`.
- Does not change `StateDelta` — `gm_beat` was always absent from it and remains so.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add types to `GMBeat.type`; add values to `GMBeat.surface_as`; add `beat_expires_turn` field; move `gm_beat` field from `SceneExtractResult` to `ProgressExtractResult`; remove `_nullify_invalid_gm_beat` validator from `SceneExtractResult`; add equivalent validator to `ProgressExtractResult`; widen `deescalate` from `bool` to `float` in no model (it is not a model field — it is a pipeline parameter) |
| `ccya/engine/extraction.py` | modify | Widen `deescalate: bool` to `deescalate: float` in `_run_extraction_pipeline` and `_extract_scene_messages`; add `deescalate: float` and `quest_ages` to `_extract_progress_messages` signature and forward them; consume `gm_beat` from `progress_result` instead of `scene_result` in `_run_extraction_pipeline`; add beat expiry logic |
| `ccya/engine/turn.py` | modify | Widen `deescalate: bool` to `deescalate: float`; compute float magnitude from momentum delta; update `pending_gm_beat` storage block to read from `progress_result` (already done via extraction pipeline — no direct change needed here beyond the `deescalate` type); add `beat_expires_turn` when storing `pending_gm_beat` |
| `ccya/engine/narrate.py` | modify | Widen `deescalate: bool` to `deescalate: float` in `_narrate_messages` signature |
| `ccya/prompts/scene_extract_user.j2` | modify | Remove `gm_beat` instruction block (if present) |
| `ccya/prompts/progress_extract_user.j2` | modify | Add `gm_beat` instruction block with `deescalate` and `quest_ages` context; add `deescalate` and `quest_ages` to `user_ctx` dict |
| `ccya/prompts/rules_user.j2` | modify | Replace truncated `t.narrative[-120:]` with full `t.narrative` for proper intent context |
| `docs/REPOMAP/models.md` | update | Reflect moved `gm_beat` field and new types |
| `docs/REPOMAP/extraction.md` | update | Reflect changed signatures and new beat source |
| `docs/plans/TODO.md` | update | Add entry for this plan |

***

## Firm decisions

1. **Progress owns `gm_beat`.** `ProgressExtractResult` receives `outcome_summary`,
   quest updates, and recent-event changes in the same extraction call. These are
   stronger signals than scene spatial state for determining narrative pacing.
2. **`deescalate` becomes `float` (0.0–1.0).** The existing bool is computed from
   momentum band and pressure urgency in `turn.py`. The float version uses the same
   conditions but maps to magnitude: `crit_success` → 1.0, `success` → 0.6,
   non-rolled or no pressure → 0.0. This flows unchanged into the Jinja2 templates
   as a numeric value (templates already receive it as a context variable).
3. **`_narrate_messages` `deescalate` parameter is widened, not renamed.** It is
   `deescalate: bool = False` today. The call sites in `run_turn` and
   `run_turn_retry` pass the value directly. Widening to `float` is a compatible
   change — existing `False` → `0.0`, `True` → `1.0` in Python numeric context.
   The Jinja2 template receives it as a context dict value and uses it in a
   conditional; `if deescalate` still evaluates correctly for both bool and float.
4. **`beat_expires_turn` added to `GMBeat`.** When the beat is stored in
   `meta.pending_gm_beat`, `beat_expires_turn = current_turn + 2` is written
   alongside it. The narration phase in `run_turn` already clears `pending_gm_beat`
   after consuming it (`state["meta"]["pending_gm_beat"] = None`). The expiry field
   is a safety net: if narration is skipped or the beat was never fired, the
   extraction phase reads `beat_expires_turn` and nullifies stale beats before
   writing a new one.
5. **`_nullify_invalid_gm_beat` validator moves from `SceneExtractResult` to
   `ProgressExtractResult` unchanged.** The validation logic is identical; only the
   class it decorates changes.
6. **New `GMBeat.type` values: `twist`, `setback`, `escalation`, `callback`.**
   Added to the `Literal` union. Existing values (`complication`, `revelation`,
   `opportunity`, `breathing_room`, `pressure`) are preserved.
7. **New `GMBeat.surface_as` values: `environmental`, `player_discovery`, `item`.**
   Added to the `Literal` union. Existing values (`ambient`, `event`,
   `npc_behavior`) are preserved.
8. **`run_turn_retry` passes `deescalate=0.0` and `quest_ages=[]`.** The existing
   code already passes `deescalate=False` and `quest_ages=[]` for retries, with a
   comment explaining the intent. The float zero is semantically identical.

9. **Rules step receives full previous turn narration.** Currently `rules_user.j2:11`
   truncates to `t.narrative[-120:]`. This must be changed to emit the full
   `t.narrative` so the rules engine can properly gauge intent, track ongoing
   threads, and distinguish continuation from new action. The call site in
   `turn.py:303` already passes `recent_turns[-1:]` — only the template needs
   updating. This is a minimal change: replace the truncated slice with the full
   narrative text in the Jinja2 template.

***

## Implementation — Phase 1: Models

### Context files to load
- `ccya/models.py`

### Overview

Extend `GMBeat` with new `type` and `surface_as` literals and a `beat_expires_turn`
field. Move the `gm_beat` field (and its validator) from `SceneExtractResult` to
`ProgressExtractResult`. No other model changes.

### Detailed steps

#### Step 1.1 — Extend GMBeat literals and add expiry field

**File:** `ccya/models.py`

**What:** Replace the `GMBeat` class definition with the extended version below.

**Why:** New `type` values cover narrative patterns the current five-value set cannot
express. New `surface_as` values cover delivery mechanisms beyond NPC/event/ambient.
`beat_expires_turn` enables safe expiry without requiring a separate cleanup pass.

**Code Snippet**
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
    surface_as: Literal[
        "ambient",
        "event",
        "npc_behavior",
        "environmental",
        "player_discovery",
        "item",
    ] = "ambient"
    instruction: str | None = None
    beat_expires_turn: int | None = None

    @field_validator("instruction", mode="after")
    @classmethod
    def _validate_instruction_quality(cls, v: str | None) -> str | None:
        if not v:
            return None
        stripped = v.strip()
        if len(stripped) < 40:
            return None
        lower = stripped.lower()
        if any(lower.startswith(prefix) for prefix in _GM_BEAT_FILLER_PREFIXES):
            return None
        return stripped
```

**Validation:** `python -c "from ccya.models import GMBeat; b = GMBeat(type='twist', surface_as='environmental', instruction='A long enough instruction string that passes the quality gate without issues'); print(b)"` — should print without error.

***

#### Step 1.2 — Remove gm_beat from SceneExtractResult

**File:** `ccya/models.py`

**What:** Remove the `gm_beat: GMBeat | None = None` field and
`_nullify_invalid_gm_beat` model validator from `SceneExtractResult`.

**Why:** Scene extractor no longer owns beat production.

**Code Snippet**
```python
class SceneExtractResult(BaseModel):
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    npc_add: list[NpcAdd] = Field(default_factory=list)
    npc_remove: list[NpcRemove] = Field(default_factory=list)
    npc_update: list[NpcUpdate] = Field(default_factory=list)
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    scene_pressure_add: list[ScenePressure] = Field(default_factory=list)
    scene_pressure_remove: list[str] = Field(default_factory=list)
    scene_pressure_update: list[ScenePressure] = Field(default_factory=list)

    @field_validator("npc_remove", mode="before")
    @classmethod
    def _coerce_npc_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x})
            else:
                out.append(x)
        return out

    @field_validator("location_description", mode="before")
    @classmethod
    def _coerce_location_description(cls, v: Any) -> Any:
        if not v:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v)
```

**Validation:** `python -c "from ccya.models import SceneExtractResult; r = SceneExtractResult(); print(r)"` — should succeed; no `gm_beat` attribute.

***

#### Step 1.3 — Add gm_beat to ProgressExtractResult

**File:** `ccya/models.py`

**What:** Add `gm_beat: GMBeat | None = None` field and the moved
`_nullify_invalid_gm_beat` validator to `ProgressExtractResult`.

**Why:** Progress is the new beat producer. The validator logic is identical.

**Code Snippet**
```python
class ProgressExtractResult(BaseModel):
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    gm_beat: GMBeat | None = None

    @model_validator(mode="after")
    def _nullify_invalid_gm_beat(self) -> "ProgressExtractResult":
        if self.gm_beat is not None:
            if not self.gm_beat.instruction or not self.gm_beat.type:
                self.gm_beat = None
        return self

    @field_validator("actions", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[str] = []
        for x in v:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                out.append(x.get("action") or x.get("description") or str(x))
            else:
                out.append(str(x))
        return out
```

Note: `model_validator` is already imported at the top of `models.py`.

**Validation:** `python -c "from ccya.models import ProgressExtractResult, GMBeat; r = ProgressExtractResult(gm_beat=GMBeat(type='twist', instruction='x')); print(r.gm_beat)"` — should print `None` (instruction too short, validator nullifies).

***

### Tests to write or update

**File:** `tests/test_models.py` (create or extend)

- `test_gm_beat_new_types` — assert `GMBeat(type="twist", ...)`, `GMBeat(type="setback", ...)`, `GMBeat(type="escalation", ...)`, `GMBeat(type="callback", ...)` all validate without error.
- `test_gm_beat_new_surface_as` — assert `GMBeat(surface_as="environmental", ...)` etc. validate.
- `test_gm_beat_expires_turn` — assert `beat_expires_turn` round-trips through `model_dump`.
- `test_scene_extract_result_no_gm_beat` — assert `SceneExtractResult` has no `gm_beat` attribute.
- `test_progress_extract_result_gm_beat_nullified` — assert short `instruction` is nullified.
- `test_progress_extract_result_gm_beat_valid` — assert a well-formed beat survives validation.

### REPOMAP updates required

`docs/REPOMAP/models.md`: update `SceneExtractResult` entry (remove `gm_beat`), update `ProgressExtractResult` entry (add `gm_beat`, `beat_expires_turn`), update `GMBeat` entry (new types and `surface_as` values).

### Risks

1. Any code that reads `scene_result.gm_beat` directly (outside of `extraction.py`)
   will raise `AttributeError` after this phase. Verify with
   `grep -r "scene_result\.gm_beat" .` — only `extraction.py` should appear.
2. `extraction_event["scene"]["output"]` is written from `scene_result.model_dump()`.
   If any log parser or test asserts the presence of `gm_beat` in the scene output
   key, it will break. Check with `grep -r "extraction.*scene.*gm_beat" tests/`.

***

## Implementation — Phase 2: Extraction pipeline

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/engine/turn.py` (for call-site signatures only — do not modify in this phase)
- `ccya/models.py` (Phase 1 must be complete)

### Overview

Widen `deescalate` from `bool` to `float` throughout the extraction pipeline. Add
`deescalate` and `quest_ages` to `_extract_progress_messages`. Update
`_run_extraction_pipeline` to read `gm_beat` from `progress_result` and write
`beat_expires_turn` when storing the beat.

### Detailed steps

#### Step 2.1 — Widen deescalate in _extract_scene_messages

**File:** `ccya/engine/extraction.py`

**What:** Change `deescalate: bool = False` to `deescalate: float = 0.0` in
`_extract_scene_messages` signature and pass it unchanged into the Jinja2 context.

**Why:** Float deescalate flows through the same context dict key; templates that
use `{% if deescalate %}` evaluate `0.0` as falsy, preserving existing behavior.

**Code Snippet**
```python
def _extract_scene_messages(
    env: Any,
    state: dict[str, Any],
    narrative: str,
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] = [],
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
) -> list[dict[str, str]]:
```

Only the type annotation on `deescalate` changes; the body is unchanged.

**Validation:** `make check` passes (mypy/ruff).

***

#### Step 2.2 — Add deescalate and quest_ages to _extract_progress_messages

**File:** `ccya/engine/extraction.py`

**What:** Add `deescalate: float = 0.0` and `quest_ages: list[dict[str, Any]] = []`
parameters to `_extract_progress_messages`. Forward both into the Jinja2 user context.

**Why:** These are the key signals that let the progress extractor decide whether a
beat is warranted, what urgency it carries, and whether to suppress one
(`deescalate > 0.5` → prefer `breathing_room` or no beat).

**Code Snippet**
```python
def _extract_progress_messages(
    env: Any,
    state: dict[str, Any],
    narrative: str,
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] = [],
    known_npcs: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        # ... existing keys unchanged ...
        "deescalate": deescalate,
        "quest_ages": quest_ages,
    }
```

Add `"deescalate": deescalate` and `"quest_ages": quest_ages` to the `user_ctx` dict
that is already being built. Do not remove any existing keys.

**Validation:** Confirm the function's `user_ctx` dict now contains both keys before
the `_render` call.

***

#### Step 2.3 — Forward deescalate and quest_ages at call site in _run_extraction_pipeline

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, the call to `_extract_progress_messages`
currently does not pass `deescalate` or `quest_ages`. Both are available as parameters
on `_run_extraction_pipeline` (added in a prior phase or already present). Add them.

**Why:** Without forwarding, the new parameters default to `0.0` / `[]` on every call,
making Step 2.2 a no-op.

**Code Snippet**

Find the existing call to `_extract_progress_messages` inside
`_run_extraction_pipeline` and add the two kwargs:

```python
progress_msgs = _extract_progress_messages(
    env, state, narrative,
    rules_outcome=rules_outcome,
    intent=intent,
    deescalate=deescalate,          # add this
    quest_ages=quest_ages,           # add this
    known_npcs=known_npcs,
    world_factions=world_factions,
    world_locations=world_locations,
    pc_allegiance=pc_allegiance,
)
```

Confirm that `deescalate` and `quest_ages` are already parameters on
`_run_extraction_pipeline` (they are: `deescalate: bool = False` and
`quest_ages: list[dict[str, Any]] = []` per current source). Widen
`deescalate: bool` to `deescalate: float` on `_run_extraction_pipeline` at the same
time.

**Validation:** `grep -n "deescalate" ccya/engine/extraction.py` — should show the
parameter on `_run_extraction_pipeline`, `_extract_scene_messages`, and
`_extract_progress_messages`, plus both call sites.

***

#### Step 2.4 — Move gm_beat consumption from scene_result to progress_result

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, find the block that reads
`scene_result.gm_beat` and stores it. Replace with a read from
`progress_result.gm_beat`.

**Why:** `gm_beat` no longer exists on `SceneExtractResult` after Phase 1.

**Code Snippet**

Current block (approximate — find exact lines in source):
```python
# Store gm_beat for next turn's narration  ← this comment is in turn.py, not here
# In extraction.py the gm_beat is returned as part of scene_result
```

The actual storage of `pending_gm_beat` is in `turn.py`, not `extraction.py`. The
pipeline returns `(delta, actions, outcome_summary, extraction_event, progress_result, scene_result)`.
`turn.py` then reads `scene_result.gm_beat`. That read is what must change.

**File:** `ccya/engine/turn.py`

Find this block in both `run_turn` and `run_turn_retry`:

```python
# Store gm_beat for next turn's narration
if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
    state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
```

Replace with (in both locations):

```python
# Store gm_beat for next turn's narration (produced by progress extractor)
if progress_result and progress_result.gm_beat and progress_result.gm_beat.type:
    _beat_dict = progress_result.gm_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
```

**Validation:** After a live turn, `state["meta"]["pending_gm_beat"]` should contain
`beat_expires_turn`. If `progress_result.gm_beat` is `None`, `pending_gm_beat` is not
written (existing behavior preserved).

***

#### Step 2.5 — Add beat expiry guard in narration phase

**File:** `ccya/engine/turn.py`

**What:** Before the narration call in `run_turn`, check whether
`pending_gm_beat["beat_expires_turn"]` (if present) is ≤ current turn. If so, nullify
it before passing to `_narrate_messages`. Do the same in `run_turn_retry`.

**Why:** If a beat was set but narration was interrupted, the beat persists. Without
expiry, a `breathing_room` beat from three turns ago could fire during an active combat
scene.

**Code Snippet**
```python
# Read pending_gm_beat from previous turn's progress extraction
_pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
if _pending_gm_beat:
    _expires = _pending_gm_beat.get("beat_expires_turn")
    if _expires is not None and turn_no > _expires:
        _pending_gm_beat = None
        state.setdefault("meta", {})["pending_gm_beat"] = None
```

Insert this block immediately after the existing `_pending_gm_beat = ...` assignment
in both `run_turn` and `run_turn_retry`. `turn_no` is already computed above this
point in `run_turn`; in `run_turn_retry` compute it the same way:
`turn_no = state.get("meta", {}).get("turn", 0) + 1` (it is already present later in
the function — move the computation up before the narration call).

**Validation:** Manually set `pending_gm_beat` with `beat_expires_turn` in the past in
a test state. Run a turn. Assert `pending_gm_beat` is `None` after narration.

***

#### Step 2.6 — Widen deescalate in turn.py and narrate.py

**File:** `ccya/engine/turn.py`

**What:** Replace the `deescalate: bool` computation block with a float magnitude
version.

**Code Snippet**
```python
# De-escalation magnitude: success on a scene with active pressure
deescalate: float = 0.0
if config and config.scene_pressure_deescalate_on_success:
    if (
        outcome.rolled
        and outcome.band in ("success", "crit_success")
        and any(
            p.get("urgency") in ("immediate", "building")
            for p in (state.get("scene") or {}).get("scene_pressure") or []
        )
    ):
        deescalate = 1.0 if outcome.band == "crit_success" else 0.6
```

**File:** `ccya/engine/narrate.py`

**What:** Change `deescalate: bool = False` to `deescalate: float = 0.0` in
`_narrate_messages` signature. The body is unchanged — `deescalate` is passed into
`user_ctx` as-is.

**Code Snippet**
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    # ... other params unchanged ...
    deescalate: float = 0.0,
    # ... remaining params unchanged ...
) -> list[dict[str, str]]:
```

**Validation:** `make check` — mypy should accept `float` passed to the float
parameter from `run_turn` and `run_turn_retry`.

***

### Tests to write or update

**File:** `tests/test_extraction.py` (create or extend)

- `test_progress_messages_receives_deescalate` — call `_extract_progress_messages`
  with `deescalate=0.6`, assert the rendered user message contains the deescalate
  value (check rendered Jinja output, not just the context dict).
- `test_progress_messages_receives_quest_ages` — same pattern for `quest_ages`.
- `test_gm_beat_from_progress_not_scene` — mock `_run_extraction_pipeline` to return
  a `ProgressExtractResult` with a valid `gm_beat` and a `SceneExtractResult` without
  one; assert the beat is stored in `meta.pending_gm_beat`.

**File:** `tests/test_turn.py` (create or extend)

- `test_beat_expiry` — set `meta.pending_gm_beat = {"type": "complication", "instruction": "...", "beat_expires_turn": 1}` with `meta.turn = 2`. Run one turn. Assert `pending_gm_beat` is not passed to narration.
- `test_deescalate_float_magnitude` — set up a state with `scene_pressure` of urgency
  `"immediate"` and simulate a `crit_success` band. Assert `deescalate == 1.0`.

### REPOMAP updates required

`docs/REPOMAP/extraction.md`: update `_run_extraction_pipeline`, `_extract_scene_messages`, `_extract_progress_messages` entries to reflect new signatures and beat source.

### Risks

1. **`run_turn_retry` `turn_no` placement.** In the current source, `turn_no` is
   computed *after* the narration call in `run_turn_retry` (`turn_no = state... + 1`
   appears near the extraction call). Step 2.5 requires it before narration for the
   expiry check. Moving the assignment earlier is safe — it is a pure read of state
   with no side effects — but confirm no other variable between the old and new
   position depends on it being computed late.
2. **Template evaluation of `deescalate` as float.** `scene_extract_user.j2` and
   `progress_extract_user.j2` (and `narrate_user.j2`) receive `deescalate` in their
   context. All existing `{% if deescalate %}` guards remain correct for floats
   (0.0 is falsy). If any template does numeric comparison (`> 0.5`), verify those
   comparisons after adding context.
3. **`extraction_event["scene"]["output"]` no longer has `gm_beat`.** Any UI or log
   viewer that renders the scene extraction output and expects a `gm_beat` key will
   now see it missing. Check `extraction_event["progress"]["output"]` for the key
   instead.
4. **`model_dump(exclude_none=True)` on `progress_result.gm_beat`.** `beat_expires_turn`
   is added by `turn.py` after `model_dump`, so it will not be present in the model's
   own dump — it is injected as a plain dict key. This is intentional and correct.

***

## Ambiguities requiring resolution before execution

1. **`_extract_progress_messages` full signature.** ✅ RESOLVED. The current signature
   (`extraction.py:257-269`) already has `active_domains`, `state_result`,
   `rules_outcome`, `enable_thinking`, `intent`, `recent_turns`, and `turn_no`.
   It does NOT have `deescalate` or `quest_ages` — those are the two targeted
   parameters to add (as described in Steps 2.2 and 2.3). It does NOT have
   `known_npcs`, `world_factions`, `world_locations`, or `pc_allegiance` — those
   are scene-extraction-only parameters and should NOT be added here.

2. **`extract_progress_user.j2` template.** ✅ RESOLVED. The template does NOT have
   a `gm_beat` instruction block. It currently has a prior-turn narration block at
   lines 52-56, but it reads `recent_turns[-2].narrative` which is the turn *before*
   the previous one (since `extraction.py:526` passes `recent_turns[-2:]`). Fix this
   to read `recent_turns[-1].narrative` — the most recent prior turn, which is the
   one the user wants for context. Add a new `gm_beat` instruction block after the
   `## END CURRENT TURN NARRATION` section (or before it, grouped with the other
   decision-context sections). The block should use `deescalate` and `quest_ages`
   context to decide beat type/urgency. Also add `"deescalate": deescalate` and
   `"quest_ages": quest_ages` to the `user_ctx` dict in `_extract_progress_messages`
   (Step 2.2).

3. **`extract_scene_user.j2` template.** ✅ RESOLVED. The template does NOT have a
   `gm_beat` instruction block — it already got removed in a prior change (or was
   never added). Lines 55-61 contain the `## previous_turn_narration` block which
   already provides the full previous turn. No `gm_beat` removal needed from this
   template.

## Known issue: rules step narration truncation

The rules step (`rules_user.j2:11`) currently receives only the last 120 characters
of the previous turn's narration:

```jinja2
T{{ t.turn }}: {{ t.input }} — {% if t.narrative | length > 120 %}… {% endif %}{{ t.narrative[-120:] }}
```

This is insufficient for intent classification. The rules engine needs the **full
previous turn narration** to understand context, track ongoing threads, and properly
gauge whether the player's current input is a continuation, escalation, or new action.

**Required change (separate from but related to this plan):** Update `rules_user.j2`
to emit the full previous turn narration. The call site in `turn.py:303` already
passes `recent_turns[-1:]` (one turn). Change the template to output the full
`prev.narrative` instead of the truncated slice.

The progress extraction pipeline passes `recent_turns[-2:]` (`extraction.py:526`)
but the template reads `recent_turns[-2].narrative` (`extract_progress_user.j2:54`),
which is the turn *before* the previous one. This must be fixed to `recent_turns[-1]`
to get the most recent prior turn. The scene extraction pipeline correctly receives
the full prior turn (`extract_scene_user.j2:55-61` shows `prev.narrative` in full).
Both the rules step (truncation) and progress step (wrong index) need fixes.

## TODO.md update

Add under **P2 — Narrative Quality**:

```
- [ ] GM beat ownership migration: scene → progress, deescalate float, beat expiry, rules full narration — [`docs/plans/progress-rules-narration.md`](docs/plans/progress-rules-narration.md)
```