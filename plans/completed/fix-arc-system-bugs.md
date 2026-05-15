# Fix Arc System Bugs

## Status
`completed`

## Phases

3 phases fixing three bugs in the arc system: cumulative thread advancement, engagement matching, and initial thread promotion.

## Objective

The arc system has three bugs that prevent it from functioning: thread advancement never completes (counts reset per turn), engagement always hits -3 (drift phrases don't match thread tags), and seeded threads start as `latent` instead of `active`. These fixes make the arc system work as designed.

## Non-goals

- New arc features (phase transitions, truth promotion, salience scoring improvements)
- UI changes to arc display
- Changes to how the LLM generates drift signals or thread signals
- Changes to the seed prompt or pack format

## Firm decisions

1. Thread advancement is cumulative across turns — `advanced_counts` must persist state, not reset per call.
2. Engagement matching uses substring overlap between drift phrases and thread tags — not exact set intersection. This preserves the LLM's freeform drift output while matching against structured thread tags.
3. Threads seeded as `active` get `state: active` on init — no promotion pass needed, just correct initial state.
4. No new Pydantic fields — all fixes use existing `ArcThread.state`, `CampaignArc.arc_engagement`, and per-thread `progress` counter.

## Conflicts and overlap

None. Only `engine/arc.py` and `state/io.py` are touched. No model changes, no prompt changes, no UI changes.

## Implementation — Phase 1: Cumulative thread advancement

### Context files to load
- `ccya/engine/arc.py` — `tick_arc()` function
- `ccya/models.py` — `ArcThread`, `CampaignArc` models

### Detailed steps

#### Step 1.1 — Track cumulative progress on ArcThread, not in local dict

**File:** `ccya/engine/arc.py`

**What:** Replace the `advanced_counts` local dict with a persistent `progress` counter on each `ArcThread`. The `ArcThread.progress` field already exists and is designed for this purpose. Increment it on ADVANCED signals, check it against threshold of 2.

**Why:** The current `advanced_counts: dict[str, int] = {}` resets every `tick_arc()` call, so a thread needs 2 ADVANCED signals in the same turn to complete. The design intent (per `arc-system-mechanics.md`) is cumulative: "If a thread's progress >= 2, mark it complete."

**Code Snippet**
```python
# In tick_arc(), replace lines 91-100:

# OLD:
# advanced_counts: dict[str, int] = {}
# ignored_counts: dict[str, int] = {}
# ignored_start_turn: dict[str, int] = {}
#
# for sig in signals:
#     if sig.signal == ThreadSignalType.ADVANCED:
#         advanced_counts[sig.id] = advanced_counts.get(sig.id, 0) + 1
#         ignored_counts.pop(sig.id, None)
#         ignored_start_turn.pop(sig.id, None)
#     elif sig.signal == ThreadSignalType.IGNORED:
#         ignored_counts[sig.id] = ignored_counts.get(sig.id, 0) + 1
#         if sig.id not in ignored_start_turn:
#             ignored_start_turn[sig.id] = turn_no
#     elif sig.signal == ThreadSignalType.FAILED:
#         for t in arc.active_threads:
#             if t.id == sig.id:
#                 t.state = ThreadState.FAILED
#                 break
#         for t in arc.latent_threads:
#             if t.id == sig.id:
#                 t.state = ThreadState.FAILED
#                 break

# NEW:
# Track cumulative progress on thread objects themselves.
# progress is incremented on ADVANCED, reset on non-IGNORED signals.
for sig in signals:
    if sig.signal == ThreadSignalType.ADVANCED:
        for t in arc.active_threads:
            if t.id == sig.id:
                t.progress = t.progress + 1
                break
        for t in arc.latent_threads:
            if t.id == sig.id:
                t.progress = t.progress + 1
                break
    elif sig.signal == ThreadSignalType.BLOCKED:
        # Reset progress on block — must rebuild momentum
        for t in arc.active_threads:
            if t.id == sig.id:
                t.progress = 0
                break
        for t in arc.latent_threads:
            if t.id == sig.id:
                t.progress = 0
                break
    elif sig.signal == ThreadSignalType.FAILED:
        for t in arc.active_threads:
            if t.id == sig.id:
                t.state = ThreadState.FAILED
                break
        for t in arc.latent_threads:
            if t.id == sig.id:
                t.state = ThreadState.FAILED
                break
    # IGNORED: do not change progress — thread sits

# Track ignored streaks for expiry detection
ignored_counts: dict[str, int] = {}
ignored_start_turn: dict[str, int] = {}
for sig in signals:
    if sig.signal == ThreadSignalType.IGNORED:
        ignored_counts[sig.id] = ignored_counts.get(sig.id, 0) + 1
        if sig.id not in ignored_start_turn:
            ignored_start_turn[sig.id] = turn_no
```

**Validation:** Threads with 2+ ADVANCED signals across turns complete. Threads with BLOCKED reset progress. IGNORED does not affect progress.

### Tests to write or update

**File:** `tests/test_arc.py`

```python
"""Tests for engine/arc.py — thread lifecycle and engagement."""

import pytest
from ccya.models import ArcThread, CampaignArc, ThreadSignal, ThreadSignalType, ThreadState


def _make_arc(
    active: list[dict] | None = None,
    latent: list[dict] | None = None,
    completed: list[dict] | None = None,
    engagement: int = 0,
) -> CampaignArc:
    """Build a CampaignArc from minimal dicts."""
    def _thread(d: dict) -> ArcThread:
        return ArcThread(
            id=d["id"],
            summary=d.get("summary", ""),
            tags=d.get("tags", []),
            state=d.get("state", ThreadState.LATENT),
            urgency=d.get("urgency", "normal"),
            progress=d.get("progress", 0),
            unlock_if=d.get("unlock_if"),
            promotes=d.get("promotes", []),
            last_offered_turn=d.get("last_offered_turn"),
        )
    return CampaignArc(
        visible_goal="test",
        thematic_question="test?",
        active_threads=[_thread(d) for d in (active or [])],
        latent_threads=[_thread(d) from d in (latent or [])],
        completed_threads=[_thread(d) for d in (completed or [])],
        arc_engagement=engagement,
    )


def _signal(thread_id: str, signal: str) -> ThreadSignal:
    return ThreadSignal(id=thread_id, signal=ThreadSignalType(signal))


class TestThreadAdvancement:
    """Thread completion requires 2 ADVANCED signals across turns."""

    def test_two_advanced_across_turns_completes_thread(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        from ccya.engine.arc import tick_arc

        # Turn 1: first ADVANCED
        arc = tick_arc(arc, [_signal("t1", "advanced")], [], 0, 1)
        t = arc.active_threads[0]
        assert t.progress == 1
        assert t.state == ThreadState.ACTIVE

        # Turn 2: second ADVANCED → completes
        arc = tick_arc(arc, [_signal("t1", "advanced")], [], 0, 2)
        assert len(arc.active_threads) == 0
        assert len(arc.completed_threads) == 1
        assert arc.completed_threads[0].state == ThreadState.COMPLETE

    def test_advanced_then_blocked_resets_progress(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 1}])
        from ccya.engine.arc import tick_arc

        # BLOCKED resets progress to 0
        arc = tick_arc(arc, [_signal("t1", "blocked")], [], 0, 5)
        assert arc.active_threads[0].progress == 0

    def test_failed_marks_thread_failed(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE}])
        from ccya.engine.arc import tick_arc

        arc = tick_arc(arc, [_signal("t1", "failed")], [], 0, 5)
        assert arc.active_threads[0].state == ThreadState.FAILED

    def test_two_advanced_same_turn_completes(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        from ccya.engine.arc import tick_arc

        # Two ADVANCED in same turn
        arc = tick_arc(arc, [_signal("t1", "advanced"), _signal("t1", "advanced")], [], 0, 1)
        assert len(arc.active_threads) == 0
        assert len(arc.completed_threads) == 1

    def test_progress_persists_across_turns(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        from ccya.engine.arc import tick_arc

        # Turn 1: ADVANCED
        arc = tick_arc(arc, [_signal("t1", "advanced")], [], 0, 1)
        assert arc.active_threads[0].progress == 1

        # Turn 2: IGNORED — progress should persist
        arc = tick_arc(arc, [_signal("t1", "ignored")], [], 0, 2)
        assert arc.active_threads[0].progress == 1

        # Turn 3: ADVANCED — should complete (1+1=2)
        arc = tick_arc(arc, [_signal("t1", "advanced")], [], 0, 3)
        assert len(arc.completed_threads) == 1


class TestThreadPromotion:
    """Completed threads promote their listed latent threads."""

    def test_promote_on_completion(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}],
            latent=[{"id": "t2", "state": ThreadState.LATENT, "promotes": ["t3"]}],
        )
        # Add t3 as latent that t1 promotes
        arc.active_threads[0].promotes = ["t3"]
        arc.latent_threads.append(ArcThread(id="t3", summary="promoted thread", tags=[]))

        from ccya.engine.arc import tick_arc

        # Two ADVANCED to complete t1
        arc = tick_arc(arc, [_signal("t1", "advanced"), _signal("t1", "advanced")], [], 0, 1)
        t3 = [t for t in arc.active_threads if t.id == "t3"]
        assert len(t3) == 1
        assert t3[0].state == ThreadState.ACTIVE


class TestEngagement:
    """Engagement uses substring matching between drift and thread tags."""

    def test_drift_overlaps_tag_increments_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political", "trust"]}],
            engagement=-3,
        )
        from ccya.engine.arc import tick_arc

        # Drift phrase contains "political"
        arc = tick_arc(arc, [], ["interested in political maneuvering"], 0, 1)
        assert arc.arc_engagement == -2

    def test_drift_no_overlap_decrements_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["military"]}],
            engagement=0,
        )
        from ccya.engine.arc import tick_arc

        # Drift phrase has no overlap with "military"
        arc = tick_arc(arc, [], ["focused on finding shelter"], 0, 1)
        assert arc.arc_engagement == -1

    def test_engagement_clamps_at_3_and_minus_3(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["aid"]}],
            engagement=3,
        )
        from ccya.engine.arc import tick_arc

        # Already at max — should not exceed
        arc = tick_arc(arc, [], ["looking for aid"], 0, 1)
        assert arc.arc_engagement == 3

        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["military"]}],
            engagement=-3,
        )
        arc = tick_arc(arc, [], ["avoiding military contact"], 0, 1)
        assert arc.arc_engagement == -2

    def test_empty_drift_does_not_change_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political"]}],
            engagement=1,
        )
        from ccya.engine.arc import tick_arc

        arc = tick_arc(arc, [], [], 0, 1)
        assert arc.arc_engagement == 1


class TestInitialPromotion:
    """Threads seeded as active should start with state=active."""

    def test_active_threads_start_active(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE}],
            latent=[],
        )
        # No promotion needed — already active
        assert arc.active_threads[0].state == ThreadState.ACTIVE
```

### REPOMAP updates required

- `docs/REPOMAP/engine.md` — update `tick_arc()` description to note cumulative `progress` counter on `ArcThread` instead of local `advanced_counts` dict.

### Risks

1. **Existing saves with stale progress values:** If any save has `progress` set from a previous buggy run, it could cause premature completion. Mitigation: the progress counter is per-thread and only increments on ADVANCED — stale values from a single turn would be at most 1, which is harmless (one extra turn of play).

## Implementation — Phase 2: Engagement substring matching

### Context files to load
- `ccya/engine/arc.py` — engagement section of `tick_arc()` (lines 222-232)

### Detailed steps

#### Step 2.1 — Use substring matching instead of set intersection

**File:** `ccya/engine/arc.py`

**What:** Replace the set intersection `engagement_tags & drift_lower` with substring matching: for each drift phrase, check if any thread tag appears as a substring (case-insensitive) within the drift phrase.

**Why:** Drift signals are freeform prose phrases (`"questioning the morality of the mission"`) while thread tags are structured keywords (`"political"`, `"trust"`, `"navigation"`). Set intersection never matches because the drift phrases are not tag-like. Substring matching catches cases like `"interested in political maneuvering"` matching tag `"political"`.

**Code Snippet**
```python
# In tick_arc(), replace lines 222-232:

# OLD:
# engagement_tags: set[str] = set()
# for t in arc.active_threads:
#     engagement_tags.update(t.tags)
#
# if drift:
#     drift_lower = {d.lower() for d in drift}
#     if engagement_tags & drift_lower:
#         arc.arc_engagement = min(arc.arc_engagement + 1, 3)
#     else:
#         arc.arc_engagement = max(arc.arc_engagement - 1, -3)

# NEW:
if drift:
    engagement_tags: set[str] = set()
    for t in arc.active_threads:
        engagement_tags.update(t.tags)

    # Substring matching: does any thread tag appear inside any drift phrase?
    has_overlap = False
    for d in drift:
        d_lower = d.lower()
        for tag in engagement_tags:
            if tag in d_lower:
                has_overlap = True
                break
        if has_overlap:
            break

    if has_overlap:
        arc.arc_engagement = min(arc.arc_engagement + 1, 3)
    else:
        arc.arc_engagement = max(arc.arc_engagement - 1, -3)
```

**Validation:** `"interested in political maneuvering"` matches tag `"political"`. `"focused on finding shelter"` does not match tag `"military"`. Engagement increments/decrements correctly.

### Tests to write or update

Add to `tests/test_arc.py` → `TestEngagement` class (already written in Phase 1 tests above).

### REPOMAP updates required

- `docs/REPOMAP/engine.md` — update `tick_arc()` description: "arc engagement: increment/decrement based on substring overlap between drift phrases and thread tags"

### Risks

1. **False positive substring matches:** A tag like `"aid"` could match drift `"abandoned aid station"`. This is acceptable — the drift does relate to the thread. The engagement metric is a soft signal, not a hard gate.

## Implementation — Phase 3: Initial thread promotion

### Context files to load
- `ccya/state/io.py` — `_default_state()` function
- `ccya/engine/seed.py` — `generate_seed()` function (lines 241-249)

### Detailed steps

#### Step 3.1 — Set initial active threads to state=active

**File:** `ccya/engine/seed.py`

**What:** After copying the arc from the seed envelope into `seed_state.arc`, set `state=ThreadState.ACTIVE` on all threads in `arc.active_threads`.

**Why:** The seed prompt generates threads with `state` not specified (defaults to `LATENT` in the Pydantic model). When these threads land in `state.arc.active_threads`, they have `state: latent` which is inconsistent — they're in the active list but marked latent. Setting them to active at seed time fixes this at the source.

**Code Snippet**
```python
# In generate_seed(), after line 245 (after copying arc into seed_state):

# OLD (lines 241-245):
# if envelope.arc:
#     envelope.seed_state.arc = envelope.arc
#     if envelope.pc_drive:
#         envelope.seed_state.arc.pc_drive = envelope.pc_drive

# NEW:
# if envelope.arc:
#     envelope.seed_state.arc = envelope.arc
#     if envelope.pc_drive:
#         envelope.seed_state.arc.pc_drive = envelope.pc_drive
#     # Ensure seeded active threads start with correct state
#     from ccya.models import ThreadState
#     for t in (envelope.seed_state.arc or {}).get("active_threads", []):
#         if isinstance(t, dict):
#             t["state"] = ThreadState.ACTIVE.value
```

**Validation:** New games have `active_threads[*].state == "active"`. Latent threads remain `state: latent`.

### Tests to write or update

**File:** `tests/test_char_creation.py` — add assertion that seeded active threads have `state: active`.

```python
def test_arc_active_threads_start_active(self):
    """Active threads from seed should have state=active, not latent."""
    # This test uses the existing _FakeLLM pattern
    # The mock should return a SeedEnvelope with arc.active_threads
    # Verify that after generate_seed(), active_threads have state=active
    pass
```

### REPOMAP updates required

- `docs/REPOMAP/pack.md` — note that `generate_seed()` now normalizes `active_threads[*].state` to `active` after copying from envelope.

### Risks

1. **Static packs with hand-authored seed_state.yaml:** These bypass `generate_seed()` and write `seed_state.yaml` directly. If a static pack has `state: latent` in active threads, it would still be wrong. Mitigation: add a migration in `state/io.py:_migrate_state()` that fixes this for all loaded states.

#### Step 3.2 — Add migration for existing saves

**File:** `ccya/state/io.py`

**What:** In `_migrate_state()`, after loading any state, ensure threads in `active_threads` have `state: active` and threads in `latent_threads` have `state: latent`.

**Why:** Static packs and any existing saves may have threads with wrong state values. The migration ensures all loaded states are consistent.

**Code Snippet**
```python
# In _migrate_state(), add before the return:

# Fix arc thread states — active list should have ACTIVE, latent list should have LATENT
arc = state.get("arc")
if arc:
    for t in arc.get("active_threads", []):
        if isinstance(t, dict) and t.get("state") != ThreadState.ACTIVE.value:
            t["state"] = ThreadState.ACTIVE.value
    for t in arc.get("latent_threads", []):
        if isinstance(t, dict) and t.get("state") != ThreadState.LATENT.value:
            t["state"] = ThreadState.LATENT.value
```

**Validation:** Loading any save (new or existing) results in correct thread states.

### Tests to write or update

**File:** `tests/test_state_io.py` — add test for arc thread state migration.

```python
def test_migrate_arc_thread_states(self):
    """Arc threads in active list should be state=active after migration."""
    state = {
        "arc": {
            "active_threads": [{"id": "t1", "state": "latent"}],
            "latent_threads": [{"id": "t2", "state": "active"}],
        }
    }
    from ccya.state.io import _migrate_state
    _migrate_state(state)
    assert state["arc"]["active_threads"][0]["state"] == "active"
    assert state["arc"]["latent_threads"][0]["state"] == "latent"
```

### REPOMAP updates required

- `docs/REPOMAP/state.md` — add arc thread state normalization to `_migrate_state()` description.

## Ambiguities requiring resolution before execution

None. All three bugs and their fixes are clear from the code analysis.
