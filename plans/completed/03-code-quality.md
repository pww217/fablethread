# Code Quality — Duplication, Fragile Patterns, Side Effects

## Status
`completed`

## Phases

4 phases: parameterize averaging functions and fix side-effect mutation in extraction.py, deduplicate coercion validators in models.py, fix fragile `dir()` introspection in turn.py, clean up `__all__` export and extract mock infrastructure from llm_client.py.

## Issue

The codebase has accumulated four distinct code-quality problems through organic growth. Three structurally identical averaging functions (`_avg_narrate_ms`, `_avg_extract_ms`, `_avg_ruling_ms`) duplicate the same 20-line logic with different field paths. `_capitalize_inventory_names()` mutates its parameters in-place while returning a value, suggesting purity while causing side effects. Coercion validators for `inventory_remove`, `pc_condition_add`, and `pc_condition_remove` are duplicated across `StateDelta` and `StateExtractResult` — identical code with a subtle punctuation-stripping divergence on `_coerce_condition_remove` (9 chars stripped in one, 6 in the other). `_apply_thread_resolutions()` uses `dir()` introspection to detect variable existence. `_fuzzy_match_inventory` is exported in `__all__` despite its underscore-private naming convention. The mock infrastructure in `llm_client.py` (101 lines) mixes test code into production as env-gated dead weight.

## Solution

Parameterize the three averaging functions into a single `_avg_event_ms(save_dir, field_path, n=5)`. Fix `_capitalize_inventory_names()` to operate as a pure function (returns new items) or change its callers to expect mutation without return. Extract the three coercion validators to module-level functions in `models.py` and reference from both dataclasses via `@field_validator(mode="before")`. Replace the `dir()` check with a boolean flag. Remove `_fuzzy_match_inventory` from `__all__`. Extract mock data and classes from `llm_client.py` into a separate `tests/mocks.py` (or `ccya/llm_mock.py`).

## Firm decisions

1. `_capitalize_inventory_names()` becomes a `None`-returning procedure. Callers no longer capture a return value that is identical to the input.
2. The extracted coercion validators follow the `_coerce_*` naming convention and live at module level in `models.py`.
3. Mock extraction from `llm_client.py` goes into `ccya/llm_mock.py`, not `tests/mocks.py`, so it can be imported by the production module without test dependencies in the import graph.
4. This plan depends on `05-config-surface-cleanup` (Phase 2) which also touches `llm_client.py`. Phase 4 of this plan should run after `05-config-surface-cleanup` is complete.

## Non-goals

- Not adding an `llm_mock.py` that is loaded at import time. The mock module is imported only when `MOCK_MODE` is set, matching current behavior.
- Not refactoring the calling logic in `extraction.py:740-745` beyond the return-value change.
- Not touching the test infrastructure beyond the mock extraction.

## Risks, Ambiguities, and Blockers

- `_avg_ruling_ms()` in `ruling.py:123-142` must be located and updated in Phase 1. It has the same structure as the extraction.py versions. All three must be removed and replaced with the single parameterized function.
- `_capitalize_inventory_names()` callers are at `extraction.py:744-745`. Both ignore the return value, confirming the fix is safe.
- The `resolve_inventory_remove_target` and `_coerce_*` validators are imported by `eval/engine_mirror.py`. Ensure any renamed/relocated validators are updated in the mirror.
- No blocker. All phases are mechanical and safe.
- **Dependency:** Phase 4 touches `llm_client.py` which is also touched by `05-config-surface-cleanup` Phase 2 (apply_thinking removal). Wait for that plan to complete first, or merge the changes.

---

## Implementation — Phase 1: Fix extraction.py — averaging functions and capitalize side-effect

### Context files to load
- `ccya/engine/extraction.py` — `_avg_narrate_ms()` (line 791), `_avg_extract_ms()` (line 814), `_capitalize_inventory_names()` (line 154), call sites at lines 744-745
- `ccya/engine/ruling.py` — `_avg_ruling_ms()` (line 123)

### Detailed steps

#### Step 1.1 — Create unified `_avg_event_ms()` function

**File:** `ccya/engine/extraction.py`

**What:** Replace the two `_avg_narrate_ms()` and `_avg_extract_ms()` functions with a single parameterized function:

```python
# Interface contract — not implementation
def _avg_event_ms(save_dir: Path, field_path: str, n: int = 5) -> int:
    ...
```

