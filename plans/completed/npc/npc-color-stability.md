# Fix NPC color consistency and entity color separation

**Status:** completed  
**Created:** 2026-07-12  
**Summary:** NPC highlight colors change after each turn and overlap with PC/inventory colors. This plan ensures deterministic NPC colors from extraction, prevents palette collisions, and separates entity color palettes.

---

## Root cause analysis

### Problem 1: NPC colors change across turns
- Seed assigns colors from a 12-color palette via SHA256(npc_id) — deterministic ✅
- New NPCs discovered **during extraction** get `color=None` because `CompendiumNpcUpdate` has no color field
- JS `_highlightEntities` falls back to `_npcColor(id)` (djb2 variant hash) — **outputs different colors than Python's SHA256**
- Result: new NPCs narrated with a NN1EJScolor different from the sidebar compendium

### Problem 2: 12-color palette causes collisions
- Multiple NPCs hashed into 12 colors — frequent same-color assignments
- PC CSS variable (`--accent-pc: #98c379`) was chosen from the palette — can visually match an NPC's palette color
- Inventory uses `entity-item` CSS with hardcoded color — no per-item coloring

## Design decisions

1. **Expand NPC palette to 48 colors** — reduces collision probability significantly
2. **Assign color on Python side during extraction** — ensures Python and JS use the same color
3. **Separate per-entity-color palettes for PC and inventory** — distinct hues, no overlap with NPCs
4. **Keep `color` field optional** (`str | None`) — avoids migration issues
5. **No CompendiumNpcUpdate.color** — the engine assigns the color, not the LLM
6. **Persist colors in state.yaml** — colors survive game restarts

## Implementation plan

### Phase 1: Python — color generation + assignment

1. **New file `ccya/engine/npc_color.py`**: centralized color generation utilities
   - `generate_npc_color(npc_id)` → NPC palette
   - `generate_pc_color()` → PC color (uses seedable input, always same value)
   - `generate_item_color(item_id)` → item palette
   - Each uses `hashlib.sha256(entity_type + id)` to get deterministic index into entity-specific palette

2. **Update `ccya/engine/npc_roster.py`**: expand `_NPC_PALETTE` to 48 colors, import and use `generate_npc_color`

3. **Update `ccya/engine/seed.py`**: update palette size to 48, use `generate_npc_color`

4. **`ccya/state/npcs.py`**: on new NPC creation (`is_new` block), add `updates["color"] = generate_npc_color(resolved_id)`

5. **`ccya/engine/turn_state.py`**: on new NPCEntry fallback creation, add `color=generate_npc_color(cu.id)`

6. **`ccya/models/state.py`**: add optional `color: str | None = None` to `PC` and `InventoryItem` models

7. **New-game setup** (`seed.py`): assign `color=generate_pc_color()` on PC, `color=generate_item_color(item.id)` on inventory items

### Phase 2: JavaScript — highlight aware of stored colors

1. **`ccya/static/game-utils.js`**:
   - Add `_entityColor(entity_type, id)` function: hashes `(entity_type, id)` via same algorithm as Python (djb2 variant, entity-specific offset) into entity-specific palette
   - Expand global palettes: `_NPC_PALETTE` to 48 entries, add `_PC_PALETTE` and `_ITEM_PALETTE`
   - Update `_highlightEntities`: use `entry.color || _entityColor('npc', id)` for NPCs, `state.pc.color || _entityColor('pc', 'pc')` for PC, `item.color || _entityColor('item', item.id)` for items
   - PC and items use entity-specific palettes (green/blue hues) so they never collide with NPC palette colors

### Phase 3: CSS — entity class styling

1. **`ccya/static/app.css`**:
   - `.entity-npc { color: var(--accent-npc, some_pal_color); }` (NPCs already get inline color, CSS is fallback)
   - `.entity-pc { color: var(--accent-pc, #98c379); }` (green PC default)
   - `.entity-item { color: var(--accent-item, #61afef); }` (blue item default)
   - `.entity-location { color: var(--accent-location, #d19a66); }` (yellow/orange default)
   - These CSS-class colors serve as fallbacks when no inline color is present

### Phase 4: Data migration

- Old saves with 12-color NPC colors will preserve those colors (stored on the field)
- New NPCs discovered mid-game will get 48-color-palette colors
- No migration code needed — fields are additive

---

## Files to modify

| File | Change |
|------|--------|
| `ccya/engine/npc_color.py` | **NEW** — color generation utilities |
| `ccya/engine/npc_roster.py` | Expand palette to 48, use generators |
| `ccya/engine/seed.py` | Expand palette to 48, use generators, assign PC/item colors |
| `ccya/state/npcs.py` | Assign color on new NPC creation during extraction |
| `ccya/engine/turn_state.py` | Assign color on NPCEntry fallback creation |
| `ccya/models/state.py` | Add optional `color` field to `PC` and `InventoryItem` |
| `ccya/static/game-utils.js` | Use stored entity colors + entity-specific palettes |
| `ccya/static/app.css` | Update entity CSS class defaults |

## Risks

- **Old saves with 12-color palette**: preserved as-is (already assigned colors)
- **48-color palette backward-compatibility**: new palette adds colors; old palette colors at indices 0-11 are preserved
- **New games**: newly seeded NPCs get 48-color palette colors — no visual regression
