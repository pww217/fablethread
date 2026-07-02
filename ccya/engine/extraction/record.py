"""Stream 3: Record extraction messages (threads + actions + outcome_summary)."""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import Environment

from ccya.engine.config import EngineConfig, _render
from ccya.engine.extraction.context import _ExtractionContext
from ccya.engine.extraction.utils import _filter_evicted_threads
from ccya.engine.narrate import _get_resolved_arcs
from ccya.models import ArcThread, LongTermObjective, WorldState
from ccya.prompts.context import _fmt_progress, _filter_completed_threads

_log = logging.getLogger(__name__)


def _record_messages(
    env: Environment,
    narration: str,
    state: WorldState,
    *,
    extraction_ctx: _ExtractionContext,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    band: str = "",
    arc_ttl: int = 3,
    config: EngineConfig | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (threads + actions + outcome_summary)."""
    scene = state.scene

    arc = state.arc
    _raw_threads = list(arc.threads)
    all_threads: list[dict[str, Any]] = []
    for t in _raw_threads:
        if isinstance(t, ArcThread):
            all_threads.append({
                "id": t.id,
                "summary": t.summary,
                "progress": _fmt_progress(list(t.major_updates)),
                "last_updated_turn": t.last_updated_turn,
            })
        else:
            try:
                t_obj = ArcThread.model_validate(t)
                all_threads.append({
                    "id": t_obj.id,
                    "summary": t_obj.summary,
                    "progress": _fmt_progress(list(t_obj.major_updates)),
                    "last_updated_turn": t_obj.last_updated_turn,
                })
            except Exception:
                all_threads.append({"id": "", "summary": ""})
    world_state = list(scene.world_state)

    # Filter prior_history to remove references to evicted threads
    completed_threads = list(arc.completed_threads)
    evicted_ids: set[str] = {ct.id for ct in completed_threads if ct.id}
    prior_history = list(state.meta.prior_history)[:-1]
    prior_history = _filter_evicted_threads(prior_history, evicted_ids)

    # TTL-filter completed_threads (only include recent ones)
    ttl_filtered_completed = _filter_completed_threads(arc, turn_no, ttl=arc_ttl)
    arc = LongTermObjective(
        long_term_objective=arc.long_term_objective,
        threads=list(arc.threads),
        completed_threads=ttl_filtered_completed,
        resolution=arc.resolution,
        last_thread_created_turn=arc.last_thread_created_turn,
        started_turn=arc.started_turn,
    )

    system_text = _render(env, "record_system.j2", {})
    user_text = _render(
        env,
        "record_user.j2",
        {
            "narration": narration,
            # State-sourced (these don't change within a turn)
            "current_objective": arc,
            "all_threads": all_threads,
            "world_state": world_state,
            "resolved_arcs": _get_resolved_arcs(state, turn_no, ttl=arc_ttl),
            "recent_turns": recent_turns or [],
            "prior_history": prior_history,
            "turn_no": turn_no,
            "band": band,
            "pc_name": state.pc.name or "Unnamed",
            "scene_phase": scene.scene_phase,
            "curtain_call": scene.curtain_call,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
