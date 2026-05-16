# Fix: Condition Re-add After Delta Validation Failure

## Status
`completed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Trace the failure path | Confirm delta validation failure suppresses all delta ops, including condition add |
| 02 | Fix: partial delta application or explicit condition dedup fallback | Either apply safe ops even when delta has validation errors, or tighten dedup |

## Objective
When a turn's delta fails validation (e.g., due to a malformed inventory or scope violation), the entire `StateDelta` may be discarded. If that delta contained a `pc_condition_add`, the condition is never written to state. On the next turn, the extractor re-observes the condition from the narration and emits it again. `reconcile_delta` has a dedup guard, but if the condition never made it to state, the guard sees it as novel and allows the add. This results in the condition appearing to be added twice (from the player's perspective) or being permanently delayed. The fix should ensure condition state is resilient to partial delta failures.

## Non-goals
- Do not change `reconcile_delta`'s behavior for the happy path.
- Do not change how inventory or scene ops are validated.
- Do not relax validation rules — failed deltas should still be flagged.

## Implementation — Phase 01: Trace the failure path

### Files to pull for context
- `ccya/engine/turn.py` — find where `reconcile_delta` and `apply_delta` are called; find where delta validation errors are handled.
- `ccya/state/delta.py` — `reconcile_delta`, `apply_delta`.
- `ccya/eval/` — read `REPORT.md` or event log structure to understand what "delta validation failure" looks like in the turn event.

### Detailed steps

#### Step 1.1 — Locate the delta validation + apply block in turn.py

**File:** `ccya/engine/turn.py`

**What:** Find the section after `_run_extraction_pipeline` where `reconcile_delta` is called and `apply_delta` is called. Determine: is there any `try/except` or `if errors:` branch that skips `apply_delta` entirely when `reconcile_delta` returns warnings?

**Why:** If `apply_delta` is skipped when `reconcile_delta` returns any warning, then a turn with even a minor inventory conflict will suppress the condition add. If `apply_delta` is always called (and warnings are just logged), then the bug is elsewhere.

**Validation:** Read the code block. Produce a one-line description of what happens when `reconcile_delta` returns a non-empty `warnings` list.

#### Step 1.2 — Check if eval REPORT shows a delta error on the turn before condition re-add

**What:** In the eval session described (T7 had delta validation failures, T8 re-added `shoulder_bruise`), check the `events.jsonl` or `REPORT.md` for T7 to confirm:
1. Was a `pc_condition_add` for `shoulder_bruise` present in T7's delta?
2. Did T7's delta have a validation error?
3. After T7, is `shoulder_bruise` absent from `state.pc.conditions`?

**Why:** Confirms the causal chain before writing code.

**Validation:** Produce a yes/no answer for each of the 3 questions.

#### Step 1.3 — Confirm reconcile_delta's dedup guard sees pre-apply state

**File:** `ccya/state/delta.py` — `reconcile_delta`

**What:** `reconcile_delta` builds `existing_conds` from `state["pc"]["conditions"]` at call time. If T7's condition add was never applied (apply_delta was skipped or failed), then at T8's `reconcile_delta` call, `existing_conds` will NOT contain `shoulder_bruise`, and the T8 add will pass through unchecked. Confirm this is the actual flow.

**Validation:** Trace the code path. If `apply_delta` is always called even with reconcile warnings, then the condition IS applied at T7 and the T8 re-add should be caught by reconcile. If that's the case, the bug is that `apply_delta` itself is failing or throwing mid-execution and leaving a partial state.

### Tests to write or update
None for Phase 01 — read-only diagnosis.

### REPOMAP and architecture updates
None.

### Risks
1. The actual failure mode may be different from the hypothesis — mitigation: do not write any fix code until Step 1.3 confirms the causal chain.

## Implementation — Phase 02: Fix dedup resilience

### Files to pull for context
- All Phase 01 files.
- `ccya/state/delta.py` — full `apply_delta` function.

### Detailed steps

#### Step 2.1 — (If apply_delta is skipped on reconcile errors) Apply safe ops even when delta has warnings

**File:** `ccya/engine/turn.py`

**What:** If the code currently reads:

```python
warnings = reconcile_delta(state, delta)
if warnings:
    # skip apply_delta
    pass
else:
    state, evicted = apply_delta(state, delta)
