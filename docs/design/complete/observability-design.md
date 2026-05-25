# Observability & Logging Standardization — Design Document

## Purpose

This document defines the structured logging, error classification, and observability patterns for ccya. It covers standardizing log output across all modules, introducing typed error kinds that surface in both server logs and the turn viewer, and establishing conventions for what errors must be visible on stdout/stderr versus hidden in JSONL files. Reference: "This document is the design authority for plans implementing logging/observability changes."

## Current State — What Exists

### Logging Infrastructure (`ccya/logging_setup.py`)

- Single `setup_logging(config)` function configures a root `"ccya"` logger with two handlers:
  - **RotatingFileHandler** → JSONL file at `logs/llm-g.log` (5MB × 3 rotations) via `_JsonFormatter`
  - **StreamHandler** → stdout/stderr via plain `%()s` formatter, level defaults to INFO from config

- `_JsonFormatter` writes: `ts`, `level`, `message`, `logger`, optional `trace_id`, optional `exception`. No structured error classification fields.

- `_SseErrorHandler` class exists but is **never instantiated or used** anywhere in the codebase. Dead code.

### Logger Naming (Inconsistent)

| Pattern | Files Using It |
|---|---|
| `_log = logging.getLogger("ccya.engine")` | turn.py, extraction.py, config.py, compactor.py, seed.py, rules.py, pack_gen.py |
| `_log = logging.getLogger(__name__)` | models.py, generate_pack.py (line 16), routes.py lines 344/412, turn.py line 1480 (`_strip_fallback`) |
| `_log = logging.getLogger("ccya.state")` | state/io.py, state/delta.py |
| `_log = logging.getLogger("ccya.eval")` | eval/runner.py, eval/report.py, eval/judge.py, eval/cli.py (lines 41+), eval/architecture_context.py |
| `_log = logging.getLogger("ccya.llm_client")` | llm_client.py line 19 |
| `logger = setup_logging(config)` → used as module global in app.py | server/app.py (`_app_mod.logger`) |

**Problem**: Mixed patterns. Some modules use `"ccya.engine"` prefix while others use `__name__` (which produces `"ccya.engine.turn"`). Server code uses the global logger reference inconsistently — routes create local loggers inline at lines 344 and 412, but other route handlers access `_app_mod.logger`.

### Error Collection & Propagation

**Engine pipeline (`run_turn`):**
- Errors collected as `errors: list[dict[str, Any]]` in turn.py line 741
- Each entry is `{"trace_id": str, "message": str}` — raw string message only
- Sources of errors appended to this list:
  - Extraction pipeline exception (turn.py:1134): `"str(exc)"` as message
  - Delta validation blocking (turn.py:1217-1222): `"Delta validation failed ({N} rejection(s))."`
  - Top-level try/except in run_turn finally block (turn.py:1453-1454)

**Server routes (`routes.py`):**
- `/turn` endpoint catches all exceptions at line 152-154, yields SSE `turn_error` event with `"error": str(e)` — no structured logging of the exception type or traceback beyond `_app_mod.logger.exception("Turn failed")`
- Errors from TurnResult.errors are appended to `_ERRORS_LOG` deque (routes.py:124-125) as raw dicts passed through from engine

**Server app startup (`app.py`):**
- `_ERRORS_LOG: deque[dict[str, Any]] = deque(maxlen=50)` — stores error dicts with `"message"` key only
- Pack load failure (line 38-40): logged via `logger.error()`, then re-raised
- New game generation failures (lines 269, 270): `_app_mod.logger.exception()` + appends to `_ERRORS_LOG`

**Turn viewer (`tv.py`):**
- `_tv_failures(ev, streams)` at line 251 extracts failure signals from a single turn event: top-level error, per-stream LLM errors, retry_errors, and state rejections
- Produces flat list with `{"kind": "top_level_error"|"llm_error"|"retry"|"rejection", "stream": str, "message": str, "attempt": int|None}`
- **Limitation**: Only reads from events.jsonl. Cannot surface server-level errors (pack load failure, new-game generation failure) that don't produce turn events.

### LLM Client (`llm_client.py`)

- `chat()` and `chat_stream()` catch exceptions generically at line 19
- No typed exception classes — all caught as bare `Exception` or re-raised as-is
- Connection timeouts, HTTP errors, JSON parse failures all produce the same untyped exception path

