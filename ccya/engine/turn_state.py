"""Turn pipeline state application: thread operations, validation, delta application."""

from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.engine.npc_roster import generate_npc_color
from ccya.models import ArcThread, LongTermObjective, NPCEntry, NpcPresence, ProgressEntry, RecordResult, StateMerge, WorldState
from ccya.state import resolve_inventory_remove_target
from ccya.state.delta_builder import _merge_arc_update


_log = logging.getLogger(__name__)


def _apply_thread_updates(
    state: WorldState,
    record_result: RecordResult,
    config: EngineConfig | None = None,
    dedup_rejections: list[dict[str, Any]] | None = None,
) -> LongTermObjective | None:
    """Apply explicit thread updates from the record step."""
    if not record_result.thread_update:
        return None

    arc_raw = state.long_term_objective
    turn_no = state.meta.turn + 1

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
    for update in record_result.thread_update:
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
            updates["urgency_set_turn"] = turn_no
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
                    updates["major_updates"] = current_progress
            else:
                current_progress.append(entry)
                updates["major_updates"] = current_progress

        # Enforce invariant: dormant threads cannot be urgent
        if updates.get("dormant") is True:
            final_urgency = updates.get("urgency", getattr(thread, "urgency", "normal"))
            if final_urgency == "urgent":
                updates["urgency"] = "background"
                updates["urgency_set_turn"] = turn_no

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

    if mutated:
        return arc.model_copy(update={
            "threads": remaining_threads,
        })
    return None


def _apply_thread_automatics(
    state: WorldState,
    config: EngineConfig | None = None,
) -> LongTermObjective | None:
    """Run auto-dormant and urgency decay every turn.

    Auto-dormant: threads untouched for >= thread_dormant_threshold turns
    are marked dormant with urgency=background.

    Urgency decay: threads that have been at their urgency level for
    >= thread_urgency_max_age turns are demoted stepwise:
    urgent → normal → background.
    """
    if not config or not state.long_term_objective:
        return None

    arc_raw = state.long_term_objective
    turn_no = state.meta.turn + 1

    try:
        arc = LongTermObjective.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_automatics.validation_failed trace_id=%d: %s", turn_no, exc, extra={"turn": turn_no},
        )
        return None

    threads = list(arc.threads)
    mutated = False

    # Auto-dormant — fire every turn.
    # Threads updated this turn already have last_updated_turn set to turn_no,
    # so they won't trigger the dormant threshold. Only untouched threads age.
    dormant_threshold = config.thread_dormant_threshold
    for i, t in enumerate(threads):
        _last_updated = t.last_updated_turn or 0
        if (
            (turn_no - _last_updated) >= dormant_threshold
            and not t.dormant
            and t.urgency != "urgent"
        ):
            updated = t.model_copy(update={
                "dormant": True,
                "urgency": "background",
                "last_updated_turn": turn_no,
            })
            threads[i] = updated
            mutated = True
            _log.info(
                "thread_automatics.auto_dormant trace_id=%d thread %s — untouched for %d turns",
                turn_no, t.id, turn_no - _last_updated, extra={"turn": turn_no},
            )

    # Urgency decay
    decay_threshold = config.thread_urgency_max_age
    for i, t in enumerate(threads):
        # Enforce invariant: dormant threads must have urgency=background.
        # Overrides any extractor update that sets dormant threads to normal/urgent.
        if t.dormant and t.urgency != "background":
            updated_dormant = t.model_copy(update={
                "urgency": "background",
            })
            threads[i] = updated_dormant
            mutated = True
            _log.info(
                "thread_automatics.dormant_urgency_enforcement trace_id=%d thread %s urgency %s→background (dormant override)",
                turn_no, t.id, t.urgency, extra={"turn": turn_no},
            )

        # Standard urgency decay (only for non-dormant threads)
        _set_turn = getattr(t, "urgency_set_turn", None)
        if _set_turn is None:
            # Seed threads and new threads may lack urgency_set_turn; default to last_updated_turn for decay tracking
            _last_updated = t.last_updated_turn or 0
            if _last_updated == 0:
                # Never updated — treat as just-seeded
                _set_turn = turn_no
            else:
                _set_turn = _last_updated
        _age = turn_no - _set_turn
        if _age >= decay_threshold:
            _current_urgency = getattr(t, "urgency", "background")
            new_urgency = None
            if _current_urgency == "urgent":
                new_urgency = "normal"
            elif _current_urgency == "normal":
                new_urgency = "background"

            if new_urgency is not None:
                updated_t = t.model_copy(update={"urgency": new_urgency, "urgency_set_turn": turn_no})
                threads[i] = updated_t
                mutated = True
                _log.info(
                    "thread_automatics.urgency_decay trace_id=%d thread %s urgency %s→%s (age=%d turns)",
                    turn_no, t.id, _current_urgency, new_urgency, _age, extra={"turn": turn_no},
                )

    if mutated:
        return arc.model_copy(update={
            "threads": threads,
        })
    return None


