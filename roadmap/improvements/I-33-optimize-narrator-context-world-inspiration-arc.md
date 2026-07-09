---
title: "Optimize narrator context — what each narrator receives from world, inspiration, and arc"
status: idea
urgency: 3
size: medium
created: 2026-07-09
ticket_id: I-33
labels:
  - engine
  - prompts
  - worldbuilding
---

## Problem

Two narrator systems have asymmetric, incomplete context from the world pack, leading to under-informed narration:

| Context | Seed narrator (opening) | Regular narrator (per-turn) |
|---------|------------------------|----------------------------|
| `world_facts` (scenario canon) | NOT received | Received via world_state (baseline facts injected at seed time, but LLM-added facts overwrite over time) |
| `narrator_rules` (genre tone) | NOT received | Received |
| `world_rules` (physical laws) | Received (via setting_info.universe_rules) | Received |
| `inspiration` blocks (pc, npcs, inventory creative direction) | Received (via setting_info.creative_direction) | NOT received |
| `factions` | NOT received | Received |
| `pool_selection` (archetypes, bundles) | Received | NOT received |
| `world_state` (evolving facts) | NOT received (explicitly excluded, seed.py:451) | Received |
| Arc/threads for motivation anchoring | Arc objective received, but NOT arc threads or urgency | Arc threads received, but NOT inspiration blocks for anchoring |

## Analysis

### Seed narrator gaps

The opening narrator generates ~700 words of prose anchoring the player in the world. It receives the arc objective but NOT the arc threads, urgency, or progression. This means the opening narration can't reference the character's active motivations or the pressure driving the campaign — it generates arc awareness from the objective alone, which is thin.

It also misses world_facts, narrator_rules, and factions. The opening narrator relies on creative_direction blocks (inspiration) for PC/NPC/inventory guidance, but has no world canon anchoring. The result is opening prose that can feel generic — it knows the character but not the world.

### Regular narrator gaps

The per-turn narrator receives narrator_rules, world_rules, factions, world_state, arc threads, and pacing context. This is the richer context set. But it misses inspiration blocks (pc, npcs, inventory creative direction) and pool selection data.

The user's concern is that the narrator's choices (actions, beat generation, narration direction) should be grounded in the player's motivation — which is closest to the arc. The arc is received, but the narrator doesn't have the inspiration blocks that describe what kind of PC, NPCs, or inventory the world expects. This creates a disconnect between the world's creative direction and the narrator's per-turn decisions.

### World_state evolution problem

World_state starts with baseline facts (injected from world_facts at seed time, seed.py:360-374). But over turns, LLM-added world_state facts can overwrite or dilute the baseline canon. The regular narrator receives world_state, but the quality of anchoring degrades as the game progresses.

## Proposed direction (to be refined in plan)

### Seed narrator should receive:
- **world_facts** — anchoring canon for the opening world context
- **narrator_rules** — tone consistency from the first word
- **factions** — world power structure awareness
- **Arc threads (not just objective)** — the opening should reference active motivations, not just the end goal

### Regular narrator should receive:
- **Inspiration blocks (pc, npcs, inventory)** — anchoring the narrator's creative direction to the world's expectations, especially for beat generation and action anchoring
- **World_facts (explicit, not just via world_state)** — ensure baseline canon is always visible, not just what survived into world_state
- **Arc urgency signals** — the narrator should know which threads are URGENT vs BACKGROUND, not just their existence

### World_state anchoring:
- Baseline facts should be preserved in world_state permanently (they already have `permanent=True`, but need to be visible in narrator context every turn, not just in world_state which can be overwritten)
- Consider injecting world_facts directly into narrator context (like narrator_rules) in addition to world_state, so the narrator always has the baseline canon visible

### Action anchoring to arc:
- The user's concern about actions being "grounded, not hallucinated, tied to pursuing threads and arcs" applies to both the opening actions (4 choices) and the beat generation (World step)
- Opening actions should reference arc urgency, not just arc objective
- Beat generation (World step) should have inspiration blocks visible so beat candidates reference the world's creative direction, not just mechanical thread states

## Files to touch

- `ccya/engine/seed.py` — _build_narrate_seed_messages() to add world_facts, narrator_rules, factions, arc threads
- `ccya/prompts/narrate_seed_system.j2` — sections for world_facts, narrator_rules, factions, arc threads
- `ccya/engine/narrate.py` — _narrate_messages() to add inspiration blocks, world_facts
- `ccya/prompts/narrate_user.j2` — sections for inspiration blocks, world_facts anchoring
- `ccya/prompts/sections/_world_state.j2` — consider separating baseline facts from LLM-added facts for anchoring
- `ccya/engine/turn.py` — _run_turn() to pass new context params

## Design reference

- `docs/architecture/step1-narrate.md` — narrator prompt architecture
- `docs/architecture/step2d-world.md` — beat generation (World step)
- `docs/architecture/step0-ruling.md` — ruling context
- `docs/architecture/state-models.md` — world_state, arc, threads models
- `ccya/pack.py` — ScenarioBrief, Inspiration, world_facts, narrator_rules, world_rules, factions
- `ccya/engine/seed.py:440-505` — _build_narrate_seed_messages() context building
- `ccya/engine/narrate.py:160-245` — _run_narrate() context building
