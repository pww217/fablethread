"""NPC compendium order tracking, proper-name heuristic, and scene management."""

from __future__ import annotations

import logging
from typing import Any

from fablethread.state.utils import is_named as _is_named, strip_non_ascii as _strip_non_ascii
from fablethread.models import NPCEntry, NpcPresence, SceneExtractResult, WorldState
from fablethread.state.inventory import normalize_inventory_id

_log = logging.getLogger(__name__)


def touch_compendium_order(state: WorldState, npc_id: str) -> WorldState:
    nid = normalize_inventory_id(npc_id)
    order = list(state.meta.compendium_touch_order)
    if nid in order:
        order.remove(nid)
    order.append(nid)
    _log.debug("touch_compendium_order npc=%s order_len=%d", npc_id, len(order))
    return state.set_compendium_touch_order(order)


def apply_npc_scene_management(
    state: WorldState,
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
    trace_id: str | None = None,
) -> WorldState:
    """Apply compendium_npc_add and compendium_npc_update entries to compendium.npcs.

    Add entries create new NPCs (write-once everything). Update entries mutate
    existing NPCs (only updatable fields). If an Add entry targets an existing
    NPC, log a warning and skip.

    Returns a new WorldState with updated compendium. Compendium entries are merged.
    """
    # --- Add path: create new NPCs ---
    for comp_add in (scene_result.compendium_npc_add or []):
        nid = normalize_inventory_id(comp_add.id)
        if nid in state.compendium.npcs:
            _log.warning(
                "apply_npc_scene_management: add entry for existing NPC %s — skipping", nid,
                extra={"trace_id": trace_id, "turn": current_turn_no},
            )
            continue

        updates: dict[str, Any] = {}
        updates["first_seen_turn"] = current_turn_no or 0
        updates["last_presence_turn"] = current_turn_no or 0
        updates["last_seen_location"] = state.location.name or ""
        from fablethread.engine.npc_roster import generate_npc_color
        updates["color"] = generate_npc_color(nid)

        if comp_add.name is not None:
            updates["name"] = _strip_non_ascii(comp_add.name)
        if comp_add.title is not None:
            updates["title"] = _strip_non_ascii(comp_add.title)
        if comp_add.bio is not None:
            updates["bio"] = _strip_non_ascii(comp_add.bio)
        if comp_add.disposition is not None:
            updates["disposition"] = comp_add.disposition
        if comp_add.motivation is not None:
            updates["motivation"] = comp_add.motivation
        if comp_add.fear is not None:
            updates["fear"] = comp_add.fear
        if comp_add.leverage is not None:
            updates["leverage"] = comp_add.leverage
        if comp_add.tie is not None:
            updates["tie"] = comp_add.tie
        if comp_add.party:
            updates["party"] = True

        # Guard: unnamed NPCs get bio + disposition only (no psychological fields)
        _is_unnamed = comp_add.name and not _is_named(comp_add.name)
        if _is_unnamed:
            updates["motivation"] = None
            updates["fear"] = None
            updates["leverage"] = None
            updates["tie"] = None

        new_entry = NPCEntry(**updates)
        state = state.add_npc(nid, new_entry)

    # --- Update path: mutate existing NPCs ---
    if scene_result.compendium_npc_update:
        _log.info(
            "apply_npc_scene_management compendium_update=%d", len(scene_result.compendium_npc_update),
            extra={"trace_id": trace_id, "turn": current_turn_no},
        )

        for comp_upd in scene_result.compendium_npc_update:
            nid = normalize_inventory_id(comp_upd.id)
            resolved_id = nid

            is_new = resolved_id not in state.compendium.npcs
            entry = state.compendium.npcs.get(resolved_id) or NPCEntry()

            upd: dict[str, Any] = {}

            if is_new and current_turn_no is not None:
                upd["first_seen_turn"] = current_turn_no
                upd["last_presence_turn"] = current_turn_no
                upd["last_seen_location"] = state.location.name or ""
                from fablethread.engine.npc_roster import generate_npc_color
                upd["color"] = generate_npc_color(resolved_id)

            if comp_upd.bio is not None:
                upd["bio"] = _strip_non_ascii(comp_upd.bio)
            if comp_upd.disposition is not None:
                upd["disposition"] = comp_upd.disposition
            if comp_upd.presence is not None:
                # Guard: don't let extractor override demotion for NPCs at old locations
                if comp_upd.presence == "present" and not is_new and entry.last_seen_location and entry.last_seen_location != state.location.name:
                    upd_pres = NpcPresence.NEARBY
                else:
                    upd_pres = NpcPresence(comp_upd.presence)
                upd["presence"] = upd_pres
                if upd_pres == "present":
                    state = touch_compendium_order(state, resolved_id)
                elif upd_pres == "known":
                    upd["position"] = None
            if comp_upd.presence == "departed":
                if comp_upd.departed_reason is not None:
                    upd["departed_reason"] = comp_upd.departed_reason
                if current_turn_no is not None and entry.departed_turn is None:
                    upd["departed_turn"] = current_turn_no
                upd["position"] = None
                upd["party"] = False
            if comp_upd.presence in ("present", "nearby"):
                if current_turn_no is not None:
                    upd["last_presence_turn"] = current_turn_no
            if comp_upd.last_seen_location is not None and not is_new:
                # Only update for existing NPCs when extractor explicitly sets a new location
                upd["last_seen_location"] = comp_upd.last_seen_location
            if comp_upd.position is not None:
                upd["position"] = comp_upd.position

            if upd:
                if is_new:
                    new_entry = NPCEntry(**upd)
                    state = state.add_npc(resolved_id, new_entry)
                else:
                    state = state.update_npc(resolved_id, **upd)

    return state
