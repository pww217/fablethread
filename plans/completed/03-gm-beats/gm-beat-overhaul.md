# GM Beat Overhaul Plan

## Purpose

Replace the type-driven `surface_as` beat system with an effect-driven, NPC-first beat model. Removes `surface_as` entirely, adds `effect`/`npc_id`/`driver` to GMBeat, injects NPC context from scene to storytell via `_ExtractionContext`, and simplifies the narrator prompt to use `effect` only.

## Problem Statement

The current GM beat system is type-driven rather than narrative-driven — the storyteller optimizes for beat type compliance (constrained by the pacing engine) rather than scene logic. The `surface_as` field has zero mechanical effect but consumes tokens in prompts, checkers, and validators. The storyteller lacks NPC context (motivation/fear/leverage) needed to generate NPC-driven beats, while simultaneously receiving too much irrelevant NPC data (bios, personalities, presence metadata) in `npc_roster`.

## Constraints

- **No new pipeline steps.** Beat generation stays in the storytell stream.
- **No async / background execution.** Single LLM call per turn.
- **Storytell context must not grow meaningfully.** `npc_context` replaces `npc_roster` for beat generation. Not additive.
- **Direct swap.** No backwards compatibility. Delete unused fields, routes, config keys, models.
- **`surface_as` removal must be clean.** Checker, validator, and prompt warnings all go.
- **`effect` is required (not nullable).** Default empty string. Null effect with non-null `npc_id` triggers a retriable error.
- **`npc_context` format:** `[{"npc_id": "x", "fear": "effect string"}, ...]` — scene passes its interpretation of what NPC fields mean right now.
- **npc_roster slimmed to id, name, title, bio only** for storytell.
- **`gm_beat` field name kept.** Not renamed to `beat`.
- **Flat JSON output.** No `record` wrapper. Structural separation is purely in the prompt.
- **Driver/npc_id mismatch → no coercion.** Leave it. The storytell has already made its best judgment.
- **Net prompt growth ~15 lines accepted.** Use existing templating patterns (sections/, conditional formatting) to limit template sprawl.

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
- Changes to the `consolidate-scene-location-extraction` design (implemented first)

## Solution

Replace `surface_as` with `effect` on the GMBeat model. Add `npc_id` and `driver` fields. Rewrite the storyteller prompts to be NPC-first with effect-driven beat generation. Inject `npc_context` from scene to storytell via `_ExtractionContext`. Slim `npc_roster` for storytell. Remove all `surface_as` references from checkers. Simplify narrator prompt to show `effect` only.

## Firm decisions

1. `effect` is a required string field with default `""`. The LLM must emit a short, concrete sentence. Empty effect with non-null `npc_id` triggers a single retry with a hint. Second failure coerces the beat to null.
2. `npc_context` is a list of dicts: `[{"npc_id": "x", "fear": "string"}, ...]`. Scene extracts it. Flows through `_ExtractionContext`. Storytell renders it.
3. `npc_roster` for storytell is slimmed to id, name, title, bio only. Built by a new `build_npc_roster_slimmed()` or a parameter to the existing function.
4. `build_npc_context()` is a new function in `scene.py`. It extracts relevant NPC psychological fields from the compendium based on narration + NPC fields alone (no arc/thread context).
5. The storyteller retry for null effect with npc_id uses the existing `_call_stream` retry mechanism — appends a user message with the hint.
6. `_npc_context.j2` is a new section template. Renders npc_context grouped by npc_id with all available fields.
7. `StorytellerResult._nullify_invalid_gm_beat` validator stays — it nullifies beats without a type. The null-effect-with-npc_id retry is handled separately in the pipeline.
8. `recent_beats` history entry changes from `{"turn": N, "type": "...", "surface_as": "..."}` to `{"turn": N, "type": "...", "effect": "..."}`.
9. `TurnResult.gm_beat` changes from `{"type": ..., "surface_as": ...}` to `{"type": ..., "effect": ...}`.

## Risks, Ambiguities, and Blockers

