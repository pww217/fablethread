---
title: "NPC scene redesign — drop aliases, drop plurals, simplify unnamed detection"
status: scoping
created: 2026-06-25
labels:
  - npc
  - scene
  - prompts
  - engine
---

# NPC Scene Redesign

## Problem

The NPC system has three intertwined issues that have never worked well:

1. **Aliases** were designed for deduplication and name discovery, but the LLM can't reliably distinguish when to use name vs alias. Self-aliasing (e.g., `black_market_traders` with `aliases: ["black_market_traders"]`) incorrectly triggers the unnamed guard. The field has never done what it was meant to do.

2. **Plural/group NPCs** were introduced so the narrator wouldn't say "a group of guards" without a count. Quantity-stripped resolution ("three guards" → "five guards") was meant to keep them tracked. But it's complex, difficult to update, and creates awkward entries.

3. **Unnamed detection** relies on alias matching (name in aliases), which is fragile. There's no reliable way to distinguish "grease-stained technician" from "John Smith" without listing every adjective and title in existence.

## Target State

### NPC Identity Model

Every NPC in the compendium is an **individual**. The `aliases` field is removed entirely. Unnamed detection uses a **proper-name heuristic** instead of alias matching.

### Proper-Name Heuristic

An NPC is **named** if their `name` field contains at least two space-separated words, **both** starting with an uppercase letter (e.g., "John Smith", "Mary Jane Watson"). Everything else is **unnamed** (e.g., "Grease-stained technician", "Scarred veteran", "Three guards").

The heuristic operates on the `name` field only. The `title` field is separate and does not participate in the heuristic.

### Name and Title Separation

- **`name`**: First + last name only (e.g., "John Smith"). No titles, prefixes, suffixes, or descriptors.
- **`title`**: Honorifics, roles, or status descriptors (e.g., "Dr.", "Sergeant", "Captain of the Guard", "local settlement doctor"). Flexible — any non-name descriptor goes here.

The proper-name heuristic only looks at `name`. If titles are in the name field, the heuristic fails. Prompt guidance enforces the separation.

### Ambient NPCs Removed

The requirement that "there MUST always be at least 1 NPC with `presence: present`" via ambient characters (crowd, bystanders) is removed. The location description and scene context already convey ambient presence. Named NPCs are sufficient.

### Scene NPC Count

The narrator and scene extractor are guided (not enforced) to keep scenes to 6-8 NPCs total, with at most 3 in confrontational scenes. This is prompt guidance only — no engine enforcement.

### Name Revelation

When an unnamed NPC's proper name is revealed, the extractor replaces the `name` field directly. No alias history is kept. The old descriptive label is irrelevant once the real name is known.

### Explicit Deduplication

The scene extractor and narrator prompts receive explicit deduplication instructions to prevent the LLM from creating duplicate entries for the same NPC.

## Decisions

### D1: Drop `aliases` field entirely

**Final.** The `aliases` field is removed from:

- `CompendiumNpcUpdate` model (`ccya/models/extraction.py`)
- All prompt templates (seed, scene extract, narrator, ruling)
- All engine logic (`npcs.py`, `seed.py`, `extraction/utils.py`, `extraction/context.py`, `npc_roster.py`)
- All templates (roster, state panels)
- `NPCRosterEntryBlock` context model (already doesn't have it)

**Rationale:** The field has never worked reliably. The LLM can't distinguish when to use name vs alias. Self-aliasing triggers the unnamed guard incorrectly. Neither deduplication nor name discovery has been reliable.

### D2: Drop plural/group NPCs

**Final.** Every NPC is an individual. The quantity-stripped resolution logic is removed.

**Rationale:** Plural NPCs are complex to update, create awkward entries, and the quantity-stripped resolution is fragile. A story generator on a small scale shouldn't have more than 6-8 total NPCs in a scene. Confrontational scenes should have at most 3.

**What stays:** Ambient presence is handled by location description and scene context, not by ambient NPC entries. The scene extractor no longer needs to emit ambient presence entries.

### D3: Proper-name heuristic (at least 2 capitalized words)

**Final.** An NPC is named if `name` contains at least two space-separated words, both starting with an uppercase letter. Everything else is unnamed.

**Rationale:** This is the simplest reliable heuristic. "John Smith" → named. "Grease-stained technician" → unnamed. "Scarred veteran" → unnamed. "Three guards" → unnamed. The heuristic doesn't need adjective lists or title lists because titles go in the `title` field.

**Implementation:** A single function `_is_named(name: str) -> bool` replaces `_is_unnamed` across all four locations where unnamed detection currently occurs.

### D4: Ambient NPCs removed

**Final.** The scene extractor no longer emits ambient presence entries (crowd, bystanders). The rule "There MUST always be at least 1 NPC with `presence: present`" is removed from the scene extractor prompt.

**Rationale:** The LLM almost never follows that rule anyway. Location description and scene context already convey ambient presence. Ambient NPC entries add noise without value.

### D5: Name revelation = direct replacement

**Final.** When an unnamed NPC's proper name is revealed, the extractor replaces the `name` field directly. No alias history is kept.

**Rationale:** Without aliases, there's no mechanism to preserve the old descriptive label. The old name is irrelevant once the real name is known. Keeping alias history adds complexity for no benefit.

### D6: Title field is flexible

**Final.** The `title` field accepts honorifics, roles, and status descriptors. Examples: "Dr.", "Sergeant", "Captain of the Guard", "local settlement doctor".

**Rationale:** The title field already works well. Strengthening prompt guidance to enforce separation from `name` is sufficient. No model changes needed.

### D7: Scene NPC count = LLM guidance only

**Final.** Add guidance to narrator and scene extractor prompts. No engine enforcement.

**Rationale:** The LLM can follow count guidance without hard enforcement. Engine enforcement adds complexity and edge cases.

### D8: Explicit deduplication in prompts

**Final.** Add explicit deduplication instructions to scene extractor and narrator prompts. Existing engine dedup logic in `_dedup_compendium_update` is simplified (no alias/group matching).

**Rationale:** Even with full IDs in context, the scene extractor sometimes creates duplicates. The narrator sometimes introduces the same NPC multiple times.

## What Changes

### Models

- **`CompendiumNpcUpdate`** (`ccya/models/extraction.py:18`): Remove `aliases` field.
- **Seed envelope schema** (`ccya/prompts/generate_seed_system.j2:36`): Remove `aliases` from the compendium NPC schema in the prompt.

### Engine

- **`ccya/state/npcs.py`**:
  - Remove `build_npc_alias_map` (line 25).
  - Remove `_resolve_group_npc_id` (line 76).
  - Remove `_find_npc_by_name` (line 146).
  - Remove `_strip_quantity_suffix` (line 128).
  - Remove `_STRIPPLABLE_QUANTITIES` (line 17).
  - Replace `_is_unnamed` guard in `apply_npc_scene_management` (line 263) with `_is_named` proper-name heuristic.
  - Remove alias merging logic in `apply_npc_scene_management` (lines 231-239, 256-261).
  - Simplify personality assignment logic (remove quantity-stripped name logic, alias-based unnamed check).
  - Simplify the function — fewer edge cases, fewer branches.

- **`ccya/engine/seed.py`** (lines 307-337):
  - Remove `_QUANTITY_WORDS` constant.
  - Replace alias-based unnamed detection with proper-name heuristic.
  - Simplify the post-processing loop.

- **`ccya/engine/extraction/utils.py`**:
  - Remove `_GROUP_QUANTIFIERS` constant (line 82).
  - Remove `_extract_group_base_type` function (line 91).
  - Simplify `_dedup_compendium_update` (line 111): remove group NPC base type matching (lines 143-152), remove alias matching (line 137).

- **`ccya/engine/extraction/context.py`** (line 80):
  - Replace `_filter_unnamed_personality`: remove alias-based unnamed detection, use proper-name heuristic.

- **`ccya/engine/npc_roster.py`** (line 14):
  - Replace `_compute_npc_score`: remove alias-based unnamed detection (lines 19-21), use proper-name heuristic.

### Prompts

- **`ccya/prompts/extract_scene_system.j2`**:
  - Remove all `aliases` references from schema (line 11), field rules (line 65), and NPC field requirements (lines 110-126).
  - Remove alias-first naming section (lines 110-116).
  - Remove group NPC rules (lines 102-108, 123-125).
  - Remove "promotion to named" logic (line 122).
  - Remove ambient presence requirement (line 188).
  - Strengthen name guidance: `name` must be first + last name with a space, no titles/prefixes/descriptors.
  - Add explicit deduplication instructions (strengthen existing section at line 178).
  - Add scene NPC count guidance (max 6-8 total, max 3 in confrontational scenes).
  - Simplify unnamed detection guidance to use proper-name heuristic.

- **`ccya/prompts/generate_seed_system.j2`**:
  - Remove all `aliases` references from schema (line 36) and NPC field requirements (lines 91-101).
  - Remove group NPC guidance (lines 97-101).
  - Strengthen name guidance: `name` must be first + last name, no titles/prefixes/descriptors.
  - Strengthen title guidance: titles, roles, descriptors go in `title` field.
  - Add scene NPC count guidance.
  - Simplify unnamed detection guidance to use proper-name heuristic.

- **`ccya/prompts/narrate_system.j2`**:
  - Add scene NPC count guidance (max 6-8 total).
  - Add guidance to reference existing NPCs by name, don't introduce duplicates.
  - Remove NPC QUANTITY RULE (line 75) — no longer relevant without group NPCs.
  - Simplify NPC NAMING guidance (line 80) — remove alias references.
  - Remove NEW GROUPS guidance (line 61) — no longer relevant.
  - Remove REINTRODUCING GROUPS guidance (line 63) — no longer relevant.

### Templates

- **`ccya/prompts/sections/_npc_roster.j2`**: No changes needed (aliases were never rendered).
- **`templates/_npc_roster.html`**: Check for and remove any `aliases` display.
- **`templates/_state_left.html`**: Check for and remove any `aliases` references.
- **`templates/_state_right.html`**: Check for and remove any `aliases` references.
- **`templates/_state_full.html`**: Check for and remove any `aliases` references.

### Context Building

- **`ccya/prompts/context.py`**: No changes needed (`NPCRosterEntryBlock` already doesn't have `aliases`).

### Server Routes

- **`ccya/server/routes.py`** (lines 620-624): Remove `alias` fallback in `display_name` logic. Use: `name` -> `title` -> `key` (ID).

### Personality System

- **`ccya/personality.py`**: No changes needed (personality assignment logic is in seed.py and npcs.py, not here).

## What Does NOT Change

- **`NPCRosterEntryBlock`** (`ccya/prompts/context.py:201`): Already doesn't have `aliases`. No changes needed.
- **Presence tracking logic** (`touch_compendium_order`, `departed` handling): Unchanged.
- **Personality archetype registry**: Unchanged.
- **`build_npc_roster` sorting/ordering**: Unchanged (only the score computation changes).
- **Compendium entry fields** (bio, motivation, fear, leverage, bond, party, position, etc.): Unchanged.
- **Scene extractor output structure** (other than removing `aliases` from `CompendiumNpcUpdate`): Unchanged.
- **Ruling prompts**: Remove `aliases` references if present.
- **Inventory system**: Inventory items have their own `aliases` field — unrelated to NPC changes.

## Unnamed Detection — Before and After

### Before (alias-based)

```python
is_unnamed = name and aliases and name.lower().strip() in {a.lower().strip() for a in aliases}
```

This appears in four places:
- `ccya/state/npcs.py:263` (apply_npc_scene_management)
- `ccya/engine/extraction/context.py:98` (_filter_unnamed_personality)
- `ccya/engine/npc_roster.py:20` (_compute_npc_score)
- `ccya/engine/seed.py:316` (seed post-processing)

### After (proper-name heuristic)

```python
def _is_named(name: str) -> bool:
    """Return True if name looks like a proper name (at least 2 capitalized words)."""
    if not name:
        return False
    words = name.strip().split()
    return len(words) >= 2 and all(w and w[0].isupper() for w in words)

is_named = _is_named(name)
is_unnamed = name and not is_named
```

The new function replaces `_is_unnamed` in all four locations. The logic is inverted: instead of checking if name matches an alias, check if name has the proper-name pattern.

## Impact Summary

| Component | Changes |
|---|---|
| `ccya/models/extraction.py` | Remove `aliases` from `CompendiumNpcUpdate` |
| `ccya/state/npcs.py` | Remove alias map, group NPC resolution, quantity stripping, alias merging. Replace unnamed detection. |
| `ccya/engine/seed.py` | Remove quantity words, alias-based unnamed detection. Replace with proper-name heuristic. |
| `ccya/engine/extraction/utils.py` | Remove group quantifiers, base type extraction. Simplify dedup. |
| `ccya/engine/extraction/context.py` | Replace alias-based unnamed detection with proper-name heuristic. |
| `ccya/engine/npc_roster.py` | Replace alias-based unnamed detection with proper-name heuristic. |
| `ccya/prompts/extract_scene_system.j2` | Remove aliases, group NPCs, ambient requirement. Strengthen name/title guidance. Add dedup/count guidance. |
| `ccya/prompts/generate_seed_system.j2` | Remove aliases, group NPCs. Strengthen name/title guidance. Add count guidance. |
| `ccya/prompts/narrate_system.j2` | Remove group NPC guidance. Add count guidance. Simplify naming guidance. |
| `ccya/server/routes.py` | Remove alias fallback in display_name. |
| Templates | Remove aliases display if present. |

## Open Questions

None. All design decisions are recorded above.