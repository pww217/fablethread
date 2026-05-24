# Fix stale GMBeat references in rubrics and scenarios

## Status
`completed`

## Phases

3 phases: Update all references to the removed `instruction` field on GMBeat, the removed save/restore behavior for beats, the stale TTL terminology (`expires_at`), and the stale `PacingContext.beat_hint` assertion text in full_cycle.py.

## Issue
Commit `71cffcb` (remove gm_beat instruction field) changed the GMBeat model from having an `instruction` field to only `type`, `surface_as`, and `beat_expires_turn`. It also removed the save/restore of pending_gm_beat around extraction — beats are now permanently cleared after narration. The rubric (`default.md`) and scenario (`full_cycle.py`) still reference these stale concepts, which would mislead judges into checking for nonexistent fields and produce incorrect evaluation scores.

## Solution
Update `evals/rubrics/default.md` Section 4H (GM Beat Lifecycle) to reflect current GMBeat schema and lifecycle behavior: replace all references to `.instruction` with references to the actual fields (`type`, `surface_as`), update the save/restore description in Phase 2, fix the TTL terminology from `expires_at` to `beat_expires_turn`. Update `evals/scenarios/full_cycle.py` line 98 to remove the stale `PacingContext.beat_hint` assertion.

## Firm decisions
- GMBeat model fields are: `type`, `surface_as`, `beat_expires_turn` (no `instruction`).
- Beat lifecycle is now: created → narrated → permanently cleared (not restored for extraction).
- PacingContext no longer has `beat_hint`; it has `directive`, `beat_locked`, `gate`, `summary`.

## Non-goals
- Do not update historical generated run artifacts in `evals/runs/` — those are output from a prior engine state and should be preserved as-is.
- Do not touch prompt templates (system/user prompts) even if they reference old GMBeat fields; that is tracked separately.
- Do not add new tests or assertions for the updated behavior.

## Risks, Ambiguities, and Blockers
- The `extraction.progress` key in rubric prose (lines 316-318 of default.md) refers to the extraction output stream name which is being renamed to `storytell` in a separate plan. This plan should use the current actual key (`progress`) since that's what exists at runtime today — the rename is tracked separately and won't happen until after this fix lands, so using `progress` here is correct for now.
- Line 318 references `extraction.progress.prompt contains ## pending_gm_beat block` — verify the prompt template still injects a `## pending_gm_beat` section even though beats are no longer restored. (It should be unchanged; only the save/restore behavior changed.)

## Implementation — Phase 1: Update GM Beat lifecycle description in default.md rubric

### Context files to load
- `evals/rubrics/default.md` (lines 295-330)
- `ccya/models.py` lines 427-448 (GMBeat model for reference)
- `ccya/engine/turn.py` lines 1120-1121 (beat clearing behavior for reference)

### Detailed steps

#### Step 1.1 — Rewrite Phase 2 description in default.md Section 4H

**File:** `evals/rubrics/default.md`, line 305

**What:** Replace the stale save/restore description:
- Old text (line 305): "After narration, beat is temporarily cleared then restored for extraction."
- New text: "After narration, pending_gm_beat is permanently set to None. It is no longer restored before extraction — Storytell no longer receives beat context."

**Why:** Commit `71cffcb` removed the save/restore of pending_gm_beat around extraction. The rubric must reflect current behavior so judges don't expect beats to be visible in the progress/storyteller prompt.

**Validation:** Read line 305 and confirm it now says "permanently set to None" (or equivalent) with no mention of restoration.

#### Step 1.2 — Fix TTL terminology: `expires_at` → `beat_expires_turn`

**File:** `evals/rubrics/default.md`, line 310

**What:** Replace the stale field name in Phase 3 description:
- Old text (line 310): "If beat's expires_at turn has passed → engine discards it"
- New text: "If beat's beat_expires_turn is at or past the current turn → engine discards it"

**Why:** The GMBeat model field is `beat_expires_turn` (ccya/models.py line 430), not `expires_at`. Using the actual field name prevents confusion when judges cross-reference with source code.

**Validation:** Confirm line 310 references `beat_expires_turn`, not `expires_at`.

#### Step 1.3 — Fix GM Beat lifecycle checklist: replace `.instruction` references

