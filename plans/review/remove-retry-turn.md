# Remove Dead retry_turn / run_turn_retry

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Engine tearout | Delete `run_turn_retry` from `engine/turn.py` and its export from `engine/__init__.py` |
| 02 | Server tearout | Delete `GET /turn/retry` route handler and remove the import of `run_turn_retry` and `IntentEnvelope` (if unused after removal) from `routes.py` |
| 03 | Test cleanup | Delete all tests covering `run_turn_retry` and `retry_turn` in `tests/test_eval.py`; verify no other test files reference either symbol |
| 04 | REPOMAP + docs | Scrub `run_turn_retry` references from `docs/REPOMAP/engine.md` and `docs/REPOMAP/server.md`; update `AGENTS.md` module table if retry language remains |

## Objective
`run_turn_retry` and the `GET /turn/retry` route that calls it are dead code. The UI retry button now invokes `POST /turn/delete`, which removes the last turn from state entirely and returns to the end of the previous turn. The older `retry_turn` path attempted to rewind to before narration while preserving the rules/dice result — that behaviour is no longer needed or wired to any frontend action. Removing it eliminates a parallel turn-execution path, its event-stream handler, its model assembly code, and its tests, reducing surface area and confusion.

## Non-goals
- Do not modify `POST /turn/delete` or its frontend wiring in any way.
- Do not change `RulesOutcome` or `IntentEnvelope` models unless `IntentEnvelope` is confirmed unused after the route is removed (check before deleting).
- Do not alter the narration or rules pipeline for normal `run_turn`.
- Do not touch `engine/rules.py`'s internal retry logic for rules LLM calls — that is unrelated.

---

## Implementation — Phase 01: Engine tearout

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/engine/__init__.py`

### Detailed steps

#### Step 1.1 — Delete `run_turn_retry` from `turn.py`

**File:** `ccya/engine/turn.py`

**What:** Locate the `run_turn_retry` function (an `async def` that accepts `save_dir`, `rules_outcome: RulesOutcome`, `intent: IntentEnvelope`, and the standard pack kwargs). Delete the entire function body including its signature.

**Why:** The function is dead — nothing calls it except the route being removed in Phase 02.

**Code Snippet**
```python
# Delete the entire run_turn_retry function. Do not replace it with anything.
# Confirm by searching for `def run_turn_retry` — after this step it must not exist.
```

**Validation:** `grep -n "run_turn_retry" ccya/engine/turn.py` returns no results.

#### Step 1.2 — Remove export from `engine/__init__.py`

**File:** `ccya/engine/__init__.py`

**What:** Remove `run_turn_retry` from the `__all__` list (if present) and from any `from .turn import ...` line.

**Why:** Exported dead symbols cause mypy noise and mislead readers about the public API.

**Code Snippet**
```python
# Before (example — verify exact import line in source):
from .turn import run_turn, run_turn_retry

# After:
from .turn import run_turn
```

**Validation:** `grep -n "run_turn_retry" ccya/engine/__init__.py` returns no results.

---

## Implementation — Phase 02: Server tearout

### Files to pull for context
- `ccya/server/routes.py`

### Detailed steps

#### Step 2.1 — Delete the `retry_turn` route handler

**File:** `ccya/server/routes.py`

**What:** Delete the entire `@_app_mod.app.get("/turn/retry")` decorated function `async def retry_turn()` — from the decorator line through the final `return EventSourceResponse(event_stream())` — including the nested `event_stream` coroutine.

**Why:** This is the only caller of `run_turn_retry`. Once it's gone, the engine function has no callers.

**Code Snippet**
```python
# Delete this entire block (lines shown are structural, verify exact line numbers in source):
@_app_mod.app.get("/turn/retry")
async def retry_turn():
    ...  # entire body including nested event_stream
    return EventSourceResponse(event_stream())
```

**Validation:** `grep -n "retry_turn\|/turn/retry\|run_turn_retry" ccya/server/routes.py` returns no results.

#### Step 2.2 — Clean up imports in `routes.py`

**File:** `ccya/server/routes.py`

**What:** Remove `run_turn_retry` from the `from ccya.engine import (...)` block. Then check whether `IntentEnvelope` is used anywhere else in `routes.py` — if it is not, remove it from the `from ccya.models import ...` line as well.

**Why:** Unused imports will fail `make check` (ruff F401).

**Code Snippet**
```python
# Before:
from ccya.engine import (
    format_change_lines,
    generate_seed,
    is_turn_in_progress,
    run_turn,
    run_turn_retry,
)
from ccya.models import IntentEnvelope, RulesOutcome

# After (remove run_turn_retry; remove IntentEnvelope only if no other use exists):
from ccya.engine import (
    format_change_lines,
    generate_seed,
    is_turn_in_progress,
    run_turn,
)
from ccya.models import RulesOutcome  # drop IntentEnvelope if unused
```

**Validation:** `make check` (ruff) passes with no F401 errors in `routes.py`.

---

## Implementation — Phase 03: Test cleanup

### Files to pull for context
- `tests/test_eval.py`
- Run `grep -rn "run_turn_retry\|retry_turn" tests/` to locate all affected test files before starting.

### Detailed steps

#### Step 3.1 — Delete retry-related tests in `test_eval.py`

**File:** `tests/test_eval.py`

**What:** Delete every test function that exercises `run_turn_retry` or the `GET /turn/retry` route. Also remove any fixtures, imports, or helper functions that exist solely to support those tests.

**Why:** Tests for deleted code must be removed; leaving them would cause import errors or dead test coverage.

**Code Snippet**
```python
# Delete any function matching these patterns (verify exact names in source):
# - test_*retry*
# - Any test that imports or patches run_turn_retry
# Do not delete tests for run_turn, delete_last_turn, or any unrelated route.
```

**Validation:** `grep -n "run_turn_retry\|retry_turn" tests/test_eval.py` returns no results.

#### Step 3.2 — Scan for stray references in other test files

**What:** Run `grep -rn "run_turn_retry\|retry_turn" tests/` and delete any remaining references.

**Validation:** The grep above returns no results across the entire `tests/` directory.

---

## Implementation — Phase 04: REPOMAP + docs

### Files to pull for context
- `docs/REPOMAP/engine.md`
- `docs/REPOMAP/server.md`
- `AGENTS.md`

### Detailed steps

#### Step 4.1 — Remove from `docs/REPOMAP/engine.md`

**File:** `docs/REPOMAP/engine.md`

**What:** Remove any entry, row, or section describing `run_turn_retry`. If the file lists function signatures for `engine/turn.py`, delete the `run_turn_retry` entry entirely.

**Why:** Stale docs violate the AGENTS.md rule: "if the code changes, the docs must change in the same commit."

**Validation:** `grep -n "run_turn_retry" docs/REPOMAP/engine.md` returns no results.

#### Step 4.2 — Remove from `docs/REPOMAP/server.md`

**File:** `docs/REPOMAP/server.md`

**What:** Remove any route entry for `GET /turn/retry` and any mention of `retry_turn`.

**Validation:** `grep -n "retry_turn\|/turn/retry" docs/REPOMAP/server.md` returns no results.

#### Step 4.3 — Update `AGENTS.md` module table if needed

**File:** `AGENTS.md`

**What:** The `engine/` row currently reads "Turn pipeline: `run_turn()`, extraction, narration, retry logic". If "retry logic" refers specifically to `run_turn_retry` (not to the rules-LLM retry in `engine/rules.py`), remove that phrase. If it refers to both, leave it and just drop the `run_turn_retry` specifics.

**Why:** Keep the module responsibility table accurate.

**Validation:** The table no longer implies `run_turn_retry` is a live public entrypoint.

### Tests to write or update
No new tests. This phase is documentation only — no test changes required beyond what Phase 03 covers.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — remove `run_turn_retry` function entry
- `docs/REPOMAP/server.md` — remove `GET /turn/retry` route entry
- `AGENTS.md` — narrow "retry logic" description in module table if it currently implies `run_turn_retry` is live

### Risks
1. `IntentEnvelope` may be used elsewhere in `routes.py` — executor must grep before removing the import. If it is used, leave it.
2. `engine/rules.py` has its own internal retry loop for rules LLM calls; that is completely unrelated and must not be touched. The name similarity is a trap.

---

## Ambiguities requiring resolution before execution

1. Is `IntentEnvelope` used anywhere in `routes.py` other than the `retry_turn` handler? Check before removing from imports. Options: A) Used elsewhere — keep import. B) Not used — delete import.

2. Does the `run_turn_retry` function in `turn.py` share any helper functions with `run_turn` that would be orphaned by its removal, or does it only call shared helpers that `run_turn` also calls? Options: A) Only shared helpers — no additional cleanup. B) Has private helpers used only by it — those must be deleted too.
