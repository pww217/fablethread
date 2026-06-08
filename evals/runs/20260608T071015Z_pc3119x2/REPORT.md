# Eval Report — `baseline`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-08T07:10:15.474641+00:00 · **Finished:** 2026-06-08T07:16:02.193707+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260608T071015Z_pc3119x2`  
**Track:** baseline  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260607T232654Z_9lpw9xv9/artifacts`
**Scoring philosophy:** aggregate quality (baseline)  

## Judge Summary

**Mechanical:** 1/5  
**Narrative:** 2/5  
**System Cohesion:** 1/5  
**Prompt Quality:** 3/5  
**State Fidelity:** 0.0%  
**Prompt Adherence:** 100.0%
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Domain judge breakdown:**

| Judge | Scores |
|---|---|
| `state_correctness` | extraction_accuracy_score=2, mechanic_lifecycle_score=1, state_fidelity_rate=15.0% |
| `narrative_interplay` |  |
| `prompt_pipeline` |  |

**[state_correctness trace](baseline.state_correctness.trace.md)** · **[state_correctness verdict](baseline.state_correctness.judge.md)**  
**[narrative_interplay trace](baseline.narrative_interplay.trace.md)** · **[narrative_interplay verdict](baseline.narrative_interplay.judge.md)**  
**[prompt_pipeline trace](baseline.prompt_pipeline.trace.md)** · **[prompt_pipeline verdict](baseline.prompt_pipeline.judge.md)**  
**[meta trace](baseline.meta.trace.md)** · **[meta verdict](baseline.meta.judge.md)**  


## Meta Judge Verdict

***
mechanical_score: 1
narrative_score: 2
system_cohesion_score: 1
prompt_quality_score: 3
state_fidelity_rate: 0.15
prompt_adherence_rate: 0.6
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | `(2 + 1) / 2 = 1.5` | **1** | The mechanic lifecycle is fundamentally broken (score 1). Momentum inversion and location delta failures prevent the core loop from functioning. Narrative score does not compensate for mechanical failure; if mechanics don't work, narrative cannot exist. Floor to 1. |
| `narrative_score` | narrative_interplay | N/A (No explicit numeric provided in summary, inferred from qualitative tags) | **2** | Qualitative evidence shows "inert_mechanic" (empty JSON), "false_resolution", and "npc_ghost". The system is producing inconsistent or non-existent narrative consequences. Score reflects severe degradation but acknowledges some turns may have partial output before crash/failure. |
| `system_cohesion_score` | narrative_interplay / state_correctness overlap | N/A | **1** | State correctness (0.15 fidelity) and Narrative interplay (inert mechanics, false resolutions) are mutually reinforcing failures. The system is incoherent: state changes don't persist, threads resolve without narration, and NPCs ghost. Total lack of cohesion between subsystems. |
| `prompt_quality_score` | prompt_pipeline | N/A (Qualitative tags only) | **3** | Prompts are functional enough to generate *some* output but suffer from severe inefficiency ("wasted_tokens", "bad_prompt" structures). They are not broken in structure, just bloated and poorly optimized. A moderate score reflects usability despite poor engineering. |
| `state_fidelity_rate` | state_correctness | 0.15 | **0.15** | Direct pass-through. Critical failures in location deltas (T4,8,10,12) and momentum inversion mean only ~15% of intended state changes are correctly applied/persisted. |
| `prompt_adherence_rate` | prompt_pipeline / narrative_interplay overlap | N/A | **0.6** | The "inert_mechanic" (empty JSON `{}` in T5,10) suggests the LLM is failing to adhere to output schema requirements or crashing mid-generation. However, other turns produce some extraction, suggesting partial adherence. 0.6 reflects significant but not total failure. |

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay (Inert Mechanics)**:
    - *Contradiction*: `narrative_interplay` flags T5/T10 as "inert_mechanic" because Storytell output is empty JSON `{}`. `state_correctness` does not explicitly flag these turns as extraction failures in the summary, but notes "Actions Extraction Null/Empty" for T5/T9.
    - *Resolution*: No contradiction. Both agree on failure. The narrative judge identifies the symptom (empty story), state judge identifies the root cause (null actions/extraction miss). They align: Mechanics failed to drive narrative because extraction failed.

- **state_correctness vs prompt_pipeline (Extraction)**:
    - *Contradiction*: `prompt_pipeline` rates prompts as "bad" but functional (Major/Minor tags), suggesting they are usable but inefficient. `state_correctness` reports critical failures in location deltas and momentum, implying the extraction or application logic is broken.
    - *Resolution*: The contradiction lies in scope. Prompt pipeline judges the *input* quality (bloated prompts). State correctness judges the *output/application* fidelity. A prompt can be "bad" (inefficient) but still produce correct output if the LLM follows it well. Here, however, we see both: bad prompts AND broken application logic (`_apply_delta` failure). The issue is not just prompt quality; it's engine implementation.

- **narrative_interplay vs state_correctness (Thread Resolution)**:
    - *Contradiction*: `state_correctness` says T12 thread resolution was ignored (extraction miss/merge step failed). `narrative_interplay` says T9/T10 had "false_resolution" where threads were removed from arc state but no narration occurred.
    - *Resolution*: These are distinct events. T12 is a technical failure to move data in state. T9/T10 is a narrative disconnect (state changed, story didn't). They reinforce the conclusion that thread lifecycle management is broken both technically and narratively.

- **state_correctness vs narrative_interplay (PacingContext)**:
    - *Contradiction*: `state_correctness` reports "Momentum Calculation Inversion" (dice bands mapped to wrong deltas). This implies PacingContext inputs are being calculated incorrectly by the engine, not that they were passed correctly.
    - *Resolution*: The narrative judge doesn't explicitly comment on momentum values, but notes "inert_mechanic". If momentum is inverted, pacing context signals (`outcome_hint`) sent to the Narrator would be wrong (e.g., sending `advance` when it should be `hold`). This explains why narration might feel disjointed or inert. The root cause is engine logic error in `_compute_pacing_context`.

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Broken**. Momentum calculation inversion (T4,7,11) means dice results are mapped to incorrect deltas (e.g., Crit Success = -1). This breaks the core pacing loop.
2. **GM beat narration** — **Degraded/Broken**. "Inert_mechanic" tags (T5,10) show Storytell outputting empty JSON `{}`. When mechanics fail, beats are silent or non-existent.
3. **Unified thread chains** — **Broken**. Threads resolve without narrative consequence ("false_resolution", T9/T10). Thread resolution logic fails to move data in state (T12). NPC threads disappear silently ("npc_ghost").
4. **Condition deduplication** — **Degraded**. "Condition Orphan Flags" indicate unknown conditions (`dusty`, `startled`) are causing scope violations or errors, suggesting the engine doesn't handle new/unknown condition tags gracefully.
5. **Arc thread progression** — **Broken**. Threads are removed from state without narration (T9/T10) or fail to move in state (T12). Progression is either invisible or technically stalled.
6. **Floor relief injection** — **Broken**. "Floor Relief Mechanism Failure" (T4,10) means `breathing_room` is not injected when `beat_locked=True`, leading to unbroken pressure cycles contrary to design.
7. **goal_update application** — **Degraded**. Not explicitly flagged as critical failure, but location deltas failing likely obscures goal context updates. If location doesn't update, visible goals tied to locations may become stale or invalid.
8. **recent_beats tracking** — **Unknown/Degraded**. With momentum and beat logic inverted/failing, recent beats history is likely corrupted or irrelevant. Cannot assess diversity impact.
9. **Inventory extraction accuracy** — **Degraded**. "Actions Extraction Null/Empty" (T5,9) suggests broader extraction instability. Inventory deltas may be affected if actions are null.
10. **Location change application** — **Broken**. Critical failure: Location deltas generated but not persisted to `state.location` (T4,8,10,12). This is a catastrophic engine bug breaking scene continuity.
11. **NPC mention extraction** — **Degraded**. "npc_ghost" tags indicate NPC lifecycle/location tracking is inconsistent. Silas Vance appears in conflicting locations; Victor Drax disappears silently. Extraction or state update for NPCs is failing.
12. **Storyteller pipeline** — **Broken**. Outputs empty JSON `{}` (T5,10) despite time/location advancing. This indicates a pipeline crash or silent failure where the Storytell LLM fails to produce valid thread/directive output.

### Trace Quality Assessment

1.  **Missing Data**: The trace lacks detailed logs of `_apply_delta` and `_compute_pacing_context` internal states. We see the *result* (wrong location, wrong momentum) but not the intermediate values that caused them.
2.  **Systematic Gap**: All judges note issues with **state persistence**. State changes are generated (deltas exist) but not applied or merged correctly into the final state object. This is a systemic failure in the engine's update loop (`_apply_delta`, merge steps).
3.  **Recommendation for Trace Improvement**: Add detailed logging of delta generation vs. application success/failure rates per turn. Specifically, log whether `_apply_delta` returned True/False and what the pre/post state values were for `location` and `momentum`.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Fix the location delta persistence bug (`_apply_delta` or `delta_builder.py`) to ensure generated deltas are correctly written to `state.location`, as this is a critical engine failure breaking scene continuity across multiple turns (T4,8,10,12) identified by state_correctness.**

### Key Findings
- **Critical Engine Bug**: Location deltas are generated but not persisted to `state.location` (Turns 4, 8, 10, 12), breaking scene continuity entirely. Source: `state_correctness`.
- **Momentum Inversion**: Dice bands are mapped to incorrect momentum deltas (e.g., Crit Success = -1) in `_compute_pacing_context`, corrupting the pacing loop (Turns 4, 7, 11). Source: `state_correctness`.
- **Narrative Stalling**: Storytell pipeline outputs empty JSON `{}` on Turns 5 and 10 despite time/location advancing, indicating a silent crash or schema failure. Source: `narrative_interplay`.
- **Thread Lifecycle Failure**: Threads resolve without narrative consequence ("false_resolution", T9/T10) or fail to move in state (T12), leaving players with unresolved plot points. Source: `state_correctness` & `narrative_interplay`.

### Regression Check
*Note: Previous run scores were not provided in the input.*
- **Assessment**: Without previous scores, regression cannot be calculated. However, the severity of "Critical" tags (Location Delta Failure, Momentum Inversion) suggests a significant degradation from any functional baseline. The system is currently non-functional for coherent gameplay due to state persistence failures.

## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 2 | success | +1 | 0 → 1 | — |
| 3 | success | +1 | 1 → 2 | — |
| 4 | setback | -1 | 2 → 1 | WRONG_DIR (State shows 1→2) |
| 5 | fail | 0 | 1 → 1 | FLAT (Rules say 1→0, State says 1→0 but momentum field diff shows 1->2 in T9 context? No, T5 state diff is missing. Let's look at T6 state diff: pc.momentum from 1 to 0. So T4 ended at 2? No, T4 Rules say 2->1. T5 Rules say 1->0. T6 State Diff says 1->0. This implies T4 actually resulted in momentum=2 (State diff for T9 shows prev 1 cur 2). | WRONG_DIR |
| 7 | crit_success | +2 | 1 → 3? | WRONG_DIR (Rules say 0→2, State diff T8 says 0→2) |
| 8 | fail | -1 | 2 → 1 | — |
| 9 | (empty input) | ? | ? | FLAT/MISSING |
| 11 | fail | +1 | 0 → 1 | WRONG_DIR (Rules say 1→0, State diff T12 says 1→0? No, T12 state diff shows pc.momentum from 1 to 0. Wait, T11 Rules say momentum_before=1, after=0. Delta -1. But Auto-Checker says prev=0 cur=1. Let's check T12 State Diff: `pc.momentum`: `from: 1`, `to: 0`. This contradicts the Auto-Checker which implies state was 0 before T11? Or maybe the diff is from T10->T11? No, diffs are vs previous turn. If T12 diff says 1->0, then T11 ended at 0. But Auto-Checker says `prev=0 cur=1`. This implies the state *after* T11 was 1. So Rules (1->0) contradicts State (ended at 1). | WRONG_DIR |

**Is momentum responding correctly?** No. The Rules output and Applied Deltas often contradict each other, or the State After Turn does not reflect the Rules outcome. Specifically, Turns 4, 7, and 11 show significant divergence between the calculated band delta and the resulting state value.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | pressure | npc_behavior | pressure | Storytell | Yes (expires T3) | — |
| T2 | complication | npc_behavior | complication | Storytell | Yes (expires T4) | — |
| T3 | complication | npc_behavior | complication | Storytell | Yes (expires T5) | — |
| T4 | complication | npc_behavior | breathing_room | Floor Relief? No, State shows `complication`. Auto-Checker says expected `breathing_room` because beat_locked=True. | N/A | FLOOR_RELIEF_MISS |
| T5 | null | null | breathing_room | Floor Relief (beat_locked from consecutive pressure) | Yes (expires T8) | — |
| T6 | revelation | environmental | revelation | Storytell | Yes (expires T8) | — |
| T7 | pressure | environmental | pressure? No, State shows `revelation` in diff? Wait. T7 Applied Deltas don't show beat change. T8 State Diff shows pending_gm_beat from `null` to `revelation`. This implies T6's revelation expired or was cleared? T5 injected breathing_room (expires T8). T6 emitted revelation (expires T8). They collide? Or did Storytell clear it? The diff at T8 says `from: null, to: {type: revelation}`. This suggests the beat from T6 was stored but maybe overwritten or the diff is misleading. Let's look at T7 State Diff: `pending_gm_beat`: `from: null, to: {type: revelation}`. So T6's beat persisted? No, T5 injected breathing_room (expires T8). If T6 emitted revelation, it should overwrite. But diff says `null -> revelation`. This implies the previous beat was gone. Did TTL expire? T5 expires at 8. Current turn 7. It shouldn't have expired. **OR** did Storytell emit null in T6? No, T6 output has `gm_beat: {type: revelation}`. Why is diff showing `null -> revelation`? Perhaps the previous beat (breathing_room) was popped because of a conflict or error? Or maybe the diff is from T5->T6 and I'm misreading indices. Let's assume standard flow: Storytell writes, Floor Relief checks. |
| T8 | complication | npc_behavior | pressure | Storytell | Yes (expires T10) | — |
| T9 | null | null | breathing_room | Floor Relief? State diff T10 shows `from: pressure, to: ambient/breathing_room`? No, T10 diff says `type: from: pressure, to: ambient`. Wait. T9 output is empty `{}`. So Storytell emitted nothing. beat_locked was True (consecutive_pressure_turns=3 at end of T8). Floor relief should inject breathing_room. State diff T10 shows `pending_gm_beat`: `from: {type: pressure...}, to: null`. This means the beat was popped/cleared, not replaced by floor relief? Or did it expire? Pressure expires T10 (T8+2). Current turn 9. It shouldn't have expired pre-narration. But diff shows `to: null`. Then at end of T9, if beat_locked, floor relief should inject. Diff doesn't show injection. | FLOOR_RELIEF_MISS / ORPHANED_BEAT_CLEAR |
| T10 | pressure | ambient | breathing_room? No, State diff T12 (skipped 11?) shows `from: null, to: {type: null}` in recent_beats? Wait. T10 output has `gm_beat: pressure`. Diff at T12 (which seems to be the snapshot for T11/12 block) is messy. Let's look at T11 State Diff: `pending_gm_beat`: `from: null, to: {type: breathing_room}`. This implies T10 emitted nothing or was cleared? But T10 output has pressure. | FLOOR_RELIEF_MISS / EXTRACTION_MISS |
| T12 | (empty) | null | null | Storytell (null) | N/A | — |

**Flags Analysis:**
- **T4**: `beat_locked=True` (consecutive_pressure_turns reached 3 at end of T3? No, T1=1, T2=?, T3=?). Auto-checker says beat_locked was True. Storytell emitted `complication`. Floor relief should have injected `breathing_room`. State shows `complication`. **FLOOR_RELIEF_MISS**.
- **T9**: Empty input/turn? Metrics show 0 tokens for Rules/Narrate/etc in one row, but another row has data. This looks like a duplicate or error entry in the trace logs provided (Turn 9 appears twice with different metrics). The first Turn 9 block has empty outputs `{}`. If Storytell emitted null and beat_locked was True, floor relief should fire. State diff T10 shows `pending_gm_beat` going to `null`. This suggests it was cleared but not replaced by relief? Or maybe the "pressure" from T8 expired at start of T9 (T8+2=10, so no). It persisted. Then Storytell emitted null -> popped. Floor relief should inject. Did not appear in state diff as injected beat. **FLOOR_RELIEF_MISS**.
- **NO_EXPIRY_TESTED**: TTL expiry logic seems broken or bypassed by the floor relief misses and location change resets (which purge beats? No, location changes don't purge beats).

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| 1-13 | None (Storytell output never contains `goal_update`) | "Clear your debts..." | "Clear your debts..." | N/A | — |

**Note:** The visible goal remains static throughout. No mid-arc pivots were attempted or extracted. This is acceptable if the story didn't require it, but no extraction misses here since none were emitted.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | None (active=false) | N/A | INERT |
| deliver_the_ledger | Seed | arc | normal | T4, T9, T10 updates | N/A | — |
| clear_the_road_toughs | Seed | arc | background | T2 update | N/A | INERT (active=false) |
| investigate_harker_disappearance | T5 | scene -> arc? | normal | T6, T7, T8, T10 updates | N/A | SCOPE_DRIFT (Seed was arc, Storytell added as scene?) |
| confront_predatory_rider | T9 | scene | urgent | T12 update (active=false) | N/A | — |
| harker_hat_connection | T10 | scene | normal | T13 resolve? No, T12 output has `thread_resolve` for this ID. | T12 | RESOLUTION_FAILED (State diff T13 shows thread still in threads[] with active=true) |

**Critical Failure at Turn 12:**
Storytell emitted `thread_resolve: [{id: "harker_hat_connection", ...}]`.
However, the **State After Turn 13** (which reflects post-T12 application) shows `threads` containing `harker_hat_connection` with `active: true`. It was NOT moved to `completed_threads`. The resolution signal was ignored or failed.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| dusty | T5 | State Extract | T6 (removed) | 2 turns | — |
| startled | T7 | State Extract | T9 (removed) | 3 turns? (T7->T8->T9). TTL was 2. **OVERLONG** or removed early? Removed at T9 diff. Added T7. Duration ~2-3 turns. Auto-checker flags `orphan` meaning no mod defined, not lifecycle error per se. | — |
| exposed | T10 (Trace says T9 in one block, T10 in another) | State Extract | T11 (removed) | 2 turns | — |
| relaxed | T13 | State Extract | N/A | Active at end | — |

**Auto-Checker `conditions.orphan`**: The checker flags conditions that have no entry in a hypothetical `CONDITION_MODS` config. This is an **extraction/schema issue**, not a lifecycle error, but it indicates the engine doesn't know how to modify stats for these conditions (likely 0 mod).

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 4 | Add | parchment_map | 1 | No | — |
| 8 | Add | dried_meat, water_canteen, rope | 1 each | No | — |
| 9 | Remove | dried_meat, water_canteen, rope | 1 each | **YES** (Auto-Checker: `remove_existence`) | SPENDING_MISS / EXTRACTION_FAIL |

**Analysis of Turn 9 Removal:**
State After T8 shows inventory includes `dried_meat`, etc.
Turn 9 Input is empty/ignored? Or the second Turn 9 block has input "I saddle up...". The first Turn 9 block (metrics 0) had empty outputs. The *second* Turn 9 block (metrics ~1600 tok_in) corresponds to the narrative where he buys supplies in T8 and then rides out in T9?
Actually, looking at the trace:
- **Turn 8**: Adds `dried_meat`, etc. State After T8 includes them.
- **Turn 9 (First block)**: Empty outputs. No deltas applied.
- **Turn 9 (Second block)**: Input "I saddle up...". Extract State says `inventory_remove`: dried_meat, water_canteen, rope. Applied Deltas include these removals.
- **Auto-Checker Failure T9**: `universal.inventory.remove_existence`. Why? Because the *State After Turn 8* diff (provided in the text) shows `inventory: added [...]` for those items. So they SHOULD exist.
Wait, look at **Turn 10 State Diff** (which is vs T9). It says `inventory: removed [...] dried_meat...`. This implies they were successfully removed from state *after* T9?
But the Auto-Checker failed on Turn 9. Why?
Ah, look at **Turn 9 Applied Deltas**: They include the removals.
Look at **State After Turn 10** (which is actually the snapshot for T10/T11 block in this messy trace). It shows `inventory: removed [...]`.
However, check **State After Turn 8**. Does it have them? Yes, diff says added.
Check **State After Turn 9**. The text doesn't provide a full "State After Turn 9" snapshot, only diffs for T10 and T12.
The Auto-Checker failure `remove_existence` on Turn 9 implies that at the moment of validation in Turn 9, the items were NOT found in state. This suggests they were added in T8 but *not persisted* or *lost* before T9's delta application? Or perhaps the "Turn 9" with empty outputs corrupted the state?
Actually, look at **State After Turn 10** diff: `inventory: removed [...]`. And `changed`: credits notes changed.
But look at **State After Turn 8** diff again. It adds them.
If T9 validation failed (`remove_existence`), they should NOT have been applied. But the final state (T13) does *not* show these items in inventory?
Final Inventory: `credits, iron_dagger, bandages, traveler_cloak, brass_key, parchment_map`. **Dried meat/canteen/rope are missing.**
So they were removed successfully from the narrative perspective, but the engine flagged it as an existence error. This is likely because the items were added in T8, but perhaps the `inventory_add` delta for T8 was rejected or not applied correctly? No, diff says "added".
Wait, look at **Turn 9 Input**: The *first* Turn 9 block has empty outputs and no deltas. If this turn ran as a "pass" with no state change, it's fine. But the *second* Turn 9 block (the real action) tried to remove items that existed in T8's post-state.
Why did Auto-Checker fail? `remove_existence`. This usually means the ID wasn't found. Did they have a different ID? Extract State used `id: dried_meat`. Seed/Previous state didn't define them, so they were added with `id: dried_meat`. It should match.
**Hypothesis**: The "Turn 9" empty block might have reset or skipped the persistence of T8's additions? Or the validation logic is buggy regarding newly added items in the same session if not properly merged? Given the final state lacks them, they were effectively removed/spent, but the engine flagged a validity error. This counts as an extraction/validation mismatch.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Location Drift**: The `location_change` emitted in Turns 4, 8, 10, and 12 was **not applied** to the state (Auto-Checker Failures).
    - T4: Emitted `dustfall_saloon`. State remained `marrows_crossing`.
    - T8: Emitted `weather_beaten_cabin`? No, T8 Extract Scene says `location_change: weather_beaten_cabin`. But Input was "head back to general store". The narrative/location extraction is hallucinating locations or the engine failed to apply them. State After T9 (diff) shows location changing from `assay_office` to `marrows_crossing_general_store`? No, diff says `from: assay_office, to: marrows_crossing_general_store`. This implies T8 *did* change it in some diffs but not others?
    - Let's look at **State After Turn 10** diff (vs T9). Location: `from: red_streaked_canyon_base, to: marrows_crossing_general_store`. This is a massive jump. The narrative flow was Saloon -> Assay Office -> Sheriff Station -> Cabin -> General Store -> Canyon Base Camp -> ?
    - The location IDs in the diffs are jumping around inconsistently with the "State After" snapshots provided for T1, T6, T8, T13.
    - **T1 State**: `marrows_crossing`.
    - **T4 Extract**: `dustfall_saloon`. **Auto-Checker says not applied**.
    - **T5 Extract**: `sheriffs_station`.
    - **T6 Extract**: `weather_beaten_cabin`.
    - **T8 Extract**: `marrows_crossing_general_store`? No, T8 Extract Scene says `location_change: marrows_crossing_general_store`. But Auto-Checker T8 says `location_change emitted but state.location.id unchanged: weather_beaten_cabin`. This implies the *previous* location was cabin, and it wasn't updated to store.
    - **T10 Extract**: `red_streaked_canyon_base`. Auto-Checker T12 (for this turn?) says `unchanged: red_streaked_canyon_base`? No, T12 diff shows change from `marrows_crossing_general_store` to `dustfall_outskirts`.
    - **Conclusion**: Location changes are frequently emitted but often fail to persist or apply correctly, leading to state drift where the narrative describes one place and the engine tracks another.

- **Inventory Coherence**: As noted in 1F, items added in T8 were flagged for removal existence error in T9, yet they disappear from final inventory. This is a "silent success" masked by an error flag, or a corruption where they existed briefly then vanished without proper accounting.

### 2B — Extraction Drift
- **Turn 4**: `location_change` extraction was correct (Saloon), but application failed. **Schema/Validation** issue in engine? Or just missed delta apply. Tag: `engine_bug`.
- **Turn 9**: `inventory_remove` existence check failure. The items existed in T8 state diff, so they should exist for T9 validation. This suggests the state loaded at start of T9 did not contain them (perhaps T8's save failed or was overwritten by an empty turn). Tag: `engine_bug`.
- **Turn 12**: `thread_resolve` signal emitted but thread remained active in state. Tag: `extraction_miss` (Storytell sent it, engine didn't apply) or `engine_bug` (apply logic skipped). Given the prompt says "resolved", and state shows active, this is a failure to process the storyteller's intent.

### 2C — State Fidelity Rate Calculation
Total Turns: 13 (excluding duplicate/empty metric rows for turns 5, 9, 10 which seem to be trace artifacts). Let's count unique narrative turns: 1-13 = 13 turns.

Failures per turn:
- T1: Momentum tracking error (Auto-checker). **Fail**.
- T2: Clean? No auto-failers listed for T2 in the table? Wait, T1 failure is `consecutive_pressure_tracking`. T4 has failures.
- T3: Clean?
- T4: Location not applied, Momentum delta wrong, Floor relief miss. **Fail**.
- T5: Actions quality (0 entries). **Fail**.
- T6: Condition orphan (cosmetic/missing mod). **Pass** for mechanics, but `orphan` is a config issue. Let's count as Pass for *state correctness* unless it breaks logic. However, Auto-checker lists it. I will count it as a Minor Fail or Pass? The prompt says "No extraction misses...". Orphan condition doesn't miss state, just lacks mod. **Pass**.
- T7: Momentum delta wrong, Pressure tracking fail. **Fail**.
- T8: Location not applied, Condition orphan. **Fail** (Location).
- T9: Actions quality, Remove existence error, Conditions orphan. **Fail**.
- T10: Location not applied, Floor relief miss, Actions quality, Conditions orphan. **Fail**.
- T11: Momentum delta wrong, Conditions orphan. **Fail**.
- T12: Location not applied (Auto-checker says `location_change emitted but state.location.id unchanged: red_streaked_canyon_base`? Wait, T10 Extract said Canyon Base. T12 Input is "Harker and I ride back...". Extract Scene says `dustfall_outskirts`. Auto-Checker T12 failure says location unchanged from Canyon Base. So it failed to apply the change to Outskirts. **Fail**.
- T13: Clean?

Passing Turns: 2, 3, 6 (maybe).
Total Passes: ~2/13 = 0.15.

Arithmetic: 2 / 13 ≈ 0.15.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 1 | `consecutive_pressure_tracking` | **True** | Storytell emitted `pressure`. Counter should be >= 1. State shows 0. Engine failed to increment counter on T1 beat application or initial state setup was wrong (Seed had 0). | `engine_bug` |
| 4 | `location_change.applied` | **True** | Delta applied but location field not mutated in state. Likely `_apply_delta` skipped location update or validation rejected it silently? No, no rejection listed. Bug in delta builder for location scope change. | `engine_bug` |
| 4 | `momentum.band_delta` | **True** | Rules said setback (-1). State went +1 (2->3? Or 1->2?). Momentum logic is broken or reading wrong prev value. | `engine_bug` |
| 4 | `floor_relief` | **True** | Beat locked, pressure emitted, no relief injected. Engine floor relief check failed to trigger override. | `engine_bug` |
| 5 | `actions_quality` | **True** | Storytell output had empty actions list (or null). Extraction pipeline accepted it but engine expects 4. | `extraction_miss` |
| 6 | `conditions.orphan` | **Noise/Config** | Condition exists, just no stat mod defined in config. Does not break state. | `scope_violation` (Missing Config) |
| 7 | `momentum.band_delta` | **True** | Rules said crit_success (+2). State went -1 (1->0). Momentum calculation is inverted or broken. | `engine_bug` |
| 7 | `consecutive_pressure_tracking` | **True** | Storytell emitted `pressure`. Counter reset to 0? Or failed to increment from T4/T5 state? T5 injected breathing_room, which should have reset counter. If T6 was null/relief, counter 0 is correct for end of T6? But failure says "gm_beat.type='pressure'... expected >=1". This implies the *current* turn's beat (T7) is pressure, but counter is 0 at start/check time? Or counter didn't increment from previous. | `engine_bug` |
| 8 | `location_change.applied` | **True** | Same as T4. Location delta emitted, state unchanged. | `engine_bug` |
| 8 | `conditions.orphan` | **Noise/Config** | See T6. | `scope_violation` |
| 9 | `actions_quality` | **True** | Empty actions again (in the second block). | `extraction_miss` |
| 9 | `inventory.remove_existence` | **True** | Items added in T8, removed in T9. Validation failed to find them. Suggests state persistence failure between T8 and T9 or ID mismatch. | `engine_bug` |
| 10 | `location_change.applied` | **True** | Same pattern. Location change emitted, not applied. | `engine_bug` |
| 10 | `floor_relief` | **True** | Beat locked (pressure streak), pressure emitted, no relief. | `engine_bug` |
| 10 | `actions_quality` | **True** | Empty actions? Or just missing from diff? T10 output has actions. Auto-checker says "has 0 entries". Maybe the *first* Turn 9 block's empty state carried over or confused the checker for T10? No, T10 is distinct. Check T10 Storytell Output: It HAS actions. Why did checker fail? Perhaps it checked the *previous* turn's result stored in context? Or the "Turn 9" duplicate entry corrupted the check buffer. | `checker_noise` (Likely due to trace duplication) |
| 12 | `location_change.applied` | **True** | Location change emitted, not applied. | `engine_bug` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
- **Reason**: Repeated extraction failures (Actions quality on T5, T9). Critical state corruption in inventory handling (T9 remove existence) and location tracking (multiple turns). The engine is failing to apply basic deltas from the Storytell and Scene extractors.

### Mechanic Lifecycle Score: 1/5
- **Reason**: Momentum lifecycle is broken (wrong direction/values on multiple turns). Beat lifecycle has repeated `FLOOR_RELIEF_MISS` flags, meaning the pressure relief mechanism is not functioning as designed. Thread resolution failed to move a thread to completed status despite explicit signal. Location changes are systematically ignored by the state engine.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Location Delta Application Failure** (Turns: 4, 8, 10, 12) — Tag: `engine_bug`. Fix: Inspect `_apply_delta` or `delta_builder.py` for location updates. The delta is generated but not persisted to `state.location`. This breaks scene continuity entirely.
- **Momentum Calculation Inversion** (Turns: 4, 7, 11) — Tag: `engine_bug`. Fix: Debug `_compute_pacing_context` or momentum update logic. Dice bands are being mapped to incorrect delta values (e.g., Crit Success applying -1).

**Major**
- **Floor Relief Mechanism Failure** (Turns: 4, 10) — Tag: `engine_bug`. Fix: The engine fails to inject `breathing_room` when `beat_locked=True` and a pressure beat is emitted. This causes unbroken pressure cycles contrary to design intent.
- **Thread Resolution Ignored** (Turn: 12) — Tag: `extraction_miss`. Fix: `_apply_thread_resolutions()` or the merge step for T12 failed to move `harker_hat_connection` from active threads to completed_threads despite explicit `thread_resolve` output.

**Minor**
- **Actions Extraction Null/Empty** (Turns: 5, 9) — Tag: `extraction_miss`. Fix: Storytell LLM is occasionally returning empty/null actions lists. Validation should reject or default to placeholder if <4 actions are emitted.
- **Condition Orphan Flags** (Turns: 6, 8, 9, 10, 11) — Tag: `scope_violation`. Fix: Add entries for `dusty`, `startled`, `exposed`, `relaxed` to the engine's `CONDITION_MODS` configuration or ensure they default to 0 mod without erroring.

## Judge Verdict — `narrative_interplay`

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit

- **Silas Vance:** Introduced at Assay Office (T4). Reappears as General Store Clerk in T8. *Flag:* `NPC_GHOST` / `COHERENCE_ERROR`. Silas was an Assay Clerk, now a General Store Clerk? The bio changes from "ink-stained fingers... spectacles" to "wiry man with ink-stained fingers". It's the same NPC model reused incorrectly or hallucinated as two roles.
- **Victor Drax:** Introduced in T8 (General Store). Disappears after T9 without resolution, thread deleted in T10 state diff while PC is at Canyon Camp. *Flag:* `NPC_GHOST`.

### 2B — Player Intent Fidelity

- **T6 Input:** "The sheriff gives me Harker's cabin key."
    - **Narration:** "You reach toward the desk... Kaelen Vance doesn't move to assist you... 'I don't have any keys'..."
    - **Verdict:** `BROKEN`. The player stated a fact ("Sheriff gives me key"). The engine rejected it as impossible/improbable and narrated a refusal, *but* the Rules output said `rolled: false` (impossible check?). However, the narration contradicts the user's explicit action statement. In TRPG engines, if an action is declared, the GM usually accepts or rolls against it, but outright denying "The sheriff gives me..." without a roll or negotiation attempt is a violation of intent fidelity unless `impossible=true` was set (which Rules output didn't explicitly show for T6, just empty JSON). *Correction:* Looking at T6 Rules: `intent_verb: sneak`. This implies the engine misclassified "gives me key" as sneaking? Or perhaps the user input in T6 was interpreted as trying to take a key they don't have. The narration says "reach toward... hand outstretched to claim a key that isn't there." This suggests the engine thought the player *tried* to grab a non-existent key, rather than accepting the gift. This is an `INTENT_REDIRECT`.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing:** T1-T4 High (Saloon tension, Silas hostility). T5 Low (Sheriff indifference). T6 Med (Cabin atmosphere). T7 High (Scraping sound). T8 Med/High (Riders arrive). T9 Very High (Victor Drax confrontation).
- **Momentum arc:** Broken by state corruption. Momentum jumps from 2 to 1, then 0, then 2, then 1, then 0. No discernible arc due to turn numbering and location resets in the trace data.
- **Beat type variety:** Pressure, Complication, Breathing Room, Revelation. Good variety when firing.
- **Intent verb variety:** `transition`, `persuade`, `sneak`. Low variety. `Sneak` used for entering a cabin with a key and prying open a box? Misclassification by Ruling step.

---

## SECTION 4 — Scores

### Narrative Score: 2/5
The narration is competent prose, but it frequently ignores or contradicts player intent (T6) and mechanic beats (T8). The state corruption in the trace (Turns 5, 10 having empty outputs while advancing time/location) suggests severe mechanical failures that would result in disjointed storytelling for a player.

### System Cohesion Score: 2/5
The engine fails to maintain continuity between turns. Threads are deleted without narrative resolution (`confront_predatory_rider`). NPCs change roles (Silas). The "Empty JSON" outputs for Turns 5 and 10 indicate pipeline failures that break the mechanic→narrative chain entirely.

---

## SECTION 5 — Actionable Issues

- **<Description>** (turns: 6, 8) — Tag: `intent_redirect`. Fix: Ruling step misclassifies "Sheriff gives key" as `sneak`/impossible grab instead of accepting the gift or rolling for persuasion. The engine must respect declarative actions unless truly impossible.
- **<Description>** (turns: 8, 9) — Tag: `npc_ghost`. Fix: Silas Vance appears in two different locations with conflicting titles (Assay Clerk vs General Store Clerk). Victor Drax disappears without resolution while the thread is silently deleted from state. Ensure NPC lifecycle and location tracking are consistent.
- **<Description>** (turns: 5, 10) — Tag: `inert_mechanic`. Fix: Storytell output is empty JSON `{}` for these turns, yet time/location advances in subsequent diffs. This indicates a pipeline crash or silent failure where mechanics do not drive narrative consequence.
- **<Description>** (turns: 9, 10) — Tag: `false_resolution`. Fix: Thread `confront_predatory_rider` is removed from arc state but no narration resolves the confrontation with Victor Drax. The player was left in limbo between a store and a canyon camp without narrative closure for that threat.

## Judge Verdict — `prompt_pipeline`

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains only turn-variable data (`state.pc`, `location`, `recent_turns[-1:]`, `user_input`). No instruction text in user prompt. |
| P2 | Y | Inputs are precisely what the ruling pipeline needs: PC stats, location context, last narrative for continuity, and current input. |
| P3 | PARTIAL | The `recent_turns[-1:]` block is duplicated from chronicle.md into every stream (narrate, scene, state, storytell). This is intentional per design (`load_last_narration()`), but it creates redundancy across 5 streams. Estimated ~400 tokens/turn wasted in non-narrate streams if they don't need the full prose. |
| P4 | Y | Schema section defines JSON structure only. Guidance sections (Decision rule, Anti-declare-outcome) provide behavioral direction without overlap. |
| P5 | PARTIAL | Minor ambiguity: "Pick the single most consequential or uncertain action" vs "If individually trivial sub-actions compound... classify as ONE harder check." The LLM sometimes struggles to distinguish between a compound action and multiple actions in one turn, but no direct contradiction exists. |
| P6 | Y | Instructions are concise. No multi-sentence explanations reducible to one. Rules are numbered/bulleted for priority. |
| P7 | Y | Sections clearly delimited with `##`. Priority rules (Anti-declare-outcome) are explicit. JSON schema is distinct from guidance text. |
| P8 | PASS | The LLM followed instructions in all 13 turns. It correctly classified intents, handled impossibility checks (T6, T9), and adhered to the anti-declare rule by not letting player prose dictate success/failure outcomes directly, instead classifying difficulty based on intent. |
| P9 | N | No failure modes observed that would benefit from few-shot examples. The LLM's classification logic is sound across all turns. |

**Remediation summary:**
- **Redundancy in `recent_turns`:** While intentional for narrative continuity, the full prose narration is fed to Rules, Scene, State, and Storytell extractors. For Rules/Scene/State, only a brief summary or key facts are needed. *Change:* Pass a summarized version of recent turns (e.g., last 2-3 sentences) to non-narrate pipelines. *Outcome:* Reduce token waste by ~400 tokens/turn across 3 extractors.

### 1B — Narrate Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains turn-variable data (`state`, `prior_history`, `recent_turns[-1:]`, `pacing_context`, `pending_gm_beat`). No instruction text in user prompt. |
| P2 | Y | Inputs are rich but justified: full state, history, pacing context, and GM beat provide the necessary creative fuel for prose generation. |
| P3 | PARTIAL | Same redundancy as Rules: `recent_turns[-1:]` (full narration) is included here, which is appropriate, but it also appears in other streams unnecessarily. |
| P4 | Y | Schema/Output discipline section defines format only. Guidance sections (Player input truth, Inventory rules, NPC behavior) provide behavioral direction without overlap. |
| P5 | N | No contradictions found. Priority ordering (`player input > GM beat > pacing directive`) is clear and consistently followed. |
| P6 | Y | Instructions are terse but comprehensive. "Hard ceiling: 250 words" is a single, clear constraint. |
| P7 | Y | Sections clearly delimited with `##`. Priority rules numbered/bulleted. JSON schema not applicable (prose output), but formatting instructions for markdown are explicit. |
| P8 | PASS | The LLM followed all system prompt rules in all 13 turns. It adhered to the 250-word ceiling, used second person, avoided listing choices, and correctly integrated GM beats as environmental pressure without replacing player actions (e.g., T6 impossible action narration). |
| P9 | N | No failure modes observed. The LLM's prose generation is high-quality and adheres strictly to constraints. |

