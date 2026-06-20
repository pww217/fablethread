# Prompt Template Fixes

## Purpose

Fix the 20+ correctness and formatting issues introduced in 02b42e4e across all 5 user prompt templates and their shared section templates.

## Problem Statement

Commit 02b42e4e consolidated inline template code into shared section includes but introduced multiple regression classes: (1) section templates had their data-access fallbacks changed from `state.inventory`/`state.location` to `[]`/`{}`, silently breaking narrate; (2) `_conditions.j2` expects top-level `conditions` but ruling and narrate contexts only have `pc.conditions`, so conditions render as nothing; (3) section headers were stripped during consolidation, leaving some callers with headerless sections; (4) `pc_name` was added to the scene template but never wired into the engine context. Root cause: no per-stream validation, no context-variable contracts, no canonical variable names.

## Constraints

- Do not change the inline ruling NPC roster (slim format is intentional).
- Do not filter PC out of compendium in scene extraction (data concern, not template concern).
- Storytell formatting fixes must not block data-access fixes — order by correctness then formatting.

## Non-goals

- Engine prompt system templates — system prompt content has no known issues.
- Engine prompt architecture beyond what's needed to pass correct context variables.
- Any changes to the `prompt_eval.py` context builder — those belong in Plan 2 (tooling).

## Solution

Phase 1 restores the section template fallbacks and adds headers. Phases 2-6 fix each user template's context passing and template-specific issues. Each phase is independently testable via `prompt-eval dump` against a real save.

## Firm decisions

1. Section headers (`## Inventory`, `## Conditions`, `## Location`) live inside the section template, not the caller. Remove redundant wrapper headers from callers.
2. `_inventory.j2` and `_location.j2` fall back to `state.inventory`/`state.location` when no top-level variable is provided.
3. All engine `_*_messages()` functions pass `conditions` at top level — no template should reach into `pc.conditions`.
4. Ruling keeps its slim inline NPC roster. Do not switch to `_npc_roster.j2`.
5. Scene keeps `pc_name` (string) not full PC header — the extractor only needs to know the character's name.
6. Remove `## Scene Phase` from ruling.
7. Remove redundant `### Current Threads` wrapper from narrate (already inside `_thread_list.j2`).
8. No changes to the inline ruling NPC render loop (intentionally slim).

## Risks, Ambiguities, and Blockers

- Scene: adding `pc_name` to `_extract_scene_messages()` requires confirming the function signature accepts the PC state. Already passes `state` dict — can extract `pc_name` from it.
- Phase ordering: Phase 1 must complete before Phases 2-6 because section template changes are consumed by all phases.

## Status
`completed` — All 6 phases executed. `make check` passes (lint + typecheck).

## Phases

6 phases: cross-cutting section template fixes, then one phase per user prompt.

## Implementation — Phase 1: Section Templates (cross-cutting)

### Context files to load
- `ccya/prompts/sections/_inventory.j2`
- `ccya/prompts/sections/_conditions.j2`
- `ccya/prompts/sections/_location.j2`
- `ccya/prompts/sections/_thread_list.j2`
- `ccya/docs/architecture/` any relevant data-shape docs

### Detailed steps

#### Step 1.1 — Fix `_inventory.j2` fallback + add header

**File:** `ccya/prompts/sections/_inventory.j2`

**What:** Restore `state.inventory` fallback, add `## Inventory` header inside the if-block. Current fallback `inventory | default([], true)` changed to `inventory | default(state.inventory, true)`.

**Why:** Narrate context has no top-level `inventory` — only `state.inventory`. The fallback change in 02b42e4e broke narrate (`"Nothing of note."` when data exists).

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "Nothing of note"` should produce no match. Inventory items should appear after `## Inventory` header.

#### Step 1.2 — Fix `_conditions.j2` header

**File:** `ccya/prompts/sections/_conditions.j2`

**What:** Add `## active_conditions` header inside the `{% if conditions -%}` block. Output format:
```
## active_conditions
- condition_id (age: N turns): label — description
```

