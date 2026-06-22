# Fix Floor Relief Override Bug

## Purpose

Fix the floor relief mechanism so that when `beat_locked=True` and Storyteller emits a pressure-type beat, it is correctly overridden with `breathing_room` before delta application — not after.

## Problem Statement

The floor relief injection runs AFTER `apply_delta()` returns. When Storyteller emits a pressure-type beat (`complication`, `pressure`, `escalation`) while `beat_locked=True`, the beat is already written to `state["meta"]["pending_gm_beat"]` by the time floor relief checks it at line 1115. The override is applied to the deep copy returned by `apply_delta`, but the original `state` object (used by subsequent code) retains Storyteller's pressure-type beat. This causes the pressure loop to persist for turns 8–10 despite the lock being active.

## Constraints

- Must not change the beat lifecycle semantics (beats shape atmosphere, not immediate mechanical feedback)
- Must not break the null-emit case where floor relief correctly injects `breathing_room` (verified on turns 7, 11)
- Must not modify `apply_delta` — it does not touch `pending_gm_beat`
- Must preserve `beat_expires_turn` TTL semantics

## Non-goals

- Does not fix extraction issues (phantom inventory removal, amount mismatch)
- Does not modify `PacingContext` dataclass or `_compute_pacing_context` signature
- Does not change when `beat_locked` is computed

## Solution

Inject floor relief BEFORE `apply_delta()` runs — immediately after Storyteller's `gm_beat` is written to `state["meta"]["pending_gm_beat"]` (around line 1030). This ensures the `breathing_room` override is in the state before the deep copy is made, so `apply_delta` preserves it. Remove the post-`apply_delta` floor relief injection (lines 1114–1123) since the early injection handles it. The early injection is gated on `_pc.beat_locked` which is already computed before the extraction pipeline runs.

## Firm decisions

