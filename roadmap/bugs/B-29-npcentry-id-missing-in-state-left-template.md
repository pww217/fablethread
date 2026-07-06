---
title: "'NPCEntry' object has no attribute 'id' in _state_left.html"
status: done
completed: 2026-07-06
urgency: 2
size: small
created: 2026-07-04
ticket_id: B-29
labels: [server, template, regression]
---

## Summary

`_state_left.html` iterated over `state.compendium.npcs` (raw `NPCEntry` objects) and accessed `.id` — but `NPCEntry` has no `id` field. The ID is the dict key.

## Impact

500 server error on `/panels/state-left`, `/panels/state`, and `/` (main page) whenever compendium has NPCs.

## Root cause

`NPCEntry` (state.py:77) has no `id` field. NPCs are keyed by ID in the compendium dict. The template iterated over `comp.items()` but then used `npc.id` instead of the dict key.

## Fix

Changed scene and nearby NPC sections to iterate with `{% for _k, npc in comp.items() %}` and use `_k` (the dict key) instead of `npc.id`.

## Files changed

- `ccya/templates/_state_left.html` — lines 12-20, 44-52 (use dict key instead of `npc.id`)
