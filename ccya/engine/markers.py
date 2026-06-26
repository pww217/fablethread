"""Eval-trace marker handling: strip sentinels before LLM call, retain in trace.

Design intent:
  Per-turn user prompts in Jinja templates wrap immutable sections
  (world state, NPC rosters) with <<<TRACE_IMMUTABLE_START>>>/<<<TRACE_IMMUTABLE_END>>>
  sentinels. The eval harness uses these to dedup immutable content when building
  judge traces — it only sends the immutable section from the first turn, not every turn.

Contract:
  - strip_trace_markers_in_messages() is called on every message list before the
    LLM call (ruling, narrate, scene, state, record — see call sites).
  - The rendered_user field in events.jsonl intentionally RETAINS the sentinels
    so the eval harness can locate immutable boundaries.
  - If stripping fails or a call site is missed, <<>> fragments and the
    "Immutable Reference" header text leak into production LLM prompts.
    The regex r"<<<TRACE_IMMUTABLE_(?:START|END)>>>\s*\n?" must match the exact
    marker format used in all prompt templates (narrate_user.j2, record_user.j2,
    extract_scene_user.j2).

Note on "Immutable Reference" text:
  The "## Immutable Reference" header is INTENTIONAL content that remains in the
  prompt after markers are stripped. It is not a bug. Only the <<...>> sentinel
  lines are removed.
"""

from __future__ import annotations

import logging
import re
from typing import Any


_log = logging.getLogger(__name__)

_RE = re.compile(r"<<<TRACE_IMMUTABLE_(?:START|END)>>>\s*\n?")


def strip_trace_markers(text: str) -> str:
    if not text:
        _log.debug("strip_trace_markers received empty text")
        return text
    cleaned = _RE.sub("", text)
    if len(cleaned) != len(text):
        _log.debug("strip_trace_markers removed %d chars from %d", len(text) - len(cleaned), len(text))
    return cleaned


def strip_trace_markers_in_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not messages:
        _log.warning("strip_trace_markers_in_messages received empty messages list")
        return messages
    _log.debug("strip_trace_markers_in_messages messages=%d", len(messages))
    for msg in messages:
        if "content" in msg and isinstance(msg["content"], str):
            msg["content"] = strip_trace_markers(msg["content"])
    return messages
