"""Tests for character creation: _validate_stats, form field reading, and
new-game override wiring.

Covers:
- _validate_stats pure-Python validation
- POST /new-game with static pack + PC overrides
- POST /new-game with dynamic pack + PlayerOverrides injection
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_STATS = {
    "strength": 2,
    "dexterity": 2,
    "wits": 2,
    "lore": 2,
    "charisma": 2,
    "resolve": 2,
}

VALID_STATS_HIGH = {
    "strength": 4,
    "dexterity": 3,
    "wits": 2,
    "lore": 1,
    "charisma": 1,
    "resolve": 1,
}


# ---------------------------------------------------------------------------
# _validate_stats — pure Python
# ---------------------------------------------------------------------------


class TestValidateStats:
    """Pure-Python validation of stat dicts."""

    def _import(self):
        from ccya.server import _validate_stats

        return _validate_stats

    def test_valid_minimal(self):
        assert self._import()(VALID_STATS) is True

    def test_valid_high_total(self):
        assert self._import()(VALID_STATS_HIGH) is True

    def test_valid_total_16(self):
        stats = {
            "strength": 4,
            "dexterity": 3,
            "wits": 3,
            "lore": 2,
            "charisma": 2,
            "resolve": 2,
        }
        # total = 16 — at max
        assert self._import()(stats) is True

    def test_invalid_total_below_12(self):
        stats = {k: 1 for k in VALID_STATS}
        # total = 6 < 12
        assert self._import()(stats) is False

    def test_invalid_total_above_16(self):
        stats = {
            "strength": 4,
            "dexterity": 4,
            "wits": 3,
            "lore": 2,
            "charisma": 2,
            "resolve": 2,
        }
        # total = 17 > 16
        assert self._import()(stats) is False

    def test_invalid_stat_zero(self):
        stats = dict(VALID_STATS)
        stats["strength"] = 0
        assert self._import()(stats) is False

    def test_invalid_stat_above_4(self):
        stats = dict(VALID_STATS)
        stats["strength"] = 5
        assert self._import()(stats) is False

    def test_wrong_keys_extra(self):
        stats = dict(VALID_STATS)
        stats["hp"] = 10
        assert self._import()(stats) is False

    def test_wrong_keys_missing(self):
        stats = {k: v for k, v in VALID_STATS.items() if k != "strength"}
        assert self._import()(stats) is False

    def test_non_int_value(self):
        stats = dict(VALID_STATS)
        stats["strength"] = 2.5
        assert self._import()(stats) is False


# ---------------------------------------------------------------------------
# POST /new-game — static pack with PC overrides
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """Import server module under MOCK_MODE so /healthz doesn't call Ollama."""
    import os

    old = os.environ.get("MOCK_MODE")
    os.environ["MOCK_MODE"] = "1"
    # Force reimport so config loads fresh
    import importlib
    import ccya.server

    importlib.reload(ccya.server)
    from ccya.server import app

    yield TestClient(app)
    if old is None:
        os.environ.pop("MOCK_MODE", None)
    else:
        os.environ["MOCK_MODE"] = old
    importlib.reload(ccya.server)


