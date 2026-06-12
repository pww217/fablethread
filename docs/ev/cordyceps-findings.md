# Cordyceps Year — Mechanic Check Findings (v2)

Session: `saves/cordyceps-year-twenty-2026-06-11` (27 turns)
Checked against: `docs/ev/RUBRIC.md`
Analysis dates: Initial + review (2026-06-12)

---

## 1. Momentum Lifecycle

**Result: PASS** | Confidence: **HIGH**

Momentum trajectory: 0→2→3→2→3→3→2→1→1→3→3→1→0→-1→1→2→1→2→3→2→3→3→3→3→2→3

- Floor (-3) never reached; lowest point -1 at T13. No floor violations.
- Roll band → delta mapping correct throughout:
  - T1: crit_success → +2 ✓
  - T3: fail → -1 ✓
  - T11: crit_fail → -2 ✓
  - T13: setback → -1 ✓
  - T14: crit_success → +2 ✓
- Values stay within [-3, +3] bounds ✓
- Recovery from low momentum (T13=-1 → T18=3) works correctly ✓
- No momentum lifecycle bugs in this session.

---

## 2. Thread Lifecycle & Arc Goals

**Result: FAIL** | Confidence: **HIGH**

### 2a. Thread ID Mismatch (Pipeline Bug)

Storyteller emits `thread_add` with id `creature_ambush_threat` at T10, but sanitizer adds `creature_ambush` (without `_threat`) at T10. The storyteller's thread_add never syncs to state — `creature_ambush_threat` never appears in any `state_snapshot.arc.threads`.

- `ev.py deltas` shows 27 turns with thread mutations in `changes.threads` (previous analysis claimed "only 1 thread mutation" — this was wrong, it was looking at the wrong data source)
- Sanitizer at T10 adds `creature_ambush` to state, not `creature_ambush_threat`
- This is a storyteller→sanitizer ID sync failure

### 2b. Goal_Update Format Mismatch (Pipeline Bug)

Storyteller emits `goal_update` as free-form narrative text (e.g., "The community has pivoted from debating medicine scarcity to executing an illicit trade for grain."), but the sanitizer at `ccya/engine/thread_sanitizer.py:217-223` requires it to be a dict with `visible_goal`/`goal_context` fields. The sanitizer silently drops free-form strings, which is why `applied.arc_update` is empty and `visible_goal` never updates from storyteller output.

- T2: storyteller goal_update ≠ state visible_goal (format mismatch, not data mismatch)
- T5: storyteller goal_update ≠ state visible_goal (same root cause)
- T25: storyteller goal_update ≠ state visible_goal (same root cause)

### 2c. Arc Goal Resolution

Previous analysis claimed "Arc goal 'Smuggle grain to David Fisher' persists throughout without update or resolution." This is **wrong**. `changes.threads` shows `arc_resolved` at T12 ("The smuggling run failed as the grain cache was destroyed...") and at T18/T24 for other arc goals.

---

## 3. GM Beat Lifecycle

**Result: FAIL** | Confidence: **MEDIUM**

Beat emissions from extraction.storytell.output:
- T1: pressure, T2: opportunity, T3: complication, T4: pressure, T5: pressure, T6: pressure, T8: opportunity, T10: escalation, T12: escalation, T13: escalation, T16: complication, T18: pressure, T19: complication, T20: complication, T21: pressure, T27: opportunity

- beat_locked fires correctly at T6 (consecutive pressure: T3-T5 = 3, threshold=3) ✓
- beat_locked fires correctly at T21 (consecutive pressure: T18-T21 = 4) ✓
- **3 consecutive escalation beats at T10, T12, T13** — exceeds the 2-consecutive-same-type limit in the rubric ✓ (flagged)
- Beat variety: pressure=7, escalation=3, complication=3, opportunity=3, null=13 — no single type exceeds 60% ✓
- Null beats (13/33 = 39%) are common — storyteller not emitting beats on most turns

**Note:** Beat type distribution from `ev.py beats` matches extraction output, confirming the 3-consecutive-escalation finding.

---

## 4. Pacing Directives

**Result: FAIL** | Confidence: **MEDIUM**

### Infrastructure blocker: `extraction_context` missing from all events

4 checkers fail on every turn because `extraction_context` doesn't exist in this save's events:
- `inventory_integrity` — requires `extraction_context.location_this_turn`
- `conditions_lifecycle` — requires `extraction_context.conditions_this_turn`
- `npc_presence` — requires `extraction_context`
- `pacing_directives` — requires `extraction_context`

This save uses `changes` key instead of `extraction_context`. The `ev.py check --all` command fails for these 4 checkers on every turn with "required field not found."

### Manual pacing check (from mechanics output)

