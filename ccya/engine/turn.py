"""Turn orchestrator: run_turn, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import difflib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Literal


from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts, is_cancel_requested, register_persist, register_turn, signal_turn_done
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.extraction import (
    _avg_event_ms,
    _context_meta,
    _run_extraction_pipeline,
)
from ccya.engine.names import generate_npc_names_split
from ccya.engine.narrate import _narrate_messages
from ccya.engine.npc_roster import build_npc_roster
from ccya.personality import ARCHETYPES
from ccya.engine.thread_sanitizer import sanitize_threads

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
    ProgressEntry,
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
    strip_npcs_notes,
)
from ccya.state.delta_builder import _merge_arc_update

_log = logging.getLogger(__name__)

PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication")


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
    _avoidance: bool = False
    _ages: dict[str, int] = field(default_factory=dict)  # set by ruling phase before narrate setup reads it
    _deescalate: float = 0.0

    intent: IntentEnvelope | None = None
    outcome: RulesOutcome | None = None

@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # "Breathe" | "Scene Imperative" | "Overwhelm" | "Pressure" | "Tension" | "Scene Pressure" | "" (may include "; Resolve a Threat" secondary when beat_locked)
    outcome_hint: str | None  # narrator's primary scene motion instruction
    beat_locked: bool  # True: floor relief fired — Progress MUST emit breathing_room beat; gate is unaffected (controlled by deescalate independently)
    gate: Literal["block_escalate", "allow"]  # Progress may only add threads when allow
    summary: str  # human-readable log string, never sent to LLM

    @staticmethod
    def neutral() -> PacingContext:
        """Default pacing context for turns without special conditions."""
        return PacingContext(directive="", outcome_hint="hold", beat_locked=False, gate="allow", summary="neutral")




def _apply_thread_updates(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
    config: EngineConfig | None = None,
) -> CampaignArc | None:
    """Apply explicit thread updates from the storyteller."""
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
        for i, t in enumerate(remaining_threads):
            if getattr(t, "id", "") == update.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_updates.unknown_id trace_id=%d thread %s — skipping", turn_no, update.id, extra={"turn": turn_no},
            )
            continue

        updates: dict[str, Any] = {}
        thread = remaining_threads[found_idx]
        if update.active is not None:
            updates["active"] = update.active
        if update.urgency is not None:
            updates["urgency"] = update.urgency
        if update.progress is not None:
            current_progress = list(thread.progress)
            kind = update.progress_kind or "advancement"
            entry = ProgressEntry(text=update.progress, kind=kind)
            if current_progress:
                last_text = current_progress[-1].text if isinstance(current_progress[-1], ProgressEntry) else str(current_progress[-1])
                ratio = difflib.SequenceMatcher(None, last_text, entry.text).ratio()
                if ratio >= 0.50:
                    _log.warning(
                        "thread_updates.dedup trace_id=%d thread %s — progress %.2f overlap with last entry, rejecting",
                        turn_no, update.id, ratio, extra={"turn": turn_no},
                    )
                else:
                    current_progress.append(entry)
                    updates["progress"] = current_progress
            else:
                current_progress.append(entry)
                updates["progress"] = current_progress

        if updates:
            updates["last_updated_turn"] = turn_no
            mutated = True

        updated_thread = thread.model_copy(update=updates)
        remaining_threads = [t for i2, t in enumerate(remaining_threads) if i2 != found_idx]
        remaining_threads.insert(found_idx, updated_thread)

        if mutated:
            _log.info(
                "thread_updates.applied trace_id=%d thread %s changes=%s", turn_no, update.id, updates, extra={"turn": turn_no},
            )

    # Auto-latent demotion — fire every turn (not gated on mutated).
    # Threads updated this turn already have last_updated_turn set to turn_no at line ~212,
    # so they won't trigger the stale threshold. Only untouched threads age and eventually get demoted.
    if config and remaining_threads:
        stale_threshold = config.thread_stale_threshold
        for i, t in enumerate(remaining_threads):
            if (
                t.last_updated_turn is not None
                and (turn_no - t.last_updated_turn) >= stale_threshold
                and t.active
            ):
                updated = t.model_copy(update={"active": False, "last_updated_turn": turn_no})
                remaining_threads[i] = updated
                _log.info(
                    "thread_updates.auto_latent trace_id=%d thread %s — untouched for %d turns",
                    turn_no, t.id, turn_no - t.last_updated_turn, extra={"turn": turn_no},
                )

    # Urgency decay: demote threads that have been at their urgency level for
    # >= thread_urgency_max_age turns. Demotes stepwise: urgent → normal → background.
    if config and remaining_threads:
        _decay_threshold = config.thread_urgency_max_age
        for i, t in enumerate(remaining_threads):
            _set_turn = getattr(t, "urgency_set_turn", None)
            if _set_turn is None or not t.active:
                continue  # skip threads without urgency tracking; decay only affects active threads
            _age = turn_no - _set_turn
            if _age >= _decay_threshold:
                _current_urgency = getattr(t, "urgency", "background")
                new_urgency = None
                if _current_urgency == "urgent":
                    new_urgency = "normal"
                elif _current_urgency == "normal":
                    new_urgency = "background"

                if new_urgency is not None:
                    updated_t = t.model_copy(update={"urgency": new_urgency, "urgency_set_turn": turn_no})
                    remaining_threads[i] = updated_t
                    mutated = True
                    _log.info(
                        "thread_updates.urgency_decay trace_id=%d thread %s urgency %s→%s (age=%d turns)",
                        turn_no, t.id, _current_urgency, new_urgency, _age, extra={"turn": turn_no},
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
    processes thread drop list (opt-out carry-over), and creates a new
    successor arc seeded with surviving + new threads.
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

    # All threads carry forward; apply drop_threads filter
    drop_ids = set(resolution.drop_threads)
    surviving_threads = [t for t in old_arc.threads if t.id not in drop_ids]

    # Warn about dropped threads
    for tid in resolution.drop_threads:
        _log.info(
            "arc_resolve.drop trace_id=%d thread %s", turn_no, tid, extra={"turn": turn_no},
        )

    # Store resolved arc entry in state's resolved_arcs list with TTL tracking
    resolved_arc_entry = {
        "visible_goal": old_arc.visible_goal,
        "resolution": resolution.resolution,
        "goal_context": resolution.goal_context,
        "resolved_turn": turn_no,
        "closed_threads": [],
    }

    state.setdefault("resolved_arcs", []).append(resolved_arc_entry)

    _log.info(
        "arc_resolve.applied trace_id=%d goal='%s' surviving=%d drop_count=%d new_threads=%d",
        turn_no, resolution.visible_goal, len(surviving_threads), len(resolution.drop_threads), len(resolution.new_threads),
        extra={"turn": turn_no},
    )

    # Create new successor arc with surviving threads + new threads
    all_thread = surviving_threads + list(resolution.new_threads)
    new_arc = CampaignArc(
        visible_goal=resolution.visible_goal,
        goal_context=resolution.goal_context,
        threads=all_thread,
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

    # Collect resolution targets by ID, building updated ArcThread for each
    resolved_ids: set[str] = set()
    updates: list[ArcThread] = []
    any_found = False

    for res in storyteller_result.thread_resolve:
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
        resolved_ids.add(thread.id)
        updates.append(thread.model_copy(update={
            "resolution_state": res.resolution_state,
            "outcome": res.outcome,
            "resolved_turn": turn_no,
        }))

        # Promote to world state if requested (Step 3.1: D3 + D7)
        if res.promote_to_world_state and res.outcome:
            ws_list = state.setdefault("scene", {}).get("world_state") or []
            existing = next((f for f in ws_list if isinstance(f, dict) and f.get("id") == res.id), None)
            if existing:
                existing["text"] = res.outcome
                existing["tier"] = "persistent"
            else:
                ws_list.append({"id": res.id, "text": res.outcome, "tier": "persistent"})
            state.setdefault("scene", {})["world_state"] = ws_list

    if not any_found:
        return None

    # Build new threads[] — exclude all resolved threads
    remaining_threads = [t for t in arc.threads if t.id not in resolved_ids]

    # Build new completed_threads[] — merge updates into existing completed list (dedup by id)
    completed_map: dict[str, ArcThread] = {}
    for ct in arc.completed_threads:
        completed_map[ct.id] = ct
    for u in updates:
        completed_map[u.id] = u

    return arc.model_copy(update={
        "threads": remaining_threads,
        "completed_threads": list(completed_map.values()),
    })


def _compute_narrative_velocity(
    deescalate: float,
    momentum: int,
    avoidance: bool,
    momentum_floor: int = -3,
    momentum_ceiling: int = 3,
    pacing_factor: float = 0.5,
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
    # Scale down -- momentum alone shouldn't dominate; caps at +/-pacing_factor
    return max(-pacing_factor, min(pacing_factor, normalized * pacing_factor))


def _compute_narration_directive(
    narrative_velocity: float,
    active_threads: list["ArcThread"],
    ages: dict[str, int],
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 5,
) -> str:
    """Compute the narration directive string using a priority stack.

    Derives urgency counts from arc.threads[]. ArcThread.urgency values map
    to directives: urgent→Pressure/Overwhelm, background→Tension.

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
        urgent_count = sum(
            1 for t in active_threads
            if getattr(t, "urgency", "") == "urgent"
        )
        if urgent_count == 0:
            return "Breathe"

    # Priority 2: scene imperative — stale scene demands attention
    effective_age = ages.get("effective_scene_age", 0)
    if effective_age >= scene_imperative_threshold:
        return "Scene Imperative"

    secondary: list[str] = []

    # Overwhelm (3+ urgent threads)
    immediate_count = sum(1 for t in active_threads if getattr(t, "urgency", "") == "urgent")
    if immediate_count >= 3:
        primary = "Overwhelm"
    else:
        primary = ""

    # Pressure (1-2 urgent)
    if not primary and immediate_count > 0:
        primary = "Pressure"

    # Tension (background only)
    if not primary:
        building_count = sum(1 for t in active_threads if getattr(t, "urgency", "") == "background")
        if building_count > 0:
            primary = "Tension"

    # Secondary: scene pressure approaching staleness (non-contradicting append)
    if scene_pressure_threshold <= effective_age < scene_imperative_threshold:
        secondary.append("Scene Pressure")

    parts = [primary] if primary else []
    parts.extend(secondary)
    return "; ".join(parts)


