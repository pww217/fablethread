from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from ccya.ev.events import (
    accumulate_intermediate_changes,
    assign_scene_ids,
    extract_field_from_event,
    find_turn,
    is_compaction_event,
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


def _thread_is_dormant(th: dict[str, Any]) -> bool:
    """Check if thread is dormant. Handles old (active) and new (dormant) schemas."""
    if "dormant" in th:
        return bool(th["dormant"])
    if "active" in th:
        return not bool(th["active"])
    return False


def _thread_is_active(th: dict[str, Any]) -> bool:
    return not _thread_is_dormant(th)


def cmd_state(fmt: str = "full", save_dir_path: Path | None = None) -> None:
    if save_dir_path is None:
        print("Error: save directory not specified", file=sys.stderr)
        sys.exit(1)
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
    from ccya.ev.events import is_compaction_event
    filtered = []
    for ev in events:
        if not isinstance(ev.get("turn"), int):
            continue
        t = ev["turn"]
        if from_turn is not None and t < from_turn:
            continue
        if to_turn is not None and t > to_turn:
            continue
        if is_compaction_event(ev):
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


def cmd_threads(events: list[dict[str, Any]], summary: bool = False, include_compaction: bool = False) -> None:
    """Show thread lifecycle across all turns in compact table."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    # Gather thread state at each turn from last_turn_states and sanitizer events
    turn_threads: dict[int, list[dict[str, Any]]] = {}
    seen_turns: set[int] = set()
    all_thread_events: dict[str, dict[str, Any]] = {}  # thread_id -> {created_turn, resolved_turn, updates}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        if t in seen_turns:
            continue

        threads = []
        # From last_turn_state (arc may be under 'arc' or 'long_term_objective')
        ss = ev.get("last_turn_state") or {}
        arc = ss.get("arc") or ss.get("long_term_objective") or {}
        for th in (arc.get("threads") or []):
            if isinstance(th, dict) and th.get("id"):
                threads.append({
                    "id": th["id"],
                    "dormant": _thread_is_dormant(th),
                    "urgency": th.get("urgency", "normal"),
                    "progress": (th.get("major_updates") or [])[-1] if th.get("major_updates") else "",
                })
                tid = th["id"]
                if tid not in all_thread_events:
                    all_thread_events[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}
                if _thread_is_dormant(th) and all_thread_events[tid]["resolved_turn"] is None:
                    all_thread_events[tid]["resolved_turn"] = t

        # Track completed threads (resolved via thread_resolve or arc_resolve)
        for ct in (arc.get("completed_threads") or []):
            if isinstance(ct, dict) and ct.get("id"):
                tid = ct["id"]
                if tid not in all_thread_events:
                    all_thread_events[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}
                if all_thread_events[tid]["resolved_turn"] is None:
                    all_thread_events[tid]["resolved_turn"] = t

        if threads:
            turn_threads[t] = threads
            seen_turns.add(t)

        # From sanitizer events (thread additions/updates/resolves)
        if ev.get("kind") == "sanitizer":
            st = ev.get("turn")
            if st and st not in seen_turns:
                st_threads = []
                for tid in (ev.get("threads_added") or []):
                    st_threads.append({"id": tid, "dormant": False, "urgency": "normal", "progress": "(new)"})
                    if tid not in all_thread_events:
                        all_thread_events[tid] = {"created_turn": st, "resolved_turn": None, "updates": 0}
                for tid in (ev.get("threads_updated") or []):
                    st_threads.append({"id": tid, "dormant": False, "urgency": "(updated)", "progress": ""})
                    if tid in all_thread_events:
                        all_thread_events[tid]["updates"] += 1
                for tid in (ev.get("threads_resolved") or []):
                    if tid in all_thread_events and all_thread_events[tid]["resolved_turn"] is None:
                        all_thread_events[tid]["resolved_turn"] = st
                if st_threads:
                    turn_threads[st] = st_threads
                    seen_turns.add(st)

    if summary:
        created = len(all_thread_events)
        resolved = sum(1 for te in all_thread_events.values() if te["resolved_turn"] is not None)
        hallucinated = sum(1 for te in all_thread_events.values() if te["created_turn"] is None)
        pending = created - resolved - hallucinated
        avg_turns = 0.0
        if resolved > 0:
            total_turns = sum(
                te["resolved_turn"] - te["created_turn"]
                for te in all_thread_events.values()
                if te["resolved_turn"] is not None and te["created_turn"] is not None
            )
            avg_turns = total_turns / resolved

        print("Thread summary:")
        print(f"  Created:   {created}")
        print(f"  Resolved:  {resolved} ({resolved/created*100:.1f}%)" if created else "  Resolved:  0 (0.0%)")
        print(f"  Hallucinated: {hallucinated}")
        print(f"  Pending:   {pending}")
        print(f"  Avg turns to resolve: {avg_turns:.1f}")
        if hallucinated > 0:
            print("\n  Hallucinated threads:")
            for tid, te in all_thread_events.items():
                if te["created_turn"] is None:
                    print(f"    {tid} (first seen T{te.get('resolved_turn', '?')})")
        return

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
                status = "dormant" if th.get("dormant") else "active"
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


def cmd_beats(events: list[dict[str, Any]], include_compaction: bool = False) -> None:
    """Show turn-by-turn beat type + effect status + scene_phase."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    # Gather beat data from storytell extraction and pacing_context
    beat_data: list[dict[str, Any]] = []
    recent_beats_history: dict[int, list[dict[str, Any]]] = {}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        beat_entry = {
            "turn": t,
            "type": "",
            "effect": "",
            "directive": "",
            "phase": "",
            "convergence": None,
            "world_candidates": [],
            "selected_beat": None,
        }

        # From state.meta.pending_gm_beat (moved from record extraction)
        last_state = ev.get("last_turn_state") or {}
        meta = last_state.get("meta") or {}
        pending_gm = meta.get("pending_gm_beat") or {}
        if isinstance(pending_gm, dict) and pending_gm.get("type"):
            beat_entry["type"] = pending_gm.get("type", "")
            beat_entry["effect"] = pending_gm.get("effect", "")

        # From pacing_context in event
        pacing = ev.get("pacing_context") or {}
        if pacing:
            beat_entry["directive"] = pacing.get("directive", "")
            beat_entry["phase"] = pacing.get("scene_phase", "")
            beat_entry["convergence"] = pacing.get("convergence_score")

        # From world extraction: beat candidates generated
        world_output = ((ev.get("extraction") or {}).get("world") or {}).get("output") or []
        if world_output:
            beat_entry["world_candidates"] = world_output

        # From ruling: which beat was selected
        ruling = ev.get("ruling") or {}
        selected = ruling.get("selected_beat")
        if selected is not None:
            beat_entry["selected_beat"] = selected

        beat_data.append(beat_entry)

        # Gather recent_beats from last_turn_state.meta for display
        snap = ev.get("last_turn_state") or {}
        meta = (snap.get("meta") or {})
        recent = meta.get("recent_beats")
        if isinstance(recent, list) and recent:
            recent_beats_history[t] = recent

    # Deduplicate by turn — keep the entry with more data (prefer storytell gm_beat)
    seen_turns: dict[int, dict[str, Any]] = {}
    for bd in beat_data:
        t = bd["turn"]
        if t not in seen_turns:
            seen_turns[t] = bd
        else:
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
    print(f"{'Turn':>5} | {'Phase':<10} | {'Beat Type':<14} | {'Effect':<14} | {'Directive'}")
    print("\u2500" * 74)
    for bd in beat_data:
        directive = bd.get("directive", "")
        phase = bd.get("phase", "")
        print(f"{bd['turn']:>5} | {phase:<10} | {bd.get('type', ''):<14} | {bd.get('effect', ''):<14} | {directive}")

    # Streak analysis — consecutive same-type beats
    streaks: list[dict[str, Any]] = []
    current_type = ""
    current_start = 0
    current_count = 0
    current_turns: list[int] = []

    for bd in beat_data:
        bt = bd.get("type", "")
        if bt == current_type and bt:
            current_count += 1
            current_turns.append(bd["turn"])
        else:
            if current_count >= 3:
                streaks.append({
                    "type": current_type,
                    "start": current_start,
                    "count": current_count,
                    "turns": current_turns,
                })
            current_type = bt
            current_start = bd["turn"]
            current_count = 1
            current_turns = [bd["turn"]]

    if current_count >= 3:
        streaks.append({
            "type": current_type,
            "start": current_start,
            "count": current_count,
            "turns": current_turns,
        })

    if streaks:
        print()
        print("Consecutive streaks (3+ same type):")
        for s in streaks:
            turns_str = ", ".join(str(t) for t in s["turns"])
            print(f"  '{s['type']}' x{s['count']}: turns {turns_str}")

    # Recent beats history per turn (from last_turn_state.meta.recent_beats)
    if recent_beats_history:
        print()
        print("--- recent_beats (from last_turn_state.meta) ---")
        for t in sorted(recent_beats_history.keys()):
            beats = recent_beats_history[t]
            entries = ", ".join(
                f"T{b.get('turn', '?')}:{b.get('type') or '-'}/{b.get('effect') or '-'}"
                for b in beats
            )
            print(f"  Turn {t}: [{entries}]")

    # Full pipeline view: world candidates → ruling selection
    print()
    print("--- Pipeline: world candidates → ruling ---")
    for bd in beat_data:
        t = bd["turn"]
        phase = bd.get("phase", "")
        conv = bd.get("convergence")
        world = bd.get("world_candidates", [])
        selected = bd.get("selected_beat")

        print(f"\nTurn {t} | Phase: {phase or 'N/A'} | Convergence: {conv if conv is not None else 'N/A'}")

        if world:
            print(f"  world candidates ({len(world)}):")
            for i, w in enumerate(world):
                marker = " ← SELECTED" if i == selected else ""
                print(f"    [{i}] {w.get('type', '?')}: {w.get('effect', '')[:80]}{marker}")
        else:
            print("  world candidates: (none)")

        if selected is not None:
            print(f"  ruling.selected_beat: {selected}")
        else:
            print("  ruling.selected_beat: null")


def cmd_goals(events: list[dict[str, Any]], include_compaction: bool = False) -> None:
    """Show goal changes over time from sanitizer events, with extraction fallback."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    goal_changes: list[dict[str, Any]] = []
    sanitizer_turns: set[int] = set()
    for ev in events:
        if ev.get("kind") != "sanitizer":
            continue
        sev_turn = ev.get("turn")
        if sev_turn is None or not isinstance(sev_turn, int):
            continue
        sanitizer_turns.add(sev_turn)
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
                    "source": "sanitizer",
                })

    if not goal_changes:
        print("(no goal changes found)")
        return

    print(f"{'Turn':>5} | Goal Change")
    print("\u2500" * 60)
    for gc in goal_changes:
        if gc["source"] == "extraction" and not gc["before"]:
            print(f"{gc['turn']:>5} | [extraction] \u2192 {gc['after']}")
        else:
            print(f"{gc['turn']:>5} | {gc['before']}")
            if gc["source"] != "extraction" or gc["before"]:
                print(f"      \u2192 {gc['after']}")
        print()


def cmd_effective_age(events: list[dict[str, Any]], include_compaction: bool = False) -> None:
    """Show effective_scene_age over time."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
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


def cmd_beat_ttl(events: list[dict[str, Any]], include_compaction: bool = False) -> None:
    """Show beat TTL expiration over time."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    ttl_data: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        # From pending_gm_beat in last_turn_state or meta
        ss = ev.get("last_turn_state") or {}
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


def _color_red(s: str) -> str:
    return f"\033[91m{s}\033[0m"

def _color_green(s: str) -> str:
    return f"\033[92m{s}\033[0m"


def cmd_convergence(events: list[dict[str, Any]], estimate: bool = False, include_compaction: bool = False, by_scene: bool = False) -> None:
    """Show convergence score + 5 components per turn."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]

    if by_scene:
        _cmd_convergence_by_scene(events, estimate)
        return

    _cmd_convergence_flat(events, estimate)


def _build_convergence_rows(events: list[dict[str, Any]], estimate: bool) -> tuple[list[dict[str, Any]], bool]:
    """Build convergence rows from events. Returns (rows, had_components)."""
    rows: list[dict[str, Any]] = []
    prev_phase = ""
    had_components = False
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        pc = ev.get("pacing_context") or {}
        phase = pc.get("scene_phase", "")
        if not phase:
            continue
        score = pc.get("convergence_score", 0)
        comps = pc.get("convergence_components", {})
        if comps:
            had_components = True

        if estimate and not comps:
            urgent_thread = 0
            threat_thread = 0
            ss = ev.get("last_turn_state") or {}
            arc = ss.get("arc") or {}
            for th in (arc.get("threads") or []):
                if isinstance(th, dict) and not _thread_is_dormant(th):
                    if th.get("urgency") == "urgent":
                        urgent_thread = 1
                    if th.get("type") == "threat":
                        threat_thread = 1

            extraction = ev.get("extraction") or {}
            scene = extraction.get("scene") or {}
            scene_output = scene.get("output") or {}
            scene_age = scene_output.get("effective_scene_age", 0)
            scene_age_component = 1 if scene_age >= 3 else 0

            recent_beats = pc.get("recent_beats", [])
            pressure_types = {"pressure", "complication", "escalation", "setback"}
            pressure_count = sum(1 for b in recent_beats if b.get("type") in pressure_types)
            beat_streak = 1 if pressure_count >= 3 else 0

            roll_starvation = 0  # Would need recent_rolls data; estimated as 0 for EV display
            threat_density = 0   # Would need active threat count; estimated as 0 for EV display

            est_score = urgent_thread + threat_thread + scene_age_component + beat_streak + roll_starvation + threat_density
            comps = {
                "urgent_thread": urgent_thread,
                "threat_thread": threat_thread,
                "scene_age": scene_age_component,
                "beat_streak": beat_streak,
                "roll_starvation": roll_starvation,
                "threat_density": threat_density,
            }
            score = est_score

        rows.append({
            "turn": t,
            "phase": phase,
            "thread": comps.get("urgent_thread", "?"),
            "depth": comps.get("threat_thread", "?"),
            "age": comps.get("scene_age", "?"),
            "beat": comps.get("beat_streak", "?"),
            "roll": comps.get("roll_starvation", "?"),
            "score": score,
            "entry": phase == "CLIMAX" and prev_phase != "CLIMAX",
        })
        prev_phase = phase

    return rows, had_components


def _format_convergence_table(rows: list[dict[str, Any]], had_components: bool, estimate: bool) -> None:
    """Format and print convergence table."""
    if not rows:
        print("(no convergence data)")
        return

    out_lines: list[str] = []
    out_lines.append(f"{'Turn':>5} | {'Phase':<10} | Thread | Depth | Age | Beat | Dice | Score | >=3?")
    out_lines.append(f"{'─' * 5}┼{'─' * 12}┼{'─' * 7}┼{'─' * 6}┼{'─' * 4}┼{'─' * 5}┼{'─' * 5}┼{'─' * 7}┼{'─' * 5}")
    for r in rows:
        marker = " " if not r["entry"] else "\u2192"
        score_ok = r["score"] >= 3
        score_visible = str(r["score"])
        score_padded = score_visible.rjust(5)
        if r["phase"] == "RISING" and not score_ok:
            score_display = _color_red(score_padded)
        elif r["entry"] and score_ok:
            score_display = _color_green(score_padded)
        else:
            score_display = score_padded
        ok_str = f"YES{marker}" if score_ok else "NO "
        out_lines.append(f"{r['turn']:>5} | {r['phase']:<10} |   {r['thread']}    |   {r['depth']}   |  {r['age']}  |  {r['beat']}   |   {r['roll']}  |  {score_display} | {ok_str}")
    if not had_components and not estimate:
        out_lines.append("")
        out_lines.append("[Note: convergence_components not recorded in this save. Use --estimate to retro-compute.]")
    if estimate and not had_components:
        out_lines.append("")
        out_lines.append("[Estimates computed from available event data — may differ from actual components]")
    print("\n".join(out_lines))


def _cmd_convergence_flat(events: list[dict[str, Any]], estimate: bool) -> None:
    """Flat convergence view (original behavior)."""
    rows, had_components = _build_convergence_rows(events, estimate)
    _format_convergence_table(rows, had_components, estimate)


def _cmd_convergence_by_scene(events: list[dict[str, Any]], estimate: bool) -> None:
    """Convergence view grouped by scene."""
    turn_to_scene = assign_scene_ids(events)
    rows, had_components = _build_convergence_rows(events, estimate)

    if not rows:
        print("(no convergence data)")
        return

    # Group rows by scene
    scenes: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        sid = turn_to_scene.get(r["turn"], 0)
        if sid not in scenes:
            scenes[sid] = []
        scenes[sid].append(r)

    for sid in sorted(scenes.keys()):
        scene_rows = scenes[sid]
        first_turn = scene_rows[0]["turn"]
        last_turn = scene_rows[-1]["turn"]
        duration = last_turn - first_turn + 1

        # Count phases
        phase_counts: dict[str, int] = {}
        for r in scene_rows:
            phase_counts[r["phase"]] = phase_counts.get(r["phase"], 0) + 1

        # Count CLIMAX entries
        climax_entries = sum(1 for r in scene_rows if r["entry"])
        climax_scores = [r["score"] for r in scene_rows if r["entry"]]

        print(f"\n--- Scene {sid} (T{first_turn}-T{last_turn}, {duration} turns) ---")
        print(f"  Phases: {', '.join(f'{k}: {v}' for k, v in sorted(phase_counts.items()))}")
        if climax_entries:
            print(f"  CLIMAX entries: {climax_entries} (scores: {', '.join(str(s) for s in climax_scores)})")

        _format_convergence_table(scene_rows, False, False)


def cmd_phase_transitions(events: list[dict[str, Any]], include_compaction: bool = False, by_scene: bool = False) -> None:
    """Detect and display scene phase transitions with triggers."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]

    if by_scene:
        _cmd_phase_transitions_by_scene(events)
        return

    _cmd_phase_transitions_flat(events)


def _build_phase_transitions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build phase transitions from events. Returns list of transition dicts."""
    prev_phase = ""
    transitions: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        pc = ev.get("pacing_context") or {}
        phase = pc.get("scene_phase", "")
        if not phase:
            continue
        if phase != prev_phase and prev_phase:
            transitions.append({
                "turn": t,
                "from": prev_phase,
                "to": phase,
                "convergence_score": pc.get("convergence_score", 0),
                "climax_turn_count": pc.get("climax_turn_count", 0),
                "breather_turn_count": pc.get("breather_turn_count", 0),
                "outcome_hint": pc.get("outcome_hint", ""),
            })
        prev_phase = phase
    return transitions


def _format_transition(tr: dict[str, Any]) -> str:
    """Format a single phase transition for output."""
    parts = [f"convergence_score={tr['convergence_score']}"]
    if tr["climax_turn_count"]:
        parts.append(f"climax_turn_count={tr['climax_turn_count']}")
    if tr["breather_turn_count"]:
        parts.append(f"breather_turn_count={tr['breather_turn_count']}")
    if tr["outcome_hint"]:
        parts.append(f"outcome_hint={tr['outcome_hint']}")
    return f"Turn {tr['turn']}: {tr['from']} \u2192 {tr['to']}   ({', '.join(parts)})"


def _cmd_phase_transitions_flat(events: list[dict[str, Any]]) -> None:
    """Flat phase transitions view (original behavior)."""
    transitions = _build_phase_transitions(events)
    if not transitions:
        print("(no phase transitions detected)")
        return
    for tr in transitions:
        print(_format_transition(tr))


def _cmd_phase_transitions_by_scene(events: list[dict[str, Any]]) -> None:
    """Phase transitions view grouped by scene."""
    turn_to_scene = assign_scene_ids(events)
    transitions = _build_phase_transitions(events)

    if not transitions:
        print("(no phase transitions detected)")
        return

    # Group transitions by scene
    scenes: dict[int, list[dict[str, Any]]] = {}
    for tr in transitions:
        sid = turn_to_scene.get(tr["turn"], 0)
        if sid not in scenes:
            scenes[sid] = []
        scenes[sid].append(tr)

    for sid in sorted(scenes.keys()):
        scene_transitions = scenes[sid]
        first_turn = scene_transitions[0]["turn"]
        last_turn = scene_transitions[-1]["turn"]

        print(f"\n--- Scene {sid} (T{first_turn}-T{last_turn}) ---")
        for tr in scene_transitions:
            print(_format_transition(tr))


def cmd_curtain_call(events: list[dict[str, Any]], include_compaction: bool = False, by_scene: bool = False) -> None:
    """Check Curtain Call compliance for CLIMAX turns."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]

    if by_scene:
        _cmd_curtain_call_by_scene(events)
        return

    _cmd_curtain_call_flat(events)


def _build_curtain_call_results(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build curtain call results from events. Returns list of result dicts."""
    results: list[dict[str, Any]] = []
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        pc = ev.get("pacing_context") or {}
        phase = pc.get("scene_phase", "")
        if phase != "CLIMAX":
            continue

        climax_turn_count = pc.get("climax_turn_count", 0)
        thread_resolve = ev.get("extraction", {}).get("record", {}).get("output", {}).get("thread_resolve", {})
        has_thread_resolve = bool(thread_resolve)
        curtain_call_status = ""
        if climax_turn_count == 1:
            curtain_call_status = "active"
        if climax_turn_count >= pc.get("climax_turn_limit", 4) - 1:
            curtain_call_status = "forced"

        passed = True
        issues: list[str] = []
        if not has_thread_resolve:
            issues.append("missing thread_resolve")
            passed = False

        results.append({
            "turn": t,
            "climax_turn_count": climax_turn_count,
            "curtain_call_status": curtain_call_status,
            "has_thread_resolve": has_thread_resolve,
            "passed": passed,
            "issues": issues,
        })
    return results


def _format_curtain_call_result(r: dict[str, Any]) -> str:
    """Format a single curtain call result for output."""
    status = "PASS" if r["passed"] else "FAIL"
    status_color = "\033[92m" if r["passed"] else "\033[91m"
    cc = f" [{r['curtain_call_status']}]" if r["curtain_call_status"] else ""
    issues_str = ", " + "; ".join(r["issues"]) if r["issues"] else ""
    return f"Turn {r['turn']} (CLIMAX #{r['climax_turn_count']}{cc}): {status_color}{status}\033[0m{issues_str}"


def _cmd_curtain_call_flat(events: list[dict[str, Any]]) -> None:
    """Flat curtain call view (original behavior)."""
    results = _build_curtain_call_results(events)
    if not results:
        print("(no CLIMAX turns in data)")
        return
    for r in results:
        print(_format_curtain_call_result(r))


def _cmd_curtain_call_by_scene(events: list[dict[str, Any]]) -> None:
    """Curtain call view grouped by scene."""
    turn_to_scene = assign_scene_ids(events)
    results = _build_curtain_call_results(events)

    if not results:
        print("(no CLIMAX turns in data)")
        return

    # Group results by scene
    scenes: dict[int, list[dict[str, Any]]] = {}
    for r in results:
        sid = turn_to_scene.get(r["turn"], 0)
        if sid not in scenes:
            scenes[sid] = []
        scenes[sid].append(r)

    for sid in sorted(scenes.keys()):
        scene_results = scenes[sid]
        first_turn = scene_results[0]["turn"]
        last_turn = scene_results[-1]["turn"]

        passed = sum(1 for r in scene_results if r["passed"])
        failed = len(scene_results) - passed

        print(f"\n--- Scene {sid} (T{first_turn}-T{last_turn}) ---")
        print(f"  CLIMAX turns: {len(scene_results)} (PASS: {passed}, FAIL: {failed})")
        for r in scene_results:
            print(_format_curtain_call_result(r))


def cmd_rolls(events: list[dict[str, Any]], summary: bool = False, include_compaction: bool = False) -> None:
    """Show roll bands + raw/final totals per turn."""
    if not include_compaction:
        events = [ev for ev in events if not is_compaction_event(ev)]
    from collections import Counter
    rows: list[dict[str, Any]] = []
    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        rows.append({
            "turn": t,
            "band": ruling.get("band", ""),
            "raw_total": ruling.get("raw_total", ""),
            "final_total": ruling.get("final_total", ""),
        })

    if not rows:
        print("(no dice rolls found)")
        return

    if summary:
        band_counts = Counter(r["band"] for r in rows)
        total = len(rows)
        print(f"Band distribution ({total} rolls):")
        for band in ("crit_fail", "fail", "setback", "partial", "success", "crit_success"):
            count = band_counts.get(band, 0)
            pct = count / total * 100 if total else 0
            print(f"  {band:<14}: {count:>3}  ({pct:.1f}%)")
        bad_total = band_counts.get("crit_fail", 0) + band_counts.get("fail", 0) + band_counts.get("setback", 0)
        bad_pct = bad_total / total * 100 if total else 0
        print(f"  Bad total: {bad_pct:.1f}%")
        return

    print(f"{'Turn':>5} | {'Band':<14} | {'Raw':>5} | {'Final':>5}")
    print("\u2500" * 40)
    for r in rows:
        raw = str(r['raw_total']) if r['raw_total'] is not None else "?"
        final = str(r['final_total']) if r['final_total'] is not None else "?"
        print(f"{r['turn']:>5} | {r['band']:<14} | {raw:>5} | {final:>5}")



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
    session_name = state.get("meta", {}).get("session_name", "")
    if any(scene.get(k) for k in ("tags",)) or session_name:
        _render_scene_section(state)
    arc = state.get("arc") or {}
    if any(arc.get(k) for k in ("long_term_objective", "threads", "completed_threads", "hidden_truths", "discovered_truths")):
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
    conditions = pc.get("conditions", []) or []
    if conditions:
        for c in conditions:
            label = (c.get("label") or c.get("id") or "?") if isinstance(c, dict) else str(c)
            print(f"  Condition: {label}")


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
    phase = scene.get("scene_phase", "SETUP")
    climax_count = scene.get("climax_turn_count", 0)
    breather_count = scene.get("breather_turn_count", 0)
    print(f"  Phase: {phase}  climax_turns={climax_count}  breather_turns={breather_count}")
    tags = scene.get("tags", []) or []
    if tags:
        print(f"  Tags: {', '.join(str(t) for t in tags)}")
    session_name = state.get("meta", {}).get("session_name", "")
    if session_name:
        print(f"  Session: {session_name}")
    compendium = state.get("compendium", {}) or {}
    npcs_comp = compendium.get("npcs", {}) or {}
    present_npcs = {k: v for k, v in npcs_comp.items() if isinstance(v, dict) and v.get("presence") == "present"}
    if present_npcs:
        print("  Present NPCs:")
        for npc_id, npc in sorted(present_npcs.items()):
            name = (npc.get("name") or "[Unnamed]") if isinstance(npc, dict) else "[Unnamed]"
            print(f"    {npc_id}: {name}")


def _render_arc_section(state: dict[str, Any]) -> None:
    arc = state.get("long_term_objective", {}) or {}
    print("--- Arc ---")
    goal = arc.get("long_term_objective") or ""
    if goal:
        print(f"  Goal: {goal}")
    threads = arc.get("threads", []) or []
    active_threads = [t for t in threads if isinstance(t, dict) and _thread_is_active(t)]
    completed = arc.get("completed_threads", []) or []
    discovered = arc.get("discovered_truths", []) or []
    hidden = arc.get("hidden_truths", []) or []
    if active_threads:
        print("  Active threads:")
        for t in active_threads:
            text = (t.get("summary") or t.get("text") or "?") if isinstance(t, dict) else "?"
            progress = t.get("major_updates", []) if isinstance(t, dict) else []
            line = f"    {text}"
            if progress:
                last = progress[-1] if isinstance(progress, list) and progress else ""
                if isinstance(last, dict):
                    last_text = last.get("text", "")
                    if last_text:
                        line += f" ({last_text})"
            print(line)
    if completed:
        comp_names = [f"{(t.get('summary') or t.get('text') or '?')}" for t in completed if isinstance(t, dict)]
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

    elif field == "scene_phase":
        pc = ev.get("pacing_context") or {}
        phase = pc.get("scene_phase", "")
        if op == "eq" and isinstance(value, str) and isinstance(phase, str):
            return phase.lower() == value.lower()
        return False

    elif field.startswith("pacing_context."):
        pc = ev.get("pacing_context") or {}
        subfield = field[len("pacing_context."):]
        result = pc.get(subfield)
        if result is None:
            return False
        if op == "eq":
            return str(result).lower() == str(value).lower()
        elif op == "regex":
            try:
                pattern = re.compile(str(value))
                return bool(pattern.search(str(result)))
            except re.error:
                return False
        elif op == "bool":
            return bool(result)
        return False

    # Generic fallback: dot-notation fields go through extract_field_from_event
    if "." in field:
        from ccya.ev.events import extract_field_from_event
        result = extract_field_from_event(ev, field)
        if result is None:
            return False
        if op == "eq":
            return str(result).lower() == str(value).lower()
        elif op == "regex":
            try:
                pattern = re.compile(str(value))
                return bool(pattern.search(str(result)))
            except re.error:
                return False
        elif op == "bool":
            return bool(result)
        return False

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

    elif field == "rejected":
        return "rejected"

    elif field == "input":
        return None

    return None
