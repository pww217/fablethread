"""Turn engine: two-call pipeline (narrate + extract) with reliability measures.

Turn counter source of truth: engine.py only.
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

from ccya.models import (
    IntentEnvelope,
    ProgressExtractResult,
    RulesCheck,
    RulesOutcome,
    Scope,
    SceneExtractResult,
    StateExtractResult,
    StateDelta,
    TurnResult,
)
import ccya.rules as rules_engine
from ccya.pack import (
    ExtractExample,
    Pack,
    PlayerOverrides,
    SeedEnvelope,
    parse_world_facts,
)
from ccya.names import generate_name_pool, generate_npc_names
from ccya.llm_client import (
    apply_thinking,
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.state import (
    append_chronicle,
    append_event,
    apply_delta,
    apply_momentum,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_recent_events,
    load_state,
    reconcile_delta,
    resolve_inventory_remove_target,
    save_state,
)

_log = logging.getLogger("ccya.engine")

# ---------------------------------------------------------------------------
# Per-save turn in-flight guard
# ---------------------------------------------------------------------------


class _EventLock:
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


@dataclass
class EngineConfig:
    host: str = "http://localhost:8080/v1"
    model: str = "mlx-community/Qwen3.6-27B-4bit"
    # Local prompt-token budget for trim_messages (NOT sent to the LLM API —
    # mlx_lm.server has no equivalent of Ollama's num_ctx knob; this just
    # caps how much we pack into a single request).
    prompt_token_budget: int = 32768
    request_timeout_s: int = 180
    narrate_temperature: float = 0.9
    extract_temperature: float = 0.4
    max_extract_retries: int = 1
    window_turns: int = 3
    chronicle_prefix_budget_tokens: int = 1500
    recent_events_max: int = 15
    enable_extract_thinking: bool = False
    enable_narrate_thinking: bool = False
    # generate_seed settings (used by POST /new-game on dynamic packs)
    generate_seed_temperature: float = 0.9
    generate_seed_max_retries: int = 1
    log_llm_io: bool = False
    log_llm_io_max_chars: int = 4000
    rules_temperature: float = 0.2
    max_rules_retries: int = 1
    log_prompts: bool = False
    # Scene pressure urgency escalation thresholds (turns)
    scene_pressure_building_at: int = 6
    scene_pressure_immediate_at: int = 10


def _build_jinja_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )


def _render(env: Environment, template_name: str, ctx: dict[str, Any]) -> str:
    return str(env.get_template(template_name).render(**ctx))


def _narrate_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: list[str] = [],
    last_turn_failed: list[str] = [],
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "last_turn_failed": last_turn_failed,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": state.get("meta", {}),
        "scene": state.get("scene", {}),
    }
    system_text = _render(env, "narrate_system.j2", {"pack_style": pack_style})
    user_text = _render(env, "narrate_user.j2", user_ctx)
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_narrate_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _known_characters_for_extract(
    state: dict[str, Any], *, compact: bool = False
) -> list[dict[str, Any]]:
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
        if compact:
            rows.append({"id": nid, "name": e.get("name") or ""})
        else:
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


def build_state_slice(
    state: dict[str, Any], active_domains: list[str]
) -> dict[str, Any]:
    _HIDDEN = "__HIDDEN__"
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    scene = state.get("scene") or {}

    slice: dict[str, Any] = {
        # Always include these
        "pc_core": {
            "name": pc.get("name", ""),
            "tagline": pc.get("tagline", "") or pc.get("concept", ""),
            "bio": pc.get("bio", ""),
            "stats": pc.get("stats", {}),
        },
        "location": location,
        "present_npcs": list(scene.get("present_npcs") or []),
        "known_characters": _known_characters_for_extract(state),
    }

    # Conditionally include based on active domains
    if "inventory" in active_domains:
        slice["inventory"] = state.get("inventory", [])
    else:
        slice["inventory"] = _HIDDEN

    if "quest_updates" in active_domains:
        slice["active_quests"] = [
            q for q in state.get("quests", []) if q.get("status") == "active"
        ]
    else:
        slice["active_quests"] = _HIDDEN

    if "recent_events" in active_domains:
        slice["recent_events"] = list(scene.get("recent_events") or [])
    else:
        slice["recent_events"] = _HIDDEN

    slice["world_state"] = list(scene.get("world_state") or [])

    if "pc_condition" in active_domains:
        slice["conditions"] = list(pc.get("conditions") or [])
    else:
        slice["conditions"] = _HIDDEN

    return slice


def _summarize_applied(applied: dict[str, Any]) -> list[str]:
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
            amt_raw = it.get("amount")
            if amt_raw is not None:
                lines.append(f"- {rid} (−{amt_raw})")
            else:
                lines.append(f"- {rid} (removed)")
    for it in applied.get("inventory_update") or []:
        if isinstance(it, dict) and it.get("id"):
            lines.append(f"~ {it['id']} updated")
    for f in applied.get("recent_events_add") or []:
        if isinstance(f, dict):
            text = f.get("text") or f.get("id", "?")
            short = str(text)[:56]
            lines.append(f"+ {short}{'…' if len(short) > 56 else ''}")
        elif isinstance(f, str):
            short = f[:56] + ("…" if len(f) > 56 else "")
            lines.append(f"+ {short}")
    for f in applied.get("recent_events_remove") or []:
        if isinstance(f, str):
            short = f[:40] + ("…" if len(f) > 40 else "")
            lines.append(f"- {short}")
    for _upd in applied.get("recent_events_update") or []:
        lines.append("~ Event revised")
    for c in applied.get("pc_condition_add") or []:
        label = c.get("label") or c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"+ {label}")
    for c in applied.get("pc_condition_remove") or []:
        cid = c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"- {cid}")
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
    for p in applied.get("scene_pressure_add") or []:
        if isinstance(p, dict):
            lines.append(f"+ [{p.get('urgency', '?')}] {p.get('text', '?')}")
    for p in applied.get("scene_pressure_update") or []:
        if isinstance(p, dict) and p.get("id"):
            lines.append(f"~ Pressure: {p['id']} updated")
    for rid in applied.get("scene_pressure_remove") or []:
        if isinstance(rid, str):
            lines.append(f"- Pressure: {rid}")
    loc = applied.get("location_change")
    if isinstance(loc, dict) and (loc.get("name") or loc.get("id")):
        lines.append(f"→ {loc.get('name') or loc.get('id')}")
    return lines[:18]


def _title_case_id(item_id: str) -> str:
    s = str(item_id or "").replace("_", " ").strip()
    return s.title() if s else "?"


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
            inventory.append(
                {
                    "kind": "failed_remove",
                    "id": rid,
                    "name": _title_case_id(rid) if rid else "?",
                    "reason": str(r.get("reason") or ""),
                }
            )

    pre_m = _inv_amount_map(pre)
    post_m = _inv_amount_map(post)
    for iid in sorted(
        set(pre_m) | set(post_m), key=lambda x: (0 if x == "credits" else 1, x)
    ):
        a, b = pre_m.get(iid), post_m.get(iid)
        label_a = (a or {}).get("name") or _title_case_id(iid)
        label_b = (b or {}).get("name") or _title_case_id(iid)
        if a and not b:
            inventory.append({"kind": "removed", "id": iid, "name": label_a})
            continue
        if b and not a:
            inventory.append(
                {
                    "kind": "added",
                    "id": iid,
                    "name": label_b,
                    "amount": int(b["amount"]),
                }
            )
            continue
        if a and b:
            amt_a, amt_b = int(a["amount"]), int(b["amount"])
            if label_a != label_b:
                inventory.append(
                    {
                        "kind": "renamed",
                        "id": iid,
                        "from_name": label_a,
                        "to_name": label_b,
                    }
                )
            if amt_b > amt_a:
                inventory.append(
                    {
                        "kind": "increased",
                        "id": iid,
                        "name": label_b,
                        "from": amt_a,
                        "to": amt_b,
                    }
                )
            elif amt_b < amt_a:
                inventory.append(
                    {
                        "kind": "decreased",
                        "id": iid,
                        "name": label_b,
                        "from": amt_a,
                        "to": amt_b,
                    }
                )

    pre_pc = pre.get("pc") or {}
    post_pc = post.get("pc") or {}
    pre_conds = list(pre_pc.get("conditions") or [])
    post_conds = list(post_pc.get("conditions") or [])

    def _cond_id(c: Any) -> str:
        return c.get("id", "") if isinstance(c, dict) else str(c)

    def _cond_label(c: Any) -> str:
        return (c.get("label") or c.get("id") or "") if isinstance(c, dict) else str(c)

    pre_cond_ids = {_cond_id(c) for c in pre_conds}
    post_cond_ids = {_cond_id(c) for c in post_conds}
    for c in post_conds:
        if _cond_id(c) not in pre_cond_ids:
            player.append({"kind": "condition_added", "value": _cond_label(c)})
    for c in pre_conds:
        if _cond_id(c) not in post_cond_ids:
            player.append({"kind": "condition_removed", "value": _cond_label(c)})

    pl = pre.get("location") or {}
    pr = post.get("location") or {}
    if (pl.get("id") or "") != (pr.get("id") or "") or (pl.get("name") or "") != (
        pr.get("name") or ""
    ):
        player.append(
            {
                "kind": "location_changed",
                "from": str(pl.get("name") or pl.get("id") or "—"),
                "to": str(pr.get("name") or pr.get("id") or "—"),
            }
        )

    pre_stats = pre_pc.get("stats") or {}
    post_stats = post_pc.get("stats") or {}
    if isinstance(pre_stats, dict) and isinstance(post_stats, dict):
        for k in sorted(set(pre_stats) | set(post_stats)):
            if pre_stats.get(k) != post_stats.get(k):
                player.append(
                    {
                        "kind": "stat_changed",
                        "stat": str(k),
                        "from": pre_stats.get(k),
                        "to": post_stats.get(k),
                    }
                )

    pre_events = list((pre.get("scene") or {}).get("recent_events") or [])
    post_events = list((post.get("scene") or {}).get("recent_events") or [])
    pre_event_ids = {e["id"] for e in pre_events if isinstance(e, dict)}
    post_event_ids = {e["id"] for e in post_events if isinstance(e, dict)}
    for eid in post_event_ids - pre_event_ids:
        evt = next(e for e in post_events if isinstance(e, dict) and e.get("id") == eid)
        facts.append({"kind": "added", "value": evt.get("text", eid)})
    for eid in pre_event_ids - post_event_ids:
        evt = next(e for e in pre_events if isinstance(e, dict) and e.get("id") == eid)
        facts.append({"kind": "removed", "value": evt.get("text", eid)})
    for eid in pre_event_ids & post_event_ids:
        pre_text = next(e for e in pre_events if isinstance(e, dict) and e.get("id") == eid).get("text", "")
        post_text = next(e for e in post_events if isinstance(e, dict) and e.get("id") == eid).get("text", "")
        if pre_text != post_text:
            facts.append({"kind": "updated", "old": pre_text, "new": post_text})

    pre_q = _quests_by_id(pre)
    post_q = _quests_by_id(post)
    for qid, pq in post_q.items():
        title = str(pq.get("title") or pq.get("id") or qid)
        prq = pre_q.get(qid)
        if prq is None:
            quests.append({"kind": "created", "id": qid, "title": title})
            continue
        st_pre, st_post = (
            str(prq.get("status") or "active"),
            str(pq.get("status") or "active"),
        )
        if st_pre != st_post:
            quests.append(
                {
                    "kind": "status_changed",
                    "id": qid,
                    "title": title,
                    "from": st_pre,
                    "to": st_post,
                }
            )
        po: list[Any] = list(prq.get("objectives") or [])
        qo: list[Any] = list(pq.get("objectives") or [])
        for i in range(max(len(po), len(qo))):
            if i >= len(qo):
                break
            qod = qo[i] if isinstance(qo[i], dict) else {}
            if i >= len(po):
                desc = str(qod.get("description") or "").strip()
                if desc:
                    quests.append(
                        {
                            "kind": "objective_added",
                            "id": qid,
                            "title": title,
                            "objective": desc,
                        }
                    )
                continue
            pod = po[i] if isinstance(po[i], dict) else {}
            if not bool(pod.get("done")) and bool(qod.get("done")):
                quests.append(
                    {
                        "kind": "objective_done",
                        "id": qid,
                        "title": title,
                        "objective": str(qod.get("description") or "").strip(),
                    }
                )
            if not bool(pod.get("failed")) and bool(qod.get("failed")):
                quests.append(
                    {
                        "kind": "objective_failed",
                        "id": qid,
                        "title": title,
                        "objective": str(qod.get("description") or "").strip(),
                    }
                )

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
            lines.append(
                f"🎒 ⚠ could not remove “{nm}”" + (f" ({reason})" if reason else "")
            )
    for row in ch.get("player") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        if k == "condition_added":
            lines.append(f"🩺 + {row.get('value')}")
        elif k == "condition_removed":
            lines.append(f"🩺 − {row.get('value')}")
        elif k == "location_changed":
            lines.append(f"📍 → {row.get('to')}")
        elif k == "stat_changed":
            lines.append(f"🩺 {row.get('stat')}: {row.get('from')} → {row.get('to')}")
    for row in ch.get("facts") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        v = str(row.get("value") or "")
        if k == "added":
            lines.append(f"📜 + {v}")
        elif k == "removed":
            lines.append(f"📜 − {v}")
        elif k == "updated":
            old = str(row.get("old") or "")
            new = str(row.get("new") or "")
            lines.append(f"📜 ↻ {old} → {new}")
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


def _active_domains(intent: "IntentEnvelope | None") -> list[str]:
    scope = intent.scope if intent else Scope()
    return scope.active_domains or [
        "scene",
        "present_npcs",
        "inventory",
        "quest_updates",
        "location_change",
        "recent_events",
        "pc_condition",
    ]


def _scene_npc_roster(
    present_npcs: list[Any], known_characters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build a deduped scene-NPC roster for the scene extractor user prompt.

    Each row is ``{id, name, notes, tags}`` where tags ⊆ {"present", "compendium"}.
    NPCs that appear in both lists merge into a single row with both tags.
    """
    by_id: dict[str, dict[str, Any]] = {}

    def _put(nid: str, name: str, notes: str, tag: str) -> None:
        if not nid:
            return
        row = by_id.setdefault(nid, {"id": nid, "name": "", "notes": "", "tags": []})
        if name and not row["name"]:
            row["name"] = name
        if notes and not row["notes"]:
            row["notes"] = notes
        if tag not in row["tags"]:
            row["tags"].append(tag)

    for n in present_npcs or []:
        if isinstance(n, dict):
            _put(str(n.get("id") or ""), str(n.get("name") or ""), str(n.get("notes") or ""), "present")
        elif isinstance(n, str):
            _put(n, n, "", "present")

    for row in known_characters or []:
        _put(str(row.get("id") or ""), str(row.get("name") or ""), "", "compendium")

    return list(by_id.values())


