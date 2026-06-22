# Grounded State Extraction

## Purpose

Make extracted state fields (location description, NPC notes, inventory notes, arc threads) more grounded, spatial, and physically descriptive — so the UI reflects a tangible world rather than mirroring event narration.

## Problem Statement

Narration is event-driven: it describes what happened, not what exists. The extraction pipeline currently mirrors that, pulling "new details" from narration rather than building a persistent spatial model. The result is:

- `location_description` reads like a narration excerpt, not a place
- NPC `notes` lack spatial positioning — who is where, how, relative to what
- Inventory `notes` are generic — no state or position info
- Arc thread summaries are abstract — no location context when relevant
- `scene_tags` exist as dead weight — no mechanical effect, no UI display, just cognitive load

## Constraints

- No new model fields beyond `position` on `CompendiumNpcUpdate`
- No changes to state shape or delta_builder logic
- No new templates or UI changes
- Tests are temporarily removed — skip test updates
- Documentation updates required per AGENTS.md
- Each phase independently executable

## Non-goals

- Nearby/POI system for locations (deferred to separate feature)
- Mechanical use of scene_tags (deferred — just remove them)
- Separate "nearby interactables" inventory (deferred)
- NPC position tracking beyond scene extraction (deferred)
- New UI components or templates

## Solution

Rewrite four prompt templates to produce more grounded, spatial, physically descriptive output. Remove `scene_tags` entirely from the extraction pipeline. Add one new field (`position`) to `CompendiumNpcUpdate` for explicit NPC spatial positioning. Tighten inventory notes to end with spatial position. Tighten arc thread summaries to naturally include location context.

## Firm decisions

1. **Remove `scene_tags` entirely** — no mechanical effect, no UI display, dead weight.
2. **`location_description` is a rewrite, not accumulation** — LLM produces a complete description informed by what's already stored. Narration is about events; this field is about the place.
3. **NPC `position` is a separate field** — explicit field on `CompendiumNpcUpdate` for spatial positioning. Keeps it consistent and visible to LLM.
4. **Inventory notes end with spatial position** — prefix is freeform (condition, narrative role, quest status, device metadata). On-person only.
5. **Arc thread summaries naturally include location** — no new field. Thread summary should naturally reference location when relevant to the objective.
6. **Narrator context unchanged** — `_location.j2` and `_npc_roster.j2` templates already pass location description and NPC notes/position to narrator. No template changes needed.

## Risks, Ambiguities, and Blockers

- **Location description rewrite cost:** LLM must produce a complete description each turn informed by existing description. Uses more tokens per scene extraction call. Acceptable tradeoff for quality.
- **NPC position consistency:** LLM must track NPC positions across turns. Explicit field helps but doesn't guarantee consistency. This is an LLM quality issue, not an engine issue.
- **scene_tags removal:** If scene_tags are consumed elsewhere (ruling/storytell/narrate prompts), removal will break those prompts. Verified: scene_tags are not consumed by ruling, storyteller, or narrator. `game_over` detection in routes.py is removed — no replacement mechanism exists yet.
- **Inventory notes format change:** Existing inventory entries with notes that don't end with spatial position will be overwritten on next update. This is acceptable — the format change is a one-time cleanup.

## Status

`completed`

## Phases

3 phases: (1) remove scene_tags, (2) rewrite location_description + add NPC position, (3) tighten inventory notes + arc thread summaries.

---

## Phase 1: Remove scene_tags

### Context files to load

- `ccya/prompts/extract_scene_system.j2`
- `ccya/models.py` (SceneExtractResult, StateDelta)
- `ccya/state/delta_builder.py`
- `ccya/engine/extraction.py`
- `ccya/engine/turn.py`
- `ccya/server/routes.py`
- `ccya/ev/state_tools.py`
- `ccya/ev/events.py`
- `ccya/ev/play.py`
- `ccya/ev/checkers/llm_checkers.py`
- `ccya/llm_mock.py`
- `ccya/prompts/SYSTEM_PROMPTING.md`