- T1-T3: Tension ✓
- T4: Tension; Scene Pressure ✓
- T5-T25: Scene Imperative ✓ (scene_age ≥ 4, short-circuits all)
- T26-T27: empty directive ✓ (scene ended, no urgency)
- No removed directives ("location pressure", "location imperative", "combat fatigue") observed ✓

---

## 5. Inventory & Conditions

**Result: FAIL** | Confidence: **HIGH**

### 5a. Condition Cap Exceeded

`PC_CONDITIONS_MAX = 5` (from `ccya/state/delta_builder.py:23`). From `applied` data tracking active conditions:

| Turn | Active Count | Conditions |
|------|-------------|------------|
| T13 | 3 | pinned, wounded_chest, bleeding_chest |
| T16-T17 | 3 | bleeding_chest, pinned_by_lights, wounded_chest |
| T19 | 4 | bleeding, bleeding_chest, injured_ribs, wounded_chest |
| T20-T24 | 5 | at cap |
| **T21** | **6** | **bleeding, bleeding_chest, injured_ribs, lightheadedness, pinned, wounded_chest** |

T21 exceeds the cap by 1 condition.

### 5b. Condition IDs Not in Ruling Reason

**100% of condition additions have empty `ruling.reason`** — all 11 condition adds have empty `ruling.reason` text. The ruling prompt requires "Always include `reason` explaining why (≤10 words)" (`ccya/prompts/ruling_system.j2:44,75`). Without reason text, condition IDs can't satisfy the rubric check that "Condition IDs appear in ruling's reason text."

### 5c. Inventory Integrity

Inventory add/remove balance is correct — no negative amounts, no overdraws. All removed items existed in previous turn's inventory. ✓

### 5d. Previous Analysis Error

Previous analysis said "max concurrent is 2 (T12: Pinned + Wounded Chest, T13: Bleeding Chest alone)." This is **wrong**. It looked at `changes.player` which shows deltas, not active state. The actual concurrent count from `applied` data shows T21 at 6 conditions.

---

## 6. NPC Presence & Compendium

**Result: FAIL** | Confidence: **HIGH**

### NPC Ghosting — 13 turns where NPCs disappear from state with zero scene data

NPCs vanish from `state_snapshot.compendium.npcs` without `recently_left` scene tags, `JUST_LEFT` presence tags, or any scene compendium data:

| Turn | Disappeared NPCs | Scene Data |
|------|-----------------|------------|
| T4 | david_fisher | None |
| T5 | alexis_henson, joseph_gill | None |
| T10 | alexis_henson | None |
| T12 | alexis_henson, pale_creature_upstream | None |
| T15 | alexis_henson, pale_creature_upstream | None |
| T17 | alexis_henson | None |
| T18 | alexis_henson, silas_vane, patrol_soldiers | None |
| T19 | patrol_soldiers | None |
| T20 | alexis_henson, silas_vane | None |
| T23-T25 | alexis_henson, silas_vane, elias_thorne | None |
| T27 | joseph_gill | None |

This is a significant state consistency issue. NPCs should have departure tracking in scene output.

### Previous Analysis Error

Previous analysis said "No ghosting (NPCs disappearing without recently_left or JUST_LEFT)." This is **wrong**. 13 turns of confirmed ghosting with zero scene data for any departure tracking.

---

## 7. Location & Scene Transitions

**Result: FAIL** | Confidence: **HIGH**

Known bug (TICK-26): `applied.location_change` doesn't exist in events — field is `applied.location_description`. Checker returns "required field not found" for every turn. ✓ (confirmed)

---

## 8. Sanitizer Lifecycle

**Result: FAIL** | Confidence: **HIGH**

5 sanitizer events at T5, T10, T15, T20, T25 ✓

- All `threads_updated` IDs exist in state.arc.threads ✓
- No `goal_changed` noops ✓
- No threads_removed (correct — engine uses completed_threads) ✓

### Thread ID Mismatch (same as §2a)

Sanitizer adds `creature_ambush` at T10, but storyteller emitted `creature_ambush_threat` at T10. The sanitizer is not using the ID from the storyteller's thread_add, creating an orphan thread reference. This is the same pipeline bug as §2a.

---

## 9. LLM-Based Quality Checks

**Result: SKIPPED** | Confidence: **N/A**

LLM-based checkers require API access and are slower. Not checked in this session.

---

## Summary

