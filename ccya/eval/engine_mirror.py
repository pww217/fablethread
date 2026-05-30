"""Read-only mirror of engine constants for use by eval scenarios and build_trace.

Import from here in scenarios — never hardcode thresholds or field names.
All values reflect current engine defaults. Where EngineConfig controls the
value at runtime, the default is used (eval runs use default EngineConfig
unless overridden in EvalConfig).
"""
from __future__ import annotations

import logging

from ccya.engine.config import EngineConfig
from ccya.state.delta_builder import PC_CONDITIONS_MAX
from ccya.state.momentum import MOMENTUM_MIN as _MOMENTUM_MIN, MOMENTUM_MAX as _MOMENTUM_MAX
from ccya.rules import MOMENTUM_DELTA as _RULES_MOMENTUM_DELTA, VALID_SKILLS

_log = logging.getLogger(__name__)

_defaults = EngineConfig()

# Thread TTL defaults (matches config defaults)
THREAD_RESOLVED_ARC_TTL: int = 3
THREAD_COMPLETED_THREAD_TTL: int = 3

# For trace injection into judge prompts — maps from ArcThread.urgency values (background/normal/urgent)
URGENCY_LEVELS: tuple[str, ...] = ("background", "normal", "urgent")

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
SCENE_NAMED_NPC_CAP: int = 10  # see ccya/prompts/extract_scene_system.j2 "## NPC scene cap"
PC_CONDITION_CAP: int = PC_CONDITIONS_MAX

# Extraction stream names — used in TurnAssert.stream validation
EXTRACT_STREAMS: tuple[str, ...] = (
    "ruling",
    "extract.scene",
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
    "storytell.extract": {"thread_update", "arc_resolve", "thread_resolve", "thread_add"},
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
        f"- Thread lifecycle: storyteller-managed via thread_update directives; TTL-based cleanup for resolved_arcs ({THREAD_RESOLVED_ARC_TTL} turns) and completed_threads ({THREAD_COMPLETED_THREAD_TTL} turns)\n"
        f"- Urgency levels (ordered): {' → '.join(URGENCY_LEVELS)}\n"
        f"- Momentum range: [{MOMENTUM_MIN}, {MOMENTUM_MAX}], delta per band: {dict(MOMENTUM_DELTA)}, floor={_defaults.momentum_floor}\n"
        f"- Bands (ordered worst→best): {', '.join(BANDS)}\n"
        f"- Skills: {', '.join(SKILLS)}\n"
        f"- Difficulties (ordered): {', '.join(DIFFICULTIES)}\n"
        f"- Intent verb hints: {', '.join(INTENT_VERBS_HINT)}\n"
        f"- PC condition cap: {PC_CONDITION_CAP}\n"
        f"- Scene named NPC cap: {SCENE_NAMED_NPC_CAP}\n"
        f"- Consecutive pressure threshold (relief trigger): {_defaults.consecutive_pressure_threshold} turns\n"
        f"- Combat scene effective age boost: +2 to scene_age for directive thresholds when 'combat' in scene tags\n\n"
    )


# Known seed_override dotpaths — used by test_eval_schema.py to validate
# scenario seed_overrides before running a full eval.
KNOWN_SEED_PATHS: frozenset[str] = frozenset((
    "meta.momentum",
    "arc.threads",
    "pc.conditions",
    "pc.credits",
))

_log.debug("engine_mirror initialized: MOMENTUM_RANGE=[%d,%d] CAPS=(thread=N/A,condition=%d,npc=%d) STREAMS=%d",
            MOMENTUM_MIN, MOMENTUM_MAX, PC_CONDITION_CAP, SCENE_NAMED_NPC_CAP, len(EXTRACT_STREAMS))
