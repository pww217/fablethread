"""Thin async httpx client for Ollama /api.chat."""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

import httpx

# ---------------------------------------------------------------------------
# Mock mode: MOCK_MODE=true in env
# ---------------------------------------------------------------------------

_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

# Canned responses for the demo pack.
# narrate -> narrative text; extract -> structured JSON matching the extract schema.
_MOCK_NARRATE = (
     "You step forward into the low-grav berth. The air is thin, the lights flicker. "
     "Your hand terminal buzzes again -- that encrypted pinger won't stop. "
     "A hauler drifts past, its cargo bay open to the ring. "
     "You need to find the signal source. The terminal buzzes insistently."
)

_MOCK_EXTRACT_NARRATE = {
     "state_delta": {
         "established_facts": ["You are at Docking Ring 7.", "Your hand terminal carries an encrypted pinger."],
     },
     "actions": [
         "Open the encrypted pinger",
         "Drift toward the cargo bay",
         "Check the terminal for sender info",
     ],
     "scene_tags": ["exploration"],
    "usage": {"prompt_tokens": 0, "total_tokens": 0},
}

_MOCK_EXTRACT_EXAMINE = {
     "state_delta": {
         "established_facts": ["The pinger is from a shell company called 'Quiet Systems.'"],
     },
     "actions": [
         "Trace the shell company",
         "Contact the sender",
         "Ignore the pinger",
     ],
     "scene_tags": ["dialogue"],
    "usage": {"prompt_tokens": 0, "total_tokens": 0},
}

_MOCK_EXTRACT_CARGO = {
     "state_delta": {
         "location_change": {
             "id": "cargo-bay-7",
             "name": "Cargo Bay 7",
             "description": "Open cargo bay, crates stacked along the walls, smelling of lubricant.",
         },
         "established_facts": ["A hauler offers passage to the lower ring.", "There is a terminal in the cargo bay."],
     },
     "actions": [
         "Accept the hauler's offer",
         "Use the cargo bay terminal",
         "Rest and observe",
     ],
     "scene_tags": ["travel"],
    "usage": {"prompt_tokens": 0, "total_tokens": 0},
}

_MOCK_EXTRACT_DEFAULT = {
     "state_delta": {
         "established_facts": ["Something new happens in the ring."],
     },
     "actions": [
         "Look around",
         "Try something else",
         "Check your state",
     ],
     "scene_tags": [],
    "usage": {"prompt_tokens": 0, "total_tokens": 0},
}


class _mock_stream:
    """Async iterator wrapper for canned mock narrative."""

    def __aiter__(self):
        self._texts = [_MOCK_NARRATE]
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._texts):
            raise StopAsyncIteration
        val = self._texts[self._idx]
        self._idx += 1
        return val


def _mock_extract_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Return canned extract JSON based on message content."""
    narrative = ""
    for msg in messages:
        narrative += msg.get("content", "")

    if "examine" in narrative.lower() or "terminal" in narrative.lower() or "pinger" in narrative.lower():
        return _MOCK_EXTRACT_EXAMINE
    if "cargo" in narrative.lower() or "bay" in narrative.lower() or "haul" in narrative.lower():
        return _MOCK_EXTRACT_CARGO
    return _MOCK_EXTRACT_NARRATE


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
) -> AsyncIterator[str]:
    """Stream tokens from Ollama's /api.chat endpoint.

     Returns an awaitable that yields an async iterator of tokens.
     This design allows both real usage (async for over the result)
     and mocking (async for over a coroutine that resolves to an iterator).
    """
    if _MOCK_MODE:
        ms = _mock_stream()
        async for chunk in ms:
            yield chunk
        return

    body = _build_body(model, messages, temperature)

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
                if data.get("done", False):
                    break
                yield data.get("response", "")


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
    """Non-streaming call to Ollama /api.chat. Returns the full response."""
    if _MOCK_MODE:
        return _mock_extract_chat(messages)

    body = _build_body(model, messages, temperature, format)

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("POST", f"{host}/api/chat", json=body) as resp:
            resp.raise_for_status()
            chunks: list[str] = []
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("done", False):
                    break
                chunks.append(data.get("response", ""))
            return {"response": "".join(chunks), "done": True, "usage": {"prompt_tokens": 0, "total_tokens": 0}}


def _build_body(
    model: str,
    messages: list[dict[str, str]],
    temperature: float | None,
    format: dict | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
         "model": model,
         "messages": messages,
         "keep_alive": "60m",
         "num_ctx": 32768,
     }
    if temperature is not None:
        body["temperature"] = temperature
    if format is not None:
        body["format"] = format
    return body
