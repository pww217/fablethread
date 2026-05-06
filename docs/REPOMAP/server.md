# server/ — FastAPI routes

## Public APIs

- **`app`** — FastAPI instance.

## Routes

- `GET /` — index page
- `GET /turn?input=` — SSE stream
- `POST /new-game` — static/dynamic seed
- `POST /new-game/reroll` — reroll character generation
- `GET /panels/*` — HTMX fragments
- `GET /turn_viewer` — standalone viewer
- `GET /turn_viewer/data` — JSON
- `GET /turn_viewer/stream` — SSE mtime poll
- `GET /opening` — opening scene
- `GET /healthz` — health check

## Global state

- `_active_pack` (Pack) — in `server/app.py`
- `_pack_id` — in `server/app.py`
- `_dynamic_opening` — in `server/app.py`
- `_dynamic_opening_actions` — in `server/app.py`
- `_ERRORS_LOG` (deque, last 50) — in `server/app.py`

## Internal functions

### server/app.py
- FastAPI `app` instance + middleware/mounts
- Jinja env
- Config bootstrap (EngineConfig, pack loading)
- `_ERRORS_LOG` deque
- `_render()` helper
- Module-level globals: `SAVE_DIR`, `PACKS_DIR`, `_active_pack`, `engine_config`
- `startup_event` / `main()`
- `_validate_stats()`

### server/routes.py
- All `@app.get` / `@app.post` handlers
- Imports from `server/app.py` for shared state, from `server/panels.py` for context,
  from `server/tv.py` for turn viewer data

### server/panels.py
- `_debug_context()`
- `_load_current_state()`
- `_load_recent_history()`
- `_load_last_actions()`
- `_load_rules_map()`
- `_get_opening()`, `_get_opening_actions()`

### server/tv.py
- `_turn_viewer_data()`
- `_tv_parse_json_blob()`
- `_tv_dict_to_lines()`
- `_tv_extract_stream_status()`
- `_tv_narration_lines()`
- `_tv_rules_status()`
- `_STATUS_CSS`, `_STAGE_CSS` constants

### server/metrics.py
- `_recent_turn_metrics()`
- `_turn_log_entries()`
- `_fmt_ms_seconds()`
- `_fmt_tokens()`
- `_fmt_tokens_exact()`
