"""Tests for ccya.pack — load_pack(), list_packs(), parse_world_facts()."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ccya.pack import (
    PlayerOverrides,
    load_pack,
    list_packs,
    parse_world_facts,
)

PACKS_DIR = Path(__file__).parent.parent / "packs"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _write_pack(tmp_path: Path, pack_id: str, files: dict[str, str], namespace: str = "default") -> Path:
    """Write a pack directory with given filename→content mapping."""
    pack_dir = tmp_path / namespace / pack_id
    pack_dir.mkdir(parents=True)
    for name, content in files.items():
        (pack_dir / name).write_text(content)
    return tmp_path


def _minimal_static_pack_files(
    include_style: bool = False,
) -> dict[str, str]:
    manifest = yaml.dump(
        {
            "id": "test-static",
            "name": "Test Static Pack",
        }
    )
    seed = yaml.dump(
        {
            "meta": {
                "game_name": "default",
                "turn": 0,
                "setting_pack": "test-static",
                "model": "",
            },
            "pc": {
                "name": "Tester",
                "tagline": "a test character",
                "bio": "",
                "stats": {"body": 2, "mind": 2, "tech": 2, "social": 2},
                "conditions": [],
            },
            "location": {
                "id": "test-loc",
                "name": "Test Location",
                "description": "A room.",
            },
            "inventory": [{"id": "item-a", "name": "Item A", "notes": "", "amount": 1}],
            "quests": [
                {
                    "id": "q1",
                    "title": "Test Quest",
                    "status": "active",
                    "objectives": [{"description": "Do a thing", "done": False}],
                }
            ],
            "scene": {
                "tagline": "",
                "tags": [],
                
                "recent_events": [],
            },
            "compendium": {"npcs": {}},
        }
    )
    opening = "You stand in the test room. What do you do?"
    files = {
        "pack.yaml": manifest,
        "seed_state.yaml": seed,
        "opening_scene.md": opening,
    }
    if include_style:
        files["style.md"] = "Stay calm. Test things methodically."
    return files


def _minimal_dynamic_pack_files(include_style: bool = True) -> dict[str, str]:
    manifest = yaml.dump(
        {
            "id": "test-dynamic",
            "name": "Test Dynamic Pack",
        }
    )
    world = (
        "# World\nThis world has rules.\n- Rule one is important.\n- Rule two follows."
    )
    scenario = yaml.dump(
        {
            "constraints": {"min_named_npcs": 2, "starting_quest_count": 1},
            "inspiration": {
                "pc": "A person.",
                "opening_situation": "A moment.",
                "npcs": "Some people.",
                "inventory": "Some things.",
                "quests": "A task.",
            },
        }
    )
    files = {"pack.yaml": manifest, "world.md": world, "scenario.yaml": scenario}
    if include_style:
        files["style.md"] = "Be terse. Be specific."
    return files


# ---------------------------------------------------------------------------
# Static pack loading
# ---------------------------------------------------------------------------


def test_load_static_pack_valid(tmp_path):
    packs_dir = _write_pack(tmp_path, "test-static", _minimal_static_pack_files())
    pack = load_pack("test-static", packs_dir)
    assert pack.seed is not None
    assert pack.seed.pc.name == "Tester"
    assert pack.opening_text.startswith("You stand")
    assert pack.world_text == ""
    assert pack.scenario is None


def test_load_static_pack_with_optional_files(tmp_path):
    files = _minimal_static_pack_files(include_style=True)
    packs_dir = _write_pack(tmp_path, "test-static", files)
    pack = load_pack("test-static", packs_dir)
    assert pack.style_text.startswith("Stay calm")


def test_load_static_pack_optional_files_missing(tmp_path):
    """Pack without style.md still loads with empty defaults."""
    packs_dir = _write_pack(tmp_path, "test-static", _minimal_static_pack_files())
    pack = load_pack("test-static", packs_dir)
    assert pack.style_text == ""


def test_static_pack_missing_seed_fails(tmp_path):
    """Static pack without seed raises ValidationError via Pack._check_playable."""
    files = _minimal_static_pack_files()
    del files["seed_state.yaml"]
    packs_dir = _write_pack(tmp_path, "test-static", files)
    with pytest.raises(Exception, match="seed_state"):
        load_pack("test-static", packs_dir)


def test_static_pack_missing_opening_fails(tmp_path):
    """Static pack without opening_scene.md still loads (opening_text defaults to empty)."""
    files = _minimal_static_pack_files()
    del files["opening_scene.md"]
    packs_dir = _write_pack(tmp_path, "test-static", files)
    pack = load_pack("test-static", packs_dir)
    assert pack.opening_text == ""


# ---------------------------------------------------------------------------
# Dynamic pack loading
# ---------------------------------------------------------------------------


def test_load_dynamic_pack_valid(tmp_path):
    packs_dir = _write_pack(tmp_path, "test-dynamic", _minimal_dynamic_pack_files())
    pack = load_pack("test-dynamic", packs_dir)
    assert pack.world_text.startswith("# World")
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2
    assert pack.seed is None
    assert pack.opening_text == ""


def test_dynamic_pack_missing_world_fails(tmp_path):
    """Dynamic pack without scenario.yaml and without seed_state.yaml raises."""
    files = _minimal_dynamic_pack_files()
    del files["scenario.yaml"]
    del files["world.md"]  # world.md is legacy fallback, not required
    packs_dir = _write_pack(tmp_path, "test-dynamic", files)
    with pytest.raises(Exception, match="seed_state"):
        load_pack("test-dynamic", packs_dir)


def test_dynamic_pack_missing_scenario_fails(tmp_path):
    """Dynamic pack without scenario.yaml and without seed_state.yaml raises."""
    files = _minimal_dynamic_pack_files()
    del files["scenario.yaml"]
    del files["world.md"]  # world.md is legacy fallback, not required
    packs_dir = _write_pack(tmp_path, "test-dynamic", files)
    with pytest.raises(Exception, match="seed_state"):
        load_pack("test-dynamic", packs_dir)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_missing_pack_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_pack("nonexistent", tmp_path)


def test_missing_manifest_raises(tmp_path):
    (tmp_path / "default" / "no-manifest").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="pack.yaml"):
        load_pack("no-manifest", tmp_path)


def test_invalid_manifest_pydantic_error(tmp_path):
    """Missing required 'id' field should raise Pydantic ValidationError."""
    from pydantic import ValidationError

    pack_dir = tmp_path / "default" / "bad-pack"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.yaml").write_text(yaml.dump({"name": "Bad"}))
    with pytest.raises(ValidationError):
        load_pack("bad-pack", tmp_path)


# ---------------------------------------------------------------------------
# list_packs
# ---------------------------------------------------------------------------


def test_list_packs_empty_dir(tmp_path):
    assert list_packs(tmp_path) == []


def test_list_packs_returns_manifests(tmp_path):
    _write_pack(tmp_path, "alpha", _minimal_static_pack_files())
    _write_pack(tmp_path, "beta", _minimal_dynamic_pack_files())
    manifests = list_packs(tmp_path)
    assert len(manifests) == 2


def test_list_packs_skips_invalid(tmp_path):
    """Invalid pack.yaml should be silently skipped."""
    _write_pack(tmp_path, "good", _minimal_static_pack_files())
    bad_dir = tmp_path / "default" / "bad"
    bad_dir.mkdir(parents=True)
    (bad_dir / "pack.yaml").write_text("not: valid: yaml: {{{")
    manifests = list_packs(tmp_path)
    assert len(manifests) == 1


# ---------------------------------------------------------------------------
# parse_world_facts
# ---------------------------------------------------------------------------


def test_parse_world_facts_headings_skipped():
    md = "# Title\n## Subtitle\nA plain fact.\n- A bullet fact.\n"
    facts = parse_world_facts(md)
    assert "# Title" not in " ".join(facts)
    assert "A plain fact." in facts
    assert "A bullet fact." in facts


def test_parse_world_facts_blank_lines_skipped():
    md = "\n\nFirst fact.\n\n\nSecond fact.\n"
    facts = parse_world_facts(md)
    assert facts == ["First fact.", "Second fact."]


def test_parse_world_facts_bullet_variants():
    md = "- dash fact\n* asterisk fact\n+ plus fact\n"
    facts = parse_world_facts(md)
    assert facts == ["dash fact", "asterisk fact", "plus fact"]


def test_parse_world_facts_empty():
    assert parse_world_facts("") == []
    assert parse_world_facts("# Only heading\n") == []


# ---------------------------------------------------------------------------
# baseline_facts
# ---------------------------------------------------------------------------


def test_baseline_facts_default_empty():
    """Manifests without baseline_facts default to []."""
    files = _minimal_static_pack_files()
    # Use tmp_path-style: write into a fresh tmp dir
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        _write_pack(td_path, "test-bf", files)
        from ccya.pack import load_pack as _load_pack

        pack = _load_pack("test-bf", td_path)
        assert pack.manifest.baseline_facts == []


def test_baseline_facts_loaded_from_manifest(tmp_path):
    """baseline_facts in pack.yaml are loaded onto PackManifest."""
    files = _minimal_static_pack_files()
    files["pack.yaml"] = yaml.dump(
        {
            "id": "test-bf-set",
            "name": "Test BF Set",
            "mode": "static",
            "baseline_facts": ["Fact A.", "Fact B.", "Fact C."],
        }
    )
    _write_pack(tmp_path, "test-bf-set", files)
    pack = load_pack("test-bf-set", tmp_path)
    assert pack.manifest.baseline_facts == ["Fact A.", "Fact B.", "Fact C."]


def test_baseline_facts_max_length_enforced(tmp_path):
    """baseline_facts cap at 3 — more raises validation error."""
    from pydantic import ValidationError

    files = _minimal_static_pack_files()
    files["pack.yaml"] = yaml.dump(
        {
            "id": "test-bf-overflow",
            "name": "Test BF Overflow",
            "baseline_facts": ["a", "b", "c", "d", "e", "f"],
        }
    )
    _write_pack(tmp_path, "test-bf-overflow", files)
    with pytest.raises(ValidationError):
        load_pack("test-bf-overflow", tmp_path)


def test_all_shipped_packs_have_baseline_facts():
    """Every shipped pack has exactly 3 hand-curated baseline_facts."""
    for manifest in list_packs(PACKS_DIR):
        pack = load_pack(manifest.id, PACKS_DIR)
        assert len(pack.manifest.baseline_facts) == 3, (
            f"Pack {manifest.id!r} has {len(pack.manifest.baseline_facts)} baseline_facts; expected 3"
        )
        for f in pack.manifest.baseline_facts:
            assert isinstance(f, str) and f.strip(), (
                f"Pack {manifest.id!r} has empty/blank baseline_fact"
            )


# ---------------------------------------------------------------------------
# Real packs load and validate
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not PACKS_DIR.is_dir(), reason="packs/ directory not found")
def test_load_expanse_valid():
    pack = load_pack("expanse", PACKS_DIR)
    assert pack.world_text != ""
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2
    assert pack.style_text != ""


@pytest.mark.skipif(not PACKS_DIR.is_dir(), reason="packs/ directory not found")
def test_load_zombie_survival_valid():
    pack = load_pack("zombie-survival", PACKS_DIR)
    assert pack.world_text != ""
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2


@pytest.mark.skipif(not PACKS_DIR.is_dir(), reason="packs/ directory not found")
def test_list_real_packs():
    manifests = list_packs(PACKS_DIR)
    ids = [m.id for m in manifests]
    assert "expanse" in ids
    assert "zombie-survival" in ids


# ---------------------------------------------------------------------------
# PlayerOverrides.is_empty
# ---------------------------------------------------------------------------


def test_player_overrides_empty():
    assert PlayerOverrides().is_empty()


def test_player_overrides_not_empty():
    assert not PlayerOverrides(pc_hints="mechanic").is_empty()
    assert not PlayerOverrides(free_form="anything").is_empty()


# ---------------------------------------------------------------------------
# _resolve_pack_dir
# ---------------------------------------------------------------------------


def test_resolve_pack_dir_namespace_default(tmp_path):
    """Namespaced slug resolves directly."""
    from ccya.pack import _resolve_pack_dir

    ns_dir = tmp_path / "default" / "ns-pack"
    ns_dir.mkdir(parents=True)
    (ns_dir / "pack.yaml").write_text(yaml.dump({"id": "ns-pack", "name": "NS"}))

    result = _resolve_pack_dir("default/ns-pack", tmp_path)
    assert result == ns_dir


def test_resolve_pack_dir_namespace_custom(tmp_path):
    """Namespaced slug resolves directly for custom namespace."""
    from ccya.pack import _resolve_pack_dir

    ns_dir = tmp_path / "custom" / "my-world"
    ns_dir.mkdir(parents=True)
    (ns_dir / "pack.yaml").write_text(yaml.dump({"id": "my-world", "name": "My World"}))

    result = _resolve_pack_dir("custom/my-world", tmp_path)
    assert result == ns_dir


def test_resolve_pack_dir_bare_slug_finds_default_first(tmp_path):
    """Bare slug finds default/ before custom/."""
    from ccya.pack import _resolve_pack_dir

    default_dir = tmp_path / "default" / "shared-name"
    default_dir.mkdir(parents=True)
    (default_dir / "pack.yaml").write_text(yaml.dump({"id": "shared-name", "name": "Default"}))

    custom_dir = tmp_path / "custom" / "shared-name"
    custom_dir.mkdir(parents=True)
    (custom_dir / "pack.yaml").write_text(yaml.dump({"id": "shared-name", "name": "Custom"}))

    result = _resolve_pack_dir("shared-name", tmp_path)
    assert result == default_dir


def test_resolve_pack_dir_not_found(tmp_path):
    """Nonexistent pack raises FileNotFoundError."""
    from ccya.pack import _resolve_pack_dir

    with pytest.raises(FileNotFoundError, match="not found"):
        _resolve_pack_dir("nonexistent", tmp_path)


# ---------------------------------------------------------------------------
# list_packs with namespace routing
# ---------------------------------------------------------------------------


def test_list_packs_aggregates_namespaces(tmp_path):
    """list_packs aggregates from default/ and custom/."""
    default_dir = tmp_path / "default" / "alpha"
    default_dir.mkdir(parents=True)
    (default_dir / "pack.yaml").write_text(yaml.dump({"id": "alpha", "name": "Alpha"}))

    custom_dir = tmp_path / "custom" / "beta"
    custom_dir.mkdir(parents=True)
    (custom_dir / "pack.yaml").write_text(yaml.dump({"id": "beta", "name": "Beta"}))

    manifests = list_packs(tmp_path)
    ids = [m.id for m in manifests]
    assert "alpha" in ids
    assert "beta" in ids


def test_list_packs_no_duplicates(tmp_path):
    """Same pack in default/ and custom/ should not duplicate."""
    default_dir = tmp_path / "default" / "dup"
    default_dir.mkdir(parents=True)
    (default_dir / "pack.yaml").write_text(yaml.dump({"id": "dup", "name": "Dup"}))

    custom_dir = tmp_path / "custom" / "dup"
    custom_dir.mkdir(parents=True)
    (custom_dir / "pack.yaml").write_text(yaml.dump({"id": "dup", "name": "Dup Custom"}))

    manifests = list_packs(tmp_path)
    ids = [m.id for m in manifests]
    assert ids.count("dup") == 1


# ---------------------------------------------------------------------------
# New Phase 2 models: Faction, NamedLocation, WorldBrief, ScenarioBrief expansion
# ---------------------------------------------------------------------------


def test_faction_defaults():
    from ccya.pack import Faction

    f = Faction(id="test", name="Test", description="A test faction")
    assert f.disposition == "neutral"
    assert f.id == "test"


def test_named_location_defaults():
    from ccya.pack import NamedLocation

    loc = NamedLocation(id="test", name="Test", type="settlement", description="A test place")
    assert loc.type == "settlement"
    assert loc.id == "test"


def test_world_brief_defaults():
    from ccya.pack import WorldBrief

    wb = WorldBrief(concept="post-flood survival")
    assert wb.concept == "post-flood survival"
    assert wb.tone == ""
    assert wb.geography == ""
    assert wb.power == ""
    assert wb.daily_life == ""
    assert wb.player_hint == ""


def test_generated_pack_meta_defaults():
    from ccya.pack import GeneratedPackMeta

    meta = GeneratedPackMeta()
    assert meta.generated is True
    assert meta.world_brief_concept == ""


def test_scenario_brief_expansion_fields():
    from ccya.pack import Faction, NamedLocation, ScenarioBrief

    scenario = ScenarioBrief(
        world_facts=["Fact 1.", "Fact 2."],
        narrator_rules=["Rule 1.", "Rule 2.", "Rule 3."],
        factions=[Faction(id="f1", name="Faction 1", description="Desc 1")],
        locations=[NamedLocation(id="l1", name="Location 1", type="settlement", description="Desc 1")],
        name_locales=[{"locale": "en_US", "weight": 1.0}],
        name_seed=42,
    )
    assert len(scenario.world_facts) == 2
    assert len(scenario.narrator_rules) == 3
    assert len(scenario.factions) == 1
    assert scenario.factions[0].name == "Faction 1"
    assert len(scenario.locations) == 1
    assert scenario.locations[0].type == "settlement"
    assert scenario.name_seed == 42


def test_scenario_brief_max_length_constraints():
    from ccya.pack import ScenarioBrief
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScenarioBrief(world_facts=["a"] * 9)

    with pytest.raises(ValidationError):
        ScenarioBrief(narrator_rules=["a"] * 13)

    with pytest.raises(ValidationError):
        ScenarioBrief(factions=[{"id": f"f{i}", "name": f"F{i}", "description": "d"} for i in range(7)])

    with pytest.raises(ValidationError):
        ScenarioBrief(locations=[{"id": f"l{i}", "name": f"L{i}", "type": "x", "description": "d"} for i in range(11)])


def test_scenario_brief_roundtrip_flooded_world():
    import yaml
    from ccya.pack import ScenarioBrief

    with open(PACKS_DIR / "default" / "flooded-world" / "scenario.yaml") as f:
        data = yaml.safe_load(f)
    scenario = ScenarioBrief(**data)
    assert len(scenario.world_facts) == 5
    assert len(scenario.narrator_rules) == 8
    assert len(scenario.factions) == 4
    assert len(scenario.locations) == 4
    assert len(scenario.name_locales) == 4
    assert scenario.name_seed == 0
    assert scenario.factions[0].name == "Cartographers' Compact"
    assert scenario.locations[0].type == "settlement"


def test_pack_with_only_scenario_validates():
    from ccya.pack import Pack, PackManifest, ScenarioBrief

    pack = Pack(
        manifest=PackManifest(id="test", name="Test"),
        scenario=ScenarioBrief(),
    )
    assert pack.mode == "dynamic"


def test_pack_with_only_seed_validates():
    from ccya.pack import Pack, PackManifest, SeedState, SeedPC, SeedLocation, SeedScene, SeedQuest

    pack = Pack(
        manifest=PackManifest(id="test", name="Test"),
        seed=SeedState(
            meta={"turn": 0},
            pc=SeedPC(name="Tester"),
            location=SeedLocation(id="loc", name="Loc"),
            inventory=[{"id": "item", "name": "Item", "notes": "", "amount": 1}],
            quests=[SeedQuest(id="q1", title="Quest", objectives=[])],
            scene=SeedScene(),
        ),
    )
    assert pack.mode == "static"


def test_pack_with_neither_raises():
    from ccya.pack import Pack, PackManifest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="seed_state"):
        Pack(manifest=PackManifest(id="test", name="Test"))


def test_old_scenario_yaml_still_loads():
    """Old-format scenario.yaml (only constraints + inspiration) still validates."""
    from ccya.pack import ScenarioBrief

    old_data = {
        "constraints": {"min_named_npcs": 2, "starting_quest_count": 1},
        "inspiration": {
            "pc": "A person.",
            "opening_situation": "A moment.",
            "npcs": "Some people.",
            "inventory": "Some things.",
            "quests": "A task.",
        },
    }
    scenario = ScenarioBrief(**old_data)
    assert scenario.world_facts == []
    assert scenario.factions == []
    assert scenario.locations == []
    assert scenario.name_seed == 0
