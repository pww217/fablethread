# Pipeline Field Routing Remediation

## Status
`open`

## Part of
`eval-results-remediation`

## Dependencies
- none (prerequisite for Plans B, C, D)

## Objective
The current three-stream extraction pipeline has fields assigned to the wrong extractors. `outcome_summary` and `actions` live in `SceneExtractResult` but both require quest context only the progress extractor has. `compendium_npc_update`, `scene_pressure_*`, and `gm_beat` live in `ProgressExtractResult` but belong semantically with scene — they are scene-centric observations, not storytelling-engine forward projections. `failed` lives in `StateExtractResult` but is not a state delta; it is a narration feedback signal and belongs as a trace-only field, not extracted from the LLM at all. This plan re-routes each field to its correct home and updates `extraction.py`, `models.py`, `turn.py`, and all affected templates to match.

## Non-goals
- Does NOT change the logic of any field (e.g. `gm_beat` rules, pressure lifecycle). Those are Plans B and C.
- Does NOT change `apply_delta` scene_pressure or compendium application logic — those already read from `StateDelta` which already maps correctly from `ProgressExtractResult`. After this plan, they map from `SceneExtractResult` instead.
- Does NOT merge the scene and state extractors.
- Does NOT move `pc_condition_*` — stays in state.
- Does NOT change `outcome_summary` or `actions` in `TurnResult` or `events.jsonl` schema — those still exist at the turn level; this plan only changes which extractor populates them.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Move `actions`, `outcome_summary` out of `SceneExtractResult`; move `compendium_npc_update`, `scene_pressure_*`, `gm_beat` out of `ProgressExtractResult` and into `SceneExtractResult`; remove `failed` from `StateExtractResult` |
| `ccya/engine/extraction.py` | modify | Update `_extract_scene_messages` to pass `known_characters`, `scene_pressure`, `deescalate`, `quest_ages`; update `_extract_progress_messages` to remove scene_pressure, compendium, gm_beat from its context; update merge block to read routed fields from correct results; fix return tuple to pull `actions`/`outcome_summary` from `progress_result`, `compendium_npc_update`/`scene_pressure_*`/`gm_beat` from `scene_result` |
| `ccya/prompts/extract_scene_system.j2` | modify | Add field rules for `compendium_npc_update`, `scene_pressure_*`, `gm_beat`; remove `actions`/`outcome_summary` field rules |
| `ccya/prompts/extract_scene_user.j2` | modify | Add `scene_pressure`, `known_characters`, `deescalate`, `quest_ages` sections; remove nothing (backwards-compatible rendering) |
| `ccya/prompts/extract_progress_system.j2` | modify | Remove field rules for `compendium_npc_update`, `scene_pressure_*`, `gm_beat`; add field rules for `actions`, `outcome_summary` |
| `ccya/prompts/extract_progress_user.j2` | modify | Add narration context needed for `actions`/`outcome_summary`; remove `scene_pressure` block; remove `known_characters` block |
| `ccya/engine/turn.py` | modify | Fix `failed` removal — cut LLM-extracted `failed` field; load `last_turn_failed` from events (already done), but remove `state_result.failed` from the pipeline return and event logging |
| `docs/REPOMAP/extraction.md` | update | Reflect new field assignments per stream |
| `docs/plans/TODO.md` | update | Add this plan |

## Firm decisions

1. `actions` and `outcome_summary` move to `ProgressExtractResult`. Progress already has quest context, narration, and outcome band — it is the right brain for "what just happened in story terms" and "what can the player do next."
2. `compendium_npc_update`, `scene_pressure_*`, and `gm_beat` move to `SceneExtractResult`. Scene is the right extractor for present-tense, observation-based facts: who is in the scene, what threats exist, what beat to set up.
3. `failed` is cut from the LLM output entirely. The state extractor is not the right place to evaluate whether an action failed — it only exists to catch inventory and conditions. `last_turn_failed` is already loaded from `events.jsonl` (pre-existing code in `turn.py`); that mechanism is preserved but the field is no longer populated by the LLM. The `failed` key in `events.jsonl` will always be `[]` going forward.
4. `SceneExtractResult` receives the full compendium roster, active `scene_pressure`, `deescalate` flag, and `quest_ages` because those are needed for the gm_beat and pressure logic now living there.
5. The `ProgressExtractResult` receives `recent_turns[-2:]` (previous full narration + current turn narration) in addition to current narration — this gives it the storytelling context needed for `outcome_summary` and `actions`. See Step 1.3.
6. Schema key names in JSON output are unchanged — LLM output keys stay the same; only which schema model they belong to changes.