def _apply_arc_resolve(
    state: WorldState,
    record_result: RecordResult,
    config: EngineConfig,
) -> WorldState:
    """Process arc resolution from the record step.

    Resolves current arc, stores it in resolved_arcs with TTL tracking,
    then creates a new successor arc with all threads carried forward.
    Returns updated state.
    """
    if not record_result.arc_resolve:
        return state

    turn_no = state.meta.turn + 1
    old_arc = state.long_term_objective

    if not old_arc:
        _log.warning(
            "arc_resolve.no_arc trace_id=%d, skipping", turn_no, extra={"turn": turn_no},
        )
        return state

    resolution = record_result.arc_resolve

    # Store resolved arc entry in state's resolved_arcs list with TTL tracking
    resolved_arc_entry = {
        "long_term_objective": old_arc.long_term_objective,
        "resolution": resolution.resolution,
        "resolved_turn": turn_no,
    }

    new_resolved_arcs = list(state.resolved_arcs or []) + [resolved_arc_entry]

    _log.info(
        "arc_resolve.applied trace_id=%d goal='%s'",
        turn_no, resolution.long_term_objective,
        extra={"turn": turn_no},
    )

    # Create new successor arc with all threads carried forward.
    # Preserve historical thread completions from resolved arc: they remain
    # visible for checkers and async sanitizer validation. Arc resolution
    # stores the resolution in resolved_arcs; completed_threads tracks
    # individual thread resolution state (abandoned/resolved/failed).
    existing_completed = list(old_arc.completed_threads) if old_arc.completed_threads else []
    new_arc = LongTermObjective(
        long_term_objective=resolution.long_term_objective,
        threads=list(old_arc.threads),
        completed_threads=existing_completed,
        last_thread_created_turn=turn_no,
        started_turn=turn_no,
    )

    state = state.set_last_arc_resolve_turn(turn_no)

    return state.model_copy(update={
        "long_term_objective": new_arc,
        "resolved_arcs": new_resolved_arcs,
    })


def _apply_thread_resolutions(
    state: WorldState,
    record_result: RecordResult,
) -> WorldState:
    """Process thread_resolve from the record step.

    Moves resolved/failed/abandoned threads from arc.threads[] to
    arc.completed_threads[], setting resolution_state on each.
    Handles missing IDs gracefully (warning + skip). Deduplicates
    completed_threads entries by updating existing entry instead of
    creating a duplicate.
    Returns updated state.
    """
    if not record_result.thread_resolve:
        return state

    turn_no = state.meta.turn + 1
    arc = state.long_term_objective

    if not arc:
        _log.debug(
            "thread_resolutions: no arc in state at T%d, skipping",
            turn_no, extra={"turn": turn_no},
        )
        return state

    # Collect resolution targets by ID, building updated ArcThread for each
    resolved_ids: set[str] = set()
    updates: list[ArcThread] = []
    any_found = False

    for res in record_result.thread_resolve:
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

        # Collect world_state_candidate for two-step promotion via thread sanitizer
        if res.world_state_candidate:
            candidates = list(state.world_state_candidates or [])
            candidates.append({
                "thread_id": res.id,
                "text": res.world_state_candidate,
                "resolved_turn": turn_no,
            })
            state = state.model_copy(update={"world_state_candidates": candidates})

    if not any_found:
        return state

    # Build new threads[] — exclude all resolved threads
    remaining_threads = [t for t in arc.threads if t.id not in resolved_ids]

    # Build new completed_threads[] — merge updates into existing completed list (dedup by id)
    completed_map: dict[str, ArcThread] = {}
    for ct in arc.completed_threads:
        completed_map[ct.id] = ct
    for u in updates:
        completed_map[u.id] = u

    return state.model_copy(update={
        "long_term_objective": arc.model_copy(update={
            "threads": remaining_threads,
            "completed_threads": list(completed_map.values()),
        }),
    })


def _validate(state: WorldState, delta: StateMerge) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list = list(state.inventory)
    inv_dicts: list[dict[str, Any]] = [it.model_dump() for it in inv_list]
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.id): it.model_dump() for it in inv_list
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_dicts, rem.id)
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


def _expire_conditions(
    state: WorldState,
    turn_no: int,
    trace_id: str,
    save_dir: str,
) -> WorldState:
    """Decrement turns_remaining on all conditions. Remove expired ones. Log events."""
    conditions = list(state.pc.conditions)
    updated_conds: list[Any] = []
    expired_ids: list[str] = []

    for c in conditions:
        # Handle both Condition model objects and legacy dict format
        if isinstance(c, dict):
            cond_id = c.get("id", "?")
            tr = c.get("turns_remaining")
        else:
            cond_id = getattr(c, "id", "?")
            tr = getattr(c, "turns_remaining", 0)

        if tr == "permanent":
            updated_conds.append(c if isinstance(c, dict) else c.model_dump())
            continue
        if isinstance(tr, int):
            new_remaining = tr - 1
            if new_remaining <= 0:
                expired_ids.append(cond_id)
                _log.info(
                    "condition expired: %s at turn %d",
                    cond_id, turn_no,
                    extra={"turn": turn_no},
                )
                # do not append — condition removed
            else:
                if isinstance(c, dict):
                    updated_conds.append({**c, "turns_remaining": new_remaining})
                else:
                    updated_conds.append(c.model_copy(update={"turns_remaining": new_remaining}))
        else:
            # Unknown type — keep as-is with warning
            _log.warning(
                "condition unknown turns_remaining type: %s for %s",
                type(tr).__name__, cond_id,
                extra={"turn": turn_no},
            )
            updated_conds.append(c if isinstance(c, dict) else c.model_dump())

    if expired_ids:
        _log.info(
            "expired_conditions trace_id=%s ids=%s turn=%d",
            trace_id, expired_ids, turn_no,
            extra={"trace_id": trace_id, "turn": turn_no},
        )

    return state.expire_conditions(expired_ids)


def _apply_state_updates(
    state: WorldState,
    delta: StateMerge | None,
    record_result: RecordResult | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
    save_dir: str,
) -> tuple[WorldState, StateMerge | None, dict[str, Any], list[dict[str, Any]], list[str], list[dict[str, Any]]]:
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
                _log.warning("[reconcile] turn %s: %s", state.meta.turn, w, extra={"trace_id": trace_id})
            state = apply_delta(
                state, delta, trace_id=trace_id,
            )

            # TTL decrement pass: expire conditions whose turns_remaining reached 0
            state = _expire_conditions(state, turn_no, trace_id, save_dir)

            applied = delta.model_dump(exclude_none=True)
            for r in rejected:
                if r.get("kind") == "warn_overdraw":
                    _log.info(
                        "inventory over-draw clamped: %s",
                        r.get("reason"),
                        extra={"trace_id": trace_id, "turn": turn_no},
                    )

        # Persist inventory change reason for right-panel tooltip
        if delta and (delta.inventory_add or delta.inventory_remove or delta.inventory_update):
            state = state.set_last_inventory_change_reason(delta.inventory_change_reason or None)
        else:
            state = state.set_last_inventory_change_reason(None)

        # Persist condition change reason for debugging
        if delta and (delta.pc_condition_add or delta.pc_condition_remove):
            if hasattr(delta, "condition_change_reason") and delta.condition_change_reason:
                state = state.set_last_condition_change_reason(delta.condition_change_reason)
            else:
                state = state.set_last_condition_change_reason(None)
        else:
            state = state.set_last_condition_change_reason(None)

        # Stamp last_presence_turn and last_seen_location on touched NPCs; create minimal entry if new
        location = state.location
        for cu in (delta.compendium_npc_update or []):
            entry = state.compendium.npcs.get(cu.id)
            if entry is None:
                new_entry = NPCEntry(
                    name=cu.id.replace("_", " ").title(),
                    presence=NpcPresence.NEARBY,
                    last_seen_location=location.name or "",
                    last_presence_turn=turn_no,
                    color=generate_npc_color(cu.id),
                )
                state = state.add_npc(cu.id, new_entry)
            else:
                state = state.update_npc(
                    cu.id,
                    last_presence_turn=turn_no,
                )

        # Auto-dormant / urgency decay — run every turn, independent of whether there's
        # a delta. This ensures the dormant-urgency-invariant (dormant→background) fires
        # even on quiet turns where the extractor/sanitizer may have bumped urgency.
        automatics_delta = _apply_thread_automatics(state, config)
        if automatics_delta is not None:
            state = state.model_copy(update={"long_term_objective": _merge_arc_update(state.long_term_objective, automatics_delta)})
            if delta is not None:
                delta = delta.model_copy(update={"arc_update": automatics_delta})

        # Arc director: explicitly apply threadUpdates and resolve threads
        if record_result and (state.long_term_objective or record_result.thread_add):
            thread_delta = _apply_thread_updates(state, record_result, config, dedup_rejections=thread_dedup_rejections)
            if thread_delta is not None:
                state = state.model_copy(update={"long_term_objective": _merge_arc_update(state.long_term_objective, thread_delta)})
                if delta is not None:
                    delta = delta.model_copy(update={"arc_update": thread_delta})

            # Apply goal_update (mid-arc long_term_objective change, separate from arc_resolve)
            if record_result.goal_update:
                state = state.model_copy(update={"long_term_objective": state.long_term_objective.model_copy(update={"long_term_objective": record_result.goal_update["long_term_objective"]})})
                _log.info(
                    "goal_update trace_id=%s long_term_objective='%s'",
                    trace_id, record_result.goal_update["long_term_objective"],
                    extra={"trace_id": trace_id},
                )

            # Detect same-turn thread_update + thread_resolve conflict
            update_ids = {u.id for u in (record_result.thread_update or [])}
            resolve_ids = {r.id for r in (record_result.thread_resolve or [])}
            conflict_ids = update_ids & resolve_ids
            if conflict_ids:
                _log.warning(
                    "thread_same_turn_conflict trace_id=%s ids=%s — thread_update and thread_resolve for same id",
                    trace_id, sorted(conflict_ids), extra={"trace_id": trace_id},
                )

            # Process arc resolution (resolves arc + creates successor)
            state = _apply_arc_resolve(state, record_result, config)

            # Process thread resolutions (resolved/failed/abandoned -> completed)
            state = _apply_thread_resolutions(state, record_result)

            if record_result.thread_add:
                _new_thread = record_result.thread_add
                turn_no_for_add = state.meta.turn + 1
                arc = state.long_term_objective
                if delta is not None:
                    try:
                        existing_ids = {t.id for t in arc.threads} | {t.id for t in arc.completed_threads}
                        if _new_thread.id not in existing_ids:
                            _updated_t = _new_thread.model_copy(update={
                                "added_turn": turn_no_for_add,
                                "urgency_set_turn": turn_no_for_add,
                            })
                            arc_with_new_thread = arc.model_copy(
                                update={"threads": list(arc.threads) + [_updated_t],
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
                            state = state.model_copy(update={"long_term_objective": arc_with_new_thread})
                            delta = delta.model_copy(update={"arc_update": arc_with_new_thread})
                        else:
                            _log.warning(
                                "thread_add.duplicate_id trace_id=%s turn=%d thread=%s — ID already exists in arc, skipping",
                                trace_id, turn_no, _new_thread.id, extra={"trace_id": trace_id, "turn": turn_no},
                            )
                            if thread_dedup_rejections is not None:
                                thread_dedup_rejections.append({
                                    "thread_id": _new_thread.id,
                                    "rejected_reason": "duplicate_id",
                                    "similarity": 1.0,
                                    "turn": turn_no,
                                })
                    except Exception as exc:
                        _log.warning(
                            "thread_add: failed to validate arc at T%d for thread %s: %s",
                            turn_no_for_add, getattr(_new_thread, 'id', '?'), exc, extra={"turn": turn_no_for_add},
                        )

            # Engine culling: when >= 3 dormant threads, move oldest to completed
            if state.long_term_objective:
                try:
                    arc = state.long_term_objective
                    dormant_threads = [t for t in arc.threads if t.dormant]
                    if len(dormant_threads) >= 3:
                        to_cull = min(dormant_threads, key=lambda t: t.last_updated_turn or 0)
                        culled = to_cull.model_copy(update={
                            "resolution_state": "abandoned",
                            "outcome": f"Thread faded from relevance — no narrative activity in {turn_no - (to_cull.last_updated_turn or 0)} turns.",
                            "resolved_turn": turn_no,
                        })
                        remaining = [t for t in arc.threads if t.id != to_cull.id]
                        arc = arc.model_copy(update={
                            "threads": remaining,
                            "completed_threads": list(arc.completed_threads) + [culled],
                        })
                        state = state.model_copy(update={"long_term_objective": arc})
                        if delta is not None:
                            delta = delta.model_copy(update={"arc_update": arc})
                        _log.info(
                            "thread_cull trace_id=%s culled=%s dormant_count=%d",
                            trace_id, to_cull.id, len(dormant_threads), extra={"trace_id": trace_id, "turn": turn_no},
                        )
                except Exception as exc:
                    _log.warning(
                        "thread_cull.failed trace_id=%s: %s",
                        trace_id, exc, extra={"trace_id": trace_id, "turn": turn_no},
                    )

        # Engine culling: when >= 3 dormant threads, moves oldest to completed.
        # Runs every turn regardless of delta. Auto-dormant (inside the delta block)
        # may mark threads dormant; culling then removes threads until dormant < 3.
        if state.long_term_objective:
            try:
                arc = state.long_term_objective
                changed = True
                while changed:
                    dormant_threads = [t for t in arc.threads if t.dormant]
                    changed = False
                    if len(dormant_threads) >= 3:
                        to_cull = min(dormant_threads, key=lambda t: t.last_updated_turn or 0)
                        culled = to_cull.model_copy(update={
                            "resolution_state": "abandoned",
                            "outcome": f"Thread faded from relevance — no narrative activity in {turn_no - (to_cull.last_updated_turn or 0)} turns.",
                            "resolved_turn": turn_no,
                        })
                        remaining = [t for t in arc.threads if t.id != to_cull.id]
                        arc = arc.model_copy(update={
                            "threads": remaining,
                            "completed_threads": list(arc.completed_threads) + [culled],
                        })
                        changed = True
                        _log.info(
                            "thread_cull trace_id=%s culled=%s dormant_count=%d",
                            trace_id, to_cull.id, len(dormant_threads), extra={"trace_id": trace_id, "turn": turn_no},
                        )
                if changed:
                    state = state.model_copy(update={"long_term_objective": arc})
                    if delta is not None:
                        delta = delta.model_copy(update={"arc_update": arc})
            except Exception as exc:
                _log.warning(
                    "thread_cull.failed trace_id=%s: %s",
                    trace_id, exc, extra={"trace_id": trace_id, "turn": turn_no},
                )

    # --- NPC lifecycle: nearby decay and departed archive ---
    nearby_ttl = config.nearby_decay_ttl if config else 2
    for nid, entry in list(state.compendium.npcs.items()):
        if entry.presence == NpcPresence.NEARBY:
            last_presence = entry.last_presence_turn
            if isinstance(last_presence, int) and turn_no - last_presence >= nearby_ttl:
                state = state.update_npc(nid, presence=NpcPresence.KNOWN)

    archive_ttl = config.departed_archive_ttl if config else 3
    archived_ids: list[str] = []
    for nid, entry in list(state.compendium.npcs.items()):
        if entry.presence == NpcPresence.DEPARTED:
            dep_turn = entry.departed_turn
            if isinstance(dep_turn, int) and turn_no - dep_turn >= archive_ttl:
                state = state.update_npc(nid, presence=NpcPresence.ARCHIVED)
                archived_ids.append(nid)
    if archived_ids:
        _log.info(
            "archived_departed_npcs ids=%s", sorted(archived_ids),
            extra={"turn": turn_no},
        )

    return state, delta, applied, rejected, reconcile_warnings, thread_dedup_rejections
