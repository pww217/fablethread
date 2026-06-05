# Block Phantom Inventory Removals at Validation Time

## Status
`completed`

## Issue

State Extract emits `inventory_remove` deltas for items that do not exist in inventory or have zero balance across multiple turns (T6, T7, T9, T13). The validation pipeline does NOT block these — it silently drops them at debug level:

- `_validate()` (turn.py:~1452): missing targets get `continue`, NOT added to rejections
- `apply_delta()` (delta_builder.py:~175): same check, logs debug only, continues
- Pipeline in `run_turn()` (~line 1109): blocking errors append message but still proceed through `reconcile_delta` → `apply_delta`

Result: phantom removals pollute `events.jsonl`, eval assertions fail on emission values that never actually corrupt state. Users see "That action didn't resolve" text but get no structured feedback about why extraction failed.

## Solution

Two changes in turn.py (~5 lines total):

### Step 1 — Make missing inventory targets a rejection (turn.py ~line 1452-1459)

Change the `continue` for missing items into an append to `rejections`:

```python
# Before:
if canonical is None:
    _log.debug("inventory_remove target %r not found...")
    continue

# After:
if canonical is None:
    rejections.append({
        "field": "inventory_remove",
        "kind": "missing_target",
        "value": rem.id,
        "reason": f"Item '{rem.id}' not found in inventory",
    })
```

### Step 2 — Return early on blocking errors (turn.py ~line 1109-1124)

Add `return` after the blocking error block so rejected deltas never reach `reconcile_delta`/`apply_delta`:

```python
if blocking:
    errors.append(...)
    narrative += "...That action didn't resolve..."
    # ADD: return early — do not apply rejected delta
    state = _record_turn_result(state, turn_no, ruling, narr, trace_id, metrics, applied, rejected, errors)  # or whatever the existing record call is
    continue  # skip to next iteration / end of turn processing
```

## Firm decisions

1. Only `inventory_remove` for missing targets gets blocking behavior — zero-balance items are already rejected (they `continue` in _validate), overdraw warnings remain non-blocking as before.
2. No changes to delta_builder.py or extraction prompts — this is a validation-layer fix only.
3. The early return should follow the existing pattern used elsewhere for turn cancellation/early exit.

## Non-goals

- Not changing State Extract prompt (extraction accuracy is a separate issue)
- Not adding condition legality checks (separate issue, tracked as M2 in EVAL-FINDINGS.md)
- Not modifying eval assertions — they will naturally pass once phantom values stop polluting events.jsonl
- Not handling `pc_condition_add` legality at any layer

## Risks, Ambiguities, and Blockers

- Need to confirm the exact early-return pattern used elsewhere in turn.py (e.g., _record_turn_result or similar). The pipeline is ~1050 lines — need to find the correct return/cancel path.
- No blocker on validation logic itself — it's a straightforward `continue` → `rejections.append()` swap plus an early return.

---

## Implementation — Phase 1: Make _validate reject missing targets + block at pipeline level

### Context files to load
- `ccya/engine/turn.py` (lines ~1095-1160, ~1445-1495)

### Detailed steps

#### Step 1.1 — Add missing_target rejection in _validate()

**File:** `ccya/engine/turn.py`, lines ~1452-1459

**What:** Replace the `continue` for missing inventory targets with an append to `rejections`:

```python
if canonical is None:
    rejections.append({
        "field": "inventory_remove",
        "kind": "missing_target",
        "value": rem.id,
        "reason": f"Item '{rem.id}' not found in inventory",
    })
```

**Why:** Currently missing targets are silently skipped (not rejected), so they never get caught by the blocking check at line ~1109. This change makes them part of `rejections` so the pipeline can block on them.

#### Step 1.2 — Return early when there are blocking errors in run_turn()

**File:** `ccya/engine/turn.py`, lines ~1107-1137

**What:** After the existing `if blocking:` block (lines ~1110-1118), add an early return that skips `reconcile_delta` and `apply_delta`. The exact mechanism depends on how turn cancellation is handled — need to find the correct pattern in the surrounding code.

The key change: when `blocking` is non-empty, do NOT proceed to lines 1119-1124 (`reconcile_delta`, `apply_delta`). Instead, record what was attempted (empty or partial applied state) and return from turn processing.

**Why:** Currently the pipeline always proceeds through reconcile/apply regardless of validation failures. This means phantom deltas reach events.jsonl even when _validate catches them. Returning early prevents this.

### Tests to write or update
- No tests — per AGENTS.md, tests are temporarily removed during refactor phase. Run `make check` (lint + typecheck) as final verification.