def _compute_pacing_context(
    deescalate: float,
    narrative_velocity: float,
    active_threads: list["ArcThread"],
    ages: dict[str, int],
    momentum: int,
    config: "EngineConfig",
    consecutive_pressure_turns: int = 0,
    scene_motion: str = "hold",
    impossible: bool = False,
) -> PacingContext:
    """Compute unified pacing context for Narrate and Progress steps.

    Derives urgency from arc.threads[]. Replaces separate deescalate/narrative_velocity
    signals with a single authoritative struct containing directive, beat_locked, gate, summary.
    """
    # Compute directive using existing logic
    directive = _compute_narration_directive(
        narrative_velocity=narrative_velocity,
        active_threads=active_threads,
        ages=ages,
        scene_pressure_threshold=config.scene_pressure_threshold,
        scene_imperative_threshold=config.scene_imperative_threshold,
    )

    # Determine beat_locked: relief fired when either consecutive pressure threshold reached or momentum at minimum
    beat_locked = False
    if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        # MB-2: never append threat resolution to Breathe — it's de-escalation, not escalation
        if directive != "Breathe":
            directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""

    # Compute outcome_hint from scene_motion and PacingContext escalation signals
    outcome_hint: str | None = "hold"
    if scene_motion == "transition":
        outcome_hint = "transition"
    elif scene_motion == "advance":
        outcome_hint = "advance"
    elif directive.startswith("Scene Imperative"):
        outcome_hint = "transition"
    elif impossible:
        outcome_hint = "advance"
    else:
        effective_age = ages.get("effective_scene_age", 0)
        if effective_age >= 3:
            outcome_hint = "advance"
        elif beat_locked:
            outcome_hint = "advance"
        else:
            urgent_count = sum(1 for t in active_threads if getattr(t, "urgency", "normal") == "urgent")
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
    scene_age = current_turn - scene_entered

    return {
        "scene_age": scene_age,
    }



