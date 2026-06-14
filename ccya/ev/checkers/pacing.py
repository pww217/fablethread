from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.engine.turn import PRESSURE_BEAT_TYPES

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
        # consecutive pressure tracking
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        gm_beat = storytell_output.get("gm_beat")
        gm_beat_type = gm_beat.get("type") if isinstance(gm_beat, dict) else None

        counter = extract_field(ev, "post_extraction_consecutive_pressure_beats")
        if counter is None:
            # engine didn't record post-extraction counter — skip validation
            counter = -1  # sentinel to skip check
        else:
            counter = int(counter)

        is_pressure = gm_beat_type in PRESSURE_BEAT_TYPES if gm_beat_type else False

        if not gm_beat_type or counter == -1:
            # no beat emitted or no post-extraction counter — skip pressure counter check
            pass
        elif is_pressure:
            # pre-turn counter can be 0 if just reset after relief — only check non-pressure resets
            pass
        else:
            if int(counter) != 0:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "consecutive_pressure",
                    "detail": f"gm_beat.type={gm_beat_type!r} (not pressure) but consecutive_pressure_beats={counter} (expected 0)",
                })
                all_passed = False

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

        removed_directives = ["Pressure", "Overwhelm", "location pressure", "location imperative", "combat fatigue"]
        found_removed: list[str] = []
        for directive in removed_directives:
            if directive.lower() in narr_user.lower():
                found_removed.append(f"{directive} (narrate)")
            if directive.lower() in storytell_rendered.lower():
                found_removed.append(f"{directive} (storytell)")
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

    # surface_as consistency (consecutive same-type beats)
    for i in range(len(events) - 1):
        cur = events[i]
        nxt = events[i + 1]

        cur_output = ((extract_field(cur, "extraction") or {}).get("storytell") or {}).get("output") or {}
        nxt_output = ((extract_field(nxt, "extraction") or {}).get("storytell") or {}).get("output") or {}

        cur_beat = cur_output.get("gm_beat")
        nxt_beat = nxt_output.get("gm_beat")

        if not isinstance(cur_beat, dict) or not isinstance(nxt_beat, dict):
            continue

        cur_type = cur_beat.get("type")
        nxt_type = nxt_beat.get("type")
        if cur_type is None or nxt_type is None or cur_type != nxt_type:
            continue

        cur_surface = cur_beat.get("surface_as")
        nxt_surface = nxt_beat.get("surface_as")
        if cur_surface is None or nxt_surface is None:
            continue

        if {cur_surface, nxt_surface} == {"ambient", "environmental"}:
            cur_pacing = extract_field(cur, "pacing_context") or {}
            nxt_pacing = extract_field(nxt, "pacing_context") or {}
            if cur_pacing.get("directive") == nxt_pacing.get("directive"):
                findings.append({
                    "turn": nxt.get("turn"),
                    "check": "surface_as_consistency",
                    "detail": f"same beat type '{cur_type}' but surface_as flipped from '{cur_surface}' to '{nxt_surface}' without directive change",
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
