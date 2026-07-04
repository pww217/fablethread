# State Models — state.yaml shape, Pydantic models, field types

## state.yaml — canonical live state

```yaml
# (no schema_version field — all saves use current format)
meta:
  session_name: str            # short evocative title for this game session (3-6 words)
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat selected by Ruling from beat_candidates, consumed by same turn's Narrate (runtime-only, no TTL — single-turn commitment)
  beat_candidates: list[dict]  # 0-3 candidate beats prepared by World step (async, end-of-prev-turn), consumed and popped by Ruling
  prior_history: list[str]     # incremental history bullets (- [T{n}] text), appended per record turn (formerly per storyteller turn), capped at 20 newest
  _pack_source: str | None     # pack ID that was used to generate this state
  consecutive_low_convergence: int  # global counter across BREATHER→RISING cycles; incremented when convergence_score < threshold, reset on reaching threshold or cancel/retry; drives stall_floor computation

# Root-level keys only present when a game has been seeded
seed_meta:                     # {opening_narrative: str, actions: [str]}; set by init_save_dir()

pc:
  name: str
  tagline: str
  bio: str
  stats: {strength, dexterity, wits, charisma}: int (1-4 each, total 8-12)
  conditions: list[Condition] — id-based dedup, FIFO cap 5; TTL-based auto-expiration (engine decrements turns_remaining each turn, removes at 0); permanent = never expires
    - id: str, label: str, description: str, added_turn: int, turns_remaining: int | Literal["permanent"]
  actions: [str]               # rolling window of last 10 Storyteller actions, persisted by apply_delta
  situation: dict[str, str]    # structured situational facts (vessel, crew, debts, alliances, home)

location: {id, name, description}: str

inventory: list[InventoryItem] — credits pinned to top
  - id: str, name: str, notes: str, amount: int (≥1), aliases: [str]

 arc:                           # managed by engine/turn_state.py
    long_term_objective: str
    threads: list[ArcThread]     # unified arc.threads[] with dormant flag; dedup is id-only
    completed_threads: list[ArcThread]   # resolved/failed/abandoned threads
    resolution: str | None       # set when arc is resolved via arc_resolve
    last_thread_created_turn: int  # tracks when a thread was last created for thread_add cooldown gate
    started_turn: int | None     # turn when arc was created (for pressure score age calculation)

resolved_arcs: list[dict]     # stored at state level, TTL-pruned in prompts; each entry has long_term_objective, resolution, resolved_turn

scene:
  world_state: list[WorldStateFact]   # global tier = seed-authored; local tier = LLM-added at runtime
  turn_entered: int            # when the current scene was entered (set on location change, used by _compute_ages())
  location_entered_turn: int   # when location was last changed

compendium.npcs: dict[id] → {name, title, bio, presence: str | "present"|"nearby"|"known"|"departed"|"archived", position: str | None, motivation: str | None (UI-visible), fear: str | None (hidden from UI), leverage: str | None (hidden from UI), personality: str | None (archetype id; write-once, immutable), first_seen_turn: int | None, last_presence_turn: int | None, last_seen_location: str | None, departed_reason: str | None, departed_turn: int | None, party: bool | None (companion flag — exempts from location-change auto-demotion, auto-cleared on departed)}

world.factions: [str], world.locations: list[KeyLocation]
```

## Pydantic models

### Core result types (ccya/models/)

