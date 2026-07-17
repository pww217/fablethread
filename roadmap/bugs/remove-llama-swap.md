---
title: Remove llama-swap references and shut it down
status: validated
urgency: 2
size: small
created: 2026-07-16
ticket_id: B-48
labels:
  - cleanup
  - infrastructure
---

## Problem

llama-swap is no longer used in the CCYA project. Port 8000 serves the LLM directly. Port 1234 serves the remote LLM. llama-swap (port 8080) is dead weight.

## References to remove

- `docs/architecture/OVERVIEW.md`
- `docs/releases/0.2.0.md`
- `docs/releases/0.3.0.md`
- `AGENTS.md`
- `README.md`
- `ccya/llm_client.py`
- `roadmap/evals/E-13-narrative-pacing-convergence.md`
- `plans/completed/completed/eval-system/sampling-params.md`
- `plans/completed/completed/prompt/01-frequency-penalty.md`
- `plans/completed/eval-system/sampling-params.md`
- `plans/completed/prompt/01-frequency-penalty.md`

## Definition of done

- All llama-swap references removed from code/docs
- llama-swap process killed (already done — `pkill llama-swap`)
- Config simplified to single LLM host per environment
