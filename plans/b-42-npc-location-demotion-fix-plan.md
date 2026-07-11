# Plan: B-42 — NPC presence does not decay after location change

## Design Reference

- Design: none (chat-consensus root cause analysis)
- Ticket: `roadmap/bugs/B-42-npc-presence-does-not-decay-after-location-change.md`

## Problem Statement

When a player changes location, non-party NPCs at the old location are demoted to `nearby` by the location-change handler (`delta_builder.py:225-229`), but two bugs prevent this demotion from sticking: (1) `turn_state.py:529` unconditionally stamps `last_seen_location` to the current location for all mentioned NPCs, overwriting their old location and causing future demotion checks to fail; (2) `state/npcs.py:97-98` compendium updates with `presence: present` override the demotion in the same pipeline. The extractor prompt (`extract_scene_system.j2`) lacks `last_seen_location` as an output field, so the LLM can't explicitly indicate if an NPC followed the player or stayed behind.

## Firm decisions (from design)

1. Only stamp `last_seen_location` for new NPCs — existing NPCs keep their tracked location.
2. When `compendium_npc_update` sets `presence: present` but the NPC was at a different location, demote to `nearby` instead of overriding the demotion.
3. Add `last_seen_location` to the extractor output schema so the LLM can explicitly indicate location-following.
4. Strengthen the narrator instruction about nearby NPCs on `narrate_system.j2:39`.

## Scope

