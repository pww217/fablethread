# NPC UI & Model Design

## Purpose

Design for splitting NPC bio into appearance/background, combining departed fields, computing relative "turns ago" for last-seen tracking, adding condition_change_reason to PC panel, and removing unused stub fields (allegiance, nearby_since_turn). Reference: "This document is the design authority for plans implementing these changes."

## Problem Statement

The NPC model has several issues:

1. **`bio` conflates two distinct dimensions.** The extraction prompt already asks for "(1) appearance and demeanor" and "(2) personality traits or tangible facts" in a single string, but the model stores it as one field. The UI renders it as a single blob. Physical appearance and backstory serve different purposes — appearance should be visible alongside position (which is already separate).

2. **`departed_reason` and `departed_summary` are redundant.** Both are extracted and stored, but `departed_summary` is never rendered in the UI. Only `departed_reason` (a short label) appears in the roster line. The summary exists but is invisible.

3. **`last_seen` stores absolute turn number instead of computing relative.** The dict `{turn, location_id, location_name}` is stored per NPC. The UI shows the raw turn number. Computing "X turns ago" at render time is more useful for players and for the narrator prompt (knowing when to reintroduce characters).

4. **`allegiance` is extracted but never stored.** `CompendiumNpcUpdate` has the field, `state/npcs.py:275` writes it, but `CompendiumEntry` has no corresponding field — Pydantic silently drops it. NPC allegiance is a stub.

5. **`nearby_since_turn` is dead code.** Set on entry creation and nearby transitions, read in `turn.py:1294`, but the computed value is never surfaced anywhere.

6. **`condition_change_reason` is not shown in the UI.** It's stored in `state.meta.last_condition_change_reason` and surfaced to the narrator prompt, but the PC panel's Player header tooltip doesn't display it (unlike the Inventory header which does).

## Constraints

- Must not break existing saves. Extra fields in saved state are silently dropped by Pydantic on load.
- Must not break the extraction pipeline. Prompt schema changes must be backward-compatible with retries.
- `last_presence_turn` must be computed at render time (current_turn - last_presence_turn), not stored as a derived value.
- `departed_reason` will absorb the combined text (short label + summary prose merged into one string).
- `bio.background` and `bio.appearance` must both be optional (`str | None`) to handle existing saves and NPCs created before the split.

## Non-goals

- Do not add `allegiance` back to the model. Only remove it.
- Do not add `first_seen_turn` to the compendium tooltip UI. It's only used in the narrator prompt.
- Do not change how `departed_turn` is used for auto-archive (3-turn threshold).
- Do not change the `presence` enum values (present/nearby/known/departed).
- Do not add new fields for tracking NPC reintroduction timing beyond `last_presence_turn`.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Bio split | `bio: str` → `bio_background: str | None`, `bio_appearance: str | None` | Extraction prompt already asks for both dimensions separately. Appearance should be visible alongside position (which is already top-level). |
| Departed fields combine | `departed_reason` absorbs `departed_summary` text. Prompt asks for "short label — long prose" in one field. | `departed_summary` is never rendered. One field is simpler for extraction and storage. |
| Last-seen relative | Replace `last_seen: dict` with `last_presence_turn: int | None`. Compute "X turns ago" at render time. | Absolute turn number is not useful to players. Relative turns ago is actionable for both UI and narrator prompt. |
| Keep location name | `last_seen.location_name` preserved as a separate field on `CompendiumEntry`. | Departed NPCs need to show where they were last seen. Location name is useful context. |
| Remove allegiance | Remove from `CompendiumNpcUpdate`, extraction prompts, and `npcs.py` merge logic. | It's a stub — extracted but never stored or displayed. |
| Remove nearby_since_turn | Remove from `CompendiumEntry`, `CompendiumNpcUpdate`, and all write/read sites. | Dead code — value is read but never surfaced. |
| Keep first_seen_turn | Retain on `CompendiumEntry`. Only used in narrator prompt as `T{{ npc.first_seen_turn }}`. | Minimal cost, serves a purpose. |
| Keep departed_turn | Retain on `CompendiumEntry`. Used for 3-turn auto-archive. | Required for engine logic. |
| condition_change_reason in UI | Add to Player header tooltip in `_state_right.html`, mirroring Inventory header pattern. | Player should see why their condition changed this turn. |
| LastSeenBlock simplified | `LastSeenBlock` keeps `location_name` only. Remove `turn` and `location_id`. | Only location name is needed for UI display. Turn is computed at render time. |

