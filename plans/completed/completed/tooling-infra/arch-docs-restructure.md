# Architecture Docs Restructure

## Purpose

Reorganize `docs/architecture/` so every concept lives in exactly one step doc, reachable by drilling down from `OVERVIEW.md`. No more hunting across 4 concept-level files to understand one system.

## Problem Statement

Four concept-level docs (`pacing-context.md`, `beat-system.md`, `campaign-arcs.md`, `thread-lifecycle.md`) duplicate content from the step docs. Readers must piece together beats across 3 files, threads across 2 files, and pacing across 2 files. Cross-references are stale or missing.

## Constraints

- Concept docs fold INTO step docs (deleted after merge)
- Design docs (`docs/design/`) left untouched
- Deduplication limited to cross-cutting concepts (beats, threads, pacing) — minor boilerplate overlaps stay
- Each step doc describes ONE step's inputs → mechanics → outputs; everything else is a link

## Non-goals

- Rewriting or restructuring doc contents beyond deduplication and merging
- Touching UI docs (`narration-ui.md`, `turn-viewer-ui.md`), eval docs (`eval-harness.md`), or infrastructure docs (`persist.md`, `cross-pipeline.md`, `delta-validate.md`, `out-of-band.md`) — these are already self-contained
- Adding new documentation content

## Solution

Remove 4 concept-level files. Merge their content into the step documents that own those systems. Add cross-reference links from consumers back to the owning step.

## Firm decisions

1. **PacingContext** → fold into `step0-ruling.md`. Pacing is computed from Step 0's outputs (scene_motion, band) + state. Step 0 is where the computation begins.
2. **Beats** → fold into `step2c-progress.md`. Storytell (Step 2c) emits beats and owns the lifecycle (TTL, floor relief). Step 1 (Narrate) gets a one-paragraph consumption note.
3. **Campaign arcs** → fold into `step2c-progress.md`. Thread lifecycle is storytell-managed; step 2c emits all thread mutations.
4. **Thread lifecycle** (mechanics detail doc) → fold into the campaign-arcs subsection of `step2c-progress.md`.
5. `OVERVIEW.md` subsystem table points only to step docs, not deleted concept docs.
6. `step2c-progress.md` will be the largest doc (~250-300 lines). That's fine — it's a single step with multiple owned subsystems.

## Risks, Ambiguities, and Blockers

None. All source content is known; this is pure restructuring.

## Status
`completed`

## Phases

3 phases: Merge 4 concept docs into owning step docs → add consumption note to consumer docs → update OVERVIEW.md and delete concept files.

## Implementation — Phase 1: Merge concept docs into owning step docs

### Context files to load

- `/Users/pwilson/Repos/ccya/docs/architecture/pacing-context.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/beat-system.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/campaign-arcs.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/thread-lifecycle.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/step0-ruling.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/step1-narrate.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/step2c-progress.md`
- `/Users/pwilson/Repos/ccya/docs/architecture/OVERVIEW.md`

All already read this session.

### Detailed steps

#### Step 1.1 — Merge pacing-context.md into step0-ruling.md

**File:** `docs/architecture/step0-ruling.md`