## Implementation — Phase 1: Models

### Context files to load
- `ccya/models.py`

### Overview
Restructure the three extractor result models and `StateDelta` to reflect the new field ownership. All changes are purely additive to one model and subtractive from another — no field semantics change.

### Detailed steps

#### Step 1.1 — Move fields in `SceneExtractResult`

**File:** `ccya/models.py`

**What:** Add `compendium_npc_update`, `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update`, and `gm_beat` to `SceneExtractResult`. Remove `actions` and `outcome_summary`.

**Why:** Scene extractor is observation-based. It sees the narration first, knows what NPCs entered/left, what threats emerged, and what beat to set up for next turn. These are all present-tense scene observations.

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
    gm_beat: GMBeat | None = None

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

**Validation:** `python -c "from ccya.models import SceneExtractResult; r = SceneExtractResult(); assert hasattr(r, 'scene_pressure_add'); assert not hasattr(r, 'actions')"` — passes without error.

---

#### Step 1.2 — Move fields in `ProgressExtractResult`

**File:** `ccya/models.py`

**What:** Add `actions` and `outcome_summary` to `ProgressExtractResult`. Remove `compendium_npc_update`, `scene_pressure_*`, and `gm_beat`.

**Why:** Progress extractor sees quest context, narration, and outcome band. `outcome_summary` is a story-beat summary (what just happened). `actions` are forward-looking choices grounded in quest objectives.

**Code Snippet**
```python
class ProgressExtractResult(BaseModel):
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""

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
                out.append(x.get("action", str(x)))
            else:
                out.append(str(x))
        return out
```

**Validation:** `python -c "from ccya.models import ProgressExtractResult; r = ProgressExtractResult(); assert hasattr(r, 'actions'); assert not hasattr(r, 'gm_beat')"` — passes without error.

---

#### Step 1.3 — Remove `failed` from `StateExtractResult`

**File:** `ccya/models.py`

**What:** Remove the `failed: list[str]` field from `StateExtractResult`.

**Why:** The state extractor should not be evaluating action failure. It's not a storytelling brain; it reads narration for physical object and condition changes only. `failed` was never meaningfully used downstream — `last_turn_failed` in `turn.py` is loaded from the previous event record directly.

**Code Snippet**
```python
class StateExtractResult(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)
    pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=2)
    pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)

    @field_validator("inventory_remove", mode="before")
    @classmethod
    def _coerce_inventory_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x, "amount": None})
            else:
                out.append(x)
        return out

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        if not v:
            return v
        return [_coerce_condition_str(x) for x in v]

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                cid = x.lower().strip().replace(" ", "_")
                for ch in ("*", "_", "`", ".", ","):
                    cid = cid.replace(ch, "")
                out.append({"id": "_".join(cid.split()) or "condition"})
            else:
                out.append(x)
        return out
```

**Validation:** `python -c "from ccya.models import StateExtractResult; r = StateExtractResult(); assert not hasattr(r, 'failed')"` — passes without error.

---

## Implementation — Phase 2: extraction.py

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/models.py` (post Phase 1)

### Overview
Update `_extract_scene_messages` to pass the new context variables scene now needs. Update `_extract_progress_messages` to remove what it no longer owns. Fix the merge block so each `StateDelta` field is populated from the correct result object. Fix the return tuple.

### Detailed steps

#### Step 2.1 — Update `_extract_scene_messages` signature and context

**File:** `ccya/engine/extraction.py`

**What:** Add `scene_pressure`, `deescalate`, `quest_ages`, and `known_characters` parameters. Pass them to the user template. `known_characters` already exists in the module via `_known_characters_for_extract` — call it here the same way it's called in `_extract_progress_messages`.

**Why:** Scene extractor now owns `scene_pressure_*`, `compendium_npc_update`, and `gm_beat` — all of which require the current pressure list, deescalate flag, quest ages, and the full compendium to render correctly.

