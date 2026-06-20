from __future__ import annotations

from typing import Any


def cmd_warnings(events: list[dict[str, Any]]) -> None:
    """Show warning signals from event data."""
    rows: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        extract = ev.get("extract") or {}
        retries = extract.get("retries", 0)

        extraction = ev.get("extraction") or {}
        retry_errors: dict[str, int] = {}
        for stream in ("scene", "state", "storytell"):
            s = extraction.get(stream) or {}
            errs = s.get("retry_errors") or []
            if errs:
                retry_errors[stream] = len(errs)

        rejected = ev.get("rejected") or []
        rejected_str = ""
        if rejected:
            items = []
            for r in rejected:
                kind = r.get("kind", "")
                item = r.get("item", r.get("reason", ""))
                items.append(f"{kind}: {item}")
            rejected_str = "; ".join(items)

        reconcile = ev.get("reconcile_warnings") or []
        rec_str = "; ".join(reconcile) if reconcile else ""

        thread_dedup = ev.get("thread_dedup_rejections") or []
        dedup_str = "; ".join(f"T{d.get('turn','?')} {d.get('thread_id','?')} ({d.get('similarity','?')}x)" for d in thread_dedup) if thread_dedup else ""

        compendium_dedup = ev.get("compendium_dedup_redirects") or []
        comp_dedup_str = "; ".join(f"{d.get('original_id','?')} → {d.get('redirected_to','?')}" for d in compendium_dedup) if compendium_dedup else ""

        retry_str = ", ".join(f"{k}: {v}" for k, v in retry_errors.items()) if retry_errors else ""

        rows.append({
            "turn": t,
            "retries": retries,
            "retry_errors": retry_str,
            "rejected": rejected_str or "\u2014",
            "reconcile": rec_str or "\u2014",
            "thread_dedup": dedup_str or "\u2014",
            "compendium_dedup": comp_dedup_str or "\u2014",
        })

    if not rows:
        print("(no events)")
        return

    print(f"{'Turn':>5} | {'Extract.Retries':>15} | {'Retry Errors':<40} | {'Rejected':<30} | {'Reconcile':<30} | {'Thread Dedup':<30} | {'Comp. NPC Dedup':<30}")
    print(f"{'─' * 5}┼{'─' * 17}┼{'─' * 42}┼{'─' * 32}┼{'─' * 32}┼{'─' * 32}┼{'─' * 32}")
    for r in rows:
        print(f"{r['turn']:>5} | {r['retries']:>15} | {r['retry_errors']:<40} | {r['rejected']:<30} | {r['reconcile']:<30} | {r['thread_dedup']:<30} | {r['compendium_dedup']:<30}")

    print()
    print("=== Warnings Gaps ===")
    print("The following warning types are produced but not stored in events:")
    print("  - generate_seed soft-check  → seed.py:421-424 (logged only)")
