"""Thin async client for OpenAI-compatible chat completions (mlx_lm.server).

Wire protocol: /v1/chat/completions (OpenAI).
Model is loaded once at server startup and stays resident.
No keep_alive, no num_ctx API knob, no format/grammar constraints.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, AsyncIterator, MutableMapping

from openai import AsyncOpenAI

import httpx

from ccya.llm_mock import _mock_extract_chat, _mock_stream
from ccya.errors import LlmcApiError, LlmcRateLimit, LlmcTimeout

_log = logging.getLogger(__name__)

_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

_client: AsyncOpenAI | None = None


def _get_client(base_url: str) -> AsyncOpenAI:
    global _client
    if _client is None:
        # Configure httpx with explicit timeouts
        # read=None: let asyncio.timeout() handle wall-clock timeout
        # This prevents httpx's per-chunk read timeout from firing during slow generation
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=None,
                write=10.0,
                pool=10.0,
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
            ),
        )
        _client = AsyncOpenAI(base_url=base_url, api_key="local", http_client=http_client)
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
                _log.debug("Truncation skipped: content fits within budget (%d <= %d)", total, budget)
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
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
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
    }
    if timeout is not None:
        kwargs["timeout"] = timeout
    if temperature is not None:
        kwargs["temperature"] = temperature
    if top_p is not None:
        kwargs["top_p"] = float(top_p)
    if frequency_penalty is not None:
        kwargs["frequency_penalty"] = float(frequency_penalty)
    if seed is not None:
        kwargs["seed"] = int(seed)
    stream = await client.chat.completions.create(**kwargs)
    try:
        async for chunk in stream:
            if not chunk.choices:
                if stream_stats is not None and chunk.usage is not None:
                    stream_stats["prompt_eval_count"] = chunk.usage.prompt_tokens or 0
                    stream_stats["eval_count"] = chunk.usage.completion_tokens or 0
                continue
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
    finally:
        await stream.response.aclose()


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    if _MOCK_MODE:
        return _mock_extract_chat(messages)

    est_tokens = sum(int(len(m.get("content", "")) / 3.5) for m in messages)
    _log.info("chat: model=%s messages=%d est_tokens=%d max_tokens=%s", model, len(messages), est_tokens, max_tokens)
    t0 = time.monotonic()
    _log.debug("chat: sending request host=%s model=%s timeout=%s", host, model, timeout)
    try:
        client = _get_client(host)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if timeout is not None:
            kwargs["timeout"] = timeout
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if top_p is not None:
            kwargs["top_p"] = float(top_p)
        if frequency_penalty is not None:
            kwargs["frequency_penalty"] = float(frequency_penalty)
        if seed is not None:
            kwargs["seed"] = int(seed)
        _log.debug("chat: request sent, waiting for response...")
        resp = await client.chat.completions.create(**kwargs)
        _log.debug("chat: response received, extracting content...")
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
            _log.debug("LLM error reclassified: HTTPStatusError(429) -> LlmcRateLimit")
            raise LlmcRateLimit("Rate limited by LLM provider") from exc
        else:
            _log.debug("LLM error reclassified: HTTPStatusError(%d) -> LlmcApiError", exc.response.status_code)
            raise LlmcApiError(
                f"LLM API error {exc.response.status_code}: {exc.response.text}",
                status_code=exc.response.status_code,
            ) from exc
    except httpx.RequestError as exc:
        elapsed = time.monotonic() - t0
        _log.debug("LLM error reclassified: RequestError -> LlmcTimeout")
        raise LlmcTimeout(f"Network error connecting to LLM: {exc}") from exc
    except Exception as exc:
        elapsed = time.monotonic() - t0
        retry_count = getattr(exc, "retry_count", None)
        msg = f"chat: failed after {elapsed:.1f}s: {exc}"
        if retry_count is not None:
            msg += f" (retries={retry_count})"
        _log.warning(msg)
        raise