### Detailed steps

#### Step 1.1 — Remove scene_tags from prompt template

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Remove `scene_tags` from the output schema (line 9), field rules (line 19), and constraints (line 129). Add `position` to compendium_npc_update schema.

**Before:**
```
## Output schema
```json
{
  "scene_tags": ["..."],
  "scene_tagline": "...",
  "location_change": {"id": "...", "name": "...", "description": "..."},
  "location_description": "...",
  "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "presence": "present|nearby|known|departed", "notes": "..."}]
}
```

## Field rules

`scene_tags`: mood/genre descriptors for the scene. Up to 5. Use concise noun or adjective phrases. Examples: `"combat"`, `"tense_conversation"`, `"investigation"`, `"stealth"`, `"discovery"`.

`scene_tagline`: 3–6 words describing the current location and situation...
```

**After:**
```
## Output schema
```json
{
  "scene_tagline": "...",
  "location_change": {"id": "...", "name": "...", "description": "..."},
  "location_description": "...",
  "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "presence": "present|nearby|known|departed", "notes": "...", "position": "..."}]
}
```

## Field rules

`scene_tagline`: 3–6 words describing the current location and situation...
```

Also remove line 129: `- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.`

**Why:** scene_tags have zero mechanical effect. They're not consumed by ruling/storytell/narrate. They're only displayed in ev.py (which can be removed). Dead weight.

**Validation:** Grep for `scene_tags` in `ccya/prompts/` — should return zero matches.

#### Step 1.2 — Remove scene_tags from models

**File:** `ccya/models.py`

**What:** Remove `scene_tags: list[str] = Field(default_factory=list)` from `StateDelta` (line 286) and `SceneExtractResult` (line 308). Remove `scene_tags: list[str] = field(default_factory=list)` from `TurnResult` (line 528).

**Why:** Field no longer emitted by prompt, no longer needed in models.

**Validation:** Grep for `scene_tags` in `ccya/models.py` — should return zero matches.

#### Step 1.3 — Remove scene_tags from delta_builder

**File:** `ccya/state/delta_builder.py`

**What:** Remove lines 274-281 (scene_tags merge logic including combat_started_turn tracking).

**Before:**
```python
    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags
        new_tags = set(delta.scene_tags)
        old_tags = set(state.get("scene", {}).get("tags") or [])
        if "combat" in new_tags and "combat" not in old_tags:
            state["scene"]["combat_started_turn"] = state.get("meta", {}).get("turn", 0)
        elif "combat" not in new_tags and "combat" in old_tags:
            state["scene"].pop("combat_started_turn", None)
```

**After:** (remove entirely)

**Why:** No scene_tags to merge. combat_started_turn tracking removed — no mechanical use.

**Validation:** Grep for `scene_tags` in `ccya/state/delta_builder.py` — should return zero matches.

#### Step 1.4 — Remove scene_tags from extraction pipeline

**File:** `ccya/engine/extraction.py`

**What:** 
- Remove `scene_tags_this_turn: list[str] = field(default_factory=list)` from `ExtractionContext` (line 53)
- Remove `scene_tags=list(scene_result.scene_tags or [])` from context build (line 80)
- Remove `scene_tags_this_turn=list(post_state.get("scene", {}).get("tags") or [])` (line 100)
- Remove `if not scene_result.scene_tags:` warning check (lines 467-469)
- Remove `scene_tags=scene_result.scene_tags` from merge (line 642)
- Remove `scene_tags=%d` from merge log (line 637)

**Before:**
```python
    scene_tags_this_turn: list[str] = field(default_factory=list)
    """scene.tags after scene stream."""
```

**After:**
```python
    # (remove scene_tags_this_turn field entirely)
```

**Why:** Field no longer emitted by extraction. No downstream consumers.

**Validation:** Grep for `scene_tags` in `ccya/engine/extraction.py` — should return zero matches.

#### Step 1.5 — Remove scene_tags from turn.py

**File:** `ccya/engine/turn.py`

