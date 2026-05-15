"""Tests for engine/arc.py — thread lifecycle and engagement."""

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
        latent_threads=[_thread(d) for d in (latent or [])],
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
