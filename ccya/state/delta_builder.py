"""Delta application logic extracted from delta.py.

Breaking the circular dependency between engine and state packages.
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

from ccya.errors import ErrorKind
from ccya.models import Condition, InventoryItem, LongTermObjective, NpcPresence, SceneExtractResult, StateDelta, WorldState
from ccya.state.inventory import (
    _fuzzy_match_inventory,
    resolve_inventory_canonical_id,
    resolve_inventory_remove_target,
)

_NAME_RE = re.compile(r"[^\x00-\x7F]")
_DEFAULT_CONDITION_TTL = 10

_log = logging.getLogger(__name__)


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    result = _NAME_RE.sub("", text).strip()
    return result


def _item_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
        if out.get("amount") is None or int(out.get("amount", 0) or 0) < 1:
            out["amount"] = 1
        return out
    amt = getattr(item, "amount", 1)
    result: dict[str, Any] = {
        "id": item.id,
        "name": item.name,
        "notes": item.notes,
        "amount": max(1, int(amt or 1)),
    }
    aliases = getattr(item, "aliases", None)
    if aliases:
        result["aliases"] = list(aliases)
    return result


def _merge_arc_update(arc: LongTermObjective, au: LongTermObjective) -> LongTermObjective:
    """Merge arc_update into live arc. long_term_objective/resolution merged conditionally; threads[] and completed_threads[] always replaced."""
    updates: dict[str, Any] = {}
    if au.long_term_objective:
        updates["long_term_objective"] = au.long_term_objective
    if au.resolution is not None:
        updates["resolution"] = au.resolution
    if au.last_thread_created_turn and au.last_thread_created_turn != 0:
        updates["last_thread_created_turn"] = au.last_thread_created_turn
    updates["threads"] = list(au.threads)
    updates["completed_threads"] = list(au.completed_threads)
    return arc.model_copy(update=updates)


def reconcile_delta(state: WorldState, delta: StateDelta) -> tuple[StateDelta, list[str]]:
    """Validate and clean `delta` against current `state`.

    Returns a ``(reconciled_delta, warnings)`` tuple.  Does NOT mutate
    the original ``delta`` -- creates a copy, reconciles the copy, and
    returns it.
    """
    delta = copy.deepcopy(delta)
    warnings: list[str] = []

    add_ids = {i.id for i in delta.inventory_add}
    remove_ids = {r.id for r in delta.inventory_remove}
    conflict = add_ids & remove_ids
    if conflict:
        delta.inventory_add = [i for i in delta.inventory_add if i.id not in conflict]
        msg = f"inventory conflict (add+remove same turn): {sorted(conflict)}"
        warnings.append(msg)
        _log.warning("reconcile_delta %s", msg)

    existing_conds = {
        c.id for c in (state.pc.conditions or [])
    }
    remove_ids = {r.id for r in delta.pc_condition_remove}
    dupes = [c for c in delta.pc_condition_add if c.id in existing_conds and c.id not in remove_ids]
    if dupes:
        delta.pc_condition_add = [c for c in delta.pc_condition_add if c.id not in existing_conds and c.id not in remove_ids]
        msg = f"duplicate condition add ignored: {[c.id for c in dupes]}"
        warnings.append(msg)
        _log.warning("reconcile_delta %s", msg)

    seen_adds: set[str] = set()
    deduped_adds = []
    for c in delta.pc_condition_add:
        if c.id not in seen_adds:
            deduped_adds.append(c)
            seen_adds.add(c.id)
        else:
            msg = f"duplicate condition add within delta: {c.id}"
            warnings.append(msg)
            _log.warning("reconcile_delta %s", msg)
    delta.pc_condition_add = deduped_adds

    return delta, warnings


def apply_delta(
    state: WorldState, delta: StateDelta,
    *, trace_id: str | None = None,
) -> WorldState:
    current_turn = state.meta.turn

    inv: list[dict[str, Any]] = [item.model_dump() for item in state.inventory]

    def _by_id() -> dict[str, dict[str, Any]]:
        return {str(i["id"]): i for i in inv}

    by_id = _by_id()

    for item in delta.inventory_add:
        d = _item_to_dict(item)
        d["name"] = _strip_non_ascii(d.get("name", item.id))
        amt = max(1, int(d.get("amount") or 1))
        canonical = resolve_inventory_canonical_id(inv, item.id)
        target_id = canonical if canonical else item.id
        if target_id in by_id:
            ex = by_id[target_id]
            ex["amount"] = int(ex.get("amount", 1)) + amt
            if d.get("notes"):
                ex["notes"] = d["notes"]
            if d.get("aliases"):
                existing_aliases = set(ex.get("aliases") or [])
                for a in d["aliases"]:
                    if a.lower() not in {x.lower() for x in existing_aliases}:
                        existing_aliases.add(a.lower())
                ex["aliases"] = list(existing_aliases)
        else:
            fuzzy_id = _fuzzy_match_inventory(d.get("name", item.id), inv)
            if fuzzy_id and fuzzy_id in by_id:
                ex = by_id[fuzzy_id]
                ex["amount"] = int(ex.get("amount", 1)) + amt
                if d.get("notes"):
                    ex["notes"] = d["notes"]
                if d.get("aliases"):
                    existing_aliases = set(ex.get("aliases") or [])
                    for a in d["aliases"]:
                        if a.lower() not in {x.lower() for x in existing_aliases}:
                            existing_aliases.add(a.lower())
                    ex["aliases"] = list(existing_aliases)
                _log.info(
                    "inventory fuzzy merge: %s -> %s (score via _fuzzy_match_inventory)",
                    d.get("name", item.id),
                    fuzzy_id,
                )
            else:
                d["amount"] = amt
                d["id"] = target_id
                inv.append(d)
                by_id = _by_id()
        _log.info("inventory_add.applied item=%s amount=%d", item.id, d["amount"],
                  extra={"trace_id": trace_id, "turn": current_turn})

    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv, rem.id)
        if not canonical:
            _log.warning(
                "inventory_remove target not found item=%r", rem.id,
                extra={"trace_id": trace_id, "turn": current_turn, "error_kind": ErrorKind.INVENTORY_REMOVE_FAILED},
            )
            continue
        ex = by_id[canonical]
        if rem.amount is None:
            inv = [x for x in inv if x.get("id") != canonical]
        else:
            amt_raw = int(rem.amount)
            if amt_raw <= 0:
                _log.warning(
                    "inventory_remove amount coerced to 0 item=%s", canonical,
                    extra={"trace_id": trace_id, "turn": current_turn, "error_kind": ErrorKind.INVENTORY_REMOVE_FAILED},
                )
                inv = [x for x in inv if x.get("id") != canonical]
            else:
                cur = int(ex.get("amount", 1))
                new_amt = max(0, cur - amt_raw)
                if new_amt <= 0:
                    inv = [x for x in inv if x.get("id") != canonical]
                else:
                    ex["amount"] = new_amt
        by_id = _by_id()

    for inv_upd in delta.inventory_update:
        canonical = resolve_inventory_canonical_id(inv, inv_upd.id)
        if not canonical:
            _log.warning(
                "inventory_update target not found item=%s", inv_upd.id,
                extra={"trace_id": trace_id, "turn": current_turn, "error_kind": ErrorKind.INVENTORY_UPDATE_FAILED},
            )
            continue
        ex = by_id[canonical]
        if inv_upd.name is not None:
            ex["name"] = _strip_non_ascii(inv_upd.name)
        if inv_upd.notes is not None:
            ex["notes"] = inv_upd.notes

    inv.sort(key=lambda x: 0 if x.get("id") == "credits" else 1)

    if delta.location_change and (delta.location_change.id or delta.location_change.name):
        for nid, entry in list(state.compendium.npcs.items()):
            if entry.presence == NpcPresence.PRESENT:
                if entry.party:
                    continue
                state = state.update_npc(nid, presence=NpcPresence.NEARBY)

        _stamp_turn = state.meta.turn + 1
        scene = state.scene.model_copy(update={
            "turn_entered": _stamp_turn,
            "location_entered_turn": _stamp_turn,
        })
        state = state.model_copy(update={
            "inventory": [InventoryItem(**i) for i in inv],
            "location": delta.location_change,
            "scene": scene,
        })
        _log.info("location_change.applied location=%s name=%s", delta.location_change.id, delta.location_change.name,
                  extra={"trace_id": trace_id, "turn": current_turn})
    elif delta.location_description:
        loc = state.location
        state = state.model_copy(update={"location": loc.model_copy(update={"description": delta.location_description})})

    # Conditions
    existing_conds: list[dict[str, Any]] = [c.model_dump() for c in state.pc.conditions]
    remove_ids = {r.id for r in delta.pc_condition_remove}
    existing_conds = [c for c in existing_conds if c.get("id") not in remove_ids]
    existing_ids = {c.get("id") for c in existing_conds}
    for ca in delta.pc_condition_add:
        cid = ca.id
        if not cid or cid in existing_ids:
            continue
        cond_dict = {
            "id": cid,
            "label": ca.label,
            "description": ca.description,
            "added_turn": current_turn,
        }
        if ca.turns_remaining == 0:
            cond_dict["turns_remaining"] = _DEFAULT_CONDITION_TTL
        elif ca.turns_remaining == "permanent":
            cond_dict["turns_remaining"] = "permanent"
        else:
            cond_dict["turns_remaining"] = ca.turns_remaining
        existing_conds.append(cond_dict)
        existing_ids.add(cid)
    pc = state.pc.model_copy(update={"conditions": [Condition(**c) for c in existing_conds]})
    if delta.pc_condition_remove or delta.pc_condition_add:
        _log.info("condition_change.applied adds=%d removes=%d",
                  len(delta.pc_condition_add), len(delta.pc_condition_remove),
                  extra={"trace_id": trace_id, "turn": current_turn})

    # --- NPC scene management (extracted to state/npcs.py) ---
    from ccya.state.npcs import apply_npc_scene_management
    state = apply_npc_scene_management(state, SceneExtractResult(
        compendium_npc_update=delta.compendium_npc_update or [],
    ), current_turn_no=current_turn, trace_id=trace_id)

    # --- Arc update: merge arc_update into state arc ---
    if delta.arc_update is not None:
        state = state.model_copy(update={"arc": _merge_arc_update(state.arc, delta.arc_update)})

    # --- Persist storyteller actions as rolling window ---
    if delta.actions:
        pc = pc.model_copy(update={"actions": list(delta.actions[-10:])})
        _log.info(
            "Applied %d Storyteller Actions", len(delta.actions),
            extra={"turn": current_turn, "trace_id": trace_id or "", "pack": "", "kind": "actions"},
        )

    return state.model_copy(update={"pc": pc})
