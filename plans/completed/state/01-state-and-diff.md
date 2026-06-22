# Phase 1: `state` and `diff` commands for ev.py

## Status
`completed`

## Phases

3 phases: (1) state + diff commands, (2) trace + search commands, (3) mechanics improvements + stream aliases + legacy deprecation

## Issue

ev.py offers per-turn pipeline debugging (prompts, outputs, deltas, connectors, timing) but cannot answer the two most common game-judging questions: "what is the current game state?" and "what changed between two turns?" Users must manually read `state.yaml` and cross-reference `deltas` output across turns.

## Solution

Add two new commands that compose existing on-disk data. `state` reads `state.yaml` directly and renders formatted output. `diff` compares `extraction_context` snapshots between two events and supplements with `applied` + `changes` from intermediate turns. Zero engine changes — all data already exists.

## Firm decisions

1. `state` reads `state.yaml` only — no turn argument. Historical state reconstruction is not provided (it would require `extraction_context` which covers only 5 fields, or a future `state_snapshot` field in events). Document this clearly in the command help.
2. `diff` uses `extraction_context` as its primary data source — the per-event snapshot of `present_npcs_this_turn`, `location_this_turn`, `scene_tags_this_turn`, `inventory_this_turn`, `conditions_this_turn`. These are the only fields with before/after semantics across turns.
3. `diff` supplements with `applied` and `changes` from intermediate events for fields not in `extraction_context`.
4. Fields not covered by any data source (pc.stats, compendium bios, arc state) are listed in a "not tracked" section at the bottom.
5. Zero engine changes. No new fields in `events.jsonl`.

## Non-goals

- Historical full-state reconstruction (no state\_snapshot in events, no turn replay logic)
- Cross-turn field tracing (Phase 2: `trace` command)
- Search/filter (Phase 2: `search` command)
- Mechanics/stream alias/summary format improvements (Phase 3)

## Risks, Ambiguities, and Blockers

- `extraction_context` is captured during the pipeline, not at the turn boundary. It represents state after scene+state extraction but before storyteller. Users comparing `diff` will see a within-turn intermediate state, not the post-turn state. Document this with a one-line note in `diff` output.
- Some fields in `extraction_context` may be empty or null for turns that didn't change them. The `diff` command must handle missing keys gracefully (treat as "unchanged").
- `state.yaml` format is a nested YAML dict with arbitrary-depth structures (compendium npcs with bio/motivation/fear/leverage, arc threads with nested dicts). The formatter must handle nested dicts and lists without crashing.
- **Flag parsing:** existing `main()` uses `args[-1]` for file path detection and positional indexing for arguments. Adding `--format`, `--save-dir`, `--section` requires a two-pass scan: first strip `--` flags, then process positional args. The existing `args[-1].startswith("saves/")` path detection runs after flag stripping. This is a single helper function, not a rewrite.

## Implementation — Phase 1: `state` + `diff` commands

### Context files to load

- `scripts/debug/ev.py` (704 lines) — whole file. Adding two new commands + helpers.
- `docs/repomap.md` section "State shape — state.yaml" for the authoritative field list.
- `ccya/engine/changes.py` lines 82–294 (`summarize_changes` + `format_change_lines`) for the field-level diff structure in the event's `changes` key.

### Detailed steps

#### Step 1.0 — Add flag scanning helper to `main()`

**File:** `scripts/debug/ev.py`, function `main()` (lines 603–700)

**What:** Add a `_strip_flags()` helper that extracts `--key value` and `--flag` tokens from `args` before the command match. This is the only parsing change needed — no `argparse`, no rewrite of existing case arms.

```python
def _strip_flags(args: list[str]) -> tuple[dict[str, str], list[str]]:
    """Separate --flags from positional args. Returns (flags dict, positional args).
    
    Handles:
      --key value     → {"key": "value"}
      --flag          → {"flag": "true"}
      saves/... paths → always positional
    """
    flags: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--") and not args[i + 1].startswith("saves/"):
                flags[name] = args[i + 1]
                i += 2
            else:
                flags[name] = "true"
                i += 1
        else:
            positional.append(a)
            i += 1
    return flags, positional
```

