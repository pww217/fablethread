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
import copy
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from jinja2 import Environment, FileSystemLoader

from ccya.models import ExtractResult, StateDelta, TurnResult
from ccya.pack import ExtractExample, Pack, PlayerOverrides, SeedEnvelope, parse_world_facts
from ccya.llm_client import apply_thinking, chat as llm_chat, chat_stream as llm_chat_stream, strip_thinking, trim_messages
from ccya.state import (
    append_chronicle,
    append_event,
    apply_delta,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_state,
    resolve_inventory_remove_target,
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
    host: str = "http://localhost:8080/v1"
    model: str = "mlx-community/Qwen3.6-27B-4bit"
    # Local prompt-token budget for trim_messages (NOT sent to the LLM API —
    # mlx_lm.server has no equivalent of Ollama's num_ctx knob; this just
    # caps how much we pack into a single request).
    prompt_token_budget: int = 8192
    request_timeout_s: int = 180
    narrate_temperature: float = 0.9
    extract_temperature: float = 0.4
    max_extract_retries: int = 1
    window_turns: int = 6
    chronicle_prefix_budget_tokens: int = 1500
    established_facts_max: int = 30
    enable_extract_thinking: bool = False
    enable_narrate_thinking: bool = False
    # generate_seed settings (used by POST /new-game on dynamic packs)
    generate_seed_temperature: float = 0.9
    generate_seed_max_retries: int = 1
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
    pack_style: str = "",
) -> list[dict[str, str]]:
    """Build narrate message list: [system, user].

    system = stable rules + world state (maximises KV-cache reuse across turns)
    user   = raw player input (volatile — never in system)
    """
    ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "pack_style": pack_style,
    }
    system_text = _render(env, "narrate_system.j2", ctx)
    user_text = _render(env, "narrate_user.j2", {"user_input": user_input})
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_narrate_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


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


def _title_case_id(item_id: str) -> str:
    s = str(item_id or "").replace("_", " ").strip()
    return s.title() if s else "?"


def _norm_fact(s: Any) -> str:
    return " ".join(str(s or "").lower().split())


def _fact_in_list(needle: str, haystack: list[Any]) -> bool:
    hn = _norm_fact(needle)
    for h in haystack:
        if _norm_fact(h) == hn:
            return True
    return False


def _inv_amount_map(st: dict[str, Any]) -> dict[str, dict[str, Any]]:
    m: dict[str, dict[str, Any]] = {}
    for it in st.get("inventory") or []:
        if not isinstance(it, dict):
            continue
        iid = str(it.get("id") or "")
        if not iid:
            continue
        m[iid] = {
            "name": str(it.get("name") or "").strip(),
            "amount": max(1, int(it.get("amount") or 1)),
        }
    return m


