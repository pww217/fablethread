# I-17 #3 Discovery: `dict[str, Any]` State Audit

**Purpose:** Document the current state shape, access patterns, and problems to inform the `WorldState` model design for I-17 #3.

---

## 1. Current State Shape

State is a single `dict[str, Any]` loaded from/saved to `state.yaml`. The default shape (from `state/io.py:_default_state()`) defines **10 top-level sections**:

| Section | Type | Purpose |
|---|---|---|
| `meta` | `dict` | Turn counter, session metadata, history, touch order, pending beats, recent rolls, convergence scores |
| `pc` | `dict` | Player character: name, tagline, bio, stats, conditions, allegiance, situation, directive |
| `location` | `dict` | Current location: id, name, description |
| `inventory` | `list[dict]` | Inventory items with id/name/notes/amount/aliases |
| `arc` | `dict` | Long-term objective: long_term_objective, threads[], completed_threads[], resolution, last_thread_created_turn |
| `scene` | `dict` | Scene state: tags, world_state[], turn_entered, scene_phase, climax_turn_count, breather_turn_count, turns_in_phase, curtain_call |
| `compendium` | `dict` | NPC registry: npcs dict keyed by id (name, title, bio, motivation, fear, leverage, presence, position, personality, tie, party, etc.) |
| `resolved_arcs` | `list[dict]` | Historical arc resolutions with TTL tracking |
| `world_state_candidates` | `list[dict]` | Pending world state facts awaiting sanitizer promotion |
| `world` | `dict` | World metadata: factions, locations |

### Nested structures (key sections)

**`meta`** contains:
- `turn: int` — current turn number
- `setting_pack: str`, `model: str`, `session_name: str`
- `compendium_touch_order: list[str]` — LRU order for NPC eviction
- `prior_history: list[str]` — rolling list of outcome summary bullets (max 10)
- `pending_gm_beat: dict` — beat selected by ruling, consumed by narrate
- `beat_candidates: list[dict]` — generated beats for ruling to select from
- `recent_beats: list[dict]` — rolling history of all generated beats (max 5)
- `recent_rolls: list[dict]` — rolling history of roll outcomes (max 5)
- `smoothed_convergence: float` — EMA-smoothed convergence score
- `last_inventory_change_reason: str`, `last_condition_change_reason: str`
- `last_rules_outcome: dict` — last ruling outcome for world step
- `last_thread_creation_turn: int` — cooldown tracking
- `last_arc_resolve_turn: int`

**`pc`** contains:
- `name: str`, `tagline: str`, `bio: str`
- `stats: dict[str, int]` — {strength/dexterity/wits/charisma: int}
- `conditions: list[dict]` — {id, label, description, turns_remaining, added_turn}
- `allegiance: str | None`
- `situation: dict`
- `directive: str` — from ruling phase
- `actions: list[str]` — rolling window of storyteller actions (max 10)

**`arc`** contains:
- `long_term_objective: str`
- `threads: list[dict]` — ArcThread shapes {id, summary, dormant, urgency, type, major_updates, resolution_state, outcome, resolved_turn, last_updated_turn, added_turn, urgency_set_turn}
- `completed_threads: list[dict]` — same shape, archived threads
- `resolution: str | None`
- `last_thread_created_turn: int`

**`scene`** contains:
- `tags: list[str]`
- `world_state: list[dict]` — {id, text, tier, permanent, valence, expires_turn}
- `turn_entered: int`
- `scene_phase: str` — SETUP/RISING/CLIMAX/RESOLUTION/BREATHER
- `climax_turn_count: int`, `breather_turn_count: int`, `turns_in_phase: int`
- `curtain_call: str` — "forced" | "active" | ""
- `location_entered_turn: int`

**`compendium.npcs`** is a dict keyed by NPC id, each entry:
- `name`, `title`, `bio`, `motivation`, `fear`, `leverage`, `presence`, `position`
- `personality: str` — archetype id
- `tie: str` — personal history
- `party: bool` — companion flag
- `last_presence_turn: int`, `last_seen_location: str`
- `first_seen_turn: int`
- `departed_reason: str`, `departed_turn: int`

---

## 2. Access Patterns

### 2.1 Read access (`state.get()`)

**100+ locations** access state via `state.get("section") or {}` or `state.get("section", {}).get("key")`.

