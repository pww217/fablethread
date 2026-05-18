# Eval Rubrics, Scenarios, and Constants Update

## Status
`open`

## Phases

3 phases: (1) update all 5 rubric files to remove references to deleted mechanics (`stakes`, `beat_disposition`, `scene_pressure[] urgency escalation`) and correct constants for unified thread lifecycle rules, (2) rewrite engine_mirror.py threshold constants from urgency-escalation-based to scope-aware age rules + active bool demotion, (3) update scenarios that directly reference removed concepts in their expects/asserts.

## Issue (North Star)

After 01-06 implement the unified ArcThread + PacingContext architecture, all eval artifacts become stale: rubrics instruct LLM judges to evaluate mechanics that no longer exist (`stakes` from Rules output, `beat_disposition` from ProgressExtractResult, `scene_pressure[] urgency escalation`, `active_threads/latent_threads split`). Engine constants in engine_mirror.py hardcode urgency-escalation thresholds (PRESSURE_BUILDING_AT/PRESSURE_IMMEDIATE_AT) that are replaced by scope-aware age rules. Scenarios reference removed concepts directly in their expects/asserts (`narration_directive` → PacingContext.directive, `scene_pressure_add/remove/update` → unified thread operations). Running evals against stale rubrics would produce false-positive compliance scores and misleading judge assessments because judges would evaluate the engine against a specification that no longer matches its behavior.

## Solution (North Star)

Systematic update of all 5 rubric files to reflect unified ArcThread + PacingContext architecture: replace scene_pressure urgency escalation tables with scope-aware thread lifecycle rules, remove stakes from rules output evaluation, replace beat_disposition inference checks with gm_beat-presence-based logic, correct mechanic ownership table for 3 unified operations instead of 6+ separate fields. Update engine_mirror.py threshold constants from urgency-escalation (background→building at turn N) to scope-aware age rules (scene-scoped threads expire on location change; arc-scoped threads demote active: True → False based on last_seen_turn). Rewrite pressure_lifecycle scenario to test unified thread lifecycle instead of urgency escalation. Update full_cycle.py expects that reference removed concepts in their asserts.

## Firm decisions
1. All 5 rubrics must be updated — no partial acceptance of stale judge specifications. The meta judge synthesizes from all 4 domain judges; if even one domain judge evaluates against a deleted mechanic, the entire synthesis is corrupted (confirmed: meta.md contradiction checks reference shared concerns across state_correctness and narrative_interplay).
2. engine_mirror.py threshold constants become scope-aware rules instead of urgency escalation — PRESSURE_BUILDING_AT/PRESSURE_IMMEDIATE_AT are replaced by `THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE` (boolean rule) and `THREAD_ARC_DEMOTE_AGE` (turns since last_seen_turn for active: True → False demotion). This reflects the actual Python lifecycle rules that 05 implements.
3. pressure_lifecycle scenario is rewritten, not deleted — it tests a critical mechanic (lifecycle management of short-lived tensions) but against unified thread scope-aware rules instead of urgency escalation on scene_pressure[]. The new scenario seeds an ArcThread(scope=scene), verifies location change causes expiration for that scope, and verifies arc-scoped threads persist across locations.

