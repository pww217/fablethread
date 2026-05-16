# Fix arc_engagement merge always-up-only bug

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Fix _merge_arc_update engagement guard | Remove the directional guard so engagement decreases are written through |
| 02 | Fix _apply_thread_signals unlock_if gate | Prevent threads with unlock_if conditions from auto-promoting |

## Objective
Two related arc correctness bugs exist in `state/delta.py` and `engine/turn.py`. First: `_merge_arc_update` contains a guard that only writes `arc_engagement` when the incoming value is greater than the stored value. This means every call to `tick_arc()` that produces a negative engagement delta is silently discarded at merge time — the arc engagement metric can only increase, never decrease. Second: `_apply_thread_signals` promotes latent threads to active when slots open, but never checks `ArcThread.unlock_if`. Threads with explicit activation conditions are promoted the moment a slot is available, bypassing the lock entirely.

## Non-goals
- No changes to `tick_arc()` scoring logic.
- No changes to the engagement range constants (`[-3, +3]`).
- No changes to thread completion or failure logic.
- No prompt changes.
- No changes to how `arc_engagement` is written by `apply_delta` (that path goes through `_merge_arc_update` and is the direct target of this fix).

---

## Implementation — Phase 01: Fix _merge_arc_update engagement guard

### Files to pull for context
- `ccya/state/delta.py`
- `ccya/models.py` (CampaignArc shape)

### Detailed steps

#### Step 1.1 — Remove directional guard on arc_engagement in _merge_arc_update

**File:** `ccya/state/delta.py`

**What:** The final block in `_merge_arc_update` reads:
```python
if au.arc_engagement and au.arc_engagement > (arc.get("arc_engagement") or 0):
    arc["arc_engagement"] = au.arc_engagement
```
Replace it with an unconditional write that still guards against `None` (the default on a freshly constructed `CampaignArc`):
```python
if au.arc_engagement is not None:
    arc["arc_engagement"] = au.arc_engagement
```

**Why:** `CampaignArc.arc_engagement` defaults to `0`, not `None`. The old guard `au.arc_engagement and ...` also suppresses writes when the value is `0` (falsy), meaning a reset-to-neutral is dropped. The `is not None` guard is the correct sentinel for "this field was intentionally set".

**Code Snippet**
```python
def _merge_arc_update(arc: dict[str, Any], au: CampaignArc) -> None:
    """Surgically merge arc_update into the live arc dict. Never wholesale replaces."""

    def _upsert_threads(
        existing: list[dict[str, Any]], updates: list[Any]
    ) -> list[dict[str, Any]]:
        by_id = {t["id"]: t for t in existing if isinstance(t, dict) and t.get("id")}
        for t in updates:
            td = t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            tid = td.get("id")
            if not tid:
                continue
            if tid in by_id:
                by_id[tid].update({k: v for k, v in td.items() if v is not None})
            else:
                by_id[tid] = td
        return list(by_id.values())

    if au.visible_goal:
        arc["visible_goal"] = au.visible_goal
    if au.thematic_question:
        arc["thematic_question"] = au.thematic_question
    current_phase = arc.get("phase")
    if au.phase and au.phase.value != current_phase:
        arc["phase"] = au.phase.value if hasattr(au.phase, "value") else str(au.phase)
    if au.pc_drive:
        arc["pc_drive"] = au.pc_drive
    if au.hidden_truths:
        arc["hidden_truths"] = au.hidden_truths
    if au.discovered_truths:
        existing_dt = set(arc.get("discovered_truths") or [])
        arc["discovered_truths"] = list(existing_dt | set(au.discovered_truths))
    if au.active_threads is not None:
        arc["active_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.active_threads
        ]
    if au.latent_threads is not None:
        arc["latent_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.latent_threads
        ]
    if au.completed_threads is not None:
        arc["completed_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.completed_threads
        ]
    if au.arc_engagement is not None:
        arc["arc_engagement"] = au.arc_engagement
```

**Validation:** After this change, write a test that calls `tick_arc()` with no matching drift (engagement should go -1), then calls `_merge_arc_update` with the resulting arc, and asserts the stored engagement is -1. Confirm an existing arc at +2 that gets a -1 tick ends up at +1 after merge.

### Tests to write or update

**File:** `tests/test_arc.py`

Add two test functions:

```python
def test_merge_arc_update_engagement_decreases() -> None:
    """arc_engagement decrease must survive _merge_arc_update."""
    from ccya.models import CampaignArc
    from ccya.state.delta import _merge_arc_update

    arc_dict: dict = {"arc_engagement": 2, "active_threads": [], "latent_threads": [], "completed_threads": []}
    update = CampaignArc(arc_engagement=-1)
    _merge_arc_update(arc_dict, update)
    assert arc_dict["arc_engagement"] == -1


def test_merge_arc_update_engagement_zero_written() -> None:
    """arc_engagement of 0 (falsy) must be written, not skipped."""
    from ccya.models import CampaignArc
    from ccya.state.delta import _merge_arc_update

    arc_dict: dict = {"arc_engagement": 3, "active_threads": [], "latent_threads": [], "completed_threads": []}
    update = CampaignArc(arc_engagement=0)
    _merge_arc_update(arc_dict, update)
    assert arc_dict["arc_engagement"] == 0
```