**Why:** All 4 callers (ruling, narrate, state, storytell) render conditions without a header, making it impossible to distinguish from adjacent sections.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream state | grep "## active_conditions"` should match.

#### Step 1.3 — Fix `_location.j2` fallback + add header

**File:** `ccya/prompts/sections/_location.j2`

**What:** Restore `state.location` fallback. Current `location | default({}, true)` → `location | default(state.location, true)`. Add `## Location` header.

**Why:** Narrate context has no top-level `location` — only `state.location`.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "^Unknown (no-id)"` should produce no match. Location section should show `## Location` header.

#### Step 1.4 — Add `type` to thread display in `_thread_list.j2`

**File:** `ccya/prompts/sections/_thread_list.j2`

**What:** Two changes:
1. Add `t.type` alongside `t.urgency` in the display. Change `[{{ t.urgency | upper }}]` to `[{{ t.type | default(t.urgency) | upper }}]`.
2. Fix progress loop (line 5): add newline before `{% endif %}` so progress entries render on separate lines. Change `{%- for entry in t.progress %}   - {{ entry }}{% endfor %}` to `{%- for entry in t.progress %}
  - {{ entry }}
{%- endfor %}`.

**Why:** Threads have a `type` field (`threat`, `complication`, `opportunity`, `revelation`) that is semantically meaningful but never rendered. Progress entries are concatenated on the same line due to whitespace stripping.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "\[THREAT\]"` should match (for the `customs_corruption` thread which has type `threat`). Progress entries should appear on separate indented lines.

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.

---

## Implementation — Phase 2: Ruling

### Depends on
Phase 1 complete (`_inventory.j2`, `_conditions.j2` headers present)

### Context files to load
- `ccya/prompts/ruling_user.j2`
- `ccya/engine/ruling.py` (lines 53-67 — `_ruling_messages()` context)

### Detailed steps

#### Step 2.1 — Pass `conditions` to ruling context

**File:** `ccya/engine/ruling.py` (line 57-67 context dict)

**What:** Add `"conditions": list(pc.get("conditions") or [])` to the ruling user context dict.

**Why:** `_conditions.j2` expects top-level `conditions`. Ruling context only has `pc` with `pc.conditions`. Without this, conditions render as nothing.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream ruling | grep "## active_conditions"` should match.

#### Step 2.2 — Add blank line between NPC roster and inventory

**File:** `ccya/prompts/ruling_user.j2`

**What:** Insert a blank line between the NPC roster section (line 8 `{% endfor -%}`) and `{% include "sections/_inventory.j2" %}` (line 19). Change `{% endfor -%}` to `{% endfor %}` and ensure a blank line separates the sections.

**Why:** NPC roster items and inventory items render mashed together with no visual separation.

**Validation:** Visual inspection of ruling dump should show a blank line between last NPC entry and first inventory item.

#### Step 2.3 — Remove Scene Phase from ruling

**File:** `ccya/prompts/ruling_user.j2` (line 23)

**What:** Delete line `## Scene Phase: {{ scene_phase | default('SETUP') }}`.

**Why:** Scene phase is not useful for the ruling step — ruling only needs current scene context, not phase metadata.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream ruling | grep "Scene Phase"` should produce no match.

---

## Implementation — Phase 3: Narrate

### Depends on
Phase 1 complete (section template fallbacks restored)

### Context files to load
- `ccya/prompts/narrate_user.j2`
- `ccya/engine/narrate.py` (lines 83-103 — `_narrate_messages()` context)

### Detailed steps

#### Step 3.1 — Pass `inventory`, `location`, `conditions` to narrate context

**File:** `ccya/engine/narrate.py` (lines 83-103 user_ctx dict)

**What:** Add three keys to `user_ctx`:
```python
"inventory": state.get("inventory") or [],
"location": state.get("location") or {},
"conditions": list((state.get("pc") or {}).get("conditions") or []),
```

**Why:** Narrate context only passes `state` (full dict) and `pc` (nested). The section templates need top-level `inventory`, `location`, and `conditions` — with the fallback from Phase 1 they'd work via `state.*`, but passing them explicitly removes the dependency on the fallback and makes the contract clear.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "Smith and Wesson"` should match. Location should show `Pier Nine Dockyards` not `Unknown`.

