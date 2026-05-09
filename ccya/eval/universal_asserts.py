"""Universal cross-pipeline assertions that apply to every event.

Each function returns dict[str, Any] with keys: assertion, passed, detail, scope.
`scope` is always 'universal'. If passed=True, the assertion is informational;
the runner discards passes and surfaces only failures.

These catch known classes of mechanical bugs without requiring scenario
authors to write per-turn asserts. Designed to be cheap and high-signal.
"""

from __future__ import annotations

import re
from typing import Any


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
        }
    if bad:
        return {
            "assertion": "universal.recent_events_add.turn_stamped",
            "passed": False,
            "detail": f"{len(bad)} entries had turn=0/null instead of {cur_turn}: {bad[:3]}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.recent_events_add.turn_stamped",
        "passed": True,
        "detail": f"all {len(adds)} entries stamped with turn={cur_turn}",
        "scope": "universal",
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
        }
    if cur_beat == prev_beat:
        return {
            "assertion": "universal.pending_gm_beat.consumed",
            "passed": False,
            "detail": f"beat persisted unchanged across turns: {prev_beat}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.pending_gm_beat.consumed",
        "passed": True,
        "detail": "beat consumed or replaced",
        "scope": "universal",
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
        }
    if prev_event is None:
        return {
            "assertion": "universal.location_change.applied",
            "passed": True,
            "detail": "(first turn)",
            "scope": "universal",
        }
    prev_loc = ((prev_event.get("state_snapshot") or {}).get("location") or {}).get("id")
    cur_loc = ((event.get("state_snapshot") or {}).get("location") or {}).get("id")
    if cur_loc == prev_loc:
        return {
            "assertion": "universal.location_change.applied",
            "passed": False,
            "detail": f"location_change emitted but state.location.id unchanged: {cur_loc}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.location_change.applied",
        "passed": True,
        "detail": f"{prev_loc} -> {cur_loc}",
        "scope": "universal",
    }


def check_rolled_implies_binding(event: dict[str, Any]) -> dict[str, Any]:
    """If rules.rolled=true, narrate_prompt.rendered_user must contain 'rules_outcome (BINDING'."""
    rules = event.get("rules") or {}
    if not rules.get("rolled"):
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "(no roll)",
            "scope": "universal",
        }
    nu = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if "rules_outcome (BINDING" in nu:
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "binding directive included",
            "scope": "universal",
        }
    return {
        "assertion": "universal.narrate.binding_present",
        "passed": False,
        "detail": "rolled=true but narrate user prompt did not include rules_outcome BINDING block",
        "scope": "universal",
    }


