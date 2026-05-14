"""Verify extract_progress_system.j2 renders the completed quest dedup example."""

from pathlib import Path

from ccya.engine import _build_jinja_env, _extract_progress_messages
from ccya.engine.extraction import _ExtractionContext
from ccya.models import StateExtractResult


class TestExtractProgressQuestDedup:
    """Verify the NEVER emit completed quest example is rendered in the system prompt."""

    def _env(self):
        return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))

    def test_completed_quest_dedup_example_present(self):
        env = self._env()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(
            env, "N.", {}, state_result=state_res, extraction_ctx=_ExtractionContext(), intent=None, recent_turns=[]
        )
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "NEVER emit a completed quest again" in system
        assert "settle_the_debt" in system
        assert "Do not re-activate completed quests" in system
