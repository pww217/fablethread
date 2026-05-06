"""Turn orchestrator: run_turn, run_turn_retry, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts
from ccya.engine.extraction import (
    _avg_extract_ms,
    _avg_narrate_ms,
    _run_extraction_pipeline,
)
from ccya.engine.names import generate_npc_names
from ccya.engine.narrate import _narrate_messages
from ccya.engine.pressure import _expire_scene_pressures
from ccya.engine.rules import _avg_rules_ms, _call_rules, _log_rules_outcome, _rules_messages
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    IntentEnvelope,
    RulesCheck,
    RulesOutcome,
    StateDelta,
    TurnResult,
)
from ccya.pack import ExtractExample
from ccya.rules import resolve_check
from ccya.state import (
    apply_delta,
    apply_momentum,
    append_chronicle,
    append_event,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_recent_events,
    load_state,
    reconcile_delta,
    resolve_inventory_remove_target,
    save_state,
)

_log = logging.getLogger("ccya.engine")


async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_style: str = "",
    pack_examples: list[ExtractExample] | None = None,
    pack_name_locales: list[dict[str, Any]] = [],
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
    recent_events: list[dict[str, Any]] = []
    intent = IntentEnvelope(
        intent="", intent_verb="act", check=RulesCheck(required=False)
    )
    outcome = RulesOutcome(rolled=False)
    rules_metrics: dict[str, Any] = {"total_ms": 0, "rolled": False}

    try:
        await _inflight.acquire(str(save_dir))

        # Prompt capture variables (initialized early for exception safety)
        rendered_rules_system = ""
        rendered_rules_user = ""
        rendered_narr_system = ""
        rendered_narr_user = ""
        rules_raw_response = ""
        narrative = ""

        # --- Memory: load chronicle tail + recent turns ---
        # chronicle_tail is older history (compressed); recent_turns is the rolling
        # window. Slice the last window_turns from the tail to avoid overlap.
        recent_turns = load_recent_chronicle_turns(save_dir, config.window_turns)
        chronicle_tail = load_chronicle_tail(
            save_dir,
            config.chronicle_prefix_budget_tokens,
            skip_last_n_turns=config.window_turns,
        )

        # Load failed preconditions from the most recent event (for narrate feedback)
        last_events = load_recent_events(save_dir, 1)
        last_turn_failed: list[str] = []
        if last_events:
            last_turn_failed = last_events[0].get("failed", [])

        # === Call 0: Rules / intent classification ===
        exp_rules_ms = _avg_rules_ms(save_dir)
        yield ("phase", {"phase": "rules_start", "expected_ms": exp_rules_ms})
        t_rules = asyncio.get_event_loop().time()

        rules_messages = _rules_messages(
            env, state, user_input, recent_turns=recent_turns[-1:]
        )
        rules_messages = trim_messages(rules_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "rules", rules_messages
            )
        rendered_rules_system = rules_messages[0]["content"] if rules_messages else ""
        rendered_rules_user = rules_messages[-1]["content"] if rules_messages else ""
        intent, rules_usage, rules_raw_response = await _call_rules(rules_messages, config, trace_id)

        # Resolve dice in Python (deterministic) — _call_rules degrades intent, we do outcome here
        if intent.check.required and intent.check.skill:
            try:
                # Normalize structured Condition dicts to ids for the rules engine.
                _pc_conds_struct = list((state.get("pc") or {}).get("conditions") or [])
                _pc_cond_ids = [
                    c.get("id", "") if isinstance(c, dict) else str(c)
                    for c in _pc_conds_struct
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
                outcome = RulesOutcome(
                    rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
                )
        else:
            outcome = RulesOutcome(
                rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
            )

        # Apply momentum deterministically from band (never from LLM)
        if outcome.rolled:
            apply_momentum(state, outcome.band)

        if config.log_prompts:
            _log_rules_outcome(
                state.get("meta", {}).get("turn", 0) + 1, intent, outcome
            )

        rules_ms = (asyncio.get_event_loop().time() - t_rules) * 1000
        rules_metrics = {
            "total_ms": round(rules_ms, 1),
            "rolled": outcome.rolled,
            "tokens_in": rules_usage.get("prompt_tokens", 0),
            "tokens_out": rules_usage.get("total_tokens", 0),
        }

        yield (
            "phase",
            {
                "phase": "rules_done",
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
        )

        # === Call 1: Narrate (streaming) ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Rolling NPC name pool for mid-game cultural anchoring
        _npc_name_pool: list[str] = []
        if pack_name_locales:
            _npc_name_pool = generate_npc_names(
                pack_name_locales,
                count=10,
                seed=state.get("meta", {}).get("turn", 0),
            )

        # Read pending_gm_beat from previous turn's progress extraction
        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")

        narr_messages = _narrate_messages(
            env,
            state,
            user_input,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            last_turn_failed=last_turn_failed,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_gm_beat=_pending_gm_beat,
        )
        narr_messages = trim_messages(narr_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages
            )
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""

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
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            if not narrative_chunks:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            narrative_chunks.append(chunk)
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

        # Clear pending_gm_beat after narration consumed it
        state.setdefault("meta", {})["pending_gm_beat"] = None

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        failed: list[str] = []
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, failed, extraction_event, progress_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    pack_examples=pack_examples,
                )
            )
            # Store gm_beat for next turn's narration
            if progress_result and progress_result.gm_beat and progress_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = progress_result.gm_beat.model_dump(exclude_none=True)
            if failed:
                _log.info(
                    "Turn %d: failed preconditions: %s",
                    turn_no,
                    failed,
                    extra={"trace_id": trace_id},
                )
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        yield ("phase", {"phase": "extract_done"})

        # --- Scene pressure: expiry + urgency escalation ---
        if delta is not None:
            _expire_scene_pressures(state, delta, config)

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        # Roll up per-stream token counts for the metrics dict
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "progress")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "progress")
        )
        # Build per-stream breakdown for UI display
        _streams = {}
        for s in ("scene", "state", "progress"):
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
            "rules": rules_metrics,
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
                reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
                recent_events = list(delta.recent_events_add)
                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

        # Decay recently_left counter (engine-side, not in state.py).
        scene = state.get("scene", {})
        turns = scene.get("recently_left_turns", 0)
        if turns > 0:
            turns -= 1
            if turns == 0:
                scene["recently_left"] = []
            else:
                scene["recently_left_turns"] = turns

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_recent_chronicle_turns).
        rules_event: dict[str, Any] = {
            "intent_verb": intent.intent_verb,
            "intent": intent.intent,
            "rolled": outcome.rolled,
            "total_ms": rules_metrics.get("total_ms"),
            "tokens_in": rules_metrics.get("tokens_in", 0),
            "tokens_out": rules_metrics.get("tokens_out", 0),
        }
        if outcome.rolled:
            rules_event.update({
                "skill": outcome.skill,
                "difficulty": outcome.difficulty,
                "dice": outcome.dice,
                "stat_mod": outcome.stat_mod,
                "diff_mod": outcome.diff_mod,
                "cond_mod": outcome.cond_mod,
                "final_total": outcome.final_total,
                "band": outcome.band,
                "outcome_summary": outcome_summary,
            })

        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "rules": rules_event,
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "changes": changes,
            "failed": failed if failed else [],
            # Prompt logging (for turn viewer)
            "rules_prompt": {
                "rendered_system": rendered_rules_system,
                "rendered_user": rendered_rules_user,
                "output": rules_raw_response,
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {user_input}\n\n{narrative.strip()}",
        )

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            recent_events=recent_events,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            rules=rules_event or {},
            outcome_summary=outcome_summary,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
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
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "value": rem.id,
                    "reason": f"Inventory item '{rem.id}' does not exist",
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

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections


async def run_turn_retry(
    save_dir: Path,
    rules_outcome: RulesOutcome,
    intent: IntentEnvelope,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_style: str = "",
    pack_examples: list[ExtractExample] | None = None,
    pack_name_locales: list[dict[str, Any]] = [],
) -> AsyncIterator[tuple[str, Any]]:
    """Re-roll narration + extraction with the same rules outcome.

    Skips Call 0 (rules), uses the provided rules_outcome for Call 1 (narrate),
    then re-runs the extraction pipeline. Increments turn counter and writes
    a new turn entry.
    """
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
    recent_events: list[dict[str, Any]] = []
    outcome = rules_outcome

    try:
        await _inflight.acquire(str(save_dir))

        rendered_narr_system = ""
        rendered_narr_user = ""
        narrative = ""

        recent_turns = load_recent_chronicle_turns(save_dir, config.window_turns)
        chronicle_tail = load_chronicle_tail(
            save_dir,
            config.chronicle_prefix_budget_tokens,
            skip_last_n_turns=config.window_turns,
        )

        last_events = load_recent_events(save_dir, 1)
        last_turn_failed: list[str] = []
        if last_events:
            last_turn_failed = last_events[0].get("failed", [])

        # === Call 1: Narrate (streaming) — same as run_turn ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        _npc_name_pool: list[str] = []
        if pack_name_locales:
            _npc_name_pool = generate_npc_names(
                pack_name_locales,
                count=10,
                seed=state.get("meta", {}).get("turn", 0),
            )

        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")

        narr_messages = _narrate_messages(
            env,
            state,
            intent.intent,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            last_turn_failed=last_turn_failed,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_gm_beat=_pending_gm_beat,
        )
        narr_messages = trim_messages(narr_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages
            )
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""

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
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            if not narrative_chunks:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            narrative_chunks.append(chunk)
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

        state.setdefault("meta", {})["pending_gm_beat"] = None

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        failed: list[str] = []
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, failed, extraction_event, progress_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    pack_examples=pack_examples,
                )
            )
            if progress_result and progress_result.gm_beat and progress_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = progress_result.gm_beat.model_dump(exclude_none=True)
            if failed:
                _log.info(
                    "Turn %d: failed preconditions: %s",
                    turn_no,
                    failed,
                    extra={"trace_id": trace_id},
                )
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        yield ("phase", {"phase": "extract_done"})

        if delta is not None:
            _expire_scene_pressures(state, delta, config)

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "progress")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "progress")
        )
        _streams = {}
        for s in ("scene", "state", "progress"):
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
            "rules": {"total_ms": 0, "rolled": False},
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
                reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
                recent_events = list(delta.recent_events_add)
                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

        scene = state.get("scene", {})
        turns = scene.get("recently_left_turns", 0)
        if turns > 0:
            turns -= 1
            if turns == 0:
                scene["recently_left"] = []
            else:
                scene["recently_left_turns"] = turns

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        rules_event: dict[str, Any] = {
            "intent_verb": intent.intent_verb,
            "intent": intent.intent,
            "rolled": outcome.rolled,
            "total_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
        }
        if outcome.rolled:
            rules_event.update({
                "skill": outcome.skill,
                "difficulty": outcome.difficulty,
                "dice": outcome.dice,
                "stat_mod": outcome.stat_mod,
                "diff_mod": outcome.diff_mod,
                "cond_mod": outcome.cond_mod,
                "final_total": outcome.final_total,
                "band": outcome.band,
                "outcome_summary": outcome_summary,
            })

        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": intent.intent,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "rules": rules_event,
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "changes": changes,
            "failed": failed if failed else [],
            "rules_prompt": {
                "rendered_system": "",
                "rendered_user": "",
                "output": "",
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {intent.intent}\n\n{narrative.strip()}",
        )

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            recent_events=recent_events,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            rules=rules_event or {},
            outcome_summary=outcome_summary,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
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
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


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
        pass
