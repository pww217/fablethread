from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.rules import compute_band, VALID_SKILLS, DIFFICULTY_MOD

_log = logging.getLogger(__name__)


@register_checker(
    "roll_band_consistency", "deterministic",
    requires_fields=["ruling"],
    description="Verify band matches dice roll using rules engine",
)
def roll_band_consistency(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue

        # Skip if no dice data (impossible rolls, no roll attempted)
        if not ruling.get("dice"):
            continue

        band = ruling.get("band")
        final_total = ruling.get("final_total")
        raw_total = ruling.get("raw_total")
        skill = ruling.get("skill")
        difficulty = ruling.get("difficulty")

        if band is None or final_total is None or raw_total is None:
            continue

        # Recompute band from dice
        stat_mod = ruling.get("stat_mod", 0)
        diff_mod = ruling.get("diff_mod", 0)
        expected_total = raw_total + stat_mod + diff_mod
        expected_band = compute_band(expected_total, raw_total)

        if band != expected_band:
            findings.append({
                "turn": ev.get("turn"),
                "check": "band_matches_dice",
                "detail": f"band={band!r} but recomputed from dice={raw_total}+{stat_mod}+{diff_mod}={expected_total} gives {expected_band!r}",
            })
            all_passed = False

        # Validate skill/difficulty are valid
        if skill and skill not in VALID_SKILLS:
            findings.append({
                "turn": ev.get("turn"),
                "check": "valid_skill",
                "detail": f"skill={skill!r} not in {sorted(VALID_SKILLS)}",
            })
            all_passed = False

        if difficulty and difficulty not in DIFFICULTY_MOD:
            findings.append({
                "turn": ev.get("turn"),
                "check": "valid_difficulty",
                "detail": f"difficulty={difficulty!r} not in {sorted(DIFFICULTY_MOD)}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="roll_band_consistency", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="roll_band_consistency", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
