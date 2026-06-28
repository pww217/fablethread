---
title: "[NPC] Always state quantity on plural NPC notes"
status: scoping
urgency: 3
size: small
created: 2026-06-12
ticket_id: I-1
labels:
  - Improvement
  - Extraction
---

## Detail

NPC notes in both scene panel and compendium sidebar don't consistently show quantities when multiple NPCs are referenced.

## Scope

* Scene panel NPC inline notes: always show count for plural NPCs (e.g., "3 guards" not just "guards")
* Compendium NPC notes: same quantity display
* Ensure this applies to all NPC note rendering paths

## Files

* `ccya/templates/_state_left.html` — scene panel NPC rendering
* `ccya/templates/_state_left.html` — compendium NPC rendering
* `ccya/server/panels.py` — NPC data preparation for templates

## Validation

Confirmed bug in codebase:

1. **Data model missing** `count` **field** — `CompendiumNpcUpdate` in `ccya/models.py:244` has no `count`/`qty`/`quantity` field. The extraction prompt (`extract_scene_system.j2:77`) requires group NPCs to state exact count, but there's no structured field to store it.
2. **Templates don't display quantities** — Both scene panel rendering (`_state_left.html:12-37`) and compendium rendering (`_state_left.html:143-165`) show NPC names without any count prefix for plural groups.
3. **Dead CSS** — `.npc-count-ctrl` and `.npc-count-val` exist in `app.src.css:2346-2359` but are never used in any template, suggesting this was planned but never implemented.
4. **No fallback parsing** — The templates don't attempt to parse counts from free-text `name` or `notes` fields, so even if the LLM emits "3 guards" in the name, it renders as-is without structured count display.
