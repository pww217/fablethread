# Plan 01 — Foundation: package structure + data access + read-only commands

## Purpose

Move `scripts/debug/ev.py` into `ccya/ev/` as a proper package with a shared data access layer, port all 10 surviving read-only subcommands, add sanitizer visibility to deltas/mechanics, and add `turn --json`.

## Problem Statement

ev.py is a 2252-line monolithic script read-only CLI with no ccya imports, no package structure, and no shared data access layer. It has 16 subcommands with overlapping concerns, zero sanitizer event visibility, and no programmatic JSON output from `turn`. TurnViewer parses `events.jsonl` independently through copy-pasted logic.

## Constraints

- `scripts/debug/ev.py` becomes a thin entry point that imports and delegates to `ccya/ev`
- Old subcommands `props`, `compact`, `outputs`, `connectors`, `pacing`, `dice` are merged into prompt, deltas, mechanics
- No ccya imports in the read-only code path (engine deps are lazy for play/check/eval in later phases)
- `ccya/ev/events.py` is the single source of truth for event reading — TurnViewer may adopt it later

## Non-goals

- `play`, `check`, `eval` commands — stubs only, implemented in phases 3-4
- Checker library — implemented in phase 2
- Deleting old eval harness — phase 6
- LLM-based checkers — phase 5

## Solution

Create `ccya/ev/` package with `__init__.py` (dispatch), `events.py` (data access), `inspect.py` (summary/timing/turn/prompt), `deltas.py` (deltas/mechanics), `state_tools.py` (state/diff/trace/search), and `output.py` (formatting). Port all 10 read-only subcommands, merging the 6 dropped ones. Add sanitizer event display to `deltas` and `mechanics`. Add `--json` flag to `turn`. Rewrite `scripts/debug/ev.py` to a 5-line wrapper.

## Firm decisions

- Explicit imports for checker modules (phase 2), not auto-discovery
- Pre-filter events to turn-only in shared layer (`filter_turn_events`)
- Extraction context: use engine's existing event field directly
- `saves/ev/<session>/` convention for play artifacts (phase 3)

## Risks, Ambiguities, and Blockers

- This phase touches every function in the current ev.py. Risk of regression in read-only commands. Mitigation: test each command against current `saves/default/events.jsonl` before/after.
- The `prompt` command merges props/compact/prompt with different defaults. The old `prompt TURN STREAM FIELD` becomes `prompt TURN STREAM --field FIELD`; the default view is user+output (old `compact` behavior). Users of the old `prompt` single-field view must add `--field`.

## Status

`completed`

## Phases

Single phase — foundational package restructure. Everything in this plan touches overlapping files in `scripts/debug/ev.py` and the new `ccya/ev/` package.

## Implementation

### Context files to load

- `scripts/debug/ev.py` (entire file — base for porting)
- `saves/default/events.jsonl` (test data for verifying ported commands produce identical output)
- `ccya/state/io.py` line 95 (`load_state` function)
- `ccya/engine/extraction.py` lines 62–101 (`_build_extraction_context` output shape)
- `ccya/models.py` line 508 (`TurnResult` — needed for events.py typing)

### Detailed steps

#### Step 1.1 — Create `ccya/ev/__init__.py`

**File:** `ccya/ev/__init__.py`

**What:** Package entry point with:
- `STREAM_ALIASES` dict (ported from ev.py:59–67)
- `_resolve_stream()` function (ev.py:70–76)
- `_strip_flags()` function (ev.py:97–120)
- `DEFAULT_SAVE_DIR = Path("saves/default")` (ev.py:32)
- `DEFAULT_FILE` constant (ev.py:33)
- `main()` function with argparse for 13 subcommands: summary, timing, turn, prompt, deltas, mechanics, state, diff, trace, search, play, check, eval
- `play`, `check`, `eval` dispatch to `_stub_command()` that prints "Not yet implemented — planned for phase N" and exits 0
- Lazy imports: each command module imported in its case branch, not at module top level
- `--json` flag on `turn`: when present, pretty-print the raw event dict instead of calling `cmd_turn()`

