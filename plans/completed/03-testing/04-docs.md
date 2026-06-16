# Post-Convergence Cleanup — Phase 4: Documentation

## Purpose

Update `docs/repomap.md`, `docs/architecture/step0-ruling.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/pacing-systems.md`, AGENTS.md, and the design doc status to reflect all convergence scoring engine changes. All Plan 1-3 phases must be merged before this phase runs.

## Firm decisions

- `docs/repomap.md`: update module descriptions for _pacing.py, turn.py, config.py, models.py. Remove tension_delta, CRISIS, derive_enforce_relief, consecutive_pressure_beats, crisis_urgency_threshold references. Add `compute_convergence_score()`.
- `docs/architecture/step0-ruling.md`: update IntentEnvelope diagram (remove tension_delta), remove Breathe directive, remove enforce_relief, remove consecutive_pressure_beats, add convergence score.
- `docs/architecture/OVERVIEW.md`: update phase engine description (CLIMAX rename, convergence score), remove tension_delta from IO table.
- `docs/architecture/pacing-systems.md`: rewrite to reflect convergence score phase machine, remove derive_enforce_relief, consecutive_pressure_beats, tension_delta.
- AGENTS.md: update signposts if file paths or build commands changed.
- `docs/design/convergence-scoring-design.md`: move from active design to `docs/design/complete/` (or add "implemented" status).

## Status

`completed`

## Dependencies

- Plan 1, 2, and 3 all merged.

## Implementation — Phase 4: Documentation

### Detailed steps

#### Step 4.1 — Update docs/repomap.md

**File:** `docs/repomap.md`

**What:**
- Line 9: Remove `TensionDelta type alias` from `models.py` description.
- Line 12: Replace `crisis_urgency_threshold, crisis_turn_limit` with `climax_turn_limit, convergence_threshold` in `config.py` description.
- Line 13: Replace `_compute_narration_directive() phase-driven priority stack` with simpler description (Breathe removed). Replace `_compute_scene_phase() 5-state phase machine` with convergence-driven description.
- Line 14: Replace `derive_enforce_relief()` with `compute_convergence_score()` in `_pacing.py` description.
- Line 66: Remove `tension_delta` checker entry from table.
- Line 68: Remove `tension_monotonicity` checker entry from table.
- Line 70: Rename `crisis_turn_counting` to `climax_turn_counting`.
- Lines 199, 241-242, 246, 259-261, 263: Update all phase machine descriptions (CRISIS→CLIMAX, remove tension_delta references, remove consecutive_pressure_beats, remove enforce_relief, update transition rules).

**Why:** All doc references must match implemented code.

**Validation:** `grep -n 'CRISIS\|tension_delta\|derive_enforce_relief\|consecutive_pressure' docs/repomap.md` should return 0 matches (after changes).

#### Step 4.2 — Update docs/architecture/step0-ruling.md

**File:** `docs/architecture/step0-ruling.md`

**What:**
- Remove `tension_delta` from the IntentEnvelope diagram (line 31).
- Remove the Breathe gate paragraph (lines 111).
- Remove the `enforce_relief` paragraph (lines 109, 158).
- Remove the `consecutive_pressure_beats` section (lines 151-158).
- Update directive table (line 146): remove Breathe row.
- Update the `_compute_pacing_context()` description to remove `tension_delta` from inputs (line 73). Replace `crisis_turn_count`→`climax_turn_count`.
- Add convergence score note in the phase machine description.

**Why:** Architecture doc must match runtime behavior.

**Validation:** `grep -n 'tension_delta\|Breathe\|enforce_relief\|consecutive_pressure' docs/architecture/step0-ruling.md` should return 0 matches (after changes).

#### Step 4.3 — Update docs/architecture/OVERVIEW.md

**File:** `docs/architecture/OVERVIEW.md`

**What:**
- Remove `tension_delta` from the quick reference table (line 54).
- Remove `tension_delta` from IntentEnvelope description (line 85).
- Update phase engine row (line 54): CRISIS→CLIMAX, replace `tension_delta` with `convergence_score`.
- Update `_compute_pacing_context()` description (line 96): remove tension_delta, update transition conditions.
- Remove `tension_delta` from the flowchart (line 41).

**Why:** Overview doc must reflect current architecture.

**Validation:** `grep -n 'tension_delta\|CRISIS' docs/architecture/OVERVIEW.md` should return 0 matches (after changes, except CLIMAX).

#### Step 4.4 — Update docs/architecture/pacing-systems.md

**File:** `docs/architecture/pacing-systems.md`

**What:**
- Replace all CRISIS→CLIMAX references.
- Remove tension_delta from all diagrams and tables.
- Remove derive_enforce_relief, consecutive_pressure_beats from all diagrams and descriptions.
- Add convergence_score to the signal table.
- Update flowcharts to show compute_convergence_score() in the phase engine path.

**Why:** Pacing systems doc is the most affected by the convergence redesign.

**Validation:** `grep -n 'CRISIS\|tension_delta\|derive_enforce_relief\|consecutive_pressure' docs/architecture/pacing-systems.md` should return 0 matches (after changes).

#### Step 4.5 — Update design doc status

**File:** `docs/design/convergence-scoring-design.md` (or move to `docs/design/complete/`)

**What:** Add a "## Status: Implemented" section at the top, or move the file to `docs/design/complete/`.

**Why:** The design doc served its purpose — plan complete.

**Validation:** File is in `docs/design/complete/` or has `## Status: Implemented` header.

#### Step 4.6 — Update docs/repomap.md section 5-call pipeline

**File:** `docs/repomap.md` around lines 255-265

**What:** Replace the entire "Phase engine changes" subsection to reflect convergence score:
- Remove tension_delta, crisis_turn_count, consecutive_pressure_beats, derive_enforce_relief, enforce_relief.
- Add convergence_score, compute_convergence_score(), climax_turn_count.
- Update transition rules: RISING→CLIMAX (convergence score ≥ threshold), no longer uses tension_delta or crisis_urgency_threshold.
- Update `_compute_narration_directive` signature to remove tension_delta parameter.

**Why:** Repomap must be the authoritative module-boundary reference.

### Tests to write or update

No tests for docs. Verify by running `make check` — should pass.
