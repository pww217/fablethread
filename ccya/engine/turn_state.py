"""Turn pipeline state application: thread operations, validation, delta application."""

from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.models import ArcThread, LongTermObjective, ProgressEntry, StorytellerResult, StateDelta
from ccya.state import resolve_inventory_remove_target
from ccya.state.delta_builder import _merge_arc_update


_log = logging.getLogger(__name__)


def _apply_thread_updates(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
    config: EngineConfig | None = None,
    dedup_rejections: list[dict[str, Any]] | None = None,
) -> LongTermObjective | None:
    """Apply explicit thread updates from the storyteller."""
    if not storyteller_result.thread_update:
        return None

    arc_raw = state.get("long_term_objective")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_updates.no_arc trace_id=%d, skipping", turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = LongTermObjective.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_updates.validation_failed trace_id=%d: %s", turn_no, exc, extra={"turn": turn_no},
        )
        return None

    mutated = False
    remaining_threads = list(arc.threads)
    for update in storyteller_result.thread_update:
        found_idx = None
        for i, t in enumerate(remaining_threads):
            if getattr(t, "id", "") == update.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_updates.unknown_id trace_id=%d thread %s — skipping", turn_no, update.id, extra={"turn": turn_no},
            )
            continue

        updates: dict[str, Any] = {}
        thread = remaining_threads[found_idx]
        if update.dormant is not None:
            updates["dormant"] = update.dormant
        if update.urgency is not None:
            updates["urgency"] = update.urgency
        if update.type is not None:
            updates["type"] = update.type
        if update.progress is not None:
            current_progress = list(thread.major_updates)
            kind = update.major_update_signal or "advancement"
            entry = ProgressEntry(text=update.progress, kind=kind)
            if current_progress:
                last_text = current_progress[-1].text if isinstance(current_progress[-1], ProgressEntry) else str(current_progress[-1])
                ratio = __import__('difflib').SequenceMatcher(None, last_text, entry.text).ratio()
                if ratio >= 0.70:
                    _log.warning(
                        "thread_updates.dedup trace_id=%d thread %s — progress %.2f overlap with last entry, rejecting",
                        turn_no, update.id, ratio, extra={"turn": turn_no},
                    )
                    if dedup_rejections is not None:
                        dedup_rejections.append({
                            "thread_id": update.id,
                            "rejected_progress": update.progress,
                            "similarity": round(ratio, 2),
                            "turn": turn_no,
                        })
                else:
                    current_progress.append(entry)
                    updates["progress"] = current_progress
            else:
                current_progress.append(entry)
                updates["progress"] = current_progress

        # Enforce invariant: dormant threads cannot be urgent
        if updates.get("dormant") is True:
            final_urgency = updates.get("urgency", getattr(thread, "urgency", "normal"))
            if final_urgency == "urgent":
                updates["urgency"] = "background"

        if updates:
            updates["last_updated_turn"] = turn_no
            mutated = True

        updated_thread = thread.model_copy(update=updates)
        remaining_threads = [t for i2, t in enumerate(remaining_threads) if i2 != found_idx]
        remaining_threads.insert(found_idx, updated_thread)

        if mutated:
            _log.info(
                "thread_updates.applied trace_id=%d thread %s changes=%s", turn_no, update.id, updates, extra={"turn": turn_no},
            )

    # Auto-dormant — fire every turn.
    # Threads updated this turn already have last_updated_turn set to turn_no,
    # so they won't trigger the dormant threshold. Only untouched threads age.
    if config and remaining_threads:
        dormant_threshold = 8  # turns without activity before auto-dormant
        for i, t in enumerate(remaining_threads):
            if (
                t.last_updated_turn is not None
                and (turn_no - t.last_updated_turn) >= dormant_threshold
                and not t.dormant
                and t.urgency != "urgent"
            ):
                updated = t.model_copy(update={
                    "dormant": True,
                    "urgency": "background",
                    "last_updated_turn": turn_no,
                })
                remaining_threads[i] = updated
                _log.info(
                    "thread_updates.auto_dormant trace_id=%d thread %s — untouched for %d turns",
                    turn_no, t.id, turn_no - t.last_updated_turn, extra={"turn": turn_no},
                )

    # Urgency decay: demote threads that have been at their urgency level for
    # >= thread_urgency_max_age turns. Demotes stepwise: urgent → normal → background.
    if config and remaining_threads:
        _decay_threshold = config.thread_urgency_max_age
        for i, t in enumerate(remaining_threads):
            _set_turn = getattr(t, "urgency_set_turn", None)
            if _set_turn is None or t.dormant:
                continue  # skip threads without urgency tracking; decay only affects active threads
            _age = turn_no - _set_turn
            if _age >= _decay_threshold:
                _current_urgency = getattr(t, "urgency", "background")
                new_urgency = None
                if _current_urgency == "urgent":
                    new_urgency = "normal"
                elif _current_urgency == "normal":
                    new_urgency = "background"

                if new_urgency is not None:
                    updated_t = t.model_copy(update={"urgency": new_urgency, "urgency_set_turn": turn_no})
                    remaining_threads[i] = updated_t
                    mutated = True
                    _log.info(
                        "thread_updates.urgency_decay trace_id=%d thread %s urgency %s→%s (age=%d turns)",
                        turn_no, t.id, _current_urgency, new_urgency, _age, extra={"turn": turn_no},
                    )

    # Thread completion: auto-resolve threads whose progress entries >= threshold
    completed: list[ArcThread] = []
    if config and remaining_threads:
        threshold = config.thread_completion_threshold
        i = 0
        while i < len(remaining_threads):
            t = remaining_threads[i]
            if not t.dormant and len(t.major_updates) >= threshold:
                resolved = t.model_copy(update={
                    "resolution_state": "resolved",
                    "outcome": "Thread reached its natural conclusion.",
                    "resolved_turn": turn_no,
                })
                completed.append(resolved)
                remaining_threads.pop(i)
                mutated = True
                _log.info(
                    "thread_updates.completed trace_id=%d thread %s progress=%d threshold=%d",
                    turn_no, t.id, len(t.major_updates), threshold, extra={"turn": turn_no},
                )
            else:
                i += 1

    if mutated or completed:
        return arc.model_copy(update={
            "threads": remaining_threads,
            "completed_threads": arc.completed_threads + completed,
        })
    return None


