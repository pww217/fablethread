"""Dice band boundaries integration test.

Tests that dice rolls map to the correct bands via the rules extraction pipeline.
Patches ccya.rules.roll_2d6 to return fixed values for each band boundary.
"""

import json

from ccya.state import save_state

from tests.integration.conftest import (
    _run,
    base_state,
)


def _rules_response_with_check(
    skill: str = "strength",
    difficulty: str = "normal",
    dice: list[int] | None = None,
) -> str:
    """Build a rules response that triggers a dice check."""
    return json.dumps({
        "intent": "attack",
        "intent_verb": "attack",
        "target": "enemy",
        "stakes": "injure the enemy",
        "check": {
            "required": True,
            "skill": skill,
            "difficulty": difficulty,
        },
    })


class TestDiceBandBoundaries:
    """Test that dice rolls map to the correct bands for all boundary values."""

    async def test_band_crit_fail(self, save_dir, config):
        """roll_2d6=2 -> crit_fail (minimum possible roll)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (1, 1)
        try:
            rules_resp = _rules_response_with_check(skill="strength", dice=[1, 1])
            fake = _FakeLLM(narrative="Vex attacks.", rules_response=rules_resp)
            with fake:
                result = await _run(save_dir, "attack with strength", config)
            assert result.turn == 1
            if result.rules:
                assert result.rules.get("band") == "crit_fail"
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_band_fail(self, save_dir, config):
        """roll_2d6=3 -> fail (just above crit_fail threshold)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (1, 2)
        try:
            fake = _FakeLLM(narrative="Vex strikes but misses.")
            with fake:
                result = await _run(save_dir, "strike at the enemy", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_band_setback(self, save_dir, config):
        """roll_2d6=7 -> setback (middle of the bell curve)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (3, 4)
        try:
            fake = _FakeLLM(narrative="Vex hits but the enemy absorbs the blow.")
            with fake:
                result = await _run(save_dir, "hit the enemy", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_band_partial(self, save_dir, config):
        """roll_2d6=8 -> partial (success with cost)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (3, 5)
        try:
            fake = _FakeLLM(narrative="Vex lands a solid blow.")
            with fake:
                result = await _run(save_dir, "land a blow", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_band_success(self, save_dir, config):
        """roll_2d6=10 -> success (clean success)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (5, 5)
        try:
            fake = _FakeLLM(narrative="Vex strikes decisively.")
            with fake:
                result = await _run(save_dir, "strike decisively", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_band_crit_success(self, save_dir, config):
        """roll_2d6=12 -> crit_success (maximum possible roll)."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (6, 6)
        try:
            fake = _FakeLLM(narrative="Vex delivers a devastating blow.")
            with fake:
                result = await _run(save_dir, "deliver a devastating blow", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll


class TestDifficultyModifiers:
    """Test that difficulty modifiers affect the band outcome."""

    async def test_hard_difficulty_reduces_total(self, save_dir, config):
        """Hard difficulty applies -1 modifier to the roll total."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (6, 6)
        try:
            rules_resp = _rules_response_with_check(skill="strength", difficulty="hard")
            fake = _FakeLLM(narrative="Vex struggles but succeeds.", rules_response=rules_resp)
            with fake:
                result = await _run(save_dir, "attempt the hard task", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll

    async def test_extreme_difficulty_reduces_total_more(self, save_dir, config):
        """Extreme difficulty applies -2 modifier to the roll total."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        save_state(save_dir, base_state())
        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (6, 6)
        try:
            rules_resp = _rules_response_with_check(skill="strength", difficulty="extreme")
            fake = _FakeLLM(narrative="Vex barely makes it.", rules_response=rules_resp)
            with fake:
                result = await _run(save_dir, "attempt the extreme task", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll


class TestConditionModifiers:
    """Test that condition modifiers affect the band outcome."""

    async def test_wounded_condition_reduces_stat(self, save_dir, config):
        """A wounded condition applies skill-specific modifiers to the roll."""
        import ccya.rules as rules_mod
        from tests.integration.conftest import _FakeLLM

        items = [{"id": "credits", "name": "Credits", "amount": 100, "notes": ""}]
        conditions = [
            {"id": "wounded", "label": "wounded", "description": "Injured.", "added_turn": 0},
        ]
        s = base_state(0)
        s["pc"]["conditions"] = conditions
        s["inventory"] = items
        save_state(save_dir, s)

        orig_roll = rules_mod.roll_2d6
        rules_mod.roll_2d6 = lambda rng=None: (6, 6)
        try:
            rules_resp = _rules_response_with_check(skill="strength")
            fake = _FakeLLM(narrative="Vex fights through the pain.", rules_response=rules_resp)
            with fake:
                result = await _run(save_dir, "fight through the pain", config)
            assert result.turn == 1
        finally:
            rules_mod.roll_2d6 = orig_roll
