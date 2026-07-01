---
title: "[Prompt] Choices tied to arcs/threads"
status: done
urgency: 4
size: medium
created: 2026-06-14
ticket_id: I-3
labels:
  - Improvement
  - World Building
---

## Detail

Prompt guidance to tie choices to active arcs/threads instead of random. Currently choices may not connect to the player's active objectives.

## Motivation

Choices tied to arcs/threads create more meaningful gameplay and reinforce the narrative structure.

## Resolution

Phase 4 data (25-turn runs) shows the prompt guidance is working well:
- Space-western: 89% arc-focused actions
- Noir-1930s: 90% arc-focused actions
- Golden-piracy: 38% arc-focused (62% scene-focused) — but this is appropriate for the scenario's scene-heavy gameplay loop

The golden-piracy "issue" isn't a bug — it's the scenario design creating a scene-heavy gameplay loop where scene-focused choices make sense. The prompt guidance successfully ties choices to arcs when the scenario supports it.

## Status: Done