- **LLM schema transition.** The LLM is trained on the current schema (`type` + `surface_as`). Removing `surface_as` and adding `effect` will cause extraction failures until the LLM adapts. Expect one or two turns of degraded quality during transition.
- **`build_npc_context()` design.** The exact logic for which NPCs and which fields to extract is underspecified. The function should extract NPCs that are present or nearby, and extract the psychological field that is most relevant to the current narration. This is a best-effort heuristic — the storytell can still choose to ignore it.
- **Storytell retry mechanics.** The retry for null effect with npc_id needs to be handled in `pipeline.py` after the storytell result is parsed. The retry uses the existing `_call_stream` retry mechanism — appends a user message with the hint. The retry hint is: "Your previous attempt set npc_id without effect. Please provide a short, concrete sentence describing what this NPC is doing."
- **`npc_context` template rendering.** The template needs to group entries by npc_id and render all available fields for each NPC. The data format is `[{"npc_id": "x", "fear": "string"}, ...]` — not a flat list of fields.

## Status
`completed`

## Phases

4 phases covering: (1) model schema changes, (2) prompt template rewrites, (3) engine integration (scene npc_context, storytell injection, turn validation), (4) checker cleanup.

---

## Implementation — Phase 1: Model Schema Changes

### Context files to load
- `ccya/models/extraction.py` — GMBeat, StorytellerResult, SceneExtractResult
- `ccya/engine/extraction/context.py` — _ExtractionContext

### Detailed steps

#### Step 1.1 — Update GMBeat model

**File:** `ccya/models/extraction.py:176-214`

**What:** Remove `surface_as` field. Add `effect: str = ""`, `npc_id: str | None = None`, `driver: Literal["motivation", "fear", "leverage"] | None = None`. Keep `type` and `beat_expires_turn` unchanged. Keep `_coerce_gm_beat_type` validator.

**Why:** The beat model needs the new fields and must not accept `surface_as`.

**Validation:** `python -c "from ccya.models import GMBeat; b = GMBeat(type='complication', effect='test'); print(b.model_dump())"` — should output `{'type': 'complication', 'effect': 'test', 'npc_id': None, 'driver': None, 'beat_expires_turn': None}`.

#### Step 1.2 — Add npc_context to SceneExtractResult

**File:** `ccya/models/extraction.py:118-121`

**What:** Add `npc_context: list[dict[str, Any]] = Field(default_factory=list)` to `SceneExtractResult`.

**Why:** Scene extractor needs to pass npc_context to storytell via extraction_ctx.

**Validation:** `python -c "from ccya.models import SceneExtractResult; r = SceneExtractResult(npc_context=[{'npc_id': 'x', 'fear': 'y'}]); print(r.npc_context)"` — should output `[{'npc_id': 'x', 'fear': 'y'}]`.

#### Step 1.3 — Add npc_context to _ExtractionContext

**File:** `ccya/engine/extraction/context.py:15-31`

**What:** Add `npc_context: list[dict[str, Any]] = field(default_factory=list)` to `_ExtractionContext` dataclass.

**Why:** The same-turn passer needs to carry npc_context from scene to storytell.

**Validation:** `python -c "from ccya.engine.extraction.context import _ExtractionContext; ctx = _ExtractionContext(npc_context=[{'npc_id': 'x'}]); print(ctx.npc_context)"` — should output `[{'npc_id': 'x'}]`.

---

## Implementation — Phase 2: Prompt Template Rewrites

### Context files to load
- `ccya/prompts/storytell_system.j2`
- `ccya/prompts/storytell_user.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_npc_roster.j2`

### Detailed steps

#### Step 2.1 — Rewrite storytell_system.j2 beat section

**File:** `ccya/prompts/storytell_system.j2:76-94`

