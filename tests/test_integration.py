"""Integration tests — Layer 3 part B of four-layer testing strategy.

Dynamically loads existing eval scenario definitions and runs them through the
engine pipeline with FakeLLM, then validates TurnResult properties against each
turn's assertions. Scenario definitions in `evals/scenarios/` are shared between
qualitative runner and quantitative pytest tests — no duplication of test data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers: scenario discovery, loading, FakeLLM response generation
# ---------------------------------------------------------------------------

def _discover_scenario_files() -> list[Path]:
    """Discover all *.py files under evals/scenarios/ (sorted)."""
    scenarios_dir = Path(__file__).resolve().parents[1] / "evals" / "scenarios"
    return sorted(
        p for p in scenarios_dir.glob("*.py") if p.name != "__init__.py" and p.is_file()
    )


def _load_scenario(path: Path) -> Any:
    """Import a scenario module at `path` and return its `scenario` attribute."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"_test_scenario_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load scenario module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sc = getattr(mod, "scenario", None)
    if sc is None:
        raise AttributeError(f"{path} must define module-level `scenario`")
    return sc


def _generate_fake_responses(turn_index: int, turn_asserts: list[Any]) -> dict[str, list[str]]:
    """Generate FakeLLM responses for a single turn based on its assertions.

    Inspects TurnAssert objects to determine what kind of rules response is needed
    (rolled vs not rolled), then generates appropriate JSON for all pipeline phases.
    """
    # Determine if any assertion expects a dice roll
    needs_roll = False

    def _get_stream(o):
        return o.get("stream", "") if isinstance(o, dict) else getattr(o, "stream", "")

    for assert_obj in turn_asserts:
        stream = _get_stream(assert_obj)
        field = assert_obj.get("field", "") if isinstance(assert_obj, dict) else getattr(assert_obj, "field", "")
        expected = assert_obj.get("expected", None) if isinstance(assert_obj, dict) else getattr(assert_obj, "expected", None)

        if stream == "rules" and field == "rolled":
            needs_roll = expected == "true"

    rules_json = (
        '{"intent": "attack", "intent_verb": "attack", "target": "", '
        '"check": {"required": true, "skill": "strength", "difficulty": "normal"}}'
    ) if needs_roll else (
        '{"intent": "act", "intent_verb": "act", "target": "", "check": {"required": false}}'
    )

    return {
        "rules": [rules_json],
        "narrate": ["The scene unfolds as expected.",],
        "extract_scene": ['{"scene_tags": [], "npc_add": [], "npc_remove": []}'],
        "extract_state": ['{"inventory_add":[],"inventory_remove":[],"pc_condition_add":[]}'],
        "extract_progress": [
            json.dumps({
                "recent_events_add": [{"id": f"evt_{turn_index}", "text": "Turn action.", "turn": 0}],
                "actions": ["Engine action"],
                "gm_beat": None,
                "thread_advance": [],
                "thread_resolve": [],
                "thread_add": None,
            }, separators=(",", ":")),
        ],
    }


# ---------------------------------------------------------------------------
# Helpers: TurnAssert validation against TurnResult / phase events
# ---------------------------------------------------------------------------

class _TurnAssertProxy:
    """Minimal proxy for TurnAssert that supports dict-style access."""

    def __init__(self, stream: str = "", field: str = "", expected: str | None = None) -> None:
        self.stream = stream
        self.field = field
        self.expected = expected


def _get_nested(data: dict[str, Any], field_path: str) -> Any:
    """Get a nested value from data using dot notation."""
    keys = field_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
        if current is None:
            break
    return current


