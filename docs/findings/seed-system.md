# Seed System Findings — CCYA

## Overview

The seed system initializes a CCYA game from nothing into a playable turn 0 state. It establishes the PC (player character), NPCs, location, inventory, campaign arc, opening narrative, and action choices. Everything downstream — the turn pipeline, extraction, state deltas — derives from the seed state.

Two distinct paths exist:
- **Static seed**: A pre-authored `seed_state.yaml` file in a pack directory, loaded directly
- **Dynamic seed**: An LLM generates a `SeedEnvelope` at new-game time from archetype pools defined in `scenario.yaml`

Both paths write identical-shaped state to `state.yaml` in the save directory and set the same `_seed_type` / `_pack_source` metadata flags.

---

## 1. Pack Structure

Packs live under `packs/` with four subdirectories: `default/`, `generated/`, `custom/`, `eval/`.

### 1.1 Pack Manifest (`pack.yaml`)

```yaml
id: space-western
name: "The Outer Rim — After Unification"
description: "..."
tone_tags: [frontier, gritty, scrap-tech, rebellion]
use_male_only_names: false          # bool — forces male-only name pool for historical combat genres
baseline_facts:                      # 0-3 hard world facts (loaded into world_state at seed time for static packs)
  - "The Rim is a frontier of dust..."
files:
  world: world.md                    # optional prose world bible
  scenario: scenario.yaml            # dynamic packs only
  seed_state: seed_state.yaml        # static packs only (eval harness)
name_locales:                        # weighted Faker locales for name generation
  - locale: en_US
    weight: 0.60
  - locale: es_MX
    weight: 0.25
```

Loaded by `load_pack()` in `ccya/pack.py:255-310`. The manifest is always loaded; `scenario.yaml` and `seed_state.yaml` are optional and mutually exclusive.

### 1.2 Scenario (`scenario.yaml`) — Dynamic Packs Only

The full schema is defined by `ScenarioBrief` in `ccya/pack.py:130-161`:

| Field | Type | Purpose |
|---|---|---|
| `world_name` | `str` | Evocative short name for the world |
| `constraints` | `Constraints` | Numeric rules (inventory range, stat range, prose word range, forbidden cliches) |
| `world_facts` | `list[str]` (max 8) | 3-8 durable facts injected into `scene.world_state` |
| `narrator_rules` | `list[str]` (max 12) | Tone/style rules injected into narrate system prompt |
| `world_rules` | `list[str]` (max 5) | Physical laws the seed must not contradict |
| `factions` | `list[Faction]` (max 6) | Named power groups with disposition |
| `name_locales` | `list[dict]` | Faker locale weights for name generation |
| `name_seed` | `int \| None` | Controls name selection randomness |
| `inspiration` | `Inspiration` | Quality anti-pattern guidance (pc, inventory, npcs — no prescriptive scenarios) |
| `situation_archetypes` | `list[PoolEntry]` (max 16) | Opening situation pressure types |
| `arc_categories` | `list[PoolEntry]` (max 20) | Longer-term narrative direction patterns |
| `character_dynamics` | `list[PoolEntry]` (max 12) | PC's position relative to power structures |
| `moral_pressures` | `list[PoolEntry]` (max 10) | Ethical dilemmas for immediate personal stakes |
| `npc_bonds` | `list[PoolEntry]` (max 8) | PC-NPC relationship types |
| `scene_detail_bundles` | `list[SceneDetailBundle]` (max 8) | Pre-packaged scene sensory/items/conditions |
| `currency_id` | `str` | e.g. `"credits"` |
| `starting_currency_amount` | `int` | e.g. `100` |

#### PoolEntry Structure (`ccya/pack.py:114-121`)

```python
class PoolEntry(BaseModel):
    id: str                          # snake_case, e.g. "border_clash"
    tags: list[str]                  # e.g. ["frontier", "violence", "territorial_dispute"]
    incompatible_with: list[str]      # ids within the SAME pool that conflict
    description: str = ""            # unused in current generation, kept for authoring
```

#### SceneDetailBundle (`ccya/pack.py:123-128`)

```python
class SceneDetailBundle(BaseModel):
    id: str
    items: list[str] (max 2)
    conditions: list[str] (max 2)
    sensory: list[str] (max 2)
```

### 1.3 Static Seed (`seed_state.yaml`)

Hand-authored YAML matching the full `SeedState` shape. The eval pack at `packs/eval/seed_state.yaml` is the canonical example. Structure:

```yaml
meta:
  game_name: eval
  turn: 0
  setting_pack: eval-pack
  model: ""

pc:
  name: Aren Voss
  tagline: Reluctant courier on the merchant road
  bio: |
    Mid-thirties, broad shoulders, careful with words. Took on a courier contract...
  stats:
    strength: 3
    dexterity: 3
    wits: 2
    charisma: 3
  conditions: []
  momentum: 0

location:
  id: marrows_crossing
  name: Marrow's Crossing
  description: |
    A market town built around the confluence...

inventory:
  - id: credits
    name: Credits
    amount: 500
    notes: Common coin...
  - id: iron_dagger
    name: Iron dagger
    amount: 1
    notes: Plain crossguard...

scene:
  tagline: Market town at dusk
  tags: [peaceful, start]
  present_npcs:
    - id: caron
      name: Caron
      title: Old creditor
      notes: Sits at a corner table...
      bio: A portly man in his sixties...
  world_state:
    - Marrow's Crossing is a market town...
  recent_events:
    - You arrived in Marrow's Crossing...

arc:
  visible_goal: Clear your debts and deliver the ledger...
  thematic_question: What does it cost to settle old debts...
  phase: setup
  hidden_truths:
    - Matthew Estrada is not a traveler...
  discovered_truths: []
  threads:
    - id: settle_the_debt
      summary: Settle the 500-credit debt with Caron.
      scope: arc
      active: false          # NOTE: old field — seed still uses active/dormant mix
      urgency: normal
      tags: [debt, caron, obligation]
      progress: 0
      last_seen_turn: null
  completed_threads: []
  arc_engagement: 0
  pc_drive: Prove you can handle the road...

compendium:
  npcs:
    caron:
      name: Caron
      title: Old creditor
      bio: A portly man in his sixties...
    halden:
      name: Halden
      title: Merchant...
```

Loaded via `SeedState(**yaml.safe_load(...))` in `ccya/pack.py:280-284`.

---

## 2. Personality Archetypes

Defined in `ccya/personality.py:11-120`. **12 fixed archetypes**, not loaded from data files — hardcoded registry.

```python
ARCHETYPES: dict[str, NpcPersonality] = {
    "cold_pragmatist":      NpcPersonality(id="cold_pragmatist", label="Cold Pragmatist", ...),
    "desperate_idealist":   NpcPersonality(id="desperate_idealist", label="Desperate Idealist", ...),
    "wary_opportunist":     NpcPersonality(id="wary_opportunist", label="Wary Opportunist", ...),
    "resigned_functionary": NpcPersonality(id="resigned_functionary", label="Resigned Functionary", ...),
    "volatile_loyalist":   NpcPersonality(id="volatile_loyalist", label="Volatile Loyalist", ...),
    "charming_manipulator": NpcPersonality(id="charming_manipulator", label="Charming Manipulator", ...),
    "blunt_survivor":      NpcPersonality(id="blunt_survivor", label="Blunt Survivor", ...),
    "true_believer":       NpcPersonality(id="true_believer", label="True Believer", ...),
    "detached_observer":   NpcPersonality(id="detached_observer", label="Detached Observer", ...),
    "conflict_avoidant":   NpcPersonality(id="conflict_avoidant", label="Conflict-Avoidant", ...),
    "ambitious_climber":   NpcPersonality(id="ambitious_climber", label="Ambitious Climber", ...),
    "broken_defeated":     NpcPersonality(id="broken_defeated", label="Broken/Defeated", ...),
}
```

Each `NpcPersonality` (`ccya/personality.py:11-18`) has:
- `id`: string key (e.g. `"wary_opportunist"`)
- `label`: human-readable ("Wary Opportunist")
- `traits`: tuple of 2-4 short descriptors
- `speech_hint`: one-line style note for narrator
- `motivation_keywords`: scored +2 on match
- `fear_keywords`: scored +1 on match

**Assignment algorithm** (`ccya/personality.py:142-178`): `assign_personality(motivation, fear, npc_id)` scores all archetypes against the NPC's `motivation` + `fear` text using keyword matching. Ties broken by registry insertion order. Falls back to `"wary_opportunist"` if both fields are empty or all scores are zero.

**Validation** (`ccya/personality.py:181-203`): `validate_and_resolve(personality_id)` checks against registry, returns `None` for unknown ids (caller falls back).

---

## 3. The `__seed_pools__` Archetype Pool System

### 3.1 Purpose

Dynamic seed generation converges on similar openings because the LLM reads prescriptive scenario menus in the prompt. The pool system fixes this by pre-selecting **one entry from each of 6 archetype pools** before generation, then feeding only the selected entries (not menus) into the prompt.

This gives ~7,200+ combinations per pack while maintaining genre coherence.

