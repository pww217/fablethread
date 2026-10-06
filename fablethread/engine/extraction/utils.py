"""Shared utilities for the three-stream extraction pipeline."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from fablethread.engine.config import EngineConfig, _find_json
from fablethread.llm_client import chat_with_config as llm_chat, strip_thinking
from fablethread.models import CompendiumNpcAdd, CompendiumNpcUpdate

_log = logging.getLogger(__name__)


def _filter_pc_situation(pc_situation: dict[str, Any], schema: list[dict[str, Any]]) -> dict[str, Any]:
    """Filter pc.situation to only include keys marked persist=true in the schema."""
    if not schema:
        return pc_situation
    persist_keys = {entry["key"] for entry in schema if entry.get("persist", False)}
    if not persist_keys:
        return {}
    return {k: v for k, v in pc_situation.items() if k in persist_keys}


def _text_references_thread(text: str, thread_id: str) -> bool:
    """Check if text contains a reference to a specific thread ID.

    Matches backtick-quoted IDs like `thread_id` and bare word references.
    """
    if not text or not thread_id:
        return False
    # Backtick-quoted: `thread_id`
    if f"`{thread_id}`" in text:
        return True
    # Word boundary match for bare references
    return bool(re.search(rf'\b{re.escape(thread_id)}\b', text))


def _filter_evicted_threads(texts: list[str], evicted_ids: set[str]) -> list[str]:
    """Remove entries from a list of text that reference evicted thread IDs."""
    if not evicted_ids or not texts:
        return texts
    result = []
    for text in texts:
        if not isinstance(text, str):
            result.append(text)
            continue
        if any(_text_references_thread(text, tid) for tid in evicted_ids):
            _log.debug("thread_filter: evicting reference to %s from context", next(t for t in evicted_ids if _text_references_thread(text, t)))
        else:
            result.append(text)
    return result


def _context_meta(rendered_system: str, rendered_user: str, was_trimmed: bool, trimmed_chars: int) -> dict[str, Any]:
    """Compute context size signals for telemetry."""
    return {
        "system_text": rendered_system,
        "user_text": rendered_user,
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
    proposed: "CompendiumNpcAdd | CompendiumNpcUpdate",
    existing_npcs: list[dict[str, Any]],
    existing_ids: set[str] | None = None,
) -> "CompendiumNpcAdd | CompendiumNpcUpdate":
    """
    If proposed.name matches any existing NPC's name (case-insensitive),
    redirect proposed.id to the existing NPC's id. If proposed.id already
    exists in the compendium, redirect to it. Otherwise return proposed unchanged.
    
    For CompendiumNpcUpdate (which has no name field), only checks if
    proposed.id already exists in the compendium.
    """
    # Get name if available (CompendiumNpcAdd has it, CompendiumNpcUpdate doesn't)
    proposed_name = getattr(proposed, "name", None)
    
    if not proposed_name:
        # No name to match on — only check if id already exists
        proposed_id = getattr(proposed, "id", "").lower().strip()
        if existing_ids and proposed_id in existing_ids:
            return proposed.model_copy(update={"id": proposed_id})
        return proposed

    candidate = proposed_name.strip().lower()
    proposed_id = getattr(proposed, "id", "").lower().strip()

    # Check 1: proposed.id already exists in compendium → redirect
    if existing_ids and proposed_id in existing_ids:
        return proposed.model_copy(update={"id": proposed_id})

    for npc in existing_npcs:
        npc_name = (npc.get("name") or "").lower()
        npc_id = (npc.get("id") or "").lower().replace("_", " ")

        # Exact name match
        if candidate == npc_name or candidate == npc_id:
            return proposed.model_copy(update={"id": str(npc["id"])})

    return proposed


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

    # Coerce compendium_npc_add entries that are strings to dicts
    if isinstance(j.get("compendium_npc_add"), list):
        coerced = []
        for item in j["compendium_npc_add"]:
            if isinstance(item, str):
                coerced.append({"id": item.lower().replace(" ", "_").strip()})
            elif isinstance(item, dict) and "id" not in item:
                name = item.get("name", "") or str(item).lower()
                coerced.append({"id": name.replace(" ", "_").strip(), **item})
            else:
                coerced.append(item)
        j["compendium_npc_add"] = coerced

    # Coerce malformed thread_add (LLM returns [] or {} when no new thread)
    if isinstance(j.get("thread_add"), list):
        del j["thread_add"]
    elif isinstance(j.get("thread_add"), dict):
        required = {"id", "summary"}
        if not required.issubset(j["thread_add"].keys()):
            del j["thread_add"]

    # Coerce empty arc_resolve (LLM often emits {} or {resolution: null} instead of omitting)
    if isinstance(j.get("arc_resolve"), dict):
        arc_res = j["arc_resolve"]
        if not arc_res or "resolution" not in arc_res or arc_res.get("resolution") is None:
            del j["arc_resolve"]

    return j


def _parse_stream_result(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    try:
        # Coerce LLM output to match Pydantic model expectations
        return model_cls(**_coerce_scene_json(j))
    except Exception as e:
        raise ValueError(f"EXTRACTION_COERCION_FAILED: {e}") from e


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
        result = await llm_chat(
            config,
            messages,
            temperature=config.extract_temperature,
            top_p=config.extract_top_p,
            frequency_penalty=config.extract_frequency_penalty,
            timeout=float(config.request_timeout_s),
            num_ctx=config.num_ctx,
            enable_thinking=False,
            reasoning_effort="none",
            thinking_budget=0,
        )
        raw = result.content
        usage = result.usage
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
                # Extract specific missing field for targeted retry guidance
                _retry_hint = ""
                if "condition_change_reason" in parse_error and "required" in parse_error:
                    _retry_hint += " You omitted the required 'condition_change_reason' field — add a one-phrase reason for why conditions changed and re-emit."
                if "inventory_change_reason" in parse_error and "required" in parse_error:
                    _retry_hint += " You omitted the required 'inventory_change_reason' field — add a one-phrase reason for why inventory changed and re-emit."
                if "location_change_reason" in parse_error and "required" in parse_error:
                    _retry_hint += " You omitted the required 'location_change_reason' field — add a one-phrase reason for the location change, or omit location_change entirely."
                if "arc_resolve" in parse_error and "resolution" in parse_error:
                    _retry_hint += " If you want to resolve the arc, provide a non-empty 'resolution' string; otherwise omit 'arc_resolve' entirely."
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous output failed to parse: {parse_error[:200]}. "
                        f"Re-emit JSON matching the schema. No prose outside <thinking>.{_retry_hint}"
                    ),
                })
    _log.error(
        "%s failed after all attempts: %s",
        phase, parse_error,
        extra={"trace_id": trace_id, "error_kind": "EXTRACTION_PARSE_FAILED"},
    )
    raise ValueError(f"{phase} failed after all attempts: {parse_error}")


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
