# state/ — state persistence

## Package structure

| File | Responsibility |
|---|---|
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | `load_state`, `save_state`, `init_save_dir`, `_migrate_state`, `_migrate_recent_events`, `_default_state` |
| `ccya/state/delta.py` | `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX`, `DEFAULT_CONDITION_TTL`, `_item_to_dict` |
| `ccya/state/inventory.py` | `normalize_inventory_id`, `resolve_inventory_canonical_id`, `resolve_inventory_remove_target`, `_fuzzy_match_inventory` |
| `ccya/state/npcs.py` | `build_npc_alias_map`, `touch_compendium_order` |
| `ccya/state/chronicle.py` | `append_event`, `append_chronicle`, `load_chronicle_tail`, `load_recent_events`, `load_recent_chronicle_turns`, `remove_last_event`, `remove_last_chronicle_turn` |
| `ccya/state/momentum.py` | `MOMENTUM_MIN`, `MOMENTUM_MAX`, `apply_momentum` |

## Public APIs

- **`load_state(save_dir)`** → `dict` — loads YAML, runs `_migrate_state()`.
- **`save_state(save_dir, state)`** — atomic write (tmp + rename).
- **`apply_delta(state, delta, recent_events_max=20)`** → `tuple[dict, bool]` — returns (deep-copied state, recent_events_evicted bool). Handles inventory merge/remove/update (duplicate add merges amount, zero-amount removal removes item), location change, condition add/remove (id-based dedup, FIFO cap 5, default TTL of 10 turns when `turns_remaining` is None), recent events (object form: id/text/turn, remove→update→add, FIFO cap), scene tags (combat started/ended turn tracking), scene tagline, scene_pressure (add/update/remove by ID), present NPCs (delta-based: add/remove/update with alias resolution, compendium hydration, NPC_SCENE_CAP=8; absence does not cause removal), recently_left tracking (populated when NPCs are removed, decay counter defaults to 2 turns), compendium NPC updates (with alias routing), arc thread signals (active/latent/completed thread management, hidden truth discovery).
- **`apply_momentum(state, band)`** — updates `pc.momentum` deterministically from a rules band, clamped to [-3, +3].
- **`append_event(save_dir, event)`** — appends to events.jsonl.
- **`append_chronicle(save_dir, text)`** — appends to chronicle.md.
- **`init_save_dir(save_dir, seed)`** — writes seed state, truncates chronicle/events.
- **`load_recent_chronicle_turns(save_dir, n, *, min_turn_exclusive=0)`** → `list[dict]` — parses chronicle.md into turn blocks, excludes turns < min_turn_exclusive.
- **`load_chronicle_tail(save_dir, max_tokens, skip_last_n_turns)`** → `str` — word-truncated tail.
- **`load_recent_events(save_dir, n)`** → `list[dict]` — last N events from JSONL.
- **`normalize_inventory_id(raw)`** → `str` — canonical id for merge/remove lookup.
- **`resolve_inventory_remove_target(inventory, raw_id)`** → `str | None` — resolves id or name to stored id.
- **`resolve_inventory_canonical_id(inventory, raw_id)`** → `str | None` — resolves id or alias to stored id (name matching not attempted).
- **`reconcile_delta(state, delta)`** → `list[str]` — validates delta against state, returns warning strings, mutates delta in place.
- **`remove_last_event(save_dir)`** → `bool` — removes last line from events.jsonl.
- **`remove_last_chronicle_turn(save_dir)`** → `bool` — removes last turn section from chronicle.md.
- **`touch_compendium_order(state, npc_id)`** — LRU ordering for compendium NPC selection.
- Constants: `PC_CONDITIONS_MAX = 5`, `MOMENTUM_MIN = -3`, `MOMENTUM_MAX = 3`.

## State shape — `state.yaml`

```yaml
meta:
  game_name: str
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat from scene extractor, consumed by next turn's narrator (runtime-only, not in default state)
  last_compacted_turn: int     # compaction tracking (0 = never compacted)
  prior_history: list[str]     # canonical append-only compacted history (bullet format: - [T{n}] ...)

pc:
  name: str
  tagline: str
  bio: str
  stats:
    strength: int              # 1-4 each, total 12-16
    dexterity: int
    wits: int
    lore: int
    charisma: int
    resolve: int
  conditions:                  # list[Condition] — id-based dedup, FIFO cap 5; TTL via turns_remaining (default 10 turns when None)
    - id: str
      label: str
      description: str
      added_turn: int
      turns_remaining: int | None  # None = permanent (not decremented); int = decremented each turn, removed at 0
  momentum: int                # [-3, +3], engine-computed from roll bands
  allegiance: str | None

location:
  id: str
  name: str
  description: str

inventory:                     # list[InventoryItem] — credits pinned to top
  - id: str
    name: str
    notes: str
    amount: int (≥1)

arc:                           # Campaign arc state — managed by engine/arc.py
  phase: str                   # setup|pursuit|reversal|crisis|resolution
  visible_goal: str
  thematic_question: str
  phase: ArcPhase              # setup | pursuit | reversal | crisis | resolution
  hidden_truths: [str]         # designer-only structural spine, never shown to player
  discovered_truths: [str]     # truths the player has learned through play (starts empty)
  active_threads: [Thread]     # {id, summary, urgency, progress, state}
  latent_threads: [Thread]     # {id, tags, ...} — hidden from player
  completed_threads: [Thread]  # {id, summary, ...}
  arc_engagement: int          # [-3, +3]
  pc_drive: str                # PC's personal motivation for being in this situation

scene:
  tags: [str]
  tagline: str
  present_npcs: [NpcRef]       # id, name, title, notes, bio — sticky: absence does not cause removal; only explicit npc_remove ops remove
  world_state: [str]           # immutable after seed
  recent_events: [Event]       # object form: {id, text, turn} — FIFO cap (configurable, default 20)
  recently_left: [dict]        # NPCs that left this turn (id, name, title) — populated when NPCs are removed via npc_remove
  recently_left_turns: int     # decay counter (defaults to 2 turns when NPCs are removed)
  turn_entered: int            # turn number when scene was entered (anti-stall tracking)
  location_entered_turn: int   # turn number when location was last changed
  scene_pressure: [Pressure]   # {id, text, urgency, turn_added, max_turns}

compendium:
  npcs:                        # dict[id] → {name, title, bio, aliases, allegiance} — durable NPC identity
    {id}:
      name: str
      title: str
      bio: str
      aliases: [str]
      allegiance: str | None

world:
  factions: [str]
  locations: [str]
```
