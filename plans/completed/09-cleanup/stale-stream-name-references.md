# Fix stale `extract_progress` stream name in prompt_pipeline rubric

## Status
`completed`

## Phases

3 phases: Rename all references to the old extraction output key `"progress"` (now `"storytell"`) throughout the prompt_pipeline.md rubric. This is a pure text rename across headings, tables, YAML template, and prose descriptions.

## Issue
The extraction output stream was renamed from `extract.progress` / `progress` to `storytell.extract` / `storytell`. The prompt_pipeline rubric (`evals/rubrics/prompt_pipeline.md`) still uses the old name in 6+ locations: the YAML front-matter template, section headings, mechanic ownership tables, prose descriptions of pipeline inputs/outputs, and the scores summary. This would cause judges to look for data under a nonexistent key or report findings using stale terminology that doesn't match actual event structure.

## Solution
Replace all occurrences of `progress` (when referring to the extraction output stream) with `storytell` throughout `evals/rubrics/prompt_pipeline.md`. Update section headings, YAML template keys, mechanic ownership table entries, and prose descriptions consistently.

## Firm decisions
- The extraction event dict key is now `"storytell"` (not `"progress"`). This is the actual runtime field name in events.jsonl under `event["extraction"]["storytell"]`.
- Stream names used in rubric headings should match the current extraction output keys: `scene`, `state`, `storytell` (alongside `rules` and `narrate`).

## Non-goals
- Do not update historical generated run artifacts in `evals/runs/` — those reflect the engine state at the time of each run.
- Do not touch scenario files or rubrics other than prompt_pipeline.md (e.g., default.md references to "progress" are about GM beats, which is handled in a separate plan).
- Do not update judge.py field masks or extraction filtering logic — those already use `"storytell"` correctly.

## Risks, Ambiguities, and Blockers
- The rubric's line 18 says "Per-turn extractor JSON outputs (rules, scene, state, progress)" — this is prose telling the judge what data it receives. Must be updated to "(rules, scene, state, storytell)".
- Line 93 in the mechanic ownership table lists `gm_beat` under the `progress` column header context. Need to verify whether the column header itself needs updating or just the row entries referencing "progress".

## Implementation — Phase 1: Update YAML front-matter template and section headings

### Context files to load
- `evals/rubrics/prompt_pipeline.md` (full file)

### Detailed steps

#### Step 1.1 — Rename stream key in YAML front-matter template

**File:** `evals/rubrics/prompt_pipeline.md`, line 9

**What:** Replace the stale pipeline score name in the YAML template:
- Old (line 9): `#   extract_progress: int 1-5`
- New: `#   storytell: int 1-5`

**Why:** The judge's `_normalize_scores()` function (judge.py lines 996-997) only accepts keys from the set `("ruling", "narrate", "extract_scene", "extract_state", "storytell")`. If an LLM outputs under `"extract_progress"` it is silently dropped. The rubric template must use the current key name so judges score correctly.

**Validation:** Confirm line 9 reads `#   storytell: int 1-5` and contains no reference to `progress` or `extract_progress`.

#### Step 1.2 — Rename section heading "Extract Progress Pipeline" → "Storyteller Pipeline"

**File:** `evals/rubrics/prompt_pipeline.md`, line 75

**What:** Update the Section 1E heading:
- Old (line 75): `### 1E — Extract Progress Pipeline`
- New: `### 1E — Storyteller Pipeline`

**Why:** Matches current extraction output key name (`storytell`) and is consistent with how other pipelines are named in the rubric ("Extract Scene", "Extract State"). The storyteller pipeline handles thread lifecycle (advance/resolve/add) and GM beats, not just "progress".

**Validation:** Confirm line 75 reads `### 1E — Storyteller Pipeline`.

#### Step 1.3 — Rename scores heading in Section 6

**File:** `evals/rubrics/prompt_pipeline.md`, line 142

**What:** Update the pipeline scores description:
- Old (line 142): "Rules, Narrate, Extract Scene, Extract State, Extract Progress."
- New: "Rules, Narrate, Extract Scene, Extract State, Storyteller."

**Why:** Consistent with current extraction output keys and avoids confusing judges who see `"storytell"` in the event data but read "Extract Progress" in the rubric.

**Validation:** Confirm line 142 contains no reference to `progress` or `extract_progress`.

