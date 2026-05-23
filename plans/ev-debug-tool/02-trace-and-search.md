# Phase 2: `trace` and `search` commands for ev.py

## Status
`open`

## Phases

3 phases: (1) state + diff commands, (2) trace + search commands, (3) mechanics improvements + stream aliases + legacy deprecation

**Dependency:** Phase 1 `_strip_flags()` is reused for `--from`/`--to` flag parsing. `load_extraction_context()` from Phase 1 is *not* used — this phase reads `extraction_context` inline for independence. Phase 1 should be complete but Phase 2 code is self-contained if `_strip_flags()` is ported.

## Issue

ev.py cannot answer "how did this field change across turns?" or "find me turns where NPC X appeared." Users must manually scan `deltas` output for every turn.

## Solution

Two new commands. `trace` walks `extraction_context` + `applied` per turn to show a single field's value across a turn range. `search` scans `applied`, `extraction_context`, ruling, and `input` for structured matches. Zero engine changes.

## Firm decisions

1. `trace` uses `extraction_context` as its primary data source for the 5 snapshot fields (npcs, inventory, conditions, location, tags). For fields not in extraction_context, it shows mutations from `applied` at turn granularity.
2. `search` operates on structured fields (*not* grep against raw event text). This avoids false positives from prompt text.
3. `search` expressions use the syntax `<field>:<value>` for exact match and `<field>~<regex>` for regex match.
4. `trace` and `search` both fall back to iterating all events when no turn range is specified. Performance is acceptable (< 100ms for 100 turns of events.jsonl).

## Non-goals

- Full state reconstruction. `trace` shows per-turn snapshots and mutations, not reconstructed state.
- AI-powered search. No LLM involvement.

## Risks, Ambiguities, and Blockers

- `trace` for NPC presence does not differentiate between "NPC was present but changed notes" and "NPC was not present." The per-turn entry either has the NPC in `present_npcs_this_turn` or doesn't.
- `search` for `thread:<id>` cannot be implemented from structured data alone — thread IDs are not stored in `applied` or `extraction_context`. The closest proxy is searching `input` regex. Mark this limitation explicitly.

## Implementation — Phase 2: `trace` + `search` commands

### Context files to load

- `scripts/debug/ev.py` (704 lines) — add new command functions + helpers. Should already be familiar from Phase 1.
- `ccya/models.py` — `StateDelta` (lines 235–293), `SceneExtractResult` (lines 296–331), `StorytellerResult` (lines 483–523) for understanding field names in `applied`.

### Detailed steps

#### Step 2.1 — `extract_field_from_event()` helper

**File:** `scripts/debug/ev.py` (new helper function)

**What:** Given an event dict and a field path (dot-separated), return the printable value of that field at that turn. The function dispatches to the right data source: first check `extraction_context` (5 snapshot fields), then `applied` (StateDelta fields like `scene_tagline`), then `changes` (computed categories like `momentum`). Fields not in any data source return `None`.

Coverage definition: a field is "tracked" if it has an entry in at least one of the three data sources (`extraction_context`, `applied`, `changes`). All other fields return `None`. The dispatch order is fixed: extraction_context → applied → changes. First match wins.

Return format per field path:

| Field path | Data source key | Return type | Example |
|---|---|---|---|
| `inventory` | `extraction_context.inventory_this_turn` | `list[dict]` — full item list (id, name, amount, notes) | `[{"id": "lockpick_set", "name": "Lockpick Set", "amount": 1}]` |
| `inventory.<id>` | same, filtered by `id` | `dict \| None` — single item or None if absent | `{"id": "lockpick_set", "amount": 1}` |
| `conditions` | `extraction_context.conditions_this_turn` | `list[dict]` — full condition list | `[{"id": "injured", "label": "Injured"}]` |
| `conditions.<id>` | same, filtered by `id` | `dict \| None` | `{"id": "injured"}` |
| `npcs` | `extraction_context.present_npcs_this_turn` | `list[str]` — list of NPC IDs *only* (for compact display) | `["matthew_ho", "crowd_thief"]` |
| `npcs.<id>` | same, find by `id` | `dict \| None` — full NPC entry (id, name, notes) or None if not present | `{"id": "matthew_ho", "name": "Matthew Ho"}` |
| `location` | `extraction_context.location_this_turn` | `str` — combined `"id (name)"` or just `"name"` if id absent | `"barrstad_outpost_junction (Barrstad Junction)"` |
| `scene.tags` | `extraction_context.scene_tags_this_turn` | `list[str]` | `["chaos", "panic"]` |
| `scene.tagline` | `applied.scene_tagline` | `str \| None` — only present when changed this turn | `"The Patrol Approaches"` |
| `pc.momentum` | `changes.momentum` → extract latest `after` value | `int \| None` — falls back to `ruling_event.momentum_after` if `changes.momentum` is empty | `-1` |

