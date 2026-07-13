from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "extraction_retry_rates", "deterministic",
    requires_fields=["extraction"],
    description="Track retry rates across all extraction steps (scene, state, record)",
    requires_all_events=True,
)
def extraction_retry_rates(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    total = 0
    retry_counts = {"scene": 0, "state": 0, "record": 0}
    retry_error_counts = {"scene": 0, "state": 0, "record": 0}

    for ev in events:
        extraction = extract_field(ev, "extraction") or {}
        turn = ev.get("turn")

        for stream in ("scene", "state", "record"):
            blob = extraction.get(stream) or {}
            if not blob or blob.get("skipped"):
                continue
            total += 1
            attempts = blob.get("attempts", 1)
            if attempts > 1:
                retry_counts[stream] += 1
                findings.append({
                    "turn": turn,
                    "stream": stream,
                    "check": "retry_rate",
                    "detail": f"{stream} required {attempts} attempts (retry)",
                })
                all_passed = False
            retry_errors = blob.get("retry_errors") or []
            if retry_errors:
                retry_error_counts[stream] += len(retry_errors)
                for err in retry_errors:
                    findings.append({
                        "turn": turn,
                        "stream": stream,
                        "check": "retry_error",
                        "detail": f"{stream} retry error: {err}",
                    })
                    all_passed = False

    detail_parts = []
    for stream in ("scene", "state", "record"):
        rate = retry_counts[stream] / total * 100 if total > 0 else 0
        detail_parts.append(f"{stream}: {retry_counts[stream]}/{total} retries ({rate:.1f}%), {retry_error_counts[stream]} errors")
    detail = "; ".join(detail_parts)

    if not all_passed:
        return CheckerResult(
            checker_id="extraction_retry_rates", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found — {detail}", findings=findings,
        )
    return CheckerResult(
        checker_id="extraction_retry_rates", passed=True, score=1.0,
        detail=f"all {total} extraction events passed — {detail}",
    )
