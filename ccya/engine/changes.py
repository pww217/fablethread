"""Change summarization and formatting for UI display."""

from __future__ import annotations

import logging
from typing import Any


_log = logging.getLogger(__name__)


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
    for c in applied.get("pc_condition_add") or []:
        label = c.get("label") or c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"+ {label}")
    for c in applied.get("pc_condition_remove") or []:
        cid = c.get("id") or str(c) if isinstance(c, dict) else str(c)
        lines.append(f"- {cid}")
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


def summarize_changes(
    pre: dict[str, Any],
    post: dict[str, Any],
    _applied: dict[str, Any],
    rejected: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    _log.debug("summarize_changes pre_keys=%d post_keys=%d", len(pre), len(post))
    inventory: list[dict[str, Any]] = []
    player: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    momentum: list[dict[str, Any]] = []

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

    pre_momentum = pre.get("pc", {}).get("momentum", 0)
    post_momentum = post.get("pc", {}).get("momentum", 0)
    if pre_momentum != post_momentum:
        momentum.append({
            "kind": "momentum_changed",
            "before": pre_momentum,
            "after": post_momentum,
            "delta": post_momentum - pre_momentum,
        })

    result = {"inventory": inventory, "player": player, "facts": facts, "momentum": momentum}
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
    for row in ch.get("momentum") or []:
        if not isinstance(row, dict):
            continue
        k = row.get("kind")
        if k == "momentum_changed":
            b, a = row.get("before", 0), row.get("after", 0)
            lines.append(f"⚡ Momentum {b:+d} → {a:+d}")
    _log.debug("format_change_lines output=%d", len(lines))
    return lines
