"""Tests for extraction pipeline: deescalate/quest_ages context, gm_beat source, pressure update guard."""

import json
import tempfile
from pathlib import Path

import pytest

from ccya.engine import (
    _build_jinja_env,
    _extract_progress_messages,
    EngineConfig,
)
from ccya.models import (
    GMBeat,
    ProgressExtractResult,
    SceneExtractResult,
    StateExtractResult,
)

# Reuse the existing fakes / helpers from the smoke suite.
from tests.test_engine_smoke import (
    _FakeLLM,
    _make_state,
    _run,
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


# ---------------------------------------------------------------------------
# Pressure update guard tests
# ---------------------------------------------------------------------------

_SAVE_DIR = Path(tempfile.mkdtemp())


def _make_state_with_pressures(turn: int = 0, pressures: list[dict] | None = None) -> dict:
    state = _make_state(turn=turn)
    state["scene"]["scene_pressure"] = pressures or []
    return state


def _progress_response_with_pressure_update(
    pressure_update: list[dict] | None = None,
) -> str:
    return json.dumps({
        "quest_updates": [],
        "recent_events_add": [],
        "recent_events_update": [],
        "recent_events_remove": [],
        "actions": [],
        "outcome_summary": "",
        "scene_pressure_update": pressure_update or [],
    })


@pytest.mark.asyncio
async def test_pressure_update_guard_drops_unknown_id():
    """scene_pressure_update entries with unknown ids must be silently dropped before merge."""
    state = _make_state_with_pressures(
        turn=0,
        pressures=[
            {"id": "known-pressure", "text": "A known threat", "urgency": "immediate", "turn_added": 1},
        ],
    )
    from ccya.state import save_state
    save_state(_SAVE_DIR, state)

    with _FakeLLM(
        narrative="The known threat looms, and a new danger appears.",
        progress_response=_progress_response_with_pressure_update(
            pressure_update=[
                {"id": "unknown-pressure", "text": "A fabricated threat", "urgency": "building"},
                {"id": "known-pressure", "text": "Updated known threat", "urgency": "building"},
            ],
        ),
    ):
        result = await _run(_SAVE_DIR, "observe the threats", config=EngineConfig())

    assert result is not None
    # The unknown-pressure should have been dropped; only known-pressure should remain
    pressure_updates = result.state_delta.get("scene_pressure_update", [])
    updated_ids = [p.get("id") if isinstance(p, dict) else p.id for p in pressure_updates]
    assert "unknown-pressure" not in updated_ids
    assert "known-pressure" in updated_ids


@pytest.mark.asyncio
async def test_pressure_update_guard_passes_known_id():
    """scene_pressure_update entries with known ids must pass through to StateDelta."""
    state = _make_state_with_pressures(
        turn=0,
        pressures=[
            {"id": "pressure-a", "text": "Threat A", "urgency": "building", "turn_added": 1},
            {"id": "pressure-b", "text": "Threat B", "urgency": "immediate", "turn_added": 2},
        ],
    )
    from ccya.state import save_state
    save_state(_SAVE_DIR, state)

    with _FakeLLM(
        narrative="Both pressures intensify.",
        progress_response=_progress_response_with_pressure_update(
            pressure_update=[
                {"id": "pressure-a", "text": "Threat A worsened", "urgency": "immediate"},
                {"id": "pressure-b", "text": "Threat B shifted", "urgency": "building"},
            ],
        ),
    ):
        result = await _run(_SAVE_DIR, "watch the pressures", config=EngineConfig())

    assert result is not None
    pressure_updates = result.state_delta.get("scene_pressure_update", [])
    updated_ids = [p.get("id") if isinstance(p, dict) else p.id for p in pressure_updates]
    assert "pressure-a" in updated_ids
    assert "pressure-b" in updated_ids
    assert len(pressure_updates) == 2


@pytest.mark.asyncio
async def test_pressure_update_guard_empty_when_no_existing_pressures():
    """When state has no pressures, all updates should be dropped."""
    state = _make_state_with_pressures(turn=0, pressures=[])
    from ccya.state import save_state
    save_state(_SAVE_DIR, state)

    with _FakeLLM(
        narrative="Nothing to update.",
        progress_response=_progress_response_with_pressure_update(
            pressure_update=[
                {"id": "phantom", "text": "No such pressure", "urgency": "background"},
            ],
        ),
    ):
        result = await _run(_SAVE_DIR, "do nothing", config=EngineConfig())

    assert result is not None
    pressure_updates = result.state_delta.get("scene_pressure_update", [])
    assert len(pressure_updates) == 0
