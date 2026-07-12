# Consolidate Scene/Location Extraction into State Stream — Implementation Plan

## Purpose

Translate the design decisions from `docs/design/consolidate-scene-location-extraction-design.md` into ordered, independently executable implementation phases for an executor with no prior context.

## Problem Statement

The Scene extractor produces three categories of output (location state, session identity, NPC compendium updates) — two of which are state-management concerns that belong in the State extractor. The `notes` NPC field overlaps with `position`. `scene_tagline` is regenerated every turn but consumed only by the UI. This split inflates the Scene extractor's system prompt and forces the LLM to evaluate location/tagline/notes on every turn despite them being state-level or redundant concerns.

## Constraints

- Pipeline stages must remain parallelizable (Steps 2a-2c run concurrently).
- No backwards compatibility or migration. Fresh seed only.
- The name "scene extractor" stays in code and docs.
- All decisions in the design doc are final.

## Non-goals

- Changing the narrator or storyteller system prompts.
- Adding or removing LLM calls.
- Restructuring pipeline step numbering.
- Changing `pc.tagline`.

## Solution

Six sequential phases, each independently verifiable: (1) update extraction models, (2) update prompt templates and boundary models, (3) update pipeline wiring, (4) update state layer, (5) update surface code (UI, seed, tv), (6) update documentation. Each phase has a zero-fix validation step before the next begins.

## Firm decisions

1. `location_change` and `location_description` move from `SceneExtractResult` to `StateExtractResult`.
2. `scene_tagline` is removed from all extraction. Replaced by static `state.meta.session_name`, set once at seed generation.
3. `notes` is removed from `CompendiumNpcUpdate` with no replacement.
4. `position` instructions expand to cover spatial + stance. Clearing moves from turn-start to presence transitions (`known`/`departed`).
5. `location_description` emitted only on tangible environment change (LLM judges from current description + narration).
6. No migration. `state.scene.tagline` and `state.meta.game_name` are deleted.
7. Fallback UI string: "Choose Your Own Adventure".

## Risks, Ambiguities, and Blockers

- Models phase must complete before any other phase can begin (everything imports from `extraction.py`).
- Prompts and pipeline can land in any order after models, but both must land before state layer (state layer processes the deltas produced by pipeline).
- The state extractor's ability to judge "tangible change" with one-turn narration context is unvalidated. Marked as risk in design.

## Status

`completed`

## Phases

6 phases: models → prompts → pipeline wiring → state layer → surface code → documentation

## Implementation — Phase 1: Extraction Models

### Context files to load

- `ccya/models/extraction.py` — all extraction models
- `ccya/models/state.py` — `LocationRef` (verify it still exists and has expected shape)

### Detailed steps

#### Step 1.1 — Remove `scene_tagline`, `location_change`, `location_description` from `SceneExtractResult`

**File:** `ccya/models/extraction.py` lines 122–139

**What:** Strip `SceneExtractResult` to a single field: `compendium_npc_update`. Remove `scene_tagline`, `location_change`, `location_description` (lines 122–125). Remove the `location_description` validator and its `@field_validator` decorator (lines 130–139).

```python
class SceneExtractResult(BaseModel):
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
```

**Why:** Scene extractor becomes pure NPC. Location/session outputs move to `StateExtractResult`.

**Validation:** `import` the module, instantiate `SceneExtractResult()` with no args, confirm no validation errors.

#### Step 1.2 — Add `location_change` and `location_description` to `StateExtractResult`

**File:** `ccya/models/extraction.py` lines 142–163

**What:** Add two optional fields to `StateExtractResult`. Add a `location_description` validator (same logic as the one removed from `SceneExtractResult` — coerces dict → str, passthrough str, returns None on falsy).

```python
class StateExtractResult(BaseModel):
    location_change: LocationRef | None = None
    location_description: str | None = None
    condition_change_reason: str = ""
    # ... existing fields unchanged ...
```