### 3.2 Pool Types

Six pool types in `scenario.yaml`:

| Pool | Min Count | Purpose |
|---|---|---|
| `situation_archetypes` | 10+ | Opening moment pressure type |
| `arc_categories` | 15+ | Longer-term narrative direction |
| `character_dynamics` | 8-10 | PC's social position relative to power |
| `moral_pressures` | 6+ | Ethical dilemma driving immediate stakes |
| `npc_bonds` | 6+ | PC-NPC relationship type |
| `scene_detail_bundles` | 6+ | Pre-packaged scene sensory/items/conditions |

### 3.3 Pre-Selection Mechanism (`ccya/engine/seed.py:85-141`)

```python
def _select_from_pool(pool_items: list[Any], seed: int, field_name: str) -> dict[str, Any]:
    """Select ONE entry from a pool using hash-based deterministic selection."""
    idx = int(sha256(f"{seed}:{field_name}".encode()).hexdigest(), 16) % len(pool_items)
    return cast(dict[str, Any], pool_items[idx].model_dump())
```

**Determinism**: Uses `sha256(f"{seed}:{field_name}")` — the same `(name_seed, field_name)` always selects the same pool entry. `name_seed` comes from `scenario.name_seed` (static int in scenario.yaml) or is randomly generated at runtime if `None`.

```python
def _preselect_pools(scenario: Any, name_seed: int) -> dict[str, Any]:
    """Pre-select from archetype pools deterministically per name_seed."""
    situation = _select_from_pool(scenario.situation_archetypes, name_seed, "situation_archetype")
    arc = _select_from_pool(scenario.arc_categories, name_seed, "arc_category")
    character_dynamic = _select_from_pool(scenario.character_dynamics, name_seed, "character_dynamic")
    moral_pressure = _select_from_pool(scenario.moral_pressures, name_seed, "moral_pressure")
    npc_bond = _select_from_pool(scenario.npc_bonds, name_seed, "npc_bond")
    scene_bundle = _select_from_pool(scenario.scene_detail_bundles, name_seed, "scene_detail_bundle")
    return _build_synthesis_context(situation, arc, character_dynamic, moral_pressure, npc_bond, scene_bundle)
```

Called in `_build_generate_seed_messages()` at `ccya/engine/seed.py:172-175`:
```python
pool_selection = _preselect_pools(scenario, name_seed)
ctx = {
    "scenario": scenario,
    "overrides": overrides if (overrides and not overrides.is_empty()) else None,
    "name_pool": name_pool,
    "name_seed": name_seed,
    "pool_selection": pool_selection,  # injected into prompt templates
}
```

### 3.4 Pool Selection in State

After successful seed generation, the selected pool entries are stored in state.yaml at the **root level** (not inside `meta`):

```yaml
__seed_pools__:
  arc:
    description: ''
    id: supply_line_warfare
    incompatible_with: []
    tags: [logistics, trade, blockade_breaking]
  character_dynamic:
    description: ''
    id: coalition_deserter
    incompatible_with: []
    tags: [coalition, desertion, fugitive_status]
  moral_pressure:
    description: ''
    id: corporate_encroachment
    incompatible_with: []
    tags: [corporations, colonization, exploitation]
  npc_bond:
    description: The NPC served on the same ship as the PC...
    id: old_crewmate
    incompatible_with: []
    tags: [crew, ship, shared_mileage]
  scene_bundle:
    conditions: [smoke from a hookah hanging in the air, a back door propped open]
    id: saloon_interior
    items: [a card table with a marked deck in the discard, ...]
    sensory: [the jangle of an out-of-tune piano, ...]
  situation:
    description: ''
    id: border_clash
    incompatible_with: []
    tags: [frontier, violence, territorial_dispute]
```

Set in `_apply_seed_to_save_dir()` at `ccya/server/routes.py:90-91`:
```python
if pool_selection:
    seed_dict["__seed_pools__"] = pool_selection
```

### 3.5 Pool Selection in Prompts

**System prompt** (`generate_seed_system.j2:16-24`): The pool selection is injected as a synthesized context block:
```
## Seeded context
Four independently selected narrative dimensions. They are NOT a menu — weave them into something coherent.

- **SITUATION ARCHETYPE** (`border_clash`): The pressure or tension the player walks into.
- **ARC CATEGORY** (`supply_line_warfare`): Longer-term narrative direction...
- **CHARACTER DYNAMIC** (`coalition_deserter`): The PC's position relative to power structures...
- **MORAL PRESSURE** (`corporate_encroachment`): The ethical dilemma driving immediate personal stakes.
```

