# Plan: Arc/Thread Overhaul — Phase 3: Prompts

## Purpose

Update all prompt templates (`storytell_system.j2`, `_thread_list.j2`, `_arc.j2`) to match the new model shapes and add behavioral guidance for goal updates, urgency decay, thread scope, arc resolution, silent-drop feedback, and no-op discouragement.

## Problem Statement

The prompt templates reference removed fields (`thematic_question`), render progress as a single string, lack guidance for the new `goal_update` mechanism, provide no urgency decay or arc resolution trigger guidance, and do not surface the pacing gate status. The thread scope guidance exists but uses wording inconsistent with the new auto-close behavior.

## Constraints

- Phase 1 (models) and Phase 2 (engine) must be complete before this phase starts.
- The prompt templates are the primary interface to the storyteller (design constraint). Code changes enforce constraints; prompt changes guide behavior.
- The `_thread_list.j2` and `_arc.j2` sections are included into the storytell user prompt via Jinja2 include. Changes to these templates affect what the LLM sees every turn.

## Non-goals

- No model shape changes (Phase 1).
- No engine logic changes (Phase 2).
- No changes to the narrate prompt templates — only storytell-facing templates.

## Solution

Update three template files: remove `thematic_question` and `goal_context` from `_arc.j2`, render the progress log as a clean list in `_thread_list.j2`, and add all new behavioral guidance from the design doc (items 2, 4, 5, 6, 7, 8, 9) to `storytell_system.j2`.

## Firm decisions

1. `goal_context` is removed from all prompts — it is UI-only now.
2. `thematic_question` is removed from all prompts — field is deleted.
3. Progress log renders as a numbered list in `_thread_list.j2`, newest last.
4. `turns_since_last_update` renders alongside each thread.
5. Soft-cap guidance (2-3 arc, 1-2 scene, ~5 total max) renders in the thread section header.
6. Gate status renders in the thread section when `block_escalate` is active.
7. `goal_update` guidance, urgency decay guidance, scope rules, arc resolution guidance, and no-op discouragement are added to `storytell_system.j2`.

## Risks, Ambiguities, and Blockers

- The `_thread_list.j2` template is small (2 lines). Progress rendering as a list will add ~5-6 lines. This is a straightforward template expansion.
- The arc_resolve output schema in `storytell_system.j2` line 11 currently includes `thematic_question`. The schema string must be updated to remove it. The LLM may emit `thematic_question` in `arc_resolve` for a few turns after deployment — this is safe because Pydantic `model_validate` ignores unknown keys. No explicit migration needed.
- `goal_context` removal from `_arc.j2` means the storyteller no longer sees the goal context in their prompt. This is intentional — it's UI-only now.
- Phase 3 depends on Phase 2 Steps 2.6 and 2.7 (engine context changes providing `turn_no`, `gate`, and updated thread dicts with `progress`/`last_updated_turn`). Ensure Phase 2 is fully complete before starting Phase 3.
- `storytell_user.j2` no longer truncates thread summaries (120 chars) — the new template shows full summaries. This is safe because the soft cap keeps thread count down.

## Status

`completed` — all steps implemented and committed in 8f93040

## Phases

Single phase. Changes four files: `ccya/prompts/storytell_system.j2`, `ccya/prompts/storytell_user.j2`, `ccya/prompts/sections/_thread_list.j2`, `ccya/prompts/sections/_arc.j2`. Also updates `ccya/prompts/context.py` (boundary models).

## Implementation — Phase 3: Prompts

### Context files to load

- `ccya/prompts/storytell_system.j2` (full file, 198 lines)
- `ccya/prompts/storytell_user.j2` (full file, 54 lines)
- `ccya/prompts/sections/_thread_list.j2` (full file, 2 lines)
- `ccya/prompts/sections/_arc.j2` (full file, 26 lines)
- `ccya/prompts/context.py` lines 76-115 (`ArcThreadSummary`, `ArcThreadBlock`, `from_state`)
- `ccya/prompts/context.py` lines 248-253 (`StorytellerBoundary` docstring)
- `docs/design/arc-thread-system-design.md` sections "Core Changes" 2, 3, 4, 5, 6, 7, 8, 9
- `docs/design/arc-thread-system-design.md` section "Decision Table"

