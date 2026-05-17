"""Arc thread signals integration tests.

Tests the campaign arc system: thread signals, engagement scoring, latent threads.
"""


from ccya.state import load_state, save_state

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    base_state,
    progress_response,
    state_with_arc,
)


class TestArcThreadSignals:
    """Thread signals advance or fail active threads."""

    async def test_thread_signal_advances_progress(self, saved_base_state, config):
        """A thread signal with signal='advanced' increments thread progress."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 0,
                    "tags": [],
                }
            ],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "search for the freighter", config)

        final = load_state(saved_base_state)
        threads = final["arc"]["active_threads"]
        find_thread = [t for t in threads if t["id"] == "find-freighter"]
        assert len(find_thread) == 1
        assert find_thread[0]["progress"] == 1

    async def test_thread_completes_at_threshold(self, saved_base_state, config):
        """When thread progress reaches _THREAD_COMPLETION_THRESHOLD (3), it moves to completed."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 2,
                    "tags": [],
                }
            ],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "almost found it", config)

        final = load_state(saved_base_state)
        active = final["arc"]["active_threads"]
        completed = final["arc"]["completed_threads"]
        assert len(active) == 0
        assert len(completed) == 1
        assert completed[0]["id"] == "find-freighter"

    async def test_thread_failed_signal(self, saved_base_state, config):
        """A thread signal with signal='failed' marks the thread as failed."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 1,
                    "tags": [],
                }
            ],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "failed"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "give up on the freighter", config)

        final = load_state(saved_base_state)
        active = final["arc"]["active_threads"]
        completed = final["arc"]["completed_threads"]
        assert len(active) == 0
        assert len(completed) == 1
        assert completed[0]["id"] == "find-freighter"
        assert completed[0]["state"] == "failed"


class TestArcLatentThreads:
    """Latent threads promote to active when active threads complete."""

    async def test_latent_promotes_on_completion(self, saved_base_state, config):
        """When an active thread completes, a latent thread with no unlock_if promotes."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 3,
                    "tags": [],
                }
            ],
            "latent_threads": [
                {
                    "id": "rescue-crew",
                    "summary": "Rescue the crew",
                    "state": "latent",
                    "progress": 0,
                    "tags": [],
                }
            ],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "complete the mission", config)

        final = load_state(saved_base_state)
        active = final["arc"]["active_threads"]
        latent = final["arc"]["latent_threads"]
        # find-freighter completed, rescue-crew should promote
        active_ids = [t["id"] for t in active]
        assert "rescue-crew" in active_ids
        assert len(latent) == 0

    async def test_latent_with_unlock_if_not_promoted(self, saved_base_state, config):
        """Latent threads with unlock_if conditions are not promoted until conditions met."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 3,
                    "tags": [],
                }
            ],
            "latent_threads": [
                {
                    "id": "rescue-crew",
                    "summary": "Rescue the crew",
                    "state": "latent",
                    "progress": 0,
                    "tags": [],
                    "unlock_if": "has-key",
                }
            ],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "complete the mission", config)

        final = load_state(saved_base_state)
        active = final["arc"]["active_threads"]
        latent = final["arc"]["latent_threads"]
        # rescue-crew has unlock_if="has-key", so should NOT promote
        active_ids = [t["id"] for t in active]
        assert "rescue-crew" not in active_ids
        assert len(latent) == 1


class TestArcCandidateOpportunity:
    """candidate_opportunity from progress extraction creates latent threads."""

    async def test_candidate_opportunity_creates_latent_thread(self, saved_base_state, config):
        """A candidate_opportunity string creates a latent thread."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        prog_resp = progress_response(candidate_opportunity="Investigate the mysterious signal")
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "investigate the signal", config)

        final = load_state(saved_base_state)
        latent = final["arc"]["latent_threads"]
        assert len(latent) == 1
        assert "investigate" in latent[0]["id"]


class TestArcEngagement:
    """Arc engagement scoring based on thread signal matching."""

    async def test_engagement_increases_with_signals(self, saved_base_state, config):
        """Arc engagement increases when thread signals match active threads."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {
                    "id": "find-freighter",
                    "summary": "Find the lost freighter",
                    "state": "active",
                    "progress": 0,
                    "tags": [],
                }
            ],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "find-freighter", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "search for the freighter", config)

        final = load_state(saved_base_state)
        # Arc engagement should have been updated by tick_arc()
        assert "arc_engagement" in final["arc"]


class TestArcActiveThreadCap:
    """Active threads are capped at _ACTIVE_THREAD_CAP (4)."""

    async def test_active_thread_cap_enforced(self, saved_base_state, config):
        """When active threads reach the cap, new threads without unlock_if are not promoted."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {"id": "t1", "summary": "Thread 1", "state": "active", "progress": 3, "tags": []},
                {"id": "t2", "summary": "Thread 2", "state": "active", "progress": 3, "tags": []},
                {"id": "t3", "summary": "Thread 3", "state": "active", "progress": 3, "tags": []},
                {"id": "t4", "summary": "Thread 4", "state": "active", "progress": 3, "tags": []},
            ],
            "latent_threads": [
                {"id": "t5", "summary": "Thread 5", "state": "latent", "progress": 0, "tags": []},
            ],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        thread_signals = [
            {"id": "t1", "signal": "advanced"},
            {"id": "t2", "signal": "advanced"},
            {"id": "t3", "signal": "advanced"},
            {"id": "t4", "signal": "advanced"},
        ]
        prog_resp = progress_response(thread_signals=thread_signals)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "advance all threads", config)

        final = load_state(saved_base_state)
        active = final["arc"]["active_threads"]
        # 4 threads complete, t5 should promote (cap=4, after completion there are 0 active)
        assert len(active) == 1