Where `field_path` is a dot-delimited path into the event dict (e.g. `"narrate.total_ms"`, `"extract.total_ms"`). The function reads `events.jsonl`, parses the last N lines, extracts the field at `field_path`, and averages non-None values.

**File:** `ccya/engine/ruling.py`

**What:** Remove `_avg_ruling_ms()` and replace its single call site with `_avg_event_ms(save_dir, "ruling.total_ms")`. Import `_avg_event_ms` from `ccya.engine.extraction`.

**Why:** Three structurally identical functions with only the field path differing. Parameterizing eliminates copy-paste debt and ensures any bug fix (e.g., edge case for <2 lines) applies to all three.

**Validation:** After the change, `_avg_event_ms` is called three times across the codebase with different field paths. `make check && make test` passes. No `_avg_narrate_ms`, `_avg_extract_ms`, or `_avg_ruling_ms` identifiers remain.

#### Step 1.2 — Fix `_capitalize_inventory_names()` side-effect

**File:** `ccya/engine/extraction.py`

**What:** Change `_capitalize_inventory_names()` from returning `list[Any]` to returning `None`. Remove the `return items` statement. Update its docstring to reflect that it mutates in place with no return value.

Update the callers at lines 744-745 to not capture the return value (they already ignore it; just change from `_capitalize_inventory_names(...)` as an expression statement — which it already is — but ensure no assignment is present).

**Why:** The function mutates items in-place but returns the list, suggesting purity to readers. Making it `None`-returning aligns signature with behavior.

**Validation:** `make check` passes. No call site assigns a variable from `_capitalize_inventory_names()`.

### Tests to write or update

- `tests/test_extraction.py`: Test `_avg_event_ms` with a mock `events.jsonl` containing known narrate/extract/ruling times. Assert correct average for each field path.
- `tests/test_extraction.py`: Test `_capitalize_inventory_names` with both Pydantic model and dict inputs. Assert that items are capitalized in-place (no return value needed).

### REPOMAP updates required

- `ccya/engine/extraction.py`: Update function signatures and docstrings.
- `ccya/engine/ruling.py`: Remove `_avg_ruling_ms`, add import of `_avg_event_ms`.

---

## Implementation — Phase 2: Deduplicate coercion validators in models.py

### Context files to load
- `ccya/models.py` — `StateDelta` class (lines 238-292) and `StateExtractResult` class (lines 340-374)

### Detailed steps

#### Step 2.1 — Extract shared validator functions to module level

**File:** `ccya/models.py`

**What:** Create three module-level functions from the duplicated `@classmethod` validators:

```python
# Interface contract
def _coerce_inventory_remove_item(v: Any) -> Any:
    """Normalize inventory_remove entries: str → {id, amount}, passthrough dicts."""
    ...

def _coerce_condition_add_item(v: Any) -> Any:
    """Normalize condition_add entries using _coerce_condition_str."""
    ...

def _coerce_condition_remove_item(v: Any) -> Any:
    """Normalize condition_remove entries: str → {id}, stripping punctuation."""
    # Single source of truth for punctuation strip set
    ...
```

Move these functions to module level (before both model classes). Remove the duplicated `@field_validator("inventory_remove", ...)` / `@field_validator("pc_condition_add", ...)` / `@field_validator("pc_condition_remove", ...)` methods from both `StateDelta` and `StateExtractResult`.

Replace each removed validator with `@field_validator("field_name", mode="before") @classmethod def validator_name(cls, v): return _coerce_field_name(v)` — a thin wrapper that delegates to the module-level function.

**Why:** The three validators are identical across `StateDelta` and `StateExtractResult` (for `inventory_remove` and `condition_add`) or nearly identical (for `condition_remove` — one strips 9 punctuation chars, the other strips 6). Extracting to module level creates a single source of truth and eliminates the latent punctuation-stripping divergence.

