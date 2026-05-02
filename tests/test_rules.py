"""Unit tests for the rules engine — no LLM, no I/O."""

import random

import pytest

from ccya.rules import (
    DIFFICULTY_MOD,
    VALID_SKILLS,
    build_directive,
    compute_band,
    conditions_modifier,
    resolve_check,
    roll_2d6,
)


# ---------------------------------------------------------------------------
# roll_2d6
# ---------------------------------------------------------------------------


class TestRoll2d6:
    def test_values_in_range(self):
        rng = random.Random(42)
        for _ in range(200):
            d1, d2 = roll_2d6(rng)
            assert 1 <= d1 <= 6
            assert 1 <= d2 <= 6

    def test_seeded_deterministic(self):
        r1, r2 = roll_2d6(random.Random(99)), roll_2d6(random.Random(99))
        assert r1 == r2

    def test_returns_tuple_of_two(self):
        result = roll_2d6(random.Random(1))
        assert len(result) == 2


# ---------------------------------------------------------------------------
# compute_band — boundary tests
# ---------------------------------------------------------------------------


class TestComputeBand:
    def test_raw_2_always_crit_fail(self):
        # dice = (1,1), raw=2; even if modifiers push total high, crit_fail wins
        assert compute_band(99, (1, 1)) == "crit_fail"

    def test_raw_12_always_crit_success(self):
        assert compute_band(-5, (6, 6)) == "crit_success"

    def test_final_le_6_is_fail(self):
        # raw (3,3)=6; final=6 → fail
        assert compute_band(6, (3, 3)) == "fail"

    def test_final_le_6_below_is_fail(self):
        assert compute_band(4, (2, 2)) == "fail"

    def test_final_7_is_mixed(self):
        assert compute_band(7, (3, 4)) == "mixed"

    def test_final_9_is_mixed(self):
        assert compute_band(9, (4, 5)) == "mixed"

    def test_final_10_is_success(self):
        assert compute_band(10, (5, 5)) == "success"

    def test_final_11_is_success(self):
        assert compute_band(11, (5, 6)) == "success"

    def test_final_12_non_crit_dice_is_crit_success(self):
        # raw (3,5)=8 → not a raw-crit; final=12 → crit_success
        assert compute_band(12, (3, 5)) == "crit_success"


# ---------------------------------------------------------------------------
# conditions_modifier
# ---------------------------------------------------------------------------


class TestConditionsModifier:
    def test_no_conditions(self):
        assert conditions_modifier("strength", []) == 0

    def test_wounded_affects_strength(self):
        assert conditions_modifier("strength", ["wounded"]) == -1

    def test_wounded_affects_dexterity(self):
        assert conditions_modifier("dexterity", ["wounded"]) == -1

    def test_wounded_does_not_affect_wits(self):
        assert conditions_modifier("wits", ["wounded"]) == 0

    def test_stacked_conditions(self):
        # wounded (-1 str) + exhausted (-1 str) = -2
        assert conditions_modifier("strength", ["wounded", "exhausted"]) == -2

    def test_exhausted_resolve(self):
        assert conditions_modifier("resolve", ["exhausted"]) == -1

    def test_unknown_condition_ignored(self):
        assert conditions_modifier("wits", ["caffeinated", "pumped"]) == 0

    def test_case_insensitive(self):
        assert conditions_modifier("strength", ["Wounded"]) == -1


# ---------------------------------------------------------------------------
# difficulty mod map
# ---------------------------------------------------------------------------


class TestDifficultyMod:
    def test_all_keys_present(self):
        for key in ["trivial", "easy", "normal", "hard", "extreme"]:
            assert key in DIFFICULTY_MOD

    def test_trivial_positive(self):
        assert DIFFICULTY_MOD["trivial"] > 0

    def test_extreme_negative(self):
        assert DIFFICULTY_MOD["extreme"] < 0

    def test_normal_zero(self):
        assert DIFFICULTY_MOD["normal"] == 0


# ---------------------------------------------------------------------------
# build_directive
# ---------------------------------------------------------------------------


class TestBuildDirective:
    def test_fail_verb_in_directive(self):
        d = build_directive("fail", "attack", "strength")
        assert "attack" in d
        assert "fail" in d.lower()

    def test_crit_success_verb(self):
        d = build_directive("crit_success", "persuade", "charisma")
        assert "persuade" in d

    def test_unknown_band_falls_back(self):
        d = build_directive("nonsense", "act", "wits")
        assert isinstance(d, str) and len(d) > 0

    def test_all_bands_covered(self):
        for band in ["crit_fail", "fail", "mixed", "success", "crit_success"]:
            d = build_directive(band, "hack", "wits")
            assert isinstance(d, str) and len(d) > 5


