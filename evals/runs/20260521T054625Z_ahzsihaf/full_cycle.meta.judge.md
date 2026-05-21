***
mechanical_score: 2
narrative_score: 1
system_cohesion_score: 1
prompt_quality_score: 3
compaction_score: 5
state_fidelity_rate: 0.0
prompt_adherence_rate: 0.6
***

## SECTION 1 — Score Synthesis

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | avg(2, 2) = 2.0 | None | State extraction is fundamentally broken (schema drift, location failures). Mechanics are present but non-functional due to data corruption at the source. |
| `narrative_score` | narrative_interplay | 1.0 | None | Narrative completely ignores mechanical directives (Success bands treated as Failures/Complications only). Thread expiration logic is hallucinated against narrative reality. Tone and mechanics are decoupled. |
| `system_cohesion_score` | narrative_interplay | 1.0 | None | The system fails to connect state changes to narrative consequences. GM beats vanish; thread expirations contradict story continuity; momentum bands dictate wrong outcomes. Total lack of cohesion between engine rules and output. |
| `prompt_quality_score` | prompt_pipeline | 3.0 | -0.5 (Adjusted) | Prompts are structurally sound but contain specific instruction gaps regarding item persistence, NPC movement logic, and event deduplication. The "World Pack" waste is minor but indicates poor optimization. Base score reflects functional prompts with known bugs. |
| `compaction_score` | compaction | 5.0 | None | No issues found in the provided summary for this judge. Assuming clean pipeline execution where data was available (though state correctness suggests data availability is low). |
| `state_fidelity_rate` | state_correctness | 0.0 | None | Explicitly reported as 0.0 due to critical schema drift and location update failures. State does not reflect reality. |
| `prompt_adherence_rate` | prompt_pipeline | 0.6 | -0.1 (Adjusted) | Prompts are being followed generally, but specific instructions on item retention and NPC movement are ignored by the LLM extractors, leading to data loss. Adherence is partial. |

## SECTION 2 — Inter-Judge Contradiction Check

- **state_correctness vs narrative_interplay**: No direct contradiction; rather, a causal link. State correctness reports extraction failures (location ID rejection), while narrative interplay reports that the resulting state leads to broken thread expiration and momentum mismatches. The "contradiction" is that narrative judges see *consequences* of state bugs as independent narrative flaws.
- **state_correctness vs prompt_pipeline**: No contradiction. Prompt pipeline identifies specific instruction gaps (item removal, NPC movement) which directly cause the extraction errors flagged by state correctness (e.g., incorrect item counts or missing NPCs in scene).
- **narrative_interplay vs prompt_pipeline**: Contradiction on "Directive Ignored" vs "Instruction Ignored". Narrative says the *Narrator* ignored momentum bands. Prompt pipeline says *Extractors* have instruction gaps. The issue is likely twofold: Extractors provide bad data (due to prompt issues), AND the Narrator prompt fails to interpret whatever state it receives correctly regarding band outcomes.
- **state_correctness vs narrative_interplay (unified threads)**: Contradiction on "Thread Expiration". State correctness doesn't explicitly flag thread lifecycle errors in its summary, but Narrative Interplay flags `false_expiration` at Turn 9. This suggests the Thread Manager logic is either not being triggered by state changes or is evaluating conditions incorrectly independent of extraction accuracy.
- **narrative_interplay vs state_correctness (PacingContext)**: Contradiction on Band/Narration alignment. State correctness focuses on data integrity; Narrative Interplay focuses on semantic alignment. The core issue is that the Narrator prompt likely lacks explicit instructions to map `momentum.band` -> `outcome_type`, causing it to default to "complication-heavy" narration regardless of success bands.

## SECTION 3 — Trace Quality Synthesis

1. **Momentum lifecycle** — **Broken**. Momentum tracks mechanically (bands are generated), but the narrative output ignores them. Success bands result in failure-like prose. The mechanic exists but is decoupled from the story engine.
2. **GM beat narration** — **Broken**. Beats are generated (e.g., "tighten perimeter" at T8) but vanish from subsequent turns. There is no mechanism to surface pending beats into active narrative or NPC dialogue.
3. **Unified thread chains** — **Broken**. Threads expire based on arbitrary progress thresholds rather than narrative resolution, leading to contradictions where antagonists are still hunting the player after a "complete" tag.
4. **Condition deduplication** — **Degraded**. Schema drift at Turn 1 (future dates) corrupts condition tracking. Phantom conditions appear/disappear without narrative justification.
5. **Arc thread progression** — **Broken**. Scope-aware rules are failing; scene-scoped threads likely aren't expiring on location change correctly, and arc-scoped threads expire prematurely based on non-narrative metrics.
6. **Inventory extraction accuracy** — **Degraded**. Reusable items (keys) are removed upon use due to prompt instruction gaps in the Extract State pipeline.
7. **Location change application** — **Broken**. Location ID updates fail at Turns 4, 10, and 12. The engine rejects valid location deltas, causing state stagnation or errors during movement.
8. **NPC mention extraction** — **Degraded**. High false positive rate for NPC mentions (common words vs proper nouns). Additionally, NPCs are incorrectly removed from scenes when they move with the player due to prompt instruction gaps in Extract Scene.
9. **Progress actions pipeline** — **Degraded**. Extraction misses actionable steps frequently. Duplicates recent events across turns instead of tracking deltas.

**Trace Quality Assessment:**
1. What data was missing? Explicit `momentum.band` values and their intended semantic mapping (e.g., "Success" -> "Goal Achieved + Complication") were not clearly linked in the trace analysis, though implied by narrative complaints.
2. Systematic gap: The **Narrator Prompt** lacks a strict directive to align prose with mechanical outcomes (bands). It treats all inputs as potential complications regardless of success/fail state. Additionally, the **State Extractor Prompts** lack explicit "persistence" rules for items and NPCs during transitions.
3. Recommendation for trace improvement: Include raw `PacingContext` objects in the trace logs to verify if the Narrator is receiving correct band data before judging narrative tone.

## SECTION 4 — Final Verdict

### Highest-Priority Fix
**Rewrite the Narrator Prompt's Outcome Mapping Logic:** Explicitly define how each Momentum Band (Success, Partial, Fail) must translate into specific narrative outcomes (e.g., Success = Primary Intent Achieved + Optional Complication; Fail = Primary Intent Failed), forcing alignment between mechanical state and prose.

### Key Findings
- **Narrative/Mechanic Decoupling**: Narrative Interplay reports that "Success" bands are narrated as failures/setbacks, indicating the Narrator prompt ignores momentum directives (Turns 8, 10).
- **State Extraction Corruption**: State Correctness identifies critical schema drift at Turn 1 and repeated location ID update failures, rendering state fidelity at 0.0% (Turns 4, 10, 12).
- **Prompt Instruction Gaps**: Prompt Pipeline highlights that Extractors incorrectly remove reusable items and NPCs during movement due to missing explicit persistence instructions in the prompts (Turns 8, 10).

### Regression Check
*Note: Previous run scores were not provided in the input. Assuming baseline comparison is unavailable.*