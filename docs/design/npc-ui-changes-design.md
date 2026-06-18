# NPC UI & Model Changes Design

## Purpose

Design for restructuring NPC compendium fields: split `bio`, consolidate `departed_reason`/`departed_summary`, remove dead fields (`allegiance`, `nearby_since_turn`, `last_seen`), add `last_presence_turn`, and surface `condition_change_reason` in UI. This document is the design authority for plans implementing these changes.

## Problem Statement

1. **`bio` mixes appearance and background** — The extraction prompt already instructs for "two sentences" (appearance + background) but stores them as a single string. The UI renders it as one blob. Formalizing as two fields makes the contract explicit and lets the UI display them separately.

2. **`departed_reason` + `departed_summary` are redundant** — Both are extracted for departed NPCs. `departed_reason` is a short label (shown in roster). `departed_summary` is 1-2 sentence prose (never shown in UI). The summary exists but is invisible to the player. Combine into one field.

3. **`allegiance` is silently dropped** — Extracted by LLM but `CompendiumEntry` has no `allegiance` field. Pydantic silently ignores the extra field. The value is never stored or displayed.

4. **`nearby_since_turn` is dead code** — Set on location change and by delta_builder, read in `turn.py:1294` but the value is never surfaced anywhere.

5. **`last_seen` stores absolute turn number** — The compendium stores `{turn, location_id, location_name}` dict. The "X turns ago" value is never computed or displayed. The absolute turn number becomes stale and requires manual computation at render time.

## Constraints

- `CompendiumNpcUpdate` is the extraction model — changes here affect the LLM prompt contract
- `CompendiumEntry` is the stored state shape (dict in `state.compendium.npcs`) — Pydantic extra fields are silently dropped on load
- Existing saves must survive the changes — Pydantic extra fields on load are silently dropped, so removing fields from models is safe for existing saves
- Prompt templates must be updated to match new field names
- UI templates must be updated to render new field structure

## Non-goals

- No changes to `last_seen` computation logic (just removal)
- No changes to NPC presence semantics (present/nearby/known/departed/archived)
- No changes to auto-archive TTL logic (departed → archived after 3 turns)
- No changes to nearby decay TTL logic (nearby → known after 2 turns)
- No changes to PC model fields (PC `bio` stays as single string)
- No changes to seed generation for NPC `bio` beyond field name changes

## Decision Table

| Decision | What | Why |
|---|---|---|
| Bio split | `bio: str | None` → `bio_appearance: str | None`, `bio_background: str | None` on `CompendiumNpcUpdate` | Flat fields are simpler for extraction (no dict nesting), match existing model style, and are easier for the LLM to produce correctly |
| Departed consolidation | Remove `departed_summary`; keep `departed_reason` as 1-2 sentence prose describing what happened | The two fields were redundant — `departed_summary` was never shown in UI. Single field eliminates confusion |
| Allegiance removal | Remove `allegiance` from `CompendiumNpcUpdate` and extraction prompts | Never stored or displayed; silently dropped by Pydantic extra-field handling |
| Nearby_since_turn removal | Remove `nearby_since_turn` from `CompendiumEntry` and all write/read sites | Dead code — set but never surfaced |
| Last_seen removal | Remove `last_seen` dict from compendium entries; compute "X turns ago" from `last_presence_turn` | Absolute turn number is stale; computed value is what the UI actually needs |
| Last_presence_turn addition | Add `last_presence_turn: int | None` to `CompendiumEntry` (dict-level, no model field needed) | Enables "X turns ago" computation for departed NPCs: `current_turn - last_presence_turn` |
| Condition change reason UI | Add `last_condition_change_reason` to Player header tooltip in `_state_right.html` | Follows existing pattern from Inventory header tooltip |

## Open Questions

None.

## Current State — What Exists

### `CompendiumNpcUpdate` (extraction model)

**File:** `ccya/models.py:242-260`

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None          # ← single string, two-aspect instruction
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None    # ← extracted but silently dropped
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None
    notes: str | None = None
    position: str | None = None
    first_seen_turn: int | None = None
    personality: str | None = None
    bond: str | None = None
    departed_reason: str | None = None     # ← short label
    departed_summary: str | None = None    # ← 1-2 sentence prose (never shown)
    departed_turn: int | None = None