**Why:** State extractor now owns all state-level deltas (inventory, conditions, location).

**Validation:** Instantiate `StateExtractResult(location_change={"id": "test", "name": "Test"})`, confirm `LocationRef` is parsed. Instantiate with `location_description="a test"` and with `location_description={"description": "nested"}`, verify both produce the same string.

#### Step 1.3 — Remove `notes` from `CompendiumNpcUpdate`

**File:** `ccya/models/extraction.py` lines 18–34

**What:** Delete the `notes: str | None = None` field line (line 28) from `CompendiumNpcUpdate`.

**Why:** Notes is redundant with `position`. Eliminating it removes the prompt ambiguity between the two fields.

**Validation:** Instantiate `CompendiumNpcUpdate(id="test")`, confirm it has no `notes` field. Instantiate with `notes="test"` and confirm Pydantic rejects the extra field (or silently ignores depending on `model_config` — verify behavior).

#### Step 1.4 — Remove `scene_tagline` from `StateDelta`

**File:** `ccya/models/extraction.py` lines 86–109

**What:** Delete the `scene_tagline: str | None` field (lines 102–104). Keep `location_change` and `location_description`.

**Why:** No extraction stream produces `scene_tagline` anymore. It's replaced by static `state.meta.session_name` set at seed time.

**Validation:** Instantiate `StateDelta()`, confirm no `scene_tagline` field. Confirm `location_change` and `location_description` still exist.

### Tests to write or update

No tests (tests are temporarily removed per AGENTS.md). Validate by running `make check` at phase end.

#### Step 1.5 — Remove `tagline` from `SeedScene`, add `session_name` handling

**File:** `ccya/pack.py` lines 54–58

**What:** Remove `tagline: str = ""` from `SeedScene`. The `session_name` lives in `SeedState.meta` (which is `dict[str, Any]`, so no explicit field needed — any key-value from the JSON `meta` block is accepted automatically).

```python
class SeedScene(BaseModel):
    tags: list[str] = Field(default_factory=list)
    world_state: list[WorldStateFact | str] = Field(default_factory=list)
```

**Why:** `session_name` replaces `tagline` and lives in `meta`. `SeedScene.tagline` is a dead field.

**Validation:** Instantiate `SeedScene()` without `tagline`. Confirm it builds. Instantiate `SeedState(meta={"session_name": "Test"}, pc=..., location=..., scene=SeedScene())` and confirm `meta["session_name"]` is accessible.

---

## Implementation — Phase 2: Prompt Templates + Boundary Models

### Context files to load

- `ccya/prompts/extract_scene_system.j2` — full file (169 lines)
- `ccya/prompts/extract_scene_user.j2` — full file (16 lines)
- `ccya/prompts/extract_state_system.j2` — full file (125 lines)
- `ccya/prompts/extract_state_user.j2` — full file (12 lines)
- `ccya/prompts/sections/_npc_roster.j2` — full file (14 lines)
- `ccya/prompts/generate_seed_system.j2` — schema section (~line 35)
- `ccya/prompts/context.py` lines 250–276 — SceneExtractBoundary and StateExtractBoundary
- `ccya/prompts/context.py` lines 324–331 — TEMPLATE_CONTRACTS (verify no change needed)

### Detailed steps

#### Step 2.1 — Remove location/tagline/notes from `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Remove `scene_tagline`, `location_change`, `location_description` from the output schema (JSON block, ~lines 9–16). Remove field rules for `scene_tagline` (~line 20), `location_change` (~line 22), `location_description` (~line 24). Remove `notes` from the `compendium_npc_update` sub-schema (~line 41) and from all example/instructor references to `notes` (~lines 103–108, "Correct notes extraction" and "Incorrect notes extraction" examples). Expand the `position` field rule:

