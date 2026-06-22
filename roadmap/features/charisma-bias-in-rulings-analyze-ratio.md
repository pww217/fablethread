---
title: "[Balancing] Charisma bias in rulings — analyze ratio"
status: scoping
urgency: 3
size: unknown
created: 2026-06-12
labels:
  - Improvement
  - Balancing
---

## Detail

Games feel overly biased towards charisma. Most turns involve talking, so charisma is used most frequently. Dex is second, then strength and wits. Need to analyze the ratio and balance.

## Scope

* Gather evidence: analyze skill usage ratios across recent sessions
* Check if ruling extractor over-weights social intent verbs
* Review if difficulty assignment favors social rolls
* Consider: difficulty assignment, ruling extraction, or prompt bias?
* Balance may require adjusting any of the above

## Files

* `ccya/engine/extraction.py` — ruling extraction (intent verb → skill mapping)
* `ccya/rules.py` — difficulty assignment
* `ccya/prompts/` — ruling extraction prompts
