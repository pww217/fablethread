# Plan: World Prop Injection

## Context

`names.py` already handles locale-aware name generation via Faker, injecting name pools for PCs, NPCs, and city names at seed time. The `location` pool uses `faker.city()` — real-world city names dropped raw into a fantasy or genre setting.

This plan extends the prop injection system in two directions:

1. **Richer location props** — not just city names, but typed, textured place names appropriate to genre (taverns, streets, districts, landmarks, wilderness areas).
2. **Broader world props** — organizations, rumors, objects, epithets, and other seeds the narrator can use to make the world feel inhabited without the LLM inventing them from nothing.

---

## Why This Matters

When the LLM has to invent a place name mid-narration, it reaches for the obvious: generic fantasy tropes ("The Rusty Dagger", "Silverkeep", "the old mill"). When names are injected from a curated, seeded pool, the story feels like it has a real geography — places recur, get referenced, accumulate meaning. The same principle that makes NPC names work applies to everything else.

---

## Part 1: Typed Place Name Generation

### The problem with `faker.city()`

`faker.city()` returns real-world city names ("Springfield", "Lagos", "Kraków"). These are fine for top-level settlement names in a realistic setting, but they don't produce:
- Tavern/inn names: "The Broken Compass", "The Pale Mare"
- Street/district names: "Coppergate Alley", "the Tanner's Quarter"
- Wilderness areas: "the Ashwood", "Godsfall Pass"
- Landmarks: "the Sunken Cathedral", "the Old Granary"

These are compositional — they're built from word pairs, not database lookups.

### Proposed: `generate_place_pool()`

Add to `names.py` alongside `generate_name_pool()`:

```python
# Word lists scoped by place type and genre tier.
# These are injected at seed time and stored in world_state or the seed manifest.

_TAVERN_ADJECTIVES = [
    "Broken", "Pale", "Gilded", "Sunken", "Wandering", "Black", "Rusted",
    "Hollow", "Crooked", "Silver", "Salted", "Weeping", "Forgotten", "Iron",
]
_TAVERN_NOUNS = [
    "Compass", "Mare", "Flagon", "Hearth", "Lantern", "Anchor", "Crow",
    "Coin", "Hammer", "Gauntlet", "Prow", "Bell", "Wheel", "Stag",
]
_DISTRICT_MODIFIERS = [
    "Copper", "Tanner's", "Miller's", "Salt", "Old", "Low", "High",
    "Ember", "Dust", "River", "Harbor", "Ash", "Iron", "Wax",
]
_DISTRICT_SUFFIXES = [
    "gate", "ward", "quarter", "row", "yard", "cross", "lane", "end", "side",
]
_WILDERNESS_ADJECTIVES = [
    "Ash", "Bone", "Frost", "Grey", "Hollow", "Blind", "Stone", "Burnt",
    "Far", "Deep", "Crook", "Salt", "Mire", "Black",
]
_WILDERNESS_NOUNS = [
    "Wood", "Fen", "Pass", "Ridge", "Moor", "Vale", "Reach", "Throat",
    "Hollow", "Run", "Gap", "Shelf", "Downs", "Crossing",
]


def generate_place_pool(
    locales: list[dict],
    *,
    settlement_count: int = 4,
    tavern_count: int = 3,
    district_count: int = 3,
    wilderness_count: int = 3,
    seed: int | None = None,
) -> dict[str, list[str]]:
    """
    Return typed place name pools for prompt injection.

    Keys: "settlements", "taverns", "districts", "wilderness"
    """
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)

    def pick_faker() -> Faker:
        return rng.choices(fakers, weights=weights, k=1)[0]

    settlements = [pick_faker().city() for _ in range(settlement_count)]

    taverns = [
        f"The {rng.choice(_TAVERN_ADJECTIVES)} {rng.choice(_TAVERN_NOUNS)}"
        for _ in range(tavern_count)
    ]

    districts = [
        f"{rng.choice(_DISTRICT_MODIFIERS)}{rng.choice(_DISTRICT_SUFFIXES)}"
        for _ in range(district_count)
    ]

    wilderness = [
        f"the {rng.choice(_WILDERNESS_ADJECTIVES)}{rng.choice(_WILDERNESS_NOUNS)}"
        for _ in range(wilderness_count)
    ]

    return {
        "settlements": settlements,
        "taverns": taverns,
        "districts": districts,
        "wilderness": wilderness,
    }
```

### Storage

Place pools are generated once at seed time and stored in the game state, same as name pools:

```yaml
# seed manifest / world_state section
name_pool:
  pc: ["Mira Sandfeld", ...]
  npc: ["Torben Klask", ...]
place_pool:
  settlements: ["Vethara", "Durn", "Saltmere"]
  taverns: ["The Hollow Compass", "The Pale Crow"]
  districts: ["Coppergate", "Ashward", "Millend"]
  wilderness: ["the AshWood", "the BlindPass"]
```

