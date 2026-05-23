# ev.py Debug Tool — Design

## Purpose

Design authority for extending `scripts/debug/ev.py` with game state inspection and cross-turn analysis. Zero engine changes. All data sources exist in the save directory today.

## Current State — What Exists

### ev.py commands

| Command | Shows |
|---|---|
| `summary` | One-line per turn: streams active, tokens, ruling intent, delta count |
| `timing` | Token counts + latency per stream per turn |
| `turn` | Full system + user + output for all 5 streams |
| `props` | System + user + output for one stream |
| `compact` | User prompt + output (no system) for one stream |
| `prompt` | Single field (system/user/output) for one stream |
| `outputs` | JSON outputs from all 5 streams |
| `deltas` | State mutations + rejections via `_build_state_diff()` |
| `mechanics` | Rules intent, GM beat, campaign arc, state deltas, connectors, summary |
| `connectors` | Inter-stream data computed from stream topology |

### Existing data sources in `saves/default/`

**events.jsonl** — per turn event with keys:
- `extraction_context` — snapshot of `present_npcs`, `location`, `scene_tags`, `inventory`, `conditions` at extraction time (after scene+state extraction, before storyteller)
- `applied` — full `StateDelta.model_dump()` including scene, state, and storyteller streams. Covers: npc_add/remove/update, compendium_npc_update, inventory_add/remove/update, pc_condition_add/remove, location_change/description, scene_tags/tagline, recent_events_add/remove/update
- `changes` — computed pre/post diff from `summarize_changes()` covering: inventory (add/remove/rename/amount), player (conditions, stats, location), facts (recent_events), momentum
- `ruling` — intent and roll outcome
- `narrate_prompt` — system, user, and output (the prose the player received)
- `pacing_context` — directive, beat_hint, beat_locked, gate

**state.yaml** — authoritative current state dict. All fields: meta, pc (name, stats, drive, momentum, conditions, etc.), inventory, location, scene (tags, tagline, present_npcs, recent_events, recently_left, etc.), arc (visible_goal, thematic_question, threads, completed_threads, hidden/discovered_truths, etc.), compendium (npcs with bios, motivations, etc.), world_state.

**chronicle.md** — prose narrative history.

### Data coverage gaps

| Field | state.yaml | extraction_context | applied | changes |
|---|---|---|---|---|
| pc.name | ✅ | ❌ | ❌ | ❌ |
| pc.stats | ✅ | ❌ | ❌ | ❌ |
| pc.conditions | ✅ | ✅ (before storyteller) | ✅ (add/remove) | ✅ |
| pc.momentum | ✅ | ❌ | ❌ | ✅ |
| inventory | ✅ | ✅ (before storyteller) | ✅ (add/remove/update) | ✅ (add/remove/rename/amount) |
| location | ✅ | ✅ (before storyteller) | ✅ (change/description) | ✅ (change) |
| scene.tags | ✅ | ✅ (before storyteller) | ✅ | ❌ |
| scene.tagline | ✅ | ❌ | ✅ | ❌ |
| scene.present_npcs | ✅ | ✅ | ✅ (add/remove/update) | ❌ |
| scene.recent_events | ✅ | ❌ | ✅ (add/remove/update) | ✅ |
| compendium.npcs | ✅ | ❌ | ✅ (update only) | ❌ |
| arc.threads | ✅ | ❌ | ❌ | ❌ |
| arc.visible_goal | ✅ | ❌ | ❌ | ❌ |
| meta.pending_gm_beat | ✅ | ❌ | ❌ | ❌ |

Column notes:
- `applied` = the structured StateDelta LLMs intended to emit. Some fields rejected by validation may not reach state.
- `changes` = computed from `state_pre_apply` vs final `state`, so it captures engine-side mutations (condition aging, arc signals, momentum). Missing npcs, scene tags, scene tagline, compendium updates, arc state.
- `extraction_context` = snapshot after scene+state extraction, before storyteller. Missing recent_events, compendium updates, gm_beat, arc, pc.momentum.

### Problems with Current State

