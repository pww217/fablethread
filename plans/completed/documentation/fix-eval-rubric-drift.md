# Plan: Fix Eval Rubric & Documentation Drift

## Status
`open`

## Phases

3 phases: (1) fix rubrics referencing removed concepts (`thread_signals`, `player_drift_signals`, `arc_engagement`, `quest_updates`) and stale constants, (2) fix ARCHITECTURE.md StateDelta diagram showing removed fields, (3) fix repomap.md pressure escalation thresholds.

## Issue

The evaluation rubrics and documentation reference engine concepts that have been removed or changed in recent commits:
- **Thread system simplification** (commit 40efb51): Replaced `thread_signals` + `player_drift_signals` with single `advanced_threads`; removed `arc_engagement` field; reduced active cap from 4 to 3. Rubrics still reference all removed concepts.
- **Arc phase removal** (commit 564fbbf): Removed arc `phase` entirely from engine and prompts, but StateDelta diagram in ARCHITECTURE.md still shows `quest_updates`.
- **Pressure escalation config change** (commit 096909e): Changed defaults from 6/10 to 3/5 turns. Repomap still says "background→building at 6 turns, building→immediate at 10".

These drifts cause the eval harness to evaluate against stale specifications, producing false-positive rubric compliance scores and misleading judge assessments.

## Solution

Three focused phases: (1) update all four rubrics (`state_correctness.md`, `narrative_interplay.md`, `prompt_pipeline.md`, `meta.md`) to remove references to deleted concepts and correct constants, (2) fix ARCHITECTURE.md StateDelta diagram showing removed `quest_updates` and missing `arc_update`, (3) fix repomap.md pressure escalation thresholds from hardcoded fallbacks to actual EngineConfig values.

## Firm decisions

1. All rubric text referencing `thread_signals`, `player_drift_signals`, or `arc_engagement` must be updated to reference `advanced_threads`.
2. The Arc Engagement Table (Section 1F in state_correctness.md) is entirely removed — it evaluates a field (`arc_engagement`) that no longer exists and had "zero downstream mechanical effect" per commit message.
3. StateDelta diagram in ARCHITECTURE.md must show `arc_update` instead of `quest_updates`.
4. Repomap pressure thresholds must reflect EngineConfig defaults (3/5), not hardcoded fallbacks in pressure.py.

## Non-goals

- Do not modify rubric scoring logic or judge behavior — only text/specification drift fixes.
- Do not add new rubric sections or evaluate new mechanics beyond fixing existing ones.
- Do not modify scenario files (`evals/scenarios/`) — they are already correct per recent plan completions.
- Do not modify the default.md monolithic rubric (legacy, not used in multi-judge config).

## Risks, Ambiguities, and Blockers

**Risk:** The `prompt_pipeline.md` Section 3 text about "vestigial quest-related inputs" is self-referential — it tells judges to flag vestigial fields that may or may not still exist. After the thread simplification commit, `quest_ages` and `quest_threshold_directive` were removed from prompts entirely (commit 4d90515). The text should be updated to reflect they're already gone rather than asking judges to check for them.

**Ambiguity:** Section 1E in state_correctness.md references `CAP_EXCEEDED (more than 4 active threads)`. After the cap change from 4→3, this flag description should say "more than 3" but also clarify that it's checking against `_ACTIVE_THREAD_CAP = 3`.

**Blocker:** None identified. All changes are text-only in rubric markdown files and documentation.

## Implementation — Phase 1: Fix rubrics referencing removed concepts

### Context files to load
- `/Users/pwilson/Repos/ccya/evals/rubrics/state_correctness.md` (Sections 1E, 1F)
- `/Users/pwilson/Repos/ccya/evals/rubrics/prompt_pipeline.md` (Lines 91, 113)
- `/Users/pwilson/Repos/ccya/evals/rubrics/meta.md` (Line 51)
- `/Users/pwilson/Repos/ccya/docs/ARCHITECTURE.md` ("Campaign Arc System" section for reference on current thread model)

### Detailed steps

#### Step 1.1 — Fix state_correctness.md: Update arc thread cap and remove engagement table

**File:** `evals/rubrics/state_correctness.md`

**What:** Two changes in Section 1 (Mechanic Lifecycle Tables):
1. Line 79: Change `CAP_EXCEEDED (more than 4 active threads)` to `CAP_EXCEEDED (more than 3 active threads)`. The cap was reduced from 4 to 3 in commit 40efb51.
2. Lines 81-88: **Remove entire Section 1F — Arc Engagement Table**. This section evaluates `arc_engagement` and `player_drift_signals`, both of which were deleted in commit 40efb51 (the engagement field had "zero downstream mechanical effect").