- Old (line 42): "Where the NPC is in the scene. One short phrase. Only update when narration moves the NPC or implies movement."
- New: "Where the NPC is in the scene and what they are doing. One short phrase. Include spatial barriers and visibility constraints (e.g., 'behind a door, not visible', 'across the bar, watching', 'standing in the doorway blocking exit', 'at the player's elbow, whispering'). Update when narration changes the NPC's position or stance."

Remove the "notes" examples block (lines 103–111: "Correct notes extraction", "Incorrect notes extraction", "Maximum 8 words for notes").

**Why:** Scene extractor is pure NPC now. No location/session/tagline outputs. Notes removed. Position expanded.

**Validation:** Render the template with an empty context dict (current behavior — zero dynamic vars). Confirm the word "notes" does not appear in the output. Confirm "position" appears with the new expanded instruction.

#### Step 2.2 — Remove location from `extract_scene_user.j2`

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Remove the `## location` section (lines 1–3). `location` is no longer passed to the scene extractor.

**Why:** Scene extractor doesn't need spatial state context — it manages NPCs from narration alone.

**Validation:** Render the template with `narration`, `npc_roster`, `pc_name`, `turn_no`. Confirm `location` does not appear in output.

#### Step 2.3 — Add location section to `extract_state_user.j2`

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Add a `## Location` section after the `## Player Character` line, mirroring `_location.j2` style:

```
## Location
{{ location.id }} | {{ location.name }}
{{ location.description }}
```

**Why:** State extractor needs the current location description to determine whether the environment has changed.

**Validation:** Render the template with a `location` dict. Confirm the section appears.

#### Step 2.4 — Add location rules to `extract_state_system.j2`

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add `location_change` and `location_description` to the output schema (JSON block, lines 61–70). Add field rules after the existing inventory/condition rules:

- `location_change`: emitted ONLY when the location ID changes. Schema: `{"id": "snake_case", "name": "Display Name", "description": "Stable short description (1 sentence)"}`. Same behavior as the current scene extractor rules for this field.
- `location_description`: emitted ONLY when the physical environment has materially changed — structural damage, new obstacles, light/shift changes, new interactable features. 1-2 sentences. Must describe new tangible details or potential opportunities NOT present in the narration. Do NOT repeat narration. Emit nothing if the environment is unchanged from its current description. The current location description is shown in the user prompt for reference.

**Why:** State extractor now owns location state deltas.

**Validation:** Render the template. Confirm `location_change` and `location_description` appear in the output schema and field rules.

#### Step 2.5 — Remove `notes` rendering from `_npc_roster.j2`

**File:** `ccya/prompts/sections/_npc_roster.j2` line 8

**What:** Remove `{%- if n.notes %} | {{ n.notes }}{% endif %}` from the rendering line. Keep `{% if n.position %} | {{ n.position }}{% endif %}`.

**Why:** Notes field no longer exists. Position covers both spatial and stance.

**Validation:** Render the template with an NPC roster. Confirm no `| None` or empty pipe appears where notes was.

#### Step 2.6 — Update `SceneExtractBoundary` in `context.py`

**File:** `ccya/prompts/context.py` lines 250–261

**What:** Remove `location: LocationBlock` from `SceneExtractBoundary` fields.

```python
class SceneExtractBoundary(BaseModel):
    narration: str
    npc_roster: list[NPCRosterEntryBlock]
    pc_name: str = "Unnamed"
    turn_no: int
```

**Why:** Scene extractor user prompt no longer receives location.

**Validation:** Instantiate the boundary without `location`. Confirm it builds.

#### Step 2.7 — Add `location` to `StateExtractBoundary` in `context.py`

**File:** `ccya/prompts/context.py` lines 264–276

**What:** Add `location: LocationBlock` field.

```python
class StateExtractBoundary(BaseModel):
    conditions: list[Condition]
    inventory: list[InventoryItem]
    location: LocationBlock
    intent: IntentEnvelope | None = None
    turn_no: int
    narration: str
```

**Why:** State extractor user prompt now receives location context.

