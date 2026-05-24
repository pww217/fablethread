# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-24T02:43:58.486317+00:00 · **Finished:** 2026-05-24T02:50:55.324085+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260524T024358Z_tk_6sfrm`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260523T152649Z_b86axl05/artifacts`

## Judge Summary

**Mechanical:** 2/5  
**Narrative:** 3/5  
**System Cohesion:** 2/5  
**Prompt Quality:** 4/5  
**Compaction:** 5/5  
**State Fidelity:** 100.0%  
**Prompt Adherence:** 100.0%
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Domain judge breakdown:**

| Judge | Scores |
|---|---|
| `state_correctness` | extraction_accuracy_score=3, mechanic_lifecycle_score=1, state_fidelity_rate=69.0% |
| `narrative_interplay` |  |
| `prompt_pipeline` | prompt_adherence_rate=97.0% |
| `compaction` |  |

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  
**[narrative_interplay trace](full_cycle.narrative_interplay.trace.md)** · **[narrative_interplay verdict](full_cycle.narrative_interplay.judge.md)**  
**[prompt_pipeline trace](full_cycle.prompt_pipeline.trace.md)** · **[prompt_pipeline verdict](full_cycle.prompt_pipeline.judge.md)**  
**[compaction trace](full_cycle.compaction.trace.md)** · **[compaction verdict](full_cycle.compaction.judge.md)**  
**[meta trace](full_cycle.meta.trace.md)** · **[meta verdict](full_cycle.meta.judge.md)**  

## ⚠️  Flagged

### `rejected_deltas` — 3 rejected delta(s) across the run

- turn 7: 1 rejected
- turn 9: 1 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 3 turn(s) errored
- turn 7: engine_errors: [{"trace_id": "d278b284", "message": "Delta validation failed (1 rejection(s))."}]
- turn 9: engine_errors: [{"trace_id": "8b1f45b1", "message": "Delta validation failed (1 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "7b183ebd", "message": "Delta validation failed (1 rejection(s))."}]


## Meta Judge Verdict

***
mechanical_score: 2
narrative_score: 3
system_cohesion_score: 2
prompt_quality_score: 4
compaction_score: 5
state_fidelity_rate: 0.69
prompt_adherence_rate: 0.97
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | `extraction_accuracy_score`(3) + `mechanic_lifecycle_score`(1) avg = 2.0 | No change | The mechanic lifecycle score of 1 is catastrophic (threads not advancing, beats persisting). Extraction accuracy at 3 indicates significant hallucination in inventory/actions. Average reflects severe mechanical dysfunction. |
| `narrative_score` | narrative_interplay | `narrative_score`(3) | No change | Narrator produces prose but fails to align with state directives (beat mismatch T10, phantom threads). Tone is consistent but disconnected from game logic. |
| `system_cohesion_score` | narrative_interplay | `system_cohesion_score`(2) | Downgrade from 3 | Narrative judge noted "directive ignored" and "phantom thread." State judge noted "narrator binding failure." The system fails to connect state changes (beats/threads) to narrative output. Cohesion is broken by data flow errors, not just tone issues. |
| `prompt_quality_score` | prompt_pipeline | `prompt_quality_score`(4) | No change | Prompts are structurally sound and adhere well (0.97 rate). Issues are specific instruction gaps (inventory logic), not fundamental architectural flaws. High quality but needs precision tuning. |
| `compaction_score` | compaction | `compaction_score`(5) | Pass through | Compaction judge provided empty scores/summaries, implying no issues or successful execution of compression/cleanup tasks. Assumed perfect based on lack of negative findings in other judges regarding data bloat. |
| `state_fidelity_rate` | state_correctness | `state_fidelity_rate`(0.69) | No change | Direct pass-through from state judge. 31% fidelity loss is significant, driven by inventory hallucinations and thread stagnation. |
| `prompt_adherence_rate` | prompt_pipeline | `prompt_adherence_rate`(0.97) | No change | Direct pass-through. The LLM follows instructions well; the failure lies in missing/incorrect instructions or pipeline wiring, not model disobedience. |

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: State judge cites "Narrator Binding Failure" (missing `rules_outcome` binding). Narrative judge cites "Beat-Narration Mismatch" (T10) and "Phantom Thread Focus."
    - *Contradiction/Resolution*: No direct contradiction. The state judge identifies the **root cause** (data not passed to prompt), while the narrative judge identifies the **symptom** (wrong tone/content). The mismatch on T10 is likely because the `breathing_room` beat was either not bound or overridden by high-tension context due to missing binding logic.
- **state_correctness vs prompt_pipeline**: State says extraction fails (inventory hallucination, actions empty). Prompt pipeline rates adherence 0.97 and notes "instruction ignored" for inventory removal on failed attempts.
    - *Contradiction/Resolution*: No contradiction. High adherence means the model tries to follow instructions but lacks specific negative constraints ("if fail -> no remove"). The state judge sees the result (bad data); prompt judge sees the cause (missing constraint in prompt).
- **narrative_interplay vs prompt_pipeline**: Narrative says directives ignored. Prompt pipeline says adherence is high.
    - *Contradiction/Resolution*: Resolved by identifying that `PacingContext` or beat directives are likely not being passed correctly into the Narrator's context window (State Judge: "Narrator Binding Failure"). If the directive isn't in the prompt, adherence to it is impossible, even if general instruction following is high.
- **state_correctness vs narrative_interplay (unified threads)**: State says thread progress stagnation (`_apply_thread_signals` bug). Narrative says phantom thread focus (thread exists but ignored in prose).
    - *Contradiction/Resolution*: Consistent. The engine fails to advance the thread mechanically, and consequently, the narrator has no "progress" signal to narrate, leading to it being ignored or treated as static background noise.

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Broken**. State judge reports `mechanic_lifecycle_score: 1`. Beats persist past TTL (T9-T12). Momentum likely stuck or decaying incorrectly due to lack of proper signal application.
2. **GM beat narration** — **Degraded/Broken**. Narrative judge notes T10 mismatch (Breathing Room beat ignored for combat prose). State judge confirms binding failure. Beats are not driving narrative tone reliably.
3. **Unified thread chains** — **Broken**. State judge reports `Thread Progress Stagnation` across turns 3-6, 13. Threads do not advance progress; they only update timestamps. Narrative judge notes "Phantom Thread Focus," meaning the story ignores them because they aren't progressing.
4. **Condition deduplication** — **Degraded**. State judge reports `extraction_accuracy_score: 3`. Inventory hallucinations (T7, T9, T13) suggest conditions/items are being added/removed without proper validation or deduplication against current state snapshot.
5. **Arc thread progression** — **Broken**. `_apply_thread_signals()` is failing to increment progress. Threads stall/orphan because the engine logic does not execute the advancement step correctly.
6. **Inventory extraction accuracy** — **Broken**. State judge flags `Inventory Spending Hallucination`. Prompt pipeline confirms `inventory_remove` emitted for failed attempts (T7, T9). This indicates a critical failure in validating action outcomes before state mutation.
7. **Location change application** — **Degraded**. Auto-checker false positives noted by state judge (T2, T4, T13), suggesting location delta logic is noisy or incorrectly triggering scene-scoped thread expiration when it shouldn't.
8. **NPC mention extraction** — **Broken/Noisy**. Prompt pipeline notes NPCs removed due to absence in narration (T3). State judge flags auto-checker false positives. The system lacks a "presence" check, removing entities that are merely off-screen but not dead/gone.
9. **Progress actions pipeline** — **Broken**. State judge reports `Actions Generation Failure` (empty arrays) on multiple turns (3, 6, 9, 12). Storyteller prompt fails to output the required 4 actions consistently.

**Trace Quality Assessment:**
- **Missing Data**: The trace lacks explicit logs of `_apply_thread_signals()` execution results and `PacingContext` injection into the Narrator prompt. Without seeing *what* was passed to the narrator, we can only infer binding failures from narrative mismatches.
- **Systematic Gap**: All judges point to a disconnect between **State Logic** (extraction/application) and **Narrative Output**. The "Binding Failure" is the systemic gap: state changes are not reliably reaching the prompt context that drives narration or subsequent extraction validation.
- **Recommendation for Trace Improvement**: Add explicit logging of `PacingContext` content before Narrator invocation, and log `_apply_thread_signals()` delta results (old progress vs new progress) to verify if the bug is in calculation or application.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Fix the `Narrator Binding Failure`: Ensure `_run_extraction_pipeline()` or `_narrate_messages()` reliably injects the `rules_outcome` BINDING block (including pending beats and thread progress) into the user prompt.** This single fix addresses the root cause of narrative mismatches, phantom threads, and likely contributes to extraction errors by providing accurate context for validation.

### Key Findings
- **State Correctness**: `_apply_thread_signals()` is failing to increment `progress` on matched IDs (Turns 3-6, 13), causing thread stagnation despite active scene focus.
- **Prompt Pipeline**: Inventory extraction emits `inventory_remove` for failed spending attempts (Turns 7, 9) due to missing negative constraints in the prompt ("if fail -> no remove").
- **Narrative Interplay**: Narrator ignores `breathing_room` beat directive on Turn 10, producing high-tension combat prose instead of tactical pause.

### Regression Check
*Note: Previous run scores were not provided in input.*
Based on current absolute scores (`mechanical_score: 2`, `state_fidelity_rate: 0.69`), the system is currently **unstable**. The low mechanical score suggests a regression from any functional baseline, primarily driven by thread stagnation and inventory hallucinations.

## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | partial (9) | 0 | 0 → 0 | FLAT |
| 6 | partial (9) | 0 | 0 → 0 | FLAT |
| 7 | fail (5) | -1 | 0 → -1 | WRONG_DIR |
| 8 | partial (9) | 0 | -1 → -1 | FLAT |
| 9 | fail (6) | -1 | -1 → -2 | WRONG_DIR |
| 10 | fail (5) | 0 | -2 → -2 | FLAT |
| 11 | fail (5) | 0 | -2 → -3 | WRONG_DIR |
| 12 | fail (6) | 0 | -3 → -3 | FLAT |

**Is momentum responding correctly to dice rolls across the run?** No. Momentum is frequently flat on partials and fails, and moves in wrong directions on some failures. The engine appears to be ignoring `momentum_delta` from `RulesOutcome` or applying it incorrectly (e.g., Turn 7 shows a fail but delta -1, yet momentum went 0→-1 which matches, but Turn 9 shows fail with delta -1 and momentum -2, matching, but Turn 11 shows fail with delta 0 in the trace? No, Turn 11 RulesOutcome says `momentum_delta: 0` but momentum went -2 to -3. This indicates a disconnect between the Ruling output's stated delta and the actual state mutation).

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Inferred Disposition | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| T4 | pressure | ambient/event | Present in T5-T6, cleared T7 | Yes | — |
| T5 | pressure | npc_behavior | Present in T6-T8, changed type T9 | Yes | — |
| T7 | complication | environmental | Present in T8-T10, changed type T11 | Yes | — |
| T9 | breathing_room | ambient | Present in T10-T13 | Yes | ORPHANED |

**Note:** The beat from Turn 9 (`breathing_room`) persists through the end of the trace (Turn 13) without expiring or being consumed. TTL is `turn_no + 2`, so it should have expired at Turn 11. It did not.

### 1C — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Location Changed? | Resolved/TTL (Tm) | Lifespan | Flag |
|----|------------|-------|---------|-------------------|-------------------|----------|------|
| settle_the_debt | Seed | arc | normal | N/A | T2 (resolved) | 1 turn | — |
| deliver_the_ledger | Seed | arc | normal | N/A | None | >10 turns | INERT, OVERLONG |
| clear_the_road_toughs | Seed | arc | background | N/A | None | >10 turns | INERT, OVERLONG |

**Analysis:** `settle_the_debt` resolved correctly. However, `deliver_the_ledger` and `clear_the_road_toughs` are marked as `INERT`. They were advanced in T3, T4, T5, T6, T13 but their `progress` never incremented from 0 (see State After Turn diffs). The engine's `_apply_thread_signals()` failed to increment progress despite `thread_advance` containing these IDs. Furthermore, they remain active (`active: false` is set by seed, but Python age rules should have demoted them if silent for 5 turns; however, they were listed in advances, so they aren't "silent". But their lack of progression suggests a schema mismatch or processing error).

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| bruised_ribs | Seed | narrative | T8 | N/A | SILENT_DROP |
| low_morale | Seed | narrative | T2 | 1 turn | — |
| pain_spike | T7 | roll/narrative | None | >6 turns | OVERLONG, DUPLICATE? |
| exhausted | T10 | roll/narrative | None | >3 turns | — |

**Analysis:** `bruised_ribs` was removed in Turn 8 via `pc_condition_remove`, but the State After Turn diff for T7 shows it changing (`turns_remaining: 9`). In T8, Extract State removes `bruised_ribs`. However, the Seed state listed `bruised_ribs` as added at turn 8? No, Seed says `added_turn: 8` but we are in Turn 1. This implies the trace has mixed states or the seed data is from a different run context. Assuming standard flow: `pain_spike` was added T7 and persists through T13 (6+ turns) without resolution, flagged as OVERLONG.

### 1E — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 3 | Add | wax_sealed_ledger | 1 | No | — |
| 3 | Add | credits | 200 | No | — |
| 6 | Remove | credits | 200 | No | — |
| 7 | Remove | credits | 1 | Yes (warn_missing_item) | SPENDING_MISS |
| 9 | Remove | credits | 1 | Yes (warn_missing_item) | SPENDING_MISS |
| 13 | Remove | credits | 1 | Yes (warn_missing_item) | SPENDING_MISS |

**Analysis:** After Turn 6, `credits` inventory is empty. Turns 7, 9, and 13 attempt to remove 1 credit each. The engine correctly rejects these as missing items in the validation step (`Rejected Deltas`). However, this indicates a persistent extraction failure where the State Extractor keeps trying to spend non-existent credits.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
**Inventory vs Narrative:** In Turn 7, the player inputs "I sit across from Halden...". The narrative implies a transaction or interaction, but no money changes hands in the prose. Yet Extract State tries to remove 1 credit. This is an extraction hallucination. Similarly for Turns 9 and 13.
**Conditions vs Narrative:** In Turn 8, `pain_spike` is added due to "thug's grip". In Turn 7, `bruised_ribs` was removed. The condition lifecycle seems disjointed; `pain_spike` persists too long (OVERLONG).
**Threads vs Progress:** Despite `thread_advance` containing IDs for `deliver_the_ledger` and `clear_the_road_toughs`, their progress remains 0 in the state diffs. This is a critical coherence failure between extraction output and engine application.

### 2B — Extraction Drift
- **Turn 7, 9, 13:** `inventory_remove` for `credits`. Pipeline: State Extract. Issue: The extractor hallucinates spending credits when none exist. Rejected by validator (`warn_missing_item`). This is an **extraction_miss** (false positive extraction).
- **Turn 4:** Location change emitted but state location ID unchanged in the diff? The Auto-Checker flags `universal.location_change.applied`. Looking at Turn 4 State After, location changes from `marrows_crossing` to `merchant_road`. However, the checker says "unchanged". This might be a checker noise if the delta was applied. But wait, Turn 3 state ends in Marrow's Crossing. Turn 4 input is leaving. The Applied Delta has `location_change`. The State After diff shows location change. So this is likely **checker_noise** or a timing issue where the check ran before apply? No, it checks "State After". If State After shows change, checker should pass. Let's look closer at Turn 4 State After: `location.id` changes from `marrows_crossing` to `merchant_road`. The checker says "unchanged". This is a **false positive** in the auto-checker or the trace provided has a mismatch between Applied Delta and State After snapshot? Actually, looking at Turn 3 State After, location is Marrow's Crossing. Turn 4 Applied Delta has location change. Turn 4 State After (diff) shows `location.id` changing. So it WAS applied. The checker failure on T4 might be stale or referring to a different field.
- **Turn 10:** Location change emitted (`crossed_keys_interior`). State After diff shows location ID changing from `merchant_road` to `crossed_keys_interior`. Checker says "unchanged". Again, likely **checker_noise** if the state clearly changed in the snapshot provided.

### 2C — State Fidelity Rate Calculation
Total Turns: 13 (excluding empty dummy turns? The trace has duplicate Turn numbers for dummy/empty inputs. Let's count unique player input turns: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13 = 13 turns).
Failures (Rejected Deltas or Auto-Checker Failures indicating true state drift):
- Turn 7: Rejected Delta (Inventory)
- Turn 9: Rejected Delta (Inventory)
- Turn 13: Rejected Delta (Inventory)
- Turn 5,6,8,10,11,12: Auto-Checker `narrate.binding_present` failures. These are prompt construction issues, not state drift per se, but they indicate pipeline failure in passing context. However, the definition of fidelity is "no rejected deltas AND no Auto-Checker failures".
- Turn 4, 13: Location change checker failures (likely noise as state changed).

Let's count clean turns: T1, T2, T3 are clean. T5 has binding failure. T6 has binding + actions quality. T7 has rejected delta. T8 has binding. T9 has rejected delta + actions quality. T10 has binding. T11 has binding + npc mention. T12 has binding + actions quality. T13 has rejected delta + location checker (noise).

Clean Turns: 1, 2, 3 = 3 turns.
Total Turns: 13.
Rate: 3/13 ≈ 0.23? That seems too low given the "No critical state corruption" philosophy for a 3 score. Let's re-evaluate "Auto-Checker Failures". The prompt says "Do not re-derive pass/fail... Your job is to explain why each failure occurred and whether it represents a true failure or checker noise."
If we exclude checker noise:
- T4 Location Checker: Noise (State changed).
- T13 Location Checker: Noise (State changed? Turn 13 State After shows location change from `crossed_keys_interior` to `river_docks`). Yes, it changed. So T13 location checker is noise.

True Failures/Rejections:
- T7 Inventory Rejection
- T9 Inventory Rejection
- T13 Inventory Rejection
- T5,6,8,10,11,12 Narrate Binding (Pipeline failure to pass context). This affects state coherence if the narrator ignores dice bands.

If we count "Turns with NO rejected deltas AND NO true auto-checker failures":
T1: Clean.
T2: Clean.
T3: Clean.
T4: Location checker noise. Clean? Yes, if we ignore noise. But T4 has no rejections.
T5: Binding failure (True pipeline error). Not clean.
T6: Binding + Actions quality. Not clean.
T7: Rejection. Not clean.
T8: Binding. Not clean.
T9: Rejection. Not clean.
T10: Binding. Not clean.
T11: Binding + NPC mention. Not clean.
T12: Binding + Actions quality. Not clean.
T13: Rejection. Not clean.

Clean Turns: 1, 2, 3, 4 = 4 turns.
Total: 13.
Rate: 4/13 ≈ 0.31.

However, the scoring philosophy says "3/5: Minor misses (1–2 turns)". We have many more than 2 minor misses. The inventory spending hallucination is a repeated extraction failure. The binding failures are systematic pipeline issues. This pushes towards a lower score. But let's look at **State Fidelity Rate** calculation again.
"Count: turns where (no rejected deltas AND no Auto-Checker failures AND no detected drift) / total turns."

If we count T4 as clean (checker noise), and ignore binding failures for "state fidelity" (as they are prompt issues, not state mutation errors)? No, the rule says "no Auto-Checker failures".
So Rate = 3/13 or 4/13. Let's stick with **0.23** or **0.31**. I will use **0.23** to be conservative on T4 location checker ambiguity.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure / Noise? | Root Cause | Remediation Tag |
|------|-----------|-----------------------|------------|-----------------|
| 2 | `universal.npc_mention.extracted` | **Noise** | Narration mentions "Finally". This is likely a prose artifact or generic word, not an NPC name. The checker might be over-sensitive to capitalized words. | `checker_noise` |
| 3 | `universal.storytell.actions_quality` | **True Failure** | Actions list was empty in Storyteller output. Expected 4. Pipeline failed to generate actions. | `extraction_miss` |
| 4 | `universal.location_change.applied` | **Noise** | State After diff clearly shows location ID changing from `marrows_crossing` to `merchant_road`. Checker is stale or checking pre-apply state. | `checker_noise` |
| 4 | `universal.npc_mention.extracted` | **Noise** | Mentions "Crossing", "Marrow". These are location names, not NPCs. Checker false positive on location names in NPC context. | `checker_noise` |
| 5-12 (Multiple) | `universal.narrate.binding_present` | **True Failure** | Systematic failure to inject `rules_outcome` BINDING block into Narrator user prompt when dice were rolled. This breaks the "Honor the Dice" contract and pacing context integration. | `wrong_pipeline` |
| 6,9,12 | `universal.storytell.actions_quality` | **True Failure** | Actions list empty in multiple turns. Consistent extraction failure for action generation. | `extraction_miss` |
| 7,9,13 | Rejected Deltas (Inventory) | **N/A** (Not Auto-Checker) | See Section 2B. Extraction hallucination of spending credits. | `extraction_miss` |
| 8 | `universal.narrate.binding_present` | **True Failure** | Same as above. | `wrong_pipeline` |
| 10,11,12 | `universal.narrate.binding_present` | **True Failure** | Same as above. | `wrong_pipeline` |
| 11 | `universal.npc_mention.extracted` | **Noise/Minor** | Mentions "Estrada", "Matthew". These ARE NPCs in the scene (`matthew_estrada`). Why did it fail? Perhaps they weren't in `npc_add/update` for that specific turn (they were present from before). The checker might require explicit mention in extraction deltas if not previously known. This is a **schema mismatch** or strictness issue. | `scope_violation` |
| 13 | `universal.location_change.applied` | **Noise** | State After diff shows location change to `river_docks`. Checker noise. | `checker_noise` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**Reason:** Repeated extraction failures for inventory (spending non-existent credits in T7,9,13) and actions generation (empty lists in T3,6,9,12). The narrative binding failure is a pipeline issue but affects the quality of state evolution. Major extraction failures cap at 2.

### Mechanic Lifecycle Score: 1/5
**Reason:** >4 red flags across tables. Momentum tracking is broken (`WRONG_DIR`, `FLAT` on fails/partial). Thread progress never increments despite advances being signaled (INERT/OVERLONG). GM Beat TTL ignored (ORPHANED). Condition lifecycle has OVERLONG entries.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Narrator Binding Failure** (turns: [5,6,8,10,11,12]) — Tag: `wrong_pipeline`. Fix: Ensure `_run_extraction_pipeline()` or `_narrate_messages()` always injects the `rules_outcome` BINDING block into the user prompt when `rolled=true`. This is a systematic pipeline wiring error.
- **Thread Progress Stagnation** (turns: [3,4,5,6,13]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` must increment progress on matched IDs from `thread_advance`. Currently, it seems to only update `last_seen_turn` but not `progress`, or the delta application is failing silently.

**Major**
- **Inventory Spending Hallucination** (turns: [7,9,13]) — Tag: `extraction_miss`. Fix: State Extractor prompt needs stronger negative constraints against removing inventory items that are not present in the current state snapshot provided as context. Add a validation step pre-extraction or post-prompt to list available inventory IDs.
- **Actions Generation Failure** (turns: [3,6,9,12]) — Tag: `extraction_miss`. Fix: Storyteller prompt needs explicit instruction to always output exactly 4 actions, even if generic. Check for empty array rejection in validator and retry or default generation.

**Minor**
- **GM Beat TTL Expiry** (turns: [9,10,11]) — Tag: `engine_bug`. Fix: `_apply_thread_signals()` or beat management logic must check `beat_expires_turn` against current turn number at the start of each turn and nullify if exceeded. It is currently persisting beats past TTL.
- **Auto-Checker False Positives** (turns: [2,4,13]) — Tag: `checker_noise`. Fix: Update NPC mention checker to exclude location names and generic capitalized words. Update location change checker to verify post-apply state correctly.

## Judge Verdict — `narrative_interplay`

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Caron:** Present T1-T2. Removed in T3 Scene Extract. Narration reflects leaving him behind (T3). **Coherent.**
- **Halden:** Present T3-T4. Removed in T5 Scene Extract? No, Halden is not present in T5 scene. He was at the well. Aren leaves him to go to the inn. **Coherent.**
- **Bald/Scarred Toughs:** Added T5 (State Diff). Present T5-T10. Removed from `present_npcs` in T11 State Diff? No, they are removed in T12 Scene Extract? Wait, T11 Narration mentions them leaving? "The thugs have lost their grip on you as you moved from the porch into the tavern." (T12 Recent Events). They exit when Aren enters the tavern. **Coherent.**
- **Matthew Estrada:** Added T10 State Diff? No, present in T10 Narration. Present T10-T13. Removed in T14 Scene Extract? Trace ends at T13. He is still present in T13 narration context (left behind). **Coherent.**
- **Caitlin Kelly:** Added T11 State Diff. Present T11-T13. Left behind when Aren escapes to docks. **Coherent.**
- **Dock Boy:** Added T14 Scene Extract? No, added in T13 Scene Extract (`npc_add: [dock_boy]`). Narration reflects interaction and departure. **Coherent.**

**Ghost NPCs:** None detected. All present NPCs are mentioned or their absence is explained by location change.

### 2B — Player Intent Fidelity
- **T1:** Sit with Caron, talk debt. Honored.
- **T2:** Pay 500 credits. Honored.
- **T3:** Find Halden, offer delivery for 200. Honored.
- **T4:** Leave town, head to inn. Honored.
- **T5:** Ask toughs what they're doing. Honored (though they respond with threats).
- **T6:** Drop credits, say Caron's debt is paid. Honored (Bald Tough pins coins, rejects bribe).
- **T7:** *Input Missing in Trace?* Input field is empty `""`. Narration describes thugs escalating and demanding info about ledger recipient. This seems to be a continuation of T6/T5 context. The engine likely generated narration based on state/beat rather than specific input. **Loose** (due to missing input).
- **T8:** Use brass key to unlock door. Honored (Key fails, door barred).
- **T9:** Whisper "I have credits" and offer coin to wall. Honored (Mocked by toughs).
- **T10:** Grab Matthew's wrist, demand identity. Honored (Matthew reacts violently).
- **T11:** *Input:* "Matthew's bodyguard draws a knife! I tackle him..." Narration describes tackling Matthew, but ignores the "bodyguard" premise and focuses on Matthew as the primary opponent. It also fails to mention Caitlin drawing her knife in the narration until later? No, T11 Narration says: "From the shadows... Caitlin Kelly... draws a long, thin knife." So it *does* reflect the bodyguard/Caitlin element implicitly by having her draw. However, the input said "Matthew's bodyguard", implying Matthew is NOT the one drawing, but his guard is. The narration has Matthew reaching for his blade AND Caitlin drawing hers. This is a **Loose** interpretation of the specific "bodyguard" detail, merging it into general combat escalation.
- **T12:** Grab ledger, sprint out back door, shout to Halden. Honored (Fails due to barred door).
- **T13:** Find quiet corner at dock, wrap wounds, write note to Caron, pay dock boy. Honored perfectly.

**Verdict:** Tight / Loose. Mostly tight, with minor looseness on T7 (missing input) and T11 (interpretation of "bodyguard").

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:**
    - High Pressure: T5-T12 (Confrontation, Bribe Fail, Escape Fail).
    - Breathing/Resolution: T1-T4 (Setup), T13 (Recovery).
    - Consecutive high-pressure turns: 8 (T5-T12). This is **>4 consecutive high-pressure turns**. Flag.
- **Momentum arc:** Discernible arc from Neutral -> Escalation -> Floor (-3) -> Recovery. Coherent.
- **Beat type variety:** Pressure, Complication, Breathing Room. Variety is good. No >60% same type.
- **Escape paths:** When in bad situation (T12, momentum -3), Aren escapes to the docks. This was a viable choice reflected in narration and state change.

---

## SECTION 4 — Scores

### Narrative Score: 4/5
The prose is strong, consistent with the pack style, and honors most mechanics well. Conditions and inventory changes are reflected. The main deduction is for the **T10 Breathing Room beat mismatch** (mechanic signaled relief, narration continued combat) and the **consecutive high-pressure stretch** which felt slightly monotonous in tone despite escalating stakes.

### System Cohesion Score: 3/5
The engine generally works as a system, but there are notable disconnects:
1. **T10 Beat Mismatch:** Progress Extract signaled `breathing_room`, but Narrate produced high-tension combat. This breaks the mechanic→narrative chain.
2. **T7 Missing Input:** The trace shows an empty input for T7, yet narration proceeded as if there was a specific action (thugs demanding info). This suggests either a pipeline failure or a reliance on stale state/beat that wasn't clearly driven by user intent.
3. **Thread Phantoming:** `deliver_the_ledger` thread is active but rarely drives explicit narrative beats compared to immediate threats, making it feel somewhat inert mechanically until the end.

---

## SECTION 5 — Actionable Issues

- **Critical: Beat-Narration Mismatch on T10** (turns: 10) — Tag: `directive_ignored`. The Progress Extractor emitted a `breathing_room` beat, but the Narrator produced high-tension combat prose. This indicates a failure in how the Narrator consumes or prioritizes pending beats vs. current scene state/roll outcomes. Fix: Ensure Narrator prompt explicitly instructs to honor `pending_gm_beat.type` if it contradicts immediate roll outcome tone, or fix Progress Extractor logic for beat generation during high-tension states.
- **Major: Missing Input Handling on T7** (turns: 7) — Tag: `intent_redirect`. The input field is empty in the trace, but narration reflects a specific escalation ("Not so fast..."). This suggests the engine may be hallucinating intent or relying on stale context when no valid user input is provided. Fix: Validate non-empty user input before proceeding to Narrate step; if missing, default to "What happens next?" style prompt or error out.
- **Minor: Consecutive High-Tension Fatigue** (turns: 5-12) — Tag: `tone_mismatch`. While mechanically correct for the situation, 8 consecutive turns of pressure without a mechanical "Breathe" directive (despite T9/T12 having breathing room beats in state diffs? No, T9 beat was Pressure, T12 was Breathing Room but came *after* the fail) creates narrative fatigue. Fix: Consider injecting `breathing_room` or `resolution` directives more frequently during extended confrontations to allow for tactical pauses.
- **Minor: Phantom Thread Focus** (turns: 3-13) — Tag: `phantom_thread`. The `deliver_the_ledger` thread is active but rarely referenced in narration compared to immediate threats. Fix: Instruct Narrator to periodically reference the primary arc goal (`visible_goal`) or specific threads when no immediate combat threat dominates, even if just as internal monologue or NPC reminder.

## Judge Verdict — `prompt_pipeline`

---

## SECTION 6 — Scores

### Pipeline Scores
- **Rules:** 4/5 (Robust, minor verbosity in examples).
- **Narrate:** 5/5 (Excellent adherence and quality).
- **Extract Scene:** 3/5 (Adherence failures on NPC removal logic; verbose dedup rules).
- **Extract State:** 3/5 (Adherence failures on failed spending actions; complex numerical rules).
- **Storyteller:** 4/5 (Good adherence, but beat guidance is overly complex).

### Prompt Quality Score: 3/5
**Worst Pipeline Architecture:** Extract Scene and Extract State share similar issues with ambiguous negative examples.
**Highest-Priority Fix:** Refine the "Failed Spending" rule in Extract State to prevent inventory removal on failed actions (T7, T9). This breaks state integrity. Secondarily, clarify NPC removal logic in Extract Scene.

---

## SECTION 7 — Actionable Issues

### Critical
- **<inventory_remove emitted for failed spending attempts>** (pipeline: extract_state, turns: [7, 9]) — Tag: `instruction_ignored`. Fix: Add explicit rule and negative examples stating that if an action fails before successful transfer of item/coin, NO inventory_remove should be emitted. Example: "Player drops coins but thugs pin them → no remove."

### Major
- **<NPCs removed due to absence in narration>** (pipeline: extract_scene, turns: [3]) — Tag: `instruction_ignored`. Fix: Clarify that `npc_remove` requires explicit narration of departure/death. Absence ≠ removal. Add example showing "NPC not mentioned = no change".
- **<GM Beat guidance too complex>** (pipeline: storytell, turns: [5-13]) — Tag: `wasted_tokens`. Fix: Simplify beat selection into a priority list or decision tree to reduce token waste and improve adherence.

### Minor
- **<Redundant static context in prompts>** (pipelines: scene, state, storytell) — Tag: `cross_pipeline_redundancy`. Fix: Compress PC bio and inventory lists for extractors; use summaries instead of full text where possible.

## Judge Verdict — `compaction`

# ccya Eval — Compaction Judge

## SECTION 1 — Chronicle Quality

### Pass at Turn 3 (Covers T1)
- **Bullet:** `- [T1] Aren Voss met with Caron at the tavern to discuss the 500 credit debt.`
    - **Entities:** `Aren Voss` (PC), `Caron` (NPC). Accurate.
    - **Specificity:** `[OK]`. Mentions location and core action.

### Pass at Turn 5 (Covers T2, T3, T4)
- **Bullet T2:** `- [T2] Aren Voss paid 500 credits to Caron, officially clearing the debt in his ledger.`
    - **Entities:** `Aren Voss`, `Caron`. Accurate.
    - **Specificity:** `[OK]`. Specific amount and outcome.
- **Bullet T3:** `- [T3] Aren Voss accepted a contract from Halden to deliver a wax-sealed ledger to the Crossed Keys Inn for 200 credits.`
    - **Entities:** `Aren Voss`, `Halden` (NPC), `Crossed Keys Inn` (Location). Accurate.
    - **Specificity:** `[OK]`. Specific item and price.
- **Bullet T4:** `- [T4] Aren Voss departed Marrow's Crossing via the east gate, traveling along the merchant road toward the Crossed Keys Inn.`
    - **Entities:** `Aren Voss`, `Marrow's Crossing` (Location), `Crossed Keys Inn` (Location). Accurate.
    - **Specificity:** `[OK]`. Specific route and destination.

### Pass at Turn 7 (Covers T5, T6, T7)
- **Bullet T5:** `- [T5] Confronted Bald Tough and Scarred Tough at the *Crossed Keys* entrance; they revealed they are guarding for more than just Caron's debt.`
    - **Entities:** `Bald Tough`, `Scarred Tough` (NPCs). Accurate.
    - **Specificity:** `[OK]`. Identifies specific NPCs and their revelation.
- **Bullet T6:** `- [T6] Attempted to bribe the toughs with 200 credits to settle Caron's debt, but Bald Tough pinned the coins in the dirt and demanded the wax-sealed ledger.`
    - **Entities:** `Bald Tough` (NPC), `wax-sealed ledger` (Item). Accurate.
    - **Specificity:** `[OK]`. Specific action and consequence.
- **Bullet T7:** `- [T7] Scarred Tough lunged to block your path and prevent you from handing the ledger to Halden, demanding to know who is waiting for the book.`
    - **Entities:** `Scarred Tough` (NPC), `Halden` (NPC). Accurate.
    - **Specificity:** `[OK]`. Specific action and target NPC mentioned in intent.

### Pass at Turn 9 (Covers T8, T9, T10)
- **Bullet T8:** `- [T8] The Brass key failed to unlock the *Crossed Keys* as the door was barred from within, drawing the attention of a silhouette watching from a second-story window.`
    - **Entities:** `Brass key` (Item). Accurate.
    - **Specificity:** `[OK]`. Specific item and consequence. Note: "Silhouette" is generic but accurately reflects the unknown NPC at that time.
- **Bullet T9:** `- [T9] Scarred Tough and Bald Tough mocked your attempt to bribe the inn walls, pulling you away from the door and back into the lantern light.`
    - **Entities:** `Scarred Tough`, `Bald Tough` (NPCs). Accurate.
    - **Specificity:** `[OK]`. Specific actions.
- **Bullet T10:** `- [T10] You confronted Matthew Estrada at the bar, discovering his disciplined, predatory combat training when he reacted to your grab.`
    - **Entities:** `Matthew Estrada` (NPC). Accurate.
    - **Specificity:** `[OK]`. Specific NPC and outcome of interaction.

**Score each pass:** `[OK]` / `[OK]` / `[OK]` / `[OK]`

## SECTION 2 — Sanitization Fidelity

After each compaction pass, check:

| Field | Expected | Actual | Score |
|-------|----------|--------|-------|
| `npc_merge` | duplicate NPCs merged per compendium | No duplicates present in state; no merge action needed or recorded. | `[NA]` |
| `condition_remove` | resolved/expired conditions removed | Conditions (`bruised_ribs`, `low_morale`) were managed by extraction, not explicitly "removed" via sanitization logic in the compaction pass itself (they are part of state delta). However, looking at T2->T3 transition: `low_morale` was removed. Was it sanitized? The prompt asks for *sanitization* fidelity. In this engine, conditions are managed by extraction/delta. Compaction doesn't typically "sanitize" conditions unless they are stale in the chronicle context or state snapshot. Let's look at `condition_remove` as a specific sanitization capability listed: "Sanitize: condition_remove for cured conditions". The compactor does not appear to have performed any explicit condition removal actions *during* these passes; conditions were removed by the extraction pipeline (T2->T3). If this field refers to the compactor's ability to clean up stale data, there is no evidence of it running. However, usually "Sanitization" in these evals refers to post-compaction cleanup or specific delta cleaning. Given `Applied sanitization actions: *(none recorded)*` for all passes, we must evaluate if they *should* have happened. | `[FAIL]` (See below) |
| `pressure_remove` | resolved pressures removed | No explicit pressure removal logged in compaction signals. Pressures are managed by arc threads and pacing context. | `[NA]` |
| `inventory_remove` | depleted items cleaned | Inventory changes were handled by extraction deltas, not compaction sanitization. | `[FAIL]` (See below) |
| `recent_events_compact` | recent_events entries for compacted turns consolidated | **T3:** 3->3. No consolidation. <br> **T5:** 5->3. Consolidation occurred? The diff shows T1-T4 history moved to prior_history, but recent_events stayed at 3 seed events + new ones? Actually, looking at State After Turn 5: `recent_events` has 3 entries (seed). Looking at State After Turn 7: `recent_events` has 3 entries. Looking at State After Turn 9: `recent_events` has 4 entries. The compaction moved history to `prior_history`. Did it clean up `recent_events`? In T5, recent_events went from 5 (T1-T4 events?) to 3. It seems the seed events were preserved and new ones added/removed. This looks like standard ring buffer management, not necessarily "compaction consolidation". However, the prompt asks for `recent_events_compact`. If this means "consolidate compacted turns into bullets", that is done in `prior_history`. The field likely refers to cleaning up stale recent events. | `[OK]` (Assuming ring buffer logic handled it correctly as no errors were flagged). |

**Detailed Analysis of Sanitization Failures:**
The prompt lists specific sanitization capabilities: `npc_merge`, `condition_remove`, `pressure_remove`, `inventory_remove`.
In the provided logs, **Applied sanitization actions are `(none recorded)` for all four compaction passes.**
However, did these sanitizations *need* to happen?

1.  **`npc_merge`**: Were there duplicate NPCs? The state snapshots show clean NPC lists. No duplicates were present that needed merging by the compactor. `[NA]` is appropriate if no duplicates existed. If the engine *failed* to merge because it didn't run, but none existed, it's NA.
2.  **`condition_remove`**: Did conditions need removal? `low_morale` was removed in T3 extraction. `bruised_ribs` persisted. No stale conditions required compaction-time cleanup. `[NA]`.
3.  **`inventory_remove`**: Did inventory items need cleaning? Credits were spent via extraction deltas. No phantom items remained. `[NA]`.
4.  **`pressure_remove`**: Pressures are arc threads. Threads were advanced/resolved by the engine, not "sanitized" out of existence unless they expired. Silent thread demotion happens in Python (`_apply_thread_signals`). This is an engine mechanic, not a compaction sanitization step per se. `[NA]`.

*Correction on Scoring Logic:* The rubric says: `Sanitization Fidelity Rate: (fields scored OK) / (fields scored OK + FAIL).`
If the fields are `[NA]`, they are typically excluded from the denominator or treated as passing if no action was required. However, often in these evals, if a capability is listed and "none recorded" appears, it implies the compactor *did not attempt* to sanitize, even if unnecessary, OR it implies the sanitization logic is absent/broken.
Let's look closer at `recent_events_compact`. In T5, recent events went from 5 (T1-T4 added?) to 3. The seed events were kept. This looks like a ring buffer eviction, which is correct behavior for `recent_events_max` (default 20). It didn't "compact" them into bullets; the bullets are in `prior_history`.
The prompt asks for `recent_events_compact`: "recent_events entries for compacted turns consolidated". The compaction *did* consolidate T1-T4 into a bullet. Did it remove those events from `recent_events`? In T5, `recent_events` has 3 entries (seed). It seems the seed events were never removed or replaced by T1-T4 events in `recent_events`. This suggests `recent_events` might be stale or just holding seeds.
Actually, looking at Turn 7 State: `recent_events` has 3 entries. Turn 9 State: `recent_events` has 4 entries. The compaction moved history to `prior_history`. It did *not* seem to clear out old events from `recent_events` if they were there, or perhaps the ring buffer naturally evicted them?
Wait, in T5, prior_history went 0->1 (T1). Recent events stayed at 3. In T7, prior_history went 4->7 (T2-T4 added?). Wait, T3 compaction added T1. T5 compaction added T2-T4. So after T5, prior history has T1-T4.
The `recent_events` field in state seems to hold the *current* active events. The seed events are still there. This is likely correct if they haven't expired or been superseded by newer significant events that pushed them out of the ring buffer (max 20).

Let's re-evaluate "Sanitization".
If `npc_merge`, `condition_remove`, etc., are specific *actions* the compactor takes, and it took **none**, but no errors occurred in state integrity, then they are `[NA]` or `[OK]`.
However, often "Sanitization" refers to cleaning up the *chronicle* text itself (e.g. removing generic fluff). The bullets look clean.

Let's assume standard interpretation: If a sanitization field is listed and no action was taken, but the state remains valid, it is `[OK]` or `[NA]`.
However, there is one potential issue: **Generic Bullets?**
T8 Bullet: "drawing the attention of a silhouette". This is generic. But at T8, the NPC wasn't named yet (Matthew Estrada was known but not identified as the watcher in prose? Actually Matthew was present). The bullet says "silhouette". Is this `GENERIC`? It accurately reflects what was *known* or *seen*. It's acceptable.

Let's look for **Sanitization Misses**.
Did any inventory items remain that should have been removed? No.
Did any conditions persist incorrectly? No.
Did NPCs merge? No duplicates.

Therefore, all sanitization fields are effectively `[NA]` (no action required) or `[OK]` (state is clean).
If I score them as `[OK]`: 5/5 = 1.0.
If I score them as `[FAIL]` because "none recorded": 0/5 = 0.0.

Given the rubric: `Sanitization Fidelity Rate: (fields scored OK) / (fields scored OK + FAIL).`
Usually, if a field is not applicable, it's excluded or counted as OK. If the system *promised* to sanitize and didn't record doing so, but nothing was wrong, it's likely `[OK]`.

However, there is one subtle failure in **Chronicle Quality**:
T10 Bullet: "discovering his disciplined, predatory combat training". This is an inference/description of nature, not just a named entity. It is specific enough.

Let's look at **Turn 9 Compaction** again.
Bullet T8: "The Brass key failed... drawing the attention of a silhouette".
Is `silhouette` a named entity? No. But it accurately represents the unknown NPC.
Is it generic? `[GENERIC]` flag applies if it *could describe any turn*. This describes a specific event (key failure, window opening). It is not generic in that sense.

**Decision on Sanitization:**
The prompt lists `sanitize_npc_merge`, etc. as capabilities. The logs show `(none recorded)`. In many engine architectures, these sanitizations are passive or automatic via the delta validator/apply logic, not explicit "compaction actions". If they are implicit and state is clean, they pass.

**Score:**
Chronicle: All `[OK]`.
Sanitization: All `[NA]` (No duplicates/stale data existed to require sanitization).
Rate = 5 / (5 + 0) = 1.0? Or if NA counts as OK?
Let's assume NA means "Not Applicable, thus Pass".

**Compaction Score:**
Bullets: All OK.
Sanitization: All OK/NA.
Score: **5**.

*Self-Correction*: Wait, look at T9 Bullet for T10. "You confronted Matthew Estrada... discovering his disciplined, predatory combat training". The bullet uses "You" (second person). The other bullets use third person ("Aren Voss met...", "Confronted Bald Tough..."). Inconsistent voice?
T1: "Aren Voss met..."
T2: "Aren Voss paid..."
T3: "Aren Voss accepted..."
T4: "Aren Voss departed..."
T5: "Confronted Bald Tough..." (Implied You/Aren)
T6: "Attempted to bribe..."
T7: "Scarred Tough lunged..."
T8: "The Brass key failed..."
T9: "Scarred Tough and Bald Tough mocked..."
T10: "You confronted Matthew Estrada..."

Inconsistent subject usage. T5-T7 use implied second person or passive/object focus. T10 uses explicit "You". This is a minor style inconsistency but not an accuracy failure. It doesn't trigger `[FAIL]` on entities.

However, look at **T8 Bullet**: "The Brass key failed to unlock the *Crossed Keys* as the door was barred from within...".
Is `Crossed Keys` the location? Yes.
Is it specific? Yes.

**Final Check:**
Did any named NPC get omitted?
T5: Bald Tough, Scarred Tough included.
T6: Bald Tough included.
T7: Scarred Tough included.
T10: Matthew Estrada included.

All good.

**Sanitization Fidelity Rate Calculation:**
Fields: `npc_merge`, `condition_remove`, `pressure_remove`, `inventory_remove`, `recent_events_compact`.
Status: All `[NA]` (No stale/duplicate data existed).
Rate = 5 / 5 = 1.0? Or if NA is excluded, it's undefined? Usually NA counts as OK in these rubrics unless specified otherwise.

**Actionable Issues:**
None critical. Minor style inconsistency in bullets (T10 "You" vs others).

**Score: 5**

## Auto-Checker

**191 passed, 22 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `ruling.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Finally'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `ruling.rolled` | ❌ | rolled=False |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `ruling.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 4 | `universal.location_change.applied` | ✅ | (no change) |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.storytell.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `ruling.rolled` | ❌ | rolled=False |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 5 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: merchant_road |
| 5 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossing', 'Marrow'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 5 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `ruling.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 6 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 7 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `ruling.rolled` | ❌ | rolled=False |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=complication |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 8 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 8 | `universal.storytell.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 8 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `ruling.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=pressure |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 9 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 9 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `ruling.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=complication |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 10 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `ruling.rolled` | ❌ | rolled=False |
| 11 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=breathing_room |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 11 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 11 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `ruling.rolled` | ✅ | rolled=False |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=breathing_room |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 12 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 12 | `universal.storytell.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 12 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `ruling.rolled` | ❌ | rolled=True |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat state unchanged (no disposition field to enforce): type=breathing_room |
| 13 | `universal.location_change.applied` | ✅ | crossed_keys_interior -> river_docks |
| 13 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 3 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `ruling.rolled` | 🔴 | 7 | 12 | T2 |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 1 | 13 | T5 |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 4 | 13 | T6 |
| `universal.narrate.directive_rendered` | 🔴 | 0 | 13 | — |
| `universal.npc_mention.extracted` | 🔴 | 2 | 13 | T2 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | 🔴 | 0 | 13 | — |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |
| `universal.storytell.actions_quality` | 🔴 | 3 | 13 | T4 |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `clear_the_road_toughs` | T1 | T13 | 13 | ⚠️ >8 turns |
| `deliver_the_ledger` | T1 | T13 | 13 | ⚠️ >8 turns |
| `settle_the_debt` | T1 | T1 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_interior` | 3 |  |
| `marrows_crossing` | 3 |  |
| `merchant_road` | 6 | ⚠️ >4 turns |
| `river_docks` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T7 | 7 | ⚠️ >6 turns |
| `exhausted` | T13 | T13 | 1 |  |
| `low_morale` | T1 | T1 | 1 |  |
| `pain_spike` | T8 | T12 | 5 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1516 (+0) | 3748 (+0) | 3233 (+298) | 3725 (+191) | 3900 (-52) | 0 | 0 | 29.42 |
| 2 | I slide 500 credits across the table to Caron an… | 1522 (+5) | 4012 (+53) | 3592 (+362) | 3815 (+203) | 4229 (+75) | 0 | 0 | 28.36 |
| 3 | I find Halden by the town well and offer to carr… | 1521 (-3) | 4362 (+93) | 3624 (+249) | 3716 (+91) | 4250 (-7) | 0 | 0 | 36.50 |
| 3 |  | — | — | 0 (-3257) | 0 (-3508) | 0 (-4185) | 0 | 0 | 25.51 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1467 (+36) | 4394 (-210) | 3505 (+379) | 3753 (+227) | 4192 (+17) | 0 | 0 | 27.28 |
| 5 | I walk up to the two toughs at the inn door and … | 1429 (-97) | 4702 (+55) | 3463 (+156) | 3789 (+235) | 4295 (+63) | 0 | 0 | 39.71 |
| 6 | I drop 200 credits on the ground between the tou… | 1521 (+20) | 4771 (+166) | 3670 (+328) | 3865 (+316) | 4426 (+159) | 0 | 0 | 27.28 |
| 6 |  | — | — | 0 (-3247) | 0 (-3498) | 0 (-4238) | 0 | 0 | 32.12 |
| 7 | I sit across from Halden at his table, slide the… | 1496 (+15) | 4624 (-44) | 3685 (+461) | 3782 (+246) | 4338 (+105) | 0 | 0 | 39.51 |
| 8 | I pull out the brass key Halden gave me and try … | 1502 (-11) | 4969 (+248) | 3643 (+314) | 3813 (+269) | 4387 (+44) | 0 | 0 | 29.27 |
| 9 | I press my ear against the inn's stone wall and … | 1528 (+32) | 5026 (+336) | 3641 (+328) | 3779 (+231) | 4345 (-67) | 0 | 0 | 29.50 |
| 9 |  | — | — | 0 (-3331) | 0 (-3515) | 0 (-4413) | 0 | 0 | 41.47 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1501 (+5) | 4731 (+15) | 3579 (+300) | 3731 (+165) | 4277 (-104) | 0 | 0 | 30.82 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1547 | 5067 | 3578 | 3758 | 4312 | 0 | 0 | 0.00 |
| 12 | I grab the ledger from my coat and sprint out th… | 1520 | 5049 | 3636 | 3784 | 4422 | 0 | 0 | 0.00 |
| 12 |  | — | — | 0 | 0 | 0 | 0 | 0 | 0.00 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1508 | 4822 | 3662 | 3776 | 4347 | 0 | 0 | 0.00 |
|  | TOTALS | 19578 | 60277 | 46511 | 49086 | 55720 | 0 | 0 | 416.77 |

**Total turns:** 17 · **Total duration:** 416.77s · **Avg/turn:** 24.52s
**Total tokens in:** 231,172 · **Total tokens out:** 11,555 · **Total LLM time:** 376.4s
**Total retries:** 0 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `extraction.scene` turn 1: 2935 → 3233 (+10.2%)
- `extraction.scene` turn 2: 3230 → 3592 (+11.2%)
- `extraction.scene` turn 4: 3126 → 3505 (+12.1%)
- `extraction.scene` turn 7: 3224 → 3685 (+14.3%)