### Error Visibility Convention

**No established convention.** With StreamHandler defaulting to INFO level:
- `_log.warning()` calls appear on stdout/stderr (visible) but are mixed with info messages
- `_log.error()` and `_log.exception()` also visible at INFO level
- No distinction between "operator should see this now" vs "diagnostic, log file only"

### What the Turn Viewer Already Does Well

`tv.py` has robust failure extraction from events.jsonl:
- Per-stream status colors (ok/skipped/retried/rejected/error) via `_STATUS_CSS` and `_STAGE_CSS`
- `_tv_failures()` aggregates all failure signals into a flat list with kind classification
- Token bar visualization, connector diagrams between stages

But it **cannot** surface server-level errors because those never reach events.jsonl.

### Problems with Current State

1. **No error type taxonomy.** All errors are untyped strings in `TurnResult.errors`. No way to count "how many LLM parse failures this session" or filter by category.

2. **Dead code: `_SseErrorHandler`** exists but is never instantiated, registered, or used anywhere. The SSE push mechanism for server-level errors doesn't exist — `_ERRORS_LOG` is read directly in panels/debug context builders and rendered as HTML.

3. **JSONL formatter lacks structured fields.** Missing `error_kind`, `phase`, `turn` (beyond trace_id), `retry_count`. Makes log file analysis require message parsing rather than field filtering.

4. **No FastAPI middleware for unhandled exceptions.** If any route handler raises an exception not caught by its own try/except, it goes to uvicorn's default logging with no structured capture and no SSE push to frontend.

5. **Logger naming inconsistency causes fragmented log output.** `"ccya.engine"` vs `"ccya.engine.turn"` vs `__name__` produces different logger names in JSONL logs, making it impossible to filter by module prefix without regex matching.

6. **Server-level errors don't reach the turn viewer.** `_ERRORS_LOG` is server-scoped and never persisted to events.jsonl or surfaced via SSE push mechanism (which doesn't exist). The turn viewer only sees engine pipeline errors from events.jsonl.

7. **LLM client exceptions are untyped.** Connection timeout, HTTP 503, JSON parse failure — all indistinguishable in logs. No way to implement retry-backoff strategies based on error type.

8. **No stdout/stderr visibility convention.** With INFO-level StreamHandler, every warning and info message appears on the server console mixed together. No pattern for "this must be visible immediately" vs "diagnostic only".

9. **Config validation errors produce unstructured tracebacks.** If `config.py` raises ValueError during startup (e.g., invalid compactor config), it crashes with a Python traceback — no structured error kind, no graceful server message to the user via `_ERRORS_LOG`.

10. **No health telemetry logging.** `/healthz` endpoint checks LLM availability but doesn't log state changes or track historical health in any persistent way.

## Target State — What It Becomes

### Core Changes

#### 1. Error Kind Taxonomy (`ccya/errors.py`)

New module defining all error types as a string-based enum for JSON serialization compatibility:

```
ErrorKind (str constant type):
    # LLM pipeline errors
    "LLM_TIMEOUT"           — request exceeded timeout
    "LLM_HTTP_ERROR"        — non-200 response from LLM server  
    "LLM_PARSE_FAILED"      — JSON parse failure after all retries
    "LLM_CONNECTION_REFUSED"— connection refused by LLM server
    
    # Extraction errors
    "EXTRACTION_SCENE_FAIL"  — scene extraction pipeline exception
    "EXTRACTION_STATE_FAIL"  — state extraction pipeline exception
    "EXTRACTION_PROGRESS_FAIL" — progress extraction pipeline exception
    
    # Validation errors  
    "VALIDATION_REJECTION"   — delta validation rejected operations
    "VALIDATION_ZERO_BALANCE"— inventory item has zero balance on remove
    
    # Server-level errors
    "PACK_LOAD_FAILED"       — pack not found or invalid
    "NEW_GAME_FAILED"        — seed generation failed
    "CONFIG_VALIDATION"      — config.yaml validation error
    
    # Operational signals (not errors, but observable)
    "COMPACTION_RAN"         — chronicle compaction completed
    "CONDITION_EXPIRED"      — PC condition TTL expired
```