---

## Part 2: Broader World Props

Beyond places, the following prop categories make the world feel materially inhabited:

### Organizations / Factions

Not a full faction system — just names. A pool of 3-4 organization names seeded at game start, available for the narrator to attach to unnamed political actors.

Generation: `{adjective} {noun}` where adjectives and nouns are drawn from a domain-appropriate list per pack genre (criminal → "Shadow", "Iron", "Quiet"; political → "Gilded", "High", "Old").

```python
_ORG_ADJECTIVES = ["Iron", "Gilded", "Shadow", "Quiet", "Pale", "Broken", "Ash", "Crimson"]
_ORG_NOUNS = ["Hand", "Circle", "Order", "Coin", "Brand", "Chain", "Compact", "Lodge"]
# e.g. "The Iron Compact", "The Pale Hand"
```

### Street-level rumors

A pool of 3-4 seeded rumors available in the name pool — short, concrete, and hook-shaped. These give the narrator something specific to have an NPC mention in passing rather than inventing generic gossip.

Generation is templated and filled with other seeded props:

```python
_RUMOR_TEMPLATES = [
    "Someone has been asking questions about {npc_name} down at {tavern}.",
    "There's talk of {faction} moving coin through {district} after dark.",
    "Three sailors from {settlement} turned up dead near {wilderness} last week.",
    "{npc_name} was seen meeting with a {adjective} stranger at {tavern}.",
]
```

Filled at seed time using the NPC name pool, place pool, and org names. Stored as plain strings in the name pool under `"rumors"`.

### Object epithets

A small pool of notable-object names (swords, relics, ships, horses) the narrator can assign to items that come up in play. Prevents every sword from being called "the blade" and every ship from being "the vessel."

```python
_OBJECT_ADJECTIVES = ["Cracked", "Gilded", "Blind", "Cold", "Pale", "Hollow", "Notched"]
_OBJECT_NOUNS = ["Promise", "Mercy", "Reckoning", "Sorrow", "Vigil", "Edge", "Mark"]
# e.g. "Cold Mercy", "The Notched Promise"
```

---

## Part 3: Injection Points

The pools need to be surfaced at the right moments, not dumped wholesale into every prompt.

| Pool | When injected | How |
|---|---|---|
| `settlements` | Seed prompt + scene change | Listed under `AVAILABLE PLACE NAMES:` in `generate_seed_user.j2` and `narrate_user.j2` when scene changes |
| `taverns` | Narrate user prompt when scene is indoors / social | Listed under `AVAILABLE LOCATIONS (indoors):` |
| `districts` | Narrate user prompt when scene is urban | Listed under `AVAILABLE DISTRICTS:` |
| `wilderness` | Narrate user prompt when scene is outdoor / travel | Listed under `AVAILABLE AREAS:` |
| `organizations` | Extractor system prompts + narrate when political context present | Listed as `KNOWN FACTIONS:` |
| `rumors` | Narrate user prompt when an NPC is speaking or social context | One or two injected as `AVAILABLE RUMORS (use at most one):` |
| `objects` | Narrate user prompt when loot, discovery, or combat is likely | Listed as `AVAILABLE OBJECT NAMES:` |

The key constraint: **the narrator is told to use names from the pool, not invent new ones.** This keeps the world internally consistent across LLM calls that have no other shared context.

### Injection rule in narrator system prompt

Add to `narrate_system.j2`:

> When the user prompt provides named pools (places, factions, objects, rumors), use names from those pools rather than inventing new ones. Do not use all of them — pick what fits the scene. Unused pool entries remain available for future turns.

---

## Part 4: Locale-Aware Word Lists

The current word lists above are English-default. For packs with non-English or non-Western locale weighting, the adjective/noun pools should shift.

Longer term: move word lists to per-pack configuration (e.g., a Slavic-flavored pack provides its own `_TAVERN_ADJECTIVES`). Short term: a `genre` flag on the pack (`"medieval_western"`, `"far_east"`, `"colonial"`) selects the appropriate built-in list.

```python
_WORD_LISTS_BY_GENRE: dict[str, dict[str, list[str]]] = {
    "medieval_western": {
        "tavern_adj": _TAVERN_ADJECTIVES,
        "wilderness_noun": _WILDERNESS_NOUNS,
        # ...
    },
    "far_east": {
        "tavern_adj": ["Silver", "Jade", "Iron", "Bone", "Black", "Cloud"],
        "wilderness_noun": ["Peak", "Grove", "Ravine", "Marsh", "Gorge", "Shore"],
        # ...
    },
}
```

Select list at `generate_place_pool()` call time based on `pack.genre`.

---

## Integration with `generate_name_pool()`

