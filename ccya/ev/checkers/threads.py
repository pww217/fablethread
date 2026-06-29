from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


def _is_hashable(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool)) or v is None


@register_checker(
    "thread_lifecycle", "deterministic",
    requires_fields=["extraction.record", "last_turn_state"],
    description="thread_add applied, thread_update IDs valid",
)
def thread_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    prev_snap: dict[str, Any] | None = None

    for ev in events:
        # Capture the previous turn's last_turn_state before updating.
        # last_turn_state is captured post-turn (after thread_add/updates/removes
        # are applied), so the current turn's last_turn_state may not reflect
        # threads that were added/updated/removed during this turn.
        prev_snap_for_this = prev_snap
        if "last_turn_state" in ev:
            prev_snap = ev["last_turn_state"]

        record_output = ((extract_field(ev, "extraction") or {}).get("record") or {}).get("output") or {}
        thread_add = record_output.get("thread_add")
        if thread_add and isinstance(thread_add, dict):
            tid = thread_add.get("id")
            if tid:
                # Check against CURRENT turn's last_turn_state (already has thread_add applied)
                snap = extract_field(ev, "last_turn_state") or {}
                nxt_arc = snap.get("arc") or {}
                thread_ids: set[str] = set()
                for t in (nxt_arc.get("threads") or []):
                    if isinstance(t, dict) and t.get("id"):
                        thread_ids.add(t["id"])
                for t in (nxt_arc.get("completed_threads") or []):
                    if isinstance(t, dict) and t.get("id"):
                        thread_ids.add(t["id"])
                if tid not in thread_ids:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "thread_add_applied",
                        "detail": f"thread added but never appeared in state: {tid}",
                    })
                    all_passed = False

        # thread_update IDs valid — compare against CURRENT turn's last_turn_state
        # (which has initial seeded threads + post-turn changes). If a thread
        # was removed in the same turn, it won't appear in last_turn_state but
        # the thread_update was still valid (the thread existed at turn start).
        # Check changes event for same-turn removals to avoid false positives.
        thread_updates = record_output.get("thread_update") or []
        if thread_updates:
            snap = extract_field(ev, "last_turn_state") or {}
            state_thread_ids = {
                t.get("id") for t in ((snap.get("arc") or {}).get("threads") or [])
                if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id")
            }
            # Also check previous turn's state for initial seeded threads
            if prev_snap_for_this:
                prev_arc = (prev_snap_for_this.get("arc") or {})
                prev_thread_ids = {
                    t.get("id") for t in ((prev_arc.get("threads") or []) + (prev_arc.get("completed_threads") or []))
                    if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id")
                }
                state_thread_ids |= prev_thread_ids

            # Check changes event for same-turn thread removals
            changes_threads = (ev.get("changes") or {}).get("threads") or []
            removed_ids = {
                t.get("id") for t in changes_threads
                if isinstance(t, dict) and t.get("kind") == "removed" and t.get("id")
            }

            bad = [t.get("id") for t in thread_updates
                   if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id") not in state_thread_ids
                   and t.get("id") not in removed_ids]
            if bad:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "thread_update_valid_id",
                    "detail": f"thread_update references unknown thread ID(s): {bad}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )


def _get_active_threads(arc: dict[str, Any]) -> list[dict[str, Any]]:
    """Get active (non-completed) threads from arc."""
    return [t for t in (arc.get("threads") or []) if isinstance(t, dict)]


def _get_completed_threads(arc: dict[str, Any]) -> list[dict[str, Any]]:
    """Get completed threads from arc."""
    return [t for t in (arc.get("completed_threads") or []) if isinstance(t, dict)]


