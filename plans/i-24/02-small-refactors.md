# Phase 02: Small refactors — dedup, coercion, deepcopy, retry, config

**Depends on:** Phase 01 (trivial cleanup) — no hard dependency but benefits from cleaner codebase
**Status:** implemented
**Ticket:** I-24

## Purpose

Consolidate duplicated code, fix fragile patterns, replace `copy.deepcopy` with `model_copy`, narrow retry criteria, and fix config mismatch.

---

## Task 02-01: Extract `_filter_pc_situation` to shared module

**Files:** `ccya/engine/ruling.py`, `ccya/engine/narrate.py`
**New location:** `ccya/engine/extraction/utils.py`

**What:** 
- Copy the identical `_filter_pc_situation` function (ruling.py:20-27 / narrate.py:22-29) to `ccya/engine/extraction/utils.py`.
- Update both ruling.py and narrate.py to import from `ccya.engine.extraction.utils` instead of defining locally.
- Delete the local definition from both files.

**Why:** Validated as duplicated code (#4). Identical implementations in both files.

**Interface contract — extracted function signature:**
```python
def _filter_pc_situation(pc_situation: dict[str, Any], schema: list[dict[str, Any]]) -> dict[str, Any]:
    """Filter pc.situation to only include keys marked persist=true in the schema."""
```

**Validation:**
- `rg -n "_filter_pc_situation" ccya/engine/ruling.py ccya/engine/narrate.py` returns only import lines (no local definition).
- `rg -n "_filter_pc_situation" ccya/engine/extraction/utils.py` returns the function definition.
- Both callers import from the shared location.

---

## Task 02-02: Extract `_to_arc_thread()` helper in _pacing.py

**Files:** `ccya/engine/_pacing.py`, `ccya/engine/narrate.py`

**What:**
- Add a private `_to_arc_thread(t: Any) -> ArcThread | None` helper in `_pacing.py` that wraps the `isinstance(t, ArcThread)` check + `ArcThread.model_validate(t)` fallback.
- Replace the duplicated coercion pattern in `_pacing.py:238-247` with a call to `_to_arc_thread(t)`.
- Replace the duplicated coercion pattern in `narrate.py:190-203` with a call to `_to_arc_thread(t)` (import from `_pacing`).

**Why:** Validated as scattered coercion (#5). Identical `isinstance(t, ArcThread)` + `ArcThread.model_validate(t)` pattern in both files.

**Interface contract — helper signature:**
```python
def _to_arc_thread(t: Any) -> ArcThread | None:
    """Convert t to ArcThread if possible, return None on failure."""
```

**Validation:**
- `rg -n "isinstance.*ArcThread.*model_validate\|ArcThread\.model_validate" ccya/engine/_pacing.py ccya/engine/narrate.py` returns only calls to `_to_arc_thread()`.
- No remaining inline `isinstance(t, ArcThread)` coercion patterns.

---

## Task 03-03: Remove dead `added_ids` from thread_sanitizer

**File:** `ccya/engine/thread_sanitizer.py`

**What:** Remove `added_ids` from the `changes_detail` dict initialization (line 346), the local variable declaration (line 354), and the assignment to `changes_detail["added_ids"]` (line 476). Also remove the `added_ids` usage in the `has_changes` check (line 492) and the `last_thread_created_turn` guard (line 480).

**Why:** Validated as dead code (#9). `added_ids` is declared but never appended to anywhere in the file.

**Validation:**
- `rg -n "added_ids" ccya/engine/thread_sanitizer.py` returns no results.
- No callers reference `added_ids` in the returned `changes_detail` dict.

---

## Task 02-04: Expand `_is_retryable` and remove unreachable else

**File:** `ccya/llm_client.py`

**What:**
- Expand `_is_retryable()` (line 137-141) to also match `LlmcRateLimit`, `LlmcApiError`, and `httpx.ConnectError` / `httpx.ReadError` — transient network failures.
- Remove the unreachable `for...else` clause at lines 210-212.

**Why:** Validated as narrow retry logic (#10). Only `TimeoutError` is currently retryable. The `else` clause is unreachable because the loop always exits via `return`/`break`/`raise`.

**Interface contract — expanded `_is_retryable`:**
```python
def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception represents a transient failure worth retrying."""
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, (LlmcRateLimit, LlmcApiError)):
        return True
    if isinstance(exc, httpx.HTTPError):
        return True
    return False
```

**Validation:**
- `_is_retryable` returns True for `TimeoutError`, `LlmcRateLimit`, `LlmcApiError`, `httpx.HTTPError`.
- No unreachable `for...else` clause remains.

---

## Task 02-05: Replace `copy.deepcopy` with `model_copy()` on Pydantic models

**Files:** `ccya/engine/extraction/context.py:57`, `ccya/engine/extraction/pipeline.py:110,261,285`

**What:**
- `context.py:57`: Replace `copy.deepcopy(state)` with `state.model_copy()`.
- `pipeline.py:110`: Replace `copy.deepcopy(state)` with `state.model_copy()`.
- `pipeline.py:261`: Replace `copy.deepcopy(s)` in lambda with `s.model_copy()`.
- `pipeline.py:285`: Replace `copy.deepcopy(s)` in lambda with `s.model_copy()`.

**Why:** Validated as non-idiomatic (#16). `WorldState` (state.py:115) is a Pydantic `BaseModel`. `copy.deepcopy` bypasses Pydantic's validation layer.

**Exception — delta_builder.py:74 stays as `copy.deepcopy`:** The function doc explicitly states "creates a copy, reconciles the copy" — deepcopy is intentional for the `StateDelta` parameter. No change needed.

**Validation:**
- `rg -n "copy\.deepcopy" ccya/engine/extraction/context.py ccya/engine/extraction/pipeline.py` returns no results.
- All replaced with `.model_copy()`.

---

## Task 02-06: Fix `_engine_config` hidden coupling in llm_checkers.py

**File:** `ccya/ev/checkers/llm_checkers.py`

**What:**
- Change `_get_config()` to accept `config: EngineConfig | None = None` as a parameter instead of reading from module-level `_engine_config`.
- Update `set_checker_config()` — remove the function entirely.
- Update all callers of `_get_config()` to pass the config explicitly.

**Why:** Validated as questionable `global` usage (#17). Hidden coupling — config is set once by check command, read by any LLM checker caller without it being in the function signature.

**Interface contract — new `_get_config` signature:**
```python
def _get_config(config: EngineConfig | None = None) -> EngineConfig:
    """Get the engine config for LLM checker calls.
    
    Accepts an optional config; falls back to EngineConfig() if None.
    Callers should pass config explicitly to avoid hidden coupling.
    """
```

**Validation:**
- `_get_config()` accepts `config` parameter.
- `set_checker_config()` no longer exists.
- No `global _engine_config` declarations remain in this file.

---

## Phase verification

Run `make check` — lint + typecheck must pass.
