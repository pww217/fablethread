# Fix remaining stale `progress` → `storytell` references in default.md and scenarios

## Status
`completed`

## Phases

3 phases: Rename all remaining references to the old extraction output key `"progress"` (now `"storytell"`) throughout default.md rubric, full_cycle.py scenario expects, and gm_beat_lifecycle.py scenario description. This is a pure text rename across headings, tables, prose descriptions, and scenario metadata.

## Issue
Plan 03 (`39eb561`) renamed `progress` → `storytell` in prompt_pipeline.md but missed the same stale references in default.md (rubric), full_cycle.py (scenario expects), and gm_beat_lifecycle.py (scenario description). These stale names would mislead judges into looking for data under a nonexistent key or report findings using terminology that doesn't match actual event structure.

## Solution
Replace all occurrences of `progress` (when referring to the extraction output stream) with `storytell` throughout default.md, full_cycle.py, and gm_beat_lifecycle.py. Update section headings, mechanic ownership tables, prose descriptions, scenario expects lines, and metadata consistently.

## Firm decisions
- The extraction event dict key is now `"storytell"` (not `"progress"`). This is the actual runtime field name in events.jsonl under `event["extraction"]["storytell"]`.
- In full_cycle.py expects lines like `extract.progress marks ... objectives done`, these should reference the current extraction output: `storytell.quest_updates` or similar.

## Non-goals
- Do not update historical generated run artifacts in `evals/runs/`.
- Do not touch prompt templates (system/user prompts).
- Do not add tests for these changes.

## Risks, Ambiguities, and Blockers
- full_cycle.py expects lines use prose like `"extract.progress marks settle_the_debt objectives done"` — the quest update mechanism is handled by the storyteller extractor's `quest_updates` field in its output dict. Need to verify what key the storyteller uses for quest updates (likely `quest_updates` within the storytelling extraction output).

## Implementation — Phase 1: Update default.md rubric stale references

### Context files to load
- `evals/rubrics/default.md` (lines 218, 400-410, 546)

### Detailed steps

#### Step 1.1 — Rename section heading in Section 3E

**File:** `evals/rubrics/default.md`, line 218

**What:** Update the extraction pipeline prompt audit heading:
- Old (line 218): `### 3E — Extract Progress Pipeline Prompt Audit`
- New: `### 3E — Storyteller Pipeline Prompt Audit`

**Why:** Matches current extraction output key name (`storytell`) and is consistent with how other pipelines are named in the rubric ("Extract Scene", "Extract State"). The storyteller pipeline handles thread lifecycle (advance/resolve/add) and GM beats, not just "progress".

**Validation:** Confirm line 218 reads `### 3E — Storyteller Pipeline Prompt Audit`.

#### Step 1.2 — Rename mechanic ownership table entries in default.md

**File:** `evals/rubrics/default.md`, lines 404-407

**What:** Update the four rows that list mechanics under the old "progress" stream column:
```markdown
| `thread_advance`, `thread_resolve`, `thread_add` (gated) | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `gm_beat` | progress |
| `actions`, `outcome_summary` | progress |
```
Replace all four instances of `progress` in the second column with `storytell`:
```markdown
| `thread_advance`, `thread_resolve`, `thread_add` (gated) | storytell |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | storytell |
| `gm_beat` | storytell |
| `actions`, `outcome_summary` | storytell |
```

**Why:** The extraction output key is now `"storytell"`. Judges use this table to verify mechanics are emitted by the correct stream. Using stale names would cause them to report false positives (flagging correctly-emitted mechanics as misplaced).

**Validation:** Confirm lines 404-407 all show `storytell` in the second column, not `progress`. Run grep:
```bash
grep -n '| progress |' evals/rubrics/default.md
```
Should return nothing.

#### Step 1.3 — Rename prose description heading in default.md Section V6

**File:** `evals/rubrics/default.md`, line 546

**What:** Update the extraction pipeline inputs description:
- Old (line 546): `**Extract Progress (Step 2c):** Inputs are narrative, state.pc, recent_events...`
- New: `**Storyteller (Step 2c):** Inputs are narrative, state.pc, recent_events...`

Also update the prose within that line if it references "progress" as a stream name. The current text says "This is justified because progress is the 'storytelling brain.'" — change to reflect the correct stream name:
- Old (within line 546): `because progress is the "storytelling brain."`
- New (within line 546): `because storyteller is the "storytelling brain."`

