---
title: "[Infra] OMLX provider"
status: done
urgency: 4
size: large
created: 2026-06-14
ticket_id: F-13
labels:
  - Improvement
  - Tooling
---

<!-- report: docs/olmx-report.md (2026-07-10) -->

## Detail

Additional model backend support. Currently limited to a single provider; need support for additional model backends.

## Motivation

Different games may need different model backends for cost, performance, or quality reasons. Supporting multiple providers would improve flexibility.

## oMLX vs mlx-lm server — feature comparison

Installed and tested oMLX 0.5.0 on M4 Max (128GB) at `localhost:8000`. Key advantages over the existing `mlx-lm` backend:

### 1. SSD KV cache persistence (biggest win)
- **oMLX:** Persists KV cache blocks (256 tokens each) to `~/.omlx/cache/` for batched-engine models. Verified cache survives model eviction — reload with same prompt hits cache at ~0.45-0.51s vs ~0.97s cold load.
- **mlx-lm:** No KV cache persistence. Every request cold-loads the full KV state.
- **Impact:** ~2x speedup on repeated prompts (game replays, testing, eval runs). Cache grows with unique prompts (~7MB per 256-token block).

### 2. Native model management
- **oMLX:** Auto-discovers models from HF cache, LRU eviction, admin dashboard for pinning/unloading models, built-in benchmark tool, HF model search/download.
- **mlx-lm:** Manual model loading/unloading. No dashboard. No model discovery.
- **Impact:** Easier model switching during dev. Pin frequently-used models to prevent eviction.

### 3. Memory management
- **oMLX:** Tiered memory guard (balanced mode), configurable ceiling, SSD tiered cache, reactive eviction when ceiling exceeded.
- **mlx-lm:** No built-in memory management. Requires manual `mlx-lm serve --max-num-tokens`.
- **Impact:** Safer on constrained hardware. Auto-evicts least-recently-used model when memory ceiling hit.

### 4. Multi-engine support
- **oMLX:** Supports batched, vlm, embeddings, audio engines from one install. 14 models discovered on this machine.
- **mlx-lm:** Only batched LLM engine. Separate tooling needed for embeddings/audio.
- **Impact:** Single install covers all use cases (LLM, vision, embeddings).

### 5. Admin dashboard
- **oMLX:** Web UI at `/admin` with real-time cache stats, model status, benchmark tool, built-in chat, SSD cache management, oQ quantization tools, HF model search/download.
- **mlx-lm:** No UI. Health check only via `/healthz`.

### 6. Anthropic-compatible API
- **oMLX:** Both OpenAI (`/v1/chat/completions`) and Anthropic (`/v1/messages`) endpoints.
- **mlx-lm:** OpenAI-compatible only.
- **Impact:** Enables Anthropic-style prompt formats if needed.

### Limitations to note
- **VLM cache not persisted:** KV cache only works for batched-engine (pure LLM) models. VLM models have non-sliceable cache layers.
- **Cache block threshold:** Only full 256-token blocks are cached. Partial blocks skipped. Prompts < 256 tokens may not fill a block.
- **Model name format:** Uses `--` separator (e.g., `mlx-community--Qwen3.6-35B-A3B-4bit`) derived from HF cache directory names.
- **Metal wired limit:** 56GB kernel cap on macOS. Can raise with `sudo sysctl iogpu.wired_limit_mb=59392`.
- **No grammar support:** `--with-grammar` not installed (structured output requires xgrammar).

## Scope

* **In scope:** OMLX provider integration, configuration options
* **Out of scope:** Other provider integrations

## Systems Affected

* — provider abstraction
* — provider configuration
* — provider-specific prompt adjustments

## Findings (2026-07-10)

Full setup and testing report: `docs/olmx-report.md`.

### Key findings

* oMLX 0.5.0 installed via Homebrew, running on `localhost:8000`
* 14 models discovered, including `gemma-4-26b-a4b-it-mxfp8` (6.2 GB) — compatible with ccya's current model
* OpenAI-compatible (`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) APIs verified working
* SSD KV cache persistence works for batched-engine (pure LLM) models only — gemma-4-26b uses `vlm` engine, **no cache persistence**
* Memory ceiling ~56 GB (Metal cap), LRU eviction confirmed
* Admin dashboard, benchmark tools, model download from HuggingFace all functional

### Impact on ccya

* **No new capabilities** — existing `localhost:8000` is already MLX on the same M4 Max hardware
* **No caching benefit** for gemma-4-26b (VLM engine doesn't persist KV cache)
* **Potential speedup** from oMLX's optimized server wrapper on cold inference
* **Local reliability** — independent of remote LMStudio on `10.75.100.51:1234`
* **No SSD caching advantage** for current workload — only batched-engine models get cache persistence
