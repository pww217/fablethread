

```yaml
---
state_fidelity_rate: 0.15
extraction_accuracy_score: 2
mechanic_lifecycle_score: 1
---
```

# ccya Eval — State Correctness Judge

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|
| T1   | partial/flat | 0         | 0 → 0             | FLAT |
| T2   | setback     | -1        | 0 → -1            | —    |
| T4   | fail        | -1        | -1 → -2           | —    |
| T5   | crit_fail/fail | -2      | -1 → -3           | WRONG_DIR (band says fail, delta says -2) |
| T6   | partial/success | +1     | -3 → -2           | WRONG_DIR (floor at -3 should cap or trigger relief) |

**Momentum Analysis:** Momentum responds to dice rolls but violates floor constraints. At `momentum=-3` (T5/T6), the engine fails to enforce `config.momentum_floor`, allowing a +1 delta on T6 despite being at the absolute minimum. The band-to-delta mapping also drifts (`fail` yielding `-2` instead of `-1`).

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Surface As | State After (type) | Injected By | TTL Respected? | Flag |
|----------------|-----------|------------|--------------------|-------------|----------------|------|
| T1             | opportunity | npc_behavior | opportunity       | Storytell   | Yes (expires T3) | —    |
| T2             | pressure    | npc_behavior | pressure          | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T4             | complication| npc_behavior | complication      | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T5             | complication| npc_behavior | complication      | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T6 (diff 5)    | pressure    | npc_behavior | pressure          | Storytell   | Yes            | FLOOR_RELIEF_MISS |
| T7 (diff 6)    | breathing_room | environmental | breathing_room  | Floor Relief| Yes (expires T10)| —    |

**Beat Analysis:** Floor relief consistently fails to inject `breathing_room` when `beat_locked=True` and storyteller emits pressure/complication beats. The counter increments on pressure types but the override logic is bypassed, creating a pressure loop until an explicit breathing_room finally fires at T7. TTL expiry checks run correctly; no orphaned beats detected.

### 1C — Arc Goal Update Table

| Turn | goal_update Emitted | visible_goal Before | visible_goal After | Applied? | Flag |
|------|---------------------|---------------------|--------------------|----------|------|
| T5   | None (empty block)  | Clear your debts... | Investigate Harker's disappearance and settle your debts. | Yes      | SILENT_CHANGE |

**Goal Analysis:** `visible_goal` changes at the end of Turn 5 without a corresponding `goal_update` string in any storyteller extraction output. This indicates either stale delta application from an unlogged turn or direct state mutation bypassing the pipeline.

### 1D — Unified Thread Lifecycle Table

| ID | Added (Tn) | Scope | Urgency | Updates | Resolved (Tm) | Flag |
|----|------------|-------|---------|---------|----------------|------|
| deliver_the_ledger | Seed | arc | normal | T2, T4, T5, T8, T9 | — | INERT (silent progress drifts: advancement→shift mix) |
| investigate_harker_disappearance | T7 | arc | normal | T10, T11, T13 | — | — |
| canyon_ambush | T9 | scene | urgent | T10 | T10 | RESOLUTION_FAILED (resolved in storyteller but state diff shows added to completed_threads with `last_updated_turn: null` mismatch) |
| unlock_the_tin_box | T5? | arc | normal | None | — | SILENT_CHANGE (appears in state without thread_add/thread_update emission trace) |

**Thread Analysis:** Scene-scoped threads purge correctly on location change. Arc threads persist but suffer from progress kind drift (`advancement` vs `shift`) and silent creation of `unlock_the_tin_box`. Resolution tracking for `canyon_ambush` shows metadata misalignment in the diff.

### 1E — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|
| heat_exhaustion | T1 | narrative | T2/T3 | ~2 turns | ORPHANED (no CONDITION_MODS entry per auto-checker) |
| rattled | T5 | narrative | T6 | ~1 turn | ORPHANED |
| chilled | T9 | environmental | T10 | ~1 turn | ORPHANED |

**Condition Analysis:** All added conditions lack `CONDITION_MODS` entries in the ruling/pacing math, meaning they do not affect dice rolls or momentum as designed. TTL tracking is disrupted by shuffled state diffs, but nominal durations align with extraction claims.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|
| T2   | Remove | credits | 1             | No        | —    |
| T4   | Update | iron_dagger | notes only | No      | —    |
| T8   | Add    | dried_meat, water_canteen, hemp_rope | 2/1/1 | No | — |
| T13  | Add    | whiskey_glass | 1           | No        | SPENDING_MISS (credits not deducted despite purchase narrative) |

**Inventory Analysis:** Extraction accurately captures additions and updates. Notable miss: `whiskey_glass` added at T13 without a corresponding credit deduction, violating the economy loop implied by the input/narrative.

---

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Inventory, conditions, threads, and location diverge significantly across turns due to trace shuffling and extraction gaps:
- **Location/Time Drift:** `meta.turn` regresses (`from: 7, to: 5` at T6 diff; `from: 13, to: 10` at T11 diff). Location IDs flip backwards (`outskirts_cabin → sheriff_station`). This breaks chronological causality for scene-scoped thread purging and beat expiry.
- **Condition/Rule Disconnect:** Conditions added via extraction never enter the ruling math (`CONDITION_MODS` missing), breaking the intended stat/difficulty interaction loop.
- **Goal/Thread Misalignment:** `visible_goal` shifts without storyteller emission; `unlock_the_tin_box` appears in state without pipeline trace, suggesting stale delta merge or out-of-band mutation.

