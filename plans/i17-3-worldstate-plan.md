# I-17 #3 Plan: WorldState Model

**Ticket:** I-17 #3 — `dict[str, Any]` state everywhere
**Status:** up-next
**Size:** large (5 phases, ~15 files, ~800 lines of model code, ~500 lines of migration)
**Risk:** medium — foundational change, but no behavioral change expected

---

## Design Reference

Discovery doc: `docs/discovery/i17-3-worldstate-audit.md`

---

## Problem

State is a single `dict[str, Any]` passed through 51+ functions across `engine/`, `state/`, and `prompts/`. Access is via `state.get("arc") or {}`, `state.get("meta", {}).get("turn", 0)` in 100+ locations. Pydantic models in `models/state.py` are parsed but immediately cast back to dicts via `.model_dump()`. This means:

1. **No type safety** — typos like `state.get("arcs")` silently return `None` → `{}`
2. **Boundary models are out of sync** — typed Pydantic models in `prompts/context.py` receive untyped dicts, so dead/missing fields are never caught by mypy
3. **setdefault() chains are error-prone** — `state.setdefault("meta", {}).setdefault("recent_rolls", []).insert(0, {...})` is hard to read, type-check, and find
4. **Deep copy everywhere** — `copy.deepcopy(state)` used in 5+ places as a workaround for mutability
5. **No single source of truth** — section shapes only known by reading code that reads/writes them

---

## Solution

Create a structured `WorldState` Pydantic model for engine-internal use. The model wraps the existing YAML persistence format — it is an **engine-internal abstraction**, not a storage format change.

### Backward compatibility

YAML persistence is the anchor. The `WorldState` model must:
1. Accept raw dicts via `model_validate(raw_dict)` — Pydantic handles this naturally
2. Export to raw dicts via `model_dump()` for YAML serialization
3. Coerce missing sections with sensible defaults (like `_default_state()`)
4. Coerce legacy field names (e.g., `active` → `dormant` on ArcThread, already handled)

---

## Phases

### Phase 01: Define `WorldState` model + section models

**Goal:** Add typed Pydantic models for all state sections in `models/state.py`. No runtime changes.

**Files:** `ccya/models/state.py`

**Tasks:**

#### 01-1: Add `Meta` model

Fields from `_default_state()["meta"]` and observed access patterns:

```python
class Meta(BaseModel):
    turn: int = 0
    setting_pack: str = ""
    model: str = ""
    session_name: str = ""
    compendium_touch_order: list[str] = Field(default_factory=list)
    prior_history: list[str] = Field(default_factory=list)
    pending_gm_beat: dict[str, Any] | None = None
    beat_candidates: list[dict[str, Any]] = Field(default_factory=list)
    recent_beats: list[dict[str, Any]] = Field(default_factory=list)
    recent_rolls: list[dict[str, Any]] = Field(default_factory=list)
    smoothed_convergence: float = 0.0
    last_inventory_change_reason: str | None = None
    last_condition_change_reason: str | None = None
    last_rules_outcome: dict[str, Any] | None = None
    last_thread_creation_turn: int | None = None
    last_arc_resolve_turn: int | None = None
```

**Why:** `meta` is the most-accessed section (turn counter, recent beats, rolls, pending beats, convergence). 30+ `state.get("meta")` calls across the codebase.

#### 01-2: Add `PC` model

Fields from `_default_state()["pc"]` and observed access patterns:

```python
class PC(BaseModel):
    name: str = ""
    tagline: str = ""
    bio: str = ""
    stats: dict[str, int] = Field(default_factory=lambda: {"strength": 2, "dexterity": 2, "wits": 2, "charisma": 2})
    conditions: list[Condition] = Field(default_factory=list)
    allegiance: str | None = None
    situation: dict[str, Any] = Field(default_factory=dict)
    directive: str = ""
    actions: list[str] = Field(default_factory=list)
```

**Why:** `pc` is accessed in ruling, narrate, world, extraction, delta_builder. 15+ `state.get("pc")` calls.

#### 01-3: Add `Scene` model

Fields from `_default_state()["scene"]` and observed access patterns:

```python
class Scene(BaseModel):
    tags: list[str] = Field(default_factory=list)
    world_state: list[dict[str, Any]] = Field(default_factory=list)
    turn_entered: int = 0
    scene_phase: str = "SETUP"
    climax_turn_count: int = 0
    breather_turn_count: int = 0
    turns_in_phase: int = 0
    curtain_call: str = ""
    location_entered_turn: int = 0
```

**Why:** `scene` is accessed in pacing, narrate, ruling, world, sanitizer, delta_builder. 20+ `state.get("scene")` calls.

#### 01-4: Add `Compendium` and `NPCEntry` models

```python
class NPCEntry(BaseModel):
    name: str = ""
    title: str | None = None
    bio: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: NpcPresence = NpcPresence.KNOWN
    position: str | None = None
    personality: str | None = None
    tie: str | None = None
    party: bool = False
    last_presence_turn: int | None = None
    last_seen_location: str | None = None
    first_seen_turn: int | None = None
    departed_reason: str | None = None
    departed_turn: int | None = None

class Compendium(BaseModel):
    npcs: dict[str, NPCEntry] = Field(default_factory=dict)
```