### REPOMAP and architecture updates
None — this is a pure bug fix with no API or signature changes.

### Risks
1. Any test that relied on the broken one-directional behavior will fail. Fix the test, not the code.
2. Existing save files have inflated `arc_engagement` values. No migration needed — the corrected logic will begin writing accurate values from the next turn.

---

## Implementation — Phase 02: Fix _apply_thread_signals unlock_if gate

### Files to pull for context
- `ccya/engine/turn.py` (full `_apply_thread_signals` function)
- `ccya/models.py` (`ArcThread.unlock_if` field)

### Detailed steps

#### Step 2.1 — Add unlock_if check to latent thread promotion loop

**File:** `ccya/engine/turn.py`

**What:** In `_apply_thread_signals`, the promotion block currently reads:
```python
completed_ids = {t.id for t in arc.completed_threads}
available = [
    t for t in arc.latent_threads
    if t.id not in completed_ids
]
slots = _ACTIVE_THREAD_CAP - len(arc.active_threads)
to_promote = available[:slots]
```
Insert a filter to exclude threads whose `unlock_if` field is set (non-empty, non-None). These threads have a designer-specified unlock condition that must be satisfied in fiction before they can become active. Automatic slot-fill promotion bypasses that gate.

**Why:** `ArcThread.unlock_if` is a `str | None` field. `None` or empty string means "no condition — promote freely." A non-empty string means "only activate when this plain-language condition is true." The engine has no evaluator for these conditions yet, so the only safe behavior is to exclude them from automatic promotion. A future plan can add explicit unlock signaling.

**Code Snippet**
```python
    completed_ids = {t.id for t in arc.completed_threads}
    available = [
        t for t in arc.latent_threads
        if t.id not in completed_ids
        and not (t.unlock_if and t.unlock_if.strip())
    ]
    slots = _ACTIVE_THREAD_CAP - len(arc.active_threads)
    to_promote = available[:slots]
    if to_promote:
        promoted = [
            t.model_copy(update={"state": ThreadState.ACTIVE}) for t in to_promote
        ]
        remaining_latent = [
            t for t in arc.latent_threads if t.id not in {p.id for p in to_promote}
        ]
        arc = arc.model_copy(update={
            "active_threads": arc.active_threads + promoted,
            "latent_threads": remaining_latent,
        })
        mutated = True
```

**Validation:** After this step, create a test with a latent thread that has `unlock_if="Player has spoken to the senator"`. Have a signal open a slot. Assert the locked thread is NOT promoted. Assert an unlocked latent thread in the same list IS promoted.

### Tests to write or update

**File:** `tests/test_arc.py`

Add:
```python
def test_apply_thread_signals_respects_unlock_if() -> None:
    """Latent threads with unlock_if must not be auto-promoted."""
    from ccya.engine.turn import _apply_thread_signals, _ACTIVE_THREAD_CAP
    from ccya.models import ArcThread, CampaignArc, ThreadState, ThreadSignalType
    from unittest.mock import MagicMock

    locked = ArcThread(id="locked", summary="locked thread", state=ThreadState.LATENT, unlock_if="Player has spoken to the senator")
    unlocked = ArcThread(id="unlocked", summary="free thread", state=ThreadState.LATENT)
    active = ArcThread(id="active", summary="active thread", state=ThreadState.ACTIVE, progress=3)

    arc = CampaignArc(
        active_threads=[active],
        latent_threads=[locked, unlocked],
        completed_threads=[],
    )
    state = {"arc": arc.model_dump(mode="json")}

    progress_result = MagicMock()
    progress_result.thread_signals = [MagicMock(id="active", signal=MagicMock(value="failed"))]

    result = _apply_thread_signals(state, progress_result)
    assert result is not None
    active_ids = {t.id for t in result.active_threads}
    assert "unlocked" in active_ids
    assert "locked" not in active_ids
```

### REPOMAP and architecture updates
`docs/REPOMAP/engine.md` — update `_apply_thread_signals` description: add note that threads with a non-empty `unlock_if` field are excluded from automatic slot-fill promotion.

### Risks
1. Packs that have `unlock_if` set on threads that were previously (incorrectly) auto-promoted will see those threads revert to latent on the next run. This is correct behavior — no mitigation needed.
2. If all latent threads have `unlock_if` set and a slot opens, no promotion occurs. This is the intended design.

## Ambiguities requiring resolution before execution
None. Both bugs are unambiguous.