# ---------------------------------------------------------------------------
# resolve_check — end-to-end
# ---------------------------------------------------------------------------


class TestResolveCheck:
    _STATS = {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 3, "resolve": 2}

    def test_returns_rolled_true(self):
        rng = random.Random(1)
        out = resolve_check(
            skill="wits", difficulty="normal",
            pc_stats=self._STATS, pc_conditions=[],
            rng=rng,
        )
        assert out.rolled is True

    def test_seeded_deterministic(self):
        o1 = resolve_check(skill="strength", difficulty="normal", pc_stats=self._STATS, pc_conditions=[], rng=random.Random(7))
        o2 = resolve_check(skill="strength", difficulty="normal", pc_stats=self._STATS, pc_conditions=[], rng=random.Random(7))
        assert o1.dice == o2.dice
        assert o1.band == o2.band

    def test_stat_mod_applied(self):
        # wits=3 → stat_mod=+1
        rng = random.Random(42)
        out = resolve_check(skill="wits", difficulty="normal", pc_stats=self._STATS, pc_conditions=[], rng=rng)
        assert out.stat_mod == 1
        assert out.final_total == out.raw_total + 1

    def test_difficulty_mod_applied(self):
        rng = random.Random(42)
        out = resolve_check(skill="wits", difficulty="hard", pc_stats=self._STATS, pc_conditions=[], rng=rng)
        assert out.diff_mod == -1

    def test_condition_mod_applied(self):
        rng = random.Random(42)
        out = resolve_check(
            skill="strength", difficulty="normal",
            pc_stats=self._STATS, pc_conditions=["wounded"],
            rng=rng,
        )
        assert out.cond_mod == -1
        assert out.final_total == out.raw_total + out.stat_mod + out.diff_mod + out.cond_mod

    def test_stat_default_2_when_missing(self):
        rng = random.Random(1)
        out = resolve_check(skill="lore", difficulty="normal", pc_stats={}, pc_conditions=[], rng=rng)
        assert out.stat_value == 2
        assert out.stat_mod == 0

    def test_invalid_skill_raises(self):
        with pytest.raises(ValueError, match="Unknown skill"):
            resolve_check(skill="magic", difficulty="normal", pc_stats=self._STATS, pc_conditions=[])

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValueError, match="Unknown difficulty"):
            resolve_check(skill="wits", difficulty="legendary", pc_stats=self._STATS, pc_conditions=[])

    def test_crit_fail_on_snake_eyes(self):
        """Raw (1,1) → crit_fail regardless of modifiers."""
        # Use seeded RNG that we know produces (1,1) by monkeypatching
        import ccya.rules as r

        orig = r.roll_2d6
        try:
            r.roll_2d6 = lambda rng=None: (1, 1)
            out = resolve_check(
                skill="charisma", difficulty="trivial",
                pc_stats={"charisma": 4}, pc_conditions=[],
            )
            assert out.band == "crit_fail"
        finally:
            r.roll_2d6 = orig

    def test_crit_success_on_boxcars(self):
        import ccya.rules as r

        orig = r.roll_2d6
        try:
            r.roll_2d6 = lambda rng=None: (6, 6)
            out = resolve_check(
                skill="strength", difficulty="extreme",
                pc_stats={"strength": 1}, pc_conditions=["exhausted"],
            )
            assert out.band == "crit_success"
        finally:
            r.roll_2d6 = orig

    def test_intent_verb_stored(self):
        rng = random.Random(3)
        out = resolve_check(
            skill="dexterity", difficulty="normal",
            pc_stats=self._STATS, pc_conditions=[],
            intent_verb="sneak", intent="Slip past the guard",
            rng=rng,
        )
        assert out.intent_verb == "sneak"
        assert out.intent == "Slip past the guard"

    def test_band_in_valid_set(self):
        rng = random.Random(999)
        for skill in VALID_SKILLS:
            out = resolve_check(skill=skill, difficulty="normal", pc_stats=self._STATS, pc_conditions=[], rng=rng)
            assert out.band in {"crit_fail", "fail", "mixed", "success", "crit_success"}
