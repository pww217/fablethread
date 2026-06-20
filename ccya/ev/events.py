from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

import yaml

from ccya.state.io import load_state as _engine_load_state

DEFAULT_SAVE_DIR = Path("saves/default")

STREAMS = ("ruling", "narrate", "scene", "state", "storytell")


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    text = path.read_text().strip()
    if not text:
        return []
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    events.append(parsed)
            except json.JSONDecodeError:
                continue
    return events


def filter_turn_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ev for ev in events if ev.get("kind", "turn") == "turn"]


def find_turn(events: list[dict[str, Any]], turn: int) -> dict[str, Any] | None:
    for ev in events:
        if ev.get("turn") == turn and ev.get("kind", "turn") == "turn":
            return ev
    for ev in events:
        if ev.get("turn") == turn and ev.get("kind") not in (None, "turn"):
            return ev
    return None


def extract_field(event: dict[str, Any], dotpath: str) -> Any | None:
    cur: Any = event
    for part in dotpath.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur



def extract_extraction_context(event: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], event.get("extraction_context", {}))


def load_current_state(save_dir: Path) -> dict[str, Any]:
    return _engine_load_state(save_dir)


def state_diff(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in ["pc", "scene", "location", "inventory", "arc", "compendium"]:
        vb = before.get(key, {})
        va = after.get(key, {})
        if vb != va:
            lines.append(f"{key}: changed")
    return lines


def load_state_yaml(save_dir: Path | None = None) -> dict[str, Any]:
    if save_dir is None:
        save_dir = DEFAULT_SAVE_DIR
    path = save_dir / "state.yaml"
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        result = yaml.safe_load(f)
        if isinstance(result, dict):
            return cast(dict[str, Any], result)
        print(f"Error: {path} is not a valid state YAML", file=sys.stderr)
        sys.exit(1)


# Internal helpers ported from ev.py


def _get_nested(d: dict[str, Any], path: str) -> Any | None:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _try_parse_json(raw: str) -> dict[str, Any] | None:
    s = raw.strip()
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, ValueError):
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = json.loads(s[i: j + 1])
                return out if isinstance(out, dict) else None
            except (json.JSONDecodeError, ValueError):
                return None
    return None


def _parse_ruling_intent(ev: dict[str, Any]) -> dict[str, Any] | None:
    raw = (ev.get("ruling_prompt") or {}).get("output", "")
    if isinstance(raw, str):
        return _try_parse_json(raw)
    return raw if isinstance(raw, dict) else None


def _metrics_path(stream: str) -> str:
    if stream == "ruling":
        return "ruling"
    elif stream == "narrate":
        return "narrate"
    else:
        return f"extraction.{stream}"


def _stream_keys(ev: dict[str, Any]) -> str:
    parts = []
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        if blob and (blob.get("tokens_in") or blob.get("ms")):
            parts.append(s)
    return ", ".join(parts) if parts else "(none)"


def _stream_ms(ev: dict[str, Any], stream: str) -> str:
    blob = _get_nested(ev, _metrics_path(stream)) or {}
    ms = blob.get("ms") or blob.get("total_ms")
    if ms is not None:
        try:
            return f"{float(ms) / 1000.0:.1f}s"
        except (TypeError, ValueError):
            return str(ms)
    return "\u2014"


def _total_tokens_in(ev: dict[str, Any]) -> str:
    total = 0
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        total += int(blob.get("tokens_in") or 0)
    return str(total)


def _total_tokens_out(ev: dict[str, Any]) -> str:
    total = 0
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        total += int(blob.get("tokens_out") or 0)
    return str(total)


def _total_tt(ev: dict[str, Any]) -> str:
    ruling_ev = ev.get("ruling") or {}
    narr_ev = ev.get("narrate") or {}
    extract_ev = ev.get("extract") or {}
    total_ms = (ruling_ev.get("total_ms") or 0) + (narr_ev.get("total_ms") or 0) + (extract_ev.get("total_ms") or 0)
    try:
        return f"{float(total_ms) / 1000.0:.1f}s"
    except (TypeError, ValueError):
        return str(total_ms)


def _has_retries(ev: dict[str, Any]) -> bool:
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        if blob.get("retry_errors"):
            return True
    return False


def _has_errors(ev: dict[str, Any]) -> bool:
    if ev.get("error"):
        return True
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        if blob.get("error"):
            return True
    return False


def _has_rejections(ev: dict[str, Any]) -> bool:
    return bool(ev.get("rejected"))


def _build_state_diff(ev: dict[str, Any]) -> list[dict[str, Any]]:
    rejected_set = set()
    for r in (ev.get("rejected") or []):
        if isinstance(r, dict) and r.get("field"):
            rejected_set.add(str(r["field"]))

    changes = []
    ruling_intent = _parse_ruling_intent(ev)
    if ruling_intent:
        val = ruling_intent.get("intent")
        if val and isinstance(val, str) and val.strip():
            changes.append({
                "domain": "intent", "op": "set", "field": "intent",
                "value": val[:120], "rejected": False, "from_stream": "ruling",
            })

    for stream_key, path in [("scene", "extraction.scene"), ("state", "extraction.state"), ("storytell", "extraction.storytell")]:
        blob = _get_nested(ev, path) or {}
        if not isinstance(blob, dict):
            continue
        raw_out = blob.get("output")
        if not raw_out:
            continue
        parsed = _try_parse_json(raw_out) if isinstance(raw_out, str) else (raw_out if isinstance(raw_out, dict) else None)
        if not parsed:
            continue
        skip = {"actions", "location_description"}
        for fk, val in parsed.items():
            if fk in skip or val is None:
                continue
            if isinstance(val, (list, dict)) and not val:
                continue
            if fk == "compendium_npc_update":
                op = "upsert"
            elif fk.endswith("_add"):
                op = "add"
            elif fk.endswith("_remove"):
                op = "remove"
            elif fk.endswith("_update"):
                op = "update"
            else:
                op = "set"
            if isinstance(val, str):
                val_str = val[:120]
            else:
                val_str = str(val)[:120]
            changes.append({
                "domain": stream_key, "op": op, "field": fk,
                "value": val_str, "rejected": fk in rejected_set, "from_stream": stream_key,
            })
    return changes


