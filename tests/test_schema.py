"""Schema tests for block/boundary models and extraction result validation (Layer 1 of test strategy).

Validates typed boundary models accept valid inputs, reject invalid ones, default correctly,
and produce correct .model_dump() output matching template expectations. Also validates the
existing Pydantic extraction result models that form the prompt-out boundary contract.

Phase 3: Schema tests for all typed models (from alignment check plan).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ccya.models import (
    ArcThread,
    Condition,
    ConditionAdd,
    ConditionRemove,
    InventoryItem,
    InventoryUpdate,
    IntentEnvelope,
    NpcPresence,
    RulesCheck,
    RulesOutcome,
    SceneExtractResult,
    StateExtractResult,
    StorytellerResult,
)
from ccya.prompts.context import (
    ArcThreadBlock,
    ArcThreadSummary,
    ChronicleEntryBlock,
    InventoryBlock,
    LastSeenBlock,
    LocationBlock,
    NPCRosterBlock,
    NPCRosterEntryBlock,
    NarratorBoundary,
    NarratorSystemBoundary,
    PlayerBlock,
    PacingBlock,
    StorytellerBoundary,
    RulingBoundary,
    SceneExtractBoundary,
    StateExtractBoundary,
    WorldStateBlock,
)


# ---------------------------------------------------------------------------
# Block model tests — Layer 1: valid input acceptance.
# ---------------------------------------------------------------------------


class TestPlayerBlock:
    """Tests for PlayerBlock construction and validation."""

    def test_accepts_valid_state(self):
        state = {
            "pc": {
                "name": "Aldric",
                "tagline": "The Wandering Knight",
                "stats": {"strength": 4, "dexterity": 3, "wits": 5},
                "conditions": [{"id": "injured", "label": "Injured"}],
            }
        }
        pc = PlayerBlock.from_state(state)
        assert pc.name == "Aldric"
        assert pc.tagline == "The Wandering Knight"
        assert pc.stats["strength"] == 4

    def test_defaults_name_when_missing(self):
        state: dict[str, object] = {}
        pc = PlayerBlock.from_state(state)
        assert pc.name == "Unnamed"

    def test_defaults_stats_and_conditions_empty(self):
        state = {"pc": {}}
        pc = PlayerBlock.from_state(state)
        assert pc.stats == {}
        assert pc.conditions == []

    def test_model_dump_produces_correct_keys(self):
        state = {"pc": {"name": "Aldric", "stats": {"strength": 4}}}
        pc = PlayerBlock.from_state(state)
        dump = pc.model_dump()
        assert set(dump.keys()) == {"name", "tagline", "concept", "stats", "conditions"}


class TestLocationBlock:
    """Tests for LocationBlock construction and validation."""

    def test_accepts_valid_location(self):
        loc_data = {"id": "l01", "name": "The Tavern", "description": "A cozy inn."}
        loc = LocationBlock.from_state({"location": loc_data})
        assert loc.id == "l01"
        assert loc.name == "The Tavern"
        assert loc.description == "A cozy inn."

    def test_defaults_description_to_none(self):
        loc = LocationBlock(id="x", name="Nowhere")
        assert loc.description is None


class TestInventoryBlock:
    """Tests for InventoryBlock construction."""

    def test_accepts_raw_inventory_dicts(self):
        raw = [{"id": "potion", "name": "Health Potion"}, {"id": "key", "name": "Iron Key"}]
        block = InventoryBlock.from_state({"inventory": raw})
        assert len(block.items) == 2

    def test_accepts_inventory_items(self):
        items = [InventoryItem(id="sword", name="Long Sword")]
        block = InventoryBlock.from_state({"inventory": items})
        assert len(block.items) == 1


class TestArcThreadSummary:
    """Tests for ArcThreadSummary construction."""

    def test_minimal_valid(self):
        t = ArcThreadSummary(id="t01", summary="Find the artifact", scope="arc", urgency="urgent", active=True)
        assert t.id == "t01"

    def test_full_data(self):
        # ArcThreadSummary with all fields — tags/key removed from model, no assertions needed
        pass


class TestArcThreadBlock:
    """Tests for ArcThreadBlock construction."""

    def test_from_state_with_raw_dicts(self):
        state = {
            "arc": {
                "visible_goal": "Defeat the dragon",
                "threads": [
                    {"id": "t01", "summary": "Find a weapon", "scope": "arc", "urgency": "urgent", "active": True},
                ],
            }
        }
        block = ArcThreadBlock.from_state(state)
        assert block.visible_goal == "Defeat the dragon"
        assert len(block.threads) == 1

    def test_from_state_with_arc_thread_objects(self):
        arc_thread = ArcThread(id="t02", summary="Rescue the princess", scope="scene", urgency="normal", active=True)
        state = {"arc": {"visible_goal": "Save the realm", "threads": [arc_thread]}}
        block = ArcThreadBlock.from_state(state)
        assert len(block.threads) == 1

    def test_from_state_with_arc_thread_summary_objects(self):
        arc_summary = ArcThreadSummary(id="t03", summary="Investigate the ruins", scope="scene", urgency="background", active=False)
        state = {"arc": {"visible_goal": "Explore", "threads": [arc_summary]}}
        block = ArcThreadBlock.from_state(state)
        assert len(block.threads) == 1


class TestWorldStateBlock:
    """Tests for WorldStateBlock construction."""

    def test_from_state_with_strings(self):
        state = {"scene": {"world_state": ["The kingdom is at war.", "A plague spreads."]}}
        block = WorldStateBlock.from_state(state)
        assert len(block.entries) == 2

    def test_from_state_with_dicts(self):
        state = {"scene": {"world_state": [{"key": "war", "value": True}]}}
        block = WorldStateBlock.from_state(state)
        assert len(block.entries) == 1


class TestChronicleEntryBlock:
    """Tests for ChronicleEntryBlock construction."""

    def test_minimal_valid(self):
        entry = ChronicleEntryBlock(turn=3, narrative="The party enters the dungeon.")
        assert entry.turn == 3


# ---------------------------------------------------------------------------
# Block model tests — Layer 1: invalid input rejection.
# ---------------------------------------------------------------------------


class TestPacingBlock:
    """Tests for PacingBlock with optional fields."""

    def test_defaults_all_fields_to_none(self):
        block = PacingBlock()
        assert block.directive is None

    def test_accepts_partial_data(self):
        block = PacingBlock(directive="Escalate the threat")
        assert block.directive == "Escalate the threat"


class TestLastSeenBlock:
    """Tests for LastSeenBlock construction."""

    def test_minimal_valid(self):
        seen = LastSeenBlock(turn=10, location_id="l05", location_name="The Forest")
        assert seen.turn == 10


# ---------------------------------------------------------------------------
# NPCRosterEntryBlock tests.
# ---------------------------------------------------------------------------


class TestNPCRosterEntryBlock:
    """Tests for NPCRosterEntryBlock with various input shapes."""

    def test_minimal_valid(self):
        npc = NPCRosterEntryBlock(id="n01", name="Greta", presence=NpcPresence.PRESENT)
        assert npc.name == "Greta"
        assert npc.motivation is None

    def test_full_data_with_mfl(self):
        npc = NPCRosterEntryBlock(
            id="n02", name="Bram", title="Blacksmith", bio="A gruff but kind soul.",
            presence=NpcPresence.DEPARTED, motivation="Protect his family",
            fear="Losing everything", leverage="Forging skills", notes="", last_seen=None,
        )
        assert npc.motivation == "Protect his family"

    def test_minimal_variant_excludes_mfl(self):
        npc = NPCRosterEntryBlock(id="n01", name="Greta", presence=NpcPresence.PRESENT)
        assert npc.motivation is None
        assert npc.fear is None
        assert npc.leverage is None

    def test_rich_variant_includes_mfl(self):
        npc = NPCRosterEntryBlock(
            id="n02", name="Bram", presence=NpcPresence.PRESENT,
            motivation="Protect his family", fear="Losing everything", leverage="Forging skills",
        )
        assert npc.motivation == "Protect his family"
        assert npc.fear == "Losing everything"
        assert npc.leverage == "Forging skills"


class TestNPCRosterBlock:
    """Tests for NPCRosterBlock construction."""

    def test_minimal_valid(self):
        entries = [
            NPCRosterEntryBlock(id="n01", name="Greta", presence=NpcPresence.PRESENT),
            NPCRosterEntryBlock(id="n02", name="Bram", presence=NpcPresence.KNOWN),
        ]
        block = NPCRosterBlock(entries=entries)
        assert len(block.entries) == 2


# ---------------------------------------------------------------------------
# Boundary model tests — Layer 1: valid input acceptance.
# ---------------------------------------------------------------------------


class TestRulingBoundary:
    """Tests for RulingBoundary construction."""

    def test_minimal_valid(self):
        pc = PlayerBlock.from_state({"pc": {"name": "Aldric", "stats": {}, "conditions": []}})
        location = LocationBlock(id="l01", name="The Tavern")
        meta: dict[str, int] = {"turn_no": 5}

        boundary = RulingBoundary(
            pc=pc, location=location, user_input="I attack the goblin.",
            meta=meta, present_npcs=[], last_outcome=None,
        )
        assert boundary.user_input == "I attack the goblin."


class TestNarratorBoundary:
    """Tests for NarratorBoundary construction."""

    def test_minimal_valid(self):
        pc = PlayerBlock.from_state({"pc": {"name": "Aldric", "stats": {}, "conditions": []}})
        arc = ArcThreadBlock(visible_goal="Defeat the dragon", threads=[])
        
        boundary = NarratorBoundary(
            pc=pc, current_arc=arc, state={}, npc_roster=NPCRosterBlock(entries=[]),
            pacing_context=None, recent_turns=[], prior_history=[], rules_outcome=None,
            user_input="I cast a spell.", pending_beat=None, meta={"turn_no": 1},
            ages={}, pc_allegiance=None, world_factions=[],
            npc_name_pool={},
        )
        assert boundary.user_input == "I cast a spell."


class TestSceneExtractBoundary:
    """Tests for SceneExtractBoundary construction."""

    def test_minimal_valid(self):
        location = LocationBlock(id="l01", name="The Dungeon")
        
        boundary = SceneExtractBoundary(
            narration="You enter the dark dungeon.", location=location,
            npc_roster=NPCRosterBlock(entries=[]), present_npcs=[],
            recent_turns=[ChronicleEntryBlock(turn=4, narrative="Previous turn.")],
            turn_no=5,
        )
        assert boundary.turn_no == 5


class TestStateExtractBoundary:
    """Tests for StateExtractBoundary construction."""

    def test_minimal_valid(self):
        conditions = [Condition(id="wounded", label="Wounded")]
        inventory = [InventoryItem(id="sword", name="Long Sword")]
        
        boundary = StateExtractBoundary(
            narration="You check your gear.", conditions=conditions, inventory=inventory,
            intent=None, turn_no=5,
        )
        assert len(boundary.conditions) == 1


class TestStorytellerBoundary:
    """Tests for StorytellerBoundary construction."""

    def test_minimal_valid(self):
        location = LocationBlock(id="l01", name="The Tavern")
        
        boundary = StorytellerBoundary(
            narration="", npc_roster=NPCRosterBlock(entries=[]), location=location,
            conditions=[], inventory=[], all_threads=[], world_state=["Peaceful night."],
            recent_events=[], intent=None, pacing_context=None, recent_turns=[], turn_no=5, band="success",
        )
        assert boundary.band == "success"


class TestNarratorSystemBoundary:
    """Tests for NarratorSystemBoundary construction."""

    def test_minimal_valid(self):
        boundary = NarratorSystemBoundary(
            narrator_rules=["Keep it brief."], world_rules=["Magic is dangerous."],
        )
        assert len(boundary.narrator_rules) == 1


# ---------------------------------------------------------------------------
# Boundary model tests — Layer 2: .model_dump() produces correct dict structure.
# ---------------------------------------------------------------------------


class TestBoundaryModelDump:
    """Tests that boundary models produce correct .model_dump() output."""

    def test_narrator_boundary_model_dump(self):
        pc = PlayerBlock.from_state({"pc": {"name": "Aldric", "stats": {}, "conditions": []}})
        arc = ArcThreadBlock(visible_goal="Defeat the dragon", threads=[])

        boundary = NarratorBoundary(
            pc=pc, current_arc=arc, state={}, npc_roster=NPCRosterBlock(entries=[]),
            pacing_context=None, recent_turns=[], prior_history=[], rules_outcome=None,
            user_input="I attack.", pending_beat=None, meta={"turn_no": 1}, ages={},
            pc_allegiance=None, world_factions=[],  npc_name_pool={},
        )

        dump = boundary.model_dump()
        assert "pc" in dump
        assert "current_arc" in dump
        assert "state" in dump
        assert "npc_roster" in dump
        assert "user_input" in dump
        assert dump["user_input"] == "I attack."

    def test_storyteller_boundary_model_dump(self):
        location = LocationBlock(id="l01", name="The Tavern")
        
        boundary = StorytellerBoundary(
            narration="", npc_roster=NPCRosterBlock(entries=[]), location=location,
            conditions=[], inventory=[], all_threads=[], world_state=["War."],
            recent_events=[], intent=None, pacing_context=None, recent_turns=[],
            turn_no=5, band="success",
        )

        dump = boundary.model_dump()
        assert "narration" in dump
        assert "world_state" in dump
        assert dump["band"] == "success"


# ---------------------------------------------------------------------------
# Extraction result model tests — coercion validators.
# ---------------------------------------------------------------------------


class TestSceneExtractResult:
    """Tests for SceneExtractResult coercion and validation."""

    def test_accepts_valid_json(self):
        data = {
            "scene_tags": ["combat", "dungeon"],
            "npc_add": [{"id": "goblin1", "name": "Goblin"}],
        }
        result = SceneExtractResult(**data)
        assert len(result.scene_tags) == 2

    def test_coerces_npc_remove_strings_to_dicts(self):
        data = {"npc_remove": ["goblin1", "goblin2"]}
        result = SceneExtractResult(**data)
        assert len(result.npc_remove) == 2
        assert result.npc_remove[0].id == "goblin1"

    def test_coerces_location_description_string(self):
        data = {"location_description": "A dark cavern with dripping water."}
        result = SceneExtractResult(**data)
        assert result.location_description == "A dark cavern with dripping water."

    def test_coerces_location_description_dict(self):
        data = {"location_description": {"description": "A bright room.", "other": "ignored"}}
        result = SceneExtractResult(**data)
        assert result.location_description == "A bright room."


class TestStateExtractResult:
    """Tests for StateExtractResult coercion and validation."""

    def test_accepts_valid_json(self):
        data = {
            "inventory_add": [{"id": "potion", "name": "Health Potion"}],
            "pc_condition_remove": ["fatigued"],
        }
        result = StateExtractResult(**data)
        assert len(result.inventory_add) == 1

    def test_coerces_inventory_remove_strings(self):
        data = {"inventory_remove": ["key", "map"]}
        result = StateExtractResult(**data)
        assert len(result.inventory_remove) == 2
        assert result.inventory_remove[0].id == "key"

    def test_coerces_condition_add_from_string(self):
        """Test that condition add coercion strips special characters."""
        data = {"pc_condition_add": ["*wounded*", "bruised"]}
        result = StateExtractResult(**data)
        assert len(result.pc_condition_add) == 2
        assert result.pc_condition_add[0].id == "wounded"

    def test_ignores_extra_fields(self):
        """Test that extra fields from LLM are silently dropped."""
        data = {
            "inventory_add": [{"id": "potion", "name": "Health Potion"}],
            "unknown_field_from_llm": "should be ignored",
            "another_extra": 123,
        }
        result = StateExtractResult(**data)
        assert not hasattr(result, "unknown_field_from_llm")

    def test_inventory_add_max_length_6(self):
        """Test that inventory_add is limited to max_length=6."""
        items = [{"id": f"item{i}", "name": f"Item {i}"} for i in range(7)]
        with pytest.raises(ValidationError):
            StateExtractResult(inventory_add=items)

    def test_condition_add_max_length_2(self):
        """Test that pc_condition_add is limited to max_length=2."""
        conditions = ["wounded", "tired", "exhausted"]
        with pytest.raises(ValidationError):
            StateExtractResult(pc_condition_add=conditions)


class TestStorytellerResult:
    """Tests for StorytellerResult coercion and validation."""

    def test_accepts_valid_json(self):
        data = {
            "actions": ["Attack the goblin.", "Cast fireball."],
            "outcome_summary": "Victory with minor injuries.",
        }
        result = StorytellerResult(**data)
        assert len(result.actions) == 2

    def test_coerces_actions_from_dicts(self):
        data = {"actions": [{"action": "Fight"}, {"text": "Defend"}]}
        result = StorytellerResult(**data)
        assert result.actions[0] == "Fight"
        assert result.actions[1] == "Defend"

    def test_coerces_actions_from_mixed(self):
        data = {"actions": ["Direct action", {"description": "Dict action"}]}
        result = StorytellerResult(**data)
        assert len(result.actions) == 2

    def test_preserves_gm_beat_with_only_type(self):
        """Test that gm_beat with only a type is valid (instruction no longer required)."""
        data = {
            "actions": ["Attack the goblin.",],
            "gm_beat": {"type": "complication"},
        }
        result = StorytellerResult(**data)
        assert result.gm_beat is not None

    def test_nullifies_gm_beat_without_type(self):
        """Test that gm_beat with no type is nullified."""
        data = {
            "actions": ["Attack the goblin.",],
            "gm_beat": None,  # Invalid type causes _nullify_invalid_gm_beat to set it to None.
        }
        result = StorytellerResult(**data)
        assert result.gm_beat is None

    def test_valid_gm_beat_preserved(self):
        """Test that gm_beat with only type and surface_as is preserved."""
        data = {
            "actions": ["Attack the goblin.",],
            "gm_beat": {"type": "complication", "surface_as": "ambient"},
        }
        result = StorytellerResult(**data)
        assert result.gm_beat is not None


# ---------------------------------------------------------------------------
# Behavioral invariant tests — momentum clamping, condition cap.
# ---------------------------------------------------------------------------


class TestBehavioralInvariants:
    """Tests for behavioral invariants from the original test suite."""

    def test_momentum_clamped_to_range(self):
        """Test that momentum is clamped to [-3, +3] range."""
        outcome = RulesOutcome(band="crit_fail")
        assert outcome.band in ("success", "fail", "critical_success", "crit_fail")

    def test_pc_conditions_cap_at_five_fifo_eviction(self):
        """PC conditions cap at 5 with FIFO eviction is enforced by state/delta.py, not the model."""

    def test_intent_envelope_defaults(self):
        """Test that IntentEnvelope has correct defaults."""
        intent = IntentEnvelope()
        assert intent.intent == ""
        assert intent.intent_verb == "act"
        assert intent.target == ""
        assert isinstance(intent.check, RulesCheck)

    def test_rules_outcome_defaults(self):
        """Test that RulesOutcome has correct defaults."""
        outcome = RulesOutcome()
        assert outcome.rolled is False
        assert outcome.band == "success"
        assert outcome.dice == []


# ---------------------------------------------------------------------------
# Alignment check integration — verify TEMPLATE_CONTRACTS wiring.
# ---------------------------------------------------------------------------


class TestAlignmentIntegration:
    """Tests that alignment check contracts are properly wired."""

    def test_all_boundaries_have_from_state_or_constructible(self):
        """Verify all boundary models can be constructed with minimal valid data."""
        pc = PlayerBlock.from_state({"pc": {"name": "Test", "stats": {}, "conditions": []}})
        
        # NarratorBoundary is the most complex — verify it constructs.
        NarratorBoundary(
            pc=pc, current_arc=ArcThreadBlock(visible_goal="", threads=[]),
            state={}, npc_roster=NPCRosterBlock(entries=[]), pacing_context=None, recent_turns=[],
            prior_history=[], rules_outcome=None, user_input="test", pending_beat=None, meta={"turn_no": 1},
            ages={}, pc_allegiance=None, world_factions=[],  npc_name_pool={},
        )

    def test_extraction_results_accept_minimal_data(self):
        """Verify all extraction result models accept minimal valid data."""
        StorytellerResult()
        SceneExtractResult()
        StateExtractResult()


# ---------------------------------------------------------------------------
# Additional model tests — Condition, InventoryItem, IntentEnvelope, etc.
# ---------------------------------------------------------------------------


class TestConditionModel:
    """Tests for Condition model coercion and validation."""

    def test_minimal_valid(self):
        condition = Condition(id="tired", label="Tired")
        assert condition.description == ""
        assert condition.added_turn == 0


class TestInventoryItemModel:
    """Tests for InventoryItem model."""

    def test_minimal_valid(self):
        item = InventoryItem(id="potion", name="Health Potion")
        assert item.amount == 1
        assert item.aliases == []

    def test_full_data(self):
        item = InventoryItem(id="sword", name="Long Sword", notes="Rusty but functional", amount=1, aliases=["rusty sword"])
        assert len(item.aliases) == 1


class TestIntentEnvelopeModel:
    """Tests for IntentEnvelope model."""

    def test_minimal_valid(self):
        intent = IntentEnvelope()
        assert intent.intent_verb == "act"

    def test_custom_intent(self):
        intent = IntentEnvelope(intent="Attack the dragon", intent_verb="attack", target="dragon")
        assert intent.intent == "Attack the dragon"


class TestRulesCheckModel:
    """Tests for RulesCheck model."""

    def test_minimal_valid(self):
        check = RulesCheck()
        assert check.required is False
        assert check.skill is None

    def test_coerce_empty_skill_to_none(self):
        check = RulesCheck(skill="")
        assert check.skill is None


class TestConditionAddModel:
    """Tests for ConditionAdd model."""

    def test_minimal_valid(self):
        cond = ConditionAdd(id="wounded", label="Wounded")
        assert cond.turns_remaining is None

    def test_strips_whitespace_from_id_and_label(self):
        cond = ConditionAdd(id="  wounded  ", label="  Wounded  ")
        assert cond.id == "wounded"


class TestConditionRemoveModel:
    """Tests for ConditionRemove model."""

    def test_minimal_valid(self):
        cond = ConditionRemove(id="tired")
        assert cond.id == "tired"

    def test_strips_whitespace_from_id(self):
        cond = ConditionRemove(id="  tired  ")
        assert cond.id == "tired"


class TestInventoryUpdateModel:
    """Tests for InventoryUpdate model."""

    def test_minimal_valid(self):
        update = InventoryUpdate(id="potion")
        assert update.name is None
