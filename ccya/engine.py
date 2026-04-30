"""Turn engine: two-call pipeline (narrate + extract) with reliability measures.

Turn counter source of truth: engine.py only.
  - apply_delta in state.py does NOT increment meta.turn.
  - The engine increments after both calls succeed and before writing events.

Async generator protocol:
  run_turn() yields:
    ("token", str)         — one per narrative token, during call 1
    ("phase", dict)         — progress phases (e.g. narrate_done, extract_start)
    ("complete", TurnResult) — exactly once at the end
  Callers should async-for over run_turn() to get streaming behavior.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from jinja2 import Environment, FileSystemLoader

from ccya.models import ExtractResult, StateDelta, TurnResult
from ccya.ollama import chat as ollama_chat, chat_stream as ollama_chat_stream
from ccya.state import (
    append_chronicle,
    append_event,
    apply_delta,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_state,
    resolve_inventory_canonical_id,
    save_state,
)

_log = logging.getLogger("ccya.engine")

# ---------------------------------------------------------------------------
# Per-save turn in-flight guard
# ---------------------------------------------------------------------------


class _EventLock:
    """Per-key async lock for turn-in-flight guard."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, key: str) -> None:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        await self._locks[key].acquire()

    async def release(self, key: str) -> None:
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()


_inflight: _EventLock = _EventLock()


def is_turn_in_progress(save_dir: str) -> bool:
    lock = _inflight._locks.get(save_dir)
    return lock is not None and lock.locked()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class EngineConfig:
    ollama_host: str = "http://localhost:11434"
    model: str = "gemma3:27b"
    keep_alive: str = "60m"
    num_ctx: int = 32768
    extract_num_ctx: int = 4096
    request_timeout_s: int = 180
    narrate_temperature: float = 0.8
    extract_temperature: float = 0.0
    max_extract_retries: int = 1
    window_turns: int = 6
    chronicle_prefix_budget_tokens: int = 1500
    established_facts_max: int = 10
    enforce_extract_schema: bool = True
    enable_extract_thinking: bool = False
    enable_narrate_thinking: bool = False
    log_llm_io: bool = False
    log_llm_io_max_chars: int = 4000


# ---------------------------------------------------------------------------
# Jinja helpers
# ---------------------------------------------------------------------------