def _recent_turn_count(state: dict[str, Any]) -> int:
    """Return max turns needed — now each consumer only needs 1 ([-1:] slice)."""
    return 1


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
        npc_roster=build_npc_roster(_comp, personality_registry=ARCHETYPES),
        inventory=state.get("inventory") or None,
        recent_turns=ctx.recent_turns[-1:],
    )
    rendered_ruling_system = ruling_messages[0]["content"] if ruling_messages else ""
    rendered_ruling_user = ruling_messages[-1]["content"] if ruling_messages else ""
    ctx._rendered_ruling_system = rendered_ruling_system
    ctx._rendered_ruling_user = rendered_ruling_user

    strip_trace_markers_in_messages(ruling_messages)
    ruling_messages, ruling_trimmed, ruling_trimmed_chars = trim_messages(
        ruling_messages, config.context_window,
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
            reason=intent.reason,
        )
        apply_momentum(state, band)
        _log.info(
            "impossible action: %s — %s",
            intent.intent_verb, intent.reason,
            extra={"trace_id": trace_id, "turn": turn_no, "pack": "", "kind": "ruling"},
        )
    elif intent.check.required and intent.check.skill:
        # Resolve dice in Python (deterministic)
        try:
            outcome = resolve_check(
                skill=intent.check.skill,
                difficulty=intent.check.difficulty,
                pc_stats=(state.get("pc") or {}).get("stats") or {},
                intent_verb=intent.intent_verb,
                intent=intent.intent,
                difficulty_mods=config._resolve_difficulty_modifiers(),
                near_miss_softening=config.near_miss_softening,
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
            isinstance(t, dict) and t.get("urgency") == "urgent"
            for t in ((state.get("arc") or {}).get("threads") or [])
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
            "directive": outcome.directive if outcome.rolled else "",
            "intent_verb": intent.intent_verb,
        },
    ))

    return intent, outcome, ruling_metrics, deescalate, phase_events


