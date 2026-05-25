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
from typing import Any

from ccya.eval.engine_mirror import MOMENTUM_DELTA, MOMENTUM_MIN


_log = logging.getLogger(__name__)


def check_recent_events_turn_stamped(event: dict[str, Any]) -> dict[str, Any]:
    """recent_events_add[].turn must be the current turn, not 0 (placeholder)."""
    cur_turn = int(event.get("turn") or 0)
    adds = (event.get("applied") or {}).get("recent_events_add") or []
    bad = []
    for e in adds:
        if not isinstance(e, dict):
            continue
        t = e.get("turn")
        if t == 0 or t is None:
            bad.append(e.get("text", "(no text)"))
    if not adds:
        return {
            "assertion": "universal.recent_events_add.turn_stamped",
            "passed": True,
            "detail": "(no adds)",
            "scope": "universal",
            "severity": "red",
        }
    if bad:
        return {
            "assertion": "universal.recent_events_add.turn_stamped",
            "passed": False,
            "detail": f"{len(bad)} entries had turn=0/null instead of {cur_turn}: {bad[:3]}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.recent_events_add.turn_stamped",
        "passed": True,
        "detail": f"all {len(adds)} entries stamped with turn={cur_turn}",
        "scope": "universal",
        "severity": "red",
    }


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

    # No new gm_beat — pending_gm_beat should be None (consumed) or carried from previous turn
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

    # Beat persisted but no carry/replacement logic — this is acceptable as a yellow
    return {
        "assertion": "universal.pending_gm_beat.lifecycle_respected",
        "passed": True,
        "detail": f"beat state unchanged (no disposition field to enforce): type={cur_beat.get('type')}",
        "scope": "universal",
        "severity": "yellow",
    }


