"""Pipeline orchestrator: runs the three extraction streams in sequence."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from jinja2 import Environment

from ccya.engine.config import EngineConfig
from ccya.engine.extraction.context import _build_extraction_context
from ccya.engine.extraction.scene import _extract_scene_messages
from ccya.engine.extraction.state import _extract_state_messages
from ccya.engine.extraction.storytell import _storytell_messages
from ccya.engine.extraction.utils import _call_stream, _capitalize_inventory_names, _context_meta, _dedup_compendium_update
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.errors import ErrorKind, LlmcTimeout
from ccya.llm_client import trim_messages
from ccya.models import (
    CompendiumNpcUpdate,
    IntentEnvelope,
    RulesOutcome,
    SceneExtractResult,
    StateDelta,
    StateExtractResult,
    StorytellerResult,
)

_log = logging.getLogger(__name__)


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
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_scene_system = scene_msgs[0]["content"] if scene_msgs else ""
    rendered_scene_user = scene_msgs[-1]["content"] if scene_msgs else ""
    strip_trace_markers_in_messages(scene_msgs)
    scene_msgs, scene_trimmed, scene_trimmed_chars = trim_messages(scene_msgs, config.context_window)

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

    if state_attempts > 1 and not state_result.inventory_add and not state_result.inventory_remove and not state_result.inventory_update and not state_result.pc_condition_add and not state_result.pc_condition_remove:
        _log.warning("extraction.state.empty trace_id=%s turn_no=%d state has no inventory or condition changes after retries", trace_id, turn_no)
    _log.debug("extraction.state.done trace_id=%s result_type=%s inv_add=%d inv_remove=%d inv_update=%d conds_add=%d conds_remove=%d tokens_in=%d tokens_out=%d", trace_id, type(state_result).__name__, len(state_result.inventory_add or []), len(state_result.inventory_remove or []), len(state_result.inventory_update or []), len(state_result.pc_condition_add or []), len(state_result.pc_condition_remove or []), state_usage.get("prompt_tokens", 0), state_usage.get("completion_tokens", 0))
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
    existing_ids: set[str] = set(_comp.keys())
    compendium_dedup_redirects: list[dict[str, Any]] = []
    for cu in (scene_result.compendium_npc_update or []):
        original_id = cu.id
        deduped = _dedup_compendium_update(cu, existing_npcs, existing_ids)
        if deduped.id != original_id:
            compendium_dedup_redirects.append({
                "original_id": original_id,
                "redirected_to": deduped.id,
                "name": deduped.name,
            })
        deduped_compendium.append(deduped)
    if compendium_dedup_redirects:
        _log.debug(
            "extraction.dedup: compendium dedup redirected %d entries", len(compendium_dedup_redirects),
            extra={"turn": turn_no, "trace_id": trace_id},
        )
        extraction_event["compendium_dedup_redirects"] = compendium_dedup_redirects
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
        condition_change_reason=state_result.condition_change_reason,
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
