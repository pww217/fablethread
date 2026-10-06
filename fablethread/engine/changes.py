"""Change summarization and formatting for UI display."""

from __future__ import annotations

import logging
from typing import Any

from fablethread.models import WorldState


_NOTEBOOK_EMOJI = "📓"
_ARC_EMOJI = "🏁"

_log = logging.getLogger(__name__)


def _summarize_applied(applied: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if not applied:
        return lines
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
    for c in applied.get("pc_condition_add") or []:
        label = c.get("label") or c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"+ {label}")
    for c in applied.get("pc_condition_remove") or []:
        cid = c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"- {cid}")
    for a in applied.get("compendium_npc_add") or []:
        if isinstance(a, dict) and a.get("id"):
            lines.append(f"+ Dossier: {a['id']}")
    for u in applied.get("compendium_npc_update") or []:
        if isinstance(u, dict) and u.get("id"):
            lines.append(f"~ Dossier: {u['id']}")
    loc = applied.get("location_change")
    if isinstance(loc, dict) and (loc.get("name") or loc.get("id")):
        lines.append(f"🗺️ → {loc.get('name') or loc.get('id')}")
    return lines[:18]


def _title_case_id(item_id: str) -> str:
    s = str(item_id or "").replace("_", " ").strip()
    return s.title() if s else "?"


def _inv_amount_map(st: WorldState) -> dict[str, dict[str, Any]]:
    m: dict[str, dict[str, Any]] = {}
    for it in st.inventory:
        if not hasattr(it, "id"):
            continue
        iid = str(getattr(it, "id", "") or "")
        if not iid:
            continue
        m[iid] = {
            "name": str(getattr(it, "name", "") or "").strip(),
            "amount": max(1, int(getattr(it, "amount", 1) or 1)),
        }
    return m


