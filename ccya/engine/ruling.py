"""Ruling LLM call: prompt building, _call_ruling, retry logic."""

from __future__ import annotations

import logging
from jinja2 import Environment
from typing import Any

from ccya.engine.config import EngineConfig, _find_json, _log_llm_io, _PROMPTS_LOG_PATH, _render
from ccya.llm_client import chat as llm_chat, strip_thinking
from ccya.models import IntentEnvelope, RulesCheck, RulesOutcome

_log = logging.getLogger(__name__)


def _ruling_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    turn_no: int = 0,
    npc_roster: list[dict[str, Any]] | None = None,
    last_outcome: str | None = None,
    inventory: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    system_text = _render(env, "ruling_system.j2", {})
    user_text = _render(
        env,
        "ruling_user.j2",
        {
            "pc": pc,
            "location": location,
            "user_input": user_input,
            "meta": {"turn": turn_no},
            "npc_roster": npc_roster or [],
            "last_outcome": last_outcome,
            "inventory": inventory or [],
            "recent_turns": recent_turns or [],
        },
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


async def _call_ruling(
    messages: list[dict[str, Any]],
    config: EngineConfig,
    trace_id: str,
    turn: int = 0,
) -> tuple[IntentEnvelope, dict[str, int], str, str]:
    _no_intent = IntentEnvelope(
        intent="",
        intent_verb="act",
        check=RulesCheck(required=False),
    )
    _no_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    parse_error = ""

    _log.info(
        "ruling call start turn=%d messages=%d max_retries=%d",
        turn, len(messages), config.max_llm_retries,
        extra={"trace_id": trace_id, "turn": turn},
    )

    for attempt in range(1 + config.max_llm_retries):
        try:
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"ruling_request_attempt_{attempt}",
                    messages=messages,
                    max_chars=config.log_llm_io_max_chars,
                )
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.ruling_temperature,
                timeout=float(config.request_timeout_s),
            )
            raw = result.get("response", "") if isinstance(result, dict) else ""
            usage = result.get("usage", {}) if isinstance(result, dict) else _no_usage
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"ruling_response_attempt_{attempt}",
                    response=raw,
                    max_chars=config.log_llm_io_max_chars,
                )
            cleaned = strip_thinking(raw)
            j = _find_json(cleaned)
            if j is None:
                raise ValueError("No JSON found in ruling response")
            intent = IntentEnvelope(**j)
            if intent.check.required and not intent.check.skill:
                raise ValueError(f"check.required=true but check.skill is missing/empty (got {j.get('check', {}).get('skill', None)})")
            return intent, {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }, raw, ""
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "ruling parse failed (attempt %d/%d): %s",
                attempt + 1,
                1 + config.max_llm_retries,
                parse_error,
                extra={"trace_id": trace_id, "turn": turn},
            )

            if attempt < config.max_llm_retries:
                fb = (
                    f"Your previous output failed to parse: {parse_error[:200]}. "
                    "Re-emit the IntentEnvelope JSON only. No prose."
                )
                messages.append({"role": "user", "content": fb})

    _log.error(
        "ruling call failed after all attempts — defaulting to no-roll",
        extra={"trace_id": trace_id, "turn": turn},
    )
    return _no_intent, _no_usage, "", parse_error



def _log_ruling_outcome(
    turn: int, intent: "IntentEnvelope", outcome: "RulesOutcome"
) -> None:
    lines: list[str] = []
    lines.append(f"## Turn {turn} — ruling engine output")
    lines.append("")
    lines.append("--- [Intent] ---")
    lines.append(f"intent:        {intent.intent}")
    lines.append(f"intent_verb:   {intent.intent_verb}")
    lines.append(f"target:        {intent.target}")
    lines.append("")
    lines.append("--- [Dice Roll] ---")
    if outcome.rolled:
        lines.append("rolled:       True")
        lines.append(f"skill:        {outcome.skill}")
        lines.append(f"stat_value:   {outcome.stat_value}")
        lines.append(f"stat_mod:     {outcome.stat_mod}")
        lines.append(f"difficulty:   {outcome.difficulty}")
        lines.append(f"diff_mod:     {outcome.diff_mod}")
        lines.append(f"cond_mod:     {outcome.cond_mod}")
        lines.append(f"dice:         {outcome.dice}")
        lines.append(f"raw_total:    {outcome.raw_total}")
        lines.append(f"final_total:  {outcome.final_total}")
        lines.append(f"band:         {outcome.band}")
        lines.append(f"directive:    {outcome.directive}")
    else:
        lines.append("rolled:       False (no dice check required)")
    lines.append("")
    lines.append("---")
    lines.append("")

    try:
        with open(_PROMPTS_LOG_PATH, "a") as f:
            f.write("\n".join(lines))
    except OSError:
        _log.warning("failed to write prompts.log (ruling outcome)", exc_info=True)