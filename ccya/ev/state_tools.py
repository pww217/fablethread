from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from ccya.ev.events import (
    accumulate_intermediate_changes,
    extract_field_from_event,
    find_turn,
    load_state_yaml,
)
from ccya.ev.output import (
    _describe_collection_change,
    _shorten_value,
    _trace_display_name,
    _values_equal,
    _wrap_text,
    format_trace_value,
)


def cmd_state(fmt: str = "full", save_dir_path: Path | None = None) -> None:
    state = load_state_yaml(save_dir_path)
    format_state(state, fmt)


def cmd_diff(
    events: list[dict[str, Any]],
    turn_a: int | None,
    turn_b: int | None,
    section_filter: str | None = None,
) -> None:
    if turn_a is None or turn_b is None:
        print("Error: diff requires two turn numbers", file=sys.stderr)
        sys.exit(1)

    if turn_b <= turn_a:
        print(f"Error: turn-B ({turn_b}) must be greater than turn-A ({turn_a})", file=sys.stderr)
        sys.exit(1)

    ev_a = find_turn(events, turn_a)
    if not ev_a:
        print(f"Turn {turn_a} not found (or is a compaction entry)", file=sys.stderr)
        sys.exit(1)

    ev_b = find_turn(events, turn_b)
    if not ev_b:
        print(f"Turn {turn_b} not found", file=sys.stderr)
        sys.exit(1)

    ctx_a = _load_extraction_context(ev_a)
    ctx_b = _load_extraction_context(ev_b)

    has_snapshot_a = ctx_a is not None
    has_snapshot_b = ctx_b is not None

    if not has_snapshot_a or not has_snapshot_b:
        print()
        if not has_snapshot_a:
            print(f"Turn {turn_a}: (no snapshot available \u2014 event predates extraction_context)")
        if not has_snapshot_b:
            print(f"Turn {turn_b}: (no snapshot available \u2014 event predates extraction_context)")

    if ctx_a is not None and ctx_b is not None:
        diff_results = diff_extraction_context(ctx_a, ctx_b)
    else:
        diff_results = []

    intermediate_changes = accumulate_intermediate_changes(events, turn_a, turn_b)

    _format_diff_output(diff_results, intermediate_changes, turn_a, turn_b, section_filter)


def cmd_trace(
    events: list[dict[str, Any]],
    field: str,
    from_turn: int | None = None,
    to_turn: int | None = None,
    show_unchanged: bool = False,
) -> None:
    filtered = []
    for ev in events:
        if not isinstance(ev.get("turn"), int):
            continue
        t = ev["turn"]
        if from_turn is not None and t < from_turn:
            continue
        if to_turn is not None and t > to_turn:
            continue
        filtered.append(ev)

    if not filtered:
        print("(no events in range)")
        return

    found = any(extract_field_from_event(ev, field) is not None for ev in filtered)
    if not found:
        print("Field not tracked per-turn")
        sys.exit(1)
    first_val = extract_field_from_event(filtered[0], field)

    display_name = _trace_display_name(field)

    print(f"trace {field}")
    print()
    col_width = 60
    print(f"{'Turn':>5} | {display_name}")
    print("\u2500" * 5 + "\u2502" + "\u2500" * col_width)

    prev_value = None
    for ev in filtered:
        turn = ev["turn"]
        value = extract_field_from_event(ev, field)
        formatted = format_trace_value(value, field)

        if not show_unchanged and prev_value is not None and _values_equal(prev_value, value):
            print(f"  {turn} | (same)")
        else:
            if prev_value is not None and not _values_equal(prev_value, value) and isinstance(value, list):
                changes = _describe_collection_change(prev_value, value)
                line = f"  {turn} | {formatted}"
                if changes:
                    padding = " " * max(0, col_width - len(formatted))
                    print(line + padding + " \u2190 " + ", ".join(changes[:3]))
                    for extra in changes[3:]:
                        print("     " + (" " * 6) + "\u2190 " + extra)
                else:
                    print(line)
            elif prev_value is not None and not _values_equal(prev_value, value):
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")
            elif prev_value is None and not _values_equal(value, first_val):
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")
            elif prev_value is None and _values_equal(value, first_val):
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")

        prev_value = value


