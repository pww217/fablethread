---
title: "Rename bond → tie across the codebase"
status: idea
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-16
labels:
  - npc
  - terminology
---

## Problem

The NPC psychological field is called `bond` everywhere, but `tie` is a better word for what it represents (a durable personal connection between PC and NPC, or between two NPCs). It's shorter, less loaded, and more consistent with how the field is used in prompts.

## Scope

Rename `bond` → `tie` in all code, prompts, templates, and UI. Pack data flavor text stays as-is (it's prose, not field names).

## Inventory

### Python code (6 files, 16 occurrences)

| File | Line(s) | Context |
|------|---------|---------|
| `ccya/pack.py` | 43 | `bond: str | None = None` — field definition |
| `ccya/models/extraction.py` | 30 | `bond: str | None = None` — CompendiumNpcUpdate field |
| `ccya/state/npcs.py` | 89, 99, 100 | `bond` key in dict operations |
| `ccya/ev/prompt_context.py` | 44 | `"bond": ndata.get("bond", "")` |
| `ccya/server/routes.py` | 562, 586, 587 | Bond lookup/resolution logic |
| `ccya/engine/npc_roster.py` | 45, 67, 100 | Bond in roster building |

### Prompt templates (6 files, 16 occurrences)

| File | Line(s) | Context |
|------|---------|---------|
| `ccya/prompts/world_user.j2` | 9 | `n.bond` |
| `ccya/prompts/ruling_user.j2` | 12 | `n.bond` |
| `ccya/prompts/sections/_npc_roster.j2` | 7 | `n.bond` |
| `ccya/prompts/extract_scene_system.j2` | 21, 36, 69, 70 | Bond field guidance in instructions |
| `ccya/prompts/prepare_seed_user.j2` | 69 | `npc_bond` |
| `ccya/prompts/prepare_seed_system.j2` | 38, 86, 90, 91 | Bond in schema + guidance |

### UI (3 files, 9 occurrences)

| File | Line(s) | Context |
|------|---------|---------|
| `ccya/templates/_state_left.html` | 19, 53, 183 | `npc_bond` variable |
| `ccya/static/game-utils.js` | 794, 795, 803 | `bond` tooltip rendering |

### Architecture docs (3 files)

| File | Line(s) | Context |
|------|---------|---------|
| `docs/architecture/cross-module-contracts.md` | 52 | CompendiumEntry field list |
| `docs/architecture/step2a-scene.md` | 43 | Pipeline description |
| `docs/architecture/prompts-architecture.md` | 63 | CompendiumEntry field list |

### Roadmap tickets (10 files)

| File | Line(s) | Context |
|------|---------|---------|
| `roadmap/bugs/B-1-beat-generation-split-realization-audit.md` | 101, 212, 213 | References |
| `roadmap/bugs/B-24-extraction-reliability-null-fields.md` | 51 | Fix description |
| `roadmap/bugs/B-15-user-reported-npc-character-system-gaps.md` | 20, 28, 30 | Fix description |
| `roadmap/archive/npc-bonds-display-bug.md` | 14, 18, 20 | Bug title + body |
| `roadmap/improvements/I-6-pr-description-template.md` | 109 | PR description body |
| `roadmap/evals/E-5-pacing-fix-and-npc-extraction.md` | 84, 319 | Fix description |
| `roadmap/improvements/prompt-audit.md` | 123, 134, 227 | Audit notes |

### Plans (10 files)

| File | Lines | Context |
|------|-------|---------|
| `plans/completed/npc/npc-lifecycle-management.md` | 324 | Code snippet |
| `plans/completed/npc/npc-compendium-plan-01-model-cap-removal.md` | 12, 23, 178, 187, 189, 202, 218, 258, 259, 261, 262, 291, 293, 303, 309 | Plan body + code snippets |
| `plans/completed/npc/02-npc-compendium-hardening.md` | 13, 20, 42, 52, 99, 173 | Plan body + code snippets |
| `plans/completed/npc/npc-personality.md` | 439, 443, 519, 533, 564 | Plan body + code snippets |
| `plans/completed/npc/npc-personality-and-seed-relevancy.md` | 36, 37, 38, 75, 79, 97, 103, 171 | Plan body + schema |
| `plans/completed/npc/npc-bonds-and-scene-detail-pools.md` | 134, 143, 275 | Plan body |
| `plans/completed/gm-beats/beat-generation-split-plan.md` | 402 | Plan body |
| `plans/completed/gm-beats/gm-beat-overhaul.md` | 267, 271, 382 | Plan body + code snippets |
| `plans/completed/workflow-org/linear-reorganization.md` | 210 | Table |
| `plans/completed/seed-two-step-plan.md` | 174 | Plan body |

### Total: 39 files, ~60 occurrences

## Execution notes

- Field rename: `bond` → `tie` in all Python dicts, Pydantic models, Jinja templates, JS
- Variable names: `npc_bond` → `npc_tie`, `raw_bond` → `raw_tie`, `bond_lookup` → `tie_lookup`
- Prompt instructions: `bond` → `tie` in all guidance text
- Pack data: flavor text descriptions keep `bond` (it's prose, not field names)
- Docs: update architecture docs to reflect `tie` field name
- Plans: update completed plans for accuracy (they're historical records but should reflect current field names)
- Roadmap: update bug/improvement tickets for accuracy

## Done when

- All 6 Python files updated
- All 6 prompt templates updated
- All 3 UI files updated
- All 3 architecture docs updated
- `make check` passes