**Why:** The rubric must reflect current engine state. Evaluating a non-existent field wastes judge tokens and produces meaningless scores. The active cap change from 4→3 is a factual correction that affects threshold checking.

**Code Snippet — Change to apply (line 79):**
```markdown
Flags: `STALLED` (progress stuck at 0 for ≥5 turns), `DUPLICATE_ID`, `ORPHANED` (active thread with no advanced_threads across ≥3 turns), `CAP_EXCEEDED` (more than 3 active threads), `FAILED_NO_SIGNAL` (thread failed without FAILED signal).
```

**Code Snippet — Remove entirely (lines 81-88):**
Delete these lines:
```markdown
### 1F — Arc Engagement Table

| Turn | arc_engagement | Drift Match? | Δ Engagement | Flag |
|------|----------------|--------------|--------------|------|

Drift match: player_drift_signals substring matched against active_thread tags.
Flags: `DRIFT_IGNORED` (engagement decreased but player action matched active thread tags), `STAGNANT` (engagement stuck at 0 for ≥4 turns), `MAX_REACHED` (engagement at +3 but no new threads activated).
```

**Validation:** Read the file after changes to confirm Section 1E flows directly into Section 2 without orphan text. Verify no remaining references to `arc_engagement`, `player_drift_signals`, or engagement-related flags in any rubric.

#### Step 1.2 — Fix state_correctness.md: Update ORPHANED flag description

**File:** `evals/rubrics/state_correctness.md`

**What:** Line 79: Change "active thread with no `thread_signals` across ≥3 turns" to "active thread with no `advanced_threads` across ≥3 turns".

**Why:** The progress extractor now emits only `advanced_threads`, not the old multi-signal system. Judges need correct terminology when analyzing traces.

#### Step 1.3 — Fix prompt_pipeline.md: Update mechanic ownership and extract progress assessment

**File:** `evals/rubrics/prompt_pipeline.md`

**What:** Two changes:
1. Line 91 (Mechanic Ownership Check table): Replace `thread_signals`, `player_drift_signals` with just `advanced_threads`. The row should read:
   ```markdown
   | `advanced_threads`, `candidate_opportunity` | progress |
   ```
2. Line 113 (Cross-Pipeline I/O Relevance, Extract Progress paragraph): Replace the text about emitting `thread_signals, player_drift_signals, and candidate_opportunity` with just `advanced_threads and candidate_opportunity`. Also remove the sentence about flagging vestigial quest-related inputs (`quest_ages`, `quest_threshold_directive`) since these were already removed from prompts in commit 4d90515 — they no longer exist to be flagged.

**Why:** The mechanic ownership table is a reference for judges checking field-to-stream mapping accuracy. Stale entries cause false-positive "misplaced_mechanic" findings. The extract progress assessment text should reflect current inputs, not legacy ones that were already cleaned up.

**Code Snippet — Change to apply (line 91):**
```markdown
| `advanced_threads`, `candidate_opportunity` | progress |
```

**Code Snippet — Change to apply (line 113, Extract Progress paragraph):**
Replace:
> Arc thread context (active_threads, latent_threads) is passed via state but thread lifecycle is engine-driven (not extraction-driven) — the extractor emits thread_signals, player_drift_signals, and candidate_opportunity rather than quest_updates. Flag any vestigial quest-related inputs (quest_ages, quest_threshold_directive) that remain in the prompt but no longer have corresponding output fields.

With:
> Arc thread context (active_threads, latent_threads) is passed via state but thread lifecycle is engine-driven (not extraction-driven) — the extractor emits advanced_threads and candidate_opportunity rather than quest_updates. The legacy cross-stream items_gained/lost from state_ctx was removed once extraction_ctx covered this-turn derived data.

#### Step 1.4 — Fix meta.md: Update inter-judge contradiction check

**File:** `evals/rubrics/meta.md`

**What:** Line 51: Change "Check if `thread_signals` are being emitted correctly" to "Check if `advanced_threads` is being emitted in the progress extraction output".

**Why:** The field name changed from multi-signal system to single-field. Judges analyzing traces need correct terminology.

### Tests to write or update

No test changes needed — rubric files are text specifications consumed by LLM judges, not executable code. However, after all phases complete, run a quick eval with `--judge-only` on one scenario to verify the updated rubrics parse and produce valid output without errors from referencing deleted fields.

