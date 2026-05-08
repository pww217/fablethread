Now I have enough. Here's the full plan:

***

# Plan: Custom World Generator (`generate_pack`)

## Status
`complete`

## Part of
`p4-world` (new effort — world generation)

## Dependencies
- No completed plans required first.
- **Conflicts with:** `docs/plans/p4-world/dynamic-storytelling.md` — that plan adds faction/location pools to engine state; this plan moves faction/location *generation* to pack creation time. Recommend sequencing this plan first: factions/locations live in the pack, `dynamic-storytelling.md` then consumes them from pack rather than generating in-engine. Coordinate before executing `dynamic-storytelling.md`.
- **Supersedes scope of:** `static-pack-tearout.md` — read it before executing Phase 1. If that plan is already merged, skip anything it already did.

## Objective
Replace the current two-file dynamic pack system (`world.md` + `scenario.yaml` + `pack.yaml` + `style.md`) with a single consolidated `scenario.yaml` that contains everything needed to generate a world, and introduce a `generate_pack()` flow that accepts a player concept (free-form text + structured prompts across 4–5 WorldBrief sections) and produces a fully playable custom pack stored in `packs/custom/`. This enables players to author worlds from scratch rather than choosing from hand-built settings. Also removes `extract_examples` entirely, removes `mode: dynamic` from manifests (all generated packs are dynamic by definition), cleans up the narrate prompt to bold NPC/item names on turn 1 the same way turns 2+ do it, and improves the opening narrative to feel organic rather than structured.

## Non-goals
- Does not implement the UI for the WorldBrief input form — that is a separate server/frontend task.
- Does not implement `static` pack tearout or deprecate existing static packs — they continue loading as-is.
- Does not implement location-keyed NPC storage (`dynamic-storytelling.md` scope).
- Does not rewrite any extraction prompts.
- Does not migrate existing `packs/flooded-world/` etc. to new schema — they remain with old files until a separate migration pass.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/pack.py` | modify | New schema: `ScenarioBrief` expands to absorb pack.yaml fields + style + factions + locations + name locales; remove `ExtractExample`, `PackFiles`, `mode` literal, `version`; add `WorldBrief`, `Faction`, `NamedLocation`, `generate_pack()`; `load_pack()` gains namespace routing |
| `ccya/engine/seed.py` | modify | Consume `scenario.factions`, `scenario.locations`, `scenario.name_locales` directly; remove `parse_world_facts` call path; inject faction/location name pool into seed prompt |
| `ccya/engine/extraction.py` | modify | Remove `pack_examples` parameter from `_extract_state_messages` and `_run_extraction_pipeline`; remove `ExtractExample` import |
| `ccya/engine/narrate.py` | modify | Pass `pack.scenario.factions` and `pack.scenario.locations` into narrate context as `world_factions`/`world_locations` |
| `ccya/engine/turn.py` | modify | Remove `pack_examples` from `_run_extraction_pipeline` call |
| `ccya/prompts/generate_seed_system.j2` | modify | Consume new scenario shape; add faction pool + location pool to context; improve opening_narrative guidance for organic feel; add name seed injection |
| `ccya/prompts/generate_seed_user.j2` | modify | Remove `world_text`/`style_text` sections (now in scenario); render factions + locations from scenario; pass `name_seed` |
| `ccya/prompts/narrate_system.j2` | modify | Clarify bold rule applies on turn 1 the same as other turns |
| `packs/default/` | create (dir) | Move all existing hand-built packs here |
| `packs/custom/` | create (dir, gitkeep) | Destination for `generate_pack()` output |
| `packs/flooded-world/scenario.yaml` | modify | Rewrite to new consolidated schema (migration example) |
| `packs/AUTHORING.md` | delete | Replaced by in-code docstrings and this plan |
| `docs/REPOMAP/pack.md` | update | Reflect new models, `generate_pack()`, namespace routing |
| `docs/plans/TODO.md` | update | Add this plan under P4 |

## Firm decisions

1. **`extract_examples` is deleted.** `ExtractExample`, `PackFiles.extract_examples`, `Pack.extract_examples`, `_extract_state_messages(pack_examples=...)`, and the `examples_data` loading path in `load_pack()` are all removed. The engine must not choke if the old field appears in a `pack.yaml` — `PackManifest` uses `model_config = {"extra": "ignore"}` so it silently passes unknown keys.
2. **`mode` field is removed from `PackManifest`.** All new packs are generated. Existing static packs continue loading via the `seed`/`opening` path in `load_pack()` — the loader auto-detects by presence of `seed_state.yaml` vs `scenario.yaml`, not by a `mode` field.
3. **`version` field is removed from `PackManifest`.** No backwards compatibility.
4. **`scenario.yaml` absorbs everything.** `pack.yaml` retains only identity fields (`id`, `name`, `description`, `genre`, `tone_tags`). All generation inputs (constraints, inspiration, style rules, world facts, factions, locations, name locales, baseline facts) live in `scenario.yaml` as a single `ScenarioBrief` with new top-level sections.
5. **`world.md` is dropped for new packs.** Its facts fold into `scenario.world_facts` (list of strings, max 8). For generation, the `WorldBrief` concept/tone/etc. sections replace it entirely. Existing packs that still have `world.md` keep working — `load_pack()` reads it as `Pack.world_text` legacy fallback.
6. **`style.md` is dropped for new packs.** Its rules fold into `scenario.narrator_rules` (list of strings, max 12). Same legacy fallback as world.md.
7. **Factions and locations live in `scenario.yaml`, injected into narrate context each turn.** Not in engine state — the narrator reads them from the pack, not from `scene.world_state`. The engine passes `pack.scenario.factions` and `pack.scenario.locations` into `_build_narrate_messages()` context.
8. **`packs/default/` and `packs/custom/` namespace split.** `load_pack(pack_id, packs_dir)` now accepts `pack_id` as either a bare slug (searches both namespaces, default first) or a namespaced slug `"default/flooded-world"` or `"custom/my-world"`. `list_packs()` aggregates both.
9. **Seed number for name randomness.** `generate_pack()` generates a random integer seed and includes it in the prompt as `name_seed`. The LLM is instructed to use it as a hash to select from the name pool rather than defaulting to its most-associated names. This is not cryptographic — it's a cheap way to vary name selection away from defaults. The seed is stored in `scenario.yaml` as `name_seed: int` so replays are consistent.
10. **`AUTHORING.md` is deleted.** Its structural documentation is replaced by docstrings in `pack.py` and the new `WorldBrief` model field descriptions.
11. **Opening narrative on turn 1 uses the same bold rules as turns 2+.** The `generate_seed_system.j2` prompt instructs: bold NPC names on first introduction, bold inventory item names on first use. No special treatment.
12. **Opening narrative quality guidance.** The `generate_seed_system.j2` prompt replaces the current "3-4 paragraphs: 1. who you are, 2. local situation, 3. scene" structure with guidance for organic flow: start mid-scene with sensory specificity, weave in character context without a biography paragraph, let quest tension surface through what the player observes rather than what the narrator summarizes.
13. **`forbid_cliches` stays in constraints but is not injected into the narrate prompt.** It is seed-generation only. The current narrate prompt does not receive it and the plan will not add it there.

***

## Implementation — Phase 1: Remove `extract_examples` + clean dead code

### Context files to load
- `ccya/pack.py`
- `ccya/engine/extraction.py`
- `ccya/engine/turn.py`
- `docs/REPOMAP/pack.md`

### Overview
Delete `ExtractExample` model, `PackFiles.extract_examples`, `Pack.extract_examples`, the `pack_examples` kwarg from `_extract_state_messages` and `_run_extraction_pipeline`, the `examples_data` loading block in `load_pack()`, and the `ExtractExample` import in `extraction.py`. Add `extra: "ignore"` to `PackManifest` so old `pack.yaml` files with stale fields don't crash.

### Detailed steps

#### Step 1.1 — Remove `ExtractExample` and `PackFiles` from `pack.py`

**File:** `ccya/pack.py`

**What:** Delete the `ExtractExample` class entirely. Delete the `PackFiles` class entirely. Remove `PackManifest.files` field (replace with direct optional `scenario_file`, `seed_file`, `opening_file` fields — or simpler: just rely on filename conventions in `load_pack()` without a manifest file map). Remove `Pack.extract_examples` field. Add `model_config = {"extra": "ignore"}` to `PackManifest`.

**Why:** `ExtractExample` is unused in the narration path; keeping it creates false documentation. `PackFiles` is indirection with no benefit — `load_pack()` can use filename conventions directly.

**Code Snippet**
```python
class PackManifest(BaseModel):
    model_config = {"extra": "ignore"}
    id: str
    name: str
    description: str = ""
    genre: str = ""
    tone_tags: list[str] = Field(default_factory=list)
    baseline_facts: list[str] = Field(default_factory=list, max_length=3)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    # mode and version removed — no backwards compat
