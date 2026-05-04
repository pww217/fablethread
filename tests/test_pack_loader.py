"""Tests for ccya.pack — load_pack(), list_packs(), parse_world_facts()."""

from __future__ import annotations

import json
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


def _write_pack(tmp_path: Path, pack_id: str, files: dict[str, str]) -> Path:
    """Write a pack directory with given filename→content mapping."""
    pack_dir = tmp_path / pack_id
    pack_dir.mkdir()
    for name, content in files.items():
        (pack_dir / name).write_text(content)
    return tmp_path


def _minimal_static_pack_files(
    mode: str = "static",
    include_style: bool = False,
    include_examples: bool = False,
) -> dict[str, str]:
    manifest = yaml.dump(
        {
            "id": "test-static",
            "name": "Test Static Pack",
            "mode": mode,
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
                "present_npcs": [],
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
    if include_examples:
        files["extract_examples.yaml"] = yaml.dump(
            {
                "examples": [
                    {
                        "title": "Test example",
                        "thinking": "- nothing",
                        "json": json.dumps({"state_delta": {"scene_tags": ["test"]}}),
                    }
                ]
            }
        )
    return files


def _minimal_dynamic_pack_files(include_style: bool = True) -> dict[str, str]:
    manifest = yaml.dump(
        {
            "id": "test-dynamic",
            "name": "Test Dynamic Pack",
            "mode": "dynamic",
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
    assert pack.manifest.mode == "static"
    assert pack.seed is not None
    assert pack.seed.pc.name == "Tester"
    assert pack.opening_text.startswith("You stand")
    assert pack.world_text == ""
    assert pack.scenario is None


def test_load_static_pack_with_optional_files(tmp_path):
    files = _minimal_static_pack_files(include_style=True, include_examples=True)
    packs_dir = _write_pack(tmp_path, "test-static", files)
    pack = load_pack("test-static", packs_dir)
    assert pack.style_text.startswith("Stay calm")
    assert len(pack.extract_examples) == 1
    assert pack.extract_examples[0].title == "Test example"


def test_load_static_pack_optional_files_missing(tmp_path):
    """Pack without style.md or extract_examples.yaml still loads with empty defaults."""
    packs_dir = _write_pack(tmp_path, "test-static", _minimal_static_pack_files())
    pack = load_pack("test-static", packs_dir)
    assert pack.style_text == ""
    assert pack.extract_examples == []


def test_static_pack_missing_seed_fails(tmp_path):
    """Static pack without seed raises ValidationError via Pack._check_mode_files."""
    files = _minimal_static_pack_files()
    del files["seed_state.yaml"]
    packs_dir = _write_pack(tmp_path, "test-static", files)
    with pytest.raises(Exception, match="seed"):
        load_pack("test-static", packs_dir)


def test_static_pack_missing_opening_fails(tmp_path):
    """Static pack without opening_scene.md raises ValidationError."""
    files = _minimal_static_pack_files()
    del files["opening_scene.md"]
    packs_dir = _write_pack(tmp_path, "test-static", files)
    with pytest.raises(Exception, match="opening"):
        load_pack("test-static", packs_dir)


# ---------------------------------------------------------------------------
# Dynamic pack loading
# ---------------------------------------------------------------------------


def test_load_dynamic_pack_valid(tmp_path):
    packs_dir = _write_pack(tmp_path, "test-dynamic", _minimal_dynamic_pack_files())
    pack = load_pack("test-dynamic", packs_dir)
    assert pack.manifest.mode == "dynamic"
    assert pack.world_text.startswith("# World")
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2
    assert pack.seed is None
    assert pack.opening_text == ""


def test_dynamic_pack_missing_world_fails(tmp_path):
    files = _minimal_dynamic_pack_files()
    del files["world.md"]
    packs_dir = _write_pack(tmp_path, "test-dynamic", files)
    with pytest.raises(Exception, match="world"):
        load_pack("test-dynamic", packs_dir)


def test_dynamic_pack_missing_scenario_fails(tmp_path):
    files = _minimal_dynamic_pack_files()
    del files["scenario.yaml"]
    packs_dir = _write_pack(tmp_path, "test-dynamic", files)
    with pytest.raises(Exception, match="scenario"):
        load_pack("test-dynamic", packs_dir)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_missing_pack_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Pack directory"):
        load_pack("nonexistent", tmp_path)


def test_missing_manifest_raises(tmp_path):
    (tmp_path / "no-manifest").mkdir()
    with pytest.raises(FileNotFoundError, match="pack.yaml"):
        load_pack("no-manifest", tmp_path)


def test_invalid_manifest_pydantic_error(tmp_path):
    """Missing required 'mode' field should raise Pydantic ValidationError."""
    from pydantic import ValidationError

    pack_dir = tmp_path / "bad-pack"
    pack_dir.mkdir()
    (pack_dir / "pack.yaml").write_text(yaml.dump({"id": "bad-pack", "name": "Bad"}))
    with pytest.raises(ValidationError):
        load_pack("bad-pack", tmp_path)


def test_extract_example_invalid_json_raises(tmp_path):
    files = _minimal_static_pack_files(include_examples=False)
    files["extract_examples.yaml"] = yaml.dump(
        {"examples": [{"title": "Bad example", "json": "not valid json {{"}]}
    )
    packs_dir = _write_pack(tmp_path, "test-static", files)
    with pytest.raises(Exception, match="[Jj][Ss][Oo][Nn]"):
        load_pack("test-static", packs_dir)


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
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
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
    """baseline_facts cap at 5 — more raises validation error."""
    from pydantic import ValidationError

    files = _minimal_static_pack_files()
    files["pack.yaml"] = yaml.dump(
        {
            "id": "test-bf-overflow",
            "name": "Test BF Overflow",
            "mode": "static",
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
    assert pack.manifest.mode == "dynamic"
    assert pack.world_text != ""
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2
    assert len(pack.extract_examples) == 5
    assert pack.style_text != ""


@pytest.mark.skipif(not PACKS_DIR.is_dir(), reason="packs/ directory not found")
def test_load_zombie_survival_valid():
    pack = load_pack("zombie-survival", PACKS_DIR)
    assert pack.manifest.mode == "dynamic"
    assert pack.world_text != ""
    assert pack.scenario is not None
    assert pack.scenario.constraints.min_named_npcs == 2
    assert len(pack.extract_examples) == 3


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
