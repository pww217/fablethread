"""Universal cross-pipeline assertions that apply to every event.

Each function returns dict[str, Any] with keys: assertion, passed, detail, scope.
`scope` is always 'universal'. If passed=True, the assertion is informational;
the runner discards passes and surfaces only failures.

These catch known classes of mechanical bugs without requiring scenario
authors to write per-turn asserts. Designed to be cheap and high-signal.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from ccya.eval.engine_mirror import (
    MOMENTUM_DELTA,
    PRESSURE_BEAT_TYPES,
    MOMENTUM_FLOOR,
)


_log = logging.getLogger(__name__)


def check_pending_gm_beat_consumed(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """pending_gm_beat from prior turn must be absent or replaced this turn."""
    if prev_event is None:
        return {
            "assertion": "universal.pending_gm_beat.consumed",
            "passed": True,
            "detail": "(first turn)",
            "scope": "universal",
            "severity": "red",
        }
    prev_snap = prev_event.get("state_snapshot") or {}
    cur_snap = event.get("state_snapshot") or {}
    prev_beat = (prev_snap.get("meta") or {}).get("pending_gm_beat")
    cur_beat = (cur_snap.get("meta") or {}).get("pending_gm_beat")
    if prev_beat is None:
        return {
            "assertion": "universal.pending_gm_beat.consumed",
            "passed": True,
            "detail": "(no prior beat)",
            "scope": "universal",
            "severity": "red",
        }
    if cur_beat == prev_beat:
        return {
            "assertion": "universal.pending_gm_beat.consumed",
            "passed": False,
            "detail": f"beat persisted unchanged across turns: {prev_beat}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.pending_gm_beat.consumed",
        "passed": True,
        "detail": "beat consumed or replaced",
        "scope": "universal",
        "severity": "red",
    }


def check_pending_gm_beat_lifecycle_respected(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """Beat lifecycle from storytell extractor must be respected in state.

    NOTE: beat_disposition field removed from StorytellerResult in Phase 01.
    Python now infers disposition directly from gm_beat presence/absence:
    - new gm_beat with type → replace (write to pending_gm_beat)
    - no gm_beat or gm_beat without type → clear pending_gm_beat

    This checks that the engine's beat lifecycle logic correctly handles this.
    """
    extraction = event.get("extraction") or {}
    storytell = extraction.get("storytell") or {}
    storytell_gm_beat = storytell.get("gm_beat")
    cur_snap = event.get("state_snapshot") or {}
    cur_beat = (cur_snap.get("meta") or {}).get("pending_gm_beat")
    prev_snap = prev_event.get("state_snapshot") or {} if prev_event else None
    prev_beat = (prev_snap.get("meta") or {}).get("pending_gm_beat") if prev_snap else None

    # If a new gm_beat was emitted, it should be in state after the turn
    if storytell_gm_beat and isinstance(storytell_gm_beat, dict) and storytell_gm_beat.get("type"):
        if cur_beat is None:
            return {
                "assertion": "universal.pending_gm_beat.lifecycle_respected",
                "passed": False,
                "detail": f"new gm_beat emitted but pending_gm_beat is None in state: {storytell_gm_beat.get('type')}",
                "scope": "universal",
                "severity": "red",
            }
        if cur_beat.get("type") != storytell_gm_beat.get("type"):
            return {
                "assertion": "universal.pending_gm_beat.lifecycle_respected",
                "passed": False,
                "detail": f"new gm_beat type mismatch: storytell={storytell_gm_beat.get('type')}, state={cur_beat.get('type')}",
                "scope": "universal",
                "severity": "red",
            }
        return {
            "assertion": "universal.pending_gm_beat.lifecycle_respected",
            "passed": True,
            "detail": f"beat replaced with type={cur_beat.get('type')}",
            "scope": "universal",
            "severity": "red",
        }

    # No new gm_beat — pending_gm_beat should be None (cleared) or floor-relief-injected breathing_room
    if prev_beat is not None and cur_beat == prev_beat:
        return {
            "assertion": "universal.pending_gm_beat.lifecycle_respected",
            "passed": True,
            "detail": f"beat carried (unchanged): type={cur_beat.get('type')}",
            "scope": "universal",
            "severity": "yellow",
        }

    if cur_beat is None:
        return {
            "assertion": "universal.pending_gm_beat.lifecycle_respected",
            "passed": True,
            "detail": "beat consumed (cleared) - no gm_beat emitted this turn",
            "scope": "universal",
            "severity": "red",
        }

    # Floor relief may have injected breathing_room — that's valid
    if isinstance(cur_beat, dict) and cur_beat.get("type") == "breathing_room" and (
        not storytell_gm_beat or not isinstance(storytell_gm_beat, dict) or not storytell_gm_beat.get("type")
    ):
        return {
            "assertion": "universal.pending_gm_beat.lifecycle_respected",
            "passed": True,
            "detail": "beat injected by floor relief (breathing_room) — storytell emitted no beat",
            "scope": "universal",
            "severity": "yellow",
        }

    # A beat exists that wasn't from storytell and isn't floor-relief — suspicious
    return {
        "assertion": "universal.pending_gm_beat.lifecycle_respected",
        "passed": True,
        "detail": f"beat present but source unclear: type={cur_beat.get('type') if isinstance(cur_beat, dict) else cur_beat}",
        "scope": "universal",
        "severity": "yellow",
    }


def check_location_change_applied(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """If applied.location_change is set, post-turn location must differ from prior turn."""
    applied = event.get("applied") or {}
    lc = applied.get("location_change")
    if not lc:
        return {
            "assertion": "universal.location_change.applied",
            "passed": True,
            "detail": "(no change)",
            "scope": "universal",
            "severity": "red",
        }
    if prev_event is None:
        return {
            "assertion": "universal.location_change.applied",
            "passed": True,
            "detail": "(first turn)",
            "scope": "universal",
            "severity": "red",
        }
    prev_loc = ((prev_event.get("state_snapshot") or {}).get("location") or {}).get("id")
    post_loc = event.get("post_turn_location_id")
    if post_loc is None:
        # Fallback: use state_snapshot (pre-turn, off by one but better than nothing)
        post_loc = ((event.get("state_snapshot") or {}).get("location") or {}).get("id")
    if post_loc == prev_loc:
        return {
            "assertion": "universal.location_change.applied",
            "passed": False,
            "detail": f"location_change emitted but post-turn location.id unchanged: {post_loc}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.location_change.applied",
        "passed": True,
        "detail": f"{prev_loc} -> {post_loc}",
        "scope": "universal",
        "severity": "red",
    }


def check_rolled_implies_binding(event: dict[str, Any]) -> dict[str, Any]:
    """If ruling.rolled=true, narrate_prompt.rendered_user must contain 'rules_outcome (BINDING'."""
    ruling = event.get("ruling") or {}
    if not ruling.get("rolled"):
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "(no roll)",
            "scope": "universal",
            "severity": "red",
        }
    nu = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if "rules_outcome (BINDING" in nu:
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "binding directive included",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.narrate.binding_present",
        "passed": False,
        "detail": "rolled=true but narrate user prompt did not include rules_outcome BINDING block",
        "scope": "universal",
        "severity": "red",
    }



def check_actions_count_and_distinct(event: dict[str, Any]) -> dict[str, Any]:
    """storytell.actions must contain exactly 4 distinct entries."""
    actions = event.get("actions") or []
    if not isinstance(actions, list):
        return {
            "assertion": "universal.storytell.actions_quality",
            "passed": False,
            "detail": "actions is not a list",
            "scope": "universal",
            "severity": "red",
        }
    n = len(actions)
    distinct = len(set(actions))
    if n != 4:
        return {
            "assertion": "universal.storytell.actions_quality",
            "passed": False,
            "detail": f"actions has {n} entries (expected 4)",
            "scope": "universal",
            "severity": "red",
        }
    if distinct != n:
        return {
            "assertion": "universal.storytell.actions_quality",
            "passed": False,
            "detail": f"actions has {n - distinct} duplicate(s): {actions}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.storytell.actions_quality",
        "passed": True,
        "detail": "4 distinct actions",
        "scope": "universal",
        "severity": "red",
    }


def check_momentum_band_delta(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """If a roll happened, momentum should change per band (see MOMENTUM_DELTA)."""
    ruling = event.get("ruling") or {}
    if not ruling.get("rolled"):
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(no roll)",
            "scope": "universal",
            "severity": "red",
        }
    band = ruling.get("band", "")
    expected = MOMENTUM_DELTA.get(band)
    if expected is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": f"(unknown band {band!r})",
            "scope": "universal",
            "severity": "red",
        }

    # MB-4: account for depth-based catch-up at -3 or below
    prev_momentum = event.get("momentum_before") or (
        (event.get("state_snapshot") or {}).get("pc") or {}
    ).get("momentum", 0)
    if band in ("success", "crit_success") and int(prev_momentum) < -2:
        expected = 2 if band == "success" else 3

    # Use the event's own momentum_delta (engine's actual value after clamping and deep recovery)
    md = event.get("momentum_delta")
    if md is None:
        # Fallback for old event files: compute from state_snapshot diffs
        if prev_event is None:
            return {"assertion": "universal.momentum.band_delta", "passed": True, "detail": "(first turn)", "scope": "universal", "severity": "red"}
        cur_snap = event.get("state_snapshot") or {}
        cur_m = (cur_snap.get("pc") or {}).get("momentum")
        if cur_m is None:
            return {"assertion": "universal.momentum.band_delta", "passed": True, "detail": "(no pc.momentum field)", "scope": "universal", "severity": "red"}
        prev_snap = prev_event.get("state_snapshot") or {}
        prev_m = (prev_snap.get("pc") or {}).get("momentum") or 0
        actual = (cur_m or 0) - prev_m
    else:
        actual = md

    if actual == expected or (expected > 0 and 0 <= actual <= expected) or (expected < 0 and expected <= actual <= 0):
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": f"band={band} delta={actual} (expected {expected:+d}, engine may clamp)",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.momentum.band_delta",
        "passed": False,
        "detail": f"band={band} expected delta {expected:+d} but got {actual:+d} (prev={prev_momentum})",
        "scope": "universal",
        "severity": "red",
    }


def check_zero_stack_overdraw(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """inventory_remove must not remove from a zero-quantity item."""
    if prev_event is None:
        return {"assertion": "universal.inventory.no_overdraw", "passed": True, "detail": "(first turn)", "scope": "universal", "severity": "red"}
    prev_inv = (prev_event.get("state_snapshot") or {}).get("inventory") or []
    zero_items = {
        item["id"] for item in prev_inv
        if isinstance(item, dict) and (item.get("amount") or 0) == 0 and item.get("id")
    }
    removes = (event.get("applied") or {}).get("inventory_remove") or []
    bad = [r for r in removes if isinstance(r, dict) and r.get("id") in zero_items]
    if bad:
        return {
            "assertion": "universal.inventory.no_overdraw",
            "passed": False,
            "detail": f"removed from zero-quantity item(s): {[b.get('id') for b in bad]}",
            "scope": "universal",
            "severity": "red",
        }
    return {"assertion": "universal.inventory.no_overdraw", "passed": True, "detail": f"checked {len(removes)} removes", "scope": "universal", "severity": "red"}


def check_momentum_floor_no_relief(
    event: dict[str, Any],
    prev_event: dict[str, Any] | None,
    event_window: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Momentum at floor for >= 3 consecutive turns without a success band is a pacing failure.

    Timing note: momentum values in state_snapshot are post-delta-apply, but delta does not
    contain momentum fields — momentum only changes via apply_momentum() during ruling phase.
    So the momentum read here matches what _compute_pacing_context used at narrate setup time.
    """
    window: list[dict[str, Any]] = event_window or ([prev_event, event] if prev_event else [event])
    floor_count = 0
    for ev in reversed(window):
        m = ((ev.get("state_snapshot") or {}).get("pc") or {}).get("momentum", 0)
        if m is not None and m <= MOMENTUM_FLOOR:
            floor_count += 1
        else:
            break
    if floor_count >= 3:
        return {"assertion": "universal.pacing.floor_no_relief", "passed": False, "detail": f"momentum at floor for {floor_count} consecutive turns", "scope": "universal", "severity": "yellow"}
    return {"assertion": "universal.pacing.floor_no_relief", "passed": True, "detail": f"floor_count={floor_count}", "scope": "universal", "severity": "yellow"}


