"""Stream 1: Scene extraction messages (NPC presence, location, tags)."""

from __future__ import annotations

from jinja2 import Environment
from typing import Any

from ccya.engine.config import _render
from ccya.engine.npc_roster import build_npc_roster
from ccya.personality import ARCHETYPES


def build_npc_context(
    comp: dict[str, Any],
    narration: str,
) -> list[dict[str, Any]]:
    """Extract NPC psychological context from compendium for storytell.

    Returns list of dicts with npc_id and relevant psychological fields
    (motivation, fear, leverage) that are non-empty.
    """
    context: list[dict[str, Any]] = []
    for nid, entry in comp.items():
        if not isinstance(entry, dict):
            continue
        entry_name = entry.get("name") or ""
        if not entry_name:
            continue
        fields: dict[str, Any] = {"npc_id": nid}
        fear = entry.get("fear") or ""
        motivation = entry.get("motivation") or ""
        leverage = entry.get("leverage") or ""
        if fear:
            fields["fear"] = fear
        if motivation:
            fields["motivation"] = motivation
        if leverage:
            fields["leverage"] = leverage
        if len(fields) > 1:
            context.append(fields)
    return context


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence)."""
    comp = (state.get("compendium") or {}).get("npcs") or {}
    npc_roster = build_npc_roster(comp, personality_registry=ARCHETYPES)

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "npc_roster": npc_roster,
            "turn_no": turn_no,
            "pc_name": (state.get("pc") or {}).get("name", "Unnamed"),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