**Decision on punctuation divergence:** Use the more aggressive set (9 chars: `"*", "_", "`", ".", ",", ";", ":", "!", "?"`). This normalizes to the stricter standard and won't cause false negatives (extra stripped chars are harmless for condition IDs).

**Validation:** `make check && make test` passes. Both `StateDelta(...)` and `StateExtractResult(...)` still accept the same input shapes as before.

### Tests to write or update

- `tests/test_models.py`: Add test cases for each `_coerce_*` function with string inputs, dict inputs, and empty/null inputs. Verify `inventory_remove` strings normalize to `{"id": str, "amount": None}`. Verify `condition_remove` strings normalize to `{"id": cleaned_id}` with consistent punctuation stripping.

### REPOMAP updates required

- `ccya/models.py`: Move coercion logic to module-level functions.

---

## Implementation — Phase 3: Fix fragile dir() introspection in turn.py

### Context files to load
- `ccya/engine/turn.py` — `_apply_thread_resolutions()` function, lines 340-370

### Detailed steps

#### Step 3.1 — Replace dir() check with boolean flag

**File:** `ccya/engine/turn.py`

**What:** Replace the `'remaining_completed' in dir()` checks (lines 355, 367) with a boolean flag:

- Initialize `found_remaining = False` before the `for res in storyteller_result.thread_resolve:` loop.
- Set `found_remaining = True` in the `if thread.id in completed_by_id:` branch that assigns `remaining_completed`.
- Change line 355 from `if any_found and 'remaining_completed' in dir():` to `if found_remaining:`.
- Change line 367 from `if not any_found and 'remaining_completed' not in dir():` to `if not any_found and not found_remaining:`.

**Why:** Using `dir()` to detect whether a local variable was assigned is fragile — any change to the code structure that affects variable initialization would break this check silently. A boolean flag is explicit and survives refactoring.

**Validation:** `make check && make test` passes. Run a game turn with a thread_resolve that updates an existing completed thread — confirm the dedup logic still works by inspecting the completed_threads list.

### Tests to write or update

- `tests/test_turn.py`: Add a test case for `_apply_thread_resolutions` with multiple `thread_resolve` entries, including one that updates an existing completed entry. Assert the final completed_threads list has no duplicates and the updated resolution_state is preserved.

### REPOMAP updates required

- `ccya/engine/turn.py`: Update the `_apply_thread_resolutions()` function.

---

## Implementation — Phase 4: Clean up __all__ and extract mock infrastructure

### Context files to load
- `ccya/state/__init__.py` — `__all__` list (line 34)
- `ccya/llm_client.py` — mock data and classes (lines 25-126)

### Detailed steps

#### Step 4.1 — Remove _fuzzy_match_inventory from __all__

**File:** `ccya/state/__init__.py`

**What:** Remove `"_fuzzy_match_inventory"` from the `__all__` list (line 35).

**Why:** The underscore prefix conventionally indicates private API. Exporting it in `__all__` suggests it's part of the public contract. No external code imports it from the package (`eval/engine_mirror.py` imports directly from `state.delta`).

**Validation:** `rg "from ccya.state import.*fuzzy" ccya/ --include='*.py'` returns zero matches. `make check` passes.

#### Step 4.2 — Extract mock infrastructure into ccya/llm_mock.py

**File:** `ccya/llm_client.py` (new file: `ccya/llm_mock.py`)

**What:** Create `ccya/llm_mock.py` containing:
- `_MOCK_NARRATE` string (27-32)
- `_MOCK_EXTRACT_NARRATE` dict (34-48)
- `_MOCK_EXTRACT_EXAMINE` dict (50-63)
- `_MOCK_EXTRACT_CARGO` dict (65-84)
- `_mock_stream` class (87-100)
- `_mock_extract_chat` function (103-126)

In `ccya/llm_client.py`, replace the inline definitions with `from ccya.llm_mock import _MOCK_NARRATE, _MOCK_EXTRACT_NARRATE, _MOCK_EXTRACT_EXAMINE, _MOCK_EXTRACT_CARGO, _mock_stream, _mock_extract_chat`.

Keep the `_MOCK_MODE` env var check in `llm_client.py` — it's the decision point. Move only the data and mock classes.

**Why:** 101 lines of mock infrastructure (~33% of `llm_client.py`) interleaves with production logic. Extracting to a dedicated module makes the production file readable and the mocks independently importable for tests.

**Validation:** `MOCK_MODE=1 python3 -c "import ccya.llm_client"` — mock objects load successfully. `make check` passes.

### Tests to write or update

- `tests/test_llm_mock.py`: Import `_mock_stream` and `_mock_extract_chat` from `ccya.llm_mock`. Test that stream yields the expected mock narration chunks. Test that `_mock_extract_chat` returns correct mock responses for different narrative keywords.

### REPOMAP updates required

- `ccya/llm_client.py`: Update imports at top of file to import from `ccya.llm_mock`.

## Notes

- Phase 4 (mock extraction from llm_client.py) deferred until after plan 05 (config-surface-cleanup) removes apply_thinking() from the same file. Return to this plan after plan 05 is complete.
