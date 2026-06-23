# State Models — state.yaml shape, Pydantic models, field types

## state.yaml — canonical live state

```yaml
schema_version: int  # CURRENT_SCHEMA_VERSION = 1 in state/io.py; migration from v0 handled by _migrate_v0_to_v1()
meta:
  session_name: str            # short evocative title for this game session (3-6 words)
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat from scene extractor, consumed by next turn's narrator (runtime-only)
  prior_history: list[str]     # incremental history bullets (- [T{n}] text), appended per storyteller turn, capped at 20 newest
  _seed_type: str | None       # "static" or "dynamic" — set by seed application, read by turn viewer
  _pack_source: str | None     # pack ID that was used to generate this state

# Root-level keys only present when a game has been seeded (not in default empty state)
__seed_meta__:                 # {opening_narrative: str, actions: [str]} — dynamic packs only; set by _apply_seed_to_save_dir()

pc:
  name: str
  tagline: str
  bio: str
  stats: {strength, dexterity, wits, charisma}: int (1-4 each, total 8-12)
  conditions: list[Condition] — id-based dedup, FIFO cap 5; conditions persist until explicitly removed by extractor
    - id: str, label: str, description: str, added_turn: int
  actions: [str]               # rolling window of last 10 Storyteller actions, persisted by apply_delta

location: {id, name, description}: str

inventory: list[InventoryItem] — credits pinned to top
  - id: str, name: str, notes: str, amount: int (≥1), aliases: [str]

 arc:                           # managed by engine/turn_state.py
   visible_goal: str
   goal_context: str            # 2–3 sentences explaining why visible_goal matters (UI-only; not rendered in prompts)
   threads: list[ArcThread]     # unified arc.threads[] with dormant flag; dedup is id-only
   completed_threads: list[ArcThread]   # resolved/failed/abandoned threads
   resolution: str | None       # set when arc is resolved via arc_resolve
   last_thread_created_turn: int  # tracks when a thread was last created for thread_add cooldown gate

resolved_arcs: list[dict]     # stored at state level, TTL-pruned in prompts; each entry has visible_goal, resolution, goal_context, resolved_turn

scene:
  world_state: list[WorldStateFact]   # permanent tier = seed-authored; persistent tier = LLM-added at runtime
  turn_entered: int            # when the current scene was entered (set on location change, used by _compute_ages())
  location_entered_turn: int   # when location was last changed

compendium.npcs: dict[id] → {name, title, bio, aliases: [str], presence: str | "present"|"nearby"|"known"|"departed"|"archived", position: str | None, motivation: str | None (UI-visible), fear: str | None (hidden from UI), leverage: str | None (hidden from UI), personality: str | None (archetype id; write-once, immutable), first_seen_turn: int | None, last_presence_turn: int | None, last_seen_location: str | None, departed_reason: str | None, departed_turn: int | None, party: bool | None (companion flag — exempts from location-change auto-demotion, auto-cleared on departed)}

world.factions: [str], world.locations: [str]
```

## Pydantic models

### Core result types (ccya/models/)

- **IntentEnvelope**: `intent`, `intent_verb`, `target`, `check` (RulesCheck), `impossible`, `reason`, `scene_motion: Literal["hold", "advance", "transition"]`
- **RulesOutcome**: `rolled`, `skill`, `difficulty`, `stat_value`, `stat_mod`, `diff_mod`, `dice`, `raw_total`, `final_total`, `band`, `directive`, `intent`, `intent_verb`, `impossible`, `reason`
- **SceneExtractResult**: `compendium_npc_update`, `candidate_npcs: list[dict]` (per-NPC beat candidates: [{id, type, effect}])
- **StateExtractResult**: `inventory_add/remove/update`, `pc_condition_add/remove`, `location_change`, `location_description`
- **StorytellerResult**: `thread_update` (list[ThreadUpdate]), `goal_update` (str | None, applied directly to arc dict), `arc_resolve` (ArcResolution | None), `thread_resolve` (with outcome sentence + promote_to_world_state flag), `thread_add`, `gm_beat`, `actions`, `outcome_summary`, `chapter_end: bool`
- **SeedEnvelope**: `seed_state: SeedState`, `opening_narrative`, `actions`, `arc: CampaignArc | None` (includes `goal_context` — UI-only, not rendered in prompts; unified `threads[]` with `progress: list[ProgressEntry]`, `completed_threads[]`)

### State models (ccya/models/state.py)