**Common patterns:**
```python
# Section access with fallback
arc = state.get("arc") or {}
scene = state.get("scene") or {}
pc = state.get("pc") or {}
comp = state.get("compendium") or {}

# Nested access
turn = state.get("meta", {}).get("turn", 0)
phase = state.get("scene", {}).get("scene_phase", "SETUP")
threads = (state.get("arc") or {}).get("threads") or []
conditions = (state.get("pc") or {}).get("conditions") or []
npcs = state.get("compendium", {}).get("npcs", {})
world_state = state.get("scene", {}).get("world_state", [])
recent_beats = (state.get("meta") or {}).get("recent_beats", [])
recent_rolls = state.get("meta", {}).get("recent_rolls", [])
pending_beat = (state.get("meta") or {}).get("pending_gm_beat")
```

**Files with heavy `state.get()` usage:**
- `engine/turn.py` — 30+ reads across the turn lifecycle
- `engine/turn_state.py` — 25+ reads for thread/arc operations
- `engine/narrate.py` — 15+ reads for context building
- `engine/_pacing.py` — 10+ reads for phase computation
- `engine/thread_sanitizer.py` — 15+ reads for sanitization
- `engine/world.py` — 8+ reads for beat generation
- `engine/ruling.py` — 8+ reads for ruling context
- `state/delta_builder.py` — 15+ reads for delta reconciliation
- `state/npcs.py` — 5+ reads for NPC scene management
- `prompts/context.py` — 15+ reads in boundary model `from_state()` methods

### 2.2 Mutation access (`state.setdefault()`)

**41+ locations** use `state.setdefault("section", {})["key"] = value` or `state.setdefault("section", {}).setdefault("sub", {})`.

**Common patterns:**
```python
# Simple setdefault
state.setdefault("meta", {})["turn"] = turn_no
state.setdefault("meta", {})["pending_gm_beat"] = beat
state.setdefault("meta", {})["beat_candidates"] = candidates
state.setdefault("meta", {})["recent_beats"].append(beat)
state.setdefault("meta", {})["recent_rolls"].insert(0, roll)
state.setdefault("meta", {})["prior_history"].append(bullet)
state.setdefault("meta", {})["smoothed_convergence"] = smoothed

# Nested setdefault
state.setdefault("scene", {})["world_state"] = filtered
state.setdefault("scene", {})["scene_phase"] = phase
state.setdefault("scene", {})["climax_turn_count"] = count
state.setdefault("pc", {})["conditions"][:] = updated_conds
state.setdefault("compendium", {}).setdefault("npcs", {})[npc_id] = entry
state.setdefault("arc", {}).update(arc_data)
state.setdefault("resolved_arcs", []).append(resolved_arc_entry)
state.setdefault("world_state_candidates", []).append(candidate)
```

**Files with heavy `state.setdefault()` usage:**
- `engine/turn.py` — 15+ mutations (meta, scene, pc, arc)
- `engine/turn_state.py` — 10+ mutations (arc, resolved_arcs, world_state_candidates, pc, meta)
- `engine/narrate.py` — 3+ mutations (scene via _compute_scene_phase)
- `engine/world.py` — 3+ mutations (meta.recent_beats, meta.beat_candidates)
- `state/delta_builder.py` — 8+ mutations (inventory, location, pc.conditions, compendium, arc, scene)
- `state/npcs.py` — 5+ mutations (compendium.npcs)
- `engine/thread_sanitizer.py` — 3+ mutations (scene.world_state, arc)

### 2.3 Deep copy + mutate

Several functions **deep copy state, mutate the copy, return it**:
- `state/delta_builder.py:apply_delta()` — copies state, applies delta, returns new dict
- `engine/extraction/context.py:_build_extraction_context()` — copies state, applies delta, extracts derived context
- `engine/turn.py:run_turn()` — `state_pre_apply = copy.deepcopy(state)` for diff computation

---

## 3. Where State Is Used

### 3.1 Engine pipeline (turn lifecycle)

```
run_turn() [turn.py]
  ├── load_state() → dict[str, Any]
  ├── _ruling_phase() [ruling.py]
  │     └── _ruling_messages() — reads pc, location, arc, scene, meta, compendium
  ├── _narrate_setup() [narrate.py]
  │     └── _narrate_messages() — reads pc, arc, scene, meta, compendium, inventory, location
  ├── _run_extraction_pipeline() [extraction/pipeline.py]
  │     ├── stream 1: scene — reads narration, state
  │     ├── stream 2: state — reads narration, state, intent
  │     └── stream 3: record — reads narration, state, extraction_ctx
  ├── _apply_state_updates() [turn_state.py]
  │     ├── reconcile_delta() — reads pc.conditions
  │     ├── apply_delta() — mutates state (inventory, location, conditions, compendium, arc, actions)
  │     ├── _expire_conditions() — reads pc.conditions
  │     ├── _apply_thread_updates() — reads arc, mutates arc
  │     ├── _apply_arc_resolve() — reads arc, mutates arc + resolved_arcs
  │     ├── _apply_thread_resolutions() — reads arc, mutates arc
  │     └── NPC lifecycle — reads mutates compendium.npcs
  ├── sanitize_threads() [thread_sanitizer.py] — reads arc, scene, mutates arc + scene
  ├── _run_world_step() [world.py] — reads arc, meta, compendium
  └── save_state() → state.yaml
```

