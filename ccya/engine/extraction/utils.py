"""Shared utilities for the three-stream extraction pipeline."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _find_json, _log_llm_io
from ccya.llm_client import (
    chat as llm_chat,
    strip_thinking,
)
from ccya.models import CompendiumNpcUpdate

_log = logging.getLogger(__name__)


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


# Quantity words that may prefix group NPC names (spelled-out integers)
_GROUP_QUANTIFIERS = frozenset(
    (
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
    )
)


def _extract_group_base_type(name: str) -> str:
    """Extract the base type from a group NPC name by stripping leading quantity words.

    E.g. "Two militia guards" → "militia guards", "Three dockworkers" → "dockworkers".
    Returns the original name if no quantity prefix is found.
    """
    if not name:
        return name
    words = name.strip().lower().split()
    if not words:
        return name
    idx = 0
    while idx < len(words) and words[idx] in _GROUP_QUANTIFIERS:
        idx += 1
    # Also handle "Unknown" as a quantity-like prefix
    if idx == 0 and words[0] == "unknown":
        idx += 1
    return " ".join(words[idx:]) if idx < len(words) else name


def _dedup_compendium_update(
    proposed: "CompendiumNpcUpdate",
    existing_npcs: list[dict[str, Any]],
    existing_ids: set[str] | None = None,
) -> "CompendiumNpcUpdate":
    """
    If proposed.name matches any existing NPC's name or aliases (case-insensitive),
    redirect proposed.id to the existing NPC's id and return the modified update.
    Also handles group NPCs: if the base type (quantity stripped) matches an existing
    group NPC, redirect to that ID. If proposed.id already exists in the compendium,
    redirect to it. Otherwise return proposed unchanged.
    """
    if not proposed.name:
        return proposed

    candidate = proposed.name.strip().lower()
    proposed_id = proposed.id.lower().strip()

    # Check 1: proposed.id already exists in compendium → redirect
    if existing_ids and proposed_id in existing_ids:
        return proposed.model_copy(update={"id": proposed_id})

    for npc in existing_npcs:
        npc_names = [
            (npc.get("name") or "").lower(),
            (npc.get("id") or "").lower().replace("_", " "),
        ] + [(a or "").lower() for a in (npc.get("aliases") or [])]

        # Exact name match
        if candidate in npc_names:
            return proposed.model_copy(update={"id": str(npc["id"])})

        # Group NPC base type match: strip quantity words and compare
        proposed_base = _extract_group_base_type(candidate)
        npc_base = _extract_group_base_type(npc.get("name") or "")
        if (
            proposed_base != candidate
            and npc_base != (npc.get("name") or "").lower()
            and proposed_base == npc_base
            and proposed_base  # non-empty base type
        ):
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

    # Coerce malformed thread_add (LLM returns [] or {} when no new thread)
    if isinstance(j.get("thread_add"), list):
        del j["thread_add"]
    elif isinstance(j.get("thread_add"), dict):
        required = {"id", "summary"}
        if not required.issubset(j["thread_add"].keys()):
            del j["thread_add"]

    # Coerce empty arc_resolve (LLM often emits {} instead of omitting)
    if isinstance(j.get("arc_resolve"), dict) and not j["arc_resolve"]:
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
                # Extract specific missing field for targeted retry guidance
                _retry_hint = ""
                if "condition_change_reason" in parse_error and "required" in parse_error:
                    _retry_hint += " You omitted the required 'condition_change_reason' field — add a one-phrase reason for why conditions changed and re-emit."
                if "inventory_change_reason" in parse_error and "required" in parse_error:
                    _retry_hint += " You omitted the required 'inventory_change_reason' field — add a one-phrase reason for why inventory changed and re-emit."
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
