---
title: "Choice grounding priority"
status: idea
urgency: 3
size: small
created: 2026-07-09
ticket_id: I-36
labels:
  - engine
  - prompts
---

## Problem

The record step's action generation prompt tells the LLM to "reference actual game state: named NPCs present, inventory items, location features" — but NPCs, inventory, and location are not provided in the user prompt. Meanwhile, the prompt provides dormant threads, band results, scene phase, and urgency decay timers — internal mechanics the player never sees.

The prompt provides no explicit instruction to exclude dormant threads from choices, so the LLM may generate actions referencing faded/background elements.

## Solution

Update `record_system.j2` actions section with clearer grounding priorities:

1. Arc goal / long-term objective
2. Urgent threads
3. Regular active threads
4. Immediate narration

Explicit instruction: **DO NOT create actions involving dormant threads or departed NPCs.**

NPCs, inventory, and location are secondary — only reference them when they tie to narration, arc, or threads.

## Files

- `ccya/prompts/record_system.j2` — actions section (lines 115-127)
- `ccya/prompts/narrate_seed_system.j2` — actions section (lines 79-89), apply similar priority

## No structural changes

- No new fields on `RecordResult`
- No changes to `record_user.j2` — dormant threads stay in the prompt (needed for thread operations)
- No `intent_verb` field on actions — outside scope

## Acceptance criteria

- Record actions prioritize arc goal → urgent thread → regular thread → narration
- Record actions never reference dormant threads
- Seed actions apply similar priority
- Actions still reference NPCs/inventory/location when they tie to the primary priorities