#### Step 3.2 — Remove wrapper headers from narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2` (lines 3, 6)

**What:** Remove `## Inventory` (line 3) and `## Location` (line 6) wrapper headers. After Phase 1, `_inventory.j2` and `_location.j2` emit their own headers internally.

```jinja2
# Before:
## Inventory
{% include "sections/_inventory.j2" %}

## Location
{% include "sections/_location.j2" %}

# After:
{% include "sections/_inventory.j2" %}

{% include "sections/_location.j2" %}
```

**Why:** Firm Decision #1 — headers live inside section templates, not callers. Having both causes double headers.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate` should show `## Inventory` once (from the section template), not twice.

#### Step 3.4 — Gate empty Immutable Reference block

**File:** `ccya/prompts/narrate_user.j2` (lines 16-31)

**What:** Wrap the entire `<<<TRACE_IMMUTABLE_START>>> ... <<<TRACE_IMMUTABLE_END>>>` block in a condition that checks whether either `world_factions` or `npc_name_pool` has content:
```jinja2
{% if world_factions or npc_name_pool %}
<<<TRACE_IMMUTABLE_START>>>
## Immutable Reference
...
<<<TRACE_IMMUTABLE_END>>>
{% endif %}
```

**Why:** Currently emits an empty Immutable Reference section even when both contain nothing, wasting tokens and confusing the LLM.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "<<<TRACE_IMMUTABLE_START>>>"` should produce no match (no factions or name_pool in test data).

#### Step 3.5 — Remove redundant `### Current Threads` header

**File:** `ccya/prompts/narrate_user.j2` (lines 34-42)

**What:** Change the thread section to just include `_thread_list.j2` without the outer `### Current Threads` header:
```jinja2
{% if current_arc and current_arc.threads %}
{% set threads = current_arc.threads %}
{% include "sections/_thread_list.j2" %}
{% elif state.arc and state.arc.threads %}
{% set threads = state.arc.threads %}
{% include "sections/_thread_list.j2" %}
{% endif %}
```

Remove the `### Current Threads` headers (lines 35, 39). `_thread_list.j2` already emits `### Active Threads`.

**Why:** Produces a double header (`### Current Threads` immediately followed by `### Active Threads`), wasting tokens and confusing hierarchy.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate | grep "Current Threads"` should produce no match.

---

## Implementation — Phase 4: Scene

### Context files to load
- `ccya/prompts/extract_scene_user.j2`
- `ccya/engine/extraction/scene.py` (lines 13-35 — `_extract_scene_messages()`)

### Detailed steps

#### Step 4.1 — Pass `pc_name` to scene context

**File:** `ccya/engine/extraction/scene.py` (lines 29-34 context dict)

**What:** Add `"pc_name": (state.get("pc") or {}).get("name", "Unnamed")` to the scene user context dict.

**Why:** The template has `## Player Character\n{{ pc_name }}` but no caller passes `pc_name`. The `{{ pc_name }}` renders as empty string, producing a bare header with nothing under it.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream scene | grep -A1 "Player Character"` should show `Michael Taylor` after the header.

---

## Implementation — Phase 5: State

### Depends on
Phase 1 complete (`_conditions.j2`, `_inventory.j2` headers present)

### Context files to load
- `ccya/prompts/extract_state_user.j2`
- `ccya/engine/extraction/state.py` (lines 24-34 — `_extract_state_messages()`)

### Detailed steps

#### Step 5.1 — Add minimal PC header to state

**File:** `ccya/engine/extraction/state.py` (lines 27-33 context dict)

**What:** Add `"pc_name": (state.get("pc") or {}).get("name", "Unnamed")` to the state user context dict.

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Add a one-line PC header at the top:
```jinja2
## Player Character: {{ pc_name }}
```

