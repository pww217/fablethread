"""Three-stream extraction pipeline: scene, state, progress."""

from __future__ import annotations

import asyncio
import json
import logging
from jinja2 import Environment
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.narrate import _known_characters_for_extract
from ccya.llm_client import (
    apply_thinking,
    chat as llm_chat,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    IntentEnvelope,
    ProgressExtractResult,
    RulesOutcome,
    SceneExtractResult,
    StateExtractResult,
    StateDelta,
)
from ccya.pack import ExtractExample

_log = logging.getLogger("ccya.engine")


def _context_meta(rendered_system: str, rendered_user: str, was_trimmed: bool, trimmed_chars: int) -> dict[str, Any]:
    """Compute context size signals for telemetry."""
    return {
        "system_chars": len(rendered_system),
        "user_chars": len(rendered_user),
        "total_chars": len(rendered_system) + len(rendered_user),
        "est_tokens": int((len(rendered_system) + len(rendered_user)) / 3.5),
        "trimmed": was_trimmed,
        "trimmed_chars": trimmed_chars,
    }


def _scene_npc_roster(known_characters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a deduped NPC roster for the scene extractor user prompt.

    Each row is ``{id, name, notes, tags}`` where tags = {"compendium"}.
    """
    by_id: dict[str, dict[str, Any]] = {}

    def _put(nid: str, name: str, notes: str, tag: str) -> None:
        if not nid:
            return
        row = by_id.setdefault(nid, {"id": nid, "name": "", "notes": "", "tags": []})
        if name and not row["name"]:
            row["name"] = name
        if notes and not row["notes"]:
            row["notes"] = notes
        if tag not in row["tags"]:
            row["tags"].append(tag)

    for row in known_characters or []:
        _put(str(row.get("id") or ""), str(row.get("name") or ""), "", "compendium")

    return list(by_id.values())


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (scene + UI hints)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=True)
    npc_roster = _scene_npc_roster(known_characters)
    present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "location": location,
            "conditions": conditions,
            "npc_roster": npc_roster,
            "present_npcs": present_npcs,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    scene_result: "SceneExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    pack_examples: list["ExtractExample"] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}

    # Cross-stream scene context (minimal surface)
    loc_id = (
        scene_result.location_change.id
        if scene_result.location_change
        else location.get("id", "")
    )
    scene_ctx = {
        "location_id": loc_id,
        "location_changed": bool(scene_result.location_change),
    }

    # Filter examples by band (band-scoped extract examples)
    band = rules_outcome.band if rules_outcome and rules_outcome.rolled else ""
    band_examples = [
        ex for ex in (pack_examples or [])
        if not ex.band or ex.band == band
    ]

    system_text = _render(env, "extract_state_system.j2", {})
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "scene_result": scene_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
            "band_examples": band_examples,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _quest_threshold_directive(active_quests: list[dict[str, Any]]) -> str:
    """One-line guidance for the progress extractor on whether to start a new quest.

    Computed in Python to keep the system prompt byte-stable; the resulting
    sentence is injected into the user prompt only.
    """
    n = len(active_quests)
    if n == 0:
        return (
            "No active quests. Bar for starting a new quest is LOW — any goal that takes "
            "more than one turn (a journey, errand, finding someone, resolving a conflict, "
            "delivering something) qualifies."
        )
    if n >= 3:
        return (
            f"{n} active quests already. Bar is HIGH — only start a new quest for a major "
            "new obligation clearly distinct from all existing quests."
        )
    return (
        "Start a new quest only if the narration introduces a clear multi-turn goal "
        "distinct from existing quests."
    )


def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (quests + facts + compendium)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])
    known_characters = _known_characters_for_extract(state, compact=False)

    # Cross-stream: minimal surfaces
    scene_ctx: dict[str, Any] = {}
    state_ctx = {
        "items_gained": [it.name for it in state_result.inventory_add],
        "items_lost": [it.id for it in state_result.inventory_remove],
    }

    system_text = _render(env, "extract_progress_system.j2", {})
    scene_pressure = list((state.get("scene") or {}).get("scene_pressure") or [])
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "active_quests": active_quests,
            "recent_events": recent_events,
            "world_state": world_state,
            "scene_pressure": scene_pressure,
            "known_characters": known_characters,
            "scene_result": scene_ctx,
            "state_result": state_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active_domains,
            "quest_threshold_directive": _quest_threshold_directive(active_quests),
            "deescalate": deescalate,
            "quest_ages": quest_ages or [],
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _parse_stream_result(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    return model_cls(**j)


async def _call_stream(
    messages: list[dict[str, Any]],
    config: "EngineConfig",
    trace_id: str,
    phase: str,
    model_cls: type[Any],
    strip_keys: tuple[str, ...] = ("_reasoning",),
) -> tuple[Any, dict[str, Any], int, list[str]]:
    """Call llm_chat with retry. Returns (parsed_result, usage_dict, attempts_used, retry_errors)."""
    parse_error = ""
    usage: dict[str, Any] = {}
    retry_errors: list[str] = []
    for attempt in range(1 + config.max_extract_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"{phase}_request_attempt_{attempt}",
                messages=messages,
                max_chars=config.log_llm_io_max_chars,
            )
        result = await llm_chat(
            config.host,
            config.model,
            messages,
            temperature=config.extract_temperature,
            timeout=float(config.request_timeout_s),
        )
        raw = result.get("response", "") if isinstance(result, dict) else ""
        usage = result.get("usage", {}) if isinstance(result, dict) else {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"{phase}_response_attempt_{attempt}",
                response=raw,
                max_chars=config.log_llm_io_max_chars,
            )
        try:
            return _parse_stream_result(raw, model_cls, strip_keys), usage, attempt + 1, retry_errors
        except Exception as exc:
            parse_error = str(exc)
            retry_errors.append(parse_error)
            _log.warning(
                "%s parse failed (attempt %d/%d): %s",
                phase,
                attempt + 1,
                1 + config.max_extract_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_extract_retries:
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous output failed to parse: {parse_error[:200]}. "
                        "Re-emit JSON matching the schema. No prose outside <thinking>."
                    ),
                })
    raise ValueError(f"{phase} failed after all attempts: {parse_error}")


async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    pack_examples: list["ExtractExample"] | None = None,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
) -> tuple["StateDelta", list[str], str, list[str], dict[str, Any], "ProgressExtractResult"]:
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, failed, per_stream_event_data, progress_result)
    """
    active = set(active_domains)

    _SKIPPED: dict[str, Any] = {
        "skipped": True,
        "tokens_in": 0,
        "tokens_out": 0,
        "ms": 0,
        "attempts": 0,
        "retry_errors": [],
    }

    # Defaults if a stream is skipped
    scene_result = SceneExtractResult()
    state_result = StateExtractResult()
    progress_result = ProgressExtractResult()
    extraction_event: dict[str, Any] = {}

    # --- Stream 1: Scene ---
    scene_domains = {"scene", "location_change"}
    run_scene = bool(scene_domains & active)
    if run_scene:
        t_scene = asyncio.get_event_loop().time()
        scene_msgs = _extract_scene_messages(
            env, narration, state,
            active_domains=active_domains,
            rules_outcome=rules_outcome,
            enable_thinking=config.enable_extract_thinking,
        )
        # Capture pre-trim content for context_meta so the judge sees original sizes
        rendered_scene_system = scene_msgs[0]["content"] if scene_msgs else ""
        rendered_scene_user = scene_msgs[-1]["content"] if scene_msgs else ""
        scene_msgs, scene_trimmed, scene_trimmed_chars = trim_messages(scene_msgs, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(turn_no, "extract_scene", scene_msgs)

        try:
            scene_result, scene_usage, scene_attempts, scene_retry_errors = await _call_stream(
                scene_msgs, config, trace_id, "extract_scene", SceneExtractResult
            )
            extraction_event["scene"] = {
                "rendered_system": rendered_scene_system,
                "rendered_user": rendered_scene_user,
                "output": scene_result.model_dump(),
                "skipped": False,
                "attempts": scene_attempts,
                "retry_errors": scene_retry_errors,
                "tokens_in": scene_usage.get("prompt_tokens", 0),
                "tokens_out": scene_usage.get("total_tokens", 0),
                "ms": round((asyncio.get_event_loop().time() - t_scene) * 1000, 1),
                "context_meta": _context_meta(rendered_scene_system, rendered_scene_user, scene_trimmed, scene_trimmed_chars),
            }
        except Exception as exc:
            _log.warning("extract_scene failed: %s", exc, extra={"trace_id": trace_id})
            extraction_event["scene"] = {**_SKIPPED, "error": str(exc)}
    else:
        _log.debug("Skipping scene stream — neither scene nor location_change in active_domains")
        extraction_event["scene"] = _SKIPPED

    # --- Stream 2: State ---
    run_state = bool({"inventory", "pc_condition"} & active)
    if run_state:
        t_state = asyncio.get_event_loop().time()
        state_msgs = _extract_state_messages(
            env, narration, state,
            active_domains=active_domains,
            scene_result=scene_result,
            rules_outcome=rules_outcome,
            enable_thinking=config.enable_extract_thinking,
            pack_examples=pack_examples,
        )
        # Capture pre-trim content for context_meta so the judge sees original sizes
        rendered_state_system = state_msgs[0]["content"] if state_msgs else ""
        rendered_state_user = state_msgs[-1]["content"] if state_msgs else ""
        state_msgs, state_trimmed, state_trimmed_chars = trim_messages(state_msgs, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(turn_no, "extract_state", state_msgs)

        try:
            state_result, state_usage, state_attempts, state_retry_errors = await _call_stream(
                state_msgs, config, trace_id, "extract_state",
                StateExtractResult, strip_keys=("_reasoning",),
            )
            extraction_event["state"] = {
                "rendered_system": rendered_state_system,
                "rendered_user": rendered_state_user,
                "output": state_result.model_dump(),
                "skipped": False,
                "attempts": state_attempts,
                "retry_errors": state_retry_errors,
                "tokens_in": state_usage.get("prompt_tokens", 0),
                "tokens_out": state_usage.get("total_tokens", 0),
                "ms": round((asyncio.get_event_loop().time() - t_state) * 1000, 1),
                "context_meta": _context_meta(rendered_state_system, rendered_state_user, state_trimmed, state_trimmed_chars),
            }
        except Exception as exc:
            _log.warning("extract_state failed: %s", exc, extra={"trace_id": trace_id})
            extraction_event["state"] = {**_SKIPPED, "error": str(exc)}
    else:
        _log.debug("Skipping state stream — neither inventory nor pc_condition in active_domains")
        extraction_event["state"] = _SKIPPED

    # --- Stream 3: Progress (always runs — post-narration storytelling brain) ---
    t_progress = asyncio.get_event_loop().time()
    progress_msgs = _extract_progress_messages(
        env, narration, state,
        active_domains=active_domains,
        scene_result=scene_result,
        state_result=state_result,
        rules_outcome=rules_outcome,
        enable_thinking=config.enable_extract_thinking,
        deescalate=deescalate,
        quest_ages=quest_ages,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_prog_system = progress_msgs[0]["content"] if progress_msgs else ""
    rendered_prog_user = progress_msgs[-1]["content"] if progress_msgs else ""
    progress_msgs, prog_trimmed, prog_trimmed_chars = trim_messages(progress_msgs, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_progress", progress_msgs)

    try:
        progress_result, prog_usage, progress_attempts, progress_retry_errors = await _call_stream(
            progress_msgs, config, trace_id, "extract_progress",
            ProgressExtractResult, strip_keys=("_reasoning",),
        )
        extraction_event["progress"] = {
            "rendered_system": rendered_prog_system,
            "rendered_user": rendered_prog_user,
            "output": progress_result.model_dump(),
            "skipped": False,
            "attempts": progress_attempts,
            "retry_errors": progress_retry_errors,
            "tokens_in": prog_usage.get("prompt_tokens", 0),
            "tokens_out": prog_usage.get("total_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_progress) * 1000, 1),
            "context_meta": _context_meta(rendered_prog_system, rendered_prog_user, prog_trimmed, prog_trimmed_chars),
        }
    except Exception as exc:
        _log.warning("extract_progress failed: %s", exc, extra={"trace_id": trace_id})
        extraction_event["progress"] = {**_SKIPPED, "error": str(exc)}

    # --- Merge into single StateDelta ---
    merged = StateDelta(
        scene_tags=scene_result.scene_tags,
        scene_tagline=scene_result.scene_tagline,
        location_change=scene_result.location_change,
        location_description=scene_result.location_description,
        npc_add=scene_result.npc_add,
        npc_remove=scene_result.npc_remove,
        npc_update=scene_result.npc_update,
        inventory_add=state_result.inventory_add,
    inventory_remove=state_result.inventory_remove,
    inventory_update=state_result.inventory_update,
    pc_condition_add=state_result.pc_condition_add,
    pc_condition_remove=state_result.pc_condition_remove,
    quest_updates=progress_result.quest_updates,
    recent_events_add=progress_result.recent_events_add,
    recent_events_update=progress_result.recent_events_update,
    recent_events_remove=progress_result.recent_events_remove,
    compendium_npc_update=progress_result.compendium_npc_update,
    scene_pressure_add=progress_result.scene_pressure_add,
    scene_pressure_remove=progress_result.scene_pressure_remove,
    scene_pressure_update=progress_result.scene_pressure_update,
)

    return (
        merged,
        scene_result.actions,
        scene_result.outcome_summary,
        state_result.failed,
        extraction_event,
        progress_result,
    )


def _avg_narrate_ms(save_dir: Path, n: int = 5) -> int:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return 0
    lines = [ln for ln in path.read_text().strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return 0
    recent = lines[-n:]
    times: list[float] = []
    for line in recent:
        try:
            ev = json.loads(line)
            narr = ev.get("narrate") or {}
            ms = narr.get("total_ms")
            if ms is not None:
                times.append(float(ms))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    if len(times) < 2:
        return 0
    return int(sum(times) / len(times))


def _avg_extract_ms(save_dir: Path, n: int = 5) -> int:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return 0
    lines = [ln for ln in path.read_text().strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return 0
    recent = lines[-n:]
    times: list[float] = []
    for line in recent:
        try:
            ev = json.loads(line)
            ext = ev.get("extract") or {}
            ms = ext.get("total_ms")
            if ms is not None:
                times.append(float(ms))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    if len(times) < 2:
        return 0
    return int(sum(times) / len(times))