### 3.2 Boundary models (prompt context)

`prompts/context.py` defines **6 boundary models** that receive `state: dict[str, Any]` and extract typed snapshots:

| Boundary | Template | `from_state()` reads |
|---|---|---|
| `PlayerBlock` | — | `state["pc"]` → name, tagline, stats, conditions |
| `LocationBlock` | — | `state["location"]` → id, name, description |
| `InventoryBlock` | — | `state["inventory"]` → list of InventoryItem |
| `ArcThreadBlock` | — | `state["arc"]` → long_term_objective, threads, completed_threads |
| `WorldStateBlock` | — | `state["scene"]["world_state"]` → list of strings |
| `NPCRosterEntryBlock` | — | compendium dict → id, name, title, bio, presence, motivation, fear, leverage, notes, last_presence_turn, last_seen_location |

**Boundaries (compose blocks):**
| Boundary | Fields | Template |
|---|---|---|
| `RulingBoundary` | pc, location, user_input, meta, npc_roster, recent_turns, inventory, scene_phase, urgent_threads | `ruling_user.j2` |
| `NarratorBoundary` | pc, current_objective, state, npc_roster, pacing_context, recent_turns, prior_history, rules_outcome, user_input, pending_beat, meta, ages, pc_allegiance, world_factions, npc_name_pool, resolved_arcs | `narrate_user.j2` |
| `SceneExtractBoundary` | narration, npc_roster, pc_name, turn_no | `extract_scene_user.j2` |
| `StateExtractBoundary` | conditions, inventory, location, intent, turn_no, narration | `extract_state_user.j2` |
| `StorytellerBoundary` | narration, npc_roster, location, conditions, inventory, current_objective, all_threads, world_state, intent, pacing_context, recent_turns, prior_history, turn_no, band, scene_phase, curtain_call, allowed_beat_types, pending_beat, recent_beats, resolved_arcs | `storytell_user.j2` |
| `NarratorSystemBoundary` | narrator_rules, world_rules | `narrate_system.j2` |

**Problem:** Boundaries receive `state: dict[str, Any]` and extract fields via `state.get()`. The boundary models are typed Pydantic models, but fields are injected via dicts **outside** the boundary system, so type checking never catches mismatches.

### 3.3 Extraction context

`engine/extraction/context.py:_ExtractionContext` carries derived state from scene + state streams into the storytell stream:
- `comp_this_turn: dict[str, Any]` — post-delta compendium.npcs
- `location_this_turn: dict[str, Any]` — location after scene delta
- `inventory_this_turn: list[dict[str, Any]]` — inventory after state delta
- `conditions_this_turn: list[dict[str, Any]]` — pc.conditions after state delta

Built by applying a combined `StateDelta` to a deep copy of state, then extracting derived sections.

### 3.4 TurnContext

`engine/turn_context.py:TurnContext` carries state across turn phases:
- `state: dict[str, Any]` — the live state dict
- `recent_turns: list[dict[str, Any]]` — chronicle entries
- `_ages: dict[str, int]` — scene_age, effective_scene_age (set by ruling, read by narrate)
- `packing: dict[str, Any]` — includes `inventory` from state

### 3.5 Pacing system

`engine/_pacing.py` functions that read state:
- `_compute_ages(state)` → `{"scene_age": int}` — reads `meta.turn`, `scene.turn_entered`
- `_compute_scene_phase(state, ages, config, convergence_score, turn_no)` → mutates `state["scene"]` — reads `scene`, `arc.threads`
- `compute_convergence_score(scene_phase, active_threads, scene_age, recent_beats, config, turn_no, recent_rolls)` — reads `meta.recent_beats`, `meta.recent_rolls`

### 3.6 Thread sanitizer

`engine/thread_sanitizer.py:sanitize_threads(state, config)` — reads `meta`, `arc`, `scene.world_state`, `world_state_candidates`; mutates `arc`, `scene.world_state`.

### 3.7 World step

