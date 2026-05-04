# state.py — state persistence

## Public APIs

- **`load_state(save_dir)`** → `dict` — loads YAML, runs `_migrate_state()`.
- **`save_state(save_dir, state)`** — atomic write (tmp + rename).
- **`apply_delta(state, delta, recent_events_max=15)`** → `dict` — mutates state in-place (deep copy), returns updated state. Handles inventory merge/remove, location change, quest upsert, condition add/remove (id-based dedup, FIFO cap 5), recent events (remove→update→add, FIFO cap), scene tags, present NPCs (hydrate from compendium), compendium updates, recently_left tracking.
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
  turn: int                    # source of truth — incremented only in engine.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection

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
  recent_events: [str]         # FIFO cap (configurable, default 15)
  recently_left: [dict]        # NPCs that left this turn
  recently_left_turns: int     # decay counter

compendium:
  npcs:                        # dict[id] → {name, title, bio} — durable NPC identity
    {id}:
      name: str
      title: str
      bio: str
```
