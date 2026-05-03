"""Tests for engine.generate_seed() — mocked LLM, no real model needed."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import ccya.engine
from ccya.engine import EngineConfig, generate_seed
from ccya.pack import (
    Constraints,
    Inspiration,
    Pack,
    PackManifest,
    PlayerOverrides,
    ScenarioBrief,
    SeedEnvelope,
)

PROMPTS_DIR = Path(__file__).parent.parent / "ccya" / "prompts"
PACKS_DIR = Path(__file__).parent.parent / "packs"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_dynamic_pack(
    *,
    min_named_npcs: int = 2,
    forbid_cliches: list[str] | None = None,
) -> Pack:
    """Return a minimal in-memory dynamic Pack object without touching disk."""
    constraints = Constraints(
        min_named_npcs=min_named_npcs,
        starting_quest_count=1,
        min_objectives_per_quest=2,
        inventory_size_range=(4, 8),
        prose_word_range=(50, 1000),
        forbid_cliches=forbid_cliches or [],
    )
    inspiration = Inspiration(
        pc="A person.",
        opening_situation="A situation.",
        npcs="Some people.",
        inventory="Some items.",
        quests="A task.",
    )
    return Pack(
        manifest=PackManifest(
            id="test-dynamic",
            name="Test Dynamic",
            mode="dynamic",
        ),
        world_text="The world is dangerous.\n- There is no power grid.\n- Water is scarce.",
        scenario=ScenarioBrief(constraints=constraints, inspiration=inspiration),
        style_text="Be concise.",
    )


def _valid_envelope_json(
    *,
    npc_names: list[str] | None = None,
    opening_words: int = 80,
    opening_text: str | None = None,
) -> str:
    npc_names = npc_names or ["Amara Cole", "Blake Osei"]
    npcs = [
        {
            "id": n.lower().replace(" ", "-"),
            "name": n,
            "title": "Survivor",
            "notes": "Cautious.",
            "bio": f"{n} has been here a while.",
        }
        for n in npc_names
    ]
    opening = opening_text or " ".join(["word"] * opening_words)
    envelope = {
        "seed_state": {
            "meta": {
                "game_name": "default",
                "turn": 0,
                "setting_pack": "test-dynamic",
                "model": "",
            },
            "pc": {
                "name": "Tester",
                "tagline": "quiet and careful",
                "bio": "A history.",
                "stats": {"body": 2, "mind": 2, "tech": 2, "social": 2},
                "conditions": [],
            },
            "location": {
                "id": "test-loc",
                "name": "Test Location",
                "description": "A ruined building.",
            },
            "inventory": [
                {"id": "knife", "name": "Knife", "notes": "Sharp.", "amount": 1},
                {
                    "id": "water",
                    "name": "Water bottle",
                    "notes": "Half full.",
                    "amount": 1,
                },
                {"id": "map", "name": "Map", "notes": "Marked.", "amount": 1},
                {"id": "backpack", "name": "Backpack", "notes": "Heavy.", "amount": 1},
            ],
            "quests": [
                {
                    "id": "q1",
                    "title": "Find safety",
                    "status": "active",
                    "objectives": [
                        {"description": "Locate the shelter.", "done": False},
                        {"description": "Reach it before nightfall.", "done": False},
                    ],
                }
            ],
            "scene": {
                "tagline": "Ruins at dusk",
                "tags": ["arrival"],
                "present_npcs": npcs,
                "recent_events": ["Tester arrived this morning."],
            },
            "compendium": {"npcs": {}},
        },
        "opening_narrative": opening,
        "actions": [
            "Search the building.",
            "Call out for survivors.",
            "Hide and wait.",
            "Move toward the shelter.",
        ],
    }
    return json.dumps(envelope)


def _config() -> EngineConfig:
    return EngineConfig(
        host="http://localhost:8080/v1",
        model="test-model",
        generate_seed_temperature=0.9,
        generate_seed_max_retries=1,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_generate_seed_happy_path():
    pack = _minimal_dynamic_pack()
    payload = _valid_envelope_json()

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(return_value={"response": payload, "done": True}),
    ) as mock_chat:
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    assert isinstance(envelope, SeedEnvelope)
    assert envelope.seed_state.pc.name == "Tester"
    assert len(envelope.seed_state.scene.present_npcs) == 2
    assert envelope.opening_narrative.startswith("word")
    mock_chat.assert_called_once()


async def test_generate_seed_injects_world_facts():
    """World facts from world.md must appear at the top of world_state."""
    pack = _minimal_dynamic_pack()
    envelope_raw = json.loads(_valid_envelope_json())
    # Seed has one scenario-specific fact already
    envelope_raw["seed_state"]["scene"]["world_state"] = [
        "Tester arrived this morning."
    ]

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(
            return_value={"response": json.dumps(envelope_raw), "done": True}
        ),
    ):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    facts = envelope.seed_state.scene.world_state
    # World facts from world_text should be prepended
    assert "The world is dangerous." in facts
    assert "There is no power grid." in facts
    # World facts should precede scenario-specific ones
    world_idx = facts.index("The world is dangerous.")
    scenario_idx = facts.index("Tester arrived this morning.")
    assert world_idx < scenario_idx


async def test_generate_seed_baseline_facts_override_world_md():
    """When pack.manifest.baseline_facts is set, those take precedence over parse_world_facts(world.md)."""
    pack = _minimal_dynamic_pack()
    pack.manifest.baseline_facts = [
        "Curated fact one.",
        "Curated fact two.",
        "Curated fact three.",
    ]
    envelope_raw = json.loads(_valid_envelope_json())
    envelope_raw["seed_state"]["scene"]["world_state"] = ["A scenario-specific fact."]

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(
            return_value={"response": json.dumps(envelope_raw), "done": True}
        ),
    ):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    facts = envelope.seed_state.scene.world_state
    # Curated baseline_facts must be at the top, in order
    assert facts[0] == "Curated fact one."
    assert facts[1] == "Curated fact two."
    assert facts[2] == "Curated fact three."
    # parse_world_facts() output (e.g. "The world is dangerous.") must NOT be present
    assert "The world is dangerous." not in facts
    assert "There is no power grid." not in facts
    # Scenario-specific fact still preserved after the baseline
    assert "A scenario-specific fact." in facts


async def test_generate_seed_clears_compendium():
    """Engine must reset compendium.npcs to {} even if LLM populated it."""
    pack = _minimal_dynamic_pack()
    envelope_raw = json.loads(_valid_envelope_json())
    envelope_raw["seed_state"]["compendium"] = {
        "npcs": {"someone": {"name": "Someone", "title": "Role", "bio": "Bio."}}
    }
    envelope_raw["seed_state"]["meta"]["compendium_touch_order"] = ["someone"]

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(
            return_value={"response": json.dumps(envelope_raw), "done": True}
        ),
    ):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    assert envelope.seed_state.compendium.npcs == {}
    assert "compendium_touch_order" not in envelope.seed_state.meta


# ---------------------------------------------------------------------------
# Retry on parse failure
# ---------------------------------------------------------------------------


async def test_generate_seed_retries_on_invalid_json():
    """First call returns garbage; second returns valid envelope; result is valid."""
    pack = _minimal_dynamic_pack()
    good = _valid_envelope_json()
    call_count = 0

    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"response": "not valid json at all {{{{", "done": True}
        return {"response": good, "done": True}

    with patch.object(ccya.engine, "llm_chat", new=_side_effect):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    assert isinstance(envelope, SeedEnvelope)
    assert call_count == 2


async def test_generate_seed_retries_on_validation_failure():
    """First call returns JSON that fails Pydantic; second returns valid."""
    pack = _minimal_dynamic_pack()
    bad_envelope = json.dumps(
        {
            "seed_state": {},  # missing required fields
            "opening_narrative": "short",
        }
    )
    good = _valid_envelope_json()
    call_count = 0

    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return {"response": bad_envelope if call_count == 1 else good, "done": True}

    with patch.object(ccya.engine, "llm_chat", new=_side_effect):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    assert isinstance(envelope, SeedEnvelope)
    assert call_count == 2


async def test_generate_seed_raises_after_all_retries_fail():
    """All attempts return garbage — RuntimeError expected."""
    pack = _minimal_dynamic_pack()

    async def _always_bad(*args, **kwargs):
        return {"response": "not json {{{", "done": True}

    with patch.object(ccya.engine, "llm_chat", new=_always_bad):
        with pytest.raises(RuntimeError, match="generate_seed failed"):
            await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))


# ---------------------------------------------------------------------------
# Soft validation warnings (logged, not raised)
# ---------------------------------------------------------------------------


async def test_generate_seed_soft_warning_npc_count(caplog):
    """With min_named_npcs=3, only 2 NPCs should trigger a warning (not a failure)."""
    pack = _minimal_dynamic_pack(min_named_npcs=3)
    payload = _valid_envelope_json(npc_names=["Amara Cole", "Blake Osei"])

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(return_value={"response": payload, "done": True}),
    ):
        import logging

        with caplog.at_level(logging.WARNING, logger="ccya.engine"):
            envelope = await generate_seed(
                pack, _config(), template_dir=str(PROMPTS_DIR)
            )

    assert isinstance(envelope, SeedEnvelope)
    assert any("named NPCs" in r.message for r in caplog.records)


async def test_generate_seed_soft_warning_cliche(caplog):
    """Opening narrative containing a forbidden cliché word triggers a soft warning."""
    pack = _minimal_dynamic_pack(forbid_cliches=["chosen one"])
    opening = "You are the chosen one who must save the world. The burden is yours alone to carry."
    payload = _valid_envelope_json(opening_text=opening)

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(return_value={"response": payload, "done": True}),
    ):
        import logging

        with caplog.at_level(logging.WARNING, logger="ccya.engine"):
            envelope = await generate_seed(
                pack, _config(), template_dir=str(PROMPTS_DIR)
            )

    assert isinstance(envelope, SeedEnvelope)
    assert any(
        "cliché" in r.message or "cliche" in r.message.lower() for r in caplog.records
    )


# ---------------------------------------------------------------------------
# Player overrides (smoke — just ensure they don't crash)
# ---------------------------------------------------------------------------


async def test_generate_seed_with_player_overrides():
    pack = _minimal_dynamic_pack()
    overrides = PlayerOverrides(
        pc_hints="Former nurse", location_hints="Somewhere cold"
    )
    payload = _valid_envelope_json()

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(return_value={"response": payload, "done": True}),
    ) as mock_chat:
        envelope = await generate_seed(
            pack, _config(), overrides=overrides, template_dir=str(PROMPTS_DIR)
        )

    assert isinstance(envelope, SeedEnvelope)
    # Overrides should appear in the messages sent to the LLM
    call_args = mock_chat.call_args
    all_text = " ".join(m["content"] for m in call_args[0][2])
    assert "nurse" in all_text.lower() or "cold" in all_text.lower()


# ---------------------------------------------------------------------------
# Static pack mode guard
# ---------------------------------------------------------------------------


async def test_generate_seed_rejects_static_pack():
    """Calling generate_seed() on a static pack should raise ValueError immediately."""
    static_pack = Pack.model_construct(
        manifest=PackManifest.model_construct(id="s", name="S", mode="static"),
    )
    with pytest.raises(ValueError, match="dynamic"):
        await generate_seed(static_pack, _config(), template_dir=str(PROMPTS_DIR))


# ---------------------------------------------------------------------------
# Real pack integration (reads from disk, mocks LLM)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (PACKS_DIR / "zombie-survival").is_dir(), reason="zombie pack not present"
)
async def test_generate_seed_zombie_pack_disk(tmp_path):
    """Load the real zombie-survival pack from disk, mock the LLM, validate output."""
    from ccya.pack import load_pack

    pack = load_pack("zombie-survival", PACKS_DIR)
    assert pack.manifest.mode == "dynamic"

    payload = _valid_envelope_json(
        opening_text="You are standing in a ruined " + " building " * 30
    )

    with patch.object(
        ccya.engine,
        "llm_chat",
        new=AsyncMock(return_value={"response": payload, "done": True}),
    ):
        envelope = await generate_seed(pack, _config(), template_dir=str(PROMPTS_DIR))

    assert isinstance(envelope, SeedEnvelope)
    # World facts should have been injected
    facts = envelope.seed_state.scene.world_state
    assert len(facts) > 1