```

In `load_pack()`, replace the `files = manifest.files` block with direct convention-based loading:
```python
def load_pack(pack_id: str, packs_dir: Path) -> Pack:
    pack_dir = _resolve_pack_dir(pack_id, packs_dir)  # new helper — see Step 1.3
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing pack.yaml in {pack_dir}")
    with open(manifest_path) as f:
        manifest_data = yaml.safe_load(f) or {}
    manifest = PackManifest(**manifest_data)

    seed: SeedState | None = None
    opening_text = ""
    opening_actions: list[str] = []
    world_text = ""
    scenario: ScenarioBrief | None = None

    # Static mode: seed_state.yaml + opening_scene.md
    seed_path = pack_dir / "seed_state.yaml"
    if seed_path.exists():
        seed_data = yaml.safe_load(seed_path.read_text()) or {}
        opening_actions = seed_data.pop("opening_actions", [])
        seed = SeedState(**seed_data)
        opening_path = pack_dir / "opening_scene.md"
        opening_text = opening_path.read_text() if opening_path.exists() else ""

    # Dynamic mode: scenario.yaml (new consolidated schema)
    scenario_path = pack_dir / "scenario.yaml"
    if scenario_path.exists():
        scenario_data = yaml.safe_load(scenario_path.read_text()) or {}
        scenario = ScenarioBrief(**scenario_data)

    # Legacy fallback: world.md and style.md (old dynamic packs)
    world_path = pack_dir / "world.md"
    world_text = world_path.read_text() if world_path.exists() else ""
    style_path = pack_dir / "style.md"
    style_text = style_path.read_text() if style_path.exists() else ""

    return Pack(
        manifest=manifest,
        style_text=style_text,
        seed=seed,
        opening_text=opening_text,
        opening_actions=opening_actions,
        world_text=world_text,
        scenario=scenario,
    )
```

**Validation:** `load_pack("flooded-world", packs_dir)` succeeds. `load_pack("muggle-world", packs_dir)` succeeds. A `pack.yaml` with `extract_examples: extract_examples.yaml` in it does not raise.

#### Step 1.2 — Remove `pack_examples` from `extraction.py`

**File:** `ccya/engine/extraction.py`

**What:** Remove `pack_examples: list["ExtractExample"] | None = None` parameter from `_extract_state_messages`. Remove the `band_examples` filter block. Remove `band_examples` from the template context dict. Remove `pack_examples: list["ExtractExample"] | None = None` parameter from `_run_extraction_pipeline`. Remove the `ExtractExample` import at top of file.

**Why:** Dead parameter — nothing downstream uses it after deletion.

**Code Snippet**
```python
def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    scene_result: "SceneExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
) -> list[dict[str, str]]:
    # ... (remove band_examples entirely from context)
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "scene_result": scene_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
            # band_examples removed
        },
    )
```

**Validation:** `grep -r "pack_examples" ccya/` returns zero results. `grep -r "ExtractExample" ccya/` returns zero results.

#### Step 1.3 — Add `_resolve_pack_dir` + namespace routing

**File:** `ccya/pack.py`

**What:** New helper that searches `packs/default/` then `packs/custom/` for bare slugs, and routes directly for namespaced slugs.

**Why:** Enables `packs/default/` and `packs/custom/` split without changing call sites.

**Code Snippet**
```python
def _resolve_pack_dir(pack_id: str, packs_dir: Path) -> Path:
    """Resolve pack_id to a directory.

    Accepts:
      "flooded-world"          -> searches packs/default/, then packs/custom/
      "default/flooded-world"  -> packs/default/flooded-world
      "custom/my-world"        -> packs/custom/my-world
    """
    if "/" in pack_id:
        namespace, slug = pack_id.split("/", 1)
        candidate = packs_dir / namespace / slug
        if not candidate.is_dir():
            raise FileNotFoundError(f"Pack not found: {candidate}")
        return candidate
    for namespace in ("default", "custom"):
        candidate = packs_dir / namespace / pack_id
        if candidate.is_dir():
            return candidate
    # Legacy fallback: packs/<pack_id>/ (existing packs not yet moved)
    legacy = packs_dir / pack_id
    if legacy.is_dir():
        return legacy
    raise FileNotFoundError(f"Pack '{pack_id}' not found in {packs_dir}")