**What:** Replace the entire beat section (lines 76-94) with new instructions:
- Remove `surface_as` from the schema example (line 17: `"gm_beat": {"type": "...", "surface_as": "..."}` → `"gm_beat": {"type": "...", "effect": "...", "npc_id": "...", "driver": "..."}`)
- Rewrite the GM Beat section (lines 76-94) to describe:
  - `gm_beat`: one beat to shape the next turn, or `null`
  - `type`: constrained by `allowed_beat_types` from user prompt
  - `effect`: a short, concrete sentence describing what is about to happen. Must be narratively specific — name NPCs, reference locations, tie to active threads. NOT a category label. NOT "ambient tension." If you cannot write a concrete sentence, emit `null` for the entire `gm_beat`.
  - `npc_id`: the ID of the NPC driving this beat. Required when `driver` is set.
  - `driver`: one of `motivation`, `fear`, `leverage`. Required when `npc_id` is set.
  - Priority: NPC action first. Check present NPCs (see NPC Context below). If an NPC has an obvious move given the current situation, that becomes the beat. Environmental/atmospheric beats are fallbacks only.
  - Null beats are allowed. Only emit `null` if no NPC has a motivated move and no thread has a natural next action.
  - Roll band guidance (kept from current).
  - Diversity: don't repeat the same beat `type` more than twice consecutively. Use `recent_beats` as guidance.
  - Remove "Vary `surface_as` turn to turn" (line 94).
  - Remove all `surface_as` references (lines 81-82).

**Why:** The storyteller needs new instructions for effect-driven, NPC-first beat generation.

**Validation:** Read the rendered system prompt and verify it contains `effect` guidance and no `surface_as` references.

#### Step 2.2 — Rewrite storytell_user.j2 beat section

**File:** `ccya/prompts/storytell_user.j2:42-58`

**What:** 
- Replace the pending beat display (lines 42-52) to remove `surface_as`:
  ```
  {% if pending_beat and pending_beat.type %}
  ## GM Beat
  Type: **{{ pending_beat.type | replace('_', ' ') | upper }}**
  Expires: Turn {{ pending_beat.beat_expires_turn }}
  
  This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.
  {% else %}
  ## GM Beat
  No beat currently carried over from the previous turn. Choose freely.
  {% endif %}
  ```
- Replace the recent beats display (lines 53-58) to remove `surface_as`:
  ```
  {% if recent_beats %}
  ## Recent Beats
  {% for b in recent_beats %}T{{ b.turn }}: {% if b.type %}{{ b.type | replace('_', ' ') | upper }}{% endif %}
  
  {% endfor %}
  {% endif %}
  ```
- Add NPC Context section before the GM Beat section (after line 41, before line 42):
  ```
  {% if npc_context %}
  ## NPC Context
  {% for entry in npc_context %}- **{{ entry.npc_id }}**: {{ entry.values() | first }}
  {% endfor %}
  
  {% endif %}
  ```
  Note: The npc_context format is `[{"npc_id": "x", "fear": "string"}, ...]`. The template renders each entry as `npc_id: field_value`.

**Why:** The user prompt needs to display beat info without `surface_as` and include the npc_context section.

**Validation:** Read the rendered user prompt and verify it contains npc_context section and no `surface_as` references.

#### Step 2.3 — Create _npc_context.j2 section template

**File:** `ccya/prompts/sections/_npc_context.j2` (new)

**What:** Create a new section template that renders npc_context grouped by npc_id with all available fields. The data format is `[{"npc_id": "x", "fear": "string"}, ...]`. The template should group by npc_id and render all fields for each NPC.

```jinja2
{# sections/_npc_context.j2 #}
{% if npc_context -%}
## NPC Context
{% set _grouped = {} %}
{% for entry in npc_context %}{% set _nid = entry.npc_id %}{% if _nid not in _grouped %}{% set _ = _grouped.__setitem__(_nid, []) %}{% endif %}{% set _ = _grouped[_nid].append(entry) %}{% endfor %}
{% for _nid, _entries in _grouped.items() %}
- **{{ _nid }}**: {% for _e in _entries %}{{ _e.values() | first }}{% if not loop.last %} | {% endif %}{% endfor %}
{% endfor %}
{% endif %}
```

**Why:** Provides a reusable template for rendering npc_context. Follows existing templating patterns (sections/, conditional formatting).

**Validation:** `python -c "from jinja2 import Environment; env = Environment(loader=None); t = env.from_string(open('ccya/prompts/sections/_npc_context.j2').read()); print(t.render(npc_context=[{'npc_id': 'x', 'fear': 'y'}]))"` — should output the formatted npc_context.

#### Step 2.4 — Update narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2:11`

