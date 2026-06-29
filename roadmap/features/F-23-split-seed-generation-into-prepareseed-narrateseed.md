---
title: "Split seed generation into prepare_seed + narrate_seed"
status: done
urgency: 3
size: medium
created: 2026-06-24
ticket_id: F-23
design: docs/design/seed-two-step-design.md
plan: plans/seed-two-step-plan.md
pr:
  url: https://github.com/anomalyco/ccya/pull/TODO
  branch: seed-two-step
related:
  - roadmap/features/pc-situation-reveal-over-time.md — gradual pc_situation reveal over turns 0-3 (prereq decision)
labels:
  - seed
  - engine
  - pipeline
---

## Eval findings (2026-06-29)

### prepare_seed prompt
**Verdict: good.** Gemma4 reliably produces valid JSON with all required fields (pc, location, inventory, compendium with 1+ present NPC, arc with threads, world.locations as array, world_state with valence mix). First attempt sometimes fails ("No JSON found") — second attempt succeeds within retry budget. Model hallucinates `meta.model` as "gpt-4o" (harmless).

### narrate_seed prompt — CRITICAL BUG FOUND AND FIXED
**Initial output: catastrophic failure.** Model generated cyberpunk/sci-fi content ("Aethelgard Transit Hub", "neon signs", "data-slate", "Enforcers in matte-black plating", "pulse-rifle", "the Breach", "the Syndicate") for the allied-ww2 pack despite all WW2 context being passed correctly in the prompt.

**Root cause:** The prompt template had zero setting constraints. It told the model to weave in PC/location/inventory data but never said "this is a historical WW2 setting" or "no sci-fi." Gemma4 hallucinated a genre because nothing stopped it.

**Fix:** Added `setting_info` context to prompt template with genre, universe_rules, and creative_direction from the pack's scenario. Template now renders these as hard constraints. After fix, model produces period-appropriate WW2 content with correct three-movement structure (close-up → exposition → crisis), 4 actions at 7-10 words each, and ~15-word outcome summary.

### End-to-end pipeline
**Verdict: working.** 3-turn `play --llm --turns 3 --pack allied-ww2` completed successfully. Seed generated, narrated, and turns processed without errors. Opening narrative correctly uses WW2 elements (Sten gun, Ardennes, jackboots, resistance network, Colt M1911).

### narrate_seed prompt — Data weaving bug found and fixed
**Initial prompt structure:** Told the model what to weave (instructions) but never actually provided the data (PC bio, arc, NPCs, etc.) in the prompt text. Only passed context variables that the template didn't render.

**Result:** Model hallucinated everything — wrong NPC names ("Sergeant Miller" instead of "Walter Briggs"), no PC name mentioned, no bio woven in, no arc objective referenced.

**Fix:** Added actual data sections to prompt template:
- PC (name, tagline, bio, stats, conditions, situation)
- Location (name, description)
- Arc origin
- World locations (first 5)
- Inventory (first 6)
- Compendium NPCs (with presence status)
- Arc (objective, threads)
- Pool selection (situation, arc, character_dynamic, moral_pressure, npc_bond, scene_bundle)

**After fix:** Model successfully weaves in PC name (Eric Marshall), PC bio (implied through tension, fear), PC situation (unit, theater, chain of command), location (Hixford Crossing, pontoon bridge, river), arc origin (lack of oversight, eastern line collapsed), compendium NPCs (Joseph Mann, Silas Vance — both present, show through action/dialogue), scene bundle (discarded ration tin, mud, fog).

### narrate_seed prompt — Over-prompting refined
**Problem:** First data-pass fix included too much — stats, full bio, inventory, world locations, all NPCs, pool selection archetypes. Model tried to weave everything, resulting in exposition-heavy prose that repeated UI-visible information.

**Insight:** Player can see bio, stats, inventory, full NPC roster in the UI. Opening narrative should fill in the gaps — establish world context (arc_origin), character's immediate situation (pc_situation), and the arc they're pursuing. Don't repeat what's already visible.

**Fix:** Slimmed prompt to only pass what the player needs at turn 0:
- PC: name, tagline, situation (NOT bio, stats, conditions)
- Location: name, description
- Arc origin (world-level context)
- Arc objective (the goal)
- Present NPCs only (bio for context)
- Scene bundle details (objects, conditions, sensory)
- Setting constraints (genre, universe rules)

**After fix:** Model produces focused opening that weaves in PC situation (Third Platoon, Hixford Crossing, Vance), arc origin (eastern line collapsed, Acostastead massacres), location (Hixford Crossing, bridge, river), present NPCs (Vance, Mann), scene bundle (periscope rifle, mud-choked duckboards). Stats, full bio, inventory not repeated — they're in the UI.

### End-to-end pipeline (final)
**Verdict: working.** 3-turn `play --llm --turns 3 --pack allied-ww2` completed successfully. Opening narrative now focuses on what the player needs at turn 0: PC situation (unit, theater, chain of command), arc origin (world-level context), arc objective (the goal), location, present NPCs, scene bundle details. Stats, full bio, inventory not repeated — they're visible in the UI.

### Remaining notes
- `prompt-eval dump/call` only works for turn prompts (ruling, narrate, etc.), not seed prompts. prompt_context module doesn't have access to seed data — expected behavior, not a bug.
- First prepare_seed attempt fails ~50% of the time ("No JSON found"), second attempt succeeds. Within retry budget but worth monitoring.
