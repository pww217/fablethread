---
title: "prepare_seed: LLM outputs malformed JSON keys with colon inside opening quote"
status: testing
urgency: 2
size: small
created: 2026-07-05
ticket_id: B-32
labels: [seed, prompt, reliability]
---

## Symptom

"prepare_seed failed (attempt 1): No JSON found in prepare_seed response" errors. The `_find_json()` regex can't handle this pattern.

## Root cause

YAML-style `key: value` patterns in the prompt prose (in backticks) are being copied by the LLM into its JSON output as `"key: value"` (colon inside the quote).

## Fix

Removed all YAML-style `key: value` patterns from `prepare_seed_system.j2` and `prepare_seed_user.j2`. Converted them to JSON-style `"key": "value"` or removed trailing colons.

### Changes

- `ccya/prompts/prepare_seed_system.j2` — removed YAML patterns from prose
- `ccya/prompts/prepare_seed_user.j2` — added clarification to name_seed line

## Verification

Run a multi-game eval and check `saves/prepare_seed_failures/` for new files. Should be zero.
