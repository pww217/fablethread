# Phase 3 — Thread processing in turn.py

## Purpose

Update `_apply_thread_updates()` to handle the new `type` and `dormant` fields, replace the staleness threshold with engine auto-dormant, update urgency decay skip and thread cap eviction, and add engine culling to the arc director.

## Problem Statement

`_apply_thread_updates()` references `update.active` and `t.active` — both removed in Phase 1. The staleness threshold code uses `active: false` which is replaced by `dormant: true`. The urgency decay skip references `t.active`. The thread cap eviction references `t.active`. No culling mechanism exists for dormant thread accumulation.

## Constraints

- Auto-dormant fires after 4 turns with no activity (no progress, urgency change, or type change).
- Any thread update resets the auto-dormant timer except setting `dormant: True` (the trigger).
- Auto-dormant also sets `urgency: background`. Urgent threads excluded.
- Culling fires when >= 3 dormant threads exist; oldest by `last_updated_turn` moves to `completed_threads[]` with `resolution_state: "abandoned"` and a mechanical fallback outcome string.
- Culled threads are visible for `thread_memory_ttl` turns before pruning.

## Non-goals

- No changes to sanitizer, seed, prompts, or context — covered in other phases.
- No changes to convergence score or phase engine — Phase 5.

## Solution

Update `_apply_thread_updates()` to apply `type` and `dormant` instead of `active`, replace the staleness threshold with auto-dormant logic, update urgency decay skip to check `t.dormant`, update thread cap eviction to use `not t.dormant`, and add culling logic to the arc director section.

## Firm decisions

1. Auto-dormant checks 4 turns since `last_updated_turn` with no changes to `progress`, `urgency`, `type`.
2. On auto-dormant: set `dormant: True`, `urgency: background`, `last_updated_turn: turn_no`.
3. Urgency decay skips dormant threads (they already have background urgency).
4. Culling moved oldest dormant thread by `last_updated_turn`, not `added_turn`.

## Risks, Ambiguities, and Blockers

- **Thread add path:** When a new thread is added via `storyteller_result.thread_add` (line 1253), the `dormant` field defaults to `False` — so new threads start non-dormant. This is correct.
- **Thread cap eviction:** Currently evicts oldest active thread when > `thread_max_active`. After the change, evicts oldest non-dormant thread. If all threads are dormant, eviction does nothing (no non-dormant threads to evict). This is acceptable — dormant threads are already deprioritized.
- **Culling interaction:** If auto-dormant and culling both fire on the same turn, auto-dormant sets threads dormant first, then culling checks the count. This is correct: the 4-turn timer means at most 1 thread auto-dormants per turn (the one that crossed the threshold), so reaching >= 3 requires 3+ separate turns.

## Status

`open`

## Implementation — Phase 3: Thread processing in turn.py

### Context files to load

- `ccya/engine/turn.py:112-245` — `_apply_thread_updates()` + urgency decay
- `ccya/engine/turn.py:1192-1291` — Arc director section (culling, thread add, cap eviction)
- `ccya/engine/config.py:160-178` — config fields (for `thread_stale_threshold` removal reference)
- `ccya/models.py:412-417` — ThreadUpdate model (for type/dormant field names)

### Detailed steps

#### Step 3.1 — Add `type` handling to `_apply_thread_updates()`

**File:** `ccya/engine/turn.py:154-165`

**What:** After the existing `if update.urgency is not None: updates["urgency"] = update.urgency` block, add:
```python
if update.type is not None:
    updates["type"] = update.type
```

**Why:** Storyteller can now change thread type mid-life via `thread_update`. No validation needed — engine trusts storyteller.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/turn.py').read()); print('syntax OK')"`

#### Step 3.2 — Replace `active` with `dormant` in `_apply_thread_updates()`

**File:** `ccya/engine/turn.py:156-158`

**What:** Replace `if update.active is not None: updates["active"] = update.active` with `if update.dormant is not None: updates["dormant"] = update.dormant`.

**Why:** `active` field removed in Phase 1. Storyteller now sets `dormant` instead.

**Validation:** Same as Step 3.1 — syntax check.

#### Step 3.3 — Replace staleness threshold with auto-dormant

**File:** `ccya/engine/turn.py:199-215`

**What:** Replace the auto-latent demotion block (lines 199-215) with auto-dormant logic:
```python
# Auto-dormant — fire every turn.
# Threads updated this turn already have last_updated_turn set to turn_no,
# so they won't trigger the dormant threshold. Only untouched threads age.
if config and remaining_threads:
    dormant_threshold = 4  # turns without activity before auto-dormant
    for i, t in enumerate(remaining_threads):
        if (
            t.last_updated_turn is not None
            and (turn_no - t.last_updated_turn) >= dormant_threshold
            and not t.dormant
            and t.urgency != "urgent"
        ):
            updated = t.model_copy(update={
                "dormant": True,
                "urgency": "background",
                "last_updated_turn": turn_no,
            })
            remaining_threads[i] = updated
            _log.info(
                "thread_updates.auto_dormant trace_id=%d thread %s — untouched for %d turns",
                turn_no, t.id, turn_no - t.last_updated_turn, extra={"turn": turn_no},
            )
```

Remove the `thread_stale_threshold` config field reference. (Config removal will be done separately.)

**Why:** Staleness threshold (`active: false` after 3 turns) replaced by auto-dormant (`dormant: true`, `urgency: background` after 4 turns). Urgent threads excluded.

**Validation:** Run `make check` — no type/lint errors.

#### Step 3.4 — Update urgency decay skip

**File:** `ccya/engine/turn.py:223`

**What:** Replace `if _set_turn is None or not t.active:` with `if _set_turn is None or t.dormant:`.

**Why:** Urgency decay should skip dormant threads (they already have background urgency set by auto-dormant). The skip condition inverts because `dormant` is the opposite semantic of `active`.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/turn.py').read()); print('syntax OK')"`

#### Step 3.5 — Update thread cap eviction

**File:** `ccya/engine/turn.py:1271`

**What:** Replace all `active` references in the cap eviction block. Lines 1271-1274 and 1279:

```python
# Before:
active = [t for t in arc_with_new_thread.threads if t.active]           # 1271
if len(active) > config.thread_max_active:                                # 1272
    evict = min(active, key=lambda t: t.last_updated_turn or 0)           # 1273
    evicted = evict.model_copy(update={"active": False, ...})            # 1274

# After:
non_dormant = [t for t in arc_with_new_thread.threads if not t.dormant]  # 1271
if len(non_dormant) > config.thread_max_active:                           # 1272
    evict = min(non_dormant, key=lambda t: t.last_updated_turn or 0)      # 1273
    evicted = evict.model_copy(update={"dormant": True, ...})             # 1274
```

Also update the log line at 1279 to reference `non_dormant_count`.

**Why:** `t.active` and `"active": False` both reference a removed field. Without this, `model_copy(update={"active": False})` silently ignores the update (due to `extra="ignore"`) and the evicted thread stays non-dormant — a silent bug.

**Why:** `t.active` removed in Phase 1. Cap eviction operates on non-dormant threads (the "active" ones), not a field that no longer exists.

**Validation:** Syntax check + `make check`.

#### Step 3.6 — Add culling to arc director

**File:** `ccya/engine/turn.py:1192-1291`

**What:** After the thread-add block (after the closing `if` at ~line 1290), add:
```python
# Engine culling: when >= 3 dormant threads, move oldest to completed
if state.get("arc"):
    try:
        arc = CampaignArc.model_validate(state["arc"])
        dormant_threads = [t for t in arc.threads if t.dormant]
        if len(dormant_threads) >= 3:
            to_cull = min(dormant_threads, key=lambda t: t.last_updated_turn or 0)
            culled = to_cull.model_copy(update={
                "resolution_state": "abandoned",
                "outcome": f"Thread faded from relevance — no narrative activity in {turn_no - (to_cull.last_updated_turn or 0)} turns.",
                "resolved_turn": turn_no,
            })
            remaining = [t for t in arc.threads if t.id != to_cull.id]
            arc.threads = remaining
            arc.completed_threads.append(culled)
            _merge_arc_update(state.setdefault("arc", {}), arc)
            if delta is not None:
                delta = delta.model_copy(update={"arc_update": arc})
            _log.info(
                "thread_cull trace_id=%s culled=%s dormant_count=%d",
                trace_id, to_cull.id, len(dormant_threads), extra={"trace_id": trace_id, "turn": turn_no},
            )
    except Exception as exc:
        _log.warning(
            "thread_cull.failed trace_id=%s: %s",
            trace_id, exc, extra={"trace_id": trace_id},
        )
```

**Why:** Prevents dormant thread accumulation beyond 3. Mechanical fallback for engine culls; sanitizer can also cull proactively with narrative outcomes.

**Validation:** Run `make check`. Can also verify by running a scenario with ev.py and checking that culling fires when 3+ dormant threads accumulate.

### Tests to write or update

No tests currently. Run `make check` for type/lint.

## Status

completed
