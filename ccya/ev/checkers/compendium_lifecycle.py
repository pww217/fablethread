from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "compendium_lifecycle", "deterministic",
    requires_fields=["applied.compendium_npc_update", "last_turn_state"],
    description="NPCs added via compendium_npc_update appear in state.compendium.npcs",
)
def compendium_lifecycle(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        applied = ev.get("applied") or {}
        npc_updates = applied.get("compendium_npc_update") or []

        if not npc_updates:
            continue

        snap = extract_field(ev, "last_turn_state") or {}
        compendium = snap.get("compendium") or {}
        npcs = compendium.get("npcs") or {}

        if not isinstance(npcs, dict):
            continue

        for update in npc_updates:
            if not isinstance(update, dict):
                continue

            npc_id = update.get("id")
            if not npc_id:
                continue

            if npc_id not in npcs:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "npc_in_state",
                    "detail": f"NPC {npc_id!r} added via compendium_npc_update but not found in state.compendium.npcs",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="compendium_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="compendium_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
