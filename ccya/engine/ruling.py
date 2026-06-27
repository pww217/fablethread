"""Ruling LLM call: prompt building, _call_ruling, retry logic."""

from __future__ import annotations

import asyncio
import logging
from jinja2 import Environment
from typing import TYPE_CHECKING, Any



from ccya.engine.config import EngineConfig, _find_json, _log_llm_io, _log_prompts, _PROMPTS_LOG_PATH, _render
from ccya.engine.extraction import _avg_event_ms
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.npc_roster import build_npc_roster
from ccya.engine._pacing import _compute_ages
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.models import Band, IntentEnvelope, RulesCheck, RulesOutcome
from ccya.personality import ARCHETYPES
from ccya.rules import resolve_check, build_directive

if TYPE_CHECKING:
    from ccya.engine.turn_context import TurnContext

_log = logging.getLogger(__name__)


def _ruling_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    turn_no: int = 0,
    npc_roster: list[dict[str, Any]] | None = None,
    inventory: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    scene_phase: str = "SETUP",
    beat_candidates: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    system_text = _render(env, "ruling_system.j2", {})

    # Build urgent_threads from arc.threads with urgency == "urgent"
    arc = state.get("arc") or {}
    threads = arc.get("threads") or []
    urgent_threads = []
    for t in threads:
        if t.get("urgency") == "urgent":
            urgent_threads.append({
                "id": t.get("id", ""),
                "summary": t.get("summary", ""),
                "progress": t.get("major_updates", []),
            })

    user_text = _render(
        env,
        "ruling_user.j2",
        {
            "pc": pc,
            "location": location,
            "user_input": user_input,
            "meta": {"turn": turn_no},
            "npc_roster": npc_roster or [],
            "inventory": inventory or [],
            "recent_turns": recent_turns or [],
            "scene_phase": scene_phase,
            "urgent_threads": urgent_threads,
            "conditions": list(pc.get("conditions") or []),
            "state": state,
            "pc_situation": pc.get("situation") or {},
            "beat_candidates": beat_candidates or [],
        },
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


async def _call_ruling(
    messages: list[dict[str, Any]],
    config: EngineConfig,
    trace_id: str,
    turn: int = 0,
) -> tuple[IntentEnvelope, dict[str, int], str, str, dict[str, Any] | None]:
    _no_intent = IntentEnvelope(
        intent="",
        intent_verb="act",
        check=RulesCheck(required=False),
    )
    _no_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    parse_error = ""

    _log.info(
        "ruling call start turn=%d messages=%d max_retries=%d",
        turn, len(messages), config.max_llm_retries,
        extra={"trace_id": trace_id, "turn": turn},
    )

    for attempt in range(1 + config.max_llm_retries):
        try:
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"ruling_request_attempt_{attempt}",
                    messages=messages,
                    max_chars=config.log_llm_io_max_chars,
                )
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.ruling_temperature,
                top_p=config.ruling_top_p,
                timeout=float(config.request_timeout_s),
            )
            raw = result.get("response", "") if isinstance(result, dict) else ""
            usage = result.get("usage", {}) if isinstance(result, dict) else _no_usage
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"ruling_response_attempt_{attempt}",
                    response=raw,
                    max_chars=config.log_llm_io_max_chars,
                )
            cleaned = strip_thinking(raw)
            j = _find_json(cleaned)
            if j is None:
                raise ValueError("No JSON found in ruling response")
            selected_beat = j.pop("selected_beat", None)
            intent = IntentEnvelope(**j)
            if not intent.reason.strip():
                raise ValueError(f"reason is empty — must use [Ruling] [connector] [Reason] structure in 5-7 words (got reason={j.get('reason', '')!r})")
            if intent.check.required and not intent.check.skill:
                raise ValueError(f"check.required=true but check.skill is missing/empty (got {j.get('check', {}).get('skill', None)})")
            return intent, {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }, raw, "", selected_beat
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "ruling parse failed (attempt %d/%d): %s",
                attempt + 1,
                1 + config.max_llm_retries,
                parse_error,
                extra={"trace_id": trace_id, "turn": turn},
            )

            if attempt < config.max_llm_retries:
                fb = (
                    f"Your previous output failed to parse: {parse_error[:200]}. "
                    "Re-emit the IntentEnvelope JSON only. No prose."
                )
                messages.append({"role": "user", "content": fb})

    _log.warning(
        "ruling call failed after all attempts — defaulting to no-roll",
        extra={"trace_id": trace_id, "turn": turn, "error_kind": "RULING_PARSE_FAILED"},
    )
    return _no_intent, _no_usage, "", parse_error, None



