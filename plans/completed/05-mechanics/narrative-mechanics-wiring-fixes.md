# Narrative Mechanics Wiring and Prompt Template Fixes

## Status
`completed`

## Phases

4 phases: Fix critical template bugs, thread context structure mismatch, incomplete directive list, and campaign arc duplication — restoring correct mechanics plumbing from Python through Jinja templates into LLM prompts.

## Issue

The narrative engine's Python-to-prompt wiring has three categories of defects: (1) a broken conditional in `narrate_user.j2` causes the GM Beat block to render twice with incorrect logic, (2) `current_arc_ctx['threads']` in `narrate.py` drops scope/id/active fields from thread dicts, breaking `_arc.j2`'s ability to filter scene vs arc threads as designed by the unified threads model, and (3) hardcoded narration directives in `narrate_system.j2` are incomplete relative to dynamic values Python can generate via `_compute_narration_directive()` and `_compute_pacing_context()`. These defects cause the narrator LLM to receive duplicate/conflicting beat instructions, miss scene-scoped thread context entirely, and lack guidance for dynamically generated directive combinations like "Resolve a Threat; Combat Fatigue".

## Solution

Fix each defect in order of dependency: (1) repair the broken Jinja conditional in `narrate_user.j2`, (2) enrich `current_arc_ctx['threads']` in `narrate.py` to include scope/id/active fields so `_arc.j2` can filter correctly, (3) expand hardcoded narration directives in `narrate_system.j2` to cover all dynamic values Python generates, and (4) deduplicate the Campaign Arc section between system prompt and user template. The expected outcome is correct mechanics data flowing from Python through Jinja templates into LLM prompts with no duplication, no missing fields, and complete directive guidance.

## Firm decisions

1. System prompts contain instructions/guidance; user prompts contain dynamic context only — this is the separation boundary for all prompt fixes in this plan.
2. Thread scope filtering must use Python-enriched data (current_arc_ctx) rather than relying on Jinja to access raw state fields, because current_arc_ctx is a simplified view designed for narrator consumption.
3. The PacingContext struct defined in `turn.py:68-79` is the single source of truth for pacing directives — no template should hardcode directive semantics that Python can generate dynamically.
4. No changes to Pydantic models, state shape, or pipeline orchestration logic are needed — this plan addresses prompt wiring and template correctness only.

## Non-goals

- Changes to `_compute_pacing_context()` computation logic (Python-side directive generation is correct).
- Changes to extraction pipeline streams (scene/state/progress) — they receive mechanics data correctly via pacing_context in user templates.
- Changes to thread lifecycle engine (`_apply_thread_signals`, `_apply_thread_resolutions`) — Python arc management works as designed.
- Adding new prompt sections or features — only fixing existing broken/duplicated content.

## Risks, Ambiguities, and Blockers

1. **State shape discrepancy:** The repomap shows `arc.active_threads` / `arc.latent_threads` as separate fields in state.yaml (line 174-175), but campaign-arcs.md states these are merged into unified `arc.threads[]`. If legacy active/latent fields still exist in some saves, the Python code at narrate.py:50 (`arc.get("threads")`) may miss them. Validation needed on existing save files.

2. **_arc.j2 scope filter behavior:** The current `_arc.j2` template filters by `t.scope == 'scene'`. If this was never working (because scope is dropped in Python), there's no baseline for what the narrator should see — need to confirm intended behavior from campaign-arcs.md design intent that scene threads appear in user prompt context while arc threads appear in system prompt context.

3. **Hardcoded directive list completeness:** The narration directives section in narrate_system.j2 lists 8 directive types, but Python can generate dynamic combinations (e.g., "Pressure; Combat Fatigue", "Breathe; Resolve a Threat"). Adding all possible secondary modifiers is impractical — the fix should document that the user prompt provides the actual value and system guidance covers primary directives only.

4. **Campaign arc duplication:** Both narrate_system.j2 (lines 61-88) and _arc.j2 (included in user prompt at line 13 of narrate_user.j2) contain campaign arc context with visible_goal, thematic_question, threads. Removing one copy requires confirming the remaining copy serves both LLM roles correctly — system needs arc update instructions, user needs full scene context.

## Implementation — Phase 1: Fix broken GM Beat conditional in narrate_user.j2

### Context files to load
- `ccya/prompts/narrate_user.j2` (lines 70-95)
- `ccya/engine/turn.py` lines 1098-1106 (pending_gm_beat lifecycle for context on how beat flows between turns)

### Detailed steps

#### Step 1.1 — Fix duplicate GM Beat block with broken elif logic in narrate_user.j2:75-91

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace the broken conditional block at lines 75-91 with three separate, non-overlapping conditions:
- `{% if pending_beat and pending_beat.type %}` → render GM Beat instruction (single occurrence)
- `{% if pacing_context and pacing_context.directive %}` → render Narration Directive  
- `{% if not pending_beat or not pending_beat.type %}{% if pacing_context and pacing_context.beat_hint %}` → render Beat Hint only when there is no pending beat

