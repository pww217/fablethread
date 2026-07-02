---
title: "NPC roster personality fields are dead weight in scene prompt"
status: scoping
urgency: 3
size: small
created: 2026-07-01
ticket_id: I-20
labels: [npc, prompt-size, efficiency]
---

## Description

The scene prompt includes full personality fields for every NPC in the compendium roster, adding ~50-100 chars per NPC. With 5 NPCs in the noir run, this wastes ~250-500 tokens across the session. The personality fields (label, traits, speech_hint) are redundant with motivation, tie, leverage, and fear — the LLM already has enough behavioral signals to generate consistent NPC behavior.

## Evidence

Noir-1930s run, T15 scene prompt includes 5 NPCs with full personality blocks:

```
- `detective_vance` | **Arthur Vance** (Lead Investigator) [KNOWN] — A man whose badge has become a shield for the city's elite.
 | tie: holding Harold for questioning | wants: Closing the heist case with minimal paperwork | fears: An internal affairs audit | personality: **Cold Pragmatist** (calculating, direct, emotionally distant). Speech: terse and transactional; no pleasantries. | last seen: Precinct Alleyway (9 turns ago)
```

Each personality block adds ~50-100 chars. With 5 NPCs, that's ~250-500 chars of dead weight in the scene prompt alone.

## Root Cause

`build_npc_roster()` in `ccya/engine/npc_roster.py` includes personality fields from the archetype registry when `personality_registry` is provided. The `_npc_roster.j2` template renders them for all NPCs regardless of presence level.

## Proposal

Remove personality fields from the scene prompt NPC roster. Keep motivation, tie, leverage, fear, bio, and notes — these are the actual behavioral signals the LLM needs. Personality labels are redundant with these fields.

Expected savings: ~50-100 chars per NPC, ~250-500 chars per scene prompt in a 5-NPC session.

## Files to Review

- `ccya/engine/npc_roster.py` — `build_npc_roster()` includes personality from registry
- `ccya/prompts/sections/_npc_roster.j2` — renders personality fields
- `ccya/engine/extraction/scene.py` — passes `personality_registry=ARCHETYPES` to scene extraction
- `ccya/engine/narrate.py` — passes `personality_registry=ARCHETYPES` to narration
- `ccya/personality.py` — ARCHETYPES definition
