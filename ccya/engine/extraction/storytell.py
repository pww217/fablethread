"""Stream 3: Storytell extraction messages (thread signals + facts + actions + outcome_summary)."""

from __future__ import annotations

import logging
from jinja2 import Environment
from typing import Any

from ccya.engine._pacing import derive_allowed_beat_types
from ccya.engine.config import EngineConfig, _render
from ccya.engine.extraction.context import _ExtractionContext
from ccya.engine.extraction.utils import _filter_evicted_threads
from ccya.engine.narrate import _get_resolved_arcs
from ccya.engine.npc_roster import build_npc_roster
from ccya.models import IntentEnvelope
from ccya.personality import ARCHETYPES
from ccya.prompts.context import _fmt_progress

_log = logging.getLogger(__name__)


def _storytell_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    extraction_ctx: _ExtractionContext,
    intent: IntentEnvelope | None = None,
    pacing_context: Any | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    band: str = "",
    arc_ttl: int = 3,
    config: EngineConfig | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (thread signals + facts + actions + outcome_summary)."""
    scene = state.get("scene") or {}

    arc = state.get("arc") or {}
    _raw_threads = arc.get("threads") or []
    all_threads: list[dict[str, Any]] = []
    for t in _raw_threads:
        if isinstance(t, dict):
            entry: dict[str, Any] = dict(t)
            entry["progress"] = _fmt_progress(entry.get("progress"))
            entry.setdefault("last_updated_turn", t.get("last_updated_turn"))
            all_threads.append(entry)
        else:
            all_threads.append({"id": "", "summary": ""})
    world_state = list(scene.get("world_state") or [])

    # Filter prior_history and recent_turns to remove references to evicted threads
    completed_threads = arc.get("completed_threads") or []
    evicted_ids: set[str] = {ct["id"] for ct in completed_threads if isinstance(ct, dict) and ct.get("id")}
    prior_history = list((state.get("meta") or {}).get("prior_history", [])[:-1])
    prior_history = _filter_evicted_threads(prior_history, evicted_ids)

    system_text = _render(
        env, "storytell_system.j2", {
            "recent_beats": list((state.get("meta") or {}).get("recent_beats", [])),
        }
    )
    npc_roster = build_npc_roster(extraction_ctx.comp_this_turn, personality_registry=ARCHETYPES, slim=True)

    # Curtain Call signal for CLIMAX phase
    curtain_call = scene.get("curtain_call", "")

    user_text = _render(
        env,
        "storytell_user.j2",
        {
            "narration": narration,
            # This-turn derived values (from extraction_ctx) — NOT state
            "npc_roster": npc_roster,
            "npc_context": extraction_ctx.npc_context,
            "comp_this_turn": extraction_ctx.comp_this_turn,
            "location": extraction_ctx.location_this_turn,
            "inventory": extraction_ctx.inventory_this_turn,
            "conditions": extraction_ctx.conditions_this_turn,
            # State-sourced (these don't change within a turn)
            "current_arc": arc,
            "all_threads": all_threads,
            "world_state": world_state,
            "resolved_arcs": _get_resolved_arcs(state, turn_no, ttl=arc_ttl),
            "intent": intent,
            "pacing_context": pacing_context,
            "recent_turns": recent_turns or [],
            "prior_history": prior_history,
            "pending_beat": (state.get("meta") or {}).get("pending_gm_beat"),
            "recent_beats": list((state.get("meta") or {}).get("recent_beats", [])),
            "turn_no": turn_no,
            "band": band,
            "scene_phase": scene.get("scene_phase", "SETUP"),
            "curtain_call": curtain_call,
            "allowed_beat_types": derive_allowed_beat_types(
                scene.get("scene_phase", "SETUP"),
                directive=pacing_context.directive if pacing_context else "",
                spiral_detected=pacing_context.spiral_detected if pacing_context else False,
            ),
            "pc_name": (state.get("pc") or {}).get("name", "Unnamed"),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