**File:** `evals/rubrics/default.md`, lines 316-317 (checklist table)

**What:** Update the two rows that reference the removed `.instruction` field on GMBeat:
- Row "Beat created" (line 316): Change pass condition from "Beat has type + instruction" to "Beat has a non-null `type` value".
- Row "Beat narrated" (line 317): Change both columns — verify column from "Narration contains content matching beat's instruction" to "Narration reflects the beat's type and surface_as semantics", pass condition from "Beat instruction reflected in prose" to "Prose is consistent with the beat's `type`/`surface_as`".

**Why:** GMBeat no longer has an `.instruction` field. The model now uses `type` (e.g., "complication") and `surface_as` (e.g., "ambient", "event"). Judges should evaluate whether narration is consistent with these fields, not look for a nonexistent instruction string.

**Validation:** Confirm lines 316-317 contain no references to `.instruction`, `beat's instruction`, or similar phrasing. All references use the actual GMBeat field names (`type`, `surface_as`).

## Tests to write or update
None — this is rubric/scenario text only, no code changes. Run a grep to confirm zero remaining stale references:
```bash
grep -n 'expires_at\|beat.*instruction\|\.instruction' evals/rubrics/default.md
```
Should return nothing (or only in historical artifact comments).

## REPOMAP updates required
None — rubric files are not referenced in the repomap.

---

## Implementation — Phase 2: Fix stale beat_hint assertion in full_cycle.py scenario

### Context files to load
- `evals/scenarios/full_cycle.py` (line 98)
- `ccya/engine/turn.py` lines 135-140 (PacingContext model for reference)

### Detailed steps

#### Step 2.1 — Replace stale PacingContext.beat_hint assertion text

**File:** `evals/scenarios/full_cycle.py`, line 98

**What:** Remove the stale expects line that references a nonexistent field:
- Old (line 98): `"PacingContext.beat_hint should suggest 'complication' when beat is pending",`
- New: Replace with an assertion about current behavior, e.g., check for `pending_gm_beat.present` via state_yaml assertions or remove the line entirely if it doesn't map to any current mechanism.

**Why:** `PacingContext.beat_hint` was removed in commit `71cffcb`. PacingContext now has only `directive`, `beat_locked`, `gate`, `summary`. This expects line references a field that no longer exists and will never be satisfied by the current engine state, causing silent test failure or false passes.

**Validation:** Confirm line 98 no longer contains `beat_hint`. Run grep:
```bash
grep -n 'beat_hint' evals/scenarios/full_cycle.py
```
Should return nothing.

## Tests to write or update
None — this is a scenario expects text fix only, no code changes.

## REPOMAP updates required
None.

---

## Implementation — Phase 3: Clean up remaining stale references in default.md Section 4H checklist

### Context files to load
- `evals/rubrics/default.md` (lines 318-320)
- `ccya/engine/turn.py` lines 1350-1360 (narrator_arc_dict filtering for reference — verify allowed keys haven't changed)

### Detailed steps

#### Step 3.1 — Verify checklist rows are consistent with current behavior

**File:** `evals/rubrics/default.md`, lines 318-320

**What:** Review the remaining three checklist rows in the GM Beat lifecycle table:
- Row "Beat visible to progress" (line 318): References `extraction.progress.prompt contains ## pending_gm_beat block`. This is currently accurate — the storyteller prompt template still injects pending_gm_beat context. However, note that since beats are no longer restored after narration, this check will only pass on turns where a new beat was created (not on subsequent turns). Document this nuance if needed in the rubric prose above the table.
- Row "TTL respected" (line 319): References `beat_expires_turn` — already fixed in Phase 1.2, verify it's correct.
- Row "No orphaned beats" (line 320): No field references to update; behavior is unchanged.

**Why:** Ensure the checklist is internally consistent with the updated phases and doesn't contradict itself after Phases 1.1–1.2 changes.

**Validation:** Read lines 318-320 in context of the full Section 4H block (lines 299-327). Confirm no contradictions between Phase descriptions and checklist rows. Run grep for any remaining stale references:
```bash
grep -n 'expires_at\|beat.*instruction' evals/rubrics/default.md
```

## Tests to write or update
None — text review only.

## REPOMAP updates required
None.
