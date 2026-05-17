# Consolidate narrate/progress user prompt sections

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Delete dead partial | Remove `_velocity.j2` — orphaned, logic superseded inline |
| 02 | Wire narrate to existing pressure partial | Replace inline Active Threats block in `narrate_user.j2` with `_scene_pressure.j2` |
| 03 | Wire progress to existing pressure partial | Replace inline Current Pressures block in `extract_progress_user.j2` with `_scene_pressure_extract.j2` |
| 04 | Replace narrate inline arc with `_arc.j2` partial | `narrate_user.j2` includes `_arc.j2` already but `_arc.j2` reads from `state.arc` — verify it matches what `narrate.py` passes, remove the inline arc fields from `narrate_user.j2` |
| 05 | Fix `_arc.j2` to use the passed `current_arc` variable | `_arc.j2` currently reads `state.arc.*` but narrate passes `current_arc` dict — align the partial |
| 06 | Extract shared `_pending_beat.j2` partial | Both prompts render the pending beat block; extract to a single partial, resolve variable name difference |

## Objective
`narrate_user.j2` and `extract_progress_user.j2` have grown duplicate inline rendering blocks for scene pressure, and `narrate_user.j2` has a working `_arc.j2` include that doesn't actually fire because the partial reads `state.arc` while `narrate.py` passes `current_arc`. Several `sections/` partials (`_scene_pressure.j2`, `_scene_pressure_extract.j2`, `_arc.j2`) exist but are not used as intended. `_velocity.j2` is a dead partial superseded by narrate's inline momentum/directive logic. This plan corrects all of that: each prompt uses the correct partial for its data source, dead code is removed, and the pending beat block (duplicated across both prompts) is extracted to a shared partial.

## Non-goals
- Do not touch `extract_scene_user.j2` or `extract_state_user.j2`.
- Do not change the Python context-building logic in `narrate.py` or `extraction.py`.
- Do not change prompt wording, directive text, or any system prompts.
- Do not add new sections or data not already present.
- Do not consolidate `_npc_roster.j2` and `_npc_roster_extract.j2` — they are intentionally different (full vs minimal fields).
- Do not consolidate location/inventory blocks — narrate reads `state.*` (last turn); progress reads `extraction_ctx.*` (this turn). They must remain separate.

---

## Implementation — Phase 01: Delete dead partial

### Files to pull for context
- `ccya/prompts/sections/_velocity.j2`
- `ccya/prompts/narrate_user.j2` (confirm no `include "_velocity.j2"` reference)
- `ccya/prompts/extract_progress_user.j2` (confirm no `include "_velocity.j2"` reference)

### Detailed steps

#### Step 1.1 — Confirm no references to `_velocity.j2`

**File:** `ccya/prompts/narrate_user.j2`, `ccya/prompts/extract_progress_user.j2`

**What:** Grep both files (and all other `.j2` files) for `_velocity`. Confirm zero references.

**Why:** Before deleting, verify it is not included anywhere. The inline logic in `narrate_user.j2` superseded this partial; it was never wired into progress.

**Validation:** `grep -r "_velocity" ccya/prompts/` returns no output.

#### Step 1.2 — Delete the file

**File:** `ccya/prompts/sections/_velocity.j2`

**What:** Delete the file.

**Why:** Dead code. AGENTS.md: "Remove dead code immediately — no `# legacy` comments, no deferred cleanup."

**Validation:** File no longer exists.

### Tests to write or update
None — no Python code touches this file directly.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — remove `_velocity` from the Shared partials list.

### Risks
1. A template somewhere includes it that grep missed (unlikely — Jinja includes use string literals). Mitigation: run the full test suite after deletion; a missing include raises a `TemplateNotFound` at render time.

---

