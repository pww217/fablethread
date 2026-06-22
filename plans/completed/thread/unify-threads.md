# Unify scene/arc threads into a single thread concept

## Purpose

Remove the `scope` field from threads and all scene/arc distinction logic, reducing LLM cognitive load and simplifying the thread lifecycle.

## Problem Statement

Threads have a `scope` field (`"scene"` or `"arc"`) with different lifecycle rules — scene threads get purged on location change and auto-expire via a two-stage lifecycle; arc threads persist across arcs and get auto-closed on arc resolution. In practice, scene threads regularly span multiple locations, making the distinction artificial. The LLM must track two sets of rules for no actual benefit, and the two-stage expiration silently deletes threads the LLM is still using.

## Constraints

- No backwards compatibility — old saves with `scope` in thread dicts may load but `scope` will be ignored (model has `extra: "ignore"`).
- All existing config.yaml keys remain valid (the removed fields were not present in config.yaml).
- The unified thread uses the same `ArcThread` model minus the `scope` field.
- `scope` in JSON schemas shown to the LLM (prompt templates) is removed so the LLM stops emitting it.

## Non-goals

- Not changing the thread model name (`ArcThread` stays, the "arc" prefix is historical).
- Not changing the pipeline execution order or thread_update/thread_resolve/thread_add mechanisms.
- Not changing thread urgency system, active/latent model, progress tracking, or auto-latent demotion.
- Not changing the narration directive priority stack structure — only shifting from scene-thread-filtered to all-active-threads.

## Solution

Remove the `scope` field from the data model, remove scene-specific lifecycle logic from the pipeline, remove scope-related guidance from prompts, and change all scene-thread-filtered computations to use all active threads instead. All threads are now uniform — they persist across locations and arc boundaries, with only explicit LLM resolve or sanitizer cleanup removing them.

## Firm decisions

1. `scope` field removed from `ArcThread` model entirely — not defaulted, not deprecated, deleted.
2. Scene two-stage lifecycle (active→latent→removed) removed entirely — all threads use only auto-latent demotion + urgency decay.
3. Location-change purge of scene-scoped threads removed — all threads survive location changes.
4. Arc resolution: all threads carry forward (minus drop_threads) — no more auto-closure of any threads on arc resolution.
5. De-escalation check uses ALL urgent threads, not only scene-scoped.
6. Narration directive computation uses ALL active threads, not only scene-scoped.
7. Prompt scope tags (`[SCENE]`/`[ARC]`) removed, prompt guidance simplified to single thread type.

## Risks, Ambiguities, and Blockers

- **[QUESTION: arc resolution behavior]** Current `_apply_arc_resolve()` auto-closes arc-scoped threads as "superseded" and carries scene-scoped forward. With no scope, all threads must behave identically. **Recommendation: all threads carry forward (minus drop_threads), no auto-closure.** This is consistent with the user's observation that scene threads persist longer than expected. The `drop_threads` list gives the LLM an explicit cleanup path. Confirm?
- **[QUESTION: Breathe guard check]** Current Breathe directive checks `if urgent scene-scoped threads exist, block Breathe`. After removing scope, this should check ALL urgent threads. Confirm?
- **[QUESTION: Overwhelm directive prompt text]** `storytell_system.j2` line 57: "Overwhelm — may add scene threads if gate allows". Should become "may add threads if gate allows". Confirm?
- **[QUESTION: thread target guidance]** Current prompt guidance says "2-3 arc threads + 1 scene thread (~4 total)". Without scope, target becomes simply "3-4 threads total, hard cap 5". Confirm?

## Status

`completed`

## Phases

4 phases: models+config → pipeline engine → prompts → documentation

## Implementation — Phase 1: Data model + config

### Context files to load
- `ccya/models.py` (ArcThread, lines 35-62)
- `ccya/prompts/context.py` (ArcThreadSummary, lines 77-86; ArcThreadBlock.from_state(), lines 115-153)
- `ccya/engine/config.py` (EngineConfig, lines 151-179; build_engine_config, lines 269-300)

### Detailed steps

#### Step 1.1 — Remove `scope` from ArcThread model

**File:** `ccya/models.py` line 40

**What:** Delete the `scope: Literal["scene", "arc"]` field from `ArcThread`.

**Why:** The scope distinction is being removed. Existing saved data may still have the field but `model_config = {"extra": "ignore"}` will silently discard it.

