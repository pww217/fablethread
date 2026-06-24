"""Pressure score system for thread and arc hint generation.

Pure functions: state in, hint context out, no side effects.
Shared by both narrator and storyteller paths.

Design spec (see docs/design/01-primitives.md):
- Duration weight: table-based cumulative (0/1/3/6/10)
- Thread progress: each advancement +1, each setback -1 (floor 0)
- Arc progress: each resolved thread +2
- Hint tiers: thread (<4/4-6/7-9/>=10), arc (<5/5-8/9-12/>=13)
"""

from __future__ import annotations

import logging
from typing import Any

from ccya.models import ArcThread, LongTermObjective

_log = logging.getLogger(__name__)


def _compute_duration_weight(age_turns: int) -> int:
    """Compute cumulative duration weight from age using the design table.

    | Age (turns active) | Cumulative weight |
    |---|---|
    | 1-4  | 0   |
    | 5-7  | 1   |
    | 8-10 | 4   |
    | 11-13| 10  |
    | 14+  | 20  |
    """
    if age_turns >= 14:
        return 20
    if age_turns >= 11:
        return 10
    if age_turns >= 8:
        return 4
    if age_turns >= 5:
        return 1
    return 0


def _compute_thread_progress_signal(thread: ArcThread) -> int:
    """Compute thread progress signal from major_updates.

    Each advancement entry = +1, each setback = -1, floor at 0.
    """
    score = 0
    for entry in thread.major_updates:
        if entry.kind == "advancement":
            score += 1
        elif entry.kind == "setback":
            score -= 1
    return max(0, score)


def _compute_arc_progress_signal(arc: LongTermObjective | dict[str, Any]) -> int:
    """Compute arc progress signal from resolved threads.

    Each resolved thread (resolution_state == "resolved") = +2.
    Failed and abandoned threads = +0.
    """
    completed = getattr(arc, "completed_threads", []) or []
    resolved_count = sum(
        1 for t in completed
        if (getattr(t, "resolution_state", None) == "resolved" or
            (isinstance(t, dict) and t.get("resolution_state") == "resolved"))
    )
    return resolved_count * 2


def _resolve_thread_hint(score: int) -> str | None:
    """Resolve thread pressure score to hint language.

    None: score < 4, Soft: 4-6, Strong: 7-9, Imperative: >=10.
    """
    if score >= 10:
        return "Wrap up — failure is a valid resolution"
    if score >= 7:
        return "This should be reaching conclusion"
    if score >= 4:
        return "Consider resolving"
    return None


def _resolve_arc_hint(score: int) -> str | None:
    """Resolve arc pressure score to hint language.

    None: score < 5, Soft: 5-8, Strong: 9-12, Imperative: >=13.
    """
    if score >= 13:
        return "Wrap up — failure is a valid resolution"
    if score >= 9:
        return "This should be reaching conclusion"
    if score >= 5:
        return "Consider resolving"
    return None


def compute_thread_pressure_score(thread: ArcThread, current_turn: int) -> tuple[int, str | None]:
    """Compute thread pressure score = duration_weight + progress_signal.

    Returns (score, hint_text) where hint_text is None for None tier.
    """
    added = thread.added_turn or 0
    age_turns = current_turn - added if added > 0 else 0
    duration_w = _compute_duration_weight(age_turns)
    progress_s = _compute_thread_progress_signal(thread)
    score = duration_w + progress_s
    hint_text = _resolve_thread_hint(score)
    return score, hint_text


def compute_arc_pressure_score(arc: LongTermObjective | dict[str, Any], current_turn: int) -> tuple[int, str | None]:
    """Compute arc pressure score = duration_weight + progress_signal.

    Returns (score, hint_text) where hint_text is None for None tier.
    """
    started = getattr(arc, "started_turn", None)
    if started is None:
        return 0, None
    age_turns = current_turn - started
    duration_w = _compute_duration_weight(age_turns)
    progress_s = _compute_arc_progress_signal(arc)
    score = duration_w + progress_s
    hint_text = _resolve_arc_hint(score)
    return score, hint_text