- **IntentEnvelope**: `intent`, `intent_verb`, `target`, `check` (RulesCheck), `impossible`, `reason`, `scene_motion: Literal["hold", "advance", "transition"]`
- **RulesOutcome**: `rolled`, `skill`, `difficulty`, `stat_value`, `stat_mod`, `diff_mod`, `dice`, `raw_total`, `final_total`, `band`, `directive`, `intent`, `intent_verb`, `impossible`, `reason`
- **SceneExtractResult**: `compendium_npc_update`, `candidate_npcs: list[dict]` (per-NPC beat candidates: [{id, type, effect}])
- **StateExtractResult**: `inventory_add/remove/update`, `pc_condition_add/remove`, `location_change`, `location_description`
- **StorytellerResult**: `thread_update` (list[ThreadUpdate]), `goal_update` (dict | None, applied directly to arc dict), `arc_resolve` (ArcResolution | None), `thread_resolve` (with outcome sentence + world_state_candidate), `thread_add`, `actions`, `outcome_summary`. **The `gm_beat` field has been removed** — beat generation moved to Step 2d (World), beat selection to Step 0 (Ruling). The Pydantic class name is preserved (`StorytellerResult`); only the field is gone.
- **SeedEnvelope**: `seed_state: SeedState`, `opening_narrative`, `actions`, `arc: LongTermObjective | None` (unified `threads[]` with `major_updates: list[ProgressEntry]`, `completed_threads[]`)

### State models (ccya/models/state.py)

