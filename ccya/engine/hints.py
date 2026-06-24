"""Pressure score system for thread and arc hint generation.

Pure functions: state in, hint context out, no side effects.
Shared by both narrator and storyteller paths.
"""

from __future__ import annotations

import logging
from typing import Any

from ccya.models import ArcThread, LongTermObjective

_log = logging.getLogger(__name__)


def _compute_duration_weight(age_turns: int, max_age: int = 10) -> float:
    """Compute a weight factor based on how long something has been active.

    Returns a value in [0.0, 1.0] that increases with age.
    """
    if age_turns <= 0:
        return 0.0
    return min(1.0, age_turns / max_age)


def _compute_urgency_weight(urgency: str) -> float:
    """Compute a weight factor based on thread urgency level."""
    weights = {
        "urgent": 1.0,
        "normal": 0.5,
        "background": 0.2,
    }
    return weights.get(urgency, 0.5)


def _resolve_hint_tier(score: int) -> tuple[str | None, str | None]:
    """Resolve a pressure score to a hint tier and hint text.

    Tiers:
    - None: score < 3
    - Soft: 3 <= score < 5
    - Strong: 5 <= score < 7
    - Imperative: score >= 7
    """
    if score >= 7:
        return "imperative", "Wrap up — failure is a valid resolution"
    if score >= 5:
        return "strong", "This should be reaching conclusion"
    if score >= 3:
        return "soft", "Consider resolving"
    return None, None


def compute_thread_pressure_score(thread: ArcThread, current_turn: int) -> tuple[int, str | None]:
    """Compute a pressure score for a single thread.

    Factors:
    - Thread age (turns since last update)
    - Urgency level
    - Whether thread is dormant
    - Number of progress entries

    Returns (score, hint_text) where hint_text is None if score < 3.
    """
    last_updated = getattr(thread, "last_updated_turn", 0) or 0
    age_turns = current_turn - last_updated if last_updated > 0 else 0

    urgency = getattr(thread, "urgency", "normal") or "normal"
    dormant = getattr(thread, "dormant", False)
    progress = getattr(thread, "progress", []) or []

    # Base score from urgency
    urgency_weight = _compute_urgency_weight(urgency)
    base = int(urgency_weight * 4)  # 0 to 4

    # Age weight
    age_weight = _compute_duration_weight(age_turns)
    age_bonus = int(age_weight * 3)  # 0 to 3

    # Dormant penalty (reduces score)
    dormant_penalty = 2 if dormant else 0

    # Progress count bonus (more progress = more pressure to resolve)
    progress_bonus = min(2, len(progress) - 2) if len(progress) > 2 else 0

    score = max(0, base + age_bonus - dormant_penalty + progress_bonus)
    hint_text, _ = _resolve_hint_tier(score)

    return score, hint_text


def compute_arc_pressure_score(arc: LongTermObjective | dict[str, Any], current_turn: int) -> tuple[int, str | None]:
    """Compute a pressure score for a LongTermObjective (arc).

    Factors:
    - Arc age (turns since started)
    - Number of active threads
    - Number of urgent threads
    - Whether arc has a resolution set

    Returns (score, hint_text) where hint_text is None if score < 3.
    """
    started = getattr(arc, "started_turn", None)
    if started is None:
        return 0, None

    age_turns = current_turn - started
    threads = getattr(arc, "threads", []) or []
    active_threads = [t for t in threads if not getattr(t, "dormant", False)]
    urgent_threads = [
        t for t in active_threads
        if getattr(t, "urgency", "normal") == "urgent"
    ]
    has_resolution = getattr(arc, "resolution", None) is not None

    # Base score from arc age
    age_weight = _compute_duration_weight(age_turns, max_age=15)
    base = int(age_weight * 4)  # 0 to 4

    # Urgent thread bonus
    urgent_bonus = min(3, len(urgent_threads))

    # Active thread count bonus
    thread_bonus = min(2, len(active_threads) - 1) if len(active_threads) > 1 else 0

    # Resolution penalty (reduces score — resolved arcs have low pressure)
    resolution_penalty = 3 if has_resolution else 0

    score = max(0, base + urgent_bonus + thread_bonus - resolution_penalty)
    hint_text, _ = _resolve_hint_tier(score)

    return score, hint_text