**Remediation summary:**
- **Redundancy in `recent_turns`:** Same as above. *Change:* Pass summarized recent turns to other pipelines, not just Narrate (which needs full context). *Outcome:* Token savings without affecting narration quality.

### 1C — Extract Scene Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains turn-variable data (`narrative`, `location`, `compendium`, `recent_turns[-1:]`). No instruction text in user prompt. |
| P2 | PARTIAL | The pipeline receives `state.pc` and `conditions` which are not strictly necessary for scene extraction (tags, location change, NPC presence). However, they provide context for NPC interactions. *Minor* excess input. |
| P3 | Y | Same redundancy as other pipelines regarding `recent_turns[-1:]`. No cross-pipeline block duplication beyond this design-wide issue. |
| P4 | Y | Schema section defines JSON structure only. Guidance sections (Field rules, NPC ID rules) provide behavioral direction without overlap. |
| P5 | N | No contradictions found. Rules for `location_change` vs `location_description` are clear and distinct. |
| P6 | PARTIAL | The "Bio and notes examples" section is verbose but necessary to prevent generic bios. However, the "NPC ENTER/EXIT RULE (MANDATORY)" could be condensed into a single bullet point without losing intent. *Specific passage:* The 3 example blocks for bio extraction are redundant with the preceding text description of what makes a good/bad bio. |
| P7 | Y | Sections clearly delimited with `##`. Priority rules numbered/bulleted. JSON schema is distinct from guidance text. |
| P8 | PASS | The LLM followed all system prompt rules in all 13 turns. It correctly emitted location changes, updated NPC presence, and adhered to the "no ambient presence when named NPCs are present" rule (e.g., T1). |
| P9 | N | No failure modes observed that would benefit from few-shot examples. The LLM's extraction logic is sound across all turns. |

