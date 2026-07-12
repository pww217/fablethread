# Phase C: ThreadResolution Outcome Field & Completed Threads Visibility

## Status
`completed`

## Phases

Add mandatory `outcome: str` field to `ThreadResolution`, persist outcomes on completed threads via `_apply_thread_resolutions()`, render ALL threads (active + latent) in the Narrator prompt, render completed threads with outcomes in both Storyteller and Narrator user prompts, and add system prompt guidance on latent thread handling (don't surface outwardly, subtle foreshadowing allowed).

## Issue
When a thread resolves (resolved/failed/abandoned), no record is made of *how* it resolved — who did what, what the cost was, what the outcome meant. Completed threads are moved to `arc.completed_threads` with only a label (`resolution_state`) and zero prose context. Future Storyteller calls have no way to know how past plot lines ended when generating new thread suggestions or narrating consequences.

## Solution
Add mandatory `outcome: str` field to `ThreadResolution` — one past-tense sentence written by the Storyteller at resolution time. Persist this on completed threads in `_apply_thread_resolutions()`. Render completed threads with outcomes in both Storyteller and Narrator prompts so future LLM calls have full continuity about how past tensions ended.

## Firm decisions
1. One-sentence outcome is sufficient — no multi-sentence summaries or structured resolution data needed (user decision)
2. Outcome processing goes into `_apply_thread_resolutions()` at turn.py:360; urgency decay stays in `_apply_thread_signals()` at turn.py:159 — separate functions, no conflict
3. Completed thread outcomes visible to both Storyteller AND Narrator (user decision #2 confirmed)
4. ALL threads (active + latent) visible in Narrator prompt — not just scene-scoped active threads
5. System prompts guide LLMs to actively push players towards exploring latent threads through narration, choices, and thread suggestions — without directly exposing the thread content ("show, don't tell").
6. No migration for old completed threads without outcome field — `outcome: str | None = None` on ArcThread allows legacy loads; new resolutions require the field per ThreadResolution model
7. Phase A must complete first (removes recent_events from StorytellerResult/StateDelta, simplifying extraction.py context)

## Non-goals
- No structured resolution data beyond one sentence
- No outcome editing after persistence — once written by LLM at resolution time, it's immutable
- No UI changes for outcomes in templates/index.html (out-of-scope for this redesign phase)
- No eval rubric updates for outcome quality assessment

## Risks, Ambiguities, and Blockers
- **Ambiguous:** Whether to render completed_threads in Storyteller prompt at all — design doc says "not in storyteller at this point unless resolved" but user decision #2 explicitly confirmed outcomes visible to both. This plan renders them in both prompts.
- **Risk:** `_apply_thread_resolutions()` has complex dedup logic (lines 394-459) that may need careful updating to preserve the existing `resolution_state` update path while adding outcome propagation. The current code updates resolution_state on line 421-423; must add outcome alongside it.
- **Risk:** narrate.py's `_narrate_messages()` builds `current_arc_ctx` from arc state (lines 56-74) but does NOT include completed_threads — only active threads. Must add completed_threads to the context dict passed to narrate_user.j2. Additionally, narrate_user.j2's template currently only renders scene-scoped threads — must be rewritten to show all threads (Step C.6).
- **Blocker:** Phase A must complete first because it changes StorytellerResult model fields; ThreadResolution.outcome addition depends on stable extraction.py rendering path after recent_events removal.

## Implementation — Phase C: Add ThreadResolution outcome field & make outcomes visible in prompts

### Context files to load
1. `ccya/models.py` (ThreadResolution, ArcThread, CampaignArc models)
2. `ccya/engine/turn.py` (_apply_thread_resolutions function at line 360-466)
3. `ccya/prompts/storytell_system.j2` (JSON schema example and thread_resolve instructions; latent thread handling guidance)
4. `ccya/prompts/narrate_system.j2` (latent thread handling instruction addition)
5. `ccya/prompts/storytell_user.j2` (active threads rendering, where to add completed_threads section)
6. `ccya/engine/narrate.py` (_narrate_messages function at line 19-118, current_arc_ctx construction at lines 56-74)
7. `ccya/prompts/narrate_user.j2` (where threads and arc context render — replace scene-only section with all-threads, add completed_threads section)

### Detailed steps

#### Step C.1 — Add outcome field to ThreadResolution and ArcThread models in models.py

**File:** `ccya/models.py`

**What:** Two changes:
1. In `class ThreadResolution(BaseModel)` at line 356-359, add a required `outcome: str = ""` field after `resolution_state`. The model becomes:
```python
class ThreadResolution(BaseModel):
    """Structured resolution for a thread — replaces scene_pressure_add/remove/update semantics."""
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
    outcome: str = ""  # one past-tense sentence written at resolution time; stored on completed ArcThread
```

2. In `class ArcThread(BaseModel)` at line 28-45, add an optional `outcome: str | None = None` field after the existing `resolution_state` field (line 39). The model becomes:
```python
    resolution_state: str | None = None  # set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads

    outcome: str | None = None  # set from ThreadResolution.outcome when moved to completed_threads; None on active/legacy threads
```

**Why:** `ThreadResolution` is the LLM-facing model — it must require an outcome sentence at resolution time. `ArcThread.completed_threads[]` stores historical resolutions and may contain legacy entries without outcomes, so the field is nullable with a default of None to avoid breaking old state loads (no migration needed per user decision).

**Validation:** `rg "outcome.*str" ccya/models.py | grep -E "(ThreadResolution|ArcThread)"` should show both new fields. Pydantic validation: `python -c "from ccya.models import ThreadResolution; r = ThreadResolution(id='t1', resolution_state='resolved', outcome='The bridge collapsed behind them.' ); print(r.outcome)"` should succeed with the one-sentence string.

#### Step C.2 — Complete _apply_thread_resolutions() in turn.py to persist outcomes on completed threads

**File:** `ccya/engine/turn.py`

**What:** One change at line 421-423 (the thread update block inside `_apply_thread_resolutions()`):
1. Add `"outcome": res.outcome` alongside the existing `"resolution_state"` in both model_copy calls:
   - Line 421-423: Change `thread.model_copy(update={"resolution_state": res.resolution_state})` to include outcome: `thread.model_copy(update={"resolution_state": res.resolution_state, "outcome": res.outcome})`.
   - Line 431-433 (dedup path): Change the existing line similarly — add `"outcome": res.outcome` to the update dict.

**Why:** Currently `_apply_thread_resolutions()` only propagates `resolution_state` from ThreadResolution to the completed ArcThread. The new `outcome: str` field must be persisted alongside it so that when the thread appears in `arc.completed_threads`, its resolution prose is available for future prompt rendering (steps C.3 and C.4). Both update paths — the initial move to completed (line 421) and the dedup re-update path (line 431)— must be updated because both are valid code paths depending on whether a thread was already in completed_threads or is being added fresh.

**Validation:** `rg "model_copy.*resolution_state" ccya/engine/turn.py` should show exactly two matches, each with `"outcome": res.outcome` alongside the resolution_state update. Load state and verify that after resolving a thread via StorytellerResult.thread_resolve, the completed thread in arc.completed_threads has both resolution_state and outcome set correctly.

#### Step C.3 — Update storytell_system.j2: add outcome to thread_resolve JSON schema example and instruction text

**File:** `ccya/prompts/storytell_system.j2`

**What:** Two changes at lines 14-36 (the thread operations section):
1. In the JSON schema example at line 14, change `"thread_resolve": [{"id": "thread_id", "resolution_state": "resolved"}]` to include outcome: `"thread_resolve": [{"id": "thread_id", "resolution_state": "resolved", "outcome": "The enemy retreated into the tunnels after a fierce battle."}]`.
2. In the instruction text at lines 31-35, add an `outcome:` field description after the resolution_state bullet list:
```markdown
`thread_resolve`: Threads fully resolved this turn (the tension ends, rather than just progressing). Each entry has an `id`, a `resolution_state`, and an `outcome`:
- `"resolved"` = tension addressed successfully
- `"failed"` = tension escalated negatively  
- `"abandoned"` = player moved on without addressing it

Each resolution MUST include an `outcome` field: one past-tense sentence describing what happened. Example: `"outcome": "The guard let them pass after they showed the merchant's seal."`. Do not omit this — future Storyteller calls will read these outcomes to understand how past plot lines ended.
```

**Why:** The JSON schema is what the LLM sees as output format — it must match ThreadResolution model fields exactly (step C.1). Without the outcome field in both the example and instructions, small models may omit it or return empty strings, breaking downstream completion persistence. The explicit instruction about why outcomes matter helps the Storyteller understand this isn't optional metadata — it's continuity context for future turns.

**Validation:** `rg "thread_resolve.*outcome" ccya/prompts/storytell_system.j2` should show both the JSON schema example and the new instruction text referencing outcome. Verify that a test LLM response with thread_resolve including outcome validates against ThreadResolution model from step C.1.

#### Step C.4 — Add completed_threads section to storytell_user.j2: render past resolutions for Storyteller continuity

**File:** `ccya/prompts/storytell_user.j2`

**What:** One addition after line 18 (after the active threads loop, before the `{% else %}` block):
Insert a new conditional block that renders completed threads with outcomes when any exist:
```jinja
{% if current_arc and current_arc.completed_threads %}
## past resolutions (for continuity — do not re-open resolved tensions)
{% for t in current_arc.completed_threads %}- `{{ t.id }}` [{{ t.resolution_state or "unknown" | upper }}] {{ t.outcome or "(no outcome recorded)" }}
{% endfor -%}
{% endif %}
```

Place this after line 18 (the active threads loop) and before the `{% else %}` at line 19. The full block should read:
```jinja
## threads (all — unified list, scope handled by Python)
{% for t in all_threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }} {% if not t.active %}(dormant){% endif %} [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}{% if t.tags %} tags: {{ t.tags | join(', ') }}{% endif %}{% if t.last_seen_turn %} (last seen T{{ t.last_seen_turn }}){% endif %}
{% endfor -%}
{% if current_arc and current_arc.completed_threads %}
## past resolutions (for continuity — do not re-open resolved tensions)
{% for t in current_arc.completed_threads %}- `{{ t.id }}` [{{ t.resolution_state or "unknown" | upper }}] {{ t.outcome or "(no outcome recorded)" }}
{% endfor -%}
{% endif %}{% else %}
## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
```

**Why:** The Storyteller generates new thread suggestions and narrates consequences — it needs to know how past plot lines ended to avoid contradicting established outcomes (e.g., suggesting a thread about "rescuing someone" when their outcome was `"The guard fell in battle"`). The directive "(for continuity — do not re-open resolved tensions)" explicitly tells the LLM these are historical records, not active suggestions. Showing completion status alongside each outcome helps distinguish between successful resolutions and failures/abandonments.

**Validation:** Render a test prompt with `current_arc.completed_threads` containing 2-3 entries with outcomes and verify output shows past resolutions section after active threads. Check that the `{% else %}` block at line 19 remains intact (no syntax errors from inserting before it).

#### Step C.5 — Pass completed_threads to narrate_user.j2 in narrate.py & add rendered section to narrate_user.j2

**File:** `ccya/engine/narrate.py`

**What:** One change at line 74 (end of current_arc_ctx construction):
1. Add `"completed_threads": arc.get("completed_threads") or []` as a new key in the `current_arc_ctx` dict that starts at line 56. The full dict should include this after line 73 (`"hidden_truths"`).

**Why:** narrate_user.j2 receives `current_arc` from narrate.py's user_ctx (line 100) and system prompt context (line 107), but the current_arc_ctx construction at lines 56-74 only includes active threads. To render completed_threads in narrate_user.j2, they must first be passed through this dict.

**Validation:** `rg "completed_threads.*arc.get" ccya/engine/narrate.py` should show one match confirming completion_threads is extracted from arc state and added to current_arc_ctx at line 74. Verify that the template can access it via `current_arc.completed_threads`.

#### Step C.6 — Rewrite narrate_user.j2 thread section: show ALL threads (active + latent) and completed_threads with outcomes

**File:** `ccya/prompts/narrate_user.j2`

**What:** Two changes:
1. Replace the scene-scoped-only thread block at lines 36-42 with a full thread rendering section that shows ALL threads (scene + arc, active + latent/dormant), using current_arc.threads from narrate.py:
```jinja
{% if current_arc and current_arc.threads %}
### Current Threads
{% for t in current_arc.threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}{% if t.last_seen_turn %} (last seen T{{ t.last_seen_turn }}){% endif %}
{% endfor -%}
{% elif state.arc and state.arc.threads %}
### Current Threads
{% for t in state.arc.threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}{% if t.last_seen_turn %} (last seen T{{ t.last_seen_turn }}){% endif %}
{% endfor -%}
{% endif %}
```

2. Add completed_threads section after the thread section and after `{% include "sections/_arc.j2" %}` (line 59):
```jinja
{% if current_arc and current_arc.completed_threads -%}
### Past Resolutions
{% for t in current_arc.completed_threads %}- `{{ t.id }}` [{{ t.resolution_state or "unknown" | upper }}] {{ t.outcome or "(no outcome recorded)" }}
{% endfor -%}{%- endif %}
```

The full replaced block (original lines 36-42) becomes:
```jinja
{% if current_arc and current_arc.threads %}
### Current Threads
{% for t in current_arc.threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}{% if t.last_seen_turn %} (last seen T{{ t.last_seen_turn }}){% endif %}
{% endfor -%}
{% elif state.arc and state.arc.threads %}
### Current Threads
{% for t in state.arc.threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}{% if t.last_seen_turn %} (last seen T{{ t.last_seen_turn }}){% endif %}
{% endfor -%}
{% endif %}
```

And after line 59 (`{% include "sections/_arc.j2" %}`), insert:
```jinja
{% if current_arc and current_arc.completed_threads -%}
### Past Resolutions
{% for t in current_arc.completed_threads %}- `{{ t.id }}` [{{ t.resolution_state or "unknown" | upper }}] {{ t.outcome or "(no outcome recorded)" }}
{% endfor -%}{%- endif %}
```

**Why:** The Narrator previously only saw scene-scoped active threads (filtered by `t.scope == 'scene'` in the Jinja template). This meant arc-scoped threads, latent/dormant threads, and completed threads with outcomes were invisible. Per user requirement, ALL arc information must be visible in the Narrator prompt. Active, latent, and completed threads all provide context for consistent narration — the system prompt (Step C.7) instructs not to outwardly surface latent/hidden details but allows subtle foreshadowing. The fallback `state.arc.threads` ensures threads are still shown even when current_arc_ctx isn't available.

**Validation:** Render a test prompt with current_arc containing threads (mix of active + latent + different scopes) and completed_threads with outcomes. Verify:
1. All threads appear under "### Current Threads" with scope tags and (latent) marker where applicable
2. Completed threads appear under "### Past Resolutions" with resolution state and outcome
3. The section order is: Current Threads → _arc.j2 (visible_goal etc.) → Past Resolutions
4. No syntax errors from Jinja2 template parsing

#### Step C.7 — Update narrate_system.j2: latent thread guidance — push towards discovery

**File:** `ccya/prompts/narrate_system.j2`

**What:** One addition after the existing arc/thread context section (after thread visibility rules). Add a paragraph about latent thread handling:

```markdown
You have visibility into all threads — active, latent, and completed — plus their resolutions. Use this knowledge actively. Latent threads represent narrative threads the party has not yet discovered. Your job is to push the player gently towards them through narration, environmental detail, and NPC behaviour — without explicitly exposing the thread content. Show, don't tell. An NPC glancing nervously at a locked door, a flicker of torchlight from an unexplored tunnel, a curious sound carried on the wind. Introduce narrative elements that hint at the latent thread's existence and invite investigation. Build the 4 player choices to naturally lead toward discovery. If a latent thread has gone unsurfaced for many turns, increase the pressure — make the hints less subtle.
```

**Why:** Per user requirement, the Narrator should actively guide players towards discovering latent threads. This is not about hiding information — it's about presenting it through narrative subtext rather than exposition. The system prompt instructs active orchestration: push, hint, invite — but never state outright what the thread contains.

**Validation:** `rg "latent.*thread\|push.*toward\|show.*tell" ccya/prompts/narrate_system.j2` should show the new instruction. Verify it uses active guidance language ("push", "invite", "build choices toward") rather than restrictive language.

#### Step C.8 — Update storytell_system.j2: latent thread guidance — push towards discovery

**File:** `ccya/prompts/storytell_system.j2`

**What:** One addition after the thread generation rules section (around the spot where thread_add/advance/resolve instructions are). Add a paragraph about latent thread handling:

```markdown
You have visibility into all threads — including those marked (dormant/latent) — plus past resolutions with outcomes. Use this knowledge actively. Latent threads represent narrative threads the party has not yet discovered but can be drawn toward. When generating new thread suggestions, choose actions and complications that create circumstances where a dormant thread could naturally surface — a character's past catching up, a long-silent threat stirring. When selecting beats and narration, use beat types and pacing to build tension toward latent discoveries. Never expose the latent content directly — instead, craft situations that make discovery feel earned and natural. The 4 player choices, suggested actions, and complications are your primary tools for gently steering the player toward what they don't yet know.
```

**Why:** The Storyteller generates thread suggestions, beats, and pacing — all of which can be used to orchestrate gradual discovery of latent threads. The system prompt should actively encourage this orchestration rather than warning against it. The distinction between "show" and "tell" is the guiding principle: show the shadow, not the source.

**Validation:** `rg "latent.*thread\|dormant.*thread\|push.*toward\|steer.*toward" ccya/prompts/storytell_system.j2` should show the new instruction. Verify the instruction is placed near the thread_add/advance/resolve guidance section.

### Tests to write or update
None — tests are temporarily removed during refactor per AGENTS.md rules. Run `make check && make typecheck` as final step instead.

### REPOMAP updates required
1. `docs/repomap.md`: Update ThreadResolution model entry in "Extraction field routing" section to include `outcome: str = ""` field; update ArcThread model entry to show new nullable outcome field on completed threads; add note about `_apply_thread_resolutions()` persisting outcomes alongside resolution_state at turn.py line 421-433.
2. `docs/repomap.md`: Add note that narrate_user.j2 renders ALL threads (active + latent) not just scene-scoped, with scope tags and (latent) markers.
3. `docs/repomap.md`: Note system prompt sections on latent thread handling in narrate_system.j2 and storytell_system.j2.