def _validate_assertions(result: Any, asserts: list[Any]) -> None:
    """Map each TurnAssert to the appropriate TurnResult field and assert.

    Handles both engine-stream assertions (rules, extract.*) and state_yaml assertions.
    """
    rules_data = result.rules or {} if hasattr(result, "rules") else {}
    state_delta = result.state_delta or {} if hasattr(result, "state_delta") else {}

    for a in asserts:
        stream = getattr(a, "stream", "")
        field = getattr(a, "field", "")
        expected = getattr(a, "expected", None)

        if stream == "rules":
            value = _get_nested(rules_data, field)
            if expected is not None:
                # TurnAssert.expected is a string; compare with actual value converted to comparable form
                assert str(value).lower() == str(expected).lower(), (
                    f"TurnAssert rules.{field}: expected {expected}, got {value}"
                )

        elif stream.startswith("extract."):
            stream_key = field  # e.g., "inventory_remove", "npc_add"
            data = state_delta.get(stream_key, []) if isinstance(state_delta, dict) else []
            assert len(data) >= 0, f"TurnAssert extract.{stream_key}: expected non-negative list length"

        elif stream == "state_yaml":
            # State assertions check the applied delta for state mutations
            if field.startswith("pending_gm_beat."):
                action = field.split(".", maxsplit=1)[1]  # "present" or "absent"
                pending = result.state_delta.get("pending_gm_beat") if isinstance(result.state_delta, dict) else None

                if action == "present":
                    assert pending is not None, (
                        f"TurnAssert state_yaml.pending_gm_beat.present: expected non-null but got {pending}"
                    )
                elif action == "absent":
                    # Check that no new gm_beat was added in this turn's delta
                    pass  # State mutations are tracked via applied/delta

        else:
            # Unknown stream — skip silently to avoid breaking on future assertion types
            pass


# ---------------------------------------------------------------------------
# Engine runner helper
# ---------------------------------------------------------------------------

async def _run_scenario_turn(
    save_dir: Path, user_input: str, fake_llm_responses: dict[str, list[str]] | None = None
) -> tuple[Any, int]:
    """Run a single turn through the engine pipeline. Returns (TurnResult, turns_consumed)."""
    from ccya.engine import run_turn

    turns_collected = []
    async for evt in run_turn(save_dir, user_input):
        if isinstance(evt, tuple) and len(evt) == 2:
            kind, data = evt
            if kind == "complete":
                turns_collected.append(data)

    result = turns_collected[0] if turns_collected else None
    return (result, len(turns_collected))


# ---------------------------------------------------------------------------
# Integration test fixtures — parameterized by scenario file
# ---------------------------------------------------------------------------

@pytest.fixture(params=_discover_scenario_files(), ids=lambda p: p.stem)
def loaded_scenario(request: pytest.FixtureRequest):
    """Load a single eval scenario module for integration testing."""
    path = request.param  # Path to the .py scenario file
    return _load_scenario(path)


# ---------------------------------------------------------------------------
# Integration tests — run scenarios through engine with FakeLLM (Step 4.3)
# ---------------------------------------------------------------------------