The current code renders GM Beat twice (lines 75-78 AND lines 84-87) because the second block uses `{% elif %}` attached to a new `{% if pending_beat %}` instead of being an alternative path. The `elif` at line 88 is syntactically connected to the duplicate GM Beat block, not to the Narration Directive block above it, so beat_hint never renders as intended when there's no pending_beat but there is a beat_hint.

**Why:** The broken conditional causes two defects: (1) GM Beat instruction appears twice in the user prompt, wasting tokens and confusing the LLM with duplicate backstage direction; (2) `beat_hint` from pacing_context can never render because it's trapped behind an `{% elif %}` that requires the second `pending_beat.type` check to be false — but if pending_beat exists, beat_hint is irrelevant anyway. The correct logic is: GM Beat takes priority when present; otherwise show beat_hint as a softer suggestion from pacing_context.

**Validation:** Read the rendered template output for a turn with both `pending_beat.type` and `pacing_context.beat_hint`. Confirm exactly one "GM Beat:" section appears, no duplicate, and that beat_hint renders in its own section when there is no pending_beat but there is a beat_hint.

### Tests to write or update
None — tests are temporarily removed per AGENTS.md. Manual verification via `ev.py prompt <turn> narrate user` on a save with both pending_beat and pacing_context.beat_hint present.

### REPOMAP updates required
No changes needed — this is a template-only fix, no module boundary or API changes.

## Implementation — Phase 2: Fix thread context structure mismatch in narrate.py + _arc.j2

### Context files to load
- `ccya/engine/narrate.py` lines 47-65 (current_arc_ctx construction)
- `ccya/prompts/sections/_arc.j2` (thread filtering logic expecting scope field)
- `ccya/models.py` lines 43-58 (ArcThread model definition with scope, active fields)

### Detailed steps

#### Step 2.1 — Enrich current_arc_ctx['threads'] in narrate.py:50-64 to include scope, id, and active fields

**File:** `ccya/engine/narrate.py`

