from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "arc_resolution_validity", "deterministic",
    requires_fields=["extraction.record", "last_turn_state"],
    description="arc_resolve has resolution + long_term_objective",
    needs_non_turn_events=True,
)
def arc_resolution_validity(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        record_output = ((extract_field(ev, "extraction") or {}).get("record") or {}).get("output") or {}
        arc_resolve = record_output.get("arc_resolve")

        if not isinstance(arc_resolve, dict):
            continue

        # Skip empty arc_resolves (LLM sometimes emits empty dict)
        resolution = arc_resolve.get("resolution")
        if not resolution or not isinstance(resolution, str) or not resolution.strip():
            continue
        if not resolution or not isinstance(resolution, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "arc_resolve_has_resolution",
                "detail": "arc_resolve missing or invalid resolution",
            })
            all_passed = False

        long_term_objective = arc_resolve.get("long_term_objective")
        if not long_term_objective or not isinstance(long_term_objective, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "arc_resolve_has_long_term_objective",
                "detail": "arc_resolve missing or invalid long_term_objective",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="arc_resolution_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="arc_resolution_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
