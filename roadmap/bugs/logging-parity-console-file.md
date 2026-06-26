---
title: "Logging parity between file and console — hard to debug in real time"
status: new
urgency: 3
size: small
created: 2026-06-26
labels:
  - logging
  - developer-experience
---

## Problem

The file log (`logs/game.log`) and console (stdout) are at different levels by default:
- File: DEBUG (from `config.yaml`)
- Console: WARNING (hardcoded in `logging_setup.py:40`)

This means when you're watching the server run, you see almost nothing useful. The interesting stuff (world step, turn pipeline phases, LLM calls) is only in the file log. You have to know to `tail logs/game.log` and filter for specific trace IDs.

The console level is hardcoded, not configurable from `config.yaml`. The only way to change it is to set the `CCYA_LOG_LEVEL` env var, which isn't documented and isn't in the Makefile.

## What's needed

1. Console level should be configurable from `config.yaml` (same `logging.level` key, or a separate `console_level` key)
2. Default console level should be INFO (not WARNING) — INFO messages are the useful ones (turn completions, LLM call timings, phase transitions)
3. Consider a `--verbose` / `-v` flag on the CLI that sets console to DEBUG
4. Document the logging config somewhere visible (AGENTS.md or a `docs/logging.md`)

## Files

- `ccya/logging_setup.py` — console handler level is hardcoded at line 40
- `ccya/cli.py` — no `--verbose` flag
- `config.yaml` — `logging.level` exists but only affects file handler