- One phase — four changes, all touching independent files with no cross-dependencies (except the stam
- Phase 1 touches: `turn_state.py`, `state/npcs.py`, `extract_scene_system.j2`, `narrate_system.j2`

## Status

`implemented`

---

## Phase 01: NPC location demotion fix

### Depends on

None

### Context files to load

- `ccya/engine/turn_state.py:516-530` — stamping loop for `last_presence_turn` and `last_seen_location`
- `ccya/state/npcs.py:60-122` — `apply_npc_scene_management()` compendium NPC update handler
- `ccya/prompts/extract_scene_system.j2:17-22,41-57` — extractor output schema and presence rules
- `ccya/prompts/narrate_system.j2:39` — narrator NPC RE-USE instruction
- `ccya/engine/npc_roster.py:96` — `presence_filter` parameter in `build_npc_roster`

### What changes

**1. `turn_state.py:526-530` — only stamp `last_seen_location` for new NPCs**

Currently the loop stamps `last_seen_location = location.name` for EVERY NPC in `compendium_npc_update`, overwriting their tracked location. Fix: only set `last_seen_location` when the NPC is new; for existing NPCs only update `last_presence_turn`.

**2. `state/npcs.py:97-98` — respect old-location demotion in compendium updates**

When `compendium_npc_update` sets `presence: present` but the NPC's old `last_seen_location` differs from the current location, demote to `nearby` instead of setting `present`. This prevents the extractor from overriding the location demotion.

**3. `extract_scene_system.j2:17-22` — add `last_seen_location` to extractor output schema**

Add `last_seen_location` as an optional output field so the LLM can explicitly set the location when an NPC follows the player to a new area. Add instructions for when to set it vs. leave it unset.

**4. `narrate_system.j2:39` — strengthen nearby NPC narrate rule**

Strengthen the existing instruction about nearby NPCs to make it explicit that the roster is authoritative and nearby NPCs must never be written into narration.

### Before (current):

**`turn_state.py:526-530`:**
```python
state = state.update_npc(
    cu.id,
    last_presence_turn=turn_no,
    last_seen_location=location.name or "",
)
```

**`state/npcs.//:**
```python
if comp_upd.presence is not None:
    updates["presence"] = comp_upd.presence
    if comp_upd.presence == "present":
        state = touch_compendium_order(state, resolved_id)
```

**`extract_scene_system.j2:17-22`:**
```json
{
   "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "motivation": "...", "fear": "...", "leverage": "...", "tie": "...", "presence": "present|nearby|known|departed", "position": "..."}]
}
```

**`narrate_system.j2:39` (already exists, needs strengthening):**
```
NEARBY NPCs are in the general area but NOT in the scene — do not write them into narration.
```

### After:

**`turn_state.py:526-530`:**
```python
if entry is None:
    # new NPC — stamp both fields
    state = state.add_npc(cu.id, NPCEntry(
        name=cu.id.replace("_", " ").title(),
        presence=NpcPresence.NEARBY,
        last_seen_location=location.name or "",
        last_presence_turn=turn_no,
    ))
else:
    # existing NPC — only update last_presence_turn, NOT last_seen_location
    state = state.update_npc(
        cu.id,
        last_presence_turn=turn_no,
    )
```

**`state/npcs.py` additions around line 95-98:**
When setting `presence: present` on an existing NPC, check if their old `last_seen_location` differs from current `state.location.name`. If it does, demote to `nearby` instead:

```python
old_presence = entry.presence if entry else None
old_last_seen = entry.last_seen_location if entry else None
current_loc = state.location.name or ""
if is_new:
    updates["last_seen_location"] = current_loc
else:
    # For existing NPCs — don't overwrite last_seen_location unless extractor explicitly set it
    if comp_upd.last_seen_location is not None:
        updates["last_seen_location"] = comp_upd.last_seen_location

if comp_upd.presence is not None:
    # Guard: don't let extractor override demotion for NPCs at old locations
    if comp_upd.presence == "present" and not is_new and old_last_seen and old_last_seen != current_loc:
        upd_pres = NpcPresence.NEARBY
    else:
        upd_pres = comp_upd.presence
    updates["presence"] = upd_pres
    if upd_pres == "present":
        state = touch_compendium_order(state, resolved_id)
```

**`extract_scene_system.j2` additions to output schema:**
```json
{
   "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "motivation": "...", "fear": "...", "leverage": "...", "tie": "...", "presence": "present|nearby|known|departed", "position": "...", "last_seen_location": "..."}]
}
```

Plus instructions in the "Presence levels" / "How to use compendium_npc_update" section:

```
- `last_seen_location`: Only set when the narration explicitly places the NPC in a location different from their previous `last_seen_location`. Omit if the NPC is at their last known location — the engine will handle location tracking. This field is how indicate an NPC followed you to a new scene (e.g., from a conversation earlier).
```

**`narrate_system.j2:39`:**
Replace:
```
NEARBY NPCs are in the general area but NOT in the scene — do not write them into narration.
```
With:
```
**NEARBY NPCs are in the general area but NOT in the scene — DO NOT write them into narration.** The `## Characters` roster is your authoritative source for who is in the scene. If an NPC has `presence: nearb
by`, they are NOT in the scene. `KNOWN` NPCs may appear in dialogue, backstory, or plot-relevant narration. Mentioning known/recently seen NPCs adds depth and continuity.
```

### Why

**Change 1** (`turn_state.py`) — prevents automatic stamming of wrong locations for extracted NPCs. If an NPC was at Central Farmstead and the narrator mentions them there, their `last_seen_location` stays Central Farmstead. Demotion checks (which compare `entry.last_seen_location != current_location.name`) fire correctly.

**Change 2** (`state/npcs.py`) — prevents compendium updates from overriding location demotion. When the extractor outputs `presence: present` for an NPC at the old location, the code demotes to `nearby` instead, respecting the demotion. The only way the LPC to front `presence: present` is by explicitly following them.

**Change 3** (`extract_scene_system`) — gives the LLM a mechanism to signal "NPC followed me" by setting `last_seen_location`. When the narrator shows an NPC genuinely moving to a new location (e.g., "Daniel Meyer follows you to the Holding Cells"), the LLM sets `last_seen_location: Holding Cells` and the demotion doesn't fire because old_ls == new_ls.

**Change 4** (`narrate_system`) — reinforces the existing instruction with authoritative language so the narrator treats the roster as gospel. Even if data bugs occur, the narrator won't compensate by inventing NPCs into the scene.

### Validation

- `make check` passes (lint + typecheck)
- `ev.py turn 15 --json --save-dir saves/cordyceps-year-twenty-2026-07-10` shows:
  - Daniel Meyer at T15 END: `presence: nearby`, `last_seen_location: Central Farmstead`
  - `farm_laborers` at T15 END: `presence: nearby`, `last_seen_location: Central Farmstead` (unchanged — they were already correct)
- `ev.py turn 16 --json --save-dir saves/cordyceps-year-twenty-2026-07-10` shows:
  - Daniel Meyer at T16 END: still `presence: nearby` (no re-promotion, no compendium update mentioned T16 explicitly placed in narration)
  - Narration does NOT mention Daniel Meyer
- `ev.py turn 17 --json --save-dir saves/cordyceps-year-twenty-2026-07-10` shows:
  - Daniel Meyer at T17 END: `nearby` ~ T16 turn
- `ev.py trace npc_updates --save-dir saves/cordyceps-year-twenty-2026-07-10` — Daniel Meyer demoted to nearby at T15, stays nearby through T17
- `ev.py compendium 17 --save-dir saves/cordyceps-year-twenty-2026-07-10` — match section checks
- All checkers pass
- Manual inspection: save `saves/cordyceps-year-twenty-2026-07-10` no new turns

---

## Documentation updates

- `docs/architecture/step2c-record.md` — update NPC compendium data shape: `last_seen_location` tracking behavior after location change
- `docs/architecture/step2d-world.md` — update NPC presence lifecycle, demotion behavior, and `last_seen_location` stamping rules
- `docs/repomap.md` — update `ccya/engine/turn_state.py` stamping loop signature, `ccya/state/npcs.py` compendium update handler
- `AGENTS.md` — no changes needed (no build/lint/run changes)
