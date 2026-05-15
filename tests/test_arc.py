"""Tests for engine/arc.py — engagement scoring and thread lifecycle."""

from ccya.engine.arc import tick_arc, update_stances
from ccya.engine.turn import _apply_thread_signals, _candidate_to_latent_thread
from ccya.models import ArcThread, CampaignArc, ThreadSignal, ThreadSignalType, ThreadState
from ccya.state.delta import _merge_arc_update


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


def _make_state(arc: CampaignArc) -> dict:
    return {"arc": arc.model_dump(mode="json")}


def _signal(thread_id: str, signal: str) -> ThreadSignal:
    return ThreadSignal(id=thread_id, signal=ThreadSignalType(signal))


class TestThreadAdvancement:
    """Thread completion requires 3 ADVANCED signals across turns."""

    def test_two_advanced_same_turn_only_increments_once(self):
        """Two ADVANCED for same thread in one call → progress +1 (dict dedup)."""
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = [_signal("t1", "advanced"), _signal("t1", "advanced")]

        result = _apply_thread_signals(state, ProgressResult())
        assert result is not None
        assert result.active_threads[0].progress == 1

    def test_three_advanced_across_turns_completes_thread(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        state = _make_state(arc)

        class PR1:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR1())
        assert result is not None
        assert result.active_threads[0].progress == 1

        arc = result
        state = _make_state(arc)

        class PR2:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR2())
        assert result is not None
        assert result.active_threads[0].progress == 2

        arc = result
        state = _make_state(arc)

        class PR3:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR3())
        assert result is not None
        assert len(result.active_threads) == 0
        assert len(result.completed_threads) == 1
        assert result.completed_threads[0].state == ThreadState.COMPLETE

    def test_failed_marks_thread_failed(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE}])
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = [_signal("t1", "failed")]

        result = _apply_thread_signals(state, ProgressResult())
        assert result is not None
        assert len(result.completed_threads) == 1
        assert result.completed_threads[0].state == ThreadState.FAILED

    def test_progress_persists_across_turns(self):
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        state = _make_state(arc)

        class PR1:
            thread_signals = [_signal("t1", "advanced")]

        result1 = _apply_thread_signals(state, PR1())
        assert result1 is not None
        assert result1.active_threads[0].progress == 1

        arc = result1
        state = _make_state(arc)

        class PR2:
            thread_signals = [_signal("t1", "ignored")]

        result2 = _apply_thread_signals(state, PR2())
        assert result2 is None  # no mutation

        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 1}])
        state = _make_state(arc)

        class PR3:
            thread_signals = [_signal("t1", "advanced")]

        result3 = _apply_thread_signals(state, PR3())
        assert result3 is not None
        assert result3.active_threads[0].progress == 2


class TestThreadPromotion:
    """Latent threads promoted when active slots open."""

    def test_latent_promoted_when_slot_available(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE}],
            latent=[{"id": "t2", "state": ThreadState.LATENT}],
        )
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = [_signal("t1", "failed")]

        result = _apply_thread_signals(state, ProgressResult())
        assert result is not None
        assert len(result.active_threads) == 1
        assert result.active_threads[0].id == "t2"
        assert result.active_threads[0].state == ThreadState.ACTIVE
        assert len(result.latent_threads) == 0

    def test_active_cap_prevents_excess_promotion(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE}],
            latent=[
                {"id": "t2", "state": ThreadState.LATENT},
                {"id": "t3", "state": ThreadState.LATENT},
                {"id": "t4", "state": ThreadState.LATENT},
                {"id": "t5", "state": ThreadState.LATENT},
            ],
        )
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = [_signal("t1", "failed")]

        result = _apply_thread_signals(state, ProgressResult())
        assert result is not None
        # t1 fails → 0 active, 4 latent → promote all 4 to reach cap of 4
        assert len(result.active_threads) == 4
        assert len(result.latent_threads) == 0

    def test_no_promotion_when_at_cap(self):
        arc = _make_arc(
            active=[
                {"id": "t1", "state": ThreadState.ACTIVE},
                {"id": "t2", "state": ThreadState.ACTIVE},
                {"id": "t3", "state": ThreadState.ACTIVE},
                {"id": "t4", "state": ThreadState.ACTIVE},
            ],
            latent=[{"id": "t5", "state": ThreadState.LATENT}],
        )
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = []

        result = _apply_thread_signals(state, ProgressResult())
        assert result is None


