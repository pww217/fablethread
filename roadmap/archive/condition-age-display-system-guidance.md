---
title: "[Conditions] Condition age display + system guidance"
status: done
created: 2026-06-11
labels:
  - Improvement
  - Extraction
---

## Status

New — needs validation.

## Detail

Python auto-expires conditions when `turns_remaining` hits 0. Permanent conditions persist indefinitely. LLM has no visibility into condition age.

## Proposed Change

* Show condition age in prompts alongside existing TTL countdown
* Add system prompt guidance: "Consider conditions > 4 turns as requiring pruning soon unless narration demands they remain"
* Shift condition lifecycle management partially to LLM rather than Python silently deleting
* IDEAS.md marks this as "needs more thought"
