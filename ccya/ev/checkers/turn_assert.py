from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.scenario import TurnAssert

_log = logging.getLogger(__name__)

STREAM_MAP: dict[str, str] = {
    "ruling": "ruling",
    "extract.state": "applied",
    "extraction_context": "extraction_context",
}


def _get_assert_field(a: Any, name: str, default: Any = None) -> Any:
    if isinstance(a, dict):
        return a.get(name, default)
    return getattr(a, name, default)


@register_checker(
    "turn_assert", "deterministic",
    requires_fields=[],
    description="Validate per-turn structured assertions (stream/field/expected)",
)
def turn_assert(events: list[dict[str, Any]], asserts: list[TurnAssert] | None = None) -> CheckerResult:
    if not asserts:
        _log.debug("turn_assert: no assertions to check")
        return CheckerResult(
            checker_id="turn_assert",
            passed=True,
            score=1.0,
            detail="no assertions to check",
        )

    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        for a in asserts:
            stream: str = _get_assert_field(a, "stream", "")
            field: str = _get_assert_field(a, "field", "")
            expected = _get_assert_field(a, "expected")
            min_amount = _get_assert_field(a, "min_amount")

            event_key = STREAM_MAP.get(stream)
            if event_key is None:
                findings.append({
                    "finding": f"unknown_stream:{stream}",
                    "field": field,
                    "stream": stream,
                    "detail": f"Unknown stream '{stream}', expected one of: {', '.join(STREAM_MAP)}",
                })
                all_passed = False
                continue

            section = ev.get(event_key, {})
            if not isinstance(section, dict):
                section = {}

            parts = field.split(".")
            cur: Any = section
            for part in parts:
                if isinstance(cur, dict):
                    cur = cur.get(part)
                else:
                    cur = None
                    break

            actual = cur
            passed = True
            detail_parts: list[str] = []

            if expected is not None:
                str_actual = str(actual) if actual is not None else ""
                if str_actual != expected:
                    passed = False
                    detail_parts.append(f"expected={expected!r}, got={str_actual!r}")

            if min_amount is not None:
                try:
                    num_actual = int(actual) if actual is not None else 0
                except (TypeError, ValueError):
                    num_actual = 0
                if num_actual < min_amount:
                    passed = False
                    detail_parts.append(f"expected >= {min_amount}, got={num_actual}")

            if not passed:
                all_passed = False

            detail = "; ".join(detail_parts) if detail_parts else "ok"
            findings.append({
                "finding": f"{stream}.{field}",
                "stream": stream,
                "field": field,
                "expected": expected,
                "actual": actual,
                "detail": detail,
            })

    passed_count = sum(1 for f in findings if f["detail"] == "ok")
    total = len(findings)
    score = passed_count / total if total > 0 else 1.0

    _log.debug("turn_assert: %d/%d assertions passed, score=%.2f", passed_count, total, score)
    return CheckerResult(
        checker_id="turn_assert",
        passed=all_passed,
        score=score,
        detail=f"{passed_count}/{total} assertions passed",
        findings=findings,
    )
