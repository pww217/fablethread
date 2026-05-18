# Eval Rubrics, Scenarios, and Constants Update

## Status
`open`

## Scope note — what's already done vs. pending
Phase 06b completed step 7.5: `engine_mirror.py` constants are updated (`THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE`, `THREAD_ARC_DEMOTE_AGE`, `URGENCY_LEVELS = ("background", "normal", "urgent")`, `KNOWN_SEED_PATHS` includes `"arc.threads"`, `constants_block()` reflects thread lifecycle). Steps 7.0–7.4 (rubric updates) and steps 7.6–7.8 (scenario rewrites/fixes) are NOT yet done. This plan covers only the pending work.

## Phases

2 phases: (1) update all rubric files to remove references to deleted mechanics (`stakes`, `beat_disposition`, `scene_pressure[] urgency escalation`) and correct constants for unified thread lifecycle rules, (2) rewrite/fix scenarios that directly reference removed concepts in their expects/asserts.

## Issue (North Star)

After 01-06 implement the unified ArcThread + PacingContext architecture, all eval artifacts become stale: rubrics instruct LLM judges to evaluate mechanics that no longer exist (`stakes` from Rules output, `beat_disposition` from ProgressExtractResult, `scene_pressure[] urgency escalation`, `active_threads/latent_threads split`). Scenarios reference removed concepts directly in their expects/asserts (`narration_directive` → PacingContext.directive). Running evals against stale rubrics would produce false-positive compliance scores and misleading judge assessments because judges evaluate the engine against a specification that no longer matches its behavior.

## Solution (North Star)

Systematic update of all rubric files to reflect unified ArcThread + PacingContext architecture: replace scene_pressure urgency escalation tables with scope-aware thread lifecycle rules, remove stakes from rules output evaluation, replace beat_disposition inference checks with gm_beat-presence-based logic, correct mechanic ownership table for 3 unified operations instead of 6+ separate fields. Rewrite pressure_lifecycle scenario to test unified thread lifecycle instead of urgency escalation. Update full_cycle.py and gm_beat_lifecycle.py expects/asserts that reference removed concepts.

## Firm decisions
1. All rubric files must be updated — no partial acceptance of stale judge specifications. The meta judge synthesizes from all domain judges; if even one domain judge evaluates against a deleted mechanic, the entire synthesis is corrupted (confirmed: meta.md contradiction checks reference shared concerns across state_correctness and narrative_interplay).
2. pressure_lifecycle scenario is rewritten, not deleted — it tests a critical mechanic (lifecycle management of short-lived tensions) but against unified thread scope-aware rules instead of urgency escalation on scene_pressure[]. The new scenario seeds an ArcThread(scope=scene), verifies location change causes expiration for that scope, and verifies arc-scoped threads persist across locations.
3. `CompactorSanitizationResult.pressure_remove` field name is NOT changed in this phase — it remains as-is in models.py line 420. The compaction.md rubric row stays as `pressure_remove`. Renaming to `thread_resolve_compact` would require a source code change outside the scope of eval-only updates.

## Non-goals
- Adding new rubric sections or evaluating new mechanics beyond fixing existing ones to match 01-06 architecture (no new judge criteria)
- Modifying the eval harness runner code itself — only rubrics, scenarios are touched (harness logic in ccya/eval/*.py is unchanged because it consumes whatever the rubrics/specs define at runtime)
- Writing comprehensive integration tests for every edge case of unified thread lifecycle

## Design Decisions Implemented From Plan Document
This phase validates/updates the following decisions from `plans/narration-simplification-design.md` in eval artifacts:
1. Unified ArcThread replaces ScenePressure + arc thread split — verify all rubrics reference unified `arc.threads[] (scope-aware)` instead of separate scene_pressure[] and active_threads/latent_threads lists after production code is validated as clean.
2. PacingContext consolidates all pacing signals — verify rubrics reference `PacingContext.directive` with values (`"" | "Breathe" | "Pressure" | "MoveOn" | "Escalate"`) instead of separate narration_directive/deescalate/narrative_velocity.
3. Stakes removed from IntentEnvelope — verify rules output evaluation in rubrics drops stakes field reference after production code is validated as clean (confirmed firm decision: band + verb/target provide sufficient failure cost context without free-text stakes string).
4. Beat_disposition removed from ProgressExtractResult — verify beat lifecycle evaluation shifts to Python-inferred disposition from gm_beat presence in delta plus turn expiry logic on `state.meta.pending_gm_beat` after production code is validated as clean (confirmed: turn.py line 1149 has comment "beat_disposition removed — Python infers from state mutations").
5. Scope-aware expiration rules replace urgency escalation — verify rubric constants reflect unified thread lifecycle rules instead of scene_pressure urgency thresholds.

## Risks, Ambiguities, and Blockers
- **Risk:** Rubric files are consumed by LLM judges at runtime — if a judge rubric references a field that no longer exists in the trace (e.g., `stakes` from rules output), the judge will produce confusing or erroneous assessments. Must verify all rubrics after updates parse correctly and reference only fields present in the new unified trace format.
- **Ambiguity:** The `pressure_remove` sanitization field in compaction.md — should it be renamed to reflect thread lifecycle? Decision: NOT changed in this phase (see firm decision 3 above). Production code still uses `CompactorSanitizationResult.pressure_remove`.

## Dependencies
All phases (01 through 06) must complete successfully before this phase can begin. Phase 06's systematic sweep of production code is a prerequisite because eval artifacts need the unified engine behavior to be fully implemented and passing `make check` — otherwise there would be no clean trace format for rubrics/judges to evaluate against.

---

## What Is Removed (stale references in eval artifacts)

| Stale reference | Lives in | Replaced by |
|-----------------|----------|-------------|
| `stakes` field from Rules output | narrative_interplay.md §0 trace description, §1A table column; default.md §4C Pressure→Stakes→Consequence Chain | Band + verb/target encode failure cost; no separate stakes string in trace |
| `beat_disposition` (consume/carry/replace) | state_correctness.md §1B "Disposition Emitted" column and CARRY_FAIL/REPLACE_FAIL flags; narrative_interplay.md §1A.5, §1B.5; default.md §4H Phase 3 Disposition + disposition-specific checks; gm_beat_lifecycle.py expects/asserts | Python infers beat lifecycle from `gm_beat` presence in delta and expiry logic on `state.meta.pending_gm_beat` (turn.py line ~1149) |
| `narration_directive` as prompt variable | narrative_interplay.md §1A.5 table column "Narration Directive"; full_cycle.py turn 5 expects/asserts; gm_beat_lifecycle.py expects | PacingContext.directive struct passed directly to Narrate and Progress pipelines (models.py line 70: `directive: str = ""`) |
| Scene pressure urgency escalation (`background→building→immediate` thresholds) | state_correctness.md §1C "Scene Pressure Lifecycle Table" with urgency column; narrative_interplay.md §1C/§1C.5 pressure removal timing based on urgency levels; default.md §1C Scene Pressure Table with urgency column and escalation tracking; pressure_lifecycle.py scenario (complete rewrite needed); prompt_pipeline.md §3 Extract Progress inputs listing `scene_pressure` | Scope-aware thread lifecycle: scene-scoped threads expire on location change (`THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE=True`); arc-scoped threads demote active→False after idle turns (`THREAD_ARC_DEMOTE_AGE=8`) — engine_mirror.py constants already updated in phase 06b |
| `active_threads` / `latent_threads` split | state_correctness.md §1E "Arc Thread Lifecycle Table" with State column values `latent/active/complete/failed/expired`; prompt_pipeline.md §3 Extract Progress inputs listing `active_threads`, `latent_threads` | Unified `arc.threads[]` with scope distinguishing scene vs arc; ArcThread lifecycle tracked via urgency + last_seen_turn (models.py line 59-60) |
| PacingContext directive values as "9 types" | narrative_interplay.md §1A.5 ("Evaluate all 9 directive types: Breathe, Pressure, Overwhelm..."); default.md §4B Momentum→Directive→Tone Chain referencing old directives | Actual PacingContext.directive has only 5 values: `"" | "Breathe" | "Pressure" | "MoveOn" | "Escalate"` (models.py line 70) |
| Old mechanic ownership entries (`advanced_threads`, `candidate_opportunity`, `scene_pressure_add/remove/update`, `beat_disposition`) | prompt_pipeline.md §2 Mechanic Ownership Table rows; default.md §7 Mechanic Ownership Table rows | Unified operations: `thread_advance`, `thread_resolve`, `thread_add` (gated) in progress stream |

## What Is Unchanged
- **engine_mirror.py constants** — already updated by phase 06b. No changes needed here (`THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE`, `THREAD_ARC_DEMOTE_AGE`, `URGENCY_LEVELS`, `KNOWN_ASSERT_FIELDS["extract.progress"]` has `"advanced_threads"`, `KNOWN_SEED_PATHS` includes `"arc.threads"`).
- **CompactorSanitizationResult.pressure_remove** — production code field name unchanged (models.py line 420); compaction.md rubric row stays as-is per firm decision 3.
- **Eval harness runner code** (`ccya/eval/judge.py`, `ccya/eval/report.py`, `ccya/eval/universal_asserts.py`) — no changes needed; they consume whatever rubrics/specs define at runtime.

## Context for Implementing LLMs

| File | Why read it |
|------|-------------|
| `ccya/models.py` lines 68-79 (PacingContext) + line 154 (RulesOutcome.directive) | Confirm directive values and PacingContext struct shape before updating rubrics that reference them |
| `ccya/engine/turn.py` lines ~1109-1160 (beat lifecycle after narration) | Understand Python-based beat disposition inference to write correct rubric language replacing beat_disposition |
| `ccya/engine/turn.py` line 473-560 (_compute_narration_directive) | Confirm directive computation derives urgency from ArcThread scope=scene threads, not raw scene_pressure dicts |
| `ccya/eval/engine_mirror.py` (full file) | Verify constants are already correct; don't duplicate work from phase 06b |

---

## Implementation Steps

### Step 7.0 — Update state_correctness.md: thread lifecycle unification, beat disposition inference

**File:** `evals/rubrics/state_correctness.md`

**What:** Three changes in this rubric:
1. Section 1B (GM Beat Lifecycle Table): Replace "Disposition Emitted" column with "Inferred Disposition". The judge evaluates whether Python correctly inferred beat lifecycle from gm_beat presence in delta plus turn expiry logic on `state.meta.pending_gm_beat` — not an LLM-emitted field. Flags change: remove `CARRY_FAIL`/`REPLACE_FAIL` (these referenced beat_disposition values the LLM would emit); keep `ORPHANED` and add `TTL_EXCEEDED`.
2. Section 1C ("Scene Pressure Lifecycle Table"): Rename to "Unified Thread Lifecycle Table". Replace urgency column with scope column (`scene` / `arc`). Add location_change tracking for scene-scoped threads (expire on location change). Flags: `INERT` (no advancement across ≥3 turns), `OVERLONG`, `UNRESOLVED_AT_END`. For scene-scoped threads, add `EARLY_EXPIRATION` and `LATE_EXPIRATION`. Replace CAP_EXCEEDED threshold from 4→3 active threads.
3. Section 1E ("Arc Thread Lifecycle Table"): Merge into unified 1C — there is now only one thread list (`arc.threads[]`) with scope distinguishing scene vs arc. Remove the separate table entirely. Update State column values: replace `latent/active/complete/failed/expired` with lifecycle tracking via urgency + last_seen_turn (ArcThread model).

**Why:** These are the direct rubric updates corresponding to 01 (unified ArcThread model), 04 (beat_disposition removal from ProgressExtractResult), and 05 (scope-aware expiration rules replacing urgency escalation). The judge must evaluate against current engine behavior.

**Validation:** Read the file after changes to confirm: Section 1B has "Inferred Disposition" instead of "Disposition Emitted"; no CARRY_FAIL/REPLACE_FAIL flags; Section 1C is a unified thread lifecycle table with scope column and location_change tracking; Section 1E no longer exists (merged into 1C); no remaining references to `beat_disposition`, `latent/active` state values, or urgency escalation in the rubric.

### Step 7.1 — Update narrative_interplay.md: stakes removed from rules output, thread lifecycle chains

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Six changes in this rubric:
1. Section 0 (trace description): Remove "stakes" from the list of rules output fields that the judge receives. The trace now contains `band`, `directive` (from PacingContext), `intent`. Stakes was removed because narration already encodes failure cost — if band was FAIL, the narrator wrote the failure.
2. Section 1A ("Rules Directive + Narration Directive → Tone"): Replace "Narration Directive" column with "PacingContext.directive". The judge evaluates whether narration tone matches PacingContext.directive values (`"" | "Breathe" | "Pressure" | "MoveOn" | "Escalate"`). Remove the old 9 directive types.
3. Section 1A.5 ("Narration Directive Analysis"): Rename to "PacingContext.directive Analysis". Replace the 9 directive types with actual PacingContext values (5: `""`, `"Breathe"`, `"Pressure"`, `"MoveOn"`, `"Escalate"`). Remove the question "Was the directive available to the progress extractor?" — PacingContext is a struct passed directly, not a separate prompt variable.
4. Section 1B.5 ("Beat Generation Quality with Directive Context"): Replace "Narration Directive" column with "PacingContext.directive". Update rule-based mapping: `""`→none/no beat expected, `"Breathe"`→breathing_room, `"Pressure"/"Escalate"`→complication, `"MoveOn"`→revelation or none.
5. Section 1C ("Pressure→Stakes→Consequence Chain"): Rename to "Thread Tension Chain". Replace `scene_pressure_add` with `thread_add (scope=scene)`. Remove the "Stakes Named?" column — stakes was removed from IntentEnvelope because band + verb/target provide sufficient failure cost context without free-text noise. Replace with "Scope" column (`scene`/`arc`). Flags: `INERT_THREAD` instead of `INERT_PRESSURE`.
6. Section 1C.5 ("Pressure Removal Evaluation"): Rename to "Thread Expiration Evaluation". For scene-scoped threads, evaluate location change expiry rules (expire on location change) instead of urgency-based removal timing. Flags: `EARLY_EXPIRATION`, `LATE_EXPIRATION` (>3 turns after location change when narration showed resolution), `FALSE_EXPIRATION` (removed when tension was still active in narration), `MISSING_EXPIRATION` (tension resolved but thread not expired). For arc-scoped threads, add flag `FAILED_DEMOTION`.

**Why:** These are the direct rubric updates corresponding to 01 (stakes removed from IntentEnvelope), 02 (PacingContext replaces scattered pacing signals), and scope-aware expiration rules replacing urgency escalation. The judge must evaluate mechanics→narrative chains against unified thread lifecycle rules instead of old separate pressure/thread systems.

**Validation:** Read the file after changes to confirm: Section 0 trace description has no `stakes` field; Sections 1A/1A.5 reference PacingContext.directive with actual values (not "9 types"); Section 1B.5 rule-based mapping uses PacingContext directive values for beat_hint generation; Sections 1C/1C.5 evaluate unified thread lifecycle rules instead of urgency escalation.

### Step 7.2 — Update prompt_pipeline.md: mechanic ownership for unified operations, inputs for PacingContext

**File:** `evals/rubrics/prompt_pipeline.md`

**What:** Two changes in this rubric:
1. Section 2 (Mechanic Ownership Check): Replace the current table with updated entries: remove rows for `advanced_threads`, `candidate_opportunity`, `scene_pressure_add/remove/update`, and `beat_disposition`. Add/verify these rows exist:
   - `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` → scene
   - `location_change`, `location_description` → scene
   - `scene_tags`, `scene_tagline` → scene
   - `inventory_add`, `inventory_remove`, `inventory_update` → state
   - `pc_condition_add`, `pc_condition_remove` → state
   - `thread_advance`, `thread_resolve`, `thread_add` (gated) → progress
   - `recent_events_add/update/remove` → progress
   - `gm_beat` → progress
   - `actions`, `outcome_summary` → progress

2. Section 3 ("Cross-Pipeline I/O Relevance"): For Extract Progress inputs, replace the old list with unified inputs: `narration`, `band`, `PacingContext` (full struct), `arc.threads[] (unified)`, `recent_turns`. Remove references to `stakes`, `deescalate`, `pending_beat`, `narration_directive`, `scene_pressure`, `active_threads`, `latent_threads`.

**Why:** The mechanic ownership table is a factual specification that judges use to verify each pipeline emits the correct fields. If it lists deleted fields, the judge would flag them as "misplaced mechanics" even though they no longer exist. The inputs list must match what PacingContext actually provides to Progress instead of old scattered signals.

**Validation:** Read the file after changes to confirm: Section 2 has no `scene_pressure_*` or `beat_disposition` entries; thread operations are listed as unified (`thread_advance`, `thread_resolve`, `thread_add`); Section 3 inputs for Extract Progress reference PacingContext struct and unified arc.threads[].

### Step 7.3 — Update meta.md: inter-judge contradiction checks for unified mechanics

**File:** `evals/rubrics/meta.md`

**What:** Section 2 (Inter-Judge Contradiction Check): Replace stale pair-check entries with updated versions referencing unified mechanics instead of deleted ones:
- Remove the entry about "narration_directive being rendered in prompts" — replaced by PacingContext struct passed directly.
- Replace "state_correctness vs narrative_interplay (pressures)" with a unified thread lifecycle check: state_correctness says thread lifecycle is clean but narrative_interplay says threads produce no story consequence — check if scope-aware expiration rules are being evaluated correctly.
- Add new entry: "state_correctness vs narrative_interplay (PacingContext)" — state_correctness says PacingContext inputs are correct but narrative_interplay says tone doesn't match directive — check if the 5 PacingContext.directive values (`"" | "Breathe" | "Pressure" | "MoveOn" | "Escalate"`) are being evaluated correctly.

**Why:** The meta judge synthesizes from all domain judges. If its contradiction checks reference deleted mechanics, the synthesis would flag contradictions that don't exist or miss real ones.

**Validation:** Read the file after changes to confirm: Section 2 has no references to `narration_directive` as a separate prompt variable; thread lifecycle and PacingContext are referenced in contradiction checks instead of pressures/urgency escalation.

### Step 7.4 — Update default.md (comprehensive judge rubric)

**File:** `evals/rubrics/default.md`

**What:** This is the "default" combined judge rubric that merges all domain evaluations into one pass. It has more stale references than any other file and needs substantial cleanup:
1. Section 1C ("Scene Pressure Table"): Replace urgency-based escalation tracking with scope-aware thread lifecycle rules. Urgency column → scope column (`scene`/`arc`). Flags should reflect location-change expiry for scene-scoped threads instead of urgency escalation thresholds.
2. Section 4B ("Momentum→Directive→Tone Chain"): Update to reference PacingContext.directive values (5 actual values) instead of old directive types.
3. Section 4C ("Pressure→Stakes→Consequence Chain"): Replace `scene_pressure_add` with `thread_add`. Remove stakes column and pressure→stakes chain — band + verb/target encode failure cost now.
4. Section 4H ("GM Beat Lifecycle"): This is the most heavily affected section. Phase 1 creation still uses `gm_beat`, but Phase 3 Disposition must be rewritten: Python infers disposition from gm_beat presence in delta (not LLM-emitted consume/carry/replace). Remove all "Disposition-specific checks" that reference beat_disposition values (`consume`/`carry`/`replace`). Replace with lifecycle-based evaluation: was the beat consumed/expired correctly per pending_gm_beat state transitions?
5. Section 5B ("Sanitization Fidelity"): Keep `pressure_remove` as-is (production code field name unchanged). No change needed here — see firm decision 3 above.
6. Section 7 Mechanic Ownership Table: Same updates as prompt_pipeline.md §2 — remove deprecated entries, add unified thread operations.

**Why:** default.md is a comprehensive judge rubric that covers all mechanic lifecycle tables and interplay assessments in one pass. It has the most stale references because it was designed before any consolidation work. If left unupdated, judges using this rubric would evaluate against deleted mechanics across every section.

**Validation:** Read the file after changes to confirm: Scene Pressure Table uses scope-aware thread rules; GM Beat Lifecycle Phase 3 no longer references beat_disposition values; Pressure→Stakes chain replaced with Thread Tension Chain; mechanic ownership table has unified operations only.

### Step 7.5 — Update full_cycle.py: narration_directive → PacingContext.directive in expects/asserts

**File:** `evals/scenarios/full_cycle.py`

**What:** One change in this scenario:
- Turn 5 (line 97): Replace `"narration_directive should include Pressure or Overwhelm (immediate pressures from confrontation)"` with `"PacingContext.directive should be 'Pressure' or 'Escalate' for the immediate threat"`.
- Turn 5 (line 98): Replace `"beat type should align with directive (complication for Pressure)"` with `"PacingContext.beat_hint should suggest 'complication' when beat is pending"`.

**Why:** The scenario expects `narration_directive` to be visible in the progress prompt, but that becomes PacingContext.directive passed as a struct. Beat type alignment check references old directive values instead of PacingContext directive values for beat_hint generation.

**Validation:** Read the file after changes to confirm: Turn 5 expects `PacingContext.directive` and `PacingContext.beat_hint` instead of `narration_directive`.

### Step 7.6 — Update gm_beat_lifecycle.py: beat_disposition → gm_beat-presence inference check

**File:** `evals/scenarios/gm_beat_lifecycle.py`

**What:** Three changes in this scenario:
1. Turn "gm_beat_trigger" expects (line 37): Remove `"beat_disposition should be present in progress extraction output"` — beat_disposition no longer exists as an LLM-emitted field. Python infers disposition from state mutations.
2. Turn "gm_beat_trigger" asserts: Remove `TurnAssert(stream="extract.progress", field="beat_disposition")` — this will fail because the field doesn't exist in ProgressExtractResult.
3. Turn "gm_beat_surface" expects (line 49): Replace `"pending_gm_beat should be consumed after this turn (beat_disposition defaults to 'consume')"` with `"pending_gm_beat should be None after narration consumes it — Python infers disposition from delta state changes, not LLM emission"`.

**Why:** This scenario tests GM beat lifecycle against the old `beat_disposition` output field. It will fail on a unified engine where Python infers disposition from gm_beat presence in delta plus turn expiry logic (turn.py line ~1149).

**Validation:** Read the file after changes to confirm: No references to `beat_disposition` values (`consume`, `carry`, `replace`) in expects/asserts; beat lifecycle evaluation uses pending_gm_beat state transitions instead of LLM-emitted disposition.

### Step 7.7 — Rewrite pressure_lifecycle scenario for unified thread lifecycle rules

**File:** `evals/scenarios/pressure_lifecycle.py`

**What:** Complete rewrite of this scenario to test unified ArcThread scope-aware lifecycle instead of scene_pressure urgency escalation:
- Remove import of deprecated constants (`PRESSURE_BUILDING_AT`, `PRESSURE_IMMEDIATE_AT`) — these no longer exist in engine_mirror.py. Import only what's needed from the new constants if any.
- New description: "Tests unified ArcThread scope-aware expiration across 8 turns."
- seed_overrides: Replace `"scene.scene_pressure"` with `"arc.threads"` path: `[{"id": "debt_collector_approaching", "summary": "...", "scope": "scene", "urgency": "background"}]`. Also add an arc-scoped thread at turn 5 via expected outputs (not seed override since it would be created by Progress during the run).
- Turn expects/asserts: Replace urgency escalation expectations with scope-aware lifecycle rules. For turns 1-3, verify scene-scoped thread is visible in narration context and not expired yet (location unchanged). For turn 4 (location change), verify scene-scoped thread expires on location change. For turns 5-8, verify arc-scoped thread persists across locations and is not expired until aged out via age-based demotion rules.

**Why:** This scenario directly tests urgency escalation on `scene_pressure[]` which no longer exists as a mechanic. The new scenario preserves the critical mechanic test (lifecycle management of short-lived tensions) but against unified thread scope-aware lifecycle rules.

**Blocker:** Current file imports `PRESSURE_BUILDING_AT, PRESSURE_IMMEDIATE_AT` from engine_mirror — these constants were removed in phase 06b. This import will raise ImportError if scenarios are loaded without rewriting first. Must rewrite before any eval run.

**Validation:** Read the file after changes to confirm: no deprecated constant imports; scenario seeds `arc.threads` with a scene-scoped entry instead of `scene.scene_pressure`; turn 4 expects location change causing thread expiration for scope=scene; turns 5-8 verify arc-scoped threads persist across locations.

### Step 7.8 — Final validation: run make check on updated rubrics and scenarios

**What:** Run `make check` as the final gate. Additionally, attempt to import all scenario modules to confirm no ImportError from deprecated constants:
```bash
python -c "from ccya.eval.scenarios.full_cycle import scenario; print('full_cycle ok')"
python -c "from ccya.eval.scenarios.gm_beat_lifecycle import scenario; print('gm_beat ok')"
# pressure_lifecycle will fail until rewritten in step 7.7 — skip or handle separately
```

**Why:** Rubric files are consumed by LLM judges at runtime — if a judge rubric references a field that no longer exists in the trace, the judge produces confusing or erroneous assessments. Import validation catches deprecated constant imports before they cause failures during eval runs.

---

## REPOMAP updates required

Update `docs/repomap.md` with:
- **Eval module section:** Note engine_mirror.py threshold constants changed from urgency escalation to scope-aware rules (already done in phase 06b — verify repomap reflects this).
- **Rubric files section:** Update descriptions for rubrics modified in this phase to reflect unified thread lifecycle rules instead of urgency escalation.
