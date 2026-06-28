---
title: Turn cancel/retry does not fully restore previous state atomically
status: done
urgency: 2
size: medium
created: 2026-06-22
ticket_id: B-4
labels:
  - turn-pipeline
  - cancel
  - retry
  - state
---

## Problem

The turn cancel (`/turn/cancel`) and delete (`/turn/delete`) endpoints restore state by loading `state_snapshot` from the turn event and writing it back. However, several mutations happen after the snapshot is taken, and the restoration is not fully atomic.

## Snapshot timing gap

In `turn.py`, `state_snapshot` is written at line 421:
```python
register_persist(str(save_dir))
save_state(save_dir, state)
event["state_snapshot"] = load_state(save_dir)
append_event(save_dir, event)
```

**After** this point, the following mutations occur:

1. **Prior history bullet** (turn.py:467-475) — appends `- [T{turn_no}] {outcome_summary}` to `meta.prior_history`
2. **Thread sanitizer** (turn.py:477-488) — may mutate `state["arc"]` (threads, completed_threads, visible_goal, goal_context)
3. **State saved again** after sanitizer (turn.py:488)

When canceling, `state_snapshot` reflects the state **before** steps 1 and 2. Restoring it correctly undoes the turn's effects, but:

**Bug 1 — Prior history bullet:** The bullet is appended after `save_state`, so restoring `state_snapshot` correctly removes it. **This is fine.**

**Bug 2 — Sanitizer mutations:** If the sanitizer ran on the canceled turn, `state["arc"]` was mutated after the snapshot. Restoring `state_snapshot` reverts `state["arc"]` to the pre-sanitizer state. **This is correct** — the sanitizer's changes are undone along with the turn.

**Bug 3 — Sanitizer event orphan:** `remove_last_event()` only removes the last line from `events.jsonl`. If the turn had a sanitizer event appended after the turn event, the sanitizer event remains orphaned. **This is the orphaned sanitizer events bug** (separate ticket).

**Bug 4 — Chronicle entry:** `remove_last_chronicle_turn()` removes the last `## Turn N` section from `chronicle.md`. This is correct.

**Bug 5 — Prompts file:** `prompts.jsonl` entries for the canceled turn are NOT removed. The turn's ruling/narrate/extraction prompts remain in `prompts.jsonl` with the canceled turn number. This is a minor inconsistency — the prompts reference a turn that no longer exists.

**Bug 6 — Server errors:** `server_errors.jsonl` entries for the canceled turn are NOT removed. Same minor inconsistency.

**Bug 7 — In-flight lock:** `signal_turn_done()` in the `finally` block (turn.py:552-553) releases the inflight lock and signals turn completion. If cancel is requested mid-turn, the turn exits early via `return` statements at various `is_cancel_requested()` checks (turn.py:108, 131, 175, 197, 203, 238, 264, 343). The `finally` block still runs, so the lock is released. **This is correct.**

**Bug 8 — Partial turn completion:** If cancel is requested after `save_state` but before `append_event` (turn.py:422), the state is saved but the event is not written. The cancel handler then reads `last_events_after` and finds no new event (turn number didn't advance), so it does nothing. **This is correct** — no event to remove.

**Bug 9 — Cancel after append_event but before sanitizer:** If cancel is requested after `append_event` (turn.py:422) but before the sanitizer (turn.py:477), the turn event IS written. The cancel handler removes it. But `prior_history` was already appended (turn.py:467-475 happens before sanitizer). Restoring `state_snapshot` removes the bullet. **This is correct.**

**Bug 10 — Cancel after sanitizer:** If cancel is requested after the sanitizer completes, the turn event and sanitizer event are both written. `remove_last_event()` should remove both (orphaned sanitizer bug). `state_snapshot` restoration undoes sanitizer mutations. **This is correct** except for the orphaned sanitizer event.

## Atomicity concern

The core concern is that cancel/delete is not truly atomic. The sequence is:

1. Request cancel → sets cancel flag
2. Wait for turn to finish → turn exits on next `is_cancel_requested()` check
3. Read last event → get turn event with `state_snapshot`
4. Remove event from `events.jsonl`
5. Remove chronicle entry
6. Restore `state.yaml` from `state_snapshot`

Between steps 4-6, the save is in an inconsistent state:
- `events.jsonl` has been modified (event removed)
- `chronicle.md` has been modified (entry removed)
- `state.yaml` still has the old state (not yet restored)

If the process crashes between steps 4-6, the user has:
- Missing event in `events.jsonl`
- Missing chronicle entry
- State still at the canceled turn's value

**This is unlikely** (all operations are fast file writes), but not impossible.

## Fix

**Option A — Two-phase cancel:**
1. Write the restored state to a temporary file
2. Atomically swap `state.yaml` → `state.yaml.restored`
3. Remove event and chronicle entry
4. If any step fails, restore from the original `state.yaml`

**Option B — Accept the risk:**
The operations are fast enough that crash between them is extremely unlikely. The orphaned sanitizer event bug is the real issue to fix.

**Option C — Redesign cancel as "undo":**
Instead of removing the last turn, keep it but mark it as `cancelled: true`. The UI filters out cancelled turns. This is simpler but changes the data model.

## Recommendation

Fix the orphaned sanitizer event bug first (small change). The atomicity concern is theoretical — the operations are fast and the user would need to crash exactly between file writes. Not worth the complexity of Option A unless crashes are observed.

**Files to change:**
- `ccya/state/chronicle.py` — `remove_last_event()` (orphaned sanitizer bug)
- `ccya/server/routes.py` — `cancel_turn()` and `delete_last_turn()` (consider cleaning `prompts.jsonl` and `server_errors.jsonl`)