**What:** In the thread comprehension at lines 55-63, change from extracting only `{summary, urgency, tags}` to also including `scope`, `id`, and `active`. The dict for each thread should be:
```python
{
    "summary": t.get("summary", "") or getattr(t, "summary", ""),
    "urgency": t.get("urgency", "normal") or getattr(t, "urgency", "normal"),
    "tags": t.get("tags", []) or getattr(t, "tags", []),
    "scope": t.get("scope", "arc") or getattr(t, "_arc.j2 can then filter by scope == 'scene' as designed.

The dormant thread filter at line 61 stays the same (exclude active=False threads). The comprehension iterates `all_threads` from state.arc.threads[] and applies the same filter, but now each dict carries enough fields for Jinja to distinguish scene vs arc scopes.

**Why:** `_arc.j2` filters by `{% if t.scope == 'scene' %}` at line 13-18, but scope is not in the dicts passed from Python, so this filter silently produces empty output every turn. The narrator never sees scene-scoped threads in its arc context section despite the design intent (campaign-arcs.md states scene threads should be visible to narrator for beat integration). Adding scope/id/active fields costs ~20 chars per thread and restores intended functionality with zero behavioral change to dormant filtering logic.

**Validation:** Run `ev.py prompt <turn> narrate user` on a save with active scene-scoped threads in the arc. Confirm the "Active Threads" section under Campaign Arc shows entries tagged as `[SCENE]`. Before this fix, that section is empty despite Python having scope=scene threads in state.arc.threads[].

#### Step 2.2 — Verify _arc.j2 thread rendering uses correct field names after enrichment

**File:** `ccya/prompts/sections/_arc.j2`

**What:** No code change needed. The existing template at line 18 (`{% for t in scene_threads %}` with `{% if t.active %}` filter) will now work correctly because scope is present on each thread dict and active is preserved from the dormant filter in Python. Confirm that `t.last_seen_turn` renders as expected — it's already accessed via Jinja's `.get()`-style syntax (`{{ t.last_seen_turn or '?' }}`) which works on dicts with string keys, matching what Python now provides.

**Why:** Validate that no template changes are needed after the Python enrichment step. The existing `_arc.j2` was written expecting scope/active fields — it just never received them from Python. This is a verification-only step to confirm zero additional work in Jinja.

**Validation:** Same as Step 2.1 validation — check rendered user prompt shows scene threads with last_seen_turn values. Also verify arc-scoped threads do NOT appear in the "Active Threads" section (they should be filtered out by scope != 'scene').

### Tests to write or update
None — tests are temporarily removed per AGENTS.md. Manual verification via `ev.py props <turn> narrate` on a save with mixed scene/arc scoped threads, then diff before/after the fix.

### REPOMAP updates required
No changes needed — this is an internal data structure enrichment in `_narrate_messages()`, no public API or module boundary change. The repomap's description of `current_arc_ctx` as a Python-internal variable for prompt building remains accurate.

## Implementation — Phase 3: Fix incomplete narration directives list in narrate_system.j2

### Context files to load
- `ccya/prompts/narrate_system.j2` lines 127-140 (narration directives section)
- `ccya/engine/turn.py` lines 467-553 (`_compute_narration_directive()` directive generation logic for reference on what Python can produce)

### Detailed steps

#### Step 3.1 — Expand narration directives in narrate_system.j2:130-138 to cover all dynamic values from Python

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add missing directive entries to the hardcoded list at lines 130-138. The current list has Breathe, Overwhelm, Pressure, Tension, Location Imperative, Location Pressure, Threat Pressure, and Resolve a Threat is MISSING from the Python-generated values (turn.py:524). Add "Resolve a Threat" with appropriate description matching its semantics in turn.py:509-524.

Additionally, add entries for secondary modifiers that can be appended via semicolon joining at turn.py:551:
- **Combat Fatigue** — combat_age >= 3; append to primary directive when fight has run long without resolution
- Any location-based directives generated by `_compute_pacing_context()` if they differ from the hardcoded ones

The section should note that Python may combine a primary directive with secondary modifiers via semicolon (e.g., "Pressure; Combat Fatigue"), and the narrator should prioritize the primary while treating the secondary as thematic context.

**Why:** When Python generates "Resolve a Threat" or combined directives like "Breathe; Resolve a Threat", the system prompt has no guidance for how to interpret them, causing the LLM to either ignore these signals or apply incorrect behavior (e.g., introducing new threats when it should resolve existing ones). The hardcoded list is the single source of instruction for the narrator — if Python can generate a directive value, the system prompt must document what each means.

**Validation:** Run `ev.py timing` on recent turns to check what directives appear in pacing_context.directive values from events.jsonl. Confirm all observed dynamic values now have corresponding entries in the narration directives section. Specifically verify "Resolve a Threat" appears after a turn where threat_ages triggered imperative-level aging (turn.py:509-524).

### Tests to write or update
None — tests are temporarily removed per AGENTS.md. Manual verification via `ev.py outputs <turn>` on turns with dynamic directive combinations, then diff against updated system prompt template.

### REPOMAP updates required
No changes needed — this is a template-only fix in the prompts directory, no module boundary or API change.

## Implementation — Phase 4: Deduplicate campaign arc context between narrate_system.j2 and _arc.j2

### Context files to load
- `ccya/prompts/narrate_system.j2` lines 61-88 (Campaign Arc section in system prompt)
- `ccya/prompts/sections/_arc.j2` (thread listing + context in user template, included at narrate_user.j2:13)
- `ccya/engine/narrate.py` lines 47-65 (current_arc_ctx construction for understanding what each section receives)

### Detailed steps

#### Step 4.1 — Remove redundant campaign arc context from narrate_system.j2, keep only ARC UPDATE instructions

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the Campaign Arc section at lines 61-88 with a condensed version that contains ONLY:
- The directive about what the narrator should NOT do (never reveal hidden_truths in prose)
- The ARC UPDATE sentinel block format instructions (lines 90-107 stay as-is, they're separate from the context section)

Remove lines 63-85 which duplicate visible_goal, thematic_question, active_threads listing, and pc_drive — these are already provided via `_arc.j2` in the user prompt. The system prompt should instruct on arc update behavior; the user prompt provides the actual current values for the narrator to reference while writing prose.

The condensed section should be approximately:
```jinja2
## Campaign Arc context (see user prompt for current values)
Your visible goal, thematic question, active threads, and pc_drive are in the user prompt below. Use them as narrative context — never state the thematic question directly or reveal hidden_truths in prose.

## ARC UPDATE (optional, after narration)
[... existing lines 90-107 unchanged ...]
```

**Why:** The Campaign Arc section appears in both system and user prompts: narrate_system.j2 has it at lines 61-85 while _arc.j2 is included from the user prompt at narrate_user.j2:13. This means the LLM receives visible_goal, thematic_question, thread listings, and pc_drive twice — once as a "system" instruction and again as dynamic context. For a typical turn with 4+ threads, this wastes ~50-80 tokens in duplication. The system prompt's role is to instruct on arc update behavior; the user prompt provides current values for prose generation. This follows firm decision #1: system = instructions/guidance, user = dynamic data only.

**Validation:** After removing lines 63-85 from narrate_system.j2, run `ev.py timing` and compare tokens_in per turn before/after the change on a save with active arc threads. Expect ~50-100 token reduction in system prompt size (proportional to thread count). Also verify via `ev.py prompt <turn> narrate system` that ARC UPDATE instructions remain intact after the edit, and check rendered user prompt still shows full campaign arc context from _arc.j2.

### Tests to write or update
None — tests are temporarily removed per AGENTS.md. Manual verification: diff of rendered system prompt before/after showing reduced size while retaining all functional content (ARC UPDATE instructions). Confirm user prompt via `ev.py prompt <turn> narrate user` still shows complete campaign arc context from _arc.j2 include.

### REPOMAP updates required
No changes needed — this is a template-only deduplication, no module boundary or API change. The repomap's description of the 5-call pipeline and prompt structure remains accurate; only token counts in practice would improve slightly.
