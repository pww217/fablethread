---
title: Orphaned sanitizer events after turn cancel/delete
status: done
completed: 2026-06-22
urgency: 1
size: small
created: 2026-06-22
ticket_id: B-16
labels:
  - sanitizer
  - turn-pipeline
  - ui
---

## Problem

`remove_last_event()` in `ccya/state/chronicle.py` removes only the last line from `events.jsonl`. When a turn has a sanitizer event appended after the turn event (every 5 turns), canceling or deleting that turn leaves the sanitizer event orphaned.

**Symptoms:**
- Duplicate turn entries in the debug panel's turn table (`_recent_turn_metrics`)
- Duplicate turn entries in the turn log panel (`_turn_log_entries`)
- Turn viewer shows sanitizer cards correctly (already filters by `row_kind`)
- Save listing shows inflated turn count (counts sanitizer events as turns)

**Example from `the-outer-rim--after-unification-2026-06-20`:**
```
Event 27 turn=25 kind=turn_complete
Event 28 turn=25 kind=sanitizer    ← orphaned after cancel/delete of turn 25
```

## Root cause

`remove_last_event()` (chronicle.py:99-111) does:
```python
lines = lines[:-1]  # removes only the last line
```

It doesn't check `kind` or `turn` — just blindly removes the last line. When the last turn had a sanitizer run, the sanitizer event is the last line, so it gets removed correctly. But if the user cancels turn 25 and turn 25 had a sanitizer event, the sanitizer event IS the last line and gets removed. However, if the user cancels turn 25 and then turn 26 runs (which has no sanitizer), the turn 25's sanitizer event is NOT the last line — it's buried between turn 25's turn event and turn 26's turn event.

**Actually:** The real issue is that `remove_last_event` removes the last line, which is the turn event. The sanitizer event (which has the same turn number) remains in the file.

## Fix

`remove_last_event()` should parse the last event to get its turn number, then remove ALL events matching that turn number (both turn events and sanitizer events).

**Files to change:**
- `ccya/state/chronicle.py` — `remove_last_event()`
- `ccya/server/routes.py` — `_list_saves()` turn count (bonus fix, already done)
- `ccya/server/metrics.py` — `_recent_turn_metrics()` and `_turn_log_entries()` (bonus fix, already done)

## Related

- Eval report item #9: "Duplicate Turns" — same pattern observed across all 5 evaluation packs
- The sanitizer runs on turns divisible by `sanitize_every` (default 5)
- Every pack showed duplicates at T5, T10, T15, T20, T25
