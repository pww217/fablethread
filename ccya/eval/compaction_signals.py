"""Compaction observability — does compaction fire, and does it perform each of
its documented capabilities?

Compaction is documented in ccya/prompts/compact_system.j2 to:

PART 1 — bullet generation:
  1. preserve named NPCs (first mention, role, title)
  2. preserve location of the turn
  3. preserve arc outcomes (advanced, blocked, failed threads)
  4. preserve key items (gained, lost, consumed)
  5. preserve condition changes
  6. preserve irreversible player choices
  7. preserve deaths/departures of named characters
  8. preserve mechanical consequences (alliances, enmities, oaths)
  9. cull atmospherics, dialogue without consequence, blow-by-blow combat,
     uneventful travel

PART 2 — state sanitization:
  10. npc_merge / inventory_remove / pressure_remove / condition_remove

This module deterministically detects whether compaction RAN, and surfaces
signals the judge can use to evaluate each capability. The judge then writes
a per-capability report.

Implementation note: compaction is "basically broken" per project owner; this
module focuses on MEASUREMENT, not on fixing compaction itself.
"""

from __future__ import annotations

import json
from typing import Any

# Capability list — exact strings from the system prompt; do not paraphrase.
CAPABILITIES = [
    ("bullet_named_npcs",      "Preserve named NPCs (first mention, role, title)"),
    ("bullet_location",        "Preserve location of the turn"),
    ("bullet_arc_outcomes",    "Preserve arc outcomes (advanced/blocked/failed threads)"),
    ("bullet_key_items",       "Preserve key items (gained/lost/consumed)"),
    ("bullet_conditions",      "Preserve condition changes"),
    ("bullet_irreversible",    "Preserve irreversible player choices"),
    ("bullet_deaths",          "Preserve deaths/departures of named characters"),
    ("bullet_mech_consequences","Preserve mechanical consequences (alliances, enmities, oaths)"),
    ("bullet_culling",         "Cull atmospherics, dialogue without consequence, blow-by-blow combat, uneventful travel"),
    ("sanitize_npc_merge",     "Sanitize: npc_merge for duplicate compendium NPCs"),
    ("sanitize_inventory",     "Sanitize: inventory_remove for duplicate items"),
    ("sanitize_pressure",      "Sanitize: pressure_remove for resolved scene pressures"),
    ("sanitize_condition",     "Sanitize: condition_remove for cured conditions"),
]


def _compaction_event(ev: dict[str, Any], prev_last_compacted: int) -> bool:
    """Returns True if this event shows compaction having run.

    Heuristics (any one is enough):
      - applied.compaction.* exists (engine logs compaction outcome under this key)
      - state_snapshot.meta.last_compacted_turn increased since prev event
      - state_snapshot.meta.prior_history grew (new bullets appended)
    """
    applied = ev.get("applied") or {}
    if "compaction" in applied:
        return True
    snap = ev.get("state_snapshot") or {}
    meta = (snap.get("meta") or {})
    last_compacted = meta.get("last_compacted_turn")
    if isinstance(last_compacted, int) and last_compacted > prev_last_compacted:
        return True
    return False


def compute_compaction_signals(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk events; identify compaction events; for each, surface signals for
    each capability so the judge can evaluate it.

    Returns:
        {
          "compaction_observed": bool,
          "events": [
            {
              "turn": int,
              "prior_history_size_before": int,
              "prior_history_size_after": int,
              "bullets_added": list[str],
              "applied_sanitization": dict[str, list],   # npc_merge, inventory_remove, etc.
              "capabilities_to_evaluate": list[(id, label)],
            },
            ...
          ],
          "summary": "no compaction observed" | "<n> compaction event(s)",
        }
    """
    out_events: list[dict[str, Any]] = []
    prev_history_size = 0
    prev_recent_events_size = 0
    prev_last_compacted = 0
    for ev in events:
        if ev.get("__metadata__"):
            continue
        snap = ev.get("state_snapshot") or {}
        meta = snap.get("meta") or {}
        scene = snap.get("scene") or {}
        prior = list(meta.get("prior_history") or [])
        recent = list(scene.get("recent_events") or [])

        if _compaction_event(ev, prev_last_compacted):
            new_bullets = prior[prev_history_size:]
            applied_san = (ev.get("applied") or {}).get("compaction") or {}
            out_events.append({
                "turn": ev.get("turn", "?"),
                "prior_history_size_before": prev_history_size,
                "prior_history_size_after": len(prior),
                "recent_events_size_before": prev_recent_events_size,
                "recent_events_size_after": len(recent),
                "bullets_added": new_bullets,
                "applied_sanitization": applied_san,
                "capabilities_to_evaluate": list(CAPABILITIES),
            })
        prev_history_size = len(prior)
        prev_recent_events_size = len(recent)
        last_compacted = meta.get("last_compacted_turn")
        if isinstance(last_compacted, int):
            prev_last_compacted = last_compacted

    return {
        "compaction_observed": bool(out_events),
        "events": out_events,
        "summary": (f"{len(out_events)} compaction event(s) observed"
                    if out_events else "no compaction observed during this run"),
    }


def render_compaction_section(signals: dict[str, Any]) -> str:
    """Render compaction signals into the # Deterministic Signals section.

    The judge is instructed (via the rubric) to write a per-capability report.
    This section lists the capabilities, the observed bullets, and the applied
    sanitization actions so the judge has the raw material.
    """
    parts: list[str] = ["\n## Compaction Features\n"]

    if not signals.get("compaction_observed"):
        parts.append("*(compaction did not fire during this run — likely because the run was shorter than `compact_every`. Judge: do not score compaction capabilities for this run; note this in your verdict.)*\n")
        return "".join(parts)

    parts.append(f"**{signals['summary']}.** For each event below, the judge must evaluate every capability and write `[OK] / [FAIL] / [NA]` with a one-line justification per capability. The 13 capabilities the compactor system prompt promises:\n\n")
    for cap_id, cap_label in CAPABILITIES:
        parts.append(f"- `{cap_id}` — {cap_label}\n")
    parts.append("\n")

    for ev in signals["events"]:
        parts.append(f"### Compaction at turn {ev['turn']}\n\n")
        parts.append(f"- prior_history: {ev['prior_history_size_before']} → {ev['prior_history_size_after']} bullets ({len(ev['bullets_added'])} added)\n")
        parts.append(f"- recent_events: {ev['recent_events_size_before']} → {ev['recent_events_size_after']} entries\n\n")
        parts.append("**Bullets added:**\n\n")
        if ev["bullets_added"]:
            for b in ev["bullets_added"]:
                parts.append(f"  > {b}\n")
        else:
            parts.append("  *(none — compaction event detected but no bullets appended; flag this)*\n")
        parts.append("\n**Applied sanitization actions:**\n\n")
        san = ev.get("applied_sanitization") or {}
        if not san:
            parts.append("  *(none recorded)*\n")
        else:
            parts.append("```json\n")
            parts.append(json.dumps(san, indent=2, default=str))
            parts.append("\n```\n")
        parts.append("\n")
    return "".join(parts)
