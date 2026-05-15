"""Campaign arc director — engagement scoring only.

Thread lifecycle (signals, completion, promotion, latent hygiene) is handled
by dedicated functions in engine/turn.py. This module exists solely for
arc engagement scoring based on player drift signals.
"""

from __future__ import annotations

from typing import Any

from ccya.models import CampaignArc


STANCE_KEYWORDS: dict[str, list[str]] = {
    "compassionate": ["help", "heal", "save", "comfort", "protect", "trust"],
    "ruthless": ["kill", "threaten", "abandon", "betray", "steal", "use"],
    "defiant": ["refuse", "resist", "defy", "challenge", "reject", "ignore"],
    "cautious": ["hide", "wait", "observe", "avoid", "sneak", "plan"],
}


def update_stances(stances: dict[str, int], user_input: str) -> dict[str, int]:
    """Update expressed stances based on player input keywords."""
    lower = user_input.lower()
    for stance, keywords in STANCE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            stances[stance] = stances.get(stance, 0) + 1
    return stances


def tick_arc(
    arc: CampaignArc,
    drift: list[str] | None = None,
    drift_analysis: list[Any] | None = None,
) -> CampaignArc:
    """Score arc engagement based on drift overlap with active thread tags.

    Thread lifecycle is handled by _apply_thread_signals / _candidate_to_latent_thread
    in engine/turn.py. This function only updates arc_engagement.
    """
    engagement_tags: set[str] = set()
    for t in arc.active_threads:
        engagement_tags.update(t.tags or [])

    # Prefer structured drift_analysis, fall back to legacy player_drift_signals
    if drift_analysis:
        has_overlap = any(da.match for da in drift_analysis)
    elif drift:
        has_overlap = False
        for d in drift:
            d_lower = d.lower()
            for tag in engagement_tags:
                if tag in d_lower:
                    has_overlap = True
                    break
            if has_overlap:
                break
    else:
        return arc

    if has_overlap:
        arc.arc_engagement = min(arc.arc_engagement + 1, 3)
    else:
        arc.arc_engagement = max(arc.arc_engagement - 1, -3)

    return arc
