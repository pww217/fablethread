"""Pipeline orchestrator: runs the three extraction streams in sequence."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment

from ccya.engine.config import EngineConfig
from ccya.engine.extraction.context import _PostDeltaContext, _build_post_delta_context
from ccya.engine.extraction.scene import _extract_scene_messages
from ccya.engine.extraction.state import _extract_state_messages
from ccya.engine.extraction.record import _record_messages
from ccya.engine.extraction.utils import _avg_event_ms, _call_stream, _capitalize_inventory_names, _context_meta, _dedup_compendium_update
from ccya.errors import ErrorKind, LlmcTimeout
from ccya.llm_client import trim_messages
from ccya.models import (
    CompendiumNpcUpdate,
    IntentEnvelope,
    SceneExtractResult,
    StateMerge,
    StateExtractResult,
    RecordResult,
    WorldState,
)

_log = logging.getLogger(__name__)


def _apply_delta_lazy(s: WorldState, merge: StateMerge, trace_id: str) -> WorldState:
    """Lazy import wrapper to avoid circular import between ccya.engine.extraction and ccya.state."""
    from ccya.state import apply_delta
    return apply_delta(s, merge, trace_id=trace_id)


@dataclass
class _ExtractionAccumulator:
    scene_result: tuple[Any, dict[str, Any]] | None = None
    state_result: tuple[Any, dict[str, Any]] | None = None
    record_result: tuple[Any, dict[str, Any]] | None = None
    extraction_ctx: _PostDeltaContext | None = None


@dataclass
class _ExtractionStreamConfig:
    name: str
    result_type: type
    build_messages: Callable[..., list[dict[str, str]]]
    build_messages_kwargs: dict[str, Any]
    strip_keys: tuple[str, ...]
    preview_builder: Callable[[WorldState, Any], WorldState]
    panel_builder: Callable[[WorldState], dict[str, Any]]
    fatal: bool = False
    call_name: str | None = None


async def _run_extraction_stream(
    state: WorldState,
    variant: _ExtractionStreamConfig,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
    container: _ExtractionAccumulator,
    save_dir: Path = Path("."),
) -> AsyncIterator[tuple[str, Any]]:
    yield ("phase", {"phase": "extract_stream_start", "stream": variant.name})
    t_stream = asyncio.get_event_loop().time()
    msgs = variant.build_messages(state, **variant.build_messages_kwargs)
    rendered_system = msgs[0]["content"] if msgs else ""
    rendered_user = msgs[-1]["content"] if msgs else ""
    msgs, trimmed, trimmed_chars = trim_messages(msgs, config.context_window)

    usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    try:
        result, usage, attempts, retry_errors = await _call_stream(
            msgs, config, trace_id, variant.call_name or variant.name, variant.result_type, strip_keys=variant.strip_keys,
        )
        extraction_event = {
            "output": result.model_dump(exclude_unset=True),
            "skipped": False,
            "attempts": attempts,
            "retry_errors": retry_errors,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_stream) * 1000, 1),
            "context_meta": _context_meta(rendered_system, rendered_user, trimmed, trimmed_chars),
        }
    except LlmcTimeout as exc:
        _log.warning(
            "%s LLM timeout", variant.name, extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
        )
        extraction_event = {**{"skipped": True, "tokens_in": 0, "tokens_out": 0, "ms": 0, "attempts": 0, "retry_errors": []}, "error": str(exc)}
        result = variant.result_type()
    except Exception as exc:
        if variant.fatal:
            _log.error(
                "%s failed (FATAL): %s", variant.name, exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
            )
            raise
        _log.warning(
            "%s failed: %s", variant.name, exc, extra={"error_kind": ErrorKind.TURN_PROCESSING_FAILED, "trace_id": trace_id},
        )
        extraction_event = {**{"skipped": True, "tokens_in": 0, "tokens_out": 0, "ms": 0, "attempts": 0, "retry_errors": []}, "error": str(exc)}
        result = variant.result_type()

    _log.debug(
        "extraction.%s.done trace_id=%s result_type=%s tokens_in=%d tokens_out=%d",
        variant.name, trace_id, type(result).__name__,
        usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
    )
    exp_ms = _avg_event_ms(save_dir, f"{variant.name}.total_ms")
    yield ("phase", {"phase": "extract_stream_done", "stream": variant.name, "expected_ms": exp_ms})

    _preview = state.model_copy()
    if not extraction_event.get("skipped", True):
        _preview = variant.preview_builder(state, result)

    _panel_data = variant.panel_builder(_preview)
    yield ("panel_update", {
        "panel": variant.name,
        "data": _panel_data,
    })

    if variant.name == "scene":
        yield ("panel_update", {
            "panel": "compendium",
            "data": {"npcs": {nid: entry.model_dump() for nid, entry in state.compendium.npcs.items()}},
        })
        container.scene_result = (result, extraction_event)
    elif variant.name == "state":
        container.state_result = (result, extraction_event)
    elif variant.name == "record":
        container.record_result = (result, extraction_event)
    return


async def _run_extraction_pipeline(
    env: "Environment",
    state: WorldState,
    narration: str,
    *,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    band: str = "",
    recent_turns: list[dict[str, Any]] | None = None,
    packing: dict[str, Any] | None = None,
    save_dir: Path = Path("."),
) -> "AsyncIterator[tuple[str, Any] | tuple['StateMerge', list[str], str, dict[str, Any], 'RecordResult', 'SceneExtractResult', '_PostDeltaContext']]":
    _log.debug("extraction.pipeline.start trace_id=%s turn_no=%d", trace_id, turn_no)
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, per_stream_event_data, record_result, scene_result, extraction_ctx)
    `band` is extracted from `rules_outcome` at the call site and passed directly.
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
    record_result = RecordResult()
    extraction_event: dict[str, Any] = {}
    container = _ExtractionAccumulator()

    # --- Stream 1: Scene ---
    async for event in _scene_stream(state, env, narration, turn_no, config, trace_id, container, save_dir):
        yield event
    scene_result, extraction_event["scene"] = container.scene_result if container.scene_result else (SceneExtractResult(), _SKIPPED)

    # --- Stream 2: State ---
    async for event in _state_stream(state, env, narration, intent, turn_no, packing, config, trace_id, container, save_dir):
        yield event
    state_result, extraction_event["state"] = container.state_result if container.state_result else (StateExtractResult(), _SKIPPED)

    # --- Stream 3: Record (always runs — post-narration backward-looking scribe) ---
    # NOTE: Record stream failures are caught (not raised) because record is a
    # "backward-looking scribe" — it's not critical for state. If it fails, the
    # turn still completes with scene+state deltas. Beat candidates are generated
    # from narration (world step), not from record.
    async for event in _record_stream(state, env, narration, scene_result, state_result, turn_no, config, trace_id, band, recent_turns, container, save_dir):
        yield event
    record_result, extraction_event["record"] = container.record_result if container.record_result else (RecordResult(), _SKIPPED)

    _log.debug("extraction.dedup.start trace_id=%s compendium_updates=%d state_inv_add=%d", trace_id, len(scene_result.compendium_npc_update or []), len(state_result.inventory_add or []))
    # --- Dedup compendium updates before merging into StateMerge ---
    _comp = {nid: entry.model_dump() for nid, entry in state.compendium.npcs.items()}
    existing_npcs: list[dict[str, Any]] = []
    for nid, npc in _comp.items():
        if not isinstance(npc, dict):
            continue
        existing_npcs.append({
            "id": nid,
            "name": npc.get("name") or "",
            "title": npc.get("title") or "",
            "bio_preview": (npc.get("bio") or "").strip()[:120],
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
    # --- Merge into single StateMerge ---
    merged = StateMerge(
        compendium_npc_update=scene_result.compendium_npc_update,
        location_change=state_result.location_change,
        location_description=state_result.location_description,
        location_change_reason=state_result.location_change_reason or "",
        inventory_change_reason=state_result.inventory_change_reason,
        condition_change_reason=state_result.condition_change_reason,
        inventory_add=state_result.inventory_add,
        inventory_remove=state_result.inventory_remove,
        inventory_update=state_result.inventory_update,
        pc_condition_add=state_result.pc_condition_add,
        pc_condition_remove=state_result.pc_condition_remove,
        actions=record_result.actions or [],
    )

    yield (
        merged,
        record_result.actions,
        record_result.outcome_summary,
        extraction_event,
        record_result,
        scene_result,
        container.extraction_ctx,  # type: ignore[misc]
    )
    _log.debug("extraction.pipeline.done trace_id=%s turn_no=%d", trace_id, turn_no)


async def _scene_stream(
    state: WorldState, env: "Environment", narration: str,
    turn_no: int, config: EngineConfig, trace_id: str,
    container: _ExtractionAccumulator, save_dir: Path = Path("."),
) -> AsyncIterator[tuple[str, Any]]:
    variant = _ExtractionStreamConfig(
        name="scene",
        result_type=SceneExtractResult,
        build_messages=lambda s: _extract_scene_messages(env, narration, s, turn_no=turn_no),
        build_messages_kwargs={},
        strip_keys=(),
        preview_builder=lambda s, r: _apply_delta_lazy(s.model_copy(), StateMerge(compendium_npc_update=r.compendium_npc_update or []), trace_id=trace_id),
        panel_builder=lambda s: {
            "npcs": {nid: entry.model_dump() for nid, entry in s.compendium.npcs.items()},
            "location": s.location.model_dump(),
        },
        fatal=True,
        call_name="extract_scene",
    )
    async for event in _run_extraction_stream(state, variant, config, trace_id, turn_no, container, save_dir):
        yield event


async def _state_stream(
    state: WorldState, env: "Environment", narration: str,
    intent: "IntentEnvelope | None", turn_no: int, packing: dict[str, Any] | None,
    config: EngineConfig, trace_id: str,
    container: _ExtractionAccumulator, save_dir: Path = Path("."),
) -> AsyncIterator[tuple[str, Any]]:
    variant = _ExtractionStreamConfig(
        name="state",
        result_type=StateExtractResult,
        build_messages=lambda s: _extract_state_messages(env, narration, s, intent=intent, turn_no=turn_no, pack_inventory=(packing or {}).get("inventory") or []),
        build_messages_kwargs={},
        strip_keys=("_reasoning",),
        preview_builder=lambda s, r: _apply_delta_lazy(s.model_copy(), StateMerge(
            inventory_add=r.inventory_add or [],
            inventory_remove=r.inventory_remove or [],
            inventory_update=r.inventory_update or [],
            pc_condition_add=r.pc_condition_add or [],
            pc_condition_remove=r.pc_condition_remove or [],
            location_change=r.location_change,
            location_change_reason=r.location_change_reason or "",
            inventory_change_reason=r.inventory_change_reason or "",
            condition_change_reason=r.condition_change_reason or "",
        ), trace_id=trace_id),
        panel_builder=lambda s: {
            "pc": s.pc.model_dump(),
            "inventory": [it.model_dump() for it in s.inventory],
            "location": s.location.model_dump(),
        },
    )
    async for event in _run_extraction_stream(state, variant, config, trace_id, turn_no, container, save_dir):
        yield event


async def _record_stream(
    state: WorldState, env: "Environment", narration: str,
    scene_result: SceneExtractResult, state_result: StateExtractResult,
    turn_no: int, config: EngineConfig, trace_id: str,
    band: str, recent_turns: list[dict[str, Any]] | None,
    container: _ExtractionAccumulator, save_dir: Path = Path("."),
) -> AsyncIterator[tuple[str, Any]]:
    container.extraction_ctx = _build_post_delta_context(state, scene_result, state_result)
    variant = _ExtractionStreamConfig(
        name="record",
        result_type=RecordResult,
        build_messages=lambda s: _record_messages(env, narration, s, extraction_ctx=container.extraction_ctx, recent_turns=(recent_turns or [])[-10:], turn_no=turn_no, band=band, arc_ttl=config.arc_memory_ttl, config=config),  # type: ignore[arg-type]
        build_messages_kwargs={},
        strip_keys=("_reasoning",),
        preview_builder=lambda s, r: s,
        panel_builder=lambda s: {
            "arc": s.long_term_objective.model_dump(),
            "scene": s.scene.model_dump(),
            "meta": s.meta.model_dump(),
        },
    )
    async for event in _run_extraction_stream(state, variant, config, trace_id, turn_no, container, save_dir):
        yield event
    record_result, extraction_event = container.record_result if container.record_result else (RecordResult(), {"skipped": True, "tokens_in": 0, "tokens_out": 0, "ms": 0, "attempts": 0, "retry_errors": []})
    if record_result and not record_result.actions:
        narr_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', narration.strip()) if len(s.strip().split()) > 5]
        present_npc_names = [getattr(entry, "name", "") for entry in container.extraction_ctx.comp_this_turn.values() if getattr(entry, "presence", None) == "present"]
        inventory_items = [getattr(item, "name", getattr(item, "id", "")) for item in state.inventory]
        arc_goal = state.long_term_objective.long_term_objective
        actions = []
        if narr_sentences:
            actions.append(f"Continue {narr_sentences[0].lower().strip()[:80]}")
        else:
            actions.append("Take a careful look around the area.")
        if present_npc_names:
            npc = present_npc_names[0]
            actions.append(f"Speak with {npc} about what just happened.")
        else:
            actions.append("Survey your surroundings for useful information.")
        if inventory_items:
            item = inventory_items[0]
            actions.append(f"Check your {item} for anything useful.")
        else:
            actions.append("Pat down your gear for anything you might have missed.")
        if arc_goal:
            actions.append(f"Focus on {arc_goal[:60]} to advance your goal.")
        else:
            actions.append("Decide what matters most and pursue it.")
        container.record_result = (record_result.model_copy(update={"actions": actions}), extraction_event)
