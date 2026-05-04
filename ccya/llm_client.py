"""Thin async client for OpenAI-compatible chat completions (mlx_lm.server).

Wire protocol: /v1/chat/completions (OpenAI).
Model is loaded once at server startup and stays resident.
No keep_alive, no num_ctx API knob, no format/grammar constraints.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, AsyncIterator, MutableMapping

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Mock mode: MOCK_MODE=true in env
# ---------------------------------------------------------------------------

_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

_MOCK_NARRATE = (
    "You step forward into the low-grav berth. The air is thin, the lights flicker. "
    "Your hand terminal buzzes again -- that encrypted pinger won't stop. "
    "A hauler drifts past, its cargo bay open to the ring. "
    "You need to find the signal source. The terminal buzzes insistently."
)

_MOCK_EXTRACT_NARRATE = {
    "state_delta": {
        "recent_events_add": [
            "You are at Docking Ring 7.",
            "Your hand terminal carries an encrypted pinger.",
        ],
        "scene_tags": ["exploration"],
    },
    "actions": [
        "Open the encrypted pinger",
        "Drift toward the cargo bay",
        "Check the terminal for sender info",
        "Scan the berth for threats",
    ],
}

_MOCK_EXTRACT_EXAMINE = {
    "state_delta": {
        "recent_events_add": [
            "The pinger is from a shell company called 'Quiet Systems.'"
        ],
        "scene_tags": ["dialogue"],
    },
    "actions": [
        "Trace the shell company",
        "Contact the sender",
        "Ignore the pinger",
        "Step back from the terminal",
    ],
}

_MOCK_EXTRACT_CARGO = {
    "state_delta": {
        "location_change": {
            "id": "cargo-bay-7",
            "name": "Cargo Bay 7",
            "description": "Open cargo bay, crates stacked along the walls, smelling of lubricant.",
        },
        "recent_events_add": [
            "A hauler offers passage to the lower ring.",
            "There is a terminal in the cargo bay.",
        ],
        "scene_tags": ["travel"],
    },
    "actions": [
        "Accept the hauler's offer",
        "Use the cargo bay terminal",
        "Rest and observe",
        "Decline and leave",
    ],
}


class _mock_stream:
    """Async iterator wrapper for canned mock narrative."""

    def __aiter__(self) -> "_mock_stream":
        self._texts = list(_MOCK_NARRATE.split(". "))
        self._idx = 0
        return self

    async def __anext__(self) -> str:
        if self._idx >= len(self._texts):
            raise StopAsyncIteration
        val = self._texts[self._idx] + (
            ". " if self._idx < len(self._texts) - 1 else ""
        )
        self._idx += 1
        return val


def _mock_extract_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Return canned extract JSON based on message content."""
    narrative = ""
    for msg in messages:
        narrative += msg.get("content", "")

    if (
        "examine" in narrative.lower()
        or "terminal" in narrative.lower()
        or "pinger" in narrative.lower()
    ):
        body = _MOCK_EXTRACT_EXAMINE
    elif (
        "cargo" in narrative.lower()
        or "bay" in narrative.lower()
        or "haul" in narrative.lower()
    ):
        body = _MOCK_EXTRACT_CARGO
    else:
        body = _MOCK_EXTRACT_NARRATE
    return {
        "response": json.dumps(body),
        "done": True,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }


# ---------------------------------------------------------------------------
# Client (lazy-init, reused across calls)
# ---------------------------------------------------------------------------

_client: AsyncOpenAI | None = None


def _get_client(base_url: str) -> AsyncOpenAI:
    """Return (or create) the shared AsyncOpenAI client.

    Timeout is NOT baked in here — pass it per-request via the ``timeout``
    argument on each ``create()`` call so that warmup (30 s) and generate_seed
    (180 s) can use different values without recreating the client.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=base_url, api_key="local")
    return _client


# ---------------------------------------------------------------------------
# Thinking helpers (Qwen3.x /think / /no_think soft switches)
# ---------------------------------------------------------------------------

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def apply_thinking(
    messages: list[dict[str, str]], enable: bool
) -> list[dict[str, str]]:
    """Append /think or /no_think to the last user message content."""
    tag = "/think" if enable else "/no_think"
    msgs = [dict(m) for m in messages]
    msgs[-1]["content"] = f"{msgs[-1]['content']} {tag}"
    return msgs


def strip_thinking(text: str) -> str:
    """Remove  block from response text."""
    return _THINK_RE.sub("", text).strip()


# ---------------------------------------------------------------------------
# Token-count truncation helper
# ---------------------------------------------------------------------------


def trim_messages(
    messages: list[dict[str, str]], max_tokens: int
) -> list[dict[str, str]]:
    """Truncate messages list so estimated token count <= max_tokens.

    Uses rough chars-per-token estimate (~3.5). Preserves system message at
    index 0.  When the budget is exceeded, truncates the last user message
    content from the **tail** (oldest context) so the LLM always receives at
    least the system prompt and a user message with the head intact.
    """

    def estimate(s: str) -> int:
        return int(len(s) / 3.5)

    total = sum(estimate(m.get("content", "")) for m in messages)
    while total > max_tokens and len(messages) > 1:
        # Skip system message at index 0 if present
        idx = 1 if messages[0].get("role") == "system" else 0
        msg = messages[idx]
        content = msg.get("content", "")
        est = estimate(content)
        # How many chars can we keep?
        budget = max_tokens - (total - est)
        if budget <= 0:
            # Even keeping one char exceeds budget — drop the message
            messages.pop(idx)
            total = sum(estimate(m.get("content", "")) for m in messages)
        else:
            # Truncate from the TAIL to preserve head (PC, location, state)
            # and the last section (player input).  Keep the first ~2000 chars
            # of state and the last ~500 chars of player input, cutting the
            # middle (chronicle tail, recent turns).
            head_keep = min(2000, int(budget * 3.5))
            tail_keep = min(500, max(0, int(budget * 3.5) - head_keep))
            if head_keep + tail_keep >= len(content):
                # Budget is large enough — no truncation needed
                pass
            else:
                msg["content"] = (
                    content[:head_keep]
                    + "\n\n[... truncated — older context removed ...]\n\n"
                    + content[-tail_keep:]
                )
            total = max_tokens + 1  # exit loop
    return messages


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------


async def chat_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
) -> AsyncIterator[str]:
    """Stream tokens from OpenAI-compatible /v1/chat/completions endpoint.

    Yields one string per token chunk.
    If ``stream_stats`` is a mutable dict, it is filled on completion
    with ``prompt_eval_count`` and ``eval_count`` (mapped from OpenAI usage fields).
    """
    if _MOCK_MODE:
        async for chunk in _mock_stream():
            yield chunk
        if stream_stats is not None:
            stream_stats["prompt_eval_count"] = 0
            stream_stats["eval_count"] = 0
        return

    client = _get_client(host)
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
        timeout=timeout,
    )

    async for chunk in stream:
        # Final usage-summary chunk: choices is empty, usage is populated.
        if not chunk.choices:
            if stream_stats is not None and chunk.usage is not None:
                stream_stats["prompt_eval_count"] = chunk.usage.prompt_tokens or 0
                stream_stats["eval_count"] = chunk.usage.completion_tokens or 0
            continue
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content


# ---------------------------------------------------------------------------
# Non-streaming chat
# ---------------------------------------------------------------------------


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    timeout: float = 180.0,
) -> dict[str, Any]:
    """Non-streaming call to OpenAI-compatible /v1/chat/completions.

    Returns {"response": str, "done": True, "usage": {"prompt_tokens": int, "total_tokens": int}}.
    """
    if _MOCK_MODE:
        return _mock_extract_chat(messages)

    client = _get_client(host)
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        timeout=timeout,
    )
    content = resp.choices[0].message.content or ""
    return {
        "response": content,
        "done": True,
        "usage": {
            "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "total_tokens": resp.usage.total_tokens if resp.usage else 0,
        },
    }
