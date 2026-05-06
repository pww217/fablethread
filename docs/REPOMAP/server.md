# server.py — FastAPI routes

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

- `_active_pack` (Pack)
- `_pack_id`
- `_dynamic_opening`
- `_dynamic_opening_actions`
- `_ERRORS_LOG` (deque, last 50)

## Internal functions

- `_turn_viewer_data(save_dir)` → `(rows, no_events)` — full turn viewer data from events.jsonl
- `_recent_turn_metrics(save_dir, n)` — debug panel metrics
- `_debug_context()` → dict for panel templates
