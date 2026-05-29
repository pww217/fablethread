# NPC Bonds & Scene Detail Pools

## Status
`completed`

## Phases
4 phases covering: (1) model fields + pack data, (2) seed selection logic, (3) seed prompt changes, (4) narrator pipeline to surface bond.

## Issue

The seed generation's 4 existing pools (situation_archetype, arc_category, character_dynamic, moral_pressure) are abstract archetypes — `{id, tags}` only. They tell the LLM what *dimension* to think about but give it zero concrete material to write into NPCs, relationships, or environment details. This is why openings remain generic: the LLM invents everything from scratch with no seed data to ground it.

Two concrete failures:
1. **Generic NPC relationships**: The prompt says "at least 1 NPC must have personal connection" but gives no material. The LLM defaults to "longtime companion" — a role, not a relationship.
2. **Static scenery**: The prompt says "describe 2-4 environmental details" but gives no specific objects. The LLM writes atmospheric color (dust, shadows) instead of interactable things.

Separately, the `relation` field from seed-time `present_npcs` does not persist into compendium. When an NPC leaves the scene, only `{name, title, bio}` survives in `CompendiumEntry`. The PC-NPC bond is lost on scene exit.

## Solution

Three additions, one fix:

1. **NPC bond pool** (new per-pack pool): Each entry defines a concrete relationship template (`{id, tags, description}`). Engine selects one at seed time. LLM encodes it as `bond` field on the NPC's compendium entry. Bond persists through scene transitions.

2. **Scene detail bundle pool** (new per-pack pool): Each entry defines 3-6 concrete interactable objects (`{id, items[], min_use}`). Engine selects one at seed time. LLM must incorporate at least `min_use` of them as examinable/interactable scene details in the opening.

3. **CompendiumEntry.bond** (persistent field): New optional `bond` field on `CompendiumEntry`. Carried through `build_npc_roster` into narrator and extract prompts. One source of truth for the PC-NPC relationship.

4. **PoolEntry.description**: Optional `description: str` field added to existing `PoolEntry` model. Empty for all existing pool entries (backward compat). Used by npc_bond pool only.

## Firm decisions

1. No new pipeline steps, no new state mutations, no new LLM calls. Everything is seed-time selection + prompt guidance + data plumbing.
2. Bond pool entries are per-pack (like all other pools). Each pack defines 8-10 bond templates appropriate to its genre.
3. Scene detail bundles are per-pack. Each pack defines 4-6 bundles of 3-6 objects each. Objects must be interactable (examinable, pick-up-able, use-able), not atmospheric.
4. `bond` is a free-text string on compendium entries. Set once at seed time. Never changed by engine — the narrator and extraction pipelines may update NPC `notes`/`motivation`/`fear`/`leverage` but never `bond`.
5. `min_use` is advisory prompt guidance, not a hard validation. If the LLM uses fewer than `min_use` objects, the seed still works.

## Non-goals

- No changes to the turn pipeline or state apply/merge logic
- No new LLM calls
- No changes to compaction, chronicle, or turn viewer
- No changes to `generate_pack`
- No changes to static packs
- No changes to the `inspiration` prose blocks

## Risks, Ambiguities, and Blockers

- **Bond pool size varies by pack**: Some genres (e.g., space-western, golden-piracy) have fewer natural relationship archetypes. May need 6-8 entries instead of 10. Acceptable — `_preselect_pools` handles any pool size >= 1.
- **Scene object overload**: If the LLM treats all 6 items as mandatory checklist items instead of 2-3 woven details, the opening may feel cluttered. Mitigation: the prompt says "at least {min_use}" and "weave them naturally."
- **`bond` field on KNOWN NPCs from non-seed sources**: NPCs added via extraction during play won't have `bond`. The roster template handles this — bond is rendered conditionally (`{% if n.bond %}`).
- **`description` field on PoolEntry is unused by existing pools**: Adding a field to a shared model that only one pool uses is technically fine (`description` defaults to `""`), but creates a latent field. No behavioral impact.

## Implementation — Phase 1: Model fields + pack data

### Context files to load
- `ccya/pack.py` — CompendiumEntry (line 44), PoolEntry (line 127), ScenarioBrief (line 135)
- All 6 scenario.yaml files for pack data reference

### Detailed steps