```

Change to always call `apply_delta`:

```python
warnings = reconcile_delta(state, delta)
for w in warnings:
    _log.warning("delta reconcile: %s", w, extra={"turn": turn_no, "trace_id": trace_id, "pack": "", "kind": "delta"})
state, evicted = apply_delta(state, delta)
```

**Why:** `reconcile_delta` is a sanitizer, not a gate. Its job is to clean the delta in place. `apply_delta` should always run on the (now-cleaned) delta.

**Validation:** Unit test: call `reconcile_delta` on a delta with an inventory conflict + condition add, then call `apply_delta`. Confirm the condition IS applied even though reconcile issued a warning.

#### Step 2.2 — (If apply_delta throws mid-execution) Add condition-apply safety net

**File:** `ccya/state/delta.py` — `apply_delta`

**What:** If `apply_delta` raises mid-execution (e.g., during inventory processing), the deepcopy at the top means state is not mutated. But the condition block is near the bottom. If an exception occurs before the condition block runs, conditions are lost.

Wrap the condition block in its own try/except so condition ops are never silently lost:

```python
try:
    # ... existing condition add/remove logic ...
    state["pc"]["conditions"] = existing_conds[-PC_CONDITIONS_MAX:]
except Exception as exc:
    _log.error(
        "apply_delta: condition block failed: %s",
        exc,
        extra={"turn": 0, "trace_id": "", "pack": "", "kind": "delta"},
    )
    raise
```

**Why:** If an unhandled exception exits `apply_delta` before the condition block, the return never happens and the caller gets nothing. Making the failure visible aids debugging.

**Validation:** Unit test: construct a delta where inventory processing would raise (e.g., mock `_strip_non_ascii` to throw), confirm the exception propagates cleanly and is logged.

#### Step 2.3 — Tighten reconcile_delta condition dedup to include pending adds in same delta

**File:** `ccya/state/delta.py` — `reconcile_delta`

**What:** The current dedup in `reconcile_delta` checks `existing_conds` (conditions already in state). If the SAME condition is added twice in the same delta (two `pc_condition_add` entries with the same `id`), the second one passes through and `apply_delta` silently ignores it only because `existing_ids` is updated in-place during the loop. This is fragile. Add an explicit within-delta dedup:

```python
# Within-delta dedup: drop duplicate condition adds within the same delta
seen_adds: set[str] = set()
deduped_adds = []
for c in delta.pc_condition_add:
    if c.id not in seen_adds:
        deduped_adds.append(c)
        seen_adds.add(c.id)
    else:
        warnings.append(f"duplicate condition add within delta: {c.id}")
delta.pc_condition_add = deduped_adds
```

**Why:** Defense in depth. Even if the extractor emits the same condition add twice in one delta, only one survives.

**Validation:** Unit test: `reconcile_delta` with a delta containing `pc_condition_add` with two entries for the same `id`. Confirm only one survives and a warning is issued.

### Tests to write or update
- `tests/test_engine_smoke.py` or new `tests/test_state_delta.py`:
  - `test_reconcile_dedup_within_delta`: confirms within-delta condition dedup.
  - `test_apply_delta_condition_survives_inventory_conflict`: confirms condition add is applied even when reconcile issued an inventory conflict warning.
- `tests/test_engine_pipeline.py`: add a multi-turn scenario where T1 has an inventory conflict in delta + condition add; assert condition appears in state after T1.

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md`: update `reconcile_delta` notes to describe within-delta condition dedup.

### Risks
1. Phase 02 step selection depends on Phase 01 findings — executor must read Phase 01 output before choosing Step 2.1 vs 2.2. Both may be needed.
2. Always-calling `apply_delta` even with reconcile warnings changes behavior for inventory conflict cases — mitigation: reconcile already mutates `delta` in place to remove conflicts before returning, so `apply_delta` receives a clean delta regardless.

## Ambiguities requiring resolution before execution
1. Does `turn.py` currently skip `apply_delta` when `reconcile_delta` returns warnings, or is `apply_delta` always called? Options: A) skipped — Step 2.1 is the primary fix. B) always called — focus on Step 2.2 and 2.3.
2. Is `apply_delta` wrapped in a try/except in `turn.py` that catches ALL exceptions and leaves state unchanged? If so, is the original (pre-deepcopy) state restored or is there simply no mutation? Options: A) exception means state is unchanged (deepcopy in `apply_delta` protects this). B) exception means partial state is written — this would be a separate bug.
