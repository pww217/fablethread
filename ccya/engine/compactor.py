"""Compactor: periodically compress narrative history + recent events."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.llm_client import chat as llm_chat
from ccya.models import CompactorSanitizationResult
from pydantic import ValidationError

_log = logging.getLogger("ccya.engine")

_COMPACTED_HEADER = re.compile(r"^## COMPACTED$", re.MULTILINE)
_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^- \[T(\d+)\] ")


async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
) -> dict[str, Any]:
    """Run compaction if current turn triggers it.

    Trigger: current_turn % compact_every == 0.
    Compacts turns [last_compacted_turn+1 .. retain_from-1].
    retain_from = max(1, current_turn - window_turns + 1).
    Sets last_compacted_turn = compact_end (NOT current_turn).
    """
    if config.compact_every <= 0:
        return state

    current_turn = int((state.get("meta") or {}).get("turn", 0) or 0)
    if current_turn == 0:
        return state

    if current_turn % config.compact_every != 0:
        return state

    last_compacted_turn = int((state.get("meta") or {}).get("last_compacted_turn", 0) or 0)
    retain_from = max(1, current_turn - config.window_turns + 1)
    compact_end = retain_from - 1
    compact_start = last_compacted_turn + 1

    if compact_start > compact_end:
        _log.info(
            "compactor: nothing to compact at turn %d (compact_start=%d > compact_end=%d)",
            current_turn, compact_start, compact_end,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state

    _log.info(
        "compactor: compacting turns %d–%d at turn %d (window=%d, compact_every=%d)",
        compact_start, compact_end, current_turn, config.window_turns, config.compact_every,
        extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
    )

    turns = _extract_turns_for_compact(save_dir, compact_start, compact_end)
    if not turns:
        return state

    env = state.get("_jinja_env")
    if env is None:
        from ccya.engine.config import _build_jinja_env

        template_dir = str(Path(__file__).parent.parent / "prompts")
        env = _build_jinja_env(template_dir)

    messages = _build_compact_messages(env, state, turns)

    try:
        resp = await llm_chat(
            config.host,
            config.model,
            messages,
            temperature=config.compact_temperature,
            timeout=float(config.request_timeout_s),
        )
        response_text = resp.get("response", "")
    except Exception as exc:
        _log.warning("compactor: LLM call failed, skipping: %s", exc)
        return state

    bullets_text, sanitization = _parse_compact_response(response_text)

    if not bullets_text.strip():
        _log.warning(
            "compactor: LLM returned empty bullets at turn %d, skipping",
            current_turn,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state

    new_bullets = [b.strip() for b in bullets_text.splitlines() if b.strip()]
    state.setdefault("meta", {}).setdefault("prior_history", []).extend(new_bullets)

    _write_compacted_block(save_dir, bullets_text, compact_start, compact_end)

    if sanitization is not None:
        _apply_sanitization(state, sanitization)

    state.setdefault("meta", {})["last_compacted_turn"] = compact_end

    return state


def _extract_turns_for_compact(
    save_dir: Path, start_turn: int, end_turn: int
) -> list[dict[str, Any]]:
    """Extract full prose for turns in [start_turn, end_turn] from chronicle.md."""
    path = save_dir / "chronicle.md"
    if not path.exists():
        return []

    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))

    result: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        turn_num = int(m.group(1))
        if turn_num < start_turn or turn_num > end_turn:
            continue

        turn_input = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        narrative = text[body_start:body_end].strip()

        result.append({
            "turn": turn_num,
            "input": turn_input,
            "narrative": narrative,
        })

    return result


def _build_compact_messages(
    env: Any,
    state: dict[str, Any],
    turns: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build system + user messages for the compaction LLM call."""
    system_prompt = env.get_template("compact_system.j2").render()

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    present_npcs = state.get("scene", {}).get("present_npcs") or []
    pressures = state.get("scene", {}).get("scene_pressure") or []
    inventory = list(state.get("inventory") or [])
    _npcs_raw = (state.get("compendium") or {}).get("npcs") or {}
    compendium_npcs: list[tuple[str, Any]] = list(_npcs_raw.items())
    all_quests = list(state.get("quests") or [])
    conditions = list((state.get("pc") or {}).get("conditions") or [])

    user_prompt = env.get_template("compact_user.j2").render(
        turns=turns,
        active_quests=active_quests,
        npc_names=[n.get("name", n) if isinstance(n, dict) else n for n in present_npcs],
        pressures=pressures,
        inventory=inventory,
        compendium_npcs=compendium_npcs,
        all_quests=all_quests,
        conditions=conditions,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _parse_compact_response(
    response_text: str,
) -> tuple[str, CompactorSanitizationResult | None]:
    """Parse LLM output into (bullet_lines_text, sanitization | None).

    Bullets: lines matching ^- \\[T\\d+\\]
    Sanitization: last JSON object in response, validated through CompactorSanitizationResult.
    """
    bullets = [
        line.strip()
        for line in response_text.splitlines()
        if _BULLET_RE.match(line.strip())
    ]
    bullets_text = "\n".join(bullets)

    # Strip markdown code fences so the brace scanner can find the JSON.
    cleaned = response_text.replace("```", "")

    # Find last JSON object (not array) in response.
    # Walk backwards from the last '}' to find the matching '{',
    # correctly handling nested braces in objects like npc_merge.
    last_close = cleaned.rfind("}")
    sanitization: CompactorSanitizationResult | None = None
    if last_close >= 0:
        depth = 0
        last_open = -1
        for i in range(last_close, -1, -1):
            if cleaned[i] == "}":
                depth += 1
            elif cleaned[i] == "{":
                depth -= 1
                if depth == 0:
                    last_open = i
                    break
        if last_open >= 0:
            candidate = cleaned[last_open : last_close + 1]
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict):
                    sanitization = CompactorSanitizationResult.model_validate(payload)
            except (json.JSONDecodeError, ValueError, ValidationError) as exc:
                _log.warning("compactor: invalid sanitization payload, skipping: %s", exc)

    return bullets_text, sanitization


