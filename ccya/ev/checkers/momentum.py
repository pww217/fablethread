from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.rules import MOMENTUM_DELTA
from ccya.state.momentum import MOMENTUM_MIN, MOMENTUM_MAX

_log = logging.getLogger(__name__)

MOMENTUM_FLOOR = -3


@register_checker(
    "momentum_lifecycle", "deterministic",
    requires_fields=["ruling.band", "momentum_before", "momentum_after", "applied"],
    description="Verify momentum delta matches roll band",
)
def momentum_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        ruling = extract_field(ev, "ruling") or {}
        if not ruling.get("rolled"):
            continue

        band = ruling.get("band", "")
        expected = MOMENTUM_DELTA.get(band)
        if expected is None:
            continue

        prev_momentum = extract_field(ev, "momentum_before") or 0
        prev_momentum = int(prev_momentum)

        if band in ("success", "crit_success") and prev_momentum < -2:
            expected = 2 if band == "success" else 3

        actual = extract_field(ev, "momentum_delta")
        if actual is None:
            snap = extract_field(ev, "state_snapshot") or {}
            cur_m = (snap.get("pc") or {}).get("momentum")
            if cur_m is not None:
                actual = int(cur_m) - prev_momentum
            else:
                continue

        actual = int(actual)
        ok = (
            actual == expected
            or (expected > 0 and 0 <= actual <= expected)
            or (expected < 0 and expected <= actual <= 0)
        )
        if not ok:
            findings.append({
                "turn": ev.get("turn"),
                "check": "band_delta",
                "detail": f"band={band} expected delta {expected:+d} but got {actual:+d} (prev={prev_momentum})",
            })
            all_passed = False

        momentum_after = extract_field(ev, "momentum_after")
        if momentum_after is not None and not (MOMENTUM_MIN <= int(momentum_after) <= MOMENTUM_MAX):
            findings.append({
                "turn": ev.get("turn"),
                "check": "momentum_bounds",
                "detail": f"momentum_after={momentum_after} outside [{MOMENTUM_MIN}, {MOMENTUM_MAX}]",
            })
            all_passed = False

    floor_streak = 0
    for ev in events:
        snap = extract_field(ev, "state_snapshot") or {}
        m = (snap.get("pc") or {}).get("momentum", 0)
        if m is not None and int(m) <= MOMENTUM_FLOOR:
            floor_streak += 1
        else:
            floor_streak = 0
        if floor_streak >= 3:
            findings.append({
                "turn": ev.get("turn"),
                "check": "floor_no_relief",
                "detail": f"momentum at floor for {floor_streak} consecutive turns",
            })
            all_passed = False
            break

    if not all_passed:
        return CheckerResult(
            checker_id="momentum_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="momentum_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
