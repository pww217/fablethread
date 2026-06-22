# Observability & Logging Standardization

## Status
`completed`
**Created:** 2025-05-18  
**Design doc:** `docs/design/observability-design.md`  

---

## Phases overview

| Phase | Title | What changes | Why this grouping | Max tokens |
|-------|-------|-------------|-------------------|------------|
| 1 | Foundation: ErrorKind + structured formatter | New `ccya/errors.py`, update `_JsonFormatter` in logging_setup.py, add `error_kind`/`phase`/`turn_id` to JSONL output | Single new file + single existing file; all downstream consumers read the same schema | ~20K |
| 2 | Logger standardization + dead code removal | Replace all non-`__name__` loggers with module-level `_log = logging.getLogger(__name__)`, remove `_SseErrorHandler` and `_ERRORS_LOG` deque, fix inline loggers in server routes | All logger changes share the same pattern; no behavioral change so nothing breaks downstream | ~15K |
| 3 | Structured error logging across engine | Replace generic `except Exception` with typed LlmcError hierarchy + ErrorKind fields in pipeline try/except blocks and extraction retry loops | Engine modules all use shared config + llm_client; changes touch the same try/except patterns across turn.py, extraction.py, seed.py, pack_gen.py | ~30K |
| 4 | Server middleware + server_errors.jsonl persistence | Add FastAPI exception handler middleware that catches unhandled exceptions and persists them to `server_errors.jsonl` with ErrorKind enrichment | Single middleware function + single file writer; server app.py wiring only | ~15K |
| 5 | Turn viewer enrichment + health telemetry | Read server_errors.jsonl in turn viewer failure extraction, add health telemetry logging for pack load failures and game generation lifecycle events | Server routes + tv.py share the error reading path; health telemetry uses same ErrorKind schema from Phase 1 | ~20K |

---

## Issue: Observability gaps across ccya codebase

The current logging system has these problems that make debugging, monitoring, and incident response difficult or impossible for server-side failures and LLM errors.

### Problem 1 — No error type taxonomy
All try/except blocks log `str(exc)` as a string with no classification. There is no way to distinguish network timeouts from parse failures from validation errors at query time. ErrorKind enum in new file will provide structured categories: `LLM_TIMEOUT`, `PARSE_ERROR`, `VALIDATION_ERROR`, `PACK_LOAD_FAILED`, etc.

### Problem 2 — Dead `_SseErrorHandler` code
`logging_setup.py` lines 60-81 define `_SseErrorHandler` which is never instantiated or referenced anywhere in the codebase. This dead code should be removed entirely.

### Problem 3 — Inconsistent logger naming across engine modules
7+ engine modules use `logging.getLogger("ccya.engine")` instead of module-level `__name__`. This prevents filtering by specific sub-module and breaks standard Python logging hierarchy. All modules should use `_log = logging.getLogger(__name__)` pattern.

### Problem 4 — JSONL formatter lacks structured fields
Current `_JsonFormatter` only outputs timestamp, level, message, logger name. Missing: `error_kind`, `phase`, `turn_id`, `trace_id` as top-level JSON keys for programmatic querying. The formatter should include all `extra` dict entries as flat JSON keys automatically.

### Problem 5 — No FastAPI middleware for unhandled exceptions
Server routes have try/except blocks but any exception that escapes them (e.g., in SSE streaming, WebSocket handlers) produces raw HTML error pages and never reaches the structured log files or turn viewer. A global exception handler middleware is needed.

### Problem 6 — Server-level errors don't reach turn viewer
`server/app.py` lines 32-40 maintain `_ERRORS_LOG` deque(maxlen=50) for server errors but this data only exists in memory and never persists to disk or enriches the turn viewer UI. Errors should be persisted to a separate `server_errors.jsonl` file alongside events.jsonl.

### Problem 7 — LLM client exceptions are untyped
`llm_client.py` line 19 catches generic `Exception` with no type distinction between connection errors, timeouts, rate limits, and API errors. A typed LlmcError exception hierarchy will allow callers to distinguish retryable vs non-retryable failures.

### Problem 8 — INFO-level StreamHandler floods server console
StreamHandler default level is INFO which produces excessive output during normal server operation (every LLM request/response log, every pipeline phase). Should be WARNING by default for production use.

---

## Solution: Five-phase implementation

Each phase must be independently executable with no prior context needed beyond what's in its section below. Phases share concerns through the ErrorKind taxonomy and structured formatter established in Phase 1.

### Firm decisions
- **ErrorKind uses string constants** (not Python Enum class) — avoids JSON serialization issues in mixed dict/list contexts like TurnResult.errors, matches existing pattern of using strings for error categories throughout the codebase
- **All modules standardize on `logging.getLogger(__name__)`** — proper logger hierarchy via `"ccya"` root anchor enables fine-grained filtering (e.g., log level per module) while maintaining shared formatter config from logging_setup.py
- **StreamHandler default level changes to WARNING** — reduces server console noise during play; INFO-level remains available via `--debug` flag or env var override for development
- **`_SseErrorHandler` dead code removed entirely** — never instantiated, never referenced in any file across the entire codebase. No migration path needed.
- **Server errors persisted to new `server_errors.jsonl` file** alongside events.jsonl for turn viewer enrichment; separate file avoids mixing server lifecycle errors with game event data

