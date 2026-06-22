---
title: "[World] World state shows bloat, not active constraints"
status: scoping
urgency: 3
size: unknown
created: 2026-06-12
labels:
  - Improvement
  - World Building
---

## Detail

World state in the right sidebar shows background context bloat instead of true constraints, lore, and facts directly relevant to the current scene.

## Scope

* Redefine what goes into world state: only active constraints, ongoing conflicts, relevant lore
* Remove background context that doesn't affect current decisions
* Add engine guidance in prompts to extract only relevant world state facts
* Consider splitting into "active constraints" vs "background lore"

## Files

* `ccya/models.py` — scene.world_state field
* `ccya/prompts/` — scene extraction prompts
* `ccya/templates/_state_right.html` — world state rendering
* `ccya/engine/extraction.py` — scene extraction logic
