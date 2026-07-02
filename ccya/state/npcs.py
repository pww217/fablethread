"""NPC compendium order tracking, proper-name heuristic, and scene management."""

from __future__ import annotations

import logging
import re
from typing import Any

from ccya.models import NPCEntry, SceneExtractResult, WorldState
from ccya.state.inventory import normalize_inventory_id

_log = logging.getLogger(__name__)


def _is_named(name: str) -> bool:
    """Heuristic: a proper name has 2+ words with first and last capitalized."""
    if not name:
        return False
    words = name.strip().split()
    if len(words) < 2:
        return False
    first_word = words[0]
    last_word = words[-1]
    return bool(first_word and first_word[0].isupper() and last_word and last_word[0].isupper())


def touch_compendium_order(state: WorldState, npc_id: str) -> WorldState:
    nid = normalize_inventory_id(npc_id)
    order = list(state.meta.compendium_touch_order)
    if nid in order:
        order.remove(nid)
    order.append(nid)
    _log.debug("touch_compendium_order npc=%s order_len=%d", npc_id, len(order))
    return state.set_compendium_touch_order(order)


def _strip_non_ascii(text: str) -> str:
    """Strip non-ASCII characters from text."""
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()


def apply_npc_scene_management(
    state: WorldState,
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
    trace_id: str | None = None,
) -> WorldState:
    """Apply compendium_npc_update entries to compendium.npcs.

    Returns a new WorldState with updated compendium. Compendium entries are merged.
    """
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

            updates: dict[str, Any] = {}

            if is_new and current_turn_no is not None:
                updates["first_seen_turn"] = current_turn_no
                updates["last_presence_turn"] = current_turn_no
                updates["last_seen_location"] = state.location.name or ""

            if comp_upd.name is not None:
                updates["name"] = _strip_non_ascii(comp_upd.name)
            if comp_upd.title is not None:
                updates["title"] = _strip_non_ascii(comp_upd.title)
            if comp_upd.bio is not None:
                updates["bio"] = _strip_non_ascii(comp_upd.bio)
            # Guard: unnamed NPCs (name doesn't look like a proper name) get bio only.
            _is_unnamed = comp_upd.name and not _is_named(comp_upd.name)
            if _is_unnamed:
                comp_upd = comp_upd.model_copy(update={
                    "motivation": None,
                    "fear": None,
                    "leverage": None,
                    "tie": None,
                    "personality": None,
                    "party": None,
                })
            if comp_upd.motivation is not None:
                updates["motivation"] = comp_upd.motivation
            if comp_upd.fear is not None:
                updates["fear"] = comp_upd.fear
            if comp_upd.leverage is not None:
                updates["leverage"] = comp_upd.leverage
            if comp_upd.tie is not None:
                updates["tie"] = comp_upd.tie
            if comp_upd.personality is not None and not entry.personality:
                updates["personality"] = comp_upd.personality
                _log.info(
                    "npc_scene_management.applied npc=%s personality=%s",
                    resolved_id, comp_upd.personality,
                    extra={"trace_id": trace_id, "turn": current_turn_no},
                )
            # Engine fallback: assign personality for named NPCs that still lack one.
            # Unnamed NPCs are intentionally skipped.
            if not entry.personality and entry.name:
                if _is_named(entry.name):
                    from ccya.personality import assign_personality
                    arch = assign_personality(
                        motivation=entry.motivation,
                        fear=entry.fear,
                        npc_id=resolved_id,
                    )
                    updates["personality"] = arch.id
            if comp_upd.party is not None:
                updates["party"] = comp_upd.party
            if comp_upd.presence is not None:
                updates["presence"] = comp_upd.presence
                if comp_upd.presence == "present":
                    state = touch_compendium_order(state, resolved_id)
                elif comp_upd.presence == "known":
                    updates["position"] = None
            if comp_upd.presence == "departed":
                if comp_upd.departed_reason is not None:
                    updates["departed_reason"] = comp_upd.departed_reason
                if current_turn_no is not None and entry.departed_turn is None:
                    updates["departed_turn"] = current_turn_no
                updates["position"] = None
                updates["party"] = False
            if comp_upd.presence in ("present", "nearby"):
                if current_turn_no is not None:
                    updates["last_presence_turn"] = current_turn_no
            if comp_upd.position is not None:
                updates["position"] = comp_upd.position

            if updates:
                if is_new:
                    new_entry = NPCEntry(**updates)
                    state = state.add_npc(resolved_id, new_entry)
                else:
                    state = state.update_npc(resolved_id, **updates)

    return state
