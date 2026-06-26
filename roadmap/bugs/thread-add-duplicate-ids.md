---
title: Thread Add Creates Duplicate IDs — Storyteller Reuses Active IDs
status: up-next
urgency: 2
size: medium
created: 2026-06-24
labels:
  - engine
  - threads
  - storyteller
---

## Validation

**Validated: confirmed root cause. FIXED.**

### Root Cause Confirmed

`_apply_thread_updates()` in `turn_state.py:17-136` handles `thread_update` events (updates to existing threads). The `thread_dedup_rejections` list is only populated for **progress dedup** (line 79-85) when progress text similarity >= 0.70.

**`thread_add` dedup was silent** — at `turn_state.py:536-537`:
```python
existing_ids = {t.id for t in _existing_arc.threads} | {t.id for t in _existing_arc.completed_threads}
if _new_thread.id not in existing_ids:
    # add thread
# else: silently skip — no logging, no dedup_rejection recorded
```

When the storyteller generated a `thread_add` with an ID that already existed in active or completed threads, the thread was silently discarded. No log message, no `dedup_rejection` entry, no feedback to the storyteller.

### Assessment

This is a real bug. The storyteller had no feedback loop for rejected thread additions.

### Fix Applied (Partial)

1. **Code-level enforcement** (`turn_state.py:563-574`): Added `else` branch for duplicate `thread_add` IDs — logs a warning and records a `dedup_rejection` entry with `rejected_reason: "duplicate_id"` and `similarity: 1.0`.

2. **Prompt-level guidance** (`storytell_system.j2`): Added explicit instruction about unique IDs.

### Still Happening (Eval 2026-06-25)

Despite the fix, duplicate thread_add IDs still occur:
- noir-1930s T23: `dockworker_confrontation` (duplicate)
- space-western T24: `militia_containment` (duplicate)

The prompt guidance is insufficient to prevent the storyteller from generating duplicates. The storyteller needs stronger constraints or a different approach to ID generation.

---

The storyteller generates `thread_add` entries with IDs that already exist in the active threads list. The thread dedup system (`thread_dedup_rejections`) does not catch these.

**Evidence (the-outer-rim save):**

| Turn | thread_add ID | Type |
|------|--------------|------|
| T1 | `corporate_enforcement_presence` | threat |
| T2 | `corporate_audit_tension` | threat |
| T3 | `corporate_pursuit` | threat |
| T4 | `corporate_oversight_crackdown` | threat |
| T5 | `black_market_shipment` | opportunity |
| T6 | `black_market_shipment` | opportunity *(DUPLICATE of T5)* |
| T7 | `unregistered_gear_smuggling` | opportunity |
| T8 | `unregistered_shipment_intercept` | opportunity |
| T9 | `corporate_pursuit` | threat *(DUPLICATE of T3)* |
| T10 | `midnight_shipment_intercept` | opportunity |
| T11 | `ambush_at_ventilation_shaft` | threat |
| T12 | `hostile_confrontation_ventilation` | threat |
| T13 | `unregistered_cargo_standoff` | complication |
| T14 | `unregistered_cargo_transit` | opportunity |

- **15 thread_adds across 14 turns** (M:F 15:1)
- **2 ID duplicates** (T3/T9 both `corporate_pursuit`, T5/T6 both `black_market_shipment`)
- **Only 1 thread_resolve** in the entire game (T9: `unregistered_shipment_intel` resolved)
- **thread_dedup_rejections** is empty on every turn — the dedup system did not reject any duplicates
- The final state (`state.yaml`) shows 4 initial threads from seed, none of the 15 storyteller-generated threads were ever added to state

## Reproduction

```bash
ev.py turn 9 --save-dir saves/the-outer-rim--after-unification-2026-06-24 --json | jq '.extraction.storytell.output.thread_add.id'
ev.py turn 3 --save-dir saves/the-outer-rim--after-unification-2026-06-24 --json | jq '.extraction.storytell.output.thread_add.id'
```

Both return `corporate_pursuit`. The storyteller reuses the same ID for different threads.

## Root Cause Estimate

The storyteller generates thread IDs without checking whether they already exist in state. The `thread_dedup_rejections` mechanism exists in the event schema but is not firing — it may look for exact ID+type+summary matching or may not have access to the active thread list.

Related to existing `thread-resolution-events-not-unique.md` — that bug covers thread_resolve events referencing completed threads. This bug covers thread_add duplicating active thread IDs. Both stem from the storyteller not having reliable access to "what thread IDs are currently in use" in a way it can reference.

## Impact

- Wasted LLM tokens generating threads that are silently discarded
- Storyteller lacks feedback that its thread IDs were rejected
- Thread accumulation rate is inflated in eval data
- Core primitive (thread ID uniqueness) is not enforced

## Suggested Fix

- Expose a flat list of currently-active thread IDs in the storyteller's user prompt (not just summaries)
- Add hard enforcement in `apply_thread_add` that rejects duplicate IDs with a warning in the event
- Consider making thread ID generation deterministic based on thread summary (hash-based) to prevent the storyteller from generating the same ID for different threads
