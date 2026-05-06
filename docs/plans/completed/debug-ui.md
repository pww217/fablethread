# Plan H — Turn Inspector Debug UI

> **Status: COMPLETE.** Archived from `plans/`. All checklist items done.

---

## What This Is

A sidebar debug panel integrated into the main game server that shows a visual breakdown of every turn: timing, token counts, and state changes for each pipeline step.

## Architecture

- Integrated into main game server — no separate process, no separate port
- Reads from `events.jsonl` (parsed on each panel request)
- Jinja2 templates: `_debug.html` and `_turn_log.html`
- Alpine.js + HTMX for frontend state/panel loading

## File Summary

| File | Role |
|------|------|
| `ccya/server.py` | Debug panel routes, `_recent_turn_metrics()`, `_turn_log_entries()`, helpers |
| `ccya/engine.py` | Writes `rules` event with token counts; writes `extraction` event with per-stream data |
| `ccya/templates/_debug.html` | Debug panel template (Turns tab, Log tab, Status, Errors) |
| `ccya/templates/_turn_log.html` | Turn Log tab template |
| `ccya/templates/index.html` | `_formatMetricsRow()` for inline metrics in narration |
| `ccya/static/app.src.css` | Debug panel styles |

## Checklist (all done)

- [x] Add `tokens_in`/`tokens_out` to rules event in engine
- [x] Add per-stream `tokens_in`/`tokens_out`/`ms`/`skipped` to extraction event
- [x] Add `rendered_system`/`rendered_user` to each extraction stream
- [x] Create `_recent_turn_metrics()` in server.py
- [x] Create `_turn_log_entries()` in server.py
- [x] Create `_debug.html` template with Turns tab (4-column table)
- [x] Create `_turn_log.html` template
- [x] Add `/panels/debug` and `/panels/debug/clear-errors` routes
- [x] Add `_formatMetricsRow()` to index.html for inline metrics
- [x] All 208 tests pass, lint clean