def cmd_search(events: list[dict[str, Any]], expressions: list[str]) -> None:
    queries = [parse_search_expression(expr) for expr in expressions]
    results = search_events(events, queries)

    if not results:
        print("(no matches)")
        return

    for r in results:
        print(f'Turn {r["turn"]}: {r["context_line"]}')
        print(f'  "{r["input_snippet"]}"')
        print()


def cmd_threads(events: list[dict[str, Any]]) -> None:
    """Show thread lifecycle across all turns in compact table."""
    # Gather thread state at each turn from state_snapshots and sanitizer events
    turn_threads: dict[int, list[dict[str, Any]]] = {}
    seen_turns: set[int] = set()

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        if t in seen_turns:
            continue

        threads = []
        # From state_snapshot
        ss = ev.get("state_snapshot") or {}
        arc = ss.get("arc") or {}
        for th in (arc.get("threads") or []):
            if isinstance(th, dict) and th.get("id"):
                threads.append({
                    "id": th["id"],
                    "active": th.get("active", True),
                    "urgency": th.get("urgency", "normal"),
                    "progress": (th.get("progress") or [])[-1] if th.get("progress") else "",
                })

        if threads:
            turn_threads[t] = threads
            seen_turns.add(t)

        # From sanitizer events (thread additions/updates)
        if ev.get("kind") == "sanitizer":
            st = ev.get("turn")
            if st and st not in seen_turns:
                st_threads = []
                for tid in (ev.get("threads_added") or []):
                    st_threads.append({"id": tid, "active": True, "urgency": "normal", "progress": "(new)"})
                for tid in (ev.get("threads_updated") or []):
                    st_threads.append({"id": tid, "active": True, "urgency": "(updated)", "progress": ""})
                if st_threads:
                    turn_threads[st] = st_threads
                    seen_turns.add(st)

    if not turn_threads:
        print("(no thread data found)")
        return

    sorted_turns = sorted(turn_threads.keys())

    # Build thread ID list for columns
    all_thread_ids: set[str] = set()
    for threads in turn_threads.values():
        for th in threads:
            all_thread_ids.add(th["id"])
    thread_ids = sorted(all_thread_ids)

    if not thread_ids:
        print("(no threads)")
        return

    # Print header
    turn_col = max(4, len(str(sorted_turns[-1])))
    header = f"{'Turn':>{turn_col}}"
    for tid in thread_ids:
        header += f"  {tid[:16]:<16}"
    print(header)
    print("\u2500" * len(header))

    # Print rows
    for t in sorted_turns:
        row = f"{t:>{turn_col}}"
        threads_at_turn = {th["id"]: th for th in turn_threads[t]}
        for tid in thread_ids:
            if tid in threads_at_turn:
                th = threads_at_turn[tid]
                status = "active" if th.get("active") else "latent"
                urgency = th.get("urgency", "")
                if isinstance(urgency, str) and urgency not in ("normal", "high", "background"):
                    status = urgency
                progress = th.get("progress", "")
                if progress:
                    row += f"  {status[:3]:<3} {str(progress)[:13]:<13}"
                else:
                    row += f"  {status[:3]:<3} {'':<13}"
            else:
                row += "  " + " " * 16
        print(row)


