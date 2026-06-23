# Thread Resolution Events ≠ Unique Threads

**Status:** open
**Priority:** high
**Component:** storyteller prompt, thread lifecycle
**Related:** [Arc System Redesign](../design/arc-system-redesign.md), [Eval Cycle 2 Report](../../evals/runs/2026-06-22_0.28.0-79-g2b62d1d_2b62d1d/REPORT.md)

## Problem

The storyteller generates `thread_resolve` events for threads that no longer exist in the active thread list. The raw numbers show ~50% resolved, but these are events, not unique threads. The same thread ID appears in multiple resolve entries because the storyteller keeps trying to resolve threads that were already moved to `completed_threads` by a prior arc_resolve. The sanitizer's dedup catches them, but the LLM keeps trying.

**Evidence (Eval Cycle 2):**
- **Zombie:** 12 thread_adds, 19 thread_resolve events, 6 arc_resolves. Many thread_resolves reference threads that were already moved to `completed_threads` by a prior arc_resolve.
- **Noir:** 10 thread_adds, 15 thread_resolve events, 7 arc_resolves. Same pattern.

## Root Cause

The storyteller's user prompt shows **both active threads AND completed threads**:

1. `_thread_list.j2` renders active threads from `all_threads` (source: `state.arc.threads`)
2. `_arc.j2` renders completed threads from `current_arc.completed_threads`

The storyteller sees completed thread IDs in the prompt and tries to resolve them, even though they're no longer in the active list.

The prompt (storytell_system.j2:54) explicitly says:
> CRITICAL: Do NOT resolve threads that do not exist. `thread_resolve` may only reference IDs from the active threads list. If a thread ID is not shown in the active threads list, do NOT resolve it — even if the narration describes events that seem to match. Resolving non-existent threads causes silent failures.

But the storyteller is seeing completed threads in the prompt and trying to resolve them. The "Completed Threads (TTL)" header in `_arc.j2` is not clear enough to prevent this.

### Engine behavior

When a thread_resolve references a thread that's not in the active list, the engine logs a warning and skips it (turn_state.py:324-329):
```python
if found_idx is None:
    _log.warning(
        "thread_resolutions: T%d thread_resolve references unknown id=%s — skipping",
        turn_no, res.id, extra={"turn": turn_no},
    )
    continue
```

This is a "silent failure" — the storyteller thinks it resolved the thread, but the engine silently skips it. The storyteller keeps trying because it doesn't see the warning in its context.

## Suggested Fixes

### Option A: Remove completed threads from storyteller's prompt (recommended)

Remove the "Completed Threads" section from `_arc.j2` in the storyteller's user prompt. The storyteller doesn't need to see completed threads — they're already completed. The only reason to show them is for context, but the storyteller can infer context from the active threads and the narration.

This is the simplest fix and directly addresses the root cause.

### Option B: Add clearer visual distinction

Add a "COMPLETED" label to each thread in the completed threads section, and make the header more prominent. For example:
```
### COMPLETED THREADS (do not resolve these)
- [COMPLETED] `thread_id`: summary
```

This is a weaker fix because the storyteller might still ignore the label.

### Option C: Add a checker that validates thread_resolve events

Add a checker that validates thread_resolve events against the active threads list and reports failures. This would catch the issue early and prevent silent failures. But this doesn't fix the root cause — the storyteller is still seeing completed threads and trying to resolve them.

### Option D: Decouple arc_resolve from thread operations

The arc redesign already plans to decouple `arc_resolve` from thread operations. This would reduce the number of arc_resolves that move threads to `completed_threads`, which would reduce the number of stale resolve events. But this is a longer-term fix and doesn't address the immediate issue.

## Priority

High. This is a structural issue that causes silent failures in the thread lifecycle. The storyteller keeps trying to resolve threads that don't exist, which wastes LLM context/tokens and creates confusion in the eval data.