```

### `CompendiumEntry` (stored state — dict)

**File:** `ccya/state/npcs.py:252-323`

Stored as `dict[str, Any]` in `state.compendium.npcs`. Keys written by `apply_npc_scene_management()`:

- `name`, `title`, `bio`, `aliases`, `allegiance`, `motivation`, `fear`, `leverage`, `bond`, `personality`, `presence`, `notes`, `position`
- `first_seen_turn` — set on first appearance
- `last_seen` — dict `{turn, location_id, location_name}` — set on every compendium update
- `nearby_since_turn` — set on location change (nearby decay tracking)
- `departed_turn` — set on first `presence: "departed"`
- `departed_reason`, `departed_summary` — set when `presence: "departed"`

### Extraction Prompt

**File:** `ccya/prompts/extract_scene_system.j2:26-47`

```json
{
  "bio": "TWO SENTENCES: (1) appearance and demeanor ... (2) personality traits ...",
  "allegiance": "faction_or_alignment",
  "departed_reason": "short label — required when presence is departed",
  "departed_summary": "1-2 sentence prose — required when presence is departed",
}
```

### UI Rendering

**File:** `ccya/templates/_state_left.html`

- Present NPCs (lines 12-37): renders `npc_bio` in tooltip
- Compendium (lines 144-165): renders `bio` in tooltip, `last_seen.location_name` on line 162

**File:** `ccya/templates/_state_right.html`

- Player header (lines 7-12): no `condition_change_reason` tooltip
- Inventory header (line 52): has `last_inventory_change_reason` tooltip (pattern to follow)

**File:** `ccya/prompts/sections/_npc_roster.j2:7`

- Roster line for departed NPCs: `— {{ n.departed_reason }}`

### `build_npc_roster`

**File:** `ccya/engine/npc_roster.py:14-81`

Returns dicts with keys: `id`, `name`, `title`, `bio`, `presence`, `motivation`, `fear`, `leverage`, `bond`, `notes`, `last_seen`, `departed_reason`.

### `NPCRosterEntryBlock`

**File:** `ccya/prompts/context.py:195-204`

```python
class NPCRosterEntryBlock(BaseModel):
    id: str
    name: str
    title: str | None = None
    bio: str | None = None
    presence: NpcPresence
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    notes: str | None = None
    last_seen: LastSeenBlock | None = None
```

### `last_seen` Population

**File:** `ccya/engine/turn.py:1177-1193`

Stamped on every compendium NPC update:
```python
entry["last_seen"] = {
    "turn": turn_no,
    "location_id": location.get("id", ""),
    "location_name": location.get("name", ""),
}
```

**File:** `ccya/state/npcs.py:257-261`

Also stamped on first appearance of new NPCs.

### `nearby_since_turn`

**File:** `ccya/engine/turn.py:1186` — set on new NPC creation
**File:** `ccya/state/delta_builder.py:225` — set on location change for all present→nearby transitions
**File:** `ccya/engine/turn.py:1294` — read for nearby decay check

### `departed_reason` + `departed_summary` Checker

**File:** `ccya/ev/checkers/npc_presence.py:48-62`

Checks both fields are present when `presence == "departed"`.

### `condition_change_reason`

**File:** `ccya/models.py:326` — on `StateExtractResult`
**File:** `ccya/state/io.py:85` — default `None` in meta
**Stored as:** `state.meta.last_condition_change_reason`
**Pattern:** Inventory header already has this tooltip pattern at `_state_right.html:52`

### `generate_seed_system.j2`

**File:** `ccya/prompts/generate_seed_system.j2:36`

Seed compendium schema has `bio: string` for NPCs.

### `pack.py` — `CompendiumEntry`

**File:** `ccya/pack.py:36-48`

Seed-time compendium model has `bio: str | None = None`.

## Proposed Solution

### Core Changes

#### 1. Split `bio` into `bio_appearance` + `bio_background`

**`CompendiumNpcUpdate`** (`ccya/models.py:246`):
```python
bio_appearance: str | None = None   # physical presentation — bearing, posture, expression, distinctive features
bio_background: str | None = None   # backstory, personality, reputation — who they are as a person
```

**Extraction prompt** (`ccya/prompts/extract_scene_system.j2:31`):
```json
{
  "bio_appearance": "Physical appearance and demeanor — bearing, posture, expression, distinctive features. One sentence.",
  "bio_background": "Backstory, personality traits, reputation — who they are as a person. One sentence."
}
```

**Engine** (`ccya/state/npcs.py:267-268`):
```python
if comp_upd.bio_appearance is not None:
    entry["bio_appearance"] = _strip_non_ascii(comp_upd.bio_appearance)
