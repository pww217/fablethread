"""Narration prompt building and NPC name generation helpers."""

from __future__ import annotations

from typing import Any

from ccya.engine.config import _render
from ccya.engine.npc_roster import build_npc_roster
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
    world_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    deescalate: float = 0.0,
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    compendium_bios: list[dict[str, Any]] = [],
    pc_allegiance: str | None = None,
    scene_pressure: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    threat_ages: list[dict[str, Any]] | None = None,
    threat_pressure_at: int = 3,
    threat_imperative_at: int = 5,
    building_threat_imperative_at: int = 4,
    npc_roster: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "pc": state.get("pc") or {},
        "chronicle_tail": chronicle_tail,
        "prior_history": list((state.get("meta") or {}).get("prior_history") or []),
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": {"turn": turn_no},
        "scene": state.get("scene", {}),
        "deescalate": deescalate,
        "ages": ages or {},
        "known_npcs": known_npcs,
        "present_npcs": present_npcs,
        "compendium_bios": compendium_bios,
        "pc_allegiance": pc_allegiance,
        "scene_pressure": scene_pressure or [],
        "world_factions": world_factions,
        "world_locations": world_locations,
        "threat_ages": threat_ages or [],
        "threat_pressure_at": threat_pressure_at,
        "threat_imperative_at": threat_imperative_at,
        "building_threat_imperative_at": building_threat_imperative_at,
        "npc_roster": npc_roster or build_npc_roster(
            present_npcs=present_npcs,
            known_npcs=known_npcs,
            recently_left=recently_left,
        ),
    }
    # Build arc context for narrator
    arc = state.get("arc") or {}
    if arc:
        current_arc_ctx = {
            "visible_goal": arc.get("visible_goal", ""),
            "thematic_question": arc.get("thematic_question", ""),
            "phase": arc.get("phase", "setup"),
            "active_threads": [
                {
                    "summary": t.get("summary", ""),
                    "urgency": t.get("urgency", "normal"),
                    "tags": t.get("tags", []),
                }
                for t in (arc.get("active_threads") or [])
            ],
            "pc_drive": arc.get("pc_drive", ""),
            "hidden_truths": arc.get("hidden_truths") or [],
        }
    else:
        current_arc_ctx = None

    system_text = _render(env, "narrate_system.j2", {
        "pack_style": pack_style,
        "narrator_rules": narrator_rules,
        "world_rules": world_rules,
        "current_arc": current_arc_ctx,
    })
    user_text = _render(env, "narrate_user.j2", user_ctx)
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_narrate_thinking)
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
            bio = (e.get("bio") or "").strip()
            if bio:
                if len(bio) > 120:
                    bio = bio[:117].rstrip() + "..."
                row["bio"] = bio
            for field in ("motivation", "fear", "leverage"):
                val = e.get(field)
                if val:
                    row[field] = val
            rows.append(row)
        else:
            bio = (e.get("bio") or "").strip()
            if len(bio) > 120:
                bio = bio[:117].rstrip() + "..."
            r: dict[str, Any] = {
                "id": nid,
                "name": e.get("name") or "",
                "title": e.get("title") or "",
                "bio": bio,
            }
            for field in ("motivation", "fear", "leverage"):
                val = e.get(field)
                if val:
                    r[field] = val
            rows.append(r)
    return rows
