"""Read-only mirror of engine constants for use by eval scenarios and build_trace.

Import from here in scenarios — never hardcode thresholds or field names.
All values reflect current engine defaults. Where EngineConfig controls the
value at runtime, the default is used (eval runs use default EngineConfig
unless overridden in EvalConfig).
"""
from __future__ import annotations

import logging
import typing as _typing

from ccya.engine.config import EngineConfig
from ccya.engine.turn import PRESSURE_BEAT_TYPES as _PRESSURE_BEAT_TYPES
from ccya.models import ArcThread, GMBeat
from ccya.state.delta_builder import PC_CONDITIONS_MAX, DEFAULT_CONDITION_TTL
from ccya.state.momentum import MOMENTUM_MIN as _MOMENTUM_MIN, MOMENTUM_MAX as _MOMENTUM_MAX
from ccya.rules import MOMENTUM_DELTA as _RULES_MOMENTUM_DELTA, VALID_SKILLS

_log = logging.getLogger(__name__)

_defaults = EngineConfig()

# Thread TTL defaults — imported from EngineConfig to prevent drift
THREAD_RESOLVED_ARC_TTL: int = _defaults.arc_memory_ttl
THREAD_COMPLETED_THREAD_TTL: int = _defaults.thread_memory_ttl

# For trace injection into judge prompts — maps from ArcThread.urgency values (background/normal/urgent)
URGENCY_LEVELS: tuple[str, ...] = ("background", "normal", "urgent")

# Validate URGENCY_LEVELS stays in sync with ArcThread urgency Literal annotation
_urgency_annotation = ArcThread.model_fields['urgency'].annotation  # Pydantic v2 — Literal["background", "normal", "urgent"]
_urgency_args: tuple[str, ...] = _urgency_annotation.__args__ if hasattr(_urgency_annotation, '__args__') else ()  # type: ignore[union-attr]
assert set(URGENCY_LEVELS) == set(_urgency_args), f"URGENCY_LEVELS mismatch: {URGENCY_LEVELS} vs {_urgency_args}"

# Momentum
MOMENTUM_MIN: int = _MOMENTUM_MIN
MOMENTUM_MAX: int = _MOMENTUM_MAX
MOMENTUM_DELTA: dict[str, int] = dict(_RULES_MOMENTUM_DELTA)

# Schema constants — sourced from production code so the rubric stays in sync
BANDS: tuple[str, ...] = ("crit_fail", "fail", "setback", "partial", "success", "crit_success")
SKILLS: tuple[str, ...] = tuple(VALID_SKILLS)
DIFFICULTIES: tuple[str, ...] = ("trivial", "easy", "normal", "hard", "extreme")
INTENT_VERBS_HINT: tuple[str, ...] = (
    "attack", "persuade", "sneak", "hack", "deceive", "intimidate",
    "climb", "repair", "recall", "escape", "negotiate",
)
PC_CONDITION_CAP: int = PC_CONDITIONS_MAX
CONDITION_TTL: int = DEFAULT_CONDITION_TTL

# Extraction stream names — used in TurnAssert.stream validation
EXTRACT_STREAMS: tuple[str, ...] = (
    "ruling",
    "extract.state",
    "storytell.extract",
    "extract",
    "state_yaml",
)

