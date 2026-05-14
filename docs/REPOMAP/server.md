# server/ — FastAPI routes

## Public APIs

- **`app`** — FastAPI instance.

## Routes

| Route | Method | Handler | Description |
|---|---|---|---|
| `/` | GET | `index()` | Index page with state, history, actions, opening |
| `/turn` | GET | `get_turn()` | SSE stream for turn pipeline (narrative tokens, phases, complete) |
| `/turn/delete` | POST | `delete_last_turn()` | Remove last turn from state, return previous turn's action choices |
| `/turn/retry` | GET | `retry_turn()` | SSE stream for retrying last turn's roll |
| `/new-game` | POST | `new_game()` | Start new game (static seed or dynamic LLM generation) |
| `/new-game/reroll` | POST | `new_game_reroll()` | Re-roll dynamic pack seed |
| `/panels/state` | GET | `panel_state()` | State panel fragment |
| `/panels/state-left` | GET | `panel_state_left()` | Left state panel |
| `/panels/state-right` | GET | `panel_state_right()` | Right state panel |
| `/panels/actions` | GET | `panel_actions()` | Actions panel |
| `/panels/debug` | GET | `panel_debug()` | Debug panel |
| `/panels/debug/clear-errors` | POST | `debug_clear_errors()` | Clear error log |
| `/panels/pack-picker` | GET | `panel_pack_picker()` | Pack selection dropdown |
| `/packs/{pack_id}` | DELETE | `delete_pack()` | Delete a custom/generated pack directory |
| `/panels/char-creation` | GET | `panel_char_creation()` | Character creation form |
| `/panels/world-builder` | GET | `panel_world_builder()` | World builder form (4-step Alpine.js) |
| `/new-game/generate-pack` | POST | `new_game_generate_pack()` | SSE endpoint; streams pack generation events (`phase`, `pack_ready`, `generation_error`); writes to `packs/generated/` |
| `/panels/turn-log` | GET | `panel_turn_log()` | Turn log with change lines |
| `/turn_viewer` | GET | `turn_viewer()` | Standalone turn viewer page |
| `/turn_viewer/data` | GET | `turn_viewer_data()` | Turn viewer JSON data |
| `/turn_viewer/stream` | GET | `turn_viewer_stream()` | SSE mtime polling for turn viewer |
| `/opening` | GET | `opening()` | Opening scene HTML |
| `/healthz` | GET | `healthz()` | LLM health check (mock or live) |

## Global state

- `BASE_DIR`, `REPO_ROOT`, `TEMPLATES_DIR`, `PROMPTS_DIR`, `PACKS_DIR`, `SAVE_DIR` — Path constants (in `server/app.py`)
- `config` — raw config dict (in `server/app.py`)
- `engine_config` — EngineConfig instance (in `server/app.py`)
- `_pack_id` (str) — current pack ID (in `server/app.py`)
- `_active_pack` (Pack) — current pack (in `server/app.py`)
- `_dynamic_opening` (str) — dynamic pack opening narrative (in `server/app.py`)
- `_dynamic_opening_actions` (list[str]) — dynamic pack opening actions (in `server/app.py`)
- `_ERRORS_LOG` (deque, last 50) — in-process errors (in `server/app.py`)
- `_jinja_env` (Environment) — Jinja2 env with autoescape (in `server/app.py`)

## Internal functions

### server/app.py
- `app` — FastAPI instance, created after pack loading
- `BASE_DIR`, `REPO_ROOT`, `TEMPLATES_DIR`, `PROMPTS_DIR`, `PACKS_DIR`, `SAVE_DIR` — Path constants
- `config` — raw config dict from `_load_config()`
- `engine_config` — EngineConfig instance from config.yaml
- `logger` — from `setup_logging()`
- `_jinja_env` — Jinja2 Environment with autoescape + `tojson` filter
- `_render(template_name, context)` → `HTMLResponse` — renders template with context
- `_validate_stats(stats)` → `bool` — validates PC stats (1-4 each, 12-16 total, all 6 skills)
- `startup_event()` — on_event("startup"), runs LLM warmup if configured
- `main()` — uvicorn entry point
- Module-level globals: `config`, `engine_config`, `logger`, `_pack_id`, `_active_pack`, `_dynamic_opening`, `_dynamic_opening_actions`, `_ERRORS_LOG`
- `app.mount("/static", ...)` — serves static files

### server/routes.py
- All `@app.get` / `@app.post` handlers
- Imports from `server/app.py` for shared state, from `server/panels.py` for context,
  from `server/tv.py` for turn viewer data

### server/panels.py
- `_debug_context()` → `dict` — builds debug panel context (errors, turns, mock_mode, state, log flags, log_file)
- `_load_current_state()` → `dict` — loads state from save dir
- `_load_recent_history(save_dir, n=8)` → `list[dict]` — last n turns from chronicle.md with rules map
- `_load_last_actions(save_dir)` → `list[str]` — actions from most recent turn event
- `_get_opening()` → `str` — opening text (dynamic or static pack)
- `_get_opening_actions()` → `list[str]` — opening actions (dynamic or static pack)
- `_load_rules_map(save_dir)` → `dict[int, dict]` — turn→rules map from events.jsonl

### server/tv.py
- `_turn_viewer_data(save_dir)` → `tuple[list[dict], bool]` — builds turn viewer rows from events.jsonl; skips `"kind": "compaction"` lines and emits `row_kind="compaction"` rows with sanitization summary; normal turn rows get `row_kind="turn"`; per-stream metrics from `_STREAMS`; connector segments derived from `sd.inputs`; `prompts` dict keyed by stream name; no named prompt keys (`rules_prompt`, etc.) exist in the row dict
- `_tv_parse_json_blob(raw)` → `dict | None` — parses JSON from string (bare or brace-scan fallback)
- `_tv_dict_to_lines(d, skip_keys, max_str=150)` → `list[dict]` — renders dict as KV lines with smart value formatting
- `_tv_extract_stream_status(name, skipped, error, attempts, rejected)` → `str` — "ok"/"skipped"/"retried"/"rejected"/"error"; NOTE: hardcodes `"state"` stream key for inventory rejection logic (see `_STREAMS` in `tv_mirror.py`)
- `_tv_narration_lines(narr)` → `list[dict]` — chars + text preview for narration
- `_STATUS_CSS` — dict mapping status → CSS class (ok, skipped, retried, rejected, error, neutral)
- `_STAGE_CSS` — dict mapping stage → CSS class (rules, narrate, scene, state, progress)

### server/tv_mirror.py
- `StreamDescriptor` — frozen dataclass: `key`, `label`, `stage_css`, `metrics_path`, `prompt_path`, `output_subkey`, `is_text_output`, `output_is_json_string`, `ms_key`, `inputs`, `skip_token_display`
- `_STREAMS` — authoritative list of all turn-pipeline stages in execution order (5 descriptors: rules, narrate, scene, state, progress)
- `STREAM_BY_KEY` — O(1) lookup dict by stream key
- `_get_nested(d, path)` — resolves dot-separated path into nested dict; returns None if any key missing or intermediate value not a dict
- `metrics_path` and `prompt_path` are separately tracked because `narrate` splits its metrics blob from its prompt blob

### server/metrics.py
- `_recent_turn_metrics(save_dir, n=10)` → `list[dict]` — last n turns from events.jsonl with per-stream metrics (tt, ttft, tokens, rejections); skips `"kind": "compaction"` lines
- `_turn_log_entries(save_dir, limit=50)` → `list[dict]` — turn log rows with change lines and rules data; skips `"kind": "compaction"` lines
- `_fmt_ms_seconds(ms)` → `str` — formats ms as "X.Xs" or "—"
- `_fmt_tokens(n)` → `str` — formats tokens as "123" or "1.23k"
- `_fmt_tokens_exact(n)` → `str` — formats tokens as "1,234" or "—"
