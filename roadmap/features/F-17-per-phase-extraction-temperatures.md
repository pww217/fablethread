---
title: "Per-phase extraction temperatures"
status: idea
urgency: 3
size: small
created: 2026-06-25
ticket_id: F-17
labels:
  - engine
  - extraction
  - config
---

## Problem

All three extraction phases (scene, state, storytell) share a single `extract_temperature` (0.4). Different phases have different needs — scene extraction benefits from lower temperature for consistency, while storytell may need more creativity.

## Current state

- `EngineConfig.extract_temperature` — single float, default 0.4
- `_call_stream()` in `ccya/engine/extraction/utils.py:230` hardcodes `config.extract_temperature` for all phases
- Called from `pipeline.py` for scene (line 86), state (line 143), and storytell (lines 220, 242)

## Proposed change

- Split `extract_temperature` into per-phase knobs:
  - `extract_scene_temperature` (default: keep 0.4 for parity)
  - `extract_state_temperature` (default: keep 0.4 for parity)
  - `extract_storytell_temperature` (default: keep 0.4 for parity)
- Update `_call_stream()` to accept a `temperature` parameter instead of reading from config
- Update `build_engine_config()` to map from new config keys
- Update eval/play configs to support the new keys

## Files to touch

- `ccya/engine/config.py` — new fields + `build_engine_config` mapping
- `ccya/engine/extraction/utils.py` — `_call_stream` accepts temperature param
- `ccya/engine/extraction/pipeline.py` — pass per-phase temperature to `_call_stream`
- `ccya/ev/eval.py` + `ccya/ev/play.py` — support new config keys in `setdefault` blocks

## Validation

- `make check` passes
- `ev.py play` runs with default temps (parity)
- `ev.py play --temp N` still works (override applies to all)
- Config with new keys loads without errors