### Detailed steps

#### Step 3.1 — Update `_thread_list.j2` to render progress as list + metadata

**File:** `ccya/prompts/sections/_thread_list.j2`

**What:** Rewrite the template to render the progress log as a bulleted list, show `turns_since_last_update`, add soft-cap guidance as a header comment, and show gate status when blocked.

New content:
```
{% if threads %}
### Active Threads ({{ threads | length }} active — target: 2-3 arc, 1-2 scene, ~5 total){% if gate and gate == "block_escalate" %} **Gate: blocked** — new threads will not be added this turn{% endif %}
{% for t in threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}
{%- if t.last_updated_turn is not none %} ({{ turn_no - t.last_updated_turn }} turns ago){% endif %}
{%- for entry in t.progress %}   - {{ entry }}{% endfor %}
{% endfor %}{% else %}No active threads.
{% endif %}
```

Key changes from current:
- Header line includes soft-cap count ("target: 2-3 arc, 1-2 scene, ~5 total")
- Gate status appended to header when `gate == "block_escalate"`
- Progress rendered as indented bullet list under each thread
- `turns_since_last_update` shown parenthetically

Note: `turn_no` must be available in the render context. It's accessible from `state.get("meta", {}).get("turn", 0)`. The executor should check whether `_thread_list.j2` receives `turn_no` or needs to access it from the state dict passed to the renderer. If the section template receives the full `state` dict, use `state.meta.turn` (adjust for actual variable name in render context). If it doesn't, add `turn_no` to the variables passed to the section render.

**Why:** Soft cap guidance makes the constraint visible to the LLM. Progress as a list preserves the investigative trail. Gate status gives the storyteller awareness when thread adds are blocked.

**Validation:** Visual inspection of rendered output. Run the server, trigger a turn, and inspect the storytell user prompt for the thread section.

#### Step 3.2 — Update `_arc.j2` to remove `thematic_question` and `goal_context`

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Remove the `goal_context` rendering block (lines 5-7) and the `thematic_question` rendering block (lines 7-9). Remove `goal_context` from the `resolved_arcs` rendering loop (line 15). The updated template should only render `visible_goal` and `resolution` from the active arc, and `resolved_arcs` with `resolution` text only.

Updated `_arc.j2`:
```
{% if current_arc and current_arc.visible_goal -%}
### Campaign Arc

**Goal:** {{ current_arc.visible_goal }}
{% if current_arc.resolution %}
**Arc resolution:** {{ current_arc.resolution }}
{% endif %}{% if resolved_arcs and resolved_arcs|length > 0 -%}

### Previously Resolved Arcs (TTL)
{%- for ra in resolved_arcs %}
- **Turn {{ ra.resolved_turn }}:** {{ ra.resolution[:120] }}{% endfor -%}

{% endif -%}{% if completed_threads and completed_threads|length > 0 -%}

### Completed Threads (TTL)
{%- for ct in completed_threads[:15] %}
- {{ ct.summary[:80] }} [{{ ct.scope }}][urgency:{{ ct.urgency }}]{% if ct.resolved_turn %} resolved turn {{ ct.resolved_turn }}{% endif %}
{%- endfor %}{% if completed_threads|length > 15 %}...and {{ completed_threads|length - 15 }} more{% endif %}
{%- endif %}
{%- else -%}
No active campaign arc.
{% endif -%}
```

Key deletions:
- `**Narrative guidance — goal context:** {{ current_arc.goal_context }}` removed
- `**Thematic question:** {{ current_arc.thematic_question }}` removed
- `(Goal: {{ ra.goal_context[:80] }})` in resolved arcs loop removed
- `(turn {{ current_arc.resolved_turn }})` removed — the current arc has no `resolved_turn` field. This was a pre-existing bug that would render as an empty `(turn )`.

**Why:** `thematic_question` is deleted from the model. `goal_context` is UI-only — the storyteller doesn't need to see it. `current_arc.resolved_turn` never existed on the current arc context.

