"""Tier 1 schema validation for eval scenarios and engine_mirror.

Runs under `make test`. No LLM calls. No I/O beyond imports.

Validates:
- engine_mirror constants are importable and self-consistent
- Every stream in EXTRACT_STREAMS has an entry in KNOWN_ASSERT_FIELDS
- Every TurnAssert in every scenario uses a known (stream, field) combination
- seed_overrides dotpaths are in a known set
"""
from __future__ import annotations

import pytest

from ccya.eval.engine_mirror import (
    EXTRACT_STREAMS,
    KNOWN_ASSERT_FIELDS,
    KNOWN_SEED_PATHS,
    MOMENTUM_MIN,
    MOMENTUM_MAX,
    PRESSURE_BUILDING_AT,
    PRESSURE_IMMEDIATE_AT,
    constants_block,
)
from ccya.eval.scenario import discover_scenarios, load_scenario


def test_engine_mirror_imports() -> None:
    """engine_mirror constants are importable and self-consistent."""
    assert PRESSURE_BUILDING_AT < PRESSURE_IMMEDIATE_AT, (
        f"PRESSURE_BUILDING_AT ({PRESSURE_BUILDING_AT}) must be < "
        f"PRESSURE_IMMEDIATE_AT ({PRESSURE_IMMEDIATE_AT})"
    )
    assert MOMENTUM_MIN < 0 < MOMENTUM_MAX
    block = constants_block()
    assert "Engine Constants" in block
    assert str(PRESSURE_BUILDING_AT) in block


def test_engine_mirror_known_fields_cover_streams() -> None:
    """Every stream in EXTRACT_STREAMS has an entry in KNOWN_ASSERT_FIELDS."""
    for stream in EXTRACT_STREAMS:
        assert stream in KNOWN_ASSERT_FIELDS, (
            f"Stream {stream!r} in EXTRACT_STREAMS has no entry in KNOWN_ASSERT_FIELDS. "
            f"Add it or remove it from EXTRACT_STREAMS."
        )


@pytest.mark.parametrize("scenario_path", discover_scenarios())
def test_scenario_assert_fields_are_known(scenario_path) -> None:
    """Every TurnAssert in every scenario uses a known (stream, field) combination.

    Fails immediately with the scenario id, turn index, and field name when a
    field is renamed in runner._check_asserts without updating KNOWN_ASSERT_FIELDS.
    """
    scenario = load_scenario(scenario_path)
    for turn_idx, turn in enumerate(scenario.turns):
        for assert_ in (turn.asserts or []):
            known_fields = KNOWN_ASSERT_FIELDS.get(assert_.stream)
            assert known_fields is not None, (
                f"Scenario {scenario.id!r} turn {turn_idx} uses unknown stream "
                f"{assert_.stream!r}. Add it to KNOWN_ASSERT_FIELDS in engine_mirror.py "
                f"and add a handler in runner._check_asserts."
            )
            assert assert_.field in known_fields, (
                f"Scenario {scenario.id!r} turn {turn_idx}: stream {assert_.stream!r} "
                f"has no field {assert_.field!r}. "
                f"Known fields: {sorted(known_fields)}. "
                f"Update engine_mirror.KNOWN_ASSERT_FIELDS and runner._check_asserts together."
            )


def test_scenario_seed_overrides_use_known_paths() -> None:
    """seed_overrides dotpaths are in a known set — catches typos before a full eval run."""
    for scenario_path in discover_scenarios():
        scenario = load_scenario(scenario_path)
        for path in (scenario.seed_overrides or {}):
            assert path in KNOWN_SEED_PATHS, (
                f"Scenario {scenario.id!r} uses unknown seed_override path {path!r}. "
                f"Add it to KNOWN_SEED_PATHS in test_eval_schema.py if it's intentional."
            )
