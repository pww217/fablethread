---
title: "General LLM client improvements: Ollama native API support, dual backend, call site consolidation"
status: done
urgency: 1
size: small
created: 2026-06-28
ticket_id: I-10
labels:
  - engine
  - llm
---

## Problem

Gemma 4 on Ollama (10.75.100.51) produces excessive thinking/reasoning output per request, causing:
- Slow turn times (35s+ per extraction)
- Inflated token counts (700-1000+ tokens per call when ~300-500 expected)
- Poor UX

The `think: false` parameter only works with Ollama's native `/api/chat` endpoint, not the OpenAI-compatible `/v1/chat/completions` endpoint. This is a known Ollama limitation.

LLM calls are spread across 8 call sites with duplicative logging/extract/parse patterns. Each site manually extracts `result["response"]` and `result["usage"]`, logs requests/responses, and handles errors.

## What Was Done

### Implemented

- **LLMResult dataclass** — standardized response with `content`, `usage`, `elapsed_ms`
- **Backend detection** — `_is_ollama_native()` routes to `/api/chat` or `/v1`
- **Ollama native `/api/chat` support** — `_chat_ollama_native()` extracts token metrics
- **OpenAI-compatible path** — `_chat_openai_compat()` preserves existing behavior
- **All 8 call sites updated** — use `result.content` / `result.usage` instead of dict access
- **Healthz updated** — detects backend type, queries `/api/tags` vs `/models`
- **Config updated** — host changed to `/api/chat`

### Verified

- Ollama native `/api/chat` with `think: false` returns token metrics:
  - `prompt_eval_count` → normalized to `prompt_tokens`
  - `eval_count` → normalized to `completion_tokens`
  - `total_duration` (ns) → normalized to `elapsed_ms`
- All imports successful across engine, ev, server modules
- Token counts reasonable (~20-30 tokens per call for simple queries)

## Plan

### Phase 1: Consolidate LLM call sites into a wrapper

**Problem:** 8 call sites each repeat the same 4-step pattern: log request → call `llm_chat()` → extract `result["response"]` / `result["usage"]` → log response → parse.

**Solution:** Add a wrapper function in `llm_client.py` that owns the logging/extract/parse lifecycle:

```python
# llm_client.py — new API
async def chat(
    config: EngineConfig,
    phase: str,           # "ruling", "extract_scene", "narrate", etc.
    messages: list[dict],
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    ...
) -> LLMResult:        # { "content": str, "usage": {...}, "phase": str, "elapsed_ms": float }
```

The wrapper handles: logging request/response, timing, extraction of content/usage, error handling. Each module only does its domain-specific parsing.

**Call sites to consolidate:**
- `engine/ruling.py:109` — ruling
- `engine/extraction/utils.py:181` — extraction
- `engine/seed.py:268` — seed
- `engine/world.py:86` — world
- `engine/generate_pack.py:98` — pack gen
- `engine/thread_sanitizer.py:67` — sanitizer
- `engine/turn.py:185` — narrate (stream)
- `engine/turn.py:657` — warmup

**Per-module params** (`config.ruling_temperature`, `config.extract_temperature`) become explicit wrapper args. This makes the config surface explicit rather than buried in per-module config objects.

### Phase 2: Add Ollama native `/api/chat` support with token metrics

**Problem:** Ollama native `/api/chat` returns token metrics in nanoseconds:
```json
{
  "prompt_eval_count": 69,
  "prompt_eval_duration": 348582000,
  "eval_count": 142,
  "eval_duration": 1532542000,
  "total_duration": 41027689100
}
```

The current `llm_client.py` uses the OpenAI SDK which routes through `/v1/chat/completions` and doesn't expose these metrics.

**Solution:** Add backend detection (`/api/chat` in host) to route to native Ollama API via raw `httpx`. Normalize metrics to the same format as OpenAI-compatible endpoint:
- `prompt_eval_count` → `prompt_tokens`
- `eval_count` → `completion_tokens`
- `total_duration` (ns) → `total_ms` (milliseconds)

### Files to change

- `ccya/llm_client.py` — add wrapper function, add Ollama native API support with metrics normalization
- `config.yaml` — change host to `/api/chat`
- `ccya/server/routes.py` — healthz detects backend type
- `ccya/engine/ruling.py` — use wrapper
- `ccya/engine/extraction/utils.py` — use wrapper
- `ccya/engine/seed.py` — use wrapper
- `ccya/engine/world.py` — use wrapper
- `ccya/engine/generate_pack.py` — use wrapper
- `ccya/engine/thread_sanitizer.py` — use wrapper
- `ccya/engine/turn.py` — use wrapper (narrate + warmup)

### Rollback

If the native Ollama API path breaks anything, revert `config.yaml` host to `/v1` and restore the OpenAI SDK path. The dual-backend code in `llm_client.py` preserves the old behavior for non-`/api/chat` hosts.