def summarize_changes(
    pre: WorldState,
    post: WorldState,
    rejected: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    _log.debug("summarize_changes pre_turn=%d post_turn=%d", pre.meta.turn, post.meta.turn)
    inventory: list[dict[str, Any]] = []
    player: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []

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

    pre_pc = pre.pc
    post_pc = post.pc
    pre_conds = list(pre_pc.conditions)
    post_conds = list(post_pc.conditions)

    def _cond_id(c: Any) -> str:
        return getattr(c, "id", "") if hasattr(c, "id") else str(c)

    def _cond_label(c: Any) -> str:
        return (getattr(c, "label", "") or getattr(c, "id", "") or "") if hasattr(c, "label") else str(c)

    pre_cond_ids = {_cond_id(c) for c in pre_conds}
    post_cond_ids = {_cond_id(c) for c in post_conds}
    for c in post_conds:
        if _cond_id(c) not in pre_cond_ids:
            player.append({"kind": "condition_added", "value": _cond_label(c)})
    for c in pre_conds:
        if _cond_id(c) not in post_cond_ids:
            player.append({"kind": "condition_removed", "value": _cond_label(c)})

    pl = pre.location
    pr = post.location
    if (pl.id or "") != (pr.id or "") or (pl.name or "") != (pr.name or ""):
        player.append(
            {
                "kind": "location_changed",
                "from": str(pl.name or pl.id or "—"),
                "to": str(pr.name or pr.id or "—"),
            }
        )

    pre_stats = dict(pre_pc.stats) if hasattr(pre_pc, "stats") else {}
    post_stats = dict(post_pc.stats) if hasattr(post_pc, "stats") else {}
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

    pre_ws = list(pre.scene.world_state)
    post_ws = list(post.scene.world_state)
    pre_ws_ids = {f["id"] for f in pre_ws if isinstance(f, dict) and "id" in f}
    post_ws_ids = {f["id"] for f in post_ws if isinstance(f, dict) and "id" in f}
    for fid in post_ws_ids - pre_ws_ids:
        fact = next(f for f in post_ws if isinstance(f, dict) and f.get("id") == fid)
        facts.append({"kind": "added", "value": fact.get("text", fid)})
    for fid in pre_ws_ids - post_ws_ids:
        fact = next(f for f in pre_ws if isinstance(f, dict) and f.get("id") == fid)
        facts.append({"kind": "removed", "value": fact.get("text", fid)})
    for fid in pre_ws_ids & post_ws_ids:
        pre_text = next(f for f in pre_ws if isinstance(f, dict) and f.get("id") == fid).get("text", "")
        post_text = next(f for f in post_ws if isinstance(f, dict) and f.get("id") == fid).get("text", "")
        if pre_text != post_text:
            facts.append({"kind": "updated", "old": pre_text, "new": post_text})

    threads: list[dict[str, Any]] = []
    pre_arc = pre.long_term_objective
    post_arc = post.long_term_objective
    if pre_arc or post_arc:
        pre_t = {t.id: t for t in pre_arc.threads}
        post_t = {t.id: t for t in post_arc.threads}
        pre_c = {t.id: t for t in pre_arc.completed_threads}
        post_c = {t.id: t for t in post_arc.completed_threads}

        all_ids = set(pre_t) | set(post_t) | set(pre_c) | set(post_c)
        for tid in all_ids:
            pr_thread = pre_t.get(tid)
            po_thread = post_t.get(tid)
            pc_thread = post_c.get(tid)

            if pr_thread and not po_thread and not pc_thread:
                threads.append({
                    "kind": "removed",
                    "id": tid,
                    "summary": pr_thread.summary if hasattr(pr_thread, "summary") else "",
                    "urgency": pr_thread.urgency if hasattr(pr_thread, "urgency") else "normal",
                    "detail": "removed",
                })
            elif not pr_thread and po_thread:
                threads.append({
                    "kind": "added",
                    "id": tid,
                    "summary": po_thread.summary if hasattr(po_thread, "summary") else "",
                    "urgency": po_thread.urgency if hasattr(po_thread, "urgency") else "normal",
                })
            elif pr_thread and pc_thread and tid not in pre_c:
                threads.append({
                    "kind": getattr(pc_thread, "resolution_state", "resolved") or "resolved",
                    "id": tid,
                    "summary": pc_thread.summary if hasattr(pc_thread, "summary") else (pr_thread.summary if hasattr(pr_thread, "summary") else ""),
                    "detail": getattr(pc_thread, "outcome", "") or "",
                })
            elif pc_thread and not pr_thread and not po_thread and tid not in pre_c:
                threads.append({
                    "kind": getattr(pc_thread, "resolution_state", "resolved") or "resolved",
                    "id": tid,
                    "summary": pc_thread.summary if hasattr(pc_thread, "summary") else "",
                    "detail": getattr(pc_thread, "outcome", "") or "",
                })
            elif po_thread and pr_thread:
                changes = []
                po_urgency = getattr(po_thread, "urgency", "normal")
                pr_urgency = getattr(pr_thread, "urgency", "normal")
                if po_urgency != pr_urgency:
                    changes.append(f"urgency: {pr_urgency}→{po_urgency}")
                po_dormant = getattr(po_thread, "dormant", False)
                pr_dormant = getattr(pr_thread, "dormant", False)
                if po_dormant != pr_dormant:
                    changes.append("deactivated" if po_dormant else "activated")
                po_summary = getattr(po_thread, "summary", "")
                pr_summary = getattr(pr_thread, "summary", "")
                if po_summary and po_summary != pr_summary:
                    changes.append("summary updated")
                pre_progress = list(getattr(pr_thread, "major_updates", []) or [])
                post_progress = list(getattr(po_thread, "major_updates", []) or [])
                if len(post_progress) < len(pre_progress):
                    changes.append("progress consolidated")
                elif post_progress and pre_progress and post_progress[-1] != pre_progress[-1]:
                    changes.append("progress updated")
                if changes:
                    new_entries = post_progress[len(pre_progress):] if len(post_progress) > len(pre_progress) else []
                    entry: dict[str, Any] = {
                        "kind": "updated",
                        "id": tid,
                        "summary": po_summary,
                        "detail": "; ".join(changes),
                    }
                    if new_entries:
                        progress_texts = [f"{p.get('text') or p}" if isinstance(p, dict) else str(p) for p in new_entries]
                        entry["new_progress"] = "; ".join(progress_texts)
                    threads.append(entry)
        pre_resolved = len(pre.resolved_arcs)
        post_resolved = len(post.resolved_arcs)
        if post_resolved > pre_resolved:
            for ra in post.resolved_arcs[pre_resolved:]:
                if isinstance(ra, dict):
                    threads.append({
                        "kind": "arc_resolved",
                        "id": ra.get("long_term_objective", "?"),
                        "summary": ra.get("long_term_objective", ""),
                        "detail": ra.get("resolution", ""),
                    })

    result = {"inventory": inventory, "player": player, "facts": facts, "threads": threads}
    total = sum(len(v) for v in result.values())
    _log.debug("summarize_changes complete lines=%d", total)
    return result


def format_change_lines(ch: dict[str, Any] | None) -> list[str]:
    if not isinstance(ch, dict):
        _log.debug("format_change_lines received None or non-dict")
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
                "🎒 ⚠ could not remove " + f"({reason})" if reason else "🎒 ⚠ could not remove " + f"“{nm}”"
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
            lines.append(f"🗺️ → {row.get('to')}")
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
    for row in ch.get("threads") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        summary = str(row.get("summary") or row.get("id") or "")
        detail = str(row.get("detail") or "")
        if k == "added":
            lines.append(f"{_NOTEBOOK_EMOJI} + {summary}")
        elif k == "updated":
            new_progress = row.get("new_progress")
            if new_progress:
                lines.append(f"{_NOTEBOOK_EMOJI} + {new_progress}")
            else:
                lines.append(f"{_NOTEBOOK_EMOJI} ↻ {summary} ({detail})")
        elif k == "resolved":
            snippet = f" — {detail}" if detail else ""
            lines.append(f"{_NOTEBOOK_EMOJI} ✓ {summary}{snippet}")
        elif k == "failed":
            snippet = f" — {detail}" if detail else ""
            lines.append(f"{_NOTEBOOK_EMOJI} ✗ {summary}{snippet}")
        elif k == "abandoned":
            lines.append(f"{_NOTEBOOK_EMOJI} ⊘ {summary}")
        elif k == "removed":
            lines.append(f"{_NOTEBOOK_EMOJI} − {summary}{' (' + detail + ')' if detail else ''}")
        elif k == "arc_resolved":
            snippet = f" — {detail}" if detail else ""
            lines.append(f"{_ARC_EMOJI} {summary}{snippet}")
    _log.debug("format_change_lines output=%d", len(lines))
    return lines
