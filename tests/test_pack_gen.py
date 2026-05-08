"""Tests for ccya.engine.pack_gen — mocked LLM, no real model needed."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import yaml

import ccya.engine
from ccya.engine import EngineConfig, generate_pack
from ccya.pack import Pack, WorldBrief

PROMPTS_DIR = Path(__file__).parent.parent / "ccya" / "prompts"


def _valid_scenario_json() -> str:
    return json.dumps({
        "constraints": {
            "min_named_npcs": 2,
            "min_objectives_per_quest": 2,
            "starting_quest_count": 1,
            "inventory_size_range": [3, 7],
            "pc_stat_range": [1, 4],
            "pc_stat_total_range": [8, 14],
            "prose_word_range": [300, 550],
            "required_inventory_kinds": ["tools"],
            "npc_distinct_first_letters": True,
            "forbid_cliches": ["chosen one", "lost heir"],
            "forbid_player_dependents": True,
            "forbid_legendary_items": True,
        },
        "world_facts": [
            "The Great Flood of 2089 submerged 40% of habitable land.",
            "The Dike Council controls all freshwater distribution.",
            "Submerged cities are rich in pre-flood technology.",
        ],
        "narrator_rules": [
            "Water is always a presence — dripping, rising, receding.",
            "Survival is mundane; heroism is rare and costly.",
            "Factions compete for resources, not ideology.",
            "Death by drowning or exposure is common.",
            "Scavenged technology is unreliable and dangerous.",
            "Trust is earned through shared labor, not words.",
        ],
        "factions": [
            {"id": "dike_council", "name": "Dike Council", "description": "Controls freshwater and flood barriers.", "disposition": "neutral"},
            {"id": "reef_raiders", "name": "Reef Raiders", "description": "Pirate gangs operating from submerged skyscrapers.", "disposition": "hostile"},
            {"id": "mud_sifters", "name": "Mud Sifters", "description": "Scavenger collective diving pre-flood ruins.", "disposition": "friendly"},
        ],
        "locations": [
            {"id": "high_ground", "name": "High Ground", "type": "settlement", "description": "Last dry district, Dike Council headquarters."},
            {"id": "sunken_mall", "name": "Sunken Mall", "type": "ruin", "description": "Partially flooded pre-flood shopping center, rich in tech."},
            {"id": "canal_route", "name": "Canal Route", "type": "transit", "description": "Main waterway connecting settlements."},
            {"id": "dike_station", "name": "Dike Station", "type": "institution", "description": "Flood barrier control center, heavily guarded."},
        ],
        "name_locales": [
            {"locale": "en_US", "weight": 0.5},
            {"locale": "en_GB", "weight": 0.3},
            {"locale": "nl_BE", "weight": 0.2},
        ],
        "name_seed": 42000000,
        "inspiration": {
            "pc": "A survivor with a specific skill.",
            "opening_situation": "Mid-crisis, not a fresh start.",
            "npcs": "People with conflicting agendas.",
            "inventory": "Scavenged, not purchased.",
            "quests": "Survival-driven, not glory-driven.",
        },
    })


def _config() -> EngineConfig:
    return EngineConfig(
        host="http://localhost:8080/v1",
        model="test-model",
        generate_seed_temperature=0.9,
        generate_seed_max_retries=1,
    )


async def test_generate_pack_writes_files_and_returns_pack(tmp_path: Path):
    """generate_pack() writes pack.yaml and scenario.yaml, returns a valid Pack."""
    brief = WorldBrief(concept="post-flood survival", tone="grim")
    packs_dir = tmp_path / "packs"

    with patch.object(
        ccya.engine.pack_gen,
        "llm_chat",
        new=AsyncMock(return_value={"response": _valid_scenario_json(), "done": True}),
    ):
        pack = await generate_pack(brief, _config(), packs_dir, template_dir=str(PROMPTS_DIR))

    # Verify files were written
    pack_dirs = list((packs_dir / "custom").iterdir())
    assert len(pack_dirs) == 1
    pack_dir = pack_dirs[0]
    assert (pack_dir / "pack.yaml").exists()
    assert (pack_dir / "scenario.yaml").exists()

    # Verify pack.yaml content
    with open(pack_dir / "pack.yaml") as f:
        manifest_data = yaml.safe_load(f)
    assert manifest_data["id"].startswith("post-flood")
    assert manifest_data["name"] == "Post-Flood Survival"
    assert manifest_data["generated"] is True
    assert manifest_data["world_brief_concept"] == "post-flood survival"

    # Verify scenario.yaml content
    with open(pack_dir / "scenario.yaml") as f:
        scenario_data = yaml.safe_load(f)
    assert "world_facts" in scenario_data
    assert "factions" in scenario_data
    assert len(scenario_data["factions"]) == 3

    # Verify returned Pack
    assert isinstance(pack, Pack)
    assert pack.scenario is not None
    assert len(pack.scenario.world_facts) == 3
    assert len(pack.scenario.factions) == 3
    assert len(pack.scenario.locations) == 4


async def test_generate_pack_retries_on_bad_json(tmp_path: Path):
    """generate_pack() retries when LLM returns non-JSON, then succeeds."""
    brief = WorldBrief(concept="space western")
    packs_dir = tmp_path / "packs"

    call_count = 0

    async def _bad_then_good(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"response": "This is not JSON at all.", "done": True}
        return {"response": _valid_scenario_json(), "done": True}

    with patch.object(ccya.engine.pack_gen, "llm_chat", new=AsyncMock(side_effect=_bad_then_good)):
        pack = await generate_pack(brief, _config(), packs_dir, template_dir=str(PROMPTS_DIR))

    assert call_count == 2
    assert pack.scenario is not None


async def test_generate_pack_retries_on_validation_failure(tmp_path: Path):
    """generate_pack() retries when ScenarioBrief validation fails, then succeeds."""
    brief = WorldBrief(concept="noir detective")
    packs_dir = tmp_path / "packs"

    bad_json = json.dumps({
        "constraints": {
            "min_named_npcs": 2,
            "min_objectives_per_quest": 2,
            "starting_quest_count": 1,
            "inventory_size_range": [3, 7],
            "pc_stat_range": [1, 4],
            "pc_stat_total_range": [8, 14],
            "prose_word_range": [300, 550],
            "required_inventory_kinds": [],
            "npc_distinct_first_letters": True,
            "forbid_cliches": [],
            "forbid_player_dependents": True,
            "forbid_legendary_items": True,
        },
        "world_facts": ["fact"],
        "narrator_rules": ["rule"],
        "factions": [{"id": "f1", "name": "Faction", "description": "desc", "disposition": "neutral"}],
        "locations": [{"id": "l1", "name": "Location", "type": "settlement", "description": "desc"}],
        "name_locales": [{"locale": "en_US", "weight": 1.0}],
        "inspiration": {"pc": "", "opening_situation": "", "npcs": "", "inventory": "", "quests": ""},
        # Invalid type for name_seed (string instead of int) — will cause validation failure
        "name_seed": "not-an-integer",
    })

    call_count = 0

    async def _bad_then_good(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"response": bad_json, "done": True}
        return {"response": _valid_scenario_json(), "done": True}

    with patch.object(ccya.engine.pack_gen, "llm_chat", new=AsyncMock(side_effect=_bad_then_good)):
        pack = await generate_pack(brief, _config(), packs_dir, template_dir=str(PROMPTS_DIR))

    assert call_count == 2
    assert pack.scenario is not None


async def test_generate_pack_injects_name_seed_when_omitted(tmp_path: Path):
    """If LLM omits name_seed, it should be injected from the generated value."""
    brief = WorldBrief(concept="underwater city")
    packs_dir = tmp_path / "packs"

    no_seed_json = json.dumps({
        "constraints": {
            "min_named_npcs": 2,
            "min_objectives_per_quest": 2,
            "starting_quest_count": 1,
            "inventory_size_range": [3, 7],
            "pc_stat_range": [1, 4],
            "pc_stat_total_range": [8, 14],
            "prose_word_range": [300, 550],
            "required_inventory_kinds": [],
            "npc_distinct_first_letters": True,
            "forbid_cliches": [],
            "forbid_player_dependents": True,
            "forbid_legendary_items": True,
        },
        "world_facts": ["Water pressure kills at depth."],
        "narrator_rules": ["Pressure is always building."],
        "factions": [{"id": "divers", "name": "Divers", "description": "Deep-sea workers.", "disposition": "neutral"}],
        "locations": [{"id": "platform", "name": "Platform", "type": "settlement", "description": "Oil rig turned home."}],
        "name_locales": [{"locale": "en_US", "weight": 1.0}],
        # name_seed intentionally omitted
        "inspiration": {"pc": "", "opening_situation": "", "npcs": "", "inventory": "", "quests": ""},
    })

    captured_name_seed = None

    async def _capture_and_reply(*args, **kwargs):
        nonlocal captured_name_seed
        msgs = kwargs.get("messages") or (args[2] if len(args) > 2 else [])
        for m in msgs:
            if m.get("role") == "user":
                for line in m["content"].splitlines():
                    if "name_seed:" in line:
                        captured_name_seed = int(line.split("name_seed:")[1].strip())
        return {"response": no_seed_json, "done": True}

    with patch.object(ccya.engine.pack_gen, "llm_chat", new=AsyncMock(side_effect=_capture_and_reply)):
        pack = await generate_pack(brief, _config(), packs_dir, template_dir=str(PROMPTS_DIR))

    assert captured_name_seed is not None
    assert 10_000_000 <= captured_name_seed <= 99_999_999
    # Verify the scenario has the injected name_seed
    assert pack.scenario.name_seed == captured_name_seed


def test_slugify_basic():
    assert ccya.engine.pack_gen._slugify("Post-Flood Survival!") == "post-flood-survival"


def test_slugify_preserves_hyphens():
    assert ccya.engine.pack_gen._slugify("space-western world") == "space-western-world"


def test_slugify_truncates_long():
    long_text = "a" * 100
    result = ccya.engine.pack_gen._slugify(long_text)
    assert len(result) <= 40


def test_slugify_empty_returns_default():
    assert ccya.engine.pack_gen._slugify("") == "custom-world"


def test_slugify_special_chars_stripped():
    assert ccya.engine.pack_gen._slugify("Café & Bar!") == "caf-bar"
