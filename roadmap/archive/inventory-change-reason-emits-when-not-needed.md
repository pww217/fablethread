---
title: "[State] Inventory change reason emits when not needed, reasons wrong"
status: done
urgency: 4
size: small
created: 2026-06-12
labels:
  - Bug
  - Extraction
---

## Detail

Inventory change reason emits when not needed and sometimes gives wrong reasons. Malfunctioning.

## Scope

* Fix inventory change reason to only emit when there's an actual change
* Improve reason accuracy — ensure it reflects the actual cause of the change
* Add engine guidance in prompts for clearer inventory change reporting
* Consider if this is an extraction issue or a rendering issue

## Files

* `ccya/engine/extraction.py` — state extraction (inventory delta)
* `ccya/prompts/` — state extraction prompts
* `ccya/state/inventory.py` — inventory normalization and resolution
* `ccya/templates/` — inventory change rendering
