# Momentum, actions, thread lifecycle + checker fixes

## Status
`completed`

## Phases

3 phases covering four confirmed engine bugs in the state merge layer — none are prompt issues, all are Python code defects verified by trace data analysis.

## Issue

The eval run `20260524T061924Z_v47zjlbj` surfaces 4 distinct engine bugs, all in the Python glue between extraction results and applied state. The LLM pipelines mostly work (Narrator 5/5, Storyteller 4/5); the Python layer connecting them is broken:

1. **Momentum delta reporting is a tautology** — `momentum_before` and `momentum_after` are both read after `apply_momentum()` already mutated state (turn.py:1057-1059). Delta is always 0 regardless of band, making every ruling event's momentum_delta field useless. The auto-checker can't catch this because it reads `meta.momentum` (universal_asserts.py:560) — a field never written by the engine.

2. **Storyteller Actions are silently dropped** — `StateDelta` has no `actions` field (models.py:274). Pydantic discards the field during merge (extraction.py:773). Actions exist in LLM output but never reach applied deltas (T3/6/9/12 failures).

3. **Resolved threads persist in arc.threads** — `_merge_arc_update` (delta_builder.py:67) uses truthy check `if au.threads:` which fails when `remaining_threads = []` after resolving the last active thread. The resolved thread stays in `arc.threads` where latent promotion reactivates it (`deliver_the_ledger` advanced again in T9/T13 after T7 resolution).

## Solution

Phase 01 fixes momentum capture ordering and checker field. Phase 02 adds actions persistence through StateDelta. Phase 03 fixes the thread removal truthy check in `_merge_arc_update` plus adds completed_threads guard in latent promotion. All three phases touch separate files and are independently executable.

## Firm decisions

1. `momentum_delta` must reflect the actual band-based change, not a post-mutation tautology. Pre-ruling momentum is captured before `_ruling_phase(ctx)`.
2. Auto-checker momentum assertions must read `state_snapshot.pc.momentum`, not `state_snapshot.meta.momentum`.
3. `StateDelta.actions` stores list of strings directly (no wrapper model). Persisted as rolling window of last 10 in `state["pc"]["actions"]`.
4. `_merge_arc_update` must always replace `arc["threads"]` when a resolution occurred, even if the replacement list is empty.
5. Latent promotion in `_apply_thread_signals` must skip IDs in `completed_threads` as a defense-in-depth measure even after the primary fix.

## Non-goals

- Not fixing inventory zero-balance extraction failure (T9/T13) — that's a prompt constraint gap, not an engine bug.
- Not fixing Ghost NPC timing (T4/T5 toughs) — requires deeper data flow investigation.
- Not fixing auto-checker NPC name parsing false positives or trace capture errors — these are eval harness issues, not engine bugs.
- Not fixing location change verbosity on scene reset — prompt-level inefficiency, not a correctness bug.
- Not adding test coverage (per AGENTS.md: tests are temporarily removed during refactor).

## Risks, Ambiguities, and Blockers

- **Momentum state change during T5 (0→1) unexplained**: Evidence confirms `apply_momentum("partial")` with delta=0 leaves momentum unchanged, yet the state snapshot diff shows 0→1. No code path found that modifies `pc.momentum` outside `_apply_momentum`. This may be a real engine bug or a timing artifact in the changes diff. The momentum capture fix (Phase 01 Step 1) will make the delta reporting accurate, enabling proper diagnosis. If the drift persists after the fix, a deeper bug exists in state mutation.
- **Thread resolution and merge ordering**: `_apply_thread_signals` runs before `_apply_thread_resolutions`. If signal processing reorders threads in a way that changes index-based removal in resolutions, the fix could behave differently with multiple parallel threads. Step 3.1 addresses this by using ID-based matching (already the case in code), but the truthy check bypass should be verified with both empty and non-empty remaining lists.

---

## Implementation — Phase 01: Momentum delta correctness

### Context files to load
- `ccya/engine/turn.py` (~lines 1040–1065 capturing momentum, ~lines 1420–1430 building ruling event)
- `ccya/eval/universal_asserts.py` (~lines 536–584 `check_momentum_band_delta`)
- `ccya/state/momentum.py` (full file, confirm write path)

### Detailed steps

#### Step 1.1 — Capture pre-ruling momentum before `_ruling_phase` mutates state

**File:** `ccya/engine/turn.py` (~lines 1042–1059)

**What:** Move `momentum_before` capture before the `await _ruling_phase(ctx)` call. Currently:
```python
_intent, _outcome, ruling_metrics, deescalate, ruling_phase_events = await _ruling_phase(ctx)
# ... yield events ...
momentum_before = state.get("pc", {}).get("momentum", 0.0) if _outcome.rolled else 0.0
# Note: apply_momentum was already called inside _ruling_phase above
momentum_after = state.get("pc", {}).get("momentum", 0.0)
```

Change to:
```python
# Capture pre-ruling momentum before _ruling_phase mutates state
momentum_before = state.get("pc", {}).get("momentum", 0.0)

_intent, _outcome, ruling_metrics, deescalate, ruling_phase_events = await _ruling_phase(ctx)
for evt in ruling_phase_events:
    yield evt
ctx._deescalate = deescalate

# Capture post-ruling momentum (reflects what apply_momentum did)
momentum_after = state.get("pc", {}).get("momentum", 0.0)
```

Remove the default-to-zero conditional — momentum_before always reads the actual state value, and momentum_after always reflects the post-apply_momentum state. The delta `momentum_after - momentum_before` now correctly represents the band-based change.

**Why:** `apply_momentum(state, outcome.band)` at turn.py:822 mutates `state["pc"]["momentum"]` in place during ruling phase. Reading both before and after after that mutation makes them equal (for delta=0 bands) or both equal to the mutated value (for non-zero delta bands like success=+1). The delta is always 0, making the field meaningless for debug and eval.

**Validation:** Run eval scenario and verify T5 (partial) shows delta=0 with matching values, T6 (success) shows delta=+1 with before=after_T5_end_value, after=before+1.

#### Step 1.2 — Fix auto-checker to read pc.momentum instead of meta.momentum

**File:** `ccya/eval/universal_asserts.py` (~lines 559–579)

**What:** Change `check_momentum_band_delta` to read from `pc.momentum` instead of `meta.momentum`:

```python
# Before:
cur_m = (cur_snap.get("meta") or {}).get("momentum")
# ...
prev_m = (prev_snap.get("meta") or {}).get("momentum") or 0

# After:
cur_m = (cur_snap.get("pc") or {}).get("momentum")
# ...
prev_m = (prev_snap.get("pc") or {}).get("momentum") or 0
```

Also update the detail messages from `"(no momentum field)"` to `"(no pc.momentum field)"` for clarity.

**Why:** The engine writes momentum to `state["pc"]["momentum"]` (see `_default_state()` in io.py:70 and `apply_momentum` in momentum.py:21). `meta.momentum` is never set by any code path. The auto-checker currently always returns `passed: True` with `"(no momentum field)"` — it's silently dead code.

**Validation:** After fix, the auto-checker should produce actual `passed: True/False` results on rolled turns. Verify T5 (partial, delta=0) passes, T6 (success, delta=+1) passes.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
- `docs/repomap.md`: Under `Momentum lifecycle` section, note that momentum delta is captured before/after ruling phase and auto-checker reads from pc.momentum.

---

## Implementation — Phase 02: Storyteller Actions persistence

### Context files to load
- `ccya/models.py` (StateDelta model ~line 274)
- `ccya/engine/extraction.py` (`_run_extraction_pipeline` merge block ~line 773)
- `ccya/state/delta_builder.py` (`apply_delta` full file)

### Detailed steps

#### Step 2.1 — Add `actions` field to StateDelta model

**File:** `ccya/models.py` (StateDelta class ~line 274)

**What:** Add an `actions` field to the StateDelta Pydantic model, placed after `recent_events_remove` and before `arc_update`:
```python
actions: list[str] = Field(default_factory=list, max_length=10)
```

No wrapper model needed — actions are simple player choice text strings.

**Why:** StateDelta is constructed in `_run_extraction_pipeline` from `scene_result`, `state_result`, and `storytell_result`. Without this field, actions from `storytell_result.actions` are silently dropped by Pydantic during merge. The field exists in StorytellerResult but cannot reach state.

**Validation:** Confirm `StateDelta.model_fields["actions"]` exists with type `list[str]` and default_factory=list.

#### Step 2.2 — Include actions in extraction merge block

**File:** `ccya/engine/extraction.py` (~line 773)

**What:** Add `actions=storytell_result.actions or []` to the StateDelta constructor call at the merge block. This passes StorytellerResult.actions into the delta so it reaches apply_delta.

**Why:** Without this, the new field from Step 2.1 defaults to empty list on every turn, regardless of what the LLM emitted.

**Validation:** Verify turns where Storyteller emits 4 actions show non-empty `actions` in StateDelta before apply_delta.

#### Step 2.3 — Persist actions in apply_delta

**File:** `ccya/state/delta_builder.py` (end of `apply_delta` function, before the return)

**What:** After applying other StateDelta fields, persist actions to state as a rolling window:
```python
if delta.actions:
    pc = state.setdefault("pc", {})
    pc["actions"] = list(delta.actions[-10:])
    _log.info(
        "Applied %d Storyteller Actions", len(delta.actions),
        extra={"turn": current_turn_no, "trace_id": "", "pack": "", "kind": "actions"},
    )
```