if comp_upd.bio_background is not None:
    entry["bio_background"] = _strip_non_ascii(comp_upd.bio_background)
```

**`build_npc_roster`** (`ccya/engine/npc_roster.py:45`):
```python
"bio_appearance": (entry.get("bio_appearance") or "").strip() or None,
"bio_background": (entry.get("bio_background") or "").strip() or None,
```

**`NPCRosterEntryBlock`** (`ccya/prompts/context.py:198`):
```python
bio_appearance: str | None = None
bio_background: str | None = None
```

**UI templates** (`_state_left.html`):
- Present NPC tooltip (line 29): render `bio_appearance` then `bio_background` on separate lines
- Compendium tooltip (line 157): render `bio_appearance` then `bio_background` on separate lines

**Seed prompt** (`generate_seed_system.j2:36`):
- Update compendium schema to use `bio_appearance` + `bio_background`

**Seed model** (`pack.py:40`):
- `CompendiumEntry`: `bio_appearance: str | None = None`, `bio_background: str | None = None`

**Roster prompt** (`_npc_roster.j2:7`):
- Update roster line to use `bio_appearance` (or `bio_background` if appearance is empty)

#### 2. Consolidate `departed_reason` + `departed_summary`

**`CompendiumNpcUpdate`** (`ccya/models.py:258-259`):
```python
departed_reason: str | None = None     # 1-2 sentence prose describing what happened
```
Remove `departed_summary`.

**Extraction prompt** (`ccya/prompts/extract_scene_system.j2:42-47`):
```json
{
  "departed_reason": "1-2 sentence prose describing what happened — required when presence is departed. Examples: 'killed in battle', 'sailed away after the raid', 'imprisoned for life'"
}
```
Remove `departed_summary` field and description.

**Engine** (`ccya/state/npcs.py:309-313`):
```python
if comp_upd.presence == "departed":
    if comp_upd.departed_reason is not None:
        entry["departed_reason"] = comp_upd.departed_reason
```
Remove `departed_summary` write.

**Checker** (`ccya/ev/checkers/npc_presence.py:48-62`):
```python
if presence == "departed":
    if not npc.get("departed_reason"):
        findings.append({
            "turn": turn,
            "check": "departed_reason",
            "detail": f"NPC '{npc_id}' is departed but missing departed_reason",
        })
        all_passed = False
```
Remove `departed_summary` check.

**Roster prompt** (`_npc_roster.j2:7`):
- Unchanged — already uses `n.departed_reason`

**UI templates** (`_state_left.html`):
- Departed NPC rendering: use `departed_reason` for the "last seen" line

#### 3. Remove `allegiance`

**`CompendiumNpcUpdate`** (`ccya/models.py:248`): Remove `allegiance: str | None = None`

**Engine** (`ccya/state/npcs.py:275-276`): Remove `allegiance` write block

**Extraction prompt** (`ccya/prompts/extract_scene_system.j2:33`): Remove `allegiance` field

**Durable instructions** (`ccya/prompts/extract_scene_system.j2:53`): Remove `allegiance` from "Durable identity updates" list

#### 4. Remove `nearby_since_turn`

**Engine** (`ccya/engine/turn.py:1186`): Remove `nearby_since_turn` from new NPC creation

**Delta builder** (`ccya/state/delta_builder.py:225`): Remove `nearby_since_turn` assignment

**Engine** (`ccya/engine/turn.py:1294`): Replace `nearby_since_turn` usage with `last_presence_turn` for nearby decay check

#### 5. Remove `last_seen`, Add `last_presence_turn`

**Engine** (`ccya/engine/turn.py:1177-1193`): Remove `last_seen` stamping. Add `last_presence_turn` tracking:

```python
# Track last turn NPC was present or nearby
if entry.get("presence") in ("present", "nearby"):
    entry["last_presence_turn"] = turn_no