**Validation:** Instantiate the boundary with a `LocationBlock`. Confirm it builds.

#### Step 2.8 — Rename `scene.tagline` to `session_name` in seed generation schema

**File:** `ccya/prompts/generate_seed_system.j2` line ~35

**What:** Change `scene: {tagline: string, ...}` to `meta: {session_name: string, ...}` in the seed_state schema. The instruction changes from "3–6 words describing location/situation" to "A short, evocative title for this game session (3-6 words). Should capture the campaign's tone and setting without describing a specific scene or character. This name defines the entire playthrough."

Remove the `scene.tagline` reference from the schema block. Add `session_name` under `meta`.

**Why:** `session_name` is a game-level title, not a scene description. Belongs in `meta`.

**Validation:** Render the template with typical seed context. Confirm `session_name` appears under `meta` schema, not `scene`.

### Tests to write or update

No tests (temporarily removed). Validate by rendering each template with sample data and inspecting output.

---

## Implementation — Phase 3: Pipeline Wiring

### Context files to load

- `ccya/engine/extraction/scene.py` — full file (41 lines)
- `ccya/engine/extraction/state.py` — full file (40 lines)
- `ccya/engine/extraction/pipeline.py` lines 287–293 — merge block
- `ccya/engine/extraction/context.py` lines 34–72 — `_build_extraction_context()`
- `ccya/models/extraction.py` — verify new model shapes

### Detailed steps

#### Step 3.1 — Remove `location` from scene extractor context

**File:** `ccya/engine/extraction/scene.py` lines 21–35

**What:** Remove the `location = state.get("location") or {}` line (line 21). Remove `"location": location` from the user template context dict (line 31).

**Why:** Scene extractor no longer receives location context.

**Validation:** Call `_extract_scene_messages()` with a mock state that has no location key. Confirm no KeyError. Confirm user message content does not contain "## Location".

#### Step 3.2 — Add `location` to state extractor context

**File:** `ccya/engine/extraction/state.py` lines 21–34

**What:** Add a `location = state.get("location") or {}` line after `pc = state.get("pc") or {}` (line 21). Add `"location": location` to the user template context dict.

**Why:** State extractor needs the current location description to determine whether the environment has changed.

**Validation:** Call `_extract_state_messages()` with a mock state that has a `location` dict. Confirm user message content contains "## Location".

#### Step 3.3 — Update pipeline merge block

**File:** `ccya/engine/extraction/pipeline.py` lines 287–293

**What:** Change the `StateDelta` merge to read `location_change` and `location_description` from `state_result` instead of `scene_result`. Remove `scene_tagline=scene_result.scene_tagline` from the merge dict.

```python
merged = StateDelta(
    compendium_npc_update=scene_result.compendium_npc_update,
    location_change=state_result.location_change,
    location_description=state_result.location_description,
    inventory_change_reason=state_result.inventory_change_reason,
    condition_change_reason=state_result.condition_change_reason,
    inventory_add=state_result.inventory_add,
    inventory_remove=state_result.inventory_remove,
    inventory_update=state_result.inventory_update,
    pc_condition_add=state_result.pc_condition_add,
    pc_condition_remove=state_result.pc_condition_remove,
    actions=storytell_result.actions or [],
)
```

**Why:** The state extractor now produces location deltas. The scene extractor no longer does.

**Validation:** Run the pipeline with mock LLM responses. Confirm `StateDelta.location_change` and `StateDelta.location_description` are populated from state extractor output, not scene extractor output.

#### Step 3.4 — Update `_build_extraction_context()` source field

**File:** `ccya/engine/extraction/context.py` lines 64–65

**What:** Two changes in the `_build_extraction_context()` function:

1. **Line 50** — Change `location_change=scene_result.location_change` to `location_change=state_result.location_change` in the `combined_delta` construction. After Phase 1, `scene_result` no longer has a `location_change` field.