class TestEngagement:
    """Engagement uses substring matching between drift and thread tags."""

    def test_drift_overlaps_tag_increments_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political", "trust"]}],
            engagement=-3,
        )
        arc = tick_arc(arc, ["interested in political maneuvering"])
        assert arc.arc_engagement == -2

    def test_drift_no_overlap_decrements_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["military"]}],
            engagement=0,
        )
        arc = tick_arc(arc, ["focused on finding shelter"])
        assert arc.arc_engagement == -1

    def test_engagement_clamps_at_3_and_minus_3(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["aid"]}],
            engagement=3,
        )
        arc = tick_arc(arc, ["looking for aid"])
        assert arc.arc_engagement == 3

        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["military"]}],
            engagement=-3,
        )
        arc = tick_arc(arc, ["avoiding military contact"])
        assert arc.arc_engagement == -2

    def test_empty_drift_does_not_change_engagement(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political"]}],
            engagement=1,
        )
        arc = tick_arc(arc, [])
        assert arc.arc_engagement == 1

    def test_drift_analysis_match_increments_engagement(self):
        from ccya.models import DriftAnalysis
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political", "trust"]}],
            engagement=-3,
        )
        drift = [DriftAnalysis(thread_id="t1", match=True, reason="Player engaged political thread")]
        arc = tick_arc(arc, drift_analysis=drift)
        assert arc.arc_engagement == -2

    def test_drift_analysis_no_match_decrements_engagement(self):
        from ccya.models import DriftAnalysis
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["military"]}],
            engagement=0,
        )
        drift = [DriftAnalysis(thread_id="t1", match=False, reason="Player avoided military", new_interest="finding shelter")]
        arc = tick_arc(arc, drift_analysis=drift)
        assert arc.arc_engagement == -1

    def test_drift_analysis_fallback_to_legacy_drift(self):
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political"]}],
            engagement=-3,
        )
        drift = []
        legacy_drift = ["interested in political maneuvering"]
        arc = tick_arc(arc, drift=legacy_drift, drift_analysis=drift)
        assert arc.arc_engagement == -2

    def test_drift_analysis_takes_precedence_over_legacy(self):
        from ccya.models import DriftAnalysis
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE, "tags": ["political"]}],
            engagement=0,
        )
        drift = [DriftAnalysis(thread_id="t1", match=False, reason="No match")]
        legacy_drift = ["interested in political maneuvering"]
        arc = tick_arc(arc, drift=legacy_drift, drift_analysis=drift)
        # drift_analysis says no match, so should decrement despite legacy drift having overlap
        assert arc.arc_engagement == -1


class TestCandidateToLatent:
    """candidate_opportunity converted to latent thread with cap enforcement."""

    def test_candidate_becomes_latent_thread(self):
        arc = _make_arc()
        result = _candidate_to_latent_thread(arc, "A mysterious stranger offers a deal", 1)
        assert result is not None
        assert len(result.latent_threads) == 1
        t = result.latent_threads[0]
        assert t.id == "a_mysterious_stranger_offers_a"
        assert t.summary == "A mysterious stranger offers a deal"
        assert t.state == ThreadState.LATENT
        assert t.tags == ["tactical"]

    def test_candidate_dedup_by_id(self):
        arc = _make_arc(latent=[{"id": "a_mysterious_stranger_offers_a", "state": ThreadState.LATENT}])
        result = _candidate_to_latent_thread(arc, "A mysterious stranger offers a deal", 1)
        assert result is not None
        assert len(result.latent_threads) == 2
        # Original stays, new one gets _t1 suffix
        ids = {t.id for t in result.latent_threads}
        assert "a_mysterious_stranger_offers_a" in ids
        assert "a_mysterious_stranger_offers_a_t1" in ids

    def test_latent_cap_evicts_tactical_first(self):
        arc = _make_arc(
            latent=[
                {"id": "t1", "state": ThreadState.LATENT, "tags": ["tactical"], "last_offered_turn": 1},
                {"id": "t2", "state": ThreadState.LATENT, "tags": ["tactical"], "last_offered_turn": 2},
                {"id": "t3", "state": ThreadState.LATENT, "tags": ["tactical"], "last_offered_turn": 3},
                {"id": "t4", "state": ThreadState.LATENT, "tags": ["tactical"], "last_offered_turn": 4},
            ]
        )
        result = _candidate_to_latent_thread(arc, "New opportunity", 5)
        assert result is not None
        assert len(result.latent_threads) == 4
        ids = {t.id for t in result.latent_threads}
        assert "t1" not in ids  # oldest tactical evicted
        assert "new_opportunity" in ids

    def test_latent_cap_never_evicts_non_tactical(self):
        arc = _make_arc(
            latent=[
                {"id": "t1", "state": ThreadState.LATENT, "tags": ["pack_seeded"]},
                {"id": "t2", "state": ThreadState.LATENT, "tags": ["pack_seeded"]},
                {"id": "t3", "state": ThreadState.LATENT, "tags": ["pack_seeded"]},
                {"id": "t4", "state": ThreadState.LATENT, "tags": ["pack_seeded"]},
            ]
        )
        result = _candidate_to_latent_thread(arc, "New opportunity", 5)
        assert result is None  # cap full, no tactical to evict


