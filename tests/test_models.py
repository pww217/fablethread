"""Unit tests for GMBeat quality validation — no LLM, no I/O."""

import pytest

from ccya.models import GMBeat, SceneExtractResult


class TestGMBeatValidatorRejectsEmpty:
    def test_empty_string(self):
        assert GMBeat(type="complication", instruction="").instruction is None

    def test_whitespace_only(self):
        assert GMBeat(type="complication", instruction="   ").instruction is None

    def test_none(self):
        assert GMBeat(type="complication", instruction=None).instruction is None


class TestGMBeatValidatorRejectsShort:
    def test_under_40_chars(self):
        assert GMBeat(type="complication", instruction="Guards arrive.").instruction is None

    def test_exactly_39_chars(self):
        assert GMBeat(type="complication", instruction="A" * 39).instruction is None

    def test_40_chars_passes(self):
        b = GMBeat(type="complication", instruction="A" * 40)
        assert b.instruction is not None


class TestGMBeatValidatorRejectsFiller:
    @pytest.mark.parametrize(
        "filler",
        [
            "Something happens to the player.",
            "Give the player a chance to rest.",
            "Add tension to the scene.",
            "Introduce a complication.",
            "Create a problem.",
            "An event occurs that affects the party.",
            "Things get worse for the player.",
            "A complication arises in the shadows.",
            "Raise the stakes with a new threat.",
            "Provide a challenge for the player.",
            "Create a dilemma for the protagonist.",
            "Introduce a new obstacle.",
            "The gm decides something happens.",
        ],
    )
    def test_filler_prefixes(self, filler):
        assert GMBeat(type="complication", instruction=filler).instruction is None, (
            f"Expected None for: {filler}"
        )


class TestGMBeatValidatorAcceptsSpecific:
    def test_named_npc(self):
        b = GMBeat(
            type="revelation",
            instruction="The woman the player spoke with at the inn, Sera Lant, is visible through the crowd — she is meeting with the harbor prefect who publicly denied knowing her."
        )
        assert b.instruction is not None

    def test_named_faction(self):
        b = GMBeat(
            type="complication",
            instruction="Marten Voss, the dockmaster's enforcer the player spoke with earlier, has quietly signaled two armed men near the exit — they are waiting for the player to leave."
        )
        assert b.instruction is not None

    def test_named_object(self):
        b = GMBeat(
            type="opportunity",
            instruction="The satchel the fleeing guard dropped contains a partial map with a location marked in red ink — the same symbol the player saw on the warehouse door."
        )
        assert b.instruction is not None

    def test_named_location(self):
        b = GMBeat(
            type="pressure",
            instruction="Councilor Drae has just entered the far end of the hall. She has not seen the player yet, but one of the staff has noticed both of them."
        )
        assert b.instruction is not None


class TestSceneExtractResultNullifiesBadBeat:
    def test_nullifies_empty_instruction(self):
        r = SceneExtractResult(gm_beat={"type": "complication", "instruction": ""})
        assert r.gm_beat is None

    def test_nullifies_short_instruction(self):
        r = SceneExtractResult(gm_beat={"type": "complication", "instruction": "Something bad happens."})
        assert r.gm_beat is None

    def test_nullifies_missing_type(self):
        r = SceneExtractResult(gm_beat={"instruction": "A valid beat with enough words to pass the length check."})
        assert r.gm_beat is None

    def test_preserves_good_beat(self):
        r = SceneExtractResult(gm_beat={
            "type": "complication",
            "surface_as": "npc_behavior",
            "instruction": "Torben Klask, who agreed to help the player, has just received a message that visibly disturbed him — he is avoiding eye contact."
        })
        assert r.gm_beat is not None
        assert r.gm_beat.type == "complication"

    def test_preserves_none_beat(self):
        r = SceneExtractResult(gm_beat=None)
        assert r.gm_beat is None