Each ErrorKind maps to a default log level and visibility rule:
- **ERROR** kind → always logged at ERROR level, visible on stderr
- **WARNING** kind → logged at WARNING level, visible on stdout (configurable)  
- **INFO** kind → logged at INFO level, file only unless DEBUG mode

#### 2. Structured JSONL Formatter Upgrade (`ccya/logging_setup.py`)

`_JsonFormatter` extended to include these fields when present via `extra`:
```json
{
    "ts": "...",
    "level": "WARNING", 
    "message": "...",
    "logger": "ccya.engine.extraction",
    "trace_id": "a1b2c3d4",
    "error_kind": "LLM_PARSE_FAILED",       // NEW: when present in extra
    "phase": "extract_scene",               // NEW: pipeline stage
    "turn": 47,                              // NEW: turn number
    "retry_count": 3                         // NEW: attempts used
}
```

All new fields are opt-in via `extra` dict — existing log calls without these keys produce identical output. The formatter iterates over all attributes on the log record and includes any that are JSON-serializable primitives (str, int, float, bool). No hardcoded key list — every caller can add structured fields by passing them in `extra={}` without touching the formatter code.

#### 3. Logger Naming Standardization

**Rule**: Every module uses `_log = logging.getLogger(__name__)`. This produces hierarchical names like `"ccya.engine.turn"`, `"ccya.server.routes"` which Python's logger hierarchy handles naturally. The root `"ccya"` logger in `setup_logging()` remains the configuration anchor — all child loggers inherit its handlers and level settings automatically via propagation.

**Exception**: Modules that need a coarser-grained logger for grouping (e.g., compactor.py uses "ccya.engine" prefix to share with other engine modules) may use explicit names, but this should be rare and documented.

#### 4. FastAPI Middleware for Unhandled Exceptions (`ccya/server/app.py`)

New middleware `ExceptionCaptureMiddleware` that:
- Wraps all route handlers in try/except at the middleware level
- Catches any unhandled exception not caught by individual routes
- Logs with structured fields including error_kind, phase="server", and trace_id (generated per-request)
- Pushes to `_ERRORS_LOG` for frontend display via SSE-compatible event format

#### 5. Server Error Persistance & Turn Viewer Enrichment (`ccya/server/app.py`, `ccya/server/tv.py`)

**Server app**: `_ERRORS_LOG` entries enriched with structured fields:
```python
{
    "ts": "...",                    # ISO timestamp  
    "kind": "PACK_LOAD_FAILED",     # ErrorKind string constant
    "message": "Pack 'foobar' not found",
    "trace_id": "",                 # empty for server-level errors
}
```

**Turn viewer**: `_turn_viewer_data()` reads both events.jsonl AND a new `server_errors.jsonl` file in the save directory, merging them into a unified timeline. Server-level errors appear as separate row entries with `"row_kind": "server_error"` alongside turn rows (`"row_kind": "turn"`).

#### 6. LLM Client Typed Exceptions (`ccya/llm_client.py`)

New exception hierarchy:
```python
class LlmcError(Exception):
    """Base for all llm_client exceptions."""
    kind: str = "LLM_ERROR"

class LlmcTimeout(LlmcError):
    kind = "LLM_TIMEOUT"

class LlmcApiError(LlmcError):  
    kind = "LLM_API_ERROR"
    status_code: int
    
class LlmcConnectionRefused(LlmcError):
    kind = "LLM_CONNECTION_REFUSED"

class LlmcParseFailed(LlmcError):
    kind = "LLM_PARSE_FAILED"
```

Each exception type carries its `kind` for structured logging. Catch sites in engine modules use these types to log with appropriate error_kind field. This follows Python's standard pattern where error classification is fixed per subclass, not configurable at instantiation time.


#### 7. Visibility Convention (stdout/stderr vs file-only)

| Level | Default Handler Behavior | When to Use |
|---|---|---|
| **ERROR** | stderr, always visible | Unrecoverable failures: LLM server down, pack load failure, config validation error |
| **WARNING** | stdout, visible unless log level > WARNING | Recoverable issues: extraction retry, delta rejection, compaction skip |
| **INFO** | stdout (configurable), visible at INFO+ | Normal operational events: turn start/complete, pack loaded, model warmup done |
| **DEBUG** | file only | Diagnostic detail: message trimming info, thread advancement counts, dedup redirects |