def _build_jinja_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _render(env: Environment, template_name: str, ctx: dict) -> str:
    return env.get_template(template_name).render(**ctx)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _narrate_messages(
    env: Environment,
    state: dict,
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict] = [],
    enable_narrate_thinking: bool = False,
) -> list[dict[str, str]]:
    """Build narrate message list: [system, user].

    system = stable rules + world state (maximises KV-cache reuse across turns)
    user   = raw player input (volatile — never in system)
    """
    ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "enable_narrate_thinking": enable_narrate_thinking,
    }
    system_text = _render(env, "narrate_system.j2", ctx)
    user_text = _render(env, "narrate_user.j2", {"user_input": user_input})
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _known_characters_for_extract(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Up to 10 compendium NPC rows for extract_user (reuse ids; bio preview truncated)."""
    comp = (state.get("compendium") or {}).get("npcs") or {}
    order = list((state.get("meta") or {}).get("compendium_touch_order") or [])
    seen: set[str] = set()
    out_ids: list[str] = []
    for nid in reversed(order):
        if nid in comp and nid not in seen:
            out_ids.append(nid)
            seen.add(nid)
            if len(out_ids) >= 10:
                break
    for k in sorted(comp.keys()):
        if k not in seen and len(out_ids) < 10:
            out_ids.append(k)
            seen.add(k)
    rows: list[dict[str, Any]] = []
    for nid in out_ids:
        e = comp.get(nid) or {}
        bio = (e.get("bio") or "").strip()
        if len(bio) > 120:
            bio = bio[:117].rstrip() + "..."
        rows.append(
            {
                "id": nid,
                "name": e.get("name") or "",
                "title": e.get("title") or "",
                "bio_preview": bio,
            },
        )
    return rows


def _summarize_applied(applied: dict[str, Any]) -> list[str]:
    """Short lines for UI diff toast (cap length)."""
    lines: list[str] = []
    if not applied:
        return lines
    # scene_tagline is shown in the header, no need to repeat in diff toast
    for it in applied.get("inventory_add") or []:
        if isinstance(it, dict):
            nm = it.get("name") or it.get("id") or "?"
            amt = int(it.get("amount") or 1)
            lines.append(f"+ {nm} ×{amt}")
    for it in applied.get("inventory_remove") or []:
        if isinstance(it, dict):
            rid = it.get("id", "?")
            amt = it.get("amount")
            if amt is not None:
                lines.append(f"- {rid} (−{amt})")
            else:
                lines.append(f"- {rid} (removed)")
    for it in applied.get("inventory_update") or []:
        if isinstance(it, dict) and it.get("id"):
            lines.append(f"~ {it['id']} updated")
    for f in applied.get("established_facts_add") or []:
        if isinstance(f, str):
            short = f[:56] + ("…" if len(f) > 56 else "")
            lines.append(f"+ {short}")
    for f in applied.get("established_facts_remove") or []:
        if isinstance(f, str):
            short = f[:40] + ("…" if len(f) > 40 else "")
            lines.append(f"- {short}")
    for _upd in applied.get("established_facts_update") or []:
        lines.append("~ Fact revised")
    for c in applied.get("pc_condition_add") or []:
        lines.append(f"+ {c}")
    for c in applied.get("pc_condition_remove") or []:
        lines.append(f"- {c}")
    for qu in applied.get("quest_updates") or []:
        if not isinstance(qu, dict):
            continue
        qid = qu.get("id", "?")
        if qu.get("status"):
            lines.append(f"! Quest {qid}: {qu['status']}")
        for o in qu.get("objectives") or []:
            if not isinstance(o, dict):
                continue
            if o.get("done"):
                lines.append(f"✓ {qid} obj {o.get('index', '?')}")
            if o.get("failed"):
                lines.append(f"✗ {qid} obj {o.get('index', '?')}")
    for u in applied.get("compendium_npc_update") or []:
        if isinstance(u, dict) and u.get("id"):
            lines.append(f"~ Dossier: {u['id']}")
    loc = applied.get("location_change")
    if isinstance(loc, dict) and (loc.get("name") or loc.get("id")):
        lines.append(f"→ {loc.get('name') or loc.get('id')}")
    return lines[:18]


def _extract_messages(
    env: Environment,
    narrative: str,
    state: dict[str, Any],
    *,
    enable_extract_thinking: bool = False,
) -> list[dict[str, str]]:
    """Build extract message list: [system, assistant, user].

    system    = schema + extraction rules (stable)
    assistant = the narrative just produced (model "owns" this output)
    user      = canonical state snapshot + emit JSON instruction
    """
    system_text = _render(
        env,
        "extract_system.j2",
        {"enable_thinking": enable_extract_thinking},
    )
    active_quests = [q for q in state.get("quests", []) if q.get("status") == "active"]
    established_facts = list(state.get("scene", {}).get("established_facts") or [])
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    present_npcs = list(state.get("scene", {}).get("present_npcs") or [])
    user_text = _render(
        env,
        "extract_user.j2",
        {
            "pc": pc,
            "location": location,
            "present_npcs": present_npcs,
            "active_quests": active_quests,
            "inventory": state.get("inventory", []),
            "established_facts": established_facts,
            "known_characters": _known_characters_for_extract(state),
        },
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": narrative},
        {"role": "user", "content": user_text},
    ]


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------


def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> block."""
    m = re.search(r"<thinking>\s*.*?\s*</thinking>", text, re.DOTALL)
    if m:
        return (text[: m.start()] + text[m.end() :]).strip()
    return text.strip()


def _find_json(text: str) -> dict | None:
    """Find and parse a JSON object from LLM output."""
    text = text.strip()

    def _try(t: str) -> dict | None:
        try:
            return json.loads(t)
        except (json.JSONDecodeError, ValueError):
            return None

    j = _try(text)
    if j is not None:
        return _unwrap(j)

    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            r = _try(p)
            if r is not None:
                return _unwrap(r)

    b = text.find("{")
    if b >= 0:
        r_idx = text.rfind("}")
        if r_idx > b:
            r = _try(text[b : r_idx + 1])
            if r is not None:
                return _unwrap(r)
    return None


def _unwrap(j: dict) -> dict:
    """If JSON is a full ExtractResult envelope, return it as-is for Pydantic.
    If it looks like a bare StateDelta, wrap it."""
    if "state_delta" in j and "actions" in j:
        return j
    return j


def _truncate(s: str, n: int) -> str:
    if not isinstance(s, str):
        s = str(s)
    if len(s) <= n:
        return s
    return s[:n] + f"…[truncated, {len(s) - n} more chars]"


def _log_llm_io(
    *,
    trace_id: str,
    phase: str,
    messages: list[dict] | None = None,
    response: str | None = None,
    extra: dict | None = None,
    max_chars: int = 4000,
) -> None:
    """Emit a single DEBUG record with prompt/response payloads."""
    payload: dict[str, Any] = {"phase": phase, "trace_id": trace_id}
    if messages is not None:
        payload["messages"] = [
            {"role": m.get("role"), "content": _truncate(m.get("content", ""), max_chars)}
            for m in messages
        ]
    if response is not None:
        payload["response"] = _truncate(response, max_chars)
    if extra:
        payload.update(extra)
    _log.debug("llm_io %s", json.dumps(payload, default=str), extra={"trace_id": trace_id})


def _avg_narrate_ms(save_dir: Path, n: int = 5) -> int:
    """Average narrate duration from the last n events. Returns 0 if fewer than 2 samples."""
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
    """Average extract duration from the last n events. Returns 0 if fewer than 2 samples."""
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


# ---------------------------------------------------------------------------
# Public async-generator API
# ---------------------------------------------------------------------------


async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
) -> AsyncIterator[tuple[str, Any]]:
    """Execute one turn. Async generator yielding:
        ("token", str)          — one per narrative chunk during call 1
        ("phase", dict)         — UI progress (narrate_done, extract_start, etc.)
        ("complete", TurnResult) — final result after call 2
    """
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict] = []
    metrics: dict = {}
    state = load_state(save_dir)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []
    established_facts: list[str] = []

    try:
        await _inflight.acquire(str(save_dir))

        # --- Memory: load chronicle tail + recent turns ---
        chronicle_tail = load_chronicle_tail(save_dir, config.chronicle_prefix_budget_tokens)
        recent_turns = load_recent_chronicle_turns(save_dir, config.window_turns)

        # === Call 1: Narrate (streaming) ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        narr_messages = _narrate_messages(
            env, state, user_input,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
        )

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id, phase="narrate_request",
                messages=narr_messages, max_chars=config.log_llm_io_max_chars,
            )
        async for chunk in ollama_chat_stream(
            config.ollama_host, config.model, narr_messages,
            temperature=config.narrate_temperature,
            keep_alive=config.keep_alive,
            num_ctx=config.num_ctx,
            timeout=float(config.request_timeout_s),
        ):
            if not narrative_chunks:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            narrative_chunks.append(chunk)
            yield ("token", chunk)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        narrative = _strip_thinking("".join(narrative_chunks))
        narr_metrics = {"first_token_ms": round(first_ms, 1), "total_ms": round(narr_ms, 1)}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id, phase="narrate_response",
                response=narrative, extra={"timing_ms": narr_metrics},
                max_chars=config.log_llm_io_max_chars,
            )

        yield ("phase", {"phase": "narrate_done"})

        # === Call 2: Extract (structured JSON) ===
        ext_messages = _extract_messages(
            env,
            narrative,
            state,
            enable_extract_thinking=config.enable_extract_thinking,
        )
        t2 = asyncio.get_event_loop().time()
        retries = 0
        parse_error = ""
        ext_usage: dict[str, int] = {}
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        ext_format = ExtractResult.model_json_schema() if config.enforce_extract_schema else None

        for attempt in range(1 + config.max_extract_retries):
            if attempt > 0:
                yield ("phase", {"phase": "extract_retry", "attempt": attempt + 1})
            try:
                if config.log_llm_io:
                    _log_llm_io(
                        trace_id=trace_id, phase=f"extract_request_attempt_{attempt}",
                        messages=ext_messages,
                        extra={"format_enforced": bool(ext_format)},
                        max_chars=config.log_llm_io_max_chars,
                    )
                result = await ollama_chat(
                    config.ollama_host, config.model, ext_messages,
                    format=ext_format,
                    temperature=config.extract_temperature,
                    keep_alive=config.keep_alive,
                    num_ctx=config.extract_num_ctx,
                    timeout=float(config.request_timeout_s),
                )
                raw = result.get("response", "") if isinstance(result, dict) else ""
                ext_usage = result.get("usage", {}) if isinstance(result, dict) else {}
                if config.log_llm_io:
                    _log_llm_io(
                        trace_id=trace_id, phase=f"extract_response_attempt_{attempt}",
                        response=raw, extra={"usage": ext_usage},
                        max_chars=config.log_llm_io_max_chars,
                    )
                cleaned = _strip_thinking(raw)
                j = _find_json(cleaned)
                if j is not None:
                    # Accept both full ExtractResult envelope and bare StateDelta
                    if "state_delta" in j:
                        er = ExtractResult(**j)
                        delta = er.state_delta
                        actions = er.actions
                    else:
                        delta = StateDelta(**j)
                    retries = attempt
                    break
                raise ValueError("No JSON found in response")
            except Exception as exc:
                parse_error = str(exc)
                _log.warning(
                    "extract parse failed (attempt %d/%d): %s",
                    attempt + 1, 1 + config.max_extract_retries, parse_error,
                    extra={"trace_id": trace_id},
                )
                if attempt < config.max_extract_retries:
                    fb = (
                        f"Your previous output failed to parse: {parse_error[:200]}. "
                        "Re-emit JSON matching the schema. No prose outside <thinking>."
                    )
                    ext_messages.append({"role": "user", "content": fb})
                    retries = attempt + 1
                else:
                    errors.append({"trace_id": trace_id, "message": parse_error})

        yield ("phase", {"phase": "extract_done"})

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        ext_metrics = {
            "retries": retries,
            "total_ms": round(ext_ms, 1),
            "tokens_in": ext_usage.get("prompt_tokens", 0),
            "tokens_out": ext_usage.get("total_tokens", 0),
        }
        # narrate and extract metrics are independent — narrate token counts
        # are not available from a streaming call so we omit them rather than
        # copy extract counts into the wrong slot.
        metrics = {
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        applied: dict = {}
        rejected: list[dict] = []

        if delta is not None:
            rejected = _validate(state, delta)
            if rejected:
                errors.append({
                    "trace_id": trace_id,
                    "message": f"Delta validation failed ({len(rejected)} rejection(s)).",
                })
                narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"
            else:
                state = apply_delta(state, delta, established_facts_max=config.established_facts_max)
                established_facts = list(delta.established_facts_add)
                applied = delta.model_dump(exclude_none=True)

        diff_lines = _summarize_applied(applied)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_recent_chronicle_turns).
        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(save_dir, f"\n\n## Turn {state['meta']['turn']} — {user_input}\n\n{narrative.strip()}")

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            established_facts=established_facts,
            diff=diff_lines,
            metrics=metrics,
            errors=errors,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
        fallback = narrative_chunks and "".join(narrative_chunks) or ""
        if not fallback:
            fallback = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        yield ("complete", TurnResult(
            turn=state.get("meta", {}).get("turn", 0),
            trace_id=trace_id,
            narrative=fallback,
            state_delta={},
            errors=errors,
            metrics=metrics,
            diff=[],
        ))
    finally:
        await _inflight.release(str(save_dir))


# ---------------------------------------------------------------------------
# Delta validator
# ---------------------------------------------------------------------------


def _validate(state: dict, delta: StateDelta) -> list[dict]:
    """Strict delta validator. Returns rejection dicts for illegal changes."""
    rejections: list[dict] = []

    inv_list: list[dict] = state.get("inventory", [])
    for rem in delta.inventory_remove:
        if resolve_inventory_canonical_id(inv_list, rem.id) is None:
            rejections.append({
                "field": "inventory_remove",
                "value": rem.id,
                "reason": f"Inventory item '{rem.id}' does not exist",
            })

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections


# ---------------------------------------------------------------------------
# Startup warmup
# ---------------------------------------------------------------------------


async def warmup(config: EngineConfig) -> None:
    """Silent 1-token chat call to pre-load the model into Ollama."""
    try:
        await ollama_chat(
            config.ollama_host, config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            keep_alive=config.keep_alive,
            num_ctx=config.num_ctx,
            timeout=30.0,
        )
    except Exception:
        pass