```

Update `list_packs()` to aggregate all three locations:
```python
def list_packs(packs_dir: Path) -> list[PackManifest]:
    manifests: list[PackManifest] = []
    if not packs_dir.is_dir():
        return manifests
    search_dirs = [
        packs_dir / "default",
        packs_dir / "custom",
        packs_dir,  # legacy root-level packs
    ]
    seen: set[str] = set()
    for search in search_dirs:
        if not search.is_dir():
            continue
        for child in sorted(search.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "pack.yaml"
            if manifest_path.exists() and child.name not in seen:
                seen.add(child.name)
                try:
                    with open(manifest_path) as f:
                        data = yaml.safe_load(f) or {}
                    manifests.append(PackManifest(**data))
                except Exception:
                    pass
    return manifests
```

**Validation:** Both `packs/default/` and `packs/custom/` directory creation tested. `list_packs()` returns packs from all locations without duplicates.

#### Step 1.4 — Remove `pack_examples` from `turn.py`

**File:** `ccya/engine/turn.py`

**What:** Find the call to `_run_extraction_pipeline(... pack_examples=pack.extract_examples ...)` and remove the `pack_examples` kwarg.

**Validation:** `grep -r "pack_examples" ccya/` returns zero.

### Tests to write or update
- `tests/test_pack.py`: assert `load_pack()` on a pack.yaml with `extract_examples: extract_examples.yaml` key does not raise.
- `tests/test_pack.py`: assert `_resolve_pack_dir` resolves bare slug via default namespace, then custom, then legacy.
- `tests/test_extraction.py`: assert `_extract_state_messages` no longer has `pack_examples` param (call it without, assert no TypeError).

### REPOMAP updates required
`docs/REPOMAP/pack.md`: Remove `ExtractExample`, `PackFiles` from models section. Remove `extract_examples` from Pack model. Add `_resolve_pack_dir`. Update `load_pack()` signature note.

### Risks
1. `turn.py` may pass `pack_examples` in more than one call site — grep carefully before removing.
2. Old `pack.yaml` files with `mode: dynamic` or `version: 1` — covered by `extra: "ignore"` on `PackManifest`.

***

## Implementation — Phase 2: New `ScenarioBrief` schema + consolidated `scenario.yaml`

### Context files to load
- `ccya/pack.py` (post-Phase-1)
- `packs/flooded-world/scenario.yaml`
- `packs/flooded-world/pack.yaml`
- `packs/flooded-world/world.md`
- `packs/flooded-world/style.md`
- `docs/REPOMAP/pack.md`

### Overview
Expand `ScenarioBrief` with new top-level sections: `world_facts`, `narrator_rules`, `factions`, `locations`, `name_locales`, `name_seed`. Add `Faction` and `NamedLocation` models. Add `WorldBrief` model (player concept input — the input to `generate_pack()`). Rewrite `flooded-world/scenario.yaml` as the canonical migration example. Do not move the file — keep it at `packs/flooded-world/scenario.yaml` but rewrite its contents to the new schema.

### Detailed steps

#### Step 2.1 — New models in `pack.py`

**File:** `ccya/pack.py`

**What:** Add `Faction`, `NamedLocation`, `WorldBrief`, `GeneratedPackMeta` models. Expand `ScenarioBrief`.

**Why:** `Faction` and `NamedLocation` feed the narrate prompt for world consistency. `WorldBrief` is the player input contract for `generate_pack()`.

**Code Snippet**
```python
class Faction(BaseModel):
    id: str                    # snake_case
    name: str                  # drawn from name pool at generate time
    description: str           # 1–2 sentences: what they do, what they want
    disposition: str = "neutral"  # "hostile" | "neutral" | "friendly" toward player by default


class NamedLocation(BaseModel):
    id: str                    # snake_case
    name: str                  # drawn from name pool at generate time
    type: str                  # settlement | ruin | wilderness | transit | institution
    description: str           # 1–2 sentences: what is here, why it matters


class Constraints(BaseModel):
    min_named_npcs: int = 2
    min_objectives_per_quest: int = 2
    starting_quest_count: int = 1
    inventory_size_range: tuple[int, int] = (4, 8)
    pc_stat_range: tuple[int, int] = (1, 4)
    pc_stat_total_range: tuple[int, int] = (12, 18)
    prose_word_range: tuple[int, int] = (200, 500)
    required_inventory_kinds: list[str] = Field(default_factory=list)
    npc_distinct_first_letters: bool = True
    forbid_cliches: list[str] = Field(default_factory=list)
    forbid_player_dependents: bool = True
    forbid_legendary_items: bool = True


class ScenarioBrief(BaseModel):
    """Complete world definition for a generated pack.

    Sections:
      constraints   — hard numeric rules for seed generation
      world_facts   — 3–8 durable facts injected into world_state (replaces world.md)
      narrator_rules — tone/style rules injected into narrate system prompt (replaces style.md)
      factions      — 3–6 named power groups injected into narrate context each turn
      locations     — 5–10 named places injected into narrate context each turn
      name_locales  — weighted Faker locales for name generation
      name_seed     — int; controls name selection randomness at generate time
      inspiration   — quality anti-pattern guidance for seed generation (no concrete examples)
    """
    constraints: Constraints = Field(default_factory=Constraints)
    world_facts: list[str] = Field(default_factory=list, max_length=8)
    narrator_rules: list[str] = Field(default_factory=list, max_length=12)
    factions: list[Faction] = Field(default_factory=list, max_length=6)
    locations: list[NamedLocation] = Field(default_factory=list, max_length=10)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    name_seed: int = 0
    inspiration: Inspiration = Field(default_factory=Inspiration)


class WorldBrief(BaseModel):
    """Player input for generate_pack(). Five structured sections + one free-form.

    Each section drives a distinct part of world generation:
      concept       — the one-line pitch ("post-flood survival", "1930s supernatural noir")
      tone          — feel and register ("grim survival", "darkly comedic", "tense political")
      geography     — what the physical world looks like and how it shapes daily life
      power         — who holds power, how it was won, what it costs ordinary people
      daily_life    — what people eat, trade, fear, and talk about (grounds the narrator)
      player_hint   — optional: what kind of person the player wants to be (soft guidance)
    """
    concept: str                   # required: the pitch
    tone: str = ""
    geography: str = ""
    power: str = ""
    daily_life: str = ""
    player_hint: str = ""          # maps to PlayerOverrides.free_form at seed time


class GeneratedPackMeta(BaseModel):
    """Written into pack.yaml for generated packs. Marks provenance."""
    generated: bool = True
    world_brief_concept: str = ""  # the original concept string, for display
```

**Validation:** `ScenarioBrief(**yaml.safe_load(new_flooded_scenario))` validates without error.

#### Step 2.2 — Rewrite `flooded-world/scenario.yaml`

**File:** `packs/flooded-world/scenario.yaml`

**What:** Rewrite to the new consolidated schema, absorbing `world.md`, `style.md`, `pack.yaml.baseline_facts`, and `pack.yaml.name_locales`. This is the migration reference.

**Why:** Proves the new schema works end-to-end before automating generation.

**Code Snippet**
```yaml
# Consolidated scenario — replaces world.md, style.md, and pack.yaml locale/facts fields

constraints:
  min_named_npcs: 2
  min_objectives_per_quest: 2
  starting_quest_count: 1
  inventory_size_range: [3, 6]
  pc_stat_range: [1, 4]
  pc_stat_total_range: [8, 11]
  prose_word_range: [275, 550]
  required_inventory_kinds: [weapon, tool]
  npc_distinct_first_letters: true
  forbid_cliches:
    - "survivor in a bunker who doesn't know what happened"
    - "the last person on Earth"
    - "the flood was secretly caused by a corporation"
    - "a child who holds the key to saving the world"
    - "the underwater city contains the answer to reversing everything"
  forbid_player_dependents: true
  forbid_legendary_items: true

world_facts:
  - "The Treaty of Andes (2138) divides the Highlands between surviving nation-states; enforcement ends fifty kilometers from any administrative center."
  - "Salt is the Highlands' most valuable trade good — desalination is energy-prohibitive; a kilo of clean salt buys a week of bunk space in any plateau city."
  - "Diving the Flooded Zones is regulated by guilds holding the only accurate maps; the Cartographers' Compact (2129) makes unsanctioned mapping a capital offense in three guilds."
  - "Sea level rose two hundred feet over forty years. The flood is not receding. The year is 2147."
  - "The world is defined by elevation: Highlands hold communities, the Edge is the contested flood-meets-land zone, the Flooded Zones are drowned ruins."

narrator_rules:
  - "The water is the constant — it rises, falls, and dictates everything. Verticality is the defining spatial feature."
  - "Violence is local and consequential: a fight on a barge puts people in the water, a fight on a highland terrace means falling on steep ground."
  - "Dialogue is practical and direct. Barge captains speak in currents. Divers speak in depths and hazards. Farmers speak in seasons."
  - "The flood zones are biologically rich but structurally hazardous: structural collapse, toxic sediment, entanglement in submerged infrastructure."
  - "Food is the primary constraint. Without refrigeration, preservation is salt, smoke, and drying. Storage is the bottleneck."
  - "The storms are bigger now. The rain lasts longer. The flood level changes with seasons."
  - "The drowned cities are haunting: lower floors bioluminescent, upper floors weathered concrete, rooftops the only visible structure."
  - "Never describe the flood as a metaphor or as something that can be reversed. It is a permanent physical fact."

factions:
  - id: cartographers_compact
    name: "Cartographers' Compact"
    description: "Guild that holds the only accurate maps of the Flooded Zones; sells dive rights and enforces mapping bans with hired muscle."
    disposition: neutral
  - id: highland_councils
    name: "Highland Councils"
    description: "Coalition of plateau city administrations; controls legal trade routes and treaty enforcement in the Highlands."
    disposition: friendly
  - id: edge_settlers
    name: "Edge Settler Communities"
    description: "Loose network of terraced farming communities on the flood-meets-land transition zone; politically unaligned, often targeted."
    disposition: neutral
  - id: salt_runners
    name: "Salt Runners"
    description: "Unsanctioned traders who extract and sell clean salt; wealthiest unlicensed class, operate outside treaty law."
    disposition: neutral

locations:
  - id: highland_plateau_city
    name: "Plateau City"
    type: settlement
    description: "A surviving city on high ground; administrative center, trade hub, and the closest thing to pre-flood civilization."
  - id: edge_terrace
    name: "Edge Terrace"
    type: settlement
    description: "Terraced farming settlement on the flood-meets-land boundary; fertile but contested, no treaty protection."
  - id: flooded_zone_skyscraper
    name: "Flooded Zone"
    type: ruin
    description: "Drowned urban infrastructure — skyscrapers as reefs, submerged highways, kelp forests in parking garages."
  - id: river_barge_route
    name: "River Route"
    type: transit
    description: "The primary trade artery connecting highland communities; controlled by barge captains and Compact toll points."

name_locales:
  - locale: en_GB
    weight: 0.35
  - locale: pt_BR
    weight: 0.25
  - locale: id_ID
    weight: 0.20
  - locale: fr_FR
    weight: 0.20

name_seed: 0  # 0 = randomized each generation

inspiration:
  pc: |
    A specific person shaped by the drowned world's pressures — their community, elevation,
    and route dependencies. Avoid the lone survivor archetype. Give them a role that ties
    them to other people's survival: a diver, barge captain, Edge farmer, scout, or trader.
    What they cannot do is as important as what they can.

  opening_situation: |
    Drop the player into a moment that requires a decision in a place where the water is
    always present. Grounded in spatial reality: a barge deck, a flooded lobby, an Edge
    hill. The opening should feel like inheriting a responsibility, not discovering a
    mystery. Something is already in motion when the player arrives.

  npcs: |
    Each NPC has a stake in the world's survival and something they are not saying.
    At least one should have interests that conflict with the player's — not as a villain,
    but as someone whose community depends on different choices. Avoid archetypal roles.

  inventory: |
    Items reflect what this person uses daily — the specific tools, the specific numbers.
    Every item should say something about who this person is and what they have survived.
    No generic loadouts.

  quests: |
    Stakes should be local and material, affecting a community, route, or dive site.
    At least one objective should create tension with another NPC or faction.
    The quest should have a visible cost — in time, risk, or trust.
```

**Validation:** `ScenarioBrief(**yaml.safe_load(open("packs/flooded-world/scenario.yaml")))` validates. `load_pack("flooded-world", packs_dir)` still loads (pack.yaml still present with identity fields; world.md and style.md still present as legacy fallback).

#### Step 2.3 — Update `Pack` model and `_check_mode_files` validator

**File:** `ccya/pack.py`

**What:** Remove the `_check_mode_files` validator that enforces `mode == "static"` or `mode == "dynamic"`. The loader auto-detects by file presence. Remove `Pack.world_text` is kept as legacy fallback field. Add `Pack.scenario` as primary. A pack is valid if it has either `seed` (static) or `scenario` (generated). `style_text` kept as legacy fallback.

**Code Snippet**
```python
class Pack(BaseModel):
    manifest: PackManifest
    # Legacy text fields (world.md / style.md — still loaded for old packs)
    world_text: str = ""
    style_text: str = ""
    # Static mode
    seed: SeedState | None = None
    opening_text: str = ""
    opening_actions: list[str] = Field(default_factory=list)
    # Generated mode (new consolidated scenario.yaml)
    scenario: ScenarioBrief | None = None

    @model_validator(mode="after")
    def _check_playable(self) -> "Pack":
        if self.seed is None and self.scenario is None:
            raise ValueError(
                "Pack must have either seed_state.yaml (static) or scenario.yaml (generated)"
            )
        return self
```

**Validation:** Old static pack still validates. New scenario-only pack validates. A pack with neither raises.

### Tests to write or update
- `tests/test_pack.py`: `ScenarioBrief` round-trips through new flooded-world YAML.
- `tests/test_pack.py`: `Pack` with only `scenario` validates. `Pack` with only `seed` validates. `Pack` with neither raises.
- `tests/test_pack.py`: `Faction` and `NamedLocation` validate expected fields.

### REPOMAP updates required
`docs/REPOMAP/pack.md`: Add `Faction`, `NamedLocation`, `WorldBrief`, `GeneratedPackMeta` to models. Update `ScenarioBrief` field list. Update `Pack` model. Note legacy fallback behavior.

### Risks
1. Existing `pack.yaml` files still have `mode` and `version` — covered by `extra: "ignore"`.
2. `_check_mode_files` removal may quietly allow half-initialized packs — the new `_check_playable` is the safety net.

***

## Implementation — Phase 3: Engine wiring for factions + locations; narrate prompt update

### Context files to load
- `ccya/engine/narrate.py`
- `ccya/engine/turn.py`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/pack.py` (post-Phase-2)

### Overview
Wire `pack.scenario.factions`, `pack.scenario.locations`, and `pack.scenario.narrator_rules` into the narrate context. Update `narrate_system.j2` to consume them and to clarify bold rules. Rewrite `generate_seed_system.j2` and `generate_seed_user.j2` to consume the new `ScenarioBrief` shape, inject faction/location name pools, inject name seed, and improve opening narrative guidance for organic feel. Remove the `_check_mode_files` / `mode` references from `engine/seed.py`.

### Detailed steps

#### Step 3.1 — Wire factions/locations/narrator_rules into narrate context

**File:** `ccya/engine/narrate.py`

**What:** In `_build_narrate_messages()`, add `world_factions`, `world_locations`, and `narrator_rules` to the context dict, sourced from `pack.scenario` when present. Fall back to `pack.style_text` (legacy) when `scenario` is absent or `narrator_rules` is empty.

**Why:** Narrate prompt already has the `{% if world_factions or world_locations %}` block — it's just not being fed data yet.

**Code Snippet**
```python
# In _build_narrate_messages, when building ctx:
scenario = pack.scenario if pack else None
world_factions = [f.model_dump() for f in scenario.factions] if scenario else []
world_locations = [loc.model_dump() for loc in scenario.locations] if scenario else []
narrator_rules = scenario.narrator_rules if scenario and scenario.narrator_rules else []
# Legacy fallback
pack_style = pack.style_text if (pack and not narrator_rules) else ""

ctx = {
    # ... existing fields ...
    "world_factions": world_factions,
    "world_locations": world_locations,
    "narrator_rules": narrator_rules,
    "pack_style": pack_style,
}
```

**Validation:** A turn narration on flooded-world references a faction name from `scenario.factions`.

#### Step 3.2 — Update `narrate_system.j2`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the `## World consistency` block to render `world_factions` with disposition info and `world_locations` with type + description. Add `narrator_rules` rendering. Clarify bold rule to say it applies on turn 1 (opening narrative) the same as other turns.

**Code Snippet** (replace the two relevant blocks):
```jinja2
## Items and inventory
Items with multiples should be always quantified, even if vaguely: "I picked up a couple pistol clips." When relevant to quests or inventory, explicit quantity is preferred.
**Bold** named inventory items on first use or direct reference in a scene. **Bold** NPC names on first introduction in a scene. This applies on the very first turn the same as all subsequent turns.
{% if narrator_rules %}
## Genre tone
{% for rule in narrator_rules %}- {{ rule }}
{% endfor %}
{% elif pack_style %}
## Genre tone
{{ pack_style }}
{% endif %}
{% if world_factions or world_locations %}
## World consistency
When the user prompt provides named factions or locations, use them rather than inventing new ones. Do not use all of them — pick what fits the scene. Unused entries remain available for future turns.
{% if world_factions %}
Factions:
{% for f in world_factions %}- **{{ f.name }}** ({{ f.disposition }}): {{ f.description }}
{% endfor %}{% endif %}
{% if world_locations %}
Locations:
{% for loc in world_locations %}- **{{ loc.name }}** ({{ loc.type }}): {{ loc.description }}
{% endfor %}{% endif %}
{% endif %}
```

**Validation:** Manual inspection of a rendered narrate_system prompt shows faction names, dispositions, and narrator_rules bullets correctly rendered. Bold guidance present.

#### Step 3.3 — Update `generate_seed_system.j2` and `generate_seed_user.j2`

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Remove the paragraph about `world_text` being `world_bible`. Add a `## Name selection` section explaining `name_seed`. Replace the rigid 3-paragraph opening narrative structure with guidance for organic prose. Keep all hard constraint blocks.

**Code Snippet** (replace `## Field guidance` → `opening_narrative` entry and add name_seed section):
```jinja2
## Name selection
A name_seed integer appears in the user prompt. Use it as follows: mentally hash each candidate name against the seed to pick less-obvious selections. Avoid defaulting to the most culturally prominent name for each locale — prefer the second or third most plausible option. This creates variance across runs.

## Field guidance
...
- `opening_narrative`: second person, present tense. Do NOT structure this as a biography paragraph → situation paragraph → scene paragraph. Instead: start mid-scene with specific sensory detail that places the player in a moment already in progress. Weave in who the character is through what they are doing, what they are carrying, and what they are thinking — not through summary. Let the quest tension surface through what the player observes rather than what the narrator announces. NPCs should appear in action, not be introduced. The opening should feel like chapter two, not a prologue. Bold NPC names on first introduction. Bold inventory item names on first use. 350–550 words.
```

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Remove `## world_bible` and `## tone_and_style` sections (now in `scenario.yaml`). Render `scenario.world_facts`, `scenario.narrator_rules`, `scenario.factions`, `scenario.locations`, and `name_seed`. Keep `creative_direction` from `scenario.inspiration`. Keep `player_overrides`. Keep `name_pool`.

**Code Snippet**:
```jinja2
{% if scenario %}
{% if scenario.world_facts %}
## world_facts (non-negotiable canon — inject into world_state verbatim)
{% for fact in scenario.world_facts %}- {{ fact }}
{% endfor %}{% endif %}
{% if scenario.narrator_rules %}
## tone_rules (narrator must follow these every turn)
{% for rule in scenario.narrator_rules %}- {{ rule }}
{% endfor %}{% endif %}
{% if scenario.factions %}
## factions (name these in the seed — use ids and names as given, do not rename)
{% for f in scenario.factions %}- {{ f.name }} ({{ f.disposition }}): {{ f.description }}
{% endfor %}{% endif %}
{% if scenario.locations %}
## locations (use these as named places in the seed — do not invent new top-level locations)
{% for loc in scenario.locations %}- {{ loc.name }} ({{ loc.type }}): {{ loc.description }}
{% endfor %}{% endif %}
{% if scenario.inspiration %}
{% set ins = scenario.inspiration %}
## creative_direction (guidance only — do not borrow phrasing or pick the obvious answer)
{% if ins.pc %}### pc
{{ ins.pc }}
{% endif %}{% if ins.opening_situation %}### opening_situation
{{ ins.opening_situation }}
{% endif %}{% if ins.npcs %}### npcs
{{ ins.npcs }}
{% endif %}{% if ins.inventory %}### inventory
{{ ins.inventory }}
{% endif %}{% if ins.quests %}### quest
{{ ins.quests }}
{% endif %}{% endif %}
{% endif %}
{% if overrides %}
## player_overrides (soft — honor when compatible with canon)
{% if overrides.pc_hints %}- pc: {{ overrides.pc_hints }}
{% endif %}{% if overrides.npc_hints %}- npcs: {{ overrides.npc_hints }}
{% endif %}{% if overrides.location_hints %}- location: {{ overrides.location_hints }}
{% endif %}{% if overrides.quest_hints %}- quest: {{ overrides.quest_hints }}
{% endif %}{% if overrides.free_form %}- other: {{ overrides.free_form }}
{% endif %}{% endif %}
{% if name_pool %}
## name_pool (sampled from this setting's locales — use at least one per category)
name_seed: {{ name_seed }}
- pc candidates: {{ name_pool.pc | join(", ") }}
- npc candidates: {{ name_pool.npc | join(", ") }}
- place name inspiration: {{ name_pool.location | join(", ") }}
{% endif %}

Emit the SeedEnvelope JSON now.
```

**Validation:** Rendered prompt contains faction names, world facts, and name_seed. No `world_bible` section present.

#### Step 3.4 — Update `engine/seed.py` for new schema

**File:** `ccya/engine/seed.py`

**What:** Remove the `parse_world_facts` call and the `baseline_facts` fallback — `world_facts` now come from `scenario.world_facts`. Update `_build_generate_seed_messages` to pass `name_seed` from `pack.scenario.name_seed` (randomized if 0). Keep the world_facts injection logic but source from `scenario.world_facts` instead.

**Code Snippet**:
```python
def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    import random
    scenario = pack.scenario
    locales = scenario.name_locales if scenario else pack.manifest.name_locales
    name_pool = generate_name_pool(locales)
    # Randomize name_seed if not set
    name_seed = (scenario.name_seed if scenario and scenario.name_seed else 0) or random.randint(10_000_000, 99_999_999)
    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count if (overrides and overrides.npc_count > 0) else 0,
        "name_pool": name_pool,
        "name_seed": name_seed,
        # Legacy fallbacks for old packs without scenario
        "world_text": pack.world_text,
        "style_text": pack.style_text,
    }
    system_text = _render(env, "generate_seed_system.j2", ctx)
    user_text = _render(env, "generate_seed_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
```

In `generate_seed()`, replace the `world_facts` sourcing:
```python
world_facts: list[str] = (
    list(pack.scenario.world_facts)
    if pack.scenario and pack.scenario.world_facts
    else list(pack.manifest.baseline_facts)
    if pack.manifest.baseline_facts
    else parse_world_facts(pack.world_text)
)
```

Remove the `pack.manifest.mode != "dynamic"` guard — replace with:
```python
if pack.seed is not None and pack.scenario is None:
    raise ValueError("generate_seed() requires a generated pack (scenario.yaml), got static seed pack")
```

**Validation:** `generate_seed()` on flooded-world produces a `SeedEnvelope` with world_facts from `scenario.world_facts`. A static pack raises on `generate_seed()` call.

### Tests to write or update
- `tests/test_narrate.py`: mock narrate build with a pack that has `scenario.factions` — assert `world_factions` appears in rendered system prompt.
- `tests/test_seed.py`: assert `generate_seed()` on new flooded-world scenario produces valid `SeedEnvelope` with world_state seeded from `scenario.world_facts`.
- `tests/test_seed.py`: assert `name_seed` is nonzero in rendered user prompt.

### REPOMAP updates required
`docs/REPOMAP/pack.md`: Add `Faction`, `NamedLocation` to models. Update `ScenarioBrief`. Update `generate_seed()` note re: new schema.
`docs/REPOMAP/engine.md`: Note `_build_narrate_messages` now accepts faction/location context from pack.

### Risks
1. Old packs without `scenario.yaml` will produce empty `world_factions`/`world_locations` — that's correct, legacy behavior unchanged.
2. `narrate_system.j2` already has the `{% if world_factions %}` block — verify the variable name matches what narrate.py passes.

***

## Implementation — Phase 4: `generate_pack()` function + `WorldBrief` prompt

### Context files to load
- `ccya/pack.py` (post-Phase-2)
- `ccya/engine/seed.py` (post-Phase-3)
- `ccya/prompts/generate_seed_system.j2` (post-Phase-3)

### Overview
Implement `generate_pack(brief: WorldBrief, config: EngineConfig) -> Pack` in a new `ccya/engine/pack_gen.py` module. This function takes a `WorldBrief` (player concept input), makes one LLM call to produce a complete `ScenarioBrief` JSON, validates it, writes it to `packs/custom/<slug>/`, and returns a loaded `Pack`. Add the two new prompt templates: `generate_pack_system.j2` and `generate_pack_user.j2`.

### Detailed steps

#### Step 4.1 — New module `ccya/engine/pack_gen.py`

**File:** `ccya/engine/pack_gen.py`

**What:** `generate_pack()` async function. Takes `WorldBrief`, generates a `ScenarioBrief` via LLM, writes pack files to `packs/custom/<slug>/`, returns `Pack`.

**Why:** Keeps pack generation isolated from the turn pipeline. `engine/seed.py` is turn-level; `engine/pack_gen.py` is new-world-level.

**Code Snippet**
```python
"""World pack generation from player concept (WorldBrief → ScenarioBrief → Pack on disk)."""

from __future__ import annotations

import logging
import random
import re
import uuid
from pathlib import Path

import yaml
from jinja2 import Environment

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.pack import Pack, PackManifest, ScenarioBrief, WorldBrief, load_pack

_log = logging.getLogger("ccya.engine")


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s[:40] or "custom-world"


def _build_generate_pack_messages(
    env: Environment,
    brief: WorldBrief,
    name_pool: dict[str, list[str]],
    name_seed: int,
) -> list[dict[str, str]]:
    ctx = {
        "brief": brief,
        "name_pool": name_pool,
        "name_seed": name_seed,
    }
    system_text = _render(env, "generate_pack_system.j2", ctx)
    user_text = _render(env, "generate_pack_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


async def generate_pack(
    brief: WorldBrief,
    config: EngineConfig,
    packs_dir: Path,
    *,
    template_dir: str | None = None,
    max_retries: int = 2,
) -> Pack:
    """Generate a complete world pack from a WorldBrief and write it to packs/custom/.

    Returns the loaded Pack ready for generate_seed().
    """
    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    # Bootstrap name pool using default locales until scenario provides them
    default_locales = [{"locale": "en_US", "weight": 1.0}]
    name_seed = random.randint(10_000_000, 99_999_999)
    name_pool = generate_name_pool(default_locales)

    messages = _build_generate_pack_messages(env, brief, name_pool, name_seed)
    messages, _, _ = trim_messages(messages, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(0, "generate_pack", messages)

    parse_error = ""
    for attempt in range(1 + max_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_pack_request_attempt_{attempt}",
                messages=messages,
                max_chars=config.log_llm_io_max_chars,
            )
        try:
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.generate_seed_temperature,
                timeout=float(config.request_timeout_s),
            )
        except Exception as exc:
            _log.error("generate_pack: LLM error: %s", exc, extra={"trace_id": trace_id})
            raise

        raw = result.get("response", "") if isinstance(result, dict) else ""
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_pack_response_attempt_{attempt}",
                response=raw,
                max_chars=config.log_llm_io_max_chars,
            )

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in generate_pack response"
            _log.warning("generate_pack failed (attempt %d): %s", attempt + 1, parse_error, extra={"trace_id": trace_id})
            if attempt < max_retries:
                messages.append({"role": "user", "content": f"Output failed to parse: {parse_error}. Re-emit valid ScenarioBrief JSON only."})
            continue

        try:
            # Inject name_seed if LLM omitted it
            if "name_seed" not in j:
                j["name_seed"] = name_seed
            scenario = ScenarioBrief(**j)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning("generate_pack validation failed (attempt %d): %s", attempt + 1, parse_error, extra={"trace_id": trace_id})
            if attempt < max_retries:
                messages.append({"role": "user", "content": f"ScenarioBrief validation failed: {parse_error[:300]}. Re-emit corrected JSON."})
            continue

        # Write pack to disk
        slug = _slugify(brief.concept) + "-" + uuid.uuid4().hex[:6]
        pack_dir = packs_dir / "custom" / slug
        pack_dir.mkdir(parents=True, exist_ok=True)

        manifest = PackManifest(
            id=slug,
            name=brief.concept.title(),
            description=brief.concept,
            genre=brief.tone or "",
            tone_tags=[],
        )
        with open(pack_dir / "pack.yaml", "w") as f:
            yaml.dump(manifest.model_dump(exclude_none=True), f, allow_unicode=True, sort_keys=False)

        scenario_dict = scenario.model_dump(exclude_none=True)
        with open(pack_dir / "scenario.yaml", "w") as f:
            yaml.dump(scenario_dict, f, allow_unicode=True, sort_keys=False)

        _log.info(
            "generate_pack: wrote pack %s",
            slug,
            extra={"trace_id": trace_id, "pack": slug},
        )

        return load_pack(slug, packs_dir)

    raise RuntimeError(f"generate_pack failed after {1 + max_retries} attempts — trace {trace_id}")
```

**Validation:** `generate_pack(WorldBrief(concept="post-flood survival"), config, packs_dir)` writes a valid pack dir with `pack.yaml` and `scenario.yaml`. The returned `Pack` has `pack.scenario.factions` with at least 3 entries.

#### Step 4.2 — New prompt `generate_pack_system.j2`

**File:** `ccya/prompts/generate_pack_system.j2`

**What:** System prompt for world generation. Instructs the LLM to produce a `ScenarioBrief` JSON given a `WorldBrief`. Covers all sections of the new schema.

**Code Snippet**
```jinja2
Generate a complete world scenario as a ScenarioBrief JSON. Emit only the JSON.

## Your job
You are building the entire seed of a playable text adventure world. The player has given you a concept and some directional notes. Your output will be used directly — it defines the factions, locations, world facts, tone rules, and generation constraints for every playthrough in this world.

## Absolute rules
- Every faction and location must have a name drawn from the name pool. Do not invent names outside the pool. The name_seed in the user prompt controls which names feel right — use less-obvious choices from each locale, not the most prominent.
- World facts must be specific and named — treaties with years, organizations with names, rules with consequences. "Magic exists" is not a world fact. "The Conclave of Seventeen banned unlicensed casting after the Ashfall of 1312" is a world fact.
- Factions must have genuine conflict potential — at least two factions should have interests that can plausibly conflict with each other and with the player.
- Locations must cover the spatial range the player will actually traverse: a home base, a dangerous destination, a transit/route, and a political/institutional node.
- Narrator rules must be behavioral directives, not world facts. "Violence is lethal and local" is a narrator rule. "The city was destroyed in 1942" is a world fact.
- Inspiration fields must describe qualities and failure modes only. No concrete examples, no named characters, no specific scenario suggestions.
- forbid_cliches must be specific story patterns to avoid — not vague ("no chosen one") but precise ("no character who turns out to be the lost heir of the ruling dynasty").
- name_seed: pass through the integer from the user prompt unchanged.

## Output schema

```json
{
  "constraints": {
    "min_named_npcs": 2,
    "min_objectives_per_quest": 2,
    "starting_quest_count": 1,
    "inventory_size_range": [int, int],
    "pc_stat_range": [int, int],
    "pc_stat_total_range": [int, int],
    "prose_word_range": [int, int],
    "required_inventory_kinds": ["string"],
    "npc_distinct_first_letters": true,
    "forbid_cliches": ["string"],
    "forbid_player_dependents": true,
    "forbid_legendary_items": true
  },
  "world_facts": ["string (3-8 named, specific, durable facts)"],
  "narrator_rules": ["string (6-12 behavioral rules for the narrator)"],
  "factions": [
    {"id": "snake_case", "name": "string from name pool", "description": "string", "disposition": "neutral|hostile|friendly"}
  ],
  "locations": [
    {"id": "snake_case", "name": "string from name pool", "type": "settlement|ruin|wilderness|transit|institution", "description": "string"}
  ],
  "name_locales": [
    {"locale": "faker_locale_code", "weight": float}
  ],
  "name_seed": int,
  "inspiration": {
    "pc": "string",
    "opening_situation": "string",
    "npcs": "string",
    "inventory": "string",
    "quests": "string"
  }
}
```

Constraints guidance: `inventory_size_range` [3,7]; `pc_stat_total_range` [8,14]; `prose_word_range` [300,550]. Scale to match the world's complexity and resource scarcity — a resource-scarce world gets a lower stat total.

name_locales: Choose 2–4 Faker locale codes that fit the setting's cultural geography. Use real Faker locales (en_GB, fr_FR, de_DE, pt_BR, ja_JP, zh_CN, ar_AA, ru_RU, es_ES, id_ID, etc.). Weight them to reflect the dominant cultural mix.
```

**Validation:** The rendered prompt is under 3,000 tokens. All schema fields are represented.

#### Step 4.3 — New prompt `generate_pack_user.j2`

**File:** `ccya/prompts/generate_pack_user.j2`

**Code Snippet**
```jinja2
## player_concept
{{ brief.concept }}
{% if brief.tone %}
## tone
{{ brief.tone }}
{% endif %}
{% if brief.geography %}
## geography
{{ brief.geography }}
{% endif %}
{% if brief.power %}
## power_structures
{{ brief.power }}
{% endif %}
{% if brief.daily_life %}
## daily_life
{{ brief.daily_life }}
{% endif %}
{% if brief.player_hint %}
## player_hint (soft — use as inspiration guidance only)
{{ brief.player_hint }}
{% endif %}

## name_pool (use these for faction and location names — do not invent outside this pool)
name_seed: {{ name_seed }}
- place/faction name candidates: {{ name_pool.location | join(", ") }}
- additional candidates: {{ name_pool.npc | join(", ") }}

Emit the ScenarioBrief JSON now.
```

**Validation:** All `WorldBrief` fields render correctly. Missing optional fields produce no blank sections.

### Tests to write or update
- `tests/test_pack_gen.py` (new): `generate_pack()` with `FakeLLM` returning a valid `ScenarioBrief` JSON writes correct files to a temp dir and returns a valid `Pack`.
- `tests/test_pack_gen.py`: `generate_pack()` retries on bad JSON from FakeLLM.
- `tests/test_pack_gen.py`: `_slugify("Post-Flood Survival!")` → `"post-flood-survival"`.

### REPOMAP updates required
`docs/REPOMAP/pack.md`: Add `generate_pack()` function, `WorldBrief` model, `engine/pack_gen.py` module note.
`docs/REPOMAP/engine.md`: Note `pack_gen.py` as new module under engine.

### Risks
1. `generate_name_pool` call in `pack_gen.py` uses default locales for initial pool — fine since the generated scenario will contain locales which then feed `generate_seed()`.
2. YAML serialization of Pydantic models: use `model_dump(exclude_none=True)` carefully — `tuple` fields like `inventory_size_range` serialize as lists in JSON/YAML which is correct for `yaml.dump`.
3. `packs/custom/` directory must exist or be created. `pack_dir.mkdir(parents=True, exist_ok=True)` handles this.

***

## Implementation — Phase 5: Directory restructure + cleanup

### Context files to load
- `ccya/pack.py` (post-Phase-1)
- `docs/REPOMAP/pack.md`

### Overview
Create `packs/default/` and `packs/custom/` directories. Move all existing packs into `packs/default/`. Delete `packs/AUTHORING.md`. Add `packs/custom/.gitkeep`. Update any hardcoded pack directory references in config or tests.

### Detailed steps

#### Step 5.1 — Create directory structure

```bash
mkdir -p packs/default packs/custom
touch packs/custom/.gitkeep
# Move each existing pack
for pack in allied-ww2 civil-war-1861 cyberpunk-2077-bladerunner expanse flooded-world muggle-world noir-1930s space-western zombie-survival; do
  mv packs/$pack packs/default/$pack
done
rm packs/AUTHORING.md
```

#### Step 5.2 — Verify `_resolve_pack_dir` covers legacy

The legacy fallback path in `_resolve_pack_dir` (checking `packs/<slug>/` directly) can be removed after this move since all packs are now under `packs/default/`. Update the function to remove the legacy root check.

#### Step 5.3 — Update tests and config fixtures

**What:** Any test that calls `load_pack("flooded-world", packs_dir)` where `packs_dir` is the repo `packs/` root will now need the namespace routing. Since `_resolve_pack_dir` checks `default/` first, this is transparent — no test changes required unless tests mock the directory structure.

**Validation:** `list_packs(Path("packs"))` returns all 9 existing packs. `load_pack("flooded-world", Path("packs"))` succeeds.

### Tests to write or update
- `tests/test_pack.py`: `list_packs(packs_dir)` returns at least 9 packs from `packs/default/`.

### REPOMAP updates required
`docs/REPOMAP/pack.md`: Update pack structure description to show `packs/default/` and `packs/custom/`.

### Risks
1. `config.yaml` may hardcode `packs_dir: packs/` — that's fine, `_resolve_pack_dir` handles the rest.
2. Git history: `mv` vs delete+create matters for git blame — use `git mv` not shell `mv`.

***

## Ambiguities requiring resolution before execution

1. **`engine/turn.py` call site for `pack_examples`** — verify there is exactly one call site before Phase 1 execution. If `narrate.py` also references it somehow, it needs to be found. Options: A) trust the grep, B) run tests before touching this.