**What:**
- Remove `"scene_tags": list(getattr(delta, "scene_tags", []))` from ruling_event (line 1412)
- Remove `scene_tags=list(getattr(delta, "scene_tags", []))` from storyteller context (line 1489)

**Why:** Field removed from StateDelta/SceneExtractResult.

**Validation:** Grep for `scene_tags` in `ccya/engine/turn.py` — should return zero matches.

#### Step 1.6 — Remove scene_tags from server/routes.py

**File:** `ccya/server/routes.py`

**What:**
- Remove `"scene_tags": result.scene_tags,` (line 278)

**Before:**
```python
                                "scene_tags": result.scene_tags,
```

**After:**
```python
                                # (remove line)
```

**Why:** route no longer needs scene_tags.

**Validation:** Grep for `scene_tags` in `ccya/server/routes.py` — should return zero matches.

#### Step 1.7 — Remove scene_tags from ev tooling

**File:** `ccya/ev/state_tools.py`

**What:**
- Remove `_diff_scene_tags` function (line 486)
- Remove `"scene_tags_this_turn": ("Scene Tags", _diff_scene_tags)` from diff functions (line 637)

**Why:** No scene_tags to diff.

**Validation:** Grep for `scene_tags` in `ccya/ev/state_tools.py` — should return zero matches.

**File:** `ccya/ev/events.py`

**What:**
- Remove `"scene_tags"` from skip set (line 240): `skip = {"actions", "location_description", "scene_tags", "scene_tagline"}`
- Remove `elif field == "scene.tags":` block (lines 339-340)

**Before:**
```python
        skip = {"actions", "location_description", "scene_tags", "scene_tagline"}
```

**After:**
```python
        skip = {"actions", "location_description", "scene_tagline"}
```

**Why:** Field removed from extraction pipeline.

**Validation:** Grep for `scene_tags` in `ccya/ev/events.py` — should return zero matches.

**File:** `ccya/ev/play.py`

**What:**
- Remove `scene_tags = scene.get("tags", [])` (line 200)
- Remove `+ scene_tags` from scene_parts (line 203)
- Remove `scene_tagline = scene.get("tagline", "")` (line 430) — wait, keep tagline
- Remove `has_data = location_name or present_npcs or inventory_items or scene_tagline` (line 442) — keep tagline
- Remove `if scene_tagline:` block (lines 445-446) — keep tagline

Actually, re-reading play.py lines 200-203 and 430-446: these reference `scene_tags` and `scene_tagline`. Need to check which is which.

Lines 200-203 reference `scene_tags` (tags) and `scene_tagline` (tagline). Remove tag references, keep tagline.

Lines 430-446 reference `scene_tagline` (tagline). Keep these.

**Before:**
```python
    scene_tags = scene.get("tags", [])
    scene_tagline = scene.get("tagline", "")
    scene_parts = [s for s in [scene_id, scene_tagline] if s] + scene_tags
```

**After:**
```python
    scene_tagline = scene.get("tagline", "")
    scene_parts = [s for s in [scene_id, scene_tagline] if s]
```

**Why:** scene_tags removed. scene_tagline kept.

**Validation:** Grep for `scene_tags` in `ccya/ev/play.py` — should return zero matches.

**File:** `ccya/ev/checkers/llm_checkers.py`

**What:**
- Remove `Scene tags: {scene_tags}` from checker output (line 41)
- Remove `requires_fields=["ruling.band", "ruling.intent", "narrate", "extraction_context.scene_tags_this_turn"]` (line 50)
- Remove `scene_tags = extract_field(ev, "extraction_context.scene_tags_this_turn") or []` (line 65)
- Remove `Scene tags: {', '.join(scene_tags) if scene_tags else '(none)'}'` (line 71)

**Before:**
```python
    requires_fields=["ruling.band", "ruling.intent", "narrate", "extraction_context.scene_tags_this_turn"],
```

**After:**
```python
    requires_fields=["ruling.band", "ruling.intent", "narrate"],
```

**Why:** scene_tags field removed from extraction context.