## Implementation — Phase 02: Wire narrate to `_scene_pressure.j2`

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_scene_pressure.j2`

### Detailed steps

#### Step 2.1 — Inspect the current inline block

**File:** `ccya/prompts/narrate_user.j2`

**What:** The current Scene Context block renders pressure inline:

```jinja2
## Scene Context
{% if state.scene.scene_pressure -%}
### Active Threats
{% for p in state.scene.scene_pressure %}- [{{ p.urgency | upper }}] {{ p.text }}
{% endfor -%}
{% endif -%}
```

**Why:** This is exactly what `_scene_pressure.j2` renders. The partial reads `state.scene.scene_pressure` — same variable path narrate already uses.

#### Step 2.2 — Replace inline block with include

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace the inline Active Threats block with an include. The surrounding `## Scene Context` header stays:

```jinja2
## Scene Context
{% include "sections/_scene_pressure.j2" %}
```

**Why:** Removes duplication. The partial is already written to read `state.scene.scene_pressure` which is what narrate's context dict contains (`state` is passed as `state`).

**Validation:** Render a test turn. The `## Scene Context` / `### Active Threats` block appears in the rendered output with the same content as before.

#### Step 2.3 — Verify the directive logic below still works

**File:** `ccya/prompts/narrate_user.j2`

**What:** The directive logic further down uses `scene_pressure` (the top-level template variable, not `state.scene.scene_pressure`). These are two different variables — `scene_pressure` is passed directly as a top-level context key from `narrate.py` and is used for counting immediate/building pressures for the Overwhelm/Pressure/Tension directive block. Do NOT change that block.

**Why:** `_scene_pressure.j2` renders from `state.scene.scene_pressure` (for display). The directive logic uses `scene_pressure` (for counting). They are the same underlying data passed via two different context paths. Only the display block is being changed.

**Validation:** Directive logic block still references `scene_pressure` (not `state.scene.scene_pressure`). No change to that section.

### Tests to write or update
None — prompt rendering is tested indirectly via integration tests. No unit test directly asserts narrate user prompt structure.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `narrate_user.j2` description: note that `_scene_pressure.j2` is now included for the Active Threats block.

### Risks
1. `state.scene.scene_pressure` vs top-level `scene_pressure` variable confusion could break directive counting if accidentally changed. Mitigation: read the directive block carefully before and after; the include only replaces the display block above it.

---

## Implementation — Phase 03: Wire progress to `_scene_pressure_extract.j2`

### Files to pull for context
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/sections/_scene_pressure_extract.j2`

### Detailed steps

#### Step 3.1 — Inspect current inline block

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** The current Current Pressures block:

```jinja2
{% if scene_pressure -%}
## Current Pressures
{% for p in scene_pressure %}- [{{ p.id }}] ({{ p.urgency }}) {{ p.text }}
{% endfor %}
{% endif -%}
```

**Why:** `_scene_pressure_extract.j2` renders exactly this format: `- [{{ p.id }}] ({{ p.urgency }}) {{ p.text }}` iterating over `scene_pressure`. The partial does not include the `## Current Pressures` header or the `if` guard.

#### Step 3.2 — Replace inline block with include, keeping header and guard

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Keep the conditional guard and header; replace only the inner loop:

```jinja2
{% if scene_pressure -%}
## Current Pressures
{% include "sections/_scene_pressure_extract.j2" %}
{% endif -%}
```

**Why:** The partial does not own the header or guard — it only renders the list. This matches how `_scene_pressure.j2` owns its own header vs the Scene Context wrapper in narrate.

Note: `_scene_pressure_extract.j2` uses `scene_pressure` (top-level variable) which is exactly what `extraction.py` passes as `scene_pressure` (from `extraction_ctx.scene_pressure_this_turn`). Variable name matches.

**Validation:** Render a test turn. `## Current Pressures` block in the progress prompt contains the same `- [id] (urgency) text` lines as before.

### Tests to write or update
None — same reasoning as Phase 02.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `extract_progress_user.j2` description: note that `_scene_pressure_extract.j2` is now included for the Current Pressures list.

### Risks
1. The partial lacks the `if scene_pressure` guard; an empty list would still enter the `## Current Pressures` section. Mitigation: the outer `{% if scene_pressure %}` guard is retained in the template.

---