**What:** Update line 11 to reference `effect` instead of `type` + `surface_as`. The line currently says:
```
**Priority ordering: player input > GM beat > outcome hint.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action.
```
This is fine as-is — it doesn't reference `surface_as`. The system prompt doesn't need changes beyond what's already there. The beat is referenced generically as "GM beat" which works with `effect`.

**Why:** The system prompt already uses generic "GM beat" language. No changes needed.

**Validation:** Read the system prompt and verify no `surface_as` references exist.

#### Step 2.5 — Update narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2:86-88`

**What:** Replace lines 86-88:
```
{% if pending_beat and pending_beat.type -%}

**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — surface as `{{ pending_beat.surface_as | default('ambient') }}`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
{%- endif %}
```
With:
```
{% if pending_beat and pending_beat.effect -%}

**GM Beat:** {{ pending_beat.effect }}
{%- endif %}
```

**Why:** The narrator receives `effect` only — no `type` or `surface_as`. This simplifies the narrator's creative guidance.

**Validation:** Read the rendered user prompt and verify it shows `effect` only.

---

## Implementation — Phase 3: Engine Integration

### Context files to load
- `ccya/engine/extraction/scene.py`
- `ccya/engine/extraction/storytell.py`
- `ccya/engine/extraction/context.py`
- `ccya/engine/extraction/pipeline.py`
- `ccya/engine/turn.py`
- `ccya/engine/turn_state.py`
- `ccya/engine/npc_roster.py`

### Detailed steps

#### Step 3.1 — Add build_npc_context() to scene.py

**File:** `ccya/engine/extraction/scene.py`

**What:** Add a new function `build_npc_context(comp: dict[str, Any]) -> list[dict[str, Any]]` that extracts relevant NPC psychological fields from the compendium. The function should:
1. Filter NPCs to those with `presence` in `["present", "nearby"]`
2. For each NPC, extract the psychological field (motivation/fear/leverage/bond) that is most relevant to the current narration
3. Return a list of dicts: `[{"npc_id": "x", "fear": "string"}, ...]`
4. If no NPCs are present/nearby, return empty list

The relevance heuristic: check which psychological field is non-null and most likely to drive action. Prioritize `fear` > `motivation` > `leverage` > `bond`. The narration text is available as context but the function signature takes comp only (the narration is passed separately in `_extract_scene_messages`).

Actually, the function should take both narration and comp. The narration is needed to determine relevance.

```python
def build_npc_context(
    narration: str,
    comp: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build npc_context for storytell from compendium.
    
    Filters to present/nearby NPCs. For each, extracts the most relevant
    psychological field based on narration context.
    
    Returns list of dicts: [{"npc_id": "x", "fear": "string"}, ...]
    """
    ...
```

**Why:** Scene is the authority on which NPCs are relevant. It extracts psychological fields and passes structured context to storytell.

**Validation:** `python -c "from ccya.engine.extraction.scene import build_npc_context; comp = {'x': {'name': 'Test', 'presence': 'present', 'fear': 'dies', 'motivation': 'lives'}}; result = build_npc_context('test narration', comp); print(result)"` — should output `[{'npc_id': 'x', 'fear': 'dies'}]`.

#### Step 3.2 — Call build_npc_context() in _extract_scene_messages

**File:** `ccya/engine/extraction/scene.py:13-39`

**What:** In `_extract_scene_messages()`, after building `npc_roster`, call `build_npc_context(narration, comp)` and add the result to the scene result. The scene result is a `SceneExtractResult` — it already has `npc_context` field from Step 1.2. The `_call_stream` function in pipeline.py parses the LLM output into `SceneExtractResult`. The `npc_context` is NOT from the LLM — it's computed locally by `build_npc_context()`.

Wait — the scene extraction is an LLM call that returns `SceneExtractResult`. The `npc_context` is NOT part of the LLM output — it's computed locally after the LLM call. The flow is:
1. `_extract_scene_messages()` builds messages
2. `_call_stream()` calls LLM and parses into `SceneExtractResult`
3. After `_call_stream()` returns, `pipeline.py` has the `scene_result`
4. `pipeline.py` should call `build_npc_context()` and update `scene_result.npc_context`

Actually, looking at the design more carefully: "Scene extracts relevant NPC psychological fields based on narration + NPC fields alone (no arc/thread context). Passes structured list with npc_id + field type + effect string to storytell via `_ExtractionContext`."

The `npc_context` is NOT extracted by the LLM — it's computed locally from the compendium. The scene extractor doesn't need to be told to extract it — it's a local computation.

So the flow is:
1. `pipeline.py` calls `_extract_scene_messages()` → gets `scene_result` from LLM
2. `pipeline.py` calls `build_npc_context(narration, comp)` → gets `npc_context` list
3. `pipeline.py` updates `scene_result = scene_result.model_copy(update={"npc_context": npc_context})`
4. `pipeline.py` calls `_build_extraction_context(state, scene_result, state_result)` → `extraction_ctx` has `npc_context`
5. `pipeline.py` calls `_storytell_messages(...)` → storytell receives `npc_context` from `extraction_ctx`

This is cleaner — `build_npc_context()` is called in `pipeline.py`, not in `scene.py`. The function lives in `scene.py` (as a utility) but is called from `pipeline.py`.

Let me update Step 3.1 and add Step 3.2a.

**Step 3.1 (revised):** Add `build_npc_context()` function to `scene.py` (as above).

**Step 3.2a — Call build_npc_context() in pipeline.py**

**File:** `ccya/engine/extraction/pipeline.py:108-109` (after scene stream, before state stream)

**What:** After the scene stream completes (after line 108), add:
```python
npc_context = build_npc_context(narration, (state.get("compendium") or {}).get("npcs") or {})
scene_result = scene_result.model_copy(update={"npc_context": npc_context})
```
Import `build_npc_context` from `ccya.engine.extraction.scene`.

**Why:** The npc_context is computed locally from the compendium, not extracted by the LLM. It needs to be available before `_build_extraction_context()` is called.

**Validation:** The `scene_result.npc_context` should be populated after the scene stream.

#### Step 3.3 — Copy npc_context in _build_extraction_context

**File:** `ccya/engine/extraction/context.py:67-72`

**What:** In `_build_extraction_context()`, add `npc_context=scene_result.npc_context` to the `_ExtractionContext` constructor call (line 67-71).

**Why:** The same-turn passer needs to carry npc_context from scene to storytell.

**Validation:** `python -c "from ccya.engine.extraction.context import _build_extraction_context; ..."` — should include `npc_context` in the returned context.

#### Step 3.4 — Pass npc_context and slimmed npc_roster to storytell

**File:** `ccya/engine/extraction/storytell.py:58-100`

**What:** 
1. In `_storytell_messages()`, add `npc_context=extraction_ctx.npc_context` to the `_render()` call for `storytell_user.j2` (line 68-100).
2. Replace the `npc_roster` variable (line 63) with a slimmed version. The slimmed version should only include id, name, title, bio. Use a new function `build_npc_roster_slimmed()` or add a `slimmed` parameter to `build_npc_roster()`.

For the slimmed roster, add a `slimmed: bool = False` parameter to `build_npc_roster()` in `npc_roster.py`. When `slimmed=True`, only include id, name, title, bio.

```python
def build_npc_roster(
    comp: dict[str, Any],
    *,
    presence_filter: str | None = None,
    max_entries: int = 10,
    sort_by_lru: bool = False,
    lru_order: list[str] | None = None,
    personality_registry: dict[str, Any] | None = None,
    slimmed: bool = False,
) -> list[dict[str, Any]]:
    ...
    seen[nid] = {
        "id": nid,
        "name": name,
        "title": _strip_non_ascii(entry.get("title") or ""),
        "bio": (entry.get("bio") or "").strip() or None,
    }
    if not slimmed:
        seen[nid].update({
            "presence": presence,
            "motivation": entry.get("motivation") or None,
            "fear": entry.get("fear") or None,
            "leverage": entry.get("leverage") or None,
            "bond": entry.get("bond") or None,
            "notes": entry.get("notes") or None,
            "last_presence_turn": entry.get("last_presence_turn"),
            "last_seen_location": entry.get("last_seen_location") or None,
            "departed_reason": entry.get("departed_reason") or None,
        })
        if personality_registry:
            ...
```