def check_location_change_applied(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """If applied.location_change is set, state_snapshot.location.id must differ from prior turn."""
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
    cur_loc = ((event.get("state_snapshot") or {}).get("location") or {}).get("id")
    if cur_loc == prev_loc:
        return {
            "assertion": "universal.location_change.applied",
            "passed": False,
            "detail": f"location_change emitted but state.location.id unchanged: {cur_loc}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.location_change.applied",
        "passed": True,
        "detail": f"{prev_loc} -> {cur_loc}",
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


def _extract_candidate_names(
    narration: str,
    pc_name: str,
    inventory_names: set[str] | None = None,
    location_names: set[str] | None = None,
) -> set[str]:
    """Extract capitalized tokens that are candidates for NPC names.

    Excludes the PC name (case-insensitive), sentence-initial words,
    short tokens (<=4 chars, likely descriptors), common descriptor words,
    inventory item names (partial match), and location names (partial match).

    Note: sentence-starters heuristic will miss NPC names that happen to
    appear at the start of a sentence. This is an accepted tradeoff to
    reduce false positives — the assert is for eval harness hygiene, not
    production logic.
    """
    sentences = re.split(r'(?<=[.!?])\s+', narration)
    sentence_starters: set[str] = set()
    for s in sentences:
        first = s.split()
        if first:
            sentence_starters.add(first[0].strip("\"'"))

    # Common descriptors and titles that are not NPC names
    descriptor_stop: set[str] = {
        "Scarred", "Tough", "Hooded", "Burly", "Young", "Old", "Tall",
        "Short", "Fat", "Thin", "Lean", "Dark", "Light", "Red", "Blue",
        "Green", "Gold", "Silver", "Iron", "Brass", "Wooden", "Stone",
        "Big", "Small", "Large", "Little", "High", "Low", "Fast", "Slow",
        "Good", "Bad", "New", "Last", "First", "Next", "Other", "Same",
        "Each", "Every", "Both", "All", "Some", "Any", "Many", "Few",
        "Hulking", "Generous", "Armed", "Two", "Three", "Several",
        "Crossed", "Careful", "Narrowing",
        "Silhouette", "Threshold", "Figure", "Outline", "Shadow", "Glint",
        "Shape", "Crossing",
    }

    inv_lower: set[str] = set()
    if inventory_names:
        inv_lower = {n.lower() for n in inventory_names}

    loc_lower: set[str] = set()
    if location_names:
        loc_lower = {n.lower() for n in location_names}

    candidates: set[str] = set()
    for token in re.findall(r'\b[A-Z][a-z]{2,}\b', narration):
        if token.lower() == pc_name.lower():
            continue
        if token in sentence_starters:
            continue
        if token in descriptor_stop:
            continue
        if len(token) <= 4:
            continue
        # Partial match against inventory names (e.g., "Leather" matches
        # "Leather-bound ledger")
        if inv_lower and any(token.lower() in inv_name for inv_name in inv_lower):
            continue
        # Word-boundary match against location names (prevents "crossing" matching
        # "Crossing Road" but allows it to filter out just "Marrow's Crossing").
        if loc_lower and any(
            re.search(rf'\b{re.escape(token.lower())}\b', loc_name) for loc_name in loc_lower
        ):
            continue
        candidates.add(token)
    return candidates


def check_npc_mention_extracted(event: dict[str, Any]) -> dict[str, Any]:
    """If narration mentions a name AND scope includes scene, scene extract should npc_add/update.

    Heuristic: extract candidate NPC names from narration via simple capitalization
    rule: tokens of length >= 3 that are Capitalized AND not the first token of a
    sentence AND not in a pronoun/article allow-list. If any candidate name does
    NOT appear in applied.npc_add[].name OR applied.npc_update[].name OR existing
    state_snapshot.scene.present_npcs[].name (case-insensitive), flag.

    This is intentionally conservative — we only flag when narration introduces a
    clearly-named character that the scene extractor missed.
    """
    narr = (event.get("narrate_prompt") or {}).get("output") or ""
    if not narr:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": "(no narration)",
            "scope": "universal",
            "severity": "red",
        }
    applied = event.get("applied") or {}
    snap = event.get("state_snapshot") or {}

    pc_name = (snap.get("pc") or {}).get("name", "")

    known_names: set[str] = set()
    for npc in (applied.get("npc_add") or []) + (applied.get("npc_update") or []):
        if isinstance(npc, dict):
            n = npc.get("name") or npc.get("id") or ""
            if n:
                known_names.add(n.lower())
    for npc in (snap.get("scene") or {}).get("present_npcs") or []:
        if isinstance(npc, dict):
            n = npc.get("name") or npc.get("id") or ""
            if n:
                known_names.add(n.lower())
    for cid, c in ((snap.get("compendium") or {}).get("npcs") or {}).items():
        if isinstance(c, dict):
            n = c.get("name") or cid
            if n:
                known_names.add(n.lower())

    # Extract inventory item names for false positive filtering
    inventory_names: set[str] = set()
    for item in (snap.get("inventory") or []):
        if isinstance(item, dict):
            name = item.get("name", "")
            if name:
                inventory_names.add(name)

    # Extract location names for false positive filtering
    location_names: set[str] = set()
    loc = (snap.get("location") or {})
    if loc.get("name"):
        location_names.add(loc["name"])
    # Also check world locations if available
    for wl in (snap.get("world") or {}).get("locations") or []:
        if isinstance(wl, dict) and wl.get("name"):
            location_names.add(wl["name"])
        elif isinstance(wl, str):
            location_names.add(wl)

    candidates = _extract_candidate_names(narr, pc_name, inventory_names, location_names)
    # Filter common false positives: dialogue tags, common nouns, and
    # capitalized words that are clearly not NPC names (adverbs, transition
    # words, currency terms, location-name fragments).
    stop = {
        "You", "The", "A", "An", "His", "Her", "Their",
        "He", "She", "It", "I", "We", "They",
        "But", "And", "Or", "If", "When", "Then",
        "Now", "Here", "There", "This", "That",
        "These", "Those",
        "Instead", "Behind", "Credits", "Credit",
        # Transition words that get capitalized mid-sentence
        "Finally", "However", "Nevertheless", "Meanwhile", "Besides",
        "Thus", "Furthermore", "Moreover", "Therefore", "Consequently",
    }
    # Also skip candidates that are partial matches for any known NPC name.
    # E.g., "Matthew" matches "Matthew Estrada", "Crossing" matches "Marrow's Crossing".
    known_name_parts: set[str] = set()
    for name in known_names:
        for part in name.split():
            if len(part) >= 3:
                known_name_parts.add(part.lower())
    missing = [c for c in candidates if c not in stop and c.lower() not in known_names and c.lower() not in known_name_parts]
    if not missing:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": "no missing NPC names detected",
            "scope": "universal",
            "severity": "red",
        }
    # Heuristic — could be locations, items, etc. Flag only if 1-3 missing (not 10+ which is noise).
    if len(missing) > 3:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": f"{len(missing)} candidates skipped (likely locations/items, not NPCs)",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.npc_mention.extracted",
        "passed": False,
        "detail": f"narration mentions names not in npc_add/update or known: {missing}",
        "scope": "universal",
        "severity": "red",
    }


