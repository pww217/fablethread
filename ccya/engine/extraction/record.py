"""Stream 3: Record extraction messages (threads + actions + outcome_summary)."""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import Environment

from ccya.engine.config import EngineConfig, _render
from ccya.engine.extraction.context import _ExtractionContext
from ccya.engine.extraction.utils import _filter_evicted_threads
from ccya.engine.narrate import _get_resolved_arcs
from ccya.prompts.context import _fmt_progress, _filter_completed_threads

_log = logging.getLogger(__name__)


def _record_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    extraction_ctx: _ExtractionContext,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    band: str = "",
    arc_ttl: int = 3,
    config: EngineConfig | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (threads + actions + outcome_summary)."""
    scene = state.get("scene") or {}

    arc = state.get("arc") or {}
    _raw_threads = arc.get("threads") or []
    all_threads: list[dict[str, Any]] = []
    for t in _raw_threads:
        if isinstance(t, dict):
            entry: dict[str, Any] = dict(t)
            entry["progress"] = _fmt_progress(entry.get("major_updates"))
            entry.setdefault("last_updated_turn", t.get("last_updated_turn"))
            all_threads.append(entry)
        else:
            all_threads.append({"id": "", "summary": ""})
    world_state = list(scene.get("world_state") or [])

    # Filter prior_history to remove references to evicted threads
    completed_threads = arc.get("completed_threads") or []
    evicted_ids: set[str] = {ct["id"] for ct in completed_threads if isinstance(ct, dict) and ct.get("id")}
    prior_history = list((state.get("meta") or {}).get("prior_history", [])[:-1])
    prior_history = _filter_evicted_threads(prior_history, evicted_ids)

    # TTL-filter completed_threads (only include recent ones)
    ttl_filtered_completed = _filter_completed_threads(arc, turn_no, ttl=arc_ttl)
    arc = {**arc, "completed_threads": ttl_filtered_completed}

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
            "pc_name": (state.get("pc") or {}).get("name", "Unnamed"),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs
