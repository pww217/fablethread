"""Turn orchestrator: run_turn, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator


from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts, is_cancel_requested, register_persist, register_turn, signal_turn_done
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.extraction import (
    _avg_event_ms,
    _context_meta,
    _run_extraction_pipeline,
)
from ccya.engine._pacing import (
    _recent_turn_count,
    derive_allowed_beat_types,
)
from ccya.engine.turn_context import TurnContext
from ccya.engine.thread_sanitizer import sanitize_threads
from ccya.engine.turn_state import (
    _apply_state_updates,
)
from ccya.engine.ruling import _ruling_phase
from ccya.engine.narrate import _narrate_setup
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    StateDelta,
    TurnResult,
)

from ccya.errors import ErrorKind, LlmcTimeout, LlmcError

from ccya.state import (
    append_chronicle,
    append_event,
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
        _intent, _outcome, ruling_metrics, deescalate, ruling_phase_events = await _ruling_phase(ctx)
        if is_cancel_requested(str(save_dir)):
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

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # Append roll to recent_rolls rolling window for spiral detection
        if ctx.outcome and ctx.outcome.rolled:
            recent_rolls = state.setdefault("meta", {}).setdefault("recent_rolls", [])
            recent_rolls.insert(0, {"turn": turn_no, "band": ctx.outcome.band})
            if len(recent_rolls) > 5:
                recent_rolls.pop()

        # === Call 1: Narration setup (extracted) + streaming ===
        exp_narrate_ms = _avg_event_ms(save_dir, "narrate.total_ms")
        if is_cancel_requested(str(save_dir)):
            return
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Build narration context and messages (extracted phase)
        _pc, narr_messages = await _narrate_setup(ctx)

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
            "output": narrative,
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
        storyteller_result = None

        # Save narrate extraction to events for verification
        extraction_event["narrate"] = {
            "rendered_system": rendered_narr_system,
            "rendered_user": rendered_narr_user,
            "output": narrative,
            "tokens_in": narr_metrics.get("tokens_in", 0),
            "tokens_out": narr_metrics.get("tokens_out", 0),
            "ms": round(narr_ms, 1),
        }

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
            errors.append({"kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id, "message": str(exc)})

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

        if is_cancel_requested(str(save_dir)):
            return
        yield ("phase", {"phase": "extract_done"})

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        # Roll up per-stream token counts for the metrics dict
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "storytell", "narrate")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "storytell", "narrate")
        )
        # Build per-stream breakdown for UI display
        _streams = {}
        for s in ("scene", "state", "storytell", "narrate"):
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
                for s in ("scene", "state", "storytell")
            ),
            "retry_errors_by_stream": {
                s: (extraction_event.get(s) or {}).get("retry_errors", [])
                for s in ("scene", "state", "storytell")
            },
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
        thread_dedup_rejections: list[dict[str, Any]] = []
        reconcile_warnings: list[str] = []

        if delta is not None:
            state, delta, applied, rejected, reconcile_warnings, thread_dedup_rejections = _apply_state_updates(
                state, delta, storyteller_result, config, trace_id, turn_no,
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
            })

        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "thread_dedup_rejections": thread_dedup_rejections,
            "actions": actions,
            "ruling": ruling_event,
            "pacing_context": {
                "directive": _pc.directive if _pc else "",
                "outcome_hint": _pc.outcome_hint if _pc else None,
                "spiral_detected": _pc.spiral_detected if _pc else False,
                "summary": _pc.summary if _pc else "",
                "scene_phase": state.get("scene", {}).get("scene_phase", "SETUP"),
                "climax_turn_count": state.get("scene", {}).get("climax_turn_count", 0),
                "breather_turn_count": state.get("scene", {}).get("breather_turn_count", 0),
                "convergence_score": _pc.convergence_score if _pc else 0,
                "convergence_components": _pc.convergence_components if _pc else {},
            },
            "post_turn_pending_beat": state.get("meta", {}).get("pending_gm_beat"),
            "allowed_beat_types": derive_allowed_beat_types(
                state.get("scene", {}).get("scene_phase", "SETUP"),
                directive=_pc.directive if _pc else "",
                spiral_detected=_pc.spiral_detected if _pc else False,
            ),
            "post_turn_location_id": state.get("location", {}).get("id"),
            "scene_phase": state.get("scene", {}).get("scene_phase", "SETUP"),
            "narrate": narr_metrics | {"prose": narrative},
            "extract": ext_metrics,
            "extraction": extraction_event,
            "changes": changes,
            "reconcile_warnings": reconcile_warnings,
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
        # Snapshot post-turn state before overwriting — used by delete_last_turn
        register_persist(str(save_dir))
        save_state(save_dir, state)
        event["state_snapshot"] = load_state(save_dir)
        append_event(save_dir, event)
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
            gm_beat={
                "type": storyteller_result.gm_beat.type,
                "effect": storyteller_result.gm_beat.effect,
            } if (storyteller_result and storyteller_result.gm_beat) else None,
            outcome_hint=_pc.outcome_hint if _pc else None,
            scene_phase=state.get("scene", {}).get("scene_phase", "SETUP"),
            summary=_pc.summary if _pc else "",
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
