"""Three-stream extraction pipeline: scene, state, progress."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from jinja2 import Environment
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.narrate import _known_characters_for_extract
from ccya.engine.npc_roster import build_npc_roster
from ccya.llm_client import (
    apply_thinking,
    chat as llm_chat,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    CompendiumNpcUpdate,
    IntentEnvelope,
    ProgressExtractResult,
    RulesOutcome,
    SceneExtractResult,
    StateExtractResult,
    StateDelta,
)

from ccya.errors import ErrorKind, LlmcTimeout

_log = logging.getLogger(__name__)


@dataclass
class _ExtractionContext:
    """Carries this-turn deltas from scene + state streams into the progress stream.

    All fields are derived from extract results, NOT from `state`.  They
    represent what happened *this turn* as determined by the prior two streams.
    """
    # Scene stream outputs (stream 1)
    present_npcs_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """present_npcs list after applying npc_add/npc_remove from scene result."""
    location_this_turn: dict[str, Any] = field(default_factory=dict)
    """Location dict after applying location_change from scene result (or state's if no change)."""
    scene_tags_this_turn: list[str] = field(default_factory=list)
    """scene.tags after scene stream."""

    # State stream outputs (stream 2)
    inventory_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """inventory list after applying inventory_add/remove/update from state result."""
    conditions_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """pc.conditions after applying pc_condition_add/remove from state result."""


def _build_extraction_context(
    state: dict[str, Any],
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
) -> _ExtractionContext:
    """Compute this-turn derived context from the two upstream extraction results.

    Calls apply_delta() on a deep copy of state so the progress extractor's
    view of NPCs, inventory, and conditions is guaranteed to match what
    apply_delta() will actually write — including any validation rejections.
    Does NOT mutate ``state``.
    """
    from ccya.state.delta import apply_delta  # local import to avoid circular deps

    combined_delta = StateDelta(
        npc_add=list(scene_result.npc_add or []),
        npc_remove=list(scene_result.npc_remove or []),
        npc_update=list(scene_result.npc_update or []),
        compendium_npc_update=list(scene_result.compendium_npc_update or []),
        location_change=scene_result.location_change,
        scene_tags=list(scene_result.scene_tags or []),
        inventory_add=list(state_result.inventory_add or []),
        inventory_remove=list(state_result.inventory_remove or []),
        inventory_update=list(state_result.inventory_update or []),
        pc_condition_add=list(state_result.pc_condition_add or []),
        pc_condition_remove=list(state_result.pc_condition_remove or []),
    )

    state_copy = copy.deepcopy(state)
    post_state, _evicted = apply_delta(state_copy, combined_delta)

    post_scene = post_state.get("scene") or {}
    post_pc = post_state.get("pc") or {}

    location_this_turn = dict(post_state.get("location") or {})
    if scene_result.location_description:
        location_this_turn["description"] = scene_result.location_description

    return _ExtractionContext(
        present_npcs_this_turn=list(post_scene.get("present_npcs") or []),
        location_this_turn=location_this_turn,
        scene_tags_this_turn=list(post_scene.get("tags") or []),
        inventory_this_turn=list(post_state.get("inventory") or []),
        conditions_this_turn=list(post_pc.get("conditions") or []),
    )


def _check_npc_ghost_cycle(
    scene_result: SceneExtractResult,
    state: dict[str, Any],
    *,
    trace_id: str,
    turn_no: int,
) -> SceneExtractResult:
    remove_ids = {op.id for op in (scene_result.npc_remove or [])}
    add_ids = {op.id for op in (scene_result.npc_add or [])}
    cycle_ids = remove_ids & add_ids
    recently_left = {
        entry.get("id", "")
        for entry in (state.get("scene") or {}).get("recently_left") or []
        if isinstance(entry, dict)
    }
    if cycle_ids:
        # Allow removes that match recently_left (legitimate departure)
        allowed = cycle_ids & recently_left
        dropped = cycle_ids - allowed
        if dropped:
            _log.warning(
                "npc_remove/npc_add cycle detected — dropping both ops for IDs",
                extra={"trace_id": trace_id, "turn": turn_no, "ids": list(dropped)},
            )
            scene_result = scene_result.model_copy(
                update={
                    "npc_remove": [op for op in (scene_result.npc_remove or []) if op.id not in dropped],
                    "npc_add": [op for op in (scene_result.npc_add or []) if op.id not in dropped],
                }
            )
    return scene_result


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


def _capitalize_inventory_names(items: list[Any]) -> list[Any]:
    """Capitalize the first letter of inventory item names.

    Modifies items in place and returns them.
    Handles both Pydantic model instances and dicts.
    """
    for item in items:
        if hasattr(item, "name"):
            name = item.name
            if name and name[0].islower():
                item.name = name[0].upper() + name[1:]
        elif isinstance(item, dict) and "name" in item:
            name = item["name"]
            if name and name[0].islower():
                item["name"] = name[0].upper() + name[1:]
    return items


def _dedup_compendium_add(
    proposed: "CompendiumNpcUpdate",
    existing_npcs: list[dict[str, Any]],
) -> "CompendiumNpcUpdate":
    """
    If proposed.name matches any existing NPC's name or aliases (case-insensitive),
    redirect proposed.id to the existing NPC's id and return the modified update.
    Otherwise return proposed unchanged.
    """
    if not proposed.name:
        return proposed
    candidate = proposed.name.strip().lower()
    for npc in existing_npcs:
        npc_names = [
            (npc.get("name") or "").lower(),
            (npc.get("id") or "").lower().replace("_", " "),
        ] + [(a or "").lower() for a in (npc.get("aliases") or [])]
        if candidate in npc_names:
            return proposed.model_copy(update={"id": str(npc["id"])})  # type: ignore[no-any-return]
    return proposed


def _scene_npc_roster(known_characters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a deduped NPC roster for the scene extractor user prompt.

    Each row is ``{id, name, title, bio, notes, tags, motivation, fear, leverage}``
    where tags = {"compendium"}.
    """
    by_id: dict[str, dict[str, Any]] = {}

    def _put(nid: str, name: str, title: str, bio: str, notes: str, tag: str, motivation: str = "", fear: str = "", leverage: str = "") -> None:
        if not nid:
            return
        row = by_id.setdefault(nid, {"id": nid, "name": "", "title": "", "bio": "", "notes": "", "tags": [], "motivation": "", "fear": "", "leverage": ""})
        if name and not row["name"]:
            row["name"] = name
        if title and not row["title"]:
            row["title"] = title
        if bio and not row["bio"]:
            row["bio"] = bio
        if notes and not row["notes"]:
            row["notes"] = notes
        if tag not in row["tags"]:
            row["tags"].append(tag)
        if motivation and not row["motivation"]:
            row["motivation"] = motivation
        if fear and not row["fear"]:
            row["fear"] = fear
        if leverage and not row["leverage"]:
            row["leverage"] = leverage

    for row in known_characters or []:
        _put(
            str(row.get("id") or ""),
            str(row.get("name") or ""),
            str(row.get("title") or ""),
            str(row.get("bio") or ""),
            "",
            "compendium",
            row.get("motivation") or "",
            row.get("fear") or "",
            row.get("leverage") or "",
        )

    return list(by_id.values())


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    enable_thinking: bool = False,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence, location, tags)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=False)
    npc_roster = _scene_npc_roster(known_characters)
    _raw_present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
    _compendium = (state.get("compendium") or {}).get("npcs") or {}
    present_npcs = []
    for npc in _raw_present_npcs:
        nid = npc.get("id", "")
        entry = _compendium.get(nid, {})
        enriched = dict(npc)
        if not enriched.get("name") and entry.get("name"):
            enriched["name"] = entry["name"]
        if not enriched.get("title") and entry.get("title"):
            enriched["title"] = entry["title"]
        if not enriched.get("bio") and entry.get("bio"):
            enriched["bio"] = (entry.get("bio") or "").strip()
        present_npcs.append(enriched)

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
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions)."""
    pc = state.get("pc") or {}

    system_text = _render(env, "extract_state_system.j2", {})
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "intent": intent,
            "turn_no": turn_no,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs


def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    state_result: "StateExtractResult",
    extraction_ctx: "_ExtractionContext",
    enable_thinking: bool = False,
        intent: "IntentEnvelope | None" = None,
        pacing_context: Any | None = None,
        recent_turns: list[dict[str, Any]] | None = None,
        turn_no: int = 0,
    band: str = "",
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (thread signals + facts + actions + outcome_summary)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}

    arc = state.get("arc") or {}
    all_threads = [t for t in (arc.get("threads") or []) if isinstance(t, dict)]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])

    system_text = _render(env, "extract_progress_system.j2", {})
    pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
    npc_roster = build_npc_roster(
        present_npcs=extraction_ctx.present_npcs_this_turn,
        known_npcs=_known_characters_for_extract(state, compact=True),
        recently_left=[],
    )
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "pc_stats": pc.get("stats") or {},
            # This-turn derived values (from extraction_ctx) — NOT state
            "npc_roster": npc_roster,
            "location": extraction_ctx.location_this_turn,
            "inventory": extraction_ctx.inventory_this_turn,
            "conditions": extraction_ctx.conditions_this_turn,
            # State-sourced (these don't change within a turn)
            "all_threads": all_threads,
            "recent_events": recent_events,
            "world_state": world_state,
            "intent": intent,
            "pacing_context": pacing_context,
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
            "band": band,
            "pending_beat": pending_beat,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs


def _coerce_scene_json(j: dict[str, Any]) -> dict[str, Any]:
    """Coerce LLM output to match Pydantic model expectations.

    Handles cases where the LLM returns strings instead of dicts for list fields:
    - npc_add: ["bystanders"] → [{"id": "bystanders", "notes": "", "bio": ""}]
    - compendium_npc_update: similar coercion needed
    """
    # Coerce npc_add entries that are strings to NpcAdd objects
    if isinstance(j.get("npc_add"), list):
        coerced = []
        for item in j["npc_add"]:
            if isinstance(item, str):
                coerced.append({"id": item.lower().replace(" ", "_").strip(), "notes": "", "bio": ""})
            elif isinstance(item, dict) and "id" not in item:
                # Dict without id — extract name/title to create id
                name = item.get("name", "") or str(item).lower()
                coerced.append({"id": name.replace(" ", "_").strip(), **item})
            else:
                coerced.append(item)
        j["npc_add"] = coerced

    # Coerce compendium_npc_update entries that are strings to dicts
    if isinstance(j.get("compendium_npc_update"), list):
        coerced = []
        for item in j["compendium_npc_update"]:
            if isinstance(item, str):
                coerced.append({"id": item.lower().replace(" ", "_").strip()})
            elif isinstance(item, dict) and "id" not in item:
                name = item.get("name", "") or str(item).lower()
                coerced.append({"id": name.replace(" ", "_").strip(), **item})
            else:
                coerced.append(item)
        j["compendium_npc_update"] = coerced

    return j


