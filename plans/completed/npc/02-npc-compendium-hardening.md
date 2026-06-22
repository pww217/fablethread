# NPC Compendium Hardening — Alias Naming, Personality Fields, Passive NPC Extraction

## Purpose

Fix three compendium quality issues that degrade NPC fidelity: alias NPCs that never resolve to proper names, named NPCs that lack personality depth, and scene extraction that misses passive/recipient NPCs.

## Problem Statement

The compendium has three related quality problems:

1. **Alias naming gap:** When the scene extractor encounters an unnamed character ("Unknown Visitor", "Scarred Soldier"), it puts the descriptive label in `name` instead of `aliases`. When the character later gets a proper name ("Leo"), the extractor creates a duplicate entry because no dedup link existed between the descriptive label and the proper name.

2. **Named NPC personality gap:** Named NPCs (those with proper names) should always receive a `bio` plus 2-3 personality fields (`motivation`, `fear`, `leverage`, `bond`) when first added to the compendium. Alias NPCs only need a `bio`. Currently the extraction prompt doesn't distinguish between these two tiers.

3. **Passive NPC extraction gap:** The scene extraction prompt biases toward NPCs performing visible actions (subjects), not NPCs being acted upon (recipients). Characters central to the story who are rescued, captured, healed, or transported never get compendium entries because the LLM spends its "new NPC budget" on active subjects instead.

## Constraints

- No backward compatibility required — dead code can be removed outright.
- Personality fields (`motivation`, `fear`, `leverage`, `bond`) already exist in both `CompendiumNpcUpdate` and `CompendiumEntry` models.
- `personality` field exists in `CompendiumNpcUpdate` but is missing as a declared field in `CompendiumEntry` (was a gap in the original npc-personality plan).
- `aliases` field already exists in `CompendiumNpcUpdate` as `list[str]`.
- No new models, no new state fields, no new systems.
- Changes are prompt-only + one model field addition + one template change.
- Tests temporarily removed per AGENTS.md.

## Non-goals

- No alias→name promotion logic in Python code (prompt + template handles it).
- No retroactive personality assignment to existing NPCs.
- No compendium TTL or cleanup changes (separate plan).
- No changes to the personality assignment system (write-once archetype selection).
- No changes to the seed generation pipeline (seed NPCs already get personality fields).
- No changes to NPC departure/death lifecycle (already completed).

## Solution

Three coordinated changes:

1. **Alias-first naming:** Update the extraction prompt to instruct the LLM to use `aliases` for non-proper names and `name` for proper names. When a proper name is later mentioned, the LLM should update `name` and keep `aliases` populated. The UI template shows `name` if populated, falls back to `aliases[0]` in tooltips.

2. **Named NPC personality requirement:** Update the extraction prompt to require `bio` + 2-3 of (motivation, fear, leverage, bond) for named NPCs on first compendium entry. Alias NPCs only need `bio`.

3. **Passive NPC extraction:** Add belt-and-suspenders instruction to the extraction prompt for NPCs who enter as recipients of major actions (rescue, capture, healing, transport).

## Firm decisions

1. **Alias-first naming is prompt-only.** The LLM is instructed to use `aliases` for non-proper names. When a proper name is later mentioned, the LLM updates `name` and keeps `aliases`. No Python dedup logic needed — the existing `_dedup_compendium_update()` handles name matching.

2. **UI shows name primary, alias fallback.** In the compendium tooltip, show `name` if populated. If `name` is empty/alias-only, show `aliases[0]` below the bio. Never show both in the main display.

3. **Named NPCs get bio + 2-3 personality fields.** The LLM picks which 2-3 of (motivation, fear, leverage, bond) are most relevant. Reduces output bloat vs requiring all 4.

4. **Personality fields assigned on first compendium entry.** When a named NPC is first added to the compendium, the LLM should assign personality fields. No separate promotion step needed.

5. **CompendiumNPC personality field added to CompendiumEntry.** Fix the gap from the original npc-personality plan — add `personality: str | None = None` as a declared field.

