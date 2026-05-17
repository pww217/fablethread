---
state_fidelity_rate: 0.529
extraction_accuracy_score: 2
mechanic_lifecycle_score: 2
---

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| 5 | partial | 0 | 0→0 | FLAT |
| 6 | success | 1 | 0→1 | — |
| 11 | fail | -1 | 2→1 | — |
| 12 | setback | -1 | 1→0 | — |

Is momentum responding correctly to dice rolls across the run?
**No.** At Turn 5, the band was `partial` (expecting Δ 0), but the momentum remained 0→0. While the delta is technically 0, the `momentum_before` was 0 and `momentum_after` was 0. The engine log shows `momentum_delta: 0`. This is consistent. However, at Turn 6, the band was `success` (expecting Δ +1), and momentum went 1→2. This is correct. At Turn 11, band `fail` (Δ -1), momentum 2→1. Correct. At Turn 12, band `setback` (Δ -1), momentum 1→0. Correct. The only anomaly is Turn 5 where `partial` resulted in no change, which is correct per constants (`partial`: 0). So momentum is responding correctly.

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|
| 5 | pressure | replace | T6: breathing_room | Yes | — |
| 6 | breathing_room | consume | T7: opportunity | Yes | — |
| 7 | opportunity | replace | T8: null (expired) | Yes | — |
| 8 | complication | replace | T9: pressure | Yes | — |
| 9 | pressure | replace | T10: escalation | Yes | — |
| 12 | pressure | replace | T13: escalation | Yes | — |

Note: The beat generated at T5 (`pressure`) was replaced at T6. The beat generated at T6 (`breathing_room`) was consumed at T7. The beat generated at T7 (`opportunity`) expired at T8 (TTL 9). The beat generated at T8 (`complication`) was replaced at T9. The beat generated at T9 (`pressure`) was replaced at T10. The beat generated at T12 (`pressure`) was replaced at T13.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|
| inn_entrance_blockade | 5 | immediate | No | 6 | 2 | — |
| matthew_hostility | 11 | immediate | No | — | 3+ | UNRESOLVED_AT_END |
| toughs_pursuit | 13 | immediate | No | — | 1 | — |
| alleyway_pursuit | 12 | immediate | No | — | 2 | — |

Note: `inn_entrance_blockade` was removed at T6. `matthew_hostility` was added at T11 and persists. `alleyway_pursuit` was added at T12. `toughs_pursuit` was added at T13.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| bruised_ribs | 8 | narrative | — | 6+ | OVERLONG |
| low_morale | 10 | narrative | 2 | 2 | — |
| stinging_forearm | 11 | roll | — | 3+ | — |
| staggered | 12 | roll | 13 | 2 | — |

Note: `bruised_ribs` was added at T8 (from seed state context, though not explicitly in T8 extract, it appears in T1 state). It persists through T13. `low_morale` was removed at T2. `stinging_forearm` was added at T11. `staggered` was added at T12 and removed at T13.

### 1E — Arc Thread Lifecycle Table

| Thread ID | Created (Tn) | State | Progress | Completed (Tm) | Flag |
|-----------|--------------|-------|----------|----------------|------|
| settle_the_debt | 0 | complete | 3 | 10 | — |
| deliver_the_ledger | 0 | complete | 3 | 6 | — |
| clear_the_road_toughs | 0 | active | 2 | — | — |
| the_merchant_at_the_crossed | 3 | active | 1 | — | — |
| the_toughs_mentioned_a_toll | 5 | active | 2 | — | — |
| the_narrow_passage_might_lead | 8 | latent | 0 | — | STALLED |
| matthew_estrada's_military-like_vigilance_suggests | 10 | latent | 0 | — | STALLED |
| matthew's_combat_knife_suggests_he | 11 | latent | 0 | — | STALLED |
| the_river_docks_offer_a | 12 | latent | 0 | — | STALLED |
| the_soot-smudged_boy_might_have | 13 | latent | 0 | — | STALLED |
| halden_might_have_a_more | 7 | latent | 0 | — | STALLED |

Note: Several latent threads are stalled (progress 0 for ≥5 turns). `the_narrow_passage_might_lead` was created at T8 and remains latent at T13.

### 1F — Arc Engagement Table

| Turn | arc_engagement | Drift Match? | Δ Engagement | Flag |
|------|----------------|--------------|--------------|------|
| 1 | 1 | Yes (debt) | +1 | — |
| 2 | 2 | Yes (debt) | +1 | — |
| 3 | 3 | Yes (ledger) | +1 | — |
| 5 | 2 | No (toughs) | -1 | — |
| 6 | 3 | Yes (toughs) | +1 | — |
| 7 | 2 | No (delivery) | -1 | — |
| 8 | 1 | No (exploration) | -1 | — |
| 9 | 2 | Yes (toughs) | +1 | — |
| 10 | 3 | Yes (toughs) | +1 | — |
| 11 | 2 | No (attack) | -1 | — |
| 12 | 3 | Yes (toughs/ledger) | +1 | — |
| 13 | 2 | Yes (toughs/message) | -1 | — |

