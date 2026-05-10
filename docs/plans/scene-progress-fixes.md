# Scene Extractor Scope Reduction + Narrative Mechanics Consolidation

## Status
`open`

## Part of
standalone

## Dependencies
- All `eval-results-remediation/` phases (completed)
- `narrative-mechanics-overhaul.md` Phases 1–3 (completed)

## Objective
The scene extractor currently owns fields that belong to storytelling, not spatial context: `scene_pressure_update` and `scene_pressure_remove` were left in the scene stream after `scene_pressure_add` migrated to progress in the narrative mechanics overhaul. The result is split ownership of a single list — progress adds new pressures, scene updates and removes them — which creates ordering hazards and muddy prompt responsibility. This plan surgically completes the migration: scene extractor is reduced to exactly four concerns (NPC roster changes, location change, scene tags/tagline, location description), and progress extractor absorbs the two remaining pressure operations. Additionally, `scene_pressure_update` is constrained to update-only (no implicit add), and `gm_beat` gets an entity-grounding rule at the prompt level.

## Non-goals
- Does not change `scene_pressure_add` (already on progress, stays there).
- Does not change the `ScenePressure` data model or fields.
- Does not touch the state extractor (stream 2) at all.
- Does not move `gm_beat` between streams (it is already on progress).
- Does not add new storytelling mechanics (personality traits, factions, etc.).
- Does not change how pressures are applied to state in `turn.py` / `state.py`.
- Does not change the narrator pipeline.
- Does not change eval scenario content or rubric dimensions — only updates mechanic placement rows in the rubric.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Remove `scene_pressure_remove` and `scene_pressure_update` from `SceneExtractResult`; add both to `ProgressExtractResult` |
| `ccya/engine/extraction.py` | modify | Move `scene_pressure_remove` and `scene_pressure_update` merge sources from `scene_result` to `progress_result`; add update-only guard; remove `scene_pressure`, `deescalate`, `quest_ages`, `active_quests` from `_extract_scene_messages` context; add `scene_pressure` to `_extract_progress_messages` context |
| `ccya/prompts/extract_scene_system.j2` | modify | Strip all pressure remove/update instructions; rewrite system prompt to the four owned fields only |
| `ccya/prompts/extract_scene_user.j2` | modify | Remove `scene_pressure`, `deescalate`, `quest_ages`, `active_quests` context blocks; keep all other context (turn number, rules_outcome, pc, location, present_npcs, compendium, recent_turns, narration) |
| `ccya/prompts/extract_progress_system.j2` | modify | Add `scene_pressure_remove` and `scene_pressure_update` to JSON schema; add pressure remove + update field rules with explicit update-only guard; add gm_beat entity-grounding rule |
| `ccya/prompts/extract_progress_user.j2` | modify | Add `scene_pressure` context block (mirroring what scene had) |
| `docs/REPOMAP/extraction.md` | update | Reflect new stream ownership table |
| `docs/REPOMAP/models.md` | update | Reflect `SceneExtractResult` and `ProgressExtractResult` field changes |
| `docs/REPOMAP/prompts.md` | update | Reflect prompt changes |
| `evals/rubric/default.md` | modify | Update Mechanic Placement rows for scene and progress streams |
| `docs/plans/TODO.md` | modify | Add entry for this plan |

## Firm decisions

1. **Scene extractor owns exactly four things:** `npc_add`, `npc_remove`, `npc_update` + `compendium_npc_update` (NPC presence); `location_change` (movement); `scene_tags` + `scene_tagline` (scene classification); `location_description` (spatial detail). Nothing else.

2. **Progress extractor owns all pressure lifecycle:** `scene_pressure_add` (already there), `scene_pressure_remove` (migrating), `scene_pressure_update` (migrating). All three live on `ProgressExtractResult` after this plan.

3. **`scene_pressure_update` is update-only:** The prompt directive and the merge logic in `extraction.py` enforce that an `id` in `scene_pressure_update` must match an existing pressure in `state.scene.scene_pressure`. If it does not match, the update is silently dropped at merge time. This prevents the LLM from using `update` as a backdoor `add`.

