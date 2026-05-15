"""Integration test: progress prompt contains this-turn NPC."""
from unittest.mock import MagicMock, patch
from ccya.engine.extraction import (
    _build_extraction_context,
    _extract_progress_messages,
)
from ccya.models import SceneExtractResult, StateExtractResult, NpcAdd


def _fake_render(env, template, ctx):
    """Stub renderer: returns the context vars as a string."""
    npcs = ctx.get("present_npcs", [])
    return " ".join(n.get("name", "") for n in npcs)


def test_progress_prompt_contains_this_turn_npc():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": [], "recent_events": [], "world_state": []},
        "inventory": [],
        "pc": {"conditions": [], "stats": {}},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
        "meta": {},
    }
    scene_result = SceneExtractResult(npc_add=[NpcAdd(id="captain_01", notes="", name="Captain Aldric")])
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)

    with patch("ccya.engine.extraction._render", side_effect=_fake_render):
        msgs = _extract_progress_messages(
            env=MagicMock(),
            narration="Captain Aldric enters.",
            state=state,
            state_result=state_result,
            extraction_ctx=ctx,
            turn_no=5,
        )

    user_msg = next((m["content"] for m in msgs if m["role"] == "user"), "")
    assert "Captain Aldric" in user_msg
