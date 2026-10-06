"""prompt_context.py — Build context dicts for prompt rendering.

Shared by prompt_eval.py (LLM eval) and deterministic checkers
(pacing_directives, gm_beat_lifecycle) that re-render prompts via Jinja2.
"""

from __future__ import annotations

import sys
from typing import Any

from fablethread.ev.events import find_turn

_PRESENCE_SORT = {"present": 0, "nearby": 2, "known": 3, "departed": 5}


def _find_prev_event(events: list[dict[str, Any]], turn_no: int) -> dict[str, Any] | None:
    """Find the immediately preceding turn event."""
    for ev in reversed(events):
        if isinstance(ev.get("turn"), int) and ev["turn"] < turn_no:
            return ev
    return None


def _find_next_event(events: list[dict[str, Any]], turn_no: int) -> dict[str, Any] | None:
    """Find the immediately following turn event."""
    for ev in events:
        if isinstance(ev.get("turn"), int) and ev["turn"] > turn_no:
            return ev
    return None


def _build_npc_roster(comp: dict[str, Any]) -> list[dict[str, Any]]:
    """Build an NPC roster from the compendium, matching engine shape."""
    entries: list[dict[str, Any]] = []
    for nid, ndata in comp.items():
        presence = ndata.get("presence") or "known"
        if presence == "archived":
            continue
        bio = ndata.get("bio") or ndata.get("description", "")
        entry = {
            "id": nid,
            "name": ndata.get("name", nid),
            "title": ndata.get("title", ""),
            "presence": presence,
            "bio": bio,
            "disposition": ndata.get("disposition", ""),
            "notes": ndata.get("notes", ndata.get("position", "")),
            "position": ndata.get("position", ""),
            "motivation": ndata.get("wants", ""),
            "fear": ndata.get("fears", ""),
            "leverage": ndata.get("leverage", ""),
            "tie": ndata.get("tie", ""),
            "last_presence_turn": ndata.get("last_presence_turn"),
            "last_seen_location": ndata.get("last_seen_location", ""),
        }
        entries.append(entry)
    entries.sort(key=lambda e: (_PRESENCE_SORT.get(e["presence"], 9), e["name"] or ""))
    return entries[:12]


def _build_rules_outcome(turn_ev: dict[str, Any]) -> dict[str, Any] | None:
    """Build a rules_outcome dict from a ruling event, matching engine shape."""
    ruling = turn_ev.get("ruling") or {}
    if not ruling.get("rolled") and not ruling.get("impossible"):
        return None
    outcome: dict[str, Any] = {
        "rolled": ruling.get("rolled", False),
        "impossible": ruling.get("impossible", False),
        "reason": ruling.get("reason", ""),
        "band": ruling.get("band", ""),
        "directive": ruling.get("directive", ""),
        "dice": ruling.get("dice", []),
        "stat_mod": ruling.get("stat_mod", 0),
        "skill": ruling.get("skill", ""),
        "final_total": ruling.get("final_total", 0),
    }
    return outcome


