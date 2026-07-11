---
title: "Scene extractor should demote non-following NPCs on location change"
status: testing
urgency: 1
size: small
created: 2026-07-09
ticket_id: I-38
labels:
  - engine
  - extraction
  - npc
---

## Problem

When the player changes location, `apply_delta()` in `delta_builder.py:225-229` correctly demotes all non-party `present` NPCs to `nearby`. However, the scene extractor then re-promotes them to `present` because it doesn't know a location change occurred — it sees the NPCs mentioned in the narration and sets `presence: "present"`, overwriting the auto-demotion.

Example: in `saves/cordyceps-year-twenty-2026-07-08` turn 6, the player flees `millerton_wall` → `abandoned_logistics_depot`. The narration shows Phillip Smith and the soldiers still at the wall. `apply_delta()` demotes them to `nearby`, but the scene extractor emits `presence: "present"` for all three, so the post-turn state shows them all as `present` at the depot — they never existed there.

## Root Cause

The scene extractor runs before the state extractor in the extraction pipeline (`_extract_phase()` in `turn.py`). It has no knowledge of `location_change` when it processes the narration, so it can't distinguish between:
- NPCs that followed the player → should stay `present`
- NPCs left behind at the old location → should be `known` or `nearby`

## Changes

### Run state extractor first, pass location_change context to scene extractor

Reorder the extraction pipeline so the state extractor runs first, detects `location_change`, and passes that context to the scene extractor before it processes the narration.

The scene extractor prompt already has re-promotion instructions:
> "Re-promotion: If an NPC was demoted to `nearby` by a location change but narration shows they followed, set `presence: 'present'`"

With location_change context available, the extractor can apply this correctly: demote non-following NPCs to `known`/`nearby`, re-promote only those the narration shows followed.

### Files to change

- `ccya/engine/turn.py` — `_extract_phase()`: reorder state → scene extraction, pass `location_change` context
- `ccya/engine/extraction/context.py` or `ccya/prompts/extract_scene_system.j2`: accept location_change context in scene extractor prompt

### Validation

- Run `ev.py turn 6 --save-dir saves/cordyceps-year-twenty-2026-07-08` to verify NPCs are `nearby`/`known` post-location-change
- Check that NPCs explicitly shown following the player are re-promoted to `present`