**What:** Append a "## Pacing Context" section at the end. Content from pacing-context.md — struct definition, computation flowchart, priority order, age computation, consecutive pressure counter, wiring diagram. Remove beat-specific details (beat_locked triggers floor relief — that's owned by beats in step2c). Keep the directive priority table.

**Why:** PacingContext is computed from Step 0's outputs (scene_motion, band). Step 0 is the logical home. Step 1 and Step 2c consume PacingContext but don't define it.

**Validation:** `grep -c "PacingContext" step0-ruling.md` should return > 1. No remaining reference to pacing-context.md in the file.

#### Step 1.2 — Merge beat-system.md into step2c-progress.md

**File:** `docs/architecture/step2c-progress.md`

**What:** Replace the current brief GM Beat reference (the single paragraph left after previous editing) with full content from beat-system.md — GMBeat schema, 3-phase lifecycle diagram, floor relief injection, directive-beat alignment, TTL mechanics table. This restores the detail that was briefly replaced with a cross-reference, but now it's the canonical source rather than a duplicate.

**Why:** Beats are emitted by Storytell (Step 2c). The full lifecycle (TTL, floor relief, directive alignment) is post-processing around the Storytell output. The owning step is Step 2c.

**Validation:** The file has a single "## GM Beat" section covering schema, lifecycle, floor relief, TTL. No remaining reference to beat-system.md.

Note: The current `storytell_system.j2:54-65` reference (both in step2c-progress.md and beat-system.md content) is stale — actual directive-beat alignment is at `storytell_system.j2:92-99`. Fix to reference the "## Pacing context" section heading instead of absolute line numbers.

#### Step 1.3 — Merge campaign-arcs.md into step2c-progress.md

**File:** `docs/architecture/step2c-progress.md`

**What:** Append a "## Campaign Arc System" section after the GM Beat section. Content from campaign-arcs.md — data model, engine-driven thread lifecycle flowchart (thread_update → arc_resolve → thread_resolutions), arc context in narration note, integration diagram. Keep it concise; thread-lifecycle mechanics detail folds into a subsection.

**Why:** Thread lifecycle is storytell-managed. Step 2c emits all thread mutations (thread_update, arc_resolve, thread_resolve, thread_add). This is the owning step.

**Validation:** `grep -c "campaign-arcs" step2c-progress.md` returns 0. OVERVIEW.md references are handled in Phase 3.

#### Step 1.4 — Merge thread-lifecycle.md into step2c-progress.md (as campaign-arcs subsection)

**File:** `docs/architecture/step2c-progress.md`

**What:** Within the "Campaign Arc System" section added in 1.3, add a "### Thread Mechanics" subsection. Content from thread-lifecycle.md — step-by-step for `_apply_thread_updates()`, `_apply_arc_resolve()`, thread creation gating (pacing gate, key collision, fuzzy merge), `_apply_thread_resolutions()`, constants reference, validation edge cases. Keep the scope table and gate computation.

**Why:** thread-lifecycle.md explicitly says "This doc complements campaign-arcs.md by detailing the exact rules." Since both fold into step2c-progress, thread-lifecycle becomes an internal subsection of the arc section.

**Validation:** No remaining reference to thread-lifecycle.md in architecture docs.

#### Step 1.5 — Delete the 4 concept-level files

**Files:** 
- `docs/architecture/pacing-context.md`
- `docs/architecture/beat-system.md`
- `docs/architecture/campaign-arcs.md`
- `docs/architecture/thread-lifecycle.md`

**What:** `git rm` all four files.

**Why:** Content exists in owning step docs. Dead files cause confusion.

**Validation:** `ls docs/architecture/ | wc -l` shows 13 (was 17). Confirm: `git status --short` shows 4 deleted files (D for each concept doc).

### Tests to write or update

None — docs only.

## Implementation — Phase 2: Add beat consumption note to step1-narrate.md

### Context files to load

- `docs/architecture/step1-narrate.md` (already read)
- The new `step2c-progress.md` after Phase 1 edits

### Detailed steps

#### Step 2.1 — Replace pending_gm_beat input in flowchart and add consumption note

**File:** `docs/architecture/step1-narrate.md`

**What:** The flowchart already shows `N10["pending_gm_beat"]` as input. Keep that. Add a one-paragraph "### GM Beat consumption" section after "Key forward dependency" that explains: the narrator receives the beat from `state.meta.pending_gm_beat`, uses type + surface_as as creative guidance, and the beat is cleared after narration. Links to `step2c-progress.md#gm-beat` for the full lifecycle.

**Why:** Step 1 is the consumer, not the owner. One paragraph + link. No duplication of the lifecycle.

**Validation:** `grep -c "beat" step1-narrate.md` returns >= 2 (flowchart + new section).

## Implementation — Phase 3: Update OVERVIEW.md cross-references

### Context files to load

- `docs/architecture/OVERVIEW.md` (already read)
- The final state of `step0-ruling.md` and `step2c-progress.md` after Phases 1-2

### Detailed steps

#### Step 3.1 — Remove concept-doc rows from subsystem table

**File:** `docs/architecture/OVERVIEW.md`

**What:** In the "Subsystem Docs" table, remove the rows for:
- PacingContext (content now in step0-ruling)
- Beat System (content now in step2c-progress)
- Campaign Arcs (content now in step2c-progress)

Update the step2c-progress row to: "Pipeline mechanics, GM beat lifecycle, campaign arc system, thread lifecycle mechanics".

Update the step0-ruling row to: "Intent classification, dice resolution flowchart, pacing context computation".

Remove all three duplicate schemas from the "Key Models Glossary":
- PacingContext schema → replace with one-liner: "### PacingContext (see step0-ruling.md#pacing-context)"
- GMBeat schema → replace with one-liner: "### GMBeat (see step2c-progress.md#gm-beat)"
- CampaignArc schema → replace with one-liner: "### CampaignArc (see step2c-progress.md#campaign-arc-system)"

**Why:** OVERVIEW.md cascades to step docs only. Concept-level files no longer exist. Duplicate schemas in the glossary waste context.

**Validation:** `grep -c "pacing-context" OVERVIEW.md` returns 0. `grep -c "beat-system" OVERVIEW.md` returns 0. `grep -c "campaign-arcs" OVERVIEW.md` returns 0. Only step docs appear in subsystem table.
