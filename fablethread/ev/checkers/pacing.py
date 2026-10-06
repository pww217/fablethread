from __future__ import annotations

import logging
import re
from typing import Any

from fablethread.engine.config import _build_jinja_env, _render
from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field
from fablethread.ev.prompt_context import build_prompt_context

_log = logging.getLogger(__name__)

_TEMPLATE_DIR = "fablethread/prompts"


@register_checker(
    "pacing_directives", "deterministic",
    requires_fields=["ruling", "pacing_context"],
    description="Directive rendering, known values",
)
def pacing_directives(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    env = _build_jinja_env(_TEMPLATE_DIR)

    for ev in events:
        # outcome_hint rendered
        pacing_ctx = extract_field(ev, "pacing_context") or {}
        outcome_hint = pacing_ctx.get("outcome_hint")

        if outcome_hint:
            turn = ev.get("turn")
            if turn is None:
                continue
            ctx = build_prompt_context(events, turn, "narrate")
            narr_user = _render(env, "narrate_user.j2", ctx)
            if f"**Outcome:** {outcome_hint}" not in narr_user:
                findings.append({
                    "turn": turn,
                    "check": "outcome_hint_rendered",
                    "detail": f"outcome_hint '{outcome_hint}' not found in narrate user prompt",
                })
                all_passed = False

        # no removed directives
        turn = ev.get("turn")
        if turn is None:
            continue
        ctx_narr = build_prompt_context(events, turn, "narrate")
        narr_user = _render(env, "narrate_user.j2", ctx_narr)

        removed_directives = [
            (r"\bOverwhelm\b", "Overwhelm"),
            (r"\blocation pressure\b", "location pressure"),
            (r"\blocation imperative\b", "location imperative"),
            (r"\bcombat fatigue\b", "combat fatigue"),
        ]
        found_removed: list[str] = []
        for pattern, name in removed_directives:
            if re.search(pattern, narr_user, re.IGNORECASE):
                found_removed.append(f"{name} (narrate)")
        if found_removed:
            findings.append({
                "turn": turn,
                "check": "no_removed_directives",
                "detail": f"Removed directives found: {'; '.join(found_removed)}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="pacing_directives", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="pacing_directives", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
