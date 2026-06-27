from __future__ import annotations

from typing import Any

from ccya.ev.events import is_compaction_event


def _try_linear_slope(values: list[float]) -> float | None:
    """Compute linear regression slope for a series. Returns None if too few points."""
    n = len(values)
    if n < 2:
        return None
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return None
    return num / den


def cmd_prompt_sizes(events: list[dict[str, Any]], include_compaction: bool = False) -> None:
    """Show token counts per pipeline stage across turns."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    rows: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        ruling = ev.get("ruling") or {}
        narrate = ev.get("narrate") or {}
        ext = ev.get("extraction") or {}

        row: dict[str, Any] = {"turn": t}
        total_in = 0
        total_out = 0

        row["ruling_in"] = ruling.get("tokens_in", 0)
        row["ruling_out"] = ruling.get("tokens_out", 0)
        total_in += row["ruling_in"]
        total_out += row["ruling_out"]

        row["narr_in"] = narrate.get("tokens_in", 0)
        row["narr_out"] = narrate.get("tokens_out", 0)
        total_in += row["narr_in"]
        total_out += row["narr_out"]

        for stage in ("scene", "state", "record"):
            s = ext.get(stage) or {}
            row[f"{stage}_in"] = s.get("tokens_in", 0)
            row[f"{stage}_out"] = s.get("tokens_out", 0)
            total_in += row[f"{stage}_in"]
            total_out += row[f"{stage}_out"]

        row["total_in"] = total_in
        row["total_out"] = total_out
        rows.append(row)

    if not rows:
        print("(no events)")
        return

    header = f"{'Turn':>5} | {'Ruling_in':>9} | {'Ruling_out':>10} | {'Narr_in':>7} | {'Narr_out':>8} | {'Scene_in':>8} | {'Scene_out':>9} | {'State_in':>8} | {'State_out':>9} | {'Record_in':>10} | {'Record_out':>11} | {'Total_in':>8} | {'Total_out':>9}"
    sep = f"{'─' * 5}┼{'─' * 11}┼{'─' * 12}┼{'─' * 9}┼{'─' * 10}┼{'─' * 10}┼{'─' * 11}┼{'─' * 10}┼{'─' * 11}┼{'─' * 12}┼{'─' * 13}┼{'─' * 10}┼{'─' * 11}"
    print(header)
    print(sep)
    for r in rows:
        print(f"{r['turn']:>5} | {r['ruling_in']:>9} | {r['ruling_out']:>10} | {r['narr_in']:>7} | {r['narr_out']:>8} | {r['scene_in']:>8} | {r['scene_out']:>9} | {r['state_in']:>8} | {r['state_out']:>9} | {r['record_in']:>10} | {r['record_out']:>11} | {r['total_in']:>8} | {r['total_out']:>9}")

    # Growth trend
    print()
    print("Growth trend (tokens/turn):")
    if len(rows) >= 2:
        for col, label in [
            ("ruling_in", "Ruling in"), ("ruling_out", "Ruling out"),
            ("narr_in", "Narr in"), ("narr_out", "Narr out"),
            ("scene_in", "Scene in"), ("scene_out", "Scene out"),
            ("state_in", "State in"), ("state_out", "State out"),
            ("record_in", "Record in"), ("record_out", "Record out"),
            ("total_in", "Total in"), ("total_out", "Total out"),
        ]:
            values = [float(r[col]) for r in rows]
            slope = _try_linear_slope(values)
            if slope is not None:
                direction = "+" if slope > 0 else ""
                print(f"  {label}: {direction}{slope:.1f}/turn")
    else:
        print("  (need at least 2 turns)")