This replaces the current all-INFO-on-console pattern. The StreamHandler level should default to WARNING (not INFO) so that normal operational chatter doesn't flood the server console during play.

#### 8. Health Telemetry Logging (`ccya/server/app.py`)

On `/healthz` check result:
- If LLM becomes available after being unavailable → log at INFO with `"error_kind": "LLM_RESTORED"`  
- If LLM becomes unavailable → log at ERROR with `"error_kind": "LLM_UNAVAILABLE"`
- Track last health state in server app module global to detect transitions

### Data Flow Diagram

```mermaid
flowchart TD
    subgraph ENGINE["engine pipeline"]
        RULES["Rules/Intent LLM call"]
        NARRATE["Narrate streaming LLM call"]  
        EXTRACT["3x Extraction streams (scene/state/storytell)"]
    end
    
    subgraph SERVER["server layer"]
        ROUTES["@app.get / @app.post handlers"]
        MIDDLEWARE[ExceptionCaptureMiddleware]
        ERRORS_LOG["_ERRORS_LOG deque"]
    end
    
    subgraph PERSISTENCE["persistence"]
        EVENTS["events.jsonl<br>(turn events + server errors)"]
        SERVER_ERRORS["server_errors.jsonl<br>(server-level errors only)"]
    end
    
    subgraph OBSERVABILITY["observability surfaces"]
        JSONL_LOGS["logs/llm-g.log<br>JSONL with structured fields"]
        STDOUT["stdout/stderr<br>warnings + errors visible"]
        TV["turn viewer<br>_tv_failures() enriched"]
        SSE_SVC["SSE turn stream<br>error events to frontend"]
    end
    
    RULES & NARRATE & EXTRACT --> ERRORS_LOG
    ROUTES -. catches unhandled .-> MIDDLEWARE
    MIDDLEWARE --> ERRORS_LOG
    ERRORS_LOG --> EVENTS
    ERRORS_LOG --> SERVER_ERRORS
    ERRORS_LOG --> SSE_SVC
    
    JSONL_LOGS <-. written by _JsonFormatter .- ENGINE & SERVER
    STDOUT <-. StreamHandler WARNING+ .- ENGINE & SERVER  
    TV <-. reads events.jsonl + server_errors.jsonl .- PERSISTENCE
```

## Decision Table

| Decision | What | Why |
|---|---|---|
| ErrorKind as string constants (not Enum) | Use `"LLM_TIMEOUT"` strings instead of Python `Enum` class | TurnResult.errors is `list[dict]`, JSON serializable, and pydantic models use these kinds. String avoids serialization issues with Enum in mixed dict/list contexts. |
| `_log = logging.getLogger(__name__)` everywhere | Standardize all modules to use `__name__` pattern | Python logger hierarchy gives automatic parent-child relationship; `"ccya"` root config propagates to all children naturally. No need for manual prefix strings. |
| StreamHandler defaults to WARNING level | Change default from INFO → WARNING in setup_logging() | Reduces console noise during normal play. Errors and warnings are what operators need on the server console; info/debug belongs in JSONL log file only. |
| `_SseErrorHandler` replaced by direct `_ERRORS_LOG` access | Remove dead `_SseErrorHandler` class entirely | It was never instantiated or used. Frontend reads `_ERRORS_LOG` via panel debug context builders directly — no SSE push mechanism needed for server errors since they're rendered on page load and refreshed via HTMX. |
| Server errors persisted to `server_errors.jsonl` | New file in save directory alongside events.jsonl | Turn viewer needs a source for server-level errors that never produce turn events. Separate file keeps it clean from turn event data. |
| LLM exceptions typed as LlmcError subclasses | Create exception hierarchy in llm_client.py | Enables structured logging with error_kind, allows callers to distinguish timeout vs HTTP error vs connection refused for retry strategy decisions. |
| JSONL formatter adds opt-in fields | Extend `_JsonFormatter` but keep all new fields optional via extra dict | Backward compatible — existing log calls produce identical output. New structured fields appear only when explicitly passed in `extra={}`. No migration needed. |
| Health state transitions logged as events | Log LLM availability changes with error_kind | Enables operators to see "LLM went down at T47, came back up at T52" without parsing raw healthz responses or checking logs continuously. |

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `_SseErrorHandler` class | `ccya/logging_setup.py:60-81` | Dead code — never instantiated, registered, or called anywhere in the codebase |
| `"ccya.engine"` hardcoded logger name | Multiple engine modules (turn.py, extraction.py, config.py, compactor.py, seed.py, rules.py, pack_gen.py) | Replace with `logging.getLogger(__name__)` for proper hierarchy |
| Inline loggers in routes.py (`log = logging.getLogger(__name__)`) | server/routes.py lines 344, 412 | Use module-level `_log` variable instead, consistent with all other modules |
| INFO default on StreamHandler | ccya/logging_setup.py line 37-38 | Change to WARNING level — info messages belong in JSONL log file only |