## Open Questions

None.

---

## Current State — What Exists

### NPC Storage: `CompendiumEntry` (`ccya/models.py:240–273`)

Runtime storage for all NPCs. Dict-based, stored in `state.compendium.npcs[npc_id]`. Fields:

```
id: str
name: str | None
title: str | None
bio: str | None
bond: str | None
presence: str  # present | nearby | known | departed
notes: str | None
motivation: str | None
fear: str | None
leverage: str | None
personality: str | None
aliases: list[str]
allegiance: str | None  # written but silently dropped (no field on model)
position: str | None
first_seen_turn: int | None
nearby_since_turn: int | None
departed_turn: int | None
departed_reason: str | None
departed_summary: str | None
last_seen: dict | None  # {turn: int, location_id: str, location_name: str}
```

### NPC Extraction: `CompendiumNpcUpdate` (`ccya/models.py:242–260`)

Pydantic model for LLM extraction output. Same fields as `CompendiumEntry` minus engine-managed fields (`first_seen_turn`, `nearby_since_turn`, `departed_turn`, `last_seen`).

### NPC Merge: `apply_npc_scene_management()` (`ccya/state/npcs.py:220–320`)

Reads `CompendiumNpcUpdate` and merges into `CompendiumEntry`. Key operations:
- Line 237–238: Sets `first_seen_turn` on new entries only
- Line 255: Sets `first_seen_turn` on creation
- Line 257–261: Sets `last_seen` dict with turn/location_id/location_name
- Line 275–276: Writes `allegiance` (silently dropped — no field on model)
- Line 315: Sets `departed_turn` on first departed
- Line 319: Sets `nearby_since_turn` on nearby transition

### NPC Prompt Context: `NPCRosterEntryBlock` (`ccya/prompts/context.py:189–204`)

Typed block for prompt rendering. Subset of `CompendiumEntry`:

```
id: str
name: str
title: str | None
bio: str | None
presence: NpcPresence
motivation: str | None
fear: str | None
leverage: str | None
notes: str | None
last_seen: LastSeenBlock | None
```

### LastSeenBlock (`ccya/prompts/context.py:181–186`)

```
turn: int
location_id: str
location_name: str
```

Used in `_npc_roster.j2:16` to show "last seen: [location_name]".

### Narrator Prompt: `_npc_roster.j2`

Renders NPC roster for narrator. Line 7: departed NPCs show `departed_reason` after presence tag. Line 16: shows `last_seen.location_name` for all NPCs.

### UI: Compendium Tooltip (`_state_left.html`)

Lines 33, 148–149, 162: Shows `last_seen.turn` and `last_seen.location_name` for departed NPCs. No `departed_summary` rendering.

### UI: Player Header Tooltip (`_state_right.html`)

Lines 52–56: Inventory header shows tooltip with `inventory_change_reason`. Player header (line 2) has no tooltip for `condition_change_reason`.

### Extraction Prompt (`extract_scene_system.j2`)

Lines 31: Bio instruction asks for two sentences (appearance + background) as one string.
Lines 42–47: `departed_reason` (short label) and `departed_summary` (1-2 sentence prose) as separate fields.
Line 33: `allegiance` extracted as `"faction_or_alignment"`.

### Seed System Prompt (`generate_seed_system.j2`)

Line 36: Compendium schema shows `bio: string` (single field).

### State I/O (`state/io.py`)

Line 85: `allegiance: None` in default PC state (not NPC state — PC allegiance is real).

### Problems with Current State

- **`bio` is one string** — extraction prompt asks for two dimensions but they're stored together. UI renders as one blob.
- **`departed_summary` is invisible** — extracted, stored, but never rendered. Only `departed_reason` appears.
- **`last_seen` stores absolute turn** — not useful to players. Computed relative value would be better.
- **`allegiance` is a stub** — extracted but never stored or displayed. Wastes LLM output space.
- **`nearby_since_turn` is dead code** — written and read but never surfaced.
- **`condition_change_reason` not in UI** — stored in `state.meta` but not shown to player.

---

## Proposed Solution

### Core Changes

#### 1. Bio Split

`CompendiumEntry` gains two fields:

```
bio_background: str | None   # backstory, personality, reputation
bio_appearance: str | None   # physical presentation, bearing, features
```

`bio` is removed from `CompendiumEntry`. Both new fields are optional to handle existing saves.

`CompendiumNpcUpdate` gains the same two fields, replaces `bio`.

Extraction prompt (`extract_scene_system.j2`) updated to ask for two separate fields:
- `bio_background`: "2–3 sentences — backstory, personality, reputation, what shaped them"
- `bio_appearance`: "1–2 sentences — physical presentation, bearing, posture, expression, distinctive features"

`NPCRosterEntryBlock` gains `bio_background` and `bio_appearance`, removes `bio`.

#### 2. Departed Fields Combine

`departed_summary` is removed from `CompendiumEntry` and `CompendiumNpcUpdate`.

`departed_reason` absorbs the combined text. Extraction prompt updated to ask for:
- `departed_reason`: "short label followed by 1–2 sentence prose — e.g. 'killed in battle — Caught in the crossfire defending the village gates.'"

`_npc_roster.j2` line 7: departed NPCs show combined `departed_reason` after presence tag (format unchanged, content is now combined).

#### 3. Last-Seen Relative

`last_seen` dict is removed from `CompendiumEntry` and `CompendiumNpcUpdate`.

New field on `CompendiumEntry`:

```
last_presence_turn: int | None   # last turn NPC was present or nearby
last_seen_location: str | None   # location name from last presence turn
```

`last_presence_turn` is set/updated in `apply_npc_scene_management()` when presence transitions to `present` or `nearby`.

`last_seen_location` is set/updated alongside `last_presence_turn` from the current location.

"X turns ago" is computed at render time: `current_turn - last_presence_turn`.

`LastSeenBlock` is simplified:

```
location_name: str
```

`turn` and `location_id` are removed. Only `location_name` is needed for UI display.

`build_npc_roster()` in `npcs.py` updated to populate `last_seen.location_name` from `last_seen_location` on the compendium entry.

#### 4. Allegiance Removed

`allegiance` removed from `CompendiumNpcUpdate`, `extract_scene_system.j2` extraction prompt, and `npcs.py` merge logic.