## Implementation — Phase 04 + 05: Fix `_arc.j2` and wire it properly in `narrate_user.j2`

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_arc.j2`
- `ccya/engine/narrate.py` — specifically the `current_arc_ctx` dict passed to the user template

### Detailed steps

#### Step 4.1 — Understand the current mismatch

**File:** `ccya/prompts/sections/_arc.j2`, `ccya/engine/narrate.py`

**What:** `narrate.py` passes `current_arc` as a top-level context variable — a dict with keys: `visible_goal`, `thematic_question`, `phase`, `active_threads`, `pc_drive`, `hidden_truths`. The `active_threads` list contains dicts with keys `summary`, `urgency`, `tags`.

`_arc.j2` currently reads `state.arc.get('visible_goal')`, `state.arc.get('phase')`, etc. — it reads from `state.arc`, not from `current_arc`.

`narrate_user.j2` includes `_arc.j2` unconditionally. Because `_arc.j2` reads `state.arc` and `state` is passed as the full state dict, this actually works today — but it bypasses the curated `current_arc_ctx` that `narrate.py` intentionally builds (which strips hidden fields, trims thread details to `summary/urgency/tags` only, and structures `active_threads` correctly). The partial also renders `discovered_truths` (from `state.arc`) which is NOT in `current_arc_ctx` and should not be shown to the narrator.

#### Step 4.2 — Rewrite `_arc.j2` to read from `current_arc`

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace all `state.arc.get(...)` references with `current_arc.*`:

```jinja2
{# sections/_arc.j2 — reads from current_arc dict passed by narrate.py #}
{% if current_arc and current_arc.visible_goal -%}
## Campaign Arc
**Goal:** {{ current_arc.visible_goal }}
**Phase:** {{ current_arc.phase or 'setup' }}
**Thematic question:** {{ current_arc.thematic_question or '' }}
{% if current_arc.pc_drive -%}
**PC drive:** {{ current_arc.pc_drive }}
{% endif -%}
{% if current_arc.active_threads -%}
**Active threads:**
{% for t in current_arc.active_threads -%}
- [{{ t.urgency | upper }}] {{ t.summary }}
{% endfor -%}
{% endif -%}
{%- else -%}
No active campaign arc.
{% endif -%}
```

**Why:**
- Reads from `current_arc` (the curated context) not `state.arc` (raw state).
- Removes `discovered_truths` — not in `current_arc_ctx`, not intended for the narrator.
- Removes `(progress: X/3)` from thread display — not in the `current_arc_ctx.active_threads` shape (`narrate.py` only passes `summary`, `urgency`, `tags`).
- `tags` from `current_arc.active_threads` is not rendered in the narrator arc block — tags are for signal matching in progress, not display in narrate.

**Validation:** Render a turn with an active arc. The `## Campaign Arc` block appears with goal, phase, thematic question, pc_drive, and threads. `discovered_truths` does not appear.

#### Step 4.3 — Confirm `narrate_user.j2` include is already present and correct

**File:** `ccya/prompts/narrate_user.j2`

**What:** The include `{% include "sections/_arc.j2" %}` is already in the template. No change needed here once `_arc.j2` is fixed.

**Validation:** No change to `narrate_user.j2` for this step.

### Tests to write or update
None — prompt content is not directly unit tested. The arc rendering is exercised by integration tests via `FakeLLM`.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `_arc` partial description: "reads from `current_arc` dict (not `state.arc`); fields: `visible_goal`, `thematic_question`, `phase`, `pc_drive`, `active_threads[summary, urgency]`."

### Risks
1. `_arc.j2` is also potentially used by other templates in the future. By switching from `state.arc` to `current_arc`, any future template including it must pass `current_arc`. This is a cleaner contract. Risk is low — only narrate currently includes it.
2. If `current_arc` is `None` (no arc), the `{% if current_arc and current_arc.visible_goal %}` guard handles it and renders "No active campaign arc." — same behavior as before.

---

## Implementation — Phase 06: Extract `_pending_beat.j2` shared partial

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/engine/narrate.py` — `pending_gm_beat` variable
- `ccya/engine/extraction.py` — `pending_beat` variable (from `state["meta"]["pending_gm_beat"]`)

### Detailed steps

#### Step 6.1 — Compare the two pending beat blocks

**File:** `ccya/prompts/narrate_user.j2`

Current narrate block:
```jinja2
{% if pending_gm_beat and pending_gm_beat.type %}

**GM Beat:** {{ pending_gm_beat.instruction }}
Surface as {{ pending_gm_beat.surface_as }}. This is backstage direction — integrate it naturally, not as player-visible narration.
{% endif %}
```

**File:** `ccya/prompts/extract_progress_user.j2`

Current progress block (under `## gm_beat`):
```jinja2
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
```

**What:** These are intentionally different in content — narrate shows `surface_as` and an integration instruction; progress shows `type`, `beat_expires_turn`, and `instruction` for planning purposes. They cannot be collapsed into one shared partial without losing their distinct framing.

**Decision:** Do NOT extract to a shared partial. The variable name difference (`pending_gm_beat` vs `pending_beat`) should be resolved instead — align both to `pending_beat` by updating `narrate.py`'s context dict key.

#### Step 6.2 — Align variable name: rename `pending_gm_beat` → `pending_beat` in narrate context

**File:** `ccya/engine/narrate.py`

**What:** In `_narrate_messages`, change the context dict key from `"pending_gm_beat"` to `"pending_beat"`:

```python
# Before
"pending_gm_beat": pending_gm_beat,

# After
"pending_beat": pending_gm_beat,
```

Also update the function signature parameter name from `pending_gm_beat` to `pending_beat` for consistency, and update all callers.

**Why:** The parameter is named `pending_gm_beat` in `narrate.py` but `pending_beat` everywhere else (extraction context, progress template, `state["meta"]["pending_gm_beat"]` storage key). Aligning the template variable name removes the inconsistency without changing the stored state key.

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace `pending_gm_beat` references with `pending_beat`:

```jinja2
{% if pending_beat and pending_beat.type %}

**GM Beat:** {{ pending_beat.instruction }}
Surface as {{ pending_beat.surface_as }}. This is backstage direction — integrate it naturally, not as player-visible narration.
{% endif %}
```

**Why:** Template variable must match the key passed in the context dict.

#### Step 6.3 — Verify all callers of `_narrate_messages` pass the kwarg

**File:** `ccya/engine/turn.py` (and any other caller)

**What:** Grep for `_narrate_messages(` calls. Any that pass `pending_gm_beat=` must be updated to `pending_beat=`.

**Why:** The function signature kwarg rename must propagate to all call sites.

**Validation:** `grep -rn "pending_gm_beat" ccya/` after changes returns zero results (only `state["meta"]["pending_gm_beat"]` storage key references remain, which are intentionally unchanged).

### Tests to write or update
- If any test directly constructs a narrate context dict with `pending_gm_beat=`, update it to `pending_beat=`.
- `grep -rn "pending_gm_beat" tests/` to find affected tests.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `narrate_user.j2` description: `pending_beat` (not `pending_gm_beat`) for the GM beat block.
`docs/REPOMAP/engine.md` — update `_narrate_messages` signature description if present.

### Risks
1. Missing a call site that passes `pending_gm_beat=` as a kwarg. Mitigation: the grep in Step 6.3 catches all cases; mypy will catch any signature mismatch after rename.
2. Confusing the template variable rename with the state storage key `state["meta"]["pending_gm_beat"]` — the storage key must NOT change (state migration would be required). Only the Python function parameter name and template variable name change.

---

## Ambiguities requiring resolution before execution

1. `_arc.j2` is used only by `narrate_user.j2` today. If any other template currently includes it (not apparent from grep), switching from `state.arc` to `current_arc` would break it. Option A) Rename the partial to `_arc_narrate.j2` to make the contract explicit. Option B) Keep the name and document the `current_arc` requirement. **Recommend B** — the name is generic enough, and the REPOMAP update covers the contract.

2. Phase 06 renames `pending_gm_beat` kwarg in `_narrate_messages`. The caller in `turn.py` must be identified and updated. If `turn.py` is currently calling with a positional arg (not kwarg), the rename is a no-op risk-wise. Executor must check before renaming.