### 2B — Extraction Drift
| Turn | Responsible Pipeline | Field That Drifted | Failure Type |
|------|---------------------|--------------------|--------------|
| T3   | Storytell           | `actions` (0 entries) | extraction_miss |
| T5   | Storytell/Ruling    | `actions` (0), `beat_locked` logic | schema_drift / engine_bug |
| T6   | Scene Extract       | `location_change.id` not applied to state | validation_rejection |
| T7-9 | Pacing Engine       | `pending_gm_beat.type` remains pressure/complication despite beat_locked=True | engine_bug (floor relief bypass) |
| T13  | State Extract       | Inventory add without credit remove | extraction_miss |

### 2C — State Fidelity Rate Calculation
Total logical turns evaluated: 13.
Turns with no rejected deltas AND no Auto-Checker failures AND no detected drift: T1, T4 (partial), T12 → **2/13**.
`state_fidelity_rate = 0.15`

---

## SECTION 3 — Auto-Checker Failure Analysis

| Turn | Assertion | True failure or checker noise? | Root Cause | Remediation Tag |
|------|-----------|-------------------------------|------------|-----------------|
| T2   | `universal.conditions.orphan` | True failure | Condition added to state but never registered in ruling/pacing math (`CONDITION_MODS`). Pipeline omission. | extraction_miss |
| T3   | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Empty user input yielded `{}` storyteller output; LLM skipped action generation. | extraction_miss |
| T3   | `universal.pacing.consecutive_pressure_tracking` | True failure | Storyteller emitted null/empty beat, but counter incremented to 1. Logic reads stale state or miscounts. | engine_bug |
| T5   | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Same as T3. | extraction_miss |
| T5   | `universal.pacing.consecutive_pressure_tracking` | True failure | Counter stuck at 1 despite beat type mismatch. TTL expiry not resetting counter correctly. | engine_bug |
| T5   | `universal.pacing.beat_locked_dual_trigger` | True failure | Momentum hit floor (-3) but `beat_locked=False`. Floor check logic missing or gated incorrectly. | engine_bug |
| T6   | `universal.location_change.applied` | True failure | Scene extract emitted location delta, but validator/apply skipped it (likely ID mismatch or schema drift). | validation_rejection |
| T6   | `universal.conditions.orphan` | True failure | Same as T2. Condition lifecycle decoupled from ruling engine. | extraction_miss |
| T7   | `universal.pacing.floor_relief` | True failure | `beat_locked=True`, storytell emitted pressure, but floor relief did not override to breathing_room. Override logic bypassed. | engine_bug |
| T8   | `universal.pacing.floor_relief` | True failure | Same as T7. Complication beat persisted despite locked state. | engine_bug |
| T9   | `universal.pacing.floor_relief` | True failure | Same as T7/T8. Pressure loop continues unchecked. | engine_bug |
| T10  | `universal.conditions.orphan` | True failure | Same systemic condition orphaning. | extraction_miss |
| T10  | `universal.storytell.actions_quality` | True failure (expected for empty input blocks) | Empty input → no actions emitted. | extraction_miss |

---

## SECTION 4 — Scores

### Extraction Accuracy Score: 2/5
**Reason:** Repeated extraction failures on critical fields (`actions` missing on multiple turns, `location_change` not applied despite emission). Condition lifecycle extraction succeeds but fails to wire into downstream math. State drift from shuffled diffs and silent goal/thread mutations further degrade accuracy. Major extraction misses cap at 2 per rubric.

### Mechanic Lifecycle Score: 1/5
**Reason:** Floor relief mechanism consistently fails across T7-T9 despite `beat_locked=True` and pressure-type beats, breaking the intended de-escalation loop. Momentum floor constraints are violated (`momentum=-3 → -2`). Consecutive pressure tracking desynchronizes from beat types. Goal updates occur silently without storyteller emission. >4 red flags across tables; core pacing/arc governance is non-functional in this trace.

---

## SECTION 5 — Actionable Issues

**Critical**
- **Floor relief override bypassed on `beat_locked=True`** (turns: T7, T8, T9) — Tag: `engine_bug`. Fix: Ensure `_check_floor_relief()` runs post-delta apply unconditionally when `beat_locked=True` and pending beat is pressure/complication/null. Verify gate logic does not block relief injection.
- **Momentum floor constraint ignored** (turns: T5, T6) — Tag: `engine_bug`. Fix: Clamp momentum deltas to `[momentum_min, momentum_max]` during `_apply_delta()` or ruling resolution; prevent +1 delta at `-3`.

**Major**
- **Conditions orphaned from ruling/pacing math** (turns: T2, T6, T10) — Tag: `extraction_miss`. Fix: Wire extracted conditions into `RulesOutcome.cond_mod` calculation during Step 0. Ensure `_apply_delta()` registers new conditions in a lookup table for future rulings.
- **Location change emission not applied to state** (turns: T6) — Tag: `validation_rejection`. Fix: Debug delta builder ID matching; ensure scene extract location IDs map correctly to state schema before validation rejection.

**Minor**
- **Actions extraction drops on empty/whitespace inputs** (turns: T3, T5, T10) — Tag: `extraction_miss`. Fix: Add fallback prompt guard in storyteller system template to always emit 4 actions even when user input is null or whitespace.
- **Silent arc goal/thread mutations without pipeline trace** (turns: T5, T7) — Tag: `stale_context`. Fix: Audit delta merge logic; ensure all state changes route through explicit extraction outputs rather than background batch processing or stale snapshot application.