def cmd_beats(events: list[dict[str, Any]]) -> None:
    """Show turn-by-turn beat type + surface_as + beat_locked status."""
    # Gather beat data from storytell extraction and pacing_context
    beat_data: list[dict[str, Any]] = []

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        beat_entry = {
            "turn": t,
            "type": "",
            "surface": "",
            "beat_locked": False,
            "directive": "",
        }

        # From storytell extraction output
        extraction = ev.get("extraction") or {}
        storytell = extraction.get("storytell") or {}
        st_output = storytell.get("output") or {}
        if isinstance(st_output, dict):
            gm_beat = st_output.get("gm_beat") or {}
            if gm_beat and isinstance(gm_beat, dict) and gm_beat.get("type"):
                beat_entry["type"] = gm_beat.get("type", "")
                beat_entry["surface"] = gm_beat.get("surface_as", "")

        # From pacing_context in event (overrides/adds beat_locked and directive)
        pacing = ev.get("pacing_context") or {}
        if pacing:
            beat_entry["beat_locked"] = pacing.get("beat_locked", False)
            beat_entry["directive"] = pacing.get("directive", "")

        beat_data.append(beat_entry)

    # Deduplicate by turn — keep the entry with more data (prefer storytell gm_beat)
    seen_turns: dict[int, dict[str, Any]] = {}
    for bd in beat_data:
        t = bd["turn"]
        if t not in seen_turns:
            seen_turns[t] = bd
        else:
            # Keep the one with more non-empty fields
            existing = seen_turns[t]
            existing_score = sum(1 for v in existing.values() if v and v is not False)
            new_score = sum(1 for v in bd.values() if v and v is not False)
            if new_score > existing_score:
                seen_turns[t] = bd
    beat_data = sorted(seen_turns.values(), key=lambda x: x["turn"])

    if not beat_data:
        print("(no beat data found)")
        return

    # Print table
    print(f"{'Turn':>5} | {'Beat Type':<14} | {'Surface':<14} | {'Locked':<6} | {'Directive'}")
    print("\u2500" * 70)
    for bd in beat_data:
        locked = "Y" if bd.get("beat_locked") else "N"
        directive = bd.get("directive", "")
        print(f"{bd['turn']:>5} | {bd.get('type', ''):<14} | {bd.get('surface', ''):<14} | {locked:<6} | {directive}")


def cmd_momentum_check(events: list[dict[str, Any]]) -> None:
    """Show momentum + band + expected delta in one table."""
    ARROW = "\u2192"

    rows: list[dict[str, Any]] = []
    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue
        t = ev.get("turn")
        if t is None:
            continue
        momentum_before = ev.get("momentum_before")
        momentum_after = ev.get("momentum_after")
        band = ruling.get("band", "?")
        momentum_delta = ev.get("momentum_delta")

        rows.append({
            "turn": t,
            "momentum_before": momentum_before if momentum_before is not None else "?",
            "momentum_after": momentum_after if momentum_after is not None else "?",
            "delta": momentum_delta if momentum_delta is not None else "?",
            "band": band,
        })

    if not rows:
        print("(no dice rolls found)")
        return

    # Print table
    print(f"{'Turn':>5} | {'Momentum':<12} | {'Band':<10} | {'Delta':<6}")
    print("\u2500" * 40)
    for r in rows:
        mb = r['momentum_before']
        ma = r['momentum_after']
        delta = r['delta']
        delta_str = f"{delta:+d}" if isinstance(delta, int) else str(delta)
        print(f"{r['turn']:>5} | {mb} {ARROW} {ma:<7} | {r['band']:<10} | {delta_str:<6}")


def cmd_goals(events: list[dict[str, Any]]) -> None:
    """Show goal changes over time from sanitizer events."""
    goal_changes: list[dict[str, Any]] = []
    for ev in events:
        if ev.get("kind") != "sanitizer":
            continue
        sev_turn = ev.get("turn")
        changes_detail = ev.get("changes_detail") or {}
        goal = changes_detail.get("goal") or {}
        if goal:
            before = goal.get("before", "")
            after = goal.get("after", "")
            if before != after:
                goal_changes.append({
                    "turn": sev_turn,
                    "before": before,
                    "after": after,
                })

    if not goal_changes:
        print("(no goal changes found)")
        return

    print(f"{'Turn':>5} | Goal Change")
    print("\u2500" * 60)
    for gc in goal_changes:
        print(f"{gc['turn']:>5} | {gc['before']}")
        print(f"      \u2192 {gc['after']}")
        print()


def cmd_effective_age(events: list[dict[str, Any]]) -> None:
    """Show effective_scene_age over time."""
    ages: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        extraction = ev.get("extraction") or {}
        scene = extraction.get("scene") or {}
        scene_output = scene.get("output") or {}
        if isinstance(scene_output, dict):
            age = scene_output.get("effective_scene_age")
            if age is not None:
                ages.append({"turn": t, "age": age})

    if not ages:
        print("(no effective_scene_age data found)")
        return

    print(f"{'Turn':>5} | {'Effective Scene Age':<20}")
    print("\u2500" * 30)
    for a in ages:
        print(f"{a['turn']:>5} | {a['age']}")