def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    enable_thinking: bool = False,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (scene + UI hints)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    scene = state.get("scene") or {}
    present_npcs = list(scene.get("present_npcs") or [])
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=True)
    active = _active_domains(intent)
    npc_roster = _scene_npc_roster(present_npcs, known_characters)

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "location": location,
            "conditions": conditions,
            "npc_roster": npc_roster,
            "rules_outcome": rules_outcome,
            "active_domains": active,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    scene_result: "SceneExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    enable_thinking: bool = False,
    pack_examples: list["ExtractExample"] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    active = _active_domains(intent)

    # Cross-stream scene context (minimal surface)
    loc_id = (
        scene_result.location_change.id
        if scene_result.location_change
        else location.get("id", "")
    )
    scene_ctx = {
        "location_id": loc_id,
        "location_changed": bool(scene_result.location_change),
        "present_npcs": [
            {"id": n.id, "name": n.name or n.id}
            for n in scene_result.present_npcs
        ],
    }

    # Filter examples by band (band-scoped extract examples)
    band = rules_outcome.band if rules_outcome and rules_outcome.rolled else ""
    band_examples = [
        ex for ex in (pack_examples or [])
        if not ex.band or ex.band == band
    ]

    system_text = _render(env, "extract_state_system.j2", {})
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "scene_result": scene_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active,
            "band_examples": band_examples,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _quest_threshold_directive(active_quests: list[dict[str, Any]]) -> str:
    """One-line guidance for the progress extractor on whether to start a new quest.

    Computed in Python to keep the system prompt byte-stable; the resulting
    sentence is injected into the user prompt only.
    """
    n = len(active_quests)
    if n == 0:
        return (
            "No active quests. Bar for starting a new quest is LOW — any goal that takes "
            "more than one turn (a journey, errand, finding someone, resolving a conflict, "
            "delivering something) qualifies."
        )
    if n >= 3:
        return (
            f"{n} active quests already. Bar is HIGH — only start a new quest for a major "
            "new obligation clearly distinct from all existing quests."
        )
    return (
        "Start a new quest only if the narration introduces a clear multi-turn goal "
        "distinct from existing quests."
    )