2. **Lines 64–65** — Change `scene_result.location_description` to `state_result.location_description` in the `location_this_turn` override.

```python
combined_delta = StateDelta(
    compendium_npc_update=list(scene_result.compendium_npc_update or []),
    location_change=state_result.location_change,          # <-- changed
    inventory_add=list(state_result.inventory_add or []),
    # ... rest unchanged ...
)

# ...

if state_result.location_description:                      # <-- changed
    location_this_turn["description"] = state_result.location_description
```

**Why:** Both `location_change` and `location_description` now come from Step 2b (state extractor), not Step 2a (scene extractor).

**Validation:** Call `_build_extraction_context()` with a `state_result` that has `location_change` and `location_description` set and `scene_result` that has neither. Confirm the returned context has both the location id/name from the change and the description from the state result.

### Tests to write or update

No tests. Validate by running `make check`.

---

## Implementation — Phase 4: State Layer

### Context files to load

- `ccya/state/io.py` lines 65–110 — `_default_state()` and surrounding structure
- `ccya/state/delta_builder.py` lines 272–282 — scene_tagline write and NPC management call
- `ccya/state/npcs.py` lines 172–182 — `strip_npcs_notes()`
- `ccya/state/npcs.py` lines 314–332 — presence transition logic (notes clearing lines)

### Detailed steps

#### Step 4.1 — Update `_default_state()` shape

**File:** `ccya/state/io.py` lines 90–103

**What:** Add `"session_name": ""` under `"meta"` (line 69 area). Remove `"game_name": "default"` from meta. Remove `"tagline": ""` from the scene dict (line 103).

```python
"meta": {
    "turn": 0,
    "setting_pack": "",
    "model": "",
    "session_name": "",
    "compendium_touch_order": [],
    "prior_history": [],
    # "game_name" deleted
},
# ...
"scene": {
    "tags": [],
    "world_state": [],
    # "tagline" deleted
    "turn_entered": 0,
},
```

**Why:** `session_name` replaces `tagline` in meta. `game_name` was dead.

**Validation:** Call `_default_state()` and inspect the returned dict. Confirm `meta.session_name` exists and is `""`. Confirm `meta.game_name` does not exist. Confirm `scene.tagline` does not exist.

#### Step 4.2 — Remove `scene_tagline` write from `apply_delta()`

**File:** `ccya/state/delta_builder.py` lines 272–273

**What:** Delete lines 272–273 (`if delta.scene_tagline is not None: state.setdefault("scene", {})["tagline"] = ...`).

**Why:** No extraction stream produces `scene_tagline` anymore.

**Validation:** Call `apply_delta()` with a StateDelta that has `scene_tagline` omitted (it no longer exists on the model). Confirm no KeyError. Confirm state dict has no `scene.tagline` key.

#### Step 4.3 — Update NPC management call in `apply_delta()`

**File:** `ccya/state/delta_builder.py` lines 277–282

**What:** Change the `SceneExtractResult(...)` construction to only pass `compendium_npc_update`, since `scene_tagline`, `location_change`, and `location_description` no longer exist on `SceneExtractResult`.

```python
state = apply_npc_scene_management(state, SceneExtractResult(
    compendium_npc_update=delta.compendium_npc_update or [],
), current_turn_no=current_turn, trace_id=trace_id)
```

**Why:** `SceneExtractResult` is now single-field.

**Validation:** Call `apply_delta()` with a StateDelta that has `compendium_npc_update`. Confirm NPC management runs without error.

#### Step 4.4 — Remove `strip_npcs_notes()`, update position clearing in presence transitions

**File:** `ccya/state/npcs.py`

**Files:**
- `ccya/state/npcs.py` lines 172–182 and 314–332
- `ccya/state/__init__.py` lines 27, 46
- `ccya/engine/turn.py` lines 52, 81