### Non-goals (explicitly excluded)
- No distributed tracing integration (OpenTelemetry, Jaeger, etc.) — out of scope for this iteration
- No log aggregation pipeline changes (ELK, Datadog, CloudWatch) — assume consumers read JSONL files directly
- No changes to prompt template rendering or Jinja2 logging behavior
- No real-time alerting or metric export — telemetry is logged-only

### Risks, Ambiguities & Blockers
- **Risk:** Changing StreamHandler default from INFO to WARNING may hide useful debug output during development. Mitigation: add `CCYA_LOG_LEVEL` env var override with default "WARNING" for prod and "INFO" when running locally via docker-compose or dev scripts.
- **Ambiguity:** ErrorKind values should be UPPER_SNAKE_CASE strings matching the existing pattern in server/app.py (`PACK_LOAD_FAILED`). New values need to cover all exception types across engine modules without being overly granular.
- **Blocker:** None identified — phases are self-contained and can proceed sequentially.

---

## Phase 1: Foundation — ErrorKind + structured formatter

**What changes:** Create new `ccya/errors.py` with ErrorKind string constants and LlmcError exception hierarchy. Update `_JsonFormatter` in logging_setup.py to include all extra dict entries as flat JSON keys. Remove dead `_SseErrorHandler` class. Change StreamHandler default level from INFO to WARNING.

### Context files to load
- `ccya/errors.py` — **new file** (create)
- `ccya/logging_setup.py` — modify lines 26-41 (`_JsonFormatter`) and lines 60-81 (`_SseErrorHandler`), line 37 (StreamHandler level)

### Detailed steps

#### Step 1.1: Create `ccya/errors.py` with ErrorKind constants and LlmcError hierarchy
**File:** `ccya/errors.py` — **What:** Create new file  
**Why:** Provides structured error classification for all try/except blocks across engine modules; replaces untyped string logging with categorized errors

```python
"""Structured error types and exception hierarchy for ccya."""

from __future__ import annotations


# ErrorKind: string constants matching existing server/app.py pattern.
# Using strings (not Enum) avoids JSON serialization issues in mixed dict/list contexts like TurnResult.errors.
class ErrorKind:
    # LLM-related errors
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_API_ERROR = "LLM_API_ERROR"

    # Parsing/validation errors
    PARSE_ERROR = "PARSE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Pack/game lifecycle errors
    PACK_LOAD_FAILED = "PACK_LOAD_FAILED"
    SEED_GENERATION_FAILED = "SEED_GENERATION_FAILED"
    PACK_GENERATION_FAILED = "PACK_GENERATION_FAILED"

    # Server/runtime errors
    SERVER_ERROR = "SERVER_ERROR"
    TURN_PROCESSING_FAILED = "TURN_PROCESSING_FAILED"


class LlmcError(Exception):
    """Typed exception hierarchy for LLM client failures.

    Each subclass carries its kind as a class attribute, following Python's standard pattern
    where error classification is fixed per type (e.g., StopIteration, ValueError).
    Callers can distinguish retryable vs non-retryable failures:
    - Retryable: LlmcTimeout, LlmcRateLimit
    - Non-retryable: LlmcApiError (e.g., 400/500 from provider)
    """

    kind: str = "LLM_ERROR"
    retryable: bool = False
    status_code: int | None = None


class LlmcTimeout(LlmcError):
    kind = ErrorKind.LLM_TIMEOUT
    retryable = True


class LlmcRateLimit(LlmcError):
    kind = ErrorKind.LLM_RATE_LIMIT
    retryable = True
    status_code = 429


class LlmcApiError(LlmcError):
    """API error with dynamic HTTP status code from the provider response."""
    kind = ErrorKind.LLM_API_ERROR
    retryable = False

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

```python
# In _JsonFormatter.to_json(), add extra fields as top-level keys:
def to_json(self, record):
    base = {
        "ts": self._format_ts(record),
        "level": record.levelname,
        "msg": self.getMessage(record),
        "logger": record.name,
    }
    # Include any JSON-serializable primitive attributes as top-level keys for programmatic querying.
    # No hardcoded key list — every caller can add structured fields via extra={} without touching the formatter.
    for attr in dir(record):
        if not attr.startswith("_"):
            val = getattr(record, attr)
            if isinstance(val, (str, int, float, bool)):
                base[attr] = val
    return json.dumps(base, default=str)