6. **Passive NPC extraction is belt-and-suspenders.** Add instruction to the extraction prompt. The primary fix is the alias-first naming (which naturally captures passive NPCs as aliases), this is extra coverage.

## Risks, Ambiguities, and Blockers

- **LLM compliance with alias-first naming:** The LLM has been trained to put descriptive labels in `name`. Changing this requires clear, explicit instructions with examples. Monitor extraction logs for compliance.
- **Name promotion detection:** When the LLM later mentions a proper name for an alias NPC, it must update `name` rather than creating a new entry. The existing dedup logic (`_find_npc_by_name` in npcs.py) handles this, but the prompt must instruct the LLM to check the compendium before creating new entries.
- **Personality field assignment timing:** Named NPCs should get personality fields on first compendium entry, not on every appearance. The prompt should say "on first entry" not "every time."
- **Passive NPC extraction may conflict with "limit 3 new NPCs per turn":** If the LLM is already at the NPC budget, passive NPCs may still be missed. The prompt should clarify that passive NPCs who are central to the plot count toward the budget.

## Status
`completed`

## Phases

3 phases covering: (1) model field addition, (2) extraction prompt changes (alias naming, personality requirements, passive NPC extraction), (3) UI template change (alias display in tooltips).

---

## Implementation — Phase 1: Model field addition

### Context files to load
- `ccya/pack.py` — `CompendiumEntry` model (lines 37-48)
- `ccya/models.py` — `CompendiumNpcUpdate` model (lines 245-263) for reference
- `docs/repomap.md` — CompendiumEntry section (lines 191, 246) for documentation update

### Detailed steps

#### Step 1.1 — Add `personality` field to `CompendiumEntry`

**File:** `ccya/pack.py`, `CompendiumEntry` class (lines 37-48)

**What:** Add `personality: str | None = None` as an optional field to `CompendiumEntry`. Place it after `leverage` to match the field ordering in `CompendiumNpcUpdate`.

**Why:** Fix the gap from the original npc-personality plan. `CompendiumNpcUpdate` has `personality` as a declared field (models.py:259), but `CompendiumEntry` only has it via `extra: "allow"`. Adding it as a declared field makes it type-safe and visible in model introspection.

```python
class CompendiumEntry(BaseModel):
    model_config = {"extra": "allow"}
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    bond: str | None = None
    presence: str | None = None
    notes: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    personality: str | None = None  # archetype id; write-once, engine-assigned
```

**Validation:**
```bash
.venv/bin/python -c "from ccya.pack import CompendiumEntry; e = CompendiumEntry(name='Test', personality='cold_pragmatist'); assert e.personality == 'cold_pragmatist'; print('ok')"
```

#### Step 1.2 — Update `docs/repomap.md` CompendiumEntry section

**File:** `docs/repomap.md`

**What:** Update the two places that reference `CompendiumEntry` fields to include `personality`:
- Line 191: Add `personality` to the field list
- Line 246: Add `personality` to the field list

**Why:** Documentation must reflect the current model. Stale docs are bugs per AGENTS.md.

**Validation:** Grep `docs/repomap.md` for `CompendiumEntry` — both references should now include `personality`.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 2: Extraction prompt changes

### Context files to load
- `ccya/prompts/extract_scene_system.j2` (full file, 137 lines)
- `ccya/state/npcs.py` — `apply_npc_scene_management()` (lines 97-190) for understanding how updates are applied
- `ccya/prompts/extract_scene_user.j2` — to understand what context the LLM receives about known characters

### Detailed steps

#### Step 2.1 — Add alias-first naming instruction to extraction prompt

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add a new section after the "NPC ID rules" section (after line 60) that establishes alias-first naming rules. Also update the "NPC dedup" section (line 119) to reference alias matching.

Add after line 60 (after "Bio is mandatory for every NPC"):