Then in `storytell.py`:
```python
npc_roster = build_npc_roster(extraction_ctx.comp_this_turn, personality_registry=ARCHETYPES, slimmed=True)
```

3. Add `npc_context` to the `_render()` call for `storytell_user.j2`:
```python
"npc_context": extraction_ctx.npc_context,
```

**Why:** Storytell needs npc_context for beat generation and a slimmed npc_roster (id, name, title, bio only) to reduce token cost.

**Validation:** The storytell user prompt should include `npc_context` section and a slimmed `npc_roster`.

#### Step 3.5 — Add beat validation and retry logic in pipeline.py

**File:** `ccya/engine/extraction/pipeline.py:181-237` (after storytell result is parsed)

**What:** After the storytell result is parsed (after line 185, before the actions fallback), add validation using the same pattern as `_call_stream`'s retry hints (utils.py:254-265): append a user message with a targeted hint and re-call `_call_stream`.

```python
# Post-parse validation: null effect with non-null npc_id is incoherent
if storytell_result.gm_beat and storytell_result.gm_beat.npc_id and not storytell_result.gm_beat.effect:
    _log.warning(
        "storytell beat: npc_id '%s' set but effect is empty, retrying",
        storytell_result.gm_beat.npc_id,
        extra={"trace_id": trace_id},
    )
    retry_msgs = list(storytell_msgs)
    retry_msgs.append({
        "role": "user",
        "content": (
            f"IMPORTANT: Your previous attempt set npc_id '{storytell_result.gm_beat.npc_id}' "
            f"without effect. Please provide a short, concrete sentence describing what this NPC is doing. "
            f"Re-emit JSON."
        ),
    })
    try:
        storytell_result, storytell_usage, storytell_attempts, storytell_retry_errors = await _call_stream(
            retry_msgs, config, trace_id, "storytell",
            StorytellerResult, strip_keys=("_reasoning",),
        )
        extraction_event["storytell"]["attempts"] = storytell_attempts
        extraction_event["storytell"]["retry_errors"].extend(storytell_retry_errors)
        # Exhausted retry — coerce to null
        if storytell_result.gm_beat and storytell_result.gm_beat.npc_id and not storytell_result.gm_beat.effect:
            _log.warning(
                "storytell beat: retry also failed — coercing beat to null",
                extra={"trace_id": trace_id},
            )
            storytell_result = storytell_result.model_copy(
                update={"gm_beat": None}
            )
    except Exception as exc:
        _log.warning(
            "storytell retry failed: %s", exc, extra={"trace_id": trace_id},
        )
        extraction_event["storytell"]["retry_errors"].append(str(exc))
```

**Why:** The storyteller may generate an NPC-driven beat but fail to write an effect sentence. The retry uses the same pattern as `_call_stream`'s parse-failure retry hints — append a user message with a targeted hint and re-call `_call_stream`. If the retry also fails, coerce the beat to null.

**Validation:** Test with a stored event that has npc_id set but empty effect. The retry should be triggered and the beat should be coerced to null on second failure.

#### Step 3.6 — Update turn_state.py beat history

**File:** `ccya/engine/turn_state.py:470-476`

**What:** Replace `surface_as` with `effect` in the beat history snapshot:
```python
meta.setdefault("recent_beats", []).append({
    "turn": turn_no,
    "type": _history_beat.get("type") if _history_beat else None,
    "effect": _history_beat.get("effect") if _history_beat else "",
})
```

**Why:** The recent_beats history should track `effect` instead of `surface_as`.

**Validation:** The `recent_beats` list in state should contain `{"turn": N, "type": "...", "effect": "..."}` entries.

#### Step 3.7 — Update turn.py TurnResult.gm_beat

**File:** `ccya/engine/turn.py:471-474`

**What:** Replace `surface_as` with `effect` in the TurnResult.gm_beat dict:
```python
gm_beat={
    "type": storyteller_result.gm_beat.type,
    "effect": storyteller_result.gm_beat.effect,
} if (storyteller_result and storyteller_result.gm_beat) else None,
```

**Why:** The TurnResult should report `effect` instead of `surface_as`.

**Validation:** The TurnResult.gm_beat should contain `{"type": "...", "effect": "..."}`.

---

## Implementation — Phase 4: Checker Cleanup

