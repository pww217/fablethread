from __future__ import annotations

from typing import Any


def _detect_npc_ghosting(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect NPC disappearance without departure tracking.

    Ghosting = an NPC that exists in the compendium at turn N, is completely
    missing from the compendium at turn N+1, and has no compendium_npc_update
    entry in this turn's extraction output.

    Presence changes (present→known, present→nearby, present→departed) are NOT
    ghosting — they're tracked in compendium_npc_update and the NPC remains in
    the compendium.

    Returns a list of dicts with keys: turn, left, has_departure_tracking, departure_type.
    """
    prev_npc_ids: set[str] | None = None
    ghosting: list[dict[str, Any]] = []

    for ev in events:
        # Skip side events (condition_expired, sanitizer, etc.) — they have
        # empty state_snapshots and would break the comparison.
        if ev.get("kind"):
            continue

        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        ss = ev.get("state_snapshot") or {}
        compendium = ss.get("compendium") or {}
        npcs = compendium.get("npcs") or {}

        if not isinstance(npcs, dict):
            continue

        current_npc_ids = set(npcs.keys())

        if prev_npc_ids is None:
            prev_npc_ids = current_npc_ids
            continue

        missing = prev_npc_ids - current_npc_ids

        if missing:
            # Check compendium_npc_update in extraction output for departure tracking
            extraction = ev.get("extraction") or {}
            scene_extraction = extraction.get("scene") or {}
            scene_output = scene_extraction.get("output") or {}

            has_departure = False
            departure_type = ""

            if isinstance(scene_output, dict):
                comp_updates = scene_output.get("compendium_npc_update") or []
                if isinstance(comp_updates, list):
                    for cu in comp_updates:
                        if isinstance(cu, dict):
                            cu_id = cu.get("id", "")
                            if cu_id in missing:
                                has_departure = True
                                departure_type = cu.get("presence", "")
                                break

            ghosting.append({
                "turn": t,
                "left": sorted(missing),
                "has_departure_tracking": has_departure,
                "departure_type": departure_type,
            })

        prev_npc_ids = current_npc_ids

    return ghosting


def cmd_state_history(events: list[dict[str, Any]]) -> None:
    """Reconstruct active state (conditions, inventory, NPCs) from applied deltas."""
    # Track active conditions
    active_conditions: list[str] = []
    condition_history: list[dict[str, Any]] = []
    max_concurrent = 0

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        applied = ev.get("applied") or {}

        # Track condition adds/removes
        if applied.get("pc_condition_add"):
            for c in applied["pc_condition_add"]:
                if isinstance(c, dict):
                    active_conditions.append(c["id"])
                    condition_history.append({
                        "turn": t,
                        "kind": "added",
                        "id": c["id"],
                        "label": c.get("label", ""),
                        "active_count": len(active_conditions),
                    })

        if applied.get("pc_condition_remove"):
            for c in applied["pc_condition_remove"]:
                if isinstance(c, dict):
                    active_conditions = [x for x in active_conditions if x != c["id"]]
                    condition_history.append({
                        "turn": t,
                        "kind": "removed",
                        "id": c["id"],
                        "active_count": len(active_conditions),
                    })

        if active_conditions:
            if len(active_conditions) > max_concurrent:
                max_concurrent = len(active_conditions)

    # Track active inventory
    active_inventory: dict[str, int] = {}
    inventory_history: list[dict[str, Any]] = []

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        applied = ev.get("applied") or {}

        if applied.get("inventory_add"):
            for item in applied["inventory_add"]:
                if isinstance(item, dict):
                    iid = item.get("id", "?")
                    qty = item.get("qty", 1)
                    active_inventory[iid] = active_inventory.get(iid, 0) + qty
                    inventory_history.append({
                        "turn": t,
                        "kind": "added",
                        "id": iid,
                        "qty": qty,
                        "total": active_inventory[iid],
                    })

        if applied.get("inventory_remove"):
            for item in applied["inventory_remove"]:
                if isinstance(item, dict):
                    iid = item.get("id", "?")
                    qty = item.get("qty", 1)
                    active_inventory[iid] = max(0, active_inventory.get(iid, 0) - qty)
                    inventory_history.append({
                        "turn": t,
                        "kind": "removed",
                        "id": iid,
                        "qty": qty,
                        "total": active_inventory[iid],
                    })

    # Track NPC ghosting
    npc_ghosting = _detect_npc_ghosting(events)

    # Print results
    print("=== State History ===")
    print()

    # Conditions
    print("--- Conditions ---")
    print(f"Max concurrent: {max_concurrent}")
    print()

    # Condition timeline
    print("Condition timeline:")
    for ch in condition_history:
        action = "+" if ch["kind"] == "added" else "-"
        label = ch.get("label", "")
        if label:
            print(f"  T{ch['turn']}: {action}{ch['id']} ({label}) [{ch['active_count']} active]")
        else:
            print(f"  T{ch['turn']}: {action}{ch['id']} [{ch['active_count']} active]")
    print()

    # Inventory
    print("--- Inventory ---")
    if inventory_history:
        print("Inventory changes:")
        for ih in inventory_history:
            action = "+" if ih["kind"] == "added" else "-"
            print(f"  T{ih['turn']}: {action}{ih['id']} x{ih['qty']} (total: {ih['total']})")
    else:
        print("No inventory changes.")
    print()

    # Final inventory
    if active_inventory:
        print("Final inventory:")
        for iid in sorted(active_inventory.keys()):
            if active_inventory[iid] > 0:
                print(f"  {iid} x{active_inventory[iid]}")
    else:
        print("Final inventory: (empty)")
    print()

    # NPC ghosting
    print("--- NPC Ghosting ---")
    if npc_ghosting:
        print(f"Ghosting events: {len(npc_ghosting)}")
        for ng in npc_ghosting:
            print(f"  T{ng['turn']}: {', '.join(ng['left'])} (no departure tracking)")
    else:
        print("No NPC ghosting detected.")


def cmd_active_conditions(events: list[dict[str, Any]]) -> None:
    """Show max concurrent conditions and per-turn active list."""
    active_conditions: list[str] = []
    turn_conds: dict[int, list[str]] = {}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        applied = ev.get("applied") or {}

        if applied.get("pc_condition_add"):
            for c in applied["pc_condition_add"]:
                if isinstance(c, dict):
                    active_conditions.append(c["id"])

        if applied.get("pc_condition_remove"):
            for c in applied["pc_condition_remove"]:
                if isinstance(c, dict):
                    active_conditions = [x for x in active_conditions if x != c["id"]]

        if active_conditions:
            turn_conds[t] = sorted(active_conditions)

    if not turn_conds:
        print("No condition data found.")
        return

    max_count = max(len(v) for v in turn_conds.values()) if turn_conds else 0

    print("=== Active Conditions ===")
    print(f"Max concurrent: {max_count}")
    print()

    # Table
    print(f"{'Turn':>5} | {'Count':>5} | {'Active Conditions'}")
    print("\u2500" * 70)
    for t in sorted(turn_conds.keys()):
        conds = turn_conds[t]
        count = len(conds)
        cond_str = ", ".join(conds)
        print(f"{t:>5} | {count:>5} | {cond_str}")


def cmd_npc_ghosting(events: list[dict[str, Any]]) -> None:
    """Detect NPC disappearance without departure tracking."""
    ghosting = _detect_npc_ghosting(events)

    if not ghosting:
        print("No NPC ghosting detected.")
        return

    total = len(ghosting)
    bad = sum(1 for g in ghosting if not g["has_departure_tracking"])
    good = total - bad

    print("=== NPC Ghosting ===")
    print(f"Total departures: {total} | Properly tracked: {good} | Ghosting: {bad}")
    print()

    if bad > 0:
        print("Ghosting events (no departure tracking):")
        for g in ghosting:
            if not g["has_departure_tracking"]:
                print(f"  T{g['turn']}: {', '.join(g['left'])}")
        print()

    if good > 0:
        print("Properly tracked departures:")
        for g in ghosting:
            if g["has_departure_tracking"]:
                print(f"  T{g['turn']}: {', '.join(g['left'])} ({g['departure_type']})")


def cmd_storyteller_audit(events: list[dict[str, Any]]) -> None:
    """Check storyteller output format compliance against sanitizer expectations."""
    violations: list[dict[str, Any]] = []
    total_checks = 0

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        extraction = ev.get("extraction") or {}
        storytell = extraction.get("storytell") or {}
        output = storytell.get("output") or {}

        if not isinstance(output, dict):
            continue

        total_checks += 1

        # Check goal_update format
        gu = output.get("goal_update")
        if gu is not None:
            if isinstance(gu, str) and gu.strip():
                # Free-form string — sanitizer requires dict with visible_goal/goal_context
                violations.append({
                    "turn": t,
                    "field": "goal_update",
                    "issue": "free-form string instead of structured dict",
                    "value": gu[:80] + "..." if len(gu) > 80 else gu,
                })
            elif isinstance(gu, dict):
                # Check if it has the required fields
                if not gu.get("visible_goal") and not gu.get("goal_context"):
                    violations.append({
                        "turn": t,
                        "field": "goal_update",
                        "issue": "dict without visible_goal or goal_context",
                        "value": str(gu)[:80],
                    })

        # Check thread_add format
        ta = output.get("thread_add")
        if ta is not None:
            if isinstance(ta, dict):
                if not ta.get("id"):
                    violations.append({
                        "turn": t,
                        "field": "thread_add",
                        "issue": "missing 'id' field",
                        "value": str(ta)[:80],
                    })
            elif not isinstance(ta, list):
                violations.append({
                    "turn": t,
                    "field": "thread_add",
                    "issue": "unexpected type (expected dict or list)",
                    "value": str(ta)[:80],
                })

        # Check gm_beat format
        gb = output.get("gm_beat")
        if gb is not None:
            if isinstance(gb, dict):
                if not gb.get("type"):
                    violations.append({
                        "turn": t,
                        "field": "gm_beat",
                        "issue": "missing 'type' field",
                        "value": str(gb)[:80],
                    })
            elif not isinstance(gb, list):
                violations.append({
                    "turn": t,
                    "field": "gm_beat",
                    "issue": "unexpected type (expected dict or list)",
                    "value": str(gb)[:80],
                })

    if not violations:
        print("No storyteller format violations found.")
        return

    print("=== Storyteller Audit ===")
    print(f"Turns checked: {total_checks} | Violations: {len(violations)}")
    print()

    # Group by field
    by_field: dict[str, list[dict[str, Any]]] = {}
    for v in violations:
        by_field.setdefault(v["field"], []).append(v)

    for field in sorted(by_field.keys()):
        fv = by_field[field]
        print(f"-- {field} ({len(fv)} violations) --")
        for v in fv:
            print(f"  T{v['turn']}: {v['issue']}")
            print(f"    value: {v['value']}")
        print()


def cmd_thread_audit(events: list[dict[str, Any]]) -> None:
    """Cross-reference storyteller thread_add IDs with sanitizer-added IDs."""
    # Gather storyteller thread_add IDs per turn
    storyteller_adds: dict[int, list[str]] = {}
    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue
        extraction = ev.get("extraction") or {}
        storytell = extraction.get("storytell") or {}
        output = storytell.get("output") or {}
        if isinstance(output, dict):
            ta = output.get("thread_add")
            if ta is not None:
                if isinstance(ta, dict) and ta.get("id"):
                    storyteller_adds.setdefault(t, []).append(ta["id"])
                elif isinstance(ta, list):
                    for item in ta:
                        if isinstance(item, dict) and item.get("id"):
                            storyteller_adds.setdefault(t, []).append(item["id"])

    # Gather sanitizer thread_add IDs per turn
    sanitizer_adds: dict[int, list[str]] = {}
    for ev in events:
        if ev.get("kind") != "sanitizer":
            continue
        st = ev.get("turn")
        if st is None or not isinstance(st, int):
            continue
        added = ev.get("threads_added") or []
        if added:
            sanitizer_adds.setdefault(st, []).extend(added)

    # Cross-reference
    mismatches: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []

    for t, sa_ids in sorted(storyteller_adds.items()):
        san_ids = sanitizer_adds.get(t, [])
        for sid in sa_ids:
            if sid in san_ids:
                matches.append({"turn": t, "id": sid, "status": "matched"})
            else:
                mismatches.append({
                    "turn": t,
                    "storyteller_id": sid,
                    "sanitizer_ids": san_ids,
                    "status": "mismatch",
                })

    if not mismatches and not matches:
        print("No thread_add data found in storyteller or sanitizer events.")
        return

    print("=== Thread Audit ===")
    print(f"Storyteller thread_adds: {len(storyteller_adds)} turns | Sanitizer thread_adds: {len(sanitizer_adds)} turns")
    print(f"Matches: {len(matches)} | Mismatches: {len(mismatches)}")
    print()

    if mismatches:
        print("Thread ID mismatches (storyteller ID not found in sanitizer):")
        for m in mismatches:
            print(f"  T{m['turn']}: storyteller='{m['storyteller_id']}' sanitizer={m['sanitizer_ids']}")
        print()

    if matches:
        print("Thread ID matches:")
        for m in matches:
            print(f"  T{m['turn']}: '{m['id']}' ✓")


def cmd_ruling_audit(events: list[dict[str, Any]]) -> None:
    """Check ruling.reason compliance — non-empty, condition IDs present."""
    violations: list[dict[str, Any]] = []
    total_rulings = 0
    empty_reasons = 0

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue

        total_rulings += 1
        reason = ruling.get("reason", "") if isinstance(ruling, dict) else ""

        if not reason or not str(reason).strip():
            empty_reasons += 1
            violations.append({
                "turn": t,
                "issue": "empty ruling.reason",
                "intent": str(ruling.get("intent", ""))[:80] if isinstance(ruling, dict) else "",
            })

        # Check condition IDs in reason
        applied = ev.get("applied") or {}
        if applied.get("pc_condition_add"):
            for c in applied["pc_condition_add"]:
                if isinstance(c, dict):
                    cid = c["id"].lower()
                    if cid not in str(reason).lower():
                        violations.append({
                            "turn": t,
                            "issue": f"condition '{c['id']}' not in ruling.reason",
                            "condition": c["id"],
                            "reason": str(reason)[:80],
                        })

    if not violations:
        print("No ruling compliance violations found.")
        return

    print("=== Ruling Audit ===")
    print(f"Total rulings: {total_rulings} | Empty reasons: {empty_reasons} | Condition ID mismatches: {total_rulings - empty_reasons}")
    print()

    # Group by issue type
    empty = [v for v in violations if v["issue"] == "empty ruling.reason"]
    cond_mismatch = [v for v in violations if v["issue"].startswith("condition")]

    if empty:
        print(f"Empty ruling.reason ({len(empty)} turns):")
        for v in empty:
            intent = v.get("intent", "")
            if intent:
                print(f"  T{v['turn']}: intent='{intent}'")
            else:
                print(f"  T{v['turn']}: (no intent)")
        print()

    if cond_mismatch:
        print(f"Condition IDs missing from ruling.reason ({len(cond_mismatch)}):")
        for v in cond_mismatch:
            reason = v.get("reason", "")
            if reason:
                print(f"  T{v['turn']}: '{v['condition']}' not in reason='{reason}'")
            else:
                print(f"  T{v['turn']}: '{v['condition']}' not in reason=(empty)")