**What:**
1. **`ccya/state/npcs.py`**: Delete `strip_npcs_notes()` function (lines 172–182).
2. **`ccya/state/npcs.py`** — In `apply_npc_scene_management()`, change the three `entry.pop("notes", None)` calls:
   - Line 319 (presence == "known"): change to `entry.pop("position", None)`
   - Line 325 (presence == "departed"): change to `entry.pop("position", None)`
   - Lines 329–330 (`if comp_upd.notes is not None: entry["notes"] = comp_upd.notes`): delete this block entirely (notes field no longer exists on `CompendiumNpcUpdate`).
3. **`ccya/state/__init__.py`**: Remove `strip_npcs_notes` from the import (line 27) and from `__all__` (line 46).
4. **`ccya/engine/turn.py`**: Remove `strip_npcs_notes` from the import (line 52) and delete the call `strip_npcs_notes(state)` at line 81.

**Why:** Notes is removed. Position clearing moves from per-turn to presence-transition-based.

**Validation:** Call `apply_npc_scene_management()` with a compendium entry that has presence transitioning to `known`. Confirm `position` key is removed from the entry. Confirm no `notes` reference causes errors. Run `make check` and confirm no unresolved `strip_npcs_notes` imports.

### Tests to write or update

No tests. Validate by running `make check`.

---

## Implementation — Phase 5: Surface Code

### Context files to load

- `ccya/templates/index.html` lines 6, 19, 513–524, 1843–1846 — all `state.scene.tagline` references
- `ccya/engine/seed.py` line 38 — tagline sanitization
- `ccya/server/tv.py` line 224 — `_SKIP_FIELDS`

### Detailed steps

#### Step 5.1 — Update page title to read `state.meta.session_name`

**File:** `ccya/templates/index.html` line 6

**What:** Change `state.scene.tagline` to `state.meta.session_name` in the `<title>` tag.

```
<title>{% if state.meta.session_name %}CCYA: {{ state.meta.session_name }}{% elif state.location.id %}{{ state.pc.get('name') or 'Player' }} @ {{ state.location.get('name') or state.location.get('id', '') }}{% else %}Choose Your Own Adventure{% endif %}</title>
```

**Why:** `session_name` replaces `scene.tagline`.

**Validation:** Render the template with a state that has `meta.session_name` set. Confirm the title shows `CCYA: <name>`.

#### Step 5.2 — Update header logo to read `state.meta.session_name`

**File:** `ccya/templates/index.html` line 19

**What:** Change `state.scene.get('tagline')` to `state.meta.get('session_name')` in the header span.

**Why:** `session_name` replaces `scene.tagline`.

**Validation:** Render the template. Confirm the header logo shows the session name.

#### Step 5.3 — Update `_headerTaglineFromState()` JS function

**File:** `ccya/templates/index.html` lines 513–524

**What:** Change `st.scene.tagline` to `st.meta.session_name` in the JS function. Keep the fallback chain to PC @ Location and "Choose Your Own Adventure".

```javascript
function _headerTaglineFromState(st) {
    if (!st || typeof st !== 'object') return 'Choose Your Own Adventure';
    const meta = st.meta || {};
    const name = (meta.session_name && String(meta.session_name).trim()) || '';
    if (name) return name;
    const pc = st.pc || {};
    const loc = st.location || {};
    if (loc.id && (pc.name || loc.name)) {
        return (pc.name || 'Player') + ' @ ' + (loc.name || loc.id);
    }
    return 'Choose Your Own Adventure';
}
```

**Why:** `session_name` replaces `scene.tagline`.

**Validation:** Call the function with `{meta: {session_name: "Test"}}` and confirm it returns "Test". Call with empty meta and confirm it falls back to PC @ Location.

#### Step 5.4 — Update turn complete handler

**File:** `ccya/templates/index.html` lines 1843–1846

**What:** Change `result.state.scene.tagline` to `result.state.meta.session_name` (the handler reads state from the turn result and updates the header/title DOM). The field path in the turn result's `state_snapshot` has `scene.tagline` → `meta.session_name`.