In `main()`, after `args = sys.argv[1:]`, insert:
```python
    flags, args = _strip_flags(args)
```

The existing `args[-1].startswith("saves/")` detection (line 612) now runs against the flag-stripped `args` and works correctly.

Each command accesses its flags from the `flags` dict. Commands without flags ignore it.

**Why:** Only parsing change needed. Zero impact on existing commands. The two-pass approach (flags first, then positionals) cleanly separates concerns.

**Validation:** `python3 scripts/debug/ev.py state --format compact` — `flags={"format": "compact"}, args=["state"]`. `python3 scripts/debug/ev.py diff 3 7 --section inventory saves/other/events.jsonl` — `flags={"section": "inventory"}, args=["diff", "3", "7", "saves/other/events.jsonl"]`.

#### Step 1.1 — `load_state_yaml()` helper

**File:** `scripts/debug/ev.py` (after line 46, before `find_turn`)

**What:** Add a helper function that reads `state.yaml` from the save directory and returns the parsed dict. Use the same `DEFAULT_SAVE_DIR` pattern as `events.jsonl`.

```python
def load_state_yaml(save_dir: Path = DEFAULT_SAVE_DIR) -> dict[str, Any]:
    """Load and parse state.yaml from the save directory."""
    path = save_dir / "state.yaml"
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    import yaml
    with open(path) as f:
        result = yaml.safe_load(f)
        if isinstance(result, dict):
            return result
        print(f"Error: {path} is not a valid state YAML", file=sys.stderr)
        sys.exit(1)
```

**Why:** Single entry point for reading state.yaml. Using `yaml.safe_load` (already available in the project — used by `ccya/models.py:load_config`).

**Validation:** `python3 -c "from scripts.debug.ev import load_state_yaml; s = load_state_yaml(); print(s.get('pc',{}).get('name'))"` — must print the PC name without error.

#### Step 1.2 — `format_state()` renderer

**File:** `scripts/debug/ev.py` (after `load_state_yaml`, new function)

**What:** A function that takes a parsed state dict and a format mode string, prints formatted output to stdout. Format modes:

- `full` — all sections (pc, inventory, location, scene, arc, compendium)
- `compact` — PC name + location + turn number only (one line)
- `pc` — PC section only
- `inventory` — inventory section only
- `location` — location section only
- `scene` — scene section only
- `arc` — arc section only
- `npcs` — compendium NPCs section only
- `compidx` — NPC IDs + names only (compact table)

The renderer accesses state dict keys directly by known field names from the state shape:

| Section | State path | Rendered as |
|---|---|---|
| PC | `pc.name`, `pc.tagline`, `pc.stats`, `pc.momentum`, `pc.conditions` | Labeled fields |
| Inventory | `inventory` (list of dicts with id, name, amount, notes) | Bullet list: `name ×amount` |
| Location | `location` (id, name, description) | Header + description |
| Scene | `scene.tags`, `scene.tagline`, `scene.present_npcs`, `scene.recently_left`, `scene.recent_events` | Tag list, NPC presence table |
| Arc | `arc.visible_goal`, `arc.thematic_question`, `arc.threads`, `arc.completed_threads`, `arc.hidden_truths`, `arc.discovered_truths` | Goal + question + thread table |
| Compendium | `compendium.npcs` (dict of id → name, title, bio, motivation, fear, leverage) | Per-NPC block or compact table for compidx |

For `full` and `compact` modes, also show turn number from `state.get('meta', {}).get('turn', '?')`. If the `meta` key or `turn` key is absent, print `?`.

Handle missing keys gracefully: skip section if its state key is absent or empty.

**Why:** Users can inspect current game state without reading raw YAML. The format modes let them focus on specific concerns.

**Validation:** Run `ev.py state` on the default save and verify output matches `state.yaml` content. Run `ev.py state --format pc` and verify only PC section printed. Run on a save dir without `state.yaml` — must print error and exit 1.

