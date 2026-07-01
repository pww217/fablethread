---
title: "NPC scene redesign — drop aliases, drop plurals, simplify unnamed detection"
status: scoping
urgency: 2
size: large
created: 2026-06-25
ticket_id: I-18
labels:
  - npc
  - scene
  - prompts
  - engine
---

## Problem Statement

The NPC system has three intertwined issues that have never worked well:

1. **Aliases** were designed for deduplication and name discovery, but the LLM can't reliably distinguish when to use name vs alias. Self-aliasing (e.g., `black_market_traders` with `aliases: ["black_market_traders"]`) incorrectly triggers the unnamed guard. The field has never done what it was meant to do.

2. **Plural/group NPCs** were introduced so the narrator wouldn't say "a group of guards" without a count. Quantity-stripped resolution ("three guards" → "five guards") was meant to keep them tracked. But it's complex, difficult to update, and creates awkward entries.

3. **Unnamed detection** relies on alias matching (name in aliases), which is fragile. There's no reliable way to distinguish "grease-stained technician" from "John Smith" without listing every adjective and title in existence.

## Decisions

### 1. Drop `aliases` field entirely

**Why:** The field has never worked reliably. The LLM can't distinguish when to use name vs alias. Self-aliasing triggers the unnamed guard incorrectly. It was meant to solve deduplication and name discovery, but neither use case has been reliable.

**Impact:**
- Remove `aliases` from `SceneExtractResult`
- Remove `aliases` from all prompts (scene extract, seed, ruling, narrate)
- Remove alias-based logic: `build_npc_alias_map`, `_resolve_group_npc_id`, `_find_npc_by_name`
- Remove `_is_unnamed` guard (replaced by proper-name heuristic)
- Remove alias merging in `apply_npc_scene_management`
- Remove alias references in templates (roster, UI)

### 2. Drop plural/group NPCs — every NPC is an individual

**Why:** Plural NPCs are complex to update, create awkward entries, and the quantity-stripped resolution is fragile. A story generator on a small scale shouldn't have more than 6-8 total NPCs in a scene. Confrontational scenes should have at most 3.

**Impact:**
- Remove `aliases` (which carried the quantity info)
- Remove `_STRIPPLABLE_QUANTITIES` constant
- Remove `_strip_quantity_suffix` function
- Remove `_resolve_group_npc_id` function
- Remove `_find_npc_by_name` function (quantity-agnostic matching)
- Remove quantity-stripped dedup logic in `apply_npc_scene_management`
- Remove group NPC guidance from prompts
- Add scene NPC count guidance to narrator and scene prompts

### 3. Unnamed detection = proper-name heuristic

**Decision:** If a name has two space-separated words both starting with a capital letter, it's a proper name (named). Everything else is unnamed.

**Rationale:** This is the simplest reliable heuristic. "John Smith" → named. "Grease-stained technician" → unnamed. "Scarred veteran" → unnamed. "Three guards" → unnamed. The heuristic doesn't need adjective lists or title lists because titles go in the `title` field (not `name`), and the heuristic only looks for the pattern: `CapitalizedWord CapitalizedWord`.

**Impact:**
- Replace `_is_unnamed` alias-based guard with proper-name heuristic
- Strengthen prompt guidance: `name` must be first + last name with a space, no prefixes/suffixes/titles
- The `title` field should contain titles (Dr., Sgt., etc.)

### 4. Add explicit deduplication instructions

**Why:** Even with full IDs in context, the scene extractor sometimes creates duplicates. The narrator sometimes introduces the same NPC multiple times.

**Impact:**
- Add explicit deduplication instructions to scene extractor prompt: "If the narration describes an NPC you already have in your compendium (same position, same description, same context), update the existing entry. Do NOT create a new entry."
- Add similar guidance to narrator prompt: "If an NPC is already in the compendium, reference them by their existing name. Do not introduce them again as a new character."

### 5. Add scene NPC count guidance

**Why:** Pacing and manageability. A scene with 6-8 NPCs max is narratively focused. Confrontational scenes should have at most 3.

**Impact:**
- Add guidance to narrator prompt about scene NPC limits
- Add guidance to scene extractor prompt about scene NPC limits
- Remove any existing guidance that encourages plural/group NPCs

### 6. Strengthen name/title field separation

**Decision:** `name` = first + last name only (e.g., "John Smith"). `title` = honorifics/titles (e.g., "Dr.", "Sgt.", "Captain").

**Rationale:** The proper-name heuristic needs clean input. If titles are in the name field ("Dr. John Smith"), the heuristic fails.

**Impact:**
- Strengthen guidance in seed prompt: name must be first + last, no titles
- Strengthen guidance in scene extract prompt: same
- Strengthen guidance in narrator prompt: use title field for titles

## Prompt Changes Required

### `generate_seed_system.j2`
- Remove all `aliases` references from NPC schema and guidance
- Strengthen name guidance: "name must be first + last name with a space, no titles/prefixes/suffixes"
- Remove group NPC guidance (plural NPCs, quantity in name)
- Add scene NPC count guidance (max 6-8 total, max 3 in confrontational scenes)

### `extract_scene_system.j2`
- Remove all `aliases` references from NPC schema and guidance
- Strengthen name guidance: same as seed
- Add explicit deduplication instructions
- Add scene NPC count guidance
- Remove "promotion to named" logic (unnecessary without aliases)
- Remove group NPC guidance

### `narrate_system.j2`
- Add scene NPC count guidance (max 6-8 total)
- Add guidance to reference existing NPCs by name, don't introduce duplicates
- Remove any guidance that encourages plural/group NPCs

### `ruling_system.j2` / `ruling_user.j2`
- Remove `aliases` references if present

### `_npc_roster.j2` template
- Remove `aliases` display

### `_conditions.j2` and other templates
- Check for any `aliases` references

## Engine Changes Required

### `ccya/models.py` (SceneNPC)
- Remove `aliases` field

### `ccya/models/state.py`
- Check for any `aliases` references

### `ccya/state/npcs.py`
- Remove `build_npc_alias_map`
- Remove `_resolve_group_npc_id`
- Remove `_find_npc_by_name`
- Remove `_strip_quantity_suffix`
- Remove `_STRIPPLABLE_QUANTITIES`
- Replace `_is_unnamed` guard with proper-name heuristic
- Remove alias merging logic in `apply_npc_scene_management`
- Simplify the function (fewer edge cases)

### `ccya/state/delta_builder.py`
- Check for any `aliases` references

### `ccya/engine/seed.py`
- Remove alias-based unnamed detection in seed generation
- Strengthen name guidance

### `ccya/engine/npc_roster.py`
- Remove `aliases` display logic

### `ccya/engine/config.py`
- Check for any `aliases` references

### `ccya/prompts/context.py`
- Remove `aliases` from context building

### `ccya/personality.py`
- Check for any `aliases` references

## Templates to Update

- `templates/_npc_roster.html` — remove aliases display
- `templates/_state_left.html` — check for aliases
- `templates/_state_right.html` — check for aliases
- `templates/_state_full.html` — check for aliases
- Any other templates referencing `aliases`

## Checklist

- [ ] Design doc created (this file)
- [ ] Plan written
- [ ] Models updated (SceneNPC, etc.)
- [ ] Prompt templates updated (seed, scene, narrator, ruling)
- [ ] Engine logic updated (npcs.py, seed.py, etc.)
- [ ] Templates updated (roster, state panels)
- [ ] Context building updated (prompts/context.py)
- [ ] Personality system updated (if aliases referenced)
- [ ] Make check passes (lint + typecheck)