**Validation:** Grep for `scene_tags` in `ccya/ev/checkers/llm_checkers.py` — should return zero matches.

#### Step 1.8 — Remove scene_tags from llm_mock.py

**File:** `ccya/llm_mock.py`

**What:**
- Remove `"scene_tags": ["exploration"]` (line 17)
- Remove `"scene_tags": ["dialogue"]` (line 29)
- Remove `"scene_tags": ["travel"]` (line 46)

**Why:** Mock responses no longer emit scene_tags.

**Validation:** Grep for `scene_tags` in `ccya/llm_mock.py` — should return zero matches.

#### Step 1.9 — Update documentation

**File:** `ccya/prompts/SYSTEM_PROMPTING.md`

**What:**
- Remove `scene_tags` from unique fields list (line 127): `**Unique fields:** scene_tags, scene_tagline, location_change, location_description, npc_add/remove/update, compendium_npc_update`
- Update description if scene_tags mentioned in "Why they exist" (line 129)

**Before:**
```
**Unique fields:** `scene_tags`, `scene_tagline`, `location_change`, `location_description`, `npc_add/remove/update`, `compendium_npc_update`
```

**After:**
```
**Unique fields:** `scene_tagline`, `location_change`, `location_description`, `npc_add/remove/update`, `compendium_npc_update`
```

**Why:** Documentation must reflect current state.

**Validation:** Grep for `scene_tags` in `ccya/prompts/SYSTEM_PROMPTING.md` — should return zero matches.

#### Step 1.10 — Update documentation

**Files:**
- `docs/repomap.md` — update CompendiumNpcUpdate field list, remove scene_tags references from extraction pipeline section, update StateDelta field list
- `docs/architecture/step2a-scene.md` — remove scene_tags from scene extraction output schema
- `docs/architecture/step2b-state.md` — update inventory notes format guidance
- `docs/architecture/step2c-storytell.md` — update thread summary guidance
- `docs/architecture/persist.md` — remove scene_tags references
- `docs/architecture/narration-ui.md` — remove scene_tags references
- `docs/architecture/delta-validate.md` — remove scene_tags references
- `docs/architecture/OVERVIEW.md` — remove scene_tags references
- `AGENTS.md` — no changes needed (build/lint commands unchanged)

**Why:** Per AGENTS.md, every code change that touches a module, config key, model field, prompt, or public API requires corresponding documentation updates.

**Validation:** Grep for `scene_tags` in `docs/` — should return zero matches.

### Tests to write or update

Tests temporarily removed per AGENTS.md. Skip.

---

## Phase 2: Rewrite location_description + add NPC position

### Context files to load

- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/models.py` (CompendiumNpcUpdate)
- `ccya/state/npcs.py`
- `ccya/state/delta_builder.py`
- `ccya/prompts/sections/_npc_roster.j2`
- `ccya/prompts/sections/_location.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/ruling_user.j2`
- `ccya/prompts/storytell_user.j2`
- `ccya/server/routes.py`
- `ccya/ev/state_tools.py`
- `ccya/ev/events.py`
- `ccya/ev/play.py`
- `ccya/llm_mock.py`

### Detailed steps

#### Step 2.1 — Add position field to CompendiumNpcUpdate

**File:** `ccya/models.py`

**What:** Add `position: str | None = None` to `CompendiumNpcUpdate` class (after `notes` field, around line 256).

**Before:**
```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None
    notes: str | None = None
    first_seen_turn: int | None = None
    personality: str | None = None
    departed_reason: str | None = None
    departed_summary: str | None = None
    departed_turn: int | None = None
```

**After:**
```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None
    notes: str | None = None
    position: str | None = None
    first_seen_turn: int | None = None
    personality: str | None = None
    departed_reason: str | None = None
    departed_summary: str | None = None
    departed_turn: int | None = None