`engine/world.py:_run_world_step(state, ...)` — reads `arc`, `meta.recent_beats`, `scene.scene_phase`, `compendium.npcs`, `pc`.

### 3.8 Ruling phase

`engine/ruling.py:_ruling_messages(state, ...)` — reads `pc`, `location`, `arc.threads`, `scene.scene_phase`, `meta.beat_candidates`, `compendium.npcs`.

---

## 4. Pydantic Models vs. Dict State

### 4.1 Models that exist but aren't used for state

`models/state.py` defines typed Pydantic models for **many** state sections, but they are **never used to hold the live state dict**. Instead, they are:
1. Parsed from dict state when needed (`LongTermObjective.model_validate(state.get("arc", {}))`)
2. Used for extraction output (`StateDelta`, `SceneExtractResult`, `StateExtractResult`)
3. Used for boundary models (`PlayerBlock`, `LocationBlock`, etc.)

**Existing models:**
| Model | Section | Used for |
|---|---|---|
| `ArcThread` | `arc.threads[]` | Extraction output, thread operations, sanitizer |
| `LongTermObjective` | `arc` | Thread operations, sanitizer, arc resolve |
| `Condition` | `pc.conditions[]` | Boundary models, ruling, narration |
| `InventoryItem` | `inventory[]` | Boundary models, extraction |
| `LocationRef` | `location` | Extraction output |
| `KeyLocation` | `world.locations[]` | Seed data |
| `WorldStateFact` | `scene.world_state[]` | Extraction output |
| `SanitizedWorldStateFact` | `scene.world_state[]` | Sanitizer output |
| `ThreadResolution` | — | Extraction output |
| `ThreadUpdate` | — | Extraction output, sanitizer |
| `ArcResolution` | — | Extraction output |
| `NpcPresence` (enum) | `compendium.npcs[].presence` | Extraction output, boundary models |
| `ProgressEntry` | `arc.threads[].major_updates[]` | Thread operations, sanitizer |
| `InventoryAdd/Remove/Update` | — | Extraction output |
| `ConditionAdd/Remove` | — | Extraction output |

**Gap:** No Pydantic model exists for the **top-level state container** or for sections like `meta`, `scene`, `compendium.npcs[entry]`, `pc`.

### 4.2 The cast-to-dict problem

Everywhere in the codebase, Pydantic models are **immediately cast back to dicts** via `.model_dump()`:
```python
# turn_state.py:228
state["arc"] = new_arc.model_dump()

# state/delta_builder.py:61-67
arc["threads"] = [t.model_dump(exclude_none=True) for t in au.threads]
arc["completed_threads"] = [t.model_dump(exclude_none=True) for t in au.completed_threads]

# thread_sanitizer.py:500
state.setdefault("arc", {}).update({**_dump_arc(arc), "threads": [t.model_dump() for t in arc.threads], ...})
```

This means **Pydantic validation only happens at the boundary** (extraction output, sanitizer input), not during state access or mutation. The live state is always a plain dict.

---

## 5. Problems Identified

### 5.1 No type safety on state access

Every `state.get("arc") or {}` is untyped. Typos like `state.get("arcs")` silently return `None` → `{}` → empty threads, with no warning.

### 5.2 Boundary models are out of sync

Every boundary model in `context.py` is typed, but fields are injected via dicts **outside** the boundary system. Dead/missing fields are never caught by mypy:
- `RulingBoundary`: has `scene_phase`, `urgent_threads` but boundary models are typed while templates access raw dicts
- `NarratorBoundary`: has `ages`, `resolved_arcs`, `pc_allegiance`, `world_factions`, `npc_name_pool` — all passed as dicts
- `StorytellerBoundary`: has `curtain_call`, `allowed_beat_types`, `recent_beats`, `resolved_arcs` — all passed as dicts

### 5.3 `setdefault()` chains are error-prone

Patterns like `state.setdefault("meta", {}).setdefault("recent_rolls", []).insert(0, {...})` are:
- Hard to read
- Hard to type-check
- Easy to get wrong (e.g., missing `setdefault` on nested key)
- Hard to find all usages of a field

### 5.4 Section shapes are undocumented in code

The shape of `meta`, `scene`, `compendium.npcs[entry]`, etc. is only known by reading the code that reads/writes them. No single source of truth.

### 5.5 Deep copy everywhere

Because state is a mutable dict passed through many functions, `copy.deepcopy(state)` is used extensively:
- `apply_delta()` — copies before mutating
- `_build_extraction_context()` — copies before applying preview delta
- `run_turn()` — copies for diff computation
- Pipeline preview state building (3 copies per turn)

This is necessary but expensive. A structured model could use immutability or copy-on-write to reduce unnecessary copies.

### 5.6 Extraction context is derived via full state copy

`_build_extraction_context()` applies a **full StateDelta to a deep copy of state** just to extract 4 derived fields (compendium, location, inventory, conditions). This is wasteful — it could compute these from the delta alone.

---

## 6. What a `WorldState` Model Needs

### 6.1 Top-level container

```python
class WorldState(BaseModel):
    meta: Meta
    pc: PC
    location: LocationRef
    inventory: list[InventoryItem]
    arc: LongTermObjective
    scene: Scene
    compendium: Compendium
    resolved_arcs: list[dict]  # simple TTL tracking, no model needed
    world_state_candidates: list[dict]  # simple pending facts, no model needed
    world: World  # factions, locations
```

### 6.2 Section models needed

| Section | Model | Fields |
|---|---|---|
| `meta` | `Meta` | turn, setting_pack, model, session_name, compendium_touch_order, prior_history, pending_gm_beat, beat_candidates, recent_beats, recent_rolls, smoothed_convergence, last_inventory_change_reason, last_condition_change_reason, last_rules_outcome, last_thread_creation_turn, last_arc_resolve_turn |
| `pc` | `PC` | name, tagline, bio, stats, conditions, allegiance, situation, directive, actions |
| `scene` | `Scene` | tags, world_state, turn_entered, scene_phase, climax_turn_count, breather_turn_count, turns_in_phase, curtain_call, location_entered_turn |
| `compendium` | `Compendium` | npcs: dict[str, NPCEntry] |
| `NPCEntry` | `NPCEntry` | name, title, bio, motivation, fear, leverage, presence, position, personality, tie, party, last_presence_turn, last_seen_location, first_seen_turn, departed_reason, departed_turn |
| `World` | `World` | factions, locations |

### 6.3 Backward compatibility

Since state is persisted as YAML and loaded from disk, the `WorldState` model must:
1. **Accept raw dicts** via `model_validate(raw_dict)` — Pydantic handles this naturally
2. **Export to raw dicts** via `model_dump()` for YAML serialization
3. **Coerce missing sections** with sensible defaults (like `_default_state()`)
4. **Coerce legacy field names** (e.g., `active` → `dormant` on ArcThread, already handled)

### 6.4 Migration strategy

The migration from `dict[str, Any]` to `WorldState` should be **phased**:

1. **Phase 01:** Define `WorldState` model + section models in `models/state.py`. No runtime changes.
2. **Phase 02:** Add `WorldState.from_dict()` / `WorldState.to_dict()` helpers. Wire through `load_state()` / `save_state()`.
3. **Phase 03:** Update read access — functions take `WorldState` instead of `dict[str, Any]`.
4. **Phase 04:** Update mutation access — functions mutate `WorldState` fields directly.
5. **Phase 05:** Cleanup — remove `dict[str, Any]` casts, dead re-exports, unused patterns.

### 6.5 Files that need updating

| Phase | Files |
|---|---|
| 01 | `models/state.py` — add WorldState + section models |
| 02 | `state/io.py` — load/save WorldState; `engine/turn_context.py` — TurnContext.state type |
| 03 | `engine/turn.py`, `engine/turn_state.py`, `engine/narrate.py`, `engine/_pacing.py`, `engine/thread_sanitizer.py`, `engine/world.py`, `engine/ruling.py`, `engine/extraction/context.py`, `prompts/context.py` |
| 04 | `state/delta_builder.py`, `state/npcs.py`, `engine/turn.py`, `engine/turn_state.py` |
| 05 | `engine/extraction/pipeline.py`, `engine/config.py`, everywhere else |

---

## 7. Key Insights

1. **Pydantic models already exist for most sections** — the gap is the top-level container and a few sections (meta, scene, pc, compendium).

2. **The cast-to-dict round-trip is the core waste** — models are parsed, validated, then immediately dumped back to dicts. With a typed `WorldState`, this round-trip disappears.

3. **Boundary models are the symptom, not the root cause** — they're typed but receive untyped dicts. Fixing the root cause (typed state) naturally fixes the symptom.

4. **Deep copy is a workaround for mutability** — if state were immutable (or copy-on-write), the deep copies would be unnecessary.

5. **Extraction context could be computed from deltas alone** — not from full state copies. This is a separate optimization from the WorldState model.

6. **YAML persistence is the anchor** — any solution must work with the existing YAML load/save cycle. The WorldState model is an **engine-internal** abstraction, not a storage format change.
