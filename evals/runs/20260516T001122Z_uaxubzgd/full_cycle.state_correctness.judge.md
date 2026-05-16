

```yaml
state_fidelity_rate: 0.0
extraction_accuracy_score: 1
mechanic_lifecycle_score: 2
```

***

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 1 | — | 0 | 0→0 | — |
| 2 | — | 0 | 0→0 | — |
| 3 | — | 0 | 0→0 | — |
| 4 | — | 0 | 0→0 | — |
| 5 | fail | -1 | 0→-1 | — |
| 6 | fail | -1 | -1→-2 | — |
| 7 | — | 0 | -2→-2 | — |
| 8 | fail | -1 | -2→-3 | — |
| 9 | partial | 0 | -3→-3 | — |
| 10 | fail | 0 | -3→-3 | — |
| 11 | fail | 0 | -3→-3 | — |
| 12 | partial | 0 | -3→-3 | — |
| 13 | — | 0 | -3→-3 | — |

Momentum responds correctly to dice rolls until hitting the floor at -3, then flatlines as expected.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| 10 | escalation | replace (T11) | ambient/breathing_room | Yes | — |
| 11 | breathing_room | consume (T12) | expires T14 | Yes | — |
| 12 | breathing_room | consume (T13) | expires T15 | Yes | — |

TTL respected. Dispositions handled correctly.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|
| thug_aggression_escalation | 9 | immediate | No | N/A | 5 turns | UNRESOLVED_AT_END |
| inn_breach_chaos | 10 | immediate | No | N/A | 4 turns | UNRESOLVED_AT_END |

Both pressures added as immediate but never escalated or resolved. Inert/Unresolved.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| shoulder_bruise | 7 | roll | 12 | 5 turns | DUPLICATE (re-added T8) |
| staggered | 10 | narrative | 11 | 1 turn | — |
| bruised_ribs | 8 | narrative | 12 | 4 turns | SILENT_DROP (removed T12 without delta) |

`low_morale` removed correctly at T2. `shoulder_bruise` duplicated at T8. `bruised_ribs` dropped silently at T12.

### 1E — Arc Thread Lifecycle Table

| Thread ID | Created (Tn) | State | Progress | Completed (Tm) | Flag |
|-----------|--------------|-------|----------|----------------|------|
| settle_the_debt | 1 | active | 0→0 | N/A | STALLED (6 turns) |
| deliver_the_ledger | 0 | active | 0→2 | N/A | — |
| clear_the_road_toughs | 0 | active | 0→1 | N/A | STALLED (5 turns) |
| the_toughs_at_the_crossed | 3 | latent→active | 0→1 | N/A | STALLED (5 turns) |
| the_shadowy_figures_leaning_against | 4 | latent | 0→0 | N/A | ORPHANED (4 turns) |
| matthew_estrada's_calm_reaction_to | 10 | latent | 0→0 | N/A | ORPHANED (3 turns) |

Multiple threads stall or orphan while engagement maxes out.

### 1F — Arc Engagement Table

| Turn | arc_engagement | Drift Match? | Δ Engagement | Flag |
|------|----------------|--------------|--------------|------|
| 1 | 0 | — | — | — |
| 3 | 1 | Yes (deliver_the_ledger) | +1 | — |
| 4 | 2 | Yes (the_toughs_at_the_crossed) | +1 | — |
| 8 | 3 | Yes (clear_the_road_toughs) | +1 | — |
| 9-13 | 3 | No | 0 | MAX_REACHED (5 turns) |

Engagement maxed out and stuck at +3 with no new thread activations.

### 1G — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 3 | Add | credits | 100 | No | — |
| 4 | Add | credits | 1 | No | AMOUNT_MISMATCH (hallucinated) |
| 5 | Remove | credits | 101 | No | — |
| 6 | Remove | credits | 101 | No | AMOUNT_MISMATCH (removed from 0) |
| 7 | Remove | merchants_seal | 1 | Yes | SCHEMA_MISMATCH (item missing) |
| 7 | Remove | halden_ledger | 1 | Yes | SCHEMA_MISMATCH (item missing) |
| 9 | Remove | credits | 1 | Yes | SCHEMA_MISMATCH (item missing) |
| 10 | Update | bandages | 3→2 | No | EXTRACTION_MISS (no delta) |
| 12 | Add | halden_ledger | 1 | No | DUPLICATE (already delivered) |
| 13 | Remove | bandages | 1 | No | — |

***

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory and conditions diverge significantly across the run. `credits` are hallucinated (+1 at T4), then double-removed (T5, T6) despite hitting zero balance. `merchants_seal` and `halden_ledger` removals at T7 are rejected because the items don't exist in state, contradicting the narrative of delivery. `bandages` deduction at T10 occurs in state but lacks an extraction delta. Arc threads (`settle_the_debt`, `clear_the_road_toughs`) stall at progress 0/1 while `arc_engagement` maxes out at 3, creating a disconnect between player focus and system tracking. Scene pressures remain `immediate` but inert from T9 to T13.

### 2B — Extraction Drift
- **T4 `inventory_add` (credits +1):** Pipeline: `state`. Field: `inventory`. Type: extraction failure (hallucination). Player input contained no credit transaction.
- **T6 `inventory_remove` (credits -101):** Pipeline: `state`. Field: `inventory`. Type: validation rejection / extraction miss. Credits were already 0 after T5; extraction failed to check balance.
- **T7 `inventory_remove` (merchants_seal, halden_ledger):** Pipeline: `state`. Field: `inventory`. Type: schema mismatch. Extraction emitted removals for items not present in state.
- **T9 `inventory_remove` (credits -1):** Pipeline: `state`. Field: `inventory`. Type: schema mismatch. Extraction attempted removal of non-existent credits.
- **T10 `inventory_update` (bandages 3→2):** Pipeline: `state`. Field: `inventory`. Type: extraction miss. State changed, but extractor emitted empty delta.
- **T12 `inventory_add` (halden_ledger +1):** Pipeline: `state`. Field: `inventory`. Type: extraction miss. Extraction added an item the player had already delivered at T7.

### 2C — State Fidelity Rate Calculation
Turns with (no rejected deltas AND no Auto-Checker failures AND no detected drift) / total turns.
- Total turns: 13
- Clean turns: 0 (Every turn has at least one auto-checker failure, rejected delta, or extraction drift)
- Arithmetic: 0 / 13 = 0.0
- **state_fidelity_rate: 0.0**

***

## SECTION 3 — Auto-Checker Failure Analysis

1. **`universal.progress.actions_quality` (All turns)**
   - True failure. The progress extraction pipeline consistently emits an empty `actions` array (0 entries vs expected 4).
   - Root cause: Progress extraction LLM prompt or parsing logic fails to generate actionable next steps.
   - Remediation tag: `extraction_miss`

2. **`universal.npc_mention.extracted` (T1, T3, T4, T7, T8, T9, T10, T11, T12, T13)**
   - True failure. Narration text references names (e.g., 'Crossed', 'Inside', 'Matthew', 'Estrada', 'Caron') that the Scene Extractor does not capture in `npc_add`/`npc_update`.
   - Root cause: Scene extraction schema is too restrictive or the extractor fails to map narrative mentions to known NPC IDs.
   - Remediation tag: `schema_drift`

3. **`universal.location_change.applied` (T4, T12)**
   - True failure. `location_change` delta is emitted by extraction, but `state.location.id` remains unchanged in the applied state.
   - Root cause: Engine location delta application logic fails to overwrite the current location ID, or validation rejects the change silently.
   - Remediation tag: `engine_bug`

4. **`universal.narrate.pressure_directive_rendered` (T8, T9, T10)**
   - True failure. Engine generates `immediate` scene pressures, but the Narrate User Prompt lacks the corresponding Pressure/Overwhelm directive.
   - Root cause: Engine data flow does not inject active immediate pressures into the narrator's context window.
   - Remediation tag: `scope_violation`

***

## SECTION 4 — Scores

### Extraction Accuracy Score: 1/5
**Reason:** Repeated inventory hallucinations (T4 +1 credit), validation failures on removals (T6, T7, T9), missing extractions for state changes (T10 bandages, T12 ledger duplicate), and a completely non-functional progress actions pipeline across all turns. State fields consistently diverge from narrated events.

### Mechanic Lifecycle Score: 2/5
**Reason:** Momentum tracks correctly until hitting the floor. GM beats respect TTL. However, Scene pressures are inert/unresolved (2 flags), Conditions show duplicates/silent drops (2 flags), Arc threads stall or orphan (4 flags), and Arc engagement maxes out and stagnates (1 flag). Total red flags exceed 4, capping the score.

***

## SECTION 5 — Actionable Issues

- **Inventory validation and extraction consistency** (turns: 4, 5, 6, 7, 9, 12) — Tag: `extraction_miss`. Fix: Implement pre-validation in the state manager to reject removals exceeding current balance or referencing non-existent IDs. Update the state extraction prompt to strictly cross-reference the current inventory snapshot before emitting deltas.
- **Progress extraction pipeline failure** (turns: 1-13) — Tag: `extraction_miss`. Fix: Debug the progress extraction LLM call; ensure the prompt mandates `actions` generation or adjust the auto-checker threshold to account for narrative-heavy turns.
- **Scene pressure directive leakage** (turns: 8, 9, 10) — Tag: `scope_violation`. Fix: Engine must inject active `scene_pressure` directives (especially `immediate` urgency) into the Narrate User Prompt to ensure the narrator acknowledges and reacts to escalating threats.
- **Location change application lag** (turns: 4, 12) — Tag: `engine_bug`. Fix: Verify the location delta application logic in the state manager; ensure `location_change` emissions correctly overwrite `state.location.id` and trigger necessary NPC/scene updates.