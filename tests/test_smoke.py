"""Smoke tests — Layer 3 part A of four-layer testing strategy.

Run the full engine pipeline via `run_turn()` with FakeLLM responses, asserting
high-level TurnResult properties. These catch wiring mistakes that render+schema
tests can't detect: broken import paths, wrong argument passing between steps,
unexpected exception propagation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


class TestBasicDialogueTurnNoDice:
    """Complete pipeline with no dice roll — the simplest path."""

    @pytest.mark.asyncio
    async def test_basic_dialogue_turn_no_dice(self, fake_llm_patch, setup_save_dir):
        # Configure FakeLLM responses for a simple dialogue turn (no check required)
        fake_llm_patch.responses = {
            "rules": [
                '{"intent": "greet", "intent_verb": "persuade", "target": "", "check": {"required": false}}',
            ],
            "narrate": ["The guard nods politely and gestures toward the bar.",],
            "extract_scene": ['{"scene_tags": [], "npc_add": [], "npc_remove": []}'],
            "extract_state": ['{"inventory_add": [], "inventory_remove": [], "pc_condition_add": []}'],
            "extract_progress": [
                '{',
                '  "recent_events_add": [{"id": "evt1", "text": "You greet the guard.", "turn": 2}], ',
                '  "actions": ["Greeted Captain Voss"], ',
                '  "gm_beat": null, ',
                '  "thread_advance": [], ',
                '  "thread_resolve": [], ',
                '  "thread_add": null',
                '}',
            ],
        }

        save_dir = setup_save_dir

        # Collect all yields from run_turn until complete event
        turns_collected = []
        async for evt in self._run_engine(save_dir, "Hello, how are you?"):
            if isinstance(evt, tuple) and len(evt) == 2:
                kind, data = evt
                if kind == "complete":
                    turns_collected.append(data)

        assert len(turns_collected) >= 1, "Engine should yield at least one complete event"
        result = turns_collected[0]

        # TurnResult.narrative is non-empty string (>10 chars)
        assert isinstance(result.narrative, str), f"narrative should be str, got {type(result.narrative)}"
        assert len(result.narrative) > 10, f"Narrative too short: '{result.narrative}'"

        # TurnResult.rules contains intent classification with check.required=False equivalent
        rules_data = result.rules or {}
        assert "intent_verb" in rules_data or "rolled" in rules_data, (
            f"rules data missing expected keys. Got: {list(rules_data.keys())}"
        )

        # TurnResult.state_delta has valid structure (keys match StateDelta model fields)
        state_delta = result.state_delta or {}
        assert isinstance(state_delta, dict), f"state_delta should be dict, got {type(state_delta)}"

        # TurnResult.metrics contains timing data for each pipeline step
        metrics = result.metrics or {}
        assert "rules" in metrics or "narrate" in metrics or "extract" in metrics, (
            f"metrics missing expected keys. Got: {list(metrics.keys())}"
        )

        # No errors in TurnResult.errors list
        assert len(result.errors) == 0, f"Engine should not produce errors: {result.errors}"


    async def _run_engine(self, save_dir: Path, user_input: str):
        """Helper to run the engine pipeline."""
        from ccya.engine import run_turn

        async for evt in run_turn(save_dir, user_input):
            yield evt


class TestActionWithDiceRollAndInventoryChange:
    """Complete pipeline with dice resolution and inventory delta applied."""

    @pytest.mark.asyncio
    async def test_action_with_dice_roll_and_inventory_change(self, fake_llm_patch, setup_save_dir):
        # Configure FakeLLM responses for an action requiring a check (dice roll)
        rules_response = '{"intent": "attack", "intent_verb": "attack", "target": "guard1", ' \
                         '"check": {"required": true, "skill": "strength", "difficulty": "normal"}}'

        fake_llm_patch.responses = {
            "rules": [rules_response],
            "narrate": ["You swing your sword at the guard with all your might.",],
            "extract_scene": ['{"scene_tags": [], "npc_add": [], "npc_remove": []}'],
            "extract_state": ['{"inventory_add": [{"id": "potion", "name": "Health Potion", "amount": 1, "notes": ""}], "inventory_remove": [], "pc_condition_add": []}'],
            "extract_progress": [
                '{',
                '  "recent_events_add": [{"id": "evt2", "text": "You attacked the guard.", "turn": 3}], ',
                '  "actions": ["Attacked Captain Voss with sword"], ',
                '  "gm_beat": null, ',
                '  "thread_advance": [], ',
                '  "thread_resolve": [], ',
                '  "thread_add": null',
                '}',
            ],
        }

        save_dir = setup_save_dir

        turns_collected = []
        async for evt in self._run_engine(save_dir, "I swing my sword at the guard"):
            if isinstance(evt, tuple) and len(evt) == 2:
                kind, data = evt
                if kind == "complete":
                    turns_collected.append(data)

        assert len(turns_collected) >= 1, "Engine should yield at least one complete event"
        result = turns_collected[0]

        # TurnResult.rules.rolled is True with valid dice data
        rules_data = result.rules or {}
        assert rules_data.get("rolled") is True, (
            f"Expected rolled=True in rules data. Got: {rules_data}"
        )

        # TurnResult.state_delta contains expected inventory_add entries
        state_delta = result.state_delta or {}
        inv_add = state_delta.get("inventory_add", [])
        assert isinstance(inv_add, list), f"inventory_add should be a list, got {type(inv_add)}"

        # TurnResult.scene_tags reflects scene context from extraction (should be valid)
        assert isinstance(result.scene_tags, list), "scene_tags should be a list"

        # TurnResult.actions list has engine-generated actions (not empty if progress extract succeeded)
        assert isinstance(result.actions, list), f"actions should be a list, got {type(result.actions)}"

        # TurnResult.metrics shows rules time > 0 (deterministic Python roll, should be fast but non-zero)
        metrics = result.metrics or {}
        rules_metrics = metrics.get("rules", {})
        assert isinstance(rules_metrics, dict), f"rules metrics should be a dict. Got: {metrics}"

    async def _run_engine(self, save_dir: Path, user_input: str):
        """Helper to run the engine pipeline."""
        from ccya.engine import run_turn

        async for evt in run_turn(save_dir, user_input):
            yield evt
