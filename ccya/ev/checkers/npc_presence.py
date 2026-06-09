from __future__ import annotations

import logging
import re
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "npc_presence", "deterministic",
    requires_fields=["extraction_context", "applied.compendium_npc_update"],
    description="NPC extraction, presence tags, scene cap",
)
def npc_presence(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        snap = extract_field(ev, "state_snapshot") or {}

        # no removed NPC states
        scene = snap.get("scene") or {}
        if "recently_left" in scene:
            findings.append({
                "turn": ev.get("turn"),
                "check": "no_removed_npc_states",
                "detail": "removed field 'recently_left' found in state_snapshot.scene",
            })
            all_passed = False

        narr_user = (extract_field(ev, "narrate_prompt") or {}).get("rendered_user") or ""
        if re.search(r"\bJUST_LEFT\b", narr_user, re.IGNORECASE):
            findings.append({
                "turn": ev.get("turn"),
                "check": "no_removed_npc_states",
                "detail": "removed NPC presence tag 'JUST_LEFT' found in rendered narrator prompt",
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
