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

        retry_str = ", ".join(f"{k}: {v}" for k, v in retry_errors.items()) if retry_errors else ""

        rows.append({
            "turn": t,
            "retries": retries,
            "retry_errors": retry_str,
            "rejected": rejected_str or "\u2014",
            "reconcile": rec_str or "\u2014",
        })

    if not rows:
        print("(no events)")
        return

    print(f"{'Turn':>5} | {'Extract.Retries':>15} | {'Retry Errors':<40} | {'Rejected':<30} | {'Reconcile Warnings':<30}")
    print(f"{'─' * 5}┼{'─' * 17}┼{'─' * 42}┼{'─' * 32}┼{'─' * 32}")
    for r in rows:
        print(f"{r['turn']:>5} | {r['retries']:>15} | {r['retry_errors']:<40} | {r['rejected']:<30} | {r['reconcile']:<30}")

    print()
    print("=== Warnings Gaps ===")
    print("The following warning types are produced but not stored in events:")
    print("  - generate_seed soft-check  → seed.py:421-424 (logged only)")
    print("  - Thread update dedup       → turn.py:161-168 (logged only)")
    print("  - Compendium NPC dedup      → extraction.py:720-743 (modified silently)")