```
## Alias-first naming (MANDATORY)

When creating or updating an NPC entry:
- **Named NPCs (proper name known):** Set `name` to the proper name (e.g., "Leo Vance"). Do NOT put proper names in `aliases`.
- **Unnamed NPCs (descriptive label only):** Set `name` to a descriptive label (e.g., "Scarred Soldier") AND add that label to `aliases`. The `name` field is a display fallback — it shows when no proper name is known.
- **Name revealed later:** When narration reveals a proper name for an NPC previously known by description, update `name` to the proper name. Keep the descriptive label in `aliases` so the history is preserved. Do NOT create a new compendium entry.
- **Placeholder names:** Labels like "Unknown Visitor", "Frantic Stranger", "Mysterious Figure", "Scarred Soldier", "Young Man" are descriptive aliases, not proper names. Put them in `aliases`, not `name`.
```

**Why:** This is the core change that prevents the "Unknown Visitor" → "Leo" duplicate problem. By instructing the LLM to use `aliases` for descriptive labels, the existing dedup logic (`_find_npc_by_name` in npcs.py) can match proper names against existing entries.

**Validation:** Read the updated template — should contain "Alias-first naming" section with clear rules for named vs unnamed NPCs.

#### Step 2.2 — Add personality field requirements for named NPCs

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add a new section after the alias-first naming section (after Step 2.1) that establishes personality field requirements based on whether the NPC has a proper name.

Add after Step 2.1:

```
## NPC field requirements

- **Named NPCs (proper name in `name`):** Must have `bio` (mandatory) plus at least 2 of these 4 fields: `motivation`, `fear`, `leverage`, `bond`. Pick the 2-3 that are most relevant to the story. On first compendium entry, assign all required fields.
- **Unnamed NPCs (descriptive label only):** Must have `bio` (mandatory). No personality fields required — they may be assigned later when/if the NPC gets a proper name.
- **Ambient/ambient presence (crowd, bystanders, inn_patrons):** Must have `bio` (mandatory, 1-2 sentences describing the group). No other fields required.
```

**Why:** Named NPCs are more important to the story and should have personality depth. Alias NPCs (unnamed, ambient) only need a bio. This reduces output bloat while ensuring named NPCs get the depth they need.

**Validation:** Read the updated template — should contain "NPC field requirements" section with three tiers.

#### Step 2.3 — Add passive NPC extraction instruction

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add a new section after the NPC field requirements section that instructs the LLM to create compendium entries for NPCs who enter as recipients of major actions.

Add after Step 2.2:

```
## Passive NPC extraction

If a named character enters the scene as the **recipient** of a major action (rescue, capture, healing, transport, medical aid), create a compendium entry for them even if they don't perform visible actions. Use whatever information is available from context — including details from recent narration history if needed for the bio. This is belt-and-suspenders: the primary mechanism is alias-first naming (above), but this ensures central plot characters are never missed.
```

**Why:** Belt-and-suspenders fix for Bug 11 (Elias never extracted). The primary fix is alias-first naming (unnamed recipients get descriptive aliases), this catches cases where the LLM might still miss a passive NPC.

**Validation:** Read the updated template — should contain "Passive NPC extraction" section.

#### Step 2.4 — Update the output schema comment

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Update the output schema comment (lines 7-13) to reflect the full field set including `aliases`, `motivation`, `fear`, `leverage`.

Replace lines 7-13:

```json
{
  "scene_tagline": "...",
  "location_change": {"id": "...", "name": "...", "description": "..."},
  "location_description": "...",
  "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "aliases": ["..."], "allegiance": "...", "motivation": "...", "fear": "...", "leverage": "...", "presence": "present|nearby|known|departed", "notes": "...", "position": "..."}]
}
```

**Why:** The schema comment should reflect the actual fields available. Currently it omits `aliases`, `motivation`, `fear`, `leverage` which are all valid fields on `CompendiumNpcUpdate`.

**Validation:** Read the updated template — schema comment should include all fields.

#### Step 2.5 — Update `docs/repomap.md` extraction prompt section

**File:** `docs/repomap.md`

**What:** Add/update the extraction system prompt section in repomap to document:
- Alias-first naming section (new)
- NPC field requirements section (new)
- Passive NPC extraction section (new)
- Schema comment update (aliases, motivation, fear, leverage now included)
- CompendiumEntry model now has explicit personality field alongside motivation/fear/leverage