```

**First appearance** (`ccya/state/npcs.py:257-261`): Remove `last_seen` dict. `last_presence_turn` is set by the engine on first appearance (via the compendium update path above).

**`build_npc_roster`** (`ccya/engine/npc_roster.py:52`): Remove `last_seen` from output dict

**`NPCRosterEntryBlock`** (`ccya/prompts/context.py:204`): Remove `last_seen` field

**UI templates** (`_state_left.html`):
- Present NPC tooltip (line 33): Remove `last_seen.location_name`
- Compendium tooltip (line 162): For departed NPCs, render `Last seen: [location_name] (X turns ago)` computed from `last_presence_turn`

**Prompt** (`_npc_roster.j2:16`): Remove `last_seen` rendering

**`prompt_eval.py`** (`ccya/ev/prompt_eval.py:63`): Remove `last_seen` from mock NPC data

**Merge logic** (`ccya/state/npcs.py:239-240`): Remove `last_seen` merge from compendium merge

#### 6. Surface `condition_change_reason` in UI

**UI** (`ccya/templates/_state_right.html:52`): Add `last_condition_change_reason` tooltip to Player header, following the existing Inventory header pattern:

```html
<div class="stat-row{% if state.pc.bio %} has-tooltip{% endif %}">
    <span class="stat-label">Name</span>
    <span class="stat-value">{{ state.pc.get('name') or '—' }}</span>
    {% if state.pc.bio %}
    <div class="tooltip-body" data-md>{{ state.pc.bio }}</div>
    {% endif %}
    {% if state.meta.get('last_condition_change_reason') %}
    <div class="tooltip-body" data-md>{{ state.meta.get('last_condition_change_reason') }}</div>
    {% endif %}
</div>
```

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Nested `bio: {appearance, background}` | Flat fields are simpler for extraction, match existing model style, no dict nesting complexity |
| Keep both `departed_reason` (label) + `departed_summary` (prose) | `departed_summary` is never shown in UI; single prose field eliminates confusion |
| Keep `last_seen` dict and compute "X turns ago" at render time | Absolute turn number is stale; storing `last_presence_turn` is cleaner and more efficient |
| Add `last_presence_turn` to `CompendiumNpcUpdate` model | `last_presence_turn` is engine-managed (not extracted by LLM); no need for extraction model field |

## Failure Modes and Risks

1. **Existing saves with `bio`** — Saves that have `bio` as a single string will keep it. The new `bio_appearance`/`bio_background` fields will be `None`. UI should handle this gracefully (fall back to `bio` if `bio_appearance` is empty).

2. **Existing saves with `departed_summary`** — Will be silently kept in the dict (Pydantic extra fields). The checker will no longer require it. The UI should use `departed_reason` only.

3. **Existing saves with `last_seen`** — Will be silently kept in the dict. The UI must check for `last_presence_turn` first, fall back to `last_seen` if needed for backward compatibility.

4. **Existing saves with `nearby_since_turn`** — Will be silently kept. The engine will no longer write it. The nearby decay check must use `last_presence_turn` instead.

5. **LLM prompt transition** — The extraction prompt must clearly instruct for the new field names. The LLM may need a few turns to adapt if the prompt changes mid-game.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `allegiance` | `CompendiumNpcUpdate` (models.py:248) | Silently dropped; never stored or displayed |
| `allegiance` | Extraction prompt (extract_scene_system.j2:33, 53) | Remove field + durable updates mention |
| `allegiance` | `state/npcs.py:275-276` | Remove write block |
| `nearby_since_turn` | `CompendiumEntry` (dict-level) | Dead code; set but never surfaced |
| `nearby_since_turn` | `turn.py:1186` | Remove from new NPC creation |
| `nearby_since_turn` | `delta_builder.py:225` | Remove from location change |
| `nearby_since_turn` | `turn.py:1294` | Replace with `last_presence_turn` |
| `departed_summary` | `CompendiumNpcUpdate` (models.py:259) | Consolidated into `departed_reason` |
| `departed_summary` | Extraction prompt (extract_scene_system.j2:43, 47) | Remove field + description |
| `departed_summary` | `state/npcs.py:312-313` | Remove write block |
| `departed_summary` | `npc_presence.py:56-62` | Remove checker |
| `last_seen` | `CompendiumEntry` (dict-level) | Replaced by `last_presence_turn` |
| `last_seen` | `turn.py:1189-1193` | Remove stamping |
| `last_seen` | `state/npcs.py:257-261` | Remove on first appearance |
| `last_seen` | `state/npcs.py:239-240` | Remove merge |
| `last_seen` | `build_npc_roster.py:52` | Remove from output |
| `last_seen` | `NPCRosterEntryBlock` (context.py:204) | Remove field |
| `last_seen` | `_npc_roster.j2:16` | Remove rendering |
| `last_seen` | `_state_left.html:33, 148, 162` | Remove rendering |
| `last_seen` | `prompt_eval.py:63` | Remove from mock data |

## What Is Unchanged

- `CompendiumEntry` stored state shape (dict-level) — still `dict[str, Any]`
- `CompendiumNpcUpdate` model structure — only field renames/additions, no structural changes
- NPC presence semantics (present/nearby/known/departed/archived)
- Nearby decay TTL (2 turns) — still triggers nearby→known transition
- Departed auto-archive TTL (3 turns) — still triggers departed→archived transition
- `departed_turn` — still set on first `presence: "departed"`, still used for archive TTL
- `first_seen_turn` — still set on first appearance, still used in narrator prompt
- `bond` field — unchanged
- `personality` field — unchanged
- `notes` field — unchanged
- `position` field — unchanged
- `aliases` field — unchanged
- `motivation`, `fear`, `leverage` fields — unchanged
- `title` field — unchanged
- `name` field — unchanged
- `id` field — unchanged
- `presence` field — unchanged
- `departed_turn` field — unchanged
- `CompendiumEntry` in `pack.py` (seed model) — only field renames
- `SeedPC.bio` — PC bio stays as single string
- `StateExtractResult.condition_change_reason` — model field unchanged
- `state.meta.last_condition_change_reason` — storage unchanged
- `build_npc_roster()` function signature — only output dict keys change
- `NPCRosterEntryBlock` model — only field renames/additions

## New Model Shapes

### `CompendiumNpcUpdate` (updated)

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio_appearance: str | None = None   # physical presentation
    bio_background: str | None = None   # backstory, personality, reputation
    aliases: list[str] = Field(default_factory=list)
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None
    notes: str | None = None
    position: str | None = None
    first_seen_turn: int | None = None
    personality: str | None = None
    bond: str | None = None
    departed_reason: str | None = None     # 1-2 sentence prose describing departure
    departed_turn: int | None = None
```

