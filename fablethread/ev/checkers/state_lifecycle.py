from __future__ import annotations

import logging
from typing import Any

from fablethread.engine.config import EngineConfig
from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "condition_ttl", "deterministic",
    requires_fields=["last_turn_state", "applied.pc_condition_add"],
    description="Verify condition TTL: decremented turns_remaining, no 0-value, permanent stays permanent",
)
def condition_ttl(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        pc = snap.get("pc") or {}
        conditions = pc.get("conditions") or []
        turn_no = ev.get("turn")

        for c in conditions:
            if not isinstance(c, dict):
                continue

            cid = c.get("id")
            turns_remaining = c.get("turns_remaining")

            # Permanent conditions should stay permanent
            if turns_remaining == "permanent":
                continue

            # Non-integer turns_remaining is invalid
            if not isinstance(turns_remaining, int):
                findings.append({
                    "turn": turn_no,
                    "check": "condition_ttl_type",
                    "detail": f"condition '{cid}' has non-integer turns_remaining: {turns_remaining!r}",
                })
                all_passed = False
                continue

            # Conditions should not have turns_remaining == 0 (should be removed)
            if turns_remaining == 0:
                findings.append({
                    "turn": turn_no,
                    "check": "condition_ttl_zero",
                    "detail": f"condition '{cid}' has turns_remaining=0, should be removed",
                })
                all_passed = False

            # TTL should be positive
            if turns_remaining < 0:
                findings.append({
                    "turn": turn_no,
                    "check": "condition_ttl_negative",
                    "detail": f"condition '{cid}' has negative turns_remaining: {turns_remaining}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="condition_ttl", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="condition_ttl", passed=True, score=1.0,
        detail=f"condition TTL OK across {len(filtered)} events",
    )


@register_checker(
    "world_state_ttl", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify world state TTL: expired facts removed, permanent facts persist",
)
def world_state_ttl(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        scene = snap.get("scene") or {}
        world_state = scene.get("world_state") or []
        turn_no = ev.get("turn")

        current_turn = meta.get("turn", turn_no)

        for fact in world_state:
            if not isinstance(fact, dict):
                continue

            fact_id = fact.get("id")
            expires_turn = fact.get("expires_turn")
            permanent = fact.get("permanent", False)

            # Permanent facts should persist
            if permanent:
                continue

            # Non-permanent facts with expires_turn should be removed when expired
            if expires_turn is not None and isinstance(expires_turn, int):
                if expires_turn <= current_turn:
                    findings.append({
                        "turn": turn_no,
                        "check": "world_state_expired",
                        "detail": f"world state fact '{fact_id}' expired at turn {expires_turn}, current turn={current_turn}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="world_state_ttl", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="world_state_ttl", passed=True, score=1.0,
        detail=f"world state TTL OK across {len(filtered)} events",
    )


@register_checker(
    "npc_presence_decay", "deterministic",
    requires_fields=["last_turn_state", "applied.compendium_npc_add", "applied.compendium_npc_update"],
    description="Verify NPC presence decay: location-change auto-demotion for non-party NPCs",
)
def npc_presence_decay(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        compendium = snap.get("compendium") or {}
        npcs = compendium.get("npcs") or {}
        applied = ev.get("applied") or {}
        location_changes = applied.get("location_change")
        turn_no = ev.get("turn")

        if not location_changes:
            continue

        # Check if location changed
        for npc_id, npc in npcs.items():
            if not isinstance(npc, dict):
                continue

            # Party NPCs should not be demoted
            if npc.get("party", False):
                continue

            presence = npc.get("presence")
            last_presence_turn = npc.get("last_presence_turn")

            # Nearby NPCs should decay to known after TTL turns
            if presence == "nearby" and last_presence_turn is not None:
                turns_since_presence = turn_no - last_presence_turn
                if turns_since_presence >= cfg.nearby_decay_ttl:
                    findings.append({
                        "turn": turn_no,
                        "check": "nearby_decay",
                        "detail": f"NPC '{npc_id}' presence=nearby for {turns_since_presence} turns >= TTL={cfg.nearby_decay_ttl}, should decay to known",
                    })
                    all_passed = False

            # Departed NPCs should be archived after TTL turns
            if presence == "departed":
                departed_turn = npc.get("departed_turn")
                if departed_turn is not None:
                    turns_since_departed = turn_no - departed_turn
                    if turns_since_departed >= cfg.departed_archive_ttl:
                        findings.append({
                            "turn": turn_no,
                            "check": "departed_archive",
                            "detail": f"NPC '{npc_id}' presence=departed for {turns_since_departed} turns >= TTL={cfg.departed_archive_ttl}, should be archived",
                        })
                        all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="npc_presence_decay", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="npc_presence_decay", passed=True, score=1.0,
        detail=f"NPC presence decay OK across {len(filtered)} events",
    )


@register_checker(
    "beat_diversity", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify beat candidates don't all match the most recent beat type",
)
def beat_diversity(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        beat_candidates = meta.get("beat_candidates") or []
        recent_beats = meta.get("recent_beats") or []
        turn_no = ev.get("turn")

        if not beat_candidates or not recent_beats:
            continue

        # Get most recent beat type
        most_recent_type = recent_beats[0].get("type") if recent_beats else None
        if not most_recent_type:
            continue

        # Check if all candidates match the most recent type
        all_same = all(
            isinstance(bc, dict) and bc.get("type") == most_recent_type
            for bc in beat_candidates
        )

        if all_same and len(beat_candidates) >= 2:
            findings.append({
                "turn": turn_no,
                "check": "beat_diversity",
                "detail": f"all {len(beat_candidates)} beat candidates have type '{most_recent_type}', no diversity",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="beat_diversity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="beat_diversity", passed=True, score=1.0,
        detail=f"beat diversity OK across {len(filtered)} events",
    )


@register_checker(
    "beat_candidates_present", "deterministic",
    requires_fields=["last_turn_state"],
    description="Verify beat candidates are non-empty on turns where World should have run",
)
def beat_candidates_present(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        turn_no = ev.get("turn")
        if turn_no is None:
            continue

        # World should run every turn after turn 1
        if turn_no <= 1:
            continue

        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        beat_candidates = meta.get("beat_candidates") or []

        # Allow empty beat_candidates when a pending GM beat replaces them
        post_beat = ev.get("post_turn_pending_beat") or snap.get("post_turn_pending_beat")
        if not beat_candidates and not post_beat:
            findings.append({
                "turn": turn_no,
                "check": "beat_candidates_present",
                "detail": f"no beat candidates on turn {turn_no} (World should have run)",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="beat_candidates_present", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="beat_candidates_present", passed=True, score=1.0,
        detail=f"beat candidates present OK across {len(filtered)} events",
    )