1. Floor relief injection moves to BEFORE `apply_delta()`, not after
2. Early injection gate: `_pc.beat_locked and (_current_beat is None or _current_beat["type"] in PRESSURE_BEAT_TYPES)` → inject `breathing_room`
3. Post-`apply_delta` injection (lines 1114–1123) is removed — redundant and runs too late
4. `beat_expires_turn` set to `turn_no + 2` (matches storyteller emission TTL at line 1027; eliminates pre-existing mismatch with floor relief's old +3)
5. `surface_as` remains `"ambient"` (same as current)

## Risks, Ambiguities, and Blockers

- No blockers identified. `_pc` is computed at line 813 before extraction pipeline starts at line 994; in scope inside the try block.
- The universal assert `universal.pacing.floor_relief` currently passes for turns 8–10 (claiming injection happened) but state shows `complication` — this contradiction needs verification: if the fix works, the assert will still pass but now correctly reflects the override.
- No other blockers identified.

## Status
`completed`

## Phases
1 phase: Move floor relief injection from post-apply to pre-apply in `turn.py`

## Implementation — Phase 1: Move floor relief injection pre-apply_delta

### Context files to load

- `ccya/engine/turn.py` — lines 1000–1040 (extraction pipeline end), lines 1108–1135 (current floor relief injection)
- `ccya/engine/turn.py` — lines 520–570 (`_compute_pacing_context` and `PacingContext` dataclass)
- `ccya/engine/turn.py` — line 64 (`PRESSURE_BEAT_TYPES` constant)
- `evals/runs/20260605T202442Z_havr6lvx/REPORT.md` — verification baseline (turns 8–10 failure)

### Detailed steps

#### Step 1.1 — Compute `beat_locked` before extraction pipeline

**File:** `ccya/engine/turn.py`

**What:** Ensure `beat_locked` is computed and available before the extraction pipeline runs, so the early floor relief injection can reference it. Currently `_pc` (containing `beat_locked`) is computed at lines 806–810, before the async generator for extraction starts at line 993. Confirm `_pc` is not None at the point where early injection will run (line ~1031).

**Why:** The early injection needs `_pc.beat_locked` to gate whether to override. `_pc` is already in scope in the try block at lines 993–1015.

**Validation:** Read lines 806–815 to confirm `_pc` assignment and scope.

---

#### Step 1.2 — Add early floor relief injection after Storyteller's gm_beat is written

**File:** `ccya/engine/turn.py`

**What:** After line 1030 (`state.get("meta", {}).pop("pending_gm_beat", None)`) and before `yield ("phase", {"phase": "extract_done"})` at line 1034, add the floor relief injection. The injection checks `_pc.beat_locked` and whether the current `pending_gm_beat` is None or a pressure type — if so, overrides with `breathing_room`.

**Why:** This runs AFTER Storyteller's `gm_beat` has been written to `state["meta"]["pending_gm_beat"]` (line 1028) but BEFORE `apply_delta()` is called (line 1111). The override is now in `state` before the deep copy, so `apply_delta` preserves it.

**Why (cont.):** The null-emit case (turns 7, 11) will be handled: if Storyteller emitted nothing, `pending_gm_beat` was popped at line 1030, `_current_beat` will be None, and the injection will fire correctly.

**Code to add (after line 1030, before line 1032):**

```python
# Floor relief injection — runs BEFORE apply_delta so breathing_room
# persists through the deep copy. Post-apply injection (lines 1114–1123) is removed.
if _pc.beat_locked:
    _current_beat = state.get("meta", {}).get("pending_gm_beat")
    if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
        meta = state.setdefault("meta", {})
        meta["pending_gm_beat"] = {
            "type": "breathing_room",
            "surface_as": "ambient",
            "beat_expires_turn": turn_no + 2,
        }
```

**Validation:** `grep -n "Floor relief injection" ccya/engine/turn.py` — should find the new injection at line ~1031.

---

#### Step 1.3 — Remove the post-apply_delta floor relief injection

**File:** `ccya/engine/turn.py`

**What:** Remove the floor relief injection block currently at lines 1114–1123 (the code that checks `_pc.beat_locked` and overrides `pending_gm_beat` after `apply_delta` returns). Keep the `recent_beats` append at lines 1124–1135 which snapshots `pending_gm_beat` after all modifications.

**Why:** Redundant — early injection (Step 1.2) handles the override before the deep copy. The post-apply injection runs too late to be useful and is the source of the bug.

**Why (cont.):** Keeping the `recent_beats` snapshot is correct — it records the final state of `pending_gm_beat` after early injection (which is the authoritative value).

**Validation:** `grep -n "Inject floor relief" ccya/engine/turn.py` — should only find the early injection. The post-apply block (lines 1114–1123) should be gone.

---

#### Step 1.4 — Verify `recent_beats` snapshot reads correct beat

**File:** `ccya/engine/turn.py`

**What:** Confirm that the `recent_beats` snapshot at lines 1124–1131 reads `pending_gm_beat` from the state returned by `apply_delta` (which now contains the `breathing_room` override from early injection). The snapshot should record `type: breathing_room` for turns 8–10, not `complication`.

**Why:** Ensures beat history reflects the corrected behavior.

**Validation:** No code change — confirm the existing logic at lines 1124–1131 reads `state.get("meta", {}).get("pending_gm_beat")` which now contains the overridden value.

---

#### Step 1.5 — Run eval to verify fix

**What:** Run the eval harness against the `full_cycle` scenario and verify that turns 8–10 no longer show `FLOOR_RELIEF_MISS` in the state_correctness trace, and that `universal.pacing.floor_relief` passes for all turns.

**Why:** Confirms the fix resolves the observed failure.

**Validation:**
```bash
cd /Users/pwilson/Repos/ccya && python -m ccya.eval run --pack eval-pack --scenario full_cycle
```

Expected: state_correctness trace shows `pending_gm_beat` as `{type: breathing_room}` for turns 8–10. `universal.pacing.floor_relief` passes all 13 turns. State fidelity rate improves from 0.538.

---

#### Step 1.6 — Run `make check`

**What:** Lint and typecheck the modified file.

**Why:** Ensure no regressions introduced.

**Validation:**
```bash
cd /Users/pwilson/Repos/ccya && make check
```

Expected: no lint errors, no typecheck errors.

---

### Tests to write or update

Tests are temporarily removed during refactor (per AGENTS.md). No test changes required for this plan.

### Documentation updates

- `evals/EVAL-FINDINGS.md` — add note that C1 (Floor Relief Override Failure) is addressed by this plan, with status `in-progress`
- No architecture docs require changes — this is a bug fix that restores intended behavior, not a design change