4. **`gm_beat` gets an "existing-entity" guard at prompt level:** The system prompt instruction is tightened to require that `instruction` explicitly references an NPC id or pressure id already present in state. This is a prompt-level constraint only (no new Pydantic validator beyond the existing `_validate_instruction_quality` check), so it fails gracefully if the LLM ignores it rather than hard-erroring.

5. **`scene_pressure` context block moves with the operations:** The `scene_pressure` list currently fed to the scene extractor user prompt is removed from scene and added to the progress extractor user prompt. Progress already receives `world_state` and `recent_events`; pressure fits naturally alongside them.

6. **No new stream is created.** Three streams remain: scene (spatial), state (PC body), progress (narrative/story brain).

7. **`_extract_scene_messages` receives no `scene_pressure`, `deescalate`, `quest_ages`, or `active_quests` argument after this plan.** The function signature is simplified; removing this context reduces scene prompt size.

---

## Implementation — Phase 1: Model Changes

### Context files to load
- `ccya/models.py`

### Overview
Remove `scene_pressure_remove` and `scene_pressure_update` from `SceneExtractResult`. Add them to `ProgressExtractResult`. The update-only guard is enforced in `extraction.py` at merge time, not in the model itself.

### Detailed steps

#### Step 1.1 — Remove pressure fields from SceneExtractResult

**File:** `ccya/models.py`

**What:** Delete `scene_pressure_remove` and `scene_pressure_update` from `SceneExtractResult`.

**Why:** Scene extractor no longer owns pressure lifecycle. Leaving them on the model would allow the LLM to emit them and have them silently merge — which is the root of the split-ownership problem.

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
    # scene_pressure_remove and scene_pressure_update REMOVED — now on ProgressExtractResult

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

**Validation:** `grep -n "scene_pressure" ccya/models.py` should show zero hits inside `SceneExtractResult`. `make check` must pass.

---

#### Step 1.2 — Add pressure fields to ProgressExtractResult

**File:** `ccya/models.py`

**What:** Add `scene_pressure_remove: list[str]` and `scene_pressure_update: list[ScenePressure]` to `ProgressExtractResult`. These mirror the types that were on `SceneExtractResult`.

**Why:** Progress is now the single owner of all pressure lifecycle operations.

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
    beat_disposition: Literal["consume", "carry", "replace"] = "consume"
    scene_pressure_add: list[ScenePressure] = Field(default_factory=list)
    scene_pressure_remove: list[str] = Field(default_factory=list)       # migrated from SceneExtractResult
    scene_pressure_update: list[ScenePressure] = Field(default_factory=list)  # migrated from SceneExtractResult

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

**Validation:** `python -c "from ccya.models import ProgressExtractResult, SceneExtractResult; r = ProgressExtractResult(); assert hasattr(r, 'scene_pressure_remove'); s = SceneExtractResult(); assert not hasattr(s, 'scene_pressure_remove')"` must pass without error.

---

### Tests to write or update

**File:** `tests/test_models.py` (create if absent, else append)

```python
def test_scene_extract_result_has_no_pressure_lifecycle():
    """SceneExtractResult must not expose pressure remove/update."""
    from ccya.models import SceneExtractResult
    r = SceneExtractResult()
    assert not hasattr(r, "scene_pressure_remove")
    assert not hasattr(r, "scene_pressure_update")


def test_progress_extract_result_has_pressure_lifecycle():
    """ProgressExtractResult must expose all three pressure operations."""
    from ccya.models import ProgressExtractResult
    r = ProgressExtractResult()
    assert hasattr(r, "scene_pressure_add")
    assert hasattr(r, "scene_pressure_remove")
    assert hasattr(r, "scene_pressure_update")
    assert r.scene_pressure_remove == []
    assert r.scene_pressure_update == []
```

### REPOMAP updates required
- `docs/REPOMAP/models.md` — Update `SceneExtractResult` field table: remove `scene_pressure_remove`, `scene_pressure_update`. Update `ProgressExtractResult` field table: add both fields.

