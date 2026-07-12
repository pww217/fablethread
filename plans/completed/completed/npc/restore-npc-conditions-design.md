# Restore NPC UI & Condition Redesign — Undo Reverts

## Purpose

Undo the regressions introduced by `f9ca751` (and partially `4faa25b`) that reverted `a21e39d`'s full implementation of the NPC UI and condition redesign design docs.

## Problem Statement

Commit `a21e39d` fully implemented both `docs/design/npc-ui-changes-design.md` and `docs/design/condition-redesign-design.md`. Subsequent commits `4faa25b` and `f9ca751` reverted large portions of this work — re-introducing removed fields (`allegiance`, `departed_summary`, `nearby_since_turn`, `last_seen` dict), removing the condition change reason from the UI, and losing the departed NPC display. The commits were billed as "fix design deviations" but the reverted changes were not called out and appear accidental.

## Constraints

- Backward compatibility is not a concern. Extra fields in saved state are silently dropped on load.
- Consolidated `bio` is KEPT (no split into bio_appearance/bio_background). This overrides that part of the design doc.
- The condition redesign prompt changes (`extract_state_system.j2`, `extract_state_user.j2`, `narrate_system.j2`) were NOT reverted and need no changes.
- The personality guard in `state/npcs.py` and `seed.py` (restored earlier this session) must be preserved.

## Non-goals

