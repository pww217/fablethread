"""Compactor: periodically compress narrative history + recent events."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.llm_client import chat as llm_chat

_log = logging.getLogger("ccya.engine")

_COMPACTED_HEADER = re.compile(r"^## COMPACTED$", re.MULTILINE)
_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^- \[T(\d+)\] ")


async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
) -> dict[str, Any]:
    """Run compaction pass if turn count triggers it.

    Mutates chronicle.md and state. Returns updated state.
    """
    if config.compact_every <= 0:
        return state

    current_turn = state.get("meta", {}).get("turn", 0)
    if current_turn == 0:
        return state

    if current_turn % config.compact_every != 0:
        return state

    last_compacted = state.get("meta", {}).get("last_compacted_turn", 0)
    window = config.window_turns
    end_turn = current_turn - window

    if last_compacted >= end_turn:
        return state

    _log.info(
        "compactor: compacting turns %d–%d (turn %d, window=%d)",
        last_compacted + 1,
        end_turn,
        current_turn,
        window,
    )

    turns = _extract_turns_for_compact(save_dir, last_compacted + 1, end_turn)
    if not turns:
        return state

    events = list(state.get("scene", {}).get("recent_events") or [])

    env = state.get("_jinja_env")
    if env is None:
        from ccya.engine.config import _build_jinja_env

        template_dir = str(Path(__file__).parent.parent / "prompts")
        env = _build_jinja_env(template_dir)

    messages = _build_compact_messages(env, state, turns, events)

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

    bullets_text, compacted_events = _parse_compact_response(response_text)

    if not bullets_text.strip():
        _log.warning("compactor: LLM returned empty bullets, skipping")
        return state

    _write_compacted_block(save_dir, bullets_text)

    if compacted_events:
        state.setdefault("scene", {})["recent_events"] = compacted_events

    state.setdefault("meta", {})["last_compacted_turn"] = current_turn

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
    events: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build system + user messages for the compaction LLM call."""
    system_prompt = env.get_template("compact_system.j2").render()

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    present_npcs = state.get("scene", {}).get("present_npcs") or []
    pressures = state.get("scene", {}).get("scene_pressure") or []

    user_prompt = env.get_template("compact_user.j2").render(
        turns=turns,
        events=events,
        active_quests=active_quests,
        npc_names=[n.get("name", n) if isinstance(n, dict) else n for n in present_npcs],
        pressures=pressures,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _parse_compact_response(response_text: str) -> tuple[str, list[str]]:
    """Parse LLM output into bullet text and compacted events list.

    Returns (bullets_text, compacted_events).
    Bullet lines match `- [T\\d+] ` pattern.
    Events are extracted from the last JSON array in the response.
    """
    bullets: list[str] = []
    lines = response_text.split("\n")

    for line in lines:
        m = _BULLET_RE.match(line.strip())
        if m:
            bullets.append(line.strip())

    # Extract last JSON array from response (non-greedy to avoid matching
    # bracket pairs in bullet lines like `- [T1] ...`)
    compacted_events: list[str] = []
    array_match = list(re.finditer(r"\[[\s\S]*?\]", response_text))
    if array_match:
        last_array_str = array_match[-1].group()
        try:
            parsed = json.loads(last_array_str)
            if isinstance(parsed, list):
                compacted_events = [str(e) for e in parsed]
        except (json.JSONDecodeError, ValueError):
            pass

    bullets_text = "\n".join(bullets)
    return bullets_text, compacted_events


def _write_compacted_block(save_dir: Path, bullets_text: str) -> None:
    """Write or append COMPACTED block to chronicle.md.

    If a COMPACTED block already exists, appends new bullets after it.
    Otherwise, prepends a new COMPACTED block before the first turn.
    """
    path = save_dir / "chronicle.md"
    if not path.exists():
        return

    text = path.read_text()
    existing = _COMPACTED_HEADER.search(text)

    if existing:
        # Find the end of the entire COMPACTED block (next ## header or EOF),
        # not just the header line, so subsequent compactions append after
        # existing bullets rather than re-inserting after the header.
        block_end = existing.end()
        remaining = text[block_end:]
        next_header = _TURN_HEADER.search(remaining)
        if next_header:
            block_end = block_end + next_header.start()
        new_block = f"\n{bullets_text}\n"
        text = text[:block_end] + new_block + text[block_end:]
    else:
        # Prepend before first turn header
        turn_match = _TURN_HEADER.search(text)
        if turn_match:
            insert_pos = turn_match.start()
            new_block = f"## COMPACTED\n{bullets_text}\n\n"
            text = text[:insert_pos] + new_block + text[insert_pos:]
        else:
            # No turns yet, just append
            text += f"\n## COMPACTED\n{bullets_text}\n"

    path.write_text(text)
