---
title: "[NPC] Character highlighting/state differentiator in scene"
status: done
created: 2026-06-12
labels:
  - Improvement
  - Extraction
---

## Detail

Characters in the scene need visual differentiation in the UI — different shades of highlighting or other state indicators. General differentiator, not tied to specific state.

## Scope

* Add visual state indicator to characters in scene panel and compendium
* Options: different highlight shades, badges, icons, or other visual cues
* Consider what state items to surface (presence, allegiance, condition, motivation, etc.)
* Keep it subtle — not overwhelming

## Files

* `ccya/templates/_state_left.html` — scene panel NPC rendering
* `ccya/templates/_state_left.html` — compendium NPC rendering
* `ccya/static/app.src.css` — new styling classes
