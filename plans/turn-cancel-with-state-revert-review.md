## Summary

`approved with notes`. Two blocks-execution issues found and fixed in the plan. One blocks-execution and one execution-hazard remain as `[QUESTION: ...]` entries for the user to decide.

## Fixes applied

- **[Step 1.2 — mechanism]** Replaced "raise a local `_TurnCancelled` exception" with `return`. The plan called for an undefined exception class plus `except _TurnCancelled: raise` before each existing except block. `return` inside an async generator's `try` achieves the same: `finally` runs, generator stops, no new class needed. Simpler and correct.

- **[Step 1.2 — ordering]** `register_turn()` was placed after `_inflight.acquire()`. If a cancel request arrived in the microsecond window between `acquire()` completing and `register_turn()` executing, `_turn_done` wouldn't exist yet and `await_turn_done` would fail. Fixed: moved `register_turn()` before `acquire()`.

- **[Steps 1.1, 2.1 — persist guard]** `restore_snapshot_state` was called unconditionally in the cancel endpoint. But `state_snapshot.yaml` always reflects the state BEFORE the last completed persist — not the state before the current running turn. If cancel happens before this turn's persist phase starts, restoring the snapshot would revert TWO turns (losing the last completed turn). Added `_persist_started: dict[str, bool]` flag set right before `snapshot_state()`; cancel endpoint checks it before restoring.

- **[Step 1.1 — cleanup]** `signal_turn_done()` now cleans up ALL three per-save-dir dict entries (`_cancel_requested`, `_turn_done`, `_persist_started`), preventing dictionary bloat on normal completions.

- **[Step 2.3 — trimmed imports]** Removed `is_cancel_requested`, `register_turn`, `register_persist`, `signal_turn_done` from the routes.py import list — these are never referenced in routes.py. Only `request_cancel`, `clear_cancel`, `await_turn_done` are needed.

- **[Phases section]** Removed literal `[...]` brackets that read as unfilled placeholders.

## Findings requiring user input

- **[blocks-execution] Step 2.1** — The `register_persist_flag` check is described in prose but the snippet still shows a placeholder `... register_persist_flag = ...  # see Step 1.1`. The executor needs to know the exact expression: `_persist_started.pop(str(_app_mod.SAVE_DIR), False)`. However, `_persist_started` is a module-level dict in `ccya/engine/config.py`, not directly accessible from `routes.py`. The functions `register_persist()` and a new `was_persist_started(save_dir) -> bool` (or using `_persist_started.pop(...)` directly) need to be exposed via the public API. **[QUESTION: Should we add a `pop_persist_started(save_dir) -> bool` function in config.py to encapsulate the access, or should the cancel endpoint call `_persist_started.pop(...)` directly?]** The latter requires importing `_persist_started` from config which is an internal module — violates the encapsulation pattern used by `_inflight` / `_cancel_requested`.

- **[execution-hazard] Step 1.1** — `signal_turn_done()` is described as cleaning "ALL per-save-dir lifecycle dict entries." This includes `_cancel_requested`, `_turn_done`, and `_persist_started`. But the cancel endpoint also calls `clear_cancel()` AFTER `await_turn_done()`, which means it tries to clean `_cancel_requested` after `signal_turn_done` already did. This is safe (idempotent, `dict.pop` with default) but the interplay should be documented to avoid confusion when debugging. **[QUESTION: Accept the mild redundancy, or change the cancel endpoint to skip `clear_cancel()` since `signal_turn_done()` already handles it?]**

## Contract checks

- [x] Signature of `is_turn_in_progress` matches call sites — PASS
- [x] Signature of `remove_last_event` / `remove_last_chronicle_turn` (takes `Path`) matches `_app_mod.SAVE_DIR` — PASS
- [x] Signature of `restore_snapshot_state` (takes `Path`) matches call site — PASS
- [x] Template variables / frontend — no template changes in this plan — PASS
- [x] `_inflight.release()` is safe when lock not held — PASS (guards with `lock.locked()`)

## Scope violations

- None. The plan does not touch LLM calls, TV SSE, or the retry/snapshot path.

## Format issues

- None after fixes. Sections in correct order, each step has File/What/Why/Validation, phases are numeric and dependency-ordered.