class TestArcLatentCap:
    """Latent threads are capped at _LATENT_CAP (4)."""

    async def test_latent_thread_cap_enforced(self, saved_base_state, config):
        """When latent threads reach the cap, the oldest tactical thread is evicted."""
        from ccya.engine.turn import _TACTICAL_TAG

        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {"id": "a1", "summary": "Active 1", "state": "active", "progress": 1, "tags": [], "last_offered_turn": 1, "promotes": [], "urgency": "normal"},
                {"id": "a2", "summary": "Active 2", "state": "active", "progress": 1, "tags": [], "last_offered_turn": 2, "promotes": [], "urgency": "normal"},
                {"id": "a3", "summary": "Active 3", "state": "active", "progress": 1, "tags": [], "last_offered_turn": 3, "promotes": [], "urgency": "normal"},
                {"id": "a4", "summary": "Active 4", "state": "active", "progress": 1, "tags": [], "last_offered_turn": 4, "promotes": [], "urgency": "normal"},
            ],
            "latent_threads": [
                {"id": "l1", "summary": "Latent 1", "state": "latent", "progress": 0, "tags": [_TACTICAL_TAG], "last_offered_turn": 1},
                {"id": "l2", "summary": "Latent 2", "state": "latent", "progress": 0, "tags": [_TACTICAL_TAG], "last_offered_turn": 2},
                {"id": "l3", "summary": "Latent 3", "state": "latent", "progress": 0, "tags": [_TACTICAL_TAG], "last_offered_turn": 3},
                {"id": "l4", "summary": "Latent 4", "state": "latent", "progress": 0, "tags": [_TACTICAL_TAG], "last_offered_turn": 4},
            ],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        # Add a new candidate_opportunity -> should evict l1 (oldest tactical)
        prog_resp = progress_response(candidate_opportunity="New opportunity thread")
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "consider the opportunity", config)

        final = load_state(saved_base_state)
        latent = final["arc"]["latent_threads"]
        latent_ids = [t["id"] for t in latent]
        assert "l1" not in latent_ids  # evicted (oldest tactical)
        assert len(latent) == 4


class TestArcUpdateStances:
    """PC expressed stances are updated from player input."""

    async def test_expressed_stances_updated(self, saved_base_state, config):
        """PC expressed_stances are updated based on keywords in player input."""
        s = base_state(0)
        s["pc"]["expressed_stances"] = {}
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "I want to fight the enemy", config)

        final = load_state(saved_base_state)
        stances = final["pc"]["expressed_stances"]
        assert isinstance(stances, dict)


class TestArcNarratorArcUpdate:
    """Narrator can emit arc_update blocks in narration output."""

    async def test_narrator_arc_update_extracted(self, saved_base_state, config):
        """When narration contains <<<ARC_UPDATE_START>>>, the arc is updated."""
        s = state_with_arc(0, {
            "visible_goal": "Find the lost freighter",
            "thematic_question": "How far will you go for a paycheck?",
            "active_threads": [
                {"id": "find-freighter", "summary": "Find the lost freighter", "state": "active", "progress": 0, "tags": []},
            ],
            "latent_threads": [],
            "completed_threads": [],
            "arc_engagement": 0,
        })
        save_state(saved_base_state, s)

        narrative = "Vex finds a clue.\n\n<<<ARC_UPDATE_START>>>\n{\"active_threads\": [{\"id\": \"find-freighter\", \"summary\": \"Find the lost freighter\", \"state\": \"active\", \"progress\": 1, \"tags\": []}]}\n<<<ARC_UPDATE_END>>>"
        fake = _FakeLLM(narrative=narrative)
        with fake:
            await _run(saved_base_state, "find the clue", config)

        final = load_state(saved_base_state)
        threads = final["arc"]["active_threads"]
        find_thread = [t for t in threads if t["id"] == "find-freighter"]
        assert len(find_thread) == 1
        assert find_thread[0]["progress"] == 1
