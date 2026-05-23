***
mechanical_score: 3
narrative_score: 2
system_cohesion_score: 2
prompt_quality_score: 3
compaction_score: 1
state_fidelity_rate: 0.85
prompt_adherence_rate: 0.75
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | avg(3, 4) = 3.5 | -0.5 | State fidelity is high (1.0), but extraction accuracy (3/5) indicates critical data corruption (credits/items). The mechanic lifecycle works logically, but the input data is often wrong. Adjusted down to reflect that "correct mechanics" on "corrupt state" yields poor mechanical outcomes. |
| `narrative_score` | narrative_interplay | 2 | 0 | Narrative suffers from causality breaks (ledger/NPC ghosting) and phantom conditions. The tone is likely inconsistent due to missing context. Score reflects the disconnect between state events and prose consequences. |
| `system_cohesion_score` | narrative_interplay | 2 | -1 | High contradiction: State says one thing, Narrative shows another (Halden's location, Ledger ownership). This indicates a failure in the feedback loop between extraction and generation. The system is not cohesive; it is fragmented. |
| `prompt_quality_score` | prompt_pipeline | 3 | 0 | Prompts are functional but lack robustness for edge cases (deduplication, implicit payments). They pass basic adherence but fail on complex semantic parsing required for continuity. |
| `compaction_score` | compaction | 1 | -1 | No pipeline scores provided in input (`pipeline_scores: {}`). However, the presence of "Phantom Item Lifecycle" and "NPC Ghosts" implies that the compaction/cleanup phase failed to reconcile state drift or merge NPC data correctly. A score of 1 reflects this total lack of visible sanitization fidelity. |
| `state_fidelity_rate` | state_correctness | 1.0 | -0.15 | While the *structure* is maintained (schema valid), the *content* is corrupted (credits dropped to 5, ledger phantom). Fidelity implies truthfulness to source/narrative. The extraction misses are significant enough to warrant a penalty despite structural integrity. |
| `prompt_adherence_rate` | prompt_pipeline | 0.75 | -0.1 | Adherence is good for simple actions but fails on complex semantic instructions (deduplication, implicit currency mapping). Deductions applied for the specific failures in T9 and T13 noted by judges. |

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: 
    - *Contradiction*: `state_correctness` reports high state fidelity (1.0) but notes extraction misses (`extraction_miss`). `narrative_interplay` reports "Inventory/Thread Causality Break" and "NPC Silently Relocated."
    - *Resolution*: This is not a contradiction of fact, but of **perception**. State correctness judges the *schema* as valid (no crashes), while narrative interplay judges the *semantic truth* as broken. The state engine thinks it's working because the JSON structure holds; the narrative judge sees that the story logic has collapsed because the data extracted was wrong (credits) or missing (Halden).
    - *Why*: The extraction pipeline is failing to capture semantic intent (implicit payments, NPC movement), leading to a "clean" but "empty/wrong" state.

- **state_correctness vs prompt_pipeline**: 
    - *Contradiction*: `prompt_pipeline` rates prompts as having issues with deduplication and implicit rules (`instruction_ignored`). `state_correctness` flags these same issues as extraction misses.
    - *Resolution*: Consistent finding. The root cause is identified in both: the prompts do not enforce strict semantic mapping for complex actions (like bribes or NPC tracking).

- **narrative_interplay vs prompt_pipeline**: 
    - *Contradiction*: `prompt_pipeline` notes that progress pipeline advances/resolves threads incorrectly (T2). `narrative_interplay` notes thread stagnation/inert mechanics (T5-13).
    - *Resolution*: Consistent. The system oscillates between over-resolving and under-managing threads due to unclear prompt directives on scope-aware rules.

- **state_correctness vs narrative_interplay (unified threads)**: 
    - *Contradiction*: `narrative_interplay` says threads produce no story consequence (stagnation). `state_correctness` doesn't explicitly flag thread lifecycle as broken, but notes "Phantom Item" issues which are often tied to thread resolution.
    - *Resolution*: The thread mechanics are likely functioning in isolation (flags toggling), but failing because the *context* (location change) isn't being passed correctly from state extraction to the progress pipeline.

- **narrative_interplay vs state_correctness (PacingContext)**: 
    - *Contradiction*: None explicitly stated regarding PacingContext directives in the provided summaries, but the "Low Morale Phantom Condition" suggests a disconnect between condition application and narrative tone.
    - *Resolution*: The system applies conditions mechanically but fails to narrate them, breaking immersion.

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Degraded**. While `mechanic_lifecycle_score` is 4/5, the corruption of credits (T3-4) suggests momentum/economy tracking is unstable. If currency defaults to small integers, economic momentum is broken.
2. **GM beat narration** — **Broken**. The "Low Morale Phantom Condition" (T2) and NPC ghosting indicate that state changes are not being translated into observable prose beats. The GM is narrating over a broken state map.
3. **Unified thread chains** — **Broken**. Threads are either resolved prematurely without narrative closure (T2, T7 ledger handover vs T12 grab) or stagnate indefinitely despite location changes (T5-13). Scope-aware rules are failing to trigger expiration/demotion.
4. **Condition deduplication** — **Degraded**. `state_correctness` notes extraction misses; `prompt_pipeline` notes NPC duplication issues. Conditions likely suffer from similar lack of idempotency checks in the prompt, leading to phantom or missing conditions (T2).
5. **Arc thread progression** — **Broken**. As noted above, threads do not advance via scope-aware rules correctly. They either resolve incorrectly or stall because the "location change" trigger isn't being detected by the progress pipeline due to extraction errors.
6. **Inventory extraction accuracy** — **Critical Failure**. Credits dropped from ~500 to 5 (T3-4). Ledger item lifecycle is broken (added/removed/re-added inconsistently T7, T12). This is a systemic failure in the `extract_state` prompt's handling of numerical values and implicit ownership.
7. **Location change application** — **Degraded**. NPC Halden moves from Inn to Docks without state update or narration (T7-T13). This implies location deltas are either not being extracted correctly for NPCs, or the `present_npcs` list is not being updated/checked against new locations during compaction.
8. **NPC mention extraction** — **Broken**. Duplicate NPC 'scarred_tough' added in T9 (T9). Halden's movement ignored. The scene extractor fails to deduplicate and track entity persistence across location changes.
9. **Progress actions pipeline** — **Degraded**. Thread resolution logic is flawed (advancing and resolving same thread in one turn, T2), leading to narrative discontinuity later when the player interacts with resolved threads as if they are active (T12).

**Trace Quality Assessment:**
- **Missing Data**: The trace lacks explicit `event_log` entries for NPC movement or item transfers that contradict state. Without a log of *intent* vs *state*, it's hard to debug whether the prompt failed extraction or generation.
- **Systematic Gap**: All judges point to a lack of **semantic grounding** in prompts. Prompts treat "200 credits" as text rather than value, and NPC names as strings rather than persistent entities with location scopes.
- **Recommendation for Trace Improvement**: Add `debug_extraction` logs that show the raw parsed values (e.g., `"credits": 5`) alongside the narrative input to immediately identify if the failure is in parsing or state application.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Implement strict semantic extraction rules for currency and entity persistence:** Update the `extract_state` prompt to explicitly parse numerical values as integers (preventing default-to-5 errors) and enforce a mandatory deduplication check against the full NPC compendium before emitting scene data, citing **state_correctness** (Inventory Balance Corruption) and **prompt_pipeline** (Scene Extractor Deduplication Failure).

### Key Findings
1. **Critical Data Corruption**: Inventory credits dropped from ~500 to 5 due to extraction parsing failure (Turns 3-4), causing immediate mechanical imbalance (**state_correctness**, Critical Issue).
2. **Narrative-State Disconnect**: NPC Halden moved locations silently, and the Ledger item lifecycle was broken across turns 7 and 12, creating a "ghost" state that contradicts narrative events (**narrative_interplay**, Critical Issues; **prompt_pipeline**, Major Issues).
3. **Thread Logic Failure**: Threads are either resolved prematurely without narrative closure or stagnate because location-change triggers are not being detected by the progress pipeline due to extraction errors (Turns 2, 5-13) (**narrative_interplay**, Minor/Major Issues; **prompt_pipeline**, Major Issue).

### Regression Check
*Note: Previous run scores were not provided in the input. Assuming baseline comparison is impossible.*
However, based on the severity of "Critical" tags across multiple judges (State, Narrative, Prompt), this system appears to be in a state of **high instability**. The combination of extraction errors and narrative disconnects suggests that previous fixes may have addressed surface-level schema issues but failed to address semantic parsing robustness.