**Why:** Session name now lives in meta.

**Validation:** Simulate a turn_complete event. Confirm the header updates from the new field path.

#### Step 5.5 — Update seed sanitizer

**Files:** `ccya/engine/seed.py` line 38, `ccya/pack.py` lines 54–58 (must be done after Step 1.5)

**What:** Change `envelope.seed_state.scene.tagline` to `envelope.seed_state.meta["session_name"]` in `_sanitize_envelope()`. Since `SeedState.meta` is `dict[str, Any]`, use subscript access.

```python
envelope.seed_state.meta["session_name"] = _strip_non_ascii(
    envelope.seed_state.meta.get("session_name", "")
)
```

**Why:** Session name lives in meta now. `SeedScene.tagline` was removed in Step 1.5.

**Validation:** Run `_sanitize_envelope()` with a seed envelope where `seed_state.meta = {"session_name": "Tést Session"}`. Confirm non-ASCII is stripped and the field reads `"Test Session"`.

#### Step 5.6 — Remove `scene_tagline` from `_SKIP_FIELDS`

**File:** `ccya/server/tv.py` line 224

**What:** Remove `"scene_tagline"` from the `_SKIP_FIELDS` set (can keep `"location_description"` since that field still exists on `StateExtractResult` and may be shown in the turn viewer now).

```
_SKIP_FIELDS = {"actions", "location_description"}
```

Or keep `_SKIP_FIELDS` as-is — harmless either way since the field no longer appears in extraction events. But removing it cleans up dead code.

**Why:** `scene_tagline` is no longer emitted by any extraction stream. `location_description` still exists but now on `StateExtractResult` — consider unhiding it so the turn viewer shows it.

**Validation:** Load a turn in the turn viewer. Confirm no KeyError from missing `scene_tagline` in extraction event rendering.

#### Step 5.7 — Update EV play output to use `session_name`

**File:** `ccya/ev/play.py` lines 118, 155, 189

**What:** In `_build_turn_result_output()` (line 118) and `_build_error_output()` (line 155), change the `scene` dict key from `"tagline"` to `"session_name"`:

```python
"scene": {
    "tags": state_after.get("scene", {}).get("tags", []),
    "session_name": state_after.get("meta", {}).get("session_name", ""),
    "id": state_after.get("location", {}).get("id", ""),
},
```

In `format_play_output()` (line 189), change the read path:

```python
scene_session_name = scene.get("session_name", "")
scene_id = scene.get("id", "")
scene_parts = [s for s in [scene_id, scene_session_name] if s]
lines.append(f"Scene:     {', '.join(scene_parts) if scene_parts else 'unknown'}")
```

**Why:** `session_name` replaces `scene.tagline`. EV play output must reflect the new state shape.

**Validation:** Run `ev.py play --turns 1` (or equivalent) and confirm the output shows the session name instead of "tagline: ...".

#### Step 5.8 — Update EV state tools to use `session_name`

**File:** `ccya/ev/state_tools.py` lines 1024, 1093

**What:** Line 1024: change `scene.get("tagline")` trigger to read from `meta.session_name`. Line 1093: change display to read from `meta.session_name`.

```python
# Line 1024:
session_name = state.get("meta", {}).get("session_name", "")
if any(scene.get(k) for k in ("tags",)) or session_name:
    _render_scene_section(state)

# Line 1093 (inside _render_scene_section):
session_name = state.get("meta", {}).get("session_name", "")
if session_name:
    print(f"  Session: {session_name}")
```

**Why:** `session_name` replaces `scene.tagline`. EV state tools must reflect the new state shape.

**Validation:** Run `ev.py state` and confirm the output shows `Session: <name>` instead of `Tagline: <name>`.

### Tests to write or update

No tests. Validate by running `make check` and manually loading the UI.

---

## Implementation — Phase 6: Documentation

### Context files to load

