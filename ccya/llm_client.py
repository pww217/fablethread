"""Thin async client for OpenAI-compatible chat completions (mlx_lm.server).

Wire protocol: /v1/chat/completions (OpenAI).
Model is loaded once at server startup and stays resident.
No keep_alive, no num_ctx API knob, no format/grammar constraints.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, AsyncIterator, MutableMapping

from openai import AsyncOpenAI

import httpx

from ccya.errors import LlmcApiError, LlmcRateLimit, LlmcTimeout

_log = logging.getLogger(__name__)

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
            {"id": "at_docking_ring_7", "text": "You are at Docking Ring 7.", "turn": 0},
            {"id": "hand_terminal_pinger", "text": "Your hand terminal carries an encrypted pinger.", "turn": 0},
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
            {"id": "pinger_shell_company", "text": "The pinger is from a shell company called 'Quiet Systems.'", "turn": 0},
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
            {"id": "hauler_passage", "text": "A hauler offers passage to the lower ring.", "turn": 0},
            {"id": "cargo_bay_terminal", "text": "There is a terminal in the cargo bay.", "turn": 0},
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


_client: AsyncOpenAI | None = None


def _get_client(base_url: str) -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=base_url, api_key="local")
    return _client


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)



def strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


def trim_messages(
    messages: list[dict[str, str]], max_tokens: int
) -> tuple[list[dict[str, str]], bool, int]:
    """Return (trimmed_messages, was_truncated, chars_removed).

    was_truncated is True when any message was dropped or truncated.
    chars_removed is the total characters removed from all messages.
    """
    def estimate(s: str) -> int:
        return int(len(s) / 3.5)

    # Capture original total chars before any mutation
    original_total_chars = sum(len(m.get("content", "")) for m in messages)

    # System message is never dropped or truncated
    if messages and messages[0].get("role") == "system":
        sys_est = estimate(messages[0].get("content", ""))
        if sys_est > max_tokens:
            raise ValueError(
                f"System message ({sys_est} tokens) exceeds budget ({max_tokens} tokens)"
            )

    total = sum(estimate(m.get("content", "")) for m in messages)
    while total > max_tokens:
        # Find the oldest non-system message to truncate
        idx = next(
            (i for i, m in enumerate(messages) if m.get("role") != "system"),
            None,
        )
        if idx is None:
            break  # only system messages remain, already checked above
        msg = messages[idx]
        content = msg.get("content", "")
        est = estimate(content)
        budget = max_tokens - (total - est)
        if budget <= 0:
            # No room for this message at all — drop it
            messages.pop(idx)
            total = sum(estimate(m.get("content", "")) for m in messages)
        else:
            head_keep = min(2000, int(budget * 3.5))
            tail_keep = min(500, max(0, int(budget * 3.5) - head_keep))
            if head_keep + tail_keep >= len(content):
                pass
            else:
                msg["content"] = (
                    content[:head_keep]
                    + "\n\n[... truncated — older context removed ...]\n\n"
                    + content[-tail_keep:]
                )
            total = max_tokens + 1  # exit loop
    new_total_chars = sum(len(m.get("content", "")) for m in messages)
    chars_removed = original_total_chars - new_total_chars
    was_truncated = chars_removed > 0
    return messages, was_truncated, chars_removed


async def chat_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
) -> AsyncIterator[str]:
    if _MOCK_MODE:
        async for chunk in _mock_stream():
            yield chunk
        if stream_stats is not None:
            stream_stats["prompt_eval_count"] = 0
            stream_stats["eval_count"] = 0
        return

    client = _get_client(host)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        "timeout": timeout,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    stream = await client.chat.completions.create(**kwargs)

    async for chunk in stream:
        if not chunk.choices:
            if stream_stats is not None and chunk.usage is not None:
                stream_stats["prompt_eval_count"] = chunk.usage.prompt_tokens or 0
                stream_stats["eval_count"] = chunk.usage.completion_tokens or 0
            continue
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    timeout: float = 180.0,
) -> dict[str, Any]:
    if _MOCK_MODE:
        return _mock_extract_chat(messages)

    est_tokens = sum(int(len(m.get("content", "")) / 3.5) for m in messages)
    _log.info("chat: model=%s messages=%d est_tokens=%d", model, len(messages), est_tokens)
    t0 = time.monotonic()
    try:
        client = _get_client(host)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": timeout,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        resp = await client.chat.completions.create(**kwargs)
        elapsed = time.monotonic() - t0
        content = resp.choices[0].message.content or ""
        _log.info(
            "chat: done in %.1fs prompt_tokens=%d completion_tokens=%d",
            elapsed,
            resp.usage.prompt_tokens if resp.usage else 0,
            resp.usage.completion_tokens if resp.usage else 0,
        )
        return {
            "response": content,
            "done": True,
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
        }
    except TimeoutError as exc:
        elapsed = time.monotonic() - t0
        raise LlmcTimeout(f"LLM request timed out after {timeout:.1f}s") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise LlmcRateLimit("Rate limited by LLM provider") from exc
        else:
            raise LlmcApiError(
                f"LLM API error {exc.response.status_code}: {exc.response.text}",
                status_code=exc.response.status_code,
            ) from exc
    except httpx.RequestError as exc:
        elapsed = time.monotonic() - t0
        raise LlmcTimeout(f"Network error connecting to LLM: {exc}") from exc
    except Exception as exc:
        elapsed = time.monotonic() - t0
        retry_count = getattr(exc, "retry_count", None)
        msg = f"chat: failed after {elapsed:.1f}s: {exc}"
        if retry_count is not None:
            msg += f" (retries={retry_count})"
        _log.warning(msg)
        raise
