---
title: "Beat Driver Always 'Motivation'"
status: done
urgency: 3
size: medium
created: 2026-06-22
ticket_id: B-2
resolved: 2026-06-24
labels:
  - beat-generation
  - scene-extractor
  - storyteller
  - npc
---

## Problem

Both runs show that the vast majority of beats use `driver="motivation"`. This creates a narrow narrative palette where all beats feel the same.

**Evidence (Eval Cycle 2):**
- Zombie (aggressive): ~90% of beats use `driver="motivation"`
- Noir (opportunist): ~85% of beats use `driver="motivation"`

## Root Cause

Two issues converged:

1. **NPC roster data was incomplete.** Named NPCs often had only `motivation` without `fear`, `leverage`, or `bond`. Unnamed NPCs had no psychological fields at all. This meant the scene extractor could only find motivation-type candidates.

2. **Scene extractor effects were beat-like, not psychological.** The old format ("X's desire for [motivation] drives them to [behavior]") conflated psychological hints with story beats. The storyteller received beat-like effects without the full NPC roster, so it had limited material to work with.

## Fix Applied

### Scene Extractor (`extract_scene_system.j2`)

- **Psychological state format:** Changed `effect` from beat-like ("X's desire drives them to [behavior]") to psychological state ("Character wants X", "Character fears Y", "Character exercises leverage over Z", "Character feels responsible for X"). The storyteller receives raw psychological material, not pre-packaged beats.

- **Selection priority:** motivation first → leverage/bond second → fear last. Motivation is the most reliable driver and should be the first choice whenever available.

- **Mandatory motivation on all NPCs:** Unnamed NPCs now get `bio` + `motivation` (was `bio` only). Named NPCs now get `bio` + `personality` + `motivation` + 2 of {fear, leverage, bond} (was "at least 2 of" without mandatory motivation).

### Storyteller (`storytell_system.j2`)

- **Blend, don't pick:** Changed guidance from "pick or combine or thread-apply" to "blend, don't pick." The preferred pattern is combining 2-3 psychological hints into a single coherent beat.

- **Raw material framing:** Clarified that psychological hints are raw material for the storyteller to work with, not beats to deliver.

### Seed Prompt (`generate_seed_system.j2`)

- **Same field requirements:** Unnamed NPCs get `bio` + `motivation`. Named NPCs get `bio` + `personality` + `motivation` + 2 of {fear, leverage, bond}. This ensures seed-generated games start with diverse psychological fields.

## Result

The root cause is addressed at both levels: (1) NPCs now have diverse psychological fields by design, and (2) the scene extractor produces psychological state hints rather than beat-like effects, giving the storyteller richer material to blend. Motivation remains the primary driver but fear/leverage/bond are now available for variety.