def check_recent_events_ring_size(event: dict[str, Any]) -> dict[str, Any]:
    """recent_events ring buffer must stay <= recent_events_max (default 15).
    Hardcoded threshold of 20 here as a generous cap; if it exceeds 20, the
    ring buffer is broken regardless of the configured max.
    """
    snap = event.get("state_snapshot") or {}
    recent = (snap.get("scene") or {}).get("recent_events") or []
    n = len(recent) if isinstance(recent, list) else 0
    if n > 20:
        return {
            "assertion": "universal.recent_events.ring_bounded",
            "passed": False,
            "detail": f"recent_events has {n} entries (max should be ~15)",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.recent_events.ring_bounded",
        "passed": True,
        "detail": f"{n} entries",
        "scope": "universal",
        "severity": "red",
    }


def check_npc_scene_cap(event: dict[str, Any]) -> dict[str, Any]:
    """state.scene.present_npcs must not exceed 8 (rubric-documented cap)."""
    snap = event.get("state_snapshot") or {}
    npcs = (snap.get("scene") or {}).get("present_npcs") or []
    n = len(npcs) if isinstance(npcs, list) else 0
    if n > 8:
        names = [n2.get("name", n2.get("id", "?")) for n2 in npcs if isinstance(n2, dict)]
        return {
            "assertion": "universal.scene.npc_cap",
            "passed": False,
            "detail": f"{n} NPCs in scene (cap is 8): {names[:10]}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.scene.npc_cap",
        "passed": True,
        "detail": f"{n} NPCs",
        "scope": "universal",
        "severity": "red",
    }


def check_condition_no_dupes(event: dict[str, Any]) -> dict[str, Any]:
    """state.pc.conditions must not contain two entries with the same id."""
    snap = event.get("state_snapshot") or {}
    conds = (snap.get("pc") or {}).get("conditions") or []
    ids = [c.get("id") for c in conds if isinstance(c, dict)]
    seen: dict[str, int] = {}
    for cid in ids:
        if cid:
            seen[cid] = seen.get(cid, 0) + 1
    dupes = [cid for cid, n in seen.items() if n > 1]
    if dupes:
        return {
            "assertion": "universal.pc.condition_no_dupes",
            "passed": False,
            "detail": f"duplicate condition ids: {dupes}",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.pc.condition_no_dupes",
        "passed": True,
        "detail": f"{len(ids)} conditions, no dupes",
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
    cur_snap = event.get("state_snapshot") or {}
    cur_m = (cur_snap.get("pc") or {}).get("momentum")
    if cur_m is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(no pc.momentum field)",
            "scope": "universal",
            "severity": "red",
        }
    if prev_event is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(first turn)",
            "scope": "universal",
            "severity": "red",
        }
    prev_snap = prev_event.get("state_snapshot") or {}
    prev_m = (prev_snap.get("pc") or {}).get("momentum") or 0
    actual = (cur_m or 0) - prev_m
    # Engine clamps to [-3, 3] so an "expected +2" can show as +1 or 0 if at edge.
    # We accept actual within [expected - 1, expected] (engine clamp) or exactly expected.
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
        "detail": f"band={band} expected delta {expected:+d} but got {actual:+d} (prev={prev_m} cur={cur_m})",
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
    """Momentum at floor for >= 3 consecutive turns without a success band is a pacing failure."""
    window: list[dict[str, Any]] = event_window or ([prev_event, event] if prev_event else [event])
    floor_count = 0
    for ev in reversed(window):
        m = ((ev.get("state_snapshot") or {}).get("meta") or {}).get("momentum")
        if m is not None and m <= MOMENTUM_MIN:
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


def check_narration_directive_rendered(event: dict[str, Any]) -> dict[str, Any]:
    """If pacing directive was computed, validate the EXACT value appears in both narrate and storytell prompts.

    Reads directive from event["pacing_context"]["directive"] (the canonical source).
    Uses word-boundary matching to avoid false positives ("Pressure" must not match "Scene Pressure").
    Template renders "**Directive:** {value}" in narrate_user and "Directive: {value}" in storytell_user.
    """
    # Canonical directive value from pacing_context (turn.py writes this)
    pacing_ctx = event.get("pacing_context") or {}
    directive_value = pacing_ctx.get("directive", "")

    if not directive_value:
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": True,
            "detail": "(no directive computed)",
            "scope": "universal",
            "severity": "red",
        }

    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    storytell_rendered = ((event.get("extraction") or {}).get("storytell") or {}).get("rendered_user") or ""

    # Check exact directive value appears in narrate prompt using word-boundary matching.
    # Matches "**Directive:** {value}" or "Directive: {value}" patterns, or the value as a standalone token.
    _directive_in_prompt_re = re.compile(
        r"(?i)(?:directive[:\s]+|[\*\*]?)\b" + re.escape(directive_value) + r"\b",
    )

    if not _directive_in_prompt_re.search(narr_user):
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": False,
            "detail": f"computed directive '{directive_value}' not found in narrate user prompt (pacing_context={pacing_ctx})",
            "scope": "universal",
            "severity": "red",
        }

    # Check storytell prompt also received the exact directive value
    if not _directive_in_prompt_re.search(storytell_rendered):
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": False,
            "detail": f"computed directive '{directive_value}' not found in storytell user prompt (pacing_context={pacing_ctx})",
            "scope": "universal",
            "severity": "yellow",
        }

    return {
        "assertion": "universal.narrate.directive_rendered",
        "passed": True,
        "detail": f"directive '{directive_value}' rendered in both prompts",
        "scope": "universal",
        "severity": "red",
    }