The rolling window stores the most recent 10 actions in `state["pc"]["actions"]` to prevent unbounded growth while keeping enough history for narrative continuity.

**Why:** Without persistence, actions exist only in extraction output trace and disappear after turn processing. Auto-checkers and eval judges check state snapshots, so actions must be in the persisted state to pass assertions like `storytell.actions_quality`.

**Validation:** After apply_delta on a turn with 4 actions, verify `state["pc"]["actions"]` contains those strings at correct indices. Confirm INFO log entry with kind="actions".

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
- `docs/repomap.md`: Add `StateDelta.actions` to field list. Note actions are stored in `state["pc"]["actions"]` as rolling window of last 10.

---

## Implementation — Phase 03: Thread lifecycle resolution + merge fixes

### Context files to load
- `ccya/state/delta_builder.py` (`_merge_arc_update` at line 53, `apply_delta` arc_update at line 328)
- `ccya/engine/turn.py` (`_apply_thread_signals` at line 158, `_apply_thread_resolutions` at line 345)
- `ccya/engine/turn.py` (~lines 1300–1320 where both are called)

### Detailed steps

#### Step 3.1 — Fix `_merge_arc_update` to always replace threads/completed_threads

**File:** `ccya/state/delta_builder.py` (lines 67–76)

**What:** Remove the truthy guards on `au.threads` and `au.completed_threads`. Always replace the lists when the CampaignArc is provided, even if the list is empty:

```python
# Lines 67-76, change from:
if au.threads:
    arc["threads"] = [
        t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
        for t in au.threads
    ]
if au.completed_threads:
    arc["completed_threads"] = [
        t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
        for t in au.completed_threads
    ]

# To:
arc["threads"] = [
    t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
    for t in au.threads
]
arc["completed_threads"] = [
    t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
    for t in au.completed_threads
]
```

**Why:** When the last active thread is resolved, `_apply_thread_resolutions` creates `remaining_threads = []` (line 411 of turn.py). The truthy check `if au.threads:` evaluates to `False` for `[]`, so `arc["threads"]` keeps the old list containing the resolved thread. This resolved-but-persistent thread then sits in `arc.threads` with `active=False`, where the latent promotion loop in `_apply_thread_signals` (line 291) can reactivate it when the Storyteller emits its ID in `thread_advance`.

The CampaignArc is always model-validated before reaching this function (turn.py:188-194 or similar), so the values in `au.threads` and `au.completed_threads` are always authoritative. The truthy check is an obsolete defensive guard that causes a correctness bug.

**Validation:** After fix, verify T7 resolution of `deliver_the_ledger` removes it from `arc.threads` and places it only in `arc.completed_threads`. Check subsequent turns' snapshots confirm it's absent from threads.

#### Step 3.2 — Guard latent promotion against completed thread IDs

**File:** `ccya/engine/turn.py` (~lines 289–305, inside `_apply_thread_signals`)

**What:** Add a completed thread ID set and check it before latent promotion. After validating the arc (lines 188-194) and before the promotion loop (line 291), add:

```python
# Build completed thread ID set for promotion guard
completed_ids = {t.id for t in arc.completed_threads}
```

Then modify the latent promotion condition to skip completed IDs:
```python
for tid in advanced_ids - set(active_by_id.keys()):
    if tid in latent_by_id and tid not in completed_ids:
        # existing promotion logic...
```

**Why:** Defense-in-depth. If a completed thread somehow ends up in `arc.threads` with `active=False` (e.g., due to the Step 3.1 bug before it's applied), the latent promotion loop would find it and reactivate it. The Storyteller LLM may also emit a resolved thread's ID in `thread_advance` (as happened in T9), which should be silently ignored rather than reactivating a completed thread.

**Validation:** After fix, verify that T9's storyteller emitting `deliver_the_ledger` in thread_advance does NOT promote it. Check that no `promoted` log entry appears for completed thread IDs.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
- `docs/repomap.md`: Note that `arc["threads"]` and `arc["completed_threads"]` are now unconditionally replaced by `_merge_arc_update`. Document the completed thread ID guard in `_apply_thread_signals` latent promotion section.

---

## Implementation summary

| Phase | Bug | Root cause | Files changed | Lines |
|-------|-----|------------|---------------|-------|
| 01 | Momentum delta always 0 | Both values captured after mutation | turn.py | ~2 |
| 01 | Auto-checker never checks momentum | Reads meta.momentum (never set) | universal_asserts.py | ~4 |
| 02 | Actions silently dropped | StateDelta has no actions field | models.py, extraction.py, delta_builder.py | ~10 |
| 03 | Resolved threads persist in arc | Truthy check fails on empty list | delta_builder.py, turn.py | ~8 |