The cleanest approach: merge place pools into the existing `generate_name_pool()` output structure so callers get everything in one dict:

```python
def generate_name_pool(
    locales: list[dict],
    genre: str = "medieval_western",
    *,
    pc_count: int = 3,
    npc_count: int = 8,
    # ... place counts ...
    seed: int | None = None,
) -> dict[str, list[str]]:
    pool = {
        "pc": [...],
        "npc": [...],
        # place types merged in:
        "settlements": [...],
        "taverns": [...],
        "districts": [...],
        "wilderness": [...],
        "organizations": [...],
        "rumors": [...],
        "objects": [...],
    }
    return pool
```

One call, one dict, backward compatible (callers that only read `"pc"` and `"npc"` are unaffected).

---

## TODO items

Add to `TODO.md` under Mechanics:

- [ ] **Typed place pool generation** — `generate_place_pool()` in `names.py`; settlements, taverns, districts, wilderness; stored in seed manifest. See `plans/world-prop-injection.md`.
- [ ] **Organization/faction name pool** — seeded at game start, injected into narrate prompt when political context is present. See `plans/world-prop-injection.md`.
- [ ] **Rumor pool** — template-filled rumors using seeded NPC names and places; injected into social narration as `AVAILABLE RUMORS`. See `plans/world-prop-injection.md`.
- [ ] **Object epithet pool** — named items pool for loot/discovery/combat turns. See `plans/world-prop-injection.md`.
- [ ] **Narrator prop injection rule** — add rule to `narrate_system.j2` instructing narrator to prefer pool names over invented ones. See `plans/world-prop-injection.md`.
- [ ] **Locale-aware word lists by genre** — `pack.genre` flag selects appropriate `_WORD_LISTS_BY_GENRE` entry. See `plans/world-prop-injection.md`.

---

## Part 5: Location-Keyed NPC Storage

### Problem

NPCs are stored in a flat global compendium. The LRU-based injection (`_known_characters_for_extract`) evicts current-scene NPCs in favor of frequently-seen but irrelevant ones. New NPCs get no compendium entry. This causes duplicate NPC creation and poor context for the extractor.

### Design

Store NPCs per location instead of in a flat global compendium:

- NPCs are stored under `compendium.npcs_by_location[location_id]`
- When the player enters a location, NPCs known to be there are loaded into context
- The extractor writes new NPCs to the current location's list
- A lightweight global index (`compendium.npc_index`: `{id: {name, home_location}}`) handles cross-location references
- Mobile NPCs (followers, recurring characters) have a `home_location` + `currently_at` override

### State schema

```yaml
compendium:
  npc_index:
    kael_marsh:
      name: "Kael Marsh"
      home_location: "durn_tavern"
      currently_at: null  # null = at home location
    torben_klask:
      name: "Torben Klask"
      home_location: "durn_docks"
      currently_at: "durn_tavern"  # mobile — overrides home
  npc_by_location:
    durn_tavern:
      kael_marsh: { name: "Kael Marsh", ... }
      torben_klask: { name: "Torben Klask", ... }
    durn_docks:
      torben_klask: { name: "Torben Klask", ... }
```

### Implementation

**`ccya/state.py`** — add migration in `_migrate_state()`:
```python
def _migrate_npc_storage(state: dict) -> dict:
    """Migrate flat compendium.npcs to location-keyed storage."""
    npcs = state.get("compendium", {}).get("npcs") or {}
    if not npcs:
        return state
    by_location: dict[str, dict] = {}
    index: dict[str, dict] = {}
    for npc_id, npc in npcs.items():
        loc = npc.get("location", "unknown")
        by_location.setdefault(loc, {})[npc_id] = npc
        index[npc_id] = {"name": npc.get("name", npc_id), "home_location": loc, "currently_at": npc.get("currently_at")}
    state.setdefault("compendium", {})["npc_index"] = index
    state.setdefault("compendium", {})["npc_by_location"] = by_location
    del state["compendium"]["npcs"]
    return state
```

**`ccya/engine.py`** — update `_known_characters_for_extract()` to read from `npc_by_location[location]` instead of the flat compendium.

**`ccya/prompts/extract_state_system.j2`** — update NPC context section to render `npc_by_location[location]` instead of the flat list.

### Related: NPC Enrichment

This plan also covers adding richer NPC data to the compendium:

- **Character traits + relationships** — persist `traits: list[str]` and `relationships: dict[str, str]` per NPC in compendium. Extractor emits these from narration.
- **Character avatars** — generated or assigned avatar string per NPC/PC, stored in compendium. Seed from name pool or generate via narrator.
- **Physical descriptions** — generated physical description per NPC at first encounter, stored in compendium. Extractor emits `npc_physical_description` for new NPCs.

All three are model/schema additions to NPC entries — no new architecture needed beyond the location-keyed storage.
