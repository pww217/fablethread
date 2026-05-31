"""Turn orchestrator: run_turn, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Literal


from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.extraction import (
    _avg_event_ms,
    _context_meta,
    _run_extraction_pipeline,
)
from ccya.engine.names import generate_npc_names_split
from ccya.engine.narrate import _narrate_messages
from ccya.engine.npc_roster import build_npc_roster

from ccya.engine.ruling import _call_ruling, _log_ruling_outcome, _ruling_messages
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    ArcThread,
    Band,
    CampaignArc,
    IntentEnvelope,
    SceneExtractResult,
    StorytellerResult,
    RulesOutcome,
    StateDelta,
    TurnResult,
)

from ccya.errors import ErrorKind, LlmcTimeout, LlmcError

from ccya.rules import resolve_check, build_directive
from ccya.state import (
    apply_delta,
    apply_momentum,
    append_chronicle,
    append_event,
    load_last_narration,
    load_state,
    reconcile_delta,
    resolve_inventory_remove_target,
    save_state,
)
from ccya.state.delta_builder import _merge_arc_update

_log = logging.getLogger(__name__)


@dataclass
class TurnContext:
    """Shared context across run_turn phases."""
    state: dict[str, Any]
    user_input: str
    turn_no: int
    trace_id: str
    config: EngineConfig
    recent_turns: list[dict[str, Any]]
    save_dir: Path
    packing: dict[str, Any]

    # Internal tracking (set during setup, consumed by phases)
    _env: Any = None  # Jinja env built in run_turn
    _rendered_ruling_system: str = ""
    _rendered_ruling_user: str = ""
    _ruling_raw_response: str = ""
    _ruling_parse_error: str | None = None
    _ruling_trimmed: bool = False
    _ruling_trimmed_chars: int = 0
    _narr_system: str = ""
    _narr_user: str = ""
    _narr_trimmed: bool = False
    _narr_trimmed_chars: int = 0
    _rendered_narr_system: str = ""
    _rendered_narr_user: str = ""
    _avoidance: bool = False
    _momentum_before: float | None = None
    _momentum_after: float | None = None
    _ages: dict[str, int] = field(default_factory=dict)  # set by ruling phase before narrate setup reads it
    _npc_name_pool: dict[str, list[str]] | None = None
    _pending_gm_beat: dict[str, Any] | None = None
    _deescalate: float = 0.0

    # Phase outputs
    pending_gm_beat: dict[str, Any] | None = None
    intent: IntentEnvelope | None = None
    outcome: RulesOutcome | None = None
    pacing_ctx: PacingContext | None = None
    narrative: str | None = None
    narrative_chunks: list[str] | None = None
    extraction_result: Any = None
    delta: StateDelta | None = None
    actions: list[str] | None = None
    outcome_summary: str | None = None
    extraction_event: dict[str, Any] | None = None
    storyteller_result: StorytellerResult | None = None
    scene_result: SceneExtractResult | None = None
    extraction_ctx: Any = None
    errors: list[dict[str, Any]] | None = None
    metrics: dict[str, Any] | None = None
    ruling_metrics: dict[str, Any] | None = None
    narr_metrics: dict[str, Any] | None = None
    ext_metrics: dict[str, Any] | None = None
    applied: dict[str, Any] | None = None
    rejected: list[dict[str, Any]] | None = None

@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # "Breathe" | "Scene Imperative" | "Overwhelm" | "Resolve a Threat" | "Pressure" | "Tension" | "Scene Pressure" | "Threat Pressure" | "" (may include "; Resolve a Threat" secondary when beat_locked)
    outcome_hint: str | None  # narrator's primary scene motion instruction
    beat_locked: bool  # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
    gate: Literal["block_escalate", "allow"]  # Progress may only add threads when allow
    summary: str  # human-readable log string, never sent to LLM

    @staticmethod
    def neutral() -> PacingContext:
        """Default pacing context for turns without special conditions."""
        return PacingContext(directive="", outcome_hint="hold", beat_locked=False, gate="allow", summary="neutral")




def _apply_thread_updates(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
) -> CampaignArc | None:
    """Apply explicit thread updates from the storyteller.

    Does NOT enforce caps, cooldowns, or silent timers. Purely applies
    the storyteller's explicit ThreadUpdate operations.
    """
    if not storyteller_result.thread_update:
        return None

    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_updates.no_arc trace_id=%d, skipping", turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_updates.validation_failed trace_id=%d: %s", turn_no, exc, extra={"turn": turn_no},
        )
        return None

    mutated = False
    remaining_threads = list(arc.threads)
    for update in storyteller_result.thread_update:
        found_idx = None
        for i, t in enumerate(arc.threads):
            if getattr(t, "id", "") == update.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_updates.unknown_id trace_id=%d thread %s — skipping", turn_no, update.id, extra={"turn": turn_no},
            )
            continue

        updates: dict[str, Any] = {}
        if update.active is not None:
            updates["active"] = update.active
        if update.urgency is not None:
            updates["urgency"] = update.urgency
        if update.summary is not None:
            updates["summary"] = update.summary

        thread = arc.threads[found_idx]
        updated_thread = thread.model_copy(update=updates)
        remaining_threads = [t for i2, t in enumerate(arc.threads) if i2 != found_idx]
        remaining_threads.insert(found_idx, updated_thread)

        if updates:
            mutated = True
            _log.info(
                "thread_updates.applied trace_id=%d thread %s changes=%s", turn_no, update.id, updates, extra={"turn": turn_no},
            )

    return arc.model_copy(update={
        "threads": remaining_threads,
    }) if mutated else None


def _apply_arc_resolve(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
    config: "EngineConfig",
) -> CampaignArc | None:
    """Process arc resolution from the storyteller.

    Resolves current arc, stores it in resolved_arcs with TTL tracking,
    processes thread directives (drop/move_latent), and creates a new
    successor arc.
    """
    if not storyteller_result.arc_resolve:
        return None

    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.warning(
            "arc_resolve.no_arc trace_id=%d, skipping", turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        old_arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "arc_resolve.validation_failed trace_id=%d: %s", turn_no, exc, extra={"turn": turn_no},
        )
        return None

    resolution = storyteller_result.arc_resolve

    # Store resolved arc in state's resolved_arcs list with TTL tracking
    resolved_arc_entry = {
        "visible_goal": old_arc.visible_goal,
        "resolution": resolution.resolution,
        "goal_context": resolution.goal_context,
        "thematic_question": old_arc.thematic_question,
        "resolved_turn": turn_no,
    }

    state.setdefault("resolved_arcs", []).append(resolved_arc_entry)

    _log.info(
        "arc_resolve.applied trace_id=%d goal='%s' threads_in_old=%d directives_count=%d",
        turn_no, resolution.visible_goal, len(old_arc.threads), len(resolution.thread_directives),
        extra={"turn": turn_no},
    )

    # Process thread directives: drop or move_latent
    directive_ids = {d.id for d in resolution.thread_directives}
    surviving_threads = []
    for t in old_arc.threads:
        if t.id not in directive_ids:
            surviving_threads.append(t)
        else:
            directive = next((d for d in resolution.thread_directives if d.id == t.id), None)
            if directive and directive.action == "drop":
                _log.info(
                    "arc_resolve.drop trace_id=%d thread %s", turn_no, t.id, extra={"turn": turn_no},
                )
            elif directive and directive.action == "move_latent":
                surviving_threads.append(t.model_copy(update={"active": False}))
                _log.info(
                    "arc_resolve.move_latent trace_id=%d thread %s", turn_no, t.id, extra={"turn": turn_no},
                )

    # Create new successor arc
    new_arc = CampaignArc(
        visible_goal=resolution.visible_goal,
        goal_context=resolution.goal_context,
        thematic_question=resolution.thematic_question if resolution.thematic_question is not None else old_arc.thematic_question,
        threads=surviving_threads,
        completed_threads=[],
        last_thread_created_turn=turn_no,
    )

    state["arc"] = new_arc.model_dump()

    return new_arc


def _apply_thread_resolutions(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
) -> CampaignArc | None:
    """Process thread_resolve from StorytellerResult.

    Moves resolved/failed/abandoned threads from arc.threads[] to
    arc.completed_threads[], setting resolution_state on each.
    Handles missing IDs gracefully (warning + skip). Deduplicates
    completed_threads entries by updating existing entry instead of
    creating a duplicate.
    """
    if not storyteller_result.thread_resolve:
        return None

    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_resolutions: no arc in state at T%d, skipping",
            turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_resolutions: failed to validate arc at T%d: %s",
            turn_no, exc, extra={"turn": turn_no},
        )
        return None

    # Build a map of existing completed threads by id for dedup
    completed_by_id: dict[str, ArcThread] = {}
    for ct in arc.completed_threads:
        if ct.id not in completed_by_id:
            completed_by_id[ct.id] = ct

    new_completed: list[ArcThread] = []
    any_found = False
    found_remaining = False

    for res in storyteller_result.thread_resolve:
        # Find matching thread in arc.threads[]
        found_idx = None
        for i, t in enumerate(arc.threads):
            if getattr(t, "id", "") == res.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_resolutions: T%d thread_resolve references unknown id=%s — skipping",
                turn_no, res.id, extra={"turn": turn_no},
            )
            continue

        any_found = True
        thread = arc.threads[found_idx]
        updated_thread = thread.model_copy(update={
            "resolution_state": res.resolution_state,
            "outcome": res.outcome,
            "resolved_turn": turn_no,
        })

        # Remove from threads[]
        remaining_threads = [t for i2, t in enumerate(arc.threads) if i2 != found_idx]

        # Dedup: update existing completed entry or collect new ones
        if thread.id in completed_by_id:
            found_remaining = True
            updated_existing = thread.model_copy(update={
                "resolution_state": res.resolution_state,
                "outcome": res.outcome,
                "resolved_turn": turn_no,
            })
            remaining_completed = [
                t if t.id != thread.id else updated_existing
                for t in arc.completed_threads
            ]
        else:
            new_completed.append(updated_thread)
            remaining_completed = list(arc.threads)  # placeholder

    # Finalize completed threads with dedup
    final_completed_map: dict[str, ArcThread] = {}
    if found_remaining:
        for ct in (remaining_completed or []):
            cid = getattr(ct, "id", "")
            if cid not in final_completed_map:
                final_completed_map[cid] = ct

    # Add new completions (deduped)
    for nc in new_completed:
        if nc.id not in final_completed_map:
            final_completed_map[nc.id] = nc

    # If no resolutions were found, keep original completed list
    if not any_found and not found_remaining:
        final_completed_list = list(arc.completed_threads)
    else:
        final_completed_list = list(final_completed_map.values())

    mutated = any_found or bool(new_completed)

    return arc.model_copy(update={
        "threads": remaining_threads if any_found else list(arc.threads),
        "completed_threads": final_completed_list,
    }) if mutated else None


def _compute_narrative_velocity(
    deescalate: float,
    momentum: int,
    avoidance: bool,
    momentum_floor: int = -3,
    momentum_ceiling: int = 3,
) -> float:
    """Compute a signed pacing scalar in [-1.0, 1.0].

    Negative values signal de-escalation (breathe, slow down).
    Positive values signal escalation (pressure, urgency).
    Zero is neutral.

    Priority:
      1. Explicit de-escalation from a successful check beats everything.
      2. Avoidance keyword in player input nudges negative.
      3. Momentum outside floor/ceiling normalizes toward +/-0.5.
      4. Default: 0.0 (neutral, let pressure/beat directives govern).
    """
    if deescalate > 0:
        return -deescalate

    if avoidance:
        return -0.4

    span = momentum_ceiling - momentum_floor
    if span <= 0:
        return 0.0
    midpoint = (momentum_ceiling + momentum_floor) / 2.0
    normalized = (momentum - midpoint) / (span / 2.0)
    # Scale down -- momentum alone shouldn't dominate; caps at +/-0.5
    return max(-0.5, min(0.5, normalized * 0.5))


def _compute_narration_directive(
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
) -> str:
    """Compute the narration directive string using a priority stack.

    Derives urgency counts from unified arc.threads[] with scope=scene.
    ArcThread.urgency values map to directives: urgent→Pressure/Overwhelm,
    background→Tension.

    Returns the highest-priority directive. Secondary directives are appended
    only when they do not contradict the primary (i.e., no escalation labels
    when velocity is negative).

    Priority order (highest to lowest):
      1. Breathe         -- explicit de-escalation (velocity < -0.3)
      2. Scene Imperative -- scene has been stale too long (effective_age >= 5)
      3. Overwhelm       -- 3+ urgent threads
      4. Pressure        -- 1-2 urgent threads
      5. Tension         -- background urgency threads only
      6. Scene Pressure  -- scene approaching staleness (effective_age >= 3)
    """
    # Priority 1: breathe (de-escalation wins unconditionally)
    if narrative_velocity < -0.3:
        return "Breathe"

    # Priority 2: scene imperative — stale scene demands attention
    effective_age = ages.get("effective_scene_age", 0)
    if effective_age >= 5:
        return "Scene Imperative"

    secondary: list[str] = []

    # Overwhelm (3+ urgent threads)
    immediate_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "") == "urgent")
    if immediate_count >= 3:
        primary = "Overwhelm"
    else:
        primary = ""

    # Pressure (1-2 urgent)
    if not primary and immediate_count > 0:
        primary = "Pressure"

    # Tension (background only)
    if not primary:
        building_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "") == "background")
        if building_count > 0:
            primary = "Tension"

    # Secondary: scene pressure approaching staleness (non-contradicting append)
    if 3 <= effective_age < 5:
        secondary.append("Scene Pressure")

    parts = [primary] if primary else []
    parts.extend(secondary)
    return "; ".join(parts)


def _compute_pacing_context(
    deescalate: float,
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    momentum: int,
    config: "EngineConfig",
    consecutive_pressure_turns: int = 0,
    scene_motion: str = "hold",
    impossible: bool = False,
) -> PacingContext:
    """Compute unified pacing context for Narrate and Progress steps.

    Derives urgency from unified arc.threads[] with scope=scene. Replaces separate
    deescalate/narrative_velocity signals with a single authoritative struct containing
    directive, beat_locked, gate, summary.
    """
    # Compute directive using existing logic
    directive = _compute_narration_directive(
        narrative_velocity=narrative_velocity,
        scope_scene_threads=scope_scene_threads,
        ages=ages,
    )

    # Determine beat_locked: relief fired when either consecutive pressure threshold reached or momentum at minimum
    beat_locked = False
    if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""

    # Compute outcome_hint from scene_motion and PacingContext escalation signals
    outcome_hint: str | None = "hold"
    if scene_motion == "transition":
        outcome_hint = "transition"
    elif scene_motion == "advance":
        outcome_hint = "advance"
    elif impossible:
        outcome_hint = "advance"
    else:
        effective_age = ages.get("effective_scene_age", 0)
        if effective_age >= 3:
            outcome_hint = "advance"
        elif beat_locked:
            outcome_hint = "advance"
        else:
            urgent_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "normal") == "urgent")
            if directive in ("Overwhelm", "Pressure") and urgent_count >= 1:
                outcome_hint = "advance"

    # Determine gate: block_add when deescalation is strong (pressure just resolved)
    gate: Literal["block_escalate", "allow"] = "allow"
    if deescalate >= 0.5:
        gate = "block_escalate"

    # Build summary for logging
    parts = [directive] if directive else []
    if beat_locked:
        parts.append("locked")
    summary = ", ".join(parts) or "neutral"

    return PacingContext(
        directive=directive or "",
        outcome_hint=outcome_hint,
        beat_locked=beat_locked,
        gate=gate,
        summary=summary,
    )


def _compute_ages(state: dict[str, Any]) -> dict[str, int]:
    """Compute age/staleness counters for narration directives."""
    meta = state.get("meta") or {}
    scene = state.get("scene") or {}
    current_turn = meta.get("turn", 0)

    scene_entered = scene.get("turn_entered", 0)
    scene_age = current_turn - scene_entered if scene_entered > 0 else 0

    return {
        "scene_age": scene_age,
    }



def _recent_turn_count(state: dict[str, Any]) -> int:
    """Return up to 21 turns for all consumers (narrator bullets + ruling/storytell slices)."""
    return 21


async def _ruling_phase(ctx: TurnContext) -> tuple[Any, Any, dict[str, Any], float, list[tuple[str, Any]]]:
    """Execute ruling phase. Returns (intent, outcome, metrics, deescalate, phase_events)."""
    config = ctx.config
    state = ctx.state
    trace_id = ctx.trace_id
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    exp_ruling_ms = _avg_event_ms(ctx.save_dir, "ruling.total_ms")
    phase_events: list[tuple[str, Any]] = [("phase", {"phase": "ruling_start", "expected_ms": exp_ruling_ms})]
    t_rules = asyncio.get_event_loop().time()

    # Avoidance detection
    avoidance = any(kw in (ctx.user_input or "").lower() for kw in config.avoidance_keywords)
    ctx._avoidance = avoidance
    if avoidance:
        _log.debug(
            "turn.pacing.avoidance detected", extra={"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "pacing"},
        )

    # Build ruling messages
    _comp = state.get("compendium", {}).get("npcs", {})
    ruling_messages = _ruling_messages(
        ctx._env, state, ctx.user_input,
        turn_no=turn_no,
        npc_roster=build_npc_roster(_comp),
        inventory=state.get("inventory") or None,
        recent_turns=ctx.recent_turns[-1:],
    )
    rendered_ruling_system = ruling_messages[0]["content"] if ruling_messages else ""
    rendered_ruling_user = ruling_messages[-1]["content"] if ruling_messages else ""
    ctx._rendered_ruling_system = rendered_ruling_system
    ctx._rendered_ruling_user = rendered_ruling_user

    strip_trace_markers_in_messages(ruling_messages)
    ruling_messages, ruling_trimmed, ruling_trimmed_chars = trim_messages(
        ruling_messages, config.prompt_token_budget,
    )
    if config.log_prompts:
        _log_prompts(state.get("meta", {}).get("turn", 0) + 1, "ruling", ruling_messages)

    intent, ruling_usage, ruling_raw_response, ruling_parse_error = await _call_ruling(
        ruling_messages, config, trace_id,
    )
    ctx.intent = intent
    ctx._ruling_raw_response = ruling_raw_response
    ctx._ruling_parse_error = ruling_parse_error
    ctx._ruling_trimmed = ruling_trimmed
    ctx._ruling_trimmed_chars = ruling_trimmed_chars

    # Handle impossible actions: no dice roll, synthesize failure outcome
    if intent.impossible:
        intent.check.required = False
        band: Band = "fail"
        directive = build_directive(band, intent.intent_verb, intent.check.skill or "")
        outcome = RulesOutcome(
            rolled=False,
            band=band,
            directive=directive,
            intent_verb=intent.intent_verb,
            intent=intent.intent,
            impossible=True,
            impossible_reason=intent.impossible_reason,
        )
        apply_momentum(state, band)
        _log.info(
            "impossible action: %s — %s",
            intent.intent_verb, intent.impossible_reason,
            extra={"trace_id": trace_id, "turn": turn_no, "pack": "", "kind": "ruling"},
        )
    elif intent.check.required and intent.check.skill:
        # Resolve dice in Python (deterministic)
        try:
            _pc_conds_struct = list((state.get("pc") or {}).get("conditions") or [])
            _pc_cond_ids = [
                c.get("id", "") if isinstance(c, dict) else str(c) for c in _pc_conds_struct
            ]
            outcome = resolve_check(
                skill=intent.check.skill,
                difficulty=intent.check.difficulty,
                pc_stats=(state.get("pc") or {}).get("stats") or {},
                pc_conditions=[cid for cid in _pc_cond_ids if cid],
                intent_verb=intent.intent_verb,
                intent=intent.intent,
            )
        except Exception as exc:
            _log.warning(
                "rules.resolve_check failed: %s", exc, extra={"trace_id": trace_id}
            )
            outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent)
    elif intent.check.required and not intent.check.skill:
        _log.warning(
            "rules: check required on T%d but skill=%s — no roll will occur",
            state.get("meta", {}).get("turn", 0) + 1,
            intent.check.skill,
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent)
    else:
        outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent)

    ctx.outcome = outcome

    # Apply momentum deterministically from band (never from LLM)
    if outcome.rolled:
        apply_momentum(state, outcome.band)

    # De-escalation magnitude
    deescalate: float = 0.0
    if config.thread_deescalate_on_success and outcome.rolled and outcome.band in ("success", "crit_success"):
        if any(
            t.get("urgency") in ("immediate", "building")
            for t in ((state.get("arc") or {}).get("threads") or [])
            if isinstance(t, dict) and t.get("scope") == "scene"
        ):
            deescalate = 1.0 if outcome.band == "crit_success" else 0.6

    # Age counters for narration directives
    ctx._ages = _compute_ages(state)

    # Pre-compute effective scene age with combat boost for directive thresholds.
    _scene_age = ctx._ages.get("scene_age", 0)
    _tags: list[str] = (state.get("scene") or {}).get("tags") or []
    if "combat" in _tags:
        _scene_age += 2
    ctx._ages["effective_scene_age"] = _scene_age

    if config.log_prompts:
        _log_ruling_outcome(
            state.get("meta", {}).get("turn", 0) + 1, intent, outcome
        )

    ruling_ms = (asyncio.get_event_loop().time() - t_rules) * 1000
    ruling_metrics = {
        "total_ms": round(ruling_ms, 1),
        "rolled": outcome.rolled,
        "tokens_in": ruling_usage.get("prompt_tokens", 0),
        "tokens_out": ruling_usage.get("completion_tokens", 0),
    }

    phase_events.append(("phase", {
            "phase": "ruling_done",
            "rolled": outcome.rolled,
            "band": outcome.band if outcome.rolled else None,
            "skill": outcome.skill if outcome.rolled else None,
            "dice": outcome.dice if outcome.rolled else [],
            "final_total": outcome.final_total if outcome.rolled else 0,
            "difficulty": outcome.difficulty if outcome.rolled else None,
            "stat_value": outcome.stat_value if outcome.rolled else 0,
            "stat_mod": outcome.stat_mod if outcome.rolled else 0,
            "diff_mod": outcome.diff_mod if outcome.rolled else 0,
            "cond_mod": outcome.cond_mod if outcome.rolled else 0,
            "directive": outcome.directive if outcome.rolled else "",
            "intent_verb": intent.intent_verb,
        },
    ))

    return intent, outcome, ruling_metrics, deescalate, phase_events


async def _narrate_setup(ctx: TurnContext) -> tuple[Any, Any]:
    """Build narration context and messages. Returns (pacing_ctx, narr_messages)."""
    state = ctx.state
    config = ctx.config
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    # Rolling NPC name pool for mid-game cultural anchoring (split by gender)
    _npc_name_pool: dict[str, list[str]] = {}
    if ctx.packing.get("name_locales"):
        _npc_name_pool = generate_npc_names_split(
            ctx.packing["name_locales"],
            male_count=5, female_count=5, seed=state.get("meta", {}).get("turn", 0),
        )

    # pending_gm_beat from the previous turn's storyteller is read here to set
    # the atmosphere/scene context for this turn's narration. Beats are consumed
    # on the turn AFTER generation — this is intentional: beats shape ongoing scene
    # atmosphere rather than providing immediate mechanical feedback.
    # Immediate feedback for roll outcomes is handled by the roll-band narration
    # directive (rules.py build_directive()), not by the beat system.
    _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
    if _pending_gm_beat:
        _expires = _pending_gm_beat.get("beat_expires_turn")
        if _expires is not None and turn_no > _expires:
            _pending_gm_beat = None
            state.setdefault("meta", {})["pending_gm_beat"] = None

    ctx._npc_name_pool = _npc_name_pool
    ctx._pending_gm_beat = _pending_gm_beat

    # PC allegiance and world context
    _pc_allegiance = (state.get("pc") or {}).get("allegiance")
    _pack_narrator_rules = ctx.packing.get("narrator_rules", [])
    _pack_world_rules = ctx.packing.get("world_rules", [])
    _world_factions = ctx.packing.get("factions", [])

    # Compute unified pacing scalar
    narrative_velocity = _compute_narrative_velocity(
        deescalate=ctx._deescalate,
        momentum=(state.get("pc") or {}).get("momentum", 0),
        avoidance=ctx._avoidance,
        momentum_floor=config.momentum_floor,
        momentum_ceiling=config.momentum_ceiling,
    )

    _raw_thread_dicts = [t for t in (state.get("arc") or {}).get("threads") or [] if isinstance(t, dict) and t.get("scope") == "scene"]

    # Convert raw thread dicts to ArcThread objects for computation functions
    _scope_scene_threads: list[ArcThread] = []
    for td in _raw_thread_dicts:
        try:
            _scope_scene_threads.append(ArcThread.model_validate(td))
        except Exception:
            _log.warning(
                "Malformed ArcThread entry: %s", td,
                extra={"turn": turn_no, "trace_id": ctx.trace_id},
            )

    # Compute unified pacing context (replaces separate directive computation)
    _scene_motion = ctx.intent.scene_motion if ctx.intent else "hold"
    _impossible = ctx.intent.impossible if ctx.intent else False
    _pc = _compute_pacing_context(
        deescalate=ctx._deescalate, narrative_velocity=narrative_velocity,
        scope_scene_threads=_scope_scene_threads, ages=ctx._ages,
        momentum=(state.get("pc") or {}).get("momentum", 0), config=config,
        consecutive_pressure_turns=(state.get("meta") or {}).get("consecutive_pressure_turns", 0),
        scene_motion=_scene_motion,
        impossible=_impossible,
    )

    _comp = (state.get("compendium") or {}).get("npcs") or {}
    narr_messages = _narrate_messages(
        ctx._env, state, ctx.user_input,
        recent_turns=ctx.recent_turns[:-1][-20:],
        narrator_rules=_pack_narrator_rules, world_rules=_pack_world_rules,
        rules_outcome=ctx.outcome, npc_name_pool=_npc_name_pool,
        momentum=(state.get("pc") or {}).get("momentum", 0), pending_beat=_pending_gm_beat,
        pacing_context=_pc, ages=ctx._ages, pc_allegiance=_pc_allegiance, turn_no=turn_no,
        world_factions=_world_factions,
        npc_roster=build_npc_roster(_comp),
    )

    ctx.pacing_ctx = _pc
    return _pc, narr_messages


async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_name_locales: list[dict[str, Any]] = [],
    pack_narrator_rules: list[str] = [],
    pack_world_rules: list[str] = [],
    pack_factions: list[dict[str, str]] = [],
) -> AsyncIterator[tuple[str, Any]]:
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    state = load_state(save_dir)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []

    try:
        await _inflight.acquire(str(save_dir))

        # --- Memory: load last narration turn + prior_history bullets ---
        recent_turns = load_last_narration(
            save_dir,
            _recent_turn_count(state),
        )

        # Build shared context for all phases
        ctx = TurnContext(
            state=state, user_input=user_input, turn_no=0, trace_id=trace_id,
            config=config, recent_turns=recent_turns,
            save_dir=save_dir, packing={
                "name_locales": pack_name_locales,
                "narrator_rules": pack_narrator_rules, "world_rules": pack_world_rules,
                "factions": pack_factions,
            }, _env=env,
        )

        # === Call 0: Rules / intent classification (extracted phase) ===
        momentum_before = state.get("pc", {}).get("momentum", 0.0)
        _intent, _outcome, ruling_metrics, deescalate, ruling_phase_events = await _ruling_phase(ctx)
        for evt in ruling_phase_events:
            yield evt
        ctx._deescalate = deescalate
        momentum_after = state.get("pc", {}).get("momentum", 0.0)

        # Capture ruling context for event logging (from ctx where ruling phase stored them)
        rendered_ruling_system = ctx._rendered_ruling_system or ""
        rendered_ruling_user = ctx._rendered_ruling_user or ""
        ruling_raw_response = ctx._ruling_raw_response or ""
        ruling_parse_error = ctx._ruling_parse_error
        ruling_trimmed = ctx._ruling_trimmed
        ruling_trimmed_chars = ctx._ruling_trimmed_chars

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # === Call 1: Narration setup (extracted) + streaming ===
        exp_narrate_ms = _avg_event_ms(save_dir, "narrate.total_ms")
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Build narration context and messages (extracted phase)
        _pc, narr_messages = await _narrate_setup(ctx)

        # Trim + log (stays inline for simplicity)
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""
        ctx._rendered_narr_system = rendered_narr_system
        ctx._rendered_narr_user = rendered_narr_user

        strip_trace_markers_in_messages(narr_messages)
        narr_messages, narr_trimmed, narr_trimmed_chars = trim_messages(
            narr_messages, config.prompt_token_budget,
        )
        if config.log_prompts:
            _log_prompts(state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages)

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_request",
                messages=narr_messages,
                max_chars=config.log_llm_io_max_chars,
            )
        first_visible = True
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            narrative_chunks.append(chunk)
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                first_visible = False
                yield ("phase", {"phase": "narrate_first_token", "first_token_ms": round(first_ms, 1)})
            yield ("token", chunk)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        narrative = strip_thinking("".join(narrative_chunks))
        narr_metrics = {
            "first_token_ms": round(first_ms, 1),
            "total_ms": round(narr_ms, 1),
            "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
            "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
        }
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_response",
                response=narrative,
                extra={"timing_ms": narr_metrics},
                max_chars=config.log_llm_io_max_chars,
            )

        yield ("phase", {"phase": "narrate_done"})

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_event_ms(save_dir, "extract.total_ms")
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}
        _extraction_ctx = None

        _extract_result = None
        try:
            _log.debug("turn.extraction_pipeline_enter trace_id=%s turn_no=%d", trace_id, turn_no)
            async for _evt in _run_extraction_pipeline(
                env, state, narrative,
                rules_outcome=_outcome,
                intent=_intent,
                config=config,
                trace_id=trace_id,
                turn_no=turn_no,
                pacing_context=_pc,
                recent_turns=recent_turns,
            ):
                if isinstance(_evt, tuple) and len(_evt) == 2:
                    _log.debug("turn.extraction_evt trace_id=%s evt_type=%s", trace_id, type(_evt[0]).__name__, extra={"event_preview": str(_evt)[:500]})
                    yield _evt
                else:
                    _extract_result = _evt
        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            _log.error("turn.extraction_pipeline_error trace_id=%s turn_no=%d\n%s", trace_id, turn_no, tb)
            errors.append({"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id, "message": str(exc)})

        if _extract_result is not None:
            # mypy cannot express heterogeneous 7-tuple unpack from async generator
            delta, actions, outcome_summary, extraction_event, storyteller_result, scene_result, _extraction_ctx = _extract_result  # type: ignore[misc]
        # Beat lifecycle: beat_disposition removed — Python infers from state mutations (gm_beat presence in delta)
            _new_beat = storyteller_result.gm_beat if storyteller_result else None

            if _new_beat and _new_beat.type:
                # New beat present → replace/clear pending_gm_beat with new value
                # Replace or fresh write (includes implicit replace when carry+new_beat)
                _beat_dict = _new_beat.model_dump(exclude_none=True)
                _beat_dict["beat_expires_turn"] = turn_no + 2
                state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict

        yield ("phase", {"phase": "extract_done"})

        # Condition age pass: decrement turns_remaining, remove expired
        updated_conds = []
        for c in (state.get("pc") or {}).get("conditions") or []:
            tr = c.get("turns_remaining")
            if tr is None:
                # Permanent condition — do not age
                updated_conds.append(c)
                continue
            new_remaining = tr - 1
            if new_remaining <= 0:
                append_event(save_dir, {
                    "kind": "condition_expired",
                    "condition_id": c.get("id"),
                    "turn": turn_no,
                })
                # do not append — condition removed
            else:
                updated_conds.append({**c, "turns_remaining": new_remaining})

        (state.setdefault("pc", {})["conditions"])[:] = updated_conds

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        # Roll up per-stream token counts for the metrics dict
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "storytell")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "storytell")
        )
        # Build per-stream breakdown for UI display
        _streams = {}
        for s in ("scene", "state", "storytell"):
            ev = extraction_event.get(s)
            if ev:
                _streams[s] = {
                    "ms": ev.get("ms", 0),
                    "tokens_in": ev.get("tokens_in", 0),
                    "tokens_out": ev.get("tokens_out", 0),
                    "skipped": ev.get("skipped", False),
                }
        ext_metrics = {
            "total_ms": round(ext_ms, 1),
            "tokens_in": _tokens_in,
            "tokens_out": _tokens_out,
            "retries": 0,
            "streams": _streams,
        }
        metrics = {
            "ruling": ruling_metrics,
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        state_pre_apply = copy.deepcopy(state)
        applied: dict[str, Any] = {}
        rejected: list[dict[str, Any]] = []

        if delta is not None:
            rejected = _validate(state, delta)
            blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
            if blocking:
                errors.append(
                    {
                        "trace_id": trace_id,
                        "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
                    }
                )
                narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"

            delta, reconcile_warnings = reconcile_delta(state, delta)
            for w in reconcile_warnings:
                _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
            state = apply_delta(
                state, delta,
            )
            # Inject floor relief beat via PacingContext.beat_locked
            if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
                meta = state.setdefault("meta", {})
                meta["pending_gm_beat"] = {
                    "type": "breathing_room",
                    "surface_as": "ambient",
                    "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
                }
            applied = delta.model_dump(exclude_none=True)
            for r in rejected:
                if r.get("kind") == "warn_overdraw":
                    _log.warning(
                        "inventory over-draw clamped: %s",
                        r.get("reason"),
                        extra={"trace_id": trace_id},
                    )

            # Stamp last_seen on touched NPCs
            comp = state.get("compendium", {}).get("npcs", {})
            location = state.get("location", {})
            for cu in (delta.compendium_npc_update or []):
                entry = comp.setdefault(cu.id, {})
                entry["last_seen"] = {
                    "turn": turn_no,
                    "location_id": location.get("id", ""),
                    "location_name": location.get("name", ""),
                }

            # Arc director: process thread updates and arc resolution
            if state.get("arc") and storyteller_result:
                thread_delta = _apply_thread_updates(state, storyteller_result)
                if thread_delta is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), thread_delta
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": thread_delta}
                        )

                # Process arc resolution (resolves arc + creates successor)
                resolved_arc = _apply_arc_resolve(state, storyteller_result, config)
                if resolved_arc is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), resolved_arc
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": resolved_arc}
                        )

                # Process thread resolutions (resolved/failed/abandoned -> completed)
                resolved_arc = _apply_thread_resolutions(state, storyteller_result)
                if resolved_arc is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), resolved_arc
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": resolved_arc}
                        )

                # Enforce PacingContext gate on thread_add
                if storyteller_result.thread_add:
                    _new_thread = storyteller_result.thread_add
                    _scope = getattr(_new_thread, "scope", "arc")
                    turn_no_for_cooldown = state.get("meta", {}).get("turn", 0) + 1
                    gate_ok = _pc is None or _pc.gate == "allow"
                    if not gate_ok:
                        _log.debug("thread_add blocked by pacing gate %s at T%d", getattr(_pc, 'gate', 'unknown'), turn_no_for_cooldown)
                        pass  # skip thread creation — same pattern as scene-scope check below

                    else:
                        # Key collision gate: if matching key exists, skip creation.
                        exact_collision_id = None
                        if _new_thread.key:
                            _state_arc = state.get("arc")
                            if _state_arc and delta is not None:
                                try:
                                    _check_arc = CampaignArc.model_validate(_state_arc)
                                    for _t in (_check_arc.threads or []) + (_check_arc.completed_threads or []):
                                        if getattr(_t, 'key') and str(getattr(_t, 'key', '')).lower() == str(_new_thread.key).lower():
                                            exact_collision_id = _t.id
                                            break
                                except Exception:
                                    pass

                            if exact_collision_id is not None:
                                _log.warning(
                                    "thread_add.key_collision",
                                    extra={"turn": turn_no_for_cooldown, "key": str(_new_thread.key), "existing_id": exact_collision_id, "new_id": _new_thread.id or "?"},
                                )
                                pass  # skip thread creation — key collision detected

                        if exact_collision_id is not None:
                            pass
                        else:
                            arc_raw = state.get("arc")
                            turn_no_for_add = state.get("meta", {}).get("turn", 0) + 1
                            _state_arc = state.get("arc")
                            if _state_arc and delta is not None:
                                try:
                                    _existing_arc = CampaignArc.model_validate(arc_raw)
                                    existing_ids = {t.id for t in _existing_arc.threads} | {t.id for t in _existing_arc.completed_threads}
                                    # Fuzzy auto-merge dedup check (only when key is non-null).
                                    fuzzy_merged = False
                                    if _new_thread.key and not exact_collision_id:
                                        new_key_tokens = set(str(_new_thread.key).lower().split())
                                        best_score, best_match_t = 0.0, None
                                        for ft in (_existing_arc.threads or []):
                                            tk = getattr(ft, 'key')
                                            if not tk:
                                                continue
                                            candidate_tokens = set(str(tk).lower().split())
                                            overlap = len(new_key_tokens & candidate_tokens)
                                            score = overlap / max(len(new_key_tokens), len(candidate_tokens)) if candidate_tokens else 0.0
                                            if score > best_score:
                                                best_score = score
                                                best_match_t = ft

                                        if best_score >= 0.70 and best_match_t is not None:
                                            _merged_t = best_match_t
                                            if _new_thread.summary and _new_thread.summary.strip():
                                                _merged_t.summary = _new_thread.summary

                                            existing_tags = set(getattr(best_match_t, 'tags', []) or [])
                                            new_tags = set(_new_thread.tags or [])
                                            merged_tags = sorted(existing_tags | new_tags)
                                            if merged_tags != list(_merged_t.tags):
                                                _merged_t.tags = merged_tags

                                            arc_with_new_thread = _existing_arc.model_copy(threads=list(_existing_arc.threads))
                                            _merge_arc_update(state.setdefault("arc", {}), arc_with_new_thread)
                                            state.setdefault("meta", {})["last_thread_created_turn"] = turn_no_for_add

                                            _log.info(
                                                "thread_add.auto_merge",
                                                extra={"turn": turn_no_for_cooldown, "key": str(getattr(best_match_t, 'key', '')), "score": round(best_score, 2), "existing_id": best_match_t.id, "new_id": _new_thread.id or "?"},
                                            )

                                            fuzzy_merged = True

                                    if not fuzzy_merged and _new_thread.id not in existing_ids:
                                        _updated_t = _new_thread.model_copy()
                                        arc_with_new_thread = _existing_arc.model_copy(
                                            update={"threads": list(_existing_arc.threads) + [_updated_t],
                                                    "last_thread_created_turn": turn_no_for_add}
                                        )
                                        _merge_arc_update(state.setdefault("arc", {}), arc_with_new_thread)
                                        state.setdefault("meta", {})["last_thread_creation_turn"] = turn_no_for_add
                                        delta = delta.model_copy(update={"arc_update": arc_with_new_thread})
                                except Exception as exc:
                                    _log.warning(
                                        "thread_add: failed to validate arc at T%d for thread %s: %s",
                                        turn_no_for_add, getattr(_new_thread, 'id', '?'), exc, extra={"turn": turn_no_for_add},
                                    )

        narrative = _strip_fallback(narrative, trace_id=trace_id, turn=turn_no)

        # Two-pass consecutive pressure counter update.
        if _extract_result is not None and _pc is not None:
            directive = _pc.directive or ""
            thread_updates = storyteller_result.thread_update if storyteller_result else []
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if (directive in ("Pressure", "Overwhelm")) and not thread_updates:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_last_narration).
        ruling_event: dict[str, Any] = {
            "intent_verb": _intent.intent_verb,
            "intent": _intent.intent,
            "rolled": _outcome.rolled,
            "total_ms": ruling_metrics.get("total_ms"),
            "tokens_in": ruling_metrics.get("tokens_in", 0),
            "tokens_out": ruling_metrics.get("tokens_out", 0),
            "outcome_summary": outcome_summary,
        }
        if _outcome.rolled:
            ruling_event.update({
                "skill": _outcome.skill,
                "difficulty": _outcome.difficulty,
                "dice": _outcome.dice,
                "stat_mod": _outcome.stat_mod,
                "diff_mod": _outcome.diff_mod,
                "cond_mod": _outcome.cond_mod,
                "raw_total": _outcome.raw_total,
                "final_total": _outcome.final_total,
                "band": _outcome.band,
                "momentum_before": momentum_before,
                "momentum_after": momentum_after,
                "momentum_delta": momentum_after - momentum_before,
            })

        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "ruling": ruling_event,
            "momentum_before": momentum_before,
            "momentum_after": momentum_after,
            "momentum_delta": momentum_after - momentum_before,
            "pacing_context": {
                "directive": _pc.directive if _pc else "",
                "beat_locked": bool(_pc.beat_locked) if _pc else False,
                "gate": _pc.gate if _pc else "allow",
                "summary": _pc.summary if _pc else "",
            },
            # Summary of what was captured in narrate_prompt rendered_user (for meta-eval visibility).
            # Full rendered content is captured above but too large to parse efficiently.
            "narrate_summary": {
                "rules_outcome_present": bool(_outcome and _outcome.rolled),
                "rules_outcome_verb": (_outcome.intent_verb if _outcome else ""),
                "pacing_directive": _pc.directive if _pc else "",
                "beat_locked": bool(_pc.beat_locked) if _pc else False,
            },
            "extraction_context": {
                "present_npcs_count": sum(1 for e in (_extraction_ctx.comp_this_turn or {}).values() if isinstance(e, dict) and e.get("presence") == "present") if _extraction_ctx else 0,
                "location_this_turn": dict(_extraction_ctx.location_this_turn) if _extraction_ctx else {},
                "scene_tags_this_turn": list(_extraction_ctx.scene_tags_this_turn) if _extraction_ctx else [],
                "inventory_this_turn": list(_extraction_ctx.inventory_this_turn) if _extraction_ctx else [],
                "conditions_this_turn": list(_extraction_ctx.conditions_this_turn) if _extraction_ctx else [],
            },
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "changes": changes,
            # Prompt logging (for turn viewer)
            "ruling_prompt": {
                "rendered_system": rendered_ruling_system,
                "rendered_user": rendered_ruling_user,
                "output": ruling_raw_response,
                "parse_error": ruling_parse_error,
                "context_meta": _context_meta(rendered_ruling_system, rendered_ruling_user, ruling_trimmed, ruling_trimmed_chars),
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
                "context_meta": _context_meta(rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars),
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {user_input}\n\n{narrative.strip()}",
        )

        # Append outcome_summary as prior_history bullet (after persist, before yield complete)
        if outcome_summary and outcome_summary.strip():
            turn_no = state["meta"]["turn"]
            bullet = f"- [T{turn_no}] {outcome_summary}"
            meta = state.setdefault("meta", {})
            prior = meta.setdefault("prior_history", [])
            prior.append(bullet)
            if len(prior) > 20:
                meta["prior_history"] = prior[-20:]
            save_state(save_dir, state)

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            ruling=ruling_event or {},
            outcome_summary=outcome_summary,
            ts=_ts,
        )
        yield ("complete", result_obj)

    except LlmcTimeout as exc:
        _log.error(
            "LLM timeout in run_turn", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
        )
        errors.append({"kind": ErrorKind.LLM_TIMEOUT, "message": str(exc)})
        raise
    except LlmcError as exc:
        _log.error(
            "LLM error in run_turn", extra={"error_kind": exc.kind, "trace_id": trace_id},
        )
        errors.append({"kind": exc.kind, "message": str(exc)})
        raise
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        _log.error(
            "run_turn failed: %s: %s\n%s", type(exc).__name__, exc, tb, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        errors.append({"kind": ErrorKind.TURN_PROCESSING_FAILED, "message": str(exc)})
        fallback = narrative_chunks and "".join(narrative_chunks) or ""
        if not fallback:
            fallback = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        yield (
            "complete",
            TurnResult(
                turn=state.get("meta", {}).get("turn", 0),
                trace_id=trace_id,
                narrative=fallback,
                state_delta={},
                errors=errors,
                metrics=metrics,
                diff=[],
                changes={},
                ts="",
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


_FALLBACK_SENTINEL = "*That action didn't resolve as expected"


def _strip_fallback(narration: str, *, trace_id: str, turn: int) -> str:
    log = logging.getLogger(__name__)
    lines = narration.splitlines()
    clean = [ln for ln in lines if not ln.strip().startswith(_FALLBACK_SENTINEL)]
    if len(clean) < len(lines):
        log.warning(
            "Fallback message stripped from narration",
            extra={"trace_id": trace_id, "turn": turn},
        )
    return "\n".join(clean)



def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            _log.debug(
                "inventory_remove target %r not found in inventory (turn %s) — skipping",
                rem.id, state.get("meta", {}).get("turn", 0),
            )
            continue
        item = inv_by_id.get(canonical)
        if item and int(item.get("amount") or 0) == 0:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "zero_balance",
                    "value": canonical,
                    "reason": f"Item '{canonical}' has zero balance",
                }
            )
            continue
        if rem.amount is None:
            continue
        try:
            requested = int(rem.amount)
        except (TypeError, ValueError):
            continue
        if requested <= 0:
            continue
        current = int(inv_by_id.get(canonical, {}).get("amount") or 1)
        if requested > current:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "warn_overdraw",
                    "value": canonical,
                    "requested": requested,
                    "current": current,
                    "reason": (
                        f"Over-draw on '{canonical}': requested {requested} but stack is {current}. "
                        "apply_delta will clamp to a full-stack remove."
                    ),
                }
            )

    return rejections


async def warmup(config: EngineConfig) -> None:
    try:
        await llm_chat(
            config.host,
            config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            timeout=30.0,
        )
    except Exception:
        _log.warning("Warmup LLM call failed — continuing without warmup cache")
