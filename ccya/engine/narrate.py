"""Narration prompt building and NPC name generation helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ccya.engine.config import _render
from ccya.engine.turn_context import _is_cancel_requested
from ccya.engine.names import generate_npc_names_split
from ccya.engine.npc_roster import build_npc_roster
from ccya.engine._pacing import (
    _compute_pacing_context,
    _compute_scene_phase,
    compute_convergence_score,
)
from ccya.models import ArcThread, RulesOutcome, WorldState
from ccya.engine.hints import compute_arc_pressure_score
from ccya.prompts.context import _fmt_progress, _filter_completed_threads
from ccya.engine.extraction.utils import _filter_pc_situation
from ccya.engine._pacing import _to_arc_thread

if TYPE_CHECKING:
    from ccya.engine.turn_context import PacingContext, TurnContext


_log = logging.getLogger(__name__)


def _narrate_messages(
    env: Any,
    state: WorldState,
    user_input: str,
    *,
    recent_turns: list[dict[str, Any]] = [],
    narrator_rules: list[str] = [],
    world_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    pending_beat: dict[str, Any] | None = None,
    pacing_context: "PacingContext | None" = None,
    ages: dict[str, int] | None = None,
    pc_allegiance: str | None = None,
    turn_no: int = 0,
    world_factions: list[dict[str, str]] = [],
    npc_roster: list[dict[str, Any]] | None = None,
    arc_ttl: int = 3,
    thread_ttl: int = 3,
    curtain_call: str = "",
) -> list[dict[str, str]]:
    if npc_roster is None:
        npc_roster = build_npc_roster(state.compendium.npcs, turn_no=turn_no)
    _log.debug(
        "narrate entry turn=%d npc_roster_len=%d",
        turn_no, len(npc_roster),
    )

    # Build arc context for narrator (needed by both system and user prompts)
    arc = state.long_term_objective
    arc_pressure_score = 0
    arc_hint_text = None
    if arc:
        all_threads = list(arc.threads)
        current_objective_ctx = {
            "long_term_objective": arc.long_term_objective,
            "resolution": arc.resolution,
            "resolved_arcs": _get_resolved_arcs(state, turn_no, ttl=arc_ttl),
            "threads": [
                {
                    "summary": t.summary,
                    "urgency": t.urgency,
                    "type": t.type,
                    "id": t.id,
                    "dormant": t.dormant,
                    "progress": _fmt_progress(t.major_updates),
                    "last_updated_turn": t.last_updated_turn,
                }
                for t in all_threads if not t.dormant
            ],
            "completed_threads": _filter_completed_threads(arc, turn_no, ttl=thread_ttl),
        }
        # Compute arc pressure score
        arc_pressure_score, arc_hint_text = compute_arc_pressure_score(arc, turn_no)
    else:
        current_objective_ctx = None

    user_ctx = {
        "state": state,
        "pc": state.pc,
        "pc_situation": _filter_pc_situation(state.pc.situation, state.pc_situation_schema),
        "prior_history": list(state.meta.prior_history)[:-1],
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "user_input": user_input,
        "pending_beat": pending_beat,
        "pacing_context": pacing_context,
        "turn_no": turn_no,
        "meta": {"turn": turn_no},
        "scene": state.scene,
        "ages": ages or {},
        "pc_allegiance": pc_allegiance,
        "world_factions": world_factions,
        "npc_roster": npc_roster,
        "current_objective": current_objective_ctx,
        "arc_pressure_score": arc_pressure_score,
        "arc_hint_text": arc_hint_text,
        "curtain_call": curtain_call,
        "resolved_arcs": _get_resolved_arcs(state, turn_no, ttl=arc_ttl),
        "inventory": [it.model_dump() for it in state.inventory],
        "location": state.location.model_dump(),
        "conditions": [c.model_dump() for c in state.pc.conditions],
    }

    system_text = _render(env, "narrate_system.j2", {
        "narrator_rules": narrator_rules,
        "world_rules": world_rules,
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


def _get_resolved_arcs(state: WorldState, turn_no: int, *, ttl: int = 3) -> list[dict[str, Any]]:
    """Get all TTL-filtered resolved arcs from state's resolved_arcs list."""
    resolved_arcs = state.resolved_arcs
    result: list[dict[str, Any]] = []
    for ra in reversed(resolved_arcs):
        resolved_turn = ra.get("resolved_turn", 0)
        if (turn_no - resolved_turn) <= ttl and resolved_turn is not None:
            result.append(dict(ra))
    return result


