# Plan H — Turn Inspector Debug UI

## Status: Implemented

---

## What This Is

A sidebar debug panel integrated into the main game server that shows a visual breakdown of every turn: timing, token counts, and state changes for each pipeline step. The purpose is to make extraction bugs, prompt bloat, and template regressions visible without reading raw log files.

This is an MVP. Filtering, search, and advanced analysis are out of scope for now.

---

## Architecture

- **Integrated into main game server** — no separate process, no separate port
- **Always available** — no feature flag, no environment variable
- **Reads from `events.jsonl`** — parsed on each panel request (no polling)
- **No database** — `events.jsonl` is the source of truth
- **Jinja2 templates** — `_debug.html` and `_turn_log.html` rendered by the main server, embedded in `index.html` via HTMX
- **Alpine.js + HTMX** — frontend uses Alpine for state management, HTMX for panel loading

---

## Events.jsonl Structure

Each turn event in `events.jsonl` contains these top-level keys:

```python
event = {
    "ts": "2025-...",           # ISO timestamp
    "trace_id": "...",          # UUID
    "turn": 42,                 # turn number
    "input": "...",             # player input
    "applied": {...},           # state delta applied
    "rejected": [...],          # rejected actions
    "actions": [...],           # game actions taken
    "scene_tags": [...],        # scene tags from extraction
    "rules": {...},             # rules call result (see below)
    "narrate": {...},           # narrate metrics (see below)
    "extract": {...},           # extract aggregate metrics
    "extraction": {...},        # per-stream extraction data
    "changes": {...},           # state change summary
    "failed": [...],            # failed streams
}
```

### `rules` event

```python
{
    "intent_verb": "examine",
    "intent": "examine the altar",
    "rolled": True,
    "skill": "lore",
    "difficulty": 3,
    "dice": [4, 6, 2, 1],
    "stat_mod": 2,
    "diff_mod": -1,
    "cond_mod": 0,
    "final_total": 12,
    "band": "success",
    "outcome_summary": "You discern faint runes...",
    "total_ms": 1234.5,
    "tokens_in": 500,
    "tokens_out": 300,
}
```

Non-rolled events omit dice/stat/diff/cond/final/band fields:

```python
{
    "intent_verb": "act",
    "intent": "go north",
    "rolled": False,
    "total_ms": 800.0,
    "tokens_in": 450,
    "tokens_out": 50,
}
```

### `narrate` event

```python
{
    "total_ms": 8500.0,
    "first_token_ms": 1200.0,
    "tokens_in": 5500,
    "tokens_out": 1200,
}
```

### `extract` event (aggregate)

```python
{
    "total_ms": 2100.0,
    "tokens_in": 6000,
    "tokens_out": 400,
    "retries": 0,
}
```

### `extraction` event (per-stream)

```python
{
    "scene": {
        "rendered_system": "...",   # full rendered system prompt
        "rendered_user": "...",     # full rendered user prompt
        "output": {...},            # parsed SceneExtractResult
        "skipped": False,
        "tokens_in": 2100,
        "tokens_out": 800,
        "ms": 520.0,
    },
    "state": {
        "rendered_system": "...",
        "rendered_user": "...",
        "output": {...},
        "skipped": False,
        "tokens_in": 2300,
        "tokens_out": 900,
        "ms": 610.0,
    },
    "progress": {
        "rendered_system": "...",
        "rendered_user": "...",
        "output": {...},
        "skipped": True,
        "tokens_in": 0,
        "tokens_out": 0,
        "ms": 0,
    },
}
```

Skipped streams have `skipped: True` with zeroed tokens and ms. Failed streams have `skipped: False` plus an `error` key.

---

## Server: `ccya/server.py`

Debug panel routes are integrated into the main FastAPI app:

### Routes

- `GET /panels/debug` — renders the debug panel (Jinja2 template)
- `POST /panels/debug/clear-errors` — clears error list, returns updated panel

### Key functions

**`_recent_turn_metrics(save_dir, n=10)`** — parses the last n lines of `events.jsonl`, extracts per-pipeline timing and token data, returns a list of dicts for the debug table. Each dict contains:

```python
{
    "turn": int,
    "trace_id": str,
    "trace_id_full": str,
    "first_s": str,           # narrate first_token_ms formatted
    "narrate_s": str,         # narrate total_ms formatted
    "extract_s": str,         # extract total_ms formatted
    "retries": int,
    "tokens": str,            # legacy combined token display
    "has_rejections": bool,
    "streams": {
        "R_ttft": str,        # rules TTFT (= total_ms, non-streaming)
        "R_tt": str,          # rules total time
        "R_tok": str,         # rules tokens (abbreviated)
        "N_ttft": str,        # narrate first token time
        "N_tt": str,          # narrate total time
        "N_tok": str,         # narrate tokens
        "Sc_ttft": str,       # scene TTFT (= total_ms, non-streaming)
        "Sc_tt": str,         # scene total time
        "Sc_tok": str,        # scene tokens
        "St_ttft": str,       # state TTFT
        "St_tt": str,         # state total time
        "St_tok": str,        # state tokens
        "P_ttft": str,        # progress TTFT
        "P_tt": str,          # progress total time
        "P_tok": str,         # progress tokens
    },
    "total_tt": str,          # summed TT across all steps
    "total_ttft": str,        # summed TTFT across all steps
    "total_tok": str,         # summed tokens (abbreviated)
}
```

**`_turn_log_entries(save_dir, limit=50)`** — builds rows for the Turn Log tab showing state changes per turn.

**`_fmt_ms_seconds(ms)`** — formats milliseconds to `X.Xs` or `X.XXXs`.

**`_fmt_tokens(n)`** — abbreviates token counts: `5451` → `5.45k`, `12000` → `12k`.

---

## UI: `ccya/templates/_debug.html`

Rendered by Jinja2, embedded in `index.html` via HTMX. Two tabs:

### Turns tab

Compact table with 4 columns: **pipe | ttft | tt | tok**

Pipeline steps shown as single letters:
- **R** — rules (Call 0, non-streaming)
- **N** — narrate (Call 1, streaming)
- **Sc** — scene extract (Call 2, non-streaming)
- **St** — state extract (Call 3, non-streaming)
- **P** — progress extract (Call 4, non-streaming)

Each turn has:
- A separator row: `Turn N`
- 5 data rows (R, N, Sc, St, P)
- A total row with summed TT, TTFT, and tokens

TTFT for non-streaming steps equals TT (no separate first-token timestamp). Skipped streams show `—`.

### Log tab

Shows state change summary per turn (inventory additions/removals, condition changes, quest updates).

### Status section

Shows current model name and mock mode status.

### Errors section

Lists any errors from recent turns with a "Clear" button.

---

## Frontend: `ccya/templates/index.html`

### Metrics display in narration window

`_formatMetricsRow(metrics)` formats turn metrics inline in the narration:

```
R 1.2s (500/300) · N 3.4s (5.5k/1.2k) · Sc 0.5s (2.1k/0.8k) · St 0.6s (2.3k/0.9k) · P 0.4s (1.8k/0.7k)
```

### Debug panel loading

HTMX `hx-get="/panels/debug"` loads the debug panel into `#debug-content`.

---

## File Summary

| File | Role |
|------|------|
| `ccya/server.py` | Debug panel routes, `_recent_turn_metrics()`, `_turn_log_entries()`, `_fmt_ms_seconds()`, `_fmt_tokens()` |
| `ccya/engine.py` | Writes `rules` event with `tokens_in`/`tokens_out`; writes `extraction` event with per-stream data |
| `ccya/templates/_debug.html` | Debug panel template (Turns tab, Log tab, Status, Errors) |
| `ccya/templates/_turn_log.html` | Turn Log tab template |
| `ccya/templates/index.html` | `_formatMetricsRow()` for inline metrics in narration |
| `ccya/static/app.src.css` | Debug panel styles (`.debug-turn-table`, `.debug-turn-sep`, `.debug-turn-total`, etc.) |

---

## Checklist

- [x] Add `tokens_in`/`tokens_out` to rules event in engine
- [x] Add per-stream `tokens_in`/`tokens_out`/`ms`/`skipped` to extraction event
- [x] Add `rendered_system`/`rendered_user` to each extraction stream
- [x] Create `_recent_turn_metrics()` in server.py
- [x] Create `_turn_log_entries()` in server.py
- [x] Create `_fmt_tokens()` helper
- [x] Create `_fmt_ms_seconds()` helper
- [x] Create `_debug.html` template with Turns tab (4-column table)
- [x] Create `_turn_log.html` template
- [x] Add `/panels/debug` and `/panels/debug/clear-errors` routes
- [x] Add `_formatMetricsRow()` to index.html for inline metrics
- [x] Add CSS for debug table, turn separators, total row
- [x] All 208 tests pass, lint clean