**Code Snippet**
```python
def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (scene + NPC + pressure + gm_beat)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=False)
    npc_roster = _scene_npc_roster(known_characters)
    present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
    scene_pressure = list((state.get("scene") or {}).get("scene_pressure") or [])
    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "location": location,
            "conditions": conditions,
            "npc_roster": npc_roster,
            "present_npcs": present_npcs,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
            "scene_pressure": scene_pressure,
            "deescalate": deescalate,
            "quest_ages": quest_ages or [],
            "active_quests": active_quests,
            "recent_turns": recent_turns or [],
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs
```

**Validation:** No Python errors on import. Template variables are available in the user prompt.

---

#### Step 2.2 — Update `_extract_progress_messages` signature and context

**File:** `ccya/engine/extraction.py`

**What:** Remove `scene_pressure`, `known_characters`, `deescalate`, and `quest_ages` from the context dict passed to `extract_progress_user.j2`. Add `recent_turns` (last 2 full turns) so progress has storytelling context for `outcome_summary` and `actions`. The `intent` object (already available as a parameter via `_run_extraction_pipeline`) should also be passed to give progress the player's action verb.

**Why:** Progress no longer owns pressure, compendium, or gm_beat. It does own `actions` and `outcome_summary`, which require the narrative arc of the last two turns plus player intent.

**Code Snippet**
```python
def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (quests + facts + actions + outcome_summary)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])

    state_ctx = {
        "items_gained": [it.name for it in state_result.inventory_add],
        "items_lost": [it.id for it in state_result.inventory_remove],
    }

    system_text = _render(env, "extract_progress_system.j2", {})
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "active_quests": active_quests,
            "recent_events": recent_events,
            "world_state": world_state,
            "state_result": state_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
            "quest_threshold_directive": _quest_threshold_directive(active_quests),
            "quest_ages": quest_ages or [],
            "intent": intent,
            "recent_turns": recent_turns or [],
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs
```

**Validation:** No Python errors on import; `scene_pressure`, `known_characters`, and `deescalate` are no longer passed; `recent_turns` and `intent` are present.

---

#### Step 2.3 — Update `_run_extraction_pipeline` call sites and merge block

**File:** `ccya/engine/extraction.py`

**What:** Three sub-changes:
1. Pass `deescalate`, `quest_ages`, and `recent_turns[-2:]` to `_extract_scene_messages`.
2. Pass `intent` and `recent_turns[-2:]` to `_extract_progress_messages`; remove `deescalate` and `known_characters`.
3. Rewrite the merge block so each `StateDelta` field comes from the correct result.
4. Fix the return tuple: `actions` and `outcome_summary` from `progress_result`; `failed` always `[]`.

**Why:** Merging must reflect the new ownership. The return tuple's `actions`/`outcome_summary` from `scene_result` was the bug.

**Code Snippet**
```python
# In _run_extraction_pipeline, Stream 1 call:
scene_msgs = _extract_scene_messages(
    env, narration, state,
    active_domains=active_domains,
    rules_outcome=rules_outcome,
    enable_thinking=config.enable_extract_thinking,
    deescalate=deescalate,
    quest_ages=quest_ages,
    recent_turns=(recent_turns or [])[-2:],
)

# In _run_extraction_pipeline, Stream 3 call:
progress_msgs = _extract_progress_messages(
    env, narration, state,
    active_domains=active_domains,
    scene_result=scene_result,
    state_result=state_result,
    rules_outcome=rules_outcome,
    enable_thinking=config.enable_extract_thinking,
    intent=intent,
    quest_ages=quest_ages,
    recent_turns=(recent_turns or [])[-2:],
)

# Merge block (complete replacement):
merged = StateDelta(
    scene_tags=scene_result.scene_tags,
    scene_tagline=scene_result.scene_tagline,
    location_change=scene_result.location_change,
    location_description=scene_result.location_description,
    npc_add=scene_result.npc_add,
    npc_remove=scene_result.npc_remove,
    npc_update=scene_result.npc_update,
    compendium_npc_update=scene_result.compendium_npc_update,
    scene_pressure_add=scene_result.scene_pressure_add,
    scene_pressure_remove=scene_result.scene_pressure_remove,
    scene_pressure_update=scene_result.scene_pressure_update,
    inventory_add=state_result.inventory_add,
    inventory_remove=state_result.inventory_remove,
    inventory_update=state_result.inventory_update,
    pc_condition_add=state_result.pc_condition_add,
    pc_condition_remove=state_result.pc_condition_remove,
    quest_updates=progress_result.quest_updates,
    recent_events_add=progress_result.recent_events_add,
    recent_events_update=progress_result.recent_events_update,
    recent_events_remove=progress_result.recent_events_remove,
)

# Return tuple fix:
return (
    merged,
    progress_result.actions,        # was: scene_result.actions
    progress_result.outcome_summary, # was: scene_result.outcome_summary
    [],                              # failed: always empty, removed from LLM
    extraction_event,
    progress_result,
)
```

**Validation:** `python -c "from ccya.engine.extraction import _run_extraction_pipeline"` imports without error. Grep confirms `scene_result.actions` and `scene_result.outcome_summary` no longer appear in the file.

---

#### Step 2.4 — Thread `recent_turns` into `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** Add `recent_turns: list[dict[str, Any]] | None = None` parameter to `_run_extraction_pipeline`. Pass through from callers in `turn.py`.

**Why:** Scene and progress extractors now need prior turn context. The function signature must accept and forward it.

**Code Snippet**
```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    pack_examples: list["ExtractExample"] | None = None,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,   # NEW
) -> tuple["StateDelta", list[str], str, list[str], dict[str, Any], "ProgressExtractResult"]:
```

**Validation:** Both call sites in `turn.py` compile after the next step.

---

#### Step 2.5 — Update `gm_beat` persistence in `turn.py`

**File:** `ccya/engine/turn.py`

**What:** The `gm_beat` store-to-meta logic currently reads from `progress_result.gm_beat`. Change it to read from `scene_result`. Also: (1) pass `recent_turns` to `_run_extraction_pipeline` in both `run_turn` and `run_turn_retry`; (2) remove the `failed` field from the event dict (replace with `[]` hardcoded since it's now always empty — keep the key for backwards compat with existing event log readers).

**Why:** `gm_beat` is now a field of `SceneExtractResult`. The `progress_result` return from `_run_extraction_pipeline` no longer has it.

**Code Snippet**
```python
# In run_turn and run_turn_retry, _run_extraction_pipeline call — add recent_turns:
delta, actions, outcome_summary, failed, extraction_event, progress_result, scene_result = (
    await _run_extraction_pipeline(
        env, state, narrative,
        active_domains=_active_domains,
        rules_outcome=outcome,
        intent=intent,
        config=config,
        trace_id=trace_id,
        turn_no=turn_no,
        pack_examples=pack_examples,
        deescalate=deescalate,
        quest_ages=quest_ages,
        recent_turns=recent_turns,   # NEW
    )
)
# Store gm_beat from scene_result (was progress_result):
if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
    state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
```

Note: `_run_extraction_pipeline` must also return `scene_result` as a 7th element of the tuple. Add it to both the return statement in `extraction.py` and the unpacking in `turn.py`.

**Validation:** `make check` passes. `grep -n "progress_result.gm_beat" ccya/engine/turn.py` → no matches.

---

## Implementation — Phase 3: Prompt Templates

### Context files to load
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_state_system.j2`
- `ccya/prompts/extract_state_user.j2`

### Overview
Move field documentation from the progress system prompt to the scene system prompt for `compendium_npc_update`, `scene_pressure_*`, and `gm_beat`. Move `actions` and `outcome_summary` from the scene system prompt to the progress system prompt. Update user prompts to render the newly available context variables. Strip `failed` from the state system prompt.

### Detailed steps

#### Step 3.1 — Rewrite `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the entire file. Keep all existing field rules verbatim. Add the field rule blocks for `compendium_npc_update`, `scene_pressure_*`, `gm_beat`, and de-escalation logic (cut verbatim from `extract_progress_system.j2`). Remove the `actions` and `outcome_summary` field rules.

**Code Snippet**
```jinja2
Extract scene state, NPC presence, location, compendium NPC updates, scene pressure, and the GM beat from a narration.
Emit one JSON object matching the schema. No prose, no markdown fences, null for optional fields that don't apply, never omit a key.

## Output schema

```json
{
  "scene_tags": [],
  "scene_tagline": "",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": null
}
```

## Field rules

`scene_tags`: 1-3 lowercase tags from {dialogue, combat, exploration, market, travel, stealth, rest}. Always provide at least one. Include `"game_over"` ONLY if the player character (not an NPC) is confirmed dead this turn. When a scene involves armed/hostile NPCs or physical confrontation, prefer "combat" over "dialogue" even if the player is speaking.

`scene_tagline`: 3-6 word phase. Relevant to story or scene only, not mechanical. Upper case words. Examples: `"Dock Fees Due at Dawn"`, `"The Emperor's Assassin"`.

`location_change`: emit `{"id": "snake_case_id", "name": "Location Name", "description": "1-2 sentences"}` if the player physically moved or the situation has changed significantly. If player has moved away from NPCs, remove them from scene. Null if no change.

`location_description`: Only emit this field if the narration describes a meaningful environmental or atmospheric change to the current location — a shift in lighting, weather, crowd density, physical damage, or emotional register of the space. Do not re-describe unchanged surroundings. If the scene looks and feels the same as before, omit `description` entirely.

`npc_add`: new NPCs entering the scene this turn. Each: `{"id": "snake_case", "notes": "current situation", "name": "Full Name", "title": "Role", "bio": "1-3 sentences"}`. Only include name/title/bio for genuinely new NPCs not in the compendium. Omit name/title/bio for ambient/extra NPCs. If an NPC was previously unnamed (referred to by descriptor), check the compendium roster — if it's the same character, use `npc_update` instead of `npc_add`. **Compendium NPCs are NOT in the scene by default. Emit `npc_add` for any NPC mentioned in the narration that is NOT in `present_npcs`, even if they appear in the compendium roster.**

`npc_remove`: IDs of named NPCs who explicitly left the scene or are no longer in proximity. Each: `{"id": "existing_id", "last_seen_state": "1-sentence description of what they were last seen doing"}`. **Only remove NPCs when the narration clearly states or implies they left.** Do NOT remove NPCs just because the scene shifted focus, or because the player moved (allies follow). When in doubt, keep them.

`npc_update`: existing scene NPCs whose notes changed this turn. Each: `{"id": "existing_id", "notes": "updated situation"}`. Name/title/bio only change when new information arrives. Notes change every turn. If the narration mentions an NPC already in the scene, you MUST emit an `npc_update` for them.

## NPC ID format rules

NPC IDs must be `firstname_lastname` only. No titles, roles, or descriptors.
- ✅ `kael_marsh`, `torben_klask`
- ❌ `scarred_soldier`, `doctor_voss`, `the_merchant`
- If only one name is known: `kael` (single token, no decorators)
- When a full name is revealed later: emit `compendium_npc_update` to set the canonical ID and add old ID as alias

IDs are immutable once assigned. Name changes go in the `name` field and `aliases`, not the ID.

## NPC match instruction

Before emitting `compendium_npc_update` to add a new NPC, check the existing compendium list in the user prompt.
If the character is likely the same person referred to differently, use the existing ID and emit an update instead.
Add the old descriptor as an alias. Only emit an add for a genuinely new NPC not present in the current compendium.
**If the character's name matches an existing compendium NPC (case-insensitive), use their existing ID. Do NOT create a new entry.**

`compendium_npc_update`: NPC records to create or update based on genuinely new durable info (allegiance changed, died, new name learned, relationship revealed). Each: `{"id": "npc_id", "name": "optional", "title": "optional", "bio": "updated 1-3 sentence durable identity"}`. Don't re-emit NPCs whose info didn't change.

If the narration describes an NPC as killed, mortally wounded, captured, or permanently removed: emit `compendium_npc_update` with `bio` recording their fate. Do not omit this update — dead NPCs must be recorded.

`scene_pressure_add`: Add a `scene_pressure` entry when the narration introduces a time-sensitive threat, pursuit, hazard, or countdown. Set `urgency` based on immediacy: "immediate" if it must be addressed this turn, "building" if it escalates over 2-4 turns, "background" for ambient threat. Set `max_turns` to an explicit fiction-grounded expiry if the narration implies a hard deadline. Do NOT add lore or permanent world facts to `scene_pressure`. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": 0, "max_turns": null}`.

`scene_pressure_remove`: IDs of pressures now resolved — the fire is out, the guards were evaded, the bomb was defused.

`scene_pressure_update`: Changes to existing pressure text or urgency. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.

## De-escalation

When `deescalate` is true in the user prompt: do NOT emit `scene_pressure_add`. Emit `scene_pressure_update` to downgrade urgency (`immediate → building`, `building → background`). If fully resolved, emit `scene_pressure_remove`. Pair with a `breathing_room` GM beat.

## NPC scene cap

No more than 8 named NPCs in a scene. If the narration introduces a 9th, the oldest/least relevant named NPC should be removed. Ambient NPCs don't count toward the cap. Allies, family, and key characters should be assumed to follow the player when they move. **NPC removal should only happen for: (1) the narration clearly shows the NPC left, or (2) the scene cap is exceeded. Never remove NPCs for any other reason.**

## GM Beat (gm_beat)

**IMPORTANT: `type` vs `surface_as` are different fields.**
- `type` is the beat category: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`.
- `surface_as` is how the beat is presented: `ambient`, `event`, or `npc_behavior`.
- **Do NOT set `type: "ambient"`.** `ambient` is a `surface_as` value only.

After extracting this turn's changes, decide whether to emit a forward-facing story beat for the NEXT turn.

Emit `null` if:
- There are 3+ active `scene_pressure` entries (don't pile on)
- `deescalate` is true (use `breathing_room` GM beat instead — see De-escalation)
- The player is in a critical resolution moment (final quest objective in reach)
- Nothing meaningful has changed in faction, NPC, or quest state to react to

Emit a beat when:
- `pc.momentum` >= +2: emit `complication` to raise stakes
- `pc.momentum` <= -2: emit `opportunity` or `breathing_room`
- A quest has been stalled (same objective for 3+ turns, shown as ⚠ in user prompt): emit `pressure` or `revelation`
- An NPC with unknown or shifting allegiance is present: emit `revelation`

Beat instruction rules:
- `instruction`: 1-2 sentences. **Concrete and story-specific — name the NPC, faction, or object involved.** Must not be empty.
- BAD: "Something bad happens to the player." GOOD: "A contact the player trusted has been seen meeting with the opposing faction at the dockside inn."
- BAD: "Give the player a break." GOOD: "The player spots a satchel left behind by a fleeing guard — it contains a vial and a partial map."

`surface_as` guidance:
- `ambient`: low-stakes background texture. Used for `breathing_room` and most `revelation` beats.
- `event`: something the player can directly interact with. Used for `opportunity` and `pressure`.
- `npc_behavior`: a present NPC shifts their demeanor, loyalty signal, or body language. Best for `revelation` and `complication`.

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only infer changes that are explicit.
```

**Validation:** Template renders without Jinja error when called with empty context.

---

#### Step 3.2 — Rewrite `extract_scene_user.j2`

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Add blocks for `scene_pressure`, `deescalate`, `quest_ages`, and the full compendium roster (not just compact). Keep existing blocks verbatim. Add `recent_turns` block showing the previous turn's narration (T-1 only — the current narration is already shown).

**Code Snippet**
```jinja2
{% if rules_outcome and rules_outcome.rolled -%}
## rules_outcome
{{ rules_outcome.band | upper }} on {{ rules_outcome.skill }} — {{ rules_outcome.directive }}

{%- elif rules_outcome and not rules_outcome.rolled -%}
## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.

{%- endif -%}
## pc
{{ pc.name }} — {{ pc.tagline }}
Stats: {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}
{% if conditions -%}
Conditions: {% for c in conditions %}{{ c.label if c is mapping else c }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
## location
`{{ location.id }}` | {{ location.name }}
{{ location.description }}

{% if present_npcs -%}
## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
{% for n in present_npcs %}- `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
{% endif -%}
{% if npc_roster -%}
<<<TRACE_IMMUTABLE_START>>>
## known_characters (compendium — reuse `id` for npc_add/npc_update/compendium_npc_update)
{% for n in npc_roster %}- `{{ n.id }}` | {{ n.name }} [{{ n.tags | join(",") }}]{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
<<<TRACE_IMMUTABLE_END>>>
{% endif -%}
{% if scene_pressure -%}
## scene_pressure (active threats — add/remove/update as fiction demands)
{% for p in scene_pressure %}- `{{ p.id }}` [{{ p.urgency }}] {{ p.text }} (added turn {{ p.turn_added }}){% if p.get('max_turns') %} max {{ p.max_turns }} turns{% endif %}
{% endfor %}
{% endif -%}
{% if deescalate -%}
## deescalate
true — player succeeded on a check against active pressure. Do NOT add new pressures. Downgrade or remove existing ones.
{% endif -%}
{% if quest_ages -%}
{% for qa in quest_ages %}{% if qa.stalled_turns >= 3%}
⚠ Quest "{{ qa.title }}" stalled for {{ qa.stalled_turns }} turns.
{% endif %}{% endfor %}
{% endif -%}
{% if active_quests -%}
## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
{% for q in active_quests %}- `{{ q.id }}` | {{ q.title }}
{% endfor %}
{% endif -%}
{% if recent_turns -%}
{% set prev = recent_turns[-1] if recent_turns | length >= 1 else none %}
{% if prev %}
## previous_turn_narration (T{{ prev.turn }} context)
{{ prev.narrative }}
{% endif %}
{% endif -%}
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

**Validation:** Template renders with the full context dict from `_extract_scene_messages` without missing variable errors.

---

#### Step 3.3 — Rewrite `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Remove field rules and schema entries for `compendium_npc_update`, `scene_pressure_*`, `gm_beat`, and de-escalation. Add field rules for `actions` and `outcome_summary` (ported from the old scene system prompt, with minor edits noting quest context is available).

**Code Snippet**
```jinja2
Extract quest updates, recent events, suggested player actions, and outcome summary from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## Output schema

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": ""
}
```

## Field rules

`quest_updates`: changes to quest state this turn.
- Update existing: `{"id": "quest_id", "status": "active|completed|failed|abandoned", "objectives": [{"index": N, "done": true}]}`. `index` is 1-based from the active_quests list shown in the user prompt.
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective.
- The engine auto-completes a quest when all objectives are done — do NOT emit `status: completed` for that case; just mark objectives done.
- New quest threshold guidance for this turn is in the user prompt.
- A quest is failed when the key objective(s) are failed, or are impossible to complete due to new information.
- A quest is abandoned when the player/narration implies they are giving up on it, gets too far away to continue, or it is no longer relevant.

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the quest, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or quest state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": 0}`.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current quest state. Structure: two choices should offer distinct avenues related to the current quest (if any), one should involve an NPC who is present in the scene, and one should be an exploration/environmental or freeform option. Weight toward quest objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices.

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

## Rules-outcome guidance (for objective resolution)
- crit_fail / fail / setback / partial: do NOT mark quest objectives done for the attempted action.
- success / crit_success: apply objective completions freely.
- No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states the objective is fulfilled. Ambiguous, partial, or conversational narration means the objective is NOT done.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.
```

**Validation:** Template renders without Jinja error when called with empty context.

---

#### Step 3.4 — Rewrite `extract_progress_user.j2`

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Remove the `scene_pressure` block and `known_characters` block. Add `recent_turns` (previous full narration, T-1 and T-2) and `intent` blocks. Keep all other blocks verbatim.

**Code Snippet**
```jinja2
## active_domains
{{ active_domains | join(", ") }}

{% if rules_outcome and rules_outcome.rolled -%}
## rules_outcome
{{ rules_outcome.band | upper }} on {{ rules_outcome.skill }}.

{%- elif rules_outcome and not rules_outcome.rolled -%}
## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.

{%- endif -%}
## pc
{{ pc.name }} — {{ pc.tagline }}

{% if intent and intent.intent -%}
## player_intent
{{ intent.intent_verb }}: {{ intent.intent }}
{% endif -%}

{% if "quest_updates" in active_domains -%}
## quest_threshold
{{ quest_threshold_directive }}

{% if active_quests -%}
## active_quests
{% for q in active_quests %}- `{{ q.id }}` | {{ q.title }}
  objectives:
{% for o in (q.objectives or []) %}    {{ loop.index }}. [{% if o.done %}x{% elif o.failed %}f{% else %} {% endif %}] {{ o.description }}
{% endfor %}{% endfor %}
{% endif -%}
{% for qa in quest_ages %}
{% if qa.stalled_turns >= 3%}
⚠ Quest "{{ qa.title }}" stalled for {{ qa.stalled_turns }} turns. Advance it, branch it, or mark an objective failed.
{% endif %}
{% endfor %}
{% endif -%}

{% if "recent_events" in active_domains -%}
{% if recent_events -%}
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
{% for event in recent_events %}- {{ event.text if event is mapping else event }}
{% endfor %}
{% endif -%}
{% if not active_quests and world_state -%}
<<<TRACE_IMMUTABLE_START>>>
## world_state (read-only — use to reason about new quests only)
{% for f in world_state %}- {{ f if f is string else f.values() | join(': ') }}
{% endfor %}
<<<TRACE_IMMUTABLE_END>>>
{% endif -%}
{% endif -%}

{% if recent_turns and recent_turns | length >= 2 -%}
## prior_turn_narration (T{{ recent_turns[-2].turn }} — for outcome_summary and actions context)
{{ recent_turns[-2].narrative }}

{% endif -%}
{% if state_result.items_gained -%}
## items_gained
{{ state_result.items_gained | join(', ') }}

{% endif -%}
{% if state_result.items_lost -%}
## items_lost
{{ state_result.items_lost | join(', ') }}

{% endif -%}
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

**Validation:** Template renders with full context dict from `_extract_progress_messages` without missing variable errors.

---

#### Step 3.5 — Strip `failed` from `extract_state_system.j2` and `extract_state_user.j2`

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Remove the `failed` entry from the output schema block and remove the `failed` field rule section entirely.

**File:** `ccya/prompts/extract_state_user.j2`

**What:** No change needed to the user template — `failed` was never rendered in the user prompt, only in the system schema.

**Code Snippet** (schema block in `extract_state_system.j2`, replace with):
```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

Also remove the `failed` field rule paragraph:
> `failed`: precondition failures this turn... *(entire paragraph deleted)*

**Validation:** State extractor LLM output no longer has a `failed` key. `StateExtractResult` model still parses correctly — `extra` fields are silently ignored by Pydantic (confirm `model_config` or that there is no `extra="forbid"`; if there is, add `model_config = {"extra": "ignore"}` to `StateExtractResult`).

---

### Tests to write or update

**File:** `tests/test_models.py` (create or extend)
```python
def test_scene_extract_result_has_pressure_fields():
    from ccya.models import SceneExtractResult
    r = SceneExtractResult()
    assert hasattr(r, "scene_pressure_add")
    assert hasattr(r, "compendium_npc_update")
    assert hasattr(r, "gm_beat")
    assert not hasattr(r, "actions")
    assert not hasattr(r, "outcome_summary")

def test_progress_extract_result_has_actions():
    from ccya.models import ProgressExtractResult
    r = ProgressExtractResult()
    assert hasattr(r, "actions")
    assert hasattr(r, "outcome_summary")
    assert not hasattr(r, "gm_beat")
    assert not hasattr(r, "scene_pressure_add")
    assert not hasattr(r, "compendium_npc_update")

def test_state_extract_result_no_failed():
    from ccya.models import StateExtractResult
    r = StateExtractResult()
    assert not hasattr(r, "failed")

def test_state_delta_merge_reads_from_scene_for_pressure():
    from ccya.models import SceneExtractResult, StateDelta, ScenePressure
    s = SceneExtractResult(
        scene_pressure_add=[ScenePressure(id="test", text="Guards incoming", urgency="immediate")]
    )
    delta = StateDelta(scene_pressure_add=s.scene_pressure_add)
    assert delta.scene_pressure_add.id == "test"
```

**File:** `tests/test_extraction.py` (create or extend)
```python
def test_run_extraction_pipeline_returns_actions_from_progress(mock_llm_env):
    # Use FakeLLM to return minimal valid JSON from all three streams.
    # Assert that the returned actions list comes from progress output, not scene.
    ...
```

### REPOMAP updates required
`docs/REPOMAP/extraction.md` — update the three-stream table to reflect new field ownership. Update `SceneExtractResult` row to include `compendium_npc_update`, `scene_pressure_*`, `gm_beat`. Update `ProgressExtractResult` row to include `actions`, `outcome_summary`. Remove `failed` from `StateExtractResult` row.

### Risks
1. **`extra="forbid"` on `StateExtractResult`** — if the LLM still emits a `failed` key, Pydantic will raise. Add `model_config = {"extra": "ignore"}` to `StateExtractResult` as a guard. Check before deploying.
2. **`_run_extraction_pipeline` return tuple arity change** — all callers unpack 6 values; changing to 7 (adding `scene_result`) breaks both call sites in `turn.py`. Both must be updated in lock-step in Step 2.5.
3. **Template context variables misspelled or missing** — any Jinja `UndefinedError` in production silently falls through to the retry path. Run `make test` against the template renders directly.

## Ambiguities requiring resolution before execution
None — all questions were resolved in pre-planning.

## TODO.md update
Under `## P1 — Active`:
Pipeline field routing remediation — docs/plans/eval-results-remediation/eval-results-remediation-pipeline-field-routing.md