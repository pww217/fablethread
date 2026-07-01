"""Thin async client for OpenAI-compatible chat completions (Ollama).

Wire protocol: /v1/chat/completions (OpenAI) or /api/chat (Ollama native).

Primary backend: Ollama on 10.75.100.51 (VladimirGav/gemma4-26b-16GB-VRAM:latest, RTX 5070 Ti — fast).
Fallback: localhost:8080 via llama-swap (Qwen3.6-35B-A3B-OptiQ-4bit, MacBook — slower).

num_ctx controls the server-side input context window (passed via extra_body).
No keep_alive, no format/grammar constraints.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, MutableMapping

from openai import AsyncOpenAI

import httpx

from ccya.llm_mock import _mock_extract_chat, _mock_stream
from ccya.errors import LlmcApiError, LlmcRateLimit, LlmcTimeout

_log = logging.getLogger(__name__)

_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

_client: dict[str, AsyncOpenAI] | None = None

# Fallback state — module-level singleton for all callers
# Initialize to far future so fallback doesn't trigger on first call
_last_fallback_time: float = float("inf")


@dataclass(frozen=True)
class LLMResult:
    """Standardized LLM response with normalized metrics."""
    content: str
    usage: dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })
    elapsed_ms: float = 0.0


def _is_ollama_native(host: str) -> bool:
    return "/api/chat" in host


def _ns_to_seconds(ns: int) -> float:
    return ns / 1e9


async def _try_host(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    t0: float,
    *,
    fallback_model: str = "",
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> LLMResult:
    """Make a single LLM call to the given host. Re-raises on failure."""
    resolved_model = _resolve_model(host, model, fallback_model)
    if _is_ollama_native(host):
        return await _chat_ollama_native(
            host, resolved_model, messages, t0, temperature, top_p, frequency_penalty, seed, num_ctx,
        )
    else:
        return await _chat_openai_compat(
            host, resolved_model, messages, t0, temperature, max_tokens, top_p, frequency_penalty, seed, num_ctx, timeout,
        )


def _resolve_model(host: str, model: str, fallback_model: str) -> str:
    """Resolve the model name for the given host. Uses fallback_model if host is the fallback."""
    if fallback_model and not _is_ollama_native(host):
        return fallback_model
    return model


async def _try_host_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    fallback_model: str = "",
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> AsyncIterator[str]:
    """Stream from the given host. Re-raises on failure."""
    resolved_model = _resolve_model(host, model, fallback_model)
    if _is_ollama_native(host):
        async for chunk in _chat_stream_ollama_native(
            host, resolved_model, messages, temperature, top_p, frequency_penalty, seed, num_ctx, stream_stats,
        ):
            yield chunk
        return
    client = _get_client(host)
    kwargs: dict[str, Any] = {
        "model": resolved_model,
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
    if num_ctx is not None:
        kwargs["extra_body"] = {"num_ctx": num_ctx}
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


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception represents a transient failure worth retrying."""
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, httpx.RequestError):
        return True
    return False


def _should_fallback(fallback_host: str, cooldown_s: int) -> bool:
    """Return True if we should attempt the fallback host."""
    if not fallback_host:
        return False
    if _last_fallback_time == float("inf"):
        return True
    elapsed = time.monotonic() - _last_fallback_time
    return elapsed >= cooldown_s


def _record_fallback() -> None:
    """Mark that we've fallen back to the secondary host."""
    global _last_fallback_time
    _last_fallback_time = time.monotonic()


