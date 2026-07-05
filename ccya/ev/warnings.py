from __future__ import annotations

from typing import Any


def cmd_warnings(events: list[dict[str, Any]]) -> None:
    """Show warning signals from event data."""
    by_turn: dict[int, dict[str, Any]] = {}
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        if t not in by_turn:
            by_turn[t] = {
                "turn": t,
                "retries": 0,
                "retry_errors": {},
                "rejected": [],
                "reconcile": [],
                "thread_dedup": [],
                "compendium_dedup": [],
            }
        row = by_turn[t]

        extract = ev.get("extract") or {}
        row["retries"] = max(row["retries"], extract.get("retries", 0))

        extraction = ev.get("extraction") or {}
        for stream in ("scene", "state", "record"):
            s = extraction.get(stream) or {}
            errs = s.get("retry_errors") or []
            if errs:
                row["retry_errors"][stream] = row["retry_errors"].get(stream, 0) + len(errs)

        rejected = ev.get("rejected") or []
        row["rejected"].extend(rejected)

        reconcile = ev.get("reconcile_warnings") or []
        row["reconcile"].extend(reconcile)

        thread_dedup = ev.get("thread_dedup_rejections") or []
        row["thread_dedup"].extend(thread_dedup)

        compendium_dedup = ev.get("compendium_dedup_redirects") or []
        row["compendium_dedup"].extend(compendium_dedup)

    rows = sorted(by_turn.values(), key=lambda r: r["turn"])

    if not rows:
        print("(no events)")
        return

    for r in rows:
        rejected_str = ""
        if r["rejected"]:
            items = []
            for rej in r["rejected"]:
                kind = rej.get("kind", "")
                item = rej.get("item", rej.get("reason", ""))
                items.append(f"{kind}: {item}")
            rejected_str = "; ".join(items)

        reconcile_str = "; ".join(r["reconcile"]) if r["reconcile"] else ""

        thread_dedup_str = "; ".join(f"T{d.get('turn','?')} {d.get('thread_id','?')} ({d.get('similarity','?')}x)" for d in r["thread_dedup"]) if r["thread_dedup"] else ""

        comp_dedup_str = "; ".join(f"{d.get('original_id','?')} → {d.get('redirected_to','?')}" for d in r["compendium_dedup"]) if r["compendium_dedup"] else ""

        retry_str = ", ".join(f"{k}: {v}" for k, v in r["retry_errors"].items()) if r["retry_errors"] else ""

        print(f"{r['turn']:>5} | {r['retries']:>15} | {retry_str:<40} | {rejected_str:<30} | {reconcile_str:<30} | {thread_dedup_str:<30} | {comp_dedup_str:<30}")

    print()
    print("=== Warnings Gaps ===")
    print("The following warning types are produced but not stored in events:")
    print("  - prepare_seed soft-check  → seed.py (no-op, removed cliché check)")