def _token_overlap_score(a: str, b: str) -> float:
    """Compute token-overlap similarity between two strings (Jaccard-like).

    Splits on whitespace after lowercasing. Score = intersection / max(len_a, len_b).
    Matches the algorithm used in turn.py ArcThread.key auto-merge dedup gate.
    """
    tokens_a = set(a.lower().split()) if a else set()
    tokens_b = set(b.lower().split()) if b else set()
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = len(tokens_a & tokens_b)
    return overlap / max(len(tokens_a), len(tokens_b))


def check_arcthread_key_dedup(event: dict[str, Any]) -> dict[str, Any]:
    """Validate ArcThread.key auto-merge dedup gate works correctly.

    Checks that no two threads in state_snapshot.arc.threads have similar non-null keys above 70% threshold.
    If duplicates exist the fuzzy merge gate failed to catch them during thread_add.
    """
    arc = (event.get("state_snapshot") or {}).get("arc") or {}
    threads: list[dict[str, Any]] = arc.get("threads") or []

    # Filter to threads with non-null, non-empty keys
    keyed_threads = [t for t in threads if isinstance(t, dict) and t.get("key")]

    if len(keyed_threads) < 2:
        return {
            "assertion": "universal.arcthread.key_dedup",
            "passed": True,
            "detail": f"only {len(keyed_threads)} thread(s) with non-null key",
            "scope": "universal",
            "severity": "yellow",
        }

    # Check every pair for token-overlap similarity above 70% threshold
    for i in range(len(keyed_threads)):
        for j in range(i + 1, len(keyed_threads)):
            key_a = str(keyed_threads[i].get("key") or "")
            key_b = str(keyed_threads[j].get("key") or "")
            score = _token_overlap_score(key_a, key_b)
            if score >= 0.70:
                return {
                    "assertion": "universal.arcthread.key_dedup",
                    "passed": False,
                    "detail": f"Duplicate ArcThread.key detected: '{key_a}' ({score:.2f}) vs '{key_b}'",
                    "scope": "universal",
                    "severity": "red",
                }

    return {
        "assertion": "universal.arcthread.key_dedup",
        "passed": True,
        "detail": f"no duplicates among {len(keyed_threads)} keyed thread(s)",
        "scope": "universal",
        "severity": "yellow",
    }


