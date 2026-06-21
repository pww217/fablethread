from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)

VALID_PRESENCE = {"present", "nearby", "known", "departed", None}


@register_checker(
    "npc_presence", "deterministic",
    requires_fields=["applied.compendium_npc_update"],
    description="NPC presence validity, departed field compliance, scene cap",
)
def npc_presence(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        turn = ev.get("turn")
        snap = extract_field(ev, "state_snapshot") or {}
        compendium = snap.get("compendium") or {}
        npcs = compendium.get("npcs") or {}

        if not isinstance(npcs, dict):
            continue

        for npc_id, npc in npcs.items():
            if not isinstance(npc, dict):
                continue

            presence = npc.get("presence")

            # Check for invalid presence values
            if presence not in VALID_PRESENCE:
                findings.append({
                    "turn": turn,
                    "check": "valid_presence",
                    "detail": f"NPC '{npc_id}' has invalid presence '{presence}'",
                })
                all_passed = False

            # Check departed NPCs have required fields
            if presence == "departed":
                if not npc.get("departed_reason"):
                    findings.append({
                        "turn": turn,
                        "check": "departed_reason",
                        "detail": f"NPC '{npc_id}' is departed but missing departed_reason",
                    })
                    all_passed = False
    if not all_passed:
        return CheckerResult(
            checker_id="npc_presence", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="npc_presence", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