def cmd_beat_ttl(events: list[dict[str, Any]]) -> None:
    """Show beat TTL expiration over time."""
    ttl_data: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        # From pending_gm_beat in state_snapshot or meta
        ss = ev.get("state_snapshot") or {}
        meta = ss.get("meta") or {}
        pending_beat = meta.get("pending_gm_beat") or {}
        if pending_beat and pending_beat.get("beat_expires_turn"):
            ttl_data.append({
                "turn": t,
                "expires_at": pending_beat.get("beat_expires_turn"),
                "beat_type": pending_beat.get("type", ""),
            })

        # From post_turn_pending_beat in event
        post_beat = ev.get("post_turn_pending_beat") or {}
        if post_beat and isinstance(post_beat, dict) and post_beat.get("beat_expires_turn"):
            ttl_data.append({
                "turn": t,
                "expires_at": post_beat.get("beat_expires_turn"),
                "beat_type": post_beat.get("type", ""),
            })

    if not ttl_data:
        print("(no beat TTL data found)")
        return

    # Deduplicate by turn — keep the entry with more recent expires_at
    seen_turns: dict[int, dict[str, Any]] = {}
    for td in ttl_data:
        t = td["turn"]
        if t not in seen_turns or td["expires_at"] > seen_turns[t]["expires_at"]:
            seen_turns[t] = td
    ttl_data = sorted(seen_turns.values(), key=lambda x: x["turn"])

    print(f"{'Turn':>5} | {'Expires At':<10} | {'Beat Type'}")
    print("\u2500" * 35)
    for td in ttl_data:
        print(f"{td['turn']:>5} | {td['expires_at']:<10} | {td['beat_type']}")



# Internal helpers


def _load_extraction_context(ev: dict[str, Any]) -> dict[str, Any] | None:
    ctx = ev.get("extraction_context")
    if isinstance(ctx, dict) and ctx:
        return ctx
    return None


def format_state(state: dict[str, Any], fmt: str = "full") -> None:
    turn_num = (state.get("meta") or {}).get("turn", "?")

    if fmt == "compact":
        pc_name = (state.get("pc") or {}).get("name", "?")
        loc_name = (state.get("location") or {}).get("name", "?")
        print(f"Turn {turn_num}: {pc_name} @ {loc_name}")
        return

    if fmt == "pc":
        _render_pc_section(state)
        return
    if fmt == "inventory":
        _render_inventory_section(state)
        return
    if fmt == "location":
        _render_location_section(state)
        return
    if fmt == "scene":
        _render_scene_section(state)
        return
    if fmt == "arc":
        _render_arc_section(state)
        return
    if fmt == "npcs":
        _render_npcs_section(state)
        return
    if fmt == "compidx":
        _render_compidx_section(state)
        return

    print(f"Turn {turn_num}")
    print()
    pc = state.get("pc") or {}
    if pc:
        _render_pc_section(state)
    inv = state.get("inventory")
    if inv:
        _render_inventory_section(state)
    loc = state.get("location")
    if loc:
        _render_location_section(state)
    scene = state.get("scene") or {}
    if any(scene.get(k) for k in ("tags", "tagline")):
        _render_scene_section(state)
    arc = state.get("arc") or {}
    if any(arc.get(k) for k in ("visible_goal", "threads", "completed_threads", "hidden_truths", "discovered_truths")):
        _render_arc_section(state)
    compendium_npcs = (state.get("compendium") or {}).get("npcs")
    if compendium_npcs:
        _render_npcs_section(state)


def _render_pc_section(state: dict[str, Any]) -> None:
    pc = state.get("pc", {})
    print("--- PC ---")
    name = pc.get("name") or "?"
    tagline = pc.get("tagline") or ""
    if tagline:
        print(f"  {name} \u2014 {tagline}")
    else:
        print(f"  {name}")
    stats = pc.get("stats", {})
    if isinstance(stats, dict) and stats:
        stat_parts = ", ".join(f"{k}: {v}" for k, v in sorted(stats.items()))
        print(f"  Stats: {stat_parts}")
    momentum = pc.get("momentum")
    if momentum is not None:
        print(f"  Momentum: {momentum:+d}")
    conditions = pc.get("conditions", []) or []
    if conditions:
        for c in conditions:
            label = (c.get("label") or c.get("id") or "?") if isinstance(c, dict) else str(c)
            ttl = ""
            if isinstance(c, dict):
                remaining = c.get("turns_remaining")
                if remaining is not None:
                    ttl = f" ({remaining} turns left)"
            print(f"  Condition: {label}{ttl}")