def _apply_arc_resolve(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
    config: EngineConfig,
) -> LongTermObjective | None:
    """Process arc resolution from the storyteller.

    Resolves current arc, stores it in resolved_arcs with TTL tracking,
    processes thread drop list (opt-out carry-over), and creates a new
    successor arc seeded with surviving + new threads.
    """
    if not storyteller_result.arc_resolve:
        return None

    arc_raw = state.get("long_term_objective")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.warning(
            "arc_resolve.no_arc trace_id=%d, skipping", turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        old_arc = LongTermObjective.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "arc_resolve.validation_failed trace_id=%d: %s", turn_no, exc, extra={"turn": turn_no},
        )
        return None

    resolution = storyteller_result.arc_resolve

    # Store resolved arc entry in state's resolved_arcs list with TTL tracking
    resolved_arc_entry = {
        "long_term_objective": old_arc.long_term_objective,
        "resolution": resolution.resolution,
        "resolved_turn": turn_no,
        "closed_threads": [],
    }

    state.setdefault("resolved_arcs", []).append(resolved_arc_entry)

    _log.info(
        "arc_resolve.applied trace_id=%d goal='%s'",
        turn_no, resolution.long_term_objective,
        extra={"turn": turn_no},
    )

    # Create new successor arc with all threads carried forward
    new_arc = LongTermObjective(
        long_term_objective=resolution.long_term_objective,
        threads=list(old_arc.threads),
        completed_threads=old_arc.completed_threads[:],
        last_thread_created_turn=turn_no,
        started_turn=turn_no,
    )

    state["long_term_objective"] = new_arc.model_dump()
    state.setdefault("meta", {})["last_arc_resolve_turn"] = turn_no

    return new_arc