def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    enable_thinking: bool = False,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (quests + facts + compendium)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}
    active = _active_domains(intent)

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])
    known_characters = _known_characters_for_extract(state, compact=False)

    # Cross-stream: minimal surfaces
    scene_ctx = {
        "present_npcs": [
            {"id": n.id, "name": n.name or n.id}
            for n in scene_result.present_npcs
        ],
    }
    state_ctx = {
        "items_gained": [it.name for it in state_result.inventory_add],
        "items_lost": [it.id for it in state_result.inventory_remove],
    }

    system_text = _render(env, "extract_progress_system.j2", {})
    scene_pressure = list((state.get("scene") or {}).get("scene_pressure") or [])
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "active_quests": active_quests,
            "recent_events": recent_events,
            "world_state": world_state,
            "scene_pressure": scene_pressure,
            "known_characters": known_characters,
            "scene_result": scene_ctx,
            "state_result": state_ctx,
            "rules_outcome": rules_outcome,
            "active_domains": active,
            "quest_threshold_directive": _quest_threshold_directive(active_quests),
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _parse_stream_result(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    return model_cls(**j)


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
    for attempt in range(1 + config.max_extract_retries):
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
                1 + config.max_extract_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_extract_retries:
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
    pack_examples: list["ExtractExample"] | None = None,
) -> tuple["StateDelta", list[str], str, list[str], dict[str, Any], "ProgressExtractResult"]:
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, failed, per_stream_event_data, progress_result)
    """
    scope = intent.scope if intent else Scope()
    skip = set(scope.skip_domains or [])

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
    progress_result = ProgressExtractResult()
    extraction_event: dict[str, Any] = {}

    # --- Stream 1: Scene (always runs) ---
    t_scene = asyncio.get_event_loop().time()
    scene_msgs = _extract_scene_messages(
        env, narration, state,
        rules_outcome=rules_outcome, intent=intent,
        enable_thinking=config.enable_extract_thinking,
    )
    scene_msgs = trim_messages(scene_msgs, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_scene", scene_msgs)

    rendered_scene_system = scene_msgs[0]["content"]
    rendered_scene_user = scene_msgs[-1]["content"]

    try:
        scene_result, scene_usage, scene_attempts, scene_retry_errors = await _call_stream(
            scene_msgs, config, trace_id, "extract_scene", SceneExtractResult
        )
        extraction_event["scene"] = {
            "rendered_system": rendered_scene_system,
            "rendered_user": rendered_scene_user,
            "output": scene_result.model_dump(),
            "skipped": False,
            "attempts": scene_attempts,
            "retry_errors": scene_retry_errors,
            "tokens_in": scene_usage.get("prompt_tokens", 0),
            "tokens_out": scene_usage.get("total_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_scene) * 1000, 1),
        }
    except Exception as exc:
        _log.warning("extract_scene failed: %s", exc, extra={"trace_id": trace_id})
        extraction_event["scene"] = {**_SKIPPED, "error": str(exc)}

    # --- Stream 2: State ---
    state_domains = {"inventory", "pc_condition"}
    run_state = not state_domains.issubset(skip)
    if run_state:
        t_state = asyncio.get_event_loop().time()
        state_msgs = _extract_state_messages(
            env, narration, state,
            scene_result=scene_result,
            rules_outcome=rules_outcome, intent=intent,
            enable_thinking=config.enable_extract_thinking,
            pack_examples=pack_examples,
        )
        state_msgs = trim_messages(state_msgs, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(turn_no, "extract_state", state_msgs)

        rendered_state_system = state_msgs[0]["content"]
        rendered_state_user = state_msgs[-1]["content"]

        try:
            state_result, state_usage, state_attempts, state_retry_errors = await _call_stream(
                state_msgs, config, trace_id, "extract_state",
                StateExtractResult, strip_keys=("_reasoning",),
            )
            extraction_event["state"] = {
                "rendered_system": rendered_state_system,
                "rendered_user": rendered_state_user,
                "output": state_result.model_dump(),
                "skipped": False,
                "attempts": state_attempts,
                "retry_errors": state_retry_errors,
                "tokens_in": state_usage.get("prompt_tokens", 0),
                "tokens_out": state_usage.get("total_tokens", 0),
                "ms": round((asyncio.get_event_loop().time() - t_state) * 1000, 1),
            }
        except Exception as exc:
            _log.warning("extract_state failed: %s", exc, extra={"trace_id": trace_id})
            extraction_event["state"] = {**_SKIPPED, "error": str(exc)}
    else:
        _log.debug("Skipping state stream — all state domains in skip_domains")
        extraction_event["state"] = _SKIPPED

    # --- Stream 3: Progress ---
    progress_domains = {"quest_updates", "recent_events", "compendium_npc"}
    run_progress = not progress_domains.issubset(skip)
    if run_progress:
        t_progress = asyncio.get_event_loop().time()
        progress_msgs = _extract_progress_messages(
            env, narration, state,
            scene_result=scene_result,
            state_result=state_result,
            rules_outcome=rules_outcome, intent=intent,
            enable_thinking=config.enable_extract_thinking,
        )
        progress_msgs = trim_messages(progress_msgs, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(turn_no, "extract_progress", progress_msgs)

        rendered_prog_system = progress_msgs[0]["content"]
        rendered_prog_user = progress_msgs[-1]["content"]

        try:
            progress_result, prog_usage, progress_attempts, progress_retry_errors = await _call_stream(
                progress_msgs, config, trace_id, "extract_progress",
                ProgressExtractResult, strip_keys=("_reasoning",),
            )
            extraction_event["progress"] = {
                "rendered_system": rendered_prog_system,
                "rendered_user": rendered_prog_user,
                "output": progress_result.model_dump(),
                "skipped": False,
                "attempts": progress_attempts,
                "retry_errors": progress_retry_errors,
                "tokens_in": prog_usage.get("prompt_tokens", 0),
                "tokens_out": prog_usage.get("total_tokens", 0),
                "ms": round((asyncio.get_event_loop().time() - t_progress) * 1000, 1),
            }
        except Exception as exc:
            _log.warning("extract_progress failed: %s", exc, extra={"trace_id": trace_id})
            extraction_event["progress"] = {**_SKIPPED, "error": str(exc)}
    else:
        _log.debug("Skipping progress stream — all progress domains in skip_domains")
        extraction_event["progress"] = _SKIPPED

    # --- Merge into single StateDelta ---
    merged = StateDelta(
        scene_tags=scene_result.scene_tags,
        scene_tagline=scene_result.scene_tagline,
        location_change=scene_result.location_change,
        location_description=scene_result.location_description,
        present_npcs=scene_result.present_npcs,
        inventory_add=state_result.inventory_add,
        inventory_remove=state_result.inventory_remove,
        inventory_update=state_result.inventory_update,
        pc_condition_add=state_result.pc_condition_add,
        pc_condition_remove=state_result.pc_condition_remove,
        quest_updates=progress_result.quest_updates,
        recent_events_add=progress_result.recent_events_add,
        recent_events_update=progress_result.recent_events_update,
        recent_events_remove=progress_result.recent_events_remove,
        compendium_npc_update=progress_result.compendium_npc_update,
        scene_pressure_add=progress_result.scene_pressure_add,
        scene_pressure_remove=progress_result.scene_pressure_remove,
        scene_pressure_update=progress_result.scene_pressure_update,
    )

    return (
        merged,
        scene_result.actions,
        scene_result.outcome_summary,
        state_result.failed,
        extraction_event,
        progress_result,
    )


def _rules_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    recent_turns: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
    system_text = _render(env, "rules_system.j2", {})
    user_text = _render(
        env,
        "rules_user.j2",
        {
            "pc": pc,
            "location": location,
            "present_npcs": present_npcs,
            "recent_turns": recent_turns or [],
            "user_input": user_input,
        },
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


async def _call_rules(
    messages: list[dict[str, Any]],
    config: EngineConfig,
    trace_id: str,
) -> tuple[IntentEnvelope, dict[str, int], str]:
    _no_intent = IntentEnvelope(
        intent="",
        intent_verb="act",
        check=RulesCheck(required=False),
        scope=Scope(
            active_domains=[
                "scene",
                "present_npcs",
                "inventory",
                "quest_updates",
                "location_change",
                "recent_events",
                "pc_condition",
            ],
            skip_domains=[],
        ),
    )
    _no_usage: dict[str, int] = {"prompt_tokens": 0, "total_tokens": 0}
    parse_error = ""
    for attempt in range(1 + config.max_rules_retries):
        try:
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"rules_request_attempt_{attempt}",
                    messages=messages,
                    max_chars=config.log_llm_io_max_chars,
                )
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.rules_temperature,
                timeout=float(config.request_timeout_s),
            )
            raw = result.get("response", "") if isinstance(result, dict) else ""
            usage = result.get("usage", {}) if isinstance(result, dict) else _no_usage
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"rules_response_attempt_{attempt}",
                    response=raw,
                    max_chars=config.log_llm_io_max_chars,
                )
            cleaned = strip_thinking(raw)
            j = _find_json(cleaned)
            if j is None:
                raise ValueError("No JSON found in rules response")
            return IntentEnvelope(**j), {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }, raw
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "rules parse failed (attempt %d/%d): %s",
                attempt + 1,
                1 + config.max_rules_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_rules_retries:
                fb = (
                    f"Your previous output failed to parse: {parse_error[:200]}. "
                    "Re-emit the IntentEnvelope JSON only. No prose."
                )
                messages.append({"role": "user", "content": fb})

    _log.warning(
        "rules call failed after all attempts — defaulting to no-roll",
        extra={"trace_id": trace_id},
    )
    return _no_intent, _no_usage, ""


def _avg_rules_ms(save_dir: Path, n: int = 5) -> int:
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
            r = (ev.get("rules") or {}).get("total_ms")
            if r is not None:
                times.append(float(r))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    if len(times) < 2:
        return 0
    return int(sum(times) / len(times))


def _find_json(text: str) -> dict[str, Any] | None:
    text = text.strip()

    def _try(t: str) -> dict[str, Any] | None:
        try:
            result = json.loads(t)
            if isinstance(result, dict):
                return result
            return None
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
    messages: list[dict[str, Any]] | None = None,
    response: str | None = None,
    extra: dict[str, Any] | None = None,
    max_chars: int = 4000,
) -> None:
    payload: dict[str, Any] = {"phase": phase, "trace_id": trace_id}
    if messages is not None:
        payload["messages"] = [
            {
                "role": m.get("role"),
                "content": _truncate(m.get("content", ""), max_chars),
            }
            for m in messages
        ]
    if response is not None:
        payload["response"] = _truncate(response, max_chars)
    if extra:
        payload.update(extra)
    _log.debug(
        "llm_io %s", json.dumps(payload, default=str), extra={"trace_id": trace_id}
    )


_PROMPTS_LOG_PATH = Path("logs/prompts.log")


def _log_prompts(turn: int, call: str, messages: list[dict[str, str]]) -> None:
    lines: list[str] = []
    lines.append(f"## Turn {turn} — {call}")
    lines.append("")
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"--- [{role}] ---")
        lines.append(content)
        lines.append("")
    lines.append("---")
    lines.append("")

    try:
        _PROMPTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_PROMPTS_LOG_PATH, "a") as f:
            f.write("\n".join(lines))
    except OSError:
        _log.warning("failed to write prompts.log", exc_info=True)


def _log_rules_outcome(
    turn: int, intent: "IntentEnvelope", outcome: "RulesOutcome"
) -> None:
    lines: list[str] = []
    lines.append(f"## Turn {turn} — rules engine output")
    lines.append("")
    lines.append("--- [Intent] ---")
    lines.append(f"intent:        {intent.intent}")
    lines.append(f"intent_verb:   {intent.intent_verb}")
    lines.append(f"target:        {intent.target}")
    lines.append(f"stakes:        {intent.stakes}")
    lines.append(f"check.required: {intent.check.required}")
    lines.append(f"check.skill:    {intent.check.skill}")
    lines.append(f"check.difficulty: {intent.check.difficulty}")
    lines.append("")
    lines.append("--- [Dice Roll] ---")
    if outcome.rolled:
        lines.append("rolled:       True")
        lines.append(f"skill:        {outcome.skill}")
        lines.append(f"stat_value:   {outcome.stat_value}")
        lines.append(f"stat_mod:     {outcome.stat_mod}")
        lines.append(f"difficulty:   {outcome.difficulty}")
        lines.append(f"diff_mod:     {outcome.diff_mod}")
        lines.append(f"cond_mod:     {outcome.cond_mod}")
        lines.append(f"dice:         {outcome.dice}")
        lines.append(f"raw_total:    {outcome.raw_total}")
        lines.append(f"final_total:  {outcome.final_total}")
        lines.append(f"band:         {outcome.band}")
        lines.append(f"directive:    {outcome.directive}")
    else:
        lines.append("rolled:       False (no dice check required)")
    lines.append("")
    lines.append("---")
    lines.append("")

    try:
        with open(_PROMPTS_LOG_PATH, "a") as f:
            f.write("\n".join(lines))
    except OSError:
        _log.warning("failed to write prompts.log (rules outcome)", exc_info=True)


def _avg_narrate_ms(save_dir: Path, n: int = 5) -> int:
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


def _expire_scene_pressures(
    state: dict[str, Any], delta: StateDelta, config: EngineConfig | None = None
) -> None:
    """Remove expired pressures and escalate urgency based on age.

    Expired = current_turn - turn_added >= max_turns (if set).
    Escalation: background → building at config threshold, building → immediate at config threshold.
    Pressures without a valid turn_added (0 or missing) are skipped — they predate
    this tracking and should not be auto-expired.
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    removed_ids: set[str] = set()
    building_at = 6
    immediate_at = 10
    if config:
        building_at = config.scene_pressure_building_at
        immediate_at = config.scene_pressure_immediate_at

    for p in pressures:
        if not isinstance(p, dict):
            continue
        turn_added = p.get("turn_added")
        # Skip pressures without turn_added — they predate this tracking.
        if turn_added is None or turn_added == 0:
            continue
        max_turns = p.get("max_turns")
        if max_turns is not None and (current_turn - turn_added) >= max_turns:
            removed_ids.add(p.get("id", ""))
            continue
        age = current_turn - turn_added
        urgency = p.get("urgency", "background")
        if age >= immediate_at and urgency == "building":
            p["urgency"] = "immediate"
        elif age >= building_at and urgency == "background":
            p["urgency"] = "building"

    if removed_ids:
        delta.scene_pressure_remove.extend(sorted(removed_ids))


