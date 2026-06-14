from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.engine._pacing import BEAT_PHASE_MAP

_log = logging.getLogger(__name__)


@register_checker(
    "beat_phase_validity", "deterministic",
    requires_fields=["extraction.storytell", "pacing_context"],
    description="gm_beat.type is allowed for the current phase",
)
def beat_phase_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        gm_beat = storytell_output.get("gm_beat")

        if not isinstance(gm_beat, dict) or not gm_beat.get("type"):
            continue

        beat_type = gm_beat["type"]
        # breathing_room is an enforce_relief override, not a storyteller choice — always allowed
        if beat_type == "breathing_room":
            continue

        pacing_ctx = extract_field(ev, "pacing_context") or {}
        scene_phase = pacing_ctx.get("scene_phase", "SETUP")

        allowed: list[str] = BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))
        if beat_type not in allowed:
            findings.append({
                "turn": ev.get("turn"),
                "check": "beat_type_allowed",
                "detail": f"beat type '{beat_type}' not allowed in phase '{scene_phase}' (allowed: {sorted(allowed)})",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="beat_phase_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="beat_phase_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