- Do NOT split `bio` into `bio_appearance`/`bio_background`. Bio stays consolidated.
- Do NOT change the condition redesign prompts (already intact).
- Do NOT change the ruling prompt (`3008766`'s changes are intentional).
- Do NOT change the thread/arc changes from `185d118` (unrelated).

## Solution

Remove the fields and features that `f9ca751` re-introduced (`allegiance`, `departed_summary`, `nearby_since_turn`, `last_seen` dict), replace with the design-doc-correct equivalents (`last_presence_turn` + `last_seen_location`, combined `departed_reason`), and restore the condition change reason display and departed NPC display in the UI. The personality guard from `4faa25b` is preserved.

## Firm decisions

1. Consolidated `bio` stays — no split.
2. `allegiance` is removed from extraction model, prompt, and merge logic (was a stub).
3. `departed_summary` is removed — `departed_reason` absorbs its text (combined format: "label — prose").
4. `last_seen` dict (turn/location_id/location_name) is replaced by `last_presence_turn: int | None` + `last_seen_location: str | None`, matching `a21e39d`'s design.
5. `nearby_since_turn` is removed — `last_presence_turn` already covers nearby presence timing.
6. Auto-demotion from nearby→known uses `last_presence_turn` (same logic as `nearby_since_turn`, just the correct field).
7. The condition change reason tooltip on the Player summary header (restored earlier this session) stays as-is with summary tooltip pattern.
8. The `LastSeenBlock` in context.py is simplified to `location_name: str` only.
9. The UI compendium tooltip shows departed_reason for departed NPCs with "X turns ago".
10. The NPC roster prompt shows `last_seen_location` with relative turns.

## Risks, Ambiguities, and Blockers

- `nearby_since_turn` removal requires turning the auto-demotion read in `turn.py:1313` to use `last_presence_turn`. The logic is identical — just different field name. Low risk.
- Existing saved games using `last_seen` dict will have that field silently ignored after the change. This is acceptable per the design doc.
- The `build_npc_roster()` function in `npc_roster.py` outputs `last_seen` and the template `_npc_roster.j2` and `_state_left.html` read it. Must switch these in lockstep.

## Status

`open`

## Phases

6 phases: model changes → state layer → engine → prompt context → prompt templates → UI templates

## Implementation — Phase 1: Model cleanup

### Context files to load
- `ccya/models.py:242-260` (CompendiumNpcUpdate)

### Detailed steps

#### Step 1.1 — Remove `allegiance` from CompendiumNpcUpdate

**File:** `ccya/models.py:248`

**What:** Delete the `allegiance` field line.

**Why:** Stub field — extracted but never stored or displayed. Design doc removes it.

**Validation:** `make check`

#### Step 1.2 — Remove `departed_summary`, update `departed_reason` docstring

**File:** `ccya/models.py:258-259`

**What:** Delete `departed_summary` field. Change `departed_reason` docstring to: `combined: "short label — prose" describing the departure`.

**Why:** `departed_summary` is never rendered. Combined field simplifies extraction and storage.

**Validation:** `make check`

### Tests to write or update

None.

## Implementation — Phase 2: State layer cleanup

### Context files to load
- `ccya/state/npcs.py:267-325` (apply_npc_scene_management field merge logic)
- `ccya/state/delta_builder.py:218-230` (location change NPC handling)

### Detailed steps

#### Step 2.1 — Remove `allegiance` write from npcs.py merge logic

**File:** `ccya/state/npcs.py:275-276`

**What:** Delete the `if comp_upd.allegiance is not None:` block.

**Why:** Field removed from model; no longer written.

**Validation:** `make check`

#### Step 2.2 — Remove `departed_summary` write from npcs.py

**File:** `ccya/state/npcs.py:324-325`

**What:** Delete the `if comp_upd.departed_summary is not None:` block.

**Why:** Field absorbed into `departed_reason`.

**Validation:** `make check`

#### Step 2.3 — Remove `nearby_since_turn` write from delta_builder.py

**File:** `ccya/state/delta_builder.py:225`

**What:** Delete the `entry["nearby_since_turn"] = ...` line.

**Why:** Dead code per design doc. `last_presence_turn` covers nearby timing.

**Validation:** `make check`

### Tests to write or update

None.

## Implementation — Phase 3: Engine layer

### Context files to load
- `ccya/engine/turn.py:1188-1204` (last_seen stamping on delta processing)
- `ccya/engine/turn.py:1305-1315` (nearby decay / auto-demotion)
- `ccya/engine/npc_roster.py:14-55` (build_npc_roster output shape)

### Detailed steps

#### Step 3.1 — Replace `last_seen` dict stamping with `last_presence_turn` + `last_seen_location`

**File:** `ccya/engine/turn.py:1188-1204`

**What:** Replace:
```python
entry["last_seen"] = {
    "turn": turn_no,
    "location_id": location.get("id", ""),
    "location_name": location.get("name", ""),
}
```
with:
```python
entry["last_presence_turn"] = turn_no
entry["last_seen_location"] = location.get("name", "")
```

Also remove `"nearby_since_turn": turn_no` from the minimal entry creation dict.

**Why:** Design doc replaces the `last_seen` dict with flat fields. Only location name is needed for display; turn is computed at render time as relative turns ago.

**Validation:** `make check`

#### Step 3.2 — Switch auto-demotion to use `last_presence_turn`

**File:** `ccya/engine/turn.py:1312-1315`

**What:** Change `nearby_since` / `nearby_since_turn` read to `last_presence_turn`.

**Why:** `nearby_since_turn` is removed. `last_presence_turn` is set at the same lifecycle point and carries identical semantics for this check.

**Validation:** `make check`

#### Step 3.3 — Update build_npc_roster to pass new fields

**File:** `ccya/engine/npc_roster.py:41-53`

**What:** Change the output dict to include `last_presence_turn` and `last_seen_location` instead of `last_seen`. Add `departed_reason` passthrough.

**Why:** Downstream templates need the new flat fields.

**Validation:** `make check`

### Tests to write or update

None.

## Implementation — Phase 4: Prompt context models

### Context files to load
- `ccya/prompts/context.py:181-204` (LastSeenBlock, NPCRosterEntryBlock)
- `ccya/prompts/context.py:260-295` (boundary models that reference NPCRosterEntryBlock)

### Detailed steps

#### Step 4.1 — Simplify LastSeenBlock

**File:** `ccya/prompts/context.py:181-186`

**What:** Replace fields with single `location_name: str`. Update docstring.

**Why:** Turn and location_id are no longer stored.

**Validation:** `make check`

#### Step 4.2 — Update NPCRosterEntryBlock

**File:** `ccya/prompts/context.py:189-204`

**What:** Replace `last_seen: LastSeenBlock | None` with `last_presence_turn: int | None` and `last_seen_location: str | None`. Update docstring.

**Why:** Templates need the new flat fields.

**Validation:** `make check`

### Tests to write or update

None.

## Implementation — Phase 5: Prompt templates

### Context files to load
- `ccya/prompts/extract_scene_system.j2:1-169` (full file — extraction schema and field rules)
- `ccya/prompts/sections/_npc_roster.j2:1-19` (narrator roster line)
- `ccya/prompts/generate_seed_system.j2` (compendium schema line ~36)

### Detailed steps

#### Step 5.1 — Remove allegiance from extraction prompt

**File:** `ccya/prompts/extract_scene_system.j2:12,33,53`

**What:** Remove `"allegiance": "faction_or_alignment"` from the JSON schema example (line 12), the field rules block (line 33), and the durable identity updates list (line 53).

**Why:** Field removed from model.

**Validation:** `grep` confirms no allegiance references remain in the file.

#### Step 5.2 — Combine departed fields in extraction prompt

**File:** `ccya/prompts/extract_scene_system.j2:42-47,119,126`

**What:**
- Replace `departed_reason` + `departed_summary` with single `departed_reason` field: `"departed_reason": "short label followed by 1-2 sentence prose describing what happened — e.g. 'killed in battle — Caught in the crossfire defending the village gates.'"`
- Remove the separate `departed_summary` guidance lines.
- Update the presence description to: `Requires departed_reason (combined label + prose).`
- Update the example format: `departed_reason: "..."`

**Why:** Combined field per design doc.

**Validation:** `make check`

#### Step 5.3 — Update NPC roster template for new fields

**File:** `ccya/prompts/sections/_npc_roster.j2:7,16`

**What:**
- Line 7: Change `n.bio` → `n.bio` (kept, no change needed).
- Line 16: Replace `n.last_seen.location_name` access with `n.last_seen_location` and add relative turns from `n.last_presence_turn`.

New rendering:
```jinja2
{%- set _ls_loc = n.last_seen_location %}{% if _ls_loc %} | last seen: {{ _ls_loc }}{% if n.last_presence_turn %} ({{ (turn_no if turn_no is defined else meta.turn) - n.last_presence_turn }} turns ago){% endif %}{% endif %}
```

**Why:** Design doc replaces absolute turn with relative turns, flat fields replace dict.

**Validation:** `make check`

#### Step 5.4 — Remove allegiance from seed generation prompt

**File:** `ccya/prompts/generate_seed_system.j2` (compendium schema line)

**What:** Remove `allegiance?: string` from the compendium NPC schema line.

**Why:** Field removed.

**Validation:** `grep` confirms no allegiance reference remains.

### Tests to write or update

None.

## Implementation — Phase 6: UI templates

### Context files to load
- `ccya/templates/_state_left.html:140-170` (compendium tooltip section)
- `ccya/templates/_state_left.html:6-40` (scene NPC section)
- `ccya/templates/_state_right.html:4-5` (Player summary tooltip — verify existing)

### Detailed steps

#### Step 6.1 — Update compendium tooltip to use new fields and show departed_reason

**File:** `ccya/templates/_state_left.html:144-165`

**What:** Replace the `last_seen` dict-based display with `last_presence_turn` + `last_seen_location`. For departed NPCs, show `departed_reason` with relative turns. For non-departed NPCs, show `last_seen_location` with relative turns.

Template logic:
```jinja2
{% set last_presence = entry.get('last_presence_turn') %}
{% set last_loc = entry.get('last_seen_location') %}
{% set is_departed = entry.get('presence') == 'departed' %}
{% if is_departed and entry.get('departed_reason') %}
<p>Last seen: {{ last_loc or 'unknown' }} — {{ entry.departed_reason }}{% if last_presence %} ({{ state.meta.turn - last_presence }} turns ago){% endif %}</p>
{% elif last_loc %}
<p>Last seen: {{ last_loc }}{% if last_presence %} ({{ state.meta.turn - last_presence }} turns ago){% endif %}</p>
{% endif %}
```

**Why:** Restores departed_reason display that was lost in `f9ca751`. Uses relative turns (design doc).

**Validation:** `make check`

#### Step 6.2 — Restore condition_change_reason tooltip on Player summary (done)

**File:** `ccya/templates/_state_right.html:5`

**What:** Confirm the Player summary tooltip (restored earlier in this session) shows condition change reason with fallback. Current expected content:
```html
<summary><span class="has-tooltip">Player{% if state.meta.last_condition_change_reason %}<div class="tooltip-body">{{ state.meta.last_condition_change_reason }}</div>{% else %}<div class="tooltip-body">No condition changes this turn</div>{% endif %}</span></summary>
```

**Why:** Design doc requires condition_change_reason in the UI, mirroring the inventory pattern.

**Validation:** Visual inspection of the file.

### Tests to write or update

None.

## Implementation — Phase 7: Restore character creator stats fix (381541c)

### Context files to load
- `ccya/server/routes.py:400-460` (new_game route, seed prep)

### Detailed steps

#### Step 7.1 — Parse pc_stats JSON, apply as hard override after seed prep

**File:** `ccya/server/routes.py:407,414-438,441-457`

**What:** Three changes:
1. Lines 414-420: After extracting `pc_stats_raw`, parse it as JSON into a dict before constructing the overrides object.
2. Lines 427-438: Do NOT fold pc_stats into hint_parts (stats are a mechanical override, not a hint). Pass `overrides=overrides` to `generate_seed()` instead of `None`.
3. Lines 441-457: After seed prep in both the static and dynamic paths, override `seed["pc"]["stats"]` with the parsed dict if available.

**Why:** `f9ca751` reverted this fix. Stats are mechanical — the LLM should not decide them. The player's exact choices must be written to state.yaml.

**Validation:** `make check`

### Tests to write or update

None.