async def _narrate_setup(ctx: TurnContext) -> tuple[Any, Any, float]:
    """Build narration context and messages. Returns (pacing_ctx, narr_messages, narrative_velocity)."""
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
        pacing_factor=config.momentum_pacing_factor,
    )

    # Build active thread list from all arc threads for pacing context
    _raw_thread_dicts = [t for t in (state.get("arc") or {}).get("threads") or [] if isinstance(t, dict)]
    _active_threads: list[ArcThread] = []
    for td in _raw_thread_dicts:
        try:
            _active_threads.append(ArcThread.model_validate(td))
        except Exception:
            _log.warning(
                "Malformed ArcThread entry: %s", td,
                extra={"turn": turn_no, "trace_id": ctx.trace_id},
            )

    # Compute unified pacing context
    _scene_motion = ctx.intent.scene_motion if ctx.intent else "hold"
    _impossible = ctx.intent.impossible if ctx.intent else False
    _pc = _compute_pacing_context(
        deescalate=ctx._deescalate, narrative_velocity=narrative_velocity,
        active_threads=_active_threads, ages=ctx._ages,
        momentum=(state.get("pc") or {}).get("momentum", 0), config=config,
        consecutive_pressure_turns=(state.get("meta") or {}).get("consecutive_pressure_turns", 0),
        scene_motion=_scene_motion,
        impossible=_impossible,
    )

    _comp = (state.get("compendium") or {}).get("npcs") or {}
    narr_messages = _narrate_messages(
        ctx._env, state, ctx.user_input,
        recent_turns=ctx.recent_turns[-1:],
        narrator_rules=_pack_narrator_rules, world_rules=_pack_world_rules,
        rules_outcome=ctx.outcome, npc_name_pool=_npc_name_pool,
        momentum=(state.get("pc") or {}).get("momentum", 0), pending_beat=_pending_gm_beat,
        pacing_context=_pc, ages=ctx._ages, pc_allegiance=_pc_allegiance, turn_no=turn_no,
        world_factions=_world_factions,
        npc_roster=build_npc_roster(_comp, personality_registry=ARCHETYPES),
        arc_ttl=config.arc_memory_ttl, thread_ttl=config.thread_memory_ttl,
    )

    return _pc, narr_messages, narrative_velocity


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
    strip_npcs_notes(state)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []

    try:
        register_turn(str(save_dir))
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
        if is_cancel_requested(str(save_dir)):
            return
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
        if is_cancel_requested(str(save_dir)):
            return
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Build narration context and messages (extracted phase)
        _pc, narr_messages, narrative_velocity = await _narrate_setup(ctx)

        # Trim + log (stays inline for simplicity)
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""

        strip_trace_markers_in_messages(narr_messages)
        narr_messages, narr_trimmed, narr_trimmed_chars = trim_messages(
            narr_messages, config.context_window,
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
            top_p=config.narrate_top_p,
            frequency_penalty=config.narrate_frequency_penalty,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            narrative_chunks.append(chunk)
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                first_visible = False
                yield ("phase", {"phase": "narrate_first_token", "first_token_ms": round(first_ms, 1)})
            if is_cancel_requested(str(save_dir)):
                return
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

        if is_cancel_requested(str(save_dir)):
            return
        yield ("phase", {"phase": "narrate_done"})

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_event_ms(save_dir, "extract.total_ms")
        if is_cancel_requested(str(save_dir)):
            return
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
                    if is_cancel_requested(str(save_dir)):
                        return
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
            else:
                state.get("meta", {}).pop("pending_gm_beat", None)

            # Floor relief injection — runs BEFORE apply_delta so breathing_room persists through the deep copy. Post-apply block was moved here and removed from its original location.
            # MB-3: only inject floor relief when beat_locked is caused by consecutive pressure, not momentum crisis
            if _pc.beat_locked:
                cur_momentum = int((state.get("pc") or {}).get("momentum", 0))
                triggered_by_momentum = (cur_momentum <= config.momentum_floor)

                # Don't inject ambient beats during momentum crisis — player needs escalation, not breathing room
                if not triggered_by_momentum:
                    _current_beat = state.get("meta", {}).get("pending_gm_beat")
                    if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
                        meta = state.setdefault("meta", {})
                        meta["pending_gm_beat"] = {
                            "type": "breathing_room",
                            "surface_as": "ambient",
                            "beat_expires_turn": turn_no + 2,
                        }

            # Consecutive pressure counter: reads post-floor-relief pending_gm_beat
            _current_beat = state.get("meta", {}).get("pending_gm_beat")
            _beat_type = _current_beat.get("type") if _current_beat else None
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if _beat_type in PRESSURE_BEAT_TYPES:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0

        if is_cancel_requested(str(save_dir)):
            return
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

            else:
                delta, reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state = apply_delta(
                    state, delta,
                )

                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

            # Beat history: snapshot pending_gm_beat after floor relief override
            _history_beat = state.get("meta", {}).get("pending_gm_beat")
            meta = state.setdefault("meta", {})
            meta.setdefault("recent_beats", []).append({
                "turn": turn_no,
                "type": _history_beat.get("type") if _history_beat else None,
                "surface_as": _history_beat.get("surface_as") if _history_beat else None,
            })
            # Cap at N entries, oldest first
            max_beats = config.recent_beats_max if config else 5
            if len(meta["recent_beats"]) > max_beats:
                meta["recent_beats"] = meta["recent_beats"][-max_beats:]

            # Stamp last_seen on touched NPCs
            comp = state.get("compendium", {}).get("npcs", {})
            location = state.get("location", {})
            for cu in (delta.compendium_npc_update or []):
                entry = comp.get(cu.id)
                if entry is None:
                    continue
                entry["last_seen"] = {
                    "turn": turn_no,
                    "location_id": location.get("id", ""),
                    "location_name": location.get("name", ""),
                }

            # Arc director: process thread updates and arc resolution
            if state.get("arc") and storyteller_result:
                thread_delta = _apply_thread_updates(state, storyteller_result, config)
                if thread_delta is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), thread_delta
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": thread_delta}
                        )

                # Apply goal_update (mid-arc visible_goal change, separate from arc_resolve)
                if storyteller_result.goal_update:
                    state.setdefault("arc", {})["visible_goal"] = storyteller_result.goal_update
                    _log.info(
                        "goal_update trace_id=%d visible_goal='%s'",
                        trace_id, storyteller_result.goal_update,
                        extra={"trace_id": trace_id},
                    )

                # Detect same-turn thread_update + thread_resolve conflict
                update_ids = {u.id for u in (storyteller_result.thread_update or [])}
                resolve_ids = {r.id for r in (storyteller_result.thread_resolve or [])}
                conflict_ids = update_ids & resolve_ids
                if conflict_ids:
                    _log.warning(
                        "thread_same_turn_conflict trace_id=%d ids=%s — thread_update and thread_resolve for same id",
                        trace_id, sorted(conflict_ids), extra={"trace_id": trace_id},
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
                    turn_no_for_add = state.get("meta", {}).get("turn", 0) + 1
                    gate_ok = _pc is None or _pc.gate == "allow"
                    if not gate_ok:
                        _log.debug("thread_add blocked by pacing gate %s at T%d", getattr(_pc, 'gate', 'unknown'), turn_no_for_add)
                    else:
                        arc_raw = state.get("arc")
                        if arc_raw and delta is not None:
                            try:
                                _existing_arc = CampaignArc.model_validate(arc_raw)
                                existing_ids = {t.id for t in _existing_arc.threads} | {t.id for t in _existing_arc.completed_threads}
                                if _new_thread.id not in existing_ids:
                                    _updated_t = _new_thread.model_copy(update={
                                        "added_turn": turn_no_for_add,
                                        "urgency_set_turn": turn_no_for_add,
                                    })
                                    arc_with_new_thread = _existing_arc.model_copy(
                                        update={"threads": list(_existing_arc.threads) + [_updated_t],
                                                "last_thread_created_turn": turn_no_for_add}
                                    )
                                    if config:
                                        active = [t for t in arc_with_new_thread.threads if t.active]
                                        if len(active) > config.thread_max_active:
                                            evict = min(active, key=lambda t: t.last_updated_turn or 0)
                                            evicted = evict.model_copy(update={"active": False, "last_updated_turn": turn_no_for_add})
                                            arc_with_new_thread = arc_with_new_thread.model_copy(
                                                update={"threads": [evicted if t.id == evict.id else t for t in arc_with_new_thread.threads]}
                                            )
                                            _log.info(
                                                "thread_cap.evict trace_id=%d evicted=%s active_count=%d max=%d",
                                                trace_id, evict.id, len(active), config.thread_max_active,
                                                extra={"trace_id": trace_id},
                                            )
                                    _merge_arc_update(state.setdefault("arc", {}), arc_with_new_thread)
                                    state.setdefault("meta", {})["last_thread_created_turn"] = turn_no_for_add
                                    delta = delta.model_copy(update={"arc_update": arc_with_new_thread})
                            except Exception as exc:
                                _log.warning(
                                    "thread_add: failed to validate arc at T%d for thread %s: %s",
                                    turn_no_for_add, getattr(_new_thread, 'id', '?'), exc, extra={"turn": turn_no_for_add},
                                )

        # --- NPC lifecycle: nearby decay and departed archive ---
        nearby_ttl = config.nearby_decay_ttl if config else 2
        comp = state.get("compendium", {}).get("npcs", {})
        for entry in comp.values():
            if not isinstance(entry, dict):
                continue
            if entry.get("presence") == "nearby":
                nearby_since = entry.get("nearby_since_turn")
                if isinstance(nearby_since, int) and turn_no - nearby_since >= nearby_ttl:
                    entry["presence"] = "known"

        archive_ttl = config.departed_archive_ttl if config else 3
        archived_ids = []
        for nid, entry in comp.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("presence") == "departed":
                dep_turn = entry.get("departed_turn")
                if isinstance(dep_turn, int) and turn_no - dep_turn >= archive_ttl:
                    entry["presence"] = "archived"
                    archived_ids.append(nid)
        if archived_ids:
            _log.info(
                "archived_departed_npcs ids=%s", sorted(archived_ids),
                extra={"turn": turn_no},
            )

        narrative = _strip_fallback(narrative, trace_id=trace_id, turn=turn_no)



        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, rejected)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        if is_cancel_requested(str(save_dir)):
            return
        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_last_narration).
        ruling_event: dict[str, Any] = {
            "intent_verb": _intent.intent_verb,
            "intent": _intent.intent,
            "rolled": _outcome.rolled,
            "impossible": _outcome.impossible,
            "reason": _outcome.reason,
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
            "ruling": ruling_event,
            "momentum_before": momentum_before,
            "momentum_after": momentum_after,
            "momentum_delta": momentum_after - momentum_before,
            "pacing_context": {
                "directive": _pc.directive if _pc else "",
                "beat_locked": bool(_pc.beat_locked) if _pc else False,
                "gate": _pc.gate if _pc else "allow",
                "outcome_hint": _pc.outcome_hint if _pc else None,
                "summary": _pc.summary if _pc else "",
            },
            "post_turn_pending_beat": state.get("meta", {}).get("pending_gm_beat"),
            "post_turn_location_id": state.get("location", {}).get("id"),
            "post_extraction_consecutive_pressure_turns": (state.get("meta") or {}).get("consecutive_pressure_turns", 0),
            "narrative_velocity": round(narrative_velocity, 2),
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
        event["state_snapshot"] = load_state(save_dir)
        append_event(save_dir, event)
        # Snapshot pre-turn state before overwriting — used by delete_last_turn
        register_persist(str(save_dir))
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

        # === Thread sanitizer (after prior_history, before yield complete) ===
        if config.sanitize_every > 0:
            t_sanitize = asyncio.get_running_loop().time()
            state, sanitize_ran = await sanitize_threads(
                save_dir, state, config, trace_id=trace_id,
            )
            if sanitize_ran:
                yield ("phase", {"phase": "sanitize_start", "expected_ms": 0})
                yield ("phase", {"phase": "sanitize_done", "ms": round(
                    (asyncio.get_running_loop().time() - t_sanitize) * 1000, 1
                )})
            save_state(save_dir, state)

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            ruling=ruling_event or {},
            outcome_summary=outcome_summary,
            narrative_velocity=narrative_velocity,
            gm_beat={
                "type": storyteller_result.gm_beat.type,
                "surface_as": storyteller_result.gm_beat.surface_as,
            } if (storyteller_result and storyteller_result.gm_beat) else None,
            outcome_hint=_pc.outcome_hint if _pc else None,
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
        signal_turn_done(str(save_dir))


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
            rejections.append({
                "field": "inventory_remove",
                "kind": "missing_target",
                "value": rem.id,
                "reason": f"Item '{rem.id}' not found in inventory",
            })
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
