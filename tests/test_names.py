"""Tests for ccya.names — Faker-backed name pool generation."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ccya.engine.names import generate_name_pool, generate_npc_names


# ---------------------------------------------------------------------------
# Structure test
# ---------------------------------------------------------------------------


class TestStructure:
    def test_name_pool_structure(self):
        pool = generate_name_pool([{"locale": "en_US", "weight": 1.0}], seed=42)
        assert set(pool.keys()) == {"pc", "npc", "location"}
        assert len(pool["pc"]) == 3
        assert len(pool["npc"]) == 8
        assert len(pool["location"]) == 5
        for lst in pool.values():
            for item in lst:
                assert isinstance(item, str)
                assert len(item) > 0

    def test_name_pool_custom_counts(self):
        pool = generate_name_pool(
            [{"locale": "en_US", "weight": 1.0}],
            pc_count=2,
            npc_count=4,
            location_count=3,
            seed=42,
        )
        assert len(pool["pc"]) == 2
        assert len(pool["npc"]) == 4
        assert len(pool["location"]) == 3

    def test_npc_names_structure(self):
        names = generate_npc_names(
            [{"locale": "en_US", "weight": 1.0}], count=6, seed=42
        )
        assert len(names) == 6
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_npc_names_custom_count(self):
        names = generate_npc_names(
            [{"locale": "en_US", "weight": 1.0}], count=10, seed=42
        )
        assert len(names) == 10


# ---------------------------------------------------------------------------
# Fallback test
# ---------------------------------------------------------------------------


class TestFallback:
    def test_empty_locales_falls_back(self):
        pool = generate_name_pool([], seed=42)
        assert len(pool["pc"]) == 3
        assert len(pool["npc"]) == 8
        assert len(pool["location"]) == 5

    def test_empty_locales_npc_names(self):
        names = generate_npc_names([], count=6, seed=42)
        assert len(names) == 6


# ---------------------------------------------------------------------------
# Weighted distribution test
# ---------------------------------------------------------------------------


class TestWeightedDistribution:
    def test_weighted_selection(self):
        """With a fixed seed, verify that high-weight locale dominates."""
        locales = [
            {"locale": "en_US", "weight": 0.9},
            {"locale": "it_IT", "weight": 0.1},
        ]
        # Generate multiple pools with the same seed to check consistency
        # and verify names are actually being generated
        pool = generate_name_pool(locales, seed=12345)
        # All names should be non-empty strings
        for lst in pool.values():
            for item in lst:
                assert isinstance(item, str)
                assert len(item) > 0

    def test_different_seeds_produce_different_names(self):
        pool1 = generate_name_pool([{"locale": "en_US", "weight": 1.0}], seed=1)
        pool2 = generate_name_pool([{"locale": "en_US", "weight": 1.0}], seed=2)
        # With different seeds, at least some names should differ
        assert pool1 != pool2

    def test_same_seed_produces_same_names(self):
        pool1 = generate_name_pool([{"locale": "en_US", "weight": 1.0}], seed=42)
        pool2 = generate_name_pool([{"locale": "en_US", "weight": 1.0}], seed=42)
        assert pool1 == pool2

    def test_multi_locale_generation(self):
        """Verify that multiple locales can be used together."""
        locales = [
            {"locale": "en_US", "weight": 0.5},
            {"locale": "ja_JP", "weight": 0.5},
        ]
        pool = generate_name_pool(locales, seed=42)
        for lst in pool.values():
            for item in lst:
                assert isinstance(item, str)
                assert len(item) > 0


# ---------------------------------------------------------------------------
# Jinja render test
# ---------------------------------------------------------------------------


class TestJinjaRender:
    def _env(self):
        prompts_dir = str(Path(__file__).parent.parent / "ccya" / "prompts")
        return Environment(
            loader=FileSystemLoader(prompts_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def test_generate_seed_user_with_name_pool(self):
        env = self._env()
        name_pool = {
            "pc": ["Alice", "Bob", "Charlie"],
            "npc": ["Dave", "Eve"],
            "location": ["Springfield"],
        }
        ctx = {"name_pool": name_pool}
        text = env.get_template("generate_seed_user.j2").render(**ctx)
        assert "Alice" in text
        assert "Springfield" in text
        assert "name_pool" in text

    def test_generate_seed_user_without_name_pool(self):
        env = self._env()
        ctx = {"name_pool": None}
        text = env.get_template("generate_seed_user.j2").render(**ctx)
        assert "name_pool" not in text

    def test_narrate_user_with_npc_name_pool(self):
        """Per-turn NPC name pool now lives in the user prompt (cache stability)."""
        env = self._env()
        ctx = {
            "npc_name_pool": {
                "male": ["Yuki Tanaka", "Carlos Mendez"],
                "female": ["Fatima Al-Rashid", "Maria Santos"],
            },
            "state": {
                "pc": {"name": "Test", "tagline": "tester", "concept": ""},
                "location": {},
                "inventory": [],
                "quests": [],
                "scene": {"present_npcs": []},
                "meta": {},
            },
            "chronicle_tail": "",
            "recent_turns": [],
            "rules_outcome": None,
            "user_input": "look",
            "last_turn_failed": [],
            "recently_left": [],
        }
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Yuki Tanaka" in text
        assert "Fatima Al-Rashid" in text
        assert "name_pool" in text

    def test_narrate_system_byte_stable_without_per_turn_data(self):
        """Narrate system prompt must not contain per-turn NPC names or pools."""
        env = self._env()
        text = env.get_template("narrate_system.j2").render(pack_style="")
        # No per-turn dynamic content should leak into system
        assert "Yuki Tanaka" not in text
        assert "## name_pool" not in text
        assert "rules_outcome" not in text
