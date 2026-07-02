"""Stream 2: State extraction messages (inventory + conditions)."""

from __future__ import annotations

from typing import Any

from jinja2 import Environment

from ccya.engine.config import _render
from ccya.models import IntentEnvelope, WorldState


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: WorldState,
    *,
    intent: "IntentEnvelope | None" = None,
    turn_no: int = 0,
    pack_inventory: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions + location)."""
    pc = state.pc
    location = state.location.model_dump()

    system_text = _render(env, "extract_state_system.j2", {
        "pack_inventory": pack_inventory,
    })
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "conditions": [c.model_dump() for c in pc.conditions],
            "inventory": [it.model_dump() for it in state.inventory],
            "location": location,
            "intent": intent,
            "turn_no": turn_no,
            "pc_name": pc.name or "Unnamed",
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