#### Step 1.1 — Add `description` to PoolEntry

**File:** `ccya/pack.py`

**What:** Add `description: str = ""` to `PoolEntry`.

**Why:** The npc_bond pool entries need a prose description field. Existing pool entries (situation_archetypes, etc.) default to `""` — no behavioral change.

**Validation:** `python -c "from ccya.pack import PoolEntry; e = PoolEntry(id='test', tags=['a']); print(e.description == '')"` prints `True`.

#### Step 1.2 — Add `bond` to CompendiumEntry

**File:** `ccya/pack.py`

**What:** Add `bond: str | None = None` to `CompendiumEntry`.

**Why:** Persistent storage for the PC-NPC relationship. Set once at seed time, never mutated by engine.

**Validation:** `python -c "from ccya.pack import CompendiumEntry; e = CompendiumEntry(name='X', bond='pulled from fire'); print(e.bond)"` prints `pulled from fire`.

#### Step 1.3 — Add SceneDetailBundle model

**File:** `ccya/pack.py`

**What:** Add new model:

```python
class SceneDetailBundle(BaseModel):
    id: str
    items: list[str] = Field(min_length=3, max_length=6)
    min_use: int = 2
```

Add after `PoolEntry` block (line 133).

**Why:** Each bundle defines a set of genre-appropriate interactable objects with a minimum-use count for the seed prompt.

**Validation:** `python -c "from ccya.pack import SceneDetailBundle; b = SceneDetailBundle(id='test', items=['a','b','c']); print(b.min_use)"` prints `2`.

#### Step 1.4 — Add `npc_bonds` and `scene_detail_bundles` to ScenarioBrief

**File:** `ccya/pack.py`

**What:** Add two new fields at the end of `ScenarioBrief` (after line 163):

```python
    npc_bonds: list[PoolEntry] = Field(default_factory=list, max_length=12)
    scene_detail_bundles: list[SceneDetailBundle] = Field(default_factory=list, max_length=8)
```

**Why:** Each pack defines its own pools. These are per-genre, just like situation_archetypes.

**Validation:** Import check passes.

#### Step 1.5 — Add bond and scene_bundle to seed output schema in system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Two changes:

1. Update compendium entry schema (line ~106) from:
```
compendium: {npcs: {snake_case: {name: string, title: string, bio: string, allegiance?: string}}}
```
to:
```
compendium: {npcs: {snake_case: {name: string, title: string, bio: string, allegiance?: string, bond?: string}}}
```

2. Add `bond` to the compendium.npcs field guidance (line ~189):
```
Compendium entries get: `name`, `title`, `bio` (and optional `allegiance` if relevant, and `bond` if this NPC has a personal tie to the PC).
```

Change the existing line:
```
Do NOT add `relation`, `notes`, `motivation`, `fear`, or `leverage` to compendium entries. Those fields are engine-managed at runtime. Compendium entries get: `name`, `title`, `bio` (and optional `allegiance` if relevant). `allegiance` is a faction id from the world pack.
```
to:
```
Do NOT add `relation`, `notes`, `motivation`, `fear`, or `leverage` to compendium entries. Those fields are engine-managed at runtime. Compendium entries get: `name`, `title`, `bio` (and optional `allegiance` if relevant, and `bond` if this NPC has a personal tie to the PC). `allegiance` is a faction id from the world pack.
```

**Why:** The LLM needs to know it can emit `bond` on compendium entries. The schema change tells it the field exists. The prose guidance tells it when to use it.

**Validation:** Template renders without Jinja errors.

### Tests to write or update
None (tests deferred).

### REPOMAP updates required
- `ccya/pack.py` — PoolEntry (description), CompendiumEntry (bond), ScenarioDetailBundle (new model), ScenarioBrief (npc_bonds, scene_detail_bundles)
- `ccya/prompts/generate_seed_system.j2` — compendium schema and guidance

## Implementation — Phase 2: Seed selection logic

### Context files to load
- `ccya/engine/seed.py` — `_preselect_pools()` (line 109), `_build_synthesis_context()` (line 94), `_select_from_pool()` (line 80), `_build_generate_seed_messages()` (line 128)

### Detailed steps

#### Step 2.1 — Extend `_preselect_pools` to select from new pools

**File:** `ccya/engine/seed.py`

