# NPC UI & Model Changes

## Required Changes

1. **`condition_change_reason`** — Add to the "Player" header tooltip in the right-side PC panel (`_state_right.html`). Show always if `state.meta.last_condition_change_reason` is populated. Pattern already exists for Inventory header.

2. **`departed_reason` + `departed_summary`** — Combine into one field: departed_reason. Render in compendium/NPC tooltip when NPC `presence == "departed"`. Show `Last Seen: [last_seen_location] - [departed_reason] (X turns ago)`

3. **`last_seen`** — Remove from UI entirely. In the engine, compute "X turns ago" as `current_turn - last_presence_turn` where `last_presence_turn` is the last turn the NPC was `present` or `nearby`. Surface this in the compendium tooltip as "last seen at [location] (N turns ago)" for departed NPCs, alongside the departed info. Surface the `last_presence_turn` value in the narrator prompt so the LLM knows when to reintroduce characters.

4. **`bio`** — Split into two sub-fields: `bio.background` (their short backstory, personality, reputation — what it mostly is now) and `bio.appearance` (physical presentation in the world — bearing, posture, expression, distinctive features). `position` remains a separate top-level field (physical space they occupy). This will require prompt changes, too.

5. **`allegiance`** — Currently extracted by the LLM but **never stored** (`state/npcs.py:275` silently drops it because `CompendiumEntry` has no `allegiance` field). Remove from extraction prompts until it's actually needed. Do not add to the model.

6. **`first_seen_turn`, `nearby_since_turn`, `departed_turn`** — Evaluate usefulness:
   - `first_seen_turn`: Used in `narrate_user.j2` as `T{{ npc.first_seen_turn }}` for display. Keep for now.
   - `nearby_since_turn`: Set in `state/npcs.py:319` and `delta_builder.py:225`, read in `turn.py:1294` but the value is not surfaced anywhere. Dead code. Remove from extraction and model.
   - `departed_turn`: Set on first `presence: "departed"`. Used for 3-turn auto-archive. Keep — it's needed for the "X turns ago" computation.

---

## Current State (Research Findings)

### NPC Model Fields (`CompendiumEntry` in `ccya/models.py:240–273`)

| Field | Type | Extracted? | Stored? | Displayed? | Notes |
|-------|------|-----------|---------|------------|-------|
| `id` | str | yes | yes | compendium list | canonical key |
| `name` | str | yes | yes | yes | |
| `title` | str | yes | yes | yes | |
| `bio` | str | yes | yes | yes | currently single string; split planned |
| `bond` | str | yes | yes | no | |
| `presence` | str | yes | yes | yes | present/nearby/known/departed |
| `notes` | str | yes | yes | no | scene-specific; cleared on departure |
| `motivation` | str | yes | yes | no | |
| `fear` | str | yes | yes | no | |
| `leverage` | str | yes | yes | no | |
| `personality` | str | yes | yes | no | archetype id |
| `aliases` | list[str] | yes | yes | no | |
| `allegiance` | str | yes | **no** | no | silently dropped at `npcs.py:275`; remove from extraction |
| `position` | str | yes | yes | yes | spatial position (keep as top-level) |
| `first_seen_turn` | int | no | yes | in narrate prompt | set by engine on entry creation |
| `nearby_since_turn` | int | no | yes | no | dead code; remove |
| `departed_turn` | int | no | yes | no | used for auto-archive; keep; needed for "X turns ago" |
| `departed_reason` | str | yes | yes | yes (roster only) | |
| `departed_summary` | str | yes | yes | **no** | combine with `departed_reason` |
| `last_seen` | dict | no | yes | yes (UI) | `{turn, location_id, location_name}`; remove — replace with computed "X turns ago" |

### `condition_change_reason` — Where It Lives

Not an NPC field. It lives on `StateExtractResult` (`ccya/models.py:326`) and is stored in `state.meta.last_condition_change_reason`. It is the reason the PC's condition changed this turn.

Referenced in:
- `ccya/models.py:326` — model field
- `ccya/state/io.py:85` — default `None`
- `ccya/prompts/sections/_narrate_user.j2` — surfaced to narrator
- `ccya/templates/_state_right.html` — NOT currently in tooltip (add it)

### `departed_reason` vs `departed_summary`

Both are extracted by the LLM (extraction prompt schema lines 42–47) and both are stored in `CompendiumEntry`. However, `departed_summary` is **never rendered in the UI** — only `departed_reason` appears in the compendium roster line (`_npc_roster.j2:7`). The `departed_summary` exists but is invisible to the player.