```python
def extract_field_from_event(ev: dict[str, Any], field: str) -> Any | None:
    """Extract a single field's printable value from an event.
    
    Returns None if the field is not tracked in any data source.
    Callers check this once before building the trace table.
    """
    ctx = ev.get("extraction_context") or {}
    applied = ev.get("applied") or {}
    changes = ev.get("changes") or {}
    ruling = ev.get("ruling") or {}
    # ... dispatch by field path with fixed order: ctx → applied → changes → ruling ...
```

**Why:** Single dispatch function that both `trace` and `search` can call. Centralizes the data source routing, return type normalization, and "tracked vs. untracked" definition.

**Validation:** Call on a known event with field `inventory` — must return the full inventory list. Call `npcs.trevor_riddle` — must return the NPC dict if present, None if absent. Call `pc.momentum` — must return an int (e.g., `-1`). Call `pc.stats` — must return None (not tracked).

#### Step 2.2 — `cmd_trace()` CLI command

**File:** `scripts/debug/ev.py` (new command function, new `match` arm in `main()`)

**What:** New CLI command:
```
ev.py trace <field> [--from N] [--to M] [--show-unchanged]
```

Algorithm:
1. Load events via `load_events()`.
2. Filter events to turn range [from, to] (default: all turns).
3. For each event in order, call `extract_field_from_event(ev, field)`.
4. Build a table: one row per turn, showing the value. For values unchanged since previous turn, print "(same)" unless `--show-unchanged`.
5. For collection fields (inventory, conditions, npcs), show a condensed list of IDs/names and highlight changes with arrows.

Output format (scalar field like `location`):
```
trace location --from 3 --to 7

Turn | Location
─────┼────────────────────────────────────────────
   3 | Barrstad Junction
   4 | (same)
   5 | (same)
   6 | (same)
   7 | (same)
```

Output format (collection field like `inventory`):
```
trace inventory --from 3 --to 7

Turn | Inventory
─────┼────────────────────────────────────────────
   3 | Lockpick×1, Pistol×1, Rounds×12, Stim×2, Slimdeck×1
   4 | (same)
   5 | Lockpick×1, Pistol×1, Rounds×12, Stim×2  ← Slimdeck removed
   6 | (same)
   7 | (same)
```

Field path is validated at the start: if `extract_field_from_event` returns `None` for the first event, print "Field not tracked per-turn" and exit 1.

Edge cases:
- No events in range: print "(no events in range)".
- Field value is None for some events: print "(no data)" for those rows.
- `--from` > `--to`: error.

Register in `main()`:
```python
case "trace":
    # parse field, --from, --to from remaining args
    cmd_trace(events, field, from_turn=from_turn, to_turn=to_turn)
```

**Why:** Cross-turn field viewer. Complements `diff` by showing one field across many turns.

**Validation:** `python3 scripts/debug/ev.py trace inventory` — must show inventory per turn. `python3 scripts/debug/ev.py trace location` — must show location changes. `python3 scripts/debug/ev.py trace pc.momentum` — must show momentum value per turn (e.g., `-1`, `0`, `-2`) or `(no data)` for turns without momentum changes.

#### Step 2.3 — `search_events()` helper

**File:** `scripts/debug/ev.py` (new helper function)

**What:** Given events list and a search expression dict, return matching events with match context.

```python
def search_events(events: list[dict[str, Any]], query: dict[str, str]) -> list[dict[str, Any]]:
    """Query dict: {field: value_or_pattern, field: ...}
    Supported search keys:
      - npc       exact: npc=trevor_riddle  — checks extraction_context.present_npcs_this_turn
                    for presence (the NPC is in the snapshot list) AND applied.npc_add/npc_remove/npc_update
                    for mutation events. Matches BOTH "NPC was present" and "NPC changed this turn."
                    An NPC added turn 3, present turns 3-5, removed turn 6: npc:trevor_riddle
                    matches turns 3, 4, 5, 6. Turn 4 has no applied entry but extraction_context
                    shows the NPC as present.
      - npc_add   exact: npc_add=crowd_thief — only in applied.npc_add (must be a mutation turn)
      - item      exact: item=compact_pistol — checks extraction_context.inventory_this_turn
                    (item present in snapshot) AND applied.inventory_add/inventory_remove/
                    inventory_update (item mutated this turn). Same across-turn semantics as npc.
      - condition exact: condition=injured   — checks extraction_context.conditions_this_turn
                    AND applied.pc_condition_add/pc_condition_remove. Same semantics.
      - band      exact: band=success        — exact match against ruling.band
      - rejected  boolean: rejected=true     — matches ev.get('rejected') truthiness
      - input     regex:  input~steal|pocket — regex match against ev.get('input')
    """
```

For each search key, define:
- Which event fields to check (extraction_context for presence, applied for mutations)
- Whether the match is exact, regex, or boolean
- What context line to return: for presence-only matches (NPC in snapshot, no mutation this turn), show "(present in scene)". For mutation matches, show the specific mutation (e.g., "npc_remove trevor_riddle").
- Deduplicate: don't emit two results for the same turn (presence + mutation → one line, mutation preferred for detail).

Returns list of dicts: `{turn, input_snippet, matched_value, field, turn_entry}`.

**Why:** Search across turns for specific NPCs, items, conditions, or dice results. Avoids false positives from prompt text by searching structured fields only.

**Validation:** Write a minimal test: create a synthetic event list, run search, verify matches.

#### Step 2.4 — `cmd_search()` CLI command

**File:** `scripts/debug/ev.py` (new command function, new `match` arm in `main()`)

**What:** New CLI command:
```
ev.py search <expr> [<expr> ...]
```

Expression syntax:
- `npc:trevor_riddle` — exact NPC ID match
- `npc_add:player_brother` — exact NPC addition match
- `item:compact_pistol` — exact item ID match
- `condition:injured` — exact condition ID match (may be abbreviated)
- `band:success` — exact band match
- `rejected` — turns with any rejection (boolean, no value needed)
- `input~steal|pocket` — regex match against player input

Multiple expressions AND together: `npc:trevor_riddle band:failure` finds turns where Trevor Riddle was present AND the dice result was a failure.

Output format:
```
$ ev.py search npc:trevor_riddle
turn 1: (present in scene) — "I look around the junction"
turn 2: (present in scene) — "I try to talk to him"
turn 3: npc_remove trevor_riddle — "I slip away"
```

$ ev.py search npc_add:player_brother
```
turn 6: npc_add player_brother — "I search for my brother in the chaos"
```

```
$ ev.py search band:failure
turn 3: band=partial (lockpick check, diff=hard, total=8) — "I try to jimmy the lock"
```

If no matches: print "(no matching turns)" and exit 0.

Register in `main()`:
```python
case "search":
    # parse expressions from remaining args
    cmd_search(events, expressions)
```

**Why:** Cross-turn search. Essential for finding when specific game elements changed.

**Validation:** `python3 scripts/debug/ev.py search npc:player_brother` — must show turns where that NPC appears. `python3 scripts/debug/ev.py search band:success` — must show successful rolls. `python3 scripts/debug/ev.py search npc:does_not_exist` — must print "(no matching turns)".

### Tests to write or update

No tests to write (tests temporarily removed). Manual validation against the default save.

### REPOMAP updates required

- `scripts/debug/README.md` — update command table to include `trace` and `search` once all phases are complete (handled in Phase 3). No repomap changes needed — `ev.py` is a standalone debug script, not part of the core library API.
