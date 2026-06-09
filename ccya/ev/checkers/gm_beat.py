from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.engine.turn import PRESSURE_BEAT_TYPES

_log = logging.getLogger(__name__)

MOMENTUM_FLOOR = -3


@register_checker(
    "gm_beat_lifecycle", "deterministic",
    requires_fields=["state_snapshot", "momentum_before", "momentum_after",
                     "ruling", "narrate_prompt"],
    description="Verify pending_gm_beat is consumed, floor relief injected, binding present on roll",
)
def gm_beat_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for i, ev in enumerate(events):
        prev_ev = events[i - 1] if i > 0 else None

        snap = extract_field(ev, "state_snapshot") or {}
        prev_snap = extract_field(prev_ev, "state_snapshot") or {} if prev_ev else {}

        cur_beat = (snap.get("meta") or {}).get("pending_gm_beat")
        prev_beat = (prev_snap.get("meta") or {}).get("pending_gm_beat") if prev_snap else None

        # pending_gm_beat consumed
        if prev_beat is not None and cur_beat == prev_beat:
            findings.append({
                "turn": ev.get("turn"),
                "check": "beat_consumed",
                "detail": f"beat persisted unchanged across turns: {prev_beat}",
            })
            all_passed = False

        # pending_gm_beat lifecycle respected
        extraction = extract_field(ev, "extraction") or {}
        storytell = extraction.get("storytell") or {}
        storytell_gm_beat = storytell.get("gm_beat")

        if storytell_gm_beat and isinstance(storytell_gm_beat, dict) and storytell_gm_beat.get("type"):
            if cur_beat is None:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "beat_lifecycle",
                    "detail": f"new gm_beat emitted but pending_gm_beat is None in state: {storytell_gm_beat.get('type')}",
                })
                all_passed = False
            elif cur_beat.get("type") != storytell_gm_beat.get("type"):
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "beat_lifecycle",
                    "detail": f"new gm_beat type mismatch: storytell={storytell_gm_beat.get('type')}, state={cur_beat.get('type')}",
                })
                all_passed = False

        # floor_relief_injection
        pacing_ctx = extract_field(ev, "pacing_context") or {}
        beat_locked = bool(pacing_ctx.get("beat_locked", False))

        storytell_output = storytell.get("output") or {}
        storytell_gm_beat_out = storytell_output.get("gm_beat")
        storytell_type = storytell_gm_beat_out.get("type") if isinstance(storytell_gm_beat_out, dict) else None

        cur_beat_post = extract_field(ev, "post_turn_pending_beat") or (snap.get("meta") or {}).get("pending_gm_beat")
        cur_type = cur_beat_post.get("type") if isinstance(cur_beat_post, dict) else None

        if beat_locked:
            storytell_is_pressure = storytell_type in PRESSURE_BEAT_TYPES if storytell_type else False
            storytell_is_non_pressure = bool(storytell_type) and not storytell_is_pressure

            if not storytell_is_non_pressure:
                if cur_type != "breathing_room":
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "floor_relief",
                        "detail": f"beat_locked=True, storytell_type={storytell_type!r} but pending_gm_beat.type={cur_type!r} (expected 'breathing_room')",
                    })
                    all_passed = False

        # rolled implies binding
        ruling = extract_field(ev, "ruling") or {}
        if ruling.get("rolled"):
            narrate_prompt = extract_field(ev, "narrate_prompt") or {}
            nu = narrate_prompt.get("rendered_user") or ""
            if "rules_outcome (BINDING" not in nu:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "binding_present",
                    "detail": "rolled=true but narrate user prompt did not include rules_outcome BINDING block",
                })
                all_passed = False

        # beat_locked_dual_trigger
        pc_momentum = (snap.get("pc") or {}).get("momentum", 0)
        expected_beat_locked = int(pc_momentum) <= MOMENTUM_FLOOR if pc_momentum is not None else False

        if expected_beat_locked and not beat_locked:
            findings.append({
                "turn": ev.get("turn"),
                "check": "beat_locked_dual_trigger",
                "detail": f"momentum={pc_momentum} at floor {MOMENTUM_FLOOR}, but beat_locked=False",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="gm_beat_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="gm_beat_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