#### Step 1.3 — `cmd_state()` CLI command

**File:** `scripts/debug/ev.py` (new command function, new `match` arm in `main()`)

**What:** New CLI command with signature:
```
ev.py state [--format {full,compact,pc,inventory,location,scene,arc,npcs,compidx}] [--save-dir <path>]
```

**Parsing approach:** Extend the existing `sys.argv` parser with ad-hoc flag scanning (no `argparse`). The existing parser uses `args[-1]` for optional file path detection. Flag scanning coexists by:
1. First pass: walk `args` list, collect any token starting with `--`, consume its value arg if it takes one, and remove both from `args`.
2. Remaining `args` are positional (command, turn, stream, field, file path).
3. The existing `args[-1].startswith("saves/")` file path detection runs after flag stripping — it sees only positional args.

This is additive to the existing parser. No existing case arms change.

Implementation:
1. Load state dict via `load_state_yaml()`
2. If `--save-dir` provided, use that instead of `DEFAULT_SAVE_DIR`
3. Call `format_state(state, format_mode)`

The `cmd_state()` function receives the `flags` dict from `_strip_flags()` (or accesses it via closure):

```python
cmd_state(flags.get("format", "full"), flags.get("save-dir"))
```

**Why:** Entry point for the new `state` command.

**Validation:** `python3 scripts/debug/ev.py state` — must print all sections. `python3 scripts/debug/ev.py state --format compact` — must print single line.

#### Step 1.4 — `load_extraction_context()` helper

**File:** `scripts/debug/ev.py` (new helper function)

**What:** Given an event dict, return its `extraction_context` as a flat dict, or `None` if absent. Return type needs to support `==` comparison between two events.

```python
def load_extraction_context(ev: dict[str, Any]) -> dict[str, Any] | None:
    """Return the extraction_context sub-dict from an event, or None."""
    ctx = ev.get("extraction_context")
    if isinstance(ctx, dict) and ctx:
        return ctx
    return None
```

**Why:** `diff` needs to compare extraction_context between two events. This helper isolates the lookup.

**Validation:** Run on a known event with extraction_context — must return the dict. Run on a compaction event — must return None.

#### Step 1.5 — `diff_extraction_context()` comparator

**File:** `scripts/debug/ev.py` (new helper function)

**What:** Compare two extraction_context dicts and produce a structured diff per field. Output format is a list of dicts with keys: `section` (the field category name), `kind` (`"changed"` | `"unchanged"`), `before_value`, `after_value`, `before_turn`, `after_turn`.

Source confirms (turn.py:1378–1384) that extraction_context keys are always present — empty list if nothing changed, never absent. No "missing" case.

Fields to compare:

| extraction_context key | Display section |
|---|---|
| `present_npcs_this_turn` | NPCs |
| `inventory_this_turn` | Inventory |
| `conditions_this_turn` | Conditions |
| `location_this_turn` | Location |
| `scene_tags_this_turn` | Scene Tags |

For each field:
- Compare by structural equality. For lists, compare sorted IDs. For dicts, compare `id` + `name`.
- If equal: emit `kind="unchanged"`.
- If not equal: emit `kind="changed"` with before/after values and a human-readable change summary.
- Empty list vs non-empty list = changed. Empty list vs empty list = unchanged. Treat empty list as "no items", not "missing data."

**NPCs comparison detail:** For `present_npcs_this_turn`, compare the set of NPC IDs present in each list. Show added IDs as `+id` and removed IDs as `-id`. IDs present in both but with different `notes` are shown as `~id (notes changed)`.

**Inventory comparison detail:** For `inventory_this_turn`, compare by item `id`. Show per-item: `id (unchanged)` if same, `id ×a→b` if amount changed, `-id` if removed, `+id` if added. Include item names.

**Why:** Produces the structured data that `cmd_diff` will format for display.

**Validation:** Write a minimal test script that loads two events, calls `diff_extraction_context()`, and prints the result. Verify added/removed/changed items are detected.

#### Step 1.6 — `accumulate_intermediate_changes()` helper

**File:** `scripts/debug/ev.py` (new helper function)

