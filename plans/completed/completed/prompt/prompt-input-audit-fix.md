# Prompt Input Audit — Implementation Plan

## Purpose

Fix 27 correctness gaps and template duplication issues across the 5-call turn pipeline's prompt inputs, boundary models, ev.py tooling, and architecture docs.

## Problem Statement

The prompt input pipeline has drifted from its target state across four dimensions: Scene extraction lacks PC identity causing NPC hallucinations; the ev.py prompt-eval dump tool has 3 bugs preventing reliable prompt testing; template duplication across 4 user prompts creates maintenance burden and format inconsistency; and architecture docs contain 5 false input claims. These gaps are scattered across `ccya/engine/extraction.py`, `ccya/prompts/context.py`, `ccya/ev/prompt_eval.py`, 4 user templates, 7 section templates, and 2 architecture docs.

## Constraints

- Do not alter prompt wording unless fixing the PC identity gap (user prompt addition).
- Section templates must be backward compatible — existing templates using `{% include %}` must continue to work.
- ev.py changes must not alter the `build_prompt_context()` function signature.
- Architecture doc flowcharts must match actual code, not aspirational design.
- No tests to write or run (tests are temporarily removed per AGENTS.md).
- Run `make check` (lint + typecheck) as final validation.

## Non-goals

- No changes to system prompts.
- No changes to LLM output models or state shapes.
- No changes to the turn pipeline orchestration (run_turn, _run_extraction_pipeline).
- No changes to server routes, UI templates, or checkers.
- No migration paths — delete unused fields, don't design backwards compatibility.

## Solution

Three phases: (1) correctness fixes — PC identity in scene, boundary model gaps; (2) ev.py tooling — 3 bugs in prompt_eval.py; (3) template dedup — 4 shared section templates + 4 user template updates + 2 architecture doc corrections + repomap update. Each phase is independently executable with no cross-phase dependencies.

## Firm decisions

1. Scene gets `pc.name` in user prompt (not system prompt) — LLM needs to see the name in the user context to distinguish PC from NPCs.
2. `_inventory.j2` accepts either `state.inventory` (narrate style) or flat `inventory` — uses Jinja2 `{{ inventory | default(state.inventory, true) }}` pattern.
3. `_location.j2` accepts either `state.location` or flat `location` — same default pattern.
4. `_conditions.j2` accepts flat `conditions` list with `id`, `label`, `description` fields — `show_age` param controls age rendering. Handles both dict items and string/list items.
5. PC header section renders name + tagline only (no conditions) — conditions get their own section.
6. All 4 user templates use the same 3 section templates for inventory, location, and conditions — format differences eliminated by parameterization.
7. `RulingBoundary` gains `inventory`, `scene_phase`, `urgent_threads` fields.
8. `StorytellerBoundary` gains `scene_phase`, `curtain_call`, `allowed_beat_types`, `pending_beat`, `recent_beats`, `resolved_arcs` fields.
9. `SceneExtractBoundary` gains `pc_name` field.
10. Conditions render as bullet lists in all templates — format change from inline comma-separated lists in ruling/narrate.

## Risks, Ambiguities, and Blockers

**Risk:** Template dedup changes the rendered output of 4 user prompts. This may affect LLM output quality if the LLM has learned to expect the old format. Mitigation: the format changes are minor (bullet lists vs inline, consistent field names) and the LLM should handle them fine.

**Risk:** ev.py `build_prompt_context("scene")` currently returns `conditions` and `inventory` fields that the scene template doesn't use. Adding `npc_roster` and `pc_name` is additive — no breaking changes.

## Status

`completed`

## Phases

3 phases covering correctness fixes, ev.py tooling, and template dedup across 10 source files and 4 architecture docs.

---

## Implementation — Phase 1: Correctness fixes (PC identity + boundary models)

### Context files to load
- `ccya/engine/extraction.py` (lines 237-264)
- `ccya/prompts/extract_scene_user.j2` (lines 1-13)
- `ccya/prompts/context.py` (lines 209-297)

### Detailed steps

#### Step 1.1 — Pass pc.name to scene context

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_scene_messages()` (line 237), add `pc_name` to the context dict passed to `extract_scene_user.j2` (line 250-258). Extract from `state.get("pc", {}).get("name", "Unnamed")`.

**Why:** The scene LLM cannot distinguish the PC from NPCs without PC identity, causing PC-as-NPC hallucinations in `compendium_npc_update`.

**Validation:** `grep -n "pc_name" ccya/engine/extraction.py` — should show the new context key. Template renders `{{ pc_name }}` on a new line after location.

#### Step 1.2 — Add PC identity line to scene user template

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Add `## Player Character\n{{ pc_name }}` after the location section and before the NPC roster section.

**Why:** Provides PC identity to the scene LLM in the user prompt.

**Validation:** Render the template with test context and verify `## Player Character` + name appears before NPC roster.

#### Step 1.3 — Fix SceneExtractBoundary model

**File:** `ccya/prompts/context.py`

**What:** In `SceneExtractBoundary` (line 247-257), add one field:
```
pc_name: str = "Unnamed"
```

**Why:** The `SceneExtractBoundary` model is the contract between production code and `extract_scene_user.j2`. It's missing `pc_name` which the template now uses.

**Validation:** `grep -A 8 "class SceneExtractBoundary" ccya/prompts/context.py` — should show 5 fields including `pc_name`.

#### Step 1.4 — Fix RulingBoundary model

**File:** `ccya/prompts/context.py`

**What:** In `RulingBoundary` (line 209-217), add three fields:
```
inventory: list[dict[str, Any]] = Field(default_factory=list)
scene_phase: str = "SETUP"
urgent_threads: list[dict[str, Any]] = Field(default_factory=list)
```

**Why:** The `RulingBoundary` model is the contract between production code and `ruling_user.j2`. It's missing 3 fields that the template actually uses.

**Validation:** `grep -A 10 "class RulingBoundary" ccya/prompts/context.py` — should show all 9 fields.

#### Step 1.5 — Fix StorytellerBoundary model

**File:** `ccya/prompts/context.py`

**What:** In `StorytellerBoundary` (line 274-297), add six fields:
```
scene_phase: str = "SETUP"
curtain_call: str = ""
allowed_beat_types: list[str] = Field(default_factory=list)
pending_beat: dict[str, Any] | None = None
recent_beats: list[dict[str, Any]] = Field(default_factory=list)
resolved_arcs: list[dict[str, Any]] = Field(default_factory=list)
```

**Why:** The `StorytellerBoundary` model is the contract between production code and `storytell_user.j2`. It's missing 6 fields that the template actually uses.

**Validation:** `grep -A 20 "class StorytellerBoundary" ccya/prompts/context.py` — should show all 17 fields.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 2: ev.py prompt-eval dump — 3 bugs

### Context files to load
- `ccya/ev/prompt_eval.py` (lines 71-167)

### Detailed steps

#### Step 2.1 — Scene dump missing npc_roster and pc_name

**File:** `ccya/ev/prompt_eval.py`

**What:** In `build_prompt_context()` scene branch (lines 101-110), add `npc_roster` and `pc_name` to the return dict:
```python
comp = state_snapshot.get("compendium", {}).get("npcs", {})
npc_roster = _build_npc_roster(comp)
pc_name = pc.get("name", "Unnamed")
```
Add `"npc_roster": npc_roster` and `"pc_name": pc_name` to the return dict. Also remove unused `conditions`, `inventory`, `intent` fields from the scene return dict (the scene template doesn't use them).

**Why:** Bug #1 — scene dump was missing npc_roster and pc_name, preventing accurate scene prompt testing.

**Validation:** `ev.py prompt-eval dump <save-dir> --turn N --stream scene` — should include NPC roster and pc_name in output.

#### Step 2.2 — Implement ruling/narrate/state stream branches

**File:** `ccya/ev/prompt_eval.py`

**What:** Add `elif stream == "ruling"` and `elif stream == "narrate"` and `elif stream == "state"` branches to `build_prompt_context()`. Each builds context matching the production code:

**Ruling branch** — mirrors `_ruling_messages()` in `ruling.py:43-56`:
```python
comp = state_snapshot.get("compendium", {}).get("npcs", {})
npc_roster = _build_npc_roster(comp)
arc = state_snapshot.get("arc") or {}
urgent_threads = [
    {"id": t.get("id", ""), "summary": t.get("summary", ""), "progress": t.get("progress", [])}
    for t in (arc.get("threads") or []) if t.get("urgency") == "urgent"
]
return {
    "pc": pc,
    "location": state_snapshot.get("location") or {},
    "user_input": "",
    "meta": {"turn": turn_no},
    "npc_roster": npc_roster,
    "inventory": state_snapshot.get("inventory") or [],
    "recent_turns": [],
    "scene_phase": scene.get("scene_phase", "SETUP"),
    "urgent_threads": urgent_threads,
}
```

**Narrate branch** — mirrors `_narrate_messages()` in `narrate.py:75-95`:
```python
comp = state_snapshot.get("compendium", {}).get("npcs", {})
npc_roster = _build_npc_roster(comp)
arc = state_snapshot.get("arc") or {}
# Build current_arc_ctx similar to narrate.py:55-71
current_arc_ctx = None
if arc:
    all_threads = [t for t in (arc.get("threads") or [])]
    current_arc_ctx = {
        "visible_goal": arc.get("visible_goal", ""),
        "resolution": arc.get("resolution"),
        "resolved_arcs": [],
        "threads": [
            {
                "summary": t.get("summary", "") if isinstance(t, dict) else getattr(t, "summary", ""),
                "urgency": t.get("urgency", "normal") if isinstance(t, dict) else getattr(t, "urgency", "normal"),
                "id": t.get("id", "") if isinstance(t, dict) else getattr(t, "id", ""),
                "dormant": t.get("dormant", False) if isinstance(t, dict) else getattr(t, "dormant", False),
                "progress": [],
                "last_updated_turn": t.get("last_updated_turn") if isinstance(t, dict) else getattr(t, "last_updated_turn", None),
            }
            for t in all_threads
        ],
        "completed_threads": [],
    }
return {
    "state": state_snapshot,
    "pc": pc,
    "prior_history": list((state_snapshot.get("meta") or {}).get("prior_history") or [])[:-1],
    "recent_turns": [],
    "rules_outcome": None,
    "npc_name_pool": {},
    "user_input": "",
    "pending_beat": prev_meta.get("pending_gm_beat"),
    "pacing_context": turn_ev.get("pacing_context") or {},
    "turn_no": turn_no,
    "meta": {"turn": turn_no},
    "scene": state_snapshot.get("scene", {}),
    "ages": {},
    "pc_allegiance": None,
    "world_factions": [],
    "npc_roster": npc_roster,
    "current_arc": current_arc_ctx,
    "curtain_call": curtain_call,
    "resolved_arcs": [],
}
```

**State branch** — mirrors `_extract_state_messages()` in `extraction.py:279-288`:
```python
return {
    "narration": narration,
    "conditions": list(pc.get("conditions") or []),
    "inventory": state_snapshot.get("inventory") or [],
    "intent": intent if isinstance(intent, dict) else None,
    "turn_no": turn_no,
}
```

**Why:** Bug #2 — only scene/storytell branches existed. Ruling/narrate/state streams need context builders for complete prompt testing.

**Validation:** `ev.py prompt-eval dump <save-dir> --turn N --stream ruling` — should render without error. Same for narrate and state.

#### Step 2.3 — Storytell empty recent_turns

**File:** `ccya/ev/prompt_eval.py`

**What:** In the storytell branch (line 151), replace `"recent_turns": []` with actual recent turns from events. Build from previous turns' narrations:
```python
recent_turns = []
for ev in reversed(events):
    if isinstance(ev.get("turn"), int) and ev["turn"] < turn_no:
        narr = (ev.get("narrate") or {}).get("output", "")
        if narr:
            recent_turns.append({"turn": ev["turn"], "narrative": narr})
        if len(recent_turns) >= 10:
            break
recent_turns = list(reversed(recent_turns))
```

**Why:** Bug #3 — hardcoded empty list prevents testing recent turns context.

**Validation:** `ev.py prompt-eval dump <save-dir> --turn 10 --stream storytell` — recent_turns should contain previous turn narrations.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 3: Template dedup + arch doc corrections

### Context files to load
- `ccya/prompts/sections/_inventory.j2`
- `ccya/prompts/sections/_location.j2`
- `ccya/prompts/sections/_npc_roster.j2` (reference — already shared)
- `ccya/prompts/sections/_recent_turns.j2` (reference — already shared)
- `ccya/prompts/sections/_thread_list.j2` (reference — already shared)
- `ccya/prompts/sections/_arc.j2` (reference — already shared)
- `ccya/prompts/ruling_user.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/storytell_user.j2`
- `ccya/prompts/context.py` (lines 209-297 — boundary models)
- `docs/architecture/step2a-scene.md`
- `docs/architecture/step2b-state.md`
- `docs/repomap.md`

### Detailed steps

#### Step 3.1 — Create _pc_header.j2

**File:** `ccya/prompts/sections/_pc_header.j2`

**What:** Create new section template:
```jinja2
## Player Character
**{{ pc.name or "Unnamed" }}** — {{ pc.tagline or pc.concept or "" }}

**Stats:** {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}
```

**Why:** PC header is duplicated identically in ruling_user.j2:1-4 and narrate_user.j2:1-4.

**Validation:** `grep "_pc_header" ccya/prompts/sections/_pc_header.j2` — file exists with correct content.

#### Step 3.2 — Create _conditions.j2

**File:** `ccya/prompts/sections/_conditions.j2`

**What:** Create new section template with `show_age` param:
```jinja2
{% if conditions -%}
{% for c in conditions -%}
- {{ c.id if c is mapping else c }}{% if show_age %} (age: {{ turn_no - (c.added_turn if c is mapping else 0) }} turns){% endif %}{% if c is mapping and c.get('label') %}: {{ c.label }}{% endif %}{% if c is mapping and c.get('description') %} — {{ c.description }}{% endif %}
{% endfor -%}
{%- endif -%}
```

**Why:** Conditions render in 3 different formats across templates. This consolidates to bullet lists with optional age rendering. Handles both dict items and string/list items.

**Validation:** Template renders correctly with both `show_age` and without.

#### Step 3.3 — Parameterize _inventory.j2

**File:** `ccya/prompts/sections/_inventory.j2`

**What:** Change from `state.inventory` to accept either `inventory` or `state.inventory`:
```jinja2
{% set inv = inventory | default(state.inventory, true) -%}
{% if inv -%}
{% for item in inv -%}
{% set amt = item.get("amount") or 1 -%}
- **{{ item.get("name", item.get("id", "?")) }}**{% if amt > 1 or item.get("id") == "credits" %} ×{{ amt }}{% endif %}{% if item.get("notes") %}: {{ item.notes }}{% endif %}
{% endfor -%}
{%- else -%}
Nothing of note.
{% endif -%}
```

**Why:** Only narrate uses `_inventory.j2` currently. Others have inline inventory. Parameterizing enables sharing.

**Validation:** Renders correctly with both `inventory` and `state.inventory` context variables.

#### Step 3.4 — Parameterize _location.j2

**File:** `ccya/prompts/sections/_location.j2`

**What:** Change from `state.location` to accept either `location` or `state.location`:
```jinja2
{% set loc = location | default(state.location, true) -%}
{{ loc.name or "Unknown" }} ({{ loc.id or "no-id" }})
{{ loc.description or "No description." }}
```

**Why:** Only narrate uses `_location.j2` currently. Others have inline location. Parameterizing enables sharing.

**Validation:** Renders correctly with both `location` and `state.location` context variables.

#### Step 3.5 — Update ruling_user.j2

**File:** `ccya/prompts/ruling_user.j2`

**What:** Replace 2 inline sections with includes:
1. Lines 1-6 (PC header + conditions inline): Replace with `{% include "sections/_pc_header.j2" %}` + `{% include "sections/_conditions.j2" %}`
2. Lines 24-28 (inventory inline): Replace with `{% include "sections/_inventory.j2" %}`
3. Line 9 (location inline): Keep as-is — ruling only needs a one-liner, not the full format.

**Why:** Dedup PC header, conditions, and inventory to shared sections.

**Validation:** Template renders with all sections present. PC header matches narrate format.

#### Step 3.6 — Update narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace 1 inline section with includes:
1. Lines 1-6 (PC header + conditions inline): Replace with `{% include "sections/_pc_header.j2" %}` + `{% include "sections/_conditions.j2" %}`
2. Lines 8-9 (inventory): Already uses `{% include "sections/_inventory.j2" %}` — no change needed.
3. Lines 11-12 (location): Already uses `{% include "sections/_location.j2" %}` — no change needed.

**Why:** Dedup PC header and extract conditions to shared section.

**Validation:** Template renders identically to current output (same PC header format, conditions as bullet list).

#### Step 3.7 — Update extract_state_user.j2

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Replace 2 inline sections with includes:
1. Lines 1-5 (conditions): Replace with `{% include "sections/_conditions.j2" % show_age=true %}`
2. Lines 6-9 (inventory): Replace with `{% include "sections/_inventory.j2" %}`

**Why:** Dedup conditions and inventory to shared sections.

**Validation:** Template renders conditions with age and inventory in consistent format.

#### Step 3.8 — Update storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`

**What:** Replace 3 inline sections with includes:
1. Lines 1-4 (inventory inline): Replace with `{% include "sections/_inventory.j2" %}`
2. Lines 5-9 (conditions inline): Replace with `{% include "sections/_conditions.j2" %}`
3. Lines 10-12 (location inline): Replace with `{% include "sections/_location.j2" %}`

**Why:** Dedup inventory, conditions, and location to shared sections.

**Validation:** Template renders all three sections in consistent format.

#### Step 3.9 — Correct step2a-scene.md flowchart

**File:** `docs/architecture/step2a-scene.md`

**What:** Remove 3 false input claims from the flowchart's IN subgraph (lines 13-21):
- Remove `S2["state.pc (name, tagline, bio, stats)"]`
- Remove `S5["state.pc.conditions"]`
- Remove `S7["recent_turns[-1:]<br>(T-1 prior narration)"]`
- Add `S2["pc.name<br>(player character name)"]` after S1

**Why:** Architecture docs must match actual code. Scene only receives `narration`, `location`, `pc.name`, `npc_roster`, `turn_no`.

**Validation:** Flowchart inputs match `extraction.py:250-258` context dict.

#### Step 3.10 — Correct step2b-state.md flowchart

**File:** `docs/architecture/step2b-state.md`

**What:** Remove 2 false input claims from the flowchart's IN subgraph (lines 13-19):
- Remove `S2["state.pc (name, bio, stats, conditions)"]`
- Remove `S3["state.location"]`
- Keep S1 (narrative), S4 (state.inventory), S5 (intent) — these are correct.

**Why:** Architecture docs must match actual code. State extract only receives `narration`, `conditions`, `inventory`, `intent`, `turn_no`.

**Validation:** Flowchart inputs match `extraction.py:279-288` context dict.

#### Step 3.11 — Update docs/repomap.md

**File:** `docs/repomap.md`

**What:** Update `RulingBoundary` and `StorytellerBoundary` field lists in the prompts/context.py section. Update `build_prompt_context()` description to note it now supports ruling/narrate/state streams.

**Why:** AGENTS.md requires doc updates for any code change touching a module, config key, model field, prompt, or public API. Stale docs are bugs.

**Validation:** `grep -A 10 "RulingBoundary" docs/repomap.md` — should show 9 fields. `grep -A 20 "StorytellerBoundary" docs/repomap.md` — should show 17 fields.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Documentation updates required

1. **`docs/repomap.md`** — Updated in Phase 3 step 3.11.
2. **`AGENTS.md`** — No changes needed — this plan doesn't alter build commands, signposts, or conventions.
3. **`docs/architecture/step2a-scene.md`** and **`docs/architecture/step2b-state.md`** — Updated in Phase 3 steps 3.9-3.10.
