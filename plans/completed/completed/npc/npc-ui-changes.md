# NPC UI & Model Changes

## Purpose

Plan for restructuring NPC compendium fields: split `bio`, consolidate `departed_reason`/`departed_summary`, remove dead fields (`allegiance`, `nearby_since_turn`, `last_seen`), add `last_presence_turn`, and surface `condition_change_reason` in UI.

## Problem Statement

The NPC compendium has several issues: `bio` mixes appearance and background into a single string despite the extraction prompt already instructing for two aspects; `departed_reason` and `departed_summary` are redundant with `departed_summary` never shown in UI; `allegiance` is silently dropped by Pydantic; `nearby_since_turn` is dead code; `last_seen` stores absolute turn numbers that are never computed into "X turns ago"; and `condition_change_reason` is not surfaced in the UI despite following an existing pattern.

## Constraints

- `CompendiumNpcUpdate` is the extraction model — changes affect the LLM prompt contract
- `CompendiumEntry` is stored as `dict[str, Any]` — Pydantic extra fields are silently dropped on load
- Existing saves must survive the changes
- Prompt templates must match new field names
- UI templates must render new field structure
- Tests are temporarily removed during refactor (per AGENTS.md)

## Non-goals

- No changes to NPC presence semantics
- No changes to TTL logic (nearby decay, departed archive)
- No changes to PC model fields
- No changes to seed generation beyond field renames

## Solution

Five phases: models first (foundation for everything), then extraction + engine (tightly coupled), then context + prompt templates (rendering layer), then UI templates (player-facing), then checkers + eval (validation layer). Each phase is independently executable.

## Firm decisions

1. Bio split uses flat fields: `bio_appearance`, `bio_background` (not nested dict)
2. `departed_summary` removed; `departed_reason` becomes 1-2 sentence prose
3. `allegiance` removed from `CompendiumNpcUpdate` and extraction prompts
4. `nearby_since_turn` removed; nearby decay uses `last_presence_turn`
5. `last_seen` removed; `last_presence_turn` added for "X turns ago" computation
6. `last_presence_turn` is engine-managed (dict-level, no model field)
7. `condition_change_reason` added to Player header tooltip following Inventory pattern
8. UI must handle backward compatibility: fall back to `bio` if `bio_appearance` is empty; fall back to `last_seen` if `last_presence_turn` is absent

## Risks, Ambiguities, and Blockers

- **LLM prompt transition**: The extraction prompt changes mid-game. The LLM may need a few turns to adapt. This is inherent to prompt changes.
- **Existing saves with `bio`**: Saves with `bio` as single string will keep it. UI must fall back gracefully.
- **Existing saves with `last_seen`**: Dict-level extra field will persist. UI must check `last_presence_turn` first, fall back to `last_seen`.

## Status

`completed`

## Phases

5 phases: models → extraction + engine → context + prompts → UI → checkers + eval

---

## Implementation — Phase 1: Models

### Context files to load

- `ccya/models.py` lines 242–260 (`CompendiumNpcUpdate`)
- `ccya/pack.py` lines 36–48 (`CompendiumEntry` seed model)

### Detailed steps

#### Step 1.1 — Update `CompendiumNpcUpdate` in models.py

**File:** `ccya/models.py`

**What:** Replace fields on `CompendiumNpcUpdate` (lines 242-260):

- Remove `bio: str | None = None` (line 246)
- Add `bio_appearance: str | None = None` (physical presentation — bearing, posture, expression, distinctive features)
- Add `bio_background: str | None = None` (backstory, personality, reputation — who they are as a person)
- Remove `allegiance: str | None = None` (line 248)
- Remove `departed_summary: str | None = None` (line 259)
- Update `departed_reason` comment on line 258 to: `# 1-2 sentence prose describing what happened`

**Why:** Field contract changes for bio split, allegiance removal, departed consolidation.

**Validation:** `rg "allegiance|departed_summary" ccya/models.py | rg "CompendiumNpcUpdate"` returns no matches.

#### Step 1.2 — Update `CompendiumEntry` in pack.py

**File:** `ccya/pack.py`

**What:** Replace fields on `CompendiumEntry` (lines 36-48):

- Remove `bio: str | None = None` (line 40)
- Add `bio_appearance: str | None = None`
- Add `bio_background: str | None = None`

**Why:** Seed-time compendium model must match extraction model field names.

**Validation:** `rg "bio:" ccya/pack.py | grep -v bio_appearance | grep -v bio_background"` returns no matches.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).

---

## Implementation — Phase 2: Extraction + Engine

### Context files to load

- `ccya/prompts/extract_scene_system.j2` lines 26–53 (extraction prompt)
- `ccya/state/npcs.py` lines 250–323 (`apply_npc_scene_management`)
- `ccya/engine/turn.py` lines 1177–1193 (`last_seen` stamping), 1186 (`nearby_since_turn`), 1294 (nearby decay)
- `ccya/state/delta_builder.py` line 225 (`nearby_since_turn` on location change)
- `ccya/engine/npc_roster.py` lines 14–81 (`build_npc_roster`)

### Detailed steps

#### Step 2.1 — Update extraction prompt

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Three changes:

1. Lines 31: Replace `bio` field description with two fields:
```
"bio_appearance": "Physical appearance and demeanor — bearing, posture, expression, distinctive features. One sentence.",
"bio_background": "Backstory, personality traits, reputation — who they are as a person. One sentence."
```

2. Line 33: Remove `allegiance` field entirely

3. Lines 42-47: Replace `departed_reason` + `departed_summary` with single field:
```
"departed_reason": "1-2 sentence prose describing what happened — required when presence is departed. Examples: killed in battle, sailed away after the raid, imprisoned for life"
```

4. Line 53: Remove `allegiance` from "Durable identity updates" list

**Why:** Prompt must instruct for new field names; allegiance is no longer extracted; departed fields consolidated.

**Validation:** `rg "allegiance|departed_summary" ccya/prompts/extract_scene_system.j2` returns no matches.

#### Step 2.2 — Update `apply_npc_scene_management` in state/npcs.py

**File:** `ccya/state/npcs.py`

**What:** Four changes:

1. Lines 267-268: Replace `bio` write with `bio_appearance` + `bio_background` writes:
```python
if comp_upd.bio_appearance is not None:
    entry["bio_appearance"] = _strip_non_ascii(comp_upd.bio_appearance)
if comp_upd.bio_background is not None:
    entry["bio_background"] = _strip_non_ascii(comp_upd.bio_background)
```

2. Lines 275-276: Remove `allegiance` write block

3. Lines 312-313: Remove `departed_summary` write block

4. Lines 257-261: Remove `last_seen` dict stamping on first appearance

5. Lines 239-240: Remove `last_seen` merge from alias merge logic

**Why:** Engine must write new field names; remove dead/consolidated fields.

**Validation:** `rg "allegiance|departed_summary|last_seen" ccya/state/npcs.py` returns no matches.

#### Step 2.3 — Update `last_seen` stamping in turn.py

**File:** `ccya/engine/turn.py`

**What:** Three changes:

1. Line 1177: Update comment from "Stamp last_seen on touched NPCs" to "Track last_presence_turn on touched NPCs"

2. Lines 1186: Remove `nearby_since_turn` from new NPC creation

3. Lines 1189-1193: Remove `last_seen` stamping block

4. After the compendium NPC update loop (around line 1194): Add `last_presence_turn` tracking:
```python
# Track last turn NPC was present or nearby
if entry.get("presence") in ("present", "nearby"):
    entry["last_presence_turn"] = turn_no
```

**Why:** Replace absolute `last_seen` dict with computed `last_presence_turn`; remove dead `nearby_since_turn`.

**Validation:** `rg "last_seen|nearby_since_turn" ccya/engine/turn.py` returns no matches.

#### Step 2.4 — Update nearby decay check in turn.py

**File:** `ccya/engine/turn.py`

**What:** Line 1294: Replace `nearby_since_turn` usage with `last_presence_turn`:

```python
# Old:
nearby_since = entry.get("nearby_since_turn")
if isinstance(nearby_since, int) and turn_no - nearby_since >= nearby_ttl:

# New:
last_present = entry.get("last_presence_turn")
if isinstance(last_present, int) and turn_no - last_present >= nearby_ttl:
```

**Why:** `nearby_since_turn` is removed; `last_presence_turn` serves the same purpose.

**Validation:** `rg "nearby_since_turn" ccya/engine/turn.py` returns no matches.

#### Step 2.5 — Update delta_builder.py

**File:** `ccya/state/delta_builder.py`

**What:** Line 225: Remove `entry["nearby_since_turn"] = state.get("meta", {}).get("turn", 0) + 1`

**Why:** `nearby_since_turn` is dead code being removed.

**Validation:** `rg "nearby_since_turn" ccya/state/delta_builder.py` returns no matches.

#### Step 2.6 — Update `build_npc_roster`

**File:** `ccya/engine/npc_roster.py`

**What:** Three changes:

1. Line 45: Replace `"bio": ...` with two entries:
```python
"bio_appearance": (entry.get("bio_appearance") or "").strip() or None,
"bio_background": (entry.get("bio_background") or "").strip() or None,
```

2. Line 52: Remove `"last_seen": entry.get("last_seen") or None,`

3. Line 26 (docstring): Update return keys description

**Why:** Output dict must match new field names; `last_seen` is removed.

**Validation:** `rg "last_seen" ccya/engine/npc_roster.py` returns no matches.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).

---

## Implementation — Phase 3: Context + Prompt Templates

### Context files to load

- `ccya/prompts/context.py` lines 190–204 (`NPCRosterEntryBlock`)
- `ccya/prompts/sections/_npc_roster.j2` (roster prompt)
- `ccya/prompts/generate_seed_system.j2` line 36 (seed prompt)

### Detailed steps

#### Step 3.1 — Update `NPCRosterEntryBlock`

**File:** `ccya/prompts/context.py`

**What:** Replace fields on `NPCRosterEntryBlock` (lines 195-204):

- Remove `bio: str | None = None` (line 198)
- Add `bio_appearance: str | None = None`
- Add `bio_background: str | None = None`
- Remove `last_seen: LastSeenBlock | None = None` (line 204)

Also update docstrings/comments that reference `last_seen`:
- Line 192: Remove `last_seen` from `NPCRosterEntryBlock` docstring
- Line 250: Remove `last_seen` from `SceneExtractBoundary` docstring
- Line 255: Remove `last_seen` from `npc_roster` field comment
- Line 284: Remove `last_seen` from `npc_roster` field comment

**Why:** Context model must match new field names; docstrings must be accurate.

**Validation:** `rg "last_seen" ccya/prompts/context.py` returns no matches.

#### Step 3.2 — Update `_npc_roster.j2`

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Two changes:

1. Line 7: Update roster line to use `bio_appearance` (fall back to `bio_background` if appearance is empty):
```
{% if n.presence == "departed" and n.departed_reason %} — {{ n.departed_reason }}{% endif %}{% if n.bio_appearance and n.presence != "departed" %} — {{ n.bio_appearance }}{% elif n.bio_background and n.presence != "departed" %} — {{ n.bio_background }}{% endif %}
```

2. Line 16: Remove `last_seen` rendering entirely

**Why:** Prompt must use new field names; `last_seen` is removed.

**Validation:** `rg "last_seen" ccya/prompts/sections/_npc_roster.j2` returns no matches.

#### Step 3.3 — Update `generate_seed_system.j2`

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Line 36: Update compendium schema to use `bio_appearance` + `bio_background` instead of `bio`.

**Why:** Seed prompt must match new field names.

**Validation:** `rg "bio:" ccya/prompts/generate_seed_system.j2 | grep -v bio_appearance | grep -v bio_background"` returns no matches.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).

---

## Implementation — Phase 4: UI Templates

### Context files to load

- `ccya/templates/_state_left.html` (sidebar + compendium)
- `ccya/templates/_state_right.html` (player + inventory)

### Detailed steps

#### Step 4.1 — Update `_state_left.html` present NPCs

**File:** `ccya/templates/_state_left.html`

**What:** Three changes:

1. Line 16: Replace `npc_bio` with `npc_bio_appearance` + `npc_bio_background`:
```python
{% set npc_bio_appearance = npc.get('bio_appearance', '') if npc is mapping else '' %}
{% set npc_bio_background = npc.get('bio_background', '') if npc is mapping else '' %}
```

2. Lines 29-30: Render appearance then background on separate lines:
```html
{% if npc_bio_appearance %}<p>{{ npc_bio_appearance }}</p>{% endif %}
{% if npc_bio_background %}<p>{{ npc_bio_background }}</p>{% endif %}
```