def _render_inventory_section(state: dict[str, Any]) -> None:
    inventory = state.get("inventory", []) or []
    print("--- Inventory ---")
    if not inventory:
        print("  (empty)")
        return
    for item in sorted(inventory, key=lambda x: ("0" if isinstance(x, dict) and x.get("id") == "credits" else "1", (x.get("name") or x.get("id") or "").lower())):
        name = (item.get("name") or item.get("id") or "?") if isinstance(item, dict) else str(item)
        amount = item.get("amount", 1) if isinstance(item, dict) else 1
        notes = item.get("notes", "") if isinstance(item, dict) else ""
        line = f"  {name} \u00d7{amount}"
        if notes:
            line += f" ({notes})"
        print(line)


def _render_location_section(state: dict[str, Any]) -> None:
    loc = state.get("location", {}) or {}
    print("--- Location ---")
    name = loc.get("name") or loc.get("id") or "?"
    desc = loc.get("description", "") or ""
    if desc:
        print(f"  {name}")
        for line in _wrap_text(desc, indent=4):
            print(line)
    else:
        print(f"  {name}")


def _render_scene_section(state: dict[str, Any]) -> None:
    scene = state.get("scene", {}) or {}
    print("--- Scene ---")
    tags = scene.get("tags", []) or []
    if tags:
        print(f"  Tags: {', '.join(str(t) for t in tags)}")
    tagline = scene.get("tagline") or ""
    if tagline:
        print(f"  Tagline: {tagline}")
    compendium = state.get("compendium", {}) or {}
    npcs_comp = compendium.get("npcs", {}) or {}
    present_npcs = {k: v for k, v in npcs_comp.items() if isinstance(v, dict) and v.get("presence") == "present"}
    if present_npcs:
        print("  Present NPCs:")
        for npc_id, npc in sorted(present_npcs.items()):
            name = (npc.get("name") or "[Unnamed]") if isinstance(npc, dict) else "[Unnamed]"
            print(f"    {npc_id}: {name}")


def _render_arc_section(state: dict[str, Any]) -> None:
    arc = state.get("arc", {}) or {}
    print("--- Arc ---")
    goal = arc.get("visible_goal") or ""
    if goal:
        print(f"  Goal: {goal}")
    threads = arc.get("threads", []) or []
    active_threads = [t for t in threads if isinstance(t, dict) and t.get("active")]
    completed = arc.get("completed_threads", []) or []
    discovered = arc.get("discovered_truths", []) or []
    hidden = arc.get("hidden_truths", []) or []
    if active_threads:
        print("  Active threads:")
        for t in active_threads:
            text = (t.get("text") or "?") if isinstance(t, dict) else "?"
            progress = t.get("progress", "") if isinstance(t, dict) else ""
            line = f"    {text}"
            if progress:
                line += f" ({progress})"
            print(line)
    if completed:
        comp_names = [f"{(t.get('text') or '?')}" for t in completed if isinstance(t, dict)]
        print("  Completed threads:")
        for cn in comp_names:
            print(f"    {cn}")
    if discovered:
        print("  Discovered truths:")
        for dt in discovered:
            print(f"    - {dt}")
    if hidden:
        print("  Hidden truths (not shown to player):")
        for ht in hidden:
            print(f"    ? {ht}")


def _render_npcs_section(state: dict[str, Any]) -> None:
    compendium = state.get("compendium", {}) or {}
    npcs = compendium.get("npcs", {}) or {}
    if not isinstance(npcs, dict):
        return
    print("--- Compendium NPCs ---")
    for npc_id in sorted(npcs.keys()):
        npc = npcs[npc_id]
        name = (npc.get("name") or "?") if isinstance(npc, dict) else "?"
        title = (npc.get("title") or "") if isinstance(npc, dict) else ""
        line = f"  {npc_id}: {name}"
        if title:
            line += f" \u2014 {title}"
        print(line)