class TestNewGameStaticOverrides:
    """Static pack: PC name/tagline/stats overwrite the seed before init_save_dir."""

    def _make_seed_state(self):
        """Minimal SeedState dict for a static pack."""
        return {
            "meta": {"game_name": "test", "compendium_touch_order": []},
            "pc": {
                "name": "DefaultPC",
                "tagline": "default role",
                "bio": "",
                "stats": {
                    "strength": 2,
                    "dexterity": 2,
                    "wits": 2,
                    "lore": 2,
                    "charisma": 2,
                    "resolve": 2,
                },
                "conditions": [],
            },
            "location": {
                "id": "test-loc",
                "name": "Test Location",
                "description": "A test place.",
            },
            "inventory": [{"id": "item1", "name": "Item One", "notes": ""}],
            "scene": {
                "tags": [],
                
                "recent_events": [],
                "tagline": "",
            },
            "compendium": {"npcs": {}},
        }

    def _mock_static_pack(self, seed_state):
        """Build a mock Pack with mode='static' and a SeedState."""
        from ccya.pack import Pack, PackManifest, SeedState

        manifest = PackManifest(
            id="test-static",
            name="Test Static",
            mode="static",
            description="A test static pack",
            tone_tags=[],
            baseline_facts=[],
            constraints=None,
        )
        seed = SeedState.model_validate(seed_state)
        pack = Pack.model_construct(
            manifest=manifest, seed=seed, opening_text="You start here."
        )
        return pack

    @pytest.mark.parametrize("mock_mode", ["static", "dynamic"])
    def test_validate_stats_helper_exists(self, mock_mode):
        """_validate_stats is importable and callable."""
        from ccya.server import _validate_stats

        assert callable(_validate_stats)
        assert _validate_stats(VALID_STATS) is True
        assert _validate_stats({"a": 1}) is False

    def test_static_pack_pc_overrides_applied(self, client):
        """POST /new-game with pc_name, pc_tagline, pc_stats patches the seed."""
        seed_state = self._make_seed_state()
        mock_pack = self._mock_static_pack(seed_state)

        save_dir = Path(tempfile.mkdtemp())

        with (
            patch.object(
                __import__("ccya.server.app", fromlist=["_active_pack"]),
                "_active_pack",
                mock_pack,
            ),
            patch("ccya.server.app.SAVE_DIR", save_dir),
            patch("ccya.server.routes.init_save_dir") as mock_init,
        ):
            resp = client.post(
                "/new-game",
                data={
                    "pack_id": "test-static",
                    "pc_name": "Wraith",
                    "pc_tagline": "shadow runner",
                    "pc_stats": json.dumps(VALID_STATS_HIGH),
                },
            )

            assert resp.status_code == 200
            mock_init.assert_called_once()
            seed_arg = mock_init.call_args[0][1]  # second positional arg
            assert seed_arg["pc"]["name"] == "Wraith"
            assert seed_arg["pc"]["tagline"] == "shadow runner"
            assert seed_arg["pc"]["stats"] == VALID_STATS_HIGH

    def test_static_pack_invalid_stats_ignored(self, client):
        """Malformed pc_stats JSON should not crash; original seed preserved."""
        seed_state = self._make_seed_state()
        mock_pack = self._mock_static_pack(seed_state)
        save_dir = Path(tempfile.mkdtemp())

        with (
            patch.object(
                __import__("ccya.server.app", fromlist=["_active_pack"]),
                "_active_pack",
                mock_pack,
            ),
            patch("ccya.server.app.SAVE_DIR", save_dir),
            patch("ccya.server.routes.init_save_dir") as mock_init,
        ):
            resp = client.post(
                "/new-game",
                data={
                    "pack_id": "test-static",
                    "pc_name": "Wraith",
                    "pc_stats": "NOT VALID JSON",
                },
            )

            assert resp.status_code == 200
            mock_init.assert_called_once()
            seed_arg = mock_init.call_args[0][1]
            # Name should still be overridden (only stats are invalid)
            assert seed_arg["pc"]["name"] == "Wraith"
            # Stats should be the original seed values, not the invalid input
            assert seed_arg["pc"]["stats"] == seed_state["pc"]["stats"]

    def test_static_pack_no_overrides_unchanged(self, client):
        """Without override fields, the seed passes through unchanged."""
        seed_state = self._make_seed_state()
        mock_pack = self._mock_static_pack(seed_state)
        save_dir = Path(tempfile.mkdtemp())

        with (
            patch.object(
                __import__("ccya.server.app", fromlist=["_active_pack"]),
                "_active_pack",
                mock_pack,
            ),
            patch("ccya.server.app.SAVE_DIR", save_dir),
            patch("ccya.server.routes.init_save_dir") as mock_init,
        ):
            resp = client.post("/new-game", data={"pack_id": "test-static"})

            assert resp.status_code == 200
            mock_init.assert_called_once()
            seed_arg = mock_init.call_args[0][1]
            assert seed_arg["pc"]["name"] == "DefaultPC"
            assert seed_arg["pc"]["stats"] == seed_state["pc"]["stats"]


