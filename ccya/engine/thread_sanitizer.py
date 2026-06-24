"""Thread sanitizer: periodically reviews arc/thread state and applies corrections."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json
from ccya.llm_client import chat as llm_chat
from ccya.models import ArcThread, LongTermObjective, ProgressEntry, SanitizedWorldStateFact, ThreadResolution, ThreadUpdate
from ccya.state.chronicle import append_event, load_last_narration

_log = logging.getLogger(__name__)


async def sanitize_threads(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
    trace_id: str = "",
) -> tuple[dict[str, Any], bool]:
    """Run thread sanitization if current turn triggers it.

    Returns:
        (state, sanitize_ran) — sanitize_ran is True when any thread
        changes were applied. state is mutated in place.
    """
    try:
        return await _sanitize_threads_impl(save_dir, state, config, trace_id)
    except Exception as exc:
        _log.warning("thread_sanitizer: unexpected error, skipping sanitization: %s", exc)
        return state, False


async def _sanitize_threads_impl(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
    trace_id: str = "",
) -> tuple[dict[str, Any], bool]:
    """Core sanitization logic (wrapped by sanitize_threads for exception safety)."""
    if config.sanitize_every <= 0:
        return state, False

    meta = state.get("meta") or {}
    current_turn = int(meta.get("turn", 0))
    if current_turn == 0:
        _log.debug("thread_sanitizer: skipping turn %d", current_turn)
        return state, False

    if current_turn % config.sanitize_every != 0:
        return state, False

    recent_turns = load_last_narration(save_dir, 5)
    prior_history = list(meta.get("prior_history") or [])
    turn_no = int(meta.get("turn", 0))

    env = _build_jinja_env(str(Path(__file__).parent.parent / "prompts"))
    messages = _build_messages(env, state, recent_turns, prior_history, turn_no, current_turn, sanitize_every=config.sanitize_every)

    t_sanitize = asyncio.get_running_loop().time()
    try:
        resp = await llm_chat(
            config.host,
            config.model,
            messages,
            temperature=config.sanitize_temperature,
            timeout=float(config.request_timeout_s),
        )
        response_text = resp.get("response", "") or ""
    except Exception as exc:
        _log.warning("thread_sanitizer: LLM call failed, skipping: %s", exc)
        return state, False

    parsed = _parse_response(response_text)
    if not parsed:
        _log.warning(
            "thread_sanitizer: LLM returned empty/invalid response at turn %d, skipping",
            current_turn,
        )
        return state, False

    changes_made, changes_detail = _apply_sanitization(state, parsed, current_turn)

    if not changes_made:
        _log.warning(
            "thread_sanitizer: LLM returned no changes at turn %d, skipping",
            current_turn,
        )
        return state, False

    elapsed_ms = (asyncio.get_running_loop().time() - t_sanitize) * 1000
    usage = resp.get("usage") or {}

    cd = changes_detail
    record = {
        "kind": "sanitizer",
        "turn": current_turn,
        "trace_id": trace_id,
        "ms": round(elapsed_ms, 1),
        "tokens_in": int(usage.get("prompt_tokens", 0)),
        "tokens_out": int(usage.get("completion_tokens", 0)),
        "threads_updated": list(cd.get("updated_ids") or []),
        "threads_resolved": list(cd.get("resolved_ids") or []),
        "threads_added": list(cd.get("added_ids") or []),
        "goal_changed": cd.get("goal_before") != cd.get("goal_after"),
        "changes_detail": {
            "updated": dict(cd.get("updates_dict") or {}),
            "resolved": [dict(r) for r in cd.get("resolved_list") or []],
            "added": [dict(t) for t in cd.get("added_list") or []],
            "goal": {
                "before": cd.get("goal_before"),
                "after": cd.get("goal_after"),
            },
        },
    }

    try:
        append_event(save_dir, record)
    except Exception as exc:
        _log.warning("thread_sanitizer: failed to write event record: %s", exc)

    return state, True


def _build_messages(
    env: Any,
    state: dict[str, Any],
    recent_turns: list[dict[str, Any]],
    prior_history: list[str],
    turn_no: int,
    current_turn: int,
    sanitize_every: int = 1,
) -> list[dict[str, str]]:
    """Build system + user messages for the sanitizer LLM call."""
    arc = state.get("arc") or {}

    system_prompt = env.get_template("sanitize_thread.j2").render()

    long_term_objective = arc.get("long_term_objective", "")
    resolution = arc.get("resolution")
    threads = [{**t, "last_updated_turn": t.get("last_updated_turn"), "progress": t.get("major_updates") or []} for t in (arc.get("threads") or [])]
    completed_threads = [{**ct, "last_updated_turn": ct.get("last_updated_turn"), "progress": ct.get("major_updates") or [], "resolved_turn": ct.get("resolved_turn")} for ct in (arc.get("completed_threads") or [])]
    # TTL pass: drop candidates older than sanitize_every * 2 turns
    # Prevents accumulation when sanitizer is disabled or skipped
    raw_candidates = state.get("world_state_candidates", [])
    ttl_cutoff = current_turn - (sanitize_every * 2)
    world_state_candidates = [c for c in raw_candidates if c.get("resolved_turn", 0) >= ttl_cutoff]
    current_world_state = state.get("scene", {}).get("world_state", [])

    user_prompt = env.get_template("sanitize_thread.j2").render(
        long_term_objective=long_term_objective,
        resolution=resolution,
        threads=threads,
        completed_threads=completed_threads,
        turn_no=turn_no,
        recent_turns=recent_turns,
        prior_history=prior_history,
        world_state_candidates=world_state_candidates,
        current_world_state=current_world_state,
        current_turn=current_turn,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _parse_response(response_text: str) -> dict[str, Any] | None:
    """Extract and validate JSON from LLM response.

    Looks for <sanitize>...</sanitize> tags first, then falls back to
    brace matching via _find_json. Validates sub-objects against existing
    Pydantic models (ThreadUpdate, ThreadResolution, ArcThread).
    Skips entries with unknown thread IDs.
    """
    text = response_text.strip()

    # Try extracting from <sanitize> tags first
    sanitize_match = re.search(
        r"<sanitize>(.*?)</sanitize>", text, re.DOTALL
    )
    if sanitize_match:
        inner = sanitize_match.group(1).strip()
        parsed = _try_parse_json(inner)
        if parsed is not None:
            return _validate_parsed(parsed)

    # Fallback to general JSON extraction (handles markdown blocks, brace matching)
    parsed = _find_json(text)
    if parsed is not None:
        return _validate_parsed(parsed)

    _log.warning("thread_sanitizer: could not extract JSON from LLM response")
    return None


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """Try parsing text as a JSON dict."""
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _validate_parsed(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Validate parsed JSON against expected schema.

    Validates sub-objects using existing Pydantic models. Skips entries
    with unknown thread IDs (logs warning). Returns validated dict or None.
    """
    if not isinstance(raw, dict):
        return None

    result: dict[str, Any] = {}

    # goal_update — optional, must have long_term_objective if present
    gu = raw.get("goal_update")
    if gu is not None:
        if isinstance(gu, dict) and gu.get("long_term_objective"):
            result["goal_update"] = {
                "long_term_objective": str(gu["long_term_objective"]),
            }

    # thread_updates — validate each against ThreadUpdate model (with progress coercion)
    tu_list = raw.get("thread_updates", [])
    validated_tus: list[dict[str, Any]] = []
    for _tu in tu_list or []:
        if not isinstance(_tu, dict):
            continue
        try:
            tu_copy = dict(_tu)
            prog = tu_copy.get("progress")
            if prog is not None and isinstance(prog, list):
                tu_copy["progress"] = str(prog[0]) if prog else None

            # Coerce unknown major_update_signal values to "advancement"
            pk = tu_copy.get("major_update_signal")
            if pk is not None and pk not in ("advancement", "setback"):
                tu_copy["major_update_signal"] = "advancement"

            validated_tu = ThreadUpdate.model_validate(tu_copy)
            result_dict = validated_tu.model_dump(exclude_none=True)
            # Re-add original progress array for apply phase (we need full replacement list)
            if isinstance(prog, list):
                result_dict["progress"] = [str(p) for p in prog]

            validated_tus.append(result_dict)
        except Exception:
            _log.warning("thread_sanitizer: skipping invalid thread_update %s", _tu.get("id"))

    if validated_tus:
        result["thread_updates"] = validated_tus

    # resolved_threads — validate against ThreadResolution model
    rt_list = raw.get("resolved_threads", [])
    validated_rts: list[dict[str, Any]] = []
    for _rt in rt_list or []:
        if not isinstance(_rt, dict):
            continue
        try:
            validated_rt = ThreadResolution.model_validate(_rt)
            validated_rts.append(validated_rt.model_dump())
        except Exception:
            _log.warning("thread_sanitizer: skipping invalid resolved_thread %s", _rt.get("id"))

    if validated_rts:
        result["resolved_threads"] = validated_rts

    # _checklist — must be dict[str, str]
    checklist = raw.get("_checklist")
    if isinstance(checklist, dict):
        result["_checklist"] = {k: str(v) for k, v in checklist.items() if isinstance(k, str)}

    # world_state — complete replacement list, validate each entry against SanitizedWorldStateFact
    ws_list = raw.get("world_state", [])
    validated_ws: list[dict[str, Any]] = []
    for _ws in ws_list or []:
        if not isinstance(_ws, dict):
            continue
        try:
            validated_ws_fact = SanitizedWorldStateFact.model_validate(_ws)
            validated_ws.append(validated_ws_fact.model_dump(exclude_none=True))
        except Exception:
            _log.warning("thread_sanitizer: skipping invalid world_state entry %s", _ws.get("id"))

    if validated_ws:
        result["world_state"] = validated_ws

    return result


