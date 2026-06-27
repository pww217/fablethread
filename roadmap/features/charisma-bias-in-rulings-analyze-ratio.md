---
title: "[Balancing] Charisma bias in rulings — analyze ratio"
status: testing
urgency: 3
size: small
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

## Resolution

Analyzed 50 runs (470 skill checks) across evals. Found dexterity at 49%, strength 23%, charisma 20%, wits 9%. Root cause: skill definitions in ruling prompt were too narrow — wits had no guidance for observation/analysis/search actions, dexterity had vague "fine motor" catch-all. Fixed by rewriting the 4 skill definitions in `ruling_system.j2` to be more explicit and balanced. Also simplified intent_verb guidance to remove false precision (verb only used as decorative prefix on setback/partial directive text).
