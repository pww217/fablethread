---
title: "World step: inject world agency and novelty"
status: idea
urgency: 2
size: large
created: 2026-07-30
ticket_id: F-35
labels:
  - world-step
  - npc-agency
  - world-simulation
---

## Problem

The world step is purely advisory. It generates 2-3 abstract beat candidates (`type` + mechanism tags) that Ruling picks from and Narrate interprets. It does not change any state. The game feels too static, too reactive, too centered on the player. NPCs don't act on their own. Threads don't advance independently. The world waits for the player instead of living.

## Current state

- World step runs async after every turn, generates 2-3 `GMBeat` candidates
- Only **present** NPCs are included in beat generation (nearby/known/departed excluded)
- Beats are mechanism tags only — abstract suggestions, not concrete content
- No state mutation from World step — it writes to `state.meta.beat_candidates` only
- Threads are referenced but never advanced by World
- Departed NPCs are invisible to beat generation

## What a true GM does between turns

A GM doesn't just suggest "a complication could happen." A GM:
- NPCs pursue goals, make moves, speak, shift alliances, act off-screen
- Threads advance with concrete developments regardless of player action
- The world changes: conditions shift, people arrive/leave, relationships evolve
- Consequences from past actions come due
- Foreshadowing is planted for future payoffs
- Scene atmosphere shifts independently of player input

## Proposed capabilities (ranked by impact vs complexity/token cost)

### 1. Expand NPC visibility — LOW complexity, HIGH impact
**What:** Include nearby, known, and departed NPCs in world step context. Currently only `presence == "present"` NPCs are passed to the world step prompt.

**Why:** The world step can't generate beats from NPCs it can't see. Departed NPCs leaving a hook, nearby NPCs arriving, known NPCs acting — all invisible right now.

**Cost:** Minimal. Just change the `npc_roster` filter in `world.py:49`. Prompt tokens increase by ~200-400 per departed/nearby NPC.

### 2. World-proposed thread progress — MEDIUM complexity, HIGH impact
**What:** World step outputs actual thread progress entries (`major_updates`) in addition to beat candidates. Dormant threads wake up. Urgent threads get new developments. New threads spawn from consequences.

**Why:** Threads currently only advance via Record (backward-looking, player-action-driven). World step is forward-looking — it's where threads should get independent agency.

**Cost:** Medium. New output field in world step response. Parser needs to handle thread progress entries. Prompt tokens increase by ~100-200 (threads already in context).

### 3. World-proposed NPC state changes — MEDIUM complexity, HIGH impact
**What:** World step proposes NPC changes: disposition shifts, presence changes (departed→returning, nearby→present), tie/relationship updates, motivation/fear evolution.

**Why:** NPCs feel like puppets right now. Their state only changes via extraction (reactive to narration). World step should let NPCs change proactively.

**Cost:** Medium. New output field. Needs validation + application pipeline (similar to how Record's thread_updates work). Prompt tokens minimal (NPCs already in context).

### 4. World as true simulation layer — HIGH complexity, HIGH impact
**What:** World step outputs actual `WorldState` mutations alongside beat candidates. Thread progress, NPC changes, new NPC additions, condition/inventory changes — all driven by world simulation, not player action.

**Why:** This is the full vision. The world runs on its own clock. NPCs act. Threads advance. The world changes. The player enters a living world, not a stage that waits for them.

**Cost:** High. New output schema, new validation pipeline, new application logic. But no backward compatibility concerns — this is a clean rework.

### 5. Concrete narrative content — LOW-MEDIUM complexity, MEDIUM impact
**What:** World step generates actual dialogue snippets, scene atmosphere descriptions, foreshadowing hooks — concrete content the narrator weaves in, not mechanism tags.

**Why:** Mechanism tags add a layer of abstraction without adding value. Direct content is cleaner and more evocative.

**Cost:** Low-medium. Changes prompt + parser. Replaces mechanism tag generation with content generation.

## Design notes

- No backward compatibility needed. Can rework the beat system entirely.
- World step already runs every turn async — it has the infrastructure for more.
- Thread sanitizer already does LLM-based state mutation (urgency adjustment, world state replacement) — proven pattern.
- Record already applies thread_updates, thread_add, thread_resolve — proven application pipeline.
- The mechanism tag system (`[highlight: X]`, `[blend: X vs Y]`) is an intermediate representation that adds complexity without adding value. Consider replacing with direct content.

## Related

- [F-18](../features/F-18-storytell-proactive-npc-agency-gm-beats-redesign.md) — Proactive NPC agency + GM beats redesign (done/speculative, same concern)
- [I-11](../improvements/I-11-world-step-read-npc-profiles-directly-from-compendium.md) — World step already reads from compendium
- [I-12](../improvements/I-12-world-step-not-blending-npc-psychological-hints.md) — NPC psychological blending