async def _narrate_setup(ctx: "TurnContext") -> tuple[Any, Any]:
    """Build narration context and messages. Returns (pacing_ctx, narr_messages)."""
    state = ctx.state
    config = ctx.config

    if _is_cancel_requested(ctx):
        return None, None

    turn_no = state.meta.turn + 1

    # Rolling NPC name pool for mid-game cultural anchoring (split by gender)
    _npc_name_pool: dict[str, list[str]] = {}
    if ctx.packing.get("name_locales"):
        _npc_name_pool = generate_npc_names_split(
            ctx.packing["name_locales"],
            male_count=5, female_count=5, seed=state.meta.turn,
        )

    # pending_gm_beat from this turn's ruling is read here to set
    # the atmosphere/scene context for this turn's narration. Beats are selected
    # same-turn by Ruling from World candidates and immediately consumed by
    # Narrate. Beat expiry is no longer tracked — Ruling's per-turn
    # always-replace-or-pop rule keeps state hygienic.
    # Immediate feedback for roll outcomes is handled by the roll-band narration
    # directive (rules.py build_directive()), not by the beat system.
    _pending_gm_beat = state.meta.pending_gm_beat

    # PC allegiance and world context
    _pc_allegiance = state.pc.allegiance
    _pack_narrator_rules = ctx.packing.get("narrator_rules", [])
    _pack_world_rules = ctx.packing.get("world_rules", [])
    _world_factions = ctx.packing.get("factions", [])

    # Phase engine: compute scene_phase before directive computation
    scene_phase = state.scene.scene_phase

    # Count urgent threads for phase engine
    _raw_thread_dicts = [t.model_dump() for t in state.long_term_objective.threads if isinstance(t, ArcThread)]
    thread_urgency_count = 0
    for t in state.long_term_objective.threads:
        if isinstance(t, ArcThread):
            if t.urgency == "urgent":
                thread_urgency_count += 1
        else:
            arc = _to_arc_thread(t)
            if arc and arc.urgency == "urgent":
                thread_urgency_count += 1
            else:
                _log.warning(
                    "Malformed ArcThread entry: %s", t,
                    extra={"turn": turn_no, "trace_id": ctx.trace_id},
                )

    # Compute convergence score before phase machine — passes raw thread list
    _convergence_score, _convergence_components = compute_convergence_score(
        scene_phase=scene_phase,
        active_threads=_raw_thread_dicts,
        scene_age=ctx._ages.get("scene_age", 0),
        recent_beats=list(state.meta.recent_beats),
        config=config,
        turn_no=turn_no,
        recent_rolls=list(state.meta.recent_rolls),
    )

    # EMA smoothing on convergence score
    prev_smoothed = state.meta.smoothed_convergence
    smoothed_convergence = config.convergence_alpha * _convergence_score + (1 - config.convergence_alpha) * prev_smoothed

    # Compute phase (returns new scene model)
    new_scene = _compute_scene_phase(state, ctx._ages, config, _convergence_score, turn_no)
    scene_phase = new_scene.scene_phase

    # Compute unified pacing context with new signal set
    _scene_motion = ctx.intent.scene_motion if ctx.intent else "hold"
    _pc = _compute_pacing_context(
        scene_phase=scene_phase,
        thread_urgency_count=thread_urgency_count,
        effective_scene_age=ctx._ages.get("effective_scene_age", 0),
        scene_motion=_scene_motion,
        scene_pressure_threshold=config.scene_pressure_threshold,
        scene_imperative_threshold=config.scene_imperative_threshold,
        config=config,
        convergence_score=int(smoothed_convergence),
    )

    _pc.convergence_score = _convergence_score
    _pc.convergence_components = _convergence_components
    _pc.convergence_threads = _raw_thread_dicts

    # Curtain Call signal for CLIMAX phase
    _curtain_call = state.scene.curtain_call

    narr_messages = _narrate_messages(
        ctx._env, state, ctx.user_input,
        recent_turns=ctx.recent_turns[-1:],
        narrator_rules=_pack_narrator_rules, world_rules=_pack_world_rules,
        rules_outcome=ctx.outcome, npc_name_pool=_npc_name_pool,
        pending_beat=_pending_gm_beat,
        pacing_context=_pc, ages=ctx._ages, pc_allegiance=_pc_allegiance, turn_no=turn_no,
        world_factions=_world_factions,
        npc_roster=[n for n in build_npc_roster(state.compendium.npcs, turn_no=turn_no) if n.get("presence") == "present"],
        arc_ttl=config.arc_memory_ttl, thread_ttl=config.thread_memory_ttl,
        curtain_call=_curtain_call,
    )

    return _pc, narr_messages