- **No `state` command.** Cannot see PC sheet, inventory, conditions, NPC roster, compendium, arc state despite `state.yaml` being co-located with `events.jsonl`.
- **No `diff` command.** Cannot compare game state between two turns. Per-turn `deltas` requires manual cross-referencing.
- **No `trace` command.** Cannot track a field (e.g., inventory, conditions, NPC presence) across turns.
- **No search.** Cannot find turns involving a specific NPC or item.
- **`mechanics` omits the narrative output** the player received.
- **Section extraction in `mechanics` uses exact markdown header matching** — any prompt template change breaks extraction silently.
- **Connectors are synthetic** (computed from stream topology, not actual data).
- **Stream naming mismatch:** skill doc says `rules`/`progress`, data model says `ruling`/`storytell`.
- **Legacy scripts (`get-turn.sh`, `get-deltas.sh`)** are thin wrappers.

## Target State — What It Becomes

### Guiding principle

Zero engine changes. All data sources exist. The commands compose them. Coverage gaps are documented, not papered over. When a field is not reconstructable from existing data, the command says so and suggests the workaround (`state.yaml` for current turn, `deltas` for a specific turn's changes).

### New ev.py commands

**1. `state [--format {full,compact,pc,inventory,arc,scene,npcs}]`**

Reads `state.yaml` directly, renders formatted output.

```
--- PC ---
Name: Michael Smith
Tagline: Information broker, eyes for the unseen
Stats: str 2, dex 4, wit 4, lore 1, cha 3, res 2
Momentum: -1
Conditions: (none)

--- Inventory ---
  Lockpick Set ×1
  Compact Pistol ×1
  Pistol Rounds ×12
  Stim Pack ×2

--- Location ---
  Barrstad Junction — The corridor is lined with dark alcoves...

--- Scene ---
  Tags: tense_atmosphere, stealth, approaching_threat
  Tagline: The Patrol Approaches
  Present NPCs: Player's Brother (Leo), ...
  Recent Events: (5)

--- Arc ---
  Goal: Secure passage credits for the highlands...
  Thematic Question: Is the safety of one person worth...
  Active Threads (1): the_brother_emergency [urgent, progress 0]
  Completed Threads (0):
  Hidden Truths (2): ...

--- Compendium NPCs (4) ---
  matthew_ho — Matthew Ho, Black Market Courier
  crowd_thief — Crowd Thief, Opportunistic Thief
  ...
```

No turn argument. The current state is the authoritative source. For historical state, use `diff` + `deltas`.

**2. `diff <turn-A> <turn-B> [--section <section>]`**

Compares the extraction_context snapshots from both events, then supplements with `applied` and `changes` from intermediate turns.

Algorithm:
1. Load event at turn-A and event at turn-B.
2. Compare `extraction_context` fields: `inventory_this_turn`, `conditions_this_turn`, `present_npcs_this_turn`, `location_this_turn`, `scene_tags_this_turn`. Show before/after for each.
3. Collect all intermediate events (turn A+1 through B). Accumulate `applied` entries (deduplicate: later applied overwrites earlier). Merge `changes` entries.
4. Combine: if an intermediate `applied` field was modified, show it and note which turn(s).
5. For fields not covered: print a note.

Output format:

```
diff 3 7

--- NPCs present ---
- matthew_ho  (removed turn 4)
+ player_brother  (added turn 6)
  crowd_thief  (unchanged)

--- Inventory ---
- Slimdeck Interface  (removed turn 5)
  Lockpick Set  (unchanged)

--- Conditions ---
(none)

--- Location ---
  Barrstad Junction  (unchanged)

--- Scene Tags ---
  chaos, panic → tense_atmosphere, stealth  (changed turn 6)

--- Also changed (from applied, not in snapshots) ---
turn 4: compendium_npc_update.matthew_ho (allegiance)
turn 5: recent_events_add (x2)
turn 6: scene_tagline → "The Patrol Approaches"

--- Not tracked in historical snapshots ---
pc.stats, pc.name, compendium.bios, arc.threads —
use `state` (current) or `deltas <turn>` to inspect.
```

`--section inventory` limits output to one section. Useful for focused debugging.

**3. `trace <field> [--from N] [--to M]`**

Single field across turns. Field paths:

| Path | Data source | Notes |
|---|---|---|
| `inventory` | extraction_context + applied | Shows item list per turn, highlights adds/removes |
| `inventory.<id>` | extraction_context + applied | Tracks single item across turns |
| `conditions` | extraction_context + applied | Condition list per turn |
| `conditions.<id>` | extraction_context + applied | Single condition lifecycle |
| `npcs` | extraction_context + applied | Present NPC IDs per turn |
| `npcs.<id>` | extraction_context + applied | Single NPC presence timeline |
| `location` | extraction_context + applied | Location name per turn |
| `scene.tags` | extraction_context + applied | Tags per turn |
| `scene.tagline` | applied | Only when changed |
| `pc.momentum` | changes | Only when changed (available at turn granularity) |

Fields not in the table draw from `applied` at turn granularity (value when modified only).

Output: table with one row per turn.

```
trace inventory --from 3 --to 7

Turn | Inventory
─────┼────────────────────────────────────────────
   3 | Lockpick Set×1, Compact Pistol×1, Rounds×12, Stim×2, Slimdeck×1
   4 | (same)
   5 | Lockpick Set×1, Compact Pistol×1, Rounds×12, Stim×2  ← Slimdeck removed
   6 | (same)
   7 | (same)
```

For collection fields with no change, shows "(same)". For changes, adds a highlight arrow.

**4. `search <expr>`**

Expression syntax: `<field>=<value>` or `<field>~<regex>`.

Searches against `applied`, `extraction_context`, and `input` in events.

| Expression | Matches |
|---|---|
| `npc:<id>` | Turns where NPC is in `present_npcs_this_turn` or in `applied.npc_add`/`.npc_remove`/`.npc_update` |
| `npc_add:<id>` | Turns where NPC was added via `applied.npc_add` |
| `item:<id>` | Turns where item in `inventory_this_turn` or `applied.inventory_add`/`.inventory_remove`/`.inventory_update` |
| `condition:<id>` | Turns where condition in `conditions_this_turn` or `applied.pc_condition_add`/`.pc_condition_remove` |
| `band:<band>` | Turns with this dice result in `ruling.band` |
| `rejected` | Turns with any `rejected` entries |
| `input~<regex>` | Turns where player input matches regex |
| `thread:<id>` | Turns where thread id appears in applied (indirect: not stored) — requires prompt section extraction; marked as (brittle) |

Output: one line per matching turn:

```
$ ev.py search npca:player_brother
turn 6: npc_add player_brother — "The Lost Brother"
turn 7: (present in scene)
turn 8: (present in scene)
turn 9: npc_update player_brother — notes changed to "Buries his face in your shoulder..."

$ ev.py search band:failure
turn 3: band=partial (lockpick check, diff=hard, total=8)
```

Uses `extraction_context` for presence checks and `applied` for mutations. For presence-only matches (no mutation that turn), shows "(present in scene)" without a breakdown.

### Existing command improvements

**`mechanics` improvements:**

1. Add narrative output section:
```
--- Narrative (player received) ---
<first 500 chars of narrate_prompt.output>
(full text: ev.py compact <N> narrate)
```

2. Regex-based section extraction. Define section markers in a config dict:

```python
SECTION_MARKERS = {
    "gm_beat": r"^## gm_beat$",
    "campaign_arc": r"^#{1,3}\s*Campaign Arc\b",
    "deescalate": r"^## deescalate$",
    "pressures": r"^## Current Pressures$",
    "rules_stakes": r"^## rules_stakes$",
    "pending_beat": r"^## pending_beat$",
}
```

3. Handle `extraction_context` fields directly (no prompt parsing needed for NPC presence, location, scene tags, inventory, conditions — they're in structured data).

4. Report what streams actually ran and which extraction streams were skipped.

**`deltas` improvements:**

Add a flag `--from-stream <stream>` to filter mutations by source. Parse the `extraction` event key to determine which stream produced which applied fields (already documented in chronicle.py: extraction.context traces this).

**`summary` improvements:**

Add `--format json` flag. Output JSON array of turn summaries for piping to `jq`:

```json
{"turn": 1, "streams": "ruling, narrate, scene, state, storytell", "tokens_in": 15291, "tokens_out": 829, "tt": "25.5s", "intent": "...", "deltas": 7}
```

### Stream naming aliases

Accept both `ruling`/`rules` and `storytell`/`progress` in stream arguments:

```python
STREAM_ALIASES = {
    "rules": "ruling",
    "ruling": "ruling",
    "progress": "storytell",
    "storytell": "storytell",
    "narrate": "narrate",
    "scene": "scene",
    "state": "state",
}
```

### Deprecations

| Item | Action |
|---|---|
| `get-turn.sh` | Replace with: `#!/bin/sh\n exec python3 scripts/debug/ev.py turn "$@"` |
| `get-deltas.sh` | Replace with: `#!/bin/sh\n exec python3 scripts/debug/ev.py deltas "$@"` |

## Decision Table

| Decision | What | Why |
|---|---|---|
| Zero engine changes | No new fields in events.jsonl. No new writes. No schema changes. | Every command uses existing data. The coverage gaps in historical reconstruction are documented rather than papered over. Maintainers can add a state_snapshot field later if needed — ev.py will use it if present (backward compat). |
| `diff` uses extraction_context as primary source | Compares snapshots from the two event boundaries, supplemented by applied + changes from intermediate turns | extraction_context is the only per-turn structured data with before/after semantics for multiple fields. Applied+changes fill gaps. |
| `state` reads state.yaml directly | No turn argument | state.yaml is the authoritative post-turn state. Historical reconstruction from extraction_context+applied is incomplete (lacks pc.stats, compendium bios, arc state). Rather than ship half-working reconstruction, document it and suggest `diff` + `deltas` for historical inspection. |
| Search runs against structured fields, not grep | Parses extraction_context and applied for exact matches | Grep would find false positives in prompt text (NPC names appearing in narrative prose, not just state mutations). Structured search is exact and faster. |
| Section extraction uses regex config | `SECTION_MARKERS` dict with compiled patterns via `re.search()` | Survives header level changes (`##` → `###`). Single-file fix when prompts change. |
| Stream aliases in argument parser | Accept both names, map internally | Resolves skill-doc vs. data-model mismatch without migration. |

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `get-turn.sh` script body | `scripts/debug/get-turn.sh` | Replaced by one-liner delegating to `ev.py turn` |
| `get-deltas.sh` script body | `scripts/debug/get-deltas.sh` | Replaced by one-liner delegating to `ev.py deltas` |
| `extract_section_by_pattern()` exact header match | `scripts/debug/ev.py` | Replaced by `SECTION_MARKERS` regex config |
| Hardcoded section header strings in `cmd_mechanics` | `scripts/debug/ev.py` | Replaced by `SECTION_MARKERS` config dict |

## What Is Unchanged

- All existing ev.py commands — stable signatures and output.
- `_extract_connectors()` — connectors remain computed from stream topology.
- `_build_state_diff()` — kept; duplication with `tv._tv_state_diff()` is acceptable (ev.py cannot import tv.py).
- `load_events()`, `find_turn()` — unchanged.
- File path resolution — unchanged.
- `events.jsonl` — no new fields.
- `state.yaml` — no new fields.
- `chronicle.md` — no changes.
- Engine code (`turn.py`, `extraction.py`, `delta.py`, `changes.py`) — no changes. Not touched.

## Migration Notes

None. No schema changes. Old saves work identically. New commands simply surface existing data in useful formats.

## Prompt Token Impact

None. No prompts modified. No new LLM calls.

## Context for Implementing LLMs

- `scripts/debug/ev.py` (704 lines) — the entire file. All changes are additive (new commands, new helpers) except the `SECTION_MARKERS` refactor in `cmd_mechanics`. Read the full file once; edit individual functions.
- `ccya/engine/changes.py` — `summarize_changes()` (lines 82–232) for the field-level diff structure stored in each event's `changes` key. Used by `diff` and `trace` for the categories it covers.
- `ccya/models.py` — `StateDelta` (lines 235–293) for the field names in `applied`. `StorytellerResult` (lines 483–523), `SceneExtractResult` (lines 296–331), `StateExtractResult` (lines 333–376) for extraction stream output shapes.
- `ccya/engine/turn.py` lines 1360–1403 — the event construction block. Reference for which keys exist in events and where each comes from. Not modified.
- `ccya/engine/extraction.py` lines 44–106 — `_build_extraction_context()` and `_ExtractionContext`. Understanding when extraction_context is captured (after scene+state, before storyteller) is essential for the `diff` command's semantics.
- `docs/repomap.md` — section "State shape — state.yaml" (lines 149–199) for the authoritative field list that `state` command renders.
