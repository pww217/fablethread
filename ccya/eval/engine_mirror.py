"""Read-only mirror of engine constants for use by eval scenarios and build_trace.

Import from here in scenarios — never hardcode thresholds or field names.
All values reflect current engine defaults. Where EngineConfig controls the
value at runtime, the default is used (eval runs use default EngineConfig
unless overridden in EvalConfig).
"""
from __future__ import annotations

from ccya.engine.config import EngineConfig
from ccya.state.delta import PC_CONDITIONS_MAX
from ccya.state.momentum import MOMENTUM_MIN as _MOMENTUM_MIN, MOMENTUM_MAX as _MOMENTUM_MAX
from ccya.rules import MOMENTUM_DELTA as _RULES_MOMENTUM_DELTA, VALID_SKILLS

_defaults = EngineConfig()

# Unified thread lifecycle rules (scope-aware, replaces urgency escalation thresholds)
THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE: bool = True        # scene-scoped threads expire when location changes
THREAD_ARC_DEMOTE_AGE: int = _defaults.thread_urgency_max_age  # arc-scoped threads demote active:True→False after this many turns without last_seen_turn update

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
SCENE_NAMED_NPC_CAP: int = 8  # see ccya/prompts/extract_scene_system.j2 "## NPC scene cap"
PC_CONDITION_CAP: int = PC_CONDITIONS_MAX

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
    "extract.progress": {"advanced_threads"},
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
        f"- Thread lifecycle: scene-scoped threads expire on location change; arc-scoped threads demote active→False after {THREAD_ARC_DEMOTE_AGE} turns idle\n"
        f"- Urgency levels (ordered): {' → '.join(URGENCY_LEVELS)}\n"
        f"- Momentum range: [{MOMENTUM_MIN}, {MOMENTUM_MAX}]\n"
        f"- Momentum delta per band: {MOMENTUM_DELTA}\n"
        f"- Bands (ordered worst→best): {', '.join(BANDS)}\n"
        f"- Skills: {', '.join(SKILLS)}\n"
        f"- Difficulties (ordered): {', '.join(DIFFICULTIES)}\n"
        f"- Intent verb hints: {', '.join(INTENT_VERBS_HINT)}\n"
        f"- PC condition cap: {PC_CONDITION_CAP}\n"
        f"- Scene named NPC cap: {SCENE_NAMED_NPC_CAP}\n\n"
    )


# Known seed_override dotpaths — used by test_eval_schema.py to validate
# scenario seed_overrides before running a full eval.
KNOWN_SEED_PATHS: frozenset[str] = frozenset((
    "meta.momentum",
    "arc.threads",
    "pc.conditions",
    "pc.credits",
))
