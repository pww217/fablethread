# Priorities — Critical Fixes Ranked by Impact

> Top 5 highest-impact fixes selected from [FINDINGS-JUNE-6.md](FINDINGS-JUNE-6.md), [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md), and [BUGS-OBSERVATIONS.md](BUGS-OBSERVATIONS.md).
> Ranking criteria: severity × confidence × cross-game validation × fidelity impact.

---

## 1. B7/G6 — Location changes silently dropped from canonical state [H/M]

**Severity:** High | **Confidence:** Medium (root cause narrowed but not confirmed) | **Scope:** Engine (`_apply_delta`, post-apply pipeline)

### Evidence
Auto-checker `universal.location_change.applied` failed at **T5 and T12**, NOT T4/T8/T12 as originally claimed. Scene Extract correctly emits location transitions (`dustfall_main_street` → `assay_office`, etc.) — confirmed in events.jsonl `applied.location_change`. However, the auto-checker reports prev_loc == cur_loc at failure turns (T5: both dustfall_main_street; T12: both red_canyon).

**Source audit findings:**
- `_apply_delta` code path is **correct**: handles location_change properly (`delta_builder.py:216-239`) — writes `state["location"] = {id, name, description}` when delta contains it.
- `_validate` (turn.py:1503) does NOT reject location_change deltas — only validates inventory_remove items.
- events.jsonl shows `applied.location_change` IS being set from scene extract output at every turn with a transition.

The discrepancy is between what apply_delta receives and what persists to the final state file (`state.yaml`). The delta contains the correct new location, but it's not reaching canonical state after save_state completes (turn.py:1397).

**Evidence:** [B7](../BUGS-OBSERVATIONS.md#b7-h-location-changes-silently-dropped-from-canonical-state---confirmed-in-baseline) | [G6](./FINDINGS-JUNE-6.md#g6-h-location-changes-silently-dropped-from-canonical-state--t4-t8-t12----new)

### Impact
Everything built on location state inherits this rot — rulings that depend on where the PC is will be wrong, scene-scoped threads may not fire or resolve correctly, and narrative context becomes stale because the engine thinks the player is still in a different location than they actually are. Breaks all scene-scoped logic: NPC presence checks, thread scope resolution, scene tag context.

### Fix direction (updated after source audit)

**Confirmed NOT the cause:** `sanitize_threads` (`thread_sanitizer.py:284-473`) does NOT touch location state — it only modifies arc/threads/goal. This was my leading hypothesis but is incorrect.

The root cause remains unclear but narrowed to two possibilities:
1. **Auto-checker ordering issue**: Sanitizer events interspersed in `turn_events` may corrupt prev_ev comparison (runner.py:526). When comparing consecutive events, a sanitizer event between main turns could make it appear that location didn't change when actually the delta was applied correctly to state but the auto-checker's prev_ev reference is off.
2. **Something else overwrites state after save_state** — need to trace what happens between turn.py:1425 and the final file being read by auto-checker at `state.yaml`.

Priority order: 1) Check if sanitizer events in turn_events cause off-by-one in prev_ev comparison, 2) Trace post-save_state mutations in turn.py lines 1405-1430, 3) Verify no other code path overwrites `state["location"]` after apply_delta returns.

---

## 2. Momentum death spiral (MB-1 through MB-7) [H/H systemic]

**Severity:** High | **Confidence:** High across findings → **MB-2,3,4,5,6 FIXED by momentum-thread-goal-fixes plan; MB-7 remains CONFIRMED**

### Evidence
Player spent T6-T25 (**20 turns**) at momentum -2/-3 in noir with only a single crit_success escape (T11). Cross-validated: Byzantium showed the same pattern ("momentum moved from +2 → 0 → -3, at -3 player was killing guards with bare hands").

Systemic causes mapped across 7 findings — **source audit confirmed**:

