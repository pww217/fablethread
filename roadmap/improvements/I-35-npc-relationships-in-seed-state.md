---
title: "Add NPC relationships to seed state"
status: idea
urgency: 3
size: medium
created: 2026-07-09
ticket_id: I-35
labels:
  - seed
  - npcs
---

## Problem

The seed generates NPCs with relationships only to the PC, not to each other. This creates a star pattern (all NPCs orbit the PC) rather than a relationship triangle. Result: opening scenes default to "one friendly NPC, one oppositional NPC" — formulaic and static.

## Solution

Add a top-level `npc_relationships` field to the seed state. Same pattern as `threads` — a separate collection of pairs that reference NPCs by ID, rendered as context in the narrate prompt.

### Before / After

**Without NPC relationships (current):**

> *Seed generates two present NPCs — both only have `tie` fields describing their relationship to the PC. The narrator opens with: "Captain Voss stands at the map table, his eyes on you. Medic Kren is cleaning a tray of instruments in the corner, glancing up occasionally."*

Both NPCs exist in relation to the PC. They don't interact with each other. The scene is static — two faces, one player, no internal dynamics.

**With NPC relationships:**

> *Seed generates two present NPCs plus `npc_relationships: [{npc1: "captain_voss", npc2: "medic_kren", description: "Voss ordered Kren to triage the wounded first; Kren treated the officer's men before the captain himself, and Voss hasn't forgotten.}]. The narrator opens with: "Captain Voss is leaning over the map table when you walk in, but his attention is on Medic Kren, who is deliberately not looking at him. 'They'll hold, Hale,' the medic says, not raising his eyes from the instruments. Voss doesn't answer. He looks at you instead, and whatever he was holding back in front of Kren leaks through."*

The two present NPCs are already in tension. The PC walks into an existing moment, not a staged introduction. The relationship gives the narrator material to work with — the NPCs have history, they have friction, they have something to *do* with each other. The PC's position in the scene becomes meaningful because of what's happening between the NPCs, not just what they think of the PC.

### Schema

```json
{
  "npc_relationships": [
    {
      "npc1": "guard_captain",
      "npc2": "medic",
      "description": "The medic refused to treat the officer until he backed down."
    }
  ]
}
```

- `npc1` and `npc2` are compendium NPC IDs
- `description` is a one-sentence relationship summary
- Immutable — set at seed time, never modified by engine
- Permanent relationships: family, long-term friends, partners, squadmates
- If one NPC departs, the relationship entry should be archived/removed (handled by validation)

### What changes

1. **`ccya/pack.py`** — Add `NpcRelationship` model, add `npc_relationships: list[NpcRelationship]` to `SeedState`
2. **`prepare_seed_system.j2`** — Add generation instructions for NPC relationships; enforce at least 1 relationship between present NPCs
3. **`prepare_seed_user.j2`** — Pass context if needed (likely not — LLM has all NPC names from compendium)
4. **`narrate_seed_system.j2`** — Add `npc_relationships` to context vars; render as section for narrator
5. **`ccya/engine/narrate.py`** — Pass `npc_relationships` to template
6. **`ccya/engine/seed.py`** — Validation: if an NPC in a relationship departs, remove the relationship; ensure present NPCs have at least one relationship
7. **`docs/architecture/`** — Update seed state docs, prompt variable contracts
8. **`docs/repomap.md`** — Update module mappings

### Scope

- Seed generation only (immutable)
- No runtime mutation of relationships
- Narrator sees them as context, same as threads
- Pack authors add `npc_bonds` pool entries if they want bond-specific relationship types

### Not in scope

- Runtime NPC-to-NPC relationship changes
- Bond pool integration (future)
- NPC relationship display in UI (future)
