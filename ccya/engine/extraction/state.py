"""Stream 2: State extraction messages (inventory + conditions)."""

from __future__ import annotations

from jinja2 import Environment
from typing import Any

from ccya.engine.config import _render
from ccya.models import IntentEnvelope


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    intent: "IntentEnvelope | None" = None,
    turn_no: int = 0,
    pack_inventory: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions + location)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}

    system_text = _render(env, "extract_state_system.j2", {
        "pack_inventory": pack_inventory,
    })
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "location": location,
            "intent": intent,
            "turn_no": turn_no,
            "pc_name": pc.get("name", "Unnamed"),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
