# Refactor Plan: Module Split

Goal: split large monolithic files by concern so each file has one reason to change
and the AI coding assistant can load targeted context instead of the whole file.

---

## File Verdicts

| File | Size | Verdict |
|---|---|---|
| `engine.py` | ~2k lines | **Split** — 6 natural seams, see below |
| `state.py` | ~700 lines | **Split** — 3 concerns in one file |
| `server.py` | ~900 lines | **Split** — debug/TV infrastructure vs. routes |
| `models.py` | ~300 lines | **Leave** — moderate size, one concern |
| `rules.py` | ~200 lines | **Leave** — already focused |
| `pack.py` | ~300 lines | **Leave** — cohesive, one concern |
| `llm_client.py` | ~200 lines | **Leave** — clean, one concern |
| `names.py` | tiny | **Move** — relocate to `engine/names.py` |
| `logging_setup.py` | tiny | **Leave** |
| `cli` / `__main__` | tiny | **Leave** |

---

## Target Structure

```
ccya/
  engine/
    __init__.py        # re-exports: EngineConfig, run_turn, generate_seed,
                       #   warmup, format_change_lines, is_turn_in_progress
    config.py          # EngineConfig dataclass + _EventLock + is_turn_in_progress
    narrate.py         # _narrate_messages, _known_characters_for_extract, names helpers
                       # absorbs names.py (generate_name_pool, generate_npc_names)
    rules.py           # _rules_messages, _call_rules, _log_rules_outcome
    extraction.py      # _run_extraction_pipeline, all _extract_*_messages, _call_stream
    seed.py            # generate_seed, _build_generate_seed_messages, _soft_validate_seed
    changes.py         # summarize_changes, format_change_lines, _summarize_applied
    turn.py            # run_turn orchestrator (thin — imports from the above)
    pressure.py        # _expire_scene_pressures
  state/
    __init__.py        # re-exports everything currently imported from ccya.state
    io.py              # load_state, save_state, init_save_dir, _default_state,
                       #   _migrate_state, _migrate_recent_events
    delta.py           # apply_delta, reconcile_delta, PC_CONDITIONS_MAX
    inventory.py       # normalize_inventory_id, resolve_inventory_canonical_id,
                       #   resolve_inventory_remove_target, _fuzzy_match_inventory,
                       #   _item_to_dict
    npcs.py            # build_npc_alias_map, touch_compendium_order
    chronicle.py       # append_event, append_chronicle, load_chronicle_tail,
                       #   load_recent_events, load_recent_chronicle_turns
    momentum.py        # apply_momentum (imports MOMENTUM_DELTA from ccya.rules)
  server/
    __init__.py        # re-exports: app, main
    app.py             # FastAPI app init, mounts, Jinja env, config bootstrap,
                       #   startup event, main()
    routes.py          # all @app.get / @app.post route handlers
    panels.py          # _debug_context, panel_* helpers, _load_*helpers
    tv.py              # _turn_viewer_data, _turn_viewer_* helpers,
                       #   _tv_parse_json_blob, _tv_dict_to_lines,
                       #   _tv_extract_stream_status, _tv_narration_lines
    metrics.py         # _recent_turn_metrics, _fmt_ms_seconds, _fmt_tokens,
                       #   _fmt_tokens_exact, _turn_log_entries, _load_rules_map
```

---

## engine/ Split Detail

### `engine/config.py`
- `EngineConfig` dataclass
- `_EventLock` class
- `is_turn_in_progress()`
- `_build_jinja_env()`
- `_render()` (the Jinja render helper)

### `engine/narrate.py`
- `_narrate_messages()`
- `_known_characters_for_extract()`
- `generate_name_pool()` (moved from `names.py`)
- `generate_npc_names()` (moved from `names.py`)

### `engine/rules.py`
- `_rules_messages()`
- `_call_rules()`
- `_log_rules_outcome()`
- Does NOT merge with `ccya/rules.py` (that stays as-is — it owns MOMENTUM_DELTA,
  band constants, dice logic)

### `engine/extraction.py`
- `_run_extraction_pipeline()`
- `_extract_scene_messages()`
- `_extract_state_messages()`
- `_extract_progress_messages()`
- `_call_stream()`

### `engine/seed.py`
- `generate_seed()`
- `_build_generate_seed_messages()`
- `_soft_validate_seed()`

### `engine/changes.py`
- `summarize_changes()`
- `format_change_lines()`
- `_summarize_applied()`

### `engine/turn.py`
- `run_turn()` — the async orchestrator
- Imports from config, narrate, rules, extraction, seed, changes, pressure
- Should be thin: no helper logic lives here, only the pipeline sequence

### `engine/pressure.py`
- `_expire_scene_pressures()`