**Validation:** `.venv/bin/python -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='test'); print(t)"` — should succeed without `scope` required.

#### Step 1.2 — Remove `scope` from ArcThreadSummary

**File:** `ccya/prompts/context.py` line 82

**What:** Delete the `scope: Literal["scene", "arc"]` field from `ArcThreadSummary`.

**Why:** Mirroring the model change for the prompt rendering variant.

**Validation:** `.venv/bin/python -c "from ccya.prompts.context import ArcThreadSummary; s = ArcThreadSummary(id='t', summary='s', urgency='normal', active=True); print(s)"` — should succeed without `scope`.

#### Step 1.3 — Remove `scope` from ArcThreadBlock.from_state()

**File:** `ccya/prompts/context.py` lines 124-131

**What:** Remove `scope=t.get("scope", "arc")` from the dict branch and `scope=t.scope` from the ArcThread branch.

**Why:** These populate the now-removed field. No replacement needed.

**Validation:** Grep for `scope` in `ccya/prompts/context.py` — only legitimate uses outside `ArcThreadSummary`/`from_state` remain (e.g. `_fmt_progress`).

#### Step 1.4 — Remove `scene_thread_expire_silent_turns` and `track_scene_thread_progress` from EngineConfig

**File:** `ccya/engine/config.py` lines 174, 176

**What:** Delete both field declarations from `EngineConfig`.

**Why:** These control the scene-specific two-stage lifecycle and scene progress tracking, both being removed.

**Validation:** `.venv/bin/python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); print(c.thread_max_active)"` — should not error.

#### Step 1.5 — Remove config mappings in `build_engine_config()`

**File:** `ccya/engine/config.py` lines 291-292

**What:** Delete `scene_thread_expire_silent_turns=int(...)` and `track_scene_thread_progress=bool(...)` lines.

**Why:** These read YAML keys that no longer map to fields.

**Validation:** `.venv/bin/python -c "from ccya.engine.config import build_engine_config; c = build_engine_config({}); print(c.thread_stale_threshold)"` — should succeed.

## Implementation — Phase 2: Pipeline engine

### Context files to load
- `ccya/engine/turn.py` (full thread lifecycle section: lines 115-277; arc resolve: 282-366; de-escalation: 763-771; narration directive: 496-560; pacing context: 563-637; scene thread extraction: 858-881)
- `ccya/state/delta_builder.py` (location change purge: lines 230-235)

### Detailed steps

#### Step 2.1 — Remove scene two-stage lifecycle from `_apply_thread_updates()`

**File:** `ccya/engine/turn.py` lines 238-275

**What:** Delete the entire "Scene-scoped two-stage lifecycle" block (from `# Scene-scoped two-stage lifecycle` through the `scene_threads_to_remove` loop and reversed pop loop).

**Why:** Scene-specific expiration is removed. All threads use only auto-latent demotion + urgency decay.

**Validation:** Grep for `scope` and `scene_thread_expire_silent_turns` in `turn.py` — only references in function signatures/docstrings remain (to be cleaned in subsequent steps).

#### Step 2.2 — Change arc resolution to carry all threads forward

**File:** `ccya/engine/turn.py` lines 315-365

**What:** Replace the arc-scoped/scene-scoped partition with: all threads carry forward minus drop_threads. Remove the auto-close block for arc-scoped threads. The surviving threads = all remaining minus drop_threads. No threads get auto-closed.

Specifically:
- Remove lines 315-317 (partition into arc_scoped/scene_scoped)
- Remove lines 319-325 (auto-close arc-scoped)
- Change line 327-329: instead of scene-only, apply drop_threads filter to ALL threads
- Change line 355: `surviving_scene_threads` → `surviving_threads`
- Update log message at line 348-351

**Why:** With no scope distinction, all threads behave like current scene threads — they survive arc boundaries unless explicitly dropped. The `drop_threads` list is the cleanup mechanism.

**Validation:** Read the updated function — should show no scope-based branching.

#### Step 2.3 — Change de-escalation check to use ALL urgent threads

**File:** `ccya/engine/turn.py` lines 765-770

**What:** Remove the `t.get("scope") == "scene"` filter. Change to check ANY active thread with `urgency == "urgent"` regardless of scope.

Before:
```python
if any(
    t.get("urgency") in ("urgent",)
    for t in ((state.get("arc") or {}).get("threads") or [])
    if isinstance(t, dict) and t.get("scope") == "scene"
):
```

