"""Turn orchestrator: run_turn, _validate, warmup."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator


from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.config import EngineConfig, _build_jinja_env
from ccya.engine.extraction import (
    _avg_event_ms,
    _context_meta,
    _run_extraction_pipeline,
)
from ccya.engine._pacing import (
    derive_allowed_beat_types,
)
from ccya.engine.turn_context import TurnContext, _is_cancel_requested
from ccya.engine.thread_sanitizer import sanitize_threads
from ccya.engine.turn_state import (
    _apply_state_updates,
)
from ccya.engine.ruling import _ruling_phase
from ccya.engine.narrate import _narrate_setup
from ccya.engine.world import _run_world_step
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    StateMerge,
    TurnResult,
    WorldState,
    IntentEnvelope,
    RulesOutcome,
)

from ccya.errors import ErrorKind, LlmcTimeout, LlmcError

from ccya.state import (
    append_chronicle,
    append_event,
    append_prompts,
    load_last_narration,
    load_state,
    save_state,
)

_log = logging.getLogger(__name__)

PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication", "setback")


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
    delta: StateMerge | None = None
    actions: list[str] = []

    try:
        from ccya.server.app import _start_turn, _signal_turn_done
        _turn_lock, _cancel_event, _turn_done_event = _start_turn()
        await _turn_lock.acquire()

        # --- Memory: load last narration turn + prior_history bullets ---
        recent_turns = load_last_narration(save_dir, 1)

        # Build shared context for all phases
        ctx = TurnContext(
            state=state, user_input=user_input, turn_no=0, trace_id=trace_id,
            config=config, recent_turns=recent_turns,
            save_dir=save_dir,             packing={
                "name_locales": pack_name_locales,
                "narrator_rules": pack_narrator_rules, "world_rules": pack_world_rules,
                "factions": pack_factions,
                "inventory": state.inventory,
            }, _env=env, _cancel_event=_cancel_event,
        )

        # === Call 0: Rules / intent classification (extracted phase) ===
        _intent, _outcome, ruling_metrics, deescalate, ruling_phase_events = await _ruling_phase(ctx)
        state = ctx.state
        if _is_cancel_requested(ctx):
            return
        for evt in ruling_phase_events:
            yield evt
        # Capture ruling context for event logging (from ctx where ruling phase stored them)
        rendered_ruling_system = ctx._rendered_ruling_system or ""
        rendered_ruling_user = ctx._rendered_ruling_user or ""
        ruling_raw_response = ctx._ruling_raw_response or ""
        ruling_parse_error = ctx._ruling_parse_error
        ruling_trimmed = ctx._ruling_trimmed
        ruling_trimmed_chars = ctx._ruling_trimmed_chars

        turn_no = state.meta.turn + 1
        # NOTE: turn_no is pre-increment (before state.meta.turn is updated via set_turn).
        # It's used for LLM calls (ruling/narrate/extraction) which need the "current" turn number.
        # The canonical state update happens via state.set_turn(state.meta.turn + 1).
        _log.info(
            "turn.ruling_complete trace_id=%s turn=%d intent=%s outcome=%s",
            trace_id, turn_no, _intent.intent, _outcome.reason,
            extra={"trace_id": trace_id, "turn": turn_no},
        )

        # TTL expiry: remove world state facts whose expires_turn has passed (before any LLM call)
        ws = list(state.scene.world_state)
        expired_ids: list[str] = []
        for fact in ws:
            if isinstance(fact, dict) and fact.get("expires_turn") is not None and fact["expires_turn"] <= turn_no:
                fact_id = fact.get("id", "")
                if fact_id:
                    expired_ids.append(fact_id)
        if expired_ids:
            state = state.expire_world_state_facts(expired_ids)
            _log.info(
                "world_state.ttl_expiry trace_id=%s turn=%d expired=%s",
                trace_id, turn_no, expired_ids, extra={"trace_id": trace_id, "turn": turn_no},
            )

        # Append roll to recent_rolls rolling window
        if ctx.outcome and ctx.outcome.rolled:
            state = state.add_recent_roll({"turn": turn_no, "band": ctx.outcome.band})

        # === Call 1: Narration streaming ===
        _narrate_result = NarrateResult()
        _narrate_gen = _narrate_phase(ctx, _narrate_result)
        try:
            async for _item in _narrate_gen:
                yield _item
        except StopAsyncIteration:
            pass  # Results are in _narrate_result
        _pc = _narrate_result.pc
        narrative = _narrate_result.narrative
        narr_metrics = _narrate_result.narr_metrics or {}
        rendered_narr_system = _narrate_result.rendered_narr_system
        rendered_narr_user = _narrate_result.rendered_narr_user
        narr_trimmed = _narrate_result.narr_trimmed
        narr_trimmed_chars = _narrate_result.narr_trimmed_chars

        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}
        _extraction_ctx = None
        record_result = None

        # Save narrate extraction to events for verification
        extraction_event["narrate"] = {
            "output": narrative,
            "tokens_in": narr_metrics.get("tokens_in", 0),
            "tokens_out": narr_metrics.get("tokens_out", 0),
            "ms": round(narr_metrics.get("total_ms", 0), 1),
        }

        # === Call 2: Extraction pipeline + metrics ===
        _extract_result_container = ExtractionResult()
        _extract_gen = _extract_phase(env, state, narrative, ctx, _intent, _outcome, config, trace_id, turn_no, recent_turns, narr_metrics, errors, _extract_result_container)
        try:
            async for _item in _extract_gen:
                yield _item
        except StopAsyncIteration:
            pass  # Results are in _extract_result_container
        delta = _extract_result_container.delta
        actions = _extract_result_container.actions or []
        outcome_summary = _extract_result_container.outcome_summary
        extraction_event = _extract_result_container.extraction_event or {}
        record_result = _extract_result_container.record_result
        _extraction_ctx = _extract_result_container.extraction_ctx
        ext_metrics = _extract_result_container.ext_metrics or {}

        metrics = {
            "ruling": ruling_metrics,
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }
        _log.info(
            "turn.extraction_complete trace_id=%s turn=%d ext_ms=%d ext_tokens_in=%d ext_tokens_out=%d",
            trace_id, turn_no, ext_metrics.get("total_ms", 0), ext_metrics.get("tokens_in", 0), ext_metrics.get("tokens_out", 0),
            extra={"trace_id": trace_id, "turn": turn_no},
        )

        # === Validate & apply delta ===
        state_pre_apply, state, delta, applied, rejected, thread_dedup_rejections, reconcile_warnings, narrative = _apply_phase(
            state, delta, record_result, config, trace_id, turn_no, str(save_dir), errors, narrative,
        )

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, rejected)

        # === Turn increment (single source of truth: here) ===
        state = state.set_turn(state.meta.turn + 1)

        if _is_cancel_requested(ctx):
            return
        yield ("phase", {"phase": "persist"})

        # === Persistence + async cleanup ===
        _persist_result = PersistResult()
        _persist_gen = _persist_and_async_cleanup(
            ctx, save_dir, env, state, narrative, user_input,
            _intent, _outcome, ruling_metrics,
            rendered_ruling_system, rendered_ruling_user,
            ruling_raw_response, ruling_parse_error,
            ruling_trimmed, ruling_trimmed_chars,
            _pc, applied, rejected,
            thread_dedup_rejections, reconcile_warnings,
            actions, outcome_summary, ext_metrics,
            extraction_event, errors, trace_id, turn_no,
            config, diff_lines, changes, metrics,
            narr_metrics, rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars,
            _persist_result,
        )
        try:
            async for _item in _persist_gen:
                yield _item
        except StopAsyncIteration:
            pass  # Results are in _persist_result

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
                turn=state.meta.turn,
                trace_id=trace_id,
                narrative=fallback,
                state_delta={},
                errors=errors,
                metrics=metrics,
                diff=[],
                changes={},
                ts="",
                state_snapshot=state,
            ),
        )
    finally:
        _signal_turn_done()


async def _narrate_phase(ctx: TurnContext, narrate_result: NarrateResult) -> AsyncIterator[tuple[str, Any]]:
    """Run narration: setup + streaming + metrics.

    Yields: phase events and tokens.
    Mutates narrate_result with (pc, narrative, narr_metrics, rendered_system, rendered_user, narr_trimmed, narr_trimmed_chars).
    """
    save_dir = ctx.save_dir
    config = ctx.config
    trace_id = ctx.trace_id
    turn_no = ctx.state.meta.turn + 1

    exp_narrate_ms = _avg_event_ms(save_dir, "narrate.total_ms")
    if _is_cancel_requested(ctx):
        return
    yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

    # Build narration context and messages (extracted phase)
    _pc, narr_messages, _ = await _narrate_setup(ctx)

    # Trim + log (stays inline for simplicity)
    rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
    rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""

    narr_messages, narr_trimmed, narr_trimmed_chars = trim_messages(
        narr_messages, config.context_window,
    )

    narrative_chunks: list[str] = []
    first_ms = 0.0
    t0 = asyncio.get_event_loop().time()
    narr_stream_stats: dict[str, Any] = {}
    first_visible = True
    async for chunk in llm_chat_stream(
        config.host,
        config.model,
        narr_messages,
        fallback_host=config.fallback_host,
        fallback_cooldown_s=config.fallback_cooldown_s,
        temperature=config.narrate_temperature,
        top_p=config.narrate_top_p,
        frequency_penalty=config.narrate_frequency_penalty,
        timeout=float(config.request_timeout_s),
        stream_stats=narr_stream_stats,
        num_ctx=config.num_ctx,
    ):
        narrative_chunks.append(chunk)
        if first_visible:
            first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            first_visible = False
            yield ("phase", {"phase": "narrate_first_token", "first_token_ms": round(first_ms, 1)})
        if _is_cancel_requested(ctx):
            return
        yield ("token", chunk)

    narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
    narrative = strip_thinking("".join(narrative_chunks))
    narr_metrics = {
        "first_token_ms": round(first_ms, 1),
        "total_ms": round(narr_ms, 1),
        "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
        "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
        "output": narrative,
    }

    if _is_cancel_requested(ctx):
        return
    yield ("phase", {"phase": "narrate_done"})
    _log.info(
        "turn.narrate_complete trace_id=%s turn=%d narr_ms=%d narr_tokens_in=%d narr_tokens_out=%d",
        trace_id, turn_no, narr_ms, narr_metrics.get("tokens_in", 0), narr_metrics.get("tokens_out", 0),
        extra={"trace_id": trace_id, "turn": turn_no},
    )
    exp_ms = _avg_event_ms(save_dir, "extract.total_ms")
    if _is_cancel_requested(ctx):
        return
    yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})

    narrate_result.pc = _pc
    narrate_result.narrative = narrative
    narrate_result.narr_metrics = narr_metrics
    narrate_result.rendered_narr_system = rendered_narr_system
    narrate_result.rendered_narr_user = rendered_narr_user
    narrate_result.narr_trimmed = narr_trimmed
    narrate_result.narr_trimmed_chars = narr_trimmed_chars


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


async def _extract_phase(
    env: Any, state: WorldState, narrative: str, ctx: TurnContext,
    intent: IntentEnvelope, outcome: RulesOutcome, config: EngineConfig,
    trace_id: str, turn_no: int, recent_turns: list[dict[str, Any]],
    narr_metrics: dict[str, Any], errors: list[dict[str, Any]],
    extract_result: ExtractionResult,
) -> AsyncIterator[tuple[str, Any]]:
    """Run extraction pipeline + build metrics.

    Yields: pipeline events and phase events.
    Mutates extract_result with (delta, actions, outcome_summary, extraction_event, record_result, scene_result, extraction_ctx, ext_metrics).
    """
    t2 = asyncio.get_event_loop().time()

    delta: StateMerge | None = None
    actions: list[str] = []
    outcome_summary: str = ""
    extraction_event: dict[str, Any] = {}
    _extraction_ctx = None
    record_result = None
    scene_result: Any = None

    # Save narrate extraction to events for verification
    extraction_event["narrate"] = {
        "output": narrative,
        "tokens_in": narr_metrics.get("tokens_in", 0),
        "tokens_out": narr_metrics.get("tokens_out", 0),
        "ms": round(narr_metrics.get("total_ms", 0), 1),
    }

    _extract_result = None
    try:
        _log.debug("turn.extraction_pipeline_enter trace_id=%s turn_no=%d", trace_id, turn_no)
        _band = outcome.band if outcome and outcome.rolled else ""
        async for _evt in _run_extraction_pipeline(
            env, state, narrative,
            band=_band,
            intent=intent,
            config=config,
            trace_id=trace_id,
            turn_no=turn_no,
            recent_turns=recent_turns,
            packing=ctx.packing,
        ):
            if isinstance(_evt, tuple) and len(_evt) == 2:
                _log.debug("turn.extraction_evt trace_id=%s evt_type=%s", trace_id, type(_evt[0]).__name__, extra={"event_preview": str(_evt)[:500]})
                if _is_cancel_requested(ctx):
                    return
                yield _evt
            else:
                _extract_result = _evt
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        _log.error("turn.extraction_pipeline_error trace_id=%s turn_no=%d\n%s", trace_id, turn_no, tb)
        errors.append({"kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id, "message": str(exc)})

    if _extract_result is not None:
        delta, actions, outcome_summary, extraction_event, record_result, scene_result, _extraction_ctx = _extract_result

    if _is_cancel_requested(ctx):
        return
    yield ("phase", {"phase": "extract_done"})

    ext_ms = (asyncio.get_event_loop().time() - t2) * 1000

    # Roll up per-stream token counts for the metrics dict
    _tokens_in = sum(
        (extraction_event.get(s) or {}).get("tokens_in", 0)
        for s in ("scene", "state", "record", "narrate", "world")
    )
    _tokens_out = sum(
        (extraction_event.get(s) or {}).get("tokens_out", 0)
        for s in ("scene", "state", "record", "narrate", "world")
    )
    # Build per-stream breakdown for UI display
    _streams = {}
    for s in ("scene", "state", "record", "narrate", "world"):
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
        "retries": sum(
            len((extraction_event.get(s) or {}).get("retry_errors", []))
            for s in ("scene", "state", "record")
        ),
        "retry_errors_by_stream": {
            s: (extraction_event.get(s) or {}).get("retry_errors", [])
            for s in ("scene", "state", "record")
        },
        "streams": _streams,
    }

    extract_result.delta = delta
    extract_result.actions = actions
    extract_result.outcome_summary = outcome_summary
    extract_result.extraction_event = extraction_event
    extract_result.record_result = record_result
    extract_result.scene_result = scene_result
    extract_result.extraction_ctx = _extraction_ctx
    extract_result.ext_metrics = ext_metrics


def _apply_phase(
    state: WorldState, delta: StateMerge | None, record_result: Any | None,
    config: EngineConfig, trace_id: str, turn_no: int, save_dir_str: str,
    errors: list[dict[str, Any]], narrative: str,
) -> tuple[WorldState, WorldState, StateMerge | None, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[str], str]:
    """Apply delta + rejection handling.

    Returns: (state_pre_apply, state, delta, applied, rejected, thread_dedup_rejections, reconcile_warnings, narrative)
    """
    state_pre_apply = state.model_copy()
    applied: dict[str, Any] = {}
    rejected: list[dict[str, Any]] = []
    thread_dedup_rejections: list[dict[str, Any]] = []
    reconcile_warnings: list[str] = []

    if delta is not None:
        state, delta, applied, rejected, reconcile_warnings, thread_dedup_rejections = _apply_state_updates(
            state, delta, record_result, config, trace_id, turn_no, save_dir_str,
        )

    # Blocking rejection handling (stays in run_turn per design)
    blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
    if blocking:
        errors.append(
            {
                "kind": ErrorKind.DELTA_VALIDATION_FAILED,
                "trace_id": trace_id,
                "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
            }
        )
        narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"

    narrative = _strip_fallback(narrative, trace_id=trace_id, turn=turn_no)

    return state_pre_apply, state, delta, applied, rejected, thread_dedup_rejections, reconcile_warnings, narrative


@dataclass
class NarrateResult:
    pc: Any = None
    narrative: str = ""
    narr_metrics: dict[str, Any] | None = None
    rendered_narr_system: str = ""
    rendered_narr_user: str = ""
    narr_trimmed: bool = False
    narr_trimmed_chars: int = 0


@dataclass
class ExtractionResult:
    delta: StateMerge | None = None
    actions: list[str] | None = None
    outcome_summary: str = ""
    extraction_event: dict[str, Any] | None = None
    record_result: Any = None
    scene_result: Any = None
    extraction_ctx: Any = None
    ext_metrics: dict[str, Any] | None = None


@dataclass
class PersistResult:
    result_obj: TurnResult | None = None
    final_metrics: dict[str, Any] | None = None
    final_state: WorldState | None = None


async def _persist_and_async_cleanup(
    ctx: TurnContext, save_dir: Path, env: Any, state: WorldState,
    narrative: str, user_input: str,
    intent: IntentEnvelope, outcome: RulesOutcome, ruling_metrics: dict[str, Any],
    rendered_ruling_system: str, rendered_ruling_user: str,
    ruling_raw_response: str, ruling_parse_error: str | None,
    ruling_trimmed: bool, ruling_trimmed_chars: int,
    pc: Any, applied: dict[str, Any], rejected: list[dict[str, Any]],
    thread_dedup_rejections: list[dict[str, Any]], reconcile_warnings: list[str],
    actions: list[str], outcome_summary: str, ext_metrics: dict[str, Any],
    extraction_event: dict[str, Any], errors: list[dict[str, Any]], trace_id: str, turn_no: int,
    config: EngineConfig, diff_lines: list[str], changes: dict[str, Any], metrics: dict[str, Any],
    narr_metrics: dict[str, Any], rendered_narr_system: str, rendered_narr_user: str,
    narr_trimmed: bool, narr_trimmed_chars: int,
    persist_result: PersistResult,
) -> AsyncIterator[tuple[str, Any]]:
    """Build event, yield complete, run async cleanup (sanitize + world + save).

    Yields: phase events and complete event.
    Mutates persist_result with (result_obj, final_metrics, final_state).
    """
    # Turn increment (single source of truth: here)
    state = state.set_turn(state.meta.turn + 1)

    if _is_cancel_requested(ctx):
        return

    # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
    ruling_event: dict[str, Any] = {
        "intent_verb": intent.intent_verb,
        "intent": intent.intent,
        "rolled": outcome.rolled,
        "impossible": outcome.impossible,
        "reason": outcome.reason,
        "total_ms": ruling_metrics.get("total_ms"),
        "tokens_in": ruling_metrics.get("tokens_in", 0),
        "tokens_out": ruling_metrics.get("tokens_out", 0),
        "outcome_summary": outcome_summary,
        "selected_beat": ctx._selected_beat,
    }
    if outcome.rolled:
        ruling_event.update({
            "skill": outcome.skill,
            "difficulty": outcome.difficulty,
            "dice": outcome.dice,
            "stat_mod": outcome.stat_mod,
            "diff_mod": outcome.diff_mod,
            "raw_total": outcome.raw_total,
            "final_total": outcome.final_total,
            "band": outcome.band,
        })

    _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    beat_candidates = state.meta.beat_candidates or []
    # NPC updates from scene extraction (observability)
    npc_updates = ((extraction_event.get("scene") or {}).get("output") or {}).get("compendium_npc_update") or []
    event = {
        "ts": _ts,
        "trace_id": trace_id,
        "turn": state.meta.turn,
        "type": "turn",
        "input": user_input,
        "applied": applied,
        "rejected": rejected,
        "thread_dedup_rejections": thread_dedup_rejections,
        "actions": actions,
        "ruling": ruling_event,
        "pacing_context": {
            "directive": pc.directive if pc else "",
            "outcome_hint": pc.outcome_hint if pc else None,
            "summary": pc.summary if pc else "",
            "scene_phase": state.scene.scene_phase,
            "climax_turn_count": state.scene.climax_turn_count,
            "breather_turn_count": state.scene.breather_turn_count,
            "convergence_score": pc.convergence_score if pc else 0,
            "convergence_components": pc.convergence_components if pc else {},
            "convergence_threads": pc.convergence_threads if pc else [],
        },
        "beat_candidates": beat_candidates,
        "npc_updates": npc_updates,
        "post_turn_pending_beat": state.meta.pending_gm_beat,
        "allowed_beat_types": derive_allowed_beat_types(
            state.scene.scene_phase,
            directive=pc.directive if pc else "",
        ),
        "post_turn_location_id": state.location.id,
        "scene_phase": state.scene.scene_phase,
        "curtain_call": state.scene.curtain_call,
        "narrate": {**narr_metrics, "prose": narrative},
        "extract": ext_metrics,
        "extraction": extraction_event,
        "changes": changes,
        "reconcile_warnings": reconcile_warnings,
        # Prompt logging (for turn viewer)
        "ruling_prompt": {
            "output": ruling_raw_response,
            "parse_error": ruling_parse_error,
            "context_meta": _context_meta(rendered_ruling_system, rendered_ruling_user, ruling_trimmed, ruling_trimmed_chars),
        },
        "narrate_prompt": {
            "output": narrative,
            "context_meta": _context_meta(rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars),
        },
    }
    # Write stripped prompts to prompts.jsonl
    prompts_list = [
        {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state.meta.turn,
            "stream": "ruling",
            "rendered_system": rendered_ruling_system,
            "rendered_user": rendered_ruling_user,
            "context_meta": _context_meta(rendered_ruling_system, rendered_ruling_user, ruling_trimmed, ruling_trimmed_chars),
        },
        {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state.meta.turn,
            "stream": "narrate",
            "rendered_system": rendered_narr_system,
            "rendered_user": rendered_narr_user,
            "context_meta": _context_meta(rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars),
        },
    ]
    # Add extraction stream prompts from context_meta
    for stream_name in ("scene", "state", "record"):
        stream_data = extraction_event.get(stream_name) or {}
        ctx_meta: dict[str, Any] | None = stream_data.get("context_meta")
        if ctx_meta:
            prompts_list.append({
                "ts": _ts,
                "trace_id": trace_id,
                "turn": state.meta.turn,
                "stream": stream_name,
                "rendered_system": ctx_meta.get("system_text", ""),
                "rendered_user": ctx_meta.get("user_text", ""),
                "context_meta": ctx_meta,
            })
    append_prompts(save_dir, prompts_list)

    append_chronicle(
        save_dir,
        f"\n\n## Turn {state.meta.turn} — {user_input}\n\n{narrative.strip()}",
    )

    # Deferred: prior_history + final save_state (sanitizer and World
    # now run as end-of-turn async phases after yield("complete"))
    if outcome_summary and outcome_summary.strip():
        turn_no = state.meta.turn
        state = state.add_prior_history_bullet(f"- [T{turn_no}] {outcome_summary}")

    result_obj = TurnResult(
        turn=state.meta.turn,
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
        outcome_hint=pc.outcome_hint if pc else None,
        scene_phase=state.scene.scene_phase,
        summary=pc.summary if pc else "",
        ts=_ts,
        state_snapshot=state,
    )
    yield ("complete", result_obj)

    # --- End-of-turn async window (lock held until generator completes) ---
    _log.debug(
        "turn.pre_complete trace_id=%s turn=%d state_turn=%d",
        trace_id, turn_no, state.meta.turn,
        extra={"trace_id": trace_id, "turn": state.meta.turn},
    )

    # 1. Sanitize (moved from synchronous critical path)
    _log.debug("turn.async_window_start trace_id=%s turn=%d", trace_id, state.meta.turn)
    yield ("phase", {"phase": "sanitize_start"})
    t_sanitize = asyncio.get_event_loop().time()
    sanitize_ms: float = 0.0
    try:
        if config.sanitize_every > 0:
            state, sanitize_ran = await sanitize_threads(
                save_dir, state, config, trace_id=trace_id,
            )
            sanitize_ms = (asyncio.get_event_loop().time() - t_sanitize) * 1000
            _log.debug("turn.sanitize_complete trace_id=%s turn=%d sanitize_ran=%s sanitize_ms=%.1f", trace_id, state.meta.turn, sanitize_ran, sanitize_ms)
        else:
            _log.debug("turn.sanitize_skipped trace_id=%s turn=%d sanitize_every=0", trace_id, state.meta.turn)
    except Exception as exc:
        sanitize_ms = (asyncio.get_event_loop().time() - t_sanitize) * 1000
        _log.warning("sanitize step failed: %s", exc, extra={"trace_id": trace_id})
        _log.debug("turn.sanitize_failed trace_id=%s turn=%d error=%s", trace_id, state.meta.turn, exc)
    yield ("phase", {"phase": "sanitize_done"})

    # Persist sanitize metrics to extraction_event for event log
    if sanitize_ms > 0:
        extraction_event["sanitize"] = {
            "ms": round(sanitize_ms, 1),
            "skipped": False,
        }

    # 2. World (beat candidates — receives same live `state` Sanitize just mutated)
    yield ("phase", {"phase": "world_start"})
    _log.debug("turn.world_start trace_id=%s turn=%d", trace_id, state.meta.turn)
    world_system_text = ""
    world_user_text = ""
    world_raw_response = ""
    beat_candidates = []
    world_usage: dict[str, int] = {"tokens_in": 0, "tokens_out": 0}
    t_world = asyncio.get_event_loop().time()
    try:
        _, beat_candidates, world_system_text, world_user_text, world_raw_response, world_usage = await _run_world_step(
            env, state, narrative, pc, config, trace_id, turn_no,
        )
    except Exception as exc:
        _log.warning("world step failed: %s", exc, extra={"trace_id": trace_id})
        _log.debug("turn.world_failed trace_id=%s turn=%d error=%s", trace_id, state.meta.turn, exc)
    world_ms = (asyncio.get_event_loop().time() - t_world) * 1000
    _log.debug("turn.world_complete trace_id=%s turn=%d beats=%d world_ms=%d", trace_id, state.meta.turn, len(beat_candidates or []), round(world_ms, 1))
    state = state.set_beat_candidates(beat_candidates or [])

    # Build world extraction event and write prompts (deferred past async window)
    extraction_event["world"] = {
        "output": beat_candidates or [],
        "skipped": False,
        "tokens_in": world_usage.get("tokens_in", 0),
        "tokens_out": world_usage.get("tokens_out", 0),
        "ms": round(world_ms, 1),
    }
    _ts_WORLD = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prompts_list.append({
        "ts": _ts_WORLD,
        "trace_id": trace_id,
        "turn": state.meta.turn,
        "stream": "world",
        "rendered_system": world_system_text,
        "rendered_user": world_user_text,
    })
    append_prompts(save_dir, prompts_list)

    # Save event/state AFTER async window (with world data included)
    event["last_turn_state"] = state.to_dict()
    append_event(save_dir, event)
    save_state(save_dir, state)
    _log.debug("turn.async_save_complete trace_id=%s turn=%d", trace_id, state.meta.turn)
    _log.info(
        "turn.complete trace_id=%s turn=%d",
        trace_id, state.meta.turn,
        extra={"trace_id": trace_id, "turn": state.meta.turn},
    )

    # Build final metrics including async steps for frontend display
    final_metrics = dict(metrics)
    world_data = extraction_event.get("world")
    if world_data:
        final_metrics.setdefault("extract", {}).setdefault("streams", {})["world"] = {
            "ms": world_data.get("ms", 0),
            "tokens_in": world_data.get("tokens_in", 0),
            "tokens_out": world_data.get("tokens_out", 0),
            "skipped": world_data.get("skipped", False),
        }
    if sanitize_ms > 0:
        final_metrics["sanitize"] = {
            "ms": round(sanitize_ms, 1),
        }

    yield ("phase", {"phase": "world_done", "metrics": final_metrics, "state": state.to_dict()})

    persist_result.result_obj = result_obj
    persist_result.final_metrics = final_metrics
    persist_result.final_state = state


async def warmup(config: EngineConfig) -> None:
    try:
        await llm_chat(
            config.host,
            config.model,
            [{"role": "user", "content": "ok"}],
            fallback_host=config.fallback_host,
            fallback_cooldown_s=config.fallback_cooldown_s,
            temperature=0.0,
            timeout=30.0,
            num_ctx=config.num_ctx,
        )
    except Exception:
        _log.warning("Warmup LLM call failed — continuing without warmup cache")
