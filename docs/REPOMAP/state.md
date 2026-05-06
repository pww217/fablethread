# state/ — state persistence

## Package structure

| File | Responsibility |
|---|---|
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | `load_state`, `save_state`, `init_save_dir`, `_migrate_state` |
| `ccya/state/delta.py` | `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX` |
| `ccya/state/inventory.py` | `normalize_inventory_id`, resolve/fuzzy match helpers |
| `ccya/state/npcs.py` | `build_npc_alias_map`, `touch_compendium_order` |
| `ccya/state/chronicle.py` | `append_event`, `append_chronicle`, `load_chronicle_tail`, `load_recent_events`, `load_recent_chronicle_turns` |
| `ccya/state/momentum.py` | `apply_momentum` |

## Public APIs

- **`load_state(save_dir)`** → `dict` — loads YAML, runs `_migrate_state()`.
- **`save_state(save_dir, state)`** — atomic write (tmp + rename).
- **`apply_delta(state, delta, recent_events_max=20)`** → `dict` — mutates state in-place (deep copy), returns updated state. Handles inventory merge/remove, location change, quest upsert, condition add/remove (id-based dedup, FIFO cap 5), recent events (remove→update→add, FIFO cap), scene tags, present NPCs (hydrate from compendium), compendium updates, recently_left tracking.
- **`apply_momentum(state, band)`** — updates `pc.momentum` deterministically from a rules band, clamped to [-3, +3].
- **`append_event(save_dir, event)`** — appends to events.jsonl.
- **`append_chronicle(save_dir, text)`** — appends to chronicle.md.
- **`init_save_dir(save_dir, seed)`** — writes seed state, truncates chronicle/events.
- **`load_recent_chronicle_turns(save_dir, n)`** → `list[dict]` — parses chronicle.md into turn blocks.
- **`load_chronicle_tail(save_dir, max_tokens, skip_last_n_turns)`** → `str` — word-truncated tail.
- **`load_recent_events(save_dir, n)`** → `list[dict]` — last N events from JSONL.
- **`normalize_inventory_id(raw)`** → `str` — canonical id for merge/remove lookup.
- **`resolve_inventory_remove_target(inventory, raw_id)`** → `str | None` — resolves id or name to stored id.
- **`touch_compendium_order(state, npc_id)`** — LRU ordering for compendium NPC selection.
- Constants: `PC_CONDITIONS_MAX = 5`.

## State shape — `state.yaml`

```yaml
meta:
  game_name: str
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat from progress extractor, consumed by next turn's narrator
  last_compacted_turn: int     # compaction tracking (0 = never compacted)

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
  conditions:                  # list[Condition] — id-based dedup, FIFO cap 5
    - id: str
      label: str
      description: str
      added_turn: int
  momentum: int                # [-3, +3], engine-computed from roll bands

location:
  id: str
  name: str
  description: str

inventory:                     # list[InventoryItem] — credits pinned to top
  - id: str
    name: str
    notes: str
    amount: int (≥1)

quests:                        # list[Quest] — upsert by id
  - id: str
    title: str
    status: active|completed|failed|abandoned
    objectives:
      - description: str
        done: bool
        failed: bool

scene:
  tags: [str]
  tagline: str
  present_npcs: [NpcRef]       # id, name, title, notes, bio
  world_state: [str]           # immutable after seed
  recent_events: [str]         # FIFO cap (configurable, default 20)
  recently_left: [dict]        # NPCs that left this turn
  recently_left_turns: int     # decay counter
  turn_entered: int            # turn number when scene was entered (anti-stall tracking)

compendium:
  npcs:                        # dict[id] → {name, title, bio} — durable NPC identity
    {id}:
      name: str
      title: str
      bio: str
```