After:
```python
if any(
    isinstance(t, dict) and t.get("urgency") == "urgent"
    for t in ((state.get("arc") or {}).get("threads") or [])
):
```

**Why:** The scope filter was excluding arc-scoped urgent threads from triggering de-escalation. With unified threads, any urgent thread should trigger it.

#### Step 2.4 — Change narration directive to use all active threads

**File:** `ccya/engine/turn.py` lines 496-560

**What:** Rename `scope_scene_threads` parameter to `active_threads` (or keep `scope_scene_threads` for minimal diff and just update the call sites — actually, rename for clarity).

Update docstring to remove "scope=scene" language. The behavior stays the same — urgency-based priority stack — but applies to all active threads instead of only scene-scoped.

**Why:** The directive priority stack already works correctly on any thread list. Removing the filter just broadens the input.

#### Step 2.5 — Change `_compute_pacing_context()` signature

**File:** `ccya/engine/turn.py` lines 563-637

**What:** Rename `scope_scene_threads` parameter to `active_threads` in both signature and body (lines 576, 583, 616).

Update docstring line 576 to remove "scope=scene" language.

#### Step 2.6 — Remove scene-thread extraction block

**File:** `ccya/engine/turn.py` lines 858-881

**What:** Remove the scene-thread filter at line 858 and the `ArcThread.model_validate` loop (lines 858-869). Instead, pass all active threads to `_compute_pacing_context()`.

Build the thread list from ALL `state.arc.threads` entries, not filtered by `scope == "scene"`.

**Why:** With no scope, there's nothing to filter by. All threads participate in pacing computation.

#### Step 2.7 — Remove location-change thread purge

**File:** `ccya/state/delta_builder.py` lines 230-235

**What:** Delete the scene-scoped thread purge block entirely.

**Why:** All threads survive location changes now.

**Validation:** Read the changed function — the location change handler should not touch `arc.threads`.

## Implementation — Phase 3: Prompt templates + context builders

### Context files to load
- `ccya/prompts/sections/_thread_list.j2` (7 lines)
- `ccya/prompts/sections/_arc.j2` (22 lines)
- `ccya/prompts/storytell_system.j2` (93 lines)
- `ccya/prompts/storytell_user.j2` (61 lines)
- `ccya/prompts/narrate_system.j2` (108 lines, specifically lines 85-89)
- `ccya/prompts/narrate_user.j2` (102 lines)
- `ccya/prompts/sanitize_thread.j2` (113 lines)
- `ccya/prompts/generate_seed_system.j2` (166 lines, specifically line 120)
- `ccya/engine/narrate.py` (lines 55-72)
- `ccya/engine/extraction.py` (lines 225-260)
- `ccya/engine/thread_sanitizer.py` (lines 140-142)

### Detailed steps

#### Step 3.1 — Remove scope from `_thread_list.j2`

**File:** `ccya/prompts/sections/_thread_list.j2` lines 1-3

**What:**
- Line 2: Change header from `"target: 2-3 arc, 1-2 scene, ~5 total"` to `"target: 3-4 threads, ~5 total"`
- Line 3: Remove scope tag logic: `{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}` and `{{ scope_tag }}` from the thread line.

**Why:** No more scope tags displayed to the LLM.

#### Step 3.2 — Remove scope from `_arc.j2`

**File:** `ccya/prompts/sections/_arc.j2` line 17

**What:** Remove `[{{ ct.scope }}]` from the completed thread display line.

**Why:** Scope no longer exists on completed threads.

#### Step 3.3 — Remove scope from `storytell_system.j2`

**File:** `ccya/prompts/storytell_system.j2`

**What:**
- Line 11: `"thread_add"` schema — remove `"scope": "scene|arc",`
- Line 12: `"arc_resolve"` → `"new_threads"` schema — remove `"scope": "arc",`
- Line 32: Update target guidance — replace `"2–3 arc threads + 1 scene thread (~4 total)"` with `"3–4 threads (~4 total)"` and remove sentence about arc vs scene scope behavior
- Line 34: Remove entire scope guidance line about scene threads auto-deleting on location change
- Line 57: Overwhelm directive — change "may add scene threads" to "may add threads"

**Why:** Remove all scope-related LLM guidance.

#### Step 3.4 — Remove scope from `storytell_user.j2`

**File:** `ccya/prompts/storytell_user.j2` line 14