| Rubric Area | Score | Confidence |
|---|---|---|
| 1. Momentum Lifecycle | 1.0 (PASS) | HIGH |
| 2. Thread Lifecycle & Arc Goals | 0.0 (FAIL) | HIGH |
| 3. GM Beat Lifecycle | 0.5 (FAIL) | MEDIUM |
| 4. Pacing Directives | 0.0 (FAIL) | MEDIUM |
| 5. Inventory & Conditions | 0.0 (FAIL) | HIGH |
| 6. NPC Presence & Compendium | 0.0 (FAIL) | HIGH |
| 7. Location & Scene Transitions | 0.0 (FAIL) | HIGH |
| 8. Sanitizer Lifecycle | 0.0 (FAIL) | HIGH |
| 9. LLM Quality Checks | — (SKIPPED) | N/A |

---

## Critical Bugs Found

1. **NPC ghosting** — 13 turns where NPCs vanish from state with zero scene departure data. State consistency issue.
2. **Thread ID mismatch** — Storyteller emits `creature_ambush_threat`, sanitizer adds `creature_ambush`. Pipeline sync failure.
3. **Condition cap exceeded** — 6 conditions active at T21, exceeding `PC_CONDITIONS_MAX = 5`.
4. **100% empty ruling.reason** — All condition additions have empty `ruling.reason`, violating rubric contract.
5. **Goal_update format mismatch** — Storyteller emits free-form text, sanitizer requires structured dict. Pipeline silently drops goal updates.
6. **3 consecutive escalation beats** (T10, T12, T13) — Exceeds 2-consecutive-same-type limit.
7. **extraction_context missing** — 4 checkers fail on every turn. This save uses `changes` instead.

---

## Comparison to Previous Analysis (cordyceps-findings.md)

The previous analysis had **3 major errors** caused by looking at `changes.*` (extraction deltas) instead of `applied.*` (actual state mutations) and `state_snapshot.*` (live state):

- **Thread lifecycle**: Claimed "only 1 thread mutation across 27 turns" — wrong, 27 turns have thread mutations in `changes.threads`
- **Condition cap**: Claimed "max concurrent is 2" — wrong, actual max is 6 at T21
- **NPC ghosting**: Claimed "no ghosting" — wrong, 13 turns of confirmed ghosting
- **Arc goal**: Claimed goal "persists throughout without update or resolution" — wrong, arc_resolved at T12/T18/T24

The previous analysis was fundamentally unreliable for condition, NPC, and thread lifecycle assessment because it used the wrong data source.

---

## Meta-Improvements for ev Tooling

These are structural issues that affect all games, not just this cordyceps session:

1. **No `narrate` extraction in events** — Events only contain `['scene', 'state', 'storytell']` in extraction. Cannot verify if `pacing_context` is rendered in narrate prompts without reading templates directly. This affects all games.

2. **`ev.py deltas` is very verbose** — Full JSON dumps make scanning 27 turns painful. A `--compact` flag showing only thread/inventory/condition/gm_beat changes in a summary format would save significant time. This affects all games.

3. **`ev.py mechanics --pacing` omits critical fields** — Doesn't show `beat_locked`, `consecutive_pressure`, or `momentum_floor`, which are essential for momentum/beat analysis. Add them to mechanics output. This affects all games.

4. **No compact thread lifecycle command** — `ev.py deltas` is the only way to find thread mutations, but requires scanning 27 verbose outputs manually. A dedicated `ev.py threads <save-dir>` command showing thread lifecycle across all turns in a compact table would be invaluable. This affects all games.

5. **`ev.py deltas` gm_beat output requires parsing** — Shows `storytell.gm_beat` in stderr, not structured output. A `ev.py beats <save-dir>` command showing turn-by-turn beat type + surface_as + beat_locked status in a compact table would be ideal. This affects all games.

6. **No arc goal history command** — Need to grep events manually for `goal_update` or `arc_resolve`. This affects all games.

7. **`ev.py trace` requires knowing exact paths** — e.g., `trace compendium.meta.pending_gm_beat` works but isn't discoverable. Better command documentation or auto-discovery would help. This affects all games.

8. **`ev.py mechanics --pacing` doesn't show `beat_locked`, `consecutive_pressure`, or `momentum_floor`** — These are critical for momentum lifecycle analysis but require reading events directly. Add them to mechanics output. This affects all games.

9. **`ev.py trace pc.momentum` requires manual cross-referencing** — Need band data from `--dice` to verify delta correctness. A combined command like `ev.py momentum-check <save-dir>` showing momentum + band + expected delta in one table would save significant manual work. This affects all games.

10. **No command shows `effective_scene_age` over time** — Needed to verify Scene Imperative firing at the right moment. This affects all games.

11. **No command shows `beat_expires_turn` over time** — Impossible to verify TTL expiration without reading events directly. This affects all games.

12. **`ev.py check sanitizer_lifecycle` requires `threads_removed` which doesn't exist** — The checker requires a field that was never emitted by the engine. Fixed in this session by removing `threads_removed` from `requires_fields` in `ccya/ev/checkers/sanitizer.py:13-14`. This affects all games.