# ---------------------------------------------------------------------------
# POST /new-game — dynamic pack with PlayerOverrides
# ---------------------------------------------------------------------------


class TestNewGameDynamicOverrides:
    """Dynamic pack: PlayerOverrides injected into generate_seed()."""

    def _mock_dynamic_pack(self):
        from ccya.pack import Pack, PackManifest

        manifest = PackManifest(
            id="test-dynamic",
            name="Test Dynamic",
            mode="dynamic",
            description="A test dynamic pack",
            tone_tags=[],
            baseline_facts=[],
            constraints=None,
        )
        return Pack.model_construct(manifest=manifest, world_text="A test world.")

    def test_dynamic_pack_passes_overrides_to_generate_seed(self, client):
        """POST /new-game with pc_name on a dynamic pack passes overrides."""
        mock_pack = self._mock_dynamic_pack()
        save_dir = Path(tempfile.mkdtemp())

        mock_envelope = MagicMock()
        mock_envelope.seed_state.model_dump.return_value = {
            "meta": {"game_name": "test"},
            "pc": {
                "name": "LLMPC",
                "tagline": "",
                "bio": "",
                "stats": {
                    "strength": 2,
                    "dexterity": 2,
                    "wits": 2,
                    "lore": 2,
                    "charisma": 2,
                    "resolve": 2,
                },
                "conditions": [],
            },
            "location": {
                "id": "llm-loc",
                "name": "LLM Location",
                "description": "Generated.",
            },
            "inventory": [{"id": "sword", "name": "Sword", "notes": ""}],
            "scene": {
                "tags": [],
                
                "recent_events": [],
                "tagline": "",
            },
            "compendium": {"npcs": {}},
        }
        mock_envelope.opening_narrative = "You awaken in a dark room."
        mock_envelope.actions = ["Explore", "Rest", "Call for help", "Check inventory"]

        captured_overrides = []

        async def mock_generate_seed(pack, config, **kwargs):
            captured_overrides.append(kwargs.get("overrides"))
            return mock_envelope

        with (
            patch.object(
                __import__("ccya.server.app", fromlist=["_active_pack"]),
                "_active_pack",
                mock_pack,
            ),
            patch("ccya.server.app.SAVE_DIR", save_dir),
            patch("ccya.server.routes.generate_seed", mock_generate_seed),
        ):
            resp = client.post(
                "/new-game",
                data={
                    "pack_id": "test-dynamic",
                    "pc_name": "Wraith",
                    "pc_tagline": "shadow runner",
                    "pc_hints": "stealthy character",
                    "free_form": "no dragons",
                },
            )

            assert resp.status_code == 200
            assert len(captured_overrides) == 1
            overrides = captured_overrides[0]
            assert overrides is not None
            assert "Wraith" in overrides.pc_hints
            assert "shadow runner" in overrides.pc_hints
            assert "stealthy character" in overrides.pc_hints
            assert "no dragons" in overrides.free_form

    def test_dynamic_pack_no_overrides_when_empty(self, client):
        """Without override fields, generate_seed receives overrides=None."""
        mock_pack = self._mock_dynamic_pack()
        save_dir = Path(tempfile.mkdtemp())

        mock_envelope = MagicMock()
        mock_envelope.seed_state.model_dump.return_value = {
            "meta": {"game_name": "test"},
            "pc": {
                "name": "LLMPC",
                "tagline": "",
                "bio": "",
                "stats": {
                    "strength": 2,
                    "dexterity": 2,
                    "wits": 2,
                    "lore": 2,
                    "charisma": 2,
                    "resolve": 2,
                },
                "conditions": [],
            },
            "location": {
                "id": "llm-loc",
                "name": "LLM Location",
                "description": "Generated.",
            },
            "inventory": [{"id": "sword", "name": "Sword", "notes": ""}],
            "scene": {
                "tags": [],
                
                "recent_events": [],
                "tagline": "",
            },
            "compendium": {"npcs": {}},
        }
        mock_envelope.opening_narrative = "You awaken in a dark room."
        mock_envelope.actions = ["Explore", "Rest", "Call for help", "Check inventory"]

        captured_overrides = []

        async def mock_generate_seed(pack, config, **kwargs):
            captured_overrides.append(kwargs.get("overrides"))
            return mock_envelope

        with (
            patch.object(
                __import__("ccya.server.app", fromlist=["_active_pack"]),
                "_active_pack",
                mock_pack,
            ),
            patch("ccya.server.app.SAVE_DIR", save_dir),
            patch("ccya.server.routes.generate_seed", mock_generate_seed),
        ):
            resp = client.post("/new-game", data={"pack_id": "test-dynamic"})

            assert resp.status_code == 200
            assert len(captured_overrides) == 1
            assert captured_overrides[0] is None


