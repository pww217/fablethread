---
title: "Beat Driver Always 'Motivation'"
status: new
priority: medium
created: 2026-06-22
labels:
  - beat-generation
  - scene-extractor
  - storyteller
  - pacing
---

## Problem

Both runs show that the vast majority of beats use `driver="motivation"`. This creates a narrow narrative palette where all beats feel the same.

**Evidence (Eval Cycle 2):**
- Zombie (aggressive): ~90% of beats use `driver="motivation"`
- Noir (opportunist): ~85% of beats use `driver="motivation"`

## Root Cause Analysis

The beat driver system has two stages:

### Stage 1: Scene Extractor (extract_scene_system.j2)

The scene extractor identifies 1-3 NPCs likely to act or be affected next turn. For each, it assigns one of four types:
- `motivation` → "X's desire for [motivation] drives them to [behavior]"
- `fear` → "X's fear of [fear] drives them to [behavior]"
- `leverage` → "X's advantage of [leverage] drives them to [behavior]"
- `bond` → "X's history with [bond] drives them to [behavior]"

The scene extractor has a "PRE-CHECK" that says: "Only assign a type if that psychological field (motivation/fear/leverage/bond) is actually present in the roster entry."

### Stage 2: Storyteller (storytell_system.j2)

The storyteller receives `candidate_npcs` from the scene extractor. The storyteller is instructed to use the `type` from the candidate_npcs entry for the chosen NPC as the driver value:
> If the candidate says `(fear)`, set `driver: "fear"`. If the candidate says `(motivation)`, set `driver: "motivation"`. Do not pick a different driver — the scene extractor already identified the relevant psychological field.

### Why "motivation" dominates

1. **NPC roster data.** Named NPCs should have "at least 2 of {motivation, fear, leverage, bond}" (extract_scene_system.j2:112), but in practice, most NPCs have "motivation" but not the other fields. This is a data issue, not a prompt issue.

2. **Scene extractor bias.** The scene extractor only identifies 1-3 candidates per turn. If most NPCs have "motivation" but not "fear", "leverage", or "bond", then the scene extractor will only identify "motivation" candidates.

3. **Storyteller constraint.** The storyteller is instructed to use the driver from the candidate_npcs entry. It cannot pick a different driver. This is by design — the scene extractor is the authority on which psychological field is relevant.

## Suggested Fixes

### Option A: Encourage diverse scene extractor candidates (recommended)

Add guidance to the scene extractor to identify diverse candidates, not just motivation:
- "Identify at least one candidate from each of motivation, fear, leverage, and bond if possible."
- "If an NPC has multiple psychological fields, pick the most narratively relevant one, not just motivation."

This addresses the root cause at the source — the scene extractor.

### Option B: Allow storyteller to pick drivers beyond candidate_npcs

Remove the constraint that the storyteller must use the driver from candidate_npcs. Instead, allow the storyteller to pick any driver that's present in the NPC's roster entry:
> "Pick a driver from the NPC's roster entry (motivation, fear, leverage, bond, personality). Prefer the most narratively relevant one."

This gives the storyteller more flexibility but may reduce the scene extractor's authority.

### Option C: Improve NPC roster data

Ensure NPC roster entries have diverse psychological fields. This is a data issue that should be fixed at the pack level, not the prompt level. But it's also a systemic issue — the scene extractor should be able to work with whatever data is available.

### Option D: Add beat driver diversity guidance to storyteller

Add guidance to the storyteller to use diverse drivers:
> "Don't repeat the same driver more than twice consecutively. If the last two beats used `driver: "motivation"`, try `driver: "fear"` or `driver: "leverage"` next."

This is a weaker fix because it doesn't address the root cause — the scene extractor is still only identifying "motivation" candidates.

## User Preference

User preference: motivation = primary, leverage/bond = secondary, fear = third, personality = removed (valid option). This suggests that "motivation" should be the most common driver, but not the only one.

## Priority

Medium. This is a narrative quality issue, not a structural bug. The beat system works correctly — it's just that the NPC roster data and scene extractor are biased toward "motivation". Fixing this would improve narrative variety but wouldn't fix any critical bugs.