**What:** Select from `npc_bonds` and `scene_detail_bundles` pools. Pass `name_seed` with a unique field name for deterministic selection.

Change `_preselect_pools` from:

```python
def _preselect_pools(scenario: Any, name_seed: int) -> dict[str, Any]:
    situation = _select_from_pool(
        scenario.situation_archetypes, name_seed, "situation_archetype"
    )
    arc = _select_from_pool(scenario.arc_categories, name_seed, "arc_category")
    character_dynamic = _select_from_pool(
        scenario.character_dynamics, name_seed, "character_dynamic"
    )
    moral_pressure = _select_from_pool(
        scenario.moral_pressures, name_seed, "moral_pressure"
    )
    return _build_synthesis_context(situation, arc, character_dynamic, moral_pressure)
```

to:

```python
def _preselect_pools(scenario: Any, name_seed: int) -> dict[str, Any]:
    situation = _select_from_pool(
        scenario.situation_archetypes, name_seed, "situation_archetype"
    )
    arc = _select_from_pool(scenario.arc_categories, name_seed, "arc_category")
    character_dynamic = _select_from_pool(
        scenario.character_dynamics, name_seed, "character_dynamic"
    )
    moral_pressure = _select_from_pool(
        scenario.moral_pressures, name_seed, "moral_pressure"
    )
    npc_bond = _select_from_pool(scenario.npc_bonds, name_seed, "npc_bond")
    scene_bundle = _select_from_pool(
        scenario.scene_detail_bundles, name_seed, "scene_detail_bundle"
    )
    return _build_synthesis_context(
        situation, arc, character_dynamic, moral_pressure, npc_bond, scene_bundle
    )
```

`_select_from_pool` already handles empty pool lists by raising ValueError. The caller catches this and continues without pools — same behavior as existing pools.

**Type hint update:** `_select_from_pool` is currently typed `pool_items: list[PoolEntry]`. Since `scene_detail_bundles` is `list[SceneDetailBundle]` (not `list[PoolEntry]`), change the parameter type to `pool_items: list[Any]` to accept heterogeneous pool types.

**Important:** Phase 1 must add at least 1 entry to `npc_bonds` and `scene_detail_bundles` in all 6 scenario.yamls before Phase 2 code runs. An empty pool causes `_select_from_pool` to raise ValueError, which cascades to `pool_selection = None` (all 6 pools disabled, not just the new ones).

**Validation:** Unit test: `_preselect_pools` returns dict with `npc_bond` and `scene_bundle` keys.

#### Step 2.2 — Extend `_build_synthesis_context`

**File:** `ccya/engine/seed.py`

**What:** Add the two new parameters and return them:

```python
def _build_synthesis_context(
    situation: dict[str, Any],
    arc: dict[str, Any],
    character_dynamic: dict[str, Any],
    moral_pressure: dict[str, Any],
    npc_bond: dict[str, Any] | None = None,
    scene_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = {
        "situation": situation,
        "arc": arc,
        "character_dynamic": character_dynamic,
        "moral_pressure": moral_pressure,
    }
    if npc_bond:
        ctx["npc_bond"] = npc_bond
    if scene_bundle:
        ctx["scene_bundle"] = scene_bundle
    return ctx
```

Return as optional keys — existing template renderers that iterate `pool_selection` keys won't break.

**Validation:** `_build_synthesis_context(s, a, c, m, npc_bond={"id": "x", "description": "y"})` returns dict with `"npc_bond"` key.

### Tests to write or update
None (tests deferred).

### REPOMAP updates required
- `ccya/engine/seed.py` — `_preselect_pools`, `_build_synthesis_context`

## Implementation — Phase 3: Seed prompt changes

### Context files to load
- `ccya/prompts/generate_seed_system.j2` — present_npcs section, opening_narrative section, exposition movement, pool_selection display
- `ccya/prompts/generate_seed_user.j2` — pool_selection display section

### Detailed steps

#### Step 3.1 — Render npc_bond in present_npcs section

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** In the `present_npcs` section, after the personal-connection paragraph, add:

```
{% if pool_selection and pool_selection.npc_bond %}
The narrative bond selected for this seed is:
{{ pool_selection.npc_bond.description }}

The personal-tie NPC's `relation` field and `bio` must embody this bond. Do not state the bond explicitly in the opening prose — let it surface through how the NPC behaves toward the PC.
{% endif %}
```

