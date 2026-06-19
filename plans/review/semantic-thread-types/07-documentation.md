# Phase 7 — Documentation updates

## Purpose

Update architecture docs, repomap, and AGENTS.md to reflect the new thread type model, dormant field, convergence components, and phase engine changes.

## Problem Statement

The code changes from Phases 1-6 introduce new fields (`type`, `dormant`), remove `active`, modify the convergence score signature, and change the phase engine's SETUP transition. Without doc updates, future developers and LLM implementors will have stale documentation.

## Constraints

- Every code change must be reflected in docs.
- Pipeline flow diagrams must show the new convergence components.
- Module boundaries in repomap must list new field signatures.

## Non-goals

- No code changes — documentation only.
- No new architecture docs — only update existing ones.

## Solution

Review each affected module's documentation and update: model shapes, function signatures, pipeline phase descriptions, and config field listings.

## Firm decisions

1. `ArcThread.active` removed; `ArcThread.dormant` added. All docs referencing `active` on threads must be updated.
2. ArcThread `type` field added to all thread-related docs.
3. Convergence score components updated to `any_urgent_thread` + `active_threat_threads`.
4. `_compute_scene_phase()` SETUP transition includes `turns_in_phase >= 3`.
5. `thread_stale_threshold` removed from config docs.

## Risks, Ambiguities, and Blockers

- **Stale doc references:** Any doc referencing `active` on threads outside the modules listed below will remain stale. Run a repo-wide grep for `\.active` on thread-related docs to catch stragglers.

## Status

`open`

## Implementation — Phase 7: Documentation updates

### Context files to load

- `docs/repomap.md` — Module boundaries, public APIs
- `docs/architecture/OVERVIEW.md` — Pipeline mechanics, data models
- `docs/architecture/` — Any subdocs (step0-ruling.md, step1-narrate.md, etc.) that reference thread models or convergence
- `AGENTS.md` — Build commands, signposts, conventions

### Detailed steps

#### Step 7.1 — Update model shapes in architecture docs

**File:** `docs/architecture/` — search for any document referencing `ArcThread`, `ThreadUpdate`, or `ArcThreadSummary`.

**What:** Update all field listings:
- `active: bool` → `dormant: bool = False`
- Add `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None`
- `ThreadUpdate`: same field replacement
- `ArcThreadSummary`: same field replacement
- Remove `"dormant"` from all urgency Literal values (revert to `["background", "normal", "urgent"]`)

**Why:** Docs must match source. Stale docs are bugs.

**Validation:** `grep -r "active" docs/architecture/` — confirm no remaining references to `active` on thread models.

#### Step 7.2 — Update convergence score in architecture docs

**File:** `docs/architecture/OVERVIEW.md` (or pipeline subdocs)

**What:** Update the convergence score description to list the 5 components with new names:
1. `any_urgent_thread >= 1` — any urgent non-dormant thread
2. `active_threat_threads >= 1` — any threat-type non-dormant thread
3. `scene_age >= threshold`
4. `beat_streak` in 5-turn window
5. `dice_weight` on crit_fail/fail + urgency

**Why:** Convergence score is a key pacing signal. Docs must reflect actual component triggers.

**Validation:** Manual review of doc output.

#### Step 7.3 — Update repomap

**File:** `docs/repomap.md`

**What:** Find the section describing:
- `ccya/models.py` — update ArcThread/ThreadUpdate field signatures
- `ccya/engine/_pacing.py` — update `compute_convergence_score()` signature
- `ccya/engine/turn.py` — update `_apply_thread_updates()`, `_compute_scene_phase()` signatures, add note about auto-dormant and culling
- `ccya/engine/config.py` — remove `thread_stale_threshold` from config listing
- `ccya/prompts/context.py` — update `ArcThreadSummary` and `ArcThreadBlock.from_state()` signatures

**Why:** Repomap is the primary navigation aid for future developers. Stale API listings cause confusion.

**Validation:** `grep -n "active" docs/repomap.md` — confirm no stale references.

#### Step 7.4 — Update AGENTS.md if needed

**File:** `AGENTS.md`

**What:** Check if any build commands, signposts, or conventions reference `active` on threads. Update if found. No changes expected unless the design introduced new make targets or config keys.

**Why:** AGENTS.md is the first file read by new sessions. Stale signposts waste context budget.

**Validation:** `grep -n "active" AGENTS.md` — confirm no stale references.

#### Step 7.5 — Repo-wide cleanup of stale `active` references in docs

**What:** Run `grep -rn "\.active" docs/ --include="*.md"` to catch any remaining references to `active` on thread-like objects. Update any hits that reference the old field on threads (not unrelated `active` uses).

**Why:** Catch stragglers outside the core architecture docs.

**Validation:** `grep -rn "\.active" docs/ --include="*.md"` returns only legitimate non-thread uses or zero results.

### Tests to write or update

No tests — documentation only.