def _apply_sanitization(
    state: dict[str, Any],
    san: CompactorSanitizationResult,
) -> None:
    """Apply compactor sanitization to state in-place.

    Validates all IDs against allowlists built from current state.
    Unknown IDs are silently skipped. Never raises.
    """
    log_ctx = {"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "compactor"}

    compendium_npcs: dict[str, Any] = (state.get("compendium") or {}).get("npcs") or {}
    inventory: list[dict[str, Any]] = list(state.get("inventory") or [])
    quests: list[dict[str, Any]] = list(state.get("quests") or [])
    pressures: list[dict[str, Any]] = list((state.get("scene") or {}).get("scene_pressure") or [])
    conditions: list[dict[str, Any]] = list((state.get("pc") or {}).get("conditions") or [])

    known_npc_ids = set(compendium_npcs.keys())
    known_inventory_ids = {it.get("id") for it in inventory if it.get("id")}
    known_quest_ids = {q.get("id") for q in quests if q.get("id")}
    known_pressure_ids = {p.get("id") for p in pressures if p.get("id")}
    known_condition_ids = {c.get("id") for c in conditions if c.get("id")}

    # npc_merge
    for merge in san.npc_merge:
        if merge.keep_id not in known_npc_ids:
            _log.warning("compactor: npc_merge keep_id %r unknown, skipping", merge.keep_id, extra=log_ctx)
            continue
        valid_remove = [rid for rid in merge.remove_ids if rid in known_npc_ids and rid != merge.keep_id]
        for rid in valid_remove:
            compendium_npcs.pop(rid, None)
            _log.info("compactor: merged duplicate NPC %r into %r", rid, merge.keep_id, extra=log_ctx)
        # Remove from present_npcs
        scene = state.setdefault("scene", {})
        remove_set = set(valid_remove)
        scene["present_npcs"] = [
            n for n in (scene.get("present_npcs") or [])
            if (n.get("id") if isinstance(n, dict) else n) not in remove_set
        ]

    # inventory_remove
    valid_inv_remove = {iid for iid in san.inventory_remove if iid in known_inventory_ids}
    if valid_inv_remove:
        state["inventory"] = [it for it in inventory if it.get("id") not in valid_inv_remove]
        for iid in valid_inv_remove:
            _log.info("compactor: removed duplicate inventory item %r", iid, extra=log_ctx)

    # quest_close (only active quests)
    valid_quest_close = {qid for qid in san.quest_close if qid in known_quest_ids}
    for q in quests:
        if q.get("id") in valid_quest_close and q.get("status") == "active":
            q["status"] = "completed"
            _log.info("compactor: closed orphaned quest %r", q.get("id"), extra=log_ctx)

    # pressure_remove
    valid_pressure_remove = {pid for pid in san.pressure_remove if pid in known_pressure_ids}
    if valid_pressure_remove:
        scene = state.setdefault("scene", {})
        scene["scene_pressure"] = [p for p in pressures if p.get("id") not in valid_pressure_remove]
        for pid in valid_pressure_remove:
            _log.info("compactor: removed stale pressure %r", pid, extra=log_ctx)

    # condition_remove
    valid_cond_remove = {cid for cid in san.condition_remove if cid in known_condition_ids}
    if valid_cond_remove:
        pc = state.setdefault("pc", {})
        pc["conditions"] = [c for c in conditions if c.get("id") not in valid_cond_remove]
        for cid in valid_cond_remove:
            _log.info("compactor: removed resolved condition %r", cid, extra=log_ctx)


def _write_compacted_block(
    save_dir: Path,
    bullets_text: str,
    compact_start: int,
    compact_end: int,
) -> None:
    """Write COMPACTED block to chronicle.md and remove compacted turn sections.

    If a COMPACTED block already exists, appends new bullets after it.
    Otherwise, prepends a new COMPACTED block before the first turn.
    After writing, removes the prose sections for turns in [compact_start, compact_end].
    """
    path = save_dir / "chronicle.md"
    if not path.exists():
        return

    text = path.read_text()
    existing = _COMPACTED_HEADER.search(text)

    if existing:
        block_end = existing.end()
        remaining = text[block_end:]
        next_header = _TURN_HEADER.search(remaining)
        if next_header:
            block_end = block_end + next_header.start()
        new_block = f"\n{bullets_text}\n"
        text = text[:block_end] + new_block + text[block_end:]
    else:
        turn_match = _TURN_HEADER.search(text)
        if turn_match:
            insert_pos = turn_match.start()
            new_block = f"## COMPACTED\n{bullets_text}\n\n"
            text = text[:insert_pos] + new_block + text[insert_pos:]
        else:
            text += f"\n## COMPACTED\n{bullets_text}\n"

    # Remove the prose sections for all compacted turns (1..compact_end).
    # This also cleans up any turns that were compacted by a previous version
    # of the code that didn't remove them.
    matches = list(_TURN_HEADER.finditer(text))
    turns_to_remove = {int(m.group(1)) for m in matches if int(m.group(1)) <= compact_end}
    if turns_to_remove:
        next_header_start: list[int] = []
        for i in range(len(matches)):
            if i + 1 < len(matches):
                next_header_start.append(matches[i + 1].start())
            else:
                next_header_start.append(len(text))
        new_text_parts: list[str] = []
        prev_end = 0
        for i, m in enumerate(matches):
            turn_num = int(m.group(1))
            section_end = next_header_start[i]
            if turn_num in turns_to_remove:
                new_text_parts.append(text[prev_end:m.start()])
            else:
                new_text_parts.append(text[prev_end:section_end])
            prev_end = section_end
        text = "".join(new_text_parts)

    path.write_text(text)
