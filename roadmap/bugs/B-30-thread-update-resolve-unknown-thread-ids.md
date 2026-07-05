---
title: "Thread update/resolve references unknown thread IDs — no thread_add events"
status: canceled
urgency: 2
size: medium
created: 2026-07-05
ticket_id: B-30
labels:
  - engine
  - threads
  - extraction
---

## Description

`thread_update` and `thread_resolve` events in extraction output reference thread IDs that were never added via `thread_add`. The storyteller is updating/resolving threads that don't exist in state.

### Evidence (space-western:speedrunner, 0002, turns 1-9)

**No `thread_add` events exist in the entire run.**

But `thread_update` and `thread_resolve` reference these IDs:

| Turn | Event | Thread ID | Details |
|------|-------|-----------|---------|
| 1 | thread_update | `guild_politics` | urgency=normal, type=complication |
| 2 | thread_update | `guild_politics` | urgency=normal, type=complication |
| 3 | thread_update | `guild_politics` | urgency=urgent, type=threat |
| 4 | thread_update | `guild_politics` | urgency=normal, type=threat |
| 5 | thread_update | `guild_politics` | urgency=normal, type=opportunity |
| 6 | thread_update | `guild_politics` | urgency=normal, type=complication |
| 7 | thread_update | `guild_politics` | urgency=urgent, type=threat |
| 8 | thread_update | `coalition_pursuit` | dormant=True, urgency=normal |
| 8 | thread_resolve | `guild_politics` | resolution_state=resolved |
| 9 | thread_update | `hidden_cargo` | urgency=normal, type=revelation |
| 9 | thread_resolve | `coalition_pursuit` | resolution_state=resolved |

Three thread IDs affected: `guild_politics`, `coalition_pursuit`, `hidden_cargo`.

## Investigation Results (2026-07-05) — FALSE POSITIVE

**All three threads were seeded at turn 0 during `prepare_seed()`, not via `thread_add`.** 

Checked `state.yaml` — all threads have `added_turn: 0`:
- `guild_politics` — RESOLVED (resolved_turn: 9)
- `coalition_pursuit` — RESOLVED (resolved_turn: 9)
- `hidden_cargo` — ACTIVE (still in long_term_objective.threads)

The storyteller correctly used `thread_update`/`thread_resolve` for existing threads. The LLM output was verified — no `thread_add` events were emitted because none were needed.

**Root cause of B-30:** The `thread_lifecycle` checker is too strict — it expects `thread_add` for every thread that gets updated, but doesn't account for threads seeded at turn 0 (which are valid active threads).

## Recommendation

Update the `thread_lifecycle` checker to treat threads with `added_turn: 0` as valid active threads (seeded at init, not via storyteller). This is the correct behavior — seed threads are legitimate LTO threads that should be updatable by the storyteller.