**Why:** Central dispatch with lazy imports keeps read-only commands fast and avoids engine deps until play/check/eval are implemented.

**Validation:** `python -m ccya.ev turn 1` or `python scripts/debug/ev.py turn 1` produces identical output to old ev.py for all read-only commands except those whose output intentionally changed (merged prompt, sanitizer in deltas/mechanics, turn --json).

#### Step 1.2 — Create `ccya/ev/events.py`

**File:** `ccya/ev/events.py`

**What:** Shared data access layer with these functions (ported from ev.py helpers):

```python
def load_events(path: Path) -> list[dict]:
    """Load events from events.jsonl. (ev.py:79–95)"""

def filter_turn_events(events: list[dict]) -> list[dict]:
    """Return only turn events (kind absent or 'turn')."""

def find_turn(events: list[dict], turn: int) -> dict | None:
    """Find a turn event by number. (ev.py:149–158)"""

def extract_field(event: dict, dotpath: str) -> Any:
    """Extract a dotpath field (e.g. 'ruling.band') from an event.
    Handles nested dict traversal. Returns None if path doesn't exist."""

def extract_fields(events: list[dict], dotpaths: list[str]) -> list[dict]:
    """Extract a subset of fields from every event. Used by checkers in phase 2."""

def extract_extraction_context(event: dict) -> dict:
    """Return the extraction_context sub-dict from a turn event.
    `event.get("extraction_context", {})` — already computed by engine."""

def load_current_state(save_dir: Path) -> dict:
    """Load state.yaml via ccya.state.io.load_state()."""

def state_diff(before: dict, after: dict) -> list[str]:
    """Compute human-readable diff between two state snapshots."""

def load_state_yaml(save_dir: Path | None = None) -> dict:
    """Load state.yaml. (ev.py:123–138)"""
```

Also port these internal helpers:
- `_get_nested()` (ev.py:617–624)
- `_try_parse_json()` (ev.py:626–640)
- `_parse_ruling_intent()` (ev.py:642–647)
- `_stream_keys()` (ev.py:649–656)
- `_stream_ms()` (ev.py:667–676)
- `_total_tokens_in()` (ev.py:678–684)
- `_total_tokens_out()` (ev.py:686–692)
- `_total_tt()` (ev.py:694–703)
- `_has_retries()` (ev.py:705–711)
- `_has_errors()` (ev.py:713–721)
- `_has_rejections()` (ev.py:723–725)
- `_build_state_diff()` (ev.py:563–616)
- `_count_state_diff()` (ev.py:558–561)
- `_build_summary_json()` (ev.py:249–263)
- `diff_extraction_context()` (ev.py:1039–1056) — moved here since it's a data access function
- `accumulate_intermediate_changes()` — for diff command
- `extract_field_from_event()` (ev.py:1434–1574) — for trace and search

**Why:** Single source of truth for event reading. Both read-only commands and future checkers consume this layer.

**Validation:** `python -c "from ccya.ev.events import load_events; events = load_events(Path('saves/default/events.jsonl')); print(len(events))"` returns same count as old ev.py.

#### Step 1.3 — Create `ccya/ev/output.py`

**File:** `ccya/ev/output.py`

**What:** Markdown formatting and rendering helpers:
- Section/marker extraction: `SECTION_MARKERS` dict (ev.py:38–51), `extract_section_by_pattern()` (ev.py:around 160–210)
- `_dict_to_lines()` (ev.py:775–880)
- `_wrap_text()` (ev.py:1027–1058)
- `_shorten()` (ev.py:1239–1257)
- `_shorten_value()` (ev.py:1377–1381)
- `_short_item_name()` (ev.py:1575–1585)
- `_values_equal()` (ev.py:1696–1714)
- `_describe_collection_change()` (ev.py:1716–1730)
- `_trace_display_name()` (ev.py:1667–1694)
- Any future Markdown table helpers (rich Table to Markdown conversion if `rich` is used)

