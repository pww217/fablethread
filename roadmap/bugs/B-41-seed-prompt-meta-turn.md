---
title: "prepare_seed prompt includes meta.turn in example — LLM may set it instead of engine"
status: testing
urgency: 3
size: small
created: 2026-07-07
ticket_id: B-41
labels:
  - prompts
  - seed
---

# B-41: prepare_seed prompt includes meta.turn in example

## Symptom

The `prepare_seed` system prompt example includes `"turn": 0` in the `meta` section. The LLM is outputting `"turn": 1` in the seed state's meta, which shifts all subsequent turn numbers.

## Evidence

- `prepare_seed_system.j2:35` shows: `"meta": {"turn": 0, "model": "mlx-community/Qwen3-32B", ...}`
- `WorldState.meta.turn` defaults to 0
- `turn_no = state.meta.turn + 1` in `turn.py:122` — the engine calculates turn numbers from the seed state's meta.turn
- If the LLM sets `meta.turn: 1`, the first player turn starts at 2 instead of 1

## Fix

**Already fixed:** Removed `"turn": 0` from the seed prompt example in `prepare_seed_system.j2`. The engine defaults `meta.turn` to 0 — the LLM should not set it.

## Impact

- Seed state `meta.turn` may be set by LLM to non-zero values
- First player turn starts at `meta.turn + 1` instead of 1
- All downstream turn numbers are offset by the seed value