async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_style: str = "",
    pack_examples: list[ExtractExample] | None = None,
    pack_name_locales: list[dict[str, Any]] = [],
) -> AsyncIterator[tuple[str, Any]]:
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    state = load_state(save_dir)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []
    recent_events: list[dict[str, Any]] = []
    intent = IntentEnvelope(
        intent="", intent_verb="act", check=RulesCheck(required=False)
    )
    outcome = RulesOutcome(rolled=False)
    rules_metrics: dict[str, Any] = {"total_ms": 0, "rolled": False}

    try:
        await _inflight.acquire(str(save_dir))

        # Prompt capture variables (initialized early for exception safety)
        rendered_rules_system = ""
        rendered_rules_user = ""
        rendered_narr_system = ""
        rendered_narr_user = ""
        rules_raw_response = ""
        narrative = ""

        # --- Memory: load chronicle tail + recent turns ---
        # chronicle_tail is older history (compressed); recent_turns is the rolling
        # window. Slice the last window_turns from the tail to avoid overlap.
        recent_turns = load_recent_chronicle_turns(save_dir, config.window_turns)
        chronicle_tail = load_chronicle_tail(
            save_dir,
            config.chronicle_prefix_budget_tokens,
            skip_last_n_turns=config.window_turns,
        )

        # Load failed preconditions from the most recent event (for narrate feedback)
        last_events = load_recent_events(save_dir, 1)
        last_turn_failed: list[str] = []
        if last_events:
            last_turn_failed = last_events[0].get("failed", [])

        # === Call 0: Rules / intent classification ===
        exp_rules_ms = _avg_rules_ms(save_dir)
        yield ("phase", {"phase": "rules_start", "expected_ms": exp_rules_ms})
        t_rules = asyncio.get_event_loop().time()

        rules_messages = _rules_messages(
            env, state, user_input, recent_turns=recent_turns[-1:]
        )
        rules_messages = trim_messages(rules_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "rules", rules_messages
            )
        rendered_rules_system = rules_messages[0]["content"] if rules_messages else ""
        rendered_rules_user = rules_messages[-1]["content"] if rules_messages else ""
        intent, rules_usage, rules_raw_response = await _call_rules(rules_messages, config, trace_id)

        # Resolve dice in Python (deterministic) — _call_rules degrades intent, we do outcome here
        if intent.check.required and intent.check.skill:
            try:
                # Normalize structured Condition dicts to ids for the rules engine.
                _pc_conds_struct = list((state.get("pc") or {}).get("conditions") or [])
                _pc_cond_ids = [
                    c.get("id", "") if isinstance(c, dict) else str(c)
                    for c in _pc_conds_struct
                ]
                outcome = rules_engine.resolve_check(
                    skill=intent.check.skill,
                    difficulty=intent.check.difficulty,
                    pc_stats=(state.get("pc") or {}).get("stats") or {},
                    pc_conditions=[cid for cid in _pc_cond_ids if cid],
                    intent_verb=intent.intent_verb,
                    intent=intent.intent,
                )
            except Exception as exc:
                _log.warning(
                    "rules.resolve_check failed: %s", exc, extra={"trace_id": trace_id}
                )
                outcome = RulesOutcome(
                    rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
                )
        else:
            outcome = RulesOutcome(
                rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
            )

        # Apply momentum deterministically from band (never from LLM)
        if outcome.rolled:
            apply_momentum(state, outcome.band)

        if config.log_prompts:
            _log_rules_outcome(
                state.get("meta", {}).get("turn", 0) + 1, intent, outcome
            )

        rules_ms = (asyncio.get_event_loop().time() - t_rules) * 1000
        rules_metrics = {
            "total_ms": round(rules_ms, 1),
            "rolled": outcome.rolled,
            "tokens_in": rules_usage.get("prompt_tokens", 0),
            "tokens_out": rules_usage.get("total_tokens", 0),
        }

        yield (
            "phase",
            {
                "phase": "rules_done",
                "rolled": outcome.rolled,
                "band": outcome.band if outcome.rolled else None,
                "skill": outcome.skill if outcome.rolled else None,
                "dice": outcome.dice if outcome.rolled else [],
                "final_total": outcome.final_total if outcome.rolled else 0,
                "difficulty": outcome.difficulty if outcome.rolled else None,
                "stat_value": outcome.stat_value if outcome.rolled else 0,
                "stat_mod": outcome.stat_mod if outcome.rolled else 0,
                "diff_mod": outcome.diff_mod if outcome.rolled else 0,
                "cond_mod": outcome.cond_mod if outcome.rolled else 0,
                "directive": outcome.directive if outcome.rolled else "",
                "intent_verb": intent.intent_verb,
            },
        )

        # === Call 1: Narrate (streaming) ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Rolling NPC name pool for mid-game cultural anchoring
        _npc_name_pool: list[str] = []
        if pack_name_locales:
            _npc_name_pool = generate_npc_names(
                pack_name_locales,
                count=10,
                seed=state.get("meta", {}).get("turn", 0),
            )

        # Read pending_gm_beat from previous turn's progress extraction
        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")

        narr_messages = _narrate_messages(
            env,
            state,
            user_input,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            last_turn_failed=last_turn_failed,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_gm_beat=_pending_gm_beat,
        )
        narr_messages = trim_messages(narr_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages
            )
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_request",
                messages=narr_messages,
                max_chars=config.log_llm_io_max_chars,
            )
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
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
                trace_id=trace_id,
                phase="narrate_response",
                response=narrative,
                extra={"timing_ms": narr_metrics},
                max_chars=config.log_llm_io_max_chars,
            )

        yield ("phase", {"phase": "narrate_done"})

        # Clear pending_gm_beat after narration consumed it
        state.setdefault("meta", {})["pending_gm_beat"] = None

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        failed: list[str] = []
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, failed, extraction_event, progress_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    pack_examples=pack_examples,
                )
            )
            # Store gm_beat for next turn's narration
            if progress_result and progress_result.gm_beat and progress_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = progress_result.gm_beat.model_dump(exclude_none=True)
            if failed:
                _log.info(
                    "Turn %d: failed preconditions: %s",
                    turn_no,
                    failed,
                    extra={"trace_id": trace_id},
                )
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        yield ("phase", {"phase": "extract_done"})

        # --- Scene pressure: expiry + urgency escalation ---
        if delta is not None:
            _expire_scene_pressures(state, delta, config)

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        # Roll up per-stream token counts for the metrics dict
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "progress")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "progress")
        )
        # Build per-stream breakdown for UI display
        _streams = {}
        for s in ("scene", "state", "progress"):
            ev = extraction_event.get(s)
            if ev:
                _streams[s] = {
                    "ms": ev.get("ms", 0),
                    "tokens_in": ev.get("tokens_in", 0),
                    "tokens_out": ev.get("tokens_out", 0),
                    "skipped": ev.get("skipped", False),
                }
        ext_metrics = {
            "total_ms": round(ext_ms, 1),
            "tokens_in": _tokens_in,
            "tokens_out": _tokens_out,
            "retries": 0,
            "streams": _streams,
        }
        metrics = {
            "rules": rules_metrics,
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        state_pre_apply = copy.deepcopy(state)
        applied: dict[str, Any] = {}
        rejected: list[dict[str, Any]] = []

        if delta is not None:
            rejected = _validate(state, delta)
            blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
            if blocking:
                errors.append(
                    {
                        "trace_id": trace_id,
                        "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
                    }
                )
                narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"
            else:
                reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
                recent_events = list(delta.recent_events_add)
                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

        # Decay recently_left counter (engine-side, not in state.py).
        scene = state.get("scene", {})
        turns = scene.get("recently_left_turns", 0)
        if turns > 0:
            turns -= 1
            if turns == 0:
                scene["recently_left"] = []
            else:
                scene["recently_left_turns"] = turns

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_recent_chronicle_turns).
        rules_event: dict[str, Any] = {
            "intent_verb": intent.intent_verb,
            "intent": intent.intent,
            "rolled": outcome.rolled,
            "total_ms": rules_metrics.get("total_ms"),
            "tokens_in": rules_metrics.get("tokens_in", 0),
            "tokens_out": rules_metrics.get("tokens_out", 0),
        }
        if outcome.rolled:
            rules_event.update({
                "skill": outcome.skill,
                "difficulty": outcome.difficulty,
                "dice": outcome.dice,
                "stat_mod": outcome.stat_mod,
                "diff_mod": outcome.diff_mod,
                "cond_mod": outcome.cond_mod,
                "final_total": outcome.final_total,
                "band": outcome.band,
                "outcome_summary": outcome_summary,
            })

        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "rules": rules_event,
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "changes": changes,
            "failed": failed if failed else [],
            # Prompt logging (for turn viewer)
            "rules_prompt": {
                "rendered_system": rendered_rules_system,
                "rendered_user": rendered_rules_user,
                "output": rules_raw_response,
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {user_input}\n\n{narrative.strip()}",
        )

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            recent_events=recent_events,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            rules=rules_event or {},
            outcome_summary=outcome_summary,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
        fallback = narrative_chunks and "".join(narrative_chunks) or ""
        if not fallback:
            fallback = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        yield (
            "complete",
            TurnResult(
                turn=state.get("meta", {}).get("turn", 0),
                trace_id=trace_id,
                narrative=fallback,
                state_delta={},
                errors=errors,
                metrics=metrics,
                diff=[],
                changes={},
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "value": rem.id,
                    "reason": f"Inventory item '{rem.id}' does not exist",
                }
            )
            continue
        if rem.amount is None:
            continue
        try:
            requested = int(rem.amount)
        except (TypeError, ValueError):
            continue
        if requested <= 0:
            continue
        current = int(inv_by_id.get(canonical, {}).get("amount") or 1)
        if requested > current:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "warn_overdraw",
                    "value": canonical,
                    "requested": requested,
                    "current": current,
                    "reason": (
                        f"Over-draw on '{canonical}': requested {requested} but stack is {current}. "
                        "apply_delta will clamp to a full-stack remove."
                    ),
                }
            )

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    name_pool = generate_name_pool(pack.manifest.name_locales)
    ctx = {
        "world_text": pack.world_text,
        "style_text": pack.style_text,
        "scenario": pack.scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "name_pool": name_pool,
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
    overrides: PlayerOverrides | None = None,
) -> list[str]:
    warnings: list[str] = []
    c = pack.scenario.constraints if pack.scenario else None
    if not c:
        return warnings

    npcs = envelope.seed_state.scene.present_npcs
    named = [n for n in npcs if n.name]
    min_npcs = (
        overrides.npc_count if (overrides and overrides.npc_count > 0) else None
    ) or c.min_named_npcs
    if len(named) < min_npcs:
        warnings.append(f"Only {len(named)} named NPCs (min {min_npcs})")

    words = len(envelope.opening_narrative.split())
    lo, hi = c.prose_word_range
    if not (lo <= words <= hi):
        warnings.append(f"Opening narrative {words} words (expected {lo}-{hi})")

    if c.npc_distinct_first_letters:
        first_letters = [n.name[0].upper() for n in named if n.name]
        if len(first_letters) != len(set(first_letters)):
            warnings.append(
                "NPC names share first letters (npc_distinct_first_letters)"
            )

    text_lower = envelope.opening_narrative.lower()
    for cliche in c.forbid_cliches:
        if cliche.lower() in text_lower:
            warnings.append(f"Opening narrative contains forbidden cliché: '{cliche}'")

    if c.forbid_player_dependents:
        dependent_words = {
            "wife",
            "husband",
            "spouse",
            "child",
            "kids",
            "son",
            "daughter",
        }
        npc_notes = " ".join(
            (n.notes or "") + " " + (n.bio or "") for n in npcs
        ).lower()
        found = dependent_words & set(npc_notes.split())
        if found:
            warnings.append(
                f"NPC text may contain player-dependent relationship: {found}"
            )

    return warnings


