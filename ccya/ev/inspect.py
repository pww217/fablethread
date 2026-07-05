from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccya.ev.events import (
    STREAMS,
    _count_state_diff,
    _stream_keys,
    _stream_ms,
    _total_tt,
    _total_tokens_in,
    _total_tokens_out,
)


def extract_prompt(
    ev: dict[str, Any],
    stream: str,
    prompts: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    turn = ev.get("turn")
    if prompts is not None and turn is not None:
        for p in prompts:
            if p.get("turn") == turn and p.get("stream") == stream:
                return {
                    "system": p.get("rendered_system") or "",
                    "user": p.get("rendered_user") or "",
                    "output": "",
                }
    if stream == "ruling":
        blob = ev.get("ruling_prompt") or {}
    elif stream == "narrate":
        blob = ev.get("narrate_prompt") or {}
    else:
        blob = (ev.get("extraction") or {}).get(stream) or {}
    raw_out = blob.get("output", "")
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
    # Support both old format (rendered_user/rendered_system) and new format (context_meta)
    meta = blob.get("context_meta") or {}
    system = blob.get("rendered_system") or meta.get("system_text") or ""
    user = blob.get("rendered_user") or meta.get("user_text") or ""
    return {
        "system": system,
        "user": user,
        "output": str(raw_out) if raw_out else "",
    }


def cmd_summary(events: list[dict[str, Any]], format: str = "text") -> None:
    print("=== Turn Viewer Summary ===\n")
    for ev in events:
        if ev.get("kind") not in (None, "turn"):
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
    print("=== Turn Viewer \u2014 Timing & Tokens ===\n")
    for ev in events:
        if ev.get("kind") not in (None, "turn"):
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


def cmd_prompt(
    ev: dict[str, Any],
    stream: str,
    field: str | None = None,
    include_system: bool = False,
    from_events: bool = False,
    save_dir: Path | None = None,
) -> None:
    prompts = None
    if from_events and save_dir is not None:
        from ccya.ev.events import load_prompts
        prompts = load_prompts(save_dir)
    p = extract_prompt(ev, stream, prompts=prompts)
    if field:
        print(f"--- Turn {ev['turn']} \u2014 {stream} {field} ---")
        print(p.get(field, ""))
        return

    if include_system:
        print(f"=== Turn {ev['turn']} \u2014 {stream} ===\n")
        print("--- SYSTEM ---")
        print(p["system"])
        print()
    else:
        print(f"=== Turn {ev['turn']} \u2014 {stream} (user + output) ===\n")

    print("--- USER ---")
    print(p["user"])
    print()
    print("--- OUTPUT ---")
    print(p["output"])
