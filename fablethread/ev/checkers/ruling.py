from __future__ import annotations

import logging
import re
from typing import Any

from fablethread.engine.config import EngineConfig
from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.checkers._llm import _PROMPT_TEMPLATES, _call_llm_checker, _result_from_llm_output, register_prompt_template
from fablethread.ev.checkers.llm_checkers import _get_config
from fablethread.ev.events import extract_field

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ruling_reason_quality
# ---------------------------------------------------------------------------

@register_checker(
    "ruling_reason_quality", "deterministic",
    requires_fields=["ruling"],
    description="Verify ruling.reason is non-empty and substantive",
)
def ruling_reason_quality(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue

        reason = ruling.get("reason", "") or ""

        if not reason.strip():
            findings.append({
                "turn": ev.get("turn"),
                "check": "reason_non_empty",
                "detail": "ruling.reason is empty",
            })
            all_passed = False
            continue

        has_structured = bool(re.match(r"^(trivial|easy|normal|hard|extreme)\s*;\s*\S", reason, re.IGNORECASE))
        if not has_structured:
            findings.append({
                "turn": ev.get("turn"),
                "check": "reason_format",
                "detail": f"ruling.reason must be structured [difficulty]; [condition/inventory]: {reason!r}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="ruling_reason_quality", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="ruling_reason_quality", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )


# ---------------------------------------------------------------------------
# ruling_band_distribution
# ---------------------------------------------------------------------------

@register_checker(
    "ruling_band_distribution", "deterministic",
    requires_fields=["ruling"],
    description="Detect skewed dice band distribution over a session",
)
def ruling_band_distribution(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    cfg = EngineConfig().checkers
    band_skew_ratio = cfg.band_skew_ratio

    # Skip if threshold >= 1.0 (effectively disabled)
    if band_skew_ratio >= 1.0:
        return CheckerResult(
            checker_id="ruling_band_distribution", passed=True, score=1.0,
            detail="band_skew_ratio >= 1.0, check disabled",
        )

    band_counts: dict[str, int] = {}
    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue
        band = ruling.get("band")
        if band:
            band_counts[band] = band_counts.get(band, 0) + 1

    if not band_counts:
        return CheckerResult(
            checker_id="ruling_band_distribution", passed=True, score=1.0,
            detail="No rolled dice found",
        )

    total = sum(band_counts.values())
    findings: list[dict[str, Any]] = []

    for band, count in band_counts.items():
        ratio = count / total if total > 0 else 0
        if ratio > band_skew_ratio:
            findings.append({
                "check": "band_skew",
                "detail": f"band {band!r} has {count}/{total} = {ratio:.1%} of rolls (threshold: {band_skew_ratio:.1%})",
            })

    if findings:
        return CheckerResult(
            checker_id="ruling_band_distribution", passed=False, score=0.0,
            detail=f"{len(findings)} skewed band(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="ruling_band_distribution", passed=True, score=1.0,
        detail=f"band distribution OK across {total} rolls",
    )


# ---------------------------------------------------------------------------
# ruling_intent_match
# ---------------------------------------------------------------------------

register_prompt_template(
    "ruling_intent_match",
    """You are evaluating whether a ruling's 'impossible' classification
matches the player's stated intent. The GM classified the action as
'impossible: true' or 'impossible: false'. Determine if this classification
is correct based on the player's input.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "findings": [{"turn": int, "issue": str}]}""",
    """Turn {turn}:
Intent: {intent}
Impossible: {impossible}
Reason: {reason}
Player input: {player_input}""",
)


@register_checker(
    "ruling_intent_match", "llm",
    requires_fields=["ruling.intent", "ruling.impossible", "ruling.reason"],
    description="LLM check if 'impossible' flag matches player intent semantics",
)
def ruling_intent_match(events: list[dict[str, Any]], *, config: EngineConfig | None = None) -> CheckerResult:
    if not events:
        return CheckerResult(
            checker_id="ruling_intent_match", passed=None, score=None,
            detail="No events to evaluate",
        )

    system_prompt, user_template = _PROMPT_TEMPLATES["ruling_intent_match"]

    user_parts: list[str] = []
    for ev in events:
        ruling = extract_field(ev, "ruling") or {}
        intent = ruling.get("intent", "")
        impossible = ruling.get("impossible", False)
        reason = ruling.get("reason", "") or ""
        player_input = ruling.get("player_input", "") or ""

        user_parts.append(user_template.format(
            turn=ev.get("turn", 0),
            intent=intent,
            impossible=impossible,
            reason=reason,
            player_input=player_input,
        ))

    user_prompt = "\n\n---\n\n".join(user_parts)

    llm_output = _call_llm_checker(system_prompt, user_prompt, config=_get_config(config))
    return _result_from_llm_output("ruling_intent_match", llm_output)
