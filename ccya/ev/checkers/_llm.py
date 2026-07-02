"""Shared utilities for LLM-based checkers.

Handles prompt rendering and structured output parsing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult


_log = logging.getLogger(__name__)


def _call_llm_checker(
    system_prompt: str,
    user_prompt: str,
    config: EngineConfig,
) -> dict[str, Any]:
    """Call the checker LLM via remote client and parse its structured output.

    1. Call llm_chat with system + user prompt via remote Ollama client
    2. Try to parse response as JSON
    3. If parsing fails, retry once with "Return ONLY JSON" instruction
    4. If parsing still fails, return {"error": "parse_failed", "raw": response}
    5. Return parsed dict

    The LLM is instructed to return a JSON object with keys:
    {"passed": bool, "score": float, "reasoning": str, "findings": list[dict]}
    """
    try:
        from ccya.llm_client import chat as llm_chat
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                llm_chat(
                    config.host,
                    config.model,
                    messages,
                    fallback_host=config.fallback_host,
                    fallback_model=config.fallback_model,
                    fallback_cooldown_s=config.fallback_cooldown_s,
                    temperature=0.3,
                    timeout=float(config.request_timeout_s),
                    num_ctx=config.num_ctx,
                ),
            )
        finally:
            loop.close()
        raw = response.content
        parsed = _try_parse_json(raw)
        if parsed is None:
            # Retry once with explicit "ONLY JSON" instruction
            retry_messages = messages + [
                {"role": "system", "content": "CRITICAL: Return ONLY a valid JSON object. No markdown, no explanation, no other text. Start with { and end with }."}
            ]
            try:
                retry_response = loop.run_until_complete(
                    llm_chat(
                        config.host,
                        config.model,
                        retry_messages,
                        fallback_host=config.fallback_host,
                        fallback_model=config.fallback_model,
                        fallback_cooldown_s=config.fallback_cooldown_s,
                        temperature=0.1,
                        timeout=float(config.request_timeout_s),
                        num_ctx=config.num_ctx,
                    ),
                )
                retry_raw = retry_response.content
                parsed = _try_parse_json(retry_raw)
                if parsed is not None:
                    return parsed
            except Exception:
                pass
            return {"error": "parse_failed", "raw": raw}
        return parsed
    except Exception as exc:
        _log.warning("LLM checker call failed: %s", exc)
        return {"error": "call_failed", "detail": str(exc)}


def _try_parse_json(raw: str) -> dict[str, Any] | None:
    """Try to parse a JSON object from LLM response text."""
    s = raw.strip()
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, ValueError):
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = json.loads(s[i: j + 1])
                return out if isinstance(out, dict) else None
            except (json.JSONDecodeError, ValueError):
                return None
    return None


def _result_from_llm_output(checker_id: str, llm_output: dict[str, Any]) -> CheckerResult:
    """Convert LLM output dict to CheckerResult."""
    if "error" in llm_output:
        return CheckerResult(
            checker_id=checker_id,
            passed=None,
            score=None,
            detail=f"LLM parse/call error: {llm_output['error']}",
        )

    passed = llm_output.get("passed")
    score = llm_output.get("score")
    reasoning = llm_output.get("reasoning", "")
    findings = llm_output.get("findings", [])
    finding = llm_output.get("finding", "")

    if finding and not findings:
        findings = [{"finding": finding}]

    return CheckerResult(
        checker_id=checker_id,
        passed=passed,
        score=score,
        detail=reasoning,
        findings=findings,
    )


# Template registry for checker prompts
_PROMPT_TEMPLATES: dict[str, tuple[str, str]] = {}


def register_prompt_template(checker_id: str, system_template: str, user_template: str) -> None:
    """Register a prompt template pair for a checker."""
    _PROMPT_TEMPLATES[checker_id] = (system_template, user_template)


def _build_checker_prompt(checker_id: str, events: list[dict[str, Any]]) -> tuple[str, str]:
    """Build system and user prompts for a checker.
    Uses a template registry: {checker_id: (system_template, user_template)}.
    Renders templates with event data.
    """
    templates = _PROMPT_TEMPLATES.get(checker_id)
    if not templates:
        return ("", "")
    system_template, user_template = templates
    # Render templates with event data
    system_prompt = system_template
    user_parts = []
    for ev in events:
        user_parts.append(user_template.format(**ev))
    user_prompt = "\n\n---\n\n".join(user_parts)
    return system_prompt, user_prompt
