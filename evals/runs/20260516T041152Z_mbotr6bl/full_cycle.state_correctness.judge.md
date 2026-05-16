

state_fidelity_rate: 0.12
extraction_accuracy_score: 2
mechanic_lifecycle_score: 3

***

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 1-4 | — | 0 | 0→0 | — |
| 5 | fail | -1 | 0→-1 | — |
| 6 | setback | -1 | -1→-2 | — |
| 7 | — | 0 | -2→-2 | — |
| 8 | fail | -1 | -2→-3 | — |
| 9 | partial | 0 | -3→-3 | FLAT |
| 10 | success | +1 | -3→-2 | — |
| 11 | fail | -1 | -2→-3 | — |
| 12 | partial | 0 | -3→-3 | FLAT |
| 13 | — | 0 | -3→-3 | — |

**Assessment:** Momentum responds correctly to dice rolls across the run. Matches `momentum_delta` constants exactly.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| 5 | escalation | consume | Beat added to state | Yes | REPLACE_FAIL |
| 6 | escalation | replace | Beat updated | Yes | — |
| 7 | escalation | replace | Beat updated | Yes | — |
| 8 | escalation | replace | Beat updated | Yes | — |
| 9 | opportunity | replace | Beat updated | Yes | — |
| 10 | revelation | replace | Beat updated | Yes | — |
| 11 | pressure | replace | Beat updated | Yes | — |
| 12 | pressure | replace | Beat updated | Yes | — |

**Assessment:** Beat TTL respected. T5 disposition says `consume` but state shows beat stored; likely a logging/direction mismatch.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|
| tough_hostility | 5 | immediate | Yes | 10 | 5 | — |
| imminent_violence | 6 | immediate | Yes | 9 | 3 | — |
| imminent_physical_pin | 7 | immediate | Yes | 9 | 2 | — |
| matthew_retaliation | 11 | immediate | Yes | 12 | 1 | — |
| pursuit_at_docks | 12 | immediate | No | — | 1 | UNRESOLVED_AT_END |

**Assessment:** Lifecycle correctly handles add/update/remove. `pursuit_at_docks` remains active at trace end.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| bruised_ribs | 1 | engine | 12 | 11 | OVERLONG |
| low_morale | 1 | engine | 2 | 1 | — |
| winded | 6 | roll | 8 | 2 | — |
| winded | 9 | roll | 9 | 0 | DUPLICATE |
| winded | 10 | roll | 10 | 0 | DUPLICATE |
| stabilized_ribs | 12 | narrative | — | 1 | — |

**Assessment:** `winded` added/removed multiple times, sometimes same turn. `bruised_ribs` persists beyond design intent.

### 1E — Arc Thread Lifecycle Table

| Thread ID | Created (Tn) | State | Progress | Completed (Tm) | Flag |
|-----------|--------------|-------|----------|----------------|------|
| settle_the_debt | 1 | active | 2 | — | STALLED |
| deliver_the_ledger | 1 | active | 2 | 6 | FAILED_NO_SIGNAL |
| clear_the_road_toughs | 1 | active | 1 | 9 | FAILED_NO_SIGNAL |
| caron's_flicker... | 2 | active | 1 | — | — |
| the_merchant_at_the... | 3 | active | 2 | — | — |
| the_source_of_the... | 7 | active | 0 | — | STALLED |

**Assessment:** Two threads stalled at progress 0/1. `deliver_the_ledger` & `clear_the_road_toughs` failed without explicit FAILED signals in progress extract.

### 1F — Arc Engagement Table

| Turn | arc_engagement | Drift Match? | Δ Engagement | Flag |
|------|----------------|--------------|--------------|------|
| 1 | 1 | Yes | +1 | — |
| 2 | 2 | Yes | +1 | — |
| 3 | 3 | Yes | +1 | MAX_REACHED |
| 4-5 | 3 | Yes | 0 | MAX_REACHED |
| 6 | 2 | No | -1 | — |
| 7 | 3 | Yes | +1 | MAX_REACHED |
| 8 | 3 | Yes | 0 | MAX_REACHED |
| 9 | 2 | No | -1 | — |
| 10-13 | 3 | Yes | +1/-1 | MAX_REACHED |

**Assessment:** Engagement correctly caps at +3. Fluctuates based on thread signal matches.

### 1G — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | remove | credits | 500 | No | — |
| 3 | add | halden_ledger | 1 | No | — |
| 6 | remove | credits | 200 | Yes | SPENDING_MISS |
| 10 | add | charcoal_stub | 1 | No | — |
| 10 | add | scrap_parchment | 1 | No | — |
| 13 | remove | credits | 1 | Yes | SPENDING_MISS |

**Assessment:** Credits correctly depleted to 0 at T2. Subsequent removal attempts correctly rejected by engine validator.

***

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory, conditions, and arc threads show minor divergence. `credits` correctly hit 0 at T2, but extraction pipeline repeatedly attempts removal at T6/T13. `winded` condition lifecycle is noisy (added/removed same-turn at T9/T10). `bruised_ribs` persists from T1 despite seed state having none, suggesting carry-over from a prior session or engine pre-load. Arc threads `deliver_the_ledger` and `clear_the_road_toughs` transition to `failed` state without explicit `FAILED` signals in the progress extract, relying on implicit engine logic.

### 2B — Extraction Drift
- **T6, T13**: `inventory_remove` for `credits` when `amount` is 0. Pipeline emitted a structurally valid delta, but engine validator rejected it. **Type:** `validation_rejection` / `extraction_miss` (pipeline should check current stock before emitting removal).
- **T1, T3, T4, T5, T10, T11**: `npc_mention.extracted` failures. Narration references names not captured in `npc_add/update`. **Type:** `schema_drift` (scene extract under-captures named entities from prose).
- **T3, T6, T9, T12**: `progress.actions_quality` failures. `actions` array is empty. **Type:** `extraction_miss` (progress pipeline fails to generate suggested choices).

### 2C — State Fidelity Rate Calculation
Total turns in metrics: 17
Turns with rejected deltas OR auto-checker failures OR detected drift: 15 (T1, T3, T4, T5, T6, T7, T9, T10, T11, T12, T13 + duplicate empty turns)
Clean turns: 2 (T2, T8)
Arithmetic: 2 / 17 = 0.1176 → **0.12**

***

## SECTION 3 — Auto-Checker Failure Analysis

1. **`universal.npc_mention.extracted` (T1, T3, T4, T5, T10, T11)**
   - True failure. Narration mentions names not reflected in scene extraction deltas.
   - Root cause: Scene extract pipeline fails to map all named entities from prose to `npc_add/update` deltas.
   - Tag: `extraction_miss`

2. **`universal.progress.actions_quality` (T3, T6, T9, T12)**
   - True failure. Progress extract emits empty `actions` list.
   - Root cause: Progress extractor omits the 4-choice suggestion block.
   - Tag: `extraction_miss`

3. **`universal.location_change.applied` (T4, T10, T12)**
   - True failure. Scene extract emits `location_change`, but `state.location.id` remains unchanged.
   - Root cause: `apply_delta()` or state merge logic fails to overwrite location ID when description/name match or when delta is merged late.
   - Tag: `engine_bug`

4. **`universal.narrate.pressure_directive_rendered` (T4, T5, T6, T7, T9)**
   - True failure. Immediate pressures exist in state but narrator prompt lacks directive.
   - Root cause: `scene_pressure` state is not correctly passed to `_narrate_messages()` inputs before streaming.
   - Tag: `scope_violation`

***

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**State cap reason:** Repeated extraction failures across multiple pipelines. Progress extract consistently omits `actions` (4 turns). Scene extract misses NPC name mapping (6 turns). State extract attempts invalid inventory removals on depleted stock (2 turns). These are systematic pipeline gaps, not isolated noise.

### Mechanic Lifecycle Score: 3/5
**State cap reason:** Core mechanics (momentum, GM beat TTL, scene pressure escalation/resolution) function correctly. Condition lifecycle shows duplicate/same-turn add-remove noise (`winded`). One arc thread (`settle_the_debt`) stalls at progress 2 for 12 turns without advancement signals. No critical state corruption, but lifecycle tracking requires tightening.

***

## SECTION 5 — Actionable Issues

- **<inventory_remove validation fails on depleted stock>** (turns: 6, 13) — Tag: `extraction_miss`. Fix: Add pre-validation in state extract prompt or engine validator to check `current_amount >= requested_remove_amount` before emitting delta.
- **<progress extract omits actions array>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Enforce exactly 4 actions in progress extraction system prompt; add fallback template if LLM omits the field.
- **<scene pressure not passed to narrator prompt>** (turns: 4, 5, 6, 7, 9) — Tag: `scope_violation`. Fix: Ensure `state.scene.scene_pressure` is merged into `_narrate_messages()` context before streaming, and directive generation is triggered when urgency ≥ immediate.
- **<location change emitted but state ID not updated>** (turns: 4, 10, 12) — Tag: `engine_bug`. Fix: Debug `apply_delta()` location merge logic; force `state.location.id = delta.location_change.id` regardless of description/name matches.
- **<scene extract misses NPC names from prose>** (turns: 1, 3, 4, 5, 10, 11) — Tag: `schema_drift`. Fix: Update scene extract few-shot examples to explicitly map all proper nouns in narration to `npc_add/update` deltas, or add a post-extraction entity normalization step.