def _quests_by_id(st: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for q in st.get("quests") or []:
        if isinstance(q, dict) and q.get("id"):
            out[str(q["id"])] = q
    return out


def summarize_changes(
    pre: dict[str, Any],
    post: dict[str, Any],
    _applied: dict[str, Any],
    rejected: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Diff pre vs post state into four UI categories (inventory, player, facts, quests)."""
    inventory: list[dict[str, Any]] = []
    player: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    quests: list[dict[str, Any]] = []

    for r in rejected or []:
        if r.get("field") == "inventory_remove":
            rid = str(r.get("value") or "")
            inventory.append({
                "kind": "failed_remove",
                "id": rid,
                "name": _title_case_id(rid) if rid else "?",
                "reason": str(r.get("reason") or ""),
            })

    pre_m = _inv_amount_map(pre)
    post_m = _inv_amount_map(post)
    for iid in sorted(set(pre_m) | set(post_m), key=lambda x: (0 if x == "credits" else 1, x)):
        a, b = pre_m.get(iid), post_m.get(iid)
        label_a = (a or {}).get("name") or _title_case_id(iid)
        label_b = (b or {}).get("name") or _title_case_id(iid)
        if a and not b:
            inventory.append({"kind": "removed", "id": iid, "name": label_a})
            continue
        if b and not a:
            inventory.append({"kind": "added", "id": iid, "name": label_b, "amount": int(b["amount"])})
            continue
        if a and b:
            amt_a, amt_b = int(a["amount"]), int(b["amount"])
            if label_a != label_b:
                inventory.append({
                    "kind": "renamed",
                    "id": iid,
                    "from_name": label_a,
                    "to_name": label_b,
                })
            if amt_b > amt_a:
                inventory.append({
                    "kind": "increased",
                    "id": iid,
                    "name": label_b,
                    "from": amt_a,
                    "to": amt_b,
                })
            elif amt_b < amt_a:
                inventory.append({
                    "kind": "decreased",
                    "id": iid,
                    "name": label_b,
                    "from": amt_a,
                    "to": amt_b,
                })

    pre_pc = pre.get("pc") or {}
    post_pc = post.get("pc") or {}
    pre_conds = list(pre_pc.get("conditions") or [])
    post_conds = list(post_pc.get("conditions") or [])
    for c in post_conds:
        if c not in pre_conds:
            player.append({"kind": "condition_added", "value": str(c)})
    for c in pre_conds:
        if c not in post_conds:
            player.append({"kind": "condition_removed", "value": str(c)})

    pl = pre.get("location") or {}
    pr = post.get("location") or {}
    if (pl.get("id") or "") != (pr.get("id") or "") or (pl.get("name") or "") != (pr.get("name") or ""):
        player.append({
            "kind": "location_changed",
            "from": str(pl.get("name") or pl.get("id") or "—"),
            "to": str(pr.get("name") or pr.get("id") or "—"),
        })

    pre_stats = pre_pc.get("stats") or {}
    post_stats = post_pc.get("stats") or {}
    if isinstance(pre_stats, dict) and isinstance(post_stats, dict):
        for k in sorted(set(pre_stats) | set(post_stats)):
            if pre_stats.get(k) != post_stats.get(k):
                player.append({
                    "kind": "stat_changed",
                    "stat": str(k),
                    "from": pre_stats.get(k),
                    "to": post_stats.get(k),
                })

    pre_facts = list((pre.get("scene") or {}).get("established_facts") or [])
    post_facts = list((post.get("scene") or {}).get("established_facts") or [])
    for pf in post_facts:
        if not _fact_in_list(str(pf), pre_facts):
            facts.append({"kind": "added", "value": str(pf)})
    for pf in pre_facts:
        if not _fact_in_list(str(pf), post_facts):
            facts.append({"kind": "removed", "value": str(pf)})

    pre_q = _quests_by_id(pre)
    post_q = _quests_by_id(post)
    for qid, pq in post_q.items():
        title = str(pq.get("title") or pq.get("id") or qid)
        prq = pre_q.get(qid)
        if prq is None:
            quests.append({"kind": "created", "id": qid, "title": title})
            continue
        st_pre, st_post = str(prq.get("status") or "active"), str(pq.get("status") or "active")
        if st_pre != st_post:
            quests.append({
                "kind": "status_changed",
                "id": qid,
                "title": title,
                "from": st_pre,
                "to": st_post,
            })
        po: list[Any] = list(prq.get("objectives") or [])
        qo: list[Any] = list(pq.get("objectives") or [])
        for i in range(max(len(po), len(qo))):
            if i >= len(qo):
                break
            qod = qo[i] if isinstance(qo[i], dict) else {}
            if i >= len(po):
                desc = str(qod.get("description") or "").strip()
                if desc:
                    quests.append({
                        "kind": "objective_added",
                        "id": qid,
                        "title": title,
                        "objective": desc,
                    })
                continue
            pod = po[i] if isinstance(po[i], dict) else {}
            if not bool(pod.get("done")) and bool(qod.get("done")):
                quests.append({
                    "kind": "objective_done",
                    "id": qid,
                    "title": title,
                    "objective": str(qod.get("description") or "").strip(),
                })
            if not bool(pod.get("failed")) and bool(qod.get("failed")):
                quests.append({
                    "kind": "objective_failed",
                    "id": qid,
                    "title": title,
                    "objective": str(qod.get("description") or "").strip(),
                })

    return {"inventory": inventory, "player": player, "facts": facts, "quests": quests}


def format_change_lines(ch: dict[str, Any] | None) -> list[str]:
    """Turn a ``changes`` dict into compact display lines (emoji + text)."""
    if not isinstance(ch, dict):
        return []
    lines: list[str] = []
    for row in ch.get("inventory") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        nm = str(row.get("name") or row.get("id") or "?")
        if k == "added":
            lines.append(f"🎒 + {nm} ×{int(row.get('amount') or 1)}")
        elif k == "removed":
            lines.append(f"🎒 − {nm}")
        elif k == "increased":
            fa, fb = int(row.get("from") or 0), int(row.get("to") or 0)
            lines.append(f"🎒 + {nm} ×{fb - fa}   ({fa} → {fb})")
        elif k == "decreased":
            fa, fb = int(row.get("from") or 0), int(row.get("to") or 0)
            lines.append(f"🎒 − {nm} ×{fa - fb}   ({fa} → {fb})")
        elif k == "renamed":
            lines.append(f"🎒 ~ {row.get('from_name')} → {row.get('to_name')}")
        elif k == "failed_remove":
            reason = str(row.get("reason") or "").strip()
            lines.append(f"🎒 ⚠ could not remove “{nm}”" + (f" ({reason})" if reason else ""))
    for row in ch.get("player") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        if k == "condition_added":
            lines.append(f"🩺 + {row.get('value')}")
        elif k == "condition_removed":
            lines.append(f"🩺 − {row.get('value')}")
        elif k == "location_changed":
            lines.append(f"🩺 → {row.get('to')}")
        elif k == "stat_changed":
            lines.append(f"🩺 {row.get('stat')}: {row.get('from')} → {row.get('to')}")
    for row in ch.get("facts") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        v = str(row.get("value") or "")
        short = v if len(v) <= 120 else v[:117].rstrip() + "…"
        if k == "added":
            lines.append(f"📜 + {short}")
        elif k == "removed":
            lines.append(f"📜 − {short}")
        elif k == "updated":
            old = str(row.get("old") or "")
            new = str(row.get("new") or "")
            o = old if len(old) <= 56 else old[:53].rstrip() + "…"
            n = new if len(new) <= 56 else new[:53].rstrip() + "…"
            lines.append(f"📜 ↻ {o} → {n}")
    for row in ch.get("quests") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        title = str(row.get("title") or row.get("id") or "?")
        if k == "created":
            lines.append(f"🗺️ + “{title}”")
        elif k == "status_changed":
            lines.append(f"🗺️ ! “{title}” → {row.get('to')}")
        elif k == "objective_done":
            od = str(row.get("objective") or "").strip()
            lines.append(f"🗺️ ✓ “{title}” — {od}" if od else f"🗺️ ✓ “{title}”")
        elif k == "objective_failed":
            od = str(row.get("objective") or "").strip()
            lines.append(f"🗺️ ✗ “{title}” — {od}" if od else f"🗺️ ✗ “{title}”")
        elif k == "objective_added":
            od = str(row.get("objective") or "").strip()
            lines.append(f"🗺️ + obj “{title}”: {od}" if od else f"🗺️ + obj “{title}”")
    return lines


def _extract_messages(
    env: Environment,
    narrative: str,
    state: dict[str, Any],
    *,
    enable_extract_thinking: bool = False,
    pack_examples: list[ExtractExample] | None = None,
) -> list[dict[str, str]]:
    """Build extract message list: [system, assistant, user].

    system    = schema + extraction rules (stable)
    assistant = the narrative just produced (model "owns" this output)
    user      = canonical state snapshot + emit JSON instruction
    """
    system_text = _render(
        env,
        "extract_system.j2",
        {
            "pack_examples": pack_examples or [],
        },
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
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": narrative},
        {"role": "user", "content": user_text},
    ]
    if enable_extract_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------


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
        return j

    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            r = _try(p)
            if r is not None:
                return r

    b = text.find("{")
    if b >= 0:
        r_idx = text.rfind("}")
        if r_idx > b:
            r = _try(text[b : r_idx + 1])
            if r is not None:
                return r
    return None


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
    pack_style: str = "",
    pack_examples: list[ExtractExample] | None = None,
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
            pack_style=pack_style,
        )
        narr_messages = trim_messages(narr_messages, config.prompt_token_budget)

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id, phase="narrate_request",
                messages=narr_messages, max_chars=config.log_llm_io_max_chars,
            )
        async for chunk in llm_chat_stream(
            config.host, config.model, narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            if not narrative_chunks:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            narrative_chunks.append(chunk)
            yield ("token", chunk)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        narrative = strip_thinking("".join(narrative_chunks))
        narr_metrics = {
            "first_token_ms": round(first_ms, 1),
            "total_ms": round(narr_ms, 1),
            "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
            "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
        }
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
            pack_examples=pack_examples,
        )
        ext_messages = trim_messages(ext_messages, config.prompt_token_budget)
        t2 = asyncio.get_event_loop().time()
        retries = 0
        parse_error = ""
        ext_usage: dict[str, int] = {}
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})

        for attempt in range(1 + config.max_extract_retries):
            if attempt > 0:
                yield ("phase", {"phase": "extract_retry", "attempt": attempt + 1})
            try:
                if config.log_llm_io:
                    _log_llm_io(
                        trace_id=trace_id, phase=f"extract_request_attempt_{attempt}",
                        messages=ext_messages,
                        max_chars=config.log_llm_io_max_chars,
                    )
                result = await llm_chat(
                    config.host, config.model, ext_messages,
                    temperature=config.extract_temperature,
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
                cleaned = strip_thinking(raw)
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
        metrics = {
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        state_pre_apply = copy.deepcopy(state)
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
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

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
            "changes": changes,
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
            changes=changes,
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
            changes={},
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
        if resolve_inventory_remove_target(inv_list, rem.id) is None:
            rejections.append({
                "field": "inventory_remove",
                "value": rem.id,
                "reason": f"Inventory item '{rem.id}' does not exist",
            })

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections


# ---------------------------------------------------------------------------
# generate_seed — New Game for dynamic packs
# ---------------------------------------------------------------------------


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    """Build the [system, user] messages for generate_seed."""
    from ccya.models import ExtractResult  # noqa: F401 — schema_json import path
    schema_json = SeedEnvelope.model_json_schema()
    ctx = {
        "schema_json": json.dumps(schema_json, indent=2),
        "world_text": pack.world_text,
        "style_text": pack.style_text,
        "scenario": pack.scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
    }
    system_text = _render(env, "generate_seed_system.j2", ctx)
    user_text = _render(env, "generate_seed_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _soft_validate_seed(
    envelope: SeedEnvelope,
    pack: Pack,
) -> list[str]:
    """Post-Pydantic soft checks that emit warnings but don't fail generation.
    Returns a list of warning strings (empty = all good)."""
    warnings: list[str] = []
    c = pack.scenario.constraints if pack.scenario else None
    if not c:
        return warnings

    npcs = envelope.seed_state.scene.present_npcs
    named = [n for n in npcs if n.name]
    if len(named) < c.min_named_npcs:
        warnings.append(f"Only {len(named)} named NPCs (min {c.min_named_npcs})")

    words = len(envelope.opening_narrative.split())
    lo, hi = c.prose_word_range
    if not (lo <= words <= hi):
        warnings.append(f"Opening narrative {words} words (expected {lo}-{hi})")

    if c.npc_distinct_first_letters:
        first_letters = [n.name[0].upper() for n in named if n.name]
        if len(first_letters) != len(set(first_letters)):
            warnings.append("NPC names share first letters (npc_distinct_first_letters)")

    text_lower = envelope.opening_narrative.lower()
    for cliche in c.forbid_cliches:
        if cliche.lower() in text_lower:
            warnings.append(f"Opening narrative contains forbidden cliché: '{cliche}'")

    if c.forbid_player_dependents:
        dependent_words = {"wife", "husband", "spouse", "child", "kids", "son", "daughter"}
        npc_notes = " ".join(
            (n.notes or "") + " " + (n.bio or "")
            for n in npcs
        ).lower()
        found = dependent_words & set(npc_notes.split())
        if found:
            warnings.append(f"NPC text may contain player-dependent relationship: {found}")

    return warnings


async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> SeedEnvelope:
    """Generate a fresh SeedEnvelope for a dynamic pack.

    Retries up to config.generate_seed_max_retries on parse/validation failure.
    Uses config.generate_seed_temperature (default 0.9) for creative variance.
    """
    if pack.manifest.mode != "dynamic":
        raise ValueError(f"generate_seed() requires a dynamic pack, got mode={pack.manifest.mode!r}")

    template_dir = template_dir or str(Path(__file__).parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    messages = _build_generate_seed_messages(env, pack, overrides)
    messages = trim_messages(messages, config.prompt_token_budget)
    world_facts = parse_world_facts(pack.world_text)

    for attempt in range(1 + config.generate_seed_max_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id, phase=f"generate_seed_request_attempt_{attempt}",
                messages=messages, max_chars=config.log_llm_io_max_chars,
            )
        try:
            result = await llm_chat(
                config.host, config.model, messages,
                temperature=config.generate_seed_temperature,
                timeout=float(config.request_timeout_s),
            )
        except Exception as exc:
            _log.error(
                "generate_seed: LLM error: %s",
                exc,
                extra={"trace_id": trace_id},
            )
            raise
        raw = result.get("response", "") if isinstance(result, dict) else ""
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id, phase=f"generate_seed_response_attempt_{attempt}",
                response=raw, max_chars=config.log_llm_io_max_chars,
            )

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in generate_seed response"
            _log.warning("generate_seed failed (attempt %d): %s", attempt + 1, parse_error,
                         extra={"trace_id": trace_id})
            if attempt < config.generate_seed_max_retries:
                fb = f"Your output failed to parse: {parse_error}. Re-emit a valid SeedEnvelope JSON only."
                messages.append({"role": "user", "content": fb})
            continue

        try:
            # Unwrap if nested under "seed_state" key (expected); also accept bare SeedState
            if "seed_state" not in j and "pc" in j:
                j = {"seed_state": j, "opening_narrative": j.pop("opening_narrative", ".")}
            envelope = SeedEnvelope(**j)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning("generate_seed validation failed (attempt %d): %s", attempt + 1, parse_error,
                         extra={"trace_id": trace_id})
            if attempt < config.generate_seed_max_retries:
                fb = (f"SeedEnvelope validation failed: {parse_error[:300]}. "
                      "Re-emit corrected JSON matching the schema.")
                messages.append({"role": "user", "content": fb})
            continue

        # Inject world facts (non-negotiable canon) at the top of established_facts
        if world_facts:
            existing = list(envelope.seed_state.scene.established_facts)
            merged = world_facts + [f for f in existing if f not in world_facts]
            envelope.seed_state.scene.established_facts = merged

        # Always start with empty compendium and touch order
        envelope.seed_state.compendium.npcs = {}
        if "compendium_touch_order" in envelope.seed_state.meta:
            del envelope.seed_state.meta["compendium_touch_order"]

        soft_warnings = _soft_validate_seed(envelope, pack)
        for w in soft_warnings:
            _log.warning("generate_seed soft-check: %s", w, extra={"trace_id": trace_id})

        return envelope

    raise RuntimeError(f"generate_seed failed after {1 + config.generate_seed_max_retries} attempts — trace {trace_id}")


# ---------------------------------------------------------------------------
# Startup warmup
# ---------------------------------------------------------------------------


async def warmup(config: EngineConfig) -> None:
    """Silent chat call to pre-load the model."""
    try:
        await llm_chat(
            config.host, config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            timeout=30.0,
        )
    except Exception:
        pass
