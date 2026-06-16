from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)

VALID_TENSION_DELTAS = {"escalates", "maintains", "de-escalates"}


@register_checker(
    "tension_delta", "deterministic",
    requires_fields=["ruling", "pacing_context"],
    description="Validate tension_delta field presence, values, and directive consistency",
)
def tension_delta(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for ev in filtered:
        ruling = extract_field(ev, "ruling") or {}
        pc = extract_field(ev, "pacing_context") or {}
        directive = pc.get("directive", "")

        # tension_delta was removed from ruling schema (convergence scoring Phase 2).
        # Skip events without it (new events); validate historical events that have it.
        td = ruling.get("tension_delta")
        if td is None:
            continue

        # Check valid values
        if td not in VALID_TENSION_DELTAS:
            findings.append({
                "turn": ev.get("turn"),
                "check": "tension_delta_valid",
                "detail": f"tension_delta={td!r} not in {VALID_TENSION_DELTAS}",
            })
            all_passed = False

        # Breathe directive consistency: de-escalates + no urgent threads → Breathe
        # If there are urgent threads, Scene Imperative/Pressure is valid even with de-escalates
        snap = extract_field(ev, "state_snapshot") or {}
        arc = snap.get("arc") or {}
        urgent_count = sum(1 for t in (arc.get("threads") or []) if isinstance(t, dict) and t.get("active") and t.get("urgency") == "urgent")
        if td == "de-escalates" and urgent_count == 0 and directive in ("Scene Imperative", "Scene Pressure"):
            findings.append({
                "turn": ev.get("turn"),
                "check": "breathe_consistency",
                "detail": f"tension_delta=de-escalates but directive={directive!r} (expected Breathe or empty)",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="tension_delta", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="tension_delta", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
