"""Tests for ccya.engine.generate_pack."""
from pathlib import Path
from unittest.mock import patch
import yaml
import pytest


def _make_llm_response():
    """Minimal valid ScenarioBrief YAML output."""
    return yaml.dump({
        "constraints": {},
        "world_facts": ["The world is covered in perpetual mist."],
        "narrator_rules": ["Write in second person."],
        "world_rules": [
            "Mist-navigation requires a tuned compass — GPS does not function.",
            "The sun has not been seen in forty years.",
            "Animals above rodent size no longer exist.",
        ],
        "factions": [],
        "locations": [],
        "name_locales": [],
        "name_seed": 1,
        "inspiration": {},
    })


@pytest.fixture
def tmp_packs(tmp_path):
    return tmp_path


@pytest.fixture
def template_dir():
    return str(Path(__file__).parent.parent / "ccya" / "prompts")


@pytest.mark.asyncio
async def test_generate_pack_from_brief_happy_path(tmp_packs, template_dir):
    from ccya.engine.generate_pack import generate_pack_from_brief

    mock_response = {"response": _make_llm_response()}

    with patch("ccya.engine.generate_pack.llm_chat") as mock_chat:
        mock_chat.return_value = mock_response

        inputs = {
            "concept": "A world of perpetual mist where the sun never shines.",
            "world_name": "The Murk",
            "tone_tags": ["horror", "survival"],
            "mood_note": "bleak",
            "world_rules": [
                "Mist-navigation requires a tuned compass.",
                "The sun has not been seen in forty years.",
            ],
        }

        events = []
        async for evt in generate_pack_from_brief(
            inputs=inputs,
            packs_root=tmp_packs,
            llm_host="http://localhost:8080/v1",
            llm_model="test-model",
            template_dir=template_dir,
            trace_id="test0001",
        ):
            events.append(evt)

    types = [e["type"] for e in events]
    assert "pack_ready" in types
    assert "generation_error" not in types

    assert (tmp_packs / "generated").exists()


@pytest.mark.asyncio
async def test_generate_pack_from_brief_llm_error(tmp_packs, template_dir):
    from ccya.engine.generate_pack import generate_pack_from_brief

    with patch("ccya.engine.generate_pack.llm_chat") as mock_chat:
        mock_chat.side_effect = RuntimeError("LLM offline")

        events = []
        async for evt in generate_pack_from_brief(
            inputs={"concept": "test"},
            packs_root=tmp_packs,
            llm_host="http://localhost:8080/v1",
            llm_model="test-model",
            template_dir=template_dir,
            trace_id="test0002",
        ):
            events.append(evt)

    assert any(e["type"] == "generation_error" for e in events)


@pytest.mark.asyncio
async def test_generate_pack_from_brief_retries_on_failure(tmp_packs, template_dir):
    from ccya.engine.generate_pack import generate_pack_from_brief

    mock_response = {"response": _make_llm_response()}

    with patch("ccya.engine.generate_pack.llm_chat") as mock_chat:
        mock_chat.side_effect = [RuntimeError("502"), RuntimeError("502"), mock_response]

        events = []
        async for evt in generate_pack_from_brief(
            inputs={"concept": "test"},
            packs_root=tmp_packs,
            llm_host="http://localhost:8080/v1",
            llm_model="test-model",
            template_dir=template_dir,
            trace_id="test0003",
            max_retries=2,
        ):
            events.append(evt)

    assert mock_chat.call_count == 3
    assert any(e["type"] == "pack_ready" for e in events)
    assert not any(e["type"] == "generation_error" for e in events)
