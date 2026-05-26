# NPC Compendium & Seed Generation Plan

## Status
`completed` (Phase 02 done)

## Phases

3 phases covering: (1) model field additions + NPC cap removal, (2) seed generation prompt/schema updates, (3) UI compendium tooltip reformat. Each phase independently executable with no prior context needed beyond its own file list.

## Issue

The seed LLM is prohibited from assigning motivation/fear/leverage to NPCs at seed time, yet these fields drive NPC behavior in narration pipelines and are populated at runtime via extraction — creating a gap where seed-generated NPCs start emotionally flat compared to runtime-discovered ones. Additionally, the hard NPC cap (8) creates mechanical pressure that conflicts with narrative pacing, and the compendium tooltip format lacks visual separation between field categories (bio vs motivation vs bond).

## Solution

Add explicit `motivation`, `fear`, `leverage` fields to CompendiumEntry model; remove NPC_SCENE_CAP enforcement and location-clear behavior from engine; update seed prompt to allow these fields on key NPCs with flexible arc-informed assignment guidance (replacing rigid personal-stakes/external-pressure pattern); reformat compendium tooltip with blank-line separators, motivation field inclusion, notes exclusion.

## Firm decisions

1. **Seed generation order: Arc before NPCs.** Move Campaign Arc above Compendium NPCs in `generate_seed_system.j2` so NPC bonds reference actual campaign goals rather than generic patterns (design #1).
2. **Allow motivation/fear/leverage at seed time.** Remove prohibition from lines 11, 203 of `generate_seed_system.j2`; add explicit fields to TypeScript-style seed output schema at line ~105; update CompendiumEntry model with three optional string fields (design #2).
3. **Fear/leverage hidden from UI.** Do NOT render fear or leverage in `_state_left.html` compendium tooltip; motivation IS rendered (design decision table row 93).
4. **Compendium tooltip format: Bio → Motivation → Bond → Last Seen with blank-line separators.** Each field separated by `\n\n`; each shown only if non-empty (conditional rendering); bio unlabelled prose, motivation/bond use bold label prefix (`**Motivation:**`, `**Bond:**`), last_seen uses plain "Last seen:" label (design #3).
5. **Remove NPC cap.** Delete `NPC_SCENE_CAP = 8`, `_enforce_npc_present_cap()`, and its call in `apply_npc_scene_management()` via `state/npcs.py:192`; delete `clear_present_npcs_on_location_change()` and its invocation on location change (design #4, #6).
6. **Soften seed NPC count.** Line 11 becomes flexible guidance; `npc_count_override` parameter controls exact number when >0 (value of 0 means seed uses judgment); default stays at 2 but is overridable (design #5).
7. **Scene NPC ideal: 1-4 present, pressure to exit above that.** Add soft narrative guidance to seed prompt only; engine does NOT track or enforce NPC count at runtime (design #6).
8. **Seed "key NPC" identification.** No formal definition — assign motivation/fear/leverage to whichever NPCs have personal ties or major story roles (design #7, #9 above for behavioral metadata distinction).
9. **Compendium tooltip excludes notes field.** Notes appear inline only on scene card NPCs; NOT rendered in compendium tooltips (design #10).

## Non-goals

- Do NOT change runtime extraction pipeline (`extract_scene_system.j2:27-43`) — it already populates motivation/fear/leverage at runtime.
- Do NOT add new presence types beyond "present" and "known".
- Do NOT touch `_npc_roster.j2` (LLM-facing NPC roster context) or `build_npc_roster()` in `ccya/engine/npc_roster.py`.
- Do NOT change compaction pipeline behavior for NPCs.

## Risks, Ambiguities, and Blockers

- **Seed TypeScript schema must include motivation/fear/leverage.** If only prohibition is removed but schema (line ~105) stays unchanged, LLM may not emit these fields — it treats its own schema as contract. This blocks execution if missed.
- **`apply_npc_scene_management()` docstring references NPC_SCENE_CAP** (line 136). Must update or remove that reference when deleting the constant.
- **No state migration needed.** Existing saved games with compendium entries lacking motivation/fear/leverage will continue to work — these fields are optional on all models (`extra="allow"` stays).

## Implementation — Phase 01: Model + Cap Removal

### Context files to load
- `ccya/pack.py` (lines 44-52)
- `ccya/state/npcs.py` (full file, focus on lines 54-78, 121-127, 136, 192)
- `ccya/state/delta_builder.py` (lines 239-246, 334-342)
- `ccya/eval/universal_asserts.py` (lines 452-472, 968-976)

### Detailed steps

#### Step 01.1 — Add motivation/fear/leverage to CompendiumEntry model

**File:** `ccya/pack.py:44-52`

**What:** Insert three explicit optional string fields after the existing `notes` field (line 51), before the closing blank line and class definition on line 54. Fields go between `notes` and `SeedCompendium`:
```python
motivation: str | None = None     # what NPC fundamentally wants (UI-visible in compendium tooltip)
fear: str | None = None           # what NPC is most afraid of (state-only, not UI-visible)
leverage: str | None = None       # what NPC can offer/threaten/withhold (state-only, not UI-visible)
```

**Why:** Explicit field declarations prevent Pydantic v2 strict-mode issues with undocumented extra fields from seed LLM or extraction. These are now part of the public contract, not implicit `extra="allow"` behavior. Note: field order within CompendiumEntry doesn't affect Pydantic validation (Pydantic uses field names, not position), but placing them after existing fields keeps the model readable and consistent with how seed LLM output maps to model fields.

**Validation:** No shell command needed — verify by reading file that three new lines appear between `notes` (line 51) and class `SeedCompendium` (line 54).

#### Step 01.2 — Delete NPC_SCENE_CAP constant

**File:** `ccya/state/npcs.py:54`

**What:** Remove line 54 entirely (`NPC_SCENE_CAP = 8`). No replacement needed — cap is removed, not replaced with a different value.

**Why:** Hard caps create mechanical pressure that conflicts with narrative pacing (design #6 above). Engine no longer evicts NPCs based on count thresholds.

#### Step 01.3 — Delete _enforce_npc_present_cap() function

**File:** `ccya/state/npcs.py:57-78`

**What:** Remove the entire `_enforce_npc_present_cap()` function (lines 57-78). This is a private helper (`_` prefix) with no callers outside this file.

**Why:** Function enforces NPC_SCENE_CAP which is being deleted (step 01.2 above). No replacement needed — engine no longer evicts NPCs by count.

#### Step 01.4 — Delete clear_present_npcs_on_location_change() function

**File:** `ccya/state/npcs.py:121-127`

**What:** Remove the entire `clear_present_npcs_on_location_change()` function (lines 121-127). This private helper has one caller in delta_builder.py:245-246.

**Why:** Not all location changes mean NPCs leave with you (design #6 above). Let LLM handle presence transitions via narration cues, not blanket resets.

#### Step 01.5 — Remove _enforce_npc_present_cap() call from apply_npc_scene_management()

**File:** `ccya/state/npcs.py:192`

**What:** Delete line 192 (`_enforce_npc_present_cap(comp)`). Read the full docstring (lines 134-137) and rewrite it to remove all references to NPC_SCENE_CAP. Change "NPC_SCENE_CAP is enforced here" → "Compendium entries are merged into state." Ensure no stale references remain in the three-line docstring block.

**Why:** The function being deleted in step 01.3 above has no callers outside this file; removing its call completes the cap removal for `apply_npc_scene_management()`.

#### Step 01.6 — Remove clear_present_npcs_on_location_change() call from delta_builder.py

**File:** `ccya/state/delta_builder.py:245-246`

**What:** Delete lines 245-246 (the import and function call). The location change branch should keep the state.location update (lines 240-243) but no longer clear NPC presence.

```python
# DELETE these two lines:
from ccya.state.npcs import clear_present_npcs_on_location_change
clear_present_npcs_on_location_change(state.setdefault("compendium", {}).setdefault("npcs", {}))
```

**Why:** Function being deleted in step 01.4 above; location changes no longer automatically evict present NPCs (design #6 above).

#### Step 01.7 — Remove check_npc_scene_cap() from eval auto-checkers

**File:** `ccya/eval/universal_asserts.py`

**What:** Delete the entire `check_npc_scene_cap()` function (lines 452-472) and remove it from the `run_all_universal_asserts()` call list on line 976. The assertion name was `"universal.scene.npc_cap"`.

```python
# DELETE this line from run_all_universal_asserts():
check_npc_scene_cap(event),
```

**Why:** Cap no longer exists (steps 01.2-01.5 above). This checker would always pass and is now dead code. Removing it prevents confusion for future eval authors who might expect a cap to exist.

### Tests to write or update
Tests are temporarily removed during refactor — skip test updates per AGENTS.md rules.

### REPOMAP updates required
- `docs/repomap.md` (EngineConfig + constants section): Delete entire line 232 (`NPC_SCENE_CAP = 8`) — do not edit, delete the whole bullet point. Note that `_enforce_npc_present_cap()` and `clear_present_npcs_on_location_change()` no longer exist in `state/npcs.py`.
- `docs/repomap.md` (Extraction field routing section): Note that CompendiumEntry now has explicit motivation/fear/leverage fields.

## Implementation — Phase 02: Seed Generation Prompt + Schema

### Context files to load
- `ccya/prompts/generate_seed_system.j2` (full file, focus on lines 11, 34-53, 105, 186-203)

### Detailed steps

#### Step 02.1 — Move Campaign Arc above Compendium NPCs in generation order

**File:** `ccya/prompts/generate_seed_system.j2:34-53`

**What:** Reorder the numbered list (lines 36-48). Current order is PC → World state → Recent events → Opening scene/NPCs (step 4) → Inventory (step 5) → Campaign arc (step 6). Change to:
1. **PC** (bio, stats, tagline)
2. **World state** (3 immutable facts)
3. **Recent events** (immediate pre-story context)
4. **Campaign arc** (visible_goal, threads, thematic_question) — moved up from step 6
5. **Opening scene / NPCs** (compendium.npcs, informed by arc) — moved down from step 4
6. **Inventory** (items tied to PC's top skills)

Also update the Campaign Arc section heading on line 205 and NPC instructions on lines 186-198 to reflect their new positions in generation order (NPCs now come after arc, not before).

**Why:** Allows seed LLM to generate NPC bonds and connections that reference actual campaign goals/threads rather than generic patterns. Arc is the narrative spine; NPCs orbit it (design #1 above).

#### Step 02.2 — Remove motivation/fear/leverage prohibition from line 11

**File:** `ccya/prompts/generate_seed_system.j2:11`

**What:** Delete "Do NOT include motivation, fear, or leverage fields on compendium entries" from the end of line 11. Keep everything else on that line (NPC count guidance, presence values).

```
Before: ...presence="known". Do NOT include motivation, fear, or leverage fields on compendium entries — engine manages those. Do NOT set meta.compendium_touch_order...
After:  ...presence="known". Do NOT set meta.compendium_touch_order...
```

**Why:** LLM must be allowed to assign these fields at seed time (design #2 above). The prohibition was the primary blocker preventing seed NPCs from having motivation/fear/leverage.

#### Step 02.3 — Remove motivation/fear/leverage prohibition from line 203

**File:** `ccya/prompts/generate_seed_system.j2:203`

**What:** Delete "Do NOT add `relation`, `notes`, `motivation`, `fear`, or `leverage` to compendium entries." Replace with guidance that explicitly allows motivation, fear, and leverage on key NPCs (see step 02.6 below for the replacement text). Keep the prohibition on `relation` (deprecated field) and notes (scene-specific, cleared on departure — engine-managed at runtime).

```
Before: Do NOT add relation, notes, motivation, fear, or leverage to compendium entries...
After:  Compendium entries get name, title, bio (and optional allegiance if relevant, and optional bond for durable personal ties). At seed time, assign motivation, fear, and leverage to whichever NPCs feel important — those with personal ties to the PC or central roles in the opening situation. Do NOT add relation (deprecated field) or notes (scene-specific attitude cleared on departure; engine-managed at runtime).
```

**Why:** Same as step 02.2 above — second prohibition blocking seed-time motivation/fear/leverage assignment (design #2 above, decision table row for key NPC identification #7 above).

#### Step 02.4 — Add motivation/fear/leverage to TypeScript-style seed output schema at line ~105

**File:** `ccya/prompts/generate_seed_system.j2:~105` (line 105)

**What:** Update the compendium entry shape in the TypeScript-style schema. Current line 105 shows `{name: string, title: string, bio: string, allegiance?: string, bond?: string}`. Add motivation, fear, leverage as optional fields:
```ts
compendium: {npcs: {snake_case: {name: string, title: string, bio: string, allegiance?: string, bond?: string, motivation?: string, fear?: string, leverage?: string}}},
```

**Why:** LLM treats its own schema as contract — if these fields are not in the TypeScript-style output schema, it may not emit them even after prohibition is removed (design #2 above). This must change alongside steps 02.2 and 02.3 or seed-time motivation/fear/leverage will silently fail to appear.

#### Step 02.5 — Soften NPC count guidance on line 11

**File:** `ccya/prompts/generate_seed_system.j2:11` (beginning of line)

**What:** Change "Generate 4–5 named NPCs total: exactly 2 with presence="present"" to flexible guidance that references the override parameter. The existing conditional on lines 187-191 already handles `npc_count_override > 0`. Update line 11 to say something like "Generate 4–5 named NPCs total, typically ~2 present in the opening scene (exact count may be overridden by player preference)."

**Why:** Line 11 hardcodes "exactly 2" which contradicts the override mechanism on lines 187-191. Softening makes line 11 consistent with the conditional guidance below (design #5 above).

#### Step 02.6 — Replace rigid NPC bond pattern (lines 193-198) with flexible arc-informed guidance + key NPC identification + scene ideal count/exit pressure

**File:** `ccya/prompts/generate_seed_system.j2:186-198`

**What:** Rewrite the entire "scene NPCs" section (lines 186-203). Replace lines 186-198 with this exact text:

```
## scene NPCs (in compendium.npcs with presence="present")
{% if npc_count_override and npc_count_override > 0 %}
Generate exactly {{ npc_count_override }} NPCs placed in compendium.npcs with `presence: "present"`, `notes: "current attitude or situation"`, and the standard compendium fields (id, name, title, bio). Aim for 1–4 present NPCs — this is ideal scene density. If you generate more than 4, give narrative reasons why some should leave (shift change, dismissed, running an errand) so their absence feels natural on turn 2+.
{% else %}
Generate 4–5 named NPCs total, typically ~2 present in the opening scene (exact count may be overridden by player preference). Aim for 1–4 present NPCs — this is ideal scene density. If you generate more than 4, give narrative reasons why some should leave (shift change, dismissed, running an errand) so their absence feels natural on turn 2+.
{% endif %}

Of the in-scene NPCs, assign motivation, fear, and leverage to whichever feel important — those with personal ties to the PC or central roles in this opening situation. There is no formal definition of "key NPC"; use judgment based on who matters narratively. For each such NPC, populate all three fields (motivation = what they fundamentally want; fear = what they dread most; leverage = what they can offer/threaten/withhold).

The remaining in-scene NPCs should have bonds reflecting their connection to the PC or situation — not generic role descriptions. If `pool_selection.npc_bond` is provided, follow that pattern for at least one NPC with a personal tie (debt owed, shared history, emotional bond, key story intersection). Express ties through the `bond` field; reference the PC by name in their bio where shared history demands it.

Do NOT force exactly two NPCs or require one to carry "personal stakes" and another "external pressure." Let narrative context determine how many NPCs belong in this scene and what roles they fill.
```

Also update line 203 (the compendium.npcs prohibition) as described in step 02.3 above, since steps 02.3 and 02.6 are related edits to adjacent sections of the same file (lines 186-203 total). Apply both changes together or ensure step 02.3 runs before/during step 02.6 so line references remain consistent.

**Why:** The rigid pattern forces formulaic NPCs (one personal + one external pressure). Flexible guidance allows the seed LLM to assign motivation/fear/leverage contextually and generate bonds that reflect the specific campaign arc rather than generic templates (design #7 above for key NPC identification, design #6 above for scene ideal count, design #1 above for arc-informed generation).

**Validation:** Read file after edit. Verify:
- Line 11 no longer contains "Do NOT include motivation, fear, or leverage"
- Line ~105 TypeScript schema includes motivation?: string, fear?: string, leverage?: string in compendium entry shape
- Lines 186-203 contain flexible arc-informed NPC guidance (no rigid two-NPC pattern)
- Generation order section shows Campaign Arc above Compendium NPCs

### Tests to write or update
Tests are temporarily removed during refactor — skip test updates per AGENTS.md rules.

### REPOMAP updates required
- `docs/repomap.md` (Prompt sections): Update seed generation order reference in generate_seed_system.j2 section (arc now before NPCs).

## Implementation — Phase 03: UI Compendium Tooltip Reformat

### Context files to load
- `ccya/templates/_state_left.html` (lines 54-74 for scene card, lines 158-179 for compendium tooltip)

### Detailed steps

#### Step 03.1 — Scene card: notes already inline (verify no change needed), confirm bio-only tooltip scope

**File:** `ccya/templates/_state_left.html:62-67`

**What:** Verify scene card NPC rendering on lines 54-74 is correct as-is for this plan's purposes. Notes appear inline via `<span class="npc-notes-inline">` (lines 63-65). Bio appears in tooltip only (lines 66-68). This matches design #10 above — notes are NOT shown in compendium tooltips, they ARE shown inline on scene card NPCs. No changes needed to this section for the plan's scope.

**Why:** Confirming existing behavior is correct prevents unnecessary churn and confirms we're not breaking anything (design #10 above).

#### Step 03.2 — Compendium tooltip: reformat with conditional rendering, blank-line separators, motivation field inclusion, notes exclusion

**File:** `ccya/templates/_state_left.html:158-179` (compendium panel NPC list section)

**What:** Replace the entire compendium tooltip content (lines 168-178). Current format renders bio → bond → fear/leverage traits block → last_seen, all separated by `<br>` tags with no blank-line visual separation. New format must:
- Render fields in order: bio → motivation → bond → last_seen (NOT fear/leverage — those are hidden per design decision #3 above)
- Use `\n\n` (blank line) separators between each field, rendered as `<br><br>` in HTML for visual blank-line separation
- Each field shown only if non-empty (conditional rendering: motivation block appears only when `motivation` is truthy; same for bond and last_seen)
- Bio renders unlabelled prose (no prefix); motivation uses bold label prefix (`**Motivation:**`); bond uses bold label prefix (`**Bond:**`); last_seen uses plain text "Last seen:" label

Current code (lines 168-178):
```html
<div class="tooltip-body" data-md>
    {{ bio or '—' }}
    {% if npc_bond %}{% if bio %}<br>{% endif %}<strong>Bond:</strong> {{ npc_bond }}{% endif %}
    {% if fear or leverage %}
    <br><div class="npc-traits">
        {% if fear %}<strong>Fear:</strong> {{ fear }}<br>{% endif %}
        {% if leverage %}<strong>Leverage:</strong> {{ leverage }}{% endif %}
    </div>
    {% endif %}
    {% if ls %}{% if npc_bond or fear or leverage %}<br>{% endif %}Last seen: {{ ls.location_name }}{% endif %}
</div>
```

New code (replace lines 168-178):
```html
<div class="tooltip-body" data-md>
    {% if bio %}{{ bio }}{% else %}—{% endif %}{% set _has = false %}
    {% if entry.motivation %}<br><br>**Motivation:** {{ entry.motivation }}{% set _has = true %}{% endif %}
    {% if npc_bond %}{% if _has %}<br><br>{% endif %}**Bond:** {{ npc_bond }}{% set _has = true %}{% endif %}
    {% if ls %}{% if _has %}<br><br>{% endif %}Last seen: {{ ls.location_name }}{% endif %}
</div>
```

Key changes from old to new:
- **Removed** fear/leverage rendering (lines 171-175 in old code) — these are behavioral metadata, not UI-visible per design #3 above
- **Added** motivation field with `**Motivation:**` bold label prefix matching existing bond/fear/leverage convention
- **Changed** `<br>` separators to `<br><br>` (blank-line visual separation between fields)
- **Conditional rendering**: `_has` flag tracks whether any previous field rendered; each subsequent field adds separator only if `_has` is true. This avoids unnecessary leading blank lines when bio is empty and motivation/bond are also absent, while ensuring proper spacing between all present fields.

Also remove unused variable extractions on lines 163-164 (both fear and leverage are hidden from UI per design #3, so neither is needed in this template):
```python
# DELETE line 163: {% set fear = entry.fear if entry is mapping else '' %}
# DELETE line 164: {% set leverage = entry.leverage if entry is mapping else '' %}
```

**Important:** The tooltip rewrite (lines 168-178) and variable deletion (lines 163-164) must be applied as a single atomic edit. If done sequentially, Jinja will temporarily reference undefined `fear`/`leverage` on old line 177 (`{% if npc_bond or fear or leverage %}`), causing a runtime error during the intermediate state.

**Why:** Compendium tooltip should show bio → motivation → bond → last_seen with blank-line visual separation for scannability. Motivation is player-facing (design #9 above). Fear/leverage are hidden because they drive NPC behavior in narration, not UI context (design decision table row 93). Notes field excluded from compendium tooltips per design #10 above (notes appear inline only on scene card NPCs via step 03.1 verification).

**Validation:** Read file after edit. Verify:
- Lines 168-178 contain new conditional rendering format with `<br><br>` separators
- No fear/leverage references in compendium tooltip section (lines 158-179)
- Motivation field renders with `**Motivation:**` bold label prefix
- Bio, motivation, bond, last_seen appear in correct order

### Tests to write or update
Tests are temporarily removed during refactor — skip test updates per AGENTS.md rules.

### REPOMAP updates required
- `docs/repomap.md` (UI template section): Update compendium tooltip field list (motivation added, fear/leverage removed).
