"""Campaign arc director — Python-only thread promotion and engagement tracking.

Runs after extraction in the turn pipeline. Consumes thread_signals and
player_drift_signals from ProgressExtractResult, mutates state.arc directly.
"""

from __future__ import annotations

import re

from ccya.models import ArcThread, CampaignArc, ThreadSignal, ThreadSignalType, ThreadState


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


def _tag_overlap(a: list[str], b: list[str]) -> int:
    """Count of tags present in both lists."""
    set_b = set(b)
    return sum(1 for t in a if t in set_b)


def _salience_score(
    thread: ArcThread,
    drift: list[str],
    active_tags: list[str],
    turn_no: int,
    momentum: float,
) -> float:
    """Score a latent thread for promotion priority.

    Higher score = more likely to be promoted.
    """
    score = 0.0

    # Tag overlap with player drift signals
    drift_tags = [d.lower() for d in drift]
    score += _tag_overlap(thread.tags, drift_tags) * 2.0

    # Tag overlap with currently active threads
    score += _tag_overlap(thread.tags, active_tags) * 1.5

    # Momentum bias
    if momentum <= -1:
        # Low momentum: prefer aid/breathing_room/ally/resource
        if any(t in thread.tags for t in ("aid", "breathing_room", "ally", "resource")):
            score += 2.0
    elif momentum >= 2:
        # High momentum: prefer cost/complication/deadline/betrayal_risk
        if any(t in thread.tags for t in ("cost", "complication", "deadline", "betrayal_risk")):
            score += 2.0

    # Recency: prefer threads not recently offered
    if thread.last_offered_turn is None or turn_no - thread.last_offered_turn > 5:
        score += 1.0

    return score