### `engine/__init__.py`
Re-export everything server.py currently imports from `ccya.engine`:
```python
from ccya.engine.config import EngineConfig, is_turn_in_progress
from ccya.engine.turn import run_turn
from ccya.engine.seed import generate_seed
from ccya.engine.changes import format_change_lines
from ccya.engine.turn import warmup  # or wherever warmup lives
```

---

## state/ Split Detail

### `state/io.py`
- `load_state`, `save_state`, `init_save_dir`
- `_default_state`
- `_migrate_state`, `_migrate_recent_events`
- `_STAT_RENAME`, `_STAT_DEFAULTS`

### `state/delta.py`
- `apply_delta` (the big one — ~250 lines)
- `reconcile_delta`
- `PC_CONDITIONS_MAX`

### `state/inventory.py`
- `normalize_inventory_id`
- `resolve_inventory_canonical_id`
- `resolve_inventory_remove_target`
- `_fuzzy_match_inventory`
- `_item_to_dict`

### `state/npcs.py`
- `build_npc_alias_map`
- `touch_compendium_order`

### `state/chronicle.py`
- `append_event`
- `append_chronicle`
- `load_chronicle_tail`
- `load_recent_events`
- `load_recent_chronicle_turns`
- `_TURN_HEADER` regex

### `state/momentum.py`
- `apply_momentum`
- `_MOMENTUM_MIN`, `_MOMENTUM_MAX`

### `state/__init__.py`
Re-export everything currently imported from `ccya.state` throughout the codebase.
Do NOT change any import sites — they all keep `from ccya.state import ...`.

---

## server/ Split Detail

The key insight: `server.py` has three distinct concerns today:
1. **App bootstrap** — FastAPI app, config, Jinja env, pack loading, startup event
2. **HTMX route handlers** — the `@app.get/post` decorated functions
3. **Debug/TV data prep** — `_turn_viewer_data`, `_recent_turn_metrics`, `_turn_log_entries`,
   and the ~150 lines of `_tv_*` helpers

The TV data prep is the biggest offender: ~400 lines of `_tv_*` helpers that have nothing
to do with routing. It should never need to be loaded when working on route logic.

### `server/app.py`
- FastAPI `app` instance + middleware/mounts
- Jinja env
- Config bootstrap (EngineConfig, pack loading)
- `_ERRORS_LOG` deque
- `_render()` helper
- Module-level globals: `SAVE_DIR`, `PACKS_DIR`, `_active_pack`, `engine_config`
- `startup_event` / `main()`
- `_validate_stats()`

### `server/routes.py`
- All `@app.get` / `@app.post` handlers
- Imports from `server/app.py` for shared state, from `server/panels.py` for context,
  from `server/tv.py` for turn viewer data

### `server/panels.py`
- `_debug_context()`
- `_load_current_state()`
- `_load_recent_history()`
- `_load_last_actions()`
- `_load_rules_map()`
- `_get_opening()`, `_get_opening_actions()`

### `server/tv.py`
- `_turn_viewer_data()`
- `_tv_parse_json_blob()`
- `_tv_dict_to_lines()`
- `_tv_extract_stream_status()`
- `_tv_narration_lines()`
- `_tv_rules_status()`
- `_STATUS_CSS`, `_STAGE_CSS` constants

### `server/metrics.py`
- `_recent_turn_metrics()`
- `_turn_log_entries()`
- `_fmt_ms_seconds()`
- `_fmt_tokens()`
- `_fmt_tokens_exact()`

### `server/__init__.py`
```python
from ccya.server.app import app, main
```

---

## Import Migration

All external import sites (engine.py → state, server.py → engine, etc.) are
preserved via `__init__.py` re-exports. No import line outside the refactored package
needs to change.

Internal cross-module imports follow this dependency order (no circular imports):

```
models.py         (no ccya deps)
rules.py          (imports models)
llm_client.py     (no ccya deps)
state/inventory   (no ccya deps)
state/npcs        (imports state/inventory)
state/chronicle   (no ccya deps)
state/momentum    (imports ccya.rules)
state/io          (imports state/* helpers)
state/delta       (imports state/inventory, state/npcs)
state/__init__    (re-exports all of the above)
engine/config     (no ccya deps)
engine/narrate    (imports models, state)
engine/rules      (imports models, llm_client, ccya.rules)
engine/extraction (imports models, llm_client, state)
engine/seed       (imports models, llm_client, pack)
engine/changes    (imports models)
engine/pressure   (imports state)
engine/turn       (imports all engine/* submodules + state, rules, pack, llm_client)
engine/__init__   (re-exports run_turn, EngineConfig, generate_seed, etc.)
server/app        (imports engine, state, pack, models)
server/metrics    (imports state)
server/panels     (imports state, server/app globals)
server/tv         (imports state)
server/routes     (imports server/app, server/panels, server/tv, engine)
server/__init__   (re-exports app, main)
```