**Why:** Formatting helpers are shared across all display commands and should not be duplicated in each module.

**Validation:** `python -c "from ccya.ev.output import _wrap_text; print(_wrap_text('hello', indent=2))"` works.

#### Step 1.4 — Create `ccya/ev/inspect.py`

**File:** `ccya/ev/inspect.py`

**What:** Read-only per-turn display commands:

- `cmd_summary(events, format="text")` — ported from ev.py:214–245. Drops the `--format json` path (no JSON consumer identified yet; add if needed).
- `cmd_timing(events)` — ported from ev.py:267–283.
- `cmd_turn(ev, json_mode=False)` — ported from ev.py:286–301. When `json_mode=True`, pretty-print the raw event dict with `json.dumps(ev, indent=2)`.
- `cmd_prompt(ev, stream, field=None, include_system=False)` — merges ev.py's `cmd_props` (304–314), `cmd_compact` (317–324), `cmd_prompt` (327–330) and `cmd_outputs` (333–338).

  New behavior:
  - Default: show user + output (old `compact`). `--system` adds system prompt (old `props`).
  - `--field <name>` shows a single field (old `prompt`).
  - Drops the separate `outputs` command; `turn --json` covers raw JSON inspection.

- `extract_prompt(ev, stream)` — ported from ev.py:161–196.

**Why:** These commands display per-turn data. Merging props/compact/prompt reduces command count and makes the interface more discoverable: one `prompt` command with flags instead of three similar commands.

**Validation:** `ev.py turn 1` and `ev.py prompt 1 ruling` produce expected output. `ev.py turn 1 --json` prints raw event JSON.

#### Step 1.5 — Create `ccya/ev/deltas.py`

**File:** `ccya/ev/deltas.py`

**What:** State mutation inspection commands:

- `cmd_deltas(ev)` — ported from ev.py:341–357. **Additions:**
  1. After the state diff section, add an **Extraction Context** section showing the in-turn data flow (NPCs, location, scene tags, inventory, conditions as seen by storyteller). Source: `extract_extraction_context(ev)`.
  2. After the extraction context, add a **Sanitizer** section. Find sanitizer events with matching turn number from `events.jsonl`. Show: threads_updated, threads_added, threads_resolved, goal_changed. If no sanitizer ran on this turn, show "(no sanitizer run)".
  - Keep the existing Rejections section.