class TestArcActiveThreadState:
    """Active threads from seed should have state=active, not latent."""

    async def test_arc_active_threads_start_active(self):
        """Active threads from seed should have state=active after generate_seed."""
        import json
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        import ccya.engine.seed
        from ccya.engine import EngineConfig
        from ccya.pack import (
            Constraints,
            Inspiration,
            Pack,
            PackManifest,
            ScenarioBrief,
        )

        PROMPTS_DIR = Path(__file__).parent.parent / "ccya" / "prompts"

        constraints = Constraints(
            min_named_npcs=2,
            inventory_size_range=(4, 8),
            prose_word_range=(50, 1000),
            forbid_cliches=[],
        )
        inspiration = Inspiration(
            pc="A person.",
            opening_situation="A situation.",
            npcs="Some people.",
            inventory="Some items.",
        )
        pack = Pack(
            manifest=PackManifest(id="test-dynamic", name="Test Dynamic"),
            world_text="The world is dangerous.",
            scenario=ScenarioBrief(constraints=constraints, inspiration=inspiration),
        )

        # Build envelope JSON with arc.active_threads having state=latent (the bug)
        envelope_raw = {
            "seed_state": {
                "meta": {"game_name": "test", "turn": 0, "setting_pack": "test-dynamic", "model": ""},
                "pc": {
                    "name": "Tester Player",
                    "tagline": "quiet and careful",
                    "bio": "A history.",
                    "stats": {"strength": 2, "dexterity": 2, "wits": 2, "lore": 2, "charisma": 2, "resolve": 2},
                    "conditions": [],
                },
                "location": {"id": "test-loc", "name": "Test Location", "description": "A ruined building."},
                "inventory": [{"id": "knife", "name": "Knife", "notes": "Sharp.", "amount": 1}],
                "scene": {"tagline": "Ruins at dusk", "tags": ["arrival"], "recent_events": []},
                "compendium": {"npcs": {}},
            },
            "arc": {
                "visible_goal": "Survive",
                "thematic_question": "Can we survive?",
                "active_threads": [
                    {"id": "t1", "summary": "Thread 1", "tags": ["political"], "state": "latent"},
                ],
                "latent_threads": [],
                "completed_threads": [],
                "arc_engagement": 0,
            },
            "pc_drive": "Survive",
            "opening_narrative": "You stand in a ruined building. The wind howls through broken windows. Dust coats your throat. You check your pockets for anything useful. A faded photograph catches the light. Somewhere in the distance, a dog barks.",
            "actions": ["Search the building.", "Call out for survivors.", "Hide and wait.", "Move toward the shelter."],
        }

        config = EngineConfig(
            host="http://localhost:8080/v1",
            model="test-model",
            generate_seed_temperature=0.9,
            generate_seed_max_retries=1,
        )

        with patch.object(
            ccya.engine.seed,
            "llm_chat",
            new=AsyncMock(return_value={"response": json.dumps(envelope_raw), "done": True}),
        ):
            envelope = await ccya.engine.seed.generate_seed(pack, config, template_dir=str(PROMPTS_DIR))

        # Verify that active_threads have state=active after generate_seed
        arc = envelope.seed_state.arc
        assert arc is not None
        for t in arc.active_threads:
            assert t.state.value == "active", f"Expected active, got {t.state.value} for thread {t.id}"