## What Is Unchanged

- **`_JsonFormatter` base schema** (`ts`, `level`, `message`, `logger`, trace_id, exception) — all existing fields preserved exactly as-is
- **RotatingFileHandler configuration** (5MB × 3 rotations, JSONL format) — unchanged
- **TurnResult.errors structure** in models.py — now includes `"kind"` (ErrorKind constant) alongside `"message"` keys; classification moves from logs-only into the data model for programmatic querying by turn viewer, SSE events, and API consumers
- **`_ERRORS_LOG` deque type and maxlen=50** in app.py — structure enriched but container unchanged
- **Turn viewer `_tv_failures()` function** — existing failure extraction from events.jsonl preserved; server_errors.jsonl read is additive via separate row kind, not a modification of the existing function
- **LLM client `chat()` and `chat_stream()` public API signatures** — exception types change but call sites catch broadly anyway (bare except or generic Exception)
- **Config validation in config.py** — ValueError raises preserved; only logging around them changes to structured format

## Migration Notes

### Phase 1: Foundation (logging_setup + errors module)
1. Create `ccya/errors.py` with ErrorKind constants and LlmcError exception hierarchy
2. Extend `_JsonFormatter` in `logging_setup.py` to include opt-in fields (`error_kind`, `phase`, `turn`, `retry_count`) when present in record extra dict
3. Remove dead `_SseErrorHandler` class from logging_setup.py

### Phase 2: Logger standardization + visibility convention  
4. Replace all `"ccya.engine"` hardcoded logger names with `logging.getLogger(__name__)` across engine modules (7 files)
5. Add module-level `_log = logging.getLogger(__name__)` to server/routes.py, replacing inline loggers at lines 344 and 412
6. Change StreamHandler default level from INFO → WARNING in setup_logging()

### Phase 3: Structured error logging across engine
7. Update all `except Exception as exc:` blocks in engine modules (turn.py, extraction.py, compactor.py, seed.py, rules.py) to include structured fields via extra dict with appropriate ErrorKind
8. Convert `_call_ruling` and `_call_stream` retry logic to use typed LlmcError exceptions from llm_client

### Phase 4: Server middleware + server error persistence
9. Add `ExceptionCaptureMiddleware` to app.py for unhandled exception capture at FastAPI level
10. Enrich `_ERRORS_LOG` entries with structured fields (ts, kind, message) in all append sites
11. Create server_errors.jsonl writer utility and reader helper

### Phase 5: Turn viewer enrichment + health telemetry
12. Extend `_turn_viewer_data()` to read server_errors.jsonl and merge into timeline as `"row_kind": "server_error"` rows  
13. Add health state transition logging in app.py startup event (track LLM availability changes)

## New Model Shapes

### Error Kind Constants (`ccya/errors.py`)

```
ErrorKind = Literal[
    # LLM pipeline errors
    "LLM_TIMEOUT",
    "LLM_HTTP_ERROR", 
    "LLM_PARSE_FAILED",
    "LLM_CONNECTION_REFUSED",
    
    # Extraction errors
    "EXTRACTION_SCENE_FAIL",
    "EXTRACTION_STATE_FAIL",  
    "EXTRACTION_PROGRESS_FAIL",
    
    # Validation errors
    "VALIDATION_REJECTION",
    "VALIDATION_ZERO_BALANCE",
    
    # Server-level errors
    "PACK_LOAD_FAILED",
    "NEW_GAME_FAILED",
    "CONFIG_VALIDATION",
]

# Operational signals (not errors, but observable)  
OperationalKind = Literal[
    "COMPACTION_RAN",
    "CONDITION_EXPIRED", 
    "LLM_RESTORED",
    "LLM_UNAVAILABLE",
]
```

