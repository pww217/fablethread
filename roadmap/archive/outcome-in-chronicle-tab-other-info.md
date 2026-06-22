---
title: "[UI] Outcome in chronicle tab + other info"
status: done
created: 2026-06-12
labels:
  - Feature
  - UI
---

## Detail

Chronicle tab shows turn events but lacks outcome summaries and arc resolution info.

## Scope

* Add outcome summaries to chronicle entries
* Surface arc resolution info in chronicle
* Add other relevant game state transitions (location changes, faction shifts, etc.)

## Files

* `ccya/state/chronicle.py` — chronicle.md and events.jsonl writing
* `ccya/templates/` — chronicle rendering templates
* `ccya/server/panels.py` — chronicle loading