**Validation:** Visual inspection of rendered prompt. Run the server, trigger a turn, verify the `_arc` section contains only `visible_goal`, `resolution`, and completed threads.

#### Step 3.3 — Update `arc_resolve` output schema in `storytell_system.j2`

**File:** `ccya/prompts/storytell_system.j2` line 11

**What:** Remove `thematic_question` from the JSON schema example in the Output schema section.

Change from:
```
"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "thematic_question": "...", "drop_threads": ["stale_thread_id"], "new_threads": [...]},
```
To:
```
"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "drop_threads": ["stale_thread_id"], "new_threads": [...]},
```

Also update line 82 where `thematic_question` is described:
Change from:
```
- `thematic_question`: Optional override for the successor arc's thematic question. Omit to inherit from the current arc.
```
To: (remove this bullet entirely)

**Why:** The field is removed from the model. The schema example must match the expected output.

**Validation:** Visual inspection. No reference to `thematic_question` in `arc_resolve` documentation remains.

#### Step 3.4 — Add `goal_update` guidance to `storytell_system.j2`

**File:** `ccya/prompts/storytell_system.j2` — add after the "Arc resolution" section (after line 88 or as a new section after the existing arc resolution guidance)

**What:** Add a new section after the `arc_resolve` guidance block:

```
## Mid-arc goal updates

`goal_update`: A single string — the new visible_goal for the current arc. Use this when the arc's
direction has shifted meaningfully but the arc itself is not over. Examples:
- The goal was "Find the stolen ledger" and the player finds it → update to "Decipher the ledger's contents"
- The goal was "Escape the quarantine zone" and the player has escaped → update to "Find safe passage to the settlement"

Do NOT use `goal_update` when the arc should end — use `arc_resolve` for that. When in doubt:
- Still the same arc, but the goalpost moved → `goal_update`
- A chapter is ending and a new one begins → `arc_resolve`
```

**Why:** The storyteller has no structured way to update `visible_goal` mid-arc. This guidance clarifies when to use `goal_update` vs `arc_resolve`.

**Validation:** Visual inspection.

#### Step 3.5 — Update arc resolution guidance in `storytell_system.j2`

**File:** `ccya/prompts/storytell_system.j2` lines 73-88

**What:** Update the arc resolution guidance section to:
1. Remove reference to `thematic_question` (line 75, 82)
2. Remove thread carry-over language (line 83: "Threads not listed carry over as-is")
3. Add trigger condition guidance (from design doc item 9)
4. Add anti-guidance

Updated section:
```
## Arc resolution

Use `arc_resolve` to signal that this campaign arc has reached its natural conclusion. The system
auto-resolves all arc-scoped threads (moves to completed with state "superseded") and creates a
successor arc that carries forward scene-scoped threads from the old arc. Arc-scoped threads do
NOT carry forward — if a thread remains relevant in the new arc, re-create it via `thread_add`
or `arc_resolve.new_threads`.

When to emit `arc_resolve`:
- **All threads resolved or irrelevant.** Every arc-scoped thread is completed, failed, abandoned,
  or narratively moot. The arc has run its course.
- **Narrative shifted fundamentally.** The story's center of gravity has moved — even if threads
  remain unresolved, the arc's premise no longer fits. Multiple `goal_update` corrections in quick
  succession is a diagnostic signal.
- **Core conflict resolved.** The player decisively achieved or failed the central conflict.
  Remaining threads are clean-up, not arc-driving content.
- **Arc has been coasting 8+ turns.** The `visible_goal` is unchanged and nothing feels fresh.
  The arc is momentum-only.

When NOT to resolve:
- Do NOT resolve an arc just because threads are getting long or because you want to clean up.
  Arc-scoped threads auto-close when the arc resolves, but that's a side effect, not a reason to
  end the arc. Use `goal_update`, thread progress updates, and thread resolutions for mid-arc
  maintenance. `arc_resolve` should feel climactic — it ends a narrative chapter.

**Only emit `arc_resolve` when resolving an arc.** If no arc is being resolved, omit the field
entirely — do NOT return `"arc_resolve": {}`.

- `resolution`: One-sentence narrative summary of how this arc concluded.
- `visible_goal`: The next arc's visible goal. Must use the current context to derive a new
  medium-to-long-term objective that follows naturally from this arc's outcome.
- `goal_context`: 2–3 sentences explaining why this new goal matters to the PC specifically —
  reference the PC's background, relationships, and what they've been through this arc.
- `drop_threads`: Optional list of scene-scoped thread IDs to drop from the successor arc. Use
  this to clean up stale scene threads that shouldn't carry forward. Arc-scoped thread IDs in
  this list are ignored (they auto-close).  
- `new_threads`: Optional list of new thread objects to seed the successor arc with fresh
  narrative tension. At least one new thread recommended per resolution.

Arc resolution timing: Emit `arc_resolve` at climactic moments — prefer turns with natural
pacing (Scene Imperative or neutral). Avoid resolving during Breathe turns (low tension).
This is guidance, not a rule — if the story demands resolution on a Breathe turn, override.

Target cadence: roughly one arc per 8-15 turns (2-3 play sessions). A resolved arc should feel
like a season finale, not a commercial break.
```