```

**Why:** Enables querying log files by structured fields like `error_kind` and `phase` without parsing message strings. The opt-in extra dict pattern scales without code changes — every caller can pass additional keys in `extra={}` and they automatically appear as JSON keys in the output. Matches design doc's extensible approach over a hardcoded key list.

#### Step 1.3: Remove dead `_SseErrorHandler` class entirely
**File:** `ccya/logging_setup.py` lines 60-81  
**What:** Delete the entire `_SseErrorHandler` class definition and any references to it in `_setup_logging()` function  
**Why:** Never instantiated or referenced anywhere in the codebase; dead code removal reduces maintenance burden

#### Step 1.4: Change StreamHandler default level from INFO to WARNING
**File:** `ccya/logging_setup.py` line ~37 (where StreamHandler is configured)  
**What:** Change `handler.setLevel(logging.INFO)` to `handler.setLevel(logging.WARNING)` in `_setup_logging()` function  
**Why:** Reduces server console noise during normal operation; INFO-level remains available via env var override

```python
# In _setup_logging():
stream_handler = logging.StreamHandler()
stream_handler.setLevel(os.getenv("CCYA_LOG_LEVEL", "WARNING"))  # Changed from logging.INFO
formatter = _JsonFormatter()
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)
```

**Validation:** Run server and verify console only shows WARNING+ messages. Verify JSONL log files contain all structured fields (error_kind, phase, turn_id, trace_id, pack) when present in log calls.

### Tests to write/update
- Unit test for ErrorKind constants: verify all expected string values exist and are unique
- Unit test for LlmcError hierarchy: verify kind, retryable flag, and status_code are correct class attributes on each subclass (LlmcTimeout, LlmcRateLimit, LlmcApiError)
- Verify `_JsonFormatter.to_json()` output includes extra fields as top-level JSON keys when present in log record

### REPOMAP updates required
Update `docs/repomap.md` "ccya.errors module" section with new ErrorKind constants list and LlmcError exception hierarchy. Add to "structured logging pipeline" diagram showing ErrorKind → _JsonFormatter → server_errors.jsonl flow.

---

## Phase 2: Logger standardization + dead code removal

**What changes:** Replace all non-`__name__` loggers with module-level `_log = logging.getLogger(__name__)`. Remove any remaining inline logger definitions in server routes. No behavioral change — only naming consistency and hierarchy improvement.

### Context files to load
- `ccya/engine/turn.py` line 70: `_log = logging.getLogger("ccya.engine")` → `_log = logging.getLogger(__name__)`
- `ccya/engine/extraction.py` line ~25: same pattern
- `ccya/engine/config.py` line ~15: same pattern  
- `ccya/engine/seed.py` line 63: `_log = logging.getLogger("ccya.engine")` → `_log = logging.getLogger(__name__)`
- `ccya/engine/pack_gen.py` line 20: `_log = logging.getLogger("ccya.engine")` → `_log = logging.getLogger(__name__)`
- `ccya/server/app.py` lines ~15, ~30: same pattern + remove `_ERRORS_LOG` deque (moved to Phase 4 persistence)
- `ccya/server/routes.py` lines 344, 412: inline logger definitions → use module-level `_log = logging.getLogger(__name__)`

### Detailed steps

#### Step 2.1: Replace all non-`__name__` loggers with module-level pattern
**Files:** All engine modules + server modules listed above  
**What:** Change every occurrence of `logging.getLogger("ccya.engine")`, `logging.getLogger("ccya.server.app")`, etc. to `_log = logging.getLogger(__name__)` at the top of each file (after imports, before first function/class)

```python
# Before:
_log = logging.getLogger("ccya.engine")

# After:
_log = logging.getLogger(__name__)
```

**Why:** Enables fine-grained log filtering by module name while maintaining shared formatter config from `"ccya"` root anchor in logging_setup.py. Standard Python logging best practice.

#### Step 2.2: Remove inline logger definitions in server routes
**File:** `ccya/server/routes.py` lines ~340-350 and ~410-420  
**What:** Replace any `_log = logging.getLogger(...)` or similar inline logger creation inside route handler functions with a single module-level `_log = logging.getLogger(__name__)` at the top of the file

```python
# Before (inline in function):
def handle_turn():
    _log = logging.getLogger("ccya.server.routes")  # Remove this line
    try:
        ...
    except Exception as exc:
        _log.error(...)

# After:
_log = logging.getLogger(__name__)  # At top of file, after imports

async def handle_turn():
    try:
        ...
    except Exception as exc:
        _log.error("turn failed", extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED})
```

**Why:** Inline loggers create new logger instances per call (wasteful), break logging hierarchy, and prevent formatter config from applying consistently. Module-level single instance is the standard pattern.

#### Step 2.3: Remove `_ERRORS_LOG` deque from server/app.py
**File:** `ccya/server/app.py` lines ~15-40  
**What:** Delete `_errors_log = deque(maxlen=50)` and all references to it in pack load failure logging and new-game generation error handling

```python
# Remove these lines entirely:
_errors_log = deque(maxlen=50)  # line ~32