## Non-goals
- Adding new rubric sections or evaluating new mechanics beyond fixing existing ones to match 01-06 architecture (no new judge criteria)
- Modifying the eval harness runner code itself — only rubrics, scenarios, engine_mirror.py constants, and config are touched (harness logic in ccya/eval/*.py is unchanged because it consumes whatever the rubrics/specs define at runtime)
- Writing comprehensive integration tests for every edge case of unified thread lifecycle — focus on critical path: a turn runs end-to-end with PacingContext inputs and unified ArcThread operations

## Design Decisions Implemented From Plan Document
This phase validates/updates the following decisions from `plans/narration-simplification-design.md` in eval artifacts:
1. Unified ArcThread replaces ScenePressure + arc thread split — verify all 5 rubrics reference unified `arc.threads[] (scope-aware)` instead of separate scene_pressure[] and active_threads/latent_threads lists after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases)
2. PacingContext consolidates all pacing signals — verify rubrics reference `PacingContext.directive` instead of separate narration_directive/deescalate/narrative_velocity after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases)
3. Stakes removed from IntentEnvelope — verify rules output evaluation in rubrics drops stakes field reference after 01+03 implement the removal that eliminates free-text noise for information already encoded in narration prose (confirmed firm decision: band + verb/target provide sufficient failure cost context without free-text stakes string)
4. Beat_disposition removed from ProgressExtractResult — verify beat lifecycle evaluation shifts from LLM-emitted disposition to Python-inferred gm_beat-presence logic after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases)
5. Scope-aware expiration rules replace urgency escalation — verify engine_mirror.py threshold constants reflect unified thread lifecycle rules instead of scene_pressure urgency thresholds after 01 unified model executed on load for backward compatibility during transition period (scene_pressure[] entries become ArcThread(scope=scene), active_threads/latent_threads become unified arc.threads[])

## Risks, Ambiguities, and Blockers
- **Risk:** Rubric files are consumed by LLM judges at runtime — if a judge rubric references a field that no longer exists in the trace (e.g., `stakes` from rules output), the judge will produce confusing or erroneous assessments. Must verify all 5 rubrics after updates parse correctly and reference only fields present in the new unified trace format after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- **Ambiguity:** The `pressure_remove` sanitization field in compaction.md — does this map to a unified thread resolution operation, or should it be renamed/dropped entirely? Default: rename to `thread_resolve_compact` (scope-aware cleanup of expired scene-scoped threads during compaction) after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- **Blocker:** If a scenario file hardcodes urgency escalation thresholds that are now replaced by scope-aware rules, the scenario would fail on a unified engine even if the engine behavior is correct. Must update all 3 scenarios (full_cycle.py, pressure_lifecycle.py, gm_beat_lifecycle.py) to reference PacingContext.directive instead of narration_directive in their expects/asserts after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

## Dependencies
All phases (01 through 05) must complete successfully before this phase can begin. 06's systematic sweep of production code is a prerequisite for 07 because 07 needs the unified engine behavior to be fully implemented and passing `make check && make test` — otherwise there would be no clean trace format for rubrics/judges to evaluate against after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

---

## Implementation Steps

### Step 7.0 — Update state_correctness.md: scene_pressure→unified thread lifecycle, beat_disposition→gm_beat inference

**File:** `evals/rubrics/state_correctness.md`

**What:** Three changes in this rubric:
1. Section 1B (GM Beat Lifecycle Table): Replace "Disposition Emitted" column with "Inferred Disposition" — the judge now evaluates whether Python correctly inferred beat disposition from gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat, not an LLM-emitted field. Flags change: `ORPHANED` (generated, never consumed/expired), `TTL_EXCEEDED`. Remove `CARRY_FAIL`/`REPLACE_FAIL` flags that referenced beat_disposition values the LLM would emit.
2. Section 1C (Scene Pressure Lifecycle Table → Unified Thread Lifecycle Table): Rename section title to "Unified Thread Lifecycle Table". Replace urgency column with scope column (`scene` / `arc`). Add location_change tracking for scene-scoped threads (expire on location change). Flags: `INERT` (no advancement across ≥3 turns), `OVERLONG`, `UNRESOLVED_AT_END`. For scene-scoped threads, add flag `EARLY_EXPIRATION` (expired before narration showed resolution) and `LATE_EXPIRATION` (persisted >3 turns after location change when narration showed resolution). For arc-scoped threads, replace CAP_EXCEEDED threshold from 4→3 active threads.
3. Section 1E (Arc Thread Lifecycle Table): Replace "State" column values from `latent/active/complete/failed/expired` to `active:True/active:False/complete`. Remove the separate table — merge into unified 1C since there's now only one thread list with scope distinguishing scene vs arc.

**Why:** These are the direct rubric updates corresponding to 01 (unified ArcThread model), 04 (beat_disposition removal from ProgressExtractResult), and 05 (scope-aware expiration rules replacing urgency escalation). The judge must evaluate against current engine behavior, not a deleted specification after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Section 1B has "Inferred Disposition" instead of "Disposition Emitted"; Section 1C is a unified thread lifecycle table with scope column and location_change tracking; Section 1E no longer exists (merged into 1C); no remaining references to `beat_disposition`, `latent/active` state values, or urgency escalation in the rubric after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.1 — Update narrative_interplay.md: stakes removed from rules output, pressure→unified thread chains

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Three changes in this rubric:
1. Section 0 (trace description): Remove "stakes" from the list of rules output fields that the judge receives. The trace now contains `band`, `directive` (from PacingContext), `intent`. Stakes was removed because narration already encodes failure cost — if band was FAIL, the narrator wrote the failure after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
2. Section 1A (Rules Directive + Narration → Tone): Replace "Narration Directive" column with "PacingContext.directive". The judge evaluates whether narration tone matches PacingContext.directive values (`Breathe`/`Pressure`/`MoveOn`/`Escalate`/``) instead of the old 9 directive types (Breathe, Pressure, Overwhelm, Tension, Combat Fatigue, Location Imperative, Location Pressure, Threat Pressure, Resolve a Threat). The new PacingContext.directive values are simpler and authoritative after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
3. Section 1A.5 (Narration Directive Analysis → PacingContext.directive Analysis): Rename section title to "PacingContext.directive Analysis". Replace the 9 directive types with 5 values: `Breathe`/`Pressure`/`MoveOn`/`Escalate`/``. Remove the question "Was the directive available to the progress extractor?" — PacingContext is a struct passed directly, not a separate prompt variable after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
4. Section 1B.5 (Beat Generation Quality): Replace "Narration Directive" column with "PacingContext.directive". Update the rule-based mapping: `Breathe`→breathing_room, `Pressure`/`Escalate`→complication, ``→none/no beat expected, `MoveOn`→revelation or none. The directive values are now 5 PacingContext values instead of 9 narration_directive types after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
5. Section 1C (Pressure→Stakes→Consequence Chain → Thread Tension Chain): Rename section title and table headers. Replace "scene_pressure_add" with "thread_add (scope=scene)". Remove the "Stakes Named?" column — stakes was removed from IntentEnvelope in 01 because band + verb/target provide sufficient failure cost context without free-text noise after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). Replace with "Scope" column (`scene`/`arc`). Flags: `INERT_THREAD` instead of `INERT_PRESSURE`.
6. Section 1C.5 (Pressure Removal → Thread Expiration): Rename section title to "Thread Expiration Evaluation". For scene-scoped threads, evaluate location change expiry rules (expire on location change) instead of urgency-based removal timing after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). Flags: `EARLY_EXPIRATION` (scene-scoped thread expired before narration showed resolution), `LATE_EXPIRATION` (persisted >3 turns after location change when narration showed resolution), `FALSE_EXPIRATION` (removed when tension was still active in narration), `MISSING_EXPIRATION` (tension resolved in narration but scene-scoped thread not expired). For arc-scoped threads, add flag `FAILED_DEMOTION` (active:True stayed True for >THREAD_ARC_DEMOTE_AGE turns without last_seen_turn update) after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** These are the direct rubric updates corresponding to 01 (stakes removed from IntentEnvelope), 02 (PacingContext replaces scattered pacing signals), and 05 (scope-aware expiration rules replace urgency escalation for scene-scoped threads after location change, age-based demotion for arc-scoped threads). The judge must evaluate mechanics→narrative chains against unified thread lifecycle rules instead of the old separate pressure/thread systems after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Section 0 trace description has no `stakes` field; Section 1A/1A.5 reference PacingContext.directive with 5 values instead of narration_directive with 9 types; Section 1B.5 rule-based mapping uses 5 PacingContext directive values; Sections 1C/1C.5 evaluate unified thread lifecycle rules (scope-aware expiration for scene-scoped, age-based demotion for arc-scoped) instead of urgency escalation after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.2 — Update prompt_pipeline.md: mechanic ownership for unified operations, inputs for PacingContext

**File:** `evals/rubrics/prompt_pipeline.md`

**What:** Two changes in this rubric:
1. Section 2 (Mechanic Ownership Check): Replace the 6+ field table with a 3-operation unified thread ownership table:

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `thread_advance`, `thread_resolve`, `thread_add` (gated) | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `gm_beat` | progress |
| `actions`, `outcome_summary` | progress |

Remove the old entries for `advanced_threads`, `candidate_opportunity`, `scene_pressure_add/remove/update`, and `beat_disposition`. The 3 unified operations replace 6+ separate fields after 04 implements unified thread operations that eliminate duplicate instruction sets in Progress's system prompt (saving ~300-500 tokens) after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

2. Section 3 (Cross-Pipeline I/O Relevance): For Extract Progress inputs, replace the old list with unified inputs: `narration`, `band`, `PacingContext` (full struct), `arc.threads[] (unified)`, `recent_turns`. Remove references to `stakes`, `deescalate`, `pending_beat`, `narration_directive`, `scene_pressure`, `active_threads`, `latent_threads`. The PacingContext struct replaces 6+ independent fields that the LLM couldn't reconcile after 02 consolidates pacing signals into a single authoritative computation in turn.py after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** The mechanic ownership table is a factual specification that judges use to verify each pipeline emits the correct fields. If it lists deleted fields (`scene_pressure_add`, `beat_disposition`), the judge would flag them as "misplaced mechanics" even though they no longer exist after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). The inputs list must match what PacingContext actually provides to Progress instead of the old scattered signals that were noise for prose generation after 03 removes deescalate/narrative_velocity from Narrate interface after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Section 2 has exactly 9 rows with unified thread operations (`thread_advance`, `thread_resolve`, `thread_add`) instead of 6+ separate fields; no references to `scene_pressure_*` or `beat_disposition`; Section 3 inputs for Extract Progress reference PacingContext struct and unified arc.threads[] instead of scattered signals after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.3 — Update meta.md: inter-judge contradiction checks for unified mechanics

**File:** `evals/rubrics/meta.md`

**What:** Section 2 (Inter-Judge Contradiction Check): Replace the 5 pair-check entries with updated versions that reference unified mechanics instead of deleted ones:
- Remove the entry about "narration_directive being rendered in prompts" — replaced by PacingContext struct passed directly after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- Replace "state_correctness vs narrative_interplay (pressures)" with a unified thread lifecycle check: state_correctness says thread lifecycle is clean but narrative_interplay says threads produce no story consequence — check if scope-aware expiration rules are being evaluated correctly after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- Add a new entry: "state_correctness vs narrative_interplay (PacingContext)" — state_correctness says PacingContext inputs are correct but narrative_interplay says tone doesn't match directive — check if the 5 PacingContext.directive values (Breathe/Pressure/MoveOn/Escalate/"") are being evaluated correctly after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** The meta judge synthesizes from all 4 domain judges. If its contradiction checks reference deleted mechanics (`narration_directive`, `pressures` as a separate concept), the synthesis would be corrupted because it would flag contradictions that don't exist or miss real ones after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Section 2 has 5 entries, all referencing unified mechanics (`PacingContext.directive`, `arc.threads[] scope-aware`); no references to `narration_directive` as a separate prompt variable or `pressures` as a standalone concept after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.4 — Update compaction.md: pressure_remove→thread_resolve_compact sanitization field

**File:** `evals/rubrics/compaction.md`

**What:** Section 2 (Sanitization Fidelity): Replace the table entry for `pressure_remove` with a unified thread sanitization row that covers both scopes:

| Field | Expected | Actual | Score |
|-------|----------|--------|-------|
| `npc_merge` | duplicate NPCs merged per compendium | | `[OK]`/`[FAIL]`/`[NA]` |
| `condition_remove` | resolved/expired conditions removed | | |
| `thread_resolve_compact` | expired scene-scoped threads (location change) + aged arc-scoped threads (active:True→False for >THREAD_ARC_DEMOTE_AGE turns without last_seen_turn update) cleaned | | `[OK]`/`[FAIL]`/`[NA]` |
| `inventory_remove` | depleted items cleaned | | |
| `recent_events_compact` | recent_events entries for compacted turns consolidated | | |

**Why:** The compactor sanitization logic would handle unified thread lifecycle after 05 implements `_manage_thread_lifecycle()` that applies scope-aware rules (scene-scoped threads expire on location change; arc-scoped ones persist across scenes until resolved or aged out via age-based demotion rules). The rubric must reflect the actual sanitization fields present in compaction signals after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Section 2 table has `thread_resolve_compact` instead of `pressure_remove`; description mentions scope-aware rules for scene-scoped location change expiry and arc-scoped age-based demotion after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.5 — Update engine_mirror.py: threshold constants from urgency escalation to scope-aware rules, KNOWN_ASSERT_FIELDS for unified operations

**File:** `ccya/eval/engine_mirror.py`

**What:** Three changes in this file:
1. Replace urgency-escalation threshold constants (lines 18-20) with scope-aware lifecycle rule constants:

```python
# Unified thread lifecycle rules (replaces scene_pressure urgency escalation thresholds after 06 validates no references remain in production code)
THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE: bool = True        # scene-scoped threads expire when location changes
THREAD_ARC_DEMOTE_AGE: int = _defaults.scene_pressure_max_age  # arc-scoped threads demote active:True→False after this many turns without last_seen_turn update (replaces urgency escalation thresholds)

# For trace injection into judge prompts — reflects unified thread lifecycle rules instead of urgency escalation after 06 validates no references remain in production code
URGENCY_LEVELS: tuple[str, ...] = ("background", "normal", "urgent")  # preserved for ArcThread.urgency field (maps from old ThreadState urgency)
```

2. Update `constants_block()` function to inject unified thread lifecycle rules instead of urgency escalation thresholds into judge traces after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

3. Replace line 55 (`KNOWN_ASSERT_FIELDS["extract.progress"]`) from `{"scene_pressure_add", "beat_disposition", "advanced_threads"}` to unified operations: `{"thread_advance", "thread_resolve", "thread_add", "gm_beat"}` after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

4. Replace line 91 (`KNOWN_SEED_PATHS`) from `"scene.scene_pressure"` to unified path: `"arc.threads"` for seeding unified thread entries on test scenarios after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** engine_mirror.py is the read-only mirror that eval scenarios and build_trace import constants from. If it hardcodes urgency-escalation thresholds that are replaced by scope-aware rules, all 3 scenario files would fail on a unified engine even if behavior is correct after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). KNOWN_ASSERT_FIELDS must match the new unified operations that ProgressExtractResult emits instead of deleted fields for schema validation to pass after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Run `python -c "from ccya.eval.engine_mirror import THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE, THREAD_ARC_DEMOTE_AGE; print(THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE); print(THREAD_ARC_DEMOTE_AGE)"` — verify unified lifecycle constants exist and have correct values after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). Also run `python -c "from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS; print(KNOWN_ASSERT_FIELDS['extract.progress'])"` — verify unified operations instead of scene_pressure_add/beat_disposition after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.6 — Rewrite pressure_lifecycle scenario for unified thread lifecycle rules

**File:** `evals/scenarios/pressure_lifecycle.py`

**What:** Complete rewrite of this scenario to test unified ArcThread scope-aware lifecycle instead of scene_pressure urgency escalation:
- New description: "Tests unified ArcThread scope-aware expiration across 8 turns. Seeds a scene-scoped thread at turn 1, verifies location change causes expiration for that scope (turn 4), seeds an arc-scoped thread at turn 5, verifies it persists after location change."
- seed_overrides: Replace `scene.scene_pressure` with unified path `arc.threads`: `[{"id": "debt_collector_approaching", "summary": "...", "scope": "scene", "urgency": "background"}]`. Also add an arc-scoped thread at turn 5 via a second entry in the scenario's expected outputs (not seed override since it would be created by Progress during the run).
- Turn expects/asserts: Replace urgency escalation expectations with scope-aware lifecycle rules. For turns 1-3, verify scene-scoped thread is visible in narration context and not expired yet (location unchanged). For turn 4 (location change), verify scene-scoped thread expires on location change after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). For turns 5-8, verify arc-scoped thread persists across locations and is not expired until aged out via age-based demotion rules after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** This scenario directly tests urgency escalation on scene_pressure[] which would be replaced by scope-aware expiration rules for unified ArcThread. The new scenario preserves the critical mechanic test (lifecycle management of short-lived tensions) but against unified thread rules after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: scenario seeds `arc.threads` with a scene-scoped entry instead of `scene.scene_pressure`; turn 4 expects location change causing thread expiration for scope=scene; turns 5-8 verify arc-scoped threads persist across locations after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.7 — Update full_cycle.py: narration_directive→PacingContext.directive in expects/asserts

**File:** `evals/scenarios/full_cycle.py`

**What:** One change in this scenario:
- Turn 5 (line 97): Replace `"narration_directive should include Pressure or Overwhelm (immediate pressures from confrontation)"` with `"PacingContext.directive should be 'Pressure' or 'Escalate' for the immediate threat"` after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- Turn 5 (line 98): Replace `"beat type should align with directive (complication for Pressure)"` with `"PacingContext.beat_hint should suggest 'complication' when beat is pending"` after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** The scenario expects `narration_directive` to be visible in the progress prompt, but that would become PacingContext.directive passed as a struct after 02 consolidates pacing signals into a single authoritative computation in turn.py. The beat type alignment check references narration_directive values (9 types) instead of PacingContext directive values (5 values) for beat_hint generation after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: Turn 5 expects `PacingContext.directive` instead of `narration_directive`; beat alignment check references PacingContext directive values for beat_hint generation after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.8 — Update gm_beat_lifecycle.py: beat_disposition→gm_beat-presence inference check

**File:** `evals/scenarios/gm_beat_lifecycle.py`

**What:** Check for and update any references to `beat_disposition`, `narration_directive`, or urgency escalation in this scenario's expects/asserts. Replace with unified mechanics: PacingContext.directive values, gm_beat-presence-based beat lifecycle inference after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** If this scenario tests GM beat lifecycle against the old beat_disposition output field from ProgressExtractResult, it would fail on a unified engine where Python infers disposition from gm_beat presence in delta plus turn expiry logic after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Read the file after changes to confirm: No references to `beat_disposition` values (`consume`, `carry`, `replace`) in expects/asserts; beat lifecycle evaluation uses gm_beat-presence inference instead of LLM-emitted disposition after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Step 7.9 — Final validation for 07: run eval with judge-only mode on updated rubrics

**What:** Run `make check && make test` as the final gate for 07 (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases after 06 validates no references remain in production code). Additionally, run a quick eval with judge-only mode on one scenario to verify the updated rubrics parse and produce valid output without errors from referencing deleted fields after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Why:** Rubric files are consumed by LLM judges at runtime — if a judge rubric references a field that no longer exists in the trace, the judge would produce confusing or erroneous assessments after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). The `make check && make test` gate ensures engine_mirror.py constants are importable and scenario files parse correctly after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

**Validation:** Run `python -c "from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS, KNOWN_SEED_PATHS; print('constants ok')"` — verify unified constants are importable after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases). Run `python -c "from ccya.eval.scenarios.full_cycle import scenario; from ccya.eval.scenarios.pressure_lifecycle import scenario as pl; print('scenarios load ok')"` — verify updated scenarios parse without errors after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

---

## Tests to write or update

### Test: `test_engine_mirror_unified_constants`
**File:** `ccya/tests/test_eval_schema.py` (new test function)  
**What:** Import unified lifecycle constants from engine_mirror. Assert that `THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE == True`. Assert that `KNOWN_ASSERT_FIELDS["extract.progress"]` contains exactly the 4 unified operations: `thread_advance`, `thread_resolve`, `thread_add`, `gm_beat`. Assert that `KNOWN_SEED_PATHS` no longer contains `"scene.scene_pressure"` but does contain `"arc.threads"`.

### Test: `test_scenario_full_cycle_no_narration_directive_reference`
**File:** `ccya/tests/test_eval_schema.py` (new test function)  
**What:** Load the full_cycle scenario and scan all turn expects/asserts for string references to removed concepts (`narration_directive`, `scene_pressure_add`). Assert that no expects or asserts contain these strings after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Test: `test_scenario_pressure_lifecycle_uses_unified_threads`
**File:** `ccya/tests/test_eval_schema.py` (new test function)  
**What:** Load the pressure_lifecycle scenario and verify that seed_overrides use `"arc.threads"` path instead of `"scene.scene_pressure"`. Assert that turn 4 expects location change causing scene-scoped thread expiration after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

### Test: `test_rubrics_parse_no_deleted_field_references`
**File:** `ccya/tests/test_eval_schema.py` (new test function)  
**What:** Read all 5 rubric files as text. Assert that none contain the strings `"beat_disposition"` (except in historical context explaining what was removed), `"stakes"` (in rules output evaluation sections), or urgency escalation threshold references (`PRESSURE_BUILDING_AT`, `PRESSURE_IMMEDIATE_AT`) after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

---

## REPOMAP updates required

Update `docs/repomap.md` with the following changes:
- **Eval module section (~line 37+):** Note that engine_mirror.py threshold constants changed from urgency escalation to scope-aware rules after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).
- **Rubric files (~line 45+):** Update descriptions for the 5 rubrics that were modified in 07 to reflect unified thread lifecycle rules instead of urgency escalation after 06 validates no references remain in production code (no orphaned imports of ScenePressure or IntentEnvelope.stakes in modules not directly touched by earlier phases).

(End of file - total 398 lines)