**Why:** Clear trigger guidance reduces the zero-resolution problem. Anti-guidance prevents routine resolution. Auto-close language sets correct expectations.

**Validation:** Visual inspection.

#### Step 3.6 — Add urgency decay guidance to thread section

**File:** `ccya/prompts/storytell_system.j2` — add after the existing thread_update guidance (after line 56)

**What:** Add:
```
Thread urgency should decay over time. If a thread has been updated once without the player
addressing it, consider lowering urgency. If it's been inactive for 3+ turns, lower urgency
to background or mark it inactive via `thread_update {active: false}`.
```

**Why:** Finding 2.4 confirmed urgency never decays. Guidance gives the LLM a reason to lower urgency.

**Validation:** Visual inspection.

#### Step 3.7 — Update thread scope guidance for auto-close behavior

**File:** `ccya/prompts/storytell_system.j2` — the existing scope guidance at lines 40-42

**What:** Update line 41 to match the new arc-scoped thread lifecycle:

Change from:
```
Scope determines thread lifetime. **Scene-scoped threads are automatically deleted when the location changes.** Arc-scoped threads persist across locations. Choose deliberately.
```
To:
```
Scope determines thread lifetime. **Scene-scoped threads are automatically deleted when the location changes.** Arc-scoped threads are automatically closed when the campaign arc resolves. Mid-arc, they persist across location changes — resolve them explicitly if they become irrelevant before the arc ends. Choose deliberately.
```

**Why:** The old guidance said "Arc-scoped threads persist across locations" without mentioning they auto-close on arc end. Update matches the new auto-close behavior.

**Validation:** Visual inspection.

#### Step 3.8 — Add no-op thread_updates discouragement

**File:** `ccya/prompts/storytell_system.j2` — add after the thread_update critical rules block (after line 55)

**What:** Add a bullet:
- Only emit `thread_update` when you are changing a thread's state. Do not emit updates with all-null or empty fields.

**Why:** Finding 2.5 confirmed many thread_updates carry no meaningful change. This discourages wasted emissions.

**Validation:** Visual inspection.

#### Step 3.9 — Add gate status rendering context

**File:** `ccya/prompts/sections/_thread_list.j2` — already handled in Step 3.1

**What:** The pacing gate `PacingContext.gate` value must be available to the thread list renderer. The executor must verify that `gate` is passed to the section template context or accessible from the state dict. If not already available, add `gate` to the variables passed when rendering `_thread_list.j2`.

The caller at `_thread_list.j2` render site (likely in `storytell_system.j2` or a Python rendering helper) currently passes something like `{"threads": arc.threads}`. Add `gate: pacing_context.gate` to this dict.

**Why:** The thread section shows "Gate: blocked" when the pacing gate is blocking thread adds. The renderer needs the gate value.

**Validation:** Visual inspection — gate status displays correctly in the thread section header.

#### Step 3.10 — Update `ArcThreadSummary` context model for new fields

**File:** `ccya/prompts/context.py` lines 76-84 (`ArcThreadSummary`)

