# Critical Pipeline Fixes

## Status
`completed`

## Phases

2 phases: fix the Jinja syntax error that crashes compaction, then fix the two state-delta validation gaps that enable phantom item lifecycles.

## Issue

Three P0 runtime bugs survive from the eval run and code audit:

1. **`compact_user.j2`** has an unclosed `{% if arc %}` at line 11 — never gets an `{% endif %}`. Every compaction turn (T3, T6, T9, T12) hits `TURN_PROCESSING_FAILED` because Jinja can't parse it.
2. **`inventory_remove`** for non-existent items passes silently through both validation (emits `warn_missing_item` non-blocking rejection) and `apply_delta()` (silently skips at delta.py:182-185). There is no engine-side logging. Items can exist in narrative but not state, with removals having no mechanical effect and no warning.
3. **`reconcile_delta()`** mutates `delta.inventory_add` and `delta.pc_condition_add` arrays in-place while also returning warnings. The caller (`run_turn()`) can't distinguish "here are the actual changes" from "here's what was rejected." The reconciled values silently overwrite what the LLM originally produced.

## Solution

Fix the template syntax error (5 min, straightforward). Add a warning log in `apply_delta()` for each silently skipped `inventory_remove` target so phantom removals are visible in logs. Make `reconcile_delta()` return a new reconciled delta instead of mutating in-place, preserving the original delta for inspection.

## Firm decisions

1. The `compact_user.j2` fix is a single `{% endif %}` insertion. No restructuring of the template.
2. `inventory_remove` non-existent items remain non-blocking (game state can drift from narrative, blocking would break existing saves). Fix is limited to engine-side logging + structured warning.
3. `reconcile_delta()` returns a new `StateDelta`; the original is preserved. The call site in `run_turn()` is updated to use the return value.

## Non-goals

- Not restructuring `compact_user.j2` beyond the syntax fix.
- Not making `inventory_remove` rejections blocking.
- Not changing the LLM extraction prompts — extraction accuracy is a separate plan.
- Not refactoring `reconcile_delta()` beyond the return-value change.

## Risks, Ambiguities, and Blockers

- `run_turn()` call site for `reconcile_delta()` is at line 1168, not ~1165. The returned `delta` overwrites the original variable — downstream use is seamless.
- No blocker. All three fixes are mechanical.

---

## Implementation — Phase 1: Fix Jinja syntax in compact_user.j2

### Context files to load
- `ccya/prompts/compact_user.j2`

### Detailed steps

#### Step 1.1 — Close the unclosed `{% if arc %}` block

**File:** `ccya/prompts/compact_user.j2`

**What:** Add `{% endif -%}` after line 25 (after the `{% if pressures -%}...{% endif -%}` block closes, before the inventory section begins). The `{% if arc and (arc.get('threads') or []) -%}` opened at line 11 must be closed before the template transitions to `## Current inventory`.

**Why:** Without the closing `{% endif %}`, Jinja parses all subsequent content (inventory, compendium, conditions) as inside the unclosed conditional. The parser raises `"Unexpected end of template"` on every compaction turn.

**Validation:** `python3 -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); e.parse(open('ccya/prompts/compact_user.j2').read())"` — must not raise.

### Tests to write or update

None. This is a syntax fix; the rendered output isn't changing semantics. Existing test scenarios that trigger compaction should no longer crash.

### REPOMAP updates required

None.

---

## Implementation — Phase 2: Fix state-delta validation gaps

### Context files to load
- `ccya/state/delta.py` — both `reconcile_delta()` (~line 84) and `apply_delta()` (~line 125)
- `ccya/engine/turn.py` — the `_validate()` function (~line 1501) and the `reconcile_delta()` call site (~line 1165)
- `ccya/models.py` — `StateDelta` class shape

### Detailed steps

#### Step 2.1 — Log warning in apply_delta() for silently skipped inventory_remove

**File:** `ccya/state/delta.py`

**What:** In the `apply_delta()` function, in the `inventory_remove` loop (~line 182), when `resolve_inventory_remove_target()` returns `None` (item not found), replace the bare `continue` with a `_log.warning(...)` call that includes the item ID and the current turn number (available as a parameter). The function signature already accepts `current_turn_no: int | None`.

**Why:** Currently a missing item is silently ignored — the phantom lifecycle (ledger added narratively, removed from state, re-added later) has no observability. This log makes the gap visible in structured logs for debugging.

**Validation:** Run a turn where inventory_remove targets a non-existent item. Confirm `_log.warning` fires with the item ID.

#### Step 2.2 — Make reconcile_delta() return a new delta instead of mutating in-place

**File:** `ccya/state/delta.py`

**What:** Change `reconcile_delta()` to create a deep copy of the input `delta`, mutate the copy, and return a new `StateDelta` instead of mutating in-place. The function signature changes from `def reconcile_delta(state, delta) -> list[str]` to `def reconcile_delta(state, delta) -> tuple[StateDelta, list[str]]`.

**Why:** The current contract says "Mutates delta in place" (line 88). The caller at `turn.py:~1165` has no way to compare "what the LLM produced" vs "what was reconciled." Returning a new delta makes the original available for inspection, logging, and debugging.

**Call site update:** At `turn.py:1168`, unpack the new return value as `delta, reconcile_warnings = reconcile_delta(state, delta)`, overwriting the original `delta` variable with the reconciled copy. The original LLM-produced delta is discarded once reconciled — preservation for inspection can be added later if needed. All downstream uses of `delta` (line 1171 `apply_delta(state, delta)`, line 1184 `delta.recent_events_add`, line 1185 `delta.model_dump(...)`) automatically use the reconciled version.

**Validation:** `make check && make test` — no type errors from the return-value change. Confirm the call site in `turn.py` unpacks the tuple correctly.

### Tests to write or update

- `tests/test_delta.py`: Add a test that calls `reconcile_delta()` and asserts the original delta is unmodified after the call (no in-place mutation).
- `tests/test_delta.py`: Add a test that `apply_delta()` with a missing-item `inventory_remove` logs a warning (capture log output with `caplog`).

### REPOMAP updates required

- `ccya/state/delta.py`: Update the function docstring and signature to reflect the new return type.