Extraction prompt (`ccya/prompts/extract_scene_system.j2:42–47`):
```
"departed_reason": "short label — required when presence is departed"
"departed_summary": "1-2 sentence prose — required when presence is departed"
```
Combine into one field with the summary merged in.

### `last_seen` Current Usage

Engine sets it at `state/npcs.py:257–261`:
```python
entry["last_seen"] = {
    "turn": current_turn_no,
    "location_id": ...,
    "location_name": ...
}
```

UI renders it at `_state_left.html`:
- Line 33: `"last_seen": {{ ...turn number... }}` (presence badge tooltip)
- Lines 148–149: `{{ n.last_seen.turn }}` and `{{ n.last_seen.location_name }}` (detail section)
- Line 162: `{{ n.last_seen.turn }}` (deputized section)

The `last_seen` dict is built from the last turn the NPC was `present` or `nearby` (`turn.py:1189–1193`), but the actual turn number is stored in `last_seen.turn` rather than being computed at render time.

The "X turns ago" value is never computed or displayed.

### `bio` Current Extraction Instruction

From `ccya/prompts/extract_scene_system.j2:31`:
> "TWO SENTENCES: (1) appearance and demeanor — how they are physically presented, bearing/posture/expression. (2) personality traits or tangible facts about who they are as a person — background details, habits, reputation that define them."

The two-aspect structure is already intended; formalizing as `bio.background` / `bio.appearance` makes it explicit and plumbs it through to the UI.

### `allegiance` Is a Stub

- Extracted by LLM (`extract_scene_system.j2:33`: `"allegiance": "faction_or_alignment"`)
- `CompendiumNpcUpdate` model has it (`models.py:248`)
- `state/npcs.py:275` writes it to `entry["allegiance"]` but `CompendiumEntry` has no `allegiance` field — Pydantic silently ignores the extra field
- **NPC allegiance is never stored or displayed anywhere**
- PC allegiance (`state.pc.allegiance`) is real: used in narrator prompts to show "— your faction" next to friendly factions (`narrate_user.j2:25`)

Remove `allegiance` from `CompendiumNpcUpdate` and extraction prompts until it's needed.

### `first_seen_turn`, `nearby_since_turn`, `departed_turn`

| Field | Set | Read | Used |
|-------|-----|------|------|
| `first_seen_turn` | `state/npcs.py:255` (on creation) | `narrate_user.j2` as `T{{ npc.first_seen_turn }}` | Displayed in narrator prompt. Keep. |
| `nearby_since_turn` | `state/npcs.py:319`, `delta_builder.py:225` | `turn.py:1294` | Value read but never surfaced. Dead code. Remove. |
| `departed_turn` | `state/npcs.py:315` (on first departed) | `turn.py:1304` | Auto-archive check (`> 3 turns`). Keep; needed for "X turns ago" computation. |

---

## Files to Change

### Extraction / Prompts
- `ccya/prompts/extract_scene_system.j2` — split `bio` into `bio.background`/`bio.appearance`; combine `departed_reason`+`departed_summary`; remove `allegiance`; remove `nearby_since_turn`
- `ccya/prompts/sections/_npc_roster.j2` — update for new field structure
- `ccya/prompts/generate_seed_system.j2` — update `bio` field

### Models
- `ccya/models.py` — split `bio` into sub-model; remove `allegiance` from `CompendiumNpcUpdate`; remove `nearby_since_turn` from `CompendiumEntry`; remove `last_seen`; add `last_presence_turn` (int, for "X turns ago" computation)

### Engine / State
- `ccya/state/npcs.py` — stop writing `last_seen`; stop writing `nearby_since_turn`; add `last_presence_turn` tracking; stop reading/writing `allegiance`
- `ccya/state/delta_builder.py` — remove `nearby_since_turn` assignment
- `ccya/engine/turn.py` — remove `last_seen` population; compute and surface `last_presence_turn`; add `last_presence_turn` to `NPCRosterEntryBlock`
- `ccya/state/io.py` — remove `last_seen` from default state
- `ccya/prompts/context.py` — update `NPCRosterEntryBlock`

### UI Templates
- `ccya/templates/_state_right.html` — add `condition_change_reason` to Player header tooltip
- `ccya/templates/_state_left.html` — update departed NPC rendering (combine departed_reason+summary; replace `last_seen` with "X turns ago")
- Any template showing compendium NPC details

---

## Deprecation / Migration Note

Removing `last_seen`, `nearby_since_turn`, and `allegiance` from stored state is safe for saves in progress — `CompendiumEntry` uses Pydantic and extra fields written to dicts are silently dropped on load. Existing saves that have these fields will lose them on next save. `departed_summary` existing in saves is fine — it will be ignored once combined.