def _apply_thread_resolutions(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
) -> LongTermObjective | None:
    """Process thread_resolve from StorytellerResult.

    Moves resolved/failed/abandoned threads from arc.threads[] to
    arc.completed_threads[], setting resolution_state on each.
    Handles missing IDs gracefully (warning + skip). Deduplicates
    completed_threads entries by updating existing entry instead of
    creating a duplicate.
    """
    if not storyteller_result.thread_resolve:
        return None

    arc_raw = state.get("long_term_objective")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_resolutions: no arc in state at T%d, skipping",
            turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = LongTermObjective.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_resolutions: failed to validate arc at T%d: %s",
            turn_no, exc, extra={"turn": turn_no},
        )
        return None

    # Collect resolution targets by ID, building updated ArcThread for each
    resolved_ids: set[str] = set()
    updates: list[ArcThread] = []
    any_found = False

    for res in storyteller_result.thread_resolve:
        found_idx = None
        for i, t in enumerate(arc.threads):
            if getattr(t, "id", "") == res.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_resolutions: T%d thread_resolve references unknown id=%s — skipping",
                turn_no, res.id, extra={"turn": turn_no},
            )
            continue

        any_found = True
        thread = arc.threads[found_idx]
        resolved_ids.add(thread.id)
        updates.append(thread.model_copy(update={
            "resolution_state": res.resolution_state,
            "outcome": res.outcome,
            "resolved_turn": turn_no,
        }))

    if not any_found:
        return None

    # Build new threads[] — exclude all resolved threads
    remaining_threads = [t for t in arc.threads if t.id not in resolved_ids]

    # Build new completed_threads[] — merge updates into existing completed list (dedup by id)
    completed_map: dict[str, ArcThread] = {}
    for ct in arc.completed_threads:
        completed_map[ct.id] = ct
    for u in updates:
        completed_map[u.id] = u

    return arc.model_copy(update={
        "threads": remaining_threads,
        "completed_threads": list(completed_map.values()),
    })


def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            rejections.append({
                "field": "inventory_remove",
                "kind": "missing_target",
                "value": rem.id,
                "reason": f"Item '{rem.id}' not found in inventory",
            })
            continue
        item = inv_by_id.get(canonical)
        if item and int(item.get("amount") or 0) == 0:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "zero_balance",
                    "value": canonical,
                    "reason": f"Item '{canonical}' has zero balance",
                }
            )
            continue
        if rem.amount is None:
            continue
        try:
            requested = int(rem.amount)
        except (TypeError, ValueError):
            continue
        if requested <= 0:
            continue
        current = int(inv_by_id.get(canonical, {}).get("amount") or 1)
        if requested > current:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "warn_overdraw",
                    "value": canonical,
                    "requested": requested,
                    "current": current,
                    "reason": (
                        f"Over-draw on '{canonical}': requested {requested} but stack is {current}. "
                        "apply_delta will clamp to a full-stack remove."
                    ),
                }
            )

    return rejections