**User prompt** (`generate_seed_user.j2:61-81`): Detailed pool injection with tags and descriptions:
```
## Pool selection (independently chosen — weave them together)

SITUATION ARCHETYPE: border_clash (tags: frontier, violence, territorial_dispute)
ARC CATEGORY: supply_line_warfare (tags: logistics, trade, blockade_breaking)
CHARACTER DYNAMIC: coalition_deserter (tags: coalition, desertion, fugitive_status)
MORAL PRESSURE: corporate_encroachment (tags: corporations, colonization, exploitation)
NPC BOND: The NPC served on the same ship as the PC — not friends, but the kind of bond formed by shared cargo holds and close calls.
SCENE BUNDLE "saloon_interior":
    Objects: a card table with a marked deck in the discard, a synthesizer dispensing something brown into a chipped cup
    Conditions: smoke from a hookah hanging in the air, a back door propped open
    Sensory: the jangle of an out-of-tune piano, the hum of a cooler unit cycling
```

---

## 4. Dynamic Seed Generation Pipeline

### 4.1 Entry Point: `POST /new-game`

In `ccya/server/routes.py:383-482`:

```
1. Parse form fields (pack_id, pc_name, pc_tagline, pc_stats, pc_hints, npc_hints, location_hints, arc_hints, free_form)
2. Build PlayerOverrides from form fields
3. Detect hint presence: has_hints = not overrides.is_empty()
4a. If has_hints → load static pack seed (pack.seed)
4b. If no hints → call generate_seed() via LLM
```

### 4.2 Hint Detection Decision Tree

```
has_hints = not overrides.is_empty()
  overrides.is_empty() = all of these are empty:
    pc_hints, npc_hints, location_hints, arc_hints, free_form

If pc_name or pc_tagline are provided AND overrides exist:
  → pc_hints gets "Name the PC '{pc_name}'. Tagline: '{pc_tagline}'." prepended
  → has_hints still controls static vs dynamic (if overrides were non-empty before this, remains True)
```

Note: If a user just fills in PC name/tagline and nothing else, the merged hint still makes `has_hints=True`, which falls back to static pack seed. Only fully empty overrides trigger dynamic generation.

### 4.3 `generate_seed()` Function (`ccya/engine/seed.py:215-460`)

```python
async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> tuple[SeedEnvelope, dict[str, Any] | None]:
```

**Steps:**

1. **Validate pack type** (`seed.py:223-224`): Requires `pack.scenario` (not `pack.seed`). Raises `ValueError` if passed a static seed pack.

2. **Build Jinja env** (`seed.py:226-227`): Loads templates from `ccya/prompts/`.

3. **Build messages** via `_build_generate_seed_messages()` (`seed.py:237`):
   - Generates name pool via `generate_name_pool()` from `ccya/engine/names.py`
   - If `male_only_names` flag set in manifest, generates male-only NPC/PC pools
   - `name_seed` randomized if `scenario.name_seed is None`
   - **Pool pre-selection** via `_preselect_pools(scenario, name_seed)` at line 173
   - Returns `[system_msg, user_msg], pool_selection`

4. **LLM call** (`seed.py:254-261`):
   - Temperature: `config.generate_seed_temperature` (default 0.9)
   - `top_p`: `config.generate_seed_top_p`
   - Retry: `1 + config.max_llm_retries` attempts

5. **Response parsing** (`seed.py:284-297`):
   - Strip `<think>` blocks via `strip_thinking()`
   - Extract JSON via `_find_json()`
   - Unwrap if nested under `"seed_state"` key
   - Parse into `SeedEnvelope` Pydantic model

6. **Sanitization** (`seed.py:307`): `_sanitize_envelope()` strips non-ASCII from all name fields; ensures at least 1 NPC has `presence="present"`.

7. **Validation** (`seed.py:308`): `_validate_seed_envelope()` checks PC has at least 2 name parts.

8. **Personality assignment** (`seed.py:310-342`):
   ```python
   for npc_id, npc_entry in envelope.seed_state.compendium.npcs.items():
       if not hasattr(npc_entry, "personality") or not getattr(npc_entry, "personality"):
           arch = assign_personality(motivation=..., fear=..., npc_id=npc_id)
           object.__setattr__(npc_entry, "personality", arch.id)
       else:
           resolved = validate_and_resolve(getattr(npc_entry, "personality"))
           if resolved is None:
               # unknown id → fall back to assign_personality()
   ```

9. **Thread limit enforcement** (`seed.py:362-398`):
   - Max 2 non-dormant threads at game start
   - Excess non-dormant → forced to `dormant=True`, `urgency="background"`
   - All dormant threads → `urgency="background"` (never `"urgent"`)
   - Sets `urgency_set_turn` and `added_turn` to current turn for tracking

