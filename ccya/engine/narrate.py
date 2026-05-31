"""Narration prompt building and NPC name generation helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ccya.engine.config import _render
from ccya.engine.npc_roster import build_npc_roster

from ccya.models import RulesOutcome

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ccya.engine.turn import PacingContext


def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    recent_turns: list[dict[str, Any]] = [],
    narrator_rules: list[str] = [],
    world_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    momentum: int = 0,
    pending_beat: dict[str, Any] | None = None,
    pacing_context: "PacingContext | None" = None,
    ages: dict[str, int] | None = None,
    pc_allegiance: str | None = None,
    turn_no: int = 0,
    world_factions: list[dict[str, str]] = [],
    npc_roster: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    if npc_roster is None:
        comp = (state.get("compendium") or {}).get("npcs") or {}
        npc_roster = build_npc_roster(comp)
    _log.debug(
        "narrate entry turn=%d npc_roster_len=%d",
        turn_no, len(npc_roster),
    )

    # Build arc context for narrator (needed by both system and user prompts)
    arc = state.get("arc") or {}
    if arc:
        all_threads = [t for t in (arc.get("threads") or [])]
        current_arc_ctx = {
            "visible_goal": arc.get("visible_goal", ""),
            "thematic_question": arc.get("thematic_question", ""),
            "resolution": arc.get("resolution"),
            "resolved_arc": _get_resolved_arc(state, turn_no),
            "threads": [
                {
                    "summary": t.get("summary", "") if isinstance(t, dict) else getattr(t, "summary", ""),
                    "urgency": t.get("urgency", "normal") if isinstance(t, dict) else getattr(t, "urgency", "normal"),
                    "tags": t.get("tags", []) if isinstance(t, dict) else getattr(t, "tags", []),
                    "scope": t.get("scope", "arc") if isinstance(t, dict) else getattr(t, "scope", "arc"),
                    "id": t.get("id", "") if isinstance(t, dict) else getattr(t, "id", ""),
                    "active": t.get("active", True) if isinstance(t, dict) else getattr(t, "active", True),
                }
                for t in all_threads if not (isinstance(t, dict) and t.get("active") is False) or not hasattr(t, "active") or getattr(t, "active", True)
            ],
            "completed_threads": _filter_completed_threads(arc, turn_no),
        }
    else:
        current_arc_ctx = None

    user_ctx = {
        "state": state,
        "pc": state.get("pc") or {},
        "prior_history": list((state.get("meta") or {}).get("prior_history") or [])[:-1],
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "user_input": user_input,
        "momentum": momentum,
        "pending_beat": pending_beat,
        "pacing_context": pacing_context,
        "meta": {"turn": turn_no},
        "scene": state.get("scene", {}),
        "ages": ages or {},
        "pc_allegiance": pc_allegiance,
        "world_factions": world_factions,
        "npc_roster": npc_roster,
        "current_arc": current_arc_ctx,
    }

    system_text = _render(env, "narrate_system.j2", {
        "narrator_rules": narrator_rules,
        "world_rules": world_rules,
        "current_arc": current_arc_ctx,
    })
    user_text = _render(env, "narrate_user.j2", user_ctx)
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if not msgs or not any(m.get("content") for m in msgs):
        _log.warning("narrate messages list is empty or has no content turn=%d", turn_no)
    else:
        _log.debug("narrate complete turn=%d messages=%d", turn_no, len(msgs))

    return msgs


def _filter_completed_threads(arc: dict[str, Any], turn_no: int) -> list[dict[str, Any]]:
    """Filter completed threads by TTL — only include recent ones."""
    # Use a default config for TTL value; actual config comes through caller context
    ttl = 3
    raw_threads = arc.get("completed_threads") or []
    result: list[dict[str, Any]] = []
    for t in raw_threads:
        resolved_turn = t.get("resolved_turn") if isinstance(t, dict) else getattr(t, "resolved_turn", None)
        if resolved_turn is not None and (turn_no - resolved_turn) <= ttl:
            result.append(dict(t) if isinstance(t, dict) else t.model_dump())
    return result


def _get_resolved_arc(state: dict[str, Any], turn_no: int) -> list[dict[str, Any]]:
    """Get resolved arcs from state's resolved_arcs list (TTL-filtered)."""
    ttl = 3
    resolved_arcs = state.get("resolved_arcs") or []
    if not resolved_arcs:
        return []
    result: list[dict[str, Any]] = []
    for ra in resolved_arcs:
        resolved_turn = ra.get("resolved_turn", 0)
        if (turn_no - resolved_turn) <= ttl:
            result.append(dict(ra))
    return result
