"""LLM-based narrative checkers.

Each checker evaluates narrative quality aspects that deterministic checkers
cannot catch: tone alignment, beat consequences, state fidelity.
"""

from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.checkers._llm import _PROMPT_TEMPLATES, _call_llm_checker, _result_from_llm_output, register_prompt_template
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# directive_tone_match
# ---------------------------------------------------------------------------

register_prompt_template(
    "directive_tone_match",
    """You are evaluating a narration's tone alignment with the game rules directive.
Given the ruling (band, intent) and the narration text, determine if the
narration's tone appropriately reflects the roll outcome.

A SUCCESS band should have confident, positive narration.
A FAIL band should have tense, setback-oriented narration.
A CRIT_FAIL should have severe consequence narration.
Scene tags may modify the expected tone (e.g., "tense_confrontation" raises stakes).

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "finding": str}""",
    """Ruling:
  Band: {band}
  Intent: {intent}

Narration:
{narrate}""",
)


@register_checker(
    "directive_tone_match", "llm",
    requires_fields=["ruling.band", "ruling.intent", "narrate"],
    description="Does narration tone match the rules directive? (per-turn LLM call)",
)
def directive_tone_match(events: list[dict[str, Any]]) -> CheckerResult:
    if not events:
        return CheckerResult(
            checker_id="directive_tone_match", passed=None, score=None,
            detail="No events to evaluate",
        )

    ev = events[0]
    ruling = extract_field(ev, "ruling") or {}
    band = ruling.get("band", "")
    intent = ruling.get("intent", "")
    narrate = extract_field(ev, "narrate") or ""

    user_prompt = f"""Ruling:
  Band: {band}
  Intent: {intent}

Narration:
{narrate}"""

    system_prompt = _PROMPT_TEMPLATES["directive_tone_match"][0]
    llm_output = _call_llm_checker(system_prompt, user_prompt, config=_get_config())
    return _result_from_llm_output("directive_tone_match", llm_output)


# ---------------------------------------------------------------------------
# beat_narrative_chain
# ---------------------------------------------------------------------------

register_prompt_template(
    "beat_narrative_chain",
    """You are evaluating whether a GM beat's narrative consequence matches its
declared type. Given:
1. The GM beat type (pressure, escalation, complication, etc.)
2. The beat's surface_as (ambient, environmental, etc.)
3. The narration text where the beat was generated
4. The narration text of the following turn

Determine if the narrative consequence plausibly follows from the beat type.
A "pressure" beat should create urgency. A "complication" should introduce
an obstacle. An "escalation" should raise existing stakes. An "ambient"
beat need not produce specific consequences.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "finding": str}""",
    """GM Beat:
  Type: {beat_type}
  Surface: {surface_as}

Narration where beat was generated:
{beat_narrate}

Narration of following turn:
{next_narrate}""",
)


@register_checker(
    "beat_narrative_chain", "llm",
    requires_fields=["state_snapshot.meta.pending_gm_beat", "narrate"],
    description="Does the GM beat produce observable narrative consequence?",
)
def beat_narrative_chain(events: list[dict[str, Any]]) -> CheckerResult:
    if not events:
        return CheckerResult(
            checker_id="beat_narrative_chain", passed=None, score=None,
            detail="No events to evaluate",
        )

    ev = events[0]
    state_snapshot = extract_field(ev, "state_snapshot") or {}
    meta = state_snapshot.get("meta", {})
    pending_beat = meta.get("pending_gm_beat") or {}
    beat_type = pending_beat.get("type", "")
    surface_as = pending_beat.get("surface_as", "ambient")
    narrate = extract_field(ev, "narrate") or ""

    # Look for next turn's narration if available
    next_narrate = ""
    if len(events) > 1:
        next_narrate = extract_field(events[1], "narrate") or ""

    user_prompt = f"""GM Beat:
  Type: {beat_type}
  Surface: {surface_as}

Narration where beat was generated:
{narrate}"""

    if next_narrate:
        user_prompt += f"""

Narration of following turn:
{next_narrate}"""

    system_prompt = _PROMPT_TEMPLATES["beat_narrative_chain"][0]
    llm_output = _call_llm_checker(system_prompt, user_prompt, config=_get_config())
    return _result_from_llm_output("beat_narrative_chain", llm_output)


# ---------------------------------------------------------------------------
# state_fidelity
# ---------------------------------------------------------------------------

register_prompt_template(
    "state_fidelity",
    """You are evaluating whether the extraction (state changes) correctly reflects
the narration. Given:
1. The narration text
2. The inventory changes (add/remove)
3. The condition changes (add/remove)

Determine if the state changes are supported by the narration. The narration
must explicitly mention or strongly imply each state change. Missing changes
that the narration describes are failures. Extra changes not supported by
narration are also failures.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "findings": [{"field": str, "issue": str}]}""",
    """Narration:
{narrate}

Inventory added:
{inventory_add}

Inventory removed:
{inventory_remove}

Conditions added:
{condition_add}

Conditions removed:
{condition_remove}""",
)


@register_checker(
    "state_fidelity", "llm",
    requires_fields=["narrate", "extraction_context",
                     "applied.inventory_add", "applied.inventory_remove",
                     "applied.pc_condition_add", "applied.pc_condition_remove"],
    description="Does extraction match what narration describes?",
)
def state_fidelity(events: list[dict[str, Any]]) -> CheckerResult:
    if not events:
        return CheckerResult(
            checker_id="state_fidelity", passed=None, score=None,
            detail="No events to evaluate",
        )

    ev = events[0]
    narrate = extract_field(ev, "narrate") or ""
    applied = extract_field(ev, "applied") or {}

    inventory_add = applied.get("inventory_add") or []
    inventory_remove = applied.get("inventory_remove") or []
    condition_add = applied.get("pc_condition_add") or []
    condition_remove = applied.get("pc_condition_remove") or []

    user_prompt = f"""Narration:
{narrate}

Inventory added:
{inventory_add}

Inventory removed:
{inventory_remove}

Conditions added:
{condition_add}

Conditions removed:
{condition_remove}"""

    system_prompt = _PROMPT_TEMPLATES["state_fidelity"][0]
    llm_output = _call_llm_checker(system_prompt, user_prompt, config=_get_config())
    return _result_from_llm_output("state_fidelity", llm_output)


# ---------------------------------------------------------------------------
# Config accessor
# ---------------------------------------------------------------------------

_engine_config: EngineConfig | None = None


def _get_config() -> EngineConfig:
    """Get the engine config for LLM checker calls.

    This is a module-level singleton that gets set by the check command
    before running LLM checkers.
    """
    global _engine_config
    if _engine_config is None:
        _engine_config = EngineConfig()
    return _engine_config


def set_checker_config(config: EngineConfig) -> None:
    """Set the engine config for LLM checker calls."""
    global _engine_config
    _engine_config = config