def _parse_stream_result(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    # Coerce LLM output to match Pydantic model expectations (e.g., string → dict for npc_add)
    return model_cls(**_coerce_scene_json(j))


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
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    pacing_context: Any | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> "AsyncIterator[tuple[str, Any] | tuple['StateDelta', list[str], str, dict[str, Any], 'ProgressExtractResult', 'SceneExtractResult']]":
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, per_stream_event_data, progress_result, scene_result)
    """

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
    yield ("phase", {"phase": "extract_stream_start", "stream": "scene"})
    t_scene = asyncio.get_event_loop().time()
    scene_msgs = _extract_scene_messages(
        env, narration, state,
        enable_thinking=config.enable_extract_thinking,
        recent_turns=(recent_turns or [])[-1:],
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_scene_system = scene_msgs[0]["content"] if scene_msgs else ""
    rendered_scene_user = scene_msgs[-1]["content"] if scene_msgs else ""
    strip_trace_markers_in_messages(scene_msgs)
    scene_msgs, scene_trimmed, scene_trimmed_chars = trim_messages(scene_msgs, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_scene", scene_msgs)

    try:
        scene_result, scene_usage, scene_attempts, scene_retry_errors = await _call_stream(
            scene_msgs, config, trace_id, "extract_scene", SceneExtractResult
        )
        scene_result = _check_npc_ghost_cycle(scene_result, state, trace_id=trace_id, turn_no=turn_no)
        extraction_event["scene"] = {
            "rendered_system": rendered_scene_system,
            "rendered_user": rendered_scene_user,
            "output": scene_result.model_dump(exclude_none=True),
            "skipped": False,
            "attempts": scene_attempts,
            "retry_errors": scene_retry_errors,
            "tokens_in": scene_usage.get("prompt_tokens", 0),
            "tokens_out": scene_usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_scene) * 1000, 1),
            "context_meta": _context_meta(rendered_scene_system, rendered_scene_user, scene_trimmed, scene_trimmed_chars),
        }
    except LlmcTimeout as exc:
        _log.warning("extract_scene LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id})
        extraction_event["scene"] = {**_SKIPPED, "error": str(exc)}
    except Exception as exc:
        _log.warning(
            "extract_scene failed: %s", exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        extraction_event["scene"] = {**_SKIPPED, "error": str(exc)}

    yield ("phase", {"phase": "extract_stream_done", "stream": "scene"})

    # --- Stream 2: State ---
    yield ("phase", {"phase": "extract_stream_start", "stream": "state"})
    t_state = asyncio.get_event_loop().time()
    state_msgs = _extract_state_messages(
        env, narration, state,
        enable_thinking=config.enable_extract_thinking,
        intent=intent,
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_state_system = state_msgs[0]["content"] if state_msgs else ""
    rendered_state_user = state_msgs[-1]["content"] if state_msgs else ""
    strip_trace_markers_in_messages(state_msgs)
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
            "output": state_result.model_dump(exclude_none=True),
            "skipped": False,
            "attempts": state_attempts,
            "retry_errors": state_retry_errors,
            "tokens_in": state_usage.get("prompt_tokens", 0),
            "tokens_out": state_usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_state) * 1000, 1),
            "context_meta": _context_meta(rendered_state_system, rendered_state_user, state_trimmed, state_trimmed_chars),
        }
    except LlmcTimeout as exc:
        _log.warning("extract_state LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id})
        extraction_event["state"] = {**_SKIPPED, "error": str(exc)}
    except Exception as exc:
        _log.warning(
            "extract_state failed: %s", exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        extraction_event["state"] = {**_SKIPPED, "error": str(exc)}

    yield ("phase", {"phase": "extract_stream_done", "stream": "state"})

    # --- Stream 3: Progress (always runs — post-narration storytelling brain) ---
    yield ("phase", {"phase": "extract_stream_start", "stream": "progress"})
    t_progress = asyncio.get_event_loop().time()
    _band = (rules_outcome.band if rules_outcome and rules_outcome.rolled else "")
    # Build this-turn context from scene + state results for the progress stream
    extraction_ctx = _build_extraction_context(state, scene_result, state_result)
    progress_msgs = _extract_progress_messages(
        env, narration, state,
        state_result=state_result,
        extraction_ctx=extraction_ctx,
        enable_thinking=config.enable_extract_thinking,
        intent=intent,
        pacing_context=pacing_context,
        recent_turns=(recent_turns or [])[-2:],
        turn_no=turn_no,
        band=_band,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_prog_system = progress_msgs[0]["content"] if progress_msgs else ""
    rendered_prog_user = progress_msgs[-1]["content"] if progress_msgs else ""
    strip_trace_markers_in_messages(progress_msgs)
    progress_msgs, prog_trimmed, prog_trimmed_chars = trim_messages(progress_msgs, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_progress", progress_msgs)

    try:
        progress_result, prog_usage, progress_attempts, progress_retry_errors = await _call_stream(
            progress_msgs, config, trace_id, "extract_progress",
            ProgressExtractResult, strip_keys=("_reasoning",),
        )
        # Overwrite turn stamp on any newly added events — the LLM cannot know the
        # current turn number reliably; the engine stamps it authoritatively.
        if progress_result.recent_events_add:
            progress_result = progress_result.model_copy(
                update={
                    "recent_events_add": [
                        e.model_copy(update={"turn": turn_no})
                        for e in progress_result.recent_events_add
                    ]
                }
            )
        extraction_event["progress"] = {
            "rendered_system": rendered_prog_system,
            "rendered_user": rendered_prog_user,
                "output": progress_result.model_dump(exclude_none=True),
            "skipped": False,
            "attempts": progress_attempts,
            "retry_errors": progress_retry_errors,
            "tokens_in": prog_usage.get("prompt_tokens", 0),
            "tokens_out": prog_usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_progress) * 1000, 1),
            "context_meta": _context_meta(rendered_prog_system, rendered_prog_user, prog_trimmed, prog_trimmed_chars),
        }
    except LlmcTimeout as exc:
        _log.warning("extract_progress LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id})
        extraction_event["progress"] = {**_SKIPPED, "error": str(exc)}
    except Exception as exc:
        _log.warning(
            "extract_progress failed: %s", exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        extraction_event["progress"] = {**_SKIPPED, "error": str(exc)}

    yield ("phase", {"phase": "extract_stream_done", "stream": "progress"})

    # --- Dedup compendium updates before merging into StateDelta ---
    _comp = (state.get("compendium") or {}).get("npcs") or {}
    existing_npcs: list[dict[str, Any]] = []
    for nid, npc in _comp.items():
        if not isinstance(npc, dict):
            continue
        existing_npcs.append({
            "id": nid,
            "name": npc.get("name") or "",
            "title": npc.get("title") or "",
            "bio_preview": (npc.get("bio") or "").strip()[:120],
            "aliases": list(npc.get("aliases") or []),
        })
    deduped_compendium: list[CompendiumNpcUpdate] = []
    for cu in (scene_result.compendium_npc_update or []):
        deduped_compendium.append(_dedup_compendium_add(cu, existing_npcs))
    if deduped_compendium != (scene_result.compendium_npc_update or []):
        _log.debug(
            "extraction.dedup: compendium dedup redirected %d entries",
            len(scene_result.compendium_npc_update or []),
            extra={"turn": turn_no, "trace_id": trace_id},
        )
    scene_result = scene_result.model_copy(update={"compendium_npc_update": deduped_compendium})

    # --- Dedup npc_add against compendium ---
    if existing_npcs:
        deduped_adds: list[Any] = []
        for npc in (scene_result.npc_add or []):
            npc_name = getattr(npc, "name", None) if hasattr(npc, "name") else npc.get("name", "") if isinstance(npc, dict) else ""
            if npc_name:
                candidate = npc_name.strip().lower()
                for existing in existing_npcs:
                    existing_names = [
                        (existing.get("name") or "").lower(),
                        (existing.get("id") or "").lower().replace("_", " "),
                    ] + [(a or "").lower() for a in (existing.get("aliases") or [])]
                    if candidate in existing_names:
                        _log.debug(
                            "extraction.dedup: npc_add %r matches compendium %r, redirecting to update",
                            npc_name,
                            existing.get("id"),
                            extra={"turn": turn_no, "trace_id": trace_id},
                        )
                        notes = getattr(npc, "notes", None) if hasattr(npc, "notes") else npc.get("notes", "") if isinstance(npc, dict) else ""
                        if notes:
                            scene_result = scene_result.model_copy(
                                update={
                                    "npc_update": (scene_result.npc_update or []) + [
                                        {"id": str(existing["id"]), "notes": notes}
                                    ]
                                }
                            )
                        break
                else:
                    deduped_adds.append(npc)
                continue
            deduped_adds.append(npc)
        scene_result = scene_result.model_copy(update={"npc_add": deduped_adds})

    # --- Capitalize inventory item names ---
    _capitalize_inventory_names(state_result.inventory_add)
    _capitalize_inventory_names(state_result.inventory_update)

    for op in (scene_result.npc_remove or []):
        _log.debug(
            "npc_remove emitted",
            extra={"trace_id": trace_id, "turn": turn_no, "npc_id": op.id},
        )

    # --- Merge into single StateDelta ---
    merged = StateDelta(
        scene_tags=scene_result.scene_tags,
        scene_tagline=scene_result.scene_tagline,
        location_change=scene_result.location_change,
        location_description=scene_result.location_description,
        npc_add=scene_result.npc_add,
        npc_remove=scene_result.npc_remove,
        npc_update=scene_result.npc_update,
        compendium_npc_update=scene_result.compendium_npc_update,
        inventory_add=state_result.inventory_add,
        inventory_remove=state_result.inventory_remove,
        inventory_update=state_result.inventory_update,
        pc_condition_add=state_result.pc_condition_add,
        pc_condition_remove=state_result.pc_condition_remove,
        recent_events_add=progress_result.recent_events_add,
        recent_events_update=progress_result.recent_events_update,
        recent_events_remove=progress_result.recent_events_remove,
    )

    # NOTE: gm_beat is intentionally absent from StateDelta — it is written
    # directly to state["meta"]["pending_gm_beat"] in turn.py Step 2.5.
    # Do NOT add gm_beat to the merge block.

    yield (  # type: ignore[misc]
        merged,
        progress_result.actions,
        progress_result.outcome_summary,
        extraction_event,
        progress_result,
        scene_result,
        extraction_ctx,
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
