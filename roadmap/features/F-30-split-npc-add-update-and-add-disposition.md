---
title: "Split NPC Add/Update ops and add disposition field"
status: testing
urgency: 2
size: medium
created: 2026-07-05
ticket_id: F-30
labels:
  - engine
  - npc
design: docs/design/F-30-split-npc-add-update-and-disposition.md
plan: plans/F-30-split-npc-add-update-and-disposition.md
---

## Problem

`CompendiumNpcUpdate` carries both write-once fields (motivation, fear, leverage, tie, party) and updatable fields (bio, presence, position, departed_reason). The single model forces the engine to track which fields are write-once via implicit logic in `apply_npc_scene_management()`. This is fragile and hard to reason about.

Additionally, the personality system (archetype-based, auto-assigned from motivation/fear) was removed in I-24 but there's value in having 2-3 freeform adjectives describing an NPC's speech style and demeanor — think "Elderly, gravelly voice, hunches forward" — to give the narrator more texture.

## Design

Split `CompendiumNpcUpdate` into two models:

### `CompendiumNpcAdd` (seed + first appearance)

All write-once fields. Used by:
- **Seed**: `seed_state.compendium.npcs` — LLM assigns disposition, motivation, fear, leverage, tie, party at world creation
- **Scene extraction (first appearance only)**: LLM assigns disposition + psychological fields when creating a new NPC

Fields:
- `id` (required)
- `name`, `title`, `bio` (write-once but updatable via Update — bio is the exception)
- `disposition` (new — freeform text, 2-3 adjectives describing speech style and demeanor)
- `motivation`, `fear`, `leverage`, `tie` (write-once psychological drivers)
- `party` (write-once — auto-cleared on departed, otherwise player-managed via `POST /api/npc/{id}/toggle-party`)

### `CompendiumNpcUpdate` (subsequent scenes)

Only updatable fields. Used by every scene extraction after first appearance.

Fields:
- `id` (required — identifies which NPC to update)
- `bio` (updatable — LLM refines understanding of the NPC)
- `presence` (updatable — present/nearby/known/departed)
- `position` (updatable — spatial position in current scene)
- `departed_reason` (updatable — combined label + prose)

### Engine changes

1. **`apply_npc_scene_management()`** — takes both `CompendiumNpcAdd` and `CompendiumNpcUpdate` lists. Add entries create new NPCs (write-once everything). Update entries mutate existing NPCs (only updatable fields).

2. **Unnamed guard** — `disposition`, `motivation`, `fear`, `leverage`, `tie` are stripped if `_is_unnamed(comp_upd.name)` returns true (same guard that already exists for psychological fields).

3. **`build_npc_roster()`** — includes `disposition` in output dicts (alongside motivation, fear, leverage, tie).

4. **`_npc_roster.j2`** — renders `disposition` in the NPC roster line (after bio, before motivation/fear/leverage).

5. **`_is_named()`** — shared between `npc_roster.py` and `state/npcs.py` (currently duplicated — this is an opportunity to consolidate).

### Prompt changes

- **Scene extraction system prompt** — instruct LLM to assign `disposition` (2-3 adjectives, speech style + posture/demeanor) when creating new NPCs. Same guard: unnamed NPCs get no disposition.
- **Seed prompt** — instruct LLM to assign `disposition` for named NPCs in the seed compendium.

### State model

Add `disposition: str | None = None` to `NPCEntry` in `ccya/models/state.py`.

## Files to touch

- `ccya/models/extraction.py` — split `CompendiumNpcUpdate` into Add/Update models
- `ccya/models/state.py` — add `disposition` to `NPCEntry`
- `ccya/state/npcs.py` — rewrite `apply_npc_scene_management()` for dual-write semantics, move `_is_named` to shared location
- `ccya/engine/npc_roster.py` — include `disposition` in output, remove duplicated `_is_named`
- `ccya/prompts/sections/_npc_roster.j2` — render disposition
- `ccya/prompts/sections/extract_scene_system.j2` — add disposition guidance
- `ccya/prompts/seed.j2` (or equivalent) — add disposition guidance for seed NPCs
- `ccya/state/delta_builder.py` — route Add vs Update through `apply_npc_scene_management()`
- `ccya/ev/prompt_context.py` — include disposition in eval NPC roster
- `docs/architecture/state-models.md` — document new models and field routing
- `docs/repomap.md` — update extraction routing section

## Done when

- `CompendiumNpcAdd` and `CompendiumNpcUpdate` exist with correct field sets
- `apply_npc_scene_management()` handles both models with write-once semantics
- `disposition` field exists on `NPCEntry`, rendered in `_npc_roster.j2`, guided in extraction/seed prompts
- Unnamed guard strips disposition (and other write-once fields) from unnamed NPCs
- `make check` passes (lint + typecheck)
- Docs updated (state-models.md, repomap.md)
