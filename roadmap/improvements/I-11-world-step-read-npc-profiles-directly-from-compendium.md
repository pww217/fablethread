---
title: "World step: read NPC profiles directly from compendium, remove candidate_npcs from scene extractor"
status: done
urgency: 1
size: large
created: 2026-06-28
ticket_id: I-11
labels:
  - engine
  - npc
  - world
  - beats
  - pacing
plan: plans/completed/I-11-world-step-compendium-plan.md
commit: 6bfea4f
---

## Problem

The scene extractor produces `candidate_npcs` — a list of per-NPC psychological hints (`[{id, type, effect}]`) — which the World step then uses to generate beat candidates. This design has three fundamental flaws:

1. **~20% failure rate.** The scene extractor is an LLM step that fails to produce `candidate_npcs` on ~20% of turns. When it fails, World has no psychological material and falls back to environmental beats.

2. **Redundant data.** The psychological fields (motivation, fear, leverage, bond) already exist in `state["compendium"]["npcs"]`. The scene extractor re-derives them via LLM for no reason — the data is already structured and durable.

3. **Weak blending.** The current prompt tells World to "combine 1-2 psychological hints" from a flat list of `(id, type, effect)` tuples. The LLM treats them independently rather than creating cross-NPC dramatic tension or single-NPC depth.

## Target State

World step reads NPC profiles directly from the compendium via `build_npc_roster()`, filtering for `presence` in `["present", "nearby"]`. Each NPC's full psychological profile (motivation, fear, leverage, bond) is rendered grouped by NPC ID. World generates beats by:

- **Cross-NPC conflict** — putting NPC A's motivation against NPC B's fear
- **Single-NPC depth** — exercising one NPC's full profile simultaneously
- **Optional threading** — threads provide context for urgency but beats don't need to anchor to them

Output schema adds `npcs` field: `[{type, effect, npcs: [id, ...]}]`.

Candidate_npcs is removed from the scene extractor output, the extraction pipeline, and all downstream consumers.

## Decisions

### D1: Use build_npc_roster() for World input

**Final.** World calls `build_npc_roster(comp)` then filters `["present", "nearby"]` in Python. Avoids duplicating presence filtering, sorting, and scoring logic from `npc_roster.py`.

### D2: Both cross-NPC and single-NPC blending

**Final.** World is instructed to create beats by either putting NPC A's motivation against NPC B's fear (drama through interaction) OR taking one NPC's full profile and exercising all three simultaneously.

### D3: Optional threading

**Final.** NPC-driven beats are primary; threads provide context for which beats feel urgent. Beats don't need to anchor to threads.

### D4: Add `npcs` field to beat output

**Final.** Each beat candidate includes `npcs: [id, ...]` listing which NPCs drive the beat. Useful for ruling awareness and future tracking.

### D5: Keep 2-3 candidates

**Final.** Same candidate count as before — the change is input quality (full profiles) not quantity.

## What Changes

### Engine

- **`ccya/engine/world.py`** — Remove `candidate_npcs` extraction from `scene_result`. Call `build_npc_roster()` to get full NPC profiles for present/nearby NPCs. Pass to prompt.
- **`ccya/engine/world.py`** — Filter candidates by `allowed_beat_types` post-hoc (also part of E-2 pacing fixes).
- **`ccya/engine/ruling.py`** — Derive `allowed_beat_types` via `derive_allowed_beat_types()` and pass to ruling prompt.
- **`ccya/engine/extraction/context.py`** — Remove `candidate_npcs` from `_ExtractionContext` dataclass.
- **`ccya/engine/extraction/pipeline.py`** — Remove `candidate_npcs` from pipeline context building.
- **`ccya/models/extraction.py`** — Remove `candidate_npcs` from `SceneExtractResult`.

### Prompts

- **`ccya/prompts/extract_scene_system.j2`** — Remove `candidate_npcs` output schema, beat candidate selection section, and all guidance about selecting/describing candidates.
- **`ccya/prompts/world_system.j2`** — Update blending instructions for cross-NPC conflict and single-NPC depth. Update action rule to reference full NPC profiles.
- **`ccya/prompts/world_user.j2`** — Replace flat `candidate_npcs` list with grouped NPC profiles (by NPC ID, showing all psychological fields).
- **`ccya/prompts/ruling_user.j2`** — Add `scene_phase` and `allowed_beat_types` rendering.

### Server/Tools

- **`ccya/server/tv.py`** — Remove `candidate_npcs` display from turn viewer.
- **`ccya/ev/state_tools.py`** — Remove `candidate_npcs` from state inspection output.
- **`ccya/ev/prompt_context.py`** — Remove `candidate_npcs` from eval prompt context.

### Docs

- **`docs/architecture/`** — Update pipeline docs (step2a-scene.md, step2d-world.md) to reflect new input source.
- **`docs/repomap.md`** — Update module boundaries and data shape descriptions.

## Impact Summary

| Component | Changes |
|---|---|
| `ccya/engine/world.py` | Read from compendium via build_npc_roster(), filter by presence, pass to prompt |
| `ccya/engine/ruling.py` | Derive allowed_beat_types, pass to ruling prompt |
| `ccya/engine/extraction/context.py` | Remove candidate_npcs from _ExtractionContext |
| `ccya/engine/extraction/pipeline.py` | Remove candidate_npcs from pipeline |
| `ccya/models/extraction.py` | Remove candidate_npcs from SceneExtractResult |
| `ccya/prompts/extract_scene_system.j2` | Remove candidate_npcs output schema and guidance |
| `ccya/prompts/world_system.j2` | Update blending instructions |
| `ccya/prompts/world_user.j2` | Group NPC profiles by ID |
| `ccya/prompts/ruling_user.j2` | Add phase + allowed_beat_types |
| `ccya/server/tv.py` | Remove candidate_npcs display |
| `ccya/ev/state_tools.py` | Remove candidate_npcs from inspection |
| `ccya/ev/prompt_context.py` | Remove candidate_npcs from eval context |
| Docs | Update pipeline docs and repomap |