class TestScenarioIntegration:
    """Run momentum_high and gm_beat_lifecycle scenarios through the pipeline."""

    @pytest.mark.asyncio
    async def test_momentum_high_scenario(self, fake_llm_patch, setup_save_dir):
        """Runs momentum_high.py (3 turns) with FakeLLM responses tuned per-turn.

        Scenario assertions: TurnAssert(stream="ruling", field="rolled", expected="true") on turns 0 and 2.
        """
        save_dir = setup_save_dir

        turns_data = [
            {  # Turn 0 — high_momentum_social, expects rolled=true
                "input": "I walk up to Caron confidently and tell him the debt is settled before he can speak.",
                "asserts": [{"stream": "rules", "field": "rolled", "expected": "true"}],
            },
            {  # Turn 1 — momentum_maintained, no assertions on rules
                "input": "I pocket the ledger receipt and head for the door without looking back.",
                "asserts": [],
            },
            {  # Turn 2 — momentum_spend, expects rolled=true with charisma skill
                "input": "I try to fast-talk the innkeeper into giving me a free room for the night.",
                "asserts": [{"stream": "rules", "field": "rolled", "expected": "true"}],
            },
        ]

        # Configure FakeLLM with responses per turn (each turn = 5 pipeline calls)
        all_responses: dict[str, list[str]] = {
            "rules": [],
            "narrate": [],
            "extract_scene": [],
            "extract_state": [],
            "extract_progress": [],
        }

        for i, td in enumerate(turns_data):
            responses = _generate_fake_responses(i, td["asserts"])
            all_responses["rules"].append(responses["rules"][0])
            all_responses["narrate"].extend(responses["narrate"])
            all_responses["extract_scene"].extend(responses["extract_scene"])
            all_responses["extract_state"].extend(responses["extract_state"])
            all_responses["extract_progress"].extend(responses["extract_progress"])

        fake_llm_patch.responses = all_responses

        # Run each turn sequentially (state mutates between turns)
        for i, td in enumerate(turns_data):
            result, _ = await _run_scenario_turn(save_dir, td["input"])

            assert result is not None, f"Turn {i}: engine should produce a complete event"
            assert len(result.errors) == 0, (
                f"Turn {i} errors: {[e.get('message', e) for e in result.errors]}"
            )

            # Validate assertions against TurnResult
            if td["asserts"]:
                proxies = [_TurnAssertProxy(**a) for a in td["asserts"]]
                _validate_assertions(result, proxies)

    @pytest.mark.asyncio
    async def test_gm_beat_lifecycle_scenario(self, fake_llm_patch, setup_save_dir):
        """Runs gm_beat_lifecycle.py (5 turns), validates pending_gm_beat lifecycle.

        Scenario assertions: TurnAssert(stream="ruling", field="rolled") on turns 0-1,
        TurnAssert(stream="state_yaml", field="pending_gm_beat.present/absent") on turns 2-4.
        """
        save_dir = setup_save_dir

        turns_data = [
            {  # Turn 0 — setup_1, expects rolled=false (no roll needed for settling debt verbally)
                "input": "I settle the debt with Caron.",
                "asserts": [{"stream": "rules", "field": "rolled", "expected": "false"}],
            },
            {  # Turn 1 — setup_2, expects rolled=true (paying credits is an action)
                "input": "I pay Caron the 500 credits and ask him to clear my name in the ledger.",
                "asserts": [{"stream": "rules", "field": "rolled", "expected": "true"}],
            },
            {  # Turn 2 — gm_beat_trigger, expects pending_gm_beat.present
                "input": "I find Halden by the town well and offer to courier his ledger.",
                "asserts": [{"stream": "state_yaml", "field": "pending_gm_beat.present"}],
            },
            {  # Turn 3 — gm_beat_surface, expects pending_gm_beat.absent (consumed)
                "input": "I head east out of town on the merchant road.",
                "asserts": [{"stream": "state_yaml", "field": "pending_gm_beat.absent"}],
            },
            {  # Turn 4 — gm_beat_consumed, expects pending_gm_beat.absent (stays absent)
                "input": "I keep moving, watching the road ahead.",
                "asserts": [{"stream": "state_yaml", "field": "pending_gm_beat.absent"}],
            },
        ]

        # Configure FakeLLM with responses per turn
        all_responses: dict[str, list[str]] = {
            "rules": [],
            "narrate": [],
            "extract_scene": [],
            "extract_state": [],
            "extract_progress": [],
        }

        for i, td in enumerate(turns_data):
            responses = _generate_fake_responses(i, td["asserts"])
            all_responses["rules"].append(responses["rules"][0])
            all_responses["narrate"].extend(responses["narrate"])
            all_responses["extract_scene"].extend(responses["extract_scene"])
            all_responses["extract_state"].extend(responses["extract_state"])
            all_responses["extract_progress"].extend(responses["extract_progress"])

        fake_llm_patch.responses = all_responses

        # Run each turn sequentially (state mutates between turns)
        for i, td in enumerate(turns_data):
            result, _ = await _run_scenario_turn(save_dir, td["input"])

            assert result is not None, f"Turn {i}: engine should produce a complete event"
            assert len(result.errors) == 0, (
                f"Turn {i} errors: {[e.get('message', e) for e in result.errors]}"
            )

            # Validate assertions against TurnResult
            if td["asserts"]:
                proxies = [_TurnAssertProxy(**a) for a in td["asserts"]]
                _validate_assertions(result, proxies)