def _render_compidx_section(state: dict[str, Any]) -> None:
    compendium = state.get("compendium", {}) or {}
    npcs = compendium.get("npcs", {}) or {}
    if not isinstance(npcs, dict):
        return
    print("--- NPC Index ---")
    for npc_id in sorted(npcs.keys()):
        npc = npcs[npc_id]
        name = (npc.get("name") or "?") if isinstance(npc, dict) else "?"
        title = (npc.get("title") or "") if isinstance(npc, dict) else ""
        print(f"  {npc_id:<25} {name}{f' ({title})' if title else ''}")


def _diff_inventory(section: str, before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _item_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {(str(item.get("id", ""))): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _item_map(before)
    am = _item_map(after)
    bid_ids = set(bm.keys())
    aid_ids = set(am.keys())

    added = sorted(aid_ids - bid_ids)
    removed = sorted(bid_ids - aid_ids)
    common = bid_ids & aid_ids

    changes = []
    amt_changes = []

    if not added and not removed:
        for iid in common:
            ba = int((bm[iid].get("amount") or 1))
            aa = int((am[iid].get("amount") or 1))
            if ba != aa:
                bname = bm[iid].get("name", "") if isinstance(bm[iid], dict) else ""
                amt_changes.append({"kind": "changed", "label": f"{iid} {bname}: \u00d7{ba} \u2192 \u00d7{aa}"})
        if not amt_changes:
            return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    for iid in added:
        item = am[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"+{iid}"
        if name:
            label += f" {name} \u00d7{amt}"
        changes.append({"kind": "added", "label": label})

    for iid in removed:
        item = bm[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"-{iid}"
        if name:
            label += f" {name} \u00d7{amt}"
        changes.append({"kind": "removed", "label": label})

    changes.extend(amt_changes)

    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": changes}


def _diff_conditions(section: str, before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _cond_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {(str(item.get("id", ""))): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _cond_map(before)
    am = _cond_map(after)
    bid_ids = set(bm.keys())
    aid_ids = set(am.keys())

    added = sorted(aid_ids - bid_ids)
    removed = sorted(bid_ids - aid_ids)

    if not added and not removed:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    changes = []
    for cid in added:
        c = am[cid]
        label = f"+{cid}"
        if isinstance(c, dict):
            lbl = c.get("label") or ""
            if lbl:
                label += f" {lbl}"
        changes.append({"kind": "added", "label": label})

    for cid in removed:
        c = bm[cid]
        label = f"-{cid}"
        if isinstance(c, dict):
            lbl = c.get("label") or ""
            if lbl:
                label += f" {lbl}"
        changes.append({"kind": "removed", "label": label})

    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": changes}


def _diff_location(section: str, before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    if not before and not after:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    b_obj = before[0] if before and isinstance(before[0], dict) else {}
    a_obj = after[0] if after and isinstance(after[0], dict) else {}
    b_id = b_obj.get("id", "")
    b_name = b_obj.get("name", "")
    a_id = a_obj.get("id", "")
    a_name = a_obj.get("name", "")

    if b_id == a_id and b_name == a_name:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    label = f"{b_name or b_id or '?'} \u2192 {a_name or a_id or '?'}"
    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": [{"kind": "changed", "label": label}]}


def _print_unchanged_inventory(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> None:
    def _item_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {(str(item.get("id", ""))): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _item_map(before)
    am = _item_map(after)
    common_ids = sorted(set(bm.keys()) & set(am.keys()))

    if not common_ids:
        print("  (none)")
        return

    for iid in common_ids:
        item = bm[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"{iid}"
        if name:
            label += f" {name} \u00d7{amt}"
        print(f"  {label}")


def _print_unchanged_conditions(items: list[dict[str, Any]]) -> None:
    if not items:
        print("  (none)")
        return
    for item in items:
        if isinstance(item, dict):
            label = f"{item.get('id', '?')}"
            lbl = item.get("label", "") or ""
            if lbl:
                label += f" {lbl}"
            print(f"  {label}")


def _format_diff_output(
    diff_results: list[dict[str, Any]],
    intermediate_changes: list[dict[str, Any]],
    turn_a: int,
    turn_b: int,
    section_filter: str | None = None,
) -> None:
    print(f"diff {turn_a} {turn_b}")

    if not any(r["kind"] == "changed" for r in diff_results):
        if not intermediate_changes:
            print()
            print("(no changes detected between turn {} and turn {})".format(turn_a, turn_b))
            return

    sections_order = ["Inventory", "Conditions", "Location"]
    for expected_section in sections_order:
        if section_filter is not None:
            filter_map = {"npcs": "NPCs", "inventory": "Inventory", "conditions": "Conditions", "location": "Location", "applied": None}
            if filter_map.get(section_filter) != expected_section:
                continue

        matching = [r for r in diff_results if r["section"] == expected_section]
        if not matching:
            continue

        result = matching[0]
        print()
        print(f"--- {expected_section} ---")

        if result["kind"] == "unchanged":
            before_val = result.get("before_value", [])
            after_val = result.get("after_value", [])
            if expected_section == "Inventory":
                _print_unchanged_inventory(before_val, after_val)
            elif expected_section == "Conditions":
                _print_unchanged_conditions(before_val)
            elif expected_section == "Location":
                print("  (unchanged)")

        elif result["kind"] == "changed":
            changes = result.get("changes", [])
            if not changes:
                print("  (no details)")
            else:
                for c in changes:
                    label = c.get("label", "")
                    print(f"  {label}")

    if section_filter != "applied":
        print()
        print("--- Also changed (from applied/changes in intermediate turns) ---")
        if not intermediate_changes:
            print("  (none)")
        else:
            for ic in intermediate_changes:
                field = ic["field"]
                value = str(ic.get("value", ""))[:100]
                turn = ic["turn"]
                if "applied." in field:
                    applied_field = field.replace("applied.", "")
                    print(f"  turn {turn}: {applied_field} \u2192 {_shorten_value(value)}")
                else:
                    changes_field = field.replace("changes.", "")
                    print(f"  turn {turn}: {changes_field} ({_shorten_value(value)})")

    if section_filter is None or section_filter == "not_tracked":
        print()
        print("--- Not tracked in historical snapshots ---")
        print("pc.stats, pc.name, compendium.npcs, arc.threads")


def diff_extraction_context(ctx_a: dict[str, Any], ctx_b: dict[str, Any]) -> list[dict[str, Any]]:
    field_map = {
        "inventory_this_turn": ("Inventory", _diff_inventory),
        "conditions_this_turn": ("Conditions", _diff_conditions),
        "location_this_turn": ("Location", _diff_location),
    }
    results = []
    for key, (section_name, diff_fn) in field_map.items():
        val_a = ctx_a.get(key)
        val_b = ctx_b.get(key)
        if val_a is None:
            val_a = []
        elif not isinstance(val_a, list):
            val_a = [val_a]
        if val_b is None:
            val_b = []
        elif not isinstance(val_b, list):
            val_b = [val_b]
        changed = diff_fn(section_name, val_a, val_b)
        results.append(changed)
    return results


def parse_search_expression(expr: str) -> dict[str, Any]:
    if expr == "rejected":
        return {"field": "rejected", "op": "bool", "value": None}

    if "~" in expr:
        idx = expr.index("~")
        field = expr[:idx]
        value = expr[idx + 1:]
        return {"field": field, "op": "regex", "value": value}

    elif ":" in expr:
        idx = expr.index(":")
        field = expr[:idx]
        value = expr[idx + 1:]
        return {"field": field, "op": "eq", "value": value}

    else:
        print(f"Error: invalid expression '{expr}'. Use format 'field:value' or 'input~regex'.", file=sys.stderr)
        sys.exit(1)


def search_events(events: list[dict[str, Any]], queries: list[dict[str, str]]) -> list[dict[str, Any]]:
    results: dict[int, dict[str, Any]] = {}

    for ev in events:
        if not isinstance(ev.get("turn"), int):
            continue
        turn = ev["turn"]
        ctx = ev.get("extraction_context") or {}
        applied = ev.get("applied") or {}
        ruling_ev = ev.get("ruling") or {}

        matches_all = True
        best_context: str | None = None

        for q in queries:
            field = q["field"]
            op = q["op"]
            value = q["value"]

            if not _match_single_query(ev, ctx, applied, ruling_ev, field, op, value):
                matches_all = False
                break

            ctx_line = _get_context_line(ctx, applied, field, op, value)
            if ctx_line:
                best_context = ctx_line

        if matches_all and queries:
            input_snippet = (ev.get("input") or "")[:80]
            context = best_context or "(match)"
            results[turn] = {
                "turn": turn,
                "context_line": context,
                "input_snippet": input_snippet,
            }

    return [results[t] for t in sorted(results.keys())]


def _match_single_query(
    ev: dict[str, Any],
    ctx: dict[str, Any],
    applied: dict[str, Any],
    ruling_ev: dict[str, Any],
    field: str,
    op: str,
    value: str | None,
) -> bool:
    if field == "npc":
        updates = applied.get("compendium_npc_update", []) or []
        return any(isinstance(m, dict) and m.get("id") == value for m in updates)

    elif field == "item":
        items = ctx.get("inventory_this_turn", []) or []
        has_presence = any(isinstance(i, dict) and i.get("id") == value for i in items)

        has_mutation = False
        for mut_field in ("inventory_add", "inventory_remove", "inventory_update"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                has_mutation = True
                break

        return has_presence or has_mutation

    elif field == "condition":
        conds = ctx.get("conditions_this_turn", []) or []
        has_presence = any(isinstance(c, dict) and c.get("id") == value for c in conds)

        has_mutation = False
        for mut_field in ("pc_condition_add", "pc_condition_remove"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                has_mutation = True
                break

        return has_presence or has_mutation

    elif field == "band":
        band_val = ruling_ev.get("band", "")
        if op == "eq" and isinstance(value, str):
            return bool(band_val == value)
        return False

    elif field == "momentum_after":
        mom = ev.get("momentum_after")
        if mom is None:
            return False
        try:
            return bool(mom is not None and value is not None and int(mom) == int(value))
        except (ValueError, TypeError):
            return False

    elif field == "momentum_before":
        mom = ev.get("momentum_before")
        if mom is None:
            return False
        try:
            return bool(mom is not None and value is not None and int(mom) == int(value))
        except (ValueError, TypeError):
            return False

    elif field == "momentum_delta":
        delta = ev.get("momentum_delta")
        if delta is None:
            return False
        try:
            return bool(delta is not None and value is not None and int(delta) == int(value))
        except (ValueError, TypeError):
            return False

    elif field == "rejected":
        return bool(ev.get("rejected"))

    elif field == "input":
        if op != "regex" or not isinstance(value, str):
            return False
        try:
            pattern = re.compile(value)
            return bool(pattern.search(ev.get("input", "") or ""))
        except re.error:
            print(f"Error: invalid regex '{value}'", file=sys.stderr)
            sys.exit(1)

    return False


def _get_context_line(
    ctx: dict[str, Any],
    applied: dict[str, Any],
    field: str,
    op: str,
    value: str | None,
) -> str | None:
    if field == "npc":
        updates = applied.get("compendium_npc_update", []) or []
        for m in updates:
            if isinstance(m, dict) and m.get("id") == value:
                return f"compendium_npc_update {value}"
        return None

    elif field == "item":
        items = ctx.get("inventory_this_turn", []) or []
        has_presence = any(isinstance(i, dict) and i.get("id") == value for i in items)

        for mut_field in ("inventory_add", "inventory_remove", "inventory_update"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                return f"{mut_field} {value}"

        if has_presence:
            return "(present in inventory)"
        return None

    elif field == "condition":
        conds = ctx.get("conditions_this_turn", []) or []
        has_presence = any(isinstance(c, dict) and c.get("id") == value for c in conds)

        for mut_field in ("pc_condition_add", "pc_condition_remove"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                return f"{mut_field} {value}"

        if has_presence:
            return "(active condition)"
        return None

    elif field == "band":
        return f"band={value}" if value else "(match)"

    elif field == "momentum_after":
        return f"momentum_after={value}"

    elif field == "momentum_before":
        return f"momentum_before={value}"

    elif field == "momentum_delta":
        return f"momentum_delta={value}"

    elif field == "rejected":
        return "rejected"

    elif field == "input":
        return None

    return None
