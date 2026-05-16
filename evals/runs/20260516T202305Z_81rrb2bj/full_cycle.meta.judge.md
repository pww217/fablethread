***
mechanical_score: 2
narrative_score: 2
system_cohesion_score: 2
prompt_quality_score: 4
compaction_score: 3
state_fidelity_rate: 0.65
prompt_adherence_rate: 0.94
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | `extraction_accuracy_score` (avg ~2.5) + `mechanic_lifecycle_score` (avg ~2.0) | **2** | Critical failures in state application (location drift, inventory loops) and mechanic lifecycle (stuck arcs, stale conditions) indicate a broken core loop. |
| `narrative_score` | narrative_interplay | `narrative_score` (avg ~2.0) | **2** | Narration is disconnected from state. Pressures are inert, conditions are phantom, and arc threads are ignored. The story does not reflect the mechanics. |
| `system_cohesion_score` | narrative_interplay | `system_cohesion_score` (avg ~2.0) | **2** | Severe decoupling between the State Engine and the Narrator. State changes (pressures, conditions) are not reflected in the prose, and narrative cues are not driving state updates effectively. |
| `prompt_quality_score` | prompt_pipeline | `prompt_quality_score` (4) | **4** | The prompts themselves are well-structured and adhere to instructions well (0.94 adherence). The issue is not prompt design, but prompt *application* or *context injection*. |
| `compaction_score` | compaction | `compaction_score` (3) | **3** | Compaction is functional but has a specific data leakage bug (T9 includes T10). It is not the primary failure point but indicates sloppy data hygiene. |
| `state_fidelity_rate` | state_correctness | `state_fidelity_rate` (0.65) | **0.65** | Significant drift. Location changes are not applied, inventory has negative/invalid deltas, and conditions persist indefinitely. |
| `prompt_adherence_rate` | prompt_pipeline | `prompt_adherence_rate` (0.94) | **0.94** | The LLM follows the prompt instructions technically, but the instructions themselves may be missing critical context (e.g., pressure directives) or the LLM is failing to *use* that context effectively despite following format. |

***

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: **Contradiction Found.** `state_correctness` identifies that pressures are "clean" (no removal flags) but `narrative_interplay` says they are "inert" (no story consequence). **Resolution:** The state engine is technically correct (the pressure exists in the JSON), but the *system cohesion* is broken because the Narrator pipeline is not receiving or rendering that state. The state is "clean" but "dead."
- **state_correctness vs prompt_pipeline**: **Contradiction Found.** `state_correctness` says extraction is failing (inventory loops, location drift), but `prompt_pipeline` rates extraction prompts highly (4/5) and adherence high (0.94). **Resolution:** The prompts are syntactically correct, but semantically insufficient. The "Zero-Tolerance" rule for inventory exists in the prompt but is being ignored or overridden by the LLM's tendency to hallucinate deltas. The prompt quality is high, but the *robustness* of the extraction against LLM drift is low.
- **narrative_interplay vs prompt_pipeline**: **Contradiction Found.** `narrative_interplay` says directives are ignored, but `prompt_pipeline` says narrate prompt adherence is good. **Resolution:** The Narrator prompt is adhering to its *format* (generating prose), but it is failing to adhere to its *content directive* (incorporating pressure/arc context). The `narrate_user.j2` template is likely missing the variable injection for `scene_pressure` or `arc_thread`, causing the LLM to narrate based on limited context.
- **state_correctness vs narrative_interplay (arc threads)**: **Contradiction Found.** `state_correctness` says arc thread lifecycle is clean (no flags) but engagement is stuck at -1. `narrative_interplay` says threads produce no story consequence. **Resolution:** The arc mechanic is broken in the *scoring logic* (stuck at -1), not just the narrative. The state is "clean" because it's stuck, not because it's progressing.
- **narrative_interplay vs state_correctness (pressures)**: **No Contradiction.** Both agree pressures are problematic. `state_correctness` says they aren't removed; `narrative_interplay` says they are removed too late. This is consistent: the state holds them too long, and the narrative doesn't reflect them until it's too late.

***

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Broken.** Momentum is not explicitly tracked in the issues, but the "stuck" nature of arcs and conditions suggests momentum is not recovering. The system is static.
2. **GM beat narration** — **Degraded.** Beats are generated (per prompt adherence) but are "silent state drivers" because the context (pressures/conditions) is not injected into the narrator.
3. **Scene pressure chains** — **Broken.** Pressures are "inert" (narrative) and "late removed" (state). They do not escalate or create consequences.
4. **Condition deduplication** — **Degraded.** `bruised_ribs` is stale (never removed). `low_morale` and `exhausted` are phantom (not narrated). Deduplication is working, but *resolution* is failing.
5. **Arc thread progression** — **Broken.** Engagement is stuck at -1. Threads do not advance from latent to active.
6. **Inventory extraction accuracy** — **Broken.** `inventory_remove` is emitted for non-existent items (credits). This is a critical data integrity failure.
7. **Location change application** — **Broken.** Location deltas are emitted but not applied to state (`schema_drift`). The player's location in state does not match the narrative.
8. **NPC mention extraction** — **Degraded.** High noise (common nouns flagged as NPCs). Extraction is technically happening but is noisy.
9. **Progress actions pipeline** — **Degraded.** Fails to generate required 4 actions. Also ignores `narration_directive`.

**Data Missing/Gap Analysis:**
1. **Missing Context Injection:** The most critical missing data is the *injection* of state variables (pressures, arcs, conditions) into the Narrator's prompt context. The Narrator is flying blind.
2. **Systematic Gap:** The `_apply_delta` logic for location and inventory is failing. This is a code/logic gap, not a prompt gap.
3. **Recommendation:** Fix the state application logic first. Then, inject state variables into the Narrator prompt.

***

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Inject `scene_pressure`, `arc_thread`, and `condition` data into the Narrator's prompt context (`narrate_user.j2`)** to resolve the "Inert Scene Pressures" and "Phantom Conditions" issues, as the Narrator is currently generating prose without awareness of the active mechanical state.

### Key Findings
1. **State-Narrator Decoupling:** The Narrator is not receiving pressure/arc context, leading to "inert" mechanics and "phantom" conditions (Narrative Interplay, Turns 4-9).
2. **Critical State Drift:** Location changes are emitted but not applied, and inventory removals target non-existent items, causing data corruption (State Correctness, Turns 6, 10, 12).
3. **Arc Mechanic Stagnation:** Arc engagement is stuck at -1 and fails to recover, indicating a flaw in the `tick_arc` scoring logic (State Correctness, Turns 11-13).
4. **Prompt Adherence vs. Robustness:** While prompt adherence is high (0.94), the LLM fails to follow "Zero-Tolerance" inventory rules, suggesting the need for stronger constraint enforcement or few-shot examples (Prompt Pipeline, Turns 6, 13).

### Regression Check
*No previous run scores provided for comparison.*