**What:** Collect all events with `turn` in the range (A, B]. For each event, extract:
- `applied` dict — the StateDelta fields (`npc_add`, `inventory_add`, `pc_condition_remove`, `scene_tags`, `location_change`, `scene_tagline`, `compendium_npc_update`, `recent_events_add`, etc.)
- `changes` dict — the computed pre/post diff (`inventory`, `player`, `facts`, `momentum`)

**Deduplication rule:** `applied` takes precedence over `changes` for overlapping fields. Overlaps:
  - inventory → `applied.inventory_add/remove/update` wins over `changes.inventory`
  - conditions → `applied.pc_condition_add/remove` wins over `changes.player` (condition entries)
  - `changes` is used for its exclusive categories only: `facts` (recent event text diffs) and `momentum` (momentum before/after/delta)
  - `changes.player` location/stat changes are dropped in favor of `applied.location_change`

Return merged lists grouped by category: one list of field names with per-turn breakdowns. Deduplicate: if the same field appears in multiple intermediate events, keep all with turn attribution.

```python
def accumulate_intermediate_changes(events: list[dict[str, Any]], turn_a: int, turn_b: int) -> list[dict[str, Any]]:
    """Collect applied + changes from events between turn_a and turn_b (exclusive of turn_a, inclusive of turn_b).
    Returns list of {turn, field, value, source} dicts."""
```

**Why:** `diff` shows not just the final before/after but the per-turn mutations. This makes it clear *which turn* caused each change.

**Validation:** Run on a known range (e.g., 3→7) and verify the output lists per-turn mutations.

#### Step 1.7 — `cmd_diff()` CLI command

**File:** `scripts/debug/ev.py` (new command function, new `match` arm in `main()`)

**What:** New CLI command:
```
ev.py diff <turn-A> <turn-B> [--section <section>]
```

Parsing: `<turn-A>` and `<turn-B>` are positional (args[1], args[2] after flag stripping). `--section` is a flag consumed during the flag scan pass.

Algorithm:
1. Load events via `load_events()`.
2. Find events at turn-A and turn-B via `find_turn()`.
3. Load extraction_context from both events via `load_extraction_context()`.
4. Call `diff_extraction_context()` to get the field-level diff.
5. Call `accumulate_intermediate_changes()` to get per-turn mutations.
6. Print output in sections:

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
pc.stats, pc.name, compendium.bios, arc.threads
```

If `--section` is provided, filter output to that section only. Valid values: `npcs`, `inventory`, `conditions`, `location`, `tags`, `applied`.

Handle edge cases:
- turn-B ≤ turn-A: print error and exit 1.
- turn-A or turn-B events not found: print error with which turn is missing.
- turn-A or turn-B events have no `extraction_context`: print "(no snapshot available — event predates extraction_context)" and skip snapshot comparison; still show accumulated changes.
- empty diff: print "(no changes detected between turn A and turn B)".

Register in `main()`:
```python
case "diff":
    turn_a = int(args[1]) if len(args) > 1 else None
    turn_b = int(args[2]) if len(args) > 2 else None
    section = flags.get("section")
    cmd_diff(events, turn_a, turn_b, section=section)
```

**Why:** Direct answer to "what changed between two turns." Composes existing data sources without engine changes.

**Validation:** `python3 scripts/debug/ev.py diff 1 9` — must show inventory changes, NPC adds/removes, location changes, etc. `python3 scripts/debug/ev.py diff 3 3` — must print error. `python3 scripts/debug/ev.py diff 1 500` — must say turn 500 not found. `python3 scripts/debug/ev.py diff 1 9 --section inventory` — must show only inventory section.

### Tests to write or update

No tests to write. Tests are temporarily removed during refactor per AGENTS.md. Run `python3 scripts/debug/ev.py` on the default save to manually verify each command.

### REPOMAP updates required

- `scripts/debug/README.md` — update command table to include `state` and `diff` once all phases are complete (handled in Phase 3). No repomap changes needed — `ev.py` is a standalone debug script, not part of the core library API.
