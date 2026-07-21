---
title: "Narration prompt lacks directive to use NPC name pool for new characters"
status: testing
urgency: 1
size: small
created: 2025-07-21
ticket_id: I-42
labels: [narration, prompts, npc-names]
design:
plan:
pr:
  url:
  branch:
---

## Problem

The narration prompt injects a `## Name Pool` (generated via `generate_npc_names_split()` from Faker) into every turn's user prompt, but the system prompt has **no instruction** telling the LLM to use these names when introducing new characters.

The seed prompt (`prepare_seed_system.j2`) has two explicit directives:
- Line 9: *"Names: pick from the name pool provided; favor fit over prominence"*
- Line 81: *"Use the name pool provided — do not invent names outside it."*

The narration prompt (`narrate_system.j2`) has neither. Its NEW CHARACTERS section (line 41) only says "describe their appearance, demeanor, or a visible trait." Its NPC NAMING section (line 55) only covers existing NPCs: "Every NPC must be referred to by their exact proper name from the Characters section."

**Result:** The LLM falls back to its training distribution when naming new characters, producing generic Anglo names (Elias, Vance, Miller, Elliot, Elara) regardless of the culturally-appropriate Faker-generated names injected into the prompt.

Evidence: Eval runs 2342 (noir-1930s) and 1717 (space-western) show `Elias Thorne` and `Silas Vane` appearing across completely different settings, confirming the LLM is not consulting the name pool.

## Root Cause

The name pool IS injected into `narrate_user.j2` under `## Immutable Reference > ### Name Pool`, but:
1. No system prompt directive tells the LLM to use it for new characters
2. The pool header doesn't clarify its purpose (it looks like reference material, not a directive)
3. The pool appears late in the prompt (after roster, world state, scene context, prior history, recent turns)

## Fix

Three targeted changes (already implemented):

### 1. `ccya/prompts/narrate_system.j2` — Add new character naming directive

Insert after the existing NEW CHARACTERS section:

> **NEW CHARACTER NAMING:** When introducing a new character (or revealing the name of an unnamed character such as "the shadowy figure"), you MUST pick their name from the `## Name Pool` section below. The name pool is NOT a list of active characters — it is a reservoir of available names. Pick one name and use it. Do not invent names outside the pool. If you have used a pool name in a recent turn, pick a different one from the pool for variety.

### 2. `ccya/prompts/narrate_user.j2` — Improve name pool header

Change `### Name Pool` to:

> ### Required Name Pool for New Characters
> The names below are available names — NOT active characters. When introducing a new character or revealing a character's name, pick one from this list. Do not invent names outside this list.

### 3. `ccya/prompts/extract_scene_system.j2` — Add revealed name extraction

Add to extraction mandate:

> - If narration reveals a name for a previously unnamed/alias character (e.g., "the shadowy figure" says "I'm Marcus Bell"), extract the revealed name and update the entry accordingly.

## Verification

Run an eval with a noir or similar pack and check:
1. New NPCs introduced in turns 2-5 have names from the Faker-generated pool (not Elias/Vance/Miller/Elara/Elliot)
2. When an unnamed/alias character gets named in narration, the extractor captures the revealed name
3. Names vary across turns (the pool regenerates each turn with seed=turn_no)
