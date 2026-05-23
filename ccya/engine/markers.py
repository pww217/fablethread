"""Eval-trace marker handling.

Per-turn user prompts are wrapped with <<<TRACE_IMMUTABLE_*>>> sentinels in the
Jinja templates. These let the eval harness dedup immutable sections in the
trace it sends to the judge. The engine strips these sentinels before sending
the prompt to the LLM, so they never affect production behavior.
"""

from __future__ import annotations

import logging
import re
from typing import Any


_log = logging.getLogger(__name__)

_RE = re.compile(r"<<<TRACE_IMMUTABLE_(?:START|END)>>>\s*\n?")


def strip_trace_markers(text: str) -> str:
    """Remove eval-trace sentinel markers from a string."""
    return _RE.sub("", text)


def strip_trace_markers_in_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Strip sentinel markers from all message content in-place.

    Returns the same list (mutated) so callers can use the result directly.
    """
    for msg in messages:
        if "content" in msg and isinstance(msg["content"], str):
            msg["content"] = strip_trace_markers(msg["content"])
    return messages