async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> SeedEnvelope:
    if pack.manifest.mode != "dynamic":
        raise ValueError(
            f"generate_seed() requires a dynamic pack, got mode={pack.manifest.mode!r}"
        )

    template_dir = template_dir or str(Path(__file__).parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    messages = _build_generate_seed_messages(env, pack, overrides)
    messages = trim_messages(messages, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(0, "generate_seed", messages)
    # Prefer hand-curated baseline_facts on the manifest; fall back to parsing
    # world.md prose (legacy behavior) for packs that haven't been migrated.
    world_facts: list[str] = (
        list(pack.manifest.baseline_facts)
        if pack.manifest.baseline_facts
        else parse_world_facts(pack.world_text)
    )

    for attempt in range(1 + config.generate_seed_max_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_seed_request_attempt_{attempt}",
                messages=messages,
                max_chars=config.log_llm_io_max_chars,
            )
        try:
            result = await llm_chat(
                config.host,
                config.model,
                messages,
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
                trace_id=trace_id,
                phase=f"generate_seed_response_attempt_{attempt}",
                response=raw,
                max_chars=config.log_llm_io_max_chars,
            )

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in generate_seed response"
            _log.warning(
                "generate_seed failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.generate_seed_max_retries:
                fb = f"Your output failed to parse: {parse_error}. Re-emit a valid SeedEnvelope JSON only."
                messages.append({"role": "user", "content": fb})
            continue

        try:
            # Unwrap if nested under "seed_state" key (expected); also accept bare SeedState
            if "seed_state" not in j and "pc" in j:
                j = {
                    "seed_state": j,
                    "opening_narrative": j.pop("opening_narrative", "."),
                }
            envelope = SeedEnvelope(**j)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "generate_seed validation failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.generate_seed_max_retries:
                fb = (
                    f"SeedEnvelope validation failed: {parse_error[:300]}. "
                    "Re-emit corrected JSON matching the schema."
                )
                messages.append({"role": "user", "content": fb})
            continue

        # Inject baseline_facts (hardcoded genre canon) into world_state
        # LLM generates 3 global facts into world_state; prepend baseline_facts
        if world_facts:
            existing_ws = list(envelope.seed_state.scene.world_state)
            merged_ws = world_facts + [f for f in existing_ws if f not in world_facts]
            envelope.seed_state.scene.world_state = merged_ws

        # Always start with empty compendium and touch order
        envelope.seed_state.compendium.npcs = {}
        if "compendium_touch_order" in envelope.seed_state.meta:
            del envelope.seed_state.meta["compendium_touch_order"]

        soft_warnings = _soft_validate_seed(envelope, pack, overrides)
        for w in soft_warnings:
            _log.warning(
                "generate_seed soft-check: %s", w, extra={"trace_id": trace_id}
            )

        return envelope

    raise RuntimeError(
        f"generate_seed failed after {1 + config.generate_seed_max_retries} attempts — trace {trace_id}"
    )


async def warmup(config: EngineConfig) -> None:
    try:
        await llm_chat(
            config.host,
            config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            timeout=30.0,
        )
    except Exception:
        pass