- **ArcThread**: `id`, `summary`, `dormant`, `type`, `urgency`, `major_updates: list[ProgressEntry]`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`, `urgency_set_turn`
- **LongTermObjective**: `long_term_objective`, `threads: list[ArcThread]`, `completed_threads: list[ArcThread]`, `resolution`, `last_thread_created_turn`, `started_turn`
- **Condition**: `id`, `label`, `description`, `added_turn`, `turns_remaining: int | Literal["permanent"]` (0 = sentinel, replaced by engine default TTL in apply_delta)
- **InventoryItem**: `id`, `name`, `notes`, `amount`, `aliases: [str]`
- **NpcPresence**: enum — `present`, `nearby`, `known`, `departed`, `archived`
- **ProgressEntry**: `kind: Literal["advancement", "setback"]`, `text`
- **ThreadResolution**: `id`, `resolution_state: Literal["resolved", "failed", "abandoned"]`, `outcome: str`, `world_state_candidate: str | None`
- **ThreadUpdate**: `id`, `dormant`, `urgency`, `type`, `major_updates`, `major_update_signal`
- **ArcResolution**: `resolution`, `long_term_objective`
- **WorldStateFact**: `id: str`, `text: str`, `tier: Literal["global", "local"] = "global"`, `permanent: bool = False`, `valence: Literal["threat", "complication", "neutral", "boon"] | None = None`, `expires_turn: int | None = None`
- **KeyLocation**: `id: str`, `name: str`, `description: str = ""`, `status: str = "active"`, `tags: list[str] = []`
- **SanitizedWorldStateFact**: `id: str`, `text: str`, `tier: Literal["global", "local"] = "global"`, `permanent: bool = False`, `valence: Literal["threat", "complication", "neutral", "boon"] | None = None`, `expires_turn: int | None = None`
- **WorldState** (root model): typed Pydantic model wrapping the full `state.yaml` shape. Fields: `meta: Meta`, `pc: PC`, `scene: Scene`, `location: KeyLocation`, `inventory: list[InventoryItem]`, `arc: LongTermObjective`, `compendium: Compendium`, `resolved_arcs: list[dict]`, `world_state_candidates: list[dict]`, `world: World`, `seed_meta: dict | None`. All functions that read or mutate state take `WorldState` (not `dict[str, Any]`). Immutable — mutation goes through typed mutator methods that return a new `WorldState`.

### Extraction models (ccya/models/extraction.py)

- **CompendiumNpcUpdate**: NPC identity changes (presence, notes, bio upserts, personality on creation, position)
- **StateDelta**: Merges scene, state, and storyteller extraction results; contains `location_change`, `location_description`, `compendium_npc_update`, `arc_update` (LongTermObjective), `inventory_add/remove/update`, `pc_condition_add/remove`. Note: `gm_beat` is NOT in StateDelta — written directly to `state.meta.pending_gm_beat`. Thread operations (`thread_update`, `thread_resolve`, `thread_add`, `arc_resolve`) are in `StorytellerResult`, not StateDelta.
- **SceneExtractResult**: See above
- **StateExtractResult**: See above
- **GMBeat**: See above
- **StorytellerResult**: See above

### Rules models (ccya/models/rules.py)

- **RulesCheck**: `required: bool`, `skill: SkillName`, `difficulty: Difficulty`
- **IntentEnvelope**: See above
- **RulesOutcome**: See above

### Config models (ccya/models/config.py)

- **TurnResult** dataclass: `turn`, `trace_id`, `narrative`, `state_delta`, `applied`, `rejected`, `actions`, `diff`, `changes`, `metrics`, `errors`, `ruling`, `outcome_summary`, `outcome_hint`, `scene_phase`, `summary`, `ts`. The `gm_beat` field has been removed; beats flow through `state.meta.pending_gm_beat` and `state.meta.beat_candidates`.
- **SkillName**: 4 skills (strength, dexterity, wits, charisma)
- **Difficulty**: 5 difficulty levels with modifiers in DIFFICULTY_MOD
- **Band**: crit_fail, fail, setback, partial, success, crit_success (1d12 natural: 1=crit_fail, 12=crit_success)
- **EngineConfig**: thread_max_active, nearby_decay_ttl, departed_archive_ttl, climax_turn_limit, breather_max_turns, convergence_alpha, convergence_enter_threshold, convergence_exit_threshold, roll_starvation_threshold, threat_density_threshold, stall_floor_max, extension_max, thread_creation_cooldown, thread_urgency_max_age, sanitize_every, arc_memory_ttl, thread_memory_ttl, debug_mode, plus sampling params per stage (ruling_temperature, narrate_temperature, etc.)

### Compactor models (ccya/models/compactor.py) — dormant

- **CompactorSanitizationResult**: `npc_merge`, `inventory_remove`, `pressure_remove`, `condition_remove` — coerced by `_coerce_sanitization_actions` (field_validator): converts bare strings to `{id: str, confidence: "high", reason: None}` dicts. Currently unused.

## Non-obvious model behavior

### GMBeat
- Repurposed as the validation schema for World candidates and Ruling's `selected_beat`. Fields: `type` (Literal — silently coerced to `None` if not in valid set), `effect` (str), `npcs` (list[str] — NPC IDs involved in this beat).
- **`npc_id`, `driver`, `beat_expires_turn` fields removed** — beats are single-turn commitments. Ruling's per-turn "always replace or pop" rule keeps state hygienic. No orphan can survive a turn boundary.
- The old `StorytellerResult._nullify_invalid_gm_beat` validator is gone; its logic (drop beat if `type` is None/falsy) now lives inline in `ruling.py:_ruling_phase`.

### WorldStateFact
- `tier: Literal["global", "local"]` — global facts are immutable world constraints (seed-authored or confirmed by sanitizer); local facts are area-specific and may be temporary
- `permanent: bool` — if true, the fact is never expired or removed; if false, it may be removed by TTL or sanitizer
- `valence: Literal["threat", "complication", "neutral", "boon"] | None` — indicates the fact's impact on the PC's situation
- `expires_turn: int | None` — if set, the fact is automatically removed at this turn number (TTL expiry pass in turn.py)
- Two-step promotion: storyteller proposes via `ThreadResolution.world_state_candidate`; thread sanitizer evaluates and confirms/rejects/modifies via `world_state_actions`

### ThreadResolution
- `outcome: str` — one past-tense sentence written at resolution time; persisted on completed ArcThread by `_apply_thread_resolutions()` alongside `resolution_state`

### StateDelta actions
- `actions: list[str]`, max_length=10 — merged from StorytellerResult.actions, persisted to `state.pc.actions` as rolling window by `apply_delta()`

### Condition TTL system
- `turns_remaining: int | Literal["permanent"]` on `Condition` and `ConditionAdd`
- `"permanent"` = never expires (explicit string, not `null`/`None`)
- Engine assigns default TTL (default 10, from `config.condition_default_ttl`) when LLM omits it (sentinel value `0` replaced in `apply_delta()`)
- TTL decrement pass in `_expire_conditions()` in `turn_state.py`: runs after delta application, decrements by 1 each turn, removes when reaching 0
- Duration bands: sensory (1-2), minor (3-4), significant (5-6), major (7+), permanent
- `condition_expired` events appended to `events.jsonl` when conditions expire

### Condition change reason
- `condition_change_reason` required when any condition change is present (Pydantic-enforced, same pattern as `inventory_change_reason`)
- Reason persisted to `state.meta.last_condition_change_reason` for debugging

### CompendiumEntry
- Has explicit `motivation`/`fear`/`leverage`/`bond`/`personality` optional string fields alongside existing `name`/`title`/`bio`/`presence`/`position`; runtime code uses `tie` (CompendiumNpcUpdate.tie), seed-time model uses `bond` (CompendiumEntry.bond)
- **bond→tie rename:** Runtime code (`CompendiumNpcUpdate.tie` in `extraction.py`) uses `tie`; seed-time model (`CompendiumEntry.bond` in `pack.py`) still uses `bond`. The scenario model field is `npc_bonds`. Most templates and prompts use `tie`.
- Seed prompt schema includes `personality` as `archetype_id` (required for named NPCs) alongside `motivation`/`fear`/`leverage`/`bond` as optional strings
- Seed prompt has tiered field requirements (named NPCs get `personality` + 2+ fields, unnamed NPCs get `bio` only)

## Typed mutators on WorldState

All state mutation goes through immutable typed methods on `WorldState`. Each returns a new `WorldState` instance (Pydantic `model_copy` under the hood). Never use `state["key"] = value` or `state.setdefault("key", value)` in engine code.

| Mutator | Purpose |
|---|---|
| `set_turn(n)` | Increment turn counter (engine/turn.py) |
| `add_recent_beat(beat, max_size=5)` | Append to recent_beats with FIFO cap |
| `add_recent_roll(roll, max_size=5)` | Append to recent_rolls with FIFO cap |
| `add_prior_history_bullet(text)` | Append history bullet (capped at 20) |
| `set_pending_beat(beat)` | Set/consume GM beat for current turn |
| `set_beat_candidates(candidates)` | Update beat candidate pool |
| `set_last_inventory_change_reason(reason)` | Debug aid for last inventory change |
| `set_last_condition_change_reason(reason)` | Debug aid for last condition change |
| `set_last_rules_outcome(outcome)` | Debug aid for last rules outcome |
| `set_last_thread_creation_turn(n)` | Track thread creation cooldown |
| `set_last_arc_resolve_turn(n)` | Track arc resolution |
| `set_smoothed_convergence(value)` | EMA-smoothed convergence score |
| `set_compendium_touch_order(order)` | LRU order for NPC selection |
| `set_world_state(facts)` | Atomic world_state swap (replaces entire array) |
| `expire_world_state_facts(current_turn)` | Remove facts whose `expires_turn` has passed |
| `set_scene_phase(phase)` | Current pacing phase |
| `add_npc(nid, entry)` | Insert new NPC into compendium |
| `update_npc(nid, **kwargs)` | Partial update of existing NPC |
| `add_condition(cond)` | Add condition to PC (id-dedup) |
| `remove_condition(cond_id)` | Remove condition from PC |
| `expire_conditions(turn_no)` | TTL-based condition expiration |

## I/O

- `ccya/state/io.py` — `load_state(save_dir) -> WorldState`, `save_state(save_dir, state)`, `init_save_dir(save_dir, seed)`, `default_world_state() -> WorldState` (replaces legacy `_default_state()` dict factory). YAML serialization coerces enums to string values via `_coerce_enums()`.
