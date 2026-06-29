# Logging Standards

## Log files

| File | What it has | Rotation |
|---|---|---|
| `logs/game.log` | Game engine logs (all levels from `server.logging.level`) | Yes (5MB, 3 backups) |
| `logs/server.log` | Server HTTP errors (middleware: LlmcTimeout, LlmcRateLimit, LlmcApiError, unhandled) | Yes (5MB, 3 backups) |
| `saves/server_errors.jsonl` | Server HTTP errors (middleware) — kept for turn viewer | No |
| `saves/*/prompts.jsonl` | Per-turn rendered prompts | No (data file) |
| `saves/*/events.jsonl` | Game events (including ruling outcomes) | No (data file) |

`logs/prompts.log` was removed — redundant with per-save `prompts.jsonl` and `events.jsonl`.

## Config keys

```yaml
server:
  logging:
    level: INFO              # File handler level (game.log)
    console_level: INFO      # Console handler level (stdout)
```

Both default to `INFO`. The `CCYA_LOG_LEVEL` env var is no longer supported.

## Log levels

| Level | When to use | Required extra context |
|---|---|---|
| `DEBUG` | Detailed trace: per-step timing, LLM call start/end, token counts, conditional branches, truncation details, silent skips (e.g., inventory target not found) | Pipeline: `trace_id`, `turn` |
| `INFO` | Phase boundaries: pipeline start/end per turn, compaction trigger, state save/load, server startup, state mutations (inventory/condition/location/NPC changes), overdraw clamps | Pipeline: `trace_id`, `turn`; State: `save_dir`; Server: `save`, `turn` |
| `WARNING` | Recoverable anomalies: malformed data skipped, non-critical parse failures, LLM retries, ruling exhaustion | Pipeline: `trace_id`, `turn`, `error_kind`; State: `save_dir`; Server: `save`, `turn`, `error_kind` |
| `ERROR` | Definitive failures: LLM call hard failure, state load failure (missing/empty file), critical parse failures, file I/O failures | Same as WARNING + `exc_info` |
| `EXCEPTION` | Use `_log.exception()` in `except` blocks where we cannot recover | Same as WARNING |

## ErrorKind values

| Kind | Module | Used in |
|---|---|---|
| `LLM_TIMEOUT` | `pipeline.py`, `turn.py`, `seed.py` | `_log.warning` in extraction pipeline and turn processing |
| `TURN_PROCESSING_FAILED` | `pipeline.py`, `turn.py` | `_log.warning` in extraction pipeline and turn processing |
| `PACK_LOAD_FAILED` | `routes.py` | `_log.warning` in server startup |
| `INVENTORY_REMOVE_FAILED` | `delta_builder.py` | `_log.warning` when inventory target not found |
| `INVENTORY_UPDATE_FAILED` | `delta_builder.py` | `_log.warning` when inventory update target not found |
| `INVENTORY_NORMALIZE_FAILED` | `inventory.py` | `_log.warning` when ID normalization fails |
| `STATE_LOAD_FAILED` | `io.py` | `_log.warning` when state file cannot be loaded |
| `SERVER_ERROR` | `app.py` | `_persist_server_error` in server middleware |
| `LLM_RATE_LIMIT` | `app.py` | `_persist_server_error` in server middleware |
| `LLM_API_ERROR` | `app.py` | `_persist_server_error` in server middleware |

**Defined but unused in logging calls:** `INVENTORY_ADD_FAILED`, `DELTA_VALIDATION_FAILED`, `LOCATION_CHANGE_INVALID`, `NPC_SCENE_MANAGEMENT_FAILED`, `THREAD_UPDATE_INVALID`, `ARC_RESOLVE_INVALID`, `THREAD_RESOLVE_INVALID`, `EXTRACTION_CONTEXT_BUILD_FAILED`, `EXTRACTION_COERCION_FAILED`, `FUZZY_MATCH_FAILED`, `NPC_NAME_LOOKUP_FAILED`, `STATE_SAVE_FAILED`, `EVENT_APPEND_FAILED`, `CHRONICLE_APPEND_FAILED`, `RULING_PARSE_FAILED`, `EXTRACTION_PARSE_FAILED`, `PARSE_ERROR`, `VALIDATION_ERROR`, `SEED_GENERATION_FAILED`, `PACK_GENERATION_FAILED`. These are defined in `errors.py` but not referenced in any `_log.warning` or `_log.error` calls.

## SSE error events

`TurnResult.errors` are yielded as `turn_error` SSE events in `routes.py`. Each event includes:
- `error`: Human-readable error message
- `kind`: ErrorKind string constant
- `trace_id`: Trace ID for correlation

See `docs/design/complete/tooling-infra/observability-design.md` for the full design authority on logging and error classification.
