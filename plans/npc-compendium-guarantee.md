# Plan: New-NPC Compendium Guarantee

## Problem

`_known_characters_for_extract` pulls up to 10 NPCs by LRU order. NPCs present in the *current scene* can be evicted from context by less-recent but more-frequently-seen NPCs. A newly-introduced NPC with no compendium entry gets zero context — the extractor has no stable identity to attach extracted facts to.

This causes:
- Extractor creates a duplicate NPC entry instead of enriching the existing one
- First-encounter NPCs get no compendium row, so their traits are never persisted
- `present_npcs` references IDs the extractor has never seen

## Fix

### Guarantee: current scene NPCs always in context

In `_known_characters_for_extract()` (or equivalent), after LRU selection:

```python
# Always include full rows for NPCs currently in the scene
scene_npc_ids = set((state.get("scene") or {}).get("present_npcs") or [])
selected_ids = {npc["id"] for npc in lru_selected}
missing_scene_ids = scene_npc_ids - selected_ids

for npc_id in missing_scene_ids:
    row = compendium.get(npc_id)
    if row:
        lru_selected.append(row)
    else:
        # New NPC — emit a placeholder row so extractor knows to create it
        lru_selected.append({"id": npc_id, "name": npc_id, "_new": True})
```

The `_new` flag in the placeholder row signals the extractor that this NPC has no compendium entry yet and one should be created from the narration.

### Extractor prompt guidance

Add to `extract_state_system.j2` (or progress equivalent):

> If a character appears in the known characters list with `_new: true`, they are newly introduced this turn. Create a full compendium entry for them from the narration: name, apparent role, first impressions, any stated relationships. Do not leave `_new` NPCs without entries.

### Injection format

Current compendium rows are rendered as `id + name` only in some contexts. For scene-present NPCs, render the full row (or the placeholder). The token cost is bounded — `present_npcs` is typically 1–4 NPCs.

## Notes

- This is distinct from the NPC alias dedup work. That prevents clones; this prevents data loss on first encounter.
- `present_npcs` should always be a list of IDs, not names. If any are names, that's a separate bug to fix first.
- After this change, the LRU selection still applies to background NPCs not in the current scene.
