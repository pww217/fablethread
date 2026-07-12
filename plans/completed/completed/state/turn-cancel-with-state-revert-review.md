## Summary

`approved with notes`. Three stale line number references and one missing import instruction fixed. Two edge cases flagged but not blocking.

## Fixes applied

- **[Step 1.2]** Updated all turn.py line references from the stale original (+13-15 lines off) to current source: acquire at 843, yields at 866/882/923-924/943/947/971/993/1184, finally at 1342, snapshot_state at 1269.
- **[Step 1.2]** Added missing import instruction — `turn.py` must import `is_cancel_requested`, `register_persist`, `register_turn`, `signal_turn_done` from `ccya.engine.config` (line 16), same import block as `_inflight`.
- **[Phase 2 context]** Updated `index.html` send-btn line range from 190-197 to 219-226.
- **[Step 2.2]** Updated `stopTurn()` line reference from 1516 to 1749.

## Findings requiring user input

- **[execution-hazard] Step 2.1** — The cancel endpoint guards on `is_turn_in_progress()`. But `register_turn()` is called BEFORE `_inflight.acquire()` (decision #3). This creates a ~microsecond window where `_turn_done` exists but `is_turn_in_progress` returns False. If a cancel HTTP request lands in this window, it returns early with no effect. The window is too narrow to hit in practice, but if you want to close it entirely, either: (a) move `register_turn` after `acquire` (which breaks the invariant that `_turn_done` always exists while a turn could be running), or (b) have the cancel endpoint additionally check for `_turn_done` key existence.
  **[QUESTION: Accept the narrow race window, or add a `_turn_done` key check to the cancel endpoint?]**

- **[maintainability] Step 1.1** — The plan says `signal_turn_done` cleans up all three dicts. But `await_turn_done` pops from `_turn_done` only, not from the other two. If a turn completes normally (no cancel), `signal_turn_done` must clean `_cancel_requested`, `_turn_done`, AND `_persist_started`. If a turn is cancelled, `signal_turn_done` (via `finally`) and `clear_cancel` (in cancel endpoint) both try to clean `_cancel_requested`. This works but the overlap should be explicitly documented in the `signal_turn_done` implementation to avoid confusion when debugging.
  **[QUESTION: Accept the redundancy (already called out in Firm decisions #7) or refactor so the cancel endpoint does NOT call `clear_cancel` and relies entirely on `signal_turn_done`?]** The timeout path requires `clear_cancel`, so removing it would need an alternative mechanism for the timeout case.

## Contract checks

- [x] `is_turn_in_progress(save_dir: str) -> bool` — PASS (source at config.py:37-39)
- [x] `remove_last_event(save_dir: Path) -> bool` — PASS (source at chronicle.py:68-81)
- [x] `remove_last_chronicle_turn(save_dir: Path) -> bool` — PASS (source at chronicle.py:84-98)
- [x] `restore_snapshot_state(save_dir: Path) -> None` — PASS (source at io.py:155-163)
- [x] `snapshot_state(save_dir: Path) -> None` — PASS (source at io.py:142-152)
- [x] All new function signatures (`request_cancel`, `is_cancel_requested`, etc.) take `save_dir: str` — consistent with existing `is_turn_in_progress` pattern — PASS
- [x] `from ccya.engine` currently exports `is_turn_in_progress` — adding new exports via `__init__.py` follows the same pattern — PASS
- [x] `_inflight.release()` is safe when lock not held (guards with `lock.locked()`) — PASS

## Scope violations

None. No step modifies LLM call paths, TV SSE, or the retry path.

## Format issues

None. All required sections present in correct order. Each step has File/What/Why/Validation.
