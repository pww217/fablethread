# Consolidate narrate/progress user prompt sections

## Status
`in-progress`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Delete dead partial ~~| ~~Remove `_velocity.j2` — ~~orphaned, logic superseded inline ~~| ~~ALREADY DELETED — file does not exist~~ |
| 02 | Wire narrate to existing pressure partial ~~| ~~Replace inline Active Threats block in `narrate_user.j2` with `_scene_pressure.j2` ~~| ~~ALREADY COMPLETE — `_scene_pressure.j2` does not exist, intentionally omitted~~ |
| 03 | Wire progress to existing pressure partial ~~| ~~Replace inline Current Pressures block in `extract_progress_user.j2` with `_scene_pressure_extract.j2` ~~| ~~ALREADY COMPLETE — `_scene_pressure_extract.j2` does not exist, intentionally omitted~~ |
| 04 | Fix `_arc.j2` to use `current_arc` from user context | `narrate_user.j2` includes `_arc.j2` which reads `state.arc` — add `current_arc` to `user_ctx` in `narrate.py`, rewrite `_arc.j2` to read from `current_arc`, include `discovered_truths` |
| 05 | ~~Align variable name~~ — merged into Phase 04 |  |
| 06 | Rename `pending_gm_beat` → `pending_beat` | Align template variable name with extraction context; update `narrate.py` param, context key, template, and callers |

## Objective
`narrate_user.j2` has a working `_arc.j2` include that reads from `state.arc` (raw state) instead of the curated `current_arc_ctx` that `narrate.py` intentionally builds (strips hidden fields, trims thread details). Additionally, `current_arc` is only passed to the system prompt, not the user prompt — it needs to be in `user_ctx` for the partial to use it. The narrator should also see `discovered_truths`. The pending beat template variable `pending_gm_beat` is inconsistent with `pending_beat` used everywhere else (extraction context, progress template, state storage key). This plan fixes both issues.

## Non-goals
- Do not touch `extract_scene_user.j2` or `extract_state_user.j2`.
- Do not change the Python context-building logic in `narrate.py` or `extraction.py`.
- Do not change prompt wording, directive text, or any system prompts.
- Do not add new sections or data not already present.
- Do not consolidate `_npc_roster.j2` and `_npc_roster_extract.j2` — they are intentionally different (full vs minimal fields).
- Do not consolidate location/inventory blocks — narrate reads `state.*` (last turn); progress reads `extraction_ctx.*` (this turn). They must remain separate.

---

## Implementation — Phase 01-03: Already complete

Phases 01-03 are marked complete. The referenced files (`_velocity.j2`, `_scene_pressure.j2`, `_scene_pressure_extract.j2`) do not exist in the codebase — they were either already deleted or intentionally omitted. No action needed.

---

## Implementation — Phase 04 + 05: Fix `_arc.j2` to use `current_arc` from user context

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_arc.j2`
- `ccya/engine/narrate.py` — specifically the `current_arc_ctx` dict and `user_ctx` dict

### Detailed steps

#### Step 4.1 — Understand the current mismatch

**File:** `ccya/prompts/sections/_arc.j2`, `ccya/engine/narrate.py`

**What:** `narrate.py` builds `current_arc_ctx` (lines 82-99) — a curated dict with keys: `visible_goal`, `thematic_question`, `phase`, `active_threads`, `pc_drive`, `hidden_truths`. The `active_threads` list contains dicts with keys `summary`, `urgency`, `tags`.

`current_arc_ctx` is passed to the **system** prompt only (line 105). The **user** prompt context (`user_ctx`, lines 46-79) does NOT include `current_arc`.

`_arc.j2` currently reads `state.arc.get('visible_goal')`, etc. — it reads from `state.arc` (raw state). This works today but bypasses the curated context and exposes `discovered_truths` from raw state.

**Decision:** Narrator SHOULD see `discovered_truths`. Add `current_arc` to `user_ctx` so `_arc.j2` can read from the curated context (which trims thread details, structures `active_threads` correctly).

#### Step 4.2 — Add `current_arc` to `user_ctx` in `narrate.py`

**File:** `ccya/engine/narrate.py`

**What:** After the existing `user_ctx` dict (line 46-79), add `current_arc`:

```python
    user_ctx = {
        ...existing keys...
        "current_arc": current_arc_ctx,  # <-- add this line
    }
```

**Why:** `_arc.j2` is included in `narrate_user.j2`. To read from `current_arc`, it must be in the user context, not just the system context.

**Validation:** `current_arc_ctx` is already built at line 82-99; just needs to be included in `user_ctx`.

#### Step 4.3 — Rewrite `_arc.j2` to read from `current_arc`

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace all `state.arc.get(...)` references with `current_arc.*`. Include `discovered_truths`:

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
{% if current_arc.discovered_truths -%}
**Revealed truths:**
{% for truth in current_arc.discovered_truths -%}
- {{ truth }}
{% endfor -%}
{% endif -%}
{%- else -%}
No active campaign arc.
{% endif -%}
```

