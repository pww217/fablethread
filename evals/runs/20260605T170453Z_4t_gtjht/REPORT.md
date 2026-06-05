# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-06-05T17:04:53.448961+00:00 · **Finished:** 2026-06-05T17:11:27.581021+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260605T170453Z_4t_gtjht`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260531T034137Z_tw3s9sfd/artifacts`

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 2/5  
**System Cohesion:** 2/5  
**Prompt Quality:** 4/5  
**State Fidelity:** 100.0%  
**Prompt Adherence:** 100.0%
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Domain judge breakdown:**

| Judge | Scores |
|---|---|
| `state_correctness` | extraction_accuracy_score=4, mechanic_lifecycle_score=3, state_fidelity_rate=62.5% |
| `narrative_interplay` |  |
| `prompt_pipeline` |  |

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  
**[narrative_interplay trace](full_cycle.narrative_interplay.trace.md)** · **[narrative_interplay verdict](full_cycle.narrative_interplay.judge.md)**  
**[prompt_pipeline trace](full_cycle.prompt_pipeline.trace.md)** · **[prompt_pipeline verdict](full_cycle.prompt_pipeline.judge.md)**  
**[meta trace](full_cycle.meta.trace.md)** · **[meta verdict](full_cycle.meta.judge.md)**  


## Meta Judge Verdict

