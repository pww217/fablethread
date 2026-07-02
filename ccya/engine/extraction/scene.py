"""Stream 1: Scene extraction messages (NPC presence, location, tags)."""

from __future__ import annotations

from jinja2 import Environment

from ccya.engine.config import _render
from ccya.engine.npc_roster import build_npc_roster
from ccya.models import WorldState


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: WorldState,
    *,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence)."""
    comp = {nid: entry.model_dump() for nid, entry in state.compendium.npcs.items()}
    npc_roster = build_npc_roster(comp, turn_no=turn_no)

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "npc_roster": npc_roster,
            "turn_no": turn_no,
            "pc_name": state.pc.name or "Unnamed",
            "show_all_fields": True,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