def _count_state_diff(ev: dict[str, Any]) -> int:
    sd = ev.get("state_diff") or _build_state_diff(ev)
    return len(sd) if sd else 0



def extract_field_from_event(ev: dict[str, Any], field: str) -> Any | None:
    ctx = ev.get("extraction_context") or {}
    applied = ev.get("applied") or {}

    if field == "inventory":
        return ctx.get("inventory_this_turn", [])
    elif field.startswith("inventory."):
        item_id = field[len("inventory."):]
        items = ctx.get("inventory_this_turn", []) or []
        for item in items:
            if isinstance(item, dict) and item.get("id") == item_id:
                return {k: v for k, v in item.items() if k != "aliases"}
        return None

    elif field == "conditions":
        return ctx.get("conditions_this_turn", []) or []
    elif field.startswith("conditions."):
        cond_id = field[len("conditions."):]
        conds = ctx.get("conditions_this_turn", []) or []
        for c in conds:
            if isinstance(c, dict) and c.get("id") == cond_id:
                return {k: v for k, v in c.items() if k != "description"}
        return None

    elif field == "npcs":
        updates = applied.get("compendium_npc_update", []) or []
        present_ids = [n.get("id", "") for n in updates if isinstance(n, dict) and n.get("presence") == "present"]
        count = ctx.get("present_npcs_count", 0)
        return present_ids if present_ids else [f"({count} present)"]
    elif field.startswith("npcs."):
        npc_id = field[len("npcs."):]
        updates = applied.get("compendium_npc_update", []) or []
        for n in updates:
            if isinstance(n, dict) and n.get("id") == npc_id:
                return {k: v for k, v in n.items() if k != "bio"}
        return None

    elif field == "location":
        loc = ctx.get("location_this_turn", {}) or {}
        name = loc.get("name", "") if isinstance(loc, dict) else ""
        loc_id = loc.get("id", "") if isinstance(loc, dict) else ""
        if loc_id and name:
            return f"{loc_id} ({name})"
        elif name:
            return name
        elif loc_id:
            return loc_id
        return None

    # Generic fallback: dot-notation traversal on event dict
    parts = field.split(".")
    current: Any = ev
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def accumulate_intermediate_changes(events: list[dict[str, Any]], turn_a: int, turn_b: int) -> list[dict[str, Any]]:
    from ccya.ev.output import _shorten

    results = []
    for ev in events:
        if not isinstance(ev.get("applied"), dict) and not isinstance(ev.get("changes"), dict):
            continue
        ev_turn = ev.get("turn")
        if ev_turn is None or ev_turn <= turn_a or ev_turn > turn_b:
            continue

        applied = ev.get("applied", {})
        if isinstance(applied, dict) and applied:
            for field in sorted(applied.keys()):
                value = applied[field]
                results.append({"turn": ev_turn, "field": f"applied.{field}", "value": _shorten(value), "source": "applied"})

        changes = ev.get("changes", {})
        if isinstance(changes, dict) and changes:
            for field in sorted(changes.keys()):
                value = changes[field]
                results.append({"turn": ev_turn, "field": f"changes.{field}", "value": _shorten(value), "source": "changes"})

    return results


def is_compaction_event(ev: dict[str, Any]) -> bool:
    """Detect compaction events (sanitizer with empty ruling, etc.).

    Compaction events are events that don't represent a full turn in the pipeline.
    They include sanitizer events with empty ruling,
    and any event where ruling is empty and tokens_in is 0.
    """
    ruling = ev.get("ruling") or {}
    if not ruling:
        return True
    tokens_in = ruling.get("tokens_in", 0)
    if not tokens_in:
        return True
    return False


def assign_scene_ids(events: list[dict[str, Any]]) -> dict[int, int]:
    """Assign scene IDs to events based on location changes and phase resets.

    A new scene starts when:
    - Location changes (detected from state_snapshot or extraction)
    - Phase resets to SETUP (after being in a different phase)

    Returns a dict mapping turn -> scene_id.
    """
    scene_id = 0
    prev_location = None
    prev_phase = None
    turn_to_scene: dict[int, int] = {}

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        # Detect location change
        new_location = None
        pc = ev.get("pacing_context") or {}
        phase = pc.get("scene_phase", "")

        # Check for location in state_snapshot
        ss = ev.get("state_snapshot") or {}
        loc = ss.get("location") or {}
        if isinstance(loc, dict):
            new_location = loc.get("name") or loc.get("id")

        # Check for location in extraction
        if not new_location:
            extraction = ev.get("extraction") or {}
            scene = extraction.get("scene") or {}
            scene_output = scene.get("output") or {}
            if isinstance(scene_output, dict):
                new_location = scene_output.get("location_name") or scene_output.get("location")

        # Detect scene boundary
        is_new_scene = False
        if prev_location is not None and new_location and new_location != prev_location:
            is_new_scene = True
        if prev_phase is not None and phase == "SETUP" and prev_phase != "SETUP":
            is_new_scene = True

        if is_new_scene:
            scene_id += 1

        turn_to_scene[t] = scene_id

        if new_location:
            prev_location = new_location
        if phase:
            prev_phase = phase

    return turn_to_scene