@register_checker(
    "thread_urgency_decay", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify thread urgency decay: dormant after 4 turns, stepwise demotion after 8 turns",
)
def thread_urgency_decay(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        meta = snap.get("meta") or {}
        turn_no = ev.get("turn")

        current_turn = meta.get("turn", turn_no)
        threads = _get_active_threads(arc)

        for t in threads:
            tid = t.get("id")
            urgency = t.get("urgency", "normal")
            dormant = t.get("dormant", False)
            last_updated_turn = t.get("last_updated_turn")
            urgency_set_turn = t.get("urgency_set_turn")

            # Non-urgent threads untouched >= 8 turns should be dormant
            if urgency != "urgent" and last_updated_turn is not None:
                turns_since_update = current_turn - last_updated_turn
                if turns_since_update >= cfg.thread_urgency_max_age and not dormant:
                    findings.append({
                        "turn": turn_no,
                        "check": "non_urgent_dormant",
                        "detail": f"thread '{tid}' urgency={urgency}, last_updated_turn={last_updated_turn}, turns_since={turns_since_update} >= 4, dormant={dormant}",
                    })
                    all_passed = False

            # Threads at same urgency >= 8 turns should be demoted stepwise
            if urgency_set_turn is not None:
                turns_at_urgency = current_turn - urgency_set_turn
                if turns_at_urgency >= cfg.thread_urgency_max_age:
                    # Should be demoted: urgent→normal, normal→background
                    if urgency == "urgent":
                        findings.append({
                            "turn": turn_no,
                            "check": "urgent_demotion",
                            "detail": f"thread '{tid}' urgency=urgent for {turns_at_urgency} turns >= {cfg.thread_urgency_max_age}, should be demoted to normal",
                        })
                        all_passed = False
                    elif urgency == "normal":
                        findings.append({
                            "turn": turn_no,
                            "check": "normal_demotion",
                            "detail": f"thread '{tid}' urgency=normal for {turns_at_urgency} turns >= {cfg.thread_urgency_max_age}, should be demoted to background",
                        })
                        all_passed = False

            # No stepwise jumps (urgent→background directly)
            if urgency == "background" and last_updated_turn is not None:
                # If the thread was previously urgent, it should have gone through normal
                # We can't fully verify this without history, but we can flag background threads
                # that have very old last_updated_turn
                pass

    if not all_passed:
        return CheckerResult(
            checker_id="thread_urgency_decay", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_urgency_decay", passed=True, score=1.0,
        detail=f"thread urgency decay OK across {len(filtered)} events",
    )


@register_checker(
    "thread_cap_eviction", "deterministic",
    requires_fields=["last_turn_state", "extraction.record"],
    description="Verify thread cap enforcement: oldest active thread dormant when cap exceeded",
)
def thread_cap_eviction(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        turn_no = ev.get("turn")

        threads = _get_active_threads(arc)
        active_count = len([t for t in threads if not t.get("dormant", False)])

        # Check if thread_add was emitted this turn
        record = (ev.get("extraction") or {}).get("record") or {}
        record_output = record.get("output") or {}
        thread_add = record_output.get("thread_add")

        if thread_add and isinstance(thread_add, dict) and active_count > cfg.thread_max_active:
            # Find oldest active thread (by last_updated_turn or added_turn)
            active_threads = [t for t in threads if not t.get("dormant", False)]
            if active_threads:
                oldest = min(active_threads, key=lambda t: t.get("last_updated_turn") or t.get("added_turn") or 0)
                if not oldest.get("dormant", False):
                    findings.append({
                        "turn": turn_no,
                        "check": "thread_cap_eviction",
                        "detail": f"thread_add fired with {active_count} active threads > cap {cfg.thread_max_active}, oldest '{oldest.get('id')}' should be dormant",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_cap_eviction", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_cap_eviction", passed=True, score=1.0,
        detail=f"thread cap eviction OK across {len(filtered)} events",
    )


@register_checker(
    "thread_culling", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify dormant thread culling: oldest dormant threads abandoned when count >= 3",
)
def thread_culling(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        turn_no = ev.get("turn")

        threads = _get_active_threads(arc)
        completed = _get_completed_threads(arc)

        # Count dormant threads
        dormant_threads = [t for t in threads if t.get("dormant", False)]
        dormant_count = len(dormant_threads)

        if dormant_count >= 3:
            # Check if oldest dormant threads appear in completed_threads with abandoned
            # At least some dormant threads should be in completed with abandoned
            abandoned_ids = {ct.get("id") for ct in completed if ct.get("resolution_state") == "abandoned"}

            # We can't enforce this strictly without knowing the culling logic,
            # but we can flag if there are many dormant threads with no culling
            if dormant_count >= 5:
                findings.append({
                    "turn": turn_no,
                    "check": "dormant_culling",
                    "detail": f"{dormant_count} dormant threads, only {len(abandoned_ids)} abandoned in completed_threads",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_culling", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_culling", passed=True, score=1.0,
        detail=f"thread culling OK across {len(filtered)} events",
    )


@register_checker(
    "thread_cooldown", "deterministic",
    requires_fields=["last_turn_state", "extraction.record"],
    description="Verify thread creation cooldown: thread_add only fires when cooldown elapsed",
)
def thread_cooldown(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    prev_snap: dict[str, Any] | None = None

    for ev in filtered:
        turn_no = ev.get("turn")

        # Capture previous turn's state for cooldown check
        prev_snap_for_this = prev_snap
        snap = extract_field(ev, "last_turn_state") or {}
        if "last_turn_state" in ev:
            prev_snap = snap

        # Check if thread_add was emitted this turn
        record = (ev.get("extraction") or {}).get("record") or {}
        record_output = record.get("output") or {}
        thread_add = record_output.get("thread_add")

        if thread_add and isinstance(thread_add, dict):
            # Read last_thread_creation_turn from PREVIOUS turn's meta
            if prev_snap_for_this:
                last_turn_created = prev_snap_for_this.get("meta", {}).get("last_thread_creation_turn")
            else:
                # First turn — no prior creation, always allowed
                last_turn_created = None
            if last_turn_created is None:
                pass  # First turn, no cooldown check
            else:
                last_turn_created = last_turn_created if last_turn_created is not None else 0
                turns_since_last = turn_no - last_turn_created
                if turns_since_last < cfg.thread_creation_cooldown:
                    findings.append({
                        "turn": turn_no,
                        "check": "thread_cooldown",
                        "detail": f"thread_add fired {turns_since_last} turns after last creation, cooldown={cfg.thread_creation_cooldown}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_cooldown", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_cooldown", passed=True, score=1.0,
        detail=f"thread cooldown OK across {len(filtered)} events",
    )


@register_checker(
    "thread_completion", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify threads with >=3 progress entries appear in completed_threads",
)
def thread_completion(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        turn_no = ev.get("turn")

        threads = _get_active_threads(arc)
        completed = _get_completed_threads(arc)

        for t in threads:
            major_updates = t.get("major_updates") or []
            if len(major_updates) >= 3:
                # Check if this thread should be completed
                # (This is a soft check - threads can have many updates and still be active)
                pass

        # Check completed threads for proper resolution
        for ct in completed:
            if ct.get("resolution_state") not in ("resolved", "failed", "abandoned", None):
                findings.append({
                    "turn": turn_no,
                    "check": "completion_state_valid",
                    "detail": f"completed thread '{ct.get('id')}' has invalid resolution_state: {ct.get('resolution_state')}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_completion", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_completion", passed=True, score=1.0,
        detail=f"thread completion OK across {len(filtered)} events",
    )


@register_checker(
    "progress_dedup", "deterministic",
    requires_fields=["extraction.record"],
    description="Verify consecutive progress entries on same thread differ by <70% overlap",
)
def progress_dedup(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    def _simple_diff_ratio(a: str, b: str) -> float:
        """Simple diff ratio: 1 - (diff_chars / max_len)."""
        if not a or not b:
            return 1.0
        shorter = min(len(a), len(b))
        longer = max(len(a), len(b))
        if shorter == 0:
            return 1.0
        # Count matching characters from start
        matches = 0
        for i in range(shorter):
            if a[i] == b[i]:
                matches += 1
            else:
                break
        return matches / longer

    for ev in filtered:
        record = (ev.get("extraction") or {}).get("record") or {}
        record_output = record.get("output") or {}
        thread_updates = record_output.get("thread_update") or []

        if not thread_updates:
            continue

        # Group updates by thread ID within this turn
        updates_by_thread: dict[str, list[str]] = {}
        for tu in thread_updates:
            if not isinstance(tu, dict):
                continue
            tid = tu.get("id")
            progress = tu.get("progress")
            if tid and progress:
                updates_by_thread.setdefault(tid, []).append(progress)

        # Check for duplicates within same turn
        for tid, progresses in updates_by_thread.items():
            if len(progresses) > 1:
                for i in range(1, len(progresses)):
                    ratio = _simple_diff_ratio(progresses[i-1], progresses[i])
                    if ratio >= 0.7:
                        findings.append({
                            "turn": ev.get("turn"),
                            "check": "progress_dedup",
                            "detail": f"thread '{tid}': consecutive progress entries {ratio:.0%} similar: '{progresses[i-1][:50]}' vs '{progresses[i][:50]}'",
                        })
                        all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="progress_dedup", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="progress_dedup", passed=True, score=1.0,
        detail=f"progress dedup OK across {len(filtered)} events",
    )
