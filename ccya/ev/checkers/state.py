from __future__ import annotations

import logging
import re
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# location_description_consistency
# ---------------------------------------------------------------------------

@register_checker(
    "location_description_consistency", "deterministic",
    requires_fields=["last_turn_state.location.description"],
    description="Verify extracted location description is non-empty and substantive",
)
def location_description_consistency(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    cfg = EngineConfig().checkers
    filtered = filter_turn_events(events)

    for ev in filtered:
        last_turn_state = extract_field(ev, "last_turn_state") or {}
        location = last_turn_state.get("location") or {}
        description = location.get("description") or ""

        if not description.strip():
            findings.append({
                "turn": ev.get("turn"),
                "check": "description_non_empty",
                "detail": "location description is empty",
            })
            all_passed = False
            continue

        words = description.split()
        sentences = re.split(r"[.!?]+", description)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(words) < cfg.location_min_words or len(sentences) < cfg.location_min_sentences:
            findings.append({
                "turn": ev.get("turn"),
                "check": "description_substantive",
                "detail": f"description has {len(words)} words and {len(sentences)} sentence(s), minimum {cfg.location_min_words} words or {cfg.location_min_sentences} sentences",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="location_description_consistency", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="location_description_consistency", passed=True, score=1.0,
        detail=f"location descriptions OK across {len(events)} events",
    )


# ---------------------------------------------------------------------------
# world_state_facts
# ---------------------------------------------------------------------------

@register_checker(
    "world_state_facts", "deterministic",
    requires_fields=["last_turn_state.scene.world_state"],
    description="Verify world_state facts are non-empty strings or dicts with text",
)
def world_state_facts(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    cfg = EngineConfig().checkers

    for ev in events:
        last_turn_state = extract_field(ev, "last_turn_state") or {}
        scene = last_turn_state.get("scene") or {}
        world_state = scene.get("world_state") or []

        if not world_state:
            continue

        for i, fact in enumerate(world_state):
            if isinstance(fact, str):
                if not fact.strip():
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "fact_non_empty",
                        "detail": f"world_state[{i}] is empty string",
                    })
                    all_passed = False
                elif len(fact) < cfg.world_state_fact_min_chars:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "fact_min_chars",
                        "detail": f"world_state[{i}] has {len(fact)} chars, minimum {cfg.world_state_fact_min_chars}",
                    })
                    all_passed = False
            elif isinstance(fact, dict):
                text = fact.get("text", "") or ""
                if not text.strip():
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "fact_dict_text",
                        "detail": f"world_state[{i}] dict has empty text field",
                    })
                    all_passed = False
            else:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "fact_type",
                    "detail": f"world_state[{i}] has unexpected type {type(fact).__name__}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="world_state_facts", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="world_state_facts", passed=True, score=1.0,
        detail=f"world_state facts OK across {len(events)} events",
    )