- **ArcThread**: `id`, `summary`, `dormant`, `type`, `urgency`, `progress: list[ProgressEntry]`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`, `urgency_set_turn`
- **CampaignArc**: `visible_goal`, `goal_context`, `threads: list[ArcThread]`, `completed_threads: list[ArcThread]`, `resolution`, `last_thread_created_turn`
- **Condition**: `id`, `label`, `description`, `added_turn`
- **InventoryItem**: `id`, `name`, `notes`, `amount`, `aliases: [str]`
- **NpcPresence**: `name`, `title`, `bio`, `aliases: [str]`, `presence`, `position`, `motivation`, `fear`, `leverage`, `personality`, `first_seen_turn`, `last_presence_turn`, `last_seen_location`, `departed_reason`, `departed_turn` — note: `party` is NOT a field on this enum (it's a compendium entry field, not a presence value)
- **ProgressEntry**: `kind: Literal["advancement", "setback", "shift"]`, `text`
- **ThreadResolution**: `id`, `resolution_state: Literal["resolved", "failed", "abandoned"]`, `outcome: str`
- **ThreadUpdate**: `id`, `dormant`, `urgency`, `type`, `summary`, `progress`, `progress_kind`
- **ArcResolution**: `resolution`, `visible_goal`, `goal_context`, `drop_threads: list[str]`, `new_threads: list[ArcThread]`
- **WorldStateFact**: `id: str`, `text: str`, `tier: Literal["permanent", "persistent"] = "persistent"`

### Extraction models (ccya/models/extraction.py)

- **CompendiumNpcUpdate**: NPC identity changes (presence, notes, bio upserts, personality on creation, position, party companion flag)
- **StateDelta**: Merges scene, state, and storyteller extraction results; contains `location_change`, `location_description`, `compendium_npc_update`, `arc_update` (CampaignArc), `inventory_add/remove/update`, `pc_condition_add/remove`. Note: `gm_beat` is NOT in StateDelta — written directly to `state.meta.pending_gm_beat`. Thread operations (`thread_update`, `thread_resolve`, `thread_add`, `arc_resolve`) are in `StorytellerResult`, not StateDelta.
- **SceneExtractResult**: See above
- **StateExtractResult**: See above
- **GMBeat**: See above
- **StorytellerResult**: See above

### Rules models (ccya/models/rules.py)

- **RulesCheck**: `required: bool`, `skill: SkillName`, `difficulty: Difficulty`
- **IntentEnvelope**: See above
- **RulesOutcome**: See above

### Config models (ccya/models/config.py)

- **TurnResult** dataclass: `turn`, `trace_id`, `narrative`, `state_delta`, `applied`, `rejected`, `actions`, `diff`, `changes`, `metrics`, `errors`, `ruling`, `outcome_summary`, `gm_beat`, `outcome_hint`, `scene_phase`, `summary`, `ts`
- **SkillName**: 4 skills (strength, dexterity, wits, charisma)
- **Difficulty**: 5 difficulty levels with modifiers in DIFFICULTY_MOD
- **Band**: crit_fail, fail, setback, partial, success, crit_success (1d12 natural: 1=crit_fail, 12=crit_success)
- **EngineConfig**: thread_max_active, nearby_decay_ttl, departed_archive_ttl, climax_turn_limit, breather_max_turns, convergence_threshold, thread_completion_threshold, thread_creation_cooldown, thread_urgency_max_age, sanitize_every, arc_memory_ttl, thread_memory_ttl, debug_mode, plus sampling params per stage (ruling_temperature, narrate_temperature, etc.)

### Compactor models (ccya/models/compactor.py) — dormant

- **CompactorSanitizationResult**: `npc_merge`, `inventory_remove`, `pressure_remove`, `condition_remove` — coerced by `_coerce_sanitization_actions` (field_validator): converts bare strings to `{id: str, confidence: "high", reason: None}` dicts. Currently unused.

## Non-obvious model behavior

### GMBeat
- Only `type` validated by `StorytellerResult._nullify_invalid_gm_beat`: beat nullified if `type` is None/falsy
- `beat_expires_turn`: turn number at which pending beat expires (set to `turn_no + 2` in turn.py)

### WorldStateFact
- `tier: Literal["permanent", "persistent"]` — permanent facts are seed-authored and never written or removed by the LLM; persistent facts are runtime-added durable environmental changes promoted from thread/arc resolution outcomes

### ThreadResolution
- `outcome: str` — one past-tense sentence written at resolution time; persisted on completed ArcThread by `_apply_thread_resolutions()` alongside `resolution_state`

### Progress migration
- `ArcThread.progress` has migrated through two versions:
  - v1: `str` — single progress string
  - v2: `list[str]` — append-only list of progress strings
  - v3 (current): `list[ProgressEntry]` — structured entries with `kind` + `text`
- A Pydantic `field_validator("progress", mode="wrap")` on `ArcThread` handles all legacy shapes: bare strings wrapped in `[{"text": v, "kind": "advancement"}]`; string lists converted to `[{"text": s, "kind": "advancement"} for s in list]`

### StateDelta actions
- `actions: list[str]`, max_length=10 — merged from StorytellerResult.actions, persisted to `state["pc"]["actions"]` as rolling window by `apply_delta()`

### Condition change reason
- `condition_change_reason` required when any condition change is present (Pydantic-enforced, same pattern as `inventory_change_reason`)
- Reason persisted to `state.meta.last_condition_change_reason` for debugging

### CompendiumEntry
- Has explicit `motivation`/`fear`/`leverage`/`bond`/`personality` optional string fields alongside existing `name`/`title`/`bio`/`aliases`/`presence`/`position`
- Seed prompt schema includes `personality` as `archetype_id` (required for named NPCs) alongside `motivation`/`fear`/`leverage`/`bond` as optional strings
- Seed prompt has tiered field requirements (named NPCs get `personality` + 2+ fields, unnamed NPCs get `bio` only)