**Why:**
- Reads from `current_arc` (the curated context) not `state.arc` (raw state).
- Includes `discovered_truths` — narrator should see this.
- Removes `(progress: X/3)` from thread display — not in the `current_arc_ctx.active_threads` shape (`narrate.py` only passes `summary`, `urgency`, `tags`).
- `tags` from `current_arc.active_threads` is not rendered in the narrator arc block — tags are for signal matching in progress, not display in narrate.

**Validation:** Render a turn with an active arc. The `## Campaign Arc` block appears with goal, phase, thematic question, pc_drive, threads, and revealed truths.

#### Step 4.4 — Confirm `narrate_user.j2` include is already present and correct

**File:** `ccya/prompts/narrate_user.j2`

**What:** The include `{% include "sections/_arc.j2" %}` is already at line 13. No change needed here once `_arc.j2` is fixed.

**Validation:** No change to `narrate_user.j2` for this step.

### Tests to write or update
None — prompt content is not directly unit tested. The arc rendering is exercised by integration tests via `FakeLLM`.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `_arc` partial description: "reads from `current_arc` dict (not `state.arc`); fields: `visible_goal`, `thematic_question`, `phase`, `pc_drive`, `active_threads[summary, urgency]`, `discovered_truths`."

### Risks
1. `_arc.j2` is also potentially used by other templates in the future. By switching from `state.arc` to `current_arc`, any future template including it must pass `current_arc`. This is a cleaner contract. Risk is low — only narrate currently includes it.
2. If `current_arc` is `None` (no arc), the `{% if current_arc and current_arc.visible_goal %}` guard handles it and renders "No active campaign arc." — same behavior as before.

---

## Implementation — Phase 06: Rename `pending_gm_beat` → `pending_beat`

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/engine/narrate.py` — `pending_gm_beat` parameter and context key
- `ccya/engine/turn.py` — caller of `_narrate_messages`

### Detailed steps

#### Step 6.1 — Rename parameter, context key, and template variable

**File:** `ccya/engine/narrate.py`

**What:** In `_narrate_messages`:
1. Rename function signature parameter from `pending_gm_beat` to `pending_beat` (line 28)
2. Rename context dict key from `"pending_gm_beat"` to `"pending_beat"` (line 57)

```python
# Before
pending_gm_beat: dict[str, Any] | None = None,
...
"pending_gm_beat": pending_gm_beat,

# After
pending_beat: dict[str, Any] | None = None,
...
"pending_beat": pending_beat,
```

**Why:** The parameter is named `pending_gm_beat` in `narrate.py` but `pending_beat` everywhere else (extraction context, progress template). Aligning the template variable name removes the inconsistency without changing the stored state key `state["meta"]["pending_gm_beat"]`.

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace `pending_gm_beat` references with `pending_beat` (lines 74-78):

```jinja2
{% if pending_beat and pending_beat.type %}

**GM Beat:** {{ pending_beat.instruction }}
Surface as {{ pending_beat.surface_as }}. This is backstage direction — integrate it naturally, not as player-visible narration.
{% endif %}
```

**Why:** Template variable must match the key passed in the context dict.

#### Step 6.2 — Update caller in `turn.py`

**File:** `ccya/engine/turn.py`

**What:** Grep for `_narrate_messages(` calls. The call at line 691-726 passes `pending_gm_beat=_pending_gm_beat`. Update to `pending_beat=_pending_gm_beat`.

**Why:** The function signature kwarg rename must propagate to all call sites.

**Validation:** `grep -rn "pending_gm_beat" ccya/engine/narrate.py ccya/prompts/` returns zero results (only `state["meta"]["pending_gm_beat"]` storage key references remain, which are intentionally unchanged).

### Tests to write or update
- `grep -rn "pending_gm_beat" tests/` to find affected tests; update any that construct narrate context dicts with `pending_gm_beat=` to `pending_beat=`.

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` — update `narrate_user.j2` description: `pending_beat` (not `pending_gm_beat`) for the GM beat block.
`docs/REPOMAP/engine.md` — update `_narrate_messages` signature if present.

### Risks
1. Missing a call site that passes `pending_gm_beat=` as a kwarg. Mitigation: grep catches all cases; mypy will catch signature mismatch.
2. Confusing the template variable rename with the state storage key `state["meta"]["pending_gm_beat"]` — the storage key must NOT change. Only the Python function param, context key, and template variable change.

---

## Ambiguities requiring resolution before execution

1. ~~`_arc.j2` contract~~ — resolved: only narrate includes it, switching to `current_arc` is cleaner.

2. ~~Phase 06 caller identification~~ — resolved: caller identified at `turn.py:705` passing `pending_gm_beat=_pending_gm_beat`.

3. **`discovered_truths` in arc** — confirmed by user: narrator SHOULD see `discovered_truths`. Added to `_arc.j2` rendering.

---