- `cmd_mechanics(ev, events=None, show_pacing=False, show_dice=False, show_sanitize=False)` — ported from ev.py:360–485. **Merges:**
  - Accepts both `ev` (per-turn dict for default view) and `events` (full list for cross-turn dice/sanitize modes).
  - `mechanics` (ev.py:360) as the default: rules intent, GM beat, rules outcome, pacing context, threads, campaign arc, narrative, state deltas, connectors, summary.
  - `--pacing` flag: show only the pacing-focused view (ev.py's `cmd_pacing`, lines 488–540).
  - `--dice` flag: show dice roll summary across all turns (ev.py's `cmd_dice`, lines 2014–2084). Requires `events` — dispatch must pass both `ev` and `events`.
  - `--sanitize` flag: show all sanitizer events from the events list with their changes. Requires `events` — dispatch must pass both `ev` and `events`.
  
  Sanitizer events are already in `events.jsonl` with `kind: "sanitizer"`. They have fields: `threads_updated`, `threads_removed`, `threads_resolved`, `threads_added`, `goal_changed`, `changes_detail`. Display these in a readable Markdown format.

- `_extract_connectors()` — ported from ev.py:727–774. Shown as part of mechanics output (the old "Connectors" section), not as a separate command.

**Why:** Sanitizer events are currently invisible to ev.py. Adding them to deltas and mechanics closes the blind spot. Merging pacing/dice into mechanics with flags reduces command count while keeping specialized views.

**Validation:** Run against a file with known sanitizer events. `ev.py deltas 5` shows "Sanitizer" section. `ev.py mechanics 5 --dice` shows dice summary. `ev.py mechanics 5 --sanitize` shows sanitizer event data.

#### Step 1.6 — Create `ccya/ev/state_tools.py`

**File:** `ccya/ev/state_tools.py`

**What:** State file display and cross-turn analysis:

- `cmd_state(fmt, save_dir_path)` — ported from ev.py:1383–1385. Uses `load_state_yaml()` from events.py. Valid formats: `full`, `compact`, `pc`, `inventory`, `location`, `scene`, `arc`, `npcs`, `compidx` (ev.py:2214).
- `format_state(state, fmt)` — ported from ev.py helper. Renders the specified section(s).
- `_render_pc_section()` (ev.py:881–907)
- `_render_inventory_section()` (ev.py:909–923)
- `_render_location_section()` (ev.py:925–936)
- `_render_scene_section()` (ev.py:938–961)
- `_render_arc_section()` (ev.py:963–996)
- `_render_npcs_section()` (ev.py:998–1012)
- `_render_compidx_section()` (ev.py:1014–1025)

- `cmd_diff(events, turn_a, turn_b, section_filter)` — ported from ev.py:1389–1431.
  - `_diff_inventory()` (ev.py:1060–1117)
  - `_diff_conditions()` (ev.py:1119–1159)
  - `_diff_location()` (ev.py:1161–1181)
  - `_diff_scene_tags()` (ev.py:1183–1237)
  - `format_diff_output()` (ev.py:diff display)
  - `_print_unchanged_inventory()` (ev.py:1334–1354)
  - `_print_unchanged_conditions()` (ev.py:1356–1367)
  - `_print_unchanged_tags()` (ev.py:1369–1375)

- `cmd_trace(events, field, from_turn, to_turn, show_unchanged)` — ported from ev.py:1589–1665.

- `cmd_search(events, expressions)` — ported from ev.py:1986–2011.
  - `parse_search_expression()` (ev.py helper)
  - `search_events()` (ev.py helper)

**Why:** These commands operate on state files and cross-turn data. They share the `events.py` data access layer and `output.py` formatting, but have no overlap with per-turn inspection (inspect.py) or state mutation analysis (deltas.py).

**Validation:** `ev.py state --format pc`, `ev.py diff 1 5 --section npcs`, `ev.py trace momentum_before --from 1 --to 10`, `ev.py search npc:trevor_riddle` all produce expected output matching old behavior.

#### Step 1.7 — Rewrite `scripts/debug/ev.py`

**File:** `scripts/debug/ev.py`

**What:** Replace the 2252-line script with a thin entry point:

```python
#!/usr/bin/env python3
"""CLI entry point for ev tooling. Delegates to ccya.ev."""

from ccya.ev import main

if __name__ == "__main__":
    main()
```

**Why:** The existing `python scripts/debug/ev.py` invocation must continue to work. The real code lives in `ccya/ev/`.

**Validation:** `python scripts/debug/ev.py summary` produces the same output as before (for commands whose output didn't intentionally change).

### Tests to write or update

No test automation exists for ev.py (tests are temporarily removed per AGENTS.md). Manual verification:

1. Run each read-only command against `saves/default/events.jsonl` and visually confirm output matches expectations
2. Verify sanitizer section appears in `deltas` on turns where sanitizer ran
3. Verify `mechanics --dice` shows a complete dice summary
4. Verify `mechanics --sanitize` shows sanitizer event data
5. Verify `turn --json` dumps the raw event dict
6. Verify `prompt` without flags shows user+output (old compact), `--system` adds system (old props), `--field output` shows single field (old prompt)