**What:** Add `last_updated_turn` field to the summary model, and add `progress` field for the thread list template to render.

Change from:
```python
class ArcThreadSummary(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    urgency: Literal["background", "normal", "urgent"]
    progress: str = ""
    active: bool
```
To:
```python
class ArcThreadSummary(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    urgency: Literal["background", "normal", "urgent"]
    progress: list[str] = Field(default_factory=list)
    active: bool
    last_updated_turn: int | None = None
```

**Why:** `_thread_list.j2` iterates `t.progress` as a list and displays `t.last_updated_turn`. The context summary model must expose these fields or the template alignment check will fail.

**Validation:** `make check` passes.

#### Step 3.11 — Update `ArcThreadBlock` to match new arc shape

**File:** `ccya/prompts/context.py` lines 87-92 (`ArcThreadBlock`)

**What:** Remove `thematic_question`, add `resolution` and `completed_threads` support. The updated `_arc.j2` references `current_arc.resolution` and `current_arc.completed_threads` — these must be available.

Change from:
```python
class ArcThreadBlock(BaseModel):
    visible_goal: str
    thematic_question: str
    threads: list[ArcThreadSummary]
```
To:
```python
class ArcThreadBlock(BaseModel):
    visible_goal: str
    resolution: str | None = None
    threads: list[ArcThreadSummary]
    completed_threads: list[ArcThreadSummary] = Field(default_factory=list)
```

**Why:** `thematic_question` is removed from all models (Phase 1). The `_arc.j2` template accesses `current_arc.resolution` and `completed_threads` (as a top-level variable). `completed_threads` is a top-level variable in the context, not a subfield of `current_arc` — it's listed here for alignment check purposes since the template accesses it via `completed_threads` in scope.

Note: `completed_threads` IS a top-level variable in the render context (built from `current_arc_ctx["completed_threads"]` in `narrate.py:68` and accessed as a bare variable in `_arc.j2`). The alignment model only checks fields on the root boundary model. If `completed_threads` is not on `ArcThreadBlock` (which is nested under `current_arc`), the alignment check won't complain — but the template needs it at the top level regardless. Keeping it on `ArcThreadBlock` as a reference for the field shape is fine.

The `resolved_turn` field is NOT added to `ArcThreadBlock` — the `_arc.j2` template's `{{ current_arc.resolved_turn }}` reference is a pre-existing bug (the current arc never has a resolved turn). The fix is applied in Step 3.2 (removing the `resolved_turn` reference from the template).

**Validation:** `make check` passes.

#### Step 3.12 — Update `from_state` method on `ArcThreadBlock`

**File:** `ccya/prompts/context.py` lines 94-115 (`ArcThreadBlock.from_state`)

**What:** Remove the `thematic_question` mapping from the classmethod, and add `resolution` and `completed_threads` mapping.

Change from:
```python
    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ArcThreadBlock:
        arc = state.get("arc", {})
        raw_threads = []
        for t in arc.get("threads", []) + arc.get("completed_threads", []):
            if isinstance(t, ArcThreadSummary):
                raw_threads.append(t)
            elif isinstance(t, dict):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.get("id", ""),
                        summary=t.get("summary", ""),
                        scope=t.get("scope", "arc"),
                        urgency=t.get("urgency", "normal"),
                        progress=t.get("progress", []) if isinstance(t.get("progress"), list) else [t.get("progress", "")] if t.get("progress") else [],
                        active=t.get("active", True),
                    )
                )
            else:
                raw_threads.append(t)
        return cls(
            visible_goal=arc.get("visible_goal", ""),
            thematic_question=arc.get("thematic_question", ""),
            threads=[t for t in raw_threads if isinstance(t, ArcThreadSummary)],
        )
```
To:
```python
    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ArcThreadBlock:
        arc = state.get("arc", {})
        raw_threads = []
        for t in arc.get("threads", []) + arc.get("completed_threads", []):
            if isinstance(t, ArcThreadSummary):
                raw_threads.append(t)
            elif isinstance(t, dict):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.get("id", ""),
                        summary=t.get("summary", ""),
                        scope=t.get("scope", "arc"),
                        urgency=t.get("urgency", "normal"),
                        progress=t.get("progress", []) if isinstance(t.get("progress"), list) else [t.get("progress", "")] if t.get("progress") else [],
                        active=t.get("active", True),
                        last_updated_turn=t.get("last_updated_turn"),
                    )
                )
            else:
                raw_threads.append(t)
        completed = [t for t in arc.get("completed_threads", []) if isinstance(t, ArcThreadSummary)]
        return cls(
            visible_goal=arc.get("visible_goal", ""),
            resolution=arc.get("resolution"),
            threads=[t for t in raw_threads if isinstance(t, ArcThreadSummary)],
            completed_threads=completed,
        )
```

