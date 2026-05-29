# Eval coverage gaps — universal asserts, rubrics, and scenario for ev1 findings

## Status
`completed`

## Phases
3 phases: universal asserts for cross-turn patterns → judge rubric improvements → new eval scenario exercising ev1-specific mechanics.

## Issue
The ev1 deep audit of Turns 1-10 found 10 behavioral, semantic, and cross-turn pattern issues in the engine. Of these, zero have deterministic coverage and only 3 have partial LLM-judge coverage via existing rubrics. The eval harness tests that the engine doesn't crash and that state mutations are well-formed, but it does not test any of the following: whether beat types match roll-band guidance (`CONSOLIDATED-REPORT.md #1`), whether thread progress actually accumulates (`#2`), whether beat expiry is dead code (`#3`), whether `surface_as` drifts (`#4`), whether conditions exist without modifier entries (`#5`), whether `thread_add` emissions are applied to state (`#6`), whether verb distribution is concentrated (`#7`), whether skills go unrolled (`#8`), whether scene-scoped threads are silently blocked from signals (`#9`), or whether urgency demotion config is wired into production (`#10`).

All 10 findings are verified against `events.jsonl`, `state.yaml`, and source code. They represent real divergences between what the engine *should* do and what it *does* — but the eval harness cannot detect any of them.

## Solution
Add three layers of coverage that close the gap:

1. **Universal asserts** — new deterministic checks in `run_all_universal_asserts()` that catch orphan conditions, thread_add→state application failures, beat-type variety collapse, and surface_as drift. These run on every turn of every scenario for zero marginal cost.
2. **Judge rubric improvements** — extend `narrative_interplay.md` and `state_correctness.md` with rubric sections that ask the LLM judge to examine surface_as consistency, skill coverage, thread progress vs extraction signals, beat expiry dead code, and scene-thread signal blocking.
3. **A dedicated eval scenario** — `eval_coverage_gap.py` that exercises specific band→beat conflicts, thread progress accumulation, orphan conditions, surface_as patterns, and skill variety across turns. Uses existing TurnAssert types and the new universal asserts from Phase 1.

## Firm decisions
1. Universal asserts live in `ccya/eval/universal_asserts.py` — they are deterministic, per-turn (with event_window access), and always run. They follow the existing pattern for red/yellow severity and `scope: universal`.
2. The orphan condition check uses `CONDITION_MODS` from `ccya/rules.py` directly (imported into universal_asserts) rather than maintaining a duplicate list. `CONDITION_MODS` is the single source of truth.
3. The thread_add→state check uses a two-pass window: the turn where `thread_add` appears in extraction output, and the subsequent turn's `state_snapshot` to verify the thread was applied.
4. Judge rubric additions use the same `constants_block()` injection mechanism that already supplies engine constants to judges. No new judge pipeline code needed.
5. The new scenario uses seed_overrides, existing TurnAssert types (`ruling.rolled`, `storytell.extract.thread_advance`, `state_yaml.pending_gm_beat.present/absent`), and universal asserts only. It does not require new TurnAssert types — those can be added as a follow-on phase if the gap analysis shows they'd provide signal that universal asserts and judges miss.
6. `known_fields` validation in `test_eval_schema.py` is updated when the scenario introduces new assertion patterns that reference existing `KNOWN_ASSERT_FIELDS`.

## Non-goals
- Does not redesign the TurnAssert system or the runner's `_check_asserts` handler.
- Does not add new LLM judges or a new rubric file.
- Does not fix the underlying production bugs found by ev1 — only adds detection coverage.
- Does not add cross-turn aggregation to TurnAsserts (they remain per-turn). Cross-turn patterns are caught by universal asserts (event_window) and LLM judges (rubric guidance).

## Risks, Ambiguities, and Blockers
- The surface_as consistency universal assert requires that `surface_as` is present in the event data. It lives in `extraction.storytell.output.gm_beat.surface_as`. If the field is sometimes absent, the assert must handle that gracefully (pass, don't fail). The rubric instruction to the judge is the primary detection mechanism; the universal assert is a secondary signal.
- The thread_add→state check may produce false positives if the thread was added but then immediately resolved/expired in the same turn. The check must allow for the thread to appear in either `arc.threads` or `arc.completed_threads`.
- The judge rubric additions must not duplicate the auto-checker's job. Rubric sections should ask the judge to *assess* patterns (e.g., "is beat variety acceptable?") that universal asserts can only *detect* (e.g., ">60% same beat type").
- LLM judges are expensive. Adding rubric sections increases trace length marginally but does not add extra LLM calls. The limiting factor is token budget, which the existing `JUDGE_EVENT_FIELDS` filtering already controls tightly.

## Implementation — Phase 1: Universal asserts for cross-turn pattern detection

### Context files to load
- `ccya/eval/universal_asserts.py`
- `ccya/rules.py` (for `CONDITION_MODS`)
- `ccya/eval/runner.py` (for `run_all_universal_asserts` call signature and event_window contract)

### Detailed steps

#### Step 1.1 — Add orphan condition check

**File:** `ccya/eval/universal_asserts.py`

**What:** Add function `check_orphan_conditions(event: dict[str, Any]) -> dict[str, Any]`. Import `CONDITION_MODS` from `ccya.rules`. Read `pc.conditions` from `state_snapshot`. For each condition with a non-null `id`, check whether that `id` exists as a key in `CONDITION_MODS`. If a condition is present in state but absent from `CONDITION_MODS`, flag it as a red severity failure with detail listing the condition id and its source turn.

**Why:** Conditions in state with no modifier entry are mechanically inert but create observability debt. The player sees them in the UI, the narrator may reference them, but they never affect dice rolls. The ev1 dataset had `startled` added on T9 with no `CONDITION_MODS` entry — this was invisible to both auto-checkers and judges.

**Validation:** `make test` passes. Run against a synthetic events.jsonl with an orphan condition and confirm the assert fires.

#### Step 1.2 — Add thread_add→state application check

**File:** `ccya/eval/universal_asserts.py`

**What:** Add function `check_thread_add_applied(event: dict[str, Any], prev_event: dict[str, Any] | None, event_window: list[dict[str, Any]] | None = None) -> dict[str, Any]`. For each event in the window where `extraction.storytell.output.thread_add` is non-null (a dict with an `id`), check that the thread's `id` appears in either `state_snapshot.arc.threads` or `state_snapshot.arc.completed_threads` in the *following* event in the window. If the thread `id` is absent from both, flag red. If no thread_add events in window, pass.

Must handle the edge case where the thread was added and immediately resolved in the same turn — in that case the thread would appear in `completed_threads` on the next turn's snapshot. Allow for that.

**Why:** The ev1 finding showed `western_gate_breach_chaos` was emitted as `thread_add` on T1 but never appeared in `arc.threads` in any subsequent state snapshot. No auto-checker caught this because no one verifies that extraction signals produce state mutations.

**Root cause (discovered Ev2):** The `elif _new_thread.key:` branch at `turn.py:1275` has a structural code bug — it checks for key collisions but has no fallthrough to add the thread when no collision is found. Every LLM `thread_add` with a non-null `key` enters this branch and is silently dropped. This assert would have caught the bug on the first game turn after compaction.

**Validation:** `make test` passes. Write a minimal synthetic events.jsonl with a `thread_add` that doesn't appear in subsequent state, confirm the assert fires on yellow severity (failed once = yellow, persistent = red).

#### Step 1.3 — Add beat-type variety warning

**File:** `ccya/eval/universal_asserts.py`

**What:** Add function `check_beat_type_variety(event: dict[str, Any], event_window: list[dict[str, Any]] | None = None) -> dict[str, Any]`. Examine `gm_beat.type` in the `extraction.storytell.output` across the event_window (up to last 10 turns). Count distinct types. If >60% of non-null beats are the same type, flag yellow with detail listing the dominant type and its frequency. If <3 beats in window, pass (insufficient data).

**Why:** The ev1 dataset showed all beats were either `pressure` or `breathing_room` with no variety — monotonous beat generation reduces narrative quality. The existing narrative_interplay rubric already asks about beat variety but relies on the judge noticing. A deterministic warning surfaces this in the auto-checker table.

**Validation:** `make test` passes. Run against the ev1 events.jsonl dataset and confirm the assert fires (all 10 beats are pressure or breathing_room).

#### Step 1.4 — Add surface_as consistency check

**File:** `ccya/eval/universal_asserts.py`

**What:** Add function `check_surface_as_consistency(event: dict[str, Any], event_window: list[dict[str, Any]] | None = None) -> dict[str, Any]`. For consecutive events with the same `gm_beat.type`, check that `surface_as` does not flip between `ambient` and `environmental` without a directive change. Pass if surface_as is the same for the same beat type or if there are <2 same-type beats in the window. Flag yellow on inconsistency.

Must handle: `surface_as` may be absent or null — skip those events rather than failing.

**Why:** The ev1 dataset showed `breathing_room=environmental` on T9 but `breathing_room=ambient` on T10 despite no directive change. This is either prompt drift or LLM inconsistency. Either way, it should be surfaced.

**Validation:** `make test` passes. Run against ev1 events.jsonl and confirm the assert fires on T10 vs T9 breathing_room surface_as mismatch.

#### Step 1.5 — Wire new checks into run_all_universal_asserts

**File:** `ccya/eval/universal_asserts.py`

**What:** Add calls to the four new functions in `run_all_universal_asserts()`, matching the existing call pattern. Pass `prev_event` and `event_window` where the function signature requires them.

**Why:** New asserts are dead code unless wired into the runner's universal assert loop.

**Validation:** `make test` passes. Verify the four new functions appear in the `results` list.

### Tests to write or update

`ccya/eval/universal_asserts.py` — No separate test file. The functions are tested indirectly via `make test` (which runs scenarios through the full pipeline, calling `run_all_universal_asserts` on each turn). For regression coverage, add inline docstrings with example input/output for each new function.

### REPOMAP updates required

`docs/repomap.md` — Add entries for new universal assert functions under `ccya/eval/universal_asserts.py` description (line 41).

---

## Implementation — Phase 2: Judge rubric improvements

### Context files to load
- `evals/rubrics/narrative_interplay.md`
- `evals/rubrics/state_correctness.md`
- `ccya/eval/judge.py` (for `_JUDGE_EVENT_FIELDS` to confirm what data each judge sees)

### Detailed steps

#### Step 2.1 — Add surface_as consistency to narrative_interplay rubric

**File:** `evals/rubrics/narrative_interplay.md`

**What:** In Section 1B (GM Beat→Narrative Effect), add a subsection 1B.3 after the existing beat tables:

```
### 1B.3 — Surface Flag Consistency

For each unique beat type, list which `surface_as` values appeared:

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|

Flag: `SURFACE_DRIFT` (same beat type used different surface_as across turns without a directive change).
```

The judge reads `surface_as` from the gm_beat dict in extraction output. Add a note: "surface_as controls how the beat is presented in narration. 'ambient' → background texture, 'environmental' → scene-level pressure, 'npc' → character-focused. Surface drift means the prompt or LLM is inconsistent about how beats are expressed."

**Why:** The ev1 finding showed breathing_room=environmental (T9) vs breathing_room=ambient (T10) for no apparent reason. The judge currently evaluates beat→prose reflection but not surface flag consistency.

**Validation:** `pip install -e ".[dev]"` passes. No code changes — text-only rubric addition.

#### Step 2.2 — Add verb variety to narrative_interplay Section 3

**File:** `evals/rubrics/narrative_interplay.md`

**What:** In Section 3 (Pacing Assessment), add a bullet after beat type variety:

```
- **Intent verb variety**: count distinct `intent_verb` values across the run. Flag if >70% are the same verb. Flag if a verb that is known from the scenario (e.g., "negotiate", "sneak", "climb") never appears.
```

The judge reads `intent_verb` from the rules output per turn. Known verb hints are listed in the Engine Constants block (`INTENT_VERBS_HINT`).

**Why:** The ev1 dataset used `repair` on 10/10 turns — a verb concentration that suggests the LLM is falling into a default pattern rather than selecting verbs appropriate to each action.

**Validation:** No code changes. Verify rubric renders alongside existing Section 3 text.

#### Step 2.3 — Add skill coverage assessment to narrative_interplay Section 3

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Add another bullet after verb variety:

```
- **Skill coverage**: list which of the 6 skills (`strength, dexterity, wits, lore, charisma, resolve`) appeared in dice rolls. Flag if a skill never appeared across the entire run.
```

The judge reads the skill from `ruling.skill` per turn. Skills are listed in Engine Constants.

**Why:** The ev1 dataset used 5 of 6 skills (never resolve). This may be intentional (resolve checks are specific) or may indicate a bias in how the LLM selects skills for action resolution.

**Validation:** No code changes.

#### Step 2.4 — Add thread progress cross-reference to state_correctness rubric

**File:** `evals/rubrics/state_correctness.md`

**What:** In Section 1C (Unified Thread Lifecycle), modify the thread lifecycle table instructions to add a column and flag:

Replace existing:
```
| ID | Added (Tn) | Scope | Urgency | Location Changed? | Resolved/TTL (Tm) | Lifespan | Flag |
```

With:
```
| ID | Added (Tn) | Scope | Urgency | Advances | Progress | Location Changed? | Resolved/TTL (Tm) | Lifespan | Flag |
```

Add a note: "Read `Advances` from `thread_advance` signal counts in extraction outputs. Read `Progress` from `arc.threads[].progress` field in state_snapshot. If `Advances > Progress` significantly (e.g., 7 advances but progress=0), flag `SIGNAL_APPLICATION_FAILURE`."

Add `SIGNAL_APPLICATION_FAILURE` to the flags list with explanation: "thread_advance signals are firing but progress in state is not incrementing — either the signal ID doesn't match the thread's `id` field, or `_apply_thread_signals` skipped the thread."

**Why:** The ev1 finding showed siege_escalation with 7 thread_advance signals but progress=0. The existing INERT flag only catches threads with no advancement across 3+ turns. The new flag catches the specific case where signals fire but state doesn't respond.

**Validation:** No code changes. Verify rubric renders.

#### Step 2.5 — Add beat expiry path dead code detection to state_correctness rubric

**File:** `evals/rubrics/state_correctness.md`

**What:** In Section 1B (GM Beat Lifecycle), add a note below the existing lifecycle table:

"Also note: if every turn emits a non-null `gm_beat`, the beat expiry path (`turn_no > beat_expires_turn`) is never exercised. This means pendings_gm_beat are perpetually replaced before they can expire, making the expiry mechanism dead code. Flag `NO_EXPIRY_TESTED` if all turns have `gm_beat != null`."

**Why:** The ev1 finding showed that beat expiry is dead code because every turn generates a replacement. This is a structural risk — if extraction ever stops emitting beats, the expiry path is untested and likely broken.

**Validation:** No code changes.

#### Step 2.6 — Add scene-thread signal gate to state_correctness rubric

**File:** `evals/rubrics/state_correctness.md`

**What:** In the Section 1C thread lifecycle table flags, add:

"`SCOPE_GATE_ACTIVE` — scene-scoped threads received no thread_advance signals. Verify from turn data whether scene-scoped threads were blocked from signal application or simply never received signals from the storyteller. If thread_advance signals exist for other threads but not scene-scoped ones, and if scene threads remain at progress=0 for their entire lifespan, this may indicate the code-level scene-thread gate at `_apply_thread_signals` is over-aggressive."

**Why:** The ev1 finding showed the code at turn.py:268-276 explicitly skips scene-scoped threads in `_apply_thread_signals`. This was an intentional design decision, but it means scene threads can never make progress toward in_narrative checks or advancement thresholds. The judge should be able to detect and evaluate this.

**Validation:** No code changes.

### Tests to write or update

None. Rubrics are text-only and validated by review, not automated tests.

### REPOMAP updates required

None. Rubrics are not documented in the repomap.

---

## Implementation — Phase 3: New eval scenario for coverage gaps

### Context files to load
- `evals/scenarios/full_cycle.py` (existing scenario as reference pattern)
- `evals/scenarios/pressure_lifecycle.py` (existing scenario as reference pattern)
- `ccya/eval/scenario.py` (Scenario, Turn, TurnAssert models)
- `ccya/eval/engine_mirror.py` (constants for scenario definition)
- `ccya/rules.py` (CONDITION_MODS for orphan condition setup)
- `state.yaml` seed state (in `evals/packs/eval-pack/seed_state.yaml`)
- `ccya/eval/universal_asserts.py` (to confirm new checks from Phase 1 cover this scenario)

### Detailed steps

#### Step 3.1 — Create scenario skeleton

**File:** `evals/scenarios/eval_coverage_gap.py`

**What:** Create a new scenario file `eval_coverage_gap.py` with 8-10 turns designed to exercise specific ev1 findings. The scenario should place the PC in situations that test:

1. **Band-beat conflict**: Mix of roll bands (fail, partial, success, crit_success) where the expected beat type per prompt guidance differs from the narration directive. Specifically:
   - T2: fail or setback band → should NOT get a pressure/complication beat per "Do NOT emit escalation/pressure on failed checks" guidance
   - T4: success or crit_success → should get escalation/pressure (momentum gain creates opportunity)
   - T6: partial band → should get complication (narrate a cost, not breathing_room)

2. **Thread progress accumulation**: Seed a thread `siege_preparations` with progress-eligible design. Have multiple turns with `thread_advance=['siege_preparations']`. Check that progress actually increments.

3. **Orphan condition**: Have the storyteller extractor produce a condition `hesitant` in `pc_condition_add` that does NOT have a corresponding entry in `CONDITION_MODS`. Verify the universal assert from Phase 1 catches it.

4. **surface_as patterns**: Alternate between `breathing_room/environmental` and `breathing_room/ambient` beats without a directive change. Verify the universal assert from Phase 1 or the judge rubric from Phase 2 flags the drift.

5. **Skill variety**: Ensure turns exercise different skills (strength, dexterity, wits, lore, charisma, resolve) so the judge can confirm coverage.

The seed state should start with momentum=0, a neutral scene with 1-2 NPCs, and a seeded thread. No player action in the scenario should violate engine expectations or require special edge-case handling.

**Why:** A dedicated scenario is the only way to guarantee these patterns are exercised regularly. The existing scenarios (full_cycle, pressure_lifecycle, momentum_high/low) each test specific mechanics but none exercises the band-beat conflict or thread progress failure modes discovered in ev1.

**Validation:** `make test` passes (the test_integration auto-discovers new scenario files via `_discover_scenario_files()`).

#### Step 3.2 — Define seed_overrides and turns

**File:** `evals/scenarios/eval_coverage_gap.py`

**What:** Implement the scenario with:

```python
scenario = Scenario(
    id="eval_coverage_gap",
    pack="eval-pack",
    description="8-turn scenario exercising ev1 findings: band-beat conflict, thread progress, orphan conditions, surface_as patterns, and skill variety.",
    seed_overrides={
        "arc.threads": [
            {
                "id": "siege_preparations",
                "summary": "The village is stockpiling weapons and fortifying the eastern wall against an expected attack.",
                "scope": "arc",
                "urgency": "normal",
                "progress": 0,
                "in_narrative": True,
            }
        ]
    },
    turns=[...],
)
```

Each turn follows the same pattern as existing scenarios: `Turn(input=..., phase=..., expects=[...], asserts=[...])`. Use `TurnAssert` for what can be checked per-turn:
- `TurnAssert(stream="ruling", field="rolled", expected="true")` on roll turns
- `TurnAssert(stream="storytell.extract", field="thread_advance", expected="siege_preparations")` on advance turns

The `expects` list documents what the turn should produce for human reviewers.

Turns should cover at minimum:
- T1: No-roll dialogue establishing scene
- T2: Fail/setback roll → pressure beat is ✗ expectation
- T3: No-roll with thread_advance → progress should increment
- T4: Success/crit_success roll → escalation beat is ✓ expectation
- T5: Partial roll with condition_add that creates an orphan condition
- T6: Breathe directive (low momentum) → breathing_room with surface_as=environmental
- T7: Breathe directive → breathing_room with surface_as=ambient (surface drift trigger)
- T8: Another roll using a different skill than previous turns

**Why:** The turn sequence is designed to exercise each ev1 finding at least once. T2 tests finding #1 (band-beat misalignment). T3 tests finding #2 (thread progress). T5 tests finding #5 (orphan condition). T6-T7 test finding #4 (surface_as inconsistency). T8 ensures skill variety (finding #8).

**Validation:** `make test` passes. All universal asserts from Phase 1 fire when expected.

#### Step 3.3 — Update KNOWN_ASSERT_FIELDS if needed

**File:** `ccya/eval/engine_mirror.py`

**What:** If the scenario uses any TurnAssert patterns that reference fields already in KNOWN_ASSERT_FIELDS (e.g., `ruling.rolled`, `storytell.extract.thread_advance`), no changes needed. If it introduces a new field pattern, add it to the appropriate stream's set. Check that `test_eval_schema.py` passes — it validates `KNOWN_ASSERT_FIELDS` against the runner's `_check_asserts` handler.

**Why:** The schema validation test ensures scenarios reference real assertable fields.

**Validation:** `make test` passes.

### Tests to write or update

`tests/test_integration.py` — No changes needed. The existing `TestScenarioIntegration` class auto-discovers new scenario files via the parametrized `loaded_scenario` fixture (conftest.py lines 256-261). The new scenario will be picked up automatically when `make test` runs.

`evals/scenarios/eval_coverage_gap.py` — This is the new test fixture itself. Its asserts run through the engine pipeline with FakeLLM.

### REPOMAP updates required

`docs/repomap.md` — Add entry for `evals/scenarios/eval_coverage_gap.py` under the eval harness description (around line 39), noting it-specific coverage for ev1 findings (band-beat conflict, thread progress, orphan conditions, surface_as drift).

---

## Deferred / Future Coverage Gaps

### Recent events removal decision
**Status:** Resolved — handled by `world-state-history-redesign` Phase A. Recent events system is removed entirely from models, state, prompts, and UI. No eval coverage needed for recent_events checks; the corresponding assert patterns have been removed from this plan.

### Template rendering gap asserts
**Status:** Future — two new template rendering gaps identified by playthrough:
- **Narrator blind to recent_events**: **Resolved** by `world-state-history-redesign` Phase A (recent_events removed).
- **Storytell blind to world_state**: **Resolved** by `world-state-history-redesign` Phase B (world_state always shown, conditional gate removed at `storytell_user.j2:26`).

Narrator continuity is maintained by Phase C (completed_threads rendered in `narrate_user.j2`). No additional eval coverage needed.
