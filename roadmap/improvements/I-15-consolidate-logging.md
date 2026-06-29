---
title: "Consolidate logging: separate game/server logs, configurable console, remove redundant prompts.log"
status: scoping
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-15
labels:
  - logging
  - developer-experience
related:
  - B-14
---

## Problem

Current logging is fragmented and inconsistent:

1. **`logs/game.log`** (rotated) — contains everything: game engine logs + server HTTP errors. File level comes from `config.yaml` but console level is hardcoded to `WARNING` (ignores config entirely).
2. **`logs/prompts.log`** (no rotation) — redundant. Full prompts already stored per-save in `saves/*/prompts.jsonl`. Ruling outcomes already in `saves/*/events.jsonl`.
3. **`saves/server_errors.jsonl`** (no rotation) — server HTTP errors from middleware. Only read by turn viewer. No rotation, tied to save directory.
4. **Console (stdout)** — `ccya` logger uses hardcoded `WARNING` (env var `CCYA_LOG_LEVEL` overrides but undocumented). Uvicorn uses its own defaults. No way to configure from config.

## Plan

### 1. Restructure log files

| File | What it has | Rotation |
|---|---|---|
| `logs/game.log` | Game engine logs (all levels) | Yes (existing) |
| `logs/server.log` | Server HTTP errors (middleware) | Yes (new) |
| `saves/server_errors.jsonl` | Server HTTP errors (middleware) | No — keep for turn viewer |
| `logs/prompts.log` | ~~Remove~~ | — |
| `saves/*/prompts.jsonl` | Per-turn prompts | No — keep (data file) |

### 2. Add config keys

```yaml
server:
  logging:
    level: INFO              # file handler level (was DEBUG)
    console_level: INFO      # NEW: stdout handler level
    log_llm_io: false
    log_prompts: true
```

Both default to `INFO` (currently file is `DEBUG`, console is hardcoded `WARNING`).

### 3. Wire up `logging_setup.py`

- Console handler: use `config.server.logging.console_level` (default `INFO`), not hardcoded env var
- File handler: use `config.server.logging.level` (default `INFO`)
- Remove `CCYA_LOG_LEVEL` env var fallback (undocumented)

### 4. Move server error persistence

- `ccya/server/app.py` middleware: write to **both** `logs/server.log` (rotated, via standard logger) and `saves/server_errors.jsonl` (for turn viewer)
- Use a standard `logging.getLogger("ccya.server")` RotatingFileHandler for `logs/server.log`
- Keep `saves/server_errors.jsonl` persistence for TV compatibility

### 5. Remove `logs/prompts.log`

- Delete `_PROMPTS_LOG_PATH` from `ccya/engine/config.py`
- Delete ruling outcome writer from `ccya/engine/ruling.py`
- Delete `log_prompts` / `log_llm_io` config keys (redundant with per-save data)
- Update `config.yaml` to remove these keys

### 6. Update docs

- `docs/architecture/logging-standards.md` — update file inventory
- `AGENTS.md` — document logging config keys
- `docs/repomap.md` — update logging section

## Files

- `ccya/logging_setup.py` — console handler level, add server.log handler
- `ccya/server/app.py` — middleware writes to both server.log and server_errors.jsonl
- `ccya/engine/config.py` — remove `_PROMPTS_LOG_PATH`, `_log_prompts`, `_log_llm_io`
- `ccya/engine/ruling.py` — remove ruling outcome writer
- `config.yaml` — add `console_level`, change `level` default to `INFO`, remove `log_prompts`/`log_llm_io`
- `ccya/__main__.py` — remove `CCYA_LOG_LEVEL` env var usage if any
- `docs/architecture/logging-standards.md` — update
- `AGENTS.md` — document config
- `docs/repomap.md` — update

## Status

completed