10. **World facts injection** (`seed.py:400-414`):
    - Prepends `scenario.world_facts` to `scene.world_state` as `WorldStateFact(id=f"baseline_{i}", tier="permanent")`
    - Deduplicates against existing LLM-generated facts

11. **Currency injection** (`seed.py:420-431`):
    - If `scenario.currency_id` is set and no inventory item with that ID exists → appends `InventoryItem(id=scenario.currency_id, name=..., amount=scenario.starting_currency_amount)`

12. **Soft validation** (`seed.py:433-438`): Checks prose word count against `constraints.prose_word_range` and forbids cliches; logs warnings.

13. **Hard validation** (`seed.py:441-448`): Ensures at least 1 NPC has `presence="present"`, else raises `ValueError`.

14. **Returns**: `(SeedEnvelope, pool_selection | None)`

---

## 5. Static Seed Loading

For packs with `seed_state.yaml` (eval harness and packs with hints provided):

### 5.1 Route Handler (`routes.py:451-461`)

```python
if has_hints:
    pack = _app_mod._active_pack
    if pack.seed is None:
        return HTMLResponse("<p>This pack has no static seed state...</p>")
    seed = pack.seed.model_dump(mode="json")
    seed["meta"]["setting_pack"] = _app_mod._pack_id
    if pc_stats_dict:
        seed.setdefault("pc", {})["stats"] = pc_stats_dict
    _apply_seed_to_save_dir(seed, None, None, pack_type="static", pack_source=_app_mod._pack_id)
```

Note: No `opening_narrative`, no `actions`, no `__seed_meta__`, no `__seed_pools__` for static seeds.

### 5.2 Personality Assignment for Static Seeds

Via `_assign_seed_personalities()` in `ccya/state/io.py:21-36`:
```python
def _assign_seed_personalities(state: dict[str, Any]) -> None:
    """Assign personality archetype ids to any NPCs missing one in the seed state."""
    from ccya.personality import ARCHETYPES, assign_personality

    npcs = (state.get("compendium") or {}).get("npcs", {})
    for npc_id, entry in npcs.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("personality") and entry["personality"] in ARCHETYPES:
            continue  # Already has valid personality
        arch = assign_personality(
            motivation=entry.get("motivation"),
            fear=entry.get("fear"),
            npc_id=npc_id,
        )
        entry["personality"] = arch.id
```

Called from `init_save_dir()` at `ccya/state/io.py:152` before `save_state()`.

---

## 6. `_apply_seed_to_save_dir()` — Final Seed Application

Defined at `ccya/server/routes.py:64-99`. This is the last step in both static and dynamic paths.

```python
def _apply_seed_to_save_dir(
    seed_dict: dict[str, Any],
    opening_narrative: str | None = None,
    actions: list[str] | None = None,
    *,
    outcome_summary: str = "",
    pack_type: str | None = None,       # "static" or "dynamic"
    pack_source: str | None = None,      # pack ID
    pool_selection: dict[str, Any] | None = None,
) -> None:
    dir_name = _generate_save_dir_name(_app_mod._active_pack.manifest.name)
    save_dir = Path("saves") / dir_name
    _app_mod.SAVE_DIR = save_dir

    seed_dict.setdefault("meta", {})["model"] = _app_mod.engine_config.model
    if pack_type is not None:
        seed_dict.setdefault("meta", {})["_seed_type"] = pack_type
    if pack_source is not None:
        seed_dict.setdefault("meta", {})["_pack_source"] = pack_source
    if opening_narrative is not None and actions is not None:
        seed_dict["__seed_meta__"] = {
            "opening_narrative": opening_narrative,
            "actions": actions,
            "outcome_summary": outcome_summary,
        }
    if pool_selection:
        seed_dict["__seed_pools__"] = pool_selection

    init_save_dir(save_dir, seed_dict)

    # Set module-level dynamic pack variables for UI
    if opening_narrative is not None:
        _app_mod._dynamic_opening = opening_narrative
    else:
        _app_mod._dynamic_opening = ""
    if actions is not None:
        _app_mod._dynamic_opening_actions = actions
    else:
        _app_mod._dynamic_opening_actions = []
```

---

## 7. `init_save_dir()` — Filesystem Write

Defined at `ccya/state/io.py:150-163`:

```python
def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    _assign_seed_personalities(seed)          # Personality assignment for static seeds
    save_state(save_dir, seed)                 # Atomic write: state.yaml
    chronicle_path = save_dir / "chronicle.md"
    seed_meta = seed.get("__seed_meta__") or {}
    opening = seed_meta.get("opening_narrative")
    if opening:
        chronicle_path.write_text(f"\n## Turn 0 — Seed\n\n{opening.strip()}")
    else:
        chronicle_path.write_text("")
    (save_dir / "events.jsonl").write_text("")  # Clear events log
    (save_dir / "state_snapshot.yaml").unlink(missing_ok=True)  # Remove stale snapshot
```

---

## 8. State Metadata Fields

Three metadata fields track seed provenance:

### `meta._seed_type` (string)
- `"static"` — loaded from pre-authored `seed_state.yaml`
- `"dynamic"` — generated via LLM

### `meta._pack_source` (string)
- The pack ID that was used: e.g. `"space-western"`, `"noir-1930s"`, `"eval-pack"`

### `__seed_meta__` (root-level, dynamic packs only)
```yaml
__seed_meta__:
  opening_narrative: "..."   # Full prose opening, written to chronicle.md
  actions:
    - "Confront the guard directly."
    - "Try to slip past while he's distracted."
    - "Look for another way around."
    - "Talk your way through with a cover story."
  outcome_summary: "A guard blocks the checkpoint, watching for contraband."
```

### `__seed_pools__` (root-level, dynamic packs only)
The full pool selection dict (see section 3.4 above). Persisted for debugging, turn viewer display, and eval audit.

---

## 9. SeedEnvelope Schema (LLM Output Contract)

The LLM generates JSON conforming to this schema (from `generate_seed_system.j2:28-43`):

```typescript
{
  seed_state: {
    meta: {turn: 0, model: string, setting_pack: string, session_name: string},
    pc: {name: string, tagline: string, bio: string, stats: {strength, dexterity, wits, charisma}, conditions: []},
    location: {id: snake_case, name: string, description: string},
    inventory: Array<{id: snake_case, name: string, notes?: string, amount: int}>,
    scene: {tags: string[], world_state: string[]},
    compendium: {npcs: {snake_case: {name: string, title: string, bio: string, presence: "present"|"nearby"|"known", bond?: string, motivation?: string, fear?: string, leverage?: string, personality?: archetype_id}}},
    arc: {visible_goal: string, goal_context: string, threads: ArcThread[], completed_threads: null}
  },
  opening_narrative: string,
  outcome_summary: string,
  actions: string[]   // exactly 4 items, 7-10 words each
}
```

**Defined as Pydantic** in `ccya/pack.py:75-89`:
```python
class SeedEnvelope(BaseModel):
    seed_state: SeedState
    opening_narrative: str = Field(min_length=50)
    actions: list[str] = Field(min_length=4, max_length=4)
    arc: CampaignArc | None = None
    outcome_summary: str = ""
```

---

## 10. NPC Field Requirements (from seed prompt)

### Named NPCs (proper name in `name` field)
- Required: `bio`, `personality` (from 12-archetype fixed list), 2+ of `{motivation, fear, leverage, bond}`
- Important NPCs (arc goal characters, faction leaders): 4-5 of the 5 fields

### Unnamed NPCs (descriptive label in `name` + same string in `aliases`)
- `bio` only. No personality fields until the NPC gets a proper name.

### Group NPCs
- `name` field states **exact count as spelled-out integer**: `"Two militia guards"`, not `"a few guards"`
- `id` field: type-level ID without quantity (e.g., `militia_guards`)
- `bio`: distinguishing features per individual

### Compendium NPCs (known-to-but-not-present)
- Generated at seed time: 2-3 additional NPCs beyond the 2 present NPCs
- Fields: `name`, `title`, `bio` only
- No `personality`, `motivation`, `fear`, `leverage`, `relation`, `notes` fields — engine-managed at runtime

---

## 11. Thread Rules at Seed Time

From `generate_seed_system.j2:142-168`:

- **IDs**: 2-4 word broad conceptual buckets, no proper nouns (e.g. `council_conspiracy` ✓, `the_missing_ledger` ✗)
- **Summaries**: one sentence (8-15 words), describe a SITUATION not an objective
- **Types** (required): `"threat"`, `"opportunity"`, `"complication"`, `"revelation"`
  - At least one with `type == "threat"`
  - At least one with `type != "threat"`
- **Count limits**:
  - 1-2 threads with `dormant: false` (prefer 1)
  - Remaining threads `dormant: true`
  - Up to 3 dormant threads
  - Total: 4-5 threads (min 3, max 6)
- **Urgency at seed**: non-dormant → `"normal"` or `"urgent"` (prefer `"normal"`); dormant → `"background"` only