This goes after line 184 (`"Of the 2 in-scene NPCs..."` paragraph) and before line 186 (`"The other in-scene NPC..."` paragraph).

The compendium.npcs guidance (line ~189) already tells the LLM it can emit `bond` on compendium entries — no change needed there beyond Step 1.5.

**Why:** The previously vague "one NPC must have a personal connection" is replaced with a concrete relationship template. The LLM writes the specific bond value into the NPC's `bond` field in compendium.

**Validation:** Template renders without Jinja errors when `pool_selection.npc_bond` is present and when absent.

#### Step 3.2 — Render scene_bundle in opening_narrative exposition movement

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** In the `opening_narrative` section, after the Exposition bullet's description text, add:

```
{% if pool_selection and pool_selection.scene_bundle %}
The scene must include at least {{ pool_selection.scene_bundle.min_use }} of the following objects as interactable details that the player could examine, pick up, or use:
{% for item in pool_selection.scene_bundle.items %}- {{ item }}
{% endfor %}
Weave them into the scene naturally — do not list them or label them as "things to interact with."
{% endif %}
```

This goes inside the "2. **Exposition**" bullet, after "Do NOT describe these as 'things you could examine' — weave them into the scene as natural details." but before the closing of that bullet paragraph.

**Why:** Replaces vague "describe 2-4 environmental details" with specific objects the scene must contain. The LLM writes about the objects, which *is* exposition.

**Validation:** Template renders without Jinja errors.

#### Step 3.3 — Display npc_bond and scene_bundle in user prompt pool selection

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** In the `## Pool selection` section (lines 72-82), add after the moral_pressure line:

```
{% if pool_selection and pool_selection.npc_bond %}
NPC BOND: {{ pool_selection.npc_bond.id }} — {{ pool_selection.npc_bond.description }}
{% endif %}
{% if pool_selection and pool_selection.scene_bundle %}
SCENE OBJECTS: bundle "{{ pool_selection.scene_bundle.id }}"
{% endif %}
{% if pool_selection.scene_bundle %}
SCENE OBJECTS: bundle "{{ pool_selection.scene_bundle.id }}" — includes objects like: {{ pool_selection.scene_bundle.items[:3] | join(", ") }}{% if pool_selection.scene_bundle.items | length > 3 %}, ...{% endif %}
{% endif %}
```

**Why:** Gives the LLM a reminder of what was selected in both prompt messages (system + user). Reinforces the seed material.

**Validation:** Template renders without Jinja errors.

### Tests to write or update
None (tests deferred).

### REPOMAP updates required
- `ccya/prompts/generate_seed_system.j2` — npc_bond and scene_bundle rendering
- `ccya/prompts/generate_seed_user.j2` — pool selection display

## Implementation — Phase 4: Narrator pipeline to surface bond

### Context files to load
- `ccya/engine/npc_roster.py` — `build_npc_roster()` (full file, 85 lines)
- `ccya/engine/narrate.py` — `_known_characters_for_extract()` (lines 143-190)
- `ccya/prompts/sections/_npc_roster.j2` — narrator NPC display (full file, 17 lines)
- `ccya/prompts/sections/_npc_roster_extract.j2` — extract NPC display (full file, 6 lines)
- `ccya/prompts/extract_scene_user.j2` — scene extract prompt (line 13)
- `ccya/prompts/compact_user.j2` — compaction prompt (line 40-46)

### Detailed steps

#### Step 4.1 — Carry `bond` through `build_npc_roster` for PRESENT NPCs

**File:** `ccya/engine/npc_roster.py`

**What:** Add `"bond": n.get("bond") or None` to the PRESENT NPC dict at line 36.

Currently `present_npcs` entries carry `id, name, title, bio, presence, motivation, fear, leverage, notes, last_seen`. Add `bond`.

The SEED-time `present_npcs` entries (generated by LLM) will not have `bond` — they have `relation`. The `bond` field is set on the compendium entry. But during play, NPCs added via extraction (not seed) will also be present, and they won't have `bond` either. This is fine — bond is optional.

**Why:** When a seed-time NPC is present in a scene, the narrator sees their `bond`. This lets the narrator reference the relationship in prose.