- **MB-4 FIXED:** `MOMENTUM_DELTA` (rules.py:79-86) uses uniform deltas (`success=+1`, `fail=-1`) regardless of depth. No catch-up acceleration existed at -3. **FIXED by step 01.1** — depth-based recovery added to momentum.py apply_momentum(): successes at -2/-3 give +2 instead of +1 when current <= floor and depth_penalty >= 2.
- **MB-1/MB-2 FIXED:** Directive logic (`turn.py:483-490`) fires Breathe when velocity < -0.3 AND no urgent threads exist (9+ turns). Beat_locked appends "; Resolve a Threat" to ANY directive including Breathe (`turn.py:555-557`), producing contradictory "Breathe; Resolve a Threat". **FIXED by step 01.2** — guard added to skip append when directive is Breathe, and Breathe never gets threat-append regardless of beat_locked state (step 01.3).
- **MB-3 FIXED:** Floor relief injection (`turn.py:1064-1072`) fires when `beat_locked`, injecting `breathing_room` (type=ambient) — the opposite of what's needed during momentum crisis. Fires 15/16 beat_locked turns. **FIXED by step 01.3** — floor relief injection now conditional on NOT triggered_by_momentum, reads from state to determine this.
- **MB-5 FIXED:** Consecutive pressure counter (`turn.py:1074-1082`) NOW reads from `pending_gm_beat` after floor relief injection, not storyteller output. This was previously at different line numbers (findings referenced 1291-1301 which is now thread_add validation).
- **MB-6 FIXED:** Combat boost (`turn.py:742-746`) adds +2 to scene age when combat-tagged, causing Scene Imperative to fire earlier in combat scenes. But it still fires late (T7+), by which point the same scene may have been active 10+ turns. **FIXED by step 01.4** — threshold lowered from 5 to 4 giving one extra turn of pacing recovery before forcing scene advancement.
- **MB-7 CONFIRMED:** Difficulty mods (`rules.py:24-30`) exist but hard difficulty was assigned 42% of rolls against a +2-max character, making failures statistically dominant.