def _apply_sanitization(
    state: dict[str, Any],
    parsed: dict[str, Any],
    current_turn: int,
    ) -> tuple[bool, dict[str, Any]]:
    """Apply sanitization changes to arc state.

    1. goal_update: replace long_term_objective if non-null
    2. thread_updates: find by ID in threads[], apply non-null fields
    3. resolved_threads: move from threads[] to completed_threads[]
    Returns (has_changes, changes_detail).
    """
    arc_raw = state.get("arc", {})
    if not arc_raw:
        return False, {}

    try:
        arc = LongTermObjective.model_validate(state.get("arc", {}))
    except Exception as exc:
        _log.warning("thread_sanitizer: failed to validate arc, skipping: %s", exc)
        return False, {}

    changes_detail: dict[str, Any] = {
        "updated": {},
        "updated_ids": [],
        "updates_dict": {},
        "resolved": [],
        "resolved_ids": [],
        "resolved_list": [],
        "added": [],
        "added_ids": [],
        "added_list": [],
        "goal": {"before": None, "after": None},
        "goal_before": None,
        "goal_after": None,
    }
    updated_ids: list[str] = []
    resolved_ids: list[str] = []
    added_ids: list[str] = []

    # 1. goal_update
    gu = parsed.get("goal_update")
    if gu and isinstance(gu, dict) and gu.get("long_term_objective"):
        new_goal = str(gu["long_term_objective"])
        if new_goal != arc.long_term_objective:
            changes_detail["goal_before"] = changes_detail["goal"]["before"] = arc.long_term_objective or None
            changes_detail["goal_after"] = changes_detail["goal"]["after"] = new_goal
            arc.long_term_objective = new_goal

    # Build lookup maps for thread resolution by ID
    threads_by_id: dict[str, int] = {}
    for i, t in enumerate(arc.threads):
        threads_by_id[t.id] = i

    # 2. thread_updates — only apply to active (non-resolved) threads
    for _tu in parsed.get("thread_updates") or []:
        tid = _tu.get("id", "")
        if not tid:
            continue

        found_idx = threads_by_id.get(tid)
        if found_idx is None:
            _log.warning(
                "thread_sanitizer: thread_update references unknown id=%s — skipping",
                tid,
            )
            continue

        updates_dict: dict[str, Any] = {}
        delta: dict[str, Any] = {"fields": [], "progress": None}

        for field in ("dormant", "urgency", "type"):
            val = _tu.get(field)
            if val is not None and val != getattr(arc.threads[found_idx], field):
                updates_dict[field] = val
                delta["fields"].append({
                    "field": field,
                    "before": getattr(arc.threads[found_idx], field),
                    "after": val,
                })

        # Progress: full replacement list from LLM (array of strings)
        # Only record if the list actually differs from current state to avoid
        # duplicate-progress entries wasting output tokens in diffs.
        prog_list = _tu.get("progress")
        if isinstance(prog_list, list) and prog_list:
            kind = _tu.get("major_update_signal", "advancement") or "advancement"
            old_progress = [p.text for p in arc.threads[found_idx].major_updates]
            if prog_list != old_progress:
                new_entries = [ProgressEntry(text=str(p), kind=kind) for p in prog_list]
                updates_dict["major_updates"] = new_entries
                delta["progress"] = {
                    "before": old_progress,
                    "after": prog_list,
                }

        # Enforce invariant: dormant threads cannot be urgent
        if updates_dict.get("dormant") is True:
            final_urgency = updates_dict.get("urgency", getattr(arc.threads[found_idx], "urgency", "normal"))
            if final_urgency == "urgent":
                updates_dict["urgency"] = "background"

        if updates_dict:
            arc.threads[found_idx] = arc.threads[found_idx].model_copy(update=updates_dict)
            updated_ids.append(tid)
            changes_detail["updated"][tid] = delta

    changes_detail["updated_ids"] = updated_ids
    changes_detail["updates_dict"] = changes_detail["updated"]

    # 3. resolved_threads — move from threads[] to completed_threads[]
    for _rt in parsed.get("resolved_threads") or []:
        tid = _rt.get("id", "")
        if not tid:
            continue

        found_idx = threads_by_id.get(tid)
        if found_idx is None:
            _log.warning(
                "thread_sanitizer: resolved_thread references unknown id=%s — skipping",
                tid,
            )
            continue

        thread = arc.threads[found_idx]
        resolution_state = _rt.get("resolution_state", "resolved")
        outcome = str(_rt.get("outcome", ""))

        completed_entry = ArcThread(
            **{**thread.model_dump(), "dormant": True, "resolution_state": resolution_state,
               "outcome": outcome, "resolved_turn": current_turn},
        )

        # Remove from threads[], add to completed_threads[] (dedup by id)
        arc.threads = [t for t in arc.threads if t.id != tid]
        existing_completed_idx: int | None = None
        for i, ct in enumerate(arc.completed_threads):
            if ct.id == tid:
                existing_completed_idx = i
                break

        if existing_completed_idx is not None:
            arc.completed_threads[existing_completed_idx] = completed_entry
        else:
            arc.completed_threads.append(completed_entry)

        resolved_ids.append(tid)
        entry = {"id": tid, "resolution_state": resolution_state, "outcome": outcome}
        changes_detail["resolved"].append(entry)

    changes_detail["resolved_ids"] = resolved_ids
    changes_detail["resolved_list"] = changes_detail["resolved"]


    changes_detail["added_ids"] = added_ids
    changes_detail["added_list"] = changes_detail["added"]

    # Set last_thread_created_turn if any threads were added
    if added_ids and arc.threads:
        arc.last_thread_created_turn = current_turn

    # 6. world_state — atomic swap: replace entire world_state array
    new_world_state = parsed.get("world_state")
    if new_world_state is not None:
        state.setdefault("scene", {})["world_state"] = new_world_state
        # Clear processed candidates
        state.pop("world_state_candidates", None)

    # Write back mutated arc (only if something changed)
    has_changes = bool(updated_ids or resolved_ids or added_ids or changes_detail["goal"]["before"] != changes_detail["goal"]["after"])

    if has_changes:
        state.setdefault("arc", {}).update({**_dump_arc(arc), "threads": [t.model_dump() for t in arc.threads], "completed_threads": [t.model_dump() for t in arc.completed_threads]})

    return has_changes, changes_detail


def _dump_arc(arc: LongTermObjective) -> dict[str, Any]:
    """Dump LongTermObjective to plain dict."""
    return {**arc.model_dump(exclude={"threads", "completed_threads"})}