def check_no_negative_inventory(event: dict[str, Any]) -> dict[str, Any]:
    inventory = (event.get("state_snapshot") or {}).get("inventory", [])
    bad = [i["id"] for i in inventory if isinstance(i, dict) and i.get("id") and i.get("amount", 1) < 1]
    if bad:
        return {
            "assertion": "universal.inventory.no_negative_amount",
            "passed": False,
            "detail": f"zero/negative inventory: {bad}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.inventory.no_negative_amount",
        "passed": True,
        "detail": "no negative amounts",
        "scope": "universal",
        "severity": "red",
    }


def check_inventory_remove_existence(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """inventory_remove must target items that exist with amount > 0 in state."""
    if prev_event is None:
        return {"assertion": "universal.inventory.remove_existence", "passed": True, "detail": "(first turn)", "scope": "universal", "severity": "red"}
    prev_inv_ids = {
        item["id"] for item in ((prev_event.get("state_snapshot") or {}).get("inventory") or [])
        if isinstance(item, dict) and item.get("id") and item.get("amount", 0) > 0
    }
    removes = (event.get("applied") or {}).get("inventory_remove") or []
    bad = [r for r in removes if isinstance(r, dict) and r.get("id") and r["id"] not in prev_inv_ids]
    if bad:
        return {
            "assertion": "universal.inventory.remove_existence",
            "passed": False,
            "detail": f"removed non-existent item(s): {[b.get('id') for b in bad]}",
            "scope": "universal",
            "severity": "red",
        }
    return {"assertion": "universal.inventory.remove_existence", "passed": True, "detail": f"checked {len(removes)} removes", "scope": "universal", "severity": "red"}


def check_thread_update_id_valid(event: dict[str, Any]) -> dict[str, Any]:
    """thread_update signals must reference thread IDs that exist in state."""
    storytell_output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
    thread_updates = storytell_output.get("thread_update") or []
    if not thread_updates:
        return {"assertion": "universal.thread_update.valid_id", "passed": True, "detail": "no thread_updates", "scope": "universal", "severity": "red"}
    def _is_hashable(v: Any) -> bool:
        return isinstance(v, (str, int, float, bool)) or v is None

    state_thread_ids = {
        t.get("id") for t in ((event.get("state_snapshot") or {}).get("arc") or {}).get("threads") or []
        if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id")
    }
    bad = [t.get("id") for t in thread_updates if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id") not in state_thread_ids] or \
          [t.id for t in thread_updates if hasattr(t, "id") and _is_hashable(t.id) and t.id not in state_thread_ids]
    if bad:
        return {
            "assertion": "universal.thread_update.valid_id",
            "passed": False,
            "detail": f"thread_update references unknown thread ID(s): {bad}",
            "scope": "universal",
            "severity": "red",
        }
    return {"assertion": "universal.thread_update.valid_id", "passed": True, "detail": f"checked {len(thread_updates)} thread_updates", "scope": "universal", "severity": "red"}


def check_outcome_hint_rendered(event: dict[str, Any]) -> dict[str, Any]:
    """If outcome_hint was computed, validate it appears in the narrate prompt.

    Reads outcome_hint from event["pacing_context"]["outcome_hint"] (the canonical source).
    Template renders "**Outcome:** {value}" followed by value-specific guidance in narrate_user.
    """
    pacing_ctx = event.get("pacing_context") or {}
    outcome_hint = pacing_ctx.get("outcome_hint")

    if not outcome_hint:
        return {
            "assertion": "universal.narrate.outcome_hint_rendered",
            "passed": True,
            "detail": "(no outcome_hint computed)",
            "scope": "universal",
            "severity": "red",
        }

    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user") or ""

    # Check outcome_hint appears in narrate prompt
    if f"**Outcome:** {outcome_hint}" not in narr_user:
        return {
            "assertion": "universal.narrate.outcome_hint_rendered",
            "passed": False,
            "detail": f"outcome_hint '{outcome_hint}' not found in narrate user prompt (pacing_context={pacing_ctx})",
            "scope": "universal",
            "severity": "red",
        }

    return {
        "assertion": "universal.narrate.outcome_hint_rendered",
        "passed": True,
        "detail": f"outcome_hint '{outcome_hint}' rendered in narrate prompt",
        "scope": "universal",
        "severity": "red",
    }


def check_directive_rendered_storytell(event: dict[str, Any]) -> dict[str, Any]:
    """If pacing directive was computed, validate it appears in the storytell prompt.

    Reads directive from event["pacing_context"]["directive"] (the canonical source).
    Template renders "Directive: {value}" in storytell_user.
    """
    pacing_ctx = event.get("pacing_context") or {}
    directive_value = pacing_ctx.get("directive", "")

    if not directive_value:
        return {
            "assertion": "universal.storytell.directive_rendered",
            "passed": True,
            "detail": "(no directive computed)",
            "scope": "universal",
            "severity": "yellow",
        }

    storytell_rendered = ((event.get("extraction") or {}).get("storytell") or {}).get("rendered_user") or ""

    # Check exact directive value appears in storytell prompt using word-boundary matching
    _directive_in_prompt_re = re.compile(
        r"(?i)(?:directive[:\s]+|[\*\*]?)\b" + re.escape(directive_value) + r"\b",
    )

    if not _directive_in_prompt_re.search(storytell_rendered):
        return {
            "assertion": "universal.storytell.directive_rendered",
            "passed": False,
            "detail": f"computed directive '{directive_value}' not found in storytell user prompt (pacing_context={pacing_ctx})",
            "scope": "universal",
            "severity": "yellow",
        }

    return {
        "assertion": "universal.storytell.directive_rendered",
        "passed": True,
        "detail": f"directive '{directive_value}' rendered in storytell prompt",
        "scope": "universal",
        "severity": "yellow",
    }






def check_consecutive_pressure_tracking(
    event: dict[str, Any], prev_event: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate consecutive pressure counter tracks storyteller gm_beat types (not directives).

    Counter increments when storytell gm_beat.type is in PRESSURE_BEAT_TYPES
    (pressure, escalation, complication); resets to 0 otherwise. Floor relief
    injection (breathing_room) does NOT affect the counter — it reads from the
    raw storyteller result, not from the post-relief pending_gm_beat.
    """
    storytell_output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
    gm_beat = storytell_output.get("gm_beat")
    gm_beat_type = gm_beat.get("type") if isinstance(gm_beat, dict) else None

    # Use post-extraction counter (captured after all extraction phases including storytell),
    # falls back to state_snapshot meta for older event files without the new field.
    counter = event.get("post_extraction_consecutive_pressure_turns")
    if counter is None:
        meta = (event.get("state_snapshot") or {}).get("meta") or {}
        counter = meta.get("consecutive_pressure_turns", 0)

    is_pressure = gm_beat_type in PRESSURE_BEAT_TYPES if gm_beat_type else False

    if is_pressure:
        if counter < 1:
            return {
                "assertion": "universal.pacing.consecutive_pressure_tracking",
                "passed": False,
                "detail": f"gm_beat.type={gm_beat_type!r} (pressure type) but consecutive_pressure_turns={counter} (expected >= 1)",
                "scope": "universal",
                "severity": "red",
            }
    else:
        if counter != 0:
            return {
                "assertion": "universal.pacing.consecutive_pressure_tracking",
                "passed": False,
                "detail": f"gm_beat.type={gm_beat_type!r} (not pressure) but consecutive_pressure_turns={counter} (expected 0)",
                "scope": "universal",
                "severity": "red",
            }

    return {
        "assertion": "universal.pacing.consecutive_pressure_tracking",
        "passed": True,
        "detail": f"gm_beat.type={gm_beat_type!r}, counter={counter}",
        "scope": "universal",
        "severity": "yellow",
    }


def check_beat_locked_dual_trigger(
    event: dict[str, Any], prev_event: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate beat_locked is consistent with momentum floor.

    The engine computes beat_locked at narrate setup time using post-ruling momentum
    and the consecutive_pressure_turns counter from before this turn's extraction.
    The eval reads state_snapshot which has the *post-update* counter (incremented after
    extraction based on storytell's beat type). This causes a one-turn lag mismatch:
    if pressure beats fire exactly at threshold, engine sees N-1 turns and sets
    beat_locked=False while post-update snapshot shows N+1.

    We only validate the momentum floor branch here (no lag issue) since that is the
    primary pacing safety valve. The consecutive counter branch is structurally unverifiable
    from state_snapshot alone — a future assert could use pre-extraction counter values if
    those are preserved in events, or flag when post-update counter >= threshold+2 and
    beat_locked=False as a heuristic (accounts for the one-turn lag).

    See check_momentum_floor_no_relief for related validation.
    """
    snap = (event.get("state_snapshot") or {})
    pc_momentum = (snap.get("pc") or {}).get("momentum", 0)

    pacing_ctx = event.get("pacing_context") or {}
    beat_locked = bool(pacing_ctx.get("beat_locked", False))

    momentum = pc_momentum

    expected_beat_locked_from_momentum = momentum <= MOMENTUM_FLOOR

    if expected_beat_locked_from_momentum and not beat_locked:
        return {
            "assertion": "universal.pacing.beat_locked_dual_trigger",
            "passed": False,
            "detail": f"momentum={momentum} at floor {MOMENTUM_FLOOR}, but beat_locked=False — engine should have fired floor relief",
            "scope": "universal",
            "severity": "red",
        }

    return {
        "assertion": "universal.pacing.beat_locked_dual_trigger",
        "passed": True,
        "detail": f"beat_locked={beat_locked} (momentum={momentum}, floor={MOMENTUM_FLOOR})",
        "scope": "universal",
        "severity": "yellow",
    }


def check_floor_relief_injection(
    event: dict[str, Any], prev_event: dict[str, Any] | None = None
) -> dict[str, Any]:
    """When beat_locked=True and storytell produced no non-pressure beat, floor relief must inject breathing_room.

    Floor relief fires after delta apply: if beat_locked=True AND pending_gm_beat is
    None or a pressure type (pressure/escalation/complication), it injects a breathing_room
    beat. This assert verifies:
    - beat_locked=True + storytell emitted null/pressure beat → pending_gm_beat is breathing_room
    - beat_locked=False + storytell emitted null → pending_gm_beat is None (no injection)
    """
    pacing_ctx = event.get("pacing_context") or {}
    beat_locked = bool(pacing_ctx.get("beat_locked", False))

    storytell_output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
    storytell_gm_beat = storytell_output.get("gm_beat")
    storytell_type = storytell_gm_beat.get("type") if isinstance(storytell_gm_beat, dict) else None

    cur_snap = event.get("state_snapshot") or {}
    cur_beat = event.get("post_turn_pending_beat") or (cur_snap.get("meta") or {}).get("pending_gm_beat")
    cur_type = cur_beat.get("type") if isinstance(cur_beat, dict) else None

    if not beat_locked:
        return {
            "assertion": "universal.pacing.floor_relief",
            "passed": True,
            "detail": "beat_locked=False, no floor relief expected",
            "scope": "universal",
            "severity": "yellow",
        }

    # beat_locked is True -- floor relief should fire if no non-pressure beat exists
    storytell_is_pressure = storytell_type in PRESSURE_BEAT_TYPES if storytell_type else False
    storytell_is_non_pressure = bool(storytell_type) and not storytell_is_pressure

    if storytell_is_non_pressure:
        # Storyteller produced a non-pressure beat -- floor relief lets it stand
        return {
            "assertion": "universal.pacing.floor_relief",
            "passed": True,
            "detail": f"beat_locked=True, storytell emitted non-pressure beat '{storytell_type}' — floor relief did not override",
            "scope": "universal",
            "severity": "yellow",
        }

    # Storyteller emitted null or pressure-type beat -- floor relief must inject breathing_room
    if cur_type != "breathing_room":
        return {
            "assertion": "universal.pacing.floor_relief",
            "passed": False,
            "detail": f"beat_locked=True, storytell_type={storytell_type!r} but pending_gm_beat.type={cur_type!r} (expected 'breathing_room')",
            "scope": "universal",
            "severity": "red",
        }

    return {
        "assertion": "universal.pacing.floor_relief",
        "passed": True,
        "detail": f"beat_locked=True, storytell_type={storytell_type!r} → floor relief injected breathing_room",
        "scope": "universal",
        "severity": "yellow",
    }


def check_no_removed_directives(event: dict[str, Any]) -> dict[str, Any]:
    """Negative assertion: removed directives ("Location Pressure", "Location Imperative", "Combat Fatigue") must NOT appear in rendered prompts.

    Catches template drift or accidental re-introduction during future edits.
    """
    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    storytell_rendered = ((event.get("extraction") or {}).get("storytell") or {}).get("rendered_user") or ""

    removed_directives = ["location pressure", "location imperative", "combat fatigue"]
    found: list[str] = []

    for directive in removed_directives:
        if directive.lower() in narr_user.lower():
            found.append(f"{directive} (narrate)")
        if directive.lower() in storytell_rendered.lower():
            found.append(f"{directive} (storytell)")

    if found:
        return {
            "assertion": "universal.directives.no_removed",
            "passed": False,
            "detail": f"Removed directives found: {'; '.join(found)}",
            "scope": "universal",
            "severity": "yellow",
        }

    return {
        "assertion": "universal.directives.no_removed",
        "passed": True,
        "detail": "no removed directives in rendered prompts",
        "scope": "universal",
        "severity": "yellow",
    }


def check_no_removed_npc_states(event: dict[str, Any]) -> dict[str, Any]:
    """Negative assertion: removed NPC states ("JUST_LEFT", "recently_left") must NOT appear in state snapshots or rendered prompts.

    Catches accidental re-introduction of scene.recently_left field or JUST_LEFT presence tag after Plan #01 removal.
    """
    scene = (event.get("state_snapshot") or {}).get("scene") or {}
    if "recently_left" in scene:
        return {
            "assertion": "universal.npc_states.no_removed",
            "passed": False,
            "detail": "removed field 'recently_left' found in state_snapshot.scene",
            "scope": "universal",
            "severity": "red",
        }

    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if re.search(r"\bJUST_LEFT\b", narr_user, re.IGNORECASE):
        return {
            "assertion": "universal.npc_states.no_removed",
            "passed": False,
            "detail": "removed NPC presence tag 'JUST_LEFT' found in rendered narrator prompt",
            "scope": "universal",
            "severity": "yellow",
        }

    return {
        "assertion": "universal.npc_states.no_removed",
        "passed": True,
        "detail": "no removed NPC states detected",
        "scope": "universal",
        "severity": "yellow",
    }


def check_orphan_conditions(event: dict[str, Any]) -> dict[str, Any]:
    """Conditions in state must each have a corresponding CONDITION_MODS entry.

    Reads pc.conditions from state_snapshot. Flags red if a condition's id
    does not exist as a key in CONDITION_MODS — it's mechanically inert and
    creates observability debt.
    """
    from ccya.rules import CONDITION_MODS

    snap = event.get("state_snapshot") or {}
    conditions = (snap.get("pc") or {}).get("conditions") or []
    orphan_ids: list[str] = []
    for cond in conditions:
        if isinstance(cond, dict):
            cid = str(cond.get("id") or "").lower()
            if cid and cid not in CONDITION_MODS and cid not in orphan_ids:
                orphan_ids.append(cid)

    if orphan_ids:
        return {
            "assertion": "universal.conditions.orphan",
            "passed": False,
            "detail": f"conditions with no CONDITION_MODS entry: {orphan_ids}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.conditions.orphan",
        "passed": True,
        "detail": "all conditions have CONDITION_MODS entries",
        "scope": "universal",
        "severity": "red",
    }


def check_thread_add_applied(
    event: dict[str, Any],
    prev_event: dict[str, Any] | None,
    event_window: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """thread_add signals must produce visible state mutations.

    For each consecutive pair in event_window where storytell output has a
    non-null thread_add, verify the thread id appears in state_snapshot.arc.threads
    or state_snapshot.arc.completed_threads of the *following* event.
    """
    window: list[dict[str, Any]] = event_window or []
    failures: list[str] = []
    for i in range(len(window) - 1):
        cur = window[i]
        nxt = window[i + 1]
        storytell_output = ((cur.get("extraction") or {}).get("storytell") or {}).get("output") or {}
        thread_add = storytell_output.get("thread_add")
        if not thread_add or not isinstance(thread_add, dict):
            continue
        tid = thread_add.get("id")
        if not tid:
            continue

        nxt_arc = (nxt.get("state_snapshot") or {}).get("arc") or {}
        thread_ids: set[str] = set()
        for t in (nxt_arc.get("threads") or []):
            if isinstance(t, dict) and t.get("id"):
                thread_ids.add(t["id"])
        for t in (nxt_arc.get("completed_threads") or []):
            if isinstance(t, dict) and t.get("id"):
                thread_ids.add(t["id"])

        if tid not in thread_ids:
            failures.append(tid)

    if failures:
        return {
            "assertion": "universal.thread_add.applied",
            "passed": False,
            "detail": f"thread(s) added but never appeared in state: {failures}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.thread_add.applied",
        "passed": True,
        "detail": "all thread_add signals produced state mutations",
        "scope": "universal",
        "severity": "red",
    }


def check_goal_update_applied(
    event: dict[str, Any],
) -> dict[str, Any]:
    """If storytell emitted goal_update, verify it appears in state.arc.visible_goal.

    goal_update is an optional storyteller field that directly overwrites
    arc.visible_goal mid-arc (separate from arc_resolve). This assert verifies
    that when the storyteller emits a goal_update, the state snapshot reflects
    the new visible_goal value.
    """
    storytell_output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
    goal_update = storytell_output.get("goal_update")

    if not goal_update or not isinstance(goal_update, str):
        return {
            "assertion": "universal.goal_update.applied",
            "passed": True,
            "detail": "(no goal_update emitted)",
            "scope": "universal",
            "severity": "yellow",
        }

    arc = (event.get("state_snapshot") or {}).get("arc") or {}
    visible_goal = arc.get("visible_goal", "")

    if goal_update == visible_goal:
        return {
            "assertion": "universal.goal_update.applied",
            "passed": True,
            "detail": f"goal_update='{goal_update}' → arc.visible_goal='{visible_goal}'",
            "scope": "universal",
            "severity": "yellow",
        }

    return {
        "assertion": "universal.goal_update.applied",
        "passed": False,
        "detail": f"storytell emitted goal_update='{goal_update}' but arc.visible_goal='{visible_goal}'",
        "scope": "universal",
        "severity": "red",
    }


def check_beat_type_variety(
    event: dict[str, Any],
    event_window: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Warn if >60% of non-null beats in the event window share the same type.

    Reads gm_beat.type from storytell extraction output across the window.
    Flags yellow when a single beat type dominates — monotonous beat generation
    reduces narrative quality. Passes if fewer than 3 beats in window.
    """
    window: list[dict[str, Any]] = event_window or []
    beats: list[str] = []
    for ev in window:
        storytell_output = ((ev.get("extraction") or {}).get("storytell") or {}).get("output") or {}
        gm_beat = storytell_output.get("gm_beat")
        if isinstance(gm_beat, dict) and gm_beat.get("type"):
            beats.append(gm_beat["type"])

    if len(beats) < 3:
        return {
            "assertion": "universal.beat_type.variety",
            "passed": True,
            "detail": f"only {len(beats)} beat(s) in window (need >= 3)",
            "scope": "universal",
            "severity": "yellow",
        }

    counts = Counter(beats)
    dominant_type, dominant_count = counts.most_common(1)[0]
    ratio = dominant_count / len(beats)

    if ratio > 0.6:
        return {
            "assertion": "universal.beat_type.variety",
            "passed": False,
            "detail": f"beats are {ratio:.0%} '{dominant_type}' (threshold: 60%): {dict(counts)}",
            "scope": "universal",
            "severity": "yellow",
        }
    return {
        "assertion": "universal.beat_type.variety",
        "passed": True,
        "detail": f"beat variety OK: {dict(counts)}",
        "scope": "universal",
        "severity": "yellow",
    }


def check_surface_as_consistency(
    event: dict[str, Any],
    event_window: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Consecutive same-type beats should keep the same surface_as flag.

    For consecutive events in the window with the same gm_beat.type, verify
    that surface_as does not flip between 'ambient' and 'environmental' without
    a directive change. Passes if surface_as is absent/null on either event, or
    if fewer than 2 same-type beats exist. Flags yellow on drift.
    """
    window: list[dict[str, Any]] = event_window or []
    for i in range(len(window) - 1):
        cur = window[i]
        nxt = window[i + 1]

        cur_output = ((cur.get("extraction") or {}).get("storytell") or {}).get("output") or {}
        nxt_output = ((nxt.get("extraction") or {}).get("storytell") or {}).get("output") or {}

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

        surface_set = {cur_surface, nxt_surface}
        if surface_set == {"ambient", "environmental"}:
            cur_pacing = cur.get("pacing_context") or {}
            nxt_pacing = nxt.get("pacing_context") or {}
            if cur_pacing.get("directive") == nxt_pacing.get("directive"):
                return {
                    "assertion": "universal.beat_type.surface_as_consistency",
                    "passed": False,
                    "detail": f"same beat type '{cur_type}' but surface_as flipped from '{cur_surface}' to '{nxt_surface}' without directive change (directive='{cur_pacing.get('directive')}')",
                    "scope": "universal",
                    "severity": "yellow",
                }

    return {
        "assertion": "universal.beat_type.surface_as_consistency",
        "passed": True,
        "detail": "no surface_as drift detected",
        "scope": "universal",
        "severity": "yellow",
    }


def run_all_universal_asserts(
    event: dict[str, Any], prev_event: dict[str, Any] | None, event_window: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = [
        check_pending_gm_beat_consumed(event, prev_event),
        check_pending_gm_beat_lifecycle_respected(event, prev_event),
        check_location_change_applied(event, prev_event),
        check_rolled_implies_binding(event),
        check_actions_count_and_distinct(event),
        check_momentum_band_delta(event, prev_event),
        check_zero_stack_overdraw(event, prev_event),
        check_outcome_hint_rendered(event),
        check_directive_rendered_storytell(event),
        check_consecutive_pressure_tracking(event, prev_event),
        check_beat_locked_dual_trigger(event, prev_event),
        check_floor_relief_injection(event, prev_event),
        check_goal_update_applied(event),
        check_no_removed_directives(event),
        check_no_removed_npc_states(event),
        check_momentum_floor_no_relief(event, prev_event, event_window=event_window),
        check_no_negative_inventory(event),
        check_inventory_remove_existence(event, prev_event),
        check_thread_update_id_valid(event),
        check_orphan_conditions(event),
        check_thread_add_applied(event, prev_event, event_window=event_window),
        check_beat_type_variety(event, event_window=event_window),
        check_surface_as_consistency(event, event_window=event_window),
    ]
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    _log.debug("universal_asserts: %d passed, %d failed", passed, failed)
    return results
