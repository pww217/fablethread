# Phase 03: Medium refactors — magic sentinel, async globals, late import

**Depends on:** Phase 02 (small refactors) — some changes touch same modules
**Status:** implemented
**Ticket:** I-24

## Purpose

Address the three items requiring design attention: replace magic string sentinel, eliminate async result globals, and restructure FastAPI route registration.

---

## Task 03-01: Replace `_FALLBACK_SENTINEL` with structured protocol

**Files:** `ccya/engine/turn.py`

**What:**
- Replace the magic string `_FALLBACK_SENTINEL = "*That action didn't resolve as expected"` (line 367) with a structured marker.
- The sentinel is used at line 373 to filter out the fallback line from LLM output.

**Design decision:** Use a special JSON key pattern in the LLM output rather than a magic string prefix. The LLM prompt should instruct the model to output a structured response with a `fallback` key when the action doesn't resolve. The parser checks for the key rather than matching a string prefix.

**Implementation approach:**
1. Add a constant `FALLBACK_KEY = "__fallback__"` at module level.
2. Update the LLM prompt to output `{"fallback": true, "reason": "..."}` instead of the magic string when the action doesn't resolve.
3. Update the parser at line 373 to check for the `fallback` key in the parsed JSON rather than filtering lines starting with `_FALLBACK_SENTINEL`.

**Validation:**
- `_FALLBACK_SENTINEL` constant removed.
- Parser checks for `fallback` key in parsed output.
- LLM prompt updated to use structured fallback format.

---

## Task 03-02: Replace module-level globals in pipeline.py with explicit return values

**Files:** `ccya/engine/extraction/pipeline.py`

**What:**
- Remove module-level globals: `_scene_result_holder`, `_state_result_holder`, `_record_result_holder`, `_extraction_ctx_holder` (lines 36-39).
- Pass results through explicit return values or a context object.

**Design decision:** Create a `_ExtractionResult` dataclass that carries all extraction results between coroutines. Replace the four separate globals with a single context object passed through the call chain.

**Interface contract — new dataclass:**
```python
@dataclass
class _ExtractionResult:
    scene_result: tuple[Any, dict[str, Any]] | None = None
    state_result: tuple[Any, dict[str, Any]] | None = None
    record_result: tuple[Any, dict[str, Any]] | None = None
    extraction_ctx: _ExtractionContext | None = None
```

**Implementation approach:**
1. Define `_ExtractionResult` dataclass at module level.
2. Pass `_ExtractionResult` instance through the extraction pipeline call chain.
3. Each coroutine reads/writes from the shared instance instead of module globals.
4. Remove the four module-level global variables.

**Validation:**
- `_scene_result_holder`, `_state_result_holder`, `_record_result_holder`, `_extraction_ctx_holder` removed.
- `_ExtractionResult` dataclass exists and is used throughout the pipeline.
- No module-level mutable state remains in pipeline.py.

---

## Task 03-03: Restructure FastAPI route registration to eliminate late import

**Files:** `ccya/server/app.py`, `ccya/server/routes.py`

**What:**
- Remove the late import `import ccya.server.routes` at app.py:205.
- Restructure route registration to avoid circular imports.

**Design decision:** Move route registration to a bootstrap function in `routes.py` that is called after `app` is created. This eliminates the circular import without requiring a late import.

**Implementation approach:**
1. Add a `register_routes(app: FastAPI) -> None` function at the bottom of `routes.py` (after all route handlers are defined).
2. Move the `@app.get`/`@app.post` decorator registrations into this function (or keep decorators and call a function that registers them).
3. In `app.py`, replace `import ccya.server.routes` with `from ccya.server.routes import register_routes` followed by `register_routes(app)`.

**Alternative (simpler):** Keep decorators on route handlers but import `routes` at the top of `app.py` inside a function that runs after `app` creation (eager import in a function body, not module-level).

**Validation:**
- No late `import ccya.server.routes` in app.py.
- Routes are registered before the server starts.
- No circular import errors on startup.

---

## Phase verification

Run `make check` — lint + typecheck must pass.
Start the server — verify routes are registered and functional.
Run `ev.py check` — verify LLM checkers work with explicit config parameter.
