from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "pacing_directives", "deterministic",
    requires_fields=["ruling", "narrate_prompt"],
    description="Directive rendering, known values",
)
def pacing_directives(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        # outcome_hint rendered
        pacing_ctx = extract_field(ev, "pacing_context") or {}
        outcome_hint = pacing_ctx.get("outcome_hint")

        if outcome_hint:
            narr_user = (extract_field(ev, "narrate_prompt") or {}).get("rendered_user") or ""
            if f"**Outcome:** {outcome_hint}" not in narr_user:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "outcome_hint_rendered",
                    "detail": f"outcome_hint '{outcome_hint}' not found in narrate user prompt",
                })
                all_passed = False

        # directive rendered storytell
        storytell_level = (extract_field(ev, "extraction") or {}).get("storytell") or {}
        directive_value = pacing_ctx.get("directive", "")
        if directive_value:
            storytell_rendered = storytell_level.get("rendered_user") or ""
            if not storytell_rendered:
                # extraction failed — can't validate rendering
                pass
            else:
                _directive_re = re.compile(
                    r"(?i)(?:directive[:\s]+|[\*\*]?)\b" + re.escape(directive_value) + r"\b",
                )
                if not _directive_re.search(storytell_rendered):
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "directive_rendered",
                        "detail": f"computed directive '{directive_value}' not found in storytell user prompt",
                    })
                    all_passed = False

        # no removed directives
        narr_user = (extract_field(ev, "narrate_prompt") or {}).get("rendered_user") or ""
        storytell_rendered = storytell_level.get("rendered_user") or ""

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
            if re.search(pattern, storytell_rendered, re.IGNORECASE):
                found_removed.append(f"{name} (storytell)")
        if found_removed:
            findings.append({
                "turn": ev.get("turn"),
                "check": "no_removed_directives",
                "detail": f"Removed directives found: {'; '.join(found_removed)}",
            })
            all_passed = False

    # Phase constraint: beat types must be allowed for the phase at time of emission
    # (beat emitted during storytell extraction, after phase engine updates)
    from ccya.engine._pacing import derive_allowed_beat_types

    for ev in events:
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        gm_beat = storytell_output.get("gm_beat")
        if not isinstance(gm_beat, dict) or not gm_beat.get("type"):
            continue

        pacing_ctx = extract_field(ev, "pacing_context") or {}
        scene_phase = pacing_ctx.get("scene_phase", "SETUP")
        allowed = derive_allowed_beat_types(
            scene_phase,
            directive=pacing_ctx.get("directive", ""),
            spiral_detected=pacing_ctx.get("spiral_detected", False),
        )
        beat_type = gm_beat["type"]

        if beat_type not in allowed:
            findings.append({
                "turn": ev.get("turn"),
                "check": "phase_constraint",
                "detail": f"beat type '{beat_type}' not allowed in phase '{scene_phase}' (allowed: {allowed})",
            })
            all_passed = False

    # beat_type_variety (looks across all events)
    beats: list[str] = []
    for ev in events:
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        gm_beat = storytell_output.get("gm_beat")
        if isinstance(gm_beat, dict) and gm_beat.get("type"):
            beats.append(gm_beat["type"])

    if len(beats) >= 3:
        counts = Counter(beats)
        dominant_type, dominant_count = counts.most_common(1)[0]
        ratio = dominant_count / len(beats)
        if ratio > 0.7:
            findings.append({
                "check": "beat_type_variety",
                "detail": f"beats are {ratio:.0%} '{dominant_type}' (threshold: 70%): {dict(counts)}",
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


@register_checker(
    "action_quality", "deterministic",
    requires_fields=["actions", "ruling"],
    description="Action count, distinctness, variety",
)
def action_quality(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        # Skip if storytell extraction failed
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        if not storytell_output:
            continue

        actions = extract_field(ev, "actions") or []
        if not isinstance(actions, list):
            findings.append({
                "turn": ev.get("turn"),
                "check": "actions_quality",
                "detail": "actions is not a list",
            })
            all_passed = False
            continue

        n = len(actions)
        distinct = len(set(actions))
        if n < 1:
            findings.append({
                "turn": ev.get("turn"),
                "check": "actions_quality",
                "detail": f"actions has {n} entries (expected at least 1)",
            })
            all_passed = False
        if distinct != n:
            findings.append({
                "turn": ev.get("turn"),
                "check": "actions_quality",
                "detail": f"actions has {n - distinct} duplicate(s): {actions}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="action_quality", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="action_quality", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