```

**Why:** Explicit spatial positioning field for NPCs. Keeps LLM focused on where NPCs are in the scene.

**Validation:** Grep for `position` in `ccya/models.py` — should find the new field.

#### Step 2.2 — Apply position in npc_scene_management

**File:** `ccya/state/npcs.py`

**What:** Add position handling in `apply_npc_scene_management` after notes handling (around line 186).

**Before:**
```python
            if comp_upd.notes is not None:
                entry["notes"] = comp_upd.notes

    return state
```

**After:**
```python
            if comp_upd.notes is not None:
                entry["notes"] = comp_upd.notes
            if comp_upd.position is not None:
                entry["position"] = comp_upd.position

    return state
```

**Why:** Persist NPC position to compendium. Narrator and other prompts read from compendium.

**Validation:** Read `ccya/state/npcs.py` lines 185-190 — should show position handling.

#### Step 2.3 — Pass position through SceneExtractResult to delta_builder

**File:** `ccya/state/delta_builder.py`

**What:** Remove `scene_tags` parameter from SceneExtractResult construction (around line 288). Position is carried within `compendium_npc_update` entries, not as a separate field on SceneExtractResult.

**Before:**
```python
    state = apply_npc_scene_management(state, SceneExtractResult(
        compendium_npc_update=delta.compendium_npc_update or [],
        scene_tags=delta.scene_tags or [],
        scene_tagline=delta.scene_tagline,
        location_change=delta.location_change,
        location_description=delta.location_description,
    ), current_turn_no=current_turn)
```

**After:**
```python
    state = apply_npc_scene_management(state, SceneExtractResult(
        compendium_npc_update=delta.compendium_npc_update or [],
        scene_tagline=delta.scene_tagline,
        location_change=delta.location_change,
        location_description=delta.location_description,
    ), current_turn_no=current_turn)
```

**Why:** scene_tags removed (phase 1). position is per-NPC in compendium_npc_update, not a top-level field.

**Validation:** Read `ccya/state/delta_builder.py` lines 286-294 — should show scene_tags removed.

#### Step 2.4 — Pass position through NPC roster template

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Add position display in NPC roster output (after notes, around line 8).

**Before:**
```
- `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.presence == "departed" and n.departed_reason %} — {{ n.departed_reason }}{% endif %}{% if n.bio and n.presence != "departed" %} — {{ n.bio }}{% endif %}
{%- if n.notes %} | {{ n.notes }}{% endif %}
{%- if n.motivation %} | wants: {{ n.motivation }}{% endif %}
```

**After:**
```
- `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.presence == "departed" and n.departed_reason %} — {{ n.departed_reason }}{% endif %}{% if n.bio and n.presence != "departed" %} — {{ n.bio }}{% endif %}
{%- if n.notes %} | {{ n.notes }}{% endif %}{% if n.position %} | {{ n.position }}{% endif %}
{%- if n.motivation %} | wants: {{ n.motivation }}{% endif %}
```

**Why:** Passes NPC position to narrator, ruling, and storyteller prompts. Makes spatial awareness explicit in context.

**Validation:** Read `ccya/prompts/sections/_npc_roster.j2` — should show position display.

#### Step 2.5 — Rewrite location_description prompt

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Rewrite the `location_description` field rules (line 25).

**Before:**
```
`location_description`: Location description — new physical/spatial detail about the current space. Only emit when the narration introduces genuinely new details not already in the stored description. Do not restate or paraphrase existing description. One to two sentences.
```

**After:**
```
`location_description`: Complete description of the current location. What the space IS — physical layout, visual details, atmosphere. Include tangible details (materials, lighting, sounds, smells) and spatial relationships. Infer from narration but don't repeat it. Narration tells what happened; this field tells what exists. Rewrite the full description each turn, informed by what's already stored. Two to four sentences.
```

**Why:** Shifts LLM from "extract new details" to "describe the place." More grounded, spatial, atmospheric output.

**Validation:** Read `ccya/prompts/extract_scene_system.j2` line 25 — should show new description.

#### Step 2.5b — Add position field rules to extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add `position` field rules after `notes` field rules (around line 27).

**Before:**
```
`notes`: NPC notes — observations, behavior, condition, dialogue. One to two sentences.
```

**After:**
```
`notes`: NPC notes — observations, behavior, condition, dialogue. One to two sentences.