**Validation:** `build_npc_roster([{"id": "x", "bond": "saved them"}], [], [])[0]["bond"]` → `"saved them"`.

#### Step 4.2 — Carry `bond` through `build_npc_roster` for KNOWN NPCs

**File:** `ccya/engine/npc_roster.py`

**What:** Add `"bond": n.get("bond") or None` to the KNOWN NPC dict at line 65.

Same change as step 4.1 but for the known_npcs loop.

**Why:** When a seed-time compendium NPC re-enters the scene (via extraction or narrator introduction), their bond persists.

**Validation:** `build_npc_roster([], [{"id": "x", "bond": "hometown friend"}], [])[0]["bond"]` → `"hometown friend"`.

#### Step 4.3 — Surface `bond` in `_known_characters_for_extract`

**File:** `ccya/engine/narrate.py`

**What:** Two changes:

1. In the `compact` path (lines 163-174), no change needed — compaction doesn't need bond for its NPC list.

2. In the non-compact path (lines 175-189), add `bond` to the row dict:

```python
r: dict[str, Any] = {
    "id": nid,
    "name": e.get("name") or "",
    "title": e.get("title") or "",
    "bio": bio,
}
```
Update to:
```python
r: dict[str, Any] = {
    "id": nid,
    "name": e.get("name") or "",
    "title": e.get("title") or "",
    "bio": bio,
    "bond": e.get("bond") or None,
}
```

**Why:** The extract pipeline builds its own NPC roster from compendium. Without `"bond"` here, bond data from compendium entries would not survive into the extract context.

**Validation:** `_known_characters_for_extract({"compendium": {"npcs": {"x": {"name": "X", "bond": "saved them"}}}}, compact=False)[0]["bond"]` → `"saved them"`.

#### Step 4.4 — Render `bond` in narrator NPC roster

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Add `bond` to the narrator's NPC display line. After `{% if n.leverage %} | leverage: {{ n.leverage }}{% endif %}`, add:

```
{%- if n.bond %} | bond: {{ n.bond }}{% endif %}
```

**Why:** The narrator sees "bond: you pulled them from a burning vehicle" in the NPC description, which directly informs the prose they write about that NPC's behavior.

**Validation:** Template renders with and without bond field.

#### Step 4.5 — Render `bond` in extract NPC roster

**File:** `ccya/prompts/sections/_npc_roster_extract.j2`

**What:** After `{% if n.title %} ({{ n.title }}){% endif %}`, add:

```
{% if n.bond %} | {{ n.bond }}{% endif %}
```

So the extract prompt now shows: `id | Name (Title) [KNOWN] — bio | bond: pulled them from a burning vehicle`

**Why:** The extract LLM sees the bond and can use it to inform NPC behavior during scene extraction.

**Validation:** Template renders without Jinja errors.

#### Step 4.6 — Add bond to compact prompt compendium display

**File:** `ccya/prompts/compact_user.j2`

**What:** In the "Compendium NPCs" section (line 40-46), add bond to the display line:

```
- [{{ npc_id }}] {{ npc.get("name", "?") }} (seen since T{{ npc.get("present_from_turn", "?") }}){% if npc.get("title") %} ({{ npc.get("title") }}){% endif %}{% if npc.get("aliases") %} aka {{ npc.get("aliases") | join(", ") }}{% endif %}
  bio: {{ npc.get("bio", "—") }}{% if npc.get("bond") %} | bond: {{ npc.get("bond") }}{% endif %}{% if npc.get("motivation") %} | wants: {{ npc.get("motivation") }}{% endif %}{% if npc.get("fear") %} | fears: {{ npc.get("fear") }}{% endif %}{% if npc.get("leverage") %} | leverage: {{ npc.get("leverage") }}{% endif %}
```

**Why:** Compaction summarises state. The bond should survive compaction summaries so later turns still know the relationship.

**Validation:** Template renders without Jinja errors.

### Tests to write or update
None (tests deferred).

### REPOMAP updates required
- `ccya/engine/npc_roster.py` — bond in present and known NPC dicts
- `ccya/engine/narrate.py` — bond in _known_characters_for_extract
- `ccya/prompts/sections/_npc_roster.j2` — bond rendering
- `ccya/prompts/sections/_npc_roster_extract.j2` — bond rendering
- `ccya/prompts/compact_user.j2` — bond in compendium display