def _extract_candidate_names(narration: str, pc_name: str) -> set[str]:
    """Extract capitalized tokens that are candidates for NPC names.

    Excludes the PC name (case-insensitive) and sentence-initial words
    to reduce false positives from tokens like 'Who', 'Instead', 'Your'.

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

    candidates: set[str] = set()
    for token in re.findall(r'\b[A-Z][a-z]{2,}\b', narration):
        if token.lower() == pc_name.lower():
            continue
        if token in sentence_starters:
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

    candidates = _extract_candidate_names(narr, pc_name)
    # Filter common false positives: dialogue tags, common nouns.
    stop = {
        "You", "The", "A", "An", "His", "Her", "Their",
        "He", "She", "It", "I", "We", "They",
        "But", "And", "Or", "If", "When", "Then",
        "Now", "Here", "There", "This", "That",
        "These", "Those",
    }
    missing = [c for c in candidates if c not in stop and c.lower() not in known_names]
    if not missing:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": "no missing NPC names detected",
            "scope": "universal",
        }
    # Heuristic — could be locations, items, etc. Flag only if 1-3 missing (not 10+ which is noise).
    if len(missing) > 3:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": f"{len(missing)} candidates skipped (likely locations/items, not NPCs)",
            "scope": "universal",
        }
    return {
        "assertion": "universal.npc_mention.extracted",
        "passed": False,
        "detail": f"narration mentions names not in npc_add/update or known: {missing}",
        "scope": "universal",
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
        }
    return {
        "assertion": "universal.recent_events.ring_bounded",
        "passed": True,
        "detail": f"{n} entries",
        "scope": "universal",
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
        }
    return {
        "assertion": "universal.scene.npc_cap",
        "passed": True,
        "detail": f"{n} NPCs",
        "scope": "universal",
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
        }
    return {
        "assertion": "universal.pc.condition_no_dupes",
        "passed": True,
        "detail": f"{len(ids)} conditions, no dupes",
        "scope": "universal",
    }


def check_actions_count_and_distinct(event: dict[str, Any]) -> dict[str, Any]:
    """progress.actions must contain exactly 4 distinct entries."""
    actions = event.get("actions") or []
    if not isinstance(actions, list):
        return {
            "assertion": "universal.progress.actions_quality",
            "passed": False,
            "detail": "actions is not a list",
            "scope": "universal",
        }
    n = len(actions)
    distinct = len(set(actions))
    if n != 4:
        return {
            "assertion": "universal.progress.actions_quality",
            "passed": False,
            "detail": f"actions has {n} entries (expected 4)",
            "scope": "universal",
        }
    if distinct != n:
        return {
            "assertion": "universal.progress.actions_quality",
            "passed": False,
            "detail": f"actions has {n - distinct} duplicate(s): {actions}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.progress.actions_quality",
        "passed": True,
        "detail": "4 distinct actions",
        "scope": "universal",
    }


def check_momentum_band_delta(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """If a roll happened, momentum should change per band: crit_success +2,
    success +1, partial 0, setback/fail -1, crit_fail -2."""
    rules = event.get("rules") or {}
    if not rules.get("rolled"):
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(no roll)",
            "scope": "universal",
        }
    band = rules.get("band", "")
    expected = {
        "crit_success": 2,
        "success": 1,
        "partial": 0,
        "setback": -1,
        "fail": -1,
        "crit_fail": -2,
    }.get(band)
    if expected is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": f"(unknown band {band!r})",
            "scope": "universal",
        }
    cur_snap = event.get("state_snapshot") or {}
    cur_m = (cur_snap.get("meta") or {}).get("momentum")
    if cur_m is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(no momentum field)",
            "scope": "universal",
        }
    if prev_event is None:
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": "(first turn)",
            "scope": "universal",
        }
    prev_snap = prev_event.get("state_snapshot") or {}
    prev_m = (prev_snap.get("meta") or {}).get("momentum") or 0
    actual = (cur_m or 0) - prev_m
    # Engine clamps to [-3, 3] so an "expected +2" can show as +1 or 0 if at edge.
    # We accept actual within [expected - 1, expected] (engine clamp) or exactly expected.
    if actual == expected or (expected > 0 and 0 <= actual <= expected) or (expected < 0 and expected <= actual <= 0):
        return {
            "assertion": "universal.momentum.band_delta",
            "passed": True,
            "detail": f"band={band} delta={actual} (expected {expected:+d}, engine may clamp)",
            "scope": "universal",
        }
    return {
        "assertion": "universal.momentum.band_delta",
        "passed": False,
        "detail": f"band={band} expected delta {expected:+d} but got {actual:+d} (prev={prev_m} cur={cur_m})",
        "scope": "universal",
    }


def run_all_universal_asserts(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> list[dict[str, Any]]:
    return [
        check_recent_events_turn_stamped(event),
        check_pending_gm_beat_consumed(event, prev_event),
        check_location_change_applied(event, prev_event),
        check_rolled_implies_binding(event),
        check_npc_mention_extracted(event),
        check_recent_events_ring_size(event),
        check_npc_scene_cap(event),
        check_condition_no_dupes(event),
        check_actions_count_and_distinct(event),
        check_momentum_band_delta(event, prev_event),
    ]