3. Line 33: Remove `last_seen.location_name` rendering

**Why:** UI must render new field structure; `last_seen` is removed.

**Validation:** `rg "last_seen" ccya/templates/_state_left.html` returns no matches.

#### Step 4.2 — Update `_state_left.html` compendium

**File:** `ccya/templates/_state_left.html`

**What:** Three changes:

1. Line 147: Replace `bio` with `bio_appearance` + `bio_background`:
```python
{% set bio_appearance = entry.get('bio_appearance', '') if entry is mapping else '' %}
{% set bio_background = entry.get('bio_background', '') if entry is mapping else '' %}
```

2. Lines 157-158: Render appearance then background:
```html
{% if bio_appearance %}<p>{{ bio_appearance }}</p>{% endif %}
{% if bio_background %}<p>{{ bio_background }}</p>{% endif %}
```

3. Line 162: For departed NPCs, render `last_presence_turn` as "X turns ago":
```html
{% if entry.get('last_presence_turn') and entry.get('presence') == 'departed' %}
{% set _turns_ago = (state.meta.get('turn', 0) - entry.get('last_presence_turn', 0)) %}
<p>Last seen: {{ (entry.get('last_seen') or {}).get('location_name', 'unknown location') }} ({{ _turns_ago }} turns ago)</p>
{% elif entry.get('last_seen') %}
<p>Last seen: {{ entry.last_seen.location_name }}</p>
{% endif %}
```

**Why:** UI must render new field structure; departed NPCs show computed "X turns ago" with backward compatibility for saves that still have `last_seen`.

**Validation:** `rg "last_seen" ccya/templates/_state_left.html` returns no matches (the fallback check for `entry.get('last_seen')` is intentional for backward compatibility).

#### Step 4.3 — Update `_state_right.html` Player header

**File:** `ccya/templates/_state_right.html`

**What:** After line 12 (after `state.pc.bio` tooltip), add `last_condition_change_reason` tooltip:

```html
{% if state.meta.get('last_condition_change_reason') %}
<div class="tooltip-body" data-md>{{ state.meta.get('last_condition_change_reason') }}</div>
{% endif %}
```

**Why:** Surface `condition_change_reason` in Player header following existing Inventory header pattern.

**Validation:** `curl localhost:8765` — Player header should show condition change reason tooltip when present.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).

---

## Implementation — Phase 5: Checkers + Eval

### Context files to load

- `ccya/ev/checkers/npc_presence.py` lines 48–62 (departed field checker)
- `ccya/ev/prompt_eval.py` line 63 (mock NPC data)

### Detailed steps

#### Step 5.1 — Update `npc_presence` checker

**File:** `ccya/ev/checkers/npc_presence.py`

**What:** Remove lines 56-62 (the `departed_summary` check):

```python
if not npc.get("departed_summary"):
    findings.append({
        "turn": turn,
        "check": "departed_summary",
        "detail": f"NPC '{npc_id}' is departed but missing departed_summary",
    })
    all_passed = False
```

**Why:** `departed_summary` is consolidated into `departed_reason`; only `departed_reason` check remains.

**Validation:** `rg "departed_summary" ccya/ev/checkers/npc_presence.py` returns no matches.

#### Step 5.2 — Update `prompt_eval.py` mock data

**File:** `ccya/ev/prompt_eval.py`

**What:** Line 63: Remove `"last_seen": ndata.get("last_seen", ""),`

**Why:** `last_seen` is removed from NPC data.

**Validation:** `rg "last_seen" ccya/ev/prompt_eval.py` returns no matches.

### Tests to write or update

None — tests are temporarily removed during refactor (per AGENTS.md).

---

## Documentation Updates

The following documentation must be updated as part of the final commit:

1. **`docs/repomap.md`** — Update `CompendiumNpcUpdate` field list (remove `bio`, `allegiance`, `departed_summary`; add `bio_appearance`, `bio_background`; remove `last_seen` references)
2. **`docs/repomap.md`** — Update `NPCRosterEntryBlock` field list
3. **`docs/repomap.md`** — Update compendium entry keys description (remove `last_seen`, `nearby_since_turn`; add `last_presence_turn`)
4. **`docs/architecture/`** — Update any pipeline/data shape docs that reference NPC compendium fields