async def _chat_with_fallback(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    fallback_host: str,
    fallback_model: str,
    fallback_cooldown_s: int,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> LLMResult:
    """Call LLM with retry on primary and fallback to secondary if primary is down.

    Per-request flow:
    1. Try primary → success: use it, reset cooldown timer
    2. Try primary → failure → wait 2s → retry primary once (confirms truly down)
    3. Both primary attempts fail → fall back to secondary, log warning, set cooldown
    4. Cooldown: once fallen back, keep using secondary for cooldown_s seconds
    """
    t0 = time.monotonic()

    # Try primary (up to 2 attempts with 2s gap to confirm it's truly down)
    for attempt in range(2):
        if attempt > 0:
            _log.debug("Primary retry after 2s delay (attempt %d/2)", attempt + 1)
            await asyncio.sleep(2.0)
        try:
            return await _try_host(
                host, model, messages, t0,
                fallback_model=fallback_model,
                temperature=temperature, max_tokens=max_tokens,
                timeout=timeout, top_p=top_p,
                frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            )
        except Exception as exc:
            if not _is_retryable(exc):
                _log.debug("Non-retryable error, not retrying: %s", exc)
                raise
            if attempt < 1:
                _log.debug("Primary attempt %d failed (retryable), retrying: %s", attempt + 1, exc)
                continue
            # Both primary attempts failed
            _log.warning(
                "Primary LLM host %s failed after 2 attempts, falling back to %s: %s",
                host, fallback_host, exc,
            )
            break
    else:
        # Should not reach here, but just in case
        raise

    # Attempt fallback
    if _should_fallback(fallback_host, fallback_cooldown_s):
        _record_fallback()
        try:
            return await _try_host(
                fallback_host, model, messages, t0,
                fallback_model=fallback_model,
                temperature=temperature, max_tokens=max_tokens,
                timeout=timeout, top_p=top_p,
                frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            )
        except Exception as exc:
            _log.warning(
                "Fallback LLM host %s also failed, re-raising primary error: %s",
                fallback_host, exc,
            )
            raise

    # Still in cooldown — use primary anyway (might be back up)
    try:
        return await _try_host(
            host, model, messages, t0,
            fallback_model=fallback_model,
            temperature=temperature, max_tokens=max_tokens,
            timeout=timeout, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        )
    except Exception as exc:
        # Primary failed again during cooldown, try fallback anyway
        if fallback_host:
            _log.warning(
                "Primary failed during cooldown, attempting fallback %s: %s",
                fallback_host, exc,
            )
            try:
                return await _try_host(
                    fallback_host, model, messages, t0,
                    fallback_model=fallback_model,
                    temperature=temperature, max_tokens=max_tokens,
                    timeout=timeout, top_p=top_p,
                    frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
                )
            except Exception as fallback_exc:
                _log.warning(
                    "Fallback also failed during cooldown, re-raising primary error: %s",
                    fallback_exc,
                )
                raise
        raise


async def _chat_stream_with_fallback(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    fallback_host: str,
    fallback_model: str,
    fallback_cooldown_s: int,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> AsyncIterator[str]:
    """Stream LLM response with retry on primary and fallback to secondary.

    Same retry/fallback logic as _chat_with_fallback but for streaming.
    """
    # Try primary (up to 2 attempts with 2s gap)
    for attempt in range(2):
        if attempt > 0:
            _log.debug("Primary stream retry after 2s delay (attempt %d/2)", attempt + 1)
            await asyncio.sleep(2.0)
        try:
            async for chunk in _try_host_stream(
                host, model, messages,
                fallback_model=fallback_model,
                temperature=temperature, timeout=timeout,
                stream_stats=stream_stats, top_p=top_p,
                frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            ):
                yield chunk
            return
        except Exception as exc:
            if not _is_retryable(exc):
                _log.debug("Non-retryable error, not retrying stream: %s", exc)
                raise
            if attempt < 1:
                _log.debug("Primary stream attempt %d failed (retryable), retrying: %s", attempt + 1, exc)
                continue
            _log.warning(
                "Primary LLM host %s stream failed after 2 attempts, falling back to %s: %s",
                host, fallback_host, exc,
            )
            break
    else:
        raise

    # Attempt fallback
    if _should_fallback(fallback_host, fallback_cooldown_s):
        _record_fallback()
        try:
            async for chunk in _try_host_stream(
                fallback_host, model, messages,
                fallback_model=fallback_model,
                temperature=temperature, timeout=timeout,
                stream_stats=stream_stats, top_p=top_p,
                frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            ):
                yield chunk
            return
        except Exception as exc:
            _log.warning(
                "Fallback LLM host %s stream also failed, re-raising primary error: %s",
                fallback_host, exc,
            )
            raise

    # Still in cooldown — try primary again
    try:
        async for chunk in _try_host_stream(
            host, model, messages,
            fallback_model=fallback_model,
            temperature=temperature, timeout=timeout,
            stream_stats=stream_stats, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        ):
            yield chunk
        return
    except Exception as exc:
        if fallback_host:
            _log.warning(
                "Primary stream failed during cooldown, attempting fallback %s: %s",
                fallback_host, exc,
            )
            try:
                async for chunk in _try_host_stream(
                    fallback_host, model, messages,
                    fallback_model=fallback_model,
                    temperature=temperature, timeout=timeout,
                    stream_stats=stream_stats, top_p=top_p,
                    frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
                ):
                    yield chunk
                return
            except Exception as fallback_exc:
                _log.warning(
                    "Fallback stream also failed during cooldown, re-raising primary error: %s",
                    fallback_exc,
                )
                raise
        raise


def _get_client(base_url: str) -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = {}
    if base_url not in _client:
        # OpenAI SDK appends /chat/completions to base_url, so we need /v1 prefix
        # for OpenAI-compatible endpoints (llama-swap, etc.)
        # Ollama-native hosts use /api/chat directly via httpx, not this path
        if not base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        http_client = _make_httpx(read_timeout=None)
        _client[base_url] = AsyncOpenAI(
            base_url=base_url, api_key="local", http_client=http_client
        )
    return _client[base_url]


def _make_httpx(read_timeout: float | None) -> httpx.AsyncClient:
    """Create an httpx.AsyncClient with standard connection pool config."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=read_timeout, write=10.0, pool=10.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50,
        ),
    )


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
    fallback_host: str = "",
    fallback_model: str = "",
    fallback_cooldown_s: int = 300,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> AsyncIterator[str]:
    if _MOCK_MODE:
        async for chunk in _mock_stream():
            yield chunk
        if stream_stats is not None:
            stream_stats["prompt_eval_count"] = 0
            stream_stats["eval_count"] = 0
        return

    async for chunk in _chat_stream_with_fallback(
        host, model, messages,
        fallback_host=fallback_host, fallback_model=fallback_model, fallback_cooldown_s=fallback_cooldown_s,
        temperature=temperature, timeout=timeout,
        stream_stats=stream_stats, top_p=top_p,
        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
    ):
        yield chunk


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    fallback_host: str = "",
    fallback_model: str = "",
    fallback_cooldown_s: int = 300,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
) -> LLMResult:
    """Call LLM and return standardized LLMResult with normalized metrics.

    Supports both OpenAI-compatible (/v1/chat/completions) and Ollama native
    (/api/chat) backends. Metrics are normalized to the same format regardless
    of backend.

    Falls back to fallback_host if the primary host is down (with retry logic).
    """
    if _MOCK_MODE:
        mock = _mock_extract_chat(messages)
        return LLMResult(
            content=mock.get("response", ""),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    est_tokens = sum(int(len(m.get("content", "")) / 3.5) for m in messages)
    _log.info("chat: model=%s messages=%d est_tokens=%d max_tokens=%s", model, len(messages), est_tokens, max_tokens)
    t0 = time.monotonic()
    _log.debug("chat: sending request host=%s model=%s timeout=%s", host, model, timeout)

    try:
        result = await _chat_with_fallback(
            host, model, messages,
            fallback_host=fallback_host, fallback_model=fallback_model, fallback_cooldown_s=fallback_cooldown_s,
            temperature=temperature, max_tokens=max_tokens,
            timeout=timeout, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        )
        return result
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


async def _chat_openai_compat(
    host: str, model: str, messages: list[dict[str, str]],
    t0: float, temperature: float | None, max_tokens: int | None,
    top_p: float | None, frequency_penalty: float | None,
    seed: int | None, num_ctx: int | None, timeout: float,
) -> LLMResult:
    """Call via OpenAI-compatible /v1/chat/completions endpoint."""
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
    if num_ctx is not None:
        kwargs["extra_body"] = {"num_ctx": num_ctx}
    _log.debug("chat: request sent, waiting for response...")
    resp = await client.chat.completions.create(**kwargs)
    _log.debug("chat: response received, extracting content...")
    elapsed = time.monotonic() - t0
    content = resp.choices[0].message.content or ""
    usage = resp.usage or type("Usage", (), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})()
    _log.info(
        "chat: done in %.1fs prompt_tokens=%d completion_tokens=%d",
        elapsed,
        usage.prompt_tokens,
        usage.completion_tokens,
    )
    return LLMResult(
        content=content,
        usage={
            "prompt_tokens": usage.prompt_tokens or 0,
            "completion_tokens": usage.completion_tokens or 0,
            "total_tokens": usage.total_tokens or 0,
        },
        elapsed_ms=elapsed * 1000,
    )


async def _chat_ollama_native(
    host: str, model: str, messages: list[dict[str, str]],
    t0: float, temperature: float | None, top_p: float | None,
    frequency_penalty: float | None, seed: int | None, num_ctx: int | None,
) -> LLMResult:
    """Call via Ollama native /api/chat endpoint.

    Returns token metrics from the native response and normalizes them to
    the same format as the OpenAI-compatible endpoint.
    """
    http_client = _make_httpx(read_timeout=300.0)
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
    }
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if top_p is not None:
        payload["top_p"] = float(top_p)
    if frequency_penalty is not None:
        payload["frequency_penalty"] = float(frequency_penalty)
    if seed is not None:
        payload["seed"] = int(seed)
    if num_ctx is not None:
        payload["num_ctx"] = int(num_ctx)

    try:
        resp = await http_client.post(f"{host}", json=payload)
        resp.raise_for_status()
        data = resp.json()
    finally:
        await http_client.aclose()

    elapsed = time.monotonic() - t0

    content = (data.get("message") or {}).get("content", "")
    prompt_eval_count = data.get("prompt_eval_count", 0)
    eval_count = data.get("eval_count", 0)

    _log.info(
        "chat: done in %.1fs prompt_tokens=%d completion_tokens=%d",
        elapsed, prompt_eval_count, eval_count,
    )
    return LLMResult(
        content=content,
        usage={
            "prompt_tokens": prompt_eval_count,
            "completion_tokens": eval_count,
            "total_tokens": prompt_eval_count + eval_count,
        },
        elapsed_ms=elapsed * 1000,
    )


async def _chat_stream_ollama_native(
    host: str, model: str, messages: list[dict[str, str]],
    temperature: float | None, top_p: float | None,
    frequency_penalty: float | None, seed: int | None, num_ctx: int | None,
    stream_stats: MutableMapping[str, Any] | None,
) -> AsyncIterator[str]:
    """Stream via Ollama native /api/chat endpoint with token metrics extraction."""
    http_client = _make_httpx(read_timeout=None)
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": False,
    }
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if top_p is not None:
        payload["top_p"] = float(top_p)
    if frequency_penalty is not None:
        payload["frequency_penalty"] = float(frequency_penalty)
    if seed is not None:
        payload["seed"] = int(seed)
    if num_ctx is not None:
        payload["num_ctx"] = int(num_ctx)

    try:
        async with http_client.stream("POST", f"{host}", json=payload) as resp:
            resp.raise_for_status()
            prompt_eval_count = 0
            eval_count = 0
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if data.get("done"):
                    prompt_eval_count = data.get("prompt_eval_count", prompt_eval_count)
                    eval_count = data.get("eval_count", eval_count)
                elif data.get("message", {}).get("content"):
                    yield data["message"]["content"]
    finally:
        await http_client.aclose()

    if stream_stats is not None:
        stream_stats["prompt_eval_count"] = prompt_eval_count
        stream_stats["eval_count"] = eval_count
