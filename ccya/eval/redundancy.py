"""Substring-overlap detector for engine prompts.

For each turn, compares the rendered_user content of the 5 streams (rules,
narrate, scene, state, progress) pairwise. Reports any line-anchored span of
length >= MIN_LINE_CHARS that appears identically in two or more streams.

Runs as a deterministic pre-pass before judge sees the trace. Output is a
plain dict suitable for JSON serialization and inclusion in the
# Deterministic Signals section.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

MIN_LINE_CHARS = 60          # ignore short trivially-shared lines
MIN_BLOCK_LINES = 3          # require at least 3 consecutive matching lines


def _stream_text(event: dict[str, Any], stream: str) -> str:
    if stream == "rules":
        return (event.get("rules_prompt") or {}).get("rendered_user") or ""
    if stream == "narrate":
        return (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    ext = event.get("extraction") or {}
    return (ext.get(stream) or {}).get("rendered_user") or ""


def _block_hashes(text: str) -> list[tuple[int, str]]:
    """Slide a window of MIN_BLOCK_LINES over the text. Yield (start_line, sha)
    for each window where every line is >= MIN_LINE_CHARS."""
    lines = text.splitlines()
    out: list[tuple[int, str]] = []
    for i in range(len(lines) - MIN_BLOCK_LINES + 1):
        window = lines[i:i + MIN_BLOCK_LINES]
        if all(len(ln) >= MIN_LINE_CHARS for ln in window):
            sha = hashlib.sha1(("\n".join(window)).encode()).hexdigest()[:16]
            out.append((i, sha))
    return out


def compute_redundancy_signals(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk every per-turn event, detect cross-stream block duplication.

    Returns:
        {
          "turns": [
            {
              "turn": int,
              "overlaps": [
                {"streams": ["narrate", "scene"], "block_count": 2,
                 "preview": "first 120 chars of one of the duplicated blocks"},
                ...
              ]
            },
            ...
          ],
          "top_overlaps": [          # aggregated across all turns
            {"streams": ["narrate", "scene"], "total_blocks": 14, "preview": "..."},
            ...
          ]
        }
    """
    streams = ("rules", "narrate", "scene", "state", "progress")
    turn_results: list[dict[str, Any]] = []
    aggregate: dict[tuple[str, ...], dict[str, Any]] = defaultdict(
        lambda: {"total_blocks": 0, "preview": ""}
    )

    for ev in events:
        if ev.get("__metadata__"):
            continue
        per_stream_hashes: dict[str, list[tuple[int, str]]] = {}
        per_stream_lines: dict[str, list[str]] = {}
        for s in streams:
            t = _stream_text(ev, s)
            if not t:
                continue
            per_stream_hashes[s] = _block_hashes(t)
            per_stream_lines[s] = t.splitlines()

        # For each pair of streams, count common hashes
        sha_to_streams: dict[str, set[str]] = defaultdict(set)
        sha_to_preview: dict[str, str] = {}
        for s, hh in per_stream_hashes.items():
            for line_idx, sha in hh:
                sha_to_streams[sha].add(s)
                if sha not in sha_to_preview:
                    block_lines = per_stream_lines[s][line_idx:line_idx + MIN_BLOCK_LINES]
                    preview = " / ".join(ln[:60] for ln in block_lines)
                    sha_to_preview[sha] = preview[:200]

        pair_blocks: dict[tuple[str, ...], int] = defaultdict(int)
        pair_preview: dict[tuple[str, ...], str] = {}
        for sha, sset in sha_to_streams.items():
            if len(sset) < 2:
                continue
            key = tuple(sorted(sset))
            pair_blocks[key] += 1
            if key not in pair_preview:
                pair_preview[key] = sha_to_preview[sha]

        if pair_blocks:
            turn_results.append({
                "turn": ev.get("turn", "?"),
                "overlaps": [
                    {"streams": list(k), "block_count": v, "preview": pair_preview[k]}
                    for k, v in sorted(pair_blocks.items(), key=lambda x: -x[1])
                ],
            })
            for k, v in pair_blocks.items():
                aggregate[k]["total_blocks"] += v
                if not aggregate[k]["preview"]:
                    aggregate[k]["preview"] = pair_preview[k]

    top = sorted(
        ({"streams": list(k), **v} for k, v in aggregate.items()),
        key=lambda x: -x["total_blocks"],
    )[:10]

    return {"turns": turn_results, "top_overlaps": top}


def render_redundancy_section(signals: dict[str, Any]) -> str:
    """Render the redundancy signals as the markdown subsection appended to
    the trace's # Deterministic Signals block."""
    parts: list[str] = ["\n## Prompt Redundancy (cross-stream duplication)\n"]
    top = signals.get("top_overlaps") or []
    if not top:
        parts.append("*(no significant cross-stream block duplication detected — all blocks were either too short or unique to one stream.)*\n")
        return "".join(parts)
    parts.append(f"Detected duplicated content blocks (>= {MIN_BLOCK_LINES} lines, each >= {MIN_LINE_CHARS} chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).\n\n")
    parts.append("### Top overlaps across all turns\n\n")
    parts.append("| Streams | Total duplicated blocks | Preview |\n|---|---:|---|\n")
    for o in top:
        streams = " + ".join(o["streams"])
        parts.append(f"| {streams} | {o['total_blocks']} | `{o['preview']}` |\n")
    return "".join(parts)