**What:** Change `"threads ({{ all_threads|length }} total — unified list; [SCENE] threads are auto-removed on location change)"` to `"threads ({{ all_threads|length }} total)"`.

**Why:** No more scene thread auto-removal.

#### Step 3.5 — Remove scope from `sanitize_thread.j2`

**File:** `ccya/prompts/sanitize_thread.j2`

**What:**
- Line 22: Remove `[{{ ct.scope }}]` from completed threads display
- Lines 58-60: Replace "Thread count — arc vs scene" section with unified guidance: "Target: 3-4 threads. Ensure threads are not redundant or stale."
- Line 103: Remove `"scope": "arc",` from new_threads JSON schema

**Why:** Remove all scope-related sanitizer guidance.

#### Step 3.6 — Remove scope from `generate_seed_system.j2`

**File:** `ccya/prompts/generate_seed_system.j2` line 120

**What:** Delete line 120: `- All new threads use `scope: "arc"`. Do not generate `scope: "scene"` threads at game start.`

**Why:** Scope no longer exists.

#### Step 3.7 — Remove scope from narrator context builder

**File:** `ccya/engine/narrate.py` line 63

**What:** Remove `"scope": t.get("scope", "arc") if isinstance(t, dict) else getattr(t, "scope", "arc"),` from the thread dict builder.

**Why:** The `_thread_list.j2` template no longer reads `scope`.

#### Step 3.8 — Remove scope from thread_sanitizer context builder

**File:** `ccya/engine/thread_sanitizer.py` lines 140-142

**What:** No code change needed — `_build_messages()` passes raw thread dicts which will still have `scope` in old data, but the sanitizer prompt no longer references it. The `scope` field in the dict is just extra data the template ignores.

**Why:** Old saved threads may still have `scope` in their dict representation, but it's harmless extra data. No need to strip it.

#### Step 3.9 — Remove scope references from `step2c-storytell.md` schematic

**File:** `ccya/docs/architecture/step2c-storytell.md`

**What:** Remove `scope` from the `ArcThread` field list in the model documentation section (line 191). Remove the "Two Thread Scopes" subsection (lines 309-316). Remove scene-scoped lifecycle references throughout.

**Why:** Documentation must reflect the simplified model.

**Validation:** Grep for `scope` in docs/architecture/ — remaining references should be in context that makes sense (e.g., explanations of what was removed, not current behavior).

## Implementation — Phase 4: Documentation

### Context files to load
- `docs/repomap.md` (lines 225-242, EngineConfig field naming + computation functions sections)
- `docs/architecture/step2c-storytell.md` (relevant sections identified in Phase 3.9)
- `docs/architecture/step0-ruling.md` (lines 77, 86, 118, 155)
- `AGENTS.md` (check signposts don't reference scope)

### Detailed steps

#### Step 4.1 — Update `docs/repomap.md`

**File:** `docs/repomap.md` line 236

**What:** Remove `scene_thread_expire_silent_turns` and `track_scene_thread_progress` from the EngineConfig field listing. Update the computation functions section (lines 240-241) to remove "scope=scene" language — change to "derives urgency counts from all active threads" and "passes all active threads".

**Validation:** No references to removed config fields or scope-scoped filtering remain.

#### Step 4.2 — Update `docs/architecture/step2c-storytell.md`

**File:** `docs/architecture/step2c-storytell.md`

**What:**
- Line 191: Remove `scope: Literal["scene", "arc"]` from ArcThread model documentation
- Lines 218, 259, 345: Remove scene-scoped two-stage expiration documentation
- Lines 231, 233, 262, 361: Update arc resolution docs — all threads carry forward, no auto-close
- Lines 309-316: Remove "Two Thread Scopes" subsection entirely
- Lines 405-406: Remove config constants table rows for removed fields

#### Step 4.3 — Update `docs/architecture/step0-ruling.md`

**File:** `docs/architecture/step0-ruling.md`

**What:**
- Line 77: Change `"arc.threads[] scope=scene urgency counts"` to `"arc.threads[] urgency counts"`
- Line 86: Update mermaid label similarly (if in diagram)
- Line 118: Change "urgent scene-scoped threads" to "urgent threads"
- Line 155: Change "May add scene-scoped threads if gate allows" to "May add threads if gate allows"

### Tests to write or update

No tests currently exist (refactor phase). Run `make check` (ruff + mypy) as final validation.