***
mechanical_score: 3
narrative_score: 2
system_cohesion_score: 2
prompt_quality_score: 4
state_fidelity_rate: 0.625
prompt_adherence_rate: 0.75
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | avg(4, 3) = **3.5** | **-0.5** | State fidelity is low (0.625). Critical momentum desync and location failure indicate the engine logic itself is broken, not just extraction accuracy. The high extraction score masks deep structural failures in how state is applied/read. |
| `narrative_score` | narrative_interplay | **2** | **No Change** | Narrative suffers from "phantom mechanics" (conditions ignored), intent redirection errors, and continuity breaks. Tone is inconsistent with player agency. |
| `system_cohesion_score` | narrative_interplay | **2** | **No Change** | High contradiction between state claims and narrative output. State says one thing (e.g., NPC presence), Narrative says another. Pacing context fails to drive appropriate prose because momentum data is stale. |
| `prompt_quality_score` | prompt_pipeline | **4** | **No Change** | Prompts are structurally sound but suffer from redundancy (wasted tokens) and minor instruction drift (goal churn). No critical failures in prompt architecture itself, just optimization needs. |
| `state_fidelity_rate` | state_correctness | **0.625** | **-0.125** | Adjusted down due to the severity of the momentum desync bug which affects multiple turns and breaks core loop mechanics (floor relief). The raw rate likely didn't account for the *impact* of these errors on game flow, only their presence. |
| `prompt_adherence_rate` | prompt_pipeline | **0.75** | **-0.10** | Storyteller pipeline fails to emit actions and duplicates threads despite clear instructions. Narrator ignores some state cues due to data flow issues (stale momentum). Adherence is compromised by engine bugs, not just prompt clarity. |

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: **Contradiction Found.** State correctness identifies `beat_locked` logic failure and stale momentum as the root cause for pacing issues. Narrative interplay reports "Intent Redirection" (T7) and "Beat Type Misalignment" (T9). The contradiction is resolved by recognizing that the *narrative errors are symptoms of the state bug*. When momentum is read as 0 instead of <=-3, the engine fails to trigger `beat_locked` or proper pacing directives, leading the Narrator/Storyteller to generate prose based on incomplete context (e.g., ignoring player intent because the "struggle" state wasn't properly flagged in the ruling phase).
- **state_correctness vs prompt_pipeline**: **No Contradiction.** State correctness flags extraction misses and schema drift. Prompt pipeline notes wasted tokens but no critical failures. Both agree that data flow is imperfect, though for different reasons (engine bug vs. prompt inefficiency).
- **narrative_interplay vs prompt_pipeline**: **Partial Contradiction/Clarification Needed.** Narrative says directives are ignored (intent redirection); Prompt Pipeline rates adherence moderately high (0.75) but notes Storyteller fails to emit actions. The issue is not that the *prompt* instructions for intent handling are missing, but that the *input data* (state context regarding NPC presence and momentum) provided by the engine was stale or incorrect at T7/T12. The Narrator couldn't follow "respect player intent" because it didn't know Halden was absent/struggle state wasn't active in its view.
- **state_correctness vs narrative_interplay (unified threads)**: **No Direct Contradiction.** State correctness notes thread duplication; Narrative interplay doesn't explicitly discuss thread lifecycle but focuses on beat/narrative output. The duplication is a data hygiene issue, not necessarily a story consequence failure yet.

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Broken.** Momentum desynchronization causes the engine to read stale values (0) instead of post-delta values. This breaks `beat_locked` logic and floor relief injection across Turns 6, 7, 10-13.
2. **GM beat narration** — **Degraded.** Beat types are misaligned (T9: revelation vs complication). Narration often ignores player intent because the underlying state (momentum/NPC presence) is incorrect or stale.
3. **Unified thread chains** — **Broken.** Storyteller pipeline duplicates thread progress entries (`clear_the_road_toughs`) and fails to emit suggested actions at T10, breaking the feedback loop for thread resolution.
4. **Condition deduplication** — **Degraded.** Conditions like `winded` are added but lack modifiers in engine config (schema drift), making them "phantom mechanics" that affect state count but not gameplay/narrative consequences.
5. **Arc thread progression** — **Broken.** Due to Storyteller pipeline failures (missing actions, duplication) and goal churn from minor updates, threads stall or become redundant rather than progressing meaningfully.
6. **Floor relief injection** — **Broken.** Directly caused by momentum desync. When `beat_locked` should fire due to low momentum, it doesn't because the engine reads 0 instead of <=-3.
7. **goal_update application** — **Degraded.** Goals are updated too frequently for minor refinements (T10), causing "goal churn" and diluting narrative focus. The prompt guidance needs tightening on what constitutes a significant shift.
8. **recent_beats tracking** — **Working (with caveats).** While not explicitly flagged as broken, the misalignment of beat types suggests recent beats are being categorized incorrectly due to state context errors.
9. **Inventory extraction accuracy** — **Working.** Extraction accuracy score is high (4). No major issues reported here.
10. **Location change application** — **Broken.** Location delta at T12 was emitted but failed to update `state.location.id`. Player narratively moved, mechanically stayed put.
11. **NPC mention extraction** — **Degraded.** False positives on location names (T4) and continuity errors with NPC presence (Halden ghosting between T7 and T12).
12. **Storyteller pipeline** — **Broken.** Fails to emit actions, duplicates threads, and updates goals too aggressively.

**Trace Quality Assessment:**
- **Missing Data:** The trace lacks clear visibility into the *internal* momentum value at each step of the ruling phase vs. the post-delta state. This makes debugging the desync difficult without engine logs.
- **Systematic Gap:** All judges note issues with "state context" being stale or incorrect when passed to LLMs (Narrator/Storyteller). The pipeline assumes atomicity that doesn't exist in the current implementation.
- **Recommendation for Trace Improvement:** Add explicit logging of `pc.momentum` before and after delta application, and log the exact state snapshot passed to each LLM prompt. This will allow judges to correlate narrative errors directly with specific state values.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Fix the momentum desynchronization bug in `_compute_pacing_context()` to ensure it reads post-delta state, as this single engine failure cascades into broken floor relief, incorrect beat locking, and subsequent narrative intent redirection errors.** (Cited by `state_correctness` Critical Issue; impacts Narrative Interplay T7/T9).

### Key Findings
- **Momentum Desync:** State correctness identifies that stale momentum reads break core loop mechanics (`beat_locked`, floor relief) across multiple turns. This is the root cause of many narrative inconsistencies. (State Correctness, Critical, Turns 6-13)
- **Narrative-State Disconnect:** Narrative interplay reports intent redirection and NPC ghosting because the engine fails to update location state (T12) or correctly flag struggle states, leading LLMs to generate prose based on incorrect context. (Narrative Interplay, T7/T12; State Correctness, Major)
- **Storyteller Pipeline Hygiene:** The storyteller pipeline is failing basic output requirements: missing actions (T10), duplicated threads, and excessive goal churn from minor updates. This degrades long-term arc coherence. (Prompt Pipeline, Major/Minor; State Correctness, Major)

### Regression Check
*Note: Previous run scores were not provided in the input.*
- Assuming baseline stability, this run shows significant degradation in **System Cohesion** and **Narrative Score**. The mechanical score is dragged down by critical engine bugs that likely weren't present or were less severe previously. If previous runs had higher fidelity rates (>0.8), this represents a notable regression due to the momentum/location bugs.

## Judge Verdict — `state_correctness`

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | fail | -1 | 0 → -1 | — |
| 6 | fail | -1 | -1 → -2 | — |
| 7 | (none) | N/A | -2 → -3 | WRONG_DIR |
| 8 | success | +1 | -3 → -2 | — |
| 9 | partial | 0 | -2 → -2 | FLAT |
| 10 | partial | 0 | -2 → -3 | WRONG_DIR |
| 11 | fail | -1 | -3 → -3 | FLAT |
| 12 | fail | 0 | -3 → -3 | FLAT |

**Analysis:** Momentum is responding correctly to dice rolls for Turns 5, 6, and 8. However, Turn 7 shows a delta of -1 despite no roll occurring (impossible/skip path), which contradicts the design where `impossible=true` or skipped rolls should not apply momentum deltas unless explicitly synthesized as fail outcomes with delta application. The auto-checker flags Turns 7, 10, and 12 for `beat_locked_dual_trigger`, indicating a systemic mismatch between Python's `_compute_pacing_context()` logic (which checks `momentum <= -3`) and the state values recorded in the trace (where momentum is often logged as 0 or inconsistent with the delta application). Specifically, Turn 7 applies `-1` to go from -2 to -3, but the auto-checker sees `momentum=0`. This suggests a **state drift** where the `pc.momentum` field is not being updated correctly in the state snapshot after T6, or the ruling engine is reading stale momentum.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1 | opportunity | npc_behavior | opportunity | Storytell | Yes (expires T3) | — |
| T2 | null | N/A | None | Storytell | N/A | — |
| T4 | pressure | npc_behavior | pressure | Storytell | Yes (expires T6) | — |
| T5 | complication | npc_behavior | complication | Storytell | Yes (expires T7) | — |
| T6 | pressure | npc_behavior | pressure | Storytell | Yes (expires T8) | — |
| T7 | twist | event | twist | Storytell | Yes (expires T9) | — |
| T8 | null | N/A | None | Storytell | N/A | FLOOR_RELIEF_MISS? |
| T9 | revelation | npc_behavior | revelation | Storytell | Yes (expires T11) | — |
| T10 | null | N/A | None | Storytell | N/A | NO_EXPIRY_TESTED |
| T11 | complication | npc_behavior | complication | Storytell | Yes (expires T13) | — |

**Analysis:** 
- **T8 Null-Clear & Floor Relief:** At Turn 7, `pending_gm_beat` is a `twist`. It expires at T9. At T8 start, it is still valid (turn 8 <= turn_expires 9). Storytell emits null. The beat should be popped. However, the auto-checker flags `beat_locked_dual_trigger` for T7 and T12, implying `beat_locked` was True when momentum hit -3. If `beat_locked` was True at T7 end (momentum -3), then at T8 start, if storyteller emits null, floor relief *should* inject a `breathing_room`. The trace shows `pending_gm_beat: None` after T8. This is a **FLOOR_RELIEF_MISS** or an implementation bug where floor relief didn't fire despite `beat_locked=True`.
- **T10 Null-Clear:** Storytell emits null. Beat from T9 (`revelation`, expires T11) is still valid at start of T10? No, T9 beat expires at 11. So it persists through T10 narration. Storytell emits null -> popped. Correct.
- **NO_EXPIRY_TESTED:** The trace shows beats expiring correctly in TTL logic (e.g., T1 opportunity expired before T3 usage if referenced), but the `recent_beats` history management is inconsistent with the design's "append after floor relief" rule, as seen by null entries appearing in `recent_beats`.

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| 2 | None | "Clear your debts..." | "Clear your debts..." | N/A | — |
| 10 (T11) | "Identify the true employer..." | "Clear your debts..." | "Identify the true employer..." | Yes | — |

**Analysis:** Goal update applied correctly at Turn 10/11. No silent changes detected.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| settle_the_debt | Seed | arc | normal | T2 (update empty) | N/A | INERT |
| deliver_the_ledger | Seed | arc | normal | T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13 | N/A | INERT |
| clear_the_road_toughs | Seed | arc | background | T4, T5, T6, T7, T8, T9, T10, T11, T12, T13 | N/A | INERT |
| mysterious_watchers | T2 | arc | normal | T10, T11 | N/A | UNRESOLVED_AT_END |

**Analysis:** 
- **Thread Progress Duplication:** `clear_the_road_toughs` has duplicate progress entries: "The confrontation has moved from the entrance into the inn's main room." appears twice in Turn 9 and again in Turn 10/12. This is a **schema_drift** or extraction error where the storyteller repeats previous context instead of appending new distinct progress.
- **Inert Threads:** `settle_the_debt` is inert but marked `active: false`. It was never resolved, just ignored. This is acceptable for completed-off-screen arcs, but `deliver_the_ledger` and `clear_the_road_toughs` are also inactive despite active plot events. The storyteller fails to activate relevant threads (`clear_the_road_toughs` should be `active: true` during the confrontation).

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| cornered | T6 | narrative | T7 | 2 turns | SILENT_DROP |
| winded | T8 | narrative | T10 | 3 turns | — |

**Analysis:** 
- **cornered (T6):** Added in T6. Removed in T7 state diff? The trace shows `pc_condition_remove: [{id: "cornered"}]` in T7 Applied Deltas. However, the auto-checker flags `universal.conditions.orphan` for `winded` and `scraped_and_bruised`.
- **orphan Conditions:** Auto-checkers flag `cornered`, `winded`, `scraped_and_bruised` as having no `CONDITION_MODS` entry. This is a **schema_drift** or configuration issue: the engine's condition system expects conditions to have defined modifiers for dice rolls, but these narrative conditions lack them in the config/prompt context, causing auto-checker failures.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 3 | Add | credits | +200 | No | — |
| 3 | Add | ledger | +1 | No | — |
| 6 | Remove | credits | -200 | No | — |
| 9 | Remove | credits | -1 | No | — |

**Analysis:** Inventory changes are accurately extracted and applied. Credits flow: 500 -> 700 (T3) -> 500 (T6) -> 499 (T9). Ledger added T3, still present at end. No mismatches.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Compendium vs Location:** At Turn 12/13, `compendium.npcs` shows `tough_a` and `tough_b` as `presence: present` at `river_docks`. However, the state snapshot for T13 does not show them in the active scene context properly (narrative implies they are there). The `last_seen` updates correctly.
- **Thread State vs Narrative:** `clear_the_road_toughs` remains `active: false` throughout the entire confrontation sequence (T4-T12). This is a mechanical failure of the Storytell pipeline to activate relevant threads, leading to inert state tracking despite high narrative tension.

### 2B — Extraction Drift
- **Turn 7:** `universal.pacing.beat_locked_dual_trigger`. Momentum went from -2 to -3. Python logic expects `beat_locked=True` when momentum <= -3. The auto-checker sees `momentum=0`. This indicates the state snapshot for T7's ruling phase read stale data (T6 end state was -2, but perhaps T7 start read 0?). Or the delta application failed to persist `-1` correctly in a way that subsequent turns see it.
- **Turn 9:** `universal.conditions.orphan`. Condition `winded` added T8 is flagged as orphaned because no modifier exists. This is a config/prompt drift, not an extraction failure per se, but the extractor didn't flag it for validation.

### 2C — State Fidelity Rate Calculation
- Total Turns: 13 (excluding empty T10 first pass). Let's count valid turns with state changes: T1-T9, T10-T13. Total 12 active turns processed in trace blocks? The trace has T1-T9, then two T10s, T11-T13.
- Failures/Rejections/Auto-Failures:
    - T4: NPC mention (minor)
    - T6: Beat locked dual trigger, Condition orphan
    - T7: Beat locked dual trigger
    - T8: Condition orphan
    - T9: Condition orphan
    - T10: Actions quality, Momentum band delta, Consecutive pressure tracking, Condition orphan
    - T11: Consecutive pressure tracking, Beat locked dual trigger
    - T12: Location change applied (major), Beat locked dual trigger, Condition orphan
    - T13: Beat locked dual trigger

- Clean Turns: T1, T2, T3, T5. (4 turns).
- Total Turns Analyzed: 13.
- Rate: 4/13 ≈ 0.307? 
- Wait, the prompt asks for `turns where (no rejected deltas AND no Auto-Checker failures AND no detected drift)`.
    - T1: Clean.
    - T2: Clean.
    - T3: Clean.
    - T4: Auto-fail (NPC mention).
    - T5: Clean? No auto-fails listed for T5 in the table? Wait, T6 has beat_locked_dual_trigger. T5 is clean.
    - T6: Auto-fails present.
    - T7: Auto-fails present.
    - T8: Auto-fail (Condition orphan).
    - T9: Auto-fail (Condition orphan).
    - T10: Auto-fails present.
    - T11: Auto-fails present.
    - T12: Auto-fails present.
    - T13: Auto-fail present.

- Clean Turns: 1, 2, 3, 5. (4 turns).
- Total: 13 turns.
- Rate: 4/13 = 0.3076... -> **0.31**. 
- *Correction*: The prompt says "State Fidelity Rate Calculation". If I look at the trace, T10 has two blocks? No, it's one turn with an empty first pass and a second input. Let's assume 12 turns of gameplay (T1-T9, T10-T13).
- Clean: T1, T2, T3, T5. 
- Rate: 4/12 = **0.33**.

Let's re-read the Auto-Checker table carefully.
Failures on: 4, 6, 7, 8, 9, 10 (x4), 11 (x2), 12 (x3), 13.
Clean turns: 1, 2, 3, 5.
Total turns in trace blocks: T1-T9, T10, T10(second), T11, T12, T13. That is 14 blocks? No, T10 is one turn with two inputs? The metrics table shows T10 twice for tok_in/out? No, it lists T10 once with 0 tokens, then again with values. This implies a retry or split. Let's count unique turns: 1-9, 10, 11, 12, 13 = 13 turns.
Clean: 1, 2, 3, 5. (4 turns).
Rate: 4/13 ≈ **0.31**.

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True Failure or Noise? | Root Cause | Remediation Tag |
|------|-----------|------------------------|------------|-----------------|
| 4 | `universal.npc_mention.extracted` | **True** (Minor) | Narration mentions "Marrow" which is the town name, not a compendium NPC. The checker likely flags any proper noun not in `compendium_npc_update`. This is false positive noise for location names. | `checker_noise` |
| 6 | `universal.pacing.beat_locked_dual_trigger` | **True** (Major) | Momentum was -2 at end of T5, went to -3 at end of T6. Python logic expects `beat_locked=True`. The checker sees `momentum=0`. This indicates the state read for pacing computation is stale or incorrect relative to the delta application. | `engine_bug` |
| 6 | `universal.conditions.orphan` | **True** (Config) | Condition `cornered` has no modifier defined in engine config/prompt context. Extractors don't validate this; it's a static config issue. | `schema_drift` |
| 7 | `universal.pacing.beat_locked_dual_trigger` | **True** (Major) | Momentum hit -3 at end of T6. T7 ruling should see momentum <= -3 -> beat_locked=True. Checker sees `momentum=0`. Same root cause as T6: state synchronization failure between delta apply and ruling readback. | `engine_bug` |
| 8-13 | `universal.conditions.orphan` | **True** (Config) | Conditions `winded`, `scraped_and_bruised` lack modifiers. Systemic config gap for narrative-only conditions. | `schema_drift` |
| 10 | `universal.storytell.actions_quality` | **True** (Extraction) | Storyteller emitted empty actions list in the first T10 pass? Or failed to generate them. The trace shows `actions: []` or missing in one block. | `extraction_miss` |
| 10 | `universal.momentum.band_delta` | **True** (Logic) | Band was `partial`. Expected delta +0. Got -1. Momentum went from -2 to -3. This contradicts the band table (`partial`=0). The ruling engine applied a fail delta (-1) instead of partial delta (0). | `engine_bug` |
| 10 | `universal.pacing.consecutive_pressure_tracking` | **True** (Logic) | Beat type was null/None, but counter incremented to 1. Should have reset or stayed same if beat is invalid/null. The tracker logic failed to handle null beats correctly. | `engine_bug` |
| 10-13 | `universal.pacing.beat_locked_dual_trigger` | **True** (Major) | Repeated failure of momentum state synchronization. Python reads stale/zero momentum while deltas apply negative values, causing `beat_locked` logic to desync from actual game state pressure. | `engine_bug` |
| 12 | `universal.location_change.applied` | **True** (Critical) | Location change emitted (`river_docks`) but `state.location.id` remained `crossed_keys_entrance`. The delta was rejected or not applied to the canonical location field, causing a state divergence. | `validation_rejection` |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 3/5
**Reasoning:** Inventory and Condition extraction are generally accurate in terms of presence (items added/removed correctly). However, there is a significant failure on Turn 10 (`actions_quality`) where the storyteller failed to emit actions. Additionally, thread progress duplication indicates minor extraction noise/repetition from the LLM. The `location_change` rejection at T12 is an engine validation/application issue, not strictly extraction, but it reflects poorly on the pipeline's end-to-end accuracy. No major inventory/condition misses were found in the trace diffs.

### Mechanic Lifecycle Score: 3/5
**Reasoning:** 
- **Momentum/Pacing:** The `beat_locked_dual_trigger` failures across T6-T13 indicate a systemic engine bug where momentum state is not synchronized between delta application and ruling/pacing computation. This breaks the core pacing mechanic (floor relief, beat locking).
- **Threads:** Threads are inert despite active plot events (`clear_the_road_toughs`). Progress duplication is present.
- **Conditions:** Orphaned conditions indicate a config/schema drift where narrative conditions aren't fully integrated into the mechanical modifier system.
- **GM Beats:** TTL and null-clear logic mostly works, but floor relief misses (T8) due to momentum sync issues are critical failures in the beat lifecycle recovery mechanism.

---

## SECTION 5 — Actionable Issues

**Critical**
- **<Description>** Momentum state desynchronization between delta application and ruling/pacing computation causes `beat_locked` logic to fail repeatedly (Turns 6, 7, 10-13). The engine reads stale momentum values (often 0) while deltas correctly apply negative changes. This breaks floor relief injection and pacing directives.
    - **Tags:** `engine_bug`, `validation_rejection`.
    - **Fix:** Ensure `_compute_pacing_context()` reads the *post-delta* state or that delta application is atomic before ruling readback for subsequent turns. Debug why `pc.momentum` appears as 0 in auto-checker logs when it should be <=-3.

**Major**
- **<Description>** Location change at Turn 12 was emitted by Scene Extract but failed to update `state.location.id`. The delta was likely rejected or ignored during apply, leaving the player narratively at the docks but mechanically at the inn entrance.
    - **Tags:** `validation_rejection`, `engine_bug`.
    - **Fix:** Investigate why `location_change` delta for T12 was not applied to `state.location`. Check validation constraints on location IDs or merge logic in `_apply_delta()`.

- **<Description>** Storyteller pipeline fails to emit suggested actions (Turn 10) and duplicates thread progress entries (`clear_the_road_toughs`).
    - **Tags:** `extraction_miss`, `schema_drift`.
    - **Fix:** Add validation in Storytell output parser to enforce non-empty `actions` list. Prompt engineering update for storyteller to prevent repetitive progress appending; add a "unique only" instruction or post-process deduplication in `_apply_thread_updates()`.

**Minor**
- **<Description>** Conditions (`cornered`, `winded`, etc.) are flagged as orphaned because they lack defined modifiers in the engine config. This breaks condition-based dice roll calculations if these conditions were ever meant to affect stats.
    - **Tags:** `schema_drift`.
    - **Fix:** Define default or zero-value modifiers for narrative-only conditions, or update auto-checker to exclude non-mechanical conditions from modifier validation.

- **<Description>** Auto-checker false positive on Turn 4 regarding NPC mention "Marrow". Location names are being flagged as missing compendium entries.
    - **Tags:** `checker_noise`.
    - **Fix:** Update auto-checker logic to exclude location names and common nouns from the `npc_mention.extracted` assertion, or ensure all locations have a corresponding (dummy) NPC entry if required by schema.

## Judge Verdict — `narrative_interplay`

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
- **Caron**: Present T1, exited implicitly after debt settled. Reappeared? No, but his ledger/debt is referenced.
- **Halden**: Present T3 (Well), then mentioned in T7/T12 narration as target of delivery/call. Did he appear at the inn? Narration T7 says "You lunge toward... phantom contact". Halden was NOT present at the inn entrance/interior during the struggle, which is consistent with him being a merchant who might have left or be elsewhere. However, T12 narration says "screaming for Halden to wait for you" and he is marked `presence: present` in T12 Scene Extract? **Flag**: T12 Scene Extract lists `halden` as `present`. But T7 narration said Aren reached for a "phantom contact". If Halden was present at the inn, why did T7 say phantom? This is a **Ghost NPC** or **Continuity Error**. The extractor marked him present in T12 because he's called out for, but his actual presence wasn't established in the scene narration until perhaps off-screen arrival? Or is he just "known" to be there? The seed says Halden is a merchant. If he's at the inn, why was Aren looking for a phantom contact in T7? This suggests Halden *wasn't* there. T12 extract might be hallucinating his presence based on the player's shout or world state `halden_delivery_contract`.
- **Toughs**: Present T3 (Shadows), T4 (Entrance), T5-T9 (Inn Entrance/Interior), T10+ (Bar/Docks). Consistent.
- **Matthew Estrada**: Present T10+. Consistent.

### 2B — Player Intent Fidelity
- **T7 Input:** "Sit across from Halden... hand him the ledger."
- **Narration Output:** "You lunge toward the heavy timber doors... phantom contact... pinned against a pillar."
- **Verdict:** **Broken**. The player attempted to interact with Halden. The engine narrated that Halden wasn't there ("phantom contact") and Aren was pinned by thugs instead. This is a massive redirection of intent. Did the ruling LLM mark it impossible? Ruling output: `rolled=false`, `outcome_summary: "physically pinned"`. It seems the engine decided the action was impossible or failed so hard that it narrated an alternative failure state (being pinned) rather than just saying "Halden is not here." This ignores the player's specific target interaction.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns:** T1-T2 Low, T4-T7 High, T8 Medium/Chaos, T9-T11 High, T12-High (Flight), T13-High (Cornered).
- **Flag:** >4 consecutive high-pressure turns? Yes. T5-T13 is essentially non-stop pressure/conflict/flights. There are very few "Breathe" moments narratively, despite mechanical floor relief attempts. The narration remains tense even when mechanics might suggest a beat of recovery (e.g., T8 success led to chaos, not rest).
- **Momentum arc:** Discernible build-up and floor hits.
- **Beat type variety:** Good variety, but `Revelation` misuse on T9 is noted.
- **recent_beats effectiveness:** Beats are diverse, but the narrative often ignores the "Breathing Room" intent if one was injected (e.g., if T12 had a breathing room beat for T13, T13 narration is still "Cornered"). This suggests Floor Relief isn't effectively changing tone.
- **Intent verb variety:** `negotiate`, `travel`, `persuade`, `deceive`, `intimidate`, `sneak`, `escape`. Good variety.
- **Skill coverage:** Charisma (T5, T6, T9, T10), Dexterity (T8, T12). Missing: Strength, Wits, Lore, Resolve.
- **Escape paths:** When pinned (T7-T9), options were limited to fight/bribe/flee. The engine provided actions like "Draw dagger", "Bribe". Viable choices existed but failed mechanically.

---

## SECTION 4 — Scores

### Narrative Score: 3/5
The prose is generally good and immersive. However, the **Intent Redirection on T7** is a major flaw where the player's specific interaction was ignored in favor of a generic "pinned" failure state. Additionally, conditions like `winded` are mechanically present but don't affect rolls (`cond_mod: 0`), making them decorative. The pacing is relentlessly high-tension with little narrative relief despite mechanical attempts at floor relief.

### System Cohesion Score: 2/5
There are significant disconnects between mechanics and narrative/state:
1. **Condition Modifiers:** `winded` condition added in T8 but `cond_mod: 0` on the roll that created it (T8 Dexterity) or subsequent turns? T8 rules show `cond_mod: 0`. This is a mechanical failure; conditions should affect rolls if they represent physical impairment.
2. **NPC Continuity:** Halden's presence status contradicts narration between T7 and T12.
3. **Beat/Narrative Misalignment:** `Revelation` beat on T9 did not match the narrative outcome (dismissal/rejection).
4. **Intent Ignored:** T7 player intent was completely bypassed by the ruling/narrate pipeline, resulting in a "phantom" interaction rather than addressing the absence of Halden directly or allowing a failed attempt to find him.

---

## SECTION 5 — Actionable Issues

- **Critical: Intent Redirection on Impossible/Failed Actions** (Turns: T7) — Tag: `intent_redirect`. The engine narrated that Aren reached for a "phantom contact" and was pinned, ignoring the player's explicit intent to interact with Halden. Fix: If an action is impossible or fails due to state (NPC not present), narrate the failure of *that specific interaction* first ("You look around but Halden isn't there") before introducing other consequences like being pinned by thugs. Do not substitute a different scene event unless it's a direct consequence of the failed attempt.
- **Major: Condition Modifiers Not Applied** (Turns: T8, T10-T12) — Tag: `phantom_mechanic`. The `winded` condition was added but `cond_mod` remained 0 on relevant rolls. Fix: Ensure conditions that impair physical ability (`winded`, `cornered`) apply appropriate modifiers to Dexterity/Strength checks or impose narrative restrictions reflected in the ruling phase.
- **Major: NPC Presence Continuity Error** (Turns: T7, T12) — Tag: `npc_ghost`. Narration T7 implies Halden is absent ("phantom contact"), but Scene Extract T12 lists him as present. Fix: Align scene extraction with narration facts. If Halden wasn't seen in the inn during the struggle, he should not be marked `present` unless there's a narrative cue of his arrival.
- **Minor: Beat Type Misalignment** (Turns: T9) — Tag: `type_mismatch`. A `revelation` beat was generated for a scene where the primary outcome was rejection/mockery by an NPC, which fits `complication` or `setback` better. Fix: Improve Storyteller prompt guidance to align `revelation` beats with moments of new information discovery rather than social failures.

## Judge Verdict — `prompt_pipeline`

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static instructions. User prompt contains only turn-variable state and input. |
| P2 | Y | Inputs are `pc`, `scene` (location/NPCs), `inventory`, `last_turn_narrative`. Correct for ruling intent/dice check. |
| P3 | N | No cross-pipeline redundancy detected in Rules prompt specifically; it is leanest of all streams. |
| P4 | Y | Schema and guidance are clearly separated by headers (`## Stats`, `## Decision rule`). |
| P5 | Y | Logic for `check.required` (default NO) is consistent with examples provided. |
| P6 | N | Some repetition in "No-roll movement" vs general rules, but serves as necessary few-shot context. Acceptable density. |
| P7 | Y | Numbered lists and clear JSON schema block aid parsing. |
| P8 | PASS | LLM correctly identified `impossible` on T7 (Halden not present) and required checks for combat/persuade actions. Adheres to anti-declare-outcome rule. |
| P9 | N | Failures were rare/non-existent in this run regarding intent classification. |

**Remediation summary:** None critical. The prompt is well-structured and adherent.

### 1B — Narrate Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static behavioral guidance. User prompt contains state, history, pacing, beat, input. |
| P2 | Y | Inputs are comprehensive: `pc`, `inventory`, `location`, `characters` (roster), `world_state`, `threads`, `prior_history`. All required for rich narration. |
| P3 | N | Narration is fed to extractors by design; no *unintentional* redundancy flagged here that isn't structural necessity. |
| P4 | Y | System prompt separates style rules from mechanics (inventory, NPCs). User prompt provides the data payload. |
| P5 | Y | Priority ordering (`player input > GM beat`) is clear and consistently followed in outputs. |
| P6 | N | Some verbosity in "NPC Behavior Drivers" section, but necessary for agency enforcement. |
| P7 | Y | Clear headers, bolded priorities, examples of Good/Bad help parsing. |
| P8 | PASS | Narrator respected `impossible` on T7 (narrated failure to find Halden). Respected GM beats (e.g., T2 Opportunity surfaced as NPC behavior). Adhered to word count and style constraints. |
| P9 | N | No major adherence failures observed that a few-shot example would have fixed; the prompt is robust. |

**Remediation summary:** None critical. The prompt successfully integrates complex state (beats, pacing) without hallucinating player actions.

### 1C — Extract Scene Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static schema/guidance. User prompt has narration and location context. |
| P2 | Y | Inputs: `location`, `previous_turn_narration` (context), `current_turn_narration`. Correct for scene extraction. |
| P3 | N | Redundancy with Narrator is intentional (narrative input). No other cross-stream duplication issues found in this stream's prompt structure. |
| P4 | Y | Schema section defines JSON output; Field rules provide behavioral guidance. Distinct separation. |
| P5 | Y | Rules for `presence` changes and `compendium_npc_update` are mutually exclusive (enter vs exit). |
| P6 | N | The "Bio and notes examples" section is long but serves as critical few-shot context to prevent generic bios. Acceptable. |
| P7 | Y | JSON schema block at top, followed by detailed field rules. Easy for LLM to parse structure first. |
| P8 | PASS | Adhered to `compendium_npc_update` format on T1-T13. Correctly omitted unchanged NPCs (e.g., Caron not updated when only toughs moved). Did not invent location IDs. |
| P9 | N | No significant failures in scene extraction logic observed this run. |

**Remediation summary:** None critical. The prompt effectively constrains the LLM to structured NPC presence tracking.

### 1D — Extract State Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static schema/guidance. User prompt has inventory, conditions, narration. |
| P2 | Y | Inputs: `inventory` (current stacks), `active_conditions`, `player_intent`, `narration`. Correct for state delta extraction. |
| P3 | N | Redundancy with Narrator is intentional. No other issues. |
| P4 | Y | Schema vs Guidance separation is clear. "Hard cap" and "Generic item mapping" sections are distinct behavioral constraints. |
| P5 | Y | Rules for `inventory_remove` (spending/giving) vs `inventory_update` are consistent. |
| P6 | N | The "Numerical extraction — mandatory checklist" is verbose but necessary to prevent hallucination of amounts. |
| P7 | Y | JSON schema first, then detailed rules. Good structure. |
| P8 | PASS | Adhered to `inventory_remove` logic on T6 (200 credits dropped) and T9 (1 credit offered). Correctly handled condition lifecycle (`winded` added/removed appropriately). Did not invent items. |
| P9 | N | No failures observed that required few-shot examples; the rules are explicit enough. |

**Remediation summary:** None critical. The prompt successfully prevents phantom item creation and handles currency mapping correctly.

### 1E — Storyteller Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static schema/guidance. User prompt has rich context: inventory, characters, location, threads, pacing, beats, rules_outcome. |
| P2 | Y | Inputs are maximal but justified for thread/beat/action generation. Includes `pacing_context` and `recent_beats`. |
| P3 | N | Redundancy with Narrator is intentional. No other issues. |
| P4 | Y | Schema first, then extensive behavioral guidance (Actions, Outcome Summary, Thread Ops, World State). Clear separation. |
| P5 | Y | Guidance on `thread_update` vs `thread_add` is consistent. Band-aligned beat selection rules are clear. |
| P6 | N | The prompt is very long (~2000 words of guidance), but most sections serve distinct mechanical purposes (beat diversity, thread lifecycle, world state dedup). Reducibility is low without losing intent. |
| P7 | Y | JSON schema at top. Numbered/bulleted lists for rules. Clear headers for each mechanic type. |
| P8 | FAIL (Partial) | **T10:** `goal_update` was emitted ("Identify the true employer..."). This is valid per prompt, BUT it replaced the original goal without resolving the arc or providing a strong narrative pivot justification in the output itself (though implied by Matthew's warning). More critically: **World State Duplication.** On T9 and T10, `world_state_add` emitted identical text for `inn_commotion_at_crossed_keys`. The prompt explicitly forbids this ("MANDATORY: Check before adding... reuse that existing ID"). This is a schema drift/adherence failure. |
| P9 | Y | A few-shot example of "Good vs Bad World State Dedup" would have prevented the T9/T10 duplication error significantly. |

**Remediation summary:** 
- **Add Few-Shot for World State Dedup:** Include an explicit example showing how to update `id` instead of creating a new one when facts overlap.
- **Clarify Goal Update Triggers:** Add guidance that `goal_update` should only be used if the *nature* of the goal shifts significantly, not just as a minor refinement based on one conversation turn (unless it's a major pivot).

---

## SECTION 2 — Mechanic Ownership Check

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene ✅ |
| `location_change`, `location_description` | scene ✅ |
| `scene_tags`, `scene_tagline` | scene ✅ |
| `inventory_add`, `inventory_remove`, `inventory_update` | state ✅ |
| `pc_condition_add`, `pc_condition_remove` | state ✅ |
| `thread_update`, `thread_resolve`, `thread_add` (gated) | storytell ✅ |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | storytell ✅ (Not explicitly used in outputs, but structure is correct) |
| `goal_update` | storytell ✅ |
| `gm_beat` | storytell ✅ |
| `actions`, `outcome_summary` | storytell ✅ |

**List any misplaced mechanics:** None. All pipelines emitted their designated mechanics correctly.

---

## SECTION 3 — Cross-Pipeline I/O Relevance

### Rules
- **Inputs focused?** Yes. Only receives `pc`, `location`, `recent_turns[-1:]`, `user_input`. No compendium or inventory bloat. Efficient.

### Narrate
- **Rich inputs justified?** Mostly yes. 
    - **Flag:** On T4-T13, the `Characters` section includes `last_seen: Marrow's Crossing` for NPCs who are no longer present (e.g., Caron). While this provides continuity, it adds token weight without affecting narration significantly if they aren't interacted with. However, the prompt requires `npc_roster`, so this is acceptable overhead for consistency.
    - **Flag:** `world_state` is included in every turn's user prompt. On T9-T13, duplicate world state entries (`A violent struggle...`) appear due to Storyteller errors (see Section 4). This bloats the Narrator prompt unnecessarily.

### Extract Scene
- **Inputs focused?** Yes. Receives `narration`, `location`. Does *not* receive inventory or arc thread data, which is correct for scene extraction. It receives `previous_turn_narration` for context, which is necessary for tracking NPC presence changes relative to the prior state.

### Extract State
- **Inputs focused?** Yes. Receives `narration`, `inventory`, `conditions`. Does *not* receive arc thread data or recent beats, which is correct. It receives `player_intent` from Step 0, which helps interpret ambiguous narration (e.g., distinguishing between "I drop credits" and "I find credits").

### Storyteller
- **Rich inputs justified?** Yes. Requires full context for thread/beat/action generation.
    - **Flag:** `recent_beats` history is included. On T13, the prompt shows 5 recent beats. This is within limits but adds token cost. Justified for beat diversity logic.
    - **Pacing Context Usage:** The Storyteller correctly uses `pacing_context.directive` and `gate`. On T4 (Breathe), it did not add threads despite gate being allow, adhering to the "Do NOT add new threads" guidance for Breathe. On T7 (Pressure; Resolve a Threat), it emitted a pressure beat initially but then corrected to twist on T10? No, T7 was Pressure, T8 was Twist. The alignment is generally good.
    - **Flag:** `world_state_add` duplication indicates the LLM is not effectively scanning existing world state for overlaps before emitting new entries, despite explicit instructions.

---

## SECTION 4 — Prompt Redundancy Analysis

### Top Overlaps Across All Turns

1.  **Narrate + Storytell: Active Threads Section**
    -   **Is it intentional?** Yes. Both pipelines need to know the current state of campaign threads to generate coherent narration and thread updates respectively. The Narrator uses them for flavor/hinting; the Storyteller uses them for mechanical lifecycle management.
    -   **Waste:** Low. This is a core dependency.

2.  **Narrate + Scene: Location Description**
    -   **Is it intentional?** Partially. The Narrator receives `location` from state. The Scene Extractor receives `location` to detect changes. However, the *full* location description (seed text) is repeated in both prompts every turn.
    -   **Waste:** Moderate. The scene extractor only needs the current ID and name to compare against narration for a change detection. It doesn't need the full poetic description unless it's writing one.
    -   **Remediation:** Pass only `location.id` and `location.name` to Scene Extractor, not the full description block.

3.  **Narrate + Storytell: World State**
    -   **Is it intentional?** Yes. Both need world facts for context.
    -   **Waste:** High (due to duplication errors). As noted in Section 1E, duplicate entries were created by the Storyteller and persisted into state, causing them to appear twice in subsequent Narrator prompts. This is a data flow error caused by prompt adherence failure, not just redundancy.

### Top 3 Dedup Opportunities

1.  **Scene Extractor Location Payload:**
    -   *Current:* Full `location` object (id, name, description) passed every turn.
    -   *Fix:* Pass only `{ "id": "...", "name": "..." }`. The extractor can infer the current location from state if no change is detected; it doesn't need the prose description to decide if a move happened.
    -   *Outcome:* Saves ~50-100 tokens per turn in Scene Extractor prompt.

2.  **Narrator Character Roster `last_seen` Field:**
    -   *Current:* Every NPC entry includes `| last seen: [Location]`.
    -   *Fix:* Remove `last_seen` from the Narrator's character roster input. The Narrator only needs to know who is present/known for current scene logic. History of where they were last seen is irrelevant to prose generation and adds token bloat.
    -   *Outcome:* Saves ~20-30 tokens per NPC, significant when 6+ NPCs are in the roster.

3.  **World State Deduplication Enforcement:**
    -   *Current:* Storyteller prompt instructs checking for overlaps but fails to do so consistently (T9/T10).
    -   *Fix:* Add a concrete few-shot example: `Example: If world_state already has "thugs_at_inn", and new fact is "struggle_at_inn", update the existing entry's text rather than creating "struggle_at_inn".`
    -   *Outcome:* Prevents state bloat which cascades into Narrator prompt inflation.

---

## SECTION 5 — Prompt Adherence Rate

**Pipeline Adherence per Turn:**

| Turn | Rules | Narrate | Scene | State | Storytell | Result |
|------|-------|---------|-------|-------|-----------|--------|
| 1    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 2    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 3    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 4    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 5    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 6    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 7    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 8    | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 9    | PASS  | PASS    | PASS  | PASS  | FAIL*     | Storytell: World State Duplication (T9) |
| 10   | PASS  | PASS    | PASS  | PASS  | FAIL*     | Storytell: World State Duplication (T10) |
| 11   | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 12   | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |
| 13   | PASS  | PASS    | PASS  | PASS  | PASS      | All Pass |

*\*Note: T9/T10 Storytell failures are minor schema drift (redundant world state entries) rather than catastrophic logic errors. The mechanics still functioned.*

**Total Instances:** 5 pipelines × 13 turns = 65
**Failures:** 2 (Storytell on T9, T10)
**Passes:** 63

`prompt_adherence_rate`: **0.97** (Rounded from 0.969 for YAML front matter consistency with previous examples, though strictly it is 0.969). *Correction based on prompt instruction: "This value goes in YAML front matter as `prompt_adherence_rate`." I will use the calculated float.*

Calculated: $63 / 65 = 0.9692...$
Rounded to 3 decimals: **0.969**

---

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)

-   **Rules:** **5**. Perfect adherence, clean inputs/outputs, no redundancy issues.
-   **Narrate:** **5**. Excellent integration of complex state (beats, pacing), strict adherence to style and mechanics.
-   **Extract Scene:** **4**. Good structure. Minor deduction for receiving redundant location description data that could be trimmed. Adherence is high.
-   **Extract State:** **4**. Good structure. Minor deduction for verbosity in numerical rules section which doesn't add much value over the examples provided. Adherence is high.
-   **Storyteller:** **4**. Strong mechanics, but adherence failure on World State deduplication (T9/T10) indicates a gap between instruction and execution that few-shot examples could fix. The prompt is also quite long, risking token budget issues in longer campaigns.

### Prompt Quality Score (1–5)

**Score: 4**

**Worst Pipeline Architecture:** **Storyteller**. While functional, it suffers from the most significant adherence drift regarding World State deduplication and has the highest token cost per turn (~9000-10000 tokens). The instruction to "check before adding" is behavioral but lacks concrete enforcement mechanisms (few-shots) compared to other pipelines.

**Highest-Priority Fix:** **Add Few-Shot Examples for World State Deduplication in Storyteller Prompt.**
The current prompt says: *"MANDATORY: Check before adding... reuse that existing ID."* The LLM ignores this 20% of the time (observed T9/T10). A concrete example showing `existing_id` update vs `new_id` creation would likely resolve this, preventing state bloat and subsequent Narrator prompt inflation.

---

## SECTION 7 — Actionable Issues

### Critical
-   **None.** No mechanical failures or data corruption observed that broke the game loop.

### Major
-   **<Storyteller World State Duplication>** (pipeline: storytell, turns: [9, 10]) — Tag: `<instruction_ignored>`. Fix: Add a concrete few-shot example in `storytell_system.j2` demonstrating how to update an existing `world_state_add` entry by ID rather than creating a new one when facts overlap. This prevents state bloat that inflates subsequent Narrator prompts.

### Minor
-   **<wasted_tokens>** (pipeline: extract_scene, turns: [1-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Pass only `location.id` and `location.name` to the Scene Extractor instead of the full location description block. The extractor does not need prose context for change detection.
-   **<wasted_tokens>** (pipeline: narrate, turns: [4-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Remove `last_seen` field from NPC roster entries in the Narrator user prompt. It adds token weight without influencing narrative generation for NPCs not currently interacting with the PC.
-   **<schema_drift>** (pipeline: storytell, turns: [10]) — Tag: `<instruction_ignored>`. Fix: Clarify `goal_update` triggers. The update on T10 ("Identify the true employer...") was a minor refinement based on one conversation turn. Guidance should emphasize that `goal_update` is for *significant* shifts in campaign direction, not incremental clarifications, to prevent goal churn.

## ⚠️  Flagged

### `tokens_regression` — 12 stream(s) over the fail threshold (worst: extraction.storytell turn 9 +51.6%)

- `extraction.storytell` turn 1: 4739 → 7044 (+48.6%)
- `extraction.storytell` turn 2: 5042 → 7524 (+49.2%)
- `extraction.storytell` turn 3: 5098 → 7656 (+50.2%)
- `extraction.storytell` turn 4: 5142 → 7676 (+49.3%)
- `extraction.storytell` turn 5: 5328 → 7830 (+47.0%)
- `extraction.storytell` turn 6: 5470 → 7978 (+45.9%)
- `extraction.storytell` turn 7: 5529 → 7906 (+43.0%)
- `extraction.storytell` turn 8: 5445 → 8063 (+48.1%)
- `extraction.storytell` turn 9: 5345 → 8101 (+51.6%)
- `extraction.storytell` turn 10: 5811 → 8214 (+41.4%)
- `extraction.storytell` turn 11: 5824 → 8249 (+41.6%)
- `extraction.storytell` turn 12: 5648 → 8242 (+45.9%)


## Auto-Checker

**307 passed, 30 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `ruling.rolled` | ✅ | rolled=False |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=opportunity |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 1 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='opportunity', counter=0 |
| 1 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 1 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 1 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 1 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 1 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 1 | `universal.inventory.remove_existence` | ✅ | (first turn) |
| 1 | `universal.thread_update.valid_id` | ✅ | no thread_updates |
| 1 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 1 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 1 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 1 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 2 | `ruling.rolled` | ❌ | rolled=False |
| 2 | `storytell.extract.thread_update` | ✅ | thread_update[settle_the_debt] found |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 2 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 2 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 2 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 2 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 2 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 2 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 2 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 2 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 2 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 2 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 2 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 2 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 2 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 2 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 3 | `ruling.rolled` | ❌ | rolled=False |
| 3 | `storytell.extract.thread_update` | ✅ | thread_update[deliver_the_ledger] found |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 3 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 3 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 3 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 3 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 3 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 3 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 3 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 3 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 3 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 3 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 3 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 4 | `ruling.rolled` | ✅ | rolled=False |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=pressure |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing -> crossed_keys_entrance |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in compendium_npc_update or known: ['Marrow'] |
| 4 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'transition' rendered in narrate prompt |
| 4 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 4 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='pressure', counter=1 |
| 4 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=1) |
| 4 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 4 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 4 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 4 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 4 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 4 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 4 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 4 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 4 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 5 | `ruling.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `storytell.extract.thread_update` | ✅ | thread_update[clear_the_road_toughs] found |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=complication |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 5 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | band=fail delta=-1 (expected -1, engine may clamp) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 5 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='complication', counter=2 |
| 5 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=2) |
| 5 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 5 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 5 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 5 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 5 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 5 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 5 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 5 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 5 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 6 | `ruling.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=200 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=pressure |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | band=fail delta=-1 (expected -1, engine may clamp) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 6 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'hold' rendered in narrate prompt |
| 6 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 6 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='pressure', counter=3 |
| 6 | `universal.pacing.beat_locked_dual_trigger` | ❌ | beat_locked=False but expected True (momentum=0, floor=-3, consecutive_pressure_turns=3, threshold=3) |
| 6 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 6 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 6 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 6 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `universal.inventory.remove_existence` | ✅ | checked 1 removes |
| 6 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 6 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['cornered'] |
| 6 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 6 | `universal.beat_type.variety` | ❌ | beats are 67% 'pressure' (threshold: 60%): {'pressure': 2, 'complication': 1} |
| 6 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 7 | `storytell.extract.thread_resolve` | ❌ | thread_resolve[deliver_the_ledger] not found (resolved: []) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=twist |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 7 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 7 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe; Resolve a Threat' rendered in storytell prompt |
| 7 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='twist', counter=0 |
| 7 | `universal.pacing.beat_locked_dual_trigger` | ❌ | beat_locked=True but expected False (momentum=0, floor=-3, consecutive_pressure_turns=0, threshold=3) |
| 7 | `universal.pacing.floor_relief` | ✅ | beat_locked=True, storytell emitted non-pressure beat 'twist' — floor relief did not override |
| 7 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 7 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 7 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 7 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 7 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 7 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 7 | `universal.beat_type.variety` | ✅ | beat variety OK: {'complication': 1, 'pressure': 1, 'twist': 1} |
| 7 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 8 | `ruling.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | band=success delta=1 (expected +1, engine may clamp) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 8 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 8 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 8 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 8 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 8 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 8 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 8 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 8 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 8 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['winded'] |
| 8 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 8 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 8 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 9 | `ruling.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat present but source unclear: type=revelation |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | band=partial delta=0 (expected +0, engine may clamp) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 9 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 9 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 9 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type='revelation', counter=0 |
| 9 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 9 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 9 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 9 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 9 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `universal.inventory.remove_existence` | ✅ | checked 1 removes |
| 9 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 9 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['winded'] |
| 9 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 9 | `universal.beat_type.variety` | ✅ | only 2 beat(s) in window (need >= 3) |
| 9 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 10 | `ruling.rolled` | ❌ | rolled=False |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat consumed (cleared) - no gm_beat emitted this turn |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 10 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 10 | `universal.storytell.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 10 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.narrate.outcome_hint_rendered` | ✅ | (no outcome_hint computed) |
| 10 | `universal.storytell.directive_rendered` | ✅ | (no directive computed) |
| 10 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 10 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=0) |
| 10 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 10 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 10 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 10 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 10 | `universal.thread_update.valid_id` | ✅ | no thread_updates |
| 10 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 10 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 10 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 10 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 11 | `ruling.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 11 | `extract.state.pc_condition_add` | ❌ | pc_condition_add[winded] not found |
| 11 | `extract.state.inventory_add` | ❌ | inventory_add[wax_sealed_cylinder] not found |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 11 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ❌ | band=partial expected delta +0 but got -1 (prev=-2 cur=-3) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 11 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe' rendered in storytell prompt |
| 11 | `universal.pacing.consecutive_pressure_tracking` | ❌ | gm_beat.type=None (not pressure) but consecutive_pressure_turns=1 (expected 0) |
| 11 | `universal.pacing.beat_locked_dual_trigger` | ✅ | beat_locked=False (momentum=0, consecutive_pressure_turns=1) |
| 11 | `universal.pacing.floor_relief` | ✅ | beat_locked=False, no floor relief expected |
| 11 | `universal.goal_update.applied` | ✅ | goal_update='Identify the true employer of the thugs to ensure safe delivery of the ledger.' → arc.visible_goal='Identify the true employer of the thugs to ensure safe delivery of the ledger.' |
| 11 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 11 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 11 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 11 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['winded'] |
| 11 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 11 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 11 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 12 | `ruling.rolled` | ❌ | rolled=True |
| 12 | `extract.state.pc_condition_remove` | ❌ | pc_condition_remove[winded] not found |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | band=fail delta=0 (expected -1, engine may clamp) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'advance' rendered in narrate prompt |
| 12 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe; Resolve a Threat' rendered in storytell prompt |
| 12 | `universal.pacing.consecutive_pressure_tracking` | ❌ | gm_beat.type='complication' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 12 | `universal.pacing.beat_locked_dual_trigger` | ❌ | beat_locked=True but expected False (momentum=0, floor=-3, consecutive_pressure_turns=0, threshold=3) |
| 12 | `universal.pacing.floor_relief` | ✅ | beat_locked=True, storytell_type='complication' → floor relief injected breathing_room |
| 12 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 12 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 12 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 12 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 12 | `universal.conditions.orphan` | ✅ | all conditions have CONDITION_MODS entries |
| 12 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 12 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 12 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |
| 13 | `ruling.rolled` | ❌ | rolled=True |
| 13 | `extract.state.pc_condition_remove` | ❌ | pc_condition_remove[bruised_ribs] not found |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.lifecycle_respected` | ✅ | beat injected by floor relief (breathing_room) — storytell emitted no beat |
| 13 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: river_docks |
| 13 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.storytell.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | band=fail delta=0 (expected -1, engine may clamp) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.narrate.outcome_hint_rendered` | ✅ | outcome_hint 'transition' rendered in narrate prompt |
| 13 | `universal.storytell.directive_rendered` | ✅ | directive 'Breathe; Resolve a Threat' rendered in storytell prompt |
| 13 | `universal.pacing.consecutive_pressure_tracking` | ✅ | gm_beat.type=None, counter=0 |
| 13 | `universal.pacing.beat_locked_dual_trigger` | ❌ | beat_locked=True but expected False (momentum=0, floor=-3, consecutive_pressure_turns=0, threshold=3) |
| 13 | `universal.pacing.floor_relief` | ✅ | beat_locked=True, storytell_type=None → floor relief injected breathing_room |
| 13 | `universal.goal_update.applied` | ✅ | (no goal_update emitted) |
| 13 | `universal.directives.no_removed` | ✅ | no removed directives in rendered prompts |
| 13 | `universal.npc_states.no_removed` | ✅ | no removed NPC states detected |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `universal.inventory.remove_existence` | ✅ | checked 0 removes |
| 13 | `universal.thread_update.valid_id` | ✅ | checked 1 thread_updates |
| 13 | `universal.conditions.orphan` | ❌ | conditions with no CONDITION_MODS entry: ['scraped_and_bruised'] |
| 13 | `universal.thread_add.applied` | ✅ | all thread_add signals produced state mutations |
| 13 | `universal.beat_type.variety` | ✅ | only 1 beat(s) in window (need >= 3) |
| 13 | `universal.beat_type.surface_as_consistency` | ✅ | no surface_as drift detected |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 3 | 3 | T5 |
| `extract.state.inventory_add` | 🔴 | 1 | 1 | T11 |
| `extract.state.inventory_remove` | 🔴 | 1 | 2 | T8 |
| `extract.state.pc_condition_add` | 🔴 | 1 | 1 | T11 |
| `extract.state.pc_condition_remove` | 🔴 | 2 | 2 | T12 |
| `ruling.rolled` | 🔴 | 5 | 12 | T2 |
| `storytell.extract.thread_resolve` | 🔴 | 1 | 1 | T7 |
| `storytell.extract.thread_update` | 🔴 | 0 | 3 | — |
| `universal.beat_type.surface_as_consistency` | 🟡 | 0 | 13 | — |
| `universal.beat_type.variety` | 🟡 | 1 | 13 | T6 |
| `universal.conditions.orphan` | 🔴 | 5 | 13 | T6 |
| `universal.directives.no_removed` | 🟡 | 0 | 13 | — |
| `universal.goal_update.applied` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.inventory.remove_existence` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 1 | 13 | T13 |
| `universal.momentum.band_delta` | 🔴 | 1 | 13 | T11 |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.outcome_hint_rendered` | 🔴 | 0 | 13 | — |
| `universal.npc_mention.extracted` | 🔴 | 1 | 13 | T4 |
| `universal.npc_states.no_removed` | 🟡 | 0 | 13 | — |
| `universal.pacing.beat_locked_dual_trigger` | 🟡 | 4 | 13 | T6 |
| `universal.pacing.consecutive_pressure_tracking` | 🟡 | 2 | 13 | T11 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pacing.floor_relief` | 🟡 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.lifecycle_respected` | 🟡 | 0 | 13 | — |
| `universal.storytell.actions_quality` | 🔴 | 1 | 13 | T10 |
| `universal.storytell.directive_rendered` | 🟡 | 0 | 13 | — |
| `universal.thread_add.applied` | 🔴 | 0 | 13 | — |
| `universal.thread_update.valid_id` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Thread Duration

| Thread ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `clear_the_road_toughs` | T1 | T12 | 12 | ⚠️ >8 turns |
| `deliver_the_ledger` | T1 | T12 | 12 | ⚠️ >8 turns |
| `mysterious_watchers` | T2 | T12 | 11 | ⚠️ >8 turns |
| `settle_the_debt` | T1 | T12 | 12 | ⚠️ >8 turns |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_entrance` | 8 | ⚠️ >4 turns |
| `marrows_crossing` | 3 |  |
| `river_docks` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `cornered` | T6 | T6 | 1 |  |
| `scraped_and_bruised` | T13 | T13 | 1 |  |
| `winded` | T8 | T11 | 4 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1923 (-4) | 3256 (+78) | 2873 (-86) | 3639 (-147) | 7044 (+2305) | 0 | 0 | 31.51 |
| 2 | I slide 500 credits across the table to Caron an… | 2182 (-128) | 3523 (-6) | 3137 (-188) | 3672 (-129) | 7524 (+2482) | 0 | 0 | 28.58 |
| 3 | I find Halden by the town well and offer to carr… | 2217 (-94) | 3598 (+58) | 3149 (-137) | 3663 (-40) | 7656 (+2558) | 0 | 0 | 31.08 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 2265 (-14) | 3738 (+154) | 3165 (-130) | 3647 (-87) | 7676 (+2534) | 0 | 0 | 27.33 |
| 5 | I walk up to the two toughs at the inn door and … | 2149 (-87) | 3811 (+108) | 3121 (-247) | 3672 (-136) | 7830 (+2502) | 0 | 0 | 27.28 |
| 6 | I drop 200 credits on the ground between the tou… | 2179 (-128) | 3882 (-8) | 3166 (-309) | 3690 (-138) | 7978 (+2508) | 0 | 0 | 31.24 |
| 7 | I sit across from Halden at his table, slide the… | 2185 (-134) | 3914 (+65) | 3142 (-356) | 3675 (-166) | 7906 (+2377) | 0 | 0 | 30.44 |
| 8 | I pull out the brass key Halden gave me and try … | 2153 (-212) | 3959 (+8) | 3140 (-223) | 3695 (+16) | 8063 (+2618) | 0 | 0 | 33.20 |
| 9 | I press my ear against the inn's stone wall and … | 2191 (-14) | 4070 (+233) | 3188 (-59) | 3696 (-28) | 8101 (+2756) | 0 | 0 | 31.94 |
| 10 |  | — | — | 0 (-3346) | 0 (-3778) | 0 (-5572) | 0 | 0 | 29.44 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 2181 (-129) | 4157 (+51) | 3197 (-270) | 3723 (-119) | 8214 (+2403) | 0 | 0 | 30.36 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 2202 (-167) | 4195 (-59) | 3207 (-272) | 3679 (-112) | 8249 (+2425) | 0 | 0 | 30.98 |
| 12 | I grab the ledger from my coat and sprint out th… | 2178 (-137) | 4280 (+275) | 3164 (-230) | 3677 (-118) | 8242 (+2594) | 0 | 0 | 30.65 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 2187 | 4200 | 3119 | 3671 | 8304 | 0 | 0 | 0.00 |
|  | TOTALS | 28192 | 50583 | 40768 | 47799 | 102787 | 0 | 0 | 394.03 |

**Total turns:** 14 · **Total duration:** 394.03s · **Avg/turn:** 28.14s
**Total tokens in:** 270,129 · **Total tokens out:** 9,826 · **Total LLM time:** 393.5s
**Total retries:** 0 · **Total parse failures:** 0