`position`: Where the NPC is in the scene. One short phrase. Only update when narration moves the NPC or implies movement.
```

**Why:** Explicit field rules guide LLM to produce consistent position data.

**Validation:** Read `ccya/prompts/extract_scene_system.j2` — should show position field rules.

#### Step 2.5c — Add position example in NPC presence examples

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add position to NPC enter example, add NPC moves example, tighten labels.

**Before:**
```
EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
Known NPCs in scene: [caron (present)]
→ Emit: `compendium_npc_update: { id: "red_haired_man", name: "Red-Haired Man", presence: "present", notes: "locks eyes aggressively", bio: "..." }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `compendium_npc_update: { id: "caron", presence: "known" }`

EXAMPLE — NPC not mentioned, no change (correct):
Narration does not mention Halden this turn.
→ Do NOT emit any update for Halden — absence ≠ departure.
```

**After:**
```
EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
Known NPCs in scene: [caron (present)]
→ Emit: `compendium_npc_update: { id: "red_haired_man", name: "Red-Haired Man", presence: "present", notes: "locks eyes aggressively", position: "standing in doorway", bio: "..." }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `compendium_npc_update: { id: "caron", presence: "known" }`

EXAMPLE — NPC moves (correct):
Narration: "Caron slides into the seat across from you."
→ Emit: `compendium_npc_update: { id: "caron", position: "seated across from PC" }`

EXAMPLE — NPC not mentioned (correct):
Narration does not mention Halden this turn.
→ Do NOT emit any update for Halden — absence ≠ departure.
```

**Why:** Examples guide LLM to produce position data alongside notes.

**Validation:** Read `ccya/prompts/extract_scene_system.j2` — should show position in examples.

#### Step 2.6 — Pass location description to narrator context

**File:** `ccya/prompts/sections/_location.j2`

**What:** No change needed. Template already passes `state.location.description` to narrator.

**Why:** Verified — template at line 2 already renders `state.location.description`.

**Validation:** Read `ccya/prompts/sections/_location.j2` — should show existing behavior.

### Tests to write or update

Tests temporarily removed per AGENTS.md. Skip.

---

## Phase 3: Tighten inventory notes + arc thread summaries

### Context files to load

- `ccya/prompts/extract_state_system.j2`
- `ccya/prompts/storytell_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/sections/_inventory.j2`
- `ccya/prompts/sections/_thread_list.j2`
- `ccya/prompts/sections/_arc.j2`
- `ccya/prompts/storytell_user.j2`
- `ccya/models.py` (InventoryItem, InventoryUpdate)
- `ccya/state/delta_builder.py`
- `ccya/state/inventory.py`
- `ccya/ev/state_tools.py`
- `ccya/ev/events.py`
- `ccya/llm_mock.py`

### Detailed steps

#### Step 3.1 — Tighten inventory notes format

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Rewrite the `inventory_add` and `inventory_update` notes guidance (lines 49-58).

**Before:**
```
`inventory_update`: patches to existing items — name changes, notes updates, damage, upgrades. Does not support amount changes — use `inventory_remove` instead. `name` and `notes` are optional within an update entry.

`inventory_remove`: items lost, used up, destroyed, or spent. Set `amount` to the count consumed (e.g. `"amount": 1` for one pistol_round). Omit `amount` to remove the entire stack.
- If narration describes spending, giving away, or parting with an item — even if the amount is vague — emit the remove. If the recipient later rejects it or the action fails, still emit the remove.
- Using a reusable item (unlocking a door with a key, reading a book) does NOT consume it. Only emit remove when the item is actually lost or used up.

