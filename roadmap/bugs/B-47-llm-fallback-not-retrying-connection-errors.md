---
title: "LLM fallback never triggered: openai.APIConnectionError not treated as retryable"
status: new
urgency: 3
size: medium
created: 2026-07-16
ticket_id: B-47
labels:
- llm-client
- fallback
design:
plan:
pr:
  url:
  branch:
---

## Description

### Symptom

When the primary LLM server (`llm.host` in config) is offline or returns a connection error, the fallback host (`llm.fallback_host`) is never tried. The game crashes with `openai.APIConnectionError` and the user never reaches the backup.

### Root Cause

In `ccya/llm_client.py`, the `_is_retryable()` method only checks for `httpx.HTTPError` subclasses:

```python
@staticmethod
def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, httpx.HTTPError)
```

`openai.APIConnectionError` is not a subclass of `httpx.HTTPError`. It inherits from `OpenAIError` → `Exception`. Similarly, `httpx.ConnectError` may be swallowed by the OpenAI SDK wrapper.

### Evidence

(2026-07-16) Config set to `host: http://10.75.100.51:1234/v1` (internal network, LMStudio). When 10.75.100.51 returns a connection error, the fallback at `http://127.0.0.1:8000/v1` is never touched because `_is_retryable()` returns False.

### Fix Plan

Add `openai.APIConnectionError` and `httpx.ConnectError` to `_is_retryable()`:

```python
from openai import APIConnectionError
import httpx

@staticmethod
def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (httpx.HTTPError, APIConnectionError))
```

### Impact

With this fix — and the config host/fallback swap discussed in this eval session — non-primary LLM backends (like the local MacBook) can work as proper fallbacks when the primary is down. Currently it's a hard failure.