class TestStances:
    """Player input stances tracked by keyword matching."""

    def test_compassionate_keywords(self):
        stances = {}
        stances = update_stances(stances, "I help the wounded guard")
        assert stances["compassionate"] == 1

    def test_ruthless_keywords(self):
        stances = {}
        stances = update_stances(stances, "I kill the guard")
        assert stances["ruthless"] == 1

    def test_multiple_keywords(self):
        stances = {}
        stances = update_stances(stances, "I help and protect the wounded")
        assert stances["compassionate"] == 1  # counted once per stance


class TestThreadCompletionState:
    """Thread completion should not leave thread in both active and completed lists."""

    def test_completed_thread_not_in_active_after_completion(self):
        """After 3 ADVANCED signals, thread is only in completed_threads, not active_threads."""
        arc = _make_arc(active=[{"id": "t1", "state": ThreadState.ACTIVE, "progress": 0}])
        state = _make_state(arc)

        class PR1:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR1())
        assert result is not None

        arc = result
        state = _make_state(arc)

        class PR2:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR2())
        assert result is not None

        arc = result
        state = _make_state(arc)

        class PR3:
            thread_signals = [_signal("t1", "advanced")]
        result = _apply_thread_signals(state, PR3())
        assert result is not None
        assert len(result.active_threads) == 0
        assert len(result.completed_threads) == 1
        assert result.completed_threads[0].state == ThreadState.COMPLETE

    def test_promoted_thread_not_in_latent_after_promotion(self):
        """After latent promoted to active, thread is only in active_threads, not latent_threads."""
        arc = _make_arc(
            active=[{"id": "t1", "state": ThreadState.ACTIVE}],
            latent=[{"id": "t2", "state": ThreadState.LATENT}],
        )
        state = _make_state(arc)

        class ProgressResult:
            thread_signals = [_signal("t1", "failed")]

        result = _apply_thread_signals(state, ProgressResult())
        assert result is not None
        assert len(result.active_threads) == 1
        assert result.active_threads[0].id == "t2"
        assert result.active_threads[0].state == ThreadState.ACTIVE
        assert len(result.latent_threads) == 0


class TestMergeArcUpdate:
    """_merge_arc_update should do set-replace, not upsert, for thread lists."""

    def test_merge_arc_update_replaces_active_threads(self):
        """Verify set-replace behavior: threads moved from active to completed should not remain in active."""
        state_arc = {"active_threads": [{"id": "t1", "summary": "old", "state": "active", "progress": 0}], "completed_threads": [{"id": "t2", "summary": "done", "state": "complete", "progress": 0}]}

        # Simulate what _apply_thread_signals returns: t1 moved to completed
        updated_arc = CampaignArc(
            active_threads=[],
            completed_threads=[
                ArcThread(id="t1", summary="old", state=ThreadState.COMPLETE, progress=0),
                ArcThread(id="t2", summary="done", state=ThreadState.COMPLETE, progress=0),
            ],
        )

        _merge_arc_update(state_arc, updated_arc)
        assert state_arc["active_threads"] == []
        assert len(state_arc["completed_threads"]) == 2
        completed_ids = {t["id"] for t in state_arc["completed_threads"]}
        assert "t1" in completed_ids
        assert "t2" in completed_ids
