# Plan 1: Thread Add Gate Bypass Bug Fix

## Status
`completed`

## Phases

1 phase: enforce PacingContext gate on thread_add in turn.py to prevent unbounded thread proliferation when deescalation is active.

## Issue

The comment at `ccya/engine/turn.py:1321` states "Handle thread_add as new arc thread (only when gate == 'allow')" but the code body at lines 1322-1351 never checks `_pc.gate`. It only verifies that the scope is not "scene" and that the thread ID doesn't already exist. This means any LLM can emit `thread_add` every turn regardless of pacing context, bypassing the deescalation gate entirely.

The storyteller prompt (`storytell_system.j2:38`) instructs the LLM to only emit thread_add when gate is "allow", but this is a soft instruction with no Python-side enforcement. If the LLM ignores or misunderstands the instruction (which happens), new threads are created unboundedly, violating `_ACTIVE_THREAD_CAP=3` and causing thread proliferation that degrades narrative focus.

## Solution

Add an explicit `gate == "allow"` check around the thread_add processing block in turn.py:1322-1351. When gate is not "allow" (i.e., "block_escalate"), log a debug message and skip thread creation for that turn. This makes Python enforce what the prompt already instructs, providing defense-in-depth against unbounded thread growth during post-success recovery periods.

## Firm decisions

1. The gate check applies to both `block_add` and `block_escalate` — neither allows new thread additions. Only `"allow"` permits creation.
2. Existing thread advance/resolve operations are unaffected; the gate only controls `thread_add`. This is already the documented design in `_apply_thread_signals()` which processes advances independently of gate state.
3. The check uses `_pc.gate` directly (the local PacingContext variable) rather than passing a separate boolean parameter, since `_pc` is already available in scope at line 1263 and referenced throughout this function body.

## Non-goals

- Does not fix the thread promotion cooldown bypass (latent threads promoted immediately on unknown advance IDs — documented behavior per comment at turn.py:174).
- Does not add a per-turn-count throttle on how frequently new threads can be added (separate tuning item in Plan 5).
- Does not modify the storyteller prompt or PacingContext model.

## Risks, Ambiguities, and Blockers

**Ambiguity:** What should happen when gate blocks thread_add — silently skip with debug log, or emit a warning? Debug is sufficient since this is expected behavior during deescalation turns (deescalate >= 0.5 fires after successful rolls). Warning would be noisy.

**Risk:** If `_pc` becomes None in some code path, the check must handle it gracefully. Current usage at line 1443 already guards with `if _pc else "allow"`, so the same pattern applies here: gate blocks only when explicitly non-allow; None defaults to allow (backward compatible).

**Blocker:** None. This is a single-location change in turn.py with no cross-module contract changes.

## Implementation — Phase 1: Enforce PacingContext gate on thread_add

### Context files to load
- `ccya/engine/turn.py` — full file; only lines 1320-1352 are modified
- No other source files need modification

### Detailed steps

#### Step 1.1 — Add gate check around thread_add processing block

**File:** `ccya/engine/turn.py`

**What:** At line 1321, change the comment to reflect enforcement (not just documentation) and add a guard clause that checks `_pc is not None and _pc.gate == "allow"` before entering the existing thread_add logic. The scope-check at lines 1325-1327 uses `pass` (no-op for scene-scoped threads), not an early return; place the gate check as another guard alongside it.

Specifically:
- Line 1321 comment stays but update to reflect enforcement ("Enforce PacingContext gate on thread_add")
- After line 1324 (`_scope = getattr(_new_thread, "scope", "arc")`), add a gate check before the scope check at lines 1325-1327:
```python
if _pc is None or _pc.gate != "allow":
    _log.debug("thread_add blocked by pacing gate %s at T%d", getattr(_pc, 'gate', 'unknown'), turn_no_for_add)
    pass  # skip thread creation — same pattern as scene-scope check below
```
- The existing scope-check (`_scope == "scene"`) continues to use `pass` (no-op); gate and scope guards are independent early-exits.

The guard uses `_pc.gate`: blocks when not `"allow"` (i.e., both `block_add` and `block_escalate`). If `_pc is None`, defaults to allow for backward compatibility.

**Why:** The comment on line 1321 documents an intended invariant that is not enforced in code. Python must enforce what the storyteller prompt already instructs, providing defense-in-depth against LLM thread proliferation during deescalation turns. Without this check, `_ACTIVE_THREAD_CAP=3` can be bypassed indefinitely via thread_add signals.

**Validation:** Run `make check` to confirm no lint or type errors. The change is a guard clause addition with no interface changes — existing callers are unaffected.

### Tests to write or update

Add one test in `tests/test_thread_signals.py` (or create if file does not exist):

- **Test: thread_add blocked when gate is block_escalate**
  - Setup: Minimal state with arc containing 0 active threads, storyteller_result with a valid thread_add object
  - Mock `_compute_pacing_context` to return `PacingContext.gate = "block_escalate"` (or set via direct injection)
  - Run the turn pipeline through extraction + thread processing
  - Assert: arc.threads does NOT contain the new thread; debug log was emitted

- **Test: thread_add allowed when gate is allow**
  - Same setup but with `PacingContext.gate = "allow"`
  - Assert: arc.threads DOES contain the new thread with active=True, last_seen_turn set

### REPOMAP updates required

None. This change does not modify any public API, model shape, or cross-module contract. The PacingContext gate field already documented at repomap.md line 139; only its enforcement location is corrected in source code.