**Why:** Remove `thematic_question` reference, add `resolution` and `completed_threads` from state. Pass through `last_updated_turn` on thread summaries.

**Validation:** `make check` passes.

#### Step 3.13 — Update `StorytellerBoundary` docstring

**File:** `ccya/prompts/context.py` lines 248-253

**What:** Update the docstring to remove `thematic_question` reference.

Change from:
```python
class StorytellerBoundary(BaseModel):
    """Context for storytell_user.j2.

    npc_roster/location/inventory/conditions come from extraction_ctx.
    all_threads/world_state/intent/pacing_context/recent_turns/turn_no/band are top-level variables.
    current_arc provides campaign arc metadata (visible_goal, thematic_question) via _arc.j2 include.
    """
```
To:
```python
class StorytellerBoundary(BaseModel):
    """Context for storytell_user.j2.

    npc_roster/location/inventory/conditions come from extraction_ctx.
    all_threads/world_state/intent/pacing_context/recent_turns/turn_no/band/gate are top-level variables.
    current_arc provides campaign arc metadata (visible_goal, resolution) via _arc.j2 include.
    all_threads is mapped to threads via {% set threads = all_threads %} before _thread_list.j2 include.
    """
```

**Why:** `thematic_question` is removed everywhere. `gate` is now a top-level variable (Phase 2 Step 2.7). The docstring must match.

**Validation:** `make check` passes.

#### Step 3.14 — Switch `storytell_user.j2` to use `_thread_list.j2` include

**File:** `ccya/prompts/storytell_user.j2` lines 13-19

**What:** Replace the inline thread rendering block with an include of `_thread_list.j2`, using `{% set threads = all_threads %}` before the include to map the variable name.

Change from:
```jinja2
{% if all_threads %}
## threads ({{ all_threads|length }} total — unified list; [SCENE] threads are auto-removed on location change)
{% for t in all_threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }} {% if not t.active %}(dormant){% endif %} [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}{% if t.progress %} [progress: {{ t.progress }}]{% endif %}
{% endfor -%}{% else %}
## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
{% endif %}
```
To:
```jinja2
{% set threads = all_threads %}
{% include "sections/_thread_list.j2" %}
```

Key changes:
- Removes old header text ("unified list; [SCENE] threads are auto-removed on location change") — the new `_thread_list.j2` header has its own text with soft-cap guidance.
- Removes `truncate(120)` on summary — the new template shows full summary. Remove intentional: the soft cap keeps thread count down, so truncation is unnecessary.
- Removes `[progress: {{ t.progress }}]` inline text — the new template renders progress as an indented bullet list.
- `all_threads` variable must stay in the render context (needed for `{% set threads = all_threads %}`). This is already provided by `StorytellerBoundary.all_threads`.
- `gate` must be available in the storytell render context — this was added in Phase 2 Step 2.7.

**Why:** Unifies thread rendering across narrate and storytell prompts. Single source of truth for thread display. The new `_thread_list.j2` provides soft-cap guidance, gate status, progress-as-list, and `turns_since_last_update` — all of which benefit the storyteller.

**Validation:** Visual inspection. Run the server, trigger a turn, inspect the storytell user prompt. The thread section should match the narrate prompt's thread section format.

### Tests to write or update

No test files exist in the current repo. Run `make check` to verify no syntax errors. Visually inspect rendered prompts by running the server and examining the storytell user prompt for a generated turn.