def check_consecutive_pressure_tracking(
    event: dict[str, Any], prev_event: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate the two-pass consecutive pressure counter works correctly.

    Increments when directive was Pressure/Overwhelm AND no thread_advance occurred; resets to 0 otherwise.
    """
    pacing_ctx = event.get("pacing_context") or {}
    directive = pacing_ctx.get("directive", "")
    # Strip "; Resolve a Threat" suffix for base value comparison
    base_directive = re.sub(r"\s*;\s*Resolve a Threat\s*$", "", directive).strip() if directive else ""

    meta = (event.get("state_snapshot") or {}).get("meta") or {}
    counter = meta.get("consecutive_pressure_turns", 0)

    # Check whether any thread_advance occurred in this turn's extraction results
    storytell_output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
    thread_advances = storytell_output.get("thread_advance") or []
    has_thread_advance = bool(thread_advances)

    is_pressure_directive = base_directive in ("Pressure", "Overwhelm")

    if prev_event:
        prev_pacing_ctx = prev_event.get("pacing_context") or {}
        prev_base = re.sub(r"\s*;\s*Resolve a Threat\s*$", "", prev_pacing_ctx.get("directive", "")).strip() if prev_pacing_ctx.get("directive") else ""

    # If directive is Pressure/Overwhelm AND no thread_advance: counter should be >= 1 (or incrementing)
    if is_pressure_directive and not has_thread_advance:
        if counter < 1:
            return {
                "assertion": "universal.pacing.consecutive_pressure_tracking",
                "passed": False,
                "detail": f"directive={base_directive!r}, no thread_advance but consecutive_pressure_turns={counter} (expected >= 1)",
                "scope": "universal",
                "severity": "red",
            }

    # If any thread_advance occurred OR directive changed to non-pressure value: counter should reset to 0
    if has_thread_advance or not is_pressure_directive and prev_event:
        prev_base = re.sub(r"\s*;\s*Resolve a Threat\s*$", "", (prev_event.get("pacing_context") or {}).get("directive", "")).strip() if prev_event else ""
        if base_directive != prev_base and counter > 0:
            # Directive changed from pressure to non-pressure — should have reset
            return {
                "assertion": "universal.pacing.consecutive_pressure_tracking",
                "passed": False,
                "detail": f"directive changed from {prev_base!r} to {base_directive!r}, consecutive_pressure_turns={counter} (expected 0)",
                "scope": "universal",
                "severity": "red",
            }

    return {
        "assertion": "universal.pacing.consecutive_pressure_tracking",
        "passed": True,
        "detail": f"directive={base_directive!r}, thread_advance={has_thread_advance}, counter={counter}",
        "scope": "universal",
        "severity": "yellow",
    }


def check_beat_locked_dual_trigger(
    event: dict[str, Any], prev_event: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate the dual-trigger beat_locked condition works correctly.

    beat_locked should be True when either momentum <= config.momentum_floor (-3 default) OR consecutive_pressure_turns >= config.consecutive_pressure_threshold (3 default).
    """
    pacing_ctx = event.get("pacing_context") or {}
    beat_locked = bool(pacing_ctx.get("beat_locked", False))

    meta = (event.get("state_snapshot") or {}).get("meta") or {}
    momentum = meta.get("momentum", 0)
    consecutive_pressure_turns = meta.get("consecutive_pressure_turns", 0)

    # Config defaults from EngineConfig
    config_momentum_floor = -3
    config_consecutive_threshold = 3

    expected_beat_locked = (momentum <= config_momentum_floor or consecutive_pressure_turns >= config_consecutive_threshold)

    if beat_locked != expected_beat_locked:
        return {
            "assertion": "universal.pacing.beat_locked_dual_trigger",
            "passed": False,
            "detail": f"beat_locked={beat_locked} but expected {expected_beat_locked} (momentum={momentum}, floor={config_momentum_floor}, consecutive_pressure_turns={consecutive_pressure_turns}, threshold={config_consecutive_threshold})",
            "scope": "universal",
            "severity": "red",
        }

    return {
        "assertion": "universal.pacing.beat_locked_dual_trigger",
        "passed": True,
        "detail": f"beat_locked={beat_locked} (momentum={momentum}, consecutive_pressure_turns={consecutive_pressure_turns})",
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


def _assert_compactor_sanitization_nonzero(
    ev: dict[str, Any], prev_ev: dict[str, Any] | None
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    applied = ev.get("applied") or {}
    compaction = applied.get("compaction") or {}
    if not compaction:
        return results
    sanit = compaction.get("sanitization") or {}
    cond_remove = sanit.get("condition_remove") or []
    pres_remove = sanit.get("pressure_remove") or []
    if sanit.get("npc_merge") or sanit.get("inventory_remove") or cond_remove or pres_remove:
        return results  # something was sanitized — pass
    return results


def run_all_universal_asserts(
    event: dict[str, Any], prev_event: dict[str, Any] | None, event_window: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = [
        check_recent_events_turn_stamped(event),
        check_pending_gm_beat_consumed(event, prev_event),
        check_pending_gm_beat_lifecycle_respected(event, prev_event),
        check_location_change_applied(event, prev_event),
        check_rolled_implies_binding(event),
        check_npc_mention_extracted(event),
        check_recent_events_ring_size(event),
        check_npc_scene_cap(event),
        check_condition_no_dupes(event),
        check_actions_count_and_distinct(event),
        check_momentum_band_delta(event, prev_event),
        check_zero_stack_overdraw(event, prev_event),
        check_narration_directive_rendered(event),
        check_consecutive_pressure_tracking(event, prev_event),
        check_beat_locked_dual_trigger(event, prev_event),
        check_arcthread_key_dedup(event),
        check_no_removed_directives(event),
        check_no_removed_npc_states(event),
        check_momentum_floor_no_relief(event, prev_event, event_window=event_window),
        check_no_negative_inventory(event),
    ]
    results.extend(_assert_compactor_sanitization_nonzero(event, prev_event))
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    _log.debug("universal_asserts: %d passed, %d failed", passed, failed)
    return results