---

## 12. Hard Constraints (from `scenario.constraints`)

Validated by `_soft_validate_seed()` at `seed.py:192-212`:

```python
# From space-western scenario.yaml:
inventory_size_range: [4, 7]
pc_stat_range: [1, 4]
pc_stat_total_range: [9, 12]       # Note: space-western has 9-12, others use 10-14 or 12-18
prose_word_range: [530, 930]
required_inventory_kinds: [weapon, tool]
forbid_cliches: [list of banned tropes...]
```

---

## 13. Re-roll Path

`POST /new-game/reroll` (`routes.py:485-507`) calls `generate_seed()` again with the same pack/overrides, producing a new `SeedEnvelope`. Writes to the **same save directory** (unlike fresh new-game which creates a new timestamped directory). The opening narrative and actions are returned as HTML fragments for HTMX swap-in on the client side.

---

## 14. Eval Harness Seed Path

For `ev.py eval` runs (`ccya/ev/eval.py:46-60`):

```python
def _create_eval_session(scenario: Scenario) -> Path:
    session_dir = EV_SAVES_DIR / f"eval_{scenario.id}_{ts}_{rand}"
    session_dir.mkdir(parents=True, exist_ok=True)

    state = _default_state()
    state["meta"]["session_name"] = scenario.id
    if scenario.seed_overrides:
        _apply_seed_overrides(state, scenario.seed_overrides)  # Direct state patches

    init_save_dir(session_dir, state)
    return session_dir
```

Uses `_default_state()` (empty shell) + optional `seed_overrides` from the scenario YAML (direct `.`-path patches like `pc.name: "Aren Voss"`). Does NOT use the full seed generation pipeline — eval seeds are minimal shells.

---

## 15. Key File Reference

| File | Responsibility |
|---|---|
| `ccya/pack.py` | `Pack`, `SeedState`, `SeedEnvelope`, `ScenarioBrief`, `PoolEntry`, `PlayerOverrides` models; `load_pack()` |
| `ccya/personality.py` | 12 archetype registry; `assign_personality()`, `validate_and_resolve()` |
| `ccya/engine/seed.py` | `generate_seed()` async function; `_sanitize_envelope()`, `_select_from_pool()`, `_preselect_pools()`, `_build_generate_seed_messages()`, thread limit enforcement |
| `ccya/state/io.py` | `init_save_dir()`, `save_state()`, `load_state()`, `_assign_seed_personalities()`, `_default_state()` |
| `ccya/server/routes.py` | `_apply_seed_to_save_dir()`, `new_game` handler, `new_game_reroll` handler |
| `ccya/prompts/generate_seed_system.j2` | System prompt for seed generation LLM |
| `ccya/prompts/generate_seed_user.j2` | User prompt for seed generation LLM |
| `ccya/models/state.py` | `ArcThread`, `CampaignArc`, `Condition`, `InventoryItem`, `WorldStateFact`, `ThreadUpdate`, `ThreadResolution`, `ArcResolution` |
| `ccya/ev/init.py` | `cmd_init()` — creates save dir + ev.yaml for ev.py sessions |
| `ccya/ev/eval.py` | `_create_eval_session()` — eval harness seed path |

---

## 16. Complete Data Flow: New Game → Turn 0