def _apply_state_updates(
    state: dict[str, Any],
    delta: StateDelta | None,
    storyteller_result: StorytellerResult | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
) -> tuple[dict[str, Any], StateDelta | None, dict[str, Any], list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Apply state updates from extraction pipeline: delta, beats, NPCs, arcs.

    Returns (state, delta, applied, rejected, reconcile_warnings, thread_dedup_rejections).
    """
    from ccya.state import apply_delta, reconcile_delta

    applied: dict[str, Any] = {}
    rejected: list[dict[str, Any]] = []
    thread_dedup_rejections: list[dict[str, Any]] = []
    reconcile_warnings: list[str] = []

    if delta is not None:
        rejected = _validate(state, delta)
        blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
        if blocking:
            pass  # Error handling stays in run_turn()
        else:
            delta, reconcile_warnings = reconcile_delta(state, delta)
            for w in reconcile_warnings:
                _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
            state = apply_delta(
                state, delta, trace_id=trace_id,
            )

            applied = delta.model_dump(exclude_none=True)
            for r in rejected:
                if r.get("kind") == "warn_overdraw":
                    _log.info(
                        "inventory over-draw clamped: %s",
                        r.get("reason"),
                        extra={"trace_id": trace_id, "turn": turn_no},
                    )

        # Beat history: snapshot pending_gm_beat after floor relief override.
        # No entry is added when delta is None (extraction pipeline error) — beat
        # history will have a gap for this turn, which is intentional for error-path
        # turns so the next turn's diversity guidance isn't contaminated.
        _history_beat = state.get("meta", {}).get("pending_gm_beat")
        meta = state.setdefault("meta", {})
        meta.setdefault("recent_beats", []).append({
            "turn": turn_no,
            "type": _history_beat.get("type") if _history_beat else None,
            "effect": _history_beat.get("effect") if _history_beat else None,
        })
        # Cap at N entries, oldest first
        max_beats = config.recent_beats_max if config else 5
        if len(meta["recent_beats"]) > max_beats:
            meta["recent_beats"] = meta["recent_beats"][-max_beats:]

        # Persist inventory change reason for right-panel tooltip
        if delta and (delta.inventory_add or delta.inventory_remove or delta.inventory_update):
            if delta.inventory_change_reason:
                meta["last_inventory_change_reason"] = delta.inventory_change_reason
            else:
                meta.pop("last_inventory_change_reason", None)
        else:
            meta.pop("last_inventory_change_reason", None)

        # Persist condition change reason for debugging
        if delta and (delta.pc_condition_add or delta.pc_condition_remove):
            if hasattr(delta, "condition_change_reason") and delta.condition_change_reason:
                meta["last_condition_change_reason"] = delta.condition_change_reason
            else:
                meta.pop("last_condition_change_reason", None)
        else:
            meta.pop("last_condition_change_reason", None)

        # Stamp last_presence_turn and last_seen_location on touched NPCs; create minimal entry if new
        comp = state.get("compendium", {}).get("npcs", {})
        location = state.get("location", {})
        for cu in (delta.compendium_npc_update or []):
            entry = comp.get(cu.id)
            if entry is None:
                comp[cu.id] = {
                    "name": cu.id.replace("_", " ").title(),
                    "presence": "nearby",
                }
                entry = comp[cu.id]
            entry["last_presence_turn"] = turn_no
            entry["last_seen_location"] = location.get("name", "")

        # Arc director: process thread updates and arc resolution
        if state.get("long_term_objective") and storyteller_result:
            # Process chapter_end signal (separate from arc_resolve)
            if storyteller_result.chapter_end:
                _log.info(
                    "chapter_end trace_id=%s turn=%d",
                    trace_id, turn_no, extra={"trace_id": trace_id, "turn": turn_no},
                )
                state.setdefault("meta", {})["last_chapter_end_turn"] = turn_no

            thread_delta = _apply_thread_updates(state, storyteller_result, config, dedup_rejections=thread_dedup_rejections)
            if thread_delta is not None:
                _merge_arc_update(
                    state.setdefault("long_term_objective", {}), thread_delta
                )
                if delta is not None:
                    delta = delta.model_copy(
                        update={"arc_update": thread_delta}
                    )

            # Apply goal_update (mid-arc long_term_objective change, separate from arc_resolve)
            if storyteller_result.goal_update:
                state.setdefault("long_term_objective", {})["long_term_objective"] = storyteller_result.goal_update["long_term_objective"]
                _log.info(
                    "goal_update trace_id=%s long_term_objective='%s'",
                    trace_id, storyteller_result.goal_update["long_term_objective"],
                    extra={"trace_id": trace_id},
                )

            # Detect same-turn thread_update + thread_resolve conflict
            update_ids = {u.id for u in (storyteller_result.thread_update or [])}
            resolve_ids = {r.id for r in (storyteller_result.thread_resolve or [])}
            conflict_ids = update_ids & resolve_ids
            if conflict_ids:
                _log.warning(
                    "thread_same_turn_conflict trace_id=%s ids=%s — thread_update and thread_resolve for same id",
                    trace_id, sorted(conflict_ids), extra={"trace_id": trace_id},
                )

            # Process arc resolution (resolves arc + creates successor)
            resolved_arc = _apply_arc_resolve(state, storyteller_result, config)
            if resolved_arc is not None:
                _merge_arc_update(
                    state.setdefault("long_term_objective", {}), resolved_arc
                )
                if delta is not None:
                    delta = delta.model_copy(
                        update={"arc_update": resolved_arc}
                    )

            # Process thread resolutions (resolved/failed/abandoned -> completed)
            resolved_arc = _apply_thread_resolutions(state, storyteller_result)
            if resolved_arc is not None:
                _merge_arc_update(
                    state.setdefault("long_term_objective", {}), resolved_arc
                )
                if delta is not None:
                    delta = delta.model_copy(
                        update={"arc_update": resolved_arc}
                    )

            if storyteller_result.thread_add:
                # Cooldown gate: only allow thread_add if cooldown satisfied
                _last_add = state.get("meta", {}).get("last_thread_creation_turn")
                if _last_add is not None and config and (turn_no - _last_add < config.thread_creation_cooldown):
                    _log.debug(
                        "thread_add.cooldown trace_id=%s turn=%d last_add=%d cooldown=%d — skipping",
                        trace_id, turn_no, _last_add, config.thread_creation_cooldown,
                        extra={"trace_id": trace_id, "turn": turn_no},
                    )
                else:
                    _new_thread = storyteller_result.thread_add
                    turn_no_for_add = state.get("meta", {}).get("turn", 0) + 1
                    arc_raw = state.get("long_term_objective")
                    if arc_raw and delta is not None:
                        try:
                            _existing_arc = LongTermObjective.model_validate(arc_raw)
                            existing_ids = {t.id for t in _existing_arc.threads} | {t.id for t in _existing_arc.completed_threads}
                            if _new_thread.id not in existing_ids:
                                _updated_t = _new_thread.model_copy(update={
                                    "added_turn": turn_no_for_add,
                                    "urgency_set_turn": turn_no_for_add,
                                })
                                arc_with_new_thread = _existing_arc.model_copy(
                                    update={"threads": list(_existing_arc.threads) + [_updated_t],
                                            "last_thread_created_turn": turn_no_for_add}
                                )
                                if config:
                                    non_dormant = [t for t in arc_with_new_thread.threads if not t.dormant]
                                    if len(non_dormant) > config.thread_max_active:
                                        evict = min(non_dormant, key=lambda t: t.last_updated_turn or 0)
                                        evicted = evict.model_copy(update={"dormant": True, "last_updated_turn": turn_no_for_add})
                                        arc_with_new_thread = arc_with_new_thread.model_copy(
                                            update={"threads": [evicted if t.id == evict.id else t for t in arc_with_new_thread.threads]}
                                        )
                                        _log.info(
                                            "thread_cap.evict trace_id=%s evicted=%s non_dormant_count=%d max=%d",
                                            trace_id, evict.id, len(non_dormant), config.thread_max_active,
                                            extra={"trace_id": trace_id, "turn": turn_no},
                                        )
                                _merge_arc_update(state.setdefault("long_term_objective", {}), arc_with_new_thread)
                                state.setdefault("meta", {})["last_thread_created_turn"] = turn_no_for_add
                                delta = delta.model_copy(update={"arc_update": arc_with_new_thread})
                        except Exception as exc:
                            _log.warning(
                                "thread_add: failed to validate arc at T%d for thread %s: %s",
                                turn_no_for_add, getattr(_new_thread, 'id', '?'), exc, extra={"turn": turn_no_for_add},
                            )

            # Engine culling: when >= 3 dormant threads, move oldest to completed
            if state.get("long_term_objective"):
                try:
                    arc = LongTermObjective.model_validate(state["long_term_objective"])
                    dormant_threads = [t for t in arc.threads if t.dormant]
                    if len(dormant_threads) >= 3:
                        to_cull = min(dormant_threads, key=lambda t: t.last_updated_turn or 0)
                        culled = to_cull.model_copy(update={
                            "resolution_state": "abandoned",
                            "outcome": f"Thread faded from relevance — no narrative activity in {turn_no - (to_cull.last_updated_turn or 0)} turns.",
                            "resolved_turn": turn_no,
                        })
                        remaining = [t for t in arc.threads if t.id != to_cull.id]
                        arc.threads = remaining
                        arc.completed_threads.append(culled)
                        _merge_arc_update(state.setdefault("long_term_objective", {}), arc)
                        if delta is not None:
                            delta = delta.model_copy(update={"arc_update": arc})
                        _log.info(
                            "thread_cull trace_id=%s culled=%s dormant_count=%d",
                            trace_id, to_cull.id, len(dormant_threads), extra={"trace_id": trace_id, "turn": turn_no},
                        )
                except Exception as exc:
                    _log.warning(
                        "thread_cull.failed trace_id=%s: %s",
                        trace_id, exc, extra={"trace_id": trace_id},
                    )

    # --- NPC lifecycle: nearby decay and departed archive ---
    nearby_ttl = config.nearby_decay_ttl if config else 2
    comp = state.get("compendium", {}).get("npcs", {})
    for entry in comp.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("presence") == "nearby":
            last_presence = entry.get("last_presence_turn")
            if isinstance(last_presence, int) and turn_no - last_presence >= nearby_ttl:
                entry["presence"] = "known"

    archive_ttl = config.departed_archive_ttl if config else 3
    archived_ids = []
    for nid, entry in comp.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("presence") == "departed":
            dep_turn = entry.get("departed_turn")
            if isinstance(dep_turn, int) and turn_no - dep_turn >= archive_ttl:
                entry["presence"] = "archived"
                archived_ids.append(nid)
    if archived_ids:
        _log.info(
            "archived_departed_npcs ids=%s", sorted(archived_ids),
            extra={"turn": turn_no},
        )

    return state, delta, applied, rejected, reconcile_warnings, thread_dedup_rejections
