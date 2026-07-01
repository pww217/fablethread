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
        # Skip side events (sanitizer, etc.) — they have
        # empty last_turn_states and would break the comparison.
        if ev.get("kind"):
            continue

        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        ss = ev.get("last_turn_state") or {}
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
    turn_conds: dict[int, list[str]] = {}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        # Read conditions from last_turn_state (accounts for TTL expiration)
        last_state = ev.get("last_turn_state") or {}
        pc = last_state.get("pc") or {}
        conditions = pc.get("conditions") or []
        
        if conditions:
            turn_conds[t] = sorted([c["id"] for c in conditions if isinstance(c, dict)])

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
    """Check record output format compliance against sanitizer expectations."""
    violations: list[dict[str, Any]] = []
    total_checks = 0

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        extraction = ev.get("extraction") or {}
        record = extraction.get("record") or {}
        output = record.get("output") or {}

        if not isinstance(output, dict):
            continue

        total_checks += 1

        # Check thread_update format
        tu = output.get("thread_update")
        if tu is not None:
            if not isinstance(tu, list):
                violations.append({
                    "turn": t,
                    "field": "thread_update",
                    "issue": "unexpected type (expected list)",
                    "value": str(tu)[:80],
                })
            else:
                for item in tu:
                    if isinstance(item, dict) and not item.get("id"):
                        violations.append({
                            "turn": t,
                            "field": "thread_update",
                            "issue": "missing 'id' field in thread_update item",
                            "value": str(item)[:80],
                        })

        # Check thread_resolve format
        tr = output.get("thread_resolve")
        if tr is not None:
            if not isinstance(tr, list):
                violations.append({
                    "turn": t,
                    "field": "thread_resolve",
                    "issue": "unexpected type (expected list)",
                    "value": str(tr)[:80],
                })

        # Check actions format
        actions = output.get("actions")
        if actions is not None:
            if not isinstance(actions, list):
                violations.append({
                    "turn": t,
                    "field": "actions",
                    "issue": "unexpected type (expected list)",
                    "value": str(actions)[:80],
                })

    if not violations:
        print("No record format violations found.")
        return

    print("=== Record Audit ===")
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


def cmd_thread_audit(events: list[dict[str, Any]]) -> None:
    """Audit thread lifecycle: creation, updates, resolution, and orphan detection."""
    violations: list[dict[str, Any]] = []
    thread_lifecycle: dict[str, dict[str, Any]] = {}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        # From sanitizer events
        if ev.get("kind") == "sanitizer":
            for tid in (ev.get("threads_added") or []):
                if tid not in thread_lifecycle:
                    thread_lifecycle[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}
                else:
                    violations.append({
                        "turn": t,
                        "thread_id": tid,
                        "issue": "thread_added_but_already_exists",
                    })

            for tid in (ev.get("threads_updated") or []):
                if tid in thread_lifecycle:
                    thread_lifecycle[tid]["updates"] += 1
                else:
                    # Thread was created in last_turn_state this turn but sanitizer
                    # runs before last_turn_state is written — create it with this update
                    thread_lifecycle[tid] = {"created_turn": t, "resolved_turn": None, "updates": 1}

            for tid in (ev.get("threads_resolved") or []):
                if tid in thread_lifecycle and thread_lifecycle[tid]["resolved_turn"] is None:
                    thread_lifecycle[tid]["resolved_turn"] = t
                elif tid not in thread_lifecycle:
                    violations.append({
                        "turn": t,
                        "thread_id": tid,
                        "issue": "thread_resolved_but_not_found",
                    })

        # From record extraction (thread_update, thread_resolve)
        record = ev.get("extraction") or {}
        record_output = record.get("record") or {}
        output = record_output.get("output") or {}

        if isinstance(output, dict):
            for tu in (output.get("thread_update") or []):
                if isinstance(tu, dict):
                    tid = tu.get("id")
                    if tid:
                        if tid not in thread_lifecycle:
                            thread_lifecycle[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}
                        thread_lifecycle[tid]["updates"] += 1

            for tr in (output.get("thread_resolve") or []):
                if isinstance(tr, dict):
                    tid = tr.get("id")
                    if tid and tid in thread_lifecycle and thread_lifecycle[tid]["resolved_turn"] is None:
                        thread_lifecycle[tid]["resolved_turn"] = t

        # From state.arc.threads
        last_state = ev.get("last_turn_state") or {}
        arc = last_state.get("arc") or {}
        for th in (arc.get("threads") or []):
            if isinstance(th, dict) and th.get("id"):
                tid = th["id"]
                if tid not in thread_lifecycle:
                    thread_lifecycle[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}

        # From state.arc.completed_threads
        for ct in (arc.get("completed_threads") or []):
            if isinstance(ct, dict) and ct.get("id"):
                tid = ct["id"]
                if tid not in thread_lifecycle:
                    thread_lifecycle[tid] = {"created_turn": t, "resolved_turn": None, "updates": 0}
                resolved_turn = ct.get("resolved_turn")
                if resolved_turn and tid in thread_lifecycle and thread_lifecycle[tid]["resolved_turn"] is None:
                    thread_lifecycle[tid]["resolved_turn"] = resolved_turn

    # Check for orphaned threads (resolved but not in lifecycle)
    for tid, info in thread_lifecycle.items():
        if info["resolved_turn"] is None and info["updates"] == 0:
            violations.append({
                "turn": info["created_turn"],
                "thread_id": tid,
                "issue": "thread_created_but_never_updated",
            })

    if not violations:
        print("=== Thread Audit ===")
        print(f"Threads tracked: {len(thread_lifecycle)} | Violations: 0")
        print()
        print("All threads have valid lifecycle (created → updated → resolved).")
        return

    print("=== Thread Audit ===")
    print(f"Threads tracked: {len(thread_lifecycle)} | Violations: {len(violations)}")
    print()

    # Group by issue type
    by_issue: dict[str, list[dict[str, Any]]] = {}
    for v in violations:
        by_issue.setdefault(v["issue"], []).append(v)

    for issue in sorted(by_issue.keys()):
        fv = by_issue[issue]
        print(f"-- {issue} ({len(fv)} violations) --")
        for v in fv:
            print(f"  T{v['turn']}: thread '{v['thread_id']}'")
        print()