`allegiance` remains on `CompendiumEntry` for now (it's written to dict but silently ignored by Pydantic extra="ignore" — removing it from the model is a separate cleanup).

#### 5. Nearby_Since_Turn Removed

`nearby_since_turn` removed from `CompendiumEntry`, `CompendiumNpcUpdate`, `state/npcs.py:319`, and `delta_builder.py:225`.

`turn.py:1294` read of `nearby_since` is removed (dead code).

#### 6. Condition_Change_Reason in UI

`_state_right.html` Player header (line 2) gains a tooltip mirroring the Inventory header pattern (lines 52–56):

```html
<div class="panel-header" title="{{ state.meta.get('last_condition_change_reason', '') }}">
    <h2>Player</h2>
</div>
```

Only shown if `state.meta.last_condition_change_reason` is populated (non-empty string).

#### 7. Compendium Tooltip Updated

Departed NPCs in `_state_left.html`:
- Line 162: Replace `last_seen.turn` with computed relative turns: `{{ (turn_no - n.last_presence_turn) if n.last_presence_turn else '?' }} turns ago`
- Show combined departed_reason: `{{ n.departed_reason }}`
- Show last_seen_location: `{{ n.last_seen_location or 'unknown' }}`

Format: `Last Seen: [location] — [departed_reason] (X turns ago)`

Non-departed NPCs:
- Lines 148–149: Replace `last_seen.turn` and `last_seen.location_name` with relative turns: `{{ (turn_no - n.last_presence_turn) if n.last_presence_turn else '?' }} turns ago`
- Show last_seen_location: `{{ n.last_seen_location or 'unknown' }}`

#### 8. Narrator Prompt Updated

`_npc_roster.j2` line 16: Update to show relative turns ago instead of absolute turn number:

```jinja2
{% if n.last_seen and n.last_seen.location_name %} | last seen: {{ n.last_seen.location_name }}{% if n.last_seen.turn %} ({{ turn_no - n.last_seen.turn }} turns ago){% endif %}{% endif %}
```

Wait — this uses `n.last_seen.turn` which will be removed. The roster block needs to pass `turn_no` or compute relative turns.

Alternative: `NPCRosterEntryBlock` gains a `turns_ago: int | None` computed field, or the roster template receives `turn_no` from the boundary.

Actually, `NPCRosterEntryBlock` is used in multiple prompt boundaries (RulingBoundary, NarratorBoundary, SceneExtractBoundary, StorytellerBoundary). Each boundary has access to `turn_no` or `meta.turn`. The roster template should compute relative turns from `turn_no` and `last_seen.turn`.

But `last_seen.turn` is being removed. So `NPCRosterEntryBlock` needs to either:
(a) Gain a `turns_ago: int | None` computed field, or
(b) Gain `last_presence_turn: int | None` and have the template compute relative turns.

Option (b) is cleaner — the roster block gets `last_presence_turn` and the template computes relative turns using the boundary's `turn_no`.

But `_npc_roster.j2` doesn't have access to `turn_no` — it's included from multiple templates. Let me check what variables are available.

In `narrate_user.j2`: `meta` is available (line 76: `meta.get('turn', '?')`).
In `ruling_user.j2`: `turn_no` is available.
In `extract_scene_user.j2`: `turn_no` is available.
In `storytell_user.j2`: `turn_no` is available.

So the roster template can access `turn_no` or `meta.turn` depending on context. The roster template should compute relative turns using whatever is available.

Actually, the simplest approach: `NPCRosterEntryBlock` gains `last_presence_turn: int | None` (replacing `last_seen: LastSeenBlock | None`). The roster template computes relative turns using `turn_no` (available in all boundary contexts).

Wait — `_npc_roster.j2` line 16 already has a complex conditional for `last_seen`. Let me simplify:

```jinja2
{% if n.last_seen_location %} | last seen: {{ n.last_seen_location }}{% if n.last_presence_turn is defined and n.last_presence_turn %} ({{ (turn_no if turn_no is defined else meta.turn) - n.last_presence_turn }} turns ago){% endif %}{% endif %}
```

This is getting complex for a template. Better approach: have `NPCRosterEntryBlock` compute `turns_ago` as a derived field.

Actually, the cleanest approach: `NPCRosterEntryBlock` gains `last_presence_turn: int | None` and the roster template receives `turn_no` from the boundary. All boundaries have `turn_no` or `meta.turn` available.

Let me simplify: `NPCRosterEntryBlock` replaces `last_seen: LastSeenBlock | None` with:

```
last_presence_turn: int | None
last_seen_location: str | None
```

The roster template computes relative turns:

```jinja2
{% if n.last_seen_location %} | last seen: {{ n.last_seen_location }}{% if n.last_presence_turn %} ({{ (turn_no if turn_no is defined else meta.turn) - n.last_presence_turn }} turns ago){% endif %}{% endif %}
```

This works because:
- `turn_no` is defined in `ruling_user.j2`, `extract_scene_user.j2`, `storytell_user.j2`
- `meta.turn` is defined in `narrate_user.j2` (line 76)

#### 9. Seed System Prompt Updated

`generate_seed_system.j2` line 36: Update compendium schema to show `bio_background` and `bio_appearance` instead of `bio`.

### Data Flow

```
LLM Extraction (extract_scene_system.j2)
    ↓
CompendiumNpcUpdate (bio_background, bio_appearance, departed_reason combined, last_presence_turn)
    ↓
apply_npc_scene_management() (state/npcs.py)
    ↓
CompendiumEntry (bio_background, bio_appearance, departed_reason combined, last_presence_turn, last_seen_location)
    ↓
build_npc_roster() (npcs.py)
    ↓
NPCRosterEntryBlock (bio_background, bio_appearance, departed_reason, last_presence_turn, last_seen_location)
    ↓
Prompt Templates (_npc_roster.j2) + UI Templates (_state_left.html)
```

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Keep `last_seen` dict, add computed `turns_ago` field | Adds redundancy. `last_seen.turn` becomes unused. Cleaner to replace entirely. |
| Keep `departed_summary` separate, render it in UI | Only one extra field to maintain. Combining is simpler for extraction and storage. |
| Add `allegiance` to `CompendiumEntry` | It's a stub with no clear use case. Remove until needed rather than add dead code. |
| Compute relative turns in Python, pass to template | Template computation is simpler and avoids duplicating the formula across multiple boundary contexts. |
| Keep `bio` as single string, add `bio_appearance` as separate | Two fields for the same concept is confusing. Split both into named sub-fields. |

---

## Failure Modes and Risks

| Risk | Impact | Mitigation |
|---|---|---|
| LLM doesn't emit new bio fields on first extraction | NPCs have `bio_background: None` or `bio_appearance: None` | Both fields are optional. Existing NPCs keep their bio as `bio_background` (engine migration step). |
| Extraction prompt change causes LLM to skip bio fields | Missing bio for new NPCs | Prompt examples should show both fields. Retry loop catches missing required fields. |
| `last_presence_turn` not set for NPCs created before migration | Computed turns_ago is None/unknown | Both fields are optional. UI shows "unknown" when not available. |
| `departed_reason` combined text is too long for roster line | Roster line becomes unwieldy | Roster line truncation is handled by template (CSS or Jinja truncate filter). |
| Seed system prompt change causes seed generation to fail | New games have broken NPC entries | Prompt schema is TypeScript-style comment, not enforced. LLM may not follow exactly. |
| `LastSeenBlock` removal breaks other prompt boundaries | RulingBoundary, SceneExtractBoundary, StorytellerBoundary all use it | All boundaries updated to use new `NPCRosterEntryBlock` shape. |

---

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `bio: str` | `CompendiumEntry`, `CompendiumNpcUpdate` | Replaced by `bio_background` + `bio_appearance` |
| `departed_summary: str` | `CompendiumEntry`, `CompendiumNpcUpdate` | Absorbed into `departed_reason` |
| `last_seen: dict` | `CompendiumEntry`, `CompendiumNpcUpdate` | Replaced by `last_presence_turn` + `last_seen_location` |
| `allegiance: str` | `CompendiumNpcUpdate`, `extract_scene_system.j2`, `npcs.py:275` | Stub — never stored or displayed |
| `nearby_since_turn: int` | `CompendiumEntry`, `CompendiumNpcUpdate`, `npcs.py:319`, `delta_builder.py:225`, `turn.py:1294` | Dead code |
| `turn: int` | `LastSeenBlock` | Only `location_name` needed |
| `location_id: str` | `LastSeenBlock` | Only `location_name` needed |

---

## What Is Unchanged

- `CompendiumEntry` fields: `id`, `name`, `title`, `bond`, `presence`, `notes`, `motivation`, `fear`, `leverage`, `personality`, `aliases`, `position`, `first_seen_turn`, `departed_turn`, `departed_reason` (kept, combined)
- `CompendiumNpcUpdate` fields: `id`, `name`, `title`, `aliases`, `motivation`, `fear`, `leverage`, `presence`, `notes`, `position`, `personality`, `bond`, `departed_turn`, `departed_reason` (kept, combined)
- `NPCRosterEntryBlock` fields: `id`, `name`, `title`, `presence`, `motivation`, `fear`, `leverage`, `notes`, `departed_reason` (kept, combined)
- `PlayerBlock`, `LocationBlock`, `InventoryBlock`, `ArcThreadBlock`, `WorldStateBlock`, `ChronicleEntryBlock`, `PacingBlock`
- All boundary models: `RulingBoundary`, `NarratorBoundary`, `SceneExtractBoundary`, `StateExtractBoundary`, `StorytellerBoundary`, `NarratorSystemBoundary`
- `TEMPLATE_CONTRACTS` mapping
- `NpcPresence` enum from `models.py`
- `CompendiumNpcUpdate` alias resolution, dedup, group merging, personality assignment, presence transitions, auto-archive, auto-demotion, note stripping, touch order
- PC allegiance (`state.pc.allegiance`) and its use in narrator prompt
- `condition_change_reason` storage in `state.meta.last_condition_change_reason` and narrator prompt usage
- `StateExtractResult` model (`ccya/models.py:325–346`)
- Extraction retry loop, coercion, dedup (`extraction.py`)
- Ruling pipeline (`ruling.py`), narrate pipeline (`engine/turn.py:743–845`)
- Presence badge rendering in `_state_left.html` line 33

---

## New Model Shapes

### `CompendiumEntry` (excerpt — fields that change)

```python
class CompendiumEntry(BaseModel):
    bio_background: str | None = None
    bio_appearance: str | None = None
    departed_reason: str | None = None          # combined: "label — prose"
    last_presence_turn: int | None = None       # last turn present or nearby
    last_seen_location: str | None = None       # location name from last presence turn
    # ... all other fields unchanged ...
```

### `CompendiumNpcUpdate` (excerpt — fields that change)

```python
class CompendiumNpcUpdate(BaseModel):
    bio_background: str | None = None
    bio_appearance: str | None = None
    departed_reason: str | None = None          # combined: "label — prose"
    last_presence_turn: int | None = None       # set by engine on presence transition
    # ... all other fields unchanged ...
    # allegiance: removed
    # departed_summary: removed
    # bio: removed
    # last_seen: removed
    # nearby_since_turn: removed
```

### `NPCRosterEntryBlock` (excerpt — fields that change)

```python
class NPCRosterEntryBlock(BaseModel):
    bio_background: str | None = None
    bio_appearance: str | None = None
    departed_reason: str | None = None
    last_presence_turn: int | None = None
    last_seen_location: str | None = None
    # ... all other fields unchanged ...
    # bio: removed
    # last_seen: removed
```

### `LastSeenBlock` (simplified)

```python
class LastSeenBlock(BaseModel):
    location_name: str
    # turn: removed
    # location_id: removed
```

---

## Context for Implementing LLMs

| File | What | Why |
|---|---|---|
| `ccya/models.py:240–273` | `CompendiumEntry` model definition | Split bio, add departed/last-seen fields, remove stubs |
| `ccya/models.py:242–260` | `CompendiumNpcUpdate` model definition | Same changes as CompendiumEntry |
| `ccya/state/npcs.py:220–320` | `apply_npc_scene_management()` | Update merge logic for new fields, remove old writes |
| `ccya/state/npcs.py:35–72` | Alias map building | Unchanged |
| `ccya/state/npcs.py:74–100` | Alias-first naming | Unchanged |
| `ccya/state/npcs.py:102–150` | Group NPC merging | Unchanged |
| `ccya/state/npcs.py:290–310` | Personality assignment | Unchanged |
| `ccya/state/npcs.py:322–340` | Auto-archive | Unchanged |
| `ccya/state/npcs.py:342–360` | Auto-demotion | Unchanged |
| `ccya/state/npcs.py:362–370` | Note stripping | Unchanged |
| `ccya/state/npcs.py:372–380` | Touch order | Unchanged |
| `ccya/state/delta_builder.py:225` | `nearby_since_turn` assignment | Remove |
| `ccya/engine/turn.py:1186` | `nearby_since_turn` write | Remove |
| `ccya/engine/turn.py:1189–1193` | `last_seen` population | Remove |
| `ccya/engine/turn.py:1294` | `nearby_since` read | Remove |
| `ccya/engine/turn.py:1304` | `departed_turn` read | Unchanged |
| `ccya/prompts/context.py:181–186` | `LastSeenBlock` | Simplify to `location_name` only |
| `ccya/prompts/context.py:189–204` | `NPCRosterEntryBlock` | Update fields |
| `ccya/prompts/extract_scene_system.j2:31` | Bio extraction instruction | Split into two fields |
| `ccya/prompts/extract_scene_system.j2:42–47` | Departed fields | Combine into one |
| `ccya/prompts/extract_scene_system.j2:33` | Allegiance | Remove |
| `ccya/prompts/sections/_npc_roster.j2:7` | Departed roster line | Show combined departed_reason |
| `ccya/prompts/sections/_npc_roster.j2:16` | Last seen roster line | Compute relative turns |
| `ccya/prompts/narrate_user.j2:14` | Roster include | Unchanged (template handles it) |
| `ccya/prompts/generate_seed_system.j2:36` | Compendium schema | Update bio fields |
| `ccya/templates/_state_right.html:2` | Player header | Add condition_change_reason tooltip |
| `ccya/templates/_state_right.html:52–56` | Inventory header | Reference pattern for tooltip |
| `ccya/templates/_state_left.html:33` | Presence badge | Unchanged |
| `ccya/templates/_state_left.html:148–149` | Last seen detail | Replace with relative turns + location |
| `ccya/templates/_state_left.html:162` | Departed last seen | Replace with combined departed_reason + relative turns |
| `ccya/state/io.py:85` | Default PC allegiance | Unchanged (PC allegiance is real) |
