---
title: "[Conditions] TTL design question"
status: canceled
created: 2026-06-14
labels:
  - Improvement
  - Extraction
---

## Detail

Force narrative resolution vs long TTLs as insurance? Currently conditions use TTL to auto-expire, but this may prevent the narrator from resolving conditions narratively.

## Motivation

TTL-based expiration is a safety net, but it may prevent the narrator from engaging with conditions meaningfully. Need to decide whether to favor narrative resolution or automated expiration.

## Scope

* **In scope:** Evaluate TTL design, determine preferred approach
* **Out of scope:** Implementation changes

## Systems Affected

* — condition model
* — condition extraction
* — condition prompts