### REPOMAP updates required

None for this phase — repomap doesn't reference rubric content directly (it references engine modules).

## Implementation — Phase 2: Fix ARCHITECTURE.md StateDelta diagram

### Context files to load
- `/Users/pwilson/Repos/ccya/docs/ARCHITECTURE.md` (lines ~458-460, Delta Merge → Validate → Apply section)
- `/Users/pwilson/Repos/ccya/ccya/models.py` (StateDelta class definition for reference)

### Detailed steps

#### Step 2.1 — Replace quest_updates with arc_update in StateDelta diagram

**File:** `docs/ARCHITECTURE.md`

**What:** In the mermaid StateDelta merge node (line ~459), replace:
```
quest_updates
```
with:
```
arc_update
```

The full StateDelta text block should read:
```
scene_tags, scene_tagline
location_change, location_description
npc_add / npc_remove / npc_update
compendium_npc_update
scene_pressure_add / remove / update
inventory_add / remove / update
pc_condition_add / remove
arc_update
recent_events_add / update / remove

(gm_beat NOT in StateDelta —
written directly to state.meta.pending_gm_beat)
```

**Why:** `quest_updates` was removed from ProgressExtractResult when the quest system was replaced by the campaign arc/thread system (commit 3a90df6). The StateDelta model now includes `arc_update: CampaignArc | None` (models.py line 277), which carries engine-driven thread signal mutations.

**Validation:** Verify that models.py StateDelta class has no field named `quest_updates`. Confirm it does have `arc_update`. Cross-reference with the repomap extraction field routing section to ensure consistency.

### Tests to write or update

None — documentation-only change.

### REPOMAP updates required

Verify that `docs/repomap.md` "Extraction field routing" section (line 114) already correctly says "(no quest_updates)" for ProgressExtractResult — it does, so no change needed there.

## Implementation — Phase 3: Fix repomap.md pressure escalation thresholds

### Context files to load
- `/Users/pwilson/Repos/ccya/docs/repomap.md` (line 99)
- `/Users/pwilson/Repos/ccya/ccya/engine/config.py` (EngineConfig defaults for reference)
- `/Users/pwilson/Repos/ccya/ccya/engine/pressure.py` (_expire_scene_pressures function for reference)

### Detailed steps

#### Step 3.1 — Update pressure escalation thresholds in repomap.md

**File:** `docs/repomap.md`

**What:** Line 99: Change "background→building at 6 turns, building→immediate at 10" to "background→building at 3 turns (configurable via scene_pressure_building_at), building→immediate at 5 turns (configurable via scene_pressure_immediate_at)".

The full corrected text should read:
> **Mutate**: `pressure.py:_expire_scene_pressures()` — post-extraction expiry/urgency escalation; background→building at 3 turns (configurable via EngineConfig.scene_pressure_building_at), building→immediate at 5 turns (configurable via EngineConfig.scene_pressure_immediate_at); immediate pressures get TTL stamp on escalation (8-turn default from scene_pressure_immediate_ttl).

**Why:** Commit 096909e changed the hardcoded defaults in pressure.py from 6/10 to 3/5 and wired them through EngineConfig. The repomap text still referenced the old hardcoded fallback values that are now dead code (config is always passed to `_expire_scene_pressures` in turn.py).

**Validation:** Verify `EngineConfig.scene_pressure_building_at = 3` and `scene_pressure_immediate_at = 5`. Cross-reference with engine_mirror.py which imports these from EngineConfig — it should show the same values. Confirm pressure.py's hardcoded fallbacks (6/10) are only used when config is None, which never happens in production code.

### Tests to write or update

None — documentation-only change.

## Execution order

Phase 1 → Phase 2 → Phase 3. All three phases are independent text changes with no code execution required between them. They could technically run in parallel but sequential is safer for review.

## Final validation

After all phases complete:
```bash
# Verify rubric files parse correctly (no broken markdown)
python -c "from ccya.eval import load_eval_config; print('config loads ok')"

# Quick eval with judge-only mode to verify updated rubrics produce valid output
make JUDGE=state_correctness test 2>/dev/null || echo "(test command may vary — adjust as needed)"
```

Manually scan each modified rubric for:
- No remaining references to `thread_signals`, `player_drift_signals`, or `arc_engagement`
- Correct field names (`advanced_threads`) and constants (cap=3)
- Consistent terminology across all four rubrics