# Known TurnAssert.field values per stream — used by test_eval_schema.py
# to validate that scenario assertions reference real fields.
# Keep in sync with runner._check_asserts handler names.
KNOWN_ASSERT_FIELDS: dict[str, set[str]] = {
    "ruling": {"rolled", "skill", "difficulty", "band", "intent_verb"},
    "storytell.extract": {"thread_update", "arc_resolve", "thread_resolve", "thread_add", "goal_update"},
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
        f"- Thread lifecycle: storyteller-managed via thread_update directives; TTL-based cleanup for resolved_arcs ({THREAD_RESOLVED_ARC_TTL} turns) and completed_threads ({THREAD_COMPLETED_THREAD_TTL} turns)\n"
        f"- Urgency levels (ordered): {' → '.join(URGENCY_LEVELS)}\n"
        f"- Momentum range: [{MOMENTUM_MIN}, {MOMENTUM_MAX}], delta per band: {dict(MOMENTUM_DELTA)}, floor={_defaults.momentum_floor}\n"
        f"- Bands (ordered worst→best): {', '.join(BANDS)}\n"
        f"- Skills: {', '.join(SKILLS)}\n"
        f"- Difficulties (ordered): {', '.join(DIFFICULTIES)}\n"
        f"- Intent verb hints: {', '.join(INTENT_VERBS_HINT)}\n"
        f"- PC condition cap: {PC_CONDITION_CAP}\n"
        f"- Consecutive pressure threshold (relief trigger): {CONSECUTIVE_PRESSURE_THRESHOLD} turns\n"
        f"- Consecutive pressure counter tracks storyteller gm_beat types: pressure/escalation/complication (not directives)\n"
        f"- GM beat type validation: {', '.join(GM_BEAT_TYPES)}\n"
        f"- Pressure beat types (counter-incrementing): {', '.join(PRESSURE_BEAT_TYPES)}\n"
        f"- Beat TTL: storyteller-emitted = {BEAT_TTL} turns; floor-relief breathing_room = {FLOOR_RELIEF_BEAT_TTL} turns\n"
        f"- Floor relief: injects breathing_room when beat_locked=True and pending_gm_beat is None or a pressure type\n"
        f"- goal_update: storyteller field that directly overwrites arc.visible_goal (mid-arc goal change, separate from arc_resolve)\n"
        f"- Combat scene effective age boost: +2 to scene_age for directive thresholds when 'combat' in scene tags\n\n"
    )


# Beat types that increment the consecutive_pressure counter (imported from turn.py)
PRESSURE_BEAT_TYPES: tuple[str, ...] = _PRESSURE_BEAT_TYPES

# All valid GM beat types — derived from GMBeat.type Literal annotation at runtime
_GM_Beat_annotation = GMBeat.model_fields['type'].annotation  # Pydantic v2 — Literal[...] | None
_GM_Beat_args: tuple[str, ...] = (
    _GM_Beat_annotation.__args__ if hasattr(_GM_Beat_annotation, '__args__') else ()  # type: ignore[union-attr]
)
# Extract string values from the Literal wrapper, filtering out NoneType
_literal_type = next((t for t in _GM_Beat_args if _typing.get_origin(t) is not None), None)  # pyright: ignore[reportUnknownVariableType]
assert _literal_type is not None, "GMBeat.type should always have a Literal annotation"
# After assert, mypy knows _literal_type is the Literal type — but still doesn't know it has __args__
GM_BEAT_TYPES: tuple[str, ...] = _typing.get_args(_literal_type)  # pyright: ignore[reportUnknownArgumentType]

# Beat lifecycle TTLs (turns) — hardcoded because no EngineConfig fields exist yet
BEAT_TTL: int = 2               # Storyteller-emitted beats expire after 2 turns (turn_no + 2)
FLOOR_RELIEF_BEAT_TTL: int = 3  # Floor-relief breathing_room beats expire after 3 turns (turn_no + 3)

# Config defaults exposed for universal asserts
CONSECUTIVE_PRESSURE_THRESHOLD: int = _defaults.consecutive_pressure_threshold
MOMENTUM_FLOOR: int = _defaults.momentum_floor

# Known seed_override dotpaths — used by test_eval_schema.py to validate
# scenario seed_overrides before running a full eval.
KNOWN_SEED_PATHS: frozenset[str] = frozenset((
    "meta.momentum",
    "arc.threads",
    "pc.conditions",
    "pc.credits",
))

_log.debug("engine_mirror initialized: MOMENTUM_RANGE=[%d,%d] CAPS=(thread=N/A,condition=%d) STREAMS=%d",
            MOMENTUM_MIN, MOMENTUM_MAX, PC_CONDITION_CAP, len(EXTRACT_STREAMS))