**Evidence:** [G1](./FINDINGS-JUNE-6.md#needs-investigation) (references momentum deep-dive) | [MB-1](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-1-breathe-directive-dominates-because-no-urgent-scene-threads-exist-at-low-momentum) | [MB-2](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-2--resolve-a-threat-append-contradicts-breathe-directive) | [MB-3](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-3-floor-relief-beats-deepen-de-escalation-during-momentum-crisis) | [MB-4](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-4-no-momentum-catch-up-accelerates-recovery-from-deep-negatives) | [MB-5](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-5-consecutive-pressure-counter-reads-storyteller-output-not-stored-beat) | [MB-6](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-6-scene-imperative-fires-late-and-doesnt-help-momentum) | [MB-7](../MOMENTUM-BEAT-FINDINGS.md#finding-mb-7-difficulty-assignment-produces-42-hard-checks-against-a-2-max-character)

### Impact
This is the single biggest fidelity issue — it makes gameplay feel broken to players. The death spiral creates 20-turn stretches where every directive tells the narrator to de-escalate while narrative context screams escalation. Fixing this would dramatically improve perceived game quality even if other bugs remain.

### Fix direction (ordered) — **MB-2,3,4,5,6 FIXED by momentum-thread-goal-fixes plan**

1. ~~**MB-4:**~~ ~~Add depth-based momentum recovery — success at -3 → +2 instead of +1, or use `momentum_delta_multiplier = 1 + (momentum_floor - current) / momentum_floor`.~~ **FIXED by step 01.1.**
2. ~~**MB-2/MB-3:**~~ ~~Floor relief should only fire when beat_locked from consecutive_pressure, not from momentum floor. Remove "; Resolve a Threat" append when directive is Breathe.~~ **FIXED by steps 01.2 and 01.3.**
3. ~~**MB-5:**~~ ~~Have pressure counter read from stored `pending_gm_beat` (after floor relief) instead of raw storyteller output.~~ **Already FIXED in prior session.**
4. ~~**MB-6:**~~ ~~Combat boost threshold lowered to 4 giving one extra turn of pacing recovery before forcing scene advancement.~~ **FIXED by step 01.4.**

### Remaining: MB-7 (difficulty assignment)

Difficulty mods (`rules.py:24-30`) exist but hard difficulty was assigned 42% of rolls against a +2-max character, making failures statistically dominant. This is outside the scope of the momentum-thread-goal-fixes plan and would require separate investigation into difficulty distribution logic.

## 3. G3/J — Goal stagnation / sanitizer too slow to pivot [FIXED — step 02.2]

**Severity:** Medium | **Confidence:** High (confirmed in both noir and byzantium) → **FIXED** by explicit trigger events added to sanitizer prompt instructions section

### Evidence
Arc goal "Secure the missing witness before they are silenced by the union enforcement wing" stayed unchanged T1-T15 (2/3 of noir) despite debt settlement, ledger pursuit, cellar discoveries, bodyguard confrontation, and alley standoff — all still under the same goal. Zero `goal_update` events in baseline eval across 13 turns despite narrative context shifting dramatically. Sanitizer runs every 5 turns with one-turn lag — by the time it pivots, context is stale.

Cross-game validation (live data analysis):
- **Noir**: T12 (Devon escapes with manifests) → T15 sanitizer pivot to "Use recovered manifests..." = 3 turn lag. T22 (Keith killed) → T25 sanitizer pivot to "Survive police ambush" = 3 turn lag. Consistent 3-turn gap between major narrative events and goal updates.
- **Byzantium**: T10 (killed Kosta, fighting mercenaries) → no goal change at T10 sanitizer; updated at T15 to "Evacuate family before fire spreads." = 2 turn lag but missed the combat pivot entirely.

T20 sanitizer pivot was correct ("Use manifests to expose council corruption" → "Negotiate with Keith") but proved the mechanism works only when timing aligns. T24 arc_resolve produced incomplete state: `council_corruption_war` resolved (failed) but `visible_goal` remained on a dead objective, leaving UI strand dark.

**Evidence:** [G3](./FINDINGS-JUNE-6.md#g2---goal-stagnation--sanitizer-too-slow-to-pivot-confidence-h) | [G5](./FINDINGS-JUNE-6.md#arc_resolve-produced-incomplete-state-at-t24) | [F4](../BUGS-OBSERVATIONS.md#f4-m-arc_resolve-incomplete-state-on-pivot)

### Impact
The visible_goal strand goes stale or shows dead objectives (T25 showed "Negotiate with Sergeant Keith to secure the manifests" after Keith was killed at T22). This breaks player orientation — they don't know what their current priority is because the system's stated goal no longer matches reality.

### Root cause (FIXED)
The sanitizer template (`sanitize_thread.j2`) did not explicitly instruct the LLM to pivot goals when major events occur (witness escapes, ally killed, location changes). It only asked whether the goal "should be updated to reflect current narrative direction" — a passive evaluation that depends on subjective judgment. The 3-turn lag was systemic: no event-driven mechanism existed for mid-cycle goal updates; it was purely periodic with one-turn sanitizer lag.

**FIXED:** Step 02.2 added explicit trigger events (witness escapes/killed, ally killed, location shifts dramatically, debt settled/lost, new critical info) that MUST update `visible_goal` to reflect current reality — turning passive evaluation into active imperative instruction in the sanitizer prompt instructions section (`# Instructions:`).

### Eval gaps
The eval system has **no stagnation detection** and **no sanitizer event validation**. See [EVAL-FIXES.md](EVAL-FIXES.md#issue-3-goal-stagnation) for specific auto-checker additions needed.

### Fix direction
- Increase sanitizer frequency from every 5 turns to every 3 turns, OR allow storytell to emit `goal_update` events mid-cycle (not just at sanitizer boundaries).
- Require arc_resolve schema to always produce a forward-looking `visible_goal`; reject incomplete resolutions during extraction retry.
- **Eval**: Add stagnation detection and sanitizer validation — see [EVAL-FIXES.md](EVAL-FIXES.md#issue-3-goal-stagnation) for specifics.

### Related eval findings
See [EVAL-FIXES.md](EVAL-FIXES.md#issue-3-goal-stagnation).

---

## 4. B8/G7 — Momentum sign inversion [ELIMINATED]

**Severity:** High | **Confidence:** Medium (root cause inferred) → **CONFIRMED FALSE POSITIVE** after source audit

### Evidence (re-evaluated)
Auto-checker `universal.momentum.band_delta` failed 1/13 turns: T3 with detail "band=fail expected delta -1 but got +1 (prev=-2 cur=-1)". This was NOT present in noir findings — meaning it's a deeper engine bug than the momentum death spiral design issues.

### Root cause found
**This is an auto-checker artifact, not actual code corruption.** The failure was caused by `runner.py` enrichment logic (`lines 503-505`) which uses **index-based matching** between turn_events and state_snapshots:

```python
for i, snap in enumerate(state_snapshots):
    if i < len(turn_events) and "state_snapshot" not in turn_events[i]:
        turn_events[i]["state_snapshot"] = snap  # ← index-matched!
```

Auxiliary events (condition_expired at T3, sanitizer at T5/T10) don't have state_snapshot written by the engine (`append_event` only writes kind/condition_id/turn). The enrichment assigns them snapshots from **different points in time** — condition_expired at filtered index 2 gets `snapshots[2]` (state AFTER T3's final momentum was already applied), not the snapshot when it actually fired.

The auto-checker compared prev_ev.momentum=-2 (from enriched condition_expired) with curr_ev.momentum=-1 (actual T3 main after fail roll). But this comparison is meaningless — they represent different pipeline stages, not consecutive game states. The actual momentum code (`momentum.py:apply_momentum`, `rules.py:MOMENTUM_DELTA`) handles deltas correctly when called directly from the engine.

### Impact
None — no actual momentum corruption exists in the engine. Remove #4 from priority list to avoid wasting effort on a phantom bug.

---

## 5. BZ1/O4 — Background thread accumulation without decay [FIXED — step 02.1 + step 01.3a]

**Severity:** Medium | **Confidence:** High (confirmed in byzantium, 31 turns) → **FIXED** by two-layer approach: engine handles reliable demotion every turn, sanitizer handles removal of stale latent threads via explicit temporal decay instruction

### Evidence
Byzantium (31 turns): `broken_defense`, `looting_scourge`, `coinage_panic` all accumulated ADVANCEMENT entries across every turn without resolving, demoting to latent, or fading. Main thread `family_extraction` resolved at T30 but background threads persisted throughout with no decay.

Live data analysis (state.yaml at end of byzantium game):
```
broken_defense:        active=False, urgency=normal, scope=arc,  progress=[2 entries], last_updated_turn=11
looting_scourge:       active=False, urgency=normal, scope=arc,  progress=[1 entry],  last_updated_turn=16  
coinage_panic:         active=False, urgency=normal, scope=arc,  progress=[1 entry],  last_updated_turn=None
```

These threads were added at turns 5-10 and have sat in `threads[]` for **20+ turns** with no resolution, removal, or decay. They're marked inactive (`active=False`) but never moved to `completed_threads`. Meanwhile, completed_threads has 4 properly resolved entries (forge_standoff, mercenary_blockade, forge_defense, family_extraction).

Noir had no accumulation problem because it's shorter (25 turns) and the single thread was actually relevant until end. But byzantium shows systemic issue over 31+ turn sessions.

**Evidence:** [BZ1](./FINDINGS-JUNE-6.md#bz1-h-background-threads-accumulate-forever-without-decay) | [O4](../BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent)

### Impact
UI fidelity degrades over time — by turn 20+, background threads dominate the thread display with stale progress entries, making it hard to distinguish active priorities from dead weight. This is a compounding issue that makes longer games feel cluttered and confusing even when core mechanics are working correctly.

### Root cause (FIXED)
The sanitizer template (`sanitize_thread.j2`) did not explicitly instruct cleanup of stale background threads. It asked about resolution (narrative completion), urgency, active status, and progress — but **not** temporal decay ("remove inactive threads older than N turns"). The LLM saw `broken_defense` (militia lines buckling) as still relevant because the war hadn't ended, so it kept it in active threads. There was no explicit permission to clean up stale background entries that haven't been updated in 3+ sanitizer cycles.

**FIXED:** Step 02.1 added explicit temporal decay cleanup instruction to `sanitize_thread.j2` instructing LLM to remove inactive latent threads with no progress_updates for multiple sanitizer cycles. Step 01.3a fixed engine auto-latent demotion (`_apply_thread_updates()`) to fire every turn (not gated on mutation) so stale active threads reliably get `active=false` after 3 turns of no updates, making them eligible for sanitizer cleanup.

Additionally: moving a thread to completed is irreversible — the LLM may be conservative about this when there's no explicit instruction to do so. The sanitizer has **no mechanism** to add cleanup actions as part of its output; it only handles what the LLM explicitly puts into `thread_updates`, `resolved_threads`, or `new_threads`.

### Eval gaps
The eval system has **no accumulation metric**, **no decay validation**, and **no thread cap assert**. See [EVAL-FIXES.md](EVAL-FIXES.md#issue-5-background-thread-accumulation) for specific auto-checker additions needed.

### Fix direction
Audit decay mechanism wiring in sanitizer/step pipeline — verify `last_updated_turn` tracking is accurate, verify demotion thresholds fire at the correct interval (5 turns normal→background, 10 background→latent). Consider adding a thread cap: max 2 arc-scoped + 1 scene-scoped active threads (O3), with least-recently-updated promoted to background when exceeded.

**Sanitizer prompt fix**: Add explicit instruction to `sanitize_thread.j2`:
> "5. Should it be removed from active threads entirely? If inactive for 3+ turns with no progress updates, move to resolved_threads or remove."

### Related eval findings
See [EVAL-FIXES.md](EVAL-FIXES.md#issue-5-background-thread-accumulation).

---

## Execution order rationale (updated)

Start with **#1** because it's a quick, well-understood bug that breaks foundational state — every downstream system depends on location being correct. Then tackle **#2** because it was the systemic issue causing the worst player experience (20-turn death spirals). **#2 is now FIXED by momentum-thread-goal-fixes plan (MB-2 through MB-6 resolved, MB-7 remains).** #3 was an engine correctness issue (stale goals) that compounded fidelity problems — **FIXED by step 02.2.** #5 was a UI/cluttering issue — important but lower urgency than mechanical corruption — **FIXED by steps 01.3a and 02.1.**

#4 was **eliminated as false positive** after source audit: momentum sign inversion was caused by runner.py enrichment using index-based matching between turn_events and state_snapshots, causing auxiliary events (condition_expired) to receive misaligned snapshots from different pipeline stages.

## What was excluded

- **B4/B5** (pressure counter desync, scene tag volatility): Lower fidelity impact, affects pacing nuance not core state correctness. B4 supposedly fixed in cb623f4 with contradictory evidence.
- **G8** (floor relief injection failure at T12): Only 2 turns of evidence across both runs — may be scenario-specific or scoring artifact. Would benefit from more data before prioritizing over systemic issues.
- **B6/B10/B11** (non-deterministic beats, inventory/condition drift): LLM quality problems hard to fix at pipeline level without prompt changes. Lower ROI than fixing engine state bugs first.