- `docs/architecture/step2a-scene.md` — full file (49 lines)
- `docs/architecture/step2b-state.md` — full file
- `docs/architecture/state-models.md` — full file (138 lines)
- `docs/architecture/OVERVIEW.md` — pipeline quick reference table (lines 49–59)
- `docs/repomap.md` — extraction section (line 21), cross-module contracts (line 113)
- `ccya/AGENTS.md` — build commands / conventions (if any need updating)

### Detailed steps

#### Step 6.1 — Update `docs/architecture/step2a-scene.md`

**File:** `docs/architecture/step2a-scene.md`

**What:**
- Change the flowchart output block to remove `scene_tagline`, `location_change`, `location_description`. Keep only `compendium_npc_update`.
- Remove the "Extraction prompt — NPC quality rules" subsections related to location/tagline (lines 35+ header, remove location-related guidance).
- Remove the "Key forward dependency" section that mentions `location_change` flowing into extraction context (lines 47–49 — now flows from state extractor).
- Update the purpose sentence at the top: "Extracts NPC presence and durable identity changes from the narrative."

**Why:** Step 2a is now pure-NPC extraction.

**Validation:** Read the final document. Confirm no references to `scene_tagline`, `location_change`, `location_description`.

#### Step 6.2 — Update `docs/architecture/step2b-state.md`

**File:** `docs/architecture/step2b-state.md`

**What:** Add location extraction to the description. Update the flowchart to include `location_change` and `location_description` as outputs alongside inventory and conditions.

**Why:** Step 2b now owns all state-level deltas.

**Validation:** Read the document. Confirm location fields appear in the output model.

#### Step 6.3 — Update `docs/architecture/state-models.md`

**File:** `docs/architecture/state-models.md`

**What:**
- Remove `scene.tagline` from the `state.yaml` shape (line 45 area).
- Add `meta.session_name` to the meta block (line 7 area).
- Remove `meta.game_name` from the meta block.
- Update `SceneExtractResult` model listing to show only `compendium_npc_update` (line 61).
- Update `StateExtractResult` model listing to include `location_change` and `location_description` (line 62).
- Update `CompendiumNpcUpdate` model listing to remove `notes` (line 77).
- Update `StateDelta` model listing to remove `scene_tagline` (line 78).
- Remove the `meta.game_name` entry in the non-obvious behavior section (if present).

**Why:** All model shapes changed.

**Validation:** Confirm every removed/added field is reflected in the document.

#### Step 6.4 — Update `docs/architecture/OVERVIEW.md`

**File:** `docs/architecture/OVERVIEW.md` lines 49–59 (pipeline quick reference table)

**What:** Update Step 2a row: remove `tagline, location_change` from key outputs. Update Step 2b row: add `location_change, location_description` to key outputs.

**Why:** Pipeline outputs changed.

**Validation:** Read the table. Confirm outputs match new model shapes.

#### Step 6.5 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:**
- Update the module index entry for extraction (line 21 area) if it lists `SceneExtractResult` fields.
- Update cross-module contracts (line 113) extraction routing description: remove `tagline, location` from scene extraction; add `location` to state extraction.
- Update extraction routing in the key models glossary (line 105) if present.

**Why:** Repomap must reflect the new field routing.

**Validation:** Grep for `scene_tagline`, `location_change`, `location_description`, `notes` in the file. Each should be updated to reflect new ownership.

#### Step 6.6 — Update `docs/architecture/cross-module-contracts.md`

**File:** `docs/architecture/cross-module-contracts.md`

**What:** Update the extraction routing description to reflect that `SceneExtractResult` now emits only `compendium_npc_update`, and `StateExtractResult` now also emits `location_change` and `location_description`.

**Why:** Extraction routing contracts changed.

**Validation:** Read the routing section. Confirm field ownership matches the new model shapes.

### Tests to write or update

No tests. Validate by running `make check` (docs changes won't affect lint/typecheck, but verify the markdown renders).