def build_prompt_context(
    events: list[dict[str, Any]],
    turn_no: int,
    stream: str,
) -> dict[str, Any]:
    """Build the context dict for rendering a prompt for the given stream and turn.

    Uses the previous turn's last_turn_state for all state fields, and the
    current turn's event data for turn-specific metadata (band, scene_phase,
    allowed_beat_types).

    Known limitations:
    - conditions/inventory reflect post-record state (close to pre-record)
    - resolved_arcs not populated (needs arc_memory_ttl config)
    """
    turn_ev = find_turn(events, turn_no)
    if turn_ev is None:
        print(f"Error: turn {turn_no} not found", file=sys.stderr)
        sys.exit(1)

    # Use previous turn's last_turn_state for all state fields
    prev_ev = _find_prev_event(events, turn_no)
    prev_snap = (prev_ev.get("last_turn_state") or {}) if prev_ev else {}
    prev_meta = prev_snap.get("meta") or {}

    # Look ahead to next turn's last_turn_state for scene data (scene is computed
    # at end of turn, so it's in the next turn's state)
    next_ev = _find_next_event(events, turn_no)
    next_snap = (next_ev.get("last_turn_state") or {}) if next_ev else {}
    next_scene = next_snap.get("scene") or {}

    narration = (turn_ev.get("narrate") or {}).get("prose", "")
    intent = (turn_ev.get("ruling") or {}).get("intent")

    if stream == "scene":
        pc = prev_snap.get("pc") or {}
        comp = prev_snap.get("compendium", {}).get("npcs", {})
        npc_roster = _build_npc_roster(comp)
        pc_name = pc.get("name", "Unnamed")
        return {
            "narration": narration,
            "location": prev_snap.get("location") or {},
            "npc_roster": npc_roster,
            "pc_name": pc_name,
            "turn_no": turn_no,
        }

    if stream == "record":
        arc = prev_snap.get("arc") or {}
        pc = prev_snap.get("pc") or {}
        # Format thread progress like record context building does
        all_threads = []
        for t in (arc.get("threads") or []):
            if isinstance(t, dict):
                entry = dict(t)
                entry.setdefault("last_updated_turn", None)
                from fablethread.prompts.context import _fmt_progress
                entry["progress"] = _fmt_progress(entry.get("major_updates"))
                all_threads.append(entry)
            else:
                all_threads.append({"id": "", "summary": ""})
        return {
            "pc_name": pc.get("name", "Unnamed"),
            "all_threads": all_threads,
            "world_state": list(prev_snap.get("scene", {}).get("world_state") or []),
            "band": (turn_ev.get("ruling") or {}).get("band", ""),
            "scene_phase": turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP"),
            "prior_history": list((prev_meta.get("prior_history") or [])[:-1]),
            "narration": narration,
            "turn_no": turn_no,
        }

    if stream == "ruling":
        comp = prev_snap.get("compendium", {}).get("npcs", {})
        npc_roster = _build_npc_roster(comp)
        arc = prev_snap.get("arc") or {}
        pc = prev_snap.get("pc") or {}
        urgent_threads = [
            {"id": t.get("id", ""), "summary": t.get("summary", ""), "progress": t.get("major_updates", [])}
            for t in (arc.get("threads") or []) if t.get("urgency") == "urgent"
        ]
        return {
            "pc": pc,
            "location": prev_snap.get("location") or {},
            "user_input": "",
            "meta": {"turn": turn_no},
            "npc_roster": npc_roster,
            "inventory": prev_snap.get("inventory") or [],
            "recent_turns": [],
            "scene_phase": turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP"),
            "urgent_threads": urgent_threads,
            "state": prev_snap,
        }

    if stream == "narrate":
        comp = prev_snap.get("compendium", {}).get("npcs", {})
        npc_roster = _build_npc_roster(comp)
        arc = prev_snap.get("arc") or {}
        scene = prev_snap.get("scene") or {}
        meta = prev_snap.get("meta") or {}
        pc = prev_snap.get("pc") or {}
        # Merge scene data from next turn's last_turn_state into state for templates
        turn_scene = turn_ev.get("scene") or {}
        state_with_scene = {**prev_snap, "scene": {**scene, **turn_scene, **next_scene}}
        current_objective_ctx = None
        if arc:
            all_threads = [t for t in (arc.get("threads") or [])]
            current_objective_ctx = {
                "long_term_objective": arc.get("long_term_objective", ""),
                "resolution": arc.get("resolution"),
                "resolved_arcs": [],
                "threads": [
                    {
                        "summary": t.get("summary", "") if isinstance(t, dict) else getattr(t, "summary", ""),
                        "urgency": t.get("urgency", "normal") if isinstance(t, dict) else getattr(t, "urgency", "normal"),
                        "type": t.get("type") if isinstance(t, dict) else getattr(t, "type", None),
                        "id": t.get("id", "") if isinstance(t, dict) else getattr(t, "id", ""),
                        "dormant": t.get("dormant", False) if isinstance(t, dict) else getattr(t, "dormant", False),
                        "progress": [],
                        "last_updated_turn": t.get("last_updated_turn") if isinstance(t, dict) else getattr(t, "last_updated_turn", None),
                    }
                    for t in all_threads
                ],
                "completed_threads": [],
            }
        return {
            "state": state_with_scene,
            "pc": pc,
            "prior_history": list((meta.get("prior_history") or [])[:-1]),
            "recent_turns": [],
            "rules_outcome": _build_rules_outcome(turn_ev),
            "user_input": "",
            "pending_beat": prev_meta.get("pending_gm_beat"),
            "pacing_context": turn_ev.get("pacing_context") or {},
            "turn_no": turn_no,
            "meta": {"turn": turn_no},
            "scene": prev_snap.get("scene", {}),
            "ages": {},
            "pc_allegiance": None,
            "world_factions": [],
            "npc_roster": npc_roster,
            "current_objective": current_objective_ctx,
            "resolved_arcs": [],
            "location": prev_snap.get("location") or {},
            "inventory": prev_snap.get("inventory") or [],
            "conditions": list(pc.get("conditions") or []),
        }

    if stream == "state":
        pc = prev_snap.get("pc") or {}
        return {
            "narration": narration,
            "conditions": list(pc.get("conditions") or []),
            "inventory": prev_snap.get("inventory") or [],
            "location": prev_snap.get("location") or {},
            "intent": intent if isinstance(intent, dict) else None,
            "turn_no": turn_no,
            "state": prev_snap,
            "pc_name": pc.get("name", "Unnamed"),
        }

    if stream == "world":
        arc = prev_snap.get("arc") or {}
        meta = prev_snap.get("meta") or {}
        # Build NPC roster from compendium
        comp = prev_snap.get("compendium", {}).get("npcs", {})
        npc_roster = _build_npc_roster(comp)
        npc_roster = [n for n in npc_roster if n.get("presence") in ("present", "nearby")]
        # Get recent_beats from state
        recent_beats = list(meta.get("recent_beats") or [])
        # Get allowed_beat_types from turn event
        allowed_beat_types = turn_ev.get("allowed_beat_types") or []
        # Get rules_outcome from state
        rules_outcome = meta.get("last_rules_outcome") or {}
        if isinstance(rules_outcome, dict):
            rules_outcome = {
                "band": rules_outcome.get("band", ""),
                "rolled": bool(rules_outcome.get("rolled", False)),
            }
        else:
            rules_outcome = {}
        return {
            "narration": narration,
            "npc_roster": npc_roster,
            "arc": arc,
            "pacing_context": turn_ev.get("pacing_context") or {},
            "recent_beats": recent_beats,
            "allowed_beat_types": allowed_beat_types,
            "rules_outcome": rules_outcome,
            "turn_no": turn_no,
            "state": prev_snap,
        }

    # Placeholder for future streams — fail loudly if used
    print(f"Error: stream '{stream}' not yet implemented in build_prompt_context()", file=sys.stderr)
    sys.exit(1)