```
User POST /new-game (with or without hints)
    │
    ▼
routes.py: new_game()
    │  1. Parse form fields → PlayerOverrides
    │  2. has_hints = not overrides.is_empty()
    │
    ├─► has_hints = TRUE → static path
    │       pack.seed.model_dump() → seed_dict
    │       seed_dict["meta"]["setting_pack"] = pack_id
    │       pc_stats hard override if provided
    │       _apply_seed_to_save_dir(seed_dict, None, None, pack_type="static", ...)
    │
    └─► has_hints = FALSE → dynamic path
            generate_seed(pack, config, overrides=None)
                │
                ├─► _build_generate_seed_messages()
                │       generate_name_pool() → name_pool
                │       name_seed = scenario.name_seed or random
                │       _preselect_pools(scenario, name_seed) → pool_selection
                │           _select_from_pool() × 6 (sha256 hash-based)
                │       Jinja render: generate_seed_system.j2 + generate_seed_user.j2
                │       ctx = {scenario, overrides, name_pool, name_seed, pool_selection}
                │
                ├─► llm_chat() → SeedEnvelope JSON
                │
                ├─► Parse + validate SeedEnvelope
                │
                ├─► _sanitize_envelope() — strip non-ASCII, ensure present NPC
                │
                ├─► Personality assignment:
                │       for each compendium NPC without personality:
                │           assign_personality(motivation, fear) → archetype id
                │       for each with personality:
                │           validate_and_resolve() → fallback if unknown
                │
                ├─► Thread limit enforcement (max 2 non-dormant, etc.)
                │
                ├─► World facts injection (prepend scenario.world_facts)
                │
                └─► Currency injection (if scenario.currency_id set)

            seed = envelope.seed_state.model_dump()
            _apply_seed_to_save_dir(seed, envelope.opening_narrative, envelope.actions,
                                    outcome_summary=envelope.outcome_summary,
                                    pack_type="dynamic", pack_source=pack_id,
                                    pool_selection=pool_selection)

    │
    ▼
_apply_seed_to_save_dir()
    │  SAVE_DIR = Path("saves/{pack-name}-{date}")
    │  seed_dict["meta"]["_seed_type"] = "static" | "dynamic"
    │  seed_dict["meta"]["_pack_source"] = pack_id
    │  seed_dict["meta"]["model"] = config.model
    │  seed_dict["__seed_meta__"] = {opening_narrative, actions, outcome_summary}
    │  seed_dict["__seed_pools__"] = pool_selection
    │
    ▼
init_save_dir(SAVE_DIR, seed_dict)
    │  mkdir SAVE_DIR
    │  _assign_seed_personalities(seed_dict)  ← for static seeds (dynamic already done)
    │  save_state(SAVE_DIR, seed_dict)  → state.yaml (atomic write)
    │  chronicle.md = "## Turn 0 — Seed\n\n{opening_narrative}"
    │  events.jsonl = "" (cleared)
    │  state_snapshot.yaml deleted
    │
    ▼
state.yaml written to disk
    turn = 0
    _seed_type / _pack_source in meta
    __seed_meta__ / __seed_pools__ at root (dynamic only)
    All PCs, NPCs, inventory, arc, world_state, compendium established

    │
    ▼
Turn 0
    load_state() → full state dict
    run_turn() → rules → narrate → scene/state/storytell extract
    apply_delta() → state updates
    save_state() → new state.yaml
```

---

## 17. Summary: What Each Subsystem Owns

| Concern | Owner |
|---|---|
| Pack manifest + loading | `ccya/pack.py` |
| 12 personality archetypes | `ccya/personality.py` (hardcoded registry) |
| 6 generation archetype pools | `scenario.yaml` per pack (PoolEntry lists) |
| Pool pre-selection (hashing) | `ccya/engine/seed.py:_preselect_pools()` |
| Dynamic seed LLM generation | `ccya/engine/seed.py:generate_seed()` |
| Seed templates (Jinja2) | `ccya/prompts/generate_seed_system.j2`, `generate_seed_user.j2` |
| Seed → filesystem | `ccya/state/io.py:init_save_dir()` |
| Seed → save dir routing | `ccya/server/routes.py:_apply_seed_to_save_dir()` |
| Static seed personality assignment | `ccya/state/io.py:_assign_seed_personalities()` |
| NPC roster (presence filtering) | `ccya/engine/npc_roster.py:build_npc_roster()` |
| State metadata flags | Written by `_apply_seed_to_save_dir()`, read by turn viewer |

---

## 18. Open Questions / Items for Revamp

1. **`_seed_pools__` stored at root level** — this is non-standard; all other seed-derived data is inside `meta`. Should `__seed_pools__` move into `meta.__seed_pools__`?

2. **`__seed_meta__` also at root level** — same concern. Both root-level keys are written and read by different parts of the system without a shared constant.

3. **Static seed files still use old `active`/`dormant` mix** — the eval `seed_state.yaml` uses both `active: false` and `dormant` fields. The model validator coerces `active → dormant` but this is technical debt.

4. **`name_seed` vs `seed` parameter confusion** — `generate_seed()` has a `seed: int | None` parameter that is never used (the actual randomness comes from `scenario.name_seed` or a random int generated inside `_build_generate_seed_messages`). Dead parameter.

5. **Pool `description` field is unused** — `PoolEntry.description` exists in the model but is never rendered into prompts. Only `id`, `tags`, `incompatible_with`, and `npc_bond.description` are used.

6. **No validation of `incompatible_with` at load time** — nothing checks that `incompatible_with` ids actually exist in the same pool. Bad YAML entries silently never match.

7. **`_resolve_npc_personalities()` in routes.py** — this UI helper resolves archetype IDs to labels/traits at panel render time. Personality resolution happens in three places: seed generation (runtime assignment), `_assign_seed_personalities()` (static seeds), and `_resolve_npc_personalities()` (UI display). The separation is confusing.
