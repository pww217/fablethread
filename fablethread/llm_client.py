"""Thin async client for OpenAI-compatible chat completions.

Wire protocol: /v1/chat/completions (OpenAI-compatible).

Primary backend: configurable via ``llm.host`` in config.yaml
(defaults to local LMStudio on port 1234).
API key: configurable via ``llm.api_key`` in config.yaml
(defaults to ``"local"`` for keyless servers; set for hosted providers).
Configurable fallback via ``llm.fallback_host`` in config.yaml.

num_ctx controls the server-side input context window (passed via extra_body).
No keep_alive, no format/grammar constraints.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, MutableMapping

from openai import APIConnectionError, AsyncOpenAI

import httpx

from fablethread.llm_mock import _mock_extract_chat, _mock_stream
from fablethread.errors import LlmcApiError, LlmcRateLimit, LlmcTimeout

_log = logging.getLogger(__name__)

_MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")

_client: dict[str, AsyncOpenAI] | None = None

# Fallback state — module-level singleton for all callers
# Initialize to far future so fallback doesn't trigger on first call
_last_fallback_time: float = float("inf")
# Health check cache per host: {host: (last_check_time, healthy_bool)}
_health_cache: dict[str, tuple[float, bool]] = {}


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


async def _try_host(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    t0: float,
    *,
    api_key: str = "local",
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> LLMResult:
    """Make a single LLM call to the given host. Re-raises on failure."""
    return await _chat_openai_compat(
        host, model, messages, t0, api_key, temperature, max_tokens, top_p,
        frequency_penalty, seed, num_ctx, timeout, enable_thinking,
        reasoning_effort, thinking_budget,
    )


async def _try_host_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    api_key: str = "local",
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> AsyncIterator[str]:
    """Stream from the given host. Re-raises on failure."""
    client = _get_client(host, api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if timeout is not None:
        kwargs["timeout"] = httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=10.0)
    kwargs.update(_build_chat_kwargs(
        temperature=temperature, top_p=top_p,
        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    ))
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


def _build_chat_kwargs(
    temperature: float | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> dict[str, Any]:
    """Build LLM chat kwargs/payload from common parameters."""
    kwargs: dict[str, Any] = {}
    if temperature is not None:
        kwargs["temperature"] = float(temperature)
    if top_p is not None:
        kwargs["top_p"] = float(top_p)
    if frequency_penalty is not None:
        kwargs["frequency_penalty"] = float(frequency_penalty)
    if seed is not None:
        kwargs["seed"] = int(seed)
    extra: dict[str, Any] = {}
    if num_ctx is not None:
        extra["num_ctx"] = num_ctx
    if enable_thinking is not None:
        extra["enable_thinking"] = enable_thinking
    if reasoning_effort is not None:
        extra["reasoning_effort"] = reasoning_effort
    if thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    if extra:
        kwargs["extra_body"] = extra
    return kwargs


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception represents a transient failure worth retrying."""
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, (LlmcRateLimit, LlmcApiError)):
        return True
    if isinstance(exc, httpx.HTTPError):
        return True
    if isinstance(exc, APIConnectionError):
        return True
    return False


def _is_model_not_loaded(exc: BaseException) -> bool:
    """Return True if the error is a 'No models loaded' transient state from any backend."""
    msg = str(exc).lower()
    if "no models loaded" in msg:
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 400:
            try:
                body = exc.response.json()
                inner = body.get("error", {}).get("message", "")
                if "no models loaded" in inner.lower():
                    return True
            except Exception:
                pass
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


async def _check_health(host: str) -> bool:
    """Check if LLM host is healthy via /v1/models endpoint. Results cached for 30s."""
    now = time.monotonic()
    if host in _health_cache:
        last_time, healthy = _health_cache[host]
        if now - last_time < 30.0:
            return healthy
    try:
        url = host.rstrip("/")
        if url.endswith("/v1"):
            url = url[:-3]
        elif url.endswith("/v1/"):
            url = url[:-4]
        timeout = httpx.Timeout(connect=2.0, read=3.0, write=5.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{url}/v1/models")
        healthy = resp.status_code == 200 and "data" in (resp.json() or {})
        _health_cache[host] = (now, healthy)
        return healthy
    except Exception:
        _health_cache[host] = (now, False)
        return False


async def _chat_with_fallback(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    api_key: str = "local",
    fallback_host: str,
    fallback_cooldown_s: int,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> LLMResult:
    """Call LLM with single attempt on primary and fallback to secondary if primary is down.

    Per-request flow:
    1. Try primary → success: use it, reset cooldown timer
    2. Try primary → failure → immediately fall back to secondary
    3. Cooldown: once fallen back, keep using secondary for cooldown_s seconds
    """
    t0 = time.monotonic()

    # Health check primary before attempting inference
    if host and not fallback_host:
        pass
    elif host:
        try:
            if await _check_health(host):
                _log.debug("Primary health OK, attempting inference")
            else:
                _log.warning("Primary /health check failed, using fallback")
                if _should_fallback(fallback_host, fallback_cooldown_s):
                    _record_fallback()
                    return await _try_host(
                        fallback_host, model, messages, t0,
                        api_key=api_key, temperature=temperature, max_tokens=max_tokens,
                        timeout=timeout, top_p=top_p,
                        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
                        enable_thinking=enable_thinking,
                        reasoning_effort=reasoning_effort,
                        thinking_budget=thinking_budget,
                    )
        except Exception:
            _log.debug("Health check failed, trying primary anyway")

    # Single attempt to primary
    primary_failed = False
    primary_exc: Exception | None = None
    try:
        return await _try_host(
            host, model, messages, t0,
            api_key=api_key, temperature=temperature, max_tokens=max_tokens,
            timeout=timeout, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            thinking_budget=thinking_budget,
        )
    except Exception as exc:
        primary_failed = True
        primary_exc = exc
        if _is_model_not_loaded(exc):
            _log.info(
                "Primary 'No models loaded' — waiting 30s for model to load, then retrying",
            )
            await asyncio.sleep(30.0)
            try:
                return await _try_host(
                    host, model, messages, t0,
                    api_key=api_key, temperature=temperature, max_tokens=max_tokens,
                    timeout=timeout, top_p=top_p,
                    frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
                    enable_thinking=enable_thinking,
                    reasoning_effort=reasoning_effort,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc2:
                primary_exc = exc2

        if not _is_retryable(exc):
            _log.debug("Non-retryable error from primary: %s", exc)

    # Attempt fallback when primary fails (retryable or non-retryable)
    if primary_failed:
        _log.warning(
            "Primary LLM host %s failed, falling back to %s: %s",
            host, fallback_host, primary_exc,
        )
        if _should_fallback(fallback_host, fallback_cooldown_s):
            _record_fallback()
            try:
                return await _try_host(
                    fallback_host, model, messages, t0,
                    api_key=api_key, temperature=temperature, max_tokens=max_tokens,
                    timeout=timeout, top_p=top_p,
                    frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
                    enable_thinking=enable_thinking,
                    reasoning_effort=reasoning_effort,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc:
                _log.warning(
                    "Fallback LLM host %s also failed, re-raising primary error: %s",
                    fallback_host, exc,
                )
                raise

    # Still in cooldown — check primary health before trying inference
    try:
        if not await _check_health(host):
            _log.debug("Primary /health check failed, using fallback %s", fallback_host)
            return await _try_host(
                fallback_host, model, messages, t0,
                temperature=temperature, max_tokens=max_tokens,
                timeout=timeout, top_p=top_p,
                frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            )
        return await _try_host(
            host, model, messages, t0,
            temperature=temperature, max_tokens=max_tokens,
            timeout=timeout, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        )
    except Exception as exc:
        # Primary inference failed during cooldown, try fallback
        if fallback_host:
            _log.warning(
                "Primary failed during cooldown, attempting fallback %s: %s",
                fallback_host, exc,
            )
            try:
                return await _try_host(
                    fallback_host, model, messages, t0,
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
    api_key: str = "local",
    fallback_host: str,
    fallback_cooldown_s: int,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> AsyncIterator[str]:
    """Stream LLM response with single attempt on primary and fallback to secondary.

    Same retry/fallback logic as _chat_with_fallback but for streaming.
    """
    _stream_kwargs: dict[str, Any] = dict(
        api_key=api_key, temperature=temperature, timeout=timeout,
        stream_stats=stream_stats, top_p=top_p,
        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    )
    primary_failed = False
    primary_exc: Exception | None = None
    try:
        async for chunk in _try_host_stream(
            host, model, messages, **_stream_kwargs,
        ):
            yield chunk
        return
    except Exception as exc:
        primary_failed = True
        primary_exc = exc
        if _is_model_not_loaded(exc):
            _log.info(
                "Primary 'No models loaded' — waiting 30s for model to load, then retrying",
            )
            await asyncio.sleep(30.0)
            try:
                async for chunk in _try_host_stream(
                    host, model, messages, **_stream_kwargs,
                ):
                    yield chunk
                return
            except Exception as exc2:
                primary_exc = exc2

        if not _is_retryable(exc):
            _log.debug("Non-retryable error from primary stream: %s", exc)

    if primary_failed:
        _log.warning(
            "Primary LLM host %s stream failed, falling back to %s: %s",
            host, fallback_host, primary_exc,
        )
        if _should_fallback(fallback_host, fallback_cooldown_s):
            _record_fallback()
            try:
                async for chunk in _try_host_stream(
                    fallback_host, model, messages, **_stream_kwargs,
                ):
                    yield chunk
                return
            except Exception as exc:
                _log.warning(
                    "Fallback LLM host %s stream also failed, re-raising primary error: %s",
                    fallback_host, exc,
                )
                raise

        # Still in cooldown — check primary health before trying stream
        try:
            if not await _check_health(host):
                _log.debug("Primary /health check failed, using fallback %s", fallback_host)
                async for chunk in _try_host_stream(
                    fallback_host, model, messages, **_stream_kwargs,
                ):
                    yield chunk
                return
            async for chunk in _try_host_stream(
                host, model, messages, **_stream_kwargs,
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
                        api_key=api_key, temperature=temperature, timeout=timeout,
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


def _get_client(base_url: str, api_key: str = "local") -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = {}
    cache_key = (base_url, api_key)
    if cache_key not in _client:
        # OpenAI SDK appends /chat/completions to base_url, so we need /v1 prefix
        # for OpenAI-compatible endpoints (LMStudio, OMLX, etc.)
        if not base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        http_client = _make_httpx(read_timeout=None)
        _client[cache_key] = AsyncOpenAI(
            base_url=base_url, api_key=api_key, http_client=http_client
        )
    return _client[cache_key]


def _make_httpx(read_timeout: float | None) -> httpx.AsyncClient:
    """Create an httpx.AsyncClient with standard connection pool config."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=3.0, read=read_timeout, write=10.0, pool=10.0),
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
    api_key: str = "local",
    fallback_host: str = "",
    fallback_cooldown_s: int = 300,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
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
        api_key=api_key, fallback_host=fallback_host, fallback_cooldown_s=fallback_cooldown_s,
        temperature=temperature, timeout=timeout,
        stream_stats=stream_stats, top_p=top_p,
        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    ):
        yield chunk


async def chat(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    api_key: str = "local",
    fallback_host: str = "",
    fallback_cooldown_s: int = 300,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> LLMResult:
    """Call LLM and return standardized LLMResult with normalized metrics.

    Uses OpenAI-compatible /v1/chat/completions endpoint.
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
            api_key=api_key, fallback_host=fallback_host, fallback_cooldown_s=fallback_cooldown_s,
            temperature=temperature, max_tokens=max_tokens,
            timeout=timeout, top_p=top_p,
            frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            thinking_budget=thinking_budget,
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
    t0: float, api_key: str,
    temperature: float | None, max_tokens: int | None,
    top_p: float | None, frequency_penalty: float | None,
    seed: int | None, num_ctx: int | None, timeout: float,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> LLMResult:
    """Call via OpenAI-compatible /v1/chat/completions endpoint."""
    client = _get_client(host, api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if timeout is not None:
        kwargs["timeout"] = httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=10.0)
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    kwargs.update(_build_chat_kwargs(
        temperature=temperature, top_p=top_p,
        frequency_penalty=frequency_penalty, seed=seed, num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    ))
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


# ---------------------------------------------------------------------------
# Config-based wrappers — extract fallback params from EngineConfig
# ---------------------------------------------------------------------------

async def chat_with_config(
    config: Any,
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 180.0,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> LLMResult:
    """Call LLM with fallback logic, extracting host/model/fallback from EngineConfig."""
    return await chat(
        host=config.host,
        api_key=api_key if api_key is not None else config.api_key,
        model=config.model,
        messages=messages,
        fallback_host=config.fallback_host,
        fallback_cooldown_s=config.fallback_cooldown_s,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        seed=seed,
        num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    )


async def chat_stream_with_config(
    config: Any,
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    temperature: float | None = None,
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    enable_thinking: bool | None = None,
    reasoning_effort: str | None = None,
    thinking_budget: int | None = None,
) -> AsyncIterator[str]:
    """Stream LLM response with fallback logic, extracting host/model/fallback from EngineConfig."""
    async for chunk in chat_stream(
        host=config.host,
        api_key=api_key if api_key is not None else config.api_key,
        model=config.model,
        messages=messages,
        fallback_host=config.fallback_host,
        fallback_cooldown_s=config.fallback_cooldown_s,
        temperature=temperature,
        timeout=timeout,
        stream_stats=stream_stats,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        seed=seed,
        num_ctx=num_ctx,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        thinking_budget=thinking_budget,
    ):
        yield chunk