### Context files to load
- `ccya/ev/checkers/pacing.py`
- `ccya/ev/checkers/gm_beat.py`
- `ccya/ev/checkers/llm_checkers.py`
- `ccya/ev/checkers/recent_beats.py`

### Detailed steps

#### Step 4.1 — Remove surface_as checker from pacing.py

**File:** `ccya/ev/checkers/pacing.py:128-161`

**What:** Remove the entire `surface_as consistency` checker block (lines 128-161). This includes the loop that checks consecutive same-type beats don't flip `surface_as` without directive change.

**Why:** `surface_as` is removed. The checker is dead code.

**Validation:** `python -c "from ccya.ev.checkers.pacing import pacing_directives; print('imports OK')"` — should import without error.

#### Step 4.2 — Update beat_narrative_chain in llm_checkers.py

**File:** `ccya/ev/checkers/llm_checkers.py:88-156`

**What:** 
1. Remove `surface_as` from the system prompt template (line 93: "The beat's surface_as (ambient, environmental, etc.)" → remove this line).
2. Remove `surface_as` from the user prompt template (line 106: "Surface: {surface_as}" → remove this line).
3. Remove `surface_as` from the checker function (line 133: `surface_as = pending_beat.get("surface_as", "ambient")` → remove this line).
4. Remove `surface_as` from the user prompt construction (line 143: "Surface: {surface_as}" → remove this line).

**Why:** The checker should evaluate beat narrative chain using `effect` instead of `surface_as`. The `surface_as` field no longer exists.

**Validation:** `python -c "from ccya.ev.checkers.llm_checkers import beat_narrative_chain; print('imports OK')"` — should import without error.

#### Step 4.3 — Update recent_beats checker

**File:** `ccya/ev/checkers/recent_beats.py:77-83`

**What:** Replace the field check:
```python
if "type" not in entry or "surface_as" not in entry:
    findings.append({
        "turn": ev.get("turn"),
        "check": "recent_beats_entry_fields",
        "detail": f"entry[{j}] missing 'type' or 'surface_as' field",
    })
```
With:
```python
if "type" not in entry or "effect" not in entry:
    findings.append({
        "turn": ev.get("turn"),
        "check": "recent_beats_entry_fields",
        "detail": f"entry[{j}] missing 'type' or 'effect' field",
    })
```

**Why:** The recent_beats history now uses `effect` instead of `surface_as`.

**Validation:** The checker should pass for events with `{"type": "...", "effect": "..."}` entries.

#### Step 4.4 — Update gm_beat checker (no changes needed)

**File:** `ccya/ev/checkers/gm_beat.py`

**What:** No changes needed. The checker validates beat lifecycle (pending_gm_beat consumed, type match) — it doesn't reference `surface_as` or `effect`.

**Why:** The checker is field-agnostic for the beat content. It only validates lifecycle mechanics.

**Validation:** Read the checker and confirm no `surface_as` or `effect` references exist.

#### Step 4.5 — Update documentation (mandatory per AGENTS.md)

**Files:** `docs/architecture/` (pipeline/data shapes), `docs/repomap.md` (module boundaries/APIs)

**What:** Update docs to reflect the changes:
- `docs/architecture/` — Update data shape docs to replace `surface_as` with `effect` in GMBeat schema. Update pipeline docs to describe npc_context flow (scene → _ExtractionContext → storytell).
- `docs/repomap.md` — Update GMBeat model section (remove `surface_as`, add `effect`/`npc_id`/`driver`). Update `_ExtractionContext` section (add `npc_context`). Update storytell module section (add `npc_context` parameter). Update checkers section (remove `surface_as` checker, update `beat_narrative_chain`).
- `docs/design/gm-beat-overhaul-design.md` — Move to `plans/completed/` with status update.

**Why:** AGENTS.md mandates doc updates for any change touching models, prompts, or checkers. Stale docs are bugs.

**Validation:** `grep -rn "surface_as" docs/` — should return zero results. `grep -rn "npc_context" docs/` — should show the new flow documentation.

---

## Tests to write or update

Tests are temporarily removed during refactor. No tests to write.

Run `make check` (lint + typecheck) as a final validation step when all phases are complete.