2. **`static-pack-tearout.md` status** — is it open/in-progress/merged? If already merged, Phase 1 may overlap. Options: A) read that plan before starting, B) assume it hasn't landed and proceed.

3. **Opening narrative word count** — current guidance says 200–500 words; the new guidance in Phase 3 says 350–550. The `Constraints.prose_word_range` default is `(200, 500)`. Should the default change, or should pack authors set their own range? Options: A) change the default in `Constraints` to `(300, 500)` and update flooded-world scenario, B) leave default alone, document that the new opening guidance implies a higher target.

4. **Seeded name selection for factions/locations in `generate_pack()`** — the `generate_name_pool()` function in `names.py` currently generates PC and NPC name pools, not faction/location name pools. The `location` pool exists but contains place-name inspiration strings, not organization names. Options: A) use the NPC name pool for faction names at generation time (organizations often named after founders), B) add a `generate_faction_names()` call that pulls from locale pool differently, C) accept that faction names come from the LLM within pool constraints and the `name_seed` instruction is the primary randomness lever.

5. **`generate_pack()` server wiring** — this plan does not add a server route or UI. Is there a stub route needed for testing from the running server, or is CLI/test-only sufficient for now? Options: A) add a `POST /api/generate-pack` stub route (body: `WorldBrief`), B) test only via pytest and defer route to a UI plan.

***

## TODO.md update

Add under **P4 — World Continuity**, before "Location-keyed NPC storage":

```
- **Custom world generator** — `generate_pack(WorldBrief)` → ScenarioBrief → Pack on disk; new schema (scenario.yaml absorbs world.md/style.md/factions/locations); extract_examples deleted; opening narrative quality pass; packs/default + packs/custom split — see [`p4-world/custom-world-generator.md`](p4-world/custom-world-generator.md)
```