# And remove this pattern from pack loading:
_errors_log.append(str(exc))  # wherever used
```

**Why:** Error persistence is handled by Phase 4 middleware writing to server_errors.jsonl. The in-memory deque is redundant and will be replaced with structured file-based logging.

#### Step 2.4: Verify all modules use `_log = logging.getLogger(__name__)` pattern
**What:** Search entire codebase for any remaining `logging.getLogger("ccya.` patterns that are not `"ccya"` root anchor in logging_setup.py  
**Why:** Ensures complete standardization; any remaining non-`__name__` loggers will break the hierarchy

```bash
# Verification command:
grep -rn 'getLogger("' ccya/ --include="*.py" | grep -v '__name__' | grep -v logging_setup.py
```

**Validation:** Run server and verify all log entries show correct module names in `"logger"` field of JSONL output (e.g., `"ccya.engine.turn"`, `"ccya.server.routes"`). Verify no duplicate or inconsistent logger instances exist.

### Tests to write/update
- No new tests needed — this is a pure naming/hierarchy change with no behavioral impact
- Manual verification: check log file entries show correct module names in `logger` field

### REPOMAP updates required
Update "Logger standardization" section in repomap.md showing all modules now use `_log = logging.getLogger(__name__)` pattern. Remove any references to old `"ccya.engine"` or `"ccya.server.app"` logger naming conventions.

---

## Phase 3: Structured error logging across engine

**What changes:** Replace generic `except Exception` blocks with typed LlmcError exceptions from llm_client.py and ErrorKind-enriched log calls in pipeline try/except blocks (turn.py), extraction retry loops (extraction.py), seed generation (seed.py), and pack generation (pack_gen.py).

### Context files to load
- **New:** `ccya/errors.py` — imported for ErrorKind constants and LlmcError types from Phase 1
- **Modify:** `ccya/llm_client.py` line ~19: wrap generic Exception with typed LlmcError subclasses
- **Modify:** `ccya/engine/turn.py` lines 74, 353, 840, 1133, 1217, 1453: pipeline try/except blocks — add ErrorKind fields to log calls and convert generic exceptions to structured logging
- **Modify:** `ccya/engine/extraction.py` lines 396, 434, 523, 563, 622: three extraction streams with retry logic — use LlmcError types for LLM failures, ErrorKind.PARSE_ERROR and ErrorKind.VALIDATION_ERROR for parse/validation blocks
- **Modify:** `ccya/engine/seed.py` lines 197-203, 238-245: generate_seed() try/except — use LlmcError types + ErrorKind.SEED_GENERATION_FAILED
- **Modify:** `ccya/engine/pack_gen.py` lines 107-109, 134-136: generate_pack() try/except — use LlmcError types + ErrorKind.PACK_GENERATION_FAILED

### Detailed steps

#### Step 3.1: Update llm_client.py to raise typed LlmcError exceptions
**File:** `ccya/llm_client.py`  
**What:** Replace generic `except Exception as exc:` with specific exception type detection and LlmcError subclass raising

```python
# In chat() function, around line 19 (existing try/except):
from ccya.errors import LlmcTimeout, LlmcRateLimit, LlmcApiError, ErrorKind

try:
    # ... existing LLM API call code ...
except TimeoutError as exc:
    raise LlmcTimeout(f"LLM request timed out after {timeout}s") from exc
except httpx.HTTPStatusError as exc:
    if exc.response.status_code == 429:
        raise LlmcRateLimit(f"Rate limited by LLM provider") from exc
    else:
        raise LlmcApiError(
            f"LLM API error {exc.response.status_code}: {exc.response.text}",
            status_code=exc.response.status_code,
        ) from exc
except httpx.RequestError as exc:
    raise LlmcTimeout(f"Network error connecting to LLM: {exc}") from exc
```

Note: `LlmcRateLimit` has fixed `status_code = 429` as a class attribute. `LlmcApiError` accepts an optional `status_code=` constructor parameter for dynamic HTTP status codes, since API errors can vary by response code while rate limits are always 429.
**Why:** Callers can now distinguish retryable vs non-retryable failures; structured logging in upstream modules will have access to ErrorKind via `exc.kind` attribute.

#### Step 3.2: Update pipeline try/except blocks in turn.py with ErrorKind fields
**File:** `ccya/engine/turn.py`  
**What:** Add ErrorKind import and enrich all existing log calls in try/except blocks at lines 74, 353, 840, 1133, 217, 1453 with structured error_kind fields

```python
# At top of file (after imports):
from ccya.errors import ErrorKind

# In pipeline try/except blocks — add extra dict to existing log calls:
try:
    # ... phase processing code ...
except LlmcTimeout as exc:
    _log.error(
        "LLM timeout in %s", phase_name,
        extra={"error_kind": ErrorKind.LLM_TIMEOUT, "turn_id": turn_id},
    )
    result.errors.append({"kind": ErrorKind.LLM_TIMEOUT, "message": str(exc)})
except LlmcRateLimit as exc:
    _log.error(
        "LLM rate limit in %s", phase_name,
        extra={"error_kind": ErrorKind.LLM_RATE_LIMIT, "turn_id": turn_id},
    )
    result.errors.append({"kind": ErrorKind.LLM_RATE_LIMIT, "message": str(exc)})
except Exception as exc:
    _log.error(
        "%s failed in %s", type(exc).__name__, phase_name,
        extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "turn_id": turn_id},
    )
    result.errors.append({"kind": ErrorKind.TURN_PROCESSING_FAILED, "message": str(exc)})
```

**Why:** Pipeline errors now have structured classification; TurnResult.errors uses dict with `kind` field matching ErrorKind constants (string-based, not Enum class). Enables querying log files by error type and turn_id.

#### Step 3.3: Update extraction retry loops in extraction.py with typed exceptions
**File:** `ccya/engine/extraction.py`  
**What:** Replace generic exception handling at lines 396, 434, 523, 563, 622 with LlmcError types for LLM failures and ErrorKind.PARSE_ERROR/ErrorKind.VALIDATION_ERROR for parse/validation blocks

```python
# At top of file:
from ccya.errors import ErrorKind, LlmcTimeout, LlmcRateLimit, LlmcApiError

# In extraction retry loop (e.g., around line 396):
for attempt in range(1 + max_retries):
    try:
        result = await llm_chat(config.host, config.model, messages, ...)
    except LlmcTimeout as exc:
        _log.warning("extraction LLM timeout (attempt %d)", attempt + 1, extra={"error_kind": ErrorKind.LLM_TIMEOUT})
        if attempt < max_retries:
            continue
        raise
    except LlmcRateLimit as exc:
        _log.error("extraction rate limited", extra={"error_kind": ErrorKind.LLM_RATE_LIMIT})
        break  # Non-retryable after single occurrence
    
    raw = result.get("response", "") if isinstance(result, dict) else ""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    
    if j is None:
        parse_error = "No JSON found in extraction response"
        _log.warning(
            "extraction parse failed (attempt %d): %s", attempt + 1, parse_error,
            extra={"error_kind": ErrorKind.PARSE_ERROR},
        )
        if attempt < max_retries:
            messages.append({"role": "user", "content": f"Output failed to parse. Re-emit valid JSON."})
            continue
    
    try:
        scene = SceneState(**j)  # or whatever extraction target type
    except Exception as exc:
        validation_error = str(exc)[:300]
        _log.warning(
            "extraction validation failed (attempt %d): %s", attempt + 1, validation_error,
            extra={"error_kind": ErrorKind.VALIDATION_ERROR},
        )
```

**Why:** Three extraction streams share the same retry pattern; typed exceptions allow distinguishing LLM network issues from JSON parse failures vs Pydantic validation errors. Each has different retry semantics (timeout = retry, rate limit = stop early, parse error = feedback + retry).

#### Step 3.4: Update seed.py and pack_gen.py with ErrorKind fields
**File:** `ccya/engine/seed.py` lines ~197-203, ~238-245  
**What:** Add ErrorKind import; enrich LLM error log call at line 198-202 and validation failure log at line 240-244 with structured fields

```python
# At top of file:
from ccya.errors import ErrorKind, LlmcTimeout, LlmcRateLimit, LlmcApiError

# In generate_seed() LLM call try/except (around line 197):
try:
    result = await llm_chat(config.host, config.model, messages, ...)
except LlmcTimeout as exc:
    _log.error(
        "generate_seed: LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
    )
    raise
# ... similar for rate limit and API errors

# In validation try/except (around line 238):
try:
    envelope = SeedEnvelope(**j)
    # ... sanitization and validation ...
except Exception as exc:
    parse_error = str(exc)[:300]
    _log.warning(
        "generate_seed validation failed (attempt %d): %s", attempt + 1, parse_error,
        extra={"error_kind": ErrorKind.VALIDATION_ERROR, "trace_id": trace_id},
    )
```

**File:** `ccya/engine/pack_gen.py` lines ~107-109, ~134-136  
**What:** Same pattern as seed.py — add ErrorKind import and enrich log calls with structured fields

```python
# At top of file:
from ccya.errors import ErrorKind, LlmcTimeout, LlmcRateLimit, LlmcApiError

# In generate_pack() LLM call try/except (around line 107):
try:
    result = await llm_chat(config.host, config.model, messages, ...)
except LlmcTimeout as exc:
    _log.error(
        "generate_pack: LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
    )
    raise

# In validation try/except (around line 134):
try:
    scenario = ScenarioBrief(**j)
except Exception as exc:
    parse_error = str(exc)[:300]
    _log.warning(
        "generate_pack validation failed (attempt %d): %s", attempt + 1, parse_error,
        extra={"error_kind": ErrorKind.VALIDATION_ERROR, "trace_id": trace_id},
    )
```

**Why:** Seed and pack generation share the same retry pattern with LLM call → JSON parse → validation flow. Structured logging enables distinguishing between network failures (retryable), rate limits (stop early), and schema mismatches (feedback + retry).

#### Step 3.5: Update TurnResult.errors to use dict with kind field
**File:** `ccya/models.py` — check existing TurnResult definition  
**What:** If errors field uses simple list of strings, change to list of dicts with `kind` and `message` fields matching ErrorKind constants

```python
# models.py — verify/update TurnResult:
class TurnResult(BaseModel):
    # ... existing fields ...
    errors: list[dict[str, str]] = []  # Each dict has "kind" (ErrorKind constant) + "message"
```

**Why:** ErrorKind uses string constants (not Enum class), so `{"kind": "LLM_TIMEOUT", "message": "..."} serializes correctly to JSON without any serialization issues. Matches the design doc decision for string-based error taxonomy.

### Tests to write/update
- Unit test LlmcTimeout/LlmcRateLimit/LlmcApiError instances verify kind, retryable flag, and status_code class attributes match ErrorKind constants
- Verify extract_scene() retry loop correctly distinguishes LlmcTimeout (continue), LlmcRateLimit (break), and parse errors (feedback + continue) in mock scenarios
- Verify generate_seed() and generate_pack() log calls include error_kind field when LLM timeout occurs

### REPOMAP updates required
Update "5-call pipeline section" in repomap.md to show ErrorKind enrichment at each try/except boundary. Update "extraction field routing section" with LlmcError exception flow through three extraction streams. Add new row for llm_client.py showing typed exception raising pattern.

---

## Phase 4: Server middleware + server_errors.jsonl persistence

**What changes:** Create FastAPI exception handler middleware that catches any unhandled exceptions in server routes and persists them to `server_errors.jsonl` with ErrorKind enrichment. Remove remaining `_ERRORS_LOG` deque references from app.py.

### Context files to load
- **Modify:** `ccya/server/app.py`: add middleware registration, remove `_ERRORS_LOG` deque wiring
- **New/modify:** Create server error persistence utility (can be inline in app.py or separate file) — writes structured JSONL entries with ErrorKind fields
- **Import:** `ccya/errors.ErrorKind` and LlmcError types from Phase 1+3

### Detailed steps

#### Step 4.1: Create server error persistence function
**File:** `ccya/server/app.py` (or new file `ccya/server/errors.py`)  
**What:** Add `_persist_server_error()` function that writes structured JSONL entries to `{data_dir}/server_errors.jsonl` with ErrorKind classification

```python
# In app.py or server/errors.py:
import json
from datetime import datetime, timezone
from pathlib import Path
from ccya.errors import ErrorKind, LlmcError

_ERRORS_FILE = None  # Set during startup from config


def _ensure_errors_file(data_dir: str) -> Path:
    global _ERRORS_FILE
    if _ERRORS_FILE is None:
        path = Path(data_dir) / "server_errors.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        _ERRORS_FILE = path
    return _ERRORS_FILE


def _persist_server_error(exc: Exception, *, kind: str | None = ErrorKind.SERVER_ERROR, **extra_fields):
    """Persist a server-level error to server_errors.jsonl for turn viewer enrichment."""
    errors_file = _ensure_errors_file(_data_dir)  # Set from app startup config
    
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "error_kind": kind,
        "message": str(exc),
        **extra_fields,
    }
    
    with open(errors_file, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# In FastAPI app startup (on_event replacement using lifespan):
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _data_dir  # Set from config/env
    yield
```

**Why:** Separate server_errors.jsonl file avoids mixing server lifecycle errors with game event data in events.jsonl. JSONL format matches existing logging infrastructure for consistency and easy querying.

#### Step 4.2: Create FastAPI middleware to catch unhandled exceptions
**File:** `ccya/server/app.py`  
**What:** Add middleware that wraps all route handlers, catches any exception that escapes them, persists via `_persist_server_error()`, and returns appropriate HTTP error response

```python
# In app.py — add middleware before routes:
from fastapi import Request, Response
from fastapi.responses import JSONResponse


@app.middleware("http")
async def server_exception_middleware(request: Request, call_next):
    """Catch any unhandled exception in route handlers and persist to server_errors.jsonl."""
    try:
        response = await call_next(request)
        return response
    except LlmcTimeout as exc:
        _persist_server_error(exc, kind=ErrorKind.LLM_TIMEOUT, path=str(request.url.path))
        return JSONResponse(status_code=504, content={"error": "LLM timeout"})
    except LlmcRateLimit as exc:
        _persist_server_error(exc, kind=ErrorKind.LLM_RATE_LIMIT, path=str(request.url.path))
        return JSONResponse(status_code=429, content={"error": "Rate limited by LLM provider"})
    except LlmcApiError as exc:
        _persist_server_error(
            exc, kind=ErrorKind.LLM_API_ERROR, 
            path=str(request.url.path), status_code=exc.status_code,
        )
        return JSONResponse(status_code=502 if exc.status_code else 500, content={"error": str(exc)})
    except Exception as exc:
        _persist_server_error(
            exc, kind=ErrorKind.SERVER_ERROR, 
            path=str(request.url.path), exception_type=type(exc).__name__,
        )
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

**Why:** Single middleware catches all exceptions that escape individual route handlers. Prevents raw HTML error pages from being sent to clients. All server errors are persisted for turn viewer enrichment and post-incident analysis.

#### Step 4.3: Remove `_ERRORS_LOG` deque references from app.py
**File:** `ccya/server/app.py`  
**What:** Delete all remaining references to `_errors_log` deque that were not removed in Phase 2 (if any survived). The middleware now handles persistence via server_errors.jsonl

```python
# Remove these entirely:
_errors_log = deque(maxlen=50)  # if still present from Phase 2 oversight

# And replace this pattern:
_errors_log.append(str(exc))  # wherever it appears

# With the new structured logging:
from ccya.errors import ErrorKind, LlmcError
# The middleware will catch and persist automatically; explicit calls use _persist_server_error()
```

**Why:** Eliminates redundant in-memory error tracking. server_errors.jsonl provides persistent, queryable record of all server errors with structured fields from Phase 1 formatter.

#### Step 4.4: Wire middleware into FastAPI app lifecycle
**File:** `ccya/server/app.py`  
**What:** Ensure the exception middleware is registered before any route handlers and that `_data_dir` config value is available to `_ensure_errors_file()` during server startup

```python
# In app.py — order matters: middleware must be added BEFORE routes
app = FastAPI()

# Register middleware early (before @app.get/@app.post decorators)
@app.middleware("http")
async def server_exception_middleware(request, call_next):
    # ... middleware code from Step 4.2 ...

# Routes come after middleware registration
@app.get("/turn/{pack_id}/{turn_number}")
async def get_turn(...):
    # ... existing route handler code ...
```

**Why:** FastAPI processes middleware in LIFO order (last registered = first executed). Registering exception middleware before routes ensures it wraps all handlers. `_data_dir` must be set during app startup so server_errors.jsonl path is known when middleware runs.

### Tests to write/update
- Unit test `_persist_server_error()` writes correct JSONL entry with ErrorKind field and timestamp to server_errors.jsonl file
- Integration test: verify FastAPI middleware catches LlmcTimeout and returns 504 status code while persisting error to server_errors.jsonl
- Verify middleware catches generic Exception and persists with kind=ErrorKind.SERVER_ERROR

### REPOMAP updates required
Update "server app.py section" in repomap.md showing new `_persist_server_error()` function, FastAPI middleware registration order, and server_errors.jsonl persistence flow. Add note that `_ERRORS_LOG` deque has been replaced by file-based persistence.

---

## Phase 5: Turn viewer enrichment + health telemetry

**What changes:** Read server_errors.jsonl in turn viewer failure extraction (tv.py) to enrich error display with ErrorKind classification and structured metadata. Add health telemetry logging for pack load failures and game generation lifecycle events using ErrorKind constants from Phase 1.

### Context files to load
- **Modify:** `ccya/server/tv.py` lines ~263, ~251: turn viewer failure extraction — add server_errors.jsonl reading alongside existing events.jsonl parsing
- **Modify:** `ccya/server/app.py`: add health telemetry logging for pack load failures and game generation lifecycle using ErrorKind constants + `_log = logging.getLogger(__name__)` from Phase 2

### Detailed steps

#### Step 5.1: Read server_errors.jsonl in turn viewer failure extraction
**File:** `ccya/server/tv.py`  
**What:** Modify `_turn_viewer_data()` to read both events.jsonl and server_errors.jsonl, merging them into a unified timeline with explicit row type discrimination via `"row_kind"` field

```python
# In tv.py — add import at top:
import json
from pathlib import Path


def _turn_viewer_data(events_path: str):
    """Build turn viewer data from events.jsonl and server_errors.jsonl."""
    turns = []
    
    # Existing logic: parse events.jsonl for turn-level events
    with open(events_path) as f:
        for line in f:
            event = json.loads(line)
            entry = dict(event)  # copy to avoid mutation
            entry["row_kind"] = "turn"  # explicit row type discrimination
            turns.append(entry)
    
    # New logic: read server_errors.jsonl and merge with explicit row_kind
    data_dir = Path(events_path).parent
    server_errors_file = data_dir / "server_errors.jsonl"
    if server_errors_file.exists():
        with open(server_errors_file) as f:
            for line in f:
                entry = json.loads(line)
                # Explicit row_kind — robust, self-documenting, no fragile heuristics
                entry["row_kind"] = "server_error"
                turns.append(entry)
    
    # Sort by timestamp for unified timeline display
    turns.sort(key=lambda e: e.get("ts", ""))
    return turns
```

**Why:** Uses explicit `"row_kind"` field (`"turn"` vs `"server_error"`) instead of fragile heuristic filtering on presence/absence of fields like `turn_id`. A game event could legitimately lack a `turn_id`, or a server error could coincidentally have one — the heuristic would misclassify either way. The design doc's explicit row_kind approach is robust, self-documenting, and gives the turn viewer a single source of truth for building its timeline.

#### Step 5.2: Add health telemetry logging for pack load failures
**File:** `ccya/server/app.py`  
**What:** Replace generic exception handling around pack loading with ErrorKind-enriched structured logging using `_log = logging.getLogger(__name__)` from Phase 2

```python
# In app.py — wherever pack is loaded (existing line ~38-40):
from ccya.errors import ErrorKind, LlmcError


async def create_new_game(pack_id: str):
    try:
        pack = await load_pack_async(pack_id)
    except FileNotFoundError as exc:
        _log.error(
            "pack not found: %s", pack_id,
            extra={"error_kind": ErrorKind.PACK_LOAD_FAILED},
        )
        raise HTTPException(status_code=404, detail=f"Pack '{pack_id}' not found") from exc
    except LlmcError as exc:
        _log.error(
            "LLM error during pack generation for %s", pack_id,
            extra={"error_kind": ErrorKind.PACK_GENERATION_FAILED},
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        _log.error(
            "pack load failed for %s: %s", pack_id, type(exc).__name__,
            extra={"error_kind": ErrorKind.PACK_LOAD_FAILED},
        )
        raise HTTPException(status_code=500, detail="Failed to load or generate pack") from exc
```

**Why:** Pack load failures are now classified by ErrorKind and persisted via server_errors.jsonl middleware. Health telemetry enables monitoring pack generation success rates and identifying problematic packs or LLM provider issues.

#### Step 5.3: Add health telemetry logging for game generation lifecycle events
**File:** `ccya/server/app.py`  
**What:** Add structured log calls at key points in the new-game generation flow (generate_pack → generate_seed → initial turn) using ErrorKind constants and `_log = logging.getLogger(__name__)`

```python
# In app.py — around game creation endpoint:
from ccya.errors import ErrorKind


async def create_game(brief: WorldBrief):
    trace_id = uuid.uuid4().hex[:8]
    
    _log.info(
        "game generation started", extra={"trace_id": trace_id},
    )
    
    try:
        pack = await generate_pack(brief, config, packs_dir)
        _log.info(
            "pack generated successfully", 
            extra={"trace_id": trace_id, "pack": pack.manifest.id},
        )
        
        seed = await generate_seed(pack, config)
        _log.info(
            "seed generated successfully",
            extra={"trace_id": trace_id, "pack": pack.manifest.id},
        )
        
        # ... create initial turn ...
        
    except LlmcTimeout as exc:
        _log.error(
            "game generation LLM timeout at seed stage",
            extra={"error_kind": ErrorKind.SEED_GENERATION_FAILED, "trace_id": trace_id},
        )
        raise HTTPException(status_code=504, detail="LLM timed out during game creation") from exc
    
    except Exception as exc:
        _log.error(
            "game generation failed", 
            extra={"error_kind": ErrorKind.SEED_GENERATION_FAILED, "trace_id": trace_id},
        )
        raise HTTPException(status_code=500, detail="Game generation failed") from exc
    
    finally:
        # Log lifecycle completion regardless of outcome for health telemetry
        _log.info(
            "game generation completed", 
            extra={"trace_id": trace_id},  # No error_kind = success path
        )
```

**Why:** Health telemetry logging enables monitoring game creation pipeline throughput and failure rates. The structured `trace_id` field links all log entries for a single game creation attempt across pack → seed → turn stages, enabling end-to-end debugging of generation failures.

#### Step 5.4: Verify server_errors.jsonl format matches events.jsonl structure
**File:** Both files  
**What:** Ensure server_errors.jsonl uses compatible JSON schema with events.jsonl for consistent querying and parsing by the turn viewer and any future log analysis tools

```python
# server_errors.jsonl entry (from Phase 4 middleware):
{
    "ts": "2025-05-18T12:34:56.789Z",
    "level": "ERROR",
    "error_kind": "LLM_TIMEOUT",
    "message": "Request timed out after 30s",
    "path": "/turn/my-pack/5"
}

# events.jsonl entry (existing pipeline):
{
    "ts": "2025-05-18T12:34:56.789Z", 
    "level": "ERROR",
    "error_kind": "LLM_TIMEOUT",
    "phase": "scene_extraction",
    "turn_id": 5,
    "message": "LLM request timed out"
}
```

**Why:** Consistent schema across both JSONL files enables unified querying (e.g., `grep 'LLM_TIMEOUT' server_errors.jsonl events.jsonl`). Both share ErrorKind constants from Phase 1 and structured formatter fields from Phase 1.

### Tests to write/update
- Unit test `_turn_viewer_data()` merges events.jsonl and server_errors.jsonl with explicit `"row_kind"` discrimination, sorted by timestamp for unified timeline display
- Integration test: verify game generation lifecycle logs include trace_id at each stage (pack → seed → turn) for end-to-end correlation
- Verify server_errors.jsonl entries have compatible schema with events.jsonl entries (same ts/level/error_kind/message structure)

### REPOMAP updates required
Update "turn viewer section" in repomap.md showing new server_errors.jsonl reading path alongside existing events.jsonl parsing. Update "server app.py health telemetry section" with ErrorKind-enriched logging for pack load and game generation lifecycle events. Add note about trace_id correlation across pipeline stages.
