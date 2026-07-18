---
title: "prompt_eval uses EngineConfig() defaults; extraction hangs on first turn after seed gen"
status: done
urgency: 1
size: medium
created: 2026-07-17
ticket_id: B-49
labels:
  - llm-client
  - fallback
  - eval
  - turn-pipeline
---

## Problem

Two related issues prevent eval runs and first-turn execution when the primary LLM is unreachable:

### 1. prompt_eval.py and ev.py use EngineConfig() with fallback_host=""

`prompt_eval.py:168` and `cmd_prompt_eval_call:250` construct `EngineConfig()` directly instead of using `build_engine_config(load_config("config.yaml"))`. This means:
- `fallback_host = ""` (empty string) — the fallback LLM at `http://127.0.0.1:8000/v1` is never reached
- `model = ""` (empty string) — no model name sent to the LLM

**Evidence:** Running `prompt-eval seed noir-1930s` fails after 230s trying the primary (which hangs at TCP level), then falls back to an empty string instead of the configured `http://127.0.0.1:8000/v1`.

**Correct behavior:** The server route handler correctly uses `build_engine_config(load_config("config.yaml"))`, so server-side turns work with the proper fallback. Only `prompt_eval` and `ev.py` are broken.

**Fix:** Replace `EngineConfig()` with `build_engine_config(load_config("config.yaml"))` in both locations. ✅ FIXED

### 2. First-turn scene extraction hangs indefinitely after seed generation succeeds

When seed generation completes successfully (via fallback, ~254s), the first turn's scene extraction pipeline never yields any events or emits a `chat:` log. `events.jsonl` is empty, `chronicle.md` is empty.

**Root cause analysis:**

The health check system (`_check_health`) uses a 30-second per-host cache (introduced in E-14, commit `323cd26b`). The health probe uses `httpx.Timeout(connect=2.0, read=3.0)` and times out quickly (2-3s) when the primary is unreachable. However:

- The primary LLM at `10.75.100.51:1234` is unreachable at TCP level — SYN packet hangs indefinitely (OS-level timeout, ~457s observed in logs)
- The health probe at `/health` returns HTTP 200 (the server responds), but the inference endpoint (`/chat/completions`) hangs because the model isn't loaded or is unresponsive
- `_check_health` returns True (health probe succeeds), so `_chat_with_fallback` tries the primary first
- OpenAI SDK `chat.completions.create()` uses a total timeout (120s default) but does NOT enforce a connect timeout — the socket hangs indefinitely because the SDK timeout only applies to data transfer, not initial socket connection
- The extraction pipeline never yields because the LLM call blocks indefinitely

**Fix:** ✅ FIXED

1. Added health check before first attempt to primary in `_chat_with_fallback` — if health check fails, skip primary and use fallback immediately
2. Pass `httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=10.0)` to SDK instead of `timeout=timeout` — enforces 5s connect timeout so socket hangs don't last indefinitely

## Validation

3-turn eval completed successfully (2026-07-17 20:04-20:07):
- All 3 turns completed with ruling, narrate, extraction, and complete phases
- Health check correctly detected primary unhealthy and fell back immediately
- No hangs, no timeouts
- Events written to `evals/runs/2026-07-17_0.31.0-139-gcefa05af_cefa05af/2005_noir-1930s_3t/events.jsonl`

## Files affected

- `ccya/llm_client.py` — `_chat_with_fallback()` (added health check before first attempt), `_chat_openai_compat()` (added connect timeout), `_try_host_stream()` (added connect timeout)
- `ccya/ev/prompt_eval.py` — replaced `EngineConfig()` with `build_engine_config(load_config())` at lines 169-170 and 252-253

## Related

- B-47: LLM fallback not retrying connection errors (partially related — different aspect of fallback)
- B-21: Turn never starts after seed gen (resolved — was SSE lifecycle issue, different root cause)
- E-14: Introduced `_check_health` with 30s per-host cache (see commit `323cd26b`)
