"""Narration prompt building and NPC name generation helpers."""

from __future__ import annotations

from typing import Any

from ccya.engine.config import _render
from ccya.llm_client import apply_thinking
from ccya.models import RulesOutcome


def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    narrator_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    last_turn_failed: list[str] = [],
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    deescalate: bool = False,
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "last_turn_failed": last_turn_failed,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": state.get("meta", {}),
        "scene": state.get("scene", {}),
        "deescalate": deescalate,
        "ages": ages or {},
        "known_npcs": known_npcs,
        "present_npcs": present_npcs,
        "world_factions": world_factions,
        "world_locations": world_locations,
        "pc_allegiance": pc_allegiance,
    }
    system_text = _render(env, "narrate_system.j2", {
        "pack_style": pack_style,
        "narrator_rules": narrator_rules,
        "world_factions": world_factions,
        "world_locations": world_locations,
    })
    user_text = _render(env, "narrate_user.j2", user_ctx)
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    if enable_narrate_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs


def _known_characters_for_extract(
    state: dict[str, Any], *, compact: bool = False
) -> list[dict[str, Any]]:
    comp = (state.get("compendium") or {}).get("npcs") or {}
    order = list((state.get("meta") or {}).get("compendium_touch_order") or [])
    seen: set[str] = set()
    out_ids: list[str] = []
    for nid in reversed(order):
        if nid in comp and nid not in seen:
            out_ids.append(nid)
            seen.add(nid)
            if len(out_ids) >= 10:
                break
    for k in sorted(comp.keys()):
        if k not in seen and len(out_ids) < 10:
            out_ids.append(k)
            seen.add(k)
    rows: list[dict[str, Any]] = []
    for nid in out_ids:
        e = comp.get(nid) or {}
        if compact:
            row: dict[str, Any] = {"id": nid, "name": e.get("name") or ""}
            ls = e.get("last_seen")
            if ls:
                row["last_seen"] = ls
            rows.append(row)
        else:
            bio = (e.get("bio") or "").strip()
            if len(bio) > 120:
                bio = bio[:117].rstrip() + "..."
            rows.append(
                {
                    "id": nid,
                    "name": e.get("name") or "",
                    "title": e.get("title") or "",
                    "bio_preview": bio,
                },
            )
    return rows


def build_state_slice(
    state: dict[str, Any], active_domains: list[str]
) -> dict[str, Any]:
    _HIDDEN = "__HIDDEN__"
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    scene = state.get("scene") or {}

    slice: dict[str, Any] = {
        # Always include these
        "pc_core": {
            "name": pc.get("name", ""),
            "tagline": pc.get("tagline", "") or pc.get("concept", ""),
            "bio": pc.get("bio", ""),
            "stats": pc.get("stats", {}),
        },
        "location": location,
        "known_characters": _known_characters_for_extract(state),
    }

    # Conditionally include based on active domains
    if "inventory" in active_domains:
        slice["inventory"] = state.get("inventory", [])
    else:
        slice["inventory"] = _HIDDEN

    if "quest_updates" in active_domains:
        slice["active_quests"] = [
            q for q in state.get("quests", []) if q.get("status") == "active"
        ]
    else:
        slice["active_quests"] = _HIDDEN

    if "recent_events" in active_domains:
        slice["recent_events"] = list(scene.get("recent_events") or [])
    else:
        slice["recent_events"] = _HIDDEN

    slice["world_state"] = list(scene.get("world_state") or [])

    if "pc_condition" in active_domains:
        slice["conditions"] = list(pc.get("conditions") or [])
    else:
        slice["conditions"] = _HIDDEN

    return slice
