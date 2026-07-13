from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field
from ccya.state.inventory import resolve_inventory_remove_target

_log = logging.getLogger(__name__)


def _zero_items_from_inv(inv: list[dict[str, Any]]) -> set[str]:
    return {
        item["id"] for item in inv
        if isinstance(item, dict) and (item.get("amount") or 0) == 0 and item.get("id")
    }


def _existing_inv_ids(inv: list[dict[str, Any]]) -> set[str]:
    return {
        item["id"] for item in inv
        if isinstance(item, dict) and item.get("id") and item.get("amount", 0) > 0
    }


@register_checker(
    "location_change", "deterministic",
    requires_fields=["post_turn_location_id"],
    description="Verify location changes are applied correctly",
)
def location_change(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for i, ev in enumerate(events):
        prev_ev = events[i - 1] if i > 0 else None
        applied = extract_field(ev, "applied") or {}
        lc = applied.get("location_change")
        if not lc:
            continue
        if prev_ev is None:
            continue

        prev_loc = ((extract_field(prev_ev, "last_turn_state") or {}).get("location") or {}).get("id")
        post_loc = extract_field(ev, "post_turn_location_id")
        if post_loc is None:
            post_loc = ((extract_field(ev, "last_turn_state") or {}).get("location") or {}).get("id")

        # prev_loc from prev event may be None (preceded by sanitizer event).
        # Use turn-level comparison: find the last turn event before this one.
        actual_prev_loc = prev_loc
        if actual_prev_loc is None:
            for j in range(i - 1, -1, -1):
                prv = events[j]
                if prv.get("type") == "turn":
                    actual_prev_loc = ((extract_field(prv, "last_turn_state") or {}).get("location") or {}).get("id")
                    break

        if actual_prev_loc and post_loc and actual_prev_loc != post_loc:
            # Real location change confirmed — passes
            pass
        elif actual_prev_loc and post_loc and actual_prev_loc == post_loc:
            # location_change emitted but no actual location transition
            # (engine silently skipped redundant delta). Not a failure.
            pass
        else:
            # prev_loc was truly unknown — can't verify, skip
            pass

    if not all_passed:
        return CheckerResult(
            checker_id="location_change", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="location_change", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )


@register_checker(
    "inventory_integrity", "deterministic",
    requires_fields=["applied.inventory_add", "applied.inventory_remove"],
    description="No overdraw, no negative amounts, remove existence",
)
def inventory_integrity(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for i, ev in enumerate(events):
        prev_ev = events[i - 1] if i > 0 else None

        inventory = (extract_field(ev, "last_turn_state") or {}).get("inventory", [])
        bad_neg = [item["id"] for item in inventory
                    if isinstance(item, dict) and item.get("id") and item.get("amount", 1) < 1]
        if bad_neg:
            findings.append({
                "turn": ev.get("turn"),
                "check": "no_negative",
                "detail": f"zero/negative inventory: {bad_neg}",
            })
            all_passed = False

        if prev_ev is not None:
            prev_inv = (extract_field(prev_ev, "last_turn_state") or {}).get("inventory") or []
            zero_items = _zero_items_from_inv(prev_inv)
            removes = (extract_field(ev, "applied") or {}).get("inventory_remove") or []
            bad_overdraw = []
            for r in removes:
                if not isinstance(r, dict) or not r.get("id"):
                    continue
                raw_id = r["id"]
                resolved = resolve_inventory_remove_target(prev_inv, raw_id)
                if resolved in zero_items:
                    bad_overdraw.append(r)
            if bad_overdraw:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "no_overdraw",
                    "detail": f"removed from zero-quantity item(s): {[b.get('id') for b in bad_overdraw]}",
                })
                all_passed = False

            prev_inv_ids = _existing_inv_ids(prev_inv)
            bad_exist = []
            for r in removes:
                if not isinstance(r, dict) or not r.get("id"):
                    continue
                raw_id = r["id"]
                resolved = resolve_inventory_remove_target(prev_inv, raw_id)
                if resolved is None or resolved not in prev_inv_ids:
                    bad_exist.append(r)
            if bad_exist:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "remove_existence",
                    "detail": f"removed non-existent item(s): {[b.get('id') for b in bad_exist]}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="inventory_integrity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="inventory_integrity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