**Why:** AGENTS.md mandates documentation updates for prompt changes. The extraction prompt is a documented public API in the repomap.

**Validation:** Grep `docs/repomap.md` for "extract_scene_system" — should include alias-first naming, NPC field requirements, passive NPC extraction, and updated schema.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 3: UI template change

### Context files to load
- `ccya/templates/_state_left.html` — compendium section (lines 139-168)
- `ccya/templates/_state_left.html` — scene NPCs section (lines 10-38) for reference

### Detailed steps

#### Step 3.1 — Add alias display to compendium tooltips

**File:** `ccya/templates/_state_left.html`, compendium section (lines 139-168)

**What:** In the compendium tooltip, add alias display below the bio and above other fields. Show the first alias if `name` is empty/alias-only.

Update the compendium tooltip block (lines 155-161):

Replace:
```html
<div class="tooltip-body" data-md-compendium>
    {% if bio %}<p>{{ bio }}</p>{% else %}—{% endif %}{% set _has = false %}
    {% if npc_pl %}<p><strong>Personality:</strong> {{ npc_pl }}{% if npc_pt %} — {{ npc_pt }}{% endif %}</p>{% set _has = true %}{% endif %}
    {% if _mot %}<p><strong>Motivation:</strong> {{ _mot }}</p>{% set _has = true %}{% endif %}
    {% if npc_bond %}<p><strong>Bond:</strong> {{ npc_bond }}</p>{% set _has = true %}{% endif %}
    {% if ls %}<p>Last seen: {{ ls.location_name }}</p>{% endif %}
</div>
```

With:
```html
<div class="tooltip-body" data-md-compendium>
    {% if bio %}<p>{{ bio }}</p>{% else %}—{% endif %}{% set _has = false %}
    {% set _aliases = entry.aliases if entry is mapping and entry.aliases else [] %}
    {% if _aliases and not nm %}<p><em>Previously known as: {{ _aliases[0] }}</em></p>{% set _has = true %}{% endif %}
    {% if npc_pl %}<p><strong>Personality:</strong> {{ npc_pl }}{% if npc_pt %} — {{ npc_pt }}{% endif %}</p>{% set _has = true %}{% endif %}
    {% if _mot %}<p><strong>Motivation:</strong> {{ _mot }}</p>{% set _has = true %}{% endif %}
    {% if npc_bond %}<p><strong>Bond:</strong> {{ npc_bond }}</p>{% set _has = true %}{% endif %}
    {% if ls %}<p>Last seen: {{ ls.location_name }}</p>{% endif %}
</div>
```

**Why:** When an NPC starts as an alias ("Unknown Visitor") and later gets a proper name ("Leo"), the player should see the alias history in the tooltip. This prevents the impression that the NPC "disappeared" and was replaced. The alias is shown only when `name` is empty (alias-only NPC), not when both exist.

**Validation:** Start a game, create an NPC with a descriptive name, verify the alias appears in the compendium tooltip when hovering over the entry.

#### Step 3.2 — Update `docs/repomap.md` NPC roster template section

**File:** `docs/repomap.md`

**What:** Update the NPC roster template section (line 202) to document:
- Compendium tooltip now shows alias fallback when `name` is empty
- Alias display appears below bio, above personality fields
- Template variable `entry.aliases` accessed in compendium section

**Why:** AGENTS.md mandates documentation updates for template changes. The compendium tooltip behavior change affects how NPC data is rendered to players.

**Validation:** Grep `docs/repomap.md` for "NPC roster template" or "compendium" — should include alias fallback behavior.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Verification

After all phases:

1. Run `make check` (lint + typecheck) — must pass.
2. Verify `CompendiumEntry` has `personality` field: `.venv/bin/python -c "from ccya.pack import CompendiumEntry; print(CompendiumEntry.model_fields.keys())"` — should include `personality`.
3. Verify extraction prompt contains "Alias-first naming" section.
4. Verify extraction prompt contains "NPC field requirements" section.
5. Verify extraction prompt contains "Passive NPC extraction" section.
6. Verify compendium tooltip shows alias when name is empty.
