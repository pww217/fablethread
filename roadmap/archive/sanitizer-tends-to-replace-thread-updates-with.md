---
title: "[Storytell] Sanitizer tends to replace thread updates with exact text - instruct not to duplicate"
status: done
created: 2026-06-14
labels:
  - Improvement
  - World Building
---

## Detail

Sanitizer tends to replace thread updates with exact text, duplicating content that already exists in the thread. This creates redundant information and makes threads harder to read.

## How to Replicate

1. Have a thread with existing update text
2. Advance through turns where the thread receives new updates
3. Observe that the sanitizer replaces the existing text with new text that duplicates parts of the original

## Evidence

* Sanitizer logic in `ccya/engine/thread_sanitizer.py` replaces thread text entirely rather than appending or merging
* Thread updates should accumulate or summarize, not replace existing content verbatim
