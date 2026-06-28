"""NPC alias map, compendium order tracking, and scene management."""

from __future__ import annotations

import logging
import re
from typing import Any

from ccya.models import SceneExtractResult
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


def touch_compendium_order(state: dict[str, Any], npc_id: str) -> None:
    nid = normalize_inventory_id(npc_id)
    order: list[str] = state.setdefault("meta", {}).setdefault(
        "compendium_touch_order", []
    )
    if nid in order:
        order.remove(nid)
    order.append(nid)
    _log.debug("touch_compendium_order npc=%s order_len=%d", npc_id, len(order))


def _strip_non_ascii(text: str) -> str:
    """Strip non-ASCII characters from text."""
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()


def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Apply compendium_npc_update entries to compendium.npcs.

    Returns the mutated state dict. Compendium entries are merged into state.
    """
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})

    if scene_result.compendium_npc_update:
        _log.info(
            "apply_npc_scene_management compendium_update=%d", len(scene_result.compendium_npc_update),
            extra={"trace_id": trace_id, "turn": current_turn_no},
        )

        for comp_upd in scene_result.compendium_npc_update:
            nid = normalize_inventory_id(comp_upd.id)
            resolved_id = nid

            is_new = resolved_id not in comp
            entry = comp.setdefault(resolved_id, {})

            if is_new and current_turn_no is not None:
                entry["first_seen_turn"] = current_turn_no  # 0-based, matches narrate_user.j2 convention (T{{ npc.first_seen_turn }})
                location = state.get("location", {})
                entry["last_presence_turn"] = current_turn_no
                entry["last_seen_location"] = location.get("name", "")

            if comp_upd.name is not None:
                entry["name"] = _strip_non_ascii(comp_upd.name)
            if comp_upd.title is not None:
                entry["title"] = _strip_non_ascii(comp_upd.title)
            if comp_upd.bio is not None:
                entry["bio"] = _strip_non_ascii(comp_upd.bio)
            # Guard: unnamed NPCs (name doesn't look like a proper name) get bio only.
            _is_unnamed = comp_upd.name and not _is_named(comp_upd.name)
            if _is_unnamed:
                comp_upd = comp_upd.model_copy(update={
                    "motivation": None,
                    "fear": None,
                    "leverage": None,
                    "bond": None,
                    "personality": None,
                    "party": None,
                })
            if comp_upd.motivation is not None:
                entry["motivation"] = comp_upd.motivation
            if comp_upd.fear is not None:
                entry["fear"] = comp_upd.fear
            if comp_upd.leverage is not None:
                entry["leverage"] = comp_upd.leverage
            if comp_upd.bond is not None:
                entry["bond"] = comp_upd.bond
            if comp_upd.personality is not None and not entry.get("personality"):
                entry["personality"] = comp_upd.personality
                _log.info(
                    "npc_scene_management.applied npc=%s personality=%s",
                    resolved_id, comp_upd.personality,
                    extra={"trace_id": trace_id, "turn": current_turn_no},
                )
            # Engine fallback: assign personality for named NPCs that still lack one.
            # Unnamed NPCs are intentionally skipped.
            if not entry.get("personality") and entry.get("name"):
                if _is_named(entry["name"]):
                    from ccya.personality import assign_personality
                    arch = assign_personality(
                        motivation=entry.get("motivation"),
                        fear=entry.get("fear"),
                        npc_id=resolved_id,
                    )
                    entry["personality"] = arch.id
            if comp_upd.party is not None:
                entry["party"] = comp_upd.party
            if comp_upd.presence is not None:
                entry["presence"] = comp_upd.presence
                if comp_upd.presence == "present":
                    touch_compendium_order(state, resolved_id)
                elif comp_upd.presence == "known":
                    entry.pop("position", None)
            if comp_upd.presence == "departed":
                if comp_upd.departed_reason is not None:
                    entry["departed_reason"] = comp_upd.departed_reason
                if current_turn_no is not None:
                    entry["departed_turn"] = entry.get("departed_turn", current_turn_no)
                entry.pop("position", None)
                entry.pop("party", None)
            if comp_upd.presence == "nearby":
                if current_turn_no is not None:
                    entry["last_presence_turn"] = current_turn_no
            if comp_upd.position is not None:
                entry["position"] = comp_upd.position

    return state