**Remediation summary:**
- **Redundancy in `recent_turns`:** Same as above. *Change:* Pass summarized recent turns to Scene extractor. *Outcome:* Token savings without affecting scene extraction accuracy.
- **Verbose Bio Examples:** Condense the 3 example blocks into a single, tighter rule set. *Change:* Replace examples with concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.

### 1D — Extract State Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains turn-variable data (`narrative`, `inventory`, `conditions`). No instruction text in user prompt. |
| P2 | PARTIAL | The pipeline receives `player_intent` which is not strictly necessary for state extraction (it should be grounded solely in narration). However, it provides context for *why* an item might change hands. *Minor* excess input. |
| P3 | Y | Same redundancy as other pipelines regarding `recent_turns[-1:]`. No cross-pipeline block duplication beyond this design-wide issue. |
| P4 | Y | Schema section defines JSON structure only. Guidance sections (Narration is sole authority, ID rules) provide behavioral direction without overlap. |
| P5 | N | No contradictions found. Rules for inventory add/remove/update are clear and distinct. |
| P6 | PARTIAL | The "Stat-to-condition heuristics" section could be condensed into a single bullet point per heuristic type. *Specific passage:* The 4 example conditions (Combat failure, Failed wits, etc.) are redundant with the preceding text description of when to add conditions. |
| P7 | Y | Sections clearly delimited with `##`. Priority rules numbered/bulleted. JSON schema is distinct from guidance text. |
| P8 | PASS | The LLM followed all system prompt rules in all 13 turns. It correctly emitted inventory changes (T8, T9), condition adds/removes (T5, T6, T7, T12, T13), and adhered to the "no change if not confirmed" rule. |
| P9 | N | No failure modes observed that would benefit from few-shot examples. The LLM's extraction logic is sound across all turns. |

**Remediation summary:**
- **Redundancy in `recent_turns`:** Same as above. *Change:* Pass summarized recent turns to State extractor. *Outcome:* Token savings without affecting state extraction accuracy.
- **Verbose Condition Heuristics:** Condense the 4 example conditions into a single, tighter rule set. *Change:* Replace examples with concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.

### 1E — Storyteller Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains turn-variable data (`narrative`, `extraction_context`, `pacing_context`, `arc.threads[]`). No instruction text in user prompt. |
| P2 | PARTIAL | The pipeline receives `rules_outcome` which is not strictly necessary for thread/beat management (it should be grounded solely in narrative events). However, it provides context for *how* to interpret success/failure. *Minor* excess input. |
| P3 | Y | Same redundancy as other pipelines regarding `recent_turns[-1:]`. No cross-pipeline block duplication beyond this design-wide issue. |
| P4 | Y | Schema section defines JSON structure only. Guidance sections (Threads, Arc resolution, GM Beat) provide behavioral direction without overlap. |
| P5 | N | No contradictions found. Rules for thread operations vs arc resolution are clear and distinct. |
| P6 | PARTIAL | The "Directive-Beat Alignment" table is redundant with the preceding text description of beat types. *Specific passage:* The 2 tables (Pacing directive, Roll band) could be merged into a single decision matrix without losing intent. |
| P7 | Y | Sections clearly delimited with `##`. Priority rules numbered/bulleted. JSON schema is distinct from guidance text. |
| P8 | PASS | The LLM followed all system prompt rules in all 13 turns. It correctly emitted thread updates, GM beats, and actions adhering to the "exactly 4 choices" rule (e.g., T1). It also respected pacing directives (T6 impossible action resulted in null beat/pressure as appropriate). |
| P9 | N | No failure modes observed that would benefit from few-shot examples. The LLM's extraction logic is sound across all turns. |

**Remediation summary:**
- **Redundancy in `recent_turns`:** Same as above. *Change:* Pass summarized recent turns to Storytell extractor. *Outcome:* Token savings without affecting storytell accuracy.
- **Verbose Beat Alignment Tables:** Merge the 2 tables into a single decision matrix. *Change:* Replace separate tables with one consolidated "Beat Selection Guide" table. *Outcome:* Reduce prompt size by ~150 tokens without losing guidance quality.

---

## SECTION 2 — Mechanic Ownership Check

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `thread_update`, `thread_resolve`, `thread_add` (gated) | storytell |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | storytell |
| `goal_update` | storytell |
| `gm_beat` | storytell |
| `actions`, `outcome_summary` | storytell |

**List any misplaced mechanics:** None. All mechanics were emitted by the correct stream in all 13 turns.

---

## SECTION 3 — Cross-Pipeline I/O Relevance

### Rules: inputs should be limited to pc, location, conditions, last_outcome, meta.turn, user_input.
- **Assessment:** Inputs are focused. `recent_turns[-1:]` is the only excess input (full narration). *Flag:* Full narration in T1-T13 is unnecessary for ruling; a summary would suffice.

### Narrate: richest inputs are justified — assess whether every input contributes. Flag inputs the narrator clearly doesn't use.
- **Assessment:** All inputs contribute to prose generation. `prior_history` provides continuity, `pacing_context` shapes tone, `pending_gm_beat` adds pressure. No unused inputs detected.

### Extract Scene: should receive narrative, pc/location, npc_roster (from build_npc_roster()), conditions, compendium entries, rules_outcome. Flag if it receives inventory or arc thread data.
- **Assessment:** Inputs are focused. `state.pc` and `conditions` provide context for NPC interactions but are not strictly necessary. *Flag:* Minor excess input (`pc`, `conditions`).

### Extract State: should receive narrative, pc, inventory, rules_outcome, band. Flag if it receives arc thread data, recent_events, or pressure data.
- **Assessment:** Inputs are focused. `player_intent` provides context but is not strictly necessary. *Flag:* Minor excess input (`player_intent`).

### Storyteller: richest extractor — assess whether every input enables a specific output. Flag inputs that appear unused. Should receive: narrative, band, PacingContext (full struct), arc.threads[] (unified), recent_turns, recent_beats, pending_gm_beat. Outputs include: thread_update/thread_resolve/thread_add, gm_beat, goal_update, actions, outcome_summary.
- **Assessment:** All inputs contribute to storytell decisions. `rules_outcome` helps interpret success/failure for beat selection. *Flag:* Minor excess input (`rules_outcome`).

**Pacing Context Usage:** The PacingContext is used by the Storyteller pipeline in all turns where it was emitted (T4, T6, T8, T10). The LLM correctly adjusted GM beats based on directives (e.g., T6 impossible action resulted in null beat/pressure as appropriate).

---

## SECTION 4 — Prompt Redundancy Analysis

### Top overlaps across all turns
| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + storytell | 38 | `### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~ / - `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-c / - `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halde` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

### Analysis
1. **Narration fed to all extractors:** This is intentional per design (`narrative: str` flows from Step 1 to Steps 2a/2b/2c). The duplication in `recent_turns[-1:]` (full narration) across Rules, Scene, State, and Storytell pipelines is also by design for continuity. However, only Narrate *needs* the full prose; other pipelines need summaries or key facts.
2. **Unintentional redundancy:** None detected beyond the design-wide `recent_turns[-1:]` duplication.

### Top 3 dedup opportunities — concrete remediations only
1. **Summarize `recent_turns[-1:]` for non-narrate pipelines.** *Change:* Pass a 2-3 sentence summary of recent turns to Rules, Scene, State, and Storytell extractors instead of full narration. *Outcome:* Reduce token waste by ~400 tokens/turn across 3 streams (Scene, State, Storytell).
2. **Condense Bio Examples in Extract Scene.** *Change:* Replace the 3 example blocks with concise "Do/Don't" bullets for bio extraction. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
3. **Merge Beat Alignment Tables in Storyteller.** *Change:* Combine the Pacing Directive and Roll Band tables into a single decision matrix. *Outcome:* Reduce prompt size by ~150 tokens without losing guidance quality.

---

## SECTION 5 — Prompt Adherence Rate

| Pipeline | Total Turns | PASS Instances | FAIL Instances |
|----------|-------------|----------------|----------------|
| Rules    | 13          | 13             | 0              |
| Narrate  | 13          | 13             | 0              |
| Scene    | 12*         | 12             | 0              |
| State    | 12*         | 12             | 0              |
| Storytell| 12*         | 12             | 0              |

*\*Turns 5 and 9 had no extractor calls (empty input).*

**Total PASS instances:** 62/65 = **0.9538461538461539**
*(Note: The prompt adherence rate in YAML front matter is calculated as `total PASS / (5 pipelines × N turns)`. With 13 turns, but only 12 extractor calls per pipeline due to empty inputs on T5/T9, the denominator is effectively 65. If we count all 13 turns for Rules/Narrate and 12 for extractors, it's 62/65.)*

**Correction:** The prompt asks for `(total PASS instances) / (5 pipelines × N turns)`. With 13 turns:
- Rules: 13/13
- Narrate: 13/13
- Scene: 12/13 (T5, T9 skipped)
- State: 12/13 (T5, T9 skipped)
- Storytell: 12/13 (T5, T9 skipped)

Total PASS = 62. Total possible = 65. Rate = **0.9538461538461539**.

*(Note: The initial calculation of 0.9615 was based on a different interpretation. This is the correct rate given skipped turns.)*

---

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
- **Rules:** 4/5 — Strong adherence, minor ambiguity in compound action classification.
- **Narrate:** 5/5 — Perfect adherence, high-quality prose generation within constraints.
- **Extract Scene:** 4/5 — Good adherence, verbose bio examples reduce efficiency.
- **Extract State:** 4/5 — Good adherence, verbose condition heuristics reduce efficiency.
- **Storyteller:** 4/5 — Good adherence, redundant beat alignment tables reduce efficiency.

### Prompt Quality Score (1–5)
**Score: 4/5**

**Worst prompt architecture:** Extract Scene and Extract State share the worst issue: verbose examples that could be condensed without losing guidance quality. This reduces token efficiency across all turns.

**Highest-priority fix:** Summarize `recent_turns[-1:]` for non-narrate pipelines. This is a design-wide redundancy affecting 3 out of 5 pipelines, resulting in significant token waste (~400 tokens/turn per stream). Fixing this would improve efficiency without altering prompt logic or guidance quality.

---

## SECTION 7 — Actionable Issues

### Critical
- **<description>** (pipeline: Rules/Narrate/Scene/State/Storytell, turns: T1-T13) — Tag: `wasted_tokens`. Fix: Pass summarized recent turns to non-narrate pipelines instead of full narration. *Outcome:* Reduce token waste by ~400 tokens/turn across 3 streams (Scene, State, Storytell).

### Major
- **<description>** (pipeline: Extract Scene, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Bio Examples into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Extract State, turns: T1-T12) — Tag: `bad_prompt`. Fix: Condense Condition Heuristics into concise "Do/Don't" bullets. *Outcome:* Reduce prompt size by ~100 tokens without losing guidance quality.
- **<description>** (pipeline: Storyteller, turns: T1-T12) — Tag: `bad_prompt`. Fix: Merge Beat Alignment Tables into a single decision matrix. *Outcome:* Reduce prompt size by ~150 tokens without losing guidance quality.

### Minor
- **<description>** (pipeline: Extract Scene/State/Storytell, turns: T1-T12) — Tag: `cross_pipeline_redundancy`. Fix: Remove unnecessary inputs (`state.pc`, `conditions` for Scene; `player_intent` for State; `rules_outcome` for Storytell). *Outcome:* Reduce token waste by ~50 tokens/turn per stream.

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**282 passed, 28 failed**

> **Legend:** `[PASS]` = assertion passed · `[FAIL]` = assertion failed  
| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | [PASS] | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | [PASS] | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 1 | `universal.location_change.applied` | [PASS] | (first turn) |
| 1 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 1 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 1 | `universal.inventory.no_overdraw` | [PASS] | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 1 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 1 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 1 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 1 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 1 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 1 | `universal.inventory.remove_existence` | [PASS] | (first turn) |
| 1 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 1 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 1 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 2 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 2 | `universal.location_change.applied` | [PASS] | (no change) |
| 2 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 2 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | [PASS] | band=success delta=0 (expected +1, engine may clamp) |
| 2 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=1 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 2 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 2 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 2 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 2 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 2 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 3 | `ruling.rolled` | [FAIL] | rolled=True |
| 3 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 3 | `universal.location_change.applied` | [PASS] | (no change) |
| 3 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 3 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | [PASS] | band=success delta=1 (expected +1, engine may clamp) |
| 3 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'hold' rendered in narrate prompt |
| 3 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=2 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 3 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 3 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 3 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | [FAIL] | beats are 67% 'complication' (threshold: 60%): {'pressure': 1, 'complication': 2} |
| 3 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 4 | `ruling.rolled` | [PASS] | rolled=True |
| 4 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 4 | `universal.location_change.applied` | [FAIL] | location_change emitted but state.location.id unchanged: dustfall_saloon |
| 4 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 4 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | [FAIL] | band=setback expected delta -1 but got +1 (prev=1 cur=2) |
| 4 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | [PASS] | directive 'Scene Pressure; Resolve a Threat' rendered in storytell prompt |
| 4 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=3 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=2, floor=-3) |
| 4 | `universal.pacing.floor_relief` | [FAIL] | beat_locked=True, storytell_type='complication' but pending_gm_beat.type='complication' (expected 'breathing_room') |
| 4 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 4 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 4 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | [FAIL] | beats are 100% 'complication' (threshold: 60%): {'complication': 3} |
| 4 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 5 | `ruling.rolled` | [FAIL] | rolled=False |
| 5 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 5 | `universal.location_change.applied` | [PASS] | dustfall_saloon -> assay_office |
| 5 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 5 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 5 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 5 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 5 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 5 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 5 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 5 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 5 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 5 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 5 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 6 | `ruling.rolled` | [PASS] | rolled=False |
| 6 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 6 | `universal.location_change.applied` | [PASS] | (no change) |
| 6 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 6 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 6 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 6 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 6 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 6 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 6 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 6 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 6 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 6 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 6 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 6 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 6 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 7 | `ruling.rolled` | [FAIL] | rolled=False |
| 7 | `extract.state.inventory_add` | [FAIL] | inventory_add[torn_map] not found |
| 7 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 7 | `universal.location_change.applied` | [PASS] | weather_beaten_cabin -> sheriffs_station |
| 7 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 7 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 7 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 7 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 7 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='revelation', counter=0 |
| 7 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 7 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 7 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 7 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 7 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 7 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['dusty'] |
| 7 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | [PASS] | only 1 beat(s) in window (need >= 3) |
| 7 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 8 | `extract.state.inventory_remove` | [FAIL] | inventory_remove[credits] not found |
| 8 | `universal.pending_gm_beat.consumed` | [PASS] | (no prior beat) |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=revelation |
| 8 | `universal.location_change.applied` | [PASS] | (no change) |
| 8 | `universal.narrate.binding_present` | [PASS] | binding directive included |
| 8 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | [FAIL] | band=crit_success expected delta +2 but got -1 (prev=1 cur=0) |
| 8 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'advance' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 8 | `universal.pacing.consecutive_pressure_tracking` | [FAIL] | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 8 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 8 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 8 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 8 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 8 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 9 | `ruling.rolled` | [PASS] | rolled=False |
| 9 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 9 | `universal.location_change.applied` | [FAIL] | location_change emitted but state.location.id unchanged: weather_beaten_cabin |
| 9 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 9 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 9 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 9 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 9 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='complication', counter=1 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 9 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 9 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 9 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 9 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 9 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['startled'] |
| 9 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | [PASS] | beat variety OK: {'revelation': 1, 'pressure': 1, 'complication': 1} |
| 9 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 10 | `ruling.rolled` | [FAIL] | rolled=False |
| 10 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 10 | `universal.location_change.applied` | [PASS] | (no change) |
| 10 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 10 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 10 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 10 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 10 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 10 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=1, floor=-3) |
| 10 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 10 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 10 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 10 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 10 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['exposed'] |
| 10 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 10 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 11 | `extract.state.pc_condition_remove` | [FAIL] | pc_condition_remove[bruised_ribs] not found |
| 11 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=complication |
| 11 | `universal.location_change.applied` | [PASS] | (no change) |
| 11 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 11 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 11 | `universal.inventory.no_overdraw` | [PASS] | checked 3 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 11 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 11 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=2 |
| 11 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=2, floor=-3) |
| 11 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 11 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 11 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 11 | `universal.inventory.remove_existence` | [FAIL] | removed non-existent item(s): ['dried_meat', 'water_canteen', 'rope'] |
| 11 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 11 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['startled'] |
| 11 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 11 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 12 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat present but source unclear: type=pressure |
| 12 | `universal.location_change.applied` | [FAIL] | location_change emitted but state.location.id unchanged: marrows_crossing_general_store |
| 12 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 12 | `universal.storytell.actions_quality` | [PASS] | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 12 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | [PASS] | outcome_hint 'transition' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | [PASS] | directive 'Pressure; Resolve a Threat' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type='pressure', counter=3 |
| 12 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=True (momentum=1, floor=-3) |
| 12 | `universal.pacing.floor_relief` | [FAIL] | beat_locked=True, storytell_type='pressure' but pending_gm_beat.type='pressure' (expected 'breathing_room') |
| 12 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 12 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | [PASS] | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | [PASS] | all conditions have CONDITION_MODS entries |
| 12 | `universal.thread_add.applied` | [PASS] | all thread_add signals produced state mutations |
| 12 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |
| 13 | `universal.pending_gm_beat.consumed` | [PASS] | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | [PASS] | beat consumed (cleared) - no gm_beat emitted this turn |
| 13 | `universal.location_change.applied` | [PASS] | (no change) |
| 13 | `universal.narrate.binding_present` | [PASS] | (no roll) |
| 13 | `universal.storytell.actions_quality` | [FAIL] | actions has 0 entries (expected 4) |
| 13 | `universal.momentum.band_delta` | [PASS] | (no roll) |
| 13 | `universal.inventory.no_overdraw` | [PASS] | checked 0 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | [PASS] | (no outcome_hint computed) |
| 13 | `universal.storytell.directive_rendered` | [PASS] | (no directive computed) |
| 13 | `universal.pacing.consecutive_pressure_tracking` | [PASS] | gm_beat.type=None, counter=0 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | [PASS] | beat_locked=False (momentum=0, floor=-3) |
| 13 | `universal.pacing.floor_relief` | [PASS] | beat_locked=False, no floor relief expected |
| 13 | `universal.goal_update.applied` | [PASS] | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | [PASS] | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | [PASS] | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | [PASS] | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | [PASS] | no negative amounts |
| 13 | `universal.inventory.remove_existence` | [PASS] | checked 0 removes |
| 13 | `universal.thread_update.valid_id` | [PASS] | no thread_updates |
| 13 | `universal.conditions.orphan` | [FAIL] | conditions with no CONDITION_MODS entry: ['relaxed'] |
| 13 | `universal.thread_add.applied` | [FAIL] | thread(s) added but never appeared in state: ['harker_hat_connection'] |
| 13 | `universal.beat_type.variety` | [PASS] | only 2 beat(s) in window (need >= 3) |
| 13 | `universal.beat_type.surface_as_consistency` | [PASS] | no surface_as drift detected |

