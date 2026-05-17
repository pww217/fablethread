# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-17T02:42:54.918897+00:00 · **Finished:** 2026-05-17T02:51:30.185318+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260517T024254Z_lsufe1_6`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260516T202305Z_81rrb2bj/artifacts`

## Judge Summary

**Mechanical:** —/5  
**Narrative:** —/5  
**System Cohesion:** —/5  
**Prompt Quality:** —/5  
**Compaction:** —/5  
**State Fidelity:** 52.9%  
**Prompt Adherence:** —
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**[state_correctness trace](full_cycle.state_correctness.trace.md)** · **[state_correctness verdict](full_cycle.state_correctness.judge.md)**  

## ⚠️  Flagged

### `rejected_deltas` — 3 rejected delta(s) across the run

- turn 7: 2 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 2 turn(s) errored
- turn 7: engine_errors: [{"trace_id": "d544380f", "message": "Delta validation failed (2 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "745c96e3", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict — `state_correctness`

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

## Auto-Checker

**238 passed, 27 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 1 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 1 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 1 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=2 |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 2 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 2 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 2 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_well |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 3 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 3 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 3 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 4 | `universal.location_change.applied` | ✅ | (no change) |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 4 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 4 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 4 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `rules.rolled` | ❌ | rolled=False |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 5 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: east_gate_road |
| 5 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossing', 'Crossed', 'Marrow'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 5 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Listen', 'Crossed'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 6 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 6 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 6 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 6 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 7 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 7 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 7 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 8 | `rules.rolled` | ❌ | rolled=False |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ❌ | beat persisted unchanged across turns: {'beat_expires_turn': 9, 'instruction': 'Halden offers you a lead on a more lucrative, albeit more dangerous, delivery job.', 'surface_as': 'npc_behavior', 'type': 'opportunity'} |
| 8 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 8 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 8 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 8 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ❌ | beat persisted unchanged across turns: {'beat_expires_turn': 9, 'instruction': 'Halden offers you a lead on a more lucrative, albeit more dangerous, delivery job.', 'surface_as': 'npc_behavior', 'type': 'opportunity'} |
| 9 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 9 | `universal.location_change.applied` | ❌ | location_change emitted but state.location.id unchanged: crossed_keys_inn |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 2 removes |
| 9 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 9 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 9 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 9 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `rules.rolled` | ❌ | rolled=False |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 10 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 10 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 10 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 10 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `rules.rolled` | ❌ | rolled=False |
| 11 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 11 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 11 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `rules.rolled` | ✅ | rolled=False |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 12 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 12 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 12 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `rules.rolled` | ❌ | rolled=True |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 13 | `universal.narrate.directive_rendered` | ✅ | (no directive computed) |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.scene.scene_tags` | 🔴 | 3 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `rules.rolled` | 🔴 | 8 | 12 | T2 |
| `universal.inventory.key_consumed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 2 | 13 | T5 |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.directive_rendered` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 4 | 13 | T5 |
| `universal.npc_mention.extracted` | 🔴 | 3 | 13 | T3 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 2 | 13 | T8 |
| `universal.pending_gm_beat.disposition_respected` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 3 | 13 | T4 |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Pressure Duration

| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `inn_entrance_blockade` | T5 | T5 | 1 |  |
| `matthew_hostility` | T11 | T13 | 3 |  |
| `toughs_pursuit` | T13 | T13 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `alleyway_passage` | 1 |  |
| `crossed_keys_inn` | 5 | ⚠️ >4 turns |
| `east_gate_road` | 3 |  |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_well` | 1 |  |
| `river_docks` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T13 | 13 | ⚠️ >6 turns |
| `low_morale` | T1 | T1 | 1 |  |
| `staggered` | T12 | T12 | 1 |  |
| `stinging_forearm` | T11 | T13 | 3 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1583 (+0) | 4071 (+0) | 2967 (-19) | 3565 (-15) | 4063 (+363) | 0 | 0 | 34.09 |
| 2 | I slide 500 credits across the table to Caron an… | 1586 (+1) | 4327 (-21) | 3342 (-5) | 3681 (+14) | 4413 (+343) | 0 | 0 | 33.70 |
| 3 | I find Halden by the town well and offer to carr… | 1594 (+2) | 4705 (-12) | 3368 (-47) | 3537 (-96) | 4447 (+290) | 0 | 0 | 41.41 |
| 3 |  | — | — | 0 | 0 | 0 | 0 | 0 | 36.49 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1548 (+11) | 4718 (-67) | 3202 (-60) | 3516 (-31) | 4332 (+238) | 0 | 0 | 45.39 |
| 5 | I walk up to the two toughs at the inn door and … | 1497 (-36) | 5004 (-200) | 3137 (-153) | 3576 (-81) | 4430 (+161) | 0 | 0 | 54.15 |
| 6 | I drop 200 credits on the ground between the tou… | 1591 (+2) | 5063 (-299) | 3325 (-160) | 3612 (-77) | 4693 (+170) | 0 | 0 | 37.13 |
| 6 |  | — | — | 0 | 0 | 0 | 0 | 0 | 32.26 |
| 7 | I sit across from Halden at his table, slide the… | 1555 (-62) | 4931 (-310) | 3359 (-116) | 3581 (-11) | 4559 (+208) | 0 | 0 | 41.74 |
| 8 | I pull out the brass key Halden gave me and try … | 1567 (-44) | 5283 (-333) | 3247 (-242) | 3479 (-236) | 4421 (-7) | 0 | 0 | 32.21 |
| 9 | I press my ear against the inn's stone wall and … | 1570 (-61) | 5183 (-492) | 3174 (-422) | 3475 (-116) | 4356 (-108) | 0 | 0 | 35.99 |
| 9 |  | — | — | 0 | 0 | 0 | 0 | 0 | 49.93 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1585 (+49) | 4815 (-445) | 3284 (-149) | 3545 (-40) | 4443 (+23) | 0 | 0 | 40.70 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1628 (+49) | 5147 (-480) | 3371 (-40) | 3537 (+19) | 4570 (+271) | 0 | 0 | 0.00 |
| 12 | I grab the ledger from my coat and sprint out th… | 1639 (+43) | 5341 (-269) | 3366 (-106) | 3561 (-44) | 4639 (+216) | 0 | 0 | 0.00 |
| 12 |  | — | — | 0 | 0 | 0 | 0 | 0 | 0.00 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1542 (+1) | 5108 (-215) | 3338 (-140) | 3645 (+37) | 4688 (+281) | 0 | 0 | 0.00 |
|  | TOTALS | 20485 | 63696 | 42480 | 46310 | 58054 | 0 | 0 | 515.18 |

**Total turns:** 17 · **Total duration:** 515.18s · **Avg/turn:** 30.30s
**Total tokens in:** 231,025 · **Total tokens out:** 15,854 · **Total LLM time:** 473.9s
**Total retries:** 0 · **Total parse failures:** 0