### Risks
1. Any test that constructs a `SceneExtractResult` with `scene_pressure_remove` or `scene_pressure_update` will break — **mitigation:** grep for usages before committing: `grep -rn "scene_pressure_remove\|scene_pressure_update" tests/`.
2. `StateDelta` still has both fields; the merge in `extraction.py` (fixed in Phase 2) must be updated atomically with this model change or the pipeline will crash — **mitigation:** commit Phases 1 and 2 together.

---

## Implementation — Phase 2: Extraction Pipeline Rewiring

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/models.py` (post Phase 1)

### Overview
Update `_run_extraction_pipeline` to source `scene_pressure_remove` and `scene_pressure_update` from `progress_result` instead of `scene_result`. Remove `scene_pressure`, `deescalate`, `quest_ages`, and `active_quests` from the context dict passed to `_extract_scene_messages`. Add `scene_pressure` to the context dict passed to `_extract_progress_messages`. Add the update-only guard: any `scene_pressure_update` entry whose `id` is not present in the current state pressure list is dropped before merge.

### Detailed steps

#### Step 2.1 — Remove pressure/quest context from scene message builder

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_scene_messages`:
- Remove `scene_pressure`, `deescalate`, `quest_ages`, `active_quests`, and `scene_location_description` from the kwargs dict passed to `_render(env, "extract_scene_user.j2", {...})`.
- Remove `deescalate`, `quest_ages` from the function signature.
- Remove `scene_pressure` and `active_quests` from the function's local variables.
- Update the docstring.

**Why:** The scene extractor no longer needs pressure context, deescalation hints, quest age warnings, or quest lists. Removing them reduces prompt size and eliminates the risk of the LLM emitting pressure ops just because they appear in context.

**Verification note:** `deescalate` and `quest_ages` appear in the scene user template only in the pressure-related blocks (lines 39-47 of `extract_scene_user.j2`). `active_quests` appears only in a block labeled "for gm_beat context only" (line 49). None of these are used for NPC/location/tag logic. All can be safely removed.

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
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence, location, tags)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=False)
    npc_roster = _scene_npc_roster(known_characters)
    present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

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
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**Validation:** `grep -n "scene_pressure\|deescalate\|quest_ages\|active_quests" ccya/engine/extraction.py` — should appear only in the merge block, in `_extract_progress_messages`, and in `_run_extraction_pipeline` call sites (for progress), not in `_extract_scene_messages`.

---

#### Step 2.2 — Add scene_pressure context to progress message builder

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_progress_messages`, add `scene_pressure` (the current list from state) to the kwargs dict passed to `_render(env, "extract_progress_user.j2", {...})`.

**Why:** Progress extractor now owns remove and update; it needs to know what pressures currently exist to reason about them.

**Code Snippet**
```python
# Inside _extract_progress_messages, in the _render call for extract_progress_user.j2:
# Add this key to the existing dict:
"scene_pressure": list((state.get("scene") or {}).get("scene_pressure") or []),
```

Full updated render call (only the additions shown for brevity; all existing keys remain):
```python
user_text = _render(
    env,
    "extract_progress_user.j2",
    {
        "narration": narration,
        "pc": pc,
        "active_quests": active_quests,
        "recent_events": recent_events,
        "world_state": world_state,
        "scene_pressure": list((state.get("scene") or {}).get("scene_pressure") or []),  # NEW
        "state_result": state_ctx,
        "rules_outcome": rules_outcome,
        "active_domains": active_domains,
        "quest_threshold_directive": _quest_threshold_directive(active_quests),
        "intent": intent,
        "deescalate": deescalate,
        "quest_ages": quest_ages,
        "recent_turns": recent_turns or [],
        "turn_no": turn_no,
        "stakes": stakes,
        "band": band,
        "pending_beat": pending_beat,
    },
)
```

**Validation:** Run one eval turn and confirm the `scene_pressure` block appears in the progress user prompt output.

---

#### Step 2.3 — Rewire the merge block

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, update the `StateDelta(...)` constructor call to source `scene_pressure_remove` and `scene_pressure_update` from `progress_result` instead of `scene_result`. Add the update-only guard before merge.

**Why:** The merge block is the authoritative point where all stream outputs combine. This is where the update-only invariant is cheapest to enforce — one filter in Python, no LLM involvement.

**Code Snippet**
```python
# --- Update-only guard: drop any scene_pressure_update whose id is not in current state ---
existing_pressure_ids: set[str] = {
    p.get("id", "") for p in (state.get("scene") or {}).get("scene_pressure") or []
    if isinstance(p, dict)
}

validated_pressure_update: list[ScenePressure] = []
for pu in (progress_result.scene_pressure_update or []):
    pid = pu.id if hasattr(pu, "id") else (pu.get("id") if isinstance(pu, dict) else None)
    if pid and pid in existing_pressure_ids:
        validated_pressure_update.append(pu)
    else:
        _log.debug(
            "extraction.pressure_update: dropped id=%r — not in existing pressures",
            pid,
            extra={"turn": turn_no, "trace_id": trace_id},
        )

# --- Merge into single StateDelta ---
merged = StateDelta(
    scene_tags=scene_result.scene_tags,
    scene_tagline=scene_result.scene_tagline,
    location_change=scene_result.location_change,
    location_description=scene_result.location_description,
    npc_add=scene_result.npc_add,
    npc_remove=scene_result.npc_remove,
    npc_update=scene_result.npc_update,
    compendium_npc_update=scene_result.compendium_npc_update,
    scene_pressure_add=progress_result.scene_pressure_add,
    scene_pressure_remove=progress_result.scene_pressure_remove,   # migrated
    scene_pressure_update=validated_pressure_update,                # migrated + guarded
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
```

**Validation:** Run `make test`. Confirm no references to `scene_result.scene_pressure_remove` or `scene_result.scene_pressure_update` remain in the file after this edit.

---

#### Step 2.4 — Update the call site for _extract_scene_messages in _run_extraction_pipeline

**File:** `ccya/engine/extraction.py`

**What:** Remove `deescalate`, `quest_ages` kwargs from the `_extract_scene_messages` call. Only pass what the updated function accepts.

**Why:** Caller must match signature. Extraneous kwargs will raise a TypeError at runtime.

**Code Snippet**
```python
scene_msgs = _extract_scene_messages(
    env, narration, state,
    active_domains=active_domains,
    rules_outcome=rules_outcome,
    enable_thinking=config.enable_extract_thinking,
    recent_turns=(recent_turns or [])[-1:],
    turn_no=turn_no,
)
```

**Validation:** `python -c "import ccya.engine.extraction"` must not raise. `make check` must pass.

---

### Tests to write or update

**File:** `tests/test_extraction_pipeline.py` (new or existing)

```python
def test_pressure_update_guard_drops_unknown_id(monkeypatch):
    """scene_pressure_update entries with unknown ids must be silently dropped before merge."""
    # This test verifies the guard in _run_extraction_pipeline using FakeLLM
    # that returns a ProgressExtractResult with a scene_pressure_update referencing
    # a non-existent id. The merged StateDelta.scene_pressure_update must be empty.
    # See existing FakeLLM pattern in tests/test_engine_pipeline.py for setup.
    pass  # Implement using FakeLLM pattern from docs/REPOMAP/testing.md


def test_pressure_update_guard_passes_known_id(monkeypatch):
    """scene_pressure_update entries with known ids must pass through to StateDelta."""
    pass  # Implement using FakeLLM pattern
```

### REPOMAP updates required
- `docs/REPOMAP/extraction.md` — Update stream ownership table: scene stream loses pressure_remove/update; progress stream gains them. Update `_extract_scene_messages` signature docs. Update `_run_extraction_pipeline` return description.

### Risks
1. Removing scene_pressure from scene context may cause the scene LLM to hallucinate pressure ops if it has seen examples in training data. **Mitigation:** The system prompt (Phase 3) explicitly forbids it.

---

## Implementation — Phase 3: Prompt Changes

### Context files to load
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`

### Overview
Rewrite the scene extractor prompts to the four-field scope. Add pressure remove + update instructions to the progress extractor prompts. Add the update-only guard to the progress system prompt and the gm_beat existing-entity guard.

### Detailed steps

#### Step 3.1 — Rewrite extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the system prompt with a scoped version that explicitly names only the four owned responsibilities. Remove all pressure-related instructions. Be explicit that this extractor does NOT emit pressure fields.

**Why:** LLMs follow the system prompt. If the system prompt names a field, the LLM will try to populate it. Scoping the system prompt is the primary control surface.

**Code Snippet**
```jinja2
You are the Scene Extractor. Your only job is to read the narration and output a JSON object
describing four things:

1. **NPC presence** — which named characters entered or left the scene, and any update to how
   they are currently behaving toward the player.
2. **Location change** — did the player move to a new place? Only emit `location_change` if the
   location ID changes. Spatial detail within the same room is NOT a location change.
3. **Scene classification** — `scene_tags` (mood/genre descriptors, up to 5) and `scene_tagline`
   (3–6 words for the UI header).
4. **Location description** — new spatial detail about the current space. Only emit this when the
   narration introduces genuinely new physical details not already in the stored description.
   Do not restate or paraphrase existing description.

You do NOT handle: inventory, conditions, quests, recent events, scene pressure, gm beats,
world state, or any other field. If you emit `scene_pressure_add`, `scene_pressure_remove`,
or `scene_pressure_update`, they will be silently discarded. Do not emit them.

Output a single JSON object matching the SceneExtractResult schema. No prose outside <thinking>.
```

**Validation:** After deploying, run one eval turn and confirm `scene_result.scene_pressure_remove` and `scene_result.scene_pressure_update` are absent from the logged output (they will be, since they're removed from the model — but the prompt should produce no spurious keys either, confirmed via `extra="ignore"` or by checking raw JSON in log).

---

#### Step 3.2 — Remove pressure/quest blocks from extract_scene_user.j2

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Remove exactly four blocks from the template (lines 34-52):
- `scene_pressure` block (lines 34-38)
- `deescalate` block (lines 39-42)
- `quest_ages` block (lines 43-47)
- `active_quests` block (lines 48-52)

Keep everything else: turn number, rules_outcome, pc (name/tagline/stats/conditions), location, present_npcs, known_characters (compendium), current_location_description, recent_turns, narration.

**Why:** Context that is not relevant to the extractor's job increases noise and token cost. The scene extractor only needs spatial/NPC data.

**Code Snippet** — Remove these lines (34-52):
```jinja2
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
```

**Validation:** `grep -n "scene_pressure\|deescalate\|quest_ages\|active_quests" ccya/prompts/extract_scene_user.j2` should return nothing.

---

#### Step 3.3 — Update extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Two changes:
1. **Update the JSON schema block** (lines 6-16) to add `scene_pressure_remove` and `scene_pressure_update` fields.
2. **Append new field rules** after the existing `scene_pressure_add` rule (after line 59): pressure remove/update rules with update-only guard, and gm_beat entity-grounding rule.

**Why:** The schema must match the model. The field rules must tell the LLM how to use the new fields.

**Code Snippet — Schema update (replace lines 6-16):**
```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

**Code Snippet — Append after line 59 (after `scene_pressure_add` rule):**
```jinja2
`scene_pressure_remove`: IDs of pressures now resolved. Emit the id string in the list.

`scene_pressure_update`: Change the text or urgency of an EXISTING pressure. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.
**RULE: update-only.** Every `id` you emit MUST match an id in the `## Current Pressures` list provided in the user prompt. Do not invent new pressure ids here. If you need a new pressure, use `scene_pressure_add` instead.

## GM Beat Grounding Rule

`gm_beat.instruction` must reference a specific named entity already present in state:
an NPC id from the Present NPCs list, or a pressure id from the Current Pressures list.
Do not invent new characters or situations in `gm_beat`. A beat that references no existing
entity will be nullified by the engine.
```

**Validation:** After deploying, run `make eval` and check that the judge no longer flags generic gm_beat instructions that reference invented entities.

---

#### Step 3.4 — Add pressure context block to extract_progress_user.j2

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add a `## Current Pressures` block that renders the `scene_pressure` list. Place it after the `## quest_ages` block (line 104) and before `## CURRENT TURN NARRATION` (line 105).

**Why:** The update-only guard in extraction.py drops entries with unknown ids, but a well-prompted LLM will reference the correct ids if we provide them. Without this block, the LLM has no way to know what pressures exist.

**Code Snippet** — Insert after line 104 (after `{%- endif %}` of quest_ages block):
```jinja2
{% if scene_pressure -%}
## Current Pressures
{% for p in scene_pressure %}- [{{ p.id }}] ({{ p.urgency }}) {{ p.text }}
{% endfor %}
{% endif -%}
```

**Validation:** Render the template and confirm the `Current Pressures` block appears in the user prompt. Run one eval turn with an active pressure; confirm the progress result can correctly emit `scene_pressure_remove` with the right id.

---

### Tests to write or update

No new test files needed for prompts. Prompt correctness is validated via eval run (`make eval`) and the auto-checker assertions.

Update any existing test that constructs a `SceneExtractResult` with pressure fields:

```bash
grep -rn "scene_pressure_remove\|scene_pressure_update" tests/
```

For each hit: if it's testing that scene extractor emits pressure ops, delete the test (the behavior is removed). If it's testing the merge, update it to source from `ProgressExtractResult`.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md` — Update `extract_scene_system.j2` and `extract_scene_user.j2` descriptions to reflect reduced scope. Add `scene_pressure` block to `extract_progress_user.j2` entry.

### Risks
1. The progress extractor already has a long system prompt. Adding pressure lifecycle instructions may push the system prompt size over a token budget threshold. **Mitigation:** Check `context_meta.system_chars` in the eval trace after deploying; if it exceeds budget, compress the existing progress system prompt prose.
2. The gm_beat grounding rule is prompt-only. A model that ignores it will still pass Pydantic validation. **Mitigation:** The existing `_validate_instruction_quality` validator catches blank/generic beats. The judge rubric (Phase 4) adds an explicit check.

---

## Implementation — Phase 4: Rubric Update

### Context files to load
- `evals/rubric/default.md`

### Overview
Update the Mechanic Placement subsection of the rubric to reflect the new stream ownership. This is a documentation change only — no code changes.

### Detailed steps

#### Step 4.1 — Update Mechanic Placement table in rubric

**File:** `evals/rubric/default.md`

**What:** Find the Mechanic Placement subsection (inside the Mechanical Design Critique section). Update the scene stream row to remove pressure_remove/pressure_update. Update the progress stream row to add them. Add a note that `scene_pressure_update` must only reference existing ids.

**Why:** The eval judge reads the rubric. If the rubric still says scene extractor owns pressure_remove, the judge will penalize the (now correct) system for not emitting it from scene.

**Code Snippet**
```markdown
### Mechanic Placement

| Field | Correct stream | Violation if seen in wrong stream |
|---|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene | — |
| `location_change`, `location_description` | scene | — |
| `scene_tags`, `scene_tagline` | scene | — |
| `inventory_add`, `inventory_remove`, `inventory_update` | state | — |
| `pc_condition_add`, `pc_condition_remove` | state | — |
| `quest_updates` | progress | — |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress | — |
| `scene_pressure_add` | progress | Flag if emitted by scene |
| `scene_pressure_remove` | progress | Flag if emitted by scene |
| `scene_pressure_update` | progress | Flag if emitted by scene; also flag if id not in existing pressure list |
| `gm_beat` | progress (via meta) | — |
| `actions`, `outcome_summary` | progress | — |
```

**Validation:** Re-run `make eval` and confirm the judge no longer flags the system for pressure placement. Score in the Mechanic Placement dimension should improve.

---

### Tests to write or update
None — rubric changes are prose, not code.

### REPOMAP updates required
None for this phase.

### Risks
1. The rubric uses `make eval` which is an LLM-based judge — results vary per run. **Mitigation:** Run eval twice and check both REPORT.md files for consistency.

---

## TODO.md update

Add under **Standalone** section:

```
- [ ] **Scene extractor scope reduction + narrative consolidation** — scene stream scoped to NPC presence, location change, scene tags/tagline, location_description only; pressure remove/update migrated to progress; update-only guard on scene_pressure_update; gm_beat entity-grounding rule — see [`scene-progress-fixes.md`](scene-progress-fixes.md)
```