### `CompendiumEntry` (dict-level, stored state)

New keys added (engine-managed, not extracted):
- `last_presence_turn: int | None` — last turn NPC was `present` or `nearby`

Keys removed:
- `last_seen` (dict)
- `nearby_since_turn` (int)

Keys renamed:
- `departed_summary` → removed (consolidated into `departed_reason`)

Keys renamed:
- `bio` → `bio_appearance`, `bio_background`

### `NPCRosterEntryBlock` (updated)

```python
class NPCRosterEntryBlock(BaseModel):
    id: str
    name: str
    title: str | None = None
    bio_appearance: str | None = None
    bio_background: str | None = None
    presence: NpcPresence
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    notes: str | None = None
```

### `CompendiumEntry` (seed model, `pack.py`)

```python
class CompendiumEntry(BaseModel):
    model_config = {"extra": "allow"}
    name: str | None = None
    title: str | None = None
    bio_appearance: str | None = None
    bio_background: str | None = None
    bond: str | None = None
    presence: str | None = None
    notes: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    personality: str | None = None
```

## Context for Implementing LLMs

- `ccya/models.py:242-260` — `CompendiumNpcUpdate` model; field renames/additions
- `ccya/state/npcs.py:250-323` — `apply_npc_scene_management()`; where compendium entries are written; remove `last_seen`, `nearby_since_turn`, `allegiance`; add `last_presence_turn`; handle bio split
- `ccya/engine/turn.py:1177-1193` — `last_seen` stamping; remove; add `last_presence_turn` tracking
- `ccya/engine/turn.py:1294` — `nearby_since_turn` usage for decay; replace with `last_presence_turn`
- `ccya/engine/turn.py:1186` — `nearby_since_turn` on new NPC creation; remove
- `ccya/state/delta_builder.py:225` — `nearby_since_turn` on location change; remove
- `ccya/engine/npc_roster.py:14-81` — `build_npc_roster()`; update output dict keys for bio split, remove `last_seen`
- `ccya/prompts/context.py:195-204` — `NPCRosterEntryBlock`; update for bio split, remove `last_seen`
- `ccya/prompts/extract_scene_system.j2:26-47` — extraction prompt; bio split, departed consolidation, allegiance removal
- `ccya/prompts/sections/_npc_roster.j2:7` — roster prompt; bio split rendering, departed_reason usage
- `ccya/prompts/generate_seed_system.j2:36` — seed prompt; bio field renames
- `ccya/pack.py:36-48` — seed compendium model; bio field renames
- `ccya/templates/_state_left.html:12-37, 144-165` — UI templates; bio split rendering, last_seen removal, departed rendering
- `ccya/templates/_state_right.html:52` — UI template; add condition_change_reason tooltip
- `ccya/ev/checkers/npc_presence.py:48-62` — checker; remove departed_summary check
- `ccya/ev/prompt_eval.py:63` — prompt eval mock data; remove last_seen
