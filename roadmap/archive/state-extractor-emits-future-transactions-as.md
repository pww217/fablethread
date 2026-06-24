---
title: "[State] State extractor emits future transactions as present"
status: done
urgency: 3
size: small
created: 2026-06-12
labels:
  - Bug
  - Extraction
---

## Detail

State extractor emits inventory changes based on future transactions rather than present state. It predicts what will happen instead of reporting what has happened.

## Example

Player trades something now for something that's going to happen later. The extractor treats this as if the transaction already occurred, which breaks the sense of time in the game.

## Scope

* Fix state extractor to only report present-tense inventory changes
* Defer future transactions until they actually occur
* Add engine guidance in prompts to clarify present vs future tense
* Consider adding a "pending" state for future transactions

## Files

* `ccya/engine/extraction.py` — state extraction logic
* `ccya/prompts/` — state extraction prompts
* `ccya/state/delta_builder.py` — delta application logic
