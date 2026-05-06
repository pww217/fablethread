"""Change summarization and formatting for UI display."""

from __future__ import annotations

from typing import Any


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
