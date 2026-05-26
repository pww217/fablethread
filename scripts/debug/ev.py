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
    ev.py mechanics TURN [TURN_FILE]   # beats, rules, pacing, threads, arcs, connectors
    ev.py connectors TURN [TURN_FILE]   # inter-stream connectors only
    ev.py pacing TURN [TURN_FILE]       # pacing context: summary, gate, momentum, band, beat_locked
    ev.py state [--format MODE] [--save-dir PATH]  # show current game state from state.yaml
    ev.py diff TURN-A TURN-B [--section SEC]       # compare two turns
    ev.py trace FIELD [--from N] [--to M]          # show field across turn range
    ev.py search <expr> [<expr> ...]               # structured cross-turn search

Defaults to saves/default/events.jsonl relative to repo root.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_SAVE_DIR = Path("saves/default")
DEFAULT_FILE = DEFAULT_SAVE_DIR / "events.jsonl"

STREAMS = ("ruling", "narrate", "scene", "state", "storytell")


SECTION_MARKERS: dict[str, str] = {
    "campaign_arc": r"^#{1,3}\s*Campaign Arc$",
    "rules_outcome": r"^## rules_outcome$",
    "pacing_context": r"^## pacing_context$",
    "player_intent": r"^## player_intent$",
    "threads": r"^## threads",
    "last_turn_narration": r"^## last_turn_narration",
    "current_narration": r"^## CURRENT TURN",
    "end_narration": r"^## END CURRENT TURN",
    # Reserved as stop markers — not used as start markers currently
    "characters": r"^## characters$",
    "location": r"^## location$",
    "inventory": r"^## Current inventory",
    "recent_events": r"^## recent_events",
}

# Compiled once at module load
_COMPILED_SECTIONS: dict[str, re.Pattern] = {
    name: re.compile(pattern) for name, pattern in SECTION_MARKERS.items()
}


STREAM_ALIASES: dict[str, str] = {
    "rules": "ruling",
    "ruling": "ruling",
    "progress": "storytell",
    "storytell": "storytell",
    "narrate": "narrate",
    "scene": "scene",
    "state": "state",
}


def _resolve_stream(name: str) -> str:
    """Map a user-facing stream name to the canonical data-model key. Dies on unknown names."""
    canonical = STREAM_ALIASES.get(name)
    if not canonical:
        print(f"Unknown stream: {name}. Valid: {', '.join(sorted(STREAM_ALIASES))}", file=sys.stderr)
        sys.exit(1)
    return canonical


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


def _strip_flags(args: list[str]) -> tuple[dict[str, str], list[str]]:
    """Separate --flags from positional args. Returns (flags dict, positional args).

    Handles:
      --key value     → {"key": "value"}
      --flag          → {"flag": "true"}
    """
    flags: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                flags[name] = args[i + 1]
                i += 2
            else:
                flags[name] = "true"
                i += 1
        else:
            positional.append(a)
            i += 1
    return flags, positional


def load_state_yaml(save_dir: Path | None = None) -> dict[str, Any]:
    """Load and parse state.yaml from the save directory."""
    if save_dir is None:
        save_dir = DEFAULT_SAVE_DIR
    path = save_dir / "state.yaml"
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    import yaml

    with open(path) as f:
        result = yaml.safe_load(f)
        if isinstance(result, dict):
            return result
        print(f"Error: {path} is not a valid state YAML", file=sys.stderr)
        sys.exit(1)


def load_extraction_context(ev: dict[str, Any]) -> dict[str, Any] | None:
    """Return the extraction_context sub-dict from an event, or None."""
    ctx = ev.get("extraction_context")
    if isinstance(ctx, dict) and ctx:
        return ctx
    return None


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


def extract_section_by_pattern(text: str | None, start_name: str, *stop_names: str) -> str:
    """Extract text between a section header (matched by name from SECTION_MARKERS) and the next stop header."""
    if not text or start_name not in _COMPILED_SECTIONS:
        return ""
    start_re = _COMPILED_SECTIONS[start_name]
    stop_re_list = [_COMPILED_SECTIONS.get(s) for s in stop_names if s in _COMPILED_SECTIONS]

    lines = text.splitlines()
    found = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if found:
            # Stop if we hit any of the stop markers
            if any(r.search(stripped) for r in stop_re_list if r):
                break
            # Skip future headers that aren't stop markers
            if stripped.startswith("#") and not any(r.search(stripped) for r in stop_re_list if r):
                continue
            if stripped:
                result.append(line)
        elif start_re.search(stripped):
            found = True
    return "\n".join(result).strip()


def cmd_summary(events: list[dict[str, Any]], format: str = "text") -> None:
    if format == "json":
        for ev in events:
            if ev.get("kind") == "compaction":
                continue
            obj = _build_summary_json(ev)
            print(json.dumps(obj))
        return
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



def _build_summary_json(ev: dict[str, Any]) -> dict[str, Any]:
    """Build a structured summary dict for one event for JSON output. All numeric fields are native types."""
    intent = _parse_ruling_intent(ev) or {}
    raw_tt = _total_tt(ev)
    return {
        "turn": ev.get("turn"),
        "streams": _stream_keys(ev),
        "user_input": (ev.get("input") or "")[:100],
        "tokens_in": int(_total_tokens_in(ev)),
        "tokens_out": int(_total_tokens_out(ev)),
        "total_tt_s": float(raw_tt.rstrip("s")) if raw_tt else 0.0,
        "ruling_intent": (intent.get("intent") or "")[:100],
        "deltas": int(_count_state_diff(ev)),
        "has_rejections": bool(_has_rejections(ev)),
    }



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
    narrate_user = extract_prompt(ev, "narrate")["user"]

    print("--- GM Beat ---")
    # Pending (carried from prior turn, consumed by narrator)
    pending_beat_match = re.search(r"\*\*Beat type:\*\*\s*(.+)", narrate_user) if narrate_user else None
    if pending_beat_match:
        print(f"  Pending (to narrate): {pending_beat_match.group(1)}")
    else:
        print("  Pending (to narrate): (none)")
    # Generated (created this turn, stored for next turn)
    storytell_output_raw = extract_prompt(ev, "storytell")["output"]
    generated_beat = None
    if storytell_output_raw:
        try:
            so = json.loads(storytell_output_raw)
            generated_beat = so.get("gm_beat")
        except (json.JSONDecodeError, TypeError):
            pass
    if generated_beat:
        print("  Generated (stored):", generated_beat)
    else:
        print("  Generated (stored): (none)")
    print()

    print("--- Rules Outcome ---")
    rules = extract_section_by_pattern(storytell_event, "rules_outcome", "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    if not rules:
        # Fallback: extract band from narrate prompt
        band_match = re.search(r"\*\*Band:\*\*\s*(.+?)(?:\s*→|$)", narrate_user) if narrate_user else None
        if band_match:
            rules = band_match.group(0)
    print(rules if rules else "(empty)")
    print()

    print("--- Pacing Context ---")
    pacing = extract_section_by_pattern(storytell_event, "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    print(pacing if pacing else "(empty)")
    print()

    print("--- Active Threads (from storytell) ---")
    threads = extract_section_by_pattern(storytell_event, "threads", "recent_events", "inventory", "rules_outcome", "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    if threads:
        for line in threads.splitlines():
            print(f"  {line.strip()}")
    else:
        print("  (none)")
    print()

    # Campaign arc from narrate
    print("--- Campaign Arc (from narrate) ---")
    narrate_user = extract_prompt(ev, "narrate")["user"]
    arc = extract_section_by_pattern(narrate_user, "campaign_arc")
    print(arc if arc else "(empty)")
    print()

    # Narrative output (player received)
    print("--- Narrative (player received) ---")
    narrate_output = extract_prompt(ev, "narrate")["output"]
    if narrate_output and len(narrate_output) > 500:
        print(narrate_output[:500])
        print("…")
        print(f"(full text: python3 scripts/debug/ev.py compact {ev.get('turn', '?')} narrate)")
    elif narrate_output:
        print(narrate_output)
    else:
        print("(empty)")
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


def cmd_pacing(ev: dict[str, Any]) -> None:
    """Display pacing context from events.jsonl directly."""
    print(f"=== Turn {ev['turn']} — Pacing Context ===\n")

    # Read from top-level event fields (always available)
    pacing_ctx = ev.get("pacing_context") or {}
    momentum_before = ev.get("momentum_before")
    momentum_after = ev.get("momentum_after")
    band_label = (ev.get("ruling") or {}).get("band", "")

    # Summary
    summary = pacing_ctx.get("summary", "")
    if summary:
        print(f"  summary: {summary}")
    else:
        print("  summary: (none)")

    # Gate
    gate = pacing_ctx.get("gate", "allow")
    if gate and gate != "allow":
        print(f"  gate: {gate}")
    else:
        print("  gate: allow")

    # Momentum
    if momentum_before is not None or momentum_after is not None:
        mb = momentum_before if momentum_before is not None else "?"
        ma = momentum_after if momentum_after is not None else "?"
        delta = (momentum_after - momentum_before) if (momentum_before is not None and momentum_after is not None) else None
        delta_str = f" ({delta:+d})" if delta is not None else ""
        print(f"  momentum: {mb} → {ma}{delta_str}")
    else:
        print("  momentum: (none)")

    # Beat locked
    beat_locked = pacing_ctx.get("beat_locked", False)
    if beat_locked:
        print("  beat_locked: true")

    # Band (only on roll turns, from ruling event)
    if band_label:
        print(f"  band: {band_label}")


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


def format_state(state: dict[str, Any], fmt: str = "full") -> None:
    """Render state.yaml content in the requested format."""
    turn_num = (state.get("meta") or {}).get("turn", "?")

    if fmt == "compact":
        pc_name = (state.get("pc") or {}).get("name", "?")
        loc_name = (state.get("location") or {}).get("name", "?")
        print(f"Turn {turn_num}: {pc_name} @ {loc_name}")
        return

    if fmt == "pc":
        _render_pc_section(state)
        return

    if fmt == "inventory":
        _render_inventory_section(state)
        return

    if fmt == "location":
        _render_location_section(state)
        return

    if fmt == "scene":
        _render_scene_section(state)
        return

    if fmt == "arc":
        _render_arc_section(state)
        return

    if fmt == "npcs":
        _render_npcs_section(state)
        return

    if fmt == "compidx":
        _render_compidx_section(state)
        return

    # full mode: all sections in order
    print(f"Turn {turn_num}")
    print()
    pc = state.get("pc") or {}
    if pc:
        _render_pc_section(state)
    inv = state.get("inventory")
    if inv:
        _render_inventory_section(state)
    loc = state.get("location")
    if loc:
        _render_location_section(state)
    scene = state.get("scene") or {}
    if any(scene.get(k) for k in ("tags", "tagline", "recently_left", "recent_events")):
        _render_scene_section(state)
    arc = state.get("arc") or {}
    if any(arc.get(k) for k in ("visible_goal", "thematic_question", "threads", "completed_threads", "hidden_truths", "discovered_truths")):
        _render_arc_section(state)
    compendium_npcs = (state.get("compendium") or {}).get("npcs")
    if compendium_npcs:
        _render_npcs_section(state)


def _render_pc_section(state: dict[str, Any]) -> None:
    pc = state.get("pc", {})
    print("--- PC ---")
    name = pc.get("name") or "?"
    tagline = pc.get("tagline") or ""
    if tagline:
        print(f"  {name} — {tagline}")
    else:
        print(f"  {name}")
    stats = pc.get("stats", {})
    if isinstance(stats, dict) and stats:
        stat_parts = ", ".join(f"{k}: {v}" for k, v in sorted(stats.items()))
        print(f"  Stats: {stat_parts}")
    momentum = pc.get("momentum")
    if momentum is not None:
        print(f"  Momentum: {momentum:+d}")
    conditions = pc.get("conditions", []) or []
    if conditions:
        for c in conditions:
            label = (c.get("label") or c.get("id") or "?") if isinstance(c, dict) else str(c)
            ttl = ""
            if isinstance(c, dict):
                remaining = c.get("turns_remaining")
                if remaining is not None:
                    ttl = f" ({remaining} turns left)"
            print(f"  Condition: {label}{ttl}")


def _render_inventory_section(state: dict[str, Any]) -> None:
    inventory = state.get("inventory", []) or []
    print("--- Inventory ---")
    if not inventory:
        print("  (empty)")
        return
    for item in sorted(inventory, key=lambda x: ("0" if isinstance(x, dict) and x.get("id") == "credits" else "1", (x.get("name") or x.get("id") or "").lower())):
        name = (item.get("name") or item.get("id") or "?") if isinstance(item, dict) else str(item)
        amount = item.get("amount", 1) if isinstance(item, dict) else 1
        notes = item.get("notes", "") if isinstance(item, dict) else ""
        line = f"  {name} ×{amount}"
        if notes:
            line += f" ({notes})"
        print(line)


def _render_location_section(state: dict[str, Any]) -> None:
    loc = state.get("location", {}) or {}
    print("--- Location ---")
    name = loc.get("name") or loc.get("id") or "?"
    desc = loc.get("description", "") or ""
    if desc:
        print(f"  {name}")
        for line in _wrap_text(desc, indent=4):
            print(line)
    else:
        print(f"  {name}")


def _render_scene_section(state: dict[str, Any]) -> None:
    scene = state.get("scene", {}) or {}
    print("--- Scene ---")
    tags = scene.get("tags", []) or []
    if tags:
        print(f"  Tags: {', '.join(str(t) for t in tags)}")
    tagline = scene.get("tagline") or ""
    if tagline:
        print(f"  Tagline: {tagline}")
    compendium = state.get("compendium", {}) or {}
    npcs = compendium.get("npcs", {}) or {}
    present_npcs = {k: v for k, v in npcs.items() if isinstance(v, dict) and v.get("presence") == "present"}
    if present_npcs:
        print("  Present NPCs:")
        for npc_id, npc in sorted(present_npcs.items()):
            name = (npc.get("name") or "[Unnamed]") if isinstance(npc, dict) else "[Unnamed]"
            print(f"    {npc_id}: {name}")
    recently_left = scene.get("recently_left", []) or []
    if recently_left:
        left_names = [f"{(n.get('id') or '?')} {(n.get('name') or '')}" for n in recently_left if isinstance(n, dict)]
        print("  Recently left:")
        for ln in left_names:
            print(f"    {ln}")


def _render_arc_section(state: dict[str, Any]) -> None:
    arc = state.get("arc", {}) or {}
    print("--- Arc ---")
    goal = arc.get("visible_goal") or ""
    if goal:
        print(f"  Goal: {goal}")
    question = arc.get("thematic_question") or ""
    if question:
        print(f"  Question: {question}")
    threads = arc.get("threads", []) or []
    active_threads = [t for t in threads if isinstance(t, dict) and t.get("active")]
    completed = arc.get("completed_threads", []) or []
    discovered = arc.get("discovered_truths", []) or []
    hidden = arc.get("hidden_truths", []) or []
    if active_threads:
        print("  Active threads:")
        for t in active_threads:
            text = (t.get("text") or "?") if isinstance(t, dict) else "?"
            progress = t.get("progress", "") if isinstance(t, dict) else ""
            line = f"    {text}"
            if progress:
                line += f" ({progress})"
            print(line)
    if completed:
        comp_names = [f"{(t.get('text') or '?')}" for t in completed if isinstance(t, dict)]
        print("  Completed threads:")
        for cn in comp_names:
            print(f"    {cn}")
    if discovered:
        print("  Discovered truths:")
        for dt in discovered:
            print(f"    - {dt}")
    if hidden:
        print("  Hidden truths (not shown to player):")
        for ht in hidden:
            print(f"    ? {ht}")


def _render_npcs_section(state: dict[str, Any]) -> None:
    compendium = state.get("compendium", {}) or {}
    npcs = compendium.get("npcs", {}) or {}
    if not isinstance(npcs, dict):
        return
    print("--- Compendium NPCs ---")
    for npc_id in sorted(npcs.keys()):
        npc = npcs[npc_id]
        name = (npc.get("name") or "?") if isinstance(npc, dict) else "?"
        title = (npc.get("title") or "") if isinstance(npc, dict) else ""
        line = f"  {npc_id}: {name}"
        if title:
            line += f" — {title}"
        print(line)


def _render_compidx_section(state: dict[str, Any]) -> None:
    compendium = state.get("compendium", {}) or {}
    npcs = compendium.get("npcs", {}) or {}
    if not isinstance(npcs, dict):
        return
    print("--- NPC Index ---")
    for npc_id in sorted(npcs.keys()):
        npc = npcs[npc_id]
        name = (npc.get("name") or "?") if isinstance(npc, dict) else "?"
        title = (npc.get("title") or "") if isinstance(npc, dict) else ""
        print(f"  {npc_id:<25} {name}{f' ({title})' if title else ''}")


def _wrap_text(text: str, indent: int = 0) -> list[str]:
    """Wrap text to a reasonable line width with indentation."""
    import textwrap

    lines = []
    for para in text.splitlines():
        wrapped = textwrap.fill(para.strip(), width=80 - indent if indent else 80, initial_indent=" " * indent, subsequent_indent=" " * indent) if para.strip() else ""
        if wrapped:
            lines.append(wrapped)
    return lines


def diff_extraction_context(ctx_a: dict[str, Any], ctx_b: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare two extraction_context dicts. Returns structured diffs."""
    field_map = {
        "inventory_this_turn": ("Inventory", _diff_inventory),
        "conditions_this_turn": ("Conditions", _diff_conditions),
        "location_this_turn": ("Location", _diff_location),
        "scene_tags_this_turn": ("Scene Tags", _diff_scene_tags),
    }
    results = []
    for key, (section_name, diff_fn) in field_map.items():
        val_a = ctx_a.get(key) or []
        val_b = ctx_b.get(key) or []
        if not isinstance(val_a, list):
            val_a = []
        if not isinstance(val_b, list):
            val_b = []
        changed = diff_fn(section_name, val_a, val_b)
        results.append(changed)
    return results


def _diff_inventory(section: str, before: list[dict], after: list[dict]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _item_map(items):
        return {(item.get("id", "")): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _item_map(before)
    am = _item_map(after)
    bid_ids = set(bm.keys())
    aid_ids = set(am.keys())

    added = sorted(aid_ids - bid_ids)
    removed = sorted(bid_ids - aid_ids)
    common = bid_ids & aid_ids

    if not added and not removed:
        # Check amount changes in common items
        amt_changes = []
        for iid in common:
            ba = int((bm[iid].get("amount") or 1))
            aa = int((am[iid].get("amount") or 1))
            if ba != aa:
                bname = bm[iid].get("name", "") if isinstance(bm[iid], dict) else ""
                amt_changes.append({"kind": "changed", "label": f"{iid} {bname}: ×{ba} → ×{aa}"})
        if not amt_changes:
            return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    changes = []
    for iid in added:
        item = am[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"+{iid}"
        if name:
            label += f" {name} ×{amt}"
        changes.append({"kind": "added", "label": label})

    for iid in removed:
        item = bm[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"-{iid}"
        if name:
            label += f" {name} ×{amt}"
        changes.append({"kind": "removed", "label": label})

    for iid in common:
        ba = int((bm[iid].get("amount") or 1))
        aa = int((am[iid].get("amount") or 1))
        if ba != aa:
            bname = bm[iid].get("name", "") if isinstance(bm[iid], dict) else ""
            changes.append({"kind": "changed", "label": f"{iid} {bname}: ×{ba} → ×{aa}"})

    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": changes}


def _diff_conditions(section: str, before: list[dict], after: list[dict]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _cond_map(items):
        return {(item.get("id", "")): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _cond_map(before)
    am = _cond_map(after)
    bid_ids = set(bm.keys())
    aid_ids = set(am.keys())

    added = sorted(aid_ids - bid_ids)
    removed = sorted(bid_ids - aid_ids)

    if not added and not removed:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    changes = []
    for cid in added:
        c = am[cid]
        label = f"+{cid}"
        if isinstance(c, dict):
            lbl = c.get("label") or ""
            if lbl:
                label += f" {lbl}"
        changes.append({"kind": "added", "label": label})

    for cid in removed:
        c = bm[cid]
        label = f"-{cid}"
        if isinstance(c, dict):
            lbl = c.get("label") or ""
            if lbl:
                label += f" {lbl}"
        changes.append({"kind": "removed", "label": label})

    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": changes}


def _diff_location(section: str, before: list[dict], after: list[dict]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _loc_info(items):
        return [(item.get("id", ""), item.get("name", "")) for item in items if isinstance(item, dict)]

    # Location is typically a single entry; compare by id+name
    b_id = before[0].get("id", "") if len(before) > 0 and isinstance(before[0], dict) else ""
    b_name = before[0].get("name", "") if len(before) > 0 and isinstance(before[0], dict) else ""
    a_id = after[0].get("id", "") if len(after) > 0 and isinstance(after[0], dict) else ""
    a_name = after[0].get("name", "") if len(after) > 0 and isinstance(after[0], dict) else ""

    if b_id == a_id and b_name == a_name:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    label = f"{b_name or b_id} → {a_name or a_id}"
    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": [{"kind": "changed", "label": label}]}


def _diff_scene_tags(section: str, before: list[dict], after: list[dict]) -> dict[str, Any]:
    if not isinstance(before, list):
        before = []
    if not isinstance(after, list):
        after = []

    def _tag_names(items):
        return sorted([item.get("name", "") or item.get("id", "") for item in items if isinstance(item, dict)])

    bt = set(_tag_names(before))
    at = set(_tag_names(after))

    added_tags = sorted(at - bt)
    removed_tags = sorted(bt - at)

    if not added_tags and not removed_tags:
        return {"section": section, "kind": "unchanged", "before_value": before, "after_value": after}

    changes = []
    for t in added_tags:
        changes.append({"kind": "added", "label": f"+{t}"})
    for t in removed_tags:
        changes.append({"kind": "removed", "label": f"-{t}"})

    return {"section": section, "kind": "changed", "before_value": before, "after_value": after, "changes": changes}


def accumulate_intermediate_changes(events: list[dict[str, Any]], turn_a: int, turn_b: int) -> list[dict[str, Any]]:
    """Collect applied + changes from events between turn_a and turn_b (exclusive of turn_a, inclusive of turn_b).

    Returns list of {turn, field, value, source} dicts."""
    results = []
    for ev in events:
        if not isinstance(ev.get("applied"), dict) and not isinstance(ev.get("changes"), dict):
            continue
        ev_turn = ev.get("turn")
        if ev_turn is None or ev_turn <= turn_a or ev_turn > turn_b:
            continue

        # Process applied fields
        applied = ev.get("applied", {})
        if isinstance(applied, dict) and applied:
            for field in sorted(applied.keys()):
                value = applied[field]
                results.append({"turn": ev_turn, "field": f"applied.{field}", "value": _shorten(value), "source": "applied"})

        # Process changes fields (exclusive categories only)
        changes = ev.get("changes", {})
        if isinstance(changes, dict) and changes:
            for field in sorted(changes.keys()):
                value = changes[field]
                results.append({"turn": ev_turn, "field": f"changes.{field}", "value": _shorten(value), "source": "changes"})

    return results


def _shorten(value: Any) -> str:
    """Shorten a value for display."""
    if isinstance(value, dict):
        keys = list(value.keys())[:3]
        rest = f" (+{len(value) - 3} more)" if len(value) > 3 else ""
        return "{" + ", ".join(str(k) for k in keys) + "}" + rest
    elif isinstance(value, list):
        if not value:
            return "[]"
        first = str(value[0])[:80]
        rest = f" (+{len(value) - 1} more)" if len(value) > 1 else ""
        return f"[{first}{rest}]"
    elif isinstance(value, str):
        return value[:200] + ("…" if len(value) > 200 else "")
    else:
        return str(value)[:200]


def format_diff_output(diff_results: list[dict[str, Any]], intermediate_changes: list[dict[str, Any]], turn_a: int, turn_b: int, section_filter: str | None = None) -> None:
    """Format the diff output for display."""
    print(f"diff {turn_a} {turn_b}")

    if not any(r["kind"] == "changed" for r in diff_results):
        if not intermediate_changes:
            print()
            print("(no changes detected between turn {} and turn {})".format(turn_a, turn_b))
            return

    # Print snapshot diffs by section
    sections_order = ["Inventory", "Conditions", "Location", "Scene Tags"]
    for expected_section in sections_order:
        if section_filter is not None:
            filter_map = {"npcs": "NPCs", "inventory": "Inventory", "conditions": "Conditions", "location": "Location", "tags": "Scene Tags", "applied": None}
            if filter_map.get(section_filter) != expected_section:
                continue

        matching = [r for r in diff_results if r["section"] == expected_section]
        if not matching:
            continue

        result = matching[0]
        print()
        print(f"--- {expected_section} ---")

        if result["kind"] == "unchanged":
            # Show the single unchanged item for context
            before_val = result.get("before_value", [])
            after_val = result.get("after_value", [])
            if expected_section == "Inventory":
                _print_unchanged_inventory(before_val, after_val)
            elif expected_section == "Conditions":
                _print_unchanged_conditions(before_val)
            elif expected_section == "Location":
                if before_val:
                    loc = before_val[0] if isinstance(before_val[0], dict) else {}
                    print(f"  {loc.get('name', loc.get('id', '?'))}")
            elif expected_section == "Scene Tags":
                _print_unchanged_tags(before_val)

        elif result["kind"] == "changed":
            changes = result.get("changes", [])
            if not changes:
                print("  (no details)")
            else:
                for c in changes:
                    label = c.get("label", "")
                    # Labels already contain +/- prefix from diff functions
                    print(f"  {label}")

    # Print intermediate changes (applied + changes from turns between A and B)
    if section_filter != "applied":
        print()
        print("--- Also changed (from applied/changes in intermediate turns) ---")
        if not intermediate_changes:
            print("  (none)")
        else:
            for ic in intermediate_changes:
                field = ic["field"]
                value = str(ic.get("value", ""))[:100]
                turn = ic["turn"]
                # Shorten display based on source and field type
                if "applied." in field:
                    applied_field = field.replace("applied.", "")
                    print(f"  turn {turn}: {applied_field} → {_shorten_value(value)}")
                else:
                    changes_field = field.replace("changes.", "")
                    print(f"  turn {turn}: {changes_field} ({_shorten_value(value)})")

    # Print not-tracked section
    if section_filter is None or section_filter == "not_tracked":
        print()
        print("--- Not tracked in historical snapshots ---")
        print("pc.stats, pc.name, compendium.npcs, arc.threads")


def _print_unchanged_inventory(before: list[dict], after: list[dict]) -> None:
    def _item_map(items):
        return {(item.get("id", "")): item for item in items if isinstance(item, dict) and item.get("id")}

    bm = _item_map(before)
    am = _item_map(after)
    common_ids = sorted(set(bm.keys()) & set(am.keys()))

    if not common_ids:
        print("  (none)")
        return

    for iid in common_ids:
        item = bm[iid]
        name = item.get("name", "") if isinstance(item, dict) else ""
        amt = int((item.get("amount") or 1))
        label = f"{iid}"
        if name:
            label += f" {name} ×{amt}"
        print(f"  {label}")


def _print_unchanged_conditions(items: list[dict]) -> None:
    if not items:
        print("  (none)")
        return
    for item in items:
        if isinstance(item, dict):
            label = f"{item.get('id', '?')}"
            lbl = item.get("label", "") or ""
            if lbl:
                label += f" {lbl}"
            print(f"  {label}")


def _print_unchanged_tags(items: list[dict]) -> None:
    if not items:
        print("  (none)")
        return
    names = [item.get("name", "") or item.get("id", "") for item in items if isinstance(item, dict)]
    print(f"  {', '.join(names)}")


def _shorten_value(value: str) -> str:
    if len(value) > 60:
        return value[:57] + "…"
    return value


def cmd_state(fmt: str = "full", save_dir_path: Path | None = None) -> None:
    """Handle the 'state' command."""
    state = load_state_yaml(save_dir_path)
    format_state(state, fmt)


def cmd_diff(events: list[dict[str, Any]], turn_a: int | None, turn_b: int | None, section_filter: str | None = None) -> None:
    """Handle the 'diff' command."""
    if turn_a is None or turn_b is None:
        print("Error: diff requires two turn numbers", file=sys.stderr)
        sys.exit(1)

    if turn_b <= turn_a:
        print(f"Error: turn-B ({turn_b}) must be greater than turn-A ({turn_a})", file=sys.stderr)
        sys.exit(1)

    ev_a = find_turn(events, turn_a)
    if not ev_a:
        print(f"Turn {turn_a} not found (or is a compaction entry)", file=sys.stderr)
        sys.exit(1)

    ev_b = find_turn(events, turn_b)
    if not ev_b:
        print(f"Turn {turn_b} not found", file=sys.stderr)
        sys.exit(1)

    ctx_a = load_extraction_context(ev_a)
    ctx_b = load_extraction_context(ev_b)

    has_snapshot_a = ctx_a is not None
    has_snapshot_b = ctx_b is not None

    if not has_snapshot_a or not has_snapshot_b:
        print()
        if not has_snapshot_a:
            print(f"Turn {turn_a}: (no snapshot available — event predates extraction_context)")
        if not has_snapshot_b:
            print(f"Turn {turn_b}: (no snapshot available — event predates extraction_context)")

    # Compute diff from snapshots if both have context
    if ctx_a is not None and ctx_b is not None:
        diff_results = diff_extraction_context(ctx_a, ctx_b)
    else:
        diff_results = []

    # Accumulate intermediate changes
    intermediate_changes = accumulate_intermediate_changes(events, turn_a, turn_b)

    format_diff_output(diff_results, intermediate_changes, turn_a, turn_b, section_filter)


def extract_field_from_event(ev: dict[str, Any], field: str) -> Any | None:
    """Extract a single field's printable value from an event.

    Returns None if the field is not tracked in any data source.
    Dispatch order: extraction_context → applied → changes → ruling.
    First match wins.
    """
    ctx = ev.get("extraction_context") or {}
    applied = ev.get("applied") or {}
    changes = ev.get("changes") or {}
    ruling_ev = ev.get("ruling") or {}

    # extraction_context fields (5 snapshot categories)
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

    elif field == "scene.tags":
        tags = ctx.get("scene_tags_this_turn", []) or []
        if isinstance(tags, list):
            return [str(t) for t in tags]
        return None

    # applied fields (StateDelta mutations)
    elif field == "scene.tagline":
        tagline = applied.get("scene_tagline")
        if isinstance(tagline, str):
            return tagline
        return None

    # changes fields + ruling fallback for momentum
    elif field == "pc.momentum":
        mom_list = (changes.get("momentum", []) or [])
        if isinstance(mom_list, list) and mom_list:
            latest = mom_list[-1] if isinstance(mom_list[-1], dict) else {}
            return int(latest.get("after", 0))
        # Fallback to ruling_event.momentum_after
        if "momentum_after" in ruling_ev:
            return int(ruling_ev["momentum_after"])
        return None

    # Not tracked
    return None


def format_trace_value(value: Any, field: str) -> str:
    """Format a value for display in the trace table."""
    if value is None:
        return "(no data)"

    if isinstance(value, list):
        if not value:
            return "(empty)"
        # Collection fields - show condensed format
        if field == "inventory":
            parts = []
            for item in sorted(value, key=lambda x: ("0" if isinstance(x, dict) and x.get("id") == "credits" else "1", (x.get("name") or "").lower())):
                if not isinstance(item, dict):
                    continue
                name = _short_item_name(item.get("name", item.get("id", "?")))
                amt = int((item.get("amount") or 1))
                parts.append(f"{name}×{amt}")
            return ", ".join(parts) if parts else "(empty)"

        elif field == "conditions":
            labels = []
            for c in value:
                if isinstance(c, dict):
                    lbl = c.get("label", "") or c.get("id", "?")
                    labels.append(lbl)
                else:
                    labels.append(str(c))
            return ", ".join(labels) if labels else "(empty)"

        elif field == "npcs":
            # value is a list of IDs from extract_field_from_event
            if isinstance(value, list):
                return ", ".join(str(n) for n in value if value) if value else "(empty)"
            return str(value)

        # Generic list display (e.g., scene.tags)
        items = [str(x)[:40] for x in value[:10]]
        result = ", ".join(items)
        if len(value) > 10:
            result += f" (+{len(value)-10} more)"
        return result

    elif isinstance(value, dict):
        name = value.get("name", "") or ""
        npc_id = value.get("id", "?")
        if name:
            return f"{npc_id}: {name}"
        return str({k: v for k, v in list(value.items())[:3]})

    elif isinstance(value, str):
        return value[:100] + ("…" if len(value) > 100 else "")

    return str(value)[:200]


def _short_item_name(name: str) -> str:
    """Shorten item names for compact display."""
    words = name.split()
    if not words:
        return "?"
    if len(name) <= 15:
        return name[:20]
    # First letter of each word, joined
    abbr = "".join(w[0].upper() for w in words if w)
    if len(words) > 2:
        return abbr + name[-3:]
    return abbr[:6]


def cmd_trace(events: list[dict[str, Any]], field: str, from_turn: int | None = None, to_turn: int | None = None, show_unchanged: bool = False) -> None:
    """Handle the 'trace' command."""
    # Filter events by turn range
    filtered = []
    for ev in events:
        if not isinstance(ev.get("turn"), int):
            continue
        t = ev["turn"]
        if from_turn is not None and t < from_turn:
            continue
        if to_turn is not None and t > to_turn:
            continue
        filtered.append(ev)

    if not filtered:
        print("(no events in range)")
        return

    # Validate field is tracked by checking any event in range
    found = any(extract_field_from_event(ev, field) is not None for ev in filtered)
    if not found:
        print("Field not tracked per-turn")
        sys.exit(1)
    first_val = extract_field_from_event(filtered[0], field)

    # Build table header based on field type
    display_name = _trace_display_name(field)

    # Print header
    print(f"trace {field}")
    print()
    col_width = 60
    print(f"{'Turn':>5} | {display_name}")
    print("─────┼" + "─" * col_width)

    prev_value = None
    for ev in filtered:
        turn = ev["turn"]
        value = extract_field_from_event(ev, field)
        formatted = format_trace_value(value, field)

        if not show_unchanged and prev_value is not None and _values_equal(prev_value, value):
            print(f"  {turn} | (same)")
        else:
            # Show change arrow for collections that changed
            if prev_value is not None and not _values_equal(prev_value, value) and isinstance(value, list):
                changes = _describe_collection_change(prev_value, value)
                line = f"  {turn} | {formatted}"
                if changes:
                    # Pad to fit arrow nicely
                    padding = " " * max(0, col_width - len(formatted))
                    print(line + padding + " ← " + ", ".join(changes[:3]))
                    for extra in changes[3:]:
                        print("     " + (" " * 6) + "← " + extra)
                else:
                    print(line)
            elif prev_value is not None and not _values_equal(prev_value, value):
                # Scalar field changed - show new value only (not "(same)")
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")
            elif prev_value is None and not _values_equal(value, first_val):
                # First non-matching value after initial check
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")
            elif prev_value is None and _values_equal(value, first_val):
                # First row - always show
                if formatted != "(no data)":
                    print(f"  {turn} | {formatted}")
                else:
                    print(f"  {turn} | (no data)")

        prev_value = value


def _trace_display_name(field: str) -> str:
    """Convert a field path to a display name for table headers."""
    if field == "inventory":
        return "Inventory"
    elif field.startswith("inventory."):
        item_id = field[len("inventory."):]
        return f"Item {item_id}"
    elif field == "conditions":
        return "Conditions"
    elif field.startswith("conditions."):
        cond_id = field[len("conditions."):]
        return f"Condition {cond_id}"
    elif field == "npcs":
        return "NPCs Present"
    elif field.startswith("npcs."):
        npc_id = field[len("npcs."):]
        return f"NPC {npc_id}"
    elif field == "location":
        return "Location"
    elif field == "scene.tags":
        return "Scene Tags"
    elif field == "scene.tagline":
        return "Tagline"
    elif field == "pc.momentum":
        return "Momentum"
    else:
        return field


def _values_equal(a: Any, b: Any) -> bool:
    """Compare two values for equality (handles None gracefully)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # For lists of dicts, compare by ID+name only
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        for i in range(len(a)):
            ai = a[i] if isinstance(a[i], dict) else {"id": str(a[i])}
            bi = b[i] if isinstance(b[i], dict) else {"id": str(b[i])}
            # Compare by id field only (ignore notes/bio/relation differences for "same" check)
            if ai.get("id") != bi.get("id"):
                return False
        return True
    return a == b


def _describe_collection_change(prev: Any, curr: Any) -> list[str]:
    """Describe what changed between two collection values."""
    changes = []

    def _item_map(items):
        m = {}
        for item in items:
            if isinstance(item, dict):
                iid = item.get("id", "")
                if iid:
                    m[iid] = item
            elif isinstance(item, str):
                m[item] = {"id": item}
        return m

    pm = _item_map(prev) if prev else {}
    cm = _item_map(curr) if curr else {}

    for iid in sorted(set(pm.keys()) | set(cm.keys())):
        if iid not in pm and iid in cm:
            name = (cm[iid].get("name", "") or "")[:20]
            changes.append(f"+{iid} {name}")
        elif iid in pm and iid not in cm:
            name = (pm[iid].get("name", "") or "")[:20]
            changes.append(f"-{iid} {name}")

    return changes


def parse_search_expression(expr: str) -> dict[str, Any]:
    """Parse a search expression like 'npc:trevor_riddle' or 'input~steal'.

    Returns dict with keys: field (str), op ('eq' | 'regex'), value (str).
    For boolean expressions like 'rejected', returns {field: 'rejected', op: 'bool', value: None}.
    """
    if expr == "rejected":
        return {"field": "rejected", "op": "bool", "value": None}

    # Check for regex operator (~) or exact match (:)
    if "~" in expr:
        idx = expr.index("~")
        field = expr[:idx]
        value = expr[idx + 1:]
        return {"field": field, "op": "regex", "value": value}

    elif ":" in expr:
        idx = expr.index(":")
        field = expr[:idx]
        value = expr[idx + 1:]
        return {"field": field, "op": "eq", "value": value}

    else:
        # Treat as exact match on the whole string (ambiguous)
        print(f"Error: invalid expression '{expr}'. Use format 'field:value' or 'input~regex'.", file=sys.stderr)
        sys.exit(1)


def search_events(events: list[dict[str, Any]], queries: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Search events by structured fields.

    Each query is a parsed expression dict {field, op, value}.
    Multiple expressions AND together (all must match).

    Supported search keys:
      - npc              exact: checks applied.compendium_npc_update
      - npc_add          exact: checks applied.compendium_npc_update
      - item             exact: checks extraction_context + applied mutations
      - condition        exact: checks extraction_context + applied mutations
      - band             exact: matches ruling.band (or top-level event.momentum fields)
      - momentum_after   exact: matches ev.momentum_after (new turns only, from events.jsonl)
      - momentum_before  exact: matches ev.momentum_before (new turns only, from events.jsonl)
      - momentum_delta   exact: matches ev.momentum_delta (new turns only, from events.jsonl)
      - rejected         boolean: matches ev.get('rejected') truthiness
      - input            regex: regex match against ev.get('input')

    Returns list of {turn, context_line, input_snippet} dicts.
    """
    results = {}  # turn -> result dict (dedup by turn)

    for ev in events:
        if not isinstance(ev.get("turn"), int):
            continue
        turn = ev["turn"]
        ctx = ev.get("extraction_context") or {}
        applied = ev.get("applied") or {}
        ruling_ev = ev.get("ruling") or {}

        # Check all queries against this event (AND logic)
        matches_all = True
        best_context = None

        for q in queries:
            field = q["field"]
            op = q["op"]
            value = q["value"]

            if not _match_single_query(ev, ctx, applied, ruling_ev, field, op, value):
                matches_all = False
                break

            # Track best context line for this query match
            ctx_line = _get_context_line(ctx, applied, field, op, value)
            if ctx_line:
                best_context = ctx_line

        if matches_all and queries:
            input_snippet = (ev.get("input") or "")[:80]
            context = best_context or "(match)"
            results[turn] = {
                "turn": turn,
                "context_line": context,
                "input_snippet": input_snippet,
            }

    # Sort by turn number and return as list
    sorted_results = [results[t] for t in sorted(results.keys())]
    return sorted_results


def _match_single_query(ev: dict[str, Any], ctx: dict, applied: dict, ruling_ev: dict, field: str, op: str, value: str | None) -> bool:
    """Check if a single query matches an event."""

    # npc: exact match in compendium_npc_update mutations
    if field == "npc":
        updates = applied.get("compendium_npc_update", []) or []
        return any(isinstance(m, dict) and m.get("id") == value for m in updates)

    # npc_add: exact match in compendium_npc_update (replaces old npc_add)
    elif field == "npc_add":
        updates = applied.get("compendium_npc_update", []) or []
        if isinstance(value, str):
            return any(isinstance(m, dict) and m.get("id") == value for m in updates)
        return False

    # item: exact match in extraction_context OR mutation in applied
    elif field == "item":
        items = ctx.get("inventory_this_turn", []) or []
        has_presence = any(isinstance(i, dict) and i.get("id") == value for i in items)

        has_mutation = False
        for mut_field in ("inventory_add", "inventory_remove", "inventory_update"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                has_mutation = True
                break

        return has_presence or has_mutation

    # condition: exact match in extraction_context OR mutation in applied
    elif field == "condition":
        conds = ctx.get("conditions_this_turn", []) or []
        has_presence = any(isinstance(c, dict) and c.get("id") == value for c in conds)

        has_mutation = False
        for mut_field in ("pc_condition_add", "pc_condition_remove"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                has_mutation = True
                break

        return has_presence or has_mutation

    # band: exact match against ruling.band (or top-level event.momentum fields)
    elif field == "band":
        band_val = ruling_ev.get("band", "")
        if op == "eq" and isinstance(value, str):
            return band_val == value
        return False

    # momentum_after: exact match on top-level event field (new turns only)
    elif field == "momentum_after":
        mom = ev.get("momentum_after")
        if mom is None:
            return False
        try:
            return int(mom) == int(value)
        except (ValueError, TypeError):
            return False

    # momentum_before: exact match on top-level event field (new turns only)
    elif field == "momentum_before":
        mom = ev.get("momentum_before")
        if mom is None:
            return False
        try:
            return int(mom) == int(value)
        except (ValueError, TypeError):
            return False

    # momentum_delta: exact match on top-level event field (new turns only)
    elif field == "momentum_delta":
        delta = ev.get("momentum_delta")
        if delta is None:
            return False
        try:
            return int(delta) == int(value)
        except (ValueError, TypeError):
            return False

    # rejected: boolean check
    elif field == "rejected":
        return bool(ev.get("rejected"))

    # input: regex match against player input text
    elif field == "input":
        if op != "regex" or not isinstance(value, str):
            return False
        try:
            pattern = re.compile(value)
            return bool(pattern.search(ev.get("input", "") or ""))
        except re.error:
            print(f"Error: invalid regex '{value}'", file=sys.stderr)
            sys.exit(1)

    # Unknown field - no match
    return False


def _get_context_line(ctx: dict, applied: dict, field: str, op: str, value: str | None) -> str | None:
    """Get a context line describing the match."""

    if field == "npc":
        updates = applied.get("compendium_npc_update", []) or []
        for m in updates:
            if isinstance(m, dict) and m.get("id") == value:
                return f"compendium_npc_update {value}"
        return None

    elif field == "npc_add":
        updates = applied.get("compendium_npc_update", []) or []
        if any(isinstance(m, dict) and m.get("id") == value for m in updates):
            return f"compendium_npc_update {value}"
        return None

    elif field == "item":
        items = ctx.get("inventory_this_turn", []) or []
        has_presence = any(isinstance(i, dict) and i.get("id") == value for i in items)

        # Check mutations first (more detail)
        for mut_field in ("inventory_add", "inventory_remove", "inventory_update"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                return f"{mut_field} {value}"

        if has_presence:
            return "(present in inventory)"
        return None

    elif field == "condition":
        conds = ctx.get("conditions_this_turn", []) or []
        has_presence = any(isinstance(c, dict) and c.get("id") == value for c in conds)

        # Check mutations first (more detail)
        for mut_field in ("pc_condition_add", "pc_condition_remove"):
            muts = applied.get(mut_field, []) or []
            if any(isinstance(m, dict) and m.get("id") == value for m in muts):
                return f"{mut_field} {value}"

        if has_presence:
            return "(active condition)"
        return None

    elif field == "band":
        # Band matching is handled in _match_single_query via ruling_ev parameter
        return f"band={value}" if value else "(match)"

    elif field == "momentum_after":
        return f"momentum_after={value}"

    elif field == "momentum_before":
        return f"momentum_before={value}"

    elif field == "momentum_delta":
        return f"momentum_delta={value}"

    elif field == "rejected":
        return "rejected"

    elif field == "input":
        return None  # Input matches don't have a context line prefix

    return None


def cmd_search(events: list[dict[str, Any]], expressions: list[str]) -> None:
    """Handle the 'search' command."""
    if not expressions:
        print("Error: search requires at least one expression", file=sys.stderr)
        sys.exit(1)

    # Parse all expressions
    queries = []
    for expr in expressions:
        parsed = parse_search_expression(expr)
        queries.append(parsed)

    # Run search
    matches = search_events(events, queries)

    if not matches:
        print("(no matching turns)")
        return

    for m in matches:
        context = m["context_line"] or ""
        input_text = m.get("input_snippet", "")
        line = f"turn {m['turn']}: {context}"
        if input_text:
            line += f' — "{input_text}"'
        print(line)



def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        sys.exit(0)

    flags, args = _strip_flags(args)
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
            fmt = flags.get("format", "text")
            cmd_summary(events, format=fmt)
        case "timing":
            cmd_timing(events)
        case "turn":
            if len(args) < 2:
                print("Usage: ev.py turn TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found (or is a compaction entry)")
                sys.exit(1)
            cmd_turn(ev)
        case "props":
            if len(args) < 3:
                print("Usage: ev.py props TURN STREAM", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            stream = args[2]
            stream = _resolve_stream(stream)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_props(ev, stream)
        case "compact":
            if len(args) < 3:
                print("Usage: ev.py compact TURN STREAM", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            stream = args[2]
            stream = _resolve_stream(stream)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_compact(ev, stream)
        case "prompt":
            if len(args) < 4:
                print("Usage: ev.py prompt TURN STREAM FIELD", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            stream = args[2]
            field = args[3]
            stream = _resolve_stream(stream)
            if field not in ("system", "user", "output"):
                print(f"Unknown field: {field}", file=sys.stderr)
                sys.exit(1)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_prompt(ev, stream, field)
        case "outputs":
            if len(args) < 2:
                print("Usage: ev.py outputs TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_outputs(ev)
        case "deltas":
            if len(args) < 2:
                print("Usage: ev.py deltas TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_deltas(ev)
        case "mechanics":
            if len(args) < 2:
                print("Usage: ev.py mechanics TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_mechanics(ev)
        case "pacing":
            if len(args) < 2:
                print("Usage: ev.py pacing TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_pacing(ev)
        case "connectors":
            turn = int(args[1]) if len(args) > 1 else None
            ev = find_turn(events, turn) if turn else None
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            cmd_connectors(ev)
        case "state":
            save_dir_path = Path(flags["save-dir"]) if "save-dir" in flags else DEFAULT_SAVE_DIR
            fmt = flags.get("format", "full")
            valid_formats = ("full", "compact", "pc", "inventory", "location", "scene", "arc", "npcs", "compidx")
            if fmt not in valid_formats:
                print(f"Error: unknown format '{fmt}'. Valid formats: {', '.join(valid_formats)}", file=sys.stderr)
                sys.exit(1)
            cmd_state(fmt, save_dir_path)
        case "diff":
            turn_a = int(args[1]) if len(args) > 1 else None
            turn_b = int(args[2]) if len(args) > 2 else None
            section = flags.get("section")
            valid_sections = ("npcs", "inventory", "conditions", "location", "tags", "applied")
            if section is not None and section not in valid_sections:
                print(f"Error: unknown section '{section}'. Valid sections: {', '.join(valid_sections)}", file=sys.stderr)
                sys.exit(1)
            cmd_diff(events, turn_a, turn_b, section_filter=section)
        case "trace":
            # Find field in remaining args (after flags are stripped)
            if len(args) < 2:
                print("Error: trace requires a field name", file=sys.stderr)
                sys.exit(1)
            field = args[1]
            from_turn = int(flags["from"]) if "from" in flags else None
            to_turn = int(flags["to"]) if "to" in flags else None
            show_unchanged = "show-unchanged" in flags
            cmd_trace(events, field, from_turn=from_turn, to_turn=to_turn, show_unchanged=show_unchanged)
        case "search":
            # Remaining args after flags are search expressions
            if len(args) < 2:
                print("Error: search requires at least one expression", file=sys.stderr)
                sys.exit(1)
            exprs = args[1:]
            cmd_search(events, exprs)
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__.strip())
            sys.exit(1)


if __name__ == "__main__":
    main()
