from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import _build_jinja_env, _render
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.ev.prompt_context import build_prompt_context

_log = logging.getLogger(__name__)

_TEMPLATE_DIR = "ccya/prompts"


@register_checker(
    "gm_beat_lifecycle", "deterministic",
    requires_fields=["last_turn_state", "ruling"],
    description="Verify pending_gm_beat is consumed and binding present on roll",
)
def gm_beat_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    env = _build_jinja_env(_TEMPLATE_DIR)

    for i, ev in enumerate(events):
        prev_ev = events[i - 1] if i > 0 else None

        snap = extract_field(ev, "last_turn_state") or {}
        prev_snap = extract_field(prev_ev, "last_turn_state") or {} if prev_ev else {}

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

        # rolled implies binding
        ruling = extract_field(ev, "ruling") or {}
        if ruling.get("rolled"):
            turn = ev.get("turn")
            if turn is not None:
                ctx = build_prompt_context(events, turn, "narrate")
                nu = _render(env, "narrate_user.j2", ctx)
            else:
                nu = ""
            if "rules_outcome (BINDING" not in nu:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "binding_present",
                    "detail": "rolled=true but narrate user prompt did not include rules_outcome BINDING block",
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