def _log_ruling_outcome(
    turn: int, intent: "IntentEnvelope", outcome: "RulesOutcome"
) -> None:
    lines: list[str] = []
    lines.append(f"## Turn {turn} — ruling engine output")
    lines.append("")
    lines.append("--- [Intent] ---")
    lines.append(f"intent:        {intent.intent}")
    lines.append(f"intent_verb:   {intent.intent_verb}")
    lines.append(f"target:        {intent.target}")
    lines.append("")
    lines.append("--- [Dice Roll] ---")
    if outcome.rolled:
        lines.append("rolled:       True")
        lines.append(f"skill:        {outcome.skill}")
        lines.append(f"stat_value:   {outcome.stat_value}")
        lines.append(f"stat_mod:     {outcome.stat_mod}")
        lines.append(f"difficulty:   {outcome.difficulty}")
        lines.append(f"diff_mod:     {outcome.diff_mod}")
        lines.append(f"reason:       {intent.reason}")
        lines.append(f"dice:         {outcome.dice}")
        lines.append(f"raw_total:    {outcome.raw_total}")
        lines.append(f"final_total:  {outcome.final_total}")
        lines.append(f"band:         {outcome.band}")
        lines.append(f"directive:    {outcome.directive}")
    else:
        lines.append("rolled:       False (no dice check required)")
    lines.append("")
    lines.append("---")
    lines.append("")

    try:
        with open(_PROMPTS_LOG_PATH, "a") as f:
            f.write("\n".join(lines))
    except OSError:
        _log.warning("failed to write prompts.log (ruling outcome)", exc_info=True)


async def _ruling_phase(ctx: "TurnContext") -> tuple[Any, Any, dict[str, Any], float, list[tuple[str, Any]]]:
    """Execute ruling phase. Returns (intent, outcome, metrics, deescalate, phase_events)."""
    config = ctx.config
    state = ctx.state
    trace_id = ctx.trace_id
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    exp_ruling_ms = _avg_event_ms(ctx.save_dir, "ruling.total_ms")
    phase_events: list[tuple[str, Any]] = [("phase", {"phase": "ruling_start", "expected_ms": exp_ruling_ms})]
    t_rules = asyncio.get_event_loop().time()

    # Build ruling messages
    _comp = state.get("compendium", {}).get("npcs", {})
    scene_phase = (state.get("scene") or {}).get("scene_phase", "SETUP")
    beat_candidates = (state.get("meta") or {}).get("beat_candidates") or []
    ruling_messages = _ruling_messages(
        ctx._env, state, ctx.user_input,
        turn_no=turn_no,
        npc_roster=build_npc_roster(_comp, turn_no=turn_no, personality_registry=ARCHETYPES),
        inventory=state.get("inventory") or None,
        recent_turns=ctx.recent_turns[-1:],
        scene_phase=scene_phase,
        beat_candidates=beat_candidates,
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

    intent, ruling_usage, ruling_raw_response, ruling_parse_error, selected_beat = await _call_ruling(
        ruling_messages, config, trace_id,
    )
    ctx.intent = intent
    ctx._ruling_raw_response = ruling_raw_response
    ctx._ruling_parse_error = ruling_parse_error
    ctx._ruling_trimmed = ruling_trimmed
    ctx._ruling_trimmed_chars = ruling_trimmed_chars

    # Beat lifecycle: index-based selection from beat_candidates
    beat_candidates = (state.get("meta") or {}).get("beat_candidates") or []
    beat: dict[str, Any] | None = None
    if selected_beat is not None and isinstance(selected_beat, int) and 0 <= selected_beat < len(beat_candidates):
        beat = beat_candidates[selected_beat]

    if beat and beat.get("type"):
        state.setdefault("meta", {})["pending_gm_beat"] = {
            "type": beat["type"],
            "effect": beat.get("effect", ""),
        }
        meta = state.setdefault("meta", {})
        meta.setdefault("recent_beats", []).append({
            "turn": turn_no,
            "type": beat["type"],
            "effect": beat.get("effect", ""),
        })
        max_beats = config.recent_beats_max or 5
        if len(meta["recent_beats"]) > max_beats:
            meta["recent_beats"] = meta["recent_beats"][-max_beats:]
    else:
        state.get("meta", {}).pop("pending_gm_beat", None)

    # Always discard candidates
    state.get("meta", {}).pop("beat_candidates", None)

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
            outcome.reason = intent.reason
        except Exception as exc:
            _log.warning(
                "rules.resolve_check failed: %s", exc, extra={"trace_id": trace_id}
            )
            outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent, reason=intent.reason)
    elif intent.check.required and not intent.check.skill:
        _log.warning(
            "rules: check required on T%d but skill=%s — no roll will occur",
            state.get("meta", {}).get("turn", 0) + 1,
            intent.check.skill,
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent)
        outcome.reason = intent.reason
    else:
        outcome = RulesOutcome(rolled=False, intent_verb=intent.intent_verb, intent=intent.intent)
        outcome.reason = intent.reason

    ctx.outcome = outcome

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