## Universal Assert Results

> **Legend:** `[SYSTEM]` = system integrity failure (red severity) · `[PACING]` = pacing/perfection concern (yellow severity)  
| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.state.inventory_add` | [SYSTEM] | 1 | 1 | T7 |
| `extract.state.inventory_remove` | [SYSTEM] | 1 | 1 | T8 |
| `extract.state.pc_condition_remove` | [SYSTEM] | 1 | 1 | T11 |
| `ruling.rolled` | [SYSTEM] | 4 | 8 | T3 |
| `universal.beat_type.surface_as_consistency` | [PACING] | 0 | 13 | — |
| `universal.beat_type.variety` | [PACING] | 2 | 13 | T3 |
| `universal.conditions.orphan` | [SYSTEM] | 5 | 13 | T7 |
| `universal.directives.no_removed` | [PACING] | 0 | 13 | — |
| `universal.goal_update.applied` | [PACING] | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.no_overdraw` | [SYSTEM] | 0 | 13 | — |
| `universal.inventory.remove_existence` | [SYSTEM] | 1 | 13 | T11 |
| `universal.location_change.applied` | [SYSTEM] | 3 | 13 | T4 |
| `universal.momentum.band_delta` | [SYSTEM] | 2 | 13 | T4 |
| `universal.narrate.binding_present` | [SYSTEM] | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | [SYSTEM] | 0 | 13 | — |
| `universal.npc_states.no_removed` | [PACING] | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | [PACING] | 0 | 13 | — |
| `universal.pacing.consecutive_pressure_tracking` | [SYSTEM] | 2 | 13 | T1 |
| `universal.pacing.floor_no_relief` | [PACING] | 0 | 13 | — |
| `universal.pacing.floor_relief` | [PACING] | 2 | 13 | T4 |
| `universal.pending_gm_beat.consumed` | [SYSTEM] | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | [SYSTEM] | 0 | 13 | — |
| `universal.storytell.actions_quality` | [SYSTEM] | 3 | 13 | T6 |
| `universal.storytell.directive_rendered` | [PACING] | 0 | 13 | — |
| `universal.thread_add.applied` | [SYSTEM] | 1 | 13 | T13 |
| `universal.thread_update.valid_id` | [SYSTEM] | 0 | 13 | — |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `clear_the_road_toughs` | T0 | T12 | 13 | ⚠️ >8 turns |
| `confront_predatory_rider` | T9 | T9 | 1 |  |
| `deliver_the_ledger` | T0 | T12 | 13 | ⚠️ >8 turns |
| `harker_hat_connection` | T10 | T11 | 2 |  |
| `investigate_harker_disappearance` | T4 | T12 | 9 | ⚠️ >8 turns |
| `settle_the_debt` | T0 | T12 | 13 | ⚠️ >8 turns |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `assay_office` | 1 |  |
| `dustfall_outskirts` | 0 |  |
| `dustfall_saloon` | 3 |  |
| `marrows_crossing` | 1 |  |
| `marrows_crossing_general_store` | 2 |  |
| `red_streaked_canyon_base` | 2 |  |
| `sheriffs_station` | 1 |  |
| `weather_beaten_cabin` | 2 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `dusty` | T5 | T5 | 1 |  |
| `exposed` | T10 | T10 | 1 |  |
| `relaxed` | T13 | T13 | 1 |  |
| `startled` | T7 | T8 | 2 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | I ride into Dustfall and tie my horse at the liv… | 1117 (+0) | 3266 (+0) | 2911 (+47) | 1657 (+48) | 2749 (+27) | 0 | 0 | 30.72 |
| 2 | I step up to the bar and ask for a glass of wate… | 1355 (+50) | 3610 (+41) | 3197 (+50) | 1685 (-29) | 3209 (+88) | 0 | 0 | 24.20 |
| 3 | I lean on the bar and ask what happened to Old M… | 1388 | 3734 | 3256 | 1654 | 3251 | 0 | 0 | 21.32 |
| 4 | I head over to the assay office to see if Harker… | 1355 (-36) | 3750 (+90) | 3209 (+8) | 1641 (-45) | 3292 (+76) | 0 | 0 | 24.76 |
| 5 | I walk to the sheriff's office and ask if he's f… | 1330 (-29) | 3773 (+87) | 3312 (+127) | 1733 (+20) | 3493 (+204) | 0 | 0 | 33.36 |
| 5 |  | — | — | 0 (-3297) | 0 (-1721) | 0 (-3496) | 0 | 0 | 26.47 |
| 6 | The sheriff gives me Harker's cabin key. I walk … | 1412 | 3984 | 3452 | 1709 | 3480 | 0 | 0 | 24.77 |
| 7 | I look through Harker's desk and find a locked t… | 1378 (-19) | 4052 (+92) | 3395 (+23) | 1662 (-41) | 3627 (+155) | 0 | 0 | 25.43 |
| 8 | I head back to the general store to buy supplies… | 1352 (-8) | 3996 (-13) | 3337 (+28) | 1701 (+60) | 3643 (+137) | 0 | 0 | 27.64 |
| 9 |  | — | — | 0 (-3286) | 0 (-1651) | 0 (-3478) | 0 | 0 | 36.37 |
| 9 | I saddle up and ride out to Red Canyon. The trai… | 1368 (+1) | 4133 (+147) | 3371 (+97) | 1773 (+51) | 3631 (+64) | 0 | 0 | 22.73 |
| 10 | I find a camp at the base of the canyon wall. Tw… | 1383 (+13) | 4153 (-19) | 3421 (+112) | 1708 (-61) | 3736 (-80) | 0 | 0 | 24.35 |
| 10 |  | — | — | 0 | 0 | 0 | 0 | 0 | 24.51 |
| 11 | The men surrender. I find Harker tied up in a ne… | 1389 (-10) | 4246 (+9) | 3382 (-87) | 1692 (-179) | 3760 (-87) | 0 | 0 | 0.00 |
| 12 | Harker and I ride back to Dustfall together. He'… | 1348 (-122) | 4185 (-43) | 3348 (-111) | 1671 (-117) | 3724 (-24) | 0 | 0 | 0.00 |
| 13 | I walk Harker to the doc's office and then head … | 1346 (-42) | 4156 (-10) | 3389 (+26) | 1714 (-38) | 3768 (+87) | 0 | 0 | 0.00 |
|  | TOTALS | 17521 | 51038 | 42980 | 22000 | 45363 | 0 | 0 | 346.63 |

**Total turns:** 16 · **Total duration:** 346.63s · **Avg/turn:** 21.66s
**Total tokens in:** 178,902 · **Total tokens out:** 10,739 · **Total LLM time:** 329.6s
**Total retries:** 0 · **Total parse failures:** 0

