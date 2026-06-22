# State/Save Bugs — Issue #6

## Status
`completed`

## Phases

2 phases covering: (1) verification that thread resolution save path is correct, and (2) fixing first_seen_turn + last_seen compendium tracking bugs.

## Issue

Two sub-issues from the mini-roadmap (#6a, #6b):

**#6a**: Roadmap claims `_apply_thread_resolutions()` sets `resolution_state`/`outcome` on threads but may fail to persist them back into state. Investigation shows this is NOT a bug — data flow is correct: function returns CampaignArc → caller merges via `_merge_arc_update()` → writes both `threads[]` and `completed_threads[]` with resolution fields → `save_state()` persists to disk. If outcomes aren't appearing, root cause is likely LLM not emitting `thread_resolve`, or thread ID mismatch (warning logged at line 474-478).

**#6b**: The `seen` field is underpopulated due to two bugs:
1. **`first_seen_turn` is NEVER set by the engine.** Model comment says "set by engine on initial entry creation" but no code does it. Compactor defaults to 0, compact_user.j2 shows `T0`.
2. **`last_seen` only stamped for NPCs in `delta.compendium_npc_update`.** If an NPC is present in a scene but the LLM doesn't emit them in compendium update (extraction omission), their last_seen goes stale. Also, new NPCs created via extraction never get initial last_seen set.

## Solution

Phase 1: Verify and document that #6a is not a code bug — confirm data flow is correct by reading the relevant source lines. No changes needed for thread resolution save path.

Phase 2: Fix both first_seen_turn and last_seen bugs in `apply_npc_scene_management()` (state/npcs.py). When creating a new NPC entry, initialize both fields with current turn/location info. This ensures all compendium NPCs have visible seen history regardless of whether they appear in extraction deltas on every turn.

## Firm decisions

1. **Thread resolution save path is correct.** No code changes for #6a. If outcomes are missing from state, it's a prompt issue (LLM not emitting thread_resolve) or ID mismatch — both outside scope of this plan.
2. **first_seen_turn and last_seen initialization belongs in `apply_npc_scene_management()`.** This is the single point where new NPCs enter the compendium. Both fields should be set at creation time with current turn number and location info from state.
3. **No changes to extraction prompt for last_seen.** Strengthening scene extractor to always emit all present NPCs is a separate concern (prompt quality). The code fix ensures that when extraction DOES work, the data is properly initialized.

## Non-goals

- Do NOT modify thread resolution save path — it works correctly
- Do NOT add auto-update pass for last_seen on presence=present NPCs — scope creep
- Do NOT change compact_user.j2 rendering logic — first_seen_turn fix makes defaults irrelevant
- Do NOT modify narrator templates or prompt quality — separate issue category

## Risks, Ambiguities, and Blockers

**Ambiguity**: What turn number to use for initial last_seen? Decision: use `current_turn` from delta_builder.py (0-based, matching condition stamps and compactor default of 0). The model field is set by engine anyway per its comment.

**Risk**: Existing NPCs in saved states have no first_seen_turn — they'll show as "T0" until next compaction re-processes them. This is acceptable; it's a one-time fix for future data, not retroactive correction of historical state.

## Implementation — Phase 1: Verify thread resolution save path (no changes)

### Context files to load
- `ccya/engine/turn.py` lines 421-530 (`_apply_thread_resolutions`)
- `ccya/engine/turn.py` lines 1361-1370 (caller in run_turn)
- `ccya/state/delta_builder.py` lines 53-74 (`_merge_arc_update`)

### Detailed steps

#### Step 1.1 — Verify data flow is correct

**File:** `ccya/engine/turn.py`, `ccya/state/delta_builder.py`

**What:** Read the three code sections above and confirm:
- `_apply_thread_resolutions()` returns a CampaignArc with updated completed_threads containing resolution_state + outcome fields (non-None values)
- Caller at run_turn line 1362 checks for non-None return, then calls _merge_arc_update(state["arc"], resolved_arc)
- _merge_arc_update writes both `threads[]` and `completed_threads[]` via model_dump(exclude_none=True), which preserves resolution_state + outcome

**Why:** The roadmap description claims these fields "may fail to persist" but the code path is: return CampaignArc → conditional merge into state dict → save_state() persists entire state. There's no break in this chain unless storyteller_result.thread_resolve is empty (line 433 returns None) or thread IDs don't match (warning logged, skip).

**Validation:** No changes needed. Document findings as confirmation that #6a is not a code bug. Update mini-roadmap accordingly.

### Tests to write or update
None — no code changes.

### REPOMAP updates required
Update mini-roadmap.md: mark 6a as "Verified correct, no code change needed" with explanation of data flow.

## Implementation — Phase 2: Fix first_seen_turn + last_seen compendium tracking

### Context files to load
- `ccya/state/npcs.py` lines 90-147 (`apply_npc_scene_management`)
- `ccya/models.py` line 221 (CompendiumNpcUpdate.first_seen_turn field definition)
- `ccya/engine/turn.py` lines 1338-1346 (last_seen stamping logic for reference)

### Detailed steps

#### Step 2.1 — Initialize first_seen_turn and last_seen on new NPC creation

**File:** `ccya/state/npcs.py`, function `apply_npc_scene_management()` around line 94-96

**What:** Add initialization for both fields when a NEW entry is created. Detect new vs existing by checking if resolved_id was NOT already in comp before setdefault:

```python
# Before line 94 (inside the "if scene_result.compendium_npc_update:" block):
comp = state.setdefault("compendium", {}).setdefault("npcs", {})

for comp_upd in scene_result.compendium_npc_update:
    ...
    is_new = resolved_id not in comp
    entry = comp.setdefault(resolved_id, {})
    
    if is_new and current_turn_no is not None:
        entry["first_seen_turn"] = current_turn_no  # 0-based, matches compact_user.j2 convention (T{{ npc.first_seen_turn }})
        location = state.get("location", {})
        entry["last_seen"] = {
            "turn": current_turn_no,
            "location_id": location.get("id", ""),
            "location_name": location.get("name", ""),
        }

# Continue with existing field-setting logic (lines 119-146) as-is.
```

**Why:** The model comment on first_seen_turn says "set by engine on initial entry creation" but no code does it. This is the single point where new NPCs enter the compendium — all paths go through apply_npc_scene_management(). Setting both fields at creation ensures:
- compact_user.j2 shows correct `T{{ npc.first_seen_turn }}` instead of T0 for newly created NPCs
- last_seen is initialized so newly created NPCs aren't "invisible" until next extraction update

**Validation:** 
```bash
uv run ruff check ccya/state/npcs.py && uv run mypy ccya/state/npcs.py
```

#### Step 2.1b — Update call site to pass current_turn_no

**File:** `ccya/state/delta_builder.py`, function `apply_delta()` around line 298

**What:** Pass the existing local variable `current_turn` (defined at line 253 as `(state.get("meta") or {}).get("turn", 0)`) to the call:

```python
# Line 297-304, change from:
    state = apply_npc_scene_management(state, SceneExtractResult(
        compendium_npc_update=delta.compendium_npc_update or [],
        scene_tags=delta.scene_tags or [],
        scene_tagline=delta.scene_tagline,
        location_change=delta.location_change,
        location_description=delta.location_description,
    ))

# To:
    state = apply_npc_scene_management(state, SceneExtractResult(
        compendium_npc_update=delta.compendium_npc_update or [],
        scene_tags=delta.scene_tags or [],
        scene_tagline=delta.scene_tagline,
        location_change=delta.location_change,
        location_description=delta.location_description,
    ), current_turn_no=current_turn)
```

**Why:** The function parameter `current_turn_no` defaults to None. Without passing it from the call site, the guard `if is_new and current_turn_no is not None:` never fires and initialization is skipped entirely. The local variable `current_turn` at line 253 is already computed as `(state.get("meta") or {}).get("turn", 0)` — a 0-based turn number consistent with condition stamps (`added_turn`) and the compactor default of 0 for first_seen_turn.

**Validation:**
```bash
uv run ruff check ccya/state/delta_builder.py && uv run mypy ccya/state/delta_builder.py
```

#### Step 2.2 — Verify no other code depends on first_seen_turn being absent or None

**File:** `ccya/engine/compactor.py` line 206, all references to first_seen_turn across repo

**What:** Grep for all uses of first_seen_turn and verify none expect it to be missing initially. The compactor defaults to 0 if not present — this is a safe fallback that will no longer trigger (since we always set it), but won't break anything.

**Why:** Ensure the fix doesn't change behavior for existing NPCs in saved states who lack first_seen_turn. They'll continue using the compact default of 0 until compaction re-processes them, then get their actual value from state.

**Validation:**
```bash
rg "first_seen_turn" --type py -n && rg "last_seen" ccya/state/npcs.py -n
```

### Tests to write or update
None — tests temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
Update mini-roadmap.md: mark 6b as DONE with commit reference, note that first_seen_turn is now properly initialized on NPC creation and last_seen is set for all new NPCs. Update line ~70 to reflect fix scope.