Note: `engine/rules.py` and `ccya/rules.py` are different files.
`engine/rules.py` = LLM call wrappers (prompt building, retries).
`ccya/rules.py` = deterministic logic (dice, bands, MOMENTUM_DELTA). Don't merge.

---

## REPOMAP Update (after refactor)

Replace the current flat entries with:

```
ccya/engine/config.py       EngineConfig dataclass, per-save turn lock, is_turn_in_progress
ccya/engine/narrate.py      Narrate prompt builder, NPC name generation (absorbs names.py)
ccya/engine/rules.py        Rules LLM call: prompt build, _call_rules, retry logic
ccya/engine/extraction.py   Three-stream extraction pipeline: scene/state/progress
ccya/engine/seed.py         Dynamic seed generation (new-game LLM call)
ccya/engine/changes.py      Change summary formatters (format_change_lines, etc.)
ccya/engine/pressure.py     Scene pressure expiry logic
ccya/engine/turn.py         run_turn() orchestrator — thin pipeline sequencing only
ccya/engine/__init__.py     Re-exports: EngineConfig, run_turn, generate_seed, warmup, format_change_lines

ccya/state/io.py             load_state, save_state, init_save_dir, state migration
ccya/state/delta.py          apply_delta, reconcile_delta (inventory/quest/NPC/condition/event/pressure)
ccya/state/inventory.py      normalize_inventory_id, resolve/fuzzy match helpers
ccya/state/npcs.py           build_npc_alias_map, touch_compendium_order
ccya/state/chronicle.py      append/load chronicle.md and events.jsonl
ccya/state/momentum.py       apply_momentum (pc.momentum from rules band)
ccya/state/__init__.py       Re-exports all state symbols (no import sites need to change)

ccya/server/app.py           FastAPI app, config bootstrap, Jinja env, pack loading, startup
ccya/server/routes.py        All HTMX route handlers (@app.get / @app.post)
ccya/server/panels.py        Panel context helpers: _debug_context, _load_*, _get_opening
ccya/server/tv.py            Turn viewer data prep and _tv_* helpers
ccya/server/metrics.py       _recent_turn_metrics, _turn_log_entries, fmt helpers
ccya/server/__init__.py      Re-exports: app, main

ccya/rules.py                Deterministic rules: dice roll, bands, MOMENTUM_DELTA — do not merge with engine/rules.py
ccya/models.py               All Pydantic models and load_config
ccya/pack.py                 Pack loading, PlayerOverrides, SeedEnvelope, parse_world_facts
ccya/llm_client.py           LLM HTTP client, chat/chat_stream, thinking helpers, trim_messages
```

---

## Execution Order

Do these in order to keep the codebase working after each step:

1. `state/` split — lowest risk, no engine dependency
   - Create `state/` directory with `__init__.py` re-exporting everything
   - Move functions in this order: inventory → npcs → chronicle → momentum → io → delta
   - Delete old `state.py` after `state/__init__` re-exports pass a smoke test

2. `engine/` split — depends on `state/` being done first
   - Create `engine/` directory
   - Move in order: config → changes → pressure → narrate (+ names) → rules →
     extraction → seed → turn
   - `engine/__init__.py` re-exports must match what `server.py` currently imports
   - Delete old `engine.py` after re-exports pass a smoke test
   - Delete `names.py` (absorbed into `engine/narrate.py`)

3. `server/` split — depends on `engine/` being done
   - Create `server/` directory
   - Move in order: metrics → tv → panels → app → routes
   - `server/__init__.py` re-exports `app` and `main`
   - Update `ccya/__main__.py` if it imports from `server` directly
   - Delete old `server.py`

4. Update REPOMAP.md and AGENTS.md with the new structure (see above sections)

---

## AGENTS.md Guidance to Add

Add a note to AGENTS.md pointing the model to the right submodule for each task type:

```
Turn pipeline questions → engine/turn.py (thin orchestrator) + relevant submodule
Narration/naming questions → engine/narrate.py
Extraction/JSON parse questions → engine/extraction.py
Dice/band/momentum questions → rules.py (deterministic, NOT engine/rules.py)
Rules LLM call questions → engine/rules.py
State mutation questions → state/delta.py
Inventory logic questions → state/inventory.py
NPC compendium questions → state/npcs.py
Save/load questions → state/io.py
Server routes questions → server/routes.py
Debug panel questions → server/panels.py + server/tv.py
New game / seed questions → engine/seed.py
```