## Tests to write or update
None — text-only changes. Run grep to verify zero remaining stale references:
```bash
grep -n 'extract_progress\|Extract Progress' evals/rubrics/prompt_pipeline.md
```
Should return nothing (excluding historical artifact comments).

## REPOMAP updates required
None — rubric files are not in the repomap.

---

## Implementation — Phase 2: Update mechanic ownership table and prose descriptions

### Context files to load
- `evals/rubrics/prompt_pipeline.md` (lines 80-115)

### Detailed steps

#### Step 2.1 — Rename "progress" column references in mechanic ownership table

**File:** `evals/rubrics/prompt_pipeline.md`, lines 91-94

**What:** The mechanic ownership table at lines 84-96 has a column header implied by the prose ("Correct stream"). Lines 91-94 list mechanics that belong to the old "progress" stream. Update these rows to reference `storytell` as the correct stream:
- Old (lines 91-94):
```markdown
| `thread_advance`, `thread_resolve`, `thread_add` (gated) | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `gm_beat` | progress |
| `actions`, `outcome_summary` | progress |
```
- New: Replace all four instances of `progress` in the second column with `storytell`:
```markdown
| `thread_advance`, `thread_resolve`, `thread_add` (gated) | storytell |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | storytell |
| `gm_beat` | storytell |
| `actions`, `outcome_summary` | storytell |
```

**Why:** The extraction output key is now `"storytell"`. Judges use this table to verify mechanics are emitted by the correct stream. Using stale names would cause them to report false positives (flagging correctly-emitted mechanics as misplaced).

**Validation:** Confirm lines 91-94 all show `storytell` in the second column, not `progress`. Run grep:
```bash
grep -n '| progress |' evals/rubrics/prompt_pipeline.md
```
Should return nothing.

## Tests to write or update
None — text-only changes.

## REPOMAP updates required
None.

---

## Implementation — Phase 3: Update prose descriptions of pipeline inputs/outputs

### Context files to load
- `evals/rubrics/prompt_pipeline.md` (lines 100-129)
- `ccya/engine/extraction.py` or relevant extraction code for reference on what the storyteller extractor actually receives as input

### Detailed steps

#### Step 3.1 — Rename "Extract Progress" references in Section 3 prose descriptions

**File:** `evals/rubrics/prompt_pipeline.md`, lines 18, 110-114

**What:** Update all prose references to the old stream name:
- Line 18 (intro): Change "(rules, scene, state, progress)" to "(rules, scene, state, storytell)".
- Lines 112-113 ("Extract Progress" heading in Section 3): Rename the bold label from "**Extract Progress**:" to "**Storyteller:**". Update the prose description if it references extraction-specific terminology that should now be storyteller terminology.

Specifically for lines 110-114:
```markdown
**Extract Progress**: richest extractor — assess whether every input enables a specific output. Flag inputs that appear unused. Should receive: narrative, band, PacingContext (full struct), arc.threads[] (unified), recent_turns.

Assess: is pacing_context being used by the storyteller? Flag if it appears in the prompt but the extractor's output shows no evidence of using directive/gate for thread/beat decisions.
```
Change to:
```markdown
**Storyteller**: richest extractor — assess whether every input enables a specific output. Flag inputs that appear unused. Should receive: narrative, band, PacingContext (full struct), arc.threads[] (unified), recent_turns.

Assess: is pacing_context being used by the storyteller? Flag if it appears in the prompt but the extractor's output shows no evidence of using directive/gate for thread/beat decisions.
```

**Why:** Consistent naming throughout the rubric. Judges reading Section 3 should see "Storyteller" matching what they see in the event data under `event["extraction"]["storytell"]`. The prose at line 114 already says "the storyteller" — lines 110-113 contradict this by calling it "Extract Progress".

**Validation:** Run grep to verify zero remaining stale references:
```bash
grep -ni 'progress' evals/rubrics/prompt_pipeline.md | grep -v '# progress\|progression\|progressive'
```
Should return nothing (the only acceptable `progress` matches are in unrelated words like "progression").

## Tests to write or update
None — text-only changes. Final verification:
```bash
grep -ni 'extract_progress\|Extract Progress\|| progress |' evals/rubrics/prompt_pipeline.md
```
Should return nothing.

## REPOMAP updates required
None.