### LLM Client Exceptions (`ccya/llm_client.py`)

```python
class LlmcError(Exception):
    """Base for all llm_client exceptions."""
    kind: str = "LLM_ERROR"
    
class LlmcTimeout(LlmcError):
    kind = "LLM_TIMEOUT"

class LlmcApiError(LlmcError):
    kind = "LLM_HTTP_ERROR"  
    status_code: int
    detail: str | None

class LlmcConnectionRefused(LlmcError):
    kind = "LLM_CONNECTION_REFUSED"

class LlmcParseFailed(LlmcError):
    kind = "LLM_PARSE_FAILED"
```

Each exception type carries its `kind` as a class attribute for structured logging. Catch sites in engine modules use these types to log with appropriate error_kind field. This follows Python's standard pattern where error classification is fixed per subclass, not configurable at instantiation time.

### TurnResult Errors (`ccya/models.py`)

```python
class TurnResult(BaseModel):
    # ... existing fields ...
    errors: list[dict[str, str]] = []  # Each dict has "kind" (ErrorKind constant) + "message"
```

Errors now carry their `kind` field alongside the message. This enables programmatic filtering by error type in the turn viewer, SSE events, and API consumers — structured logging alone is insufficient when you need to query turn result data after processing completes.

### Server Error Log Entry (`server_errors.jsonl`)

Each line is a JSON object:
```json
{
    "ts": "2025-01-15T14:30:00Z",
    "kind": "PACK_LOAD_FAILED", 
    "message": "Pack 'foobar' not found in /path/to/packs",
    "trace_id": ""
}
```

### JSONL Log Record (extended `_JsonFormatter` output)

When structured fields are present via `extra`:
```json
{
    "ts": "2025-01-15T14:30:00.123",
    "level": "WARNING", 
    "message": "extract_scene failed after 3 attempts: No JSON found in response",
    "logger": "ccya.engine.extraction",
    "trace_id": "a1b2c3d4",
    "error_kind": "LLM_PARSE_FAILED",
    "phase": "extract_scene",
    "turn": 47,
    "retry_count": 3
}
```

When no structured fields present (backward compatible):
```json
{
    "ts": "2025-01-15T14:30:00.123", 
    "level": "WARNING",
    "message": "extract_scene failed after 3 attempts: No JSON found in response",
    "logger": "ccya.engine.extraction"
}
```

## Context for Implementing LLMs

Files to read before starting any plan phase. One line per file: what it contains and why it matters.

- **`ccya/logging_setup.py`** — Current logging infrastructure; `_JsonFormatter` and dead `_SseErrorHandler` live here. Must be modified in Phase 1.
- **`ccya/errors.py` (new)** — Will contain ErrorKind constants and LlmcError exception hierarchy. Created in Phase 1.
- **`ccya/llm_client.py:19`** — LLM client with generic Exception handling; needs typed exceptions in Phase 3. Logger at line 19 uses `getLogger(__name__)`.
- **`ccya/engine/turn.py`** — Main pipeline orchestrator; has try/except blocks at lines 741, 840, 1133, 1217, 1453 that collect errors. Logger uses `"ccya.engine"` prefix (Phase 2).
- **`ccya/engine/extraction.py:35`** — Three extraction streams with retry logic; `_call_stream` at line 396 has parse failure handling. Logger uses `"ccya.engine"` prefix (Phase 2+3).
- **`ccya/server/app.py`** — FastAPI app bootstrap, `_ERRORS_LOG`, startup event. Needs middleware and health telemetry in Phase 4+5. Uses global logger reference from setup_logging().
- **`ccya/server/routes.py`** — All HTMX route handlers; `/turn` SSE endpoint at line 81 catches exceptions at line 152. Has inline loggers at lines 344, 412 (Phase 2).
- **`ccya/server/tv.py`** — Turn viewer data preparation with `_tv_failures()` and `_turn_viewer_data()`. Needs server_errors.jsonl reading in Phase 5.
- **`ccya/models.py:13`** — Pydantic models + TurnResult; `TurnResult.errors` is `list[dict]` with `"kind"` + `"message"` keys (updated in Phase 4 to include ErrorKind classification). Logger uses `getLogger(__name__)`.
