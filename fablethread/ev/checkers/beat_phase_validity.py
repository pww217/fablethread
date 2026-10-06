from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field
from fablethread.engine._pacing import derive_allowed_beat_types

_log = logging.getLogger(__name__)


@register_checker(
    "beat_phase_validity", "deterministic",
    requires_fields=["ruling", "pacing_context"],
    description="selected beat type is allowed for the current phase",
)
def beat_phase_validity(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        ruling = extract_field(ev, "ruling") or {}
        selected_beat_idx = ruling.get("selected_beat")

        if not isinstance(selected_beat_idx, int):
            continue

        # Get beat candidates from state.meta or pacing_context
        last_state = ev.get("last_turn_state") or {}
        meta = last_state.get("meta") or {}
        beat_candidates = meta.get("beat_candidates") or []

        if not isinstance(beat_candidates, list) or selected_beat_idx >= len(beat_candidates):
            continue

        beat = beat_candidates[selected_beat_idx]
        if not isinstance(beat, dict) or not beat.get("type"):
            continue

        beat_type = beat["type"]

        pacing_ctx = extract_field(ev, "pacing_context") or {}
        scene_phase = pacing_ctx.get("scene_phase", "SETUP")

        allowed: list[str] = derive_allowed_beat_types(
            scene_phase,
            directive=pacing_ctx.get("directive", ""),
        )
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
