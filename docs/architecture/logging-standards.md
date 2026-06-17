# Logging Standards

## Log levels

| Level | When to use | Required extra context |
|---|---|---|
| `DEBUG` | Detailed trace: per-step timing, LLM call start/end, token counts, conditional branches, truncation details, silent skips (e.g., inventory target not found) | Pipeline: `trace_id`, `turn` |
| `INFO` | Phase boundaries: pipeline start/end per turn, compaction trigger, state save/load, server startup, state mutations (inventory/condition/location/NPC changes), overdraw clamps | Pipeline: `trace_id`, `turn`; State: `save_dir`; Server: `save`, `turn` |
| `WARNING` | Recoverable anomalies: malformed data skipped, non-critical parse failures, deprecated paths, LLM retries, ruling exhaustion | Pipeline: `trace_id`, `turn`, `error_kind`; State: `save_dir`; Server: `save`, `turn`, `error_kind` |
| `ERROR` | Definitive failures: LLM call hard failure, state load failure (missing/empty file), migration failure, critical parse failures, file I/O failures | Same as WARNING + `exc_info` |
| `EXCEPTION` | Use `_log.exception()` in `except` blocks where we cannot recover | Same as WARNING |

## ErrorKind values

| Kind | Module | Description |
|---|---|---|
| `INVENTORY_REMOVE_FAILED` | `delta_builder.py` | Inventory remove target not found |
| `INVENTORY_UPDATE_FAILED` | `delta_builder.py` | Inventory update target not found |
| `INVENTORY_ADD_FAILED` | `delta_builder.py` | Inventory add failed |
| `DELTA_VALIDATION_FAILED` | `delta_builder.py` | Delta validation failed |
| `LOCATION_CHANGE_INVALID` | `delta_builder.py` | Location change invalid |
| `NPC_SCENE_MANAGEMENT_FAILED` | `npcs.py` | NPC scene management failed |
| `THREAD_UPDATE_INVALID` | `turn.py` | Thread update invalid |
| `ARC_RESOLVE_INVALID` | `turn.py` | Arc resolve invalid |
| `THREAD_RESOLVE_INVALID` | `turn.py` | Thread resolve invalid |
| `EXTRACTION_CONTEXT_BUILD_FAILED` | `extraction.py` | Extraction context build failed |
| `EXTRACTION_COERCION_FAILED` | `extraction.py` | Scene JSON coercion failed |
| `INVENTORY_NORMALIZE_FAILED` | `inventory.py` | Inventory ID normalization failed |
| `FUZZY_MATCH_FAILED` | `inventory.py` | Fuzzy match failed |
| `NPC_NAME_LOOKUP_FAILED` | `npcs.py` | NPC name lookup failed |
| `STATE_LOAD_FAILED` | `io.py` | State load failed |
| `STATE_SAVE_FAILED` | `io.py` | State save failed |
| `EVENT_APPEND_FAILED` | `chronicle.py` | Event file append failed |
| `CHRONICLE_APPEND_FAILED` | `chronicle.py` | Chronicle file append failed |
| `RULING_PARSE_FAILED` | `ruling.py` | Ruling LLM parse failed after all retries |
| `EXTRACTION_PARSE_FAILED` | `extraction.py` | Extraction LLM parse failed after all retries |

## SSE error events

`TurnResult.errors` are yielded as `turn_error` SSE events in `routes.py`. Each event includes:
- `error`: Human-readable error message
- `kind`: ErrorKind string constant
- `trace_id`: Trace ID for correlation

See `docs/design/complete/observability-design.md` for the full design authority on logging and error classification.