**Why:** Consistent naming throughout the rubric. Judges reading Section V6 should see "Storyteller" matching what they see in the event data under `event["extraction"]["storytell"]`. The prose at line 547 already says "the storyteller" — lines contradict this by calling it "Extract Progress".

**Validation:** Confirm line 546 contains no references to stale stream name. Run grep:
```bash
grep -n 'Extract Progress' evals/rubrics/default.md
```
Should return nothing (excluding historical artifact comments).

## Tests to write or update
None — text-only changes. Final verification:
```bash
grep -ni 'extract_progress\|Extract Progress\|| progress |' evals/rubrics/default.md
```
Should return nothing.

## REPOMAP updates required
None — rubric files are not in the repomap.

---

## Implementation — Phase 2: Update full_cycle.py scenario expects references

### Context files to load
- `evals/scenarios/full_cycle.py` (lines 18, 56, 69, 112, 124, 192)
- `ccya/models.py` or relevant extraction code for StorytellerResult quest_updates field

### Detailed steps

#### Step 2.1 — Rename all extract.progress references in full_cycle.py expects lines

**File:** `evals/scenarios/full_cycle.py`, lines 18, 56, 69, 112, 124, 192

**What:** Replace the stale stream name across six expects lines:
- Line 18 (scenario description): Change `"extract.progress marks quest objectives done"` → `"storytell.quest_updates marks quest objectives done"`
- Line 56 (Turn 2 expects): Change `"extract.progress marks settle_the_debt objectives done"` → `"storytell.quest_updates settles the debt objective"`
- Line 69 (Turn 3 expects): Change `"extract.progress marks deliver_the_ledger objectives done (accept contract)"` → `"storytell.quest_updates accepts the courier contract for deliver_the_ledger"`
- Line 112 (Turn 6 expects): Change `"extract.progress marks clear_the_road_toughs done"` → `"storytell.quest_updates clears the road toughs objective"`
- Line 124 (Turn 7 expects): Change `"extract.progress marks deliver_the_ledger objectives done"` → `"storytell.quest_updates completes the deliver_the_ledger objective"`
- Line 192 (Turn 13 expects): Change `"extract.progress quest_updates for deliver_the_ledger"` → `"storytell.quest_updates updates deliver_the_ledger"`

**Why:** The extraction output key is now `"storytell"`. Quest updates are emitted by the storyteller extractor's `quest_updates` field. Using stale names would mislead judges into looking for data under a nonexistent stream name or reporting findings using terminology that doesn't match actual event structure.

**Validation:** Run grep to confirm zero remaining stale references:
```bash
grep -n 'extract\.progress' evals/scenarios/full_cycle.py
```
Should return nothing.

## Tests to write or update
None — text-only changes.

## REPOMAP updates required
None.

---

## Implementation — Phase 3: Update gm_beat_lifecycle.py scenario references

### Context files to load
- `evals/scenarios/gm_beat_lifecycle.py` (full file)

### Detailed steps

#### Step 3.1 — Rename extract.progress references in module docstring and description

**File:** `evals/scenarios/gm_beat_lifecycle.py`, lines 4, 17, 35

**What:** Replace the stale stream name across three locations:
- Line 4 (module docstring): Change `"extract.progress generates a pending_gm_beat"` → `"storytell extracts a pending_gm_beat"`
- Line 17 (scenario description): Change `"Verifies pending_gm_beat is set by extract.progress, surfaced in next narration..."` → `"Verifies pending_gm_beat is set by the storyteller extractor, surfaced in next narration..."`
- Line 35 (Turn expects): Change `"extract.progress should generate a pending_gm_beat here"` → `"storytell should emit a pending_gm_beat here"`

**Why:** GM beats are now emitted by the storyteller extraction stream. Using stale names would mislead judges and scenario authors into looking for data under a nonexistent stream name.

**Validation:** Run grep to confirm zero remaining stale references:
```bash
grep -n 'extract\.progress' evals/scenarios/gm_beat_lifecycle.py
```
Should return nothing.

## Tests to write or update
None — text-only changes. Final verification across all files:
```bash
grep -rn 'extract\.progress\|Extract Progress\b\|| progress |' evals/rubrics/default.md evals/scenarios/full_cycle.py evals/scenarios/gm_beat_lifecycle.py 2>&1 || echo "All clean"
```

## REPOMAP updates required
None.
