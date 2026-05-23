#!/usr/bin/env python3
"""Read events.jsonl directly — replacement for curl + jq debug scripts.

Usage:
    ev.py summary [TURN_FILE]          # one-line overview of all turns
    ev.py timing [TURN_FILE]           # token counts and timing per stream
    ev.py turn TURN [TURN_FILE]        # full prompts + outputs for one turn
    ev.py props TURN STREAM [TURN_FILE]  # one stream on one turn
    ev.py compact TURN STREAM [TURN_FILE]  # user + output only
    ev.py prompt TURN STREAM FIELD [TURN_FILE]  # single field
    ev.py outputs TURN [TURN_FILE]     # JSON outputs from all streams
    ev.py deltas TURN [TURN_FILE]      # state diffs and rejections
    ev.py mechanics TURN [TURN_FILE]   # beats, pressures, arcs, connectors
    ev.py connectors TURN [TURN_FILE]  # inter-stream connectors only

Defaults to saves/default/events.jsonl relative to repo root.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_SAVE_DIR = Path("saves/default")
DEFAULT_FILE = DEFAULT_SAVE_DIR / "events.jsonl"

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
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def find_turn(events: list[dict[str, Any]], turn: int) -> dict[str, Any] | None:
    # Prefer actual turn events over auxiliary entries (condition_expired etc.)
    for ev in events:
        if ev.get("turn") == turn and ev.get("kind", "turn") == "turn":
            return ev
    # Fallback to any non-compaction event with matching turn number
    for ev in events:
        if ev.get("turn") == turn and ev.get("kind") != "compaction":
            return ev
    return None


def extract_prompt(ev: dict[str, Any], stream: str) -> dict[str, str]:
    """Extract {system, user, output} for a stream from a raw event."""
    if stream == "ruling":
        blob = ev.get("ruling_prompt") or {}
    elif stream == "narrate":
        blob = ev.get("narrate_prompt") or {}
    else:
        blob = (ev.get("extraction") or {}).get(stream) or {}
    raw_out = blob.get("output", "")
    # JSON outputs (ruling, scene, state, storytell) — pretty-print
    if stream != "narrate":
        if isinstance(raw_out, str):
            try:
                parsed = json.loads(raw_out)
                if isinstance(parsed, dict):
                    raw_out = json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(raw_out, dict):
            raw_out = json.dumps(raw_out, indent=2)
    return {
        "system": blob.get("rendered_system") or "",
        "user": blob.get("rendered_user") or "",
        "output": str(raw_out) if raw_out else "",
    }


def extract_section(text: str | None, *headers: str) -> str:
    """Extract text between two section headers."""
    if not text:
        return ""
    lines = text.splitlines()
    found = False
    result = []
    stop_set = set(headers)
    for line in lines:
        stripped = line.strip()
        if found:
            if stripped in stop_set and stripped != headers[0]:
                break
            if stripped and not stripped.startswith("#"):
                result.append(line)
            elif stripped.startswith("##") and stripped not in stop_set:
                break
        if stripped == headers[0]:
            found = True
    return "\n".join(result).strip()


def extract_section_by_pattern(text: str | None, start_pattern: str, *stop_patterns: str) -> str:
    """Extract text between a start header and the next matching stop header."""
    if not text:
        return ""
    lines = text.splitlines()
    found = False
    result = []
    stop_set = set(stop_patterns)
    for line in lines:
        stripped = line.strip()
        if found:
            if stripped in stop_set:
                break
            if stripped and not stripped.startswith("#"):
                result.append(line)
        if stripped == start_pattern:
            found = True
    return "\n".join(result).strip()


def cmd_summary(events: list[dict[str, Any]]) -> None:
    print("=== Turn Viewer Summary ===\n")
    for ev in events:
        if ev.get("kind") == "compaction":
            continue
        turn = ev.get("turn", "?")
        user_input = (ev.get("input") or "")[:60]
        intent = ""
        ruling_prompt = ev.get("ruling_prompt") or {}
        raw = ruling_prompt.get("output", "")
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                intent = (parsed.get("intent") or "")[:80]
            except (json.JSONDecodeError, ValueError):
                pass
        state_diff = _count_state_diff(ev)
        total_in = _total_tokens_in(ev)
        total_out = _total_tokens_out(ev)
        total_tt = _total_tt(ev)
        print(
            f"Turn {turn}: streams={_stream_keys(ev)} user={user_input} "
            f"tokens: in={total_in} out={total_out} tt={total_tt} "
            f"ruling_intent: {intent} deltas: {state_diff}"
        )


def cmd_timing(events: list[dict[str, Any]]) -> None:
    print("=== Turn Viewer — Timing & Tokens ===\n")
    for ev in events:
        if ev.get("kind") == "compaction":
            continue
        turn = ev.get("turn", "?")
        total_tt = _total_tt(ev)
        total_in = _total_tokens_in(ev)
        total_out = _total_tokens_out(ev)
        print(f"Turn {turn}:")
        print(f"  total_tt: {total_tt}")
        print(f"  tokens_in: {total_in}")
        print(f"  tokens_out: {total_out}")
        for s in STREAMS:
            ms = _stream_ms(ev, s)
            print(f"  {s}: {ms}")
        print()


def cmd_turn(ev: dict[str, Any]) -> None:
    for stream in STREAMS:
        p = extract_prompt(ev, stream)
        print(f"--- BEGIN {stream.upper()} PIPELINE ---")
        print()
        print("--- SYSTEM ---")
        print(p["system"])
        print()
        print("--- USER ---")
        print(p["user"])
        print()
        print("--- OUTPUT ---")
        print(p["output"])
        print()
        print(f"--- END {stream.upper()} PIPELINE ---")
        print()


def cmd_props(ev: dict[str, Any], stream: str) -> None:
    p = extract_prompt(ev, stream)
    print(f"=== Turn {ev['turn']} — {stream} ===\n")
    print("--- SYSTEM ---")
    print(p["system"])
    print()
    print("--- USER ---")
    print(p["user"])
    print()
    print("--- OUTPUT ---")
    print(p["output"])


def cmd_compact(ev: dict[str, Any], stream: str) -> None:
    p = extract_prompt(ev, stream)
    print(f"=== Turn {ev['turn']} — {stream} (user + output only) ===\n")
    print("--- USER ---")
    print(p["user"])
    print()
    print("--- OUTPUT ---")
    print(p["output"])


def cmd_prompt(ev: dict[str, Any], stream: str, field: str) -> None:
    p = extract_prompt(ev, stream)
    print(f"--- Turn {ev['turn']} — {stream} {field} ---")
    print(p.get(field, ""))


def cmd_outputs(ev: dict[str, Any]) -> None:
    for stream in STREAMS:
        p = extract_prompt(ev, stream)
        print(f"--- {stream} output ---")
        print(p["output"])
        print()


def cmd_deltas(ev: dict[str, Any]) -> None:
    print(f"=== Turn {ev['turn']} — State Deltas ===\n")
    state_diff = ev.get("state_diff") or _build_state_diff(ev)
    for entry in state_diff:
        if isinstance(entry, dict):
            print(f"[{entry.get('from_stream', '?')}] {entry.get('domain', '')}.{entry.get('field', '')} = {entry.get('value', '')}")
        else:
            print(entry)
    print()
    print("--- Rejections ---")
    rejections = ev.get("rejected") or []
    if rejections:
        for r in rejections:
            if isinstance(r, dict):
                print(f"  {r.get('field', '?')}: {r.get('reason', '')}")
    else:
        print("  (none)")


def cmd_mechanics(ev: dict[str, Any]) -> None:
    print(f"=== Turn {ev['turn']} — Mechanics ===\n")

    # Rules intent
    print("--- Rules Intent ---")
    intent = _parse_ruling_intent(ev)
    print(json.dumps(intent, indent=2) if intent else "(none)")
    print()

    # Extract storytell user prompt sections
    storytell_event = extract_prompt(ev, "storytell")["user"]

    print("--- GM Beat ---")
    beat = extract_section_by_pattern(storytell_event, "## gm_beat", "## pending_beat", "## pacing_context", "## last_turn_narration")
    print(beat if beat else "(empty)")
    print()

    # Campaign arc from narrate
    print("--- Campaign Arc (from narrate) ---")
    narrate_user = extract_prompt(ev, "narrate")["user"]
    arc = extract_section_by_pattern(narrate_user, "### Campaign Arc", "### Characters")
    print(arc if arc else "(empty)")
    print()

    # State deltas
    print("--- State Deltas ---")
    state_diff = ev.get("state_diff") or _build_state_diff(ev)
    if state_diff:
        for entry in state_diff:
            if isinstance(entry, dict):
                print(f"  [{entry.get('from_stream', '?')}] {entry.get('domain', '')}.{entry.get('field', '')} = {entry.get('value', '')}")
            else:
                print(f"  {entry}")
    else:
        print("  (none)")
    print()

    # Connectors
    print("--- Connectors ---")
    connectors = _extract_connectors(ev)
    if connectors:
        for conn in connectors:
            print(f"before_stage: {conn.get('before_stage', '?')}")
            for seg in conn.get("segments", []):
                print(f"  from={seg.get('from', '?')} label={seg.get('label', '')}")
                for line in seg.get("lines", []):
                    if isinstance(line, dict):
                        print(f"    {line.get('k', '?')} = {line.get('v', '')}")
                    else:
                        print(f"    {line}")
    else:
        print("  (none)")
    print()

    # Summary
    print("--- Summary ---")
    total_tt = _total_tt(ev)
    total_in = _total_tokens_in(ev)
    total_out = _total_tokens_out(ev)
    has_retries = _has_retries(ev)
    has_errors = _has_errors(ev)
    has_rejections = _has_rejections(ev)
    print(
        f"  streams: {_stream_keys(ev)} "
        f"has_rejections: {has_rejections} "
        f"has_retries: {has_retries} "
        f"has_errors: {has_errors} "
        f"total_tt: {total_tt} "
        f"tokens_in: {total_in} "
        f"tokens_out: {total_out}"
    )


def cmd_connectors(ev: dict[str, Any]) -> None:
    connectors = _extract_connectors(ev)
    if connectors:
        for conn in connectors:
            print(f"before_stage: {conn.get('before_stage', '?')}")
            for seg in conn.get("segments", []):
                print(f"  from={seg.get('from', '?')} label={seg.get('label', '')}")
                for line in seg.get("lines", []):
                    if isinstance(line, dict):
                        print(f"    {line.get('k', '?')} = {line.get('v', '')}")
                    else:
                        print(f"    {line}")
    else:
        print("(none)")


# ── helpers ───────────────────────────────────────────────────────────────

def _count_state_diff(ev: dict[str, Any]) -> int:
    sd = ev.get("state_diff") or _build_state_diff(ev)
    return len(sd) if sd else 0


def _build_state_diff(ev: dict[str, Any]) -> list:
    """Reproduce tv._tv_state_diff logic at a minimum."""
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
        skip = {"actions", "location_description", "scene_tags", "scene_tagline"}
        for fk, val in parsed.items():
            if fk in skip or val is None:
                continue
            if isinstance(val, (list, dict)) and not val:
                continue
            if fk.endswith("_add"):
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


def _get_nested(d: dict, path: str) -> Any | None:
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _try_parse_json(raw: str) -> dict | None:
    s = raw.strip()
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, ValueError):
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = json.loads(s[i : j + 1])
                return out if isinstance(out, dict) else None
            except (json.JSONDecodeError, ValueError):
                return None
    return None


def _parse_ruling_intent(ev: dict[str, Any]) -> dict | None:
    raw = (ev.get("ruling_prompt") or {}).get("output", "")
    if isinstance(raw, str):
        return _try_parse_json(raw)
    return raw if isinstance(raw, dict) else None


def _stream_keys(ev: dict[str, Any]) -> str:
    parts = []
    for s in STREAMS:
        blob = _get_nested(ev, _metrics_path(s)) or {}
        if blob and (blob.get("tokens_in") or blob.get("ms")):
            parts.append(s)
    return ", ".join(parts) if parts else "(none)"


def _metrics_path(stream: str) -> str:
    if stream == "ruling":
        return "ruling"
    elif stream == "narrate":
        return "narrate"
    else:
        return f"extraction.{stream}"


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


def _extract_connectors(ev: dict[str, Any]) -> list[dict]:
    """Reproduce tv._turn_viewer_data connector generation."""
    connectors = []
    # Define inputs per stream (matches tv_mirror._STREAMS)
    stream_inputs = {
        "ruling": [],
        "narrate": ["ruling"],
        "scene": ["ruling", "narrate"],
        "state": ["ruling", "narrate", "scene"],
        "storytell": ["ruling", "narrate", "scene", "state"],
    }
    # Output types per stream
    is_text = {"narrate": True}

    for sd in STREAMS:
        inputs = stream_inputs.get(sd, [])
        if not inputs:
            continue
        segments = []
        for inp_key in inputs:
            inp_path = "narrate_prompt" if inp_key == "narrate" else ("ruling_prompt" if inp_key == "ruling" else f"extraction.{inp_key}")
            inp_blob = _get_nested(ev, inp_path) or {}
            if not isinstance(inp_blob, dict):
                inp_blob = {}
            raw_out = inp_blob.get("output")

            if is_text.get(inp_key):
                seg_lines = [{"k": "chars", "v": str(len(str(raw_out or ""))), "dim": not raw_out},
                             {"k": "text", "v": str(raw_out or "")[:150], "dim": False}]
            else:
                parsed = _try_parse_json(raw_out) if isinstance(raw_out, str) else (raw_out if isinstance(raw_out, dict) else None)
                if parsed and isinstance(parsed, dict):
                    seg_lines = _dict_to_lines(parsed)
                elif parsed:
                    seg_lines = [{"k": "_", "v": str(parsed), "dim": False}]
                else:
                    seg_lines = [{"k": "_", "v": str(raw_out or ""), "dim": False}] if raw_out else []

            segments.append({
                "from": inp_key,
                "label": f"{inp_key} \u2192 {sd}",
                "lines": seg_lines,
                "anchor": inp_key,
            })
        connectors.append({"before_stage": sd, "segments": segments})
    return connectors


def _dict_to_lines(d: dict, max_str: int = 150) -> list[dict]:
    lines = []
    for k, v in d.items():
        if v is None:
            lines.append({"k": k, "v": "null", "dim": True})
        elif isinstance(v, bool):
            lines.append({"k": k, "v": str(v).lower(), "dim": not v})
        elif isinstance(v, list):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            elif all(isinstance(x, (str, int, float)) for x in v):
                joined = ", ".join(str(x) for x in v)
                lines.append({"k": k, "v": joined[:max_str] + ("\u2026" if len(joined) > max_str else "")})
            elif all(isinstance(x, dict) for x in v):
                labels = []
                for x in v:
                    for key in ("id", "name", "text", "label"):
                        val = x.get(key)
                        if val and isinstance(val, str):
                            labels.append(val[:60])
                            break
                summary = ", ".join(lbl for lbl in labels if lbl)
                display = f"[{len(v)}] {summary}" if summary else f"[{len(v)}]"
                lines.append({"k": k, "v": display[:max_str]})
            else:
                lines.append({"k": k, "v": f"[{len(v)} items]"})
        elif isinstance(v, dict):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            else:
                for sk, sv in v.items():
                    sub_k = f"{k}.{sk}"
                    if sv is None:
                        lines.append({"k": sub_k, "v": "null", "dim": True})
                    elif isinstance(sv, str):
                        lines.append({"k": sub_k, "v": sv[:max_str] + ("\u2026" if len(sv) > max_str else "")})
                    else:
                        lines.append({"k": sub_k, "v": str(sv)[:max_str]})
        elif isinstance(v, str):
            lines.append({"k": k, "v": v[:max_str] + ("\u2026" if len(v) > max_str else "")})
        else:
            lines.append({"k": k, "v": str(v)})
    return lines


# ── main ──────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        sys.exit(0)

    cmd = args[0]

    # Determine events file
    if len(args) > 1 and args[-1].startswith("saves/"):
        turn_file = Path(args[-1])
        args = args[:-1]
    else:
        turn_file = DEFAULT_FILE

    events = load_events(turn_file)

    match cmd:
        case "summary":
            cmd_summary(events)
        case "timing":
            cmd_timing(events)
        case "turn":
            turn = int(args[1]) if len(args) > 1 else None
            ev = find_turn(events, turn) if turn else None
            if not ev:
                print(f"Turn {turn} not found (or is a compaction entry)")
                sys.exit(1)
            cmd_turn(ev)
        case "props":
            turn = int(args[1])
            stream = args[2]
            if stream not in STREAMS:
                print(f"Unknown stream: {stream}", file=sys.stderr)
                sys.exit(1)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_props(ev, stream)
        case "compact":
            turn = int(args[1])
            stream = args[2]
            if stream not in STREAMS:
                print(f"Unknown stream: {stream}", file=sys.stderr)
                sys.exit(1)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_compact(ev, stream)
        case "prompt":
            turn = int(args[1])
            stream = args[2]
            field = args[3]
            if stream not in STREAMS:
                print(f"Unknown stream: {stream}", file=sys.stderr)
                sys.exit(1)
            if field not in ("system", "user", "output"):
                print(f"Unknown field: {field}", file=sys.stderr)
                sys.exit(1)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_prompt(ev, stream, field)
        case "outputs":
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_outputs(ev)
        case "deltas":
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_deltas(ev)
        case "mechanics":
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_mechanics(ev)
        case "connectors":
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_connectors(ev)
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__.strip())
            sys.exit(1)


if __name__ == "__main__":
    main()