**Why:** `compendium.npcs` is accessed in ruling, narrate, world, extraction, delta_builder, npcs.py. 15+ `state.get("compendium")` calls. NPCEntry fields are set by `state/npcs.py:apply_npc_scene_management()`.

#### 01-5: Add `World` model

```python
class World(BaseModel):
    factions: list[dict[str, str]] = Field(default_factory=list)
    locations: list[KeyLocation] = Field(default_factory=list)
```

**Why:** `world` is accessed in seed data and narration context.

#### 01-6: Add `WorldState` top-level container

```python
class WorldState(BaseModel):
    meta: Meta
    pc: PC
    location: LocationRef
    inventory: list[InventoryItem]
    arc: LongTermObjective
    scene: Scene
    compendium: Compendium
    resolved_arcs: list[dict[str, Any]] = Field(default_factory=list)
    world_state_candidates: list[dict[str, Any]] = Field(default_factory=list)
    world: World
```

**Why:** This is the single source of truth for engine-internal state. Replaces `dict[str, Any]` everywhere.

#### 01-7: Add `WorldState.from_dict()` and `WorldState.to_dict()` helpers

```python
@classmethod
def from_dict(cls, raw: dict[str, Any]) -> "WorldState":
    """Validate and coerce raw YAML dict into WorldState."""
    # Apply defaults for missing sections
    defaults = _default_state()
    merged = {**defaults, **raw}
    return cls.model_validate(merged)

def to_dict(self) -> dict[str, Any]:
    """Export WorldState to raw dict for YAML serialization."""
    return self.model_dump(exclude_none=False)
```

**Why:** Bridges YAML persistence (raw dicts) with engine-internal typed access.

**Verification:** `make typecheck` passes. No runtime changes yet — models are defined but not used.

---

### Phase 02: Wire `WorldState` through I/O

**Goal:** `load_state()` and `save_state()` use `WorldState`. `TurnContext.state` is typed. No behavioral change.

**Files:** `ccya/state/io.py`, `ccya/engine/turn_context.py`

**Tasks:**

#### 02-1: Update `load_state()` to return `WorldState`

```python
def load_state(save_dir: Path) -> WorldState:
    path = save_dir / "state.yaml"
    if not path.exists():
        return WorldState.from_dict(_default_state())
    # ... load YAML ...
    return WorldState.from_dict(raw)
```

**Why:** Single entry point for state loading. All callers get a typed `WorldState`.

#### 02-2: Update `save_state()` to accept `WorldState`

```python
def save_state(save_dir: Path, state: WorldState) -> None:
    raw = state.to_dict()
    raw = _coerce_enums(raw)
    # ... write YAML ...
```

**Why:** Single exit point for state saving. `to_dict()` handles enum coercion via model_dump.

#### 02-3: Update `TurnContext.state` type

```python
@dataclass
class TurnContext:
    state: WorldState  # was: dict[str, Any]
    # ... rest unchanged
```

**Why:** `TurnContext` is the shared context across all turn phases. Typing it propagates to all phases.

#### 02-4: Update `init_save_dir()` to accept `WorldState`

```python
def init_save_dir(save_dir: Path, seed: WorldState) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    # ... rest unchanged
```

**Verification:** `make typecheck` passes. `load_state()` returns `WorldState`, `save_state()` accepts `WorldState`. All callers need updating in Phase 03.

---

### Phase 03: Migrate read access

**Goal:** Functions that only read state take `WorldState` instead of `dict[str, Any]`. No mutation changes yet.

**Files:** `ccya/engine/turn.py`, `ccya/engine/turn_state.py`, `ccya/engine/narrate.py`, `ccya/engine/_pacing.py`, `ccya/engine/thread_sanitizer.py`, `ccya/engine/world.py`, `ccya/engine/ruling.py`, `ccya/engine/extraction/context.py`, `ccya/prompts/context.py`, `ccya/engine/extraction/pipeline.py`

**Tasks:**

#### 03-1: Update `turn.py` — `run_turn()` and inline reads

Replace all `state.get("section")` with `state.section` access. Key changes:

```python
# Before:
turn_no = state.get("meta", {}).get("turn", 0) + 1
scene = state.get("scene") or {}
pc = state.get("pc") or {}
comp = state.get("compendium") or {}
threads = (state.get("arc") or {}).get("threads") or []

# After:
turn_no = state.meta.turn + 1
scene = state.scene
pc = state.pc
comp = state.compendium
threads = state.arc.threads
```

**Specific locations in `turn.py`:**
- Line 92: `_recent_turn_count(state)` — remove, function is trivial now
- Line 121: `turn_no = state.meta.turn + 1`
- Line 132: `state.scene.world_state` — TTL expiry loop
- Line 150: `state.meta.recent_rolls` — roll tracking
- Line 352: `state.meta.turn` — turn increment (will move to Phase 04)
- Line 399-412: scene_phase, climax_turn_count, breather_turn_count, location_id — direct access
- Line 474: `state.meta.turn` — prior_history bullet
- Line 500: `state.scene.scene_phase` — scene phase for TurnResult
- Line 510-511: `state.meta.turn` — logging
- Line 525: `state.meta.turn` — logging
- Line 558: `state.meta.turn` — logging
- Line 561: `state.meta.beat_candidates` — (will move to Phase 04)
- Line 585: `save_state(save_dir, state)` — already typed from Phase 02

