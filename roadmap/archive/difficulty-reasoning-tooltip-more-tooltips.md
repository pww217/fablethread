---
title: "Difficulty reasoning tooltip + more tooltips throughout"
status: done
created: 2026-06-12
labels:
  - Feature
  - UI
---

## Detail

Surface "why chose difficulty" in UI with tooltips. More tooltips in general across the UI to help players understand game mechanics.

## Scope

* Difficulty tooltip: show reasoning for difficulty assignment (e.g., "hard because NPC has armor")
* Stat tooltips: clarify what each stat is used for (already partially done)
* Condition tooltips: clarify TTL, effects, removal conditions
* Thread tooltips: show progress history, urgency reasoning
* Arc goal tooltip: show goal_context (already done, check if working)
* Location tooltip: show description, nearby locations, factions present
* Inventory tooltip: show acquisition method, condition, notes

## Files

* `ccya/templates/_state_left.html` — scene panel tooltips
* `ccya/templates/_state_right.html` — player panel tooltips
* `ccya/static/app.src.css` — tooltip styling
* `ccya/server/panels.py` — tooltip data preparation
* `ccya/engine/turn.py` — difficulty reasoning capture

## Related

* TICK-14: UI improvements - turn numbers and developer mode (Backlog, different scope)
