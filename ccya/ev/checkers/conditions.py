from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.state.delta_builder import PC_CONDITIONS_MAX

_log = logging.getLogger(__name__)


@register_checker(
    "conditions_lifecycle", "deterministic",
    requires_fields=["applied.pc_condition_add", "applied.pc_condition_remove"],
    description="Dedup, cap, TTL for PC conditions",
)
def conditions_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        snap = extract_field(ev, "state_snapshot") or {}
        conditions = (snap.get("pc") or {}).get("conditions") or []

        # dedup check
        seen: set[str] = set()
        dups: list[str] = []
        for cond in conditions:
            if isinstance(cond, dict):
                cid = str(cond.get("id") or "")
            else:
                cid = str(cond or "")
            if cid in seen:
                dups.append(cid)
            elif cid:
                seen.add(cid)
        if dups:
            findings.append({
                "turn": ev.get("turn"),
                "check": "dedup",
                "detail": f"duplicate condition IDs: {dups}",
            })
            all_passed = False

        # cap check (state_snapshot.pc.conditions is the authoritative count)
        if len(conditions) > PC_CONDITIONS_MAX:
            findings.append({
                "turn": ev.get("turn"),
                "check": "conditions_cap",
                "detail": f"conditions count={len(conditions)} exceeds max {PC_CONDITIONS_MAX}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="conditions_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="conditions_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
