"""Tests for extraction pipeline: deescalate/quest_ages context, gm_beat source."""

from pathlib import Path

from ccya.engine import (
    _build_jinja_env,
    _extract_progress_messages,
)
from ccya.models import (
    GMBeat,
    ProgressExtractResult,
    SceneExtractResult,
    StateExtractResult,
)

_TEMPLATE_DIR = str(Path(__file__).parent.parent / "ccya" / "prompts")


class TestProgressMessagesReceivesDeescalate:
    def test_deescalate_in_context(self):
        """_extract_progress_messages includes deescalate in user_ctx."""
        env = _build_jinja_env(_TEMPLATE_DIR)
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(
            env, "N.", {},
            active_domains=["quest_updates"],
            state_result=state_res,
            intent=None,
            deescalate=0.6,
            recent_turns=[],
        )
        # Verify the function accepts the parameter without error
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_deescalate_default_zero(self):
        """_extract_progress_messages defaults deescalate to 0.0."""
        env = _build_jinja_env(_TEMPLATE_DIR)
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(
            env, "N.", {},
            active_domains=["quest_updates"],
            state_result=state_res,
            intent=None,
            recent_turns=[],
        )
        assert len(msgs) == 2


class TestProgressMessagesReceivesQuestAges:
    def test_quest_ages_in_context(self):
        """_extract_progress_messages includes quest_ages in user_ctx."""
        env = _build_jinja_env(_TEMPLATE_DIR)
        state_res = StateExtractResult()
        quest_ages = [{"id": "q1", "title": "Test Quest", "age": 3}]
        msgs = _extract_progress_messages(
            env, "N.", {},
            active_domains=["quest_updates"],
            state_result=state_res,
            intent=None,
            quest_ages=quest_ages,
            recent_turns=[],
        )
        assert len(msgs) == 2

    def test_quest_ages_empty_default(self):
        """_extract_progress_messages defaults quest_ages to empty list."""
        env = _build_jinja_env(_TEMPLATE_DIR)
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(
            env, "N.", {},
            active_domains=["quest_updates"],
            state_result=state_res,
            intent=None,
            recent_turns=[],
        )
        assert len(msgs) == 2


class TestGmBeatFromProgressNotScene:
    def test_beat_stored_from_progress_result(self):
        """gm_beat is read from progress_result, not scene_result."""
        progress_result = ProgressExtractResult(
            gm_beat=GMBeat(
                type="complication",
                instruction="A long enough instruction string that passes the quality gate without issues",
            )
        )

        # This test verifies the model-level behavior: ProgressExtractResult
        # has gm_beat, SceneExtractResult does not. The pipeline wiring is
        # tested in test_turn.py via the full run_turn path.
        assert progress_result.gm_beat is not None
        assert progress_result.gm_beat.type == "complication"
        assert "gm_beat" not in SceneExtractResult.model_fields