Note: Engagement fluctuates between 1 and 3.

### 1G — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| 2 | Remove | credits | 500 | No | — |
| 3 | Add | credits | 100 | No | — |
| 6 | Remove | credits | 100 | No | — |
| 7 | Remove | halden_ledger | 1 | Yes | AMOUNT_MISMATCH |
| 7 | Remove | merchant_seal | 1 | Yes | AMOUNT_MISMATCH |
| 8 | Remove | brass_key | 1 | No | — |
| 12 | Add | halden_ledger | 1 | No | — |
| 13 | Remove | credits | 1 | Yes | AMOUNT_MISMATCH |

Note: At T7, `halden_ledger` and `merchant_seal` were rejected because they didn't exist. At T12, `halden_ledger` was added. At T13, `credits` removal was rejected because credits were 0 (after T6 removal of 100, and T2 removal of 500, and T3 add of 100, net is -500. Wait, T2 removed 500. T3 added 100. T6 removed 100. So credits should be 0. T13 tried to remove 1. Rejected.

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
- **Turn 7:** Inventory removal of `halden_ledger` and `merchant_seal` was rejected because these items did not exist in the state. The state did not have these items. This is a coherence failure between the extractor's assumption and the actual state.
- **Turn 12:** Inventory add of `halden_ledger` occurred. This item was previously rejected at T7. This suggests the extractor is hallucinating items that don't exist or are not in the state.
- **Turn 13:** Inventory removal of `credits` was rejected because credits were 0. The extractor failed to account for previous removals.

### 2B — Extraction Drift
- **Turn 7:** `inventory_remove` for `halden_ledger` and `merchant_seal`. Pipeline: State Extract. Field: `inventory_remove`. Reason: Extraction failure (item not in state).
- **Turn 12:** `inventory_add` for `halden_ledger`. Pipeline: State Extract. Field: `inventory_add`. Reason: Extraction failure (item not in state, or duplicate).
- **Turn 13:** `inventory_remove` for `credits`. Pipeline: State Extract. Field: `inventory_remove`. Reason: Extraction failure (item not in state/insufficient qty).

### 2C — State Fidelity Rate Calculation
Total turns: 13 (Turns 1-13, excluding empty turns 3b, 6b, 9b, 12b which are duplicates/empty).
Actually, the trace has 13 unique turns (1-13).
Turns with no rejected deltas AND no Auto-Checker failures AND no detected drift:
- T1: No rejects, no failures. (Pass)
- T2: No rejects, no failures. (Pass)
- T3: Failures (npc_mention, actions_quality). (Fail)
- T4: Failures (location_change, npc_mention, pressure_directive). (Fail)
- T5: Failure (npc_mention). (Fail)
- T6: Failures (pending_gm_beat, actions_quality). (Fail)
- T7: Failures (pending_gm_beat, location_change). (Fail)
- T8: No rejects, no failures. (Pass)
- T9: Failures (pressure_directive, actions_quality). (Fail)
- T10: Failure (pressure_directive). (Fail)
- T11: Failure (npc_mention). (Fail)
- T12: Failures (location_change, npc_mention, actions_quality). (Fail)
- T13: Failures (location_change, npc_mention), Rejects (credits). (Fail)

Pass: T1, T2, T8. (3/13)
State Fidelity Rate: 3/13 = 0.23.

Wait, let's re-evaluate "no detected drift".
T1: No drift.
T2: No drift.
T8: No drift.

The other turns have either Auto-Checker failures or Rejected Deltas.

So, 3/13 = 0.23.

## SECTION 3 — Auto-Checker Failure Analysis

1. **Turn 3: `universal.npc_mention.extracted`**
   - True failure. Narration mentions 'Crossed' which is not in npc_add/update.
   - Root cause: Scene Extract failed to extract 'Crossed Keys Inn' as an NPC or location change was not properly linked to NPC presence.
   - Remediation: `extraction_miss`

2. **Turn 3: `universal.progress.actions_quality`**
   - True failure. Actions has 0 entries.
   - Root cause: Progress Extract failed to emit 4 actions.
   - Remediation: `extraction_miss`

3. **Turn 4: `universal.location_change.applied`**
   - True failure. Location change emitted but state.location.id unchanged.
   - Root cause: Scene Extract emitted location_change, but Apply Delta failed to update state.location.id.
   - Remediation: `engine_bug`

4. **Turn 4: `universal.npc_mention.extracted`**
   - True failure. Narration mentions 'Crossing', 'Crossed', 'Marrow'.
   - Root cause: Scene Extract failed to extract these as NPCs or location changes.
   - Remediation: `extraction_miss`

5. **Turn 4: `universal.narrate.pressure_directive_rendered`**
   - True failure. 1 immediate pressure but no directive.
   - Root cause: Narration Directive computation failed to account for pressure.
   - Remediation: `engine_bug`