**Verification:** `make typecheck` passes for `turn.py`.

#### 03-2: Update `_pacing.py` — `_compute_ages`, `_compute_scene_phase`, `compute_convergence_score`

```python
# Before:
def _compute_ages(state: dict[str, Any]) -> dict[str, int]:
    meta = state.get("meta") or {}
    scene = state.get("scene") or {}
    current_turn = meta.get("turn", 0)
    scene_entered = scene.get("turn_entered", 0)
    scene_age = current_turn - scene_entered
    return {"scene_age": scene_age}

# After:
def _compute_ages(state: WorldState) -> dict[str, int]:
    scene_age = state.meta.turn - state.scene.turn_entered
    return {"scene_age": scene_age}
```

```python
# Before:
def _compute_scene_phase(state: dict[str, Any], ...) -> dict[str, Any]:
    scene = state.get("scene") or {}
    phase = scene.get("scene_phase", "SETUP")
    # ...
    _raw_threads = (state.get("arc") or {}).get("threads") or []
    # ...
    return {**scene, "scene_phase": phase, ...}

# After:
def _compute_scene_phase(state: WorldState, ...) -> WorldState:
    scene = state.scene
    phase = scene.scene_phase
    # ...
    threads = state.arc.threads
    # ...
    updated_scene = scene.model_copy(update={...})
    return state.model_copy(update={"scene": updated_scene})
```

**Specific locations in `_pacing.py`:**
- Line 200-211: `_compute_ages` — simplify to direct field access
- Line 214-308: `_compute_scene_phase` — take `WorldState`, return `WorldState`, access `state.scene`, `state.arc.threads`
- Line 52-128: `compute_convergence_score` — take `list[ArcThread]` instead of `list[dict[str, Any]]` for `active_threads`

**Verification:** `make typecheck` passes for `_pacing.py`.

#### 03-3: Update `ruling.py` — `_ruling_messages`, `_ruling_phase`

```python
# Before:
def _ruling_messages(env, state: dict[str, Any], ...):
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    arc = state.get("arc") or {}
    threads = arc.get("threads") or []
    # ...

# After:
def _ruling_messages(env, state: WorldState, ...):
    pc = state.pc
    location = state.location
    arc = state.arc
    threads = arc.threads
    # ...
```

**Specific locations in `ruling.py`:**
- Line 27-77: `_ruling_messages` — take `WorldState`, access `state.pc`, `state.location`, `state.arc.threads`, `state.meta.beat_candidates`
- Line 155-323: `_ruling_phase` — take `TurnContext` (already has `state: WorldState`), access `ctx.state.pc`, `ctx.state.scene`, `ctx.state.meta`, `ctx.state.compendium.npcs`
- Line 167-169: compendium, scene_phase, beat_candidates — direct access
- Line 253: `state.pc.stats` — resolve_check
- Line 285: `state.arc.threads` — de-escalation check
- Line 294: `state.scene.tags` — combat boost

**Verification:** `make typecheck` passes for `ruling.py`.

#### 03-4: Update `narrate.py` — `_narrate_messages`, `_narrate_setup`

```python
# Before:
def _narrate_messages(env, state: dict[str, Any], ...):
    comp = (state.get("compendium") or {}).get("npcs") or {}
    arc = state.get("arc") or {}
    # ...

# After:
def _narrate_messages(env, state: WorldState, ...):
    comp = state.compendium.npcs
    arc = state.arc
    # ...
```

**Specific locations in `narrate.py`:**
- Line 27-129: `_narrate_messages` — take `WorldState`, access `state.compendium.npcs`, `state.arc`, `state.pc`, `state.meta`, `state.scene`, `state.inventory`, `state.location`
- Line 132-140: `_get_resolved_arcs` — take `WorldState`, access `state.resolved_arcs`
- Line 143-255: `_narrate_setup` — take `TurnContext`, access `ctx.state.scene`, `ctx.state.meta`, `ctx.state.arc`, `ctx.state.compendium.npcs`
- Line 51: compendium access
- Line 59: arc access
- Line 91: prior_history
- Line 151: turn_no
- Line 158: meta.turn
- Line 168: pending_gm_beat
- Line 171: pc.allegiance
- Line 177-181: scene defaults (will move to Phase 04)
- Line 184: arc.threads
- Line 202: meta.recent_beats
- Line 205: meta.recent_rolls
- Line 218: scene mutation (will move to Phase 04)
- Line 241: compendium.npcs
- Line 250: compendium.npcs

**Verification:** `make typecheck` passes for `narrate.py`.

#### 03-5: Update `thread_sanitizer.py` — `sanitize_threads`, `_build_messages`, `_apply_sanitization`

```python
# Before:
async def sanitize_threads(save_dir, state: dict[str, Any], config, ...):
    meta = state.get("meta") or {}
    arc = state.get("arc") or {}
    # ...

# After:
async def sanitize_threads(save_dir, state: WorldState, config, ...):
    meta = state.meta
    arc = state.arc
    # ...
```

**Specific locations in `thread_sanitizer.py`:**
- Line 20-36: `sanitize_threads` — take `WorldState`, access `state.meta.turn`
- Line 39-130: `_sanitize_threads_impl` — take `WorldState`, access `state.meta`, `state.arc`, `state.world_state_candidates`, `state.scene.world_state`
- Line 133-174: `_build_messages` — take `WorldState`, access `state.arc`, `state.world_state_candidates`, `state.scene.world_state`
- Line 328-502: `_apply_sanitization` — take `WorldState`, access `state.arc`, `state.scene.world_state`, `state.world_state_candidates` (will need mutation access in Phase 04)

**Verification:** `make typecheck` passes for `thread_sanitizer.py`.

#### 03-6: Update `world.py` — `_run_world_step`

```python
# Before:
async def _run_world_step(env, state: dict[str, Any], ...):
    arc = state.get("arc") or {}
    recent_beats = list((state.get("meta") or {}).get("recent_beats", []) or [])
    scene_phase = (state.get("scene") or {}).get("scene_phase", "SETUP")
    comp = state.get("compendium", {}).get("npcs", {})
    pc = state.get("pc") or {}
    # ...

# After:
async def _run_world_step(env, state: WorldState, ...):
    arc = state.arc
    recent_beats = list(state.meta.recent_beats)
    scene_phase = state.scene.scene_phase
    comp = state.compendium.npcs
    pc = state.pc
    # ...
```

**Specific locations in `world.py`:**
- Line 23-210: `_run_world_step` — take `WorldState`, access `state.arc`, `state.meta.recent_beats`, `state.scene.scene_phase`, `state.compendium.npcs`, `state.pc`
- Line 41-53: arc, recent_beats, scene_phase, comp, pc — direct access
- Line 198-207: meta.recent_beats mutation (will move to Phase 04)

**Verification:** `make typecheck` passes for `world.py`.

#### 03-7: Update `turn_state.py` — thread operations, validation, condition expiry

```python
# Before:
def _apply_thread_updates(state: dict[str, Any], ...):
    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1
    # ...

# After:
def _apply_thread_updates(state: WorldState, ...):
    arc = state.arc
    turn_no = state.meta.turn + 1
    # ...
```

**Specific locations in `turn_state.py`:**
- Line 17-165: `_apply_thread_updates` — take `WorldState`, access `state.arc`, `state.meta.turn`
- Line 168-231: `_apply_arc_resolve` — take `WorldState`, access `state.arc`, `state.meta.turn`, `state.resolved_arcs` (will need mutation access in Phase 04)
- Line 234-320: `_apply_thread_resolutions` — take `WorldState`, access `state.arc`, `state.meta.turn`, `state.world_state_candidates` (will need mutation access in Phase 04)
- Line 323-375: `_validate` — take `WorldState`, access `state.inventory`
- Line 378-424: `_expire_conditions` — take `WorldState`, access `state.pc.conditions` (will need mutation access in Phase 04)
- Line 427-685: `_apply_state_updates` — take `WorldState`, access `state.compendium.npcs`, `state.location`, `state.arc`, `state.meta` (will need mutation access in Phase 04)

**Verification:** `make typecheck` passes for `turn_state.py`.

#### 03-8: Update `extraction/context.py` — `_build_extraction_context`

```python
# Before:
def _build_extraction_context(state: dict[str, Any], ...):
    state_copy = copy.deepcopy(state)
    post_state = apply_delta(state_copy, combined_delta)
    post_pc = post_state.get("pc") or {}
    # ...

# After:
def _build_extraction_context(state: WorldState, ...):
    # Still need copy for preview — apply_delta returns WorldState
    state_copy = copy.deepcopy(state)
    post_state = apply_delta(state_copy, combined_delta)
    post_pc = post_state.pc
    # ...
```

**Specific locations in `extraction/context.py`:**
- Line 33-71: `_build_extraction_context` — take `WorldState`, access `state.pc`, `state.location`, `state.compendium.npcs`, `state.inventory`

**Verification:** `make typecheck` passes for `extraction/context.py`.

#### 03-9: Update `prompts/context.py` — boundary models

Replace `from_state(cls, state: dict[str, Any])` with `from_state(cls, state: WorldState)`:

```python
# Before:
@classmethod
def from_state(cls, state: dict[str, Any]) -> PlayerBlock:
    pc = state.get("pc", {})
    return cls(name=pc.get("name", "Unnamed"), ...)

# After:
@classmethod
def from_state(cls, state: WorldState) -> PlayerBlock:
    pc = state.pc
    return cls(name=pc.name or "Unnamed", ...)
```

**Specific locations in `prompts/context.py`:**
- Line 37-46: `PlayerBlock.from_state` — access `state.pc.name`, `state.pc.tagline`, `state.pc.stats`, `state.pc.conditions`
- Line 56-63: `LocationBlock.from_state` — access `state.location.id`, `state.location.name`, `state.location.description`
- Line 71-74: `InventoryBlock.from_state` — access `state.inventory`
- Line 126-164: `ArcThreadBlock.from_state` — access `state.arc.long_term_objective`, `state.arc.threads`, `state.arc.completed_threads`, `state.arc.resolution`
- Line 172-175: `WorldStateBlock.from_state` — access `state.scene.world_state`
- Line 107-115: `_filter_completed_threads` — take `LongTermObjective` instead of `dict[str, Any]`

**Verification:** `make typecheck` passes for `prompts/context.py`.

#### 03-10: Update `extraction/pipeline.py` — stream access

```python
# Before:
async def _run_extraction_pipeline(env, state: dict[str, Any], ...):
    scene_msgs = _extract_scene_messages(env, narration, state, ...)
    # ...

# After:
async def _run_extraction_pipeline(env, state: WorldState, ...):
    scene_msgs = _extract_scene_messages(env, narration, state, ...)
    # ...
```

**Specific locations in `extraction/pipeline.py`:**
- Line 35-351: `_run_extraction_pipeline` — take `WorldState`, access `state.compendium.npcs`, `state.inventory`, `state.arc`, `state.meta`
- Line 73-76: scene stream — pass `state` to `_extract_scene_messages`
- Line 128-133: state stream — pass `state` to `_extract_state_messages`
- Line 197: extraction_ctx — pass `state` to `_build_extraction_context`
- Line 223-224: fallback actions — access `state.inventory`, `state.arc.long_term_objective`
- Line 280-284: panel_update — access `state.arc`, `state.scene`, `state.meta`
- Line 288-298: compendium dedup — access `state.compendium.npcs`

**Verification:** `make typecheck` passes for `extraction/pipeline.py`.

---

### Phase 04: Migrate mutation access

**Goal:** Functions that mutate state use typed accessors/mutators on `WorldState`. No more `state.setdefault()`.

**Files:** `ccya/state/delta_builder.py`, `ccya/state/npcs.py`, `ccya/engine/turn.py`, `ccya/engine/turn_state.py`, `ccya/engine/narrate.py`, `ccya/engine/world.py`, `ccya/engine/thread_sanitizer.py`

**Tasks:**

#### 04-1: Add typed mutators to `WorldState`

Add methods to `WorldState` for common mutation patterns:

```python
class WorldState(BaseModel):
    # ... fields from Phase 01 ...

    def set_turn(self, turn: int) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"turn": turn})})

    def add_recent_beat(self, beat: dict[str, Any], max_size: int = 5) -> "WorldState":
        beats = list(self.meta.recent_beats)
        beats.append(beat)
        beats = beats[-max_size:]
        return self.model_copy(update={"meta": self.meta.model_copy(update={"recent_beats": beats})})

    def add_recent_roll(self, roll: dict[str, Any], max_size: int = 5) -> "WorldState":
        rolls = [roll] + list(self.meta.recent_rolls)
        rolls = rolls[:max_size]
        return self.model_copy(update={"meta": self.meta.model_copy(update={"recent_rolls": rolls})})

    def add_prior_history_bullet(self, bullet: str) -> "WorldState":
        history = list(self.meta.prior_history)
        history.append(bullet)
        history = history[-10:]
        return self.model_copy(update={"meta": self.meta.model_copy(update={"prior_history": history})})

    def set_pending_beat(self, beat: dict[str, Any] | None) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"pending_gm_beat": beat})})

    def set_beat_candidates(self, candidates: list[dict[str, Any]]) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"beat_candidates": candidates})})

    def set_last_inventory_change_reason(self, reason: str | None) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"last_inventory_change_reason": reason})})

    def set_last_condition_change_reason(self, reason: str | None) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"last_condition_change_reason": reason})})

    def set_last_rules_outcome(self, outcome: dict[str, Any] | None) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"last_rules_outcome": outcome})})

    def set_last_thread_creation_turn(self, turn: int) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"last_thread_creation_turn": turn})})

    def set_last_arc_resolve_turn(self, turn: int) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"last_arc_resolve_turn": turn})})

    def set_smoothed_convergence(self, score: float) -> "WorldState":
        return self.model_copy(update={"meta": self.meta.model_copy(update={"smoothed_convergence": score})})

    def set_world_state(self, facts: list[dict[str, Any]]) -> "WorldState":
        return self.model_copy(update={"scene": self.scene.model_copy(update={"world_state": facts})})

    def expire_world_state_facts(self, expired_ids: list[str]) -> "WorldState":
        facts = [f for f in self.scene.world_state if not (isinstance(f, dict) and f.get("id") in expired_ids)]
        return self.model_copy(update={"scene": self.scene.model_copy(update={"world_state": facts})})

    def set_scene_phase(self, phase: str, **kwargs) -> "WorldState":
        scene = self.scene.model_copy(update={"scene_phase": phase, **kwargs})
        return self.model_copy(update={"scene": scene})

    def add_npc(self, npc_id: str, entry: NPCEntry) -> "WorldState":
        npcs = dict(self.compendium.npcs)
        npcs[npc_id] = entry
        return self.model_copy(update={"compendium": self.compendium.model_copy(update={"npcs": npcs})})

    def update_npc(self, npc_id: str, **kwargs) -> "WorldState":
        npcs = dict(self.compendium.npcs)
        if npc_id in npcs:
            npcs[npc_id] = npcs[npc_id].model_copy(update=kwargs)
        return self.model_copy(update={"compendium": self.compendium.model_copy(update={"npcs": npcs})})

    def add_condition(self, condition: Condition) -> "WorldState":
        conditions = list(self.pc.conditions)
        conditions.append(condition)
        return self.model_copy(update={"pc": self.pc.model_copy(update={"conditions": conditions})})

    def remove_condition(self, condition_id: str) -> "WorldState":
        conditions = [c for c in self.pc.conditions if c.id != condition_id]
        return self.model_copy(update={"pc": self.pc.model_copy(update={"conditions": conditions})})

    def expire_conditions(self, expired_ids: list[str]) -> "WorldState":
        """Decrement turns_remaining on all conditions, remove expired ones.
        
        Matches current _expire_conditions() logic: decrement int turns,
        remove if new_remaining <= 0, keep "permanent" as-is.
        """
        updated_conds = []
        for c in self.pc.conditions:
            if c.turns_remaining == "permanent":
                updated_conds.append(c)
                continue
            if isinstance(c.turns_remaining, int):
                new_remaining = c.turns_remaining - 1
                if new_remaining <= 0:
                    continue  # removed
                else:
                    updated_conds.append(c.model_copy(update={"turns_remaining": new_remaining}))
            else:
                updated_conds.append(c)  # unknown type, keep as-is
        return self.model_copy(update={"pc": self.pc.model_copy(update={"conditions": updated_conds})})
```

**Why:** Replaces `state.setdefault("meta", {})["turn"] = ...` patterns with typed, self-documenting mutators. Each mutator returns a new `WorldState` (immutable pattern), avoiding the need for `copy.deepcopy`.

#### 04-2: Update `turn.py` — turn increment, scene phase, beat tracking

Replace `state.setdefault()` chains with mutators:

```python
# Before:
state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

# After:
state = state.set_turn(state.meta.turn + 1)
```

```python
# Before:
state.setdefault("scene", {})["world_state"] = [f for f in ws if ...]

# After:
state = state.expire_world_state_facts(expired_ids)
```

```python
# Before:
state.setdefault("meta", {}).setdefault("recent_rolls", []).insert(0, {"turn": turn_no, "band": ctx.outcome.band})
if len(recent_rolls) > 5:
    recent_rolls.pop()

# After:
state = state.add_recent_roll({"turn": turn_no, "band": ctx.outcome.band})
```

**Specific locations in `turn.py`:**
- Line 140: `state.setdefault("scene", {})["world_state"]` → `state = state.expire_world_state_facts(expired_ids)`
- Line 150-153: `state.setdefault("meta", {}).setdefault("recent_rolls", [])` → `state = state.add_recent_roll({"turn": turn_no, "band": ctx.outcome.band})`
- Line 352: `state.setdefault("meta", {})["turn"]` → `state = state.set_turn(state.meta.turn + 1)`
- Line 476-480: `state.setdefault("meta", {}).setdefault("prior_history", [])` → `state = state.add_prior_history_bullet(bullet)`
- Line 561: `state.setdefault("meta", {})["beat_candidates"]` → `state = state.set_beat_candidates(beat_candidates)`
- Line 585: `save_state(save_dir, state)` — state is now WorldState, save_state accepts WorldState

**Verification:** `make typecheck` passes for `turn.py`.

#### 04-3: Update `narrate.py` — scene phase computation, convergence, scene defaults

```python
# Before:
scene = state.setdefault("scene", {})
scene.setdefault("scene_phase", "SETUP")
scene.setdefault("climax_turn_count", 0)
scene.setdefault("breather_turn_count", 0)
scene_phase = scene.get("scene_phase", "SETUP")
state["scene"] = _compute_scene_phase(state, ctx._ages, config, _convergence_score, turn_no)
scene_phase = state["scene"].get("scene_phase", "SETUP")

# After:
scene = state.scene
scene_phase = scene.scene_phase
state = state.set_scene_phase(
    scene_phase,
    climax_turn_count=...,
    breather_turn_count=...,
    turns_in_phase=...,
    curtain_call=...,
)
```

**Specific locations in `narrate.py`:**
- Line 177-181: scene defaults → remove, scene always has defaults from WorldState model
- Line 209-215: `state.setdefault("meta", {})["smoothed_convergence"]` → `state = state.set_smoothed_convergence(smoothed)`
- Line 218: `state["scene"] = _compute_scene_phase(...)` → `state = _compute_scene_phase(state, ...)` (returns WorldState)

**Verification:** `make typecheck` passes for `narrate.py`.

#### 04-4: Update `turn_state.py` — thread operations, arc resolve, conditions

Replace `state.setdefault()` and `state["key"] = value` with mutators:

```python
# Before:
state["arc"] = new_arc.model_dump()
state.setdefault("resolved_arcs", []).append(resolved_arc_entry)
state.setdefault("meta", {})["last_arc_resolve_turn"] = turn_no

# After:
state = state.model_copy(update={"arc": new_arc, "resolved_arcs": list(state.resolved_arcs) + [resolved_arc_entry], "meta": state.meta.model_copy(update={"last_arc_resolve_turn": turn_no})})
```

**Specific locations in `turn_state.py`:**
- Line 208: `state.setdefault("resolved_arcs", []).append(...)` → `state.model_copy(update={"resolved_arcs": list(state.resolved_arcs) + [resolved_arc_entry]})`
- Line 228: `state["arc"] = new_arc.model_dump()` → `state.model_copy(update={"arc": new_arc})`
- Line 229: `state.setdefault("meta", {})["last_arc_resolve_turn"]` → `state.set_last_arc_resolve_turn(turn_no)`
- Line 298-302: `state.setdefault("world_state_candidates", []).append(...)` → `state.model_copy(update={"world_state_candidates": list(state.world_state_candidates) + [candidate]})`
- Line 424: `(state.setdefault("pc", {})["conditions"])[:] = updated_conds` → `state = state.expire_conditions(expired_ids)` (or direct model_copy for in-place update)
- Line 473-478: `state.setdefault("meta", {})["last_inventory_change_reason"]` → `state.set_last_inventory_change_reason(delta.inventory_change_reason)`
- Line 483-489: `state.setdefault("meta", {})["last_condition_change_reason"]` → `state.set_last_condition_change_reason(delta.condition_change_reason)`
- Line 492-503: compendium.npcs update → `state.update_npc(npc_id, last_presence_turn=..., last_seen_location=...)`
- Line 507-556: arc updates → `state.model_copy(update={"arc": updated_arc})`
- Line 519: `state.setdefault("arc", {})["long_term_objective"]` → `state.model_copy(update={"arc": state.arc.model_copy(update={"long_term_objective": ...})})`
- Line 561, 569, 570, 610: meta turns → `state.set_last_thread_creation_turn(turn_no_for_add)`
- Line 609, 645: arc merge → `state.model_copy(update={"arc": updated_arc})`

**Verification:** `make typecheck` passes for `turn_state.py`.

#### 04-5: Update `delta_builder.py` — `apply_delta`, `_merge_arc_update`

Replace `state.setdefault()` chains with mutators:

```python
# Before:
state["inventory"] = inv
state["location"] = {...}
state.setdefault("compendium", {}).setdefault("npcs", {})[npc_id] = entry
state.setdefault("arc", {}).update(arc_data)

# After:
state = state.model_copy(update={"inventory": inv, "location": location_ref, "compendium": compendium, "arc": arc})
```

**Specific locations in `delta_builder.py`:**
- Line 221: `state["inventory"] = inv` → `state.model_copy(update={"inventory": inv})`
- Line 223-244: location_change → `state.model_copy(update={"location": ..., "scene": ..., "compendium": ...})`
- Line 246-275: conditions → `state.model_copy(update={"pc": ...})`
- Line 289: `_merge_arc_update(state.setdefault("arc", {}), ...)` → `state.model_copy(update={"arc": ...})`
- Line 293-294: `state.setdefault("pc", {})["actions"]` → mutator

**Verification:** `make typecheck` passes for `delta_builder.py`.

#### 04-6: Update `state/npcs.py` — `apply_npc_scene_management`, `touch_compendium_order`

```python
# Before:
def touch_compendium_order(state: dict[str, Any], npc_id: str):
    order: list[str] = state.setdefault("meta", {}).setdefault("compendium_touch_order", [])
    if nid in order:
        order.remove(nid)
    order.append(nid)

# After:
def touch_compendium_order(state: WorldState, npc_id: str) -> WorldState:
    order = list(state.meta.compendium_touch_order)
    if nid in order:
        order.remove(nid)
    order.append(nid)
    return state.model_copy(update={"meta": state.meta.model_copy(update={"compendium_touch_order": order})})
```

**Specific locations in `state/npcs.py`:**
- Line 27-35: `touch_compendium_order` — take `WorldState`, return `WorldState`
- Line 45-140: `apply_npc_scene_management` — take `WorldState`, return `WorldState`, access `state.compendium.npcs`, `state.location`, `state.meta.turn`

**Verification:** `make typecheck` passes for `state/npcs.py`.

#### 04-7: Update `world.py` — beat tracking

```python
# Before:
meta = state.setdefault("meta", {})
for vb in valid_beats:
    meta.setdefault("recent_beats", []).append({...})
max_beats = config.recent_beats_max
if len(meta["recent_beats"]) > max_beats:
    meta["recent_beats"] = meta["recent_beats"][-max_beats:]

# After:
for vb in valid_beats:
    state = state.add_recent_beat({"turn": turn_no, "type": vb.get("type"), "effect": vb.get("effect", "")}, max_size=config.recent_beats_max)
```

**Specific locations in `world.py`:**
- Line 198-207: recent_beats tracking → `state.add_recent_beat(..., max_size=config.recent_beats_max)`

**Verification:** `make typecheck` passes for `world.py`.

#### 04-8: Update `thread_sanitizer.py` — `_apply_sanitization`

Replace `state.setdefault()` with mutators:

```python
# Before:
state.setdefault("scene", {})["world_state"] = new_world_state
state.pop("world_state_candidates", None)
state.setdefault("arc", {}).update(...)

# After:
state = state.set_world_state(new_world_state)
state = state.model_copy(update={"world_state_candidates": []})
state = state.model_copy(update={"arc": updated_arc})
```

**Specific locations in `thread_sanitizer.py`:**
- Line 492: `state.setdefault("scene", {})["world_state"]` → `state.set_world_state(new_world_state)`
- Line 494: `state.pop("world_state_candidates", None)` → `state.model_copy(update={"world_state_candidates": []})`
- Line 500: `state.setdefault("arc", {}).update(...)` → `state.model_copy(update={"arc": ...})`

**Verification:** `make typecheck` passes for `thread_sanitizer.py`.

---

### Phase 05: Cleanup

**Goal:** Remove dead code, unused re-exports, `dict[str, Any]` casts. Final `make check`.

**Files:** `ccya/engine/turn.py`, `ccya/engine/turn_state.py`, `ccya/state/delta_builder.py`, `ccya/state/io.py`, `ccya/engine/extraction/pipeline.py`, `ccya/engine/config.py`, `ccya/models/state.py`, `ccya/prompts/context.py`

**Tasks:**

#### 05-1: Remove `dict[str, Any]` casts and model_dump() round-trips

Everywhere in the codebase where Pydantic models are immediately cast back to dicts:

```python
# Before:
state["arc"] = new_arc.model_dump()
arc["threads"] = [t.model_dump(exclude_none=True) for t in au.threads]

# After:
state = state.model_copy(update={"arc": new_arc})
# No need to dump threads — arc is already a LongTermObjective model
```

**Verification:** `make typecheck` passes. No `.model_dump()` calls remain in engine code (only in extraction output serialization).

#### 05-2: Remove unused re-exports and dead code

- Remove `state/delta.py` if not already removed (already done per I-17 investigation)
- Remove any `dict[str, Any]` type annotations that are no longer needed
- Remove `_default_state()` from `state/io.py` — replace with `WorldState()` default constructor

#### 05-3: Update `_default_state()` to `default_world_state()`

```python
# Before:
def _default_state() -> dict[str, Any]:
    return {"meta": {...}, "pc": {...}, ...}

# After:
def default_world_state() -> WorldState:
    return WorldState()  # all fields have defaults
```

**Verification:** `make typecheck` passes for `state/io.py`.

#### 05-4: Update `config.py` — remove `dict[str, Any]` from `_EventLock` if needed

No changes expected — `_EventLock` is independent of state shape.

#### 05-5: Final `make check`

Run `make check` (lint + typecheck). Fix any remaining issues.

**Verification:** `make check` passes with no errors.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Backward compat break with existing YAML | Low | `WorldState.from_dict()` applies `_default_state()` defaults, coerces enums, handles legacy `active`→`dormant` |
| Type errors in 51+ functions | Medium | Phase 03 is read-only — easiest to verify. Typecheck catches all mismatches |
| Mutation pattern confusion (immutable vs mutable) | Medium | Phase 04 introduces immutable mutators — each returns new `WorldState`. Clear pattern, easy to follow |
| Performance regression from model_copy() | Low | `model_copy()` is O(n) where n = number of fields (~15). Negligible vs LLM call latency |
| Extraction context deep copy still needed | N/A | `_build_extraction_context()` still needs `copy.deepcopy` for preview — no change |

---

## Execution Order

1. **Phase 01** — Define models (no runtime impact, safe to start)
2. **Phase 02** — Wire I/O (load/save, TurnContext type)
3. **Phase 03** — Migrate read access (51+ functions, largest phase)
4. **Phase 04** — Migrate mutation access (setdefault chains → mutators)
5. **Phase 05** — Cleanup (remove casts, dead code, final check)

Each phase is independently verifiable via `make typecheck`. Phase 03 is the largest (~50 functions across 10 files). Phase 04 introduces the immutable mutator pattern.

---

## Documentation Updates Required

After implementation:
1. **`docs/architecture/`** — Update data shapes doc to reflect `WorldState` model
2. **`docs/repomap.md`** — Update module boundaries for `models/state.py`, `state/io.py`, `engine/turn_context.py`
3. **`AGENTS.md`** — Update signposts for `WorldState` usage pattern

---

## Done When

- Every function that reads state takes `WorldState` (Phase 03 complete)
- Every function that mutates state uses typed mutators (Phase 04 complete)
- No `state.get("section")` or `state.setdefault("section")` calls remain in engine code
- `make check` passes (lint + typecheck)
- `load_state()` returns `WorldState`, `save_state()` accepts `WorldState`
- Boundary models in `prompts/context.py` accept `WorldState`
- Documentation updated (repomap, architecture docs, AGENTS.md)