`inventory_add`: items explicitly received by the player character.
- Do not cap items explicitly received. Items found incidentally (e.g. "searched the crates") are limited to ≤2 per turn.
- Firearms and finite-use items always come with ammo or uses. Infer a realistic starting amount from context. If compatible ammo already exists in inventory, use `inventory_add` — it merges with the existing stack.
- Never emit `inventory_add` and `inventory_remove` for the same ID in one turn.
```

**After:**
```
`inventory_update`: patches to existing items — name changes, notes updates, damage, upgrades. Does not support amount changes — use `inventory_remove` instead. `name` and `notes` are optional within an update entry.

`inventory_remove`: items lost, used up, destroyed, or spent. Set `amount` to the count consumed (e.g. `"amount": 1` for one pistol_round). Omit `amount` to remove the entire stack.
- If narration describes spending, giving away, or parting with an item — even if the amount is vague — emit the remove. If the recipient later rejects it or the action fails, still emit the remove.
- Using a reusable item (unlocking a door with a key, reading a book) does NOT consume it. Only emit remove when the item is actually lost or used up.

`inventory_add`: items explicitly received by the player character.
- Do not cap items explicitly received. Items found incidentally (e.g. "searched the crates") are limited to ≤2 per turn.
- Firearms and finite-use items always come with ammo or uses. Infer a realistic starting amount from context. If compatible ammo already exists in inventory, use `inventory_add` — it merges with the existing stack.
- Never emit `inventory_add` and `inventory_remove` for the same ID in one turn.

**Inventory notes:** End with spatial position. Prefix is freeform — condition, narrative role, quest status, device metadata. Examples: `"quest item, in locked safe"`, `"handheld screen, in backpack"`, `"worn, in right holster"`. On-person only.
```

**Why:** Tightens notes to be consistent and useful. "State + position" format helps narrator track where items are and their condition. Clarifies that inventory = on-person only.

**Validation:** Read `ccya/prompts/extract_state_system.j2` — should show new notes format guidance.

#### Step 3.2 — Tighten arc thread summaries for location context

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add guidance about location context in thread summaries (after line 28, in the thread_update section).

**Before:**
```
**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation. `progress_kind` classifies the change. If the thread is no longer relevant, resolve it (thread_resolve) or set active: false, then create a new thread via thread_add — do not repurpose with progress that contradicts the summary.
```

**After:**
```
**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation. `progress_kind` classifies the change. If the thread is no longer relevant, resolve it (thread_resolve) or set active: false, then create a new thread via thread_add — do not repurpose with progress that contradicts the summary.

**Include location in thread summaries when relevant:** `"rescue hostages from warehouse district"` not `"rescue hostages"`.
```

**Why:** Thread summaries are the primary UI element for tracking objectives. Adding location context naturally (no new field) makes them more useful and helps narrator maintain spatial awareness.

**Validation:** Read `ccya/prompts/storytell_system.j2` — should show new location context guidance.

#### Step 3.3 — Update inventory display template

**File:** `ccya/prompts/sections/_inventory.j2`

**What:** No change needed. Template already renders `item.notes`. The format change is in the prompt, not the template.

**Why:** Template is format-agnostic. It displays whatever notes the extraction produces.

**Validation:** Read `ccya/prompts/sections/_inventory.j2` — should show existing behavior.

### Tests to write or update

Tests temporarily removed per AGENTS.md. Skip.

---

## Documentation updates required

Per AGENTS.md, every code change that touches a module, config key, model field, prompt, or public API requires corresponding updates to:

1. **`docs/architecture/`** — if pipeline flow, data shapes, or stage contracts change
    - `docs/architecture/step2a-scene.md` — update scene extraction output schema (remove scene_tags, add NPC position)
    - `docs/architecture/step2b-state.md` — update inventory notes format guidance
    - `docs/architecture/step2c-storytell.md` — update thread summary guidance

2. **`docs/repomap.md`** — if module boundaries, function signatures, or public APIs change
   - Update `CompendiumNpcUpdate` field list
   - Remove `scene_tags` references from extraction pipeline section
   - Update `StateDelta` field list

3. **`AGENTS.md`** (this file) — if build commands, test commands, signposts, or repo conventions change
   - No changes needed — build/lint commands unchanged.