**Why:** State manages conditions and inventory but has no way to identify whose they are. Adding just the name (matching ruling's minimal approach) identifies the subject without verbosity.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream state | grep "Player Character"` should show `## Player Character: Michael Taylor`.

---

## Implementation — Phase 6: Storytell

### Depends on
Phase 1 complete (section template headers present)

### Context files to load
- `ccya/prompts/storytell_user.j2`

### Detailed steps

#### Step 6.1 — Add PC header

**File:** `ccya/engine/extraction/storytell.py` (lines 68-98 context dict)

**What:** Add `"pc_name": (state.get("pc") or {}).get("name", "Unnamed")` to the storytell user context dict.

**File:** `ccya/prompts/storytell_user.j2`

**What:** Insert at the top, before the include line:
```jinja2
## Player Character: {{ pc_name or "Unnamed" }}
```

**Why:** Storytell has no PC info — no `pc` object or `pc_name` in context. The template needs to identify whose inventory/conditions/arc are being shown.

#### Step 6.2 — Fix one-line includes, add `## Location` header

**File:** `ccya/prompts/storytell_user.j2` (line 2)

**What:** Break the single-line include chain into separate lines separated by blank lines:
```jinja2
{% set show_age = true %}
{% include "sections/_inventory.j2" %}

{% include "sections/_conditions.j2" %}

{% include "sections/_npc_roster.j2" %}

{% include "sections/_location.j2" %}

{% include "sections/_arc.j2" %}
```

Also add a `## Location` header before `_location.j2` include (the section template has the header now via Phase 1).

**Why:** All 5 includes render back-to-back with no visual separation between sections.

**Validation:** Visual inspection of storytell dump should show blank lines between inventory, conditions, NPC roster, and location sections.

#### Step 6.3 — Fix storytell formatting (world_state newlines + section spacing)

**File:** `ccya/prompts/storytell_user.j2` (lines 8-33)

**What:** Fix two issues in one pass:
1. Remove `{%-` whitespace control from `endfor` in world_state loop so items render on separate lines.
2. Add blank lines between top-level sections (world_state → pacing_context → scene_phase → curtain_call).

```jinja2
{% if world_state %}
<<<TRACE_IMMUTABLE_START>>>
## world_state (read-only context)
{% for f in world_state %}{% if f is string %}- {{ f }}
{% else %}- [{% if "tier" in f and f["tier"] == "permanent" %}permanent{% else %}persistent{% endif %}] {% if "text" in f %}{{ f["text"] }}{% else %}(no text){% endif %}
{% endif %}
{% endfor %}
<<<TRACE_IMMUTABLE_END>>>
{% endif %}

{% if pacing_context and (pacing_context.directive or pacing_context.outcome_hint) %}
## pacing_context
Directive: {{ pacing_context.directive or "none" }}
Outcome: {{ pacing_context.outcome_hint or "hold" }}
{% endif %}

{% if scene_phase %}
## Scene phase: {{ scene_phase }} — allowed beat types: {{ allowed_beat_types | join(", ") }}
{% endif %}

{% if curtain_call and curtain_call != "" %}
## Curtain Call: {{ curtain_call | upper }}
{% endif %}
```

**Why:** Items render back-to-back (`- first item- second item`) and sections concatenate with no visual separation.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream storytell | grep -A10 "world_state"` should show each item on its own line. Visual inspection should show blank lines between world_state, pacing_context, scene_phase, and curtain_call blocks.

---

## Documentation updates

1. **`docs/architecture/step0-ruling.md`** — Add `conditions` to ruling context inputs.
2. **`docs/architecture/step1-narrate.md`** — Add `inventory`, `location`, `conditions` to narrate context inputs.
3. **`docs/architecture/step2a-scene.md`** — Add `pc_name` to scene context inputs.
4. **`docs/architecture/step2b-state.md`** — Add `pc_name` to state context inputs.
5. **`docs/architecture/step2c-storytell.md`** — Add `pc_name` to storytell context inputs.
6. **`docs/repomap.md`** — Update prompt template section if it lists context variables per stream.
7. **`AGENTS.md`** — No changes needed (build/test commands unchanged).

---

## Done when

All 5 user templates render correctly via `prompt-eval dump` on a real noir save:
- Ruling: shows conditions, inventory with header, no Scene Phase
- Narrate: shows actual inventory, actual location, no empty Immutable Reference, threads with type
- Scene: shows PC name under ## Player Character
- State: shows ## Player Character: {name}, ## active_conditions, ## Inventory
- Storytell: shows PC name, location with header, spaced sections, world_state items on separate lines
