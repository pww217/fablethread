"""Read-only mirror of engine constants for use by eval scenarios and build_trace.

Import from here in scenarios — never hardcode thresholds or field names.
All values reflect current engine defaults. Where EngineConfig controls the
value at runtime, the default is used (eval runs use default EngineConfig
unless overridden in EvalConfig).
"""
from __future__ import annotations

from ccya.engine.config import EngineConfig
from ccya.state.momentum import MOMENTUM_MIN as _MOMENTUM_MIN, MOMENTUM_MAX as _MOMENTUM_MAX
from ccya.rules import MOMENTUM_DELTA as _RULES_MOMENTUM_DELTA

_defaults = EngineConfig()

# Scene pressure urgency escalation thresholds (turns since pressure was added)
PRESSURE_BUILDING_AT: int = _defaults.scene_pressure_building_at   # background → building
PRESSURE_IMMEDIATE_AT: int = _defaults.scene_pressure_immediate_at  # building → immediate
PRESSURE_MAX_AGE: int = _defaults.scene_pressure_max_age

URGENCY_LEVELS: tuple[str, ...] = ("background", "building", "immediate")

# Momentum
MOMENTUM_MIN: int = _MOMENTUM_MIN
MOMENTUM_MAX: int = _MOMENTUM_MAX
MOMENTUM_DELTA: dict[str, int] = dict(_RULES_MOMENTUM_DELTA)

# Extraction stream names — used in TurnAssert.stream validation
EXTRACT_STREAMS: tuple[str, ...] = (
    "rules",
    "extract.scene",
    "extract.state",
    "extract.progress",
    "extract",
    "state_yaml",
)

# Known TurnAssert.field values per stream — used by test_eval_schema.py
# to validate that scenario assertions reference real fields.
# Keep in sync with runner._check_asserts handler names.
KNOWN_ASSERT_FIELDS: dict[str, set[str]] = {
    "rules": {"rolled", "skill", "difficulty", "band", "intent_verb"},
    "extract.progress": {"quest_updates", "quest_status", "scene_pressure_add"},
    "extract.scene": {"scene_tags"},
    "extract.state": {"inventory_remove", "inventory_add", "pc_condition_add", "pc_condition_remove"},
    "extract": {"attempts:scene", "attempts:state", "skipped:scene", "skipped:state"},
    "state_yaml": {"pending_gm_beat.present", "pending_gm_beat.absent"},
}


def constants_block() -> str:
    """Return a markdown block of live engine constants for injection into judge traces.

    Called by build_trace() so the LLM judge always reasons from current values,
    not from whatever the rubric prose says.
    """
    return (
        "## Engine Constants (live — do not override with rubric prose)\n\n"
        f"- Scene pressure: background→building at turn age {PRESSURE_BUILDING_AT}, "
        f"building→immediate at turn age {PRESSURE_IMMEDIATE_AT}, "
        f"max age {PRESSURE_MAX_AGE}\n"
        f"- Urgency levels (ordered): {' → '.join(URGENCY_LEVELS)}\n"
        f"- Momentum range: [{MOMENTUM_MIN}, {MOMENTUM_MAX}]\n"
        f"- Momentum delta per band: {MOMENTUM_DELTA}\n\n"
    )


# Known seed_override dotpaths — used by test_eval_schema.py to validate
# scenario seed_overrides before running a full eval.
KNOWN_SEED_PATHS: frozenset[str] = frozenset((
    "meta.momentum",
    "scene.scene_pressure",
    "pc.conditions",
    "pc.credits",
))
