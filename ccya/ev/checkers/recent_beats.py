from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "recent_beats", "deterministic",
    requires_fields=["state_snapshot"],
    description="Validate recent_beats history list structure and constraints",
)
def recent_beats(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "state_snapshot") or {}
        meta = (snap.get("meta") or {})
        recent = meta.get("recent_beats")

        if recent is None:
            # Turn 1 has no recent_beats yet (it's populated after turn 1 processes)
            if ev.get("turn", 1) <= 1:
                continue
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_exists",
                "detail": "recent_beats not found in state_snapshot.meta",
            })
            all_passed = False
            continue

        if not isinstance(recent, list):
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_is_list",
                "detail": f"recent_beats is {type(recent).__name__}, expected list",
            })
            all_passed = False
            continue

        # Check cap (default 5)
        if len(recent) > 5:
            findings.append({
                "turn": ev.get("turn"),
                "check": "recent_beats_cap",
                "detail": f"recent_beats has {len(recent)} entries (max 5)",
            })
            all_passed = False

        # Check entry structure
        for j, entry in enumerate(recent):
            if not isinstance(entry, dict):
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_structure",
                    "detail": f"entry[{j}] is {type(entry).__name__}, expected dict",
                })
                all_passed = False
                continue

            if "turn" not in entry:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_turn",
                    "detail": f"entry[{j}] missing 'turn' field",
                })
                all_passed = False

            if "type" not in entry or "effect" not in entry:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "recent_beats_entry_fields",
                    "detail": f"entry[{j}] missing 'type' or 'effect' field",
                })
                all_passed = False

        # Check monotonic turn numbers
        if isinstance(recent, list) and len(recent) > 1:
            for j in range(1, len(recent)):
                prev_turn = recent[j - 1].get("turn", 0)
                cur_turn = recent[j].get("turn", 0)
                if cur_turn <= prev_turn:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "recent_beats_monotonic",
                        "detail": f"entry[{j}].turn={cur_turn} <= entry[{j-1}].turn={prev_turn}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="recent_beats", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="recent_beats", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
