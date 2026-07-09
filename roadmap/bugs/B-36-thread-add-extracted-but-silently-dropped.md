---
title: "thread_add extracted but silently dropped — never applied to arc.threads"
status: done
urgency: 3
size: medium
created: 2026-07-06
completed: 2026-07-06
ticket_id: B-36
labels:
  - engine
  - threads
  - extraction
---

## Resolution

**Root cause confirmed via event data analysis.**

`physical_bypass_retrieval` (T4 zombie) was blocked by `thread_creation_cooldown=3` at `turn_state.py:533`. `last_thread_creation_turn=3` (set by T3), so `4-3=1 < 3` → cooldown blocks. The cooldown path logs only `_log.debug` (not written to event) and does NOT append to `thread_dedup_rejections`. This is an observability gap, not a logic bug — the thread should never have been extracted so soon after the last one.

**Two issues found:**
1. **Silent cooldown** — no rejection written to event, no warning-level log
2. **Silent exception** — try/except at line 590-594 logs warning but doesn't add to rejections list

**Fix:** Add rejection to `thread_dedup_rejections` on cooldown path. Upgrade cooldown log to warning level.
urgency: 2
size: small
created: 2026-07-06
ticket_id: B-36
labels:
  - engine
  - threads
  - extraction
---

## Detail

During E-11 thread lifecycle deep dive on zombie-survival:cautious (25t), found that `physical_bypass_retrieval` was extracted as a thread_add event at turn 4 but never applied to `arc.threads`. The thread was extracted (visible in `extraction.record.output.thread_add`) but never appears in any turn's `pacing_context.convergence_threads` — confirming it was silently dropped.

### Evidence

**Zombie-survival 25t run:**
- Turn 4 extraction output includes `thread_add: {id: "physical_bypass_retrieval", urgency: "urgent", type: "opportunity"}`
- No dedup rejection or cooldown rejection logged for this thread at turn 4
- `physical_bypass_retrieval` never appears in any turn's `pacing_context.convergence_threads`
- Thread lifecycle shows it as "active" with 0 updates and never resolved — extracted but abandoned

**Comparison — locker_security_lockdown (turn 6):**
- Same extraction pattern: thread_add at turn 6
- Appears in turn 7's convergence_threads with `added_turn: 6`
- Resolved at turn 7 (1-turn lifetime) — valid lifecycle

**Difference:** locker_security_lockdown was applied to arc.threads; physical_bypass_retrieval was not.

### Suspected cause

In `ccya/engine/turn_state.py:530-589` (`_apply_state_updates`), thread_add is gated by:
1. Cooldown check (line 533) — if cooldown not met, rejected with `rejected_reason: "cooldown"`
2. Duplicate ID check (line 553) — if ID exists in `arc.threads | arc.completed_threads`, rejected with `rejected_reason: "duplicate_id"`

If neither condition triggers, the thread should be added to `arc.threads`. The fact that physical_bypass_retrieval was extracted but never applied suggests either:
- A silent exception in the arc validation block (lines 550-594) that was logged but not reflected in events
- The thread was added at `state.meta.turn + 1` (turn 5) but evicted by `thread_max_active` cap before being observable
- A race condition where thread_add is applied after convergence_threads is serialized for the event

### Impact

- Threads extracted by storyteller can be silently lost without any indication in events
- Player may believe a thread exists (extraction output shows it) but it has no effect on gameplay
- No dedup rejection or error logged, making debugging difficult

### Files

- `ccya/engine/turn_state.py:530-589` — thread_add application logic
- `ccya/engine/turn.py:507-534` — `_apply_phase` orchestration