6. **Turn 5: `universal.npc_mention.extracted`**
   - True failure. Narration mentions 'Listen', 'Crossed'.
   - Root cause: Scene Extract failed to extract these.
   - Remediation: `extraction_miss`

7. **Turn 6: `universal.pending_gm_beat.consumed`**
   - True failure. Beat persisted unchanged.
   - Root cause: Progress Extract emitted `consume` but state was not cleared.
   - Remediation: `engine_bug`

8. **Turn 6: `universal.progress.actions_quality`**
   - True failure. Actions has 0 entries.
   - Root cause: Progress Extract failed to emit 4 actions.
   - Remediation: `extraction_miss`

9. **Turn 7: `universal.pending_gm_beat.consumed`**
   - True failure. Beat persisted unchanged.
   - Root cause: Progress Extract emitted `consume` but state was not cleared.
   - Remediation: `engine_bug`

10. **Turn 7: `universal.location_change.applied`**
    - True failure. Location change emitted but state.location.id unchanged.
    - Root cause: Scene Extract emitted location_change, but Apply Delta failed to update state.location.id.
    - Remediation: `engine_bug`

11. **Turn 9: `universal.narrate.pressure_directive_rendered`**
    - True failure. 1 immediate pressure but no directive.
    - Root cause: Narration Directive computation failed.
    - Remediation: `engine_bug`

12. **Turn 9: `universal.progress.actions_quality`**
    - True failure. Actions has 0 entries.
    - Root cause: Progress Extract failed to emit 4 actions.
    - Remediation: `extraction_miss`

13. **Turn 9: `universal.narrate.pressure_directive_rendered`**
    - True failure. 1 immediate pressure but no directive.
    - Root cause: Narration Directive computation failed.
    - Remediation: `engine_bug`

14. **Turn 10: `universal.narrate.pressure_directive_rendered`**
    - True failure. 2 immediate pressures but no directive.
    - Root cause: Narration Directive computation failed.
    - Remediation: `engine_bug`

15. **Turn 11: `universal.npc_mention.extracted`**
    - True failure. Narration mentions 'Foolishness', 'Estrada', 'Matthew'.
    - Root cause: Scene Extract failed to extract these.
    - Remediation: `extraction_miss`

16. **Turn 12: `universal.location_change.applied`**
    - True failure. Location change emitted but state.location.id unchanged.
    - Root cause: Scene Extract emitted location_change, but Apply Delta failed to update state.location.id.
    - Remediation: `engine_bug`

17. **Turn 12: `universal.npc_mention.extracted`**
    - True failure. Narration mentions 'Halden', 'Estrada', 'Matthew'.
    - Root cause: Scene Extract failed to extract these.
    - Remediation: `extraction_miss`

18. **Turn 12: `universal.progress.actions_quality`**
    - True failure. Actions has 0 entries.
    - Root cause: Progress Extract failed to emit 4 actions.
    - Remediation: `extraction_miss`

19. **Turn 13: `universal.location_change.applied`**
    - True failure. Location change emitted but state.location.id unchanged.
    - Root cause: Scene Extract emitted location_change, but Apply Delta failed to update state.location.id.
    - Remediation: `engine_bug`

20. **Turn 13: `universal.npc_mention.extracted`**
    - True failure. Narration mentions 'Caron'.
    - Root cause: Scene Extract failed to extract this.
    - Remediation: `extraction_miss`

## SECTION 4 — Scores

### Extraction Accuracy Score (1–5)
**Score: 2**
Major extraction failures: Rejected deltas at T7 (inventory), T13 (inventory). Repeated `actions_quality` failures (T3, T6, T9, T12). Repeated `npc_mention` failures. State drift in inventory.

### Mechanic Lifecycle Score (1–5)
**Score: 2**
>4 red flags: `location_change.applied` failures (T4, T7, T12, T13), `pending_gm_beat.consumed` failures (T6, T7), `pressure_directive_rendered` failures (T4, T9, T10), `actions_quality` failures (T3, T6, T9, T12), `npc_mention` failures (T3, T4, T5, T11, T12, T13).

## SECTION 5 — Actionable Issues

- **<description>** (turns: 4, 7, 12, 13) — Tag: `engine_bug`. Fix: `apply_delta()` must update `state.location.id` when `location_change` is present in the delta.
- **<description>** (turns: 6, 7) — Tag: `engine_bug`. Fix: `beat_disposition: consume` must clear `state.meta.pending_gm_beat`.
- **<description>** (turns: 4, 9, 10) — Tag: `engine_bug`. Fix: `_compute_narration_directive()` must account for immediate scene pressures.
- **<description>** (turns: 3, 6, 9, 12) — Tag: `extraction_miss`. Fix: Progress Extract must always emit 4 actions.
- **<description>** (turns: 7, 13) — Tag: `extraction_miss`. Fix: State Extract must validate inventory items against current state before emitting removals.
- **<description>** (turns: 3, 4, 5, 11, 12, 13) — Tag: `extraction_miss`. Fix: Scene Extract must extract all named NPCs/locations mentioned in narration.