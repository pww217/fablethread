---
title: Remove llama-swap references and shut it down
status: done
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

## References removed

- `scripts/infra/llama-swap.sh` — deleted
- `Makefile` — removed llama-swap target and dependencies
- `README.md` — updated setup section to reflect LMStudio as primary, removed port 8080 references
- `ccya/llm_client.py` — updated docstrings to remove llama-swap mentions
- `roadmap/evals/E-13-narrative-pacing-convergence.md` — updated fallback description

## Definition of done

- All llama-swap references removed from code/docs ✅
- llama-swap process killed (already done — `pkill llama-swap`) ✅
- Config simplified to single LLM host per environment ✅
