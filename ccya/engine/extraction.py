"""Three-stream extraction pipeline: scene, state, storytell."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from jinja2 import Environment
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.narrate import _get_resolved_arcs
from ccya.engine._pacing import derive_allowed_beat_types, derive_enforce_relief
from ccya.prompts.context import _fmt_progress
from ccya.engine.npc_roster import build_npc_roster
from ccya.personality import ARCHETYPES
from ccya.llm_client import (
    chat as llm_chat,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    CompendiumNpcUpdate,
    IntentEnvelope,
    StorytellerResult,
    RulesOutcome,
    SceneExtractResult,
    StateExtractResult,
    StateDelta,
)

from ccya.errors import ErrorKind, LlmcTimeout

_log = logging.getLogger(__name__)


@dataclass
class _ExtractionContext:
    """Carries this-turn deltas from scene + state streams into the storytell stream.

    All fields are derived from extract results, NOT from `state`.  They
    represent what happened *this turn* as determined by the prior two streams.
    """
    comp_this_turn: dict[str, Any] = field(default_factory=dict)
    """Reference to post-delta compendium.npcs dict (not a copy)."""
    location_this_turn: dict[str, Any] = field(default_factory=dict)
    """Location dict after applying location_change from scene result (or state's if no change)."""

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

    Calls apply_delta() on a deep copy of state so the storyteller's
    view of NPCs, inventory, and conditions is guaranteed to match what
    apply_delta() will actually write — including any validation rejections.
    Does NOT mutate ``state``.
    """
    from ccya.state.delta_builder import apply_delta

    combined_delta = StateDelta(
        compendium_npc_update=list(scene_result.compendium_npc_update or []),
        location_change=scene_result.location_change,
        inventory_add=list(state_result.inventory_add or []),
        inventory_remove=list(state_result.inventory_remove or []),
        inventory_update=list(state_result.inventory_update or []),
        pc_condition_add=list(state_result.pc_condition_add or []),
        pc_condition_remove=list(state_result.pc_condition_remove or []),
    )

    state_copy = copy.deepcopy(state)
    post_state = apply_delta(state_copy, combined_delta)

    post_pc = post_state.get("pc") or {}

    location_this_turn = dict(post_state.get("location") or {})
    if scene_result.location_description:
        location_this_turn["description"] = scene_result.location_description

    return _ExtractionContext(
        comp_this_turn=post_state.setdefault("compendium", {}).setdefault("npcs", {}),
        location_this_turn=location_this_turn,
        inventory_this_turn=list(post_state.get("inventory") or []),
        conditions_this_turn=list(post_pc.get("conditions") or []),
    )

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



def _capitalize_inventory_names(items: list[Any]) -> None:
    """Capitalize the first letter of inventory item names in-place.

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


def _dedup_compendium_update(
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
            return proposed.model_copy(update={"id": str(npc["id"])})
    return proposed


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence, location, tags)."""
    location = state.get("location") or {}
    comp = (state.get("compendium") or {}).get("npcs") or {}
    npc_roster = build_npc_roster(comp, personality_registry=ARCHETYPES)

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "location": location,
            "npc_roster": npc_roster,
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
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
    return msgs


def _storytell_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    extraction_ctx: _ExtractionContext,
    intent: IntentEnvelope | None = None,
    pacing_context: Any | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    band: str = "",
    arc_ttl: int = 3,
    config: EngineConfig | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (thread signals + facts + actions + outcome_summary)."""
    scene = state.get("scene") or {}

    arc = state.get("arc") or {}
    _raw_threads = arc.get("threads") or []
    all_threads: list[dict[str, Any]] = []
    for t in _raw_threads:
        if isinstance(t, dict):
            entry: dict[str, Any] = dict(t)
            entry["progress"] = _fmt_progress(entry.get("progress"))
            entry.setdefault("last_updated_turn", t.get("last_updated_turn"))
            all_threads.append(entry)
        else:
            all_threads.append({"id": "", "summary": ""})
    world_state = list(scene.get("world_state") or [])

    system_text = _render(
        env, "storytell_system.j2", {
            "recent_beats": list((state.get("meta") or {}).get("recent_beats", [])),
        }
    )
    npc_roster = build_npc_roster(extraction_ctx.comp_this_turn, personality_registry=ARCHETYPES)
    user_text = _render(
        env,
        "storytell_user.j2",
        {
            "narration": narration,
            # This-turn derived values (from extraction_ctx) — NOT state
            "npc_roster": npc_roster,
            "location": extraction_ctx.location_this_turn,
            "inventory": extraction_ctx.inventory_this_turn,
            "conditions": extraction_ctx.conditions_this_turn,
            # State-sourced (these don't change within a turn)
            "current_arc": arc,
            "all_threads": all_threads,
            "world_state": world_state,
            "resolved_arcs": _get_resolved_arcs(state, turn_no, ttl=arc_ttl),
            "intent": intent,
            "pacing_context": pacing_context,
            "recent_turns": recent_turns or [],
            "prior_history": list((state.get("meta") or {}).get("prior_history", [])[:-1]),
            "pending_beat": (state.get("meta") or {}).get("pending_gm_beat"),
            "recent_beats": list((state.get("meta") or {}).get("recent_beats", [])),
            "turn_no": turn_no,
            "band": band,
            "scene_phase": scene.get("scene_phase", "SETUP"),
            "allowed_beat_types": derive_allowed_beat_types(
                scene.get("scene_phase", "SETUP"),
                enforce_relief=derive_enforce_relief(
                    scene.get("scene_phase", "SETUP"),
                    state.get("meta", {}).get("consecutive_pressure_beats", 0),
                    config or EngineConfig(),
                ),
            ),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return msgs


def _coerce_scene_json(j: dict[str, Any]) -> dict[str, Any]:
    """Coerce LLM output to match Pydantic model expectations.

    Handles cases where the LLM returns strings instead of dicts for list fields:
    - compendium_npc_update: ["bystanders"] → [{"id": "bystanders"}]
    """
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

    # Coerce malformed thread_add (LLM returns [] or {} when no new thread)
    if isinstance(j.get("thread_add"), list):
        del j["thread_add"]
    elif isinstance(j.get("thread_add"), dict):
        required = {"id", "summary"}
        if not required.issubset(j["thread_add"].keys()):
            del j["thread_add"]

    return j


def _parse_stream_result(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    # Coerce LLM output to match Pydantic model expectations
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
    for attempt in range(1 + config.max_llm_retries):
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
            top_p=config.extract_top_p,
            frequency_penalty=config.extract_frequency_penalty,
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
                1 + config.max_llm_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
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
) -> "AsyncIterator[tuple[str, Any] | tuple['StateDelta', list[str], str, dict[str, Any], 'StorytellerResult', 'SceneExtractResult']]":
    _log.debug("extraction.pipeline.start trace_id=%s turn_no=%d", trace_id, turn_no)
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, per_stream_event_data, storyteller_result, scene_result)
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
    storytell_result = StorytellerResult()
    extraction_event: dict[str, Any] = {}

    # --- Stream 1: Scene ---
    yield ("phase", {"phase": "extract_stream_start", "stream": "scene"})
    t_scene = asyncio.get_event_loop().time()
    scene_msgs = _extract_scene_messages(
        env, narration, state,
        recent_turns=(recent_turns or [])[-1:],
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_scene_system = scene_msgs[0]["content"] if scene_msgs else ""
    rendered_scene_user = scene_msgs[-1]["content"] if scene_msgs else ""
    strip_trace_markers_in_messages(scene_msgs)
    scene_msgs, scene_trimmed, scene_trimmed_chars = trim_messages(scene_msgs, config.context_window)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_scene", scene_msgs)

    scene_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    try:
        scene_result, scene_usage, scene_attempts, scene_retry_errors = await _call_stream(
            scene_msgs, config, trace_id, "extract_scene", SceneExtractResult
        )
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

    _log.debug("extraction.scene.done trace_id=%s result_type=%s tokens_in=%d tokens_out=%d", trace_id, type(scene_result).__name__, scene_usage.get("prompt_tokens", 0), scene_usage.get("completion_tokens", 0))
    yield ("phase", {"phase": "extract_stream_done", "stream": "scene"})

    # --- Stream 2: State ---
    yield ("phase", {"phase": "extract_stream_start", "stream": "state"})
    t_state = asyncio.get_event_loop().time()
    state_msgs = _extract_state_messages(
        env, narration, state,
        intent=intent,
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_state_system = state_msgs[0]["content"] if state_msgs else ""
    rendered_state_user = state_msgs[-1]["content"] if state_msgs else ""
    strip_trace_markers_in_messages(state_msgs)
    state_msgs, state_trimmed, state_trimmed_chars = trim_messages(state_msgs, config.context_window)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_state", state_msgs)

    state_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
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

    if not state_result.inventory_add and not state_result.pc_condition_add:
        _log.warning("extraction.state.empty trace_id=%s turn_no=%d state has no inventory or condition changes after retries", trace_id, turn_no)
    _log.debug("extraction.state.done trace_id=%s result_type=%s inv_add=%d conds_add=%d tokens_in=%d tokens_out=%d", trace_id, type(state_result).__name__, len(state_result.inventory_add or []), len(state_result.pc_condition_add or []), state_usage.get("prompt_tokens", 0), state_usage.get("completion_tokens", 0))
    yield ("phase", {"phase": "extract_stream_done", "stream": "state"})

    # --- Stream 3: Storytell (always runs — post-narration storytelling brain) ---
    yield ("phase", {"phase": "extract_stream_start", "stream": "storytell"})
    t_storytell = asyncio.get_event_loop().time()
    _band = (rules_outcome.band if rules_outcome and rules_outcome.rolled else "")
    # Build this-turn context from scene + state results for the storyteller stream
    extraction_ctx = _build_extraction_context(state, scene_result, state_result)
    storytell_msgs = _storytell_messages(
        env, narration, state,
        extraction_ctx=extraction_ctx,
        intent=intent,
        pacing_context=pacing_context,
        recent_turns=(recent_turns or [])[-10:],
        turn_no=turn_no,
        band=_band,
        arc_ttl=config.arc_memory_ttl,
        config=config,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_storytell_system = storytell_msgs[0]["content"] if storytell_msgs else ""
    rendered_storytell_user = storytell_msgs[-1]["content"] if storytell_msgs else ""
    strip_trace_markers_in_messages(storytell_msgs)
    storytell_msgs, storytell_trimmed, storytell_trimmed_chars = trim_messages(storytell_msgs, config.context_window)
    if config.log_prompts:
        _log_prompts(turn_no, "storytell", storytell_msgs)

    storytell_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    try:
        storytell_result, storytell_usage, storytell_attempts, storytell_retry_errors = await _call_stream(
            storytell_msgs, config, trace_id, "storytell",
            StorytellerResult, strip_keys=("_reasoning",),
        )

        # Generate fallback actions when LLM omits them (prompt requires exactly 4)
        if not storytell_result.actions:
            narr_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', narration.strip()) if len(s.strip().split()) > 5]
            present_npc_names = [entry.get("name", "") for entry in extraction_ctx.comp_this_turn.values() if isinstance(entry, dict) and entry.get("presence") == "present"]
            inventory_items = [item.get("name", item.get("id", "")) if isinstance(item, dict) else str(item) for item in (state.get("inventory") or [])]
            arc_goal = (state.get("arc") or {}).get("visible_goal", "")

            actions = []
            # Action from narration summary
            if narr_sentences:
                actions.append(f"Continue {narr_sentences[0].lower().strip()[:80]}")
            else:
                actions.append("Take a careful look around the area.")
            # NPC interaction action
            if present_npc_names:
                npc = present_npc_names[0]
                actions.append(f"Speak with {npc} about what just happened.")
            else:
                actions.append("Survey your surroundings for useful information.")
            # Inventory-based action
            if inventory_items:
                item = inventory_items[0]
                actions.append(f"Check your {item} for anything useful.")
            else:
                actions.append("Pat down your gear for anything you might have missed.")
            # Arc goal action
            if arc_goal:
                actions.append(f"Focus on {arc_goal[:60]} to advance your goal.")
            else:
                actions.append("Decide what matters most and pursue it.")
            storytell_result = storytell_result.model_copy(update={"actions": actions})
        extraction_event["storytell"] = {
            "rendered_system": rendered_storytell_system,
            "rendered_user": rendered_storytell_user,
                "output": storytell_result.model_dump(exclude_none=True),
            "skipped": False,
            "attempts": storytell_attempts,
            "retry_errors": storytell_retry_errors,
            "tokens_in": storytell_usage.get("prompt_tokens", 0),
            "tokens_out": storytell_usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_storytell) * 1000, 1),
            "context_meta": _context_meta(rendered_storytell_system, rendered_storytell_user, storytell_trimmed, storytell_trimmed_chars),
        }
    except LlmcTimeout as exc:
        _log.warning("storytell LLM timeout", extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id})
        extraction_event["storytell"] = {**_SKIPPED, "error": str(exc)}
    except Exception as exc:
        _log.warning(
            "storytell failed: %s", exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        extraction_event["storytell"] = {**_SKIPPED, "error": str(exc)}

    if not storytell_result.actions:
        _log.warning("extraction.storytell.empty trace_id=%s turn_no=%d storytell has no actions after retries", trace_id, turn_no)
    _log.debug("extraction.storytell.done trace_id=%s result_type=%s actions=%d tokens_in=%d tokens_out=%d gm_beat=%s", trace_id, type(storytell_result).__name__, len(storytell_result.actions or []), storytell_usage.get("prompt_tokens", 0), storytell_usage.get("completion_tokens", 0), storytell_result.gm_beat.type if storytell_result.gm_beat else None)
    yield ("phase", {"phase": "extract_stream_done", "stream": "storytell"})

    _log.debug("extraction.dedup.start trace_id=%s compendium_updates=%d state_inv_add=%d", trace_id, len(scene_result.compendium_npc_update or []), len(state_result.inventory_add or []))
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
        deduped_compendium.append(_dedup_compendium_update(cu, existing_npcs))
    if deduped_compendium != (scene_result.compendium_npc_update or []):
        _log.debug(
            "extraction.dedup: compendium dedup redirected %d entries", len(scene_result.compendium_npc_update or []),
            extra={"turn": turn_no, "trace_id": trace_id},
        )
    scene_result = scene_result.model_copy(update={"compendium_npc_update": deduped_compendium})

    # --- Capitalize inventory item names ---
    _capitalize_inventory_names(state_result.inventory_add)
    _capitalize_inventory_names(state_result.inventory_update)

    _log.debug(
        "extraction.merge.start trace_id=%s inv_add=%d", trace_id, len(state_result.inventory_add or [])
    )
    # --- Merge into single StateDelta ---
    merged = StateDelta(
        inventory_change_reason=state_result.inventory_change_reason,
        scene_tagline=scene_result.scene_tagline,
        location_change=scene_result.location_change,
        location_description=scene_result.location_description,
        compendium_npc_update=scene_result.compendium_npc_update,
        inventory_add=state_result.inventory_add,
        inventory_remove=state_result.inventory_remove,
        inventory_update=state_result.inventory_update,
        pc_condition_add=state_result.pc_condition_add,
        pc_condition_remove=state_result.pc_condition_remove,
        actions=storytell_result.actions or [],
    )

    # NOTE: gm_beat is intentionally absent from StateDelta — it is written
    # directly to state["meta"]["pending_gm_beat"] in turn.py Step 2.5.
    # Do NOT add gm_beat to the merge block.

    # mypy cannot express heterogeneous 7-tuple yield from async generator
    yield (  # type: ignore[misc]
        merged,
        storytell_result.actions,
        storytell_result.outcome_summary,
        extraction_event,
        storytell_result,
        scene_result,
        extraction_ctx,
    )
    _log.debug("extraction.pipeline.done trace_id=%s turn_no=%d", trace_id, turn_no)


def _avg_event_ms(save_dir: Path, field_path: str, n: int = 5) -> int:
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
            parts = field_path.split(".")
            val: Any = ev
            for p in parts:
                val = (val or {}).get(p) if isinstance(val, dict) else None
            if val is not None:
                times.append(float(val))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    if len(times) < 2:
        return 0
    return int(sum(times) / len(times))
