"""Thin async httpx client for Ollama /api/chat.

Ollama API contract (confirmed against https://docs.ollama.com/api/chat):
- keep_alive    -> top-level field
- temperature   -> body["options"]["temperature"]
- num_ctx       -> body["options"]["num_ctx"]
- format        -> top-level field (for structured output)
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator, MutableMapping

import httpx

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
        "established_facts_add": [
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
        "established_facts_add": ["The pinger is from a shell company called 'Quiet Systems.'"],
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
        "established_facts_add": [
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

_MOCK_EXTRACT_DEFAULT = {
    "state_delta": {
        "established_facts_add": ["Something new happens in the ring."],
        "scene_tags": ["exploration"],
    },
    "actions": [
        "Look around",
        "Try something else",
        "Check your state",
        "Wait and listen",
    ],
}


class _mock_stream:
    """Async iterator wrapper for canned mock narrative."""

    def __aiter__(self):
        self._texts = list(_MOCK_NARRATE.split(". "))
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._texts):
            raise StopAsyncIteration
        val = self._texts[self._idx] + (". " if self._idx < len(self._texts) - 1 else "")
        self._idx += 1
        return val


def _mock_extract_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Return canned extract JSON (same shape as Ollama /api/chat) based on message content."""
    narrative = ""
    for msg in messages:
        narrative += msg.get("content", "")

    if "examine" in narrative.lower() or "terminal" in narrative.lower() or "pinger" in narrative.lower():
        body = _MOCK_EXTRACT_EXAMINE
    elif "cargo" in narrative.lower() or "bay" in narrative.lower() or "haul" in narrative.lower():
        body = _MOCK_EXTRACT_CARGO
    else:
        body = _MOCK_EXTRACT_NARRATE
    return {
        "response": json.dumps(body),
        "done": True,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }


# ---------------------------------------------------------------------------
# Real clients
# ---------------------------------------------------------------------------


async def chat_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    keep_alive: str = "60m",
    num_ctx: int = 32768,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
) -> AsyncIterator[str]:
    """Stream tokens from Ollama's /api/chat endpoint.

    Yields one string per token chunk.
    If ``stream_stats`` is a mutable dict, it is filled on the final ``done`` chunk
    with ``prompt_eval_count`` and ``eval_count`` (Ollama field names).
    """
    if _MOCK_MODE:
        async for chunk in _mock_stream():
            yield chunk
        if stream_stats is not None:
            stream_stats["prompt_eval_count"] = 0
            stream_stats["eval_count"] = 0
        return

    body = _build_body(
        model, messages, temperature=temperature, num_ctx=num_ctx,
        keep_alive=keep_alive, stream=True,
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("POST", f"{host}/api/chat", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if stream_stats is not None and data.get("done"):
                    stream_stats["prompt_eval_count"] = int(data.get("prompt_eval_count") or 0)
                    stream_stats["eval_count"] = int(data.get("eval_count") or 0)
                if data.get("done", False):
                    msg = data.get("message", {})
                    if isinstance(msg, dict) and msg.get("content"):
                        yield msg["content"]
                    break
                msg = data.get("message", {})
                if isinstance(msg, dict) and msg.get("content"):
                    yield msg["content"]


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    format: dict | None = None,
    keep_alive: str = "60m",
    num_ctx: int = 32768,
    timeout: float = 180.0,
) -> dict[str, Any]:
    """Non-streaming call to Ollama /api/chat. Returns the full response dict."""
    if _MOCK_MODE:
        return _mock_extract_chat(messages)

    body = _build_body(
        model, messages, temperature=temperature, num_ctx=num_ctx,
        keep_alive=keep_alive, format=format, stream=False,
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        resp = await client.post(f"{host}/api/chat", json=body)
        resp.raise_for_status()
        data = resp.json()
        return {
            "response": data.get("message", {}).get("content", ""),
            "done": True,
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "total_tokens": data.get("eval_count", 0),
            },
        }


def _build_body(
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    num_ctx: int | None = None,
    keep_alive: str | None = None,
    format: dict | None = None,
    stream: bool | None = None,
) -> dict[str, Any]:
    """Build the Ollama /api/chat request body.

    Per the Ollama API spec:
    - temperature and num_ctx belong inside body["options"]
    - keep_alive is a top-level field
    - format is top-level (for structured output)
    """
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    options: dict[str, Any] = {}
    if temperature is not None:
        options["temperature"] = temperature
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    if options:
        body["options"] = options
    if keep_alive is not None:
        body["keep_alive"] = keep_alive
    if format is not None:
        body["format"] = format
    if stream is not None:
        body["stream"] = stream
    return body
