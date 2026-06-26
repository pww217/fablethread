"""prompt_context.py — Build context dicts for prompt rendering.

Shared by prompt_eval.py (LLM eval) and deterministic checkers
(pacing_directives, gm_beat_lifecycle) that re-render prompts via Jinja2.
"""

from __future__ import annotations

import sys
from typing import Any

from ccya.ev.events import find_turn

_PRESENCE_SORT = {"present": 0, "nearby": 2, "known": 3, "departed": 5}


def _find_prev_event(events: list[dict[str, Any]], turn_no: int) -> dict[str, Any] | None:
    """Find the immediately preceding turn event."""
    for ev in reversed(events):
        if isinstance(ev.get("turn"), int) and ev["turn"] < turn_no:
            return ev
    return None


def _build_npc_roster(comp: dict[str, Any]) -> list[dict[str, Any]]:
    """Build an NPC roster from the compendium, matching engine shape."""
    entries: list[dict[str, Any]] = []
    for nid, ndata in comp.items():
        presence = ndata.get("presence", "known")
        if presence == "archived":
            continue
        bio = ndata.get("bio") or ndata.get("description", "")
        entry = {
            "id": nid,
            "name": ndata.get("name", nid),
            "title": ndata.get("title", ""),
            "presence": presence,
            "bio": bio,
            "notes": ndata.get("notes", ndata.get("position", "")),
            "position": ndata.get("position", ""),
            "motivation": ndata.get("wants", ""),
            "fear": ndata.get("fears", ""),
            "leverage": ndata.get("leverage", ""),
            "bond": ndata.get("bond", ""),
            "personality_label": "",
            "personality_traits": "",
            "personality_speech_hint": "",
            "last_presence_turn": ndata.get("last_presence_turn"),
            "last_seen_location": ndata.get("last_seen_location", ""),
        }
        entries.append(entry)
    entries.sort(key=lambda e: (_PRESENCE_SORT.get(e["presence"], 9), e["name"]))
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
    - conditions/inventory reflect post-storytell state (close to pre-storytell)
    - NPC roster lacks personality archetype enrichment
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

    narration = (turn_ev.get("narrate") or {}).get("output", "")
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

    if stream == "storytell":
        arc = prev_snap.get("arc") or {}
        scene = prev_snap.get("scene") or {}
        meta = prev_snap.get("meta") or {}
        pc = prev_snap.get("pc") or {}
        # Format thread progress like _storytell_messages does
        all_threads = []
        for t in (arc.get("threads") or []):
            if isinstance(t, dict):
                entry = dict(t)
                entry.setdefault("last_updated_turn", None)
                from ccya.prompts.context import _fmt_progress
                entry["progress"] = _fmt_progress(entry.get("major_updates"))
                all_threads.append(entry)
            else:
                all_threads.append({"id": "", "summary": ""})
        # Build NPC roster from compendium
        comp = prev_snap.get("compendium", {}).get("npcs", {})
        npc_roster = _build_npc_roster(comp)
        # Compute curtain_call like the engine does
        curtain_call = ""
        scene_phase = turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP")
        if scene_phase == "CLIMAX":
            climax_turn_count = scene.get("climax_turn_count", 0)
            climax_turn_limit = scene.get("climax_turn_limit", 5)
            if climax_turn_count >= climax_turn_limit - 1:
                curtain_call = "forced"
            elif climax_turn_count == 1:
                curtain_call = "active"
        # Build recent_turns from previous turn narrations
        recent_turns = []
        for ev in reversed(events):
            if isinstance(ev.get("turn"), int) and ev["turn"] < turn_no:
                narr = (ev.get("narrate") or {}).get("output", "")
                if narr:
                    recent_turns.append({"turn": ev["turn"], "narrative": narr})
                if len(recent_turns) >= 10:
                    break
        recent_turns = list(reversed(recent_turns))
        return {
            "narration": narration,
            "npc_roster": npc_roster,
            "location": prev_snap.get("location") or {},
            "inventory": prev_snap.get("inventory") or [],
            "conditions": list(pc.get("conditions") or []),
            "current_objective": arc,
            "all_threads": all_threads,
            "world_state": list(scene.get("world_state") or []),
            "resolved_arcs": [],
            "intent": intent if isinstance(intent, dict) else None,
            "pacing_context": turn_ev.get("pacing_context") or {},
            "recent_turns": recent_turns,
            "prior_history": list((meta.get("prior_history") or [])[:-1]),
            # Use previous turn's pending_beat (pre-turn) not current (post-turn)
            "pending_beat": prev_meta.get("pending_gm_beat"),
            # Use previous turn's recent_beats (pre-turn, excludes current turn's beat)
            "recent_beats": list(prev_meta.get("recent_beats") or []),
            "turn_no": turn_no,
            # Read band from current turn's ruling outcome
            "band": (turn_ev.get("ruling") or {}).get("band", ""),
            "scene_phase": scene_phase,
            "curtain_call": curtain_call,
            "allowed_beat_types": turn_ev.get("allowed_beat_types") or [],
            "state": prev_snap,
            "pc_name": pc.get("name", "Unnamed"),
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
            "scene_phase": prev_snap.get("scene", {}).get("scene_phase", "SETUP"),
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
        curtain_call = ""
        if scene.get("scene_phase") == "CLIMAX":
            climax_turn_count = scene.get("climax_turn_count", 0)
            climax_turn_limit = scene.get("climax_turn_limit", 5)
            if climax_turn_count >= climax_turn_limit - 1:
                curtain_call = "forced"
            elif climax_turn_count == 1:
                curtain_call = "active"
        return {
            "state": prev_snap,
            "pc": pc,
            "prior_history": list((meta.get("prior_history") or [])[:-1]),
            "recent_turns": [],
            "rules_outcome": _build_rules_outcome(turn_ev),
            "npc_name_pool": {},
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
            "curtain_call": curtain_call,
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
        scene_phase = turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP")
        # Get candidate_npcs from scene extraction
        scene_ev = turn_ev.get("extraction", {}).get("scene", {})
        candidate_npcs = scene_ev.get("output", {}).get("candidate_npcs", []) if isinstance(scene_ev.get("output"), dict) else []
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
            "candidate_npcs": candidate_npcs,
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