def tick_arc(
    arc: CampaignArc,
    signals: list[ThreadSignal],
    drift: list[str],
    momentum: float,
    turn_no: int,
    candidate: str | None = None,
) -> CampaignArc:
    """Process thread signals and update arc state.

    Responsibilities:
    - Thread advancement: 2 "advanced" signals → complete + promote
    - Thread failure: "failed" → mark failed
    - Thread expiry: 8+ turns of only "ignored" → expire + promote next
    - Active thread cap: keep 2-3 active threads
    - Arc engagement: increment/decrement based on drift overlap
    """
    # Track cumulative progress on thread objects themselves.
    # progress is incremented on ADVANCED, reset on BLOCKED.
    for sig in signals:
        if sig.signal == ThreadSignalType.ADVANCED:
            for t in arc.active_threads:
                if t.id == sig.id:
                    t.progress = t.progress + 1
                    break
            for t in arc.latent_threads:
                if t.id == sig.id:
                    t.progress = t.progress + 1
                    break
        elif sig.signal == ThreadSignalType.BLOCKED:
            # Reset progress on block — must rebuild momentum
            for t in arc.active_threads:
                if t.id == sig.id:
                    t.progress = 0
                    break
            for t in arc.latent_threads:
                if t.id == sig.id:
                    t.progress = 0
                    break
        elif sig.signal == ThreadSignalType.FAILED:
            # Mark thread as failed
            for t in arc.active_threads:
                if t.id == sig.id:
                    t.state = ThreadState.FAILED
                    break
            for t in arc.latent_threads:
                if t.id == sig.id:
                    t.state = ThreadState.FAILED
                    break
        # IGNORED: do not change progress — thread sits

    # Track ignored streaks for expiry detection
    ignored_counts: dict[str, int] = {}
    ignored_start_turn: dict[str, int] = {}
    for sig in signals:
        if sig.signal == ThreadSignalType.IGNORED:
            ignored_counts[sig.id] = ignored_counts.get(sig.id, 0) + 1
            if sig.id not in ignored_start_turn:
                ignored_start_turn[sig.id] = turn_no

    # Process completed threads (progress >= 2)
    threads_to_complete = []
    for t in arc.active_threads:
        if t.progress >= 2:
            threads_to_complete.append(t.id)
    for t in arc.latent_threads:
        if t.progress >= 2:
            threads_to_complete.append(t.id)

    for tid in threads_to_complete:
        for t in arc.active_threads:
            if t.id == tid:
                t.state = ThreadState.COMPLETE
                arc.active_threads.remove(t)
                arc.completed_threads.append(t)
                break
        for t in arc.latent_threads:
            if t.id == tid:
                t.state = ThreadState.COMPLETE
                arc.latent_threads.remove(t)
                arc.completed_threads.append(t)
                break

    # Process thread expiry (8+ turns of only ignored)
    threads_to_expire = []
    for sig in signals:
        if sig.signal != ThreadSignalType.IGNORED:
            continue
        for t in arc.active_threads:
            if t.id == sig.id and t.last_offered_turn is not None:
                if turn_no - t.last_offered_turn >= 8:
                    threads_to_expire.append(t.id)
                    break

    for tid in threads_to_expire:
        for i, t in enumerate(arc.active_threads):
            if t.id == tid:
                t.state = ThreadState.EXPIRED
                arc.active_threads.pop(i)
                arc.completed_threads.append(t)
                break

    # Promote threads from completes
    for t in arc.completed_threads:
        for promote_id in t.promotes:
            for lt in arc.latent_threads:
                if lt.id == promote_id and lt.state == ThreadState.LATENT:
                    lt.state = ThreadState.ACTIVE
                    lt.last_offered_turn = turn_no
                    arc.latent_threads.remove(lt)
                    arc.active_threads.append(lt)
                    break

    # Active thread cap: ensure at least 2 active, at most 3
    while len(arc.active_threads) < 2 and arc.latent_threads:
        # Score and promote highest salience latent thread
        active_tags = []
        for at in arc.active_threads:
            active_tags.extend(at.tags)
        candidates = []
        for lt in arc.latent_threads:
            if lt.state == ThreadState.LATENT:
                score = _salience_score(lt, drift, active_tags, turn_no, momentum)
                candidates.append((score, lt))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best = candidates[0][1]
            best.state = ThreadState.ACTIVE
            best.last_offered_turn = turn_no
            arc.latent_threads.remove(best)
            arc.active_threads.append(best)
        else:
            break

    while len(arc.active_threads) > 3 and arc.latent_threads:
        # Demote the lowest urgency active thread
        demote = None
        for t in arc.active_threads:
            if t.urgency != "immediate":
                demote = t
                break
        if demote:
            demote.state = ThreadState.LATENT
            demote.last_offered_turn = None
            arc.active_threads.remove(demote)
            arc.latent_threads.append(demote)
        else:
            break

    # Update last_offered_turn for active threads that received signals
    for sig in signals:
        for t in arc.active_threads:
            if t.id == sig.id:
                t.last_offered_turn = turn_no

    # Store candidate_opportunity as a latent thread
    if candidate:
        slug_id = re.sub(r'[^a-z0-9]+', '_', candidate[:40].lower().strip())
        slug_id = slug_id.strip('_') or 'opportunity'
        new_thread = ArcThread(
            id=slug_id,
            summary=candidate,
            tags=[],
            state=ThreadState.LATENT,
            urgency="normal",
            progress=0,
            unlock_if=None,
            promotes=[],
            last_offered_turn=None,
        )
        arc.latent_threads.append(new_thread)

    # Arc engagement: check drift overlap with active thread tags
    engagement_tags: set[str] = set()
    for t in arc.active_threads:
        engagement_tags.update(t.tags)

    if drift:
        # Substring matching: does any thread tag appear inside any drift phrase?
        has_overlap = False
        for d in drift:
            d_lower = d.lower()
            for tag in engagement_tags:
                if tag in d_lower:
                    has_overlap = True
                    break
            if has_overlap:
                break

        if has_overlap:
            arc.arc_engagement = min(arc.arc_engagement + 1, 3)
        else:
            arc.arc_engagement = max(arc.arc_engagement - 1, -3)

    return arc
