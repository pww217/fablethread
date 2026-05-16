"""Unit tests for GMBeat quality validation — no LLM, no I/O."""

import pytest

from ccya.models import GMBeat, ProgressExtractResult, SceneExtractResult, ScenePressure
from ccya.pack import ScenarioBrief


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


class TestProgressExtractResultNullifiesBadBeat:
    def test_nullifies_empty_instruction(self):
        r = ProgressExtractResult(gm_beat={"type": "complication", "instruction": ""})
        assert r.gm_beat is None

    def test_nullifies_short_instruction(self):
        r = ProgressExtractResult(gm_beat={"type": "complication", "instruction": "Something bad happens."})
        assert r.gm_beat is None

    def test_nullifies_missing_type(self):
        r = ProgressExtractResult(gm_beat={"instruction": "A valid beat with enough words to pass the length check."})
        assert r.gm_beat is None

    def test_preserves_good_beat(self):
        r = ProgressExtractResult(gm_beat={
            "type": "complication",
            "surface_as": "npc_behavior",
            "instruction": "Torben Klask, who agreed to help the player, has just received a message that visibly disturbed him — he is avoiding eye contact."
        })
        assert r.gm_beat is not None
        assert r.gm_beat.type == "complication"

    def test_preserves_none_beat(self):
        r = ProgressExtractResult(gm_beat=None)
        assert r.gm_beat is None


class TestSceneExtractResultNoGmBeat:
    def test_no_gm_beat_attribute(self):
        r = SceneExtractResult()
        assert "gm_beat" not in r.model_fields


class TestGMBeatNewTypes:
    @pytest.mark.parametrize("beat_type", ["twist", "setback", "escalation", "callback"])
    def test_new_types_validate(self, beat_type):
        b = GMBeat(type=beat_type, instruction="A long enough instruction string that passes the quality gate without issues")
        assert b.type == beat_type


class TestGMBeatNewSurfaceAs:
    @pytest.mark.parametrize("surface", ["environmental", "player_discovery", "item"])
    def test_new_surface_as_validate(self, surface):
        b = GMBeat(surface_as=surface, instruction="A long enough instruction string that passes the quality gate without issues")
        assert b.surface_as == surface


class TestGMBeatExpiresTurn:
    def test_expires_turn_roundtrips(self):
        b = GMBeat(
            type="complication",
            instruction="A long enough instruction string that passes the quality gate without issues",
            beat_expires_turn=5,
        )
        dump = b.model_dump(exclude_none=True)
        assert dump["beat_expires_turn"] == 5

    def test_expires_turn_none_excluded(self):
        b = GMBeat(
            type="complication",
            instruction="A long enough instruction string that passes the quality gate without issues",
        )
        dump = b.model_dump(exclude_none=True)
        assert "beat_expires_turn" not in dump


class TestScenarioBriefWorldRules:
    def test_defaults_empty(self):
        s = ScenarioBrief()
        assert s.world_rules == []

    def test_accepts_three(self):
        s = ScenarioBrief(world_rules=["a", "b", "c"])
        assert len(s.world_rules) == 3

    def test_rejects_six(self):
        with pytest.raises(Exception):
            ScenarioBrief(world_rules=["a", "b", "c", "d", "e", "f"])

    def test_accepts_five(self):
        s = ScenarioBrief(world_rules=["a", "b", "c", "d", "e"])
        assert len(s.world_rules) == 5


class TestSceneExtractResultNoPressureLifecycle:
    def test_no_pressure_lifecycle_fields(self):
        r = SceneExtractResult()
        assert not hasattr(r, "scene_pressure_remove")
        assert not hasattr(r, "scene_pressure_update")


class TestProgressExtractResultHasPressureLifecycle:
    def test_has_all_three_pressure_operations(self):
        r = ProgressExtractResult()
        assert hasattr(r, "scene_pressure_add")
        assert hasattr(r, "scene_pressure_remove")
        assert hasattr(r, "scene_pressure_update")
        assert r.scene_pressure_remove == []
        assert r.scene_pressure_update == []

    def test_pressure_update_accepts_scene_pressure(self):
        r = ProgressExtractResult(scene_pressure_update=[
            ScenePressure(id="p1", text="updated", urgency="immediate")
        ])
        assert len(r.scene_pressure_update) == 1
        assert r.scene_pressure_update[0].id == "p1"


class TestProgressExtractResultActionsValidator:
    def test_empty_actions_warns(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            r = ProgressExtractResult(actions=[])
        assert r.actions == []
        assert any("progress.actions is empty" in record.message for record in caplog.records)

    def test_missing_actions_warns(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            r = ProgressExtractResult()
        assert r.actions == []
        assert any("progress.actions is empty" in record.message for record in caplog.records)

    def test_nonempty_actions_no_warning(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            r = ProgressExtractResult(actions=["go left", "go right", "attack", "speak"])
        assert len(r.actions) == 4
        assert not any("progress.actions is empty" in record.message for record in caplog.records)

    def test_actions_coerced_from_dicts(self):
        r = ProgressExtractResult(actions=[
            {"action": "fire at the chest"},
            {"description": "convince the guard"},
            {"text": "climb the wall"},
            "jump over the fence",
        ])
        assert len(r.actions) == 4
        assert r.actions[0] == "fire at the chest"
        assert r.actions[1] == "convince the guard"
        assert r.actions[2] == "climb the wall"
        assert r.actions[3] == "jump over the fence"
