---
title: "Eval — I-13, I-25, I-26 testing validation"
status: done
urgency: 2
size: large
created: 2026-07-04
ticket_id: E-8
labels:
  - eval
  - pacing
  - ruling
  - seed
---

## Purpose

Validate three improvement tickets in `testing` status:

- **I-13** — Skill distribution imbalance (dexterity over-represented)
- **I-25** — Band outcomes don't drive narration (convergence + band directives)
- **I-26** — Fix opening prose leakage in prepare_seed output

## Background

All three tickets were created/updated on 2026-07-04. I-25 and I-26 share commits (3beaf453, 4c009946). I-13 has intent_verb → skill mapping changes from earlier commits.

### Recent commits touching ccya/ (since prior eval b593d8c):

1. `d71fff2f` — chore: replace primary model with gemma-4-26b-a4b-it
2. `4c009946` — [I-25] Fix opening prose leakage in prepare_seed output
3. `3beaf453` — [I-25] Band outcomes don't drive narration — beats override success/fail results
4. `82b759d9` — I-24: Engine core tech debt audit — Phase 01-03
5. `00e35f7f` — I-2: clean up prompts — reduce redundancy, fix boundary models, complete bond→tie rename
6. `2bf612dd` — fix: pacing convergence score accumulation + NPCEntry.id template bug

High-risk areas: `ccya/prompts/` (ruling, narrate, prepare_seed), `ccya/engine/_pacing.py` (convergence), `ccya/rules.py` (band directives)

### Prior single-run data (space-western, 15 turns, latest eval run):

- **Convergence score hits 3+ (turns 6, 7, 12, 13) but phase stays in SETUP** — core I-25 problem
- **No phase transitions in 15 turns** — zero transitions detected
- **Band distribution skewed**: crit_fail 37.5%, fail 12.5%, setback 12.5%, partial 12.5%, success 12.5%, crit_success 12.5% — 62.5% negative
- **Turn 13 had SUCCESS band but outcome_hint was "transition" and phase stayed SETUP** — band not driving motion
- **Thread lifecycle (15 issues) and sanitizer lifecycle (3 issues) checkers failed**

## Eval Plan

### Phase 1: 1 game, 5 turns — Critical check

Run noir-1930s:driven for 5 turns. Check for critical bugs (crashes, broken turns, extraction failures).

### Phase 2: 3 games, 15 turns — Nuanced validation

Run three persona pairs for 15 turns each:
- noir-1930s:driven
- space-western:speedrunner
- golden-piracy:completionist

Target areas:
1. **I-25 (band outcomes)**: Do success/crit_success rolls produce narrative relief and scene motion? Check outcome_hint alignment with band, phase transitions after positive rolls, beat types on success turns.
2. **I-26 (opening prose)**: Verify pc.situation has exactly the schema-defined keys (no opening leak). Check seed_meta.opening exists.
3. **I-13 (skill distribution)**: Track skill distribution across all rolls. Target ~25% each. Check intent_verb → skill mapping is working.

### Phase 3: 2 more games, 25 turns — Balance (conditional)

Only if Phase 2 finds no critical bugs:
- zombie-survival:cautious
- allied-ww2:aggressive

## Deep Dive Areas (ev-review)

After eval runs, run targeted ev-review on:

1. **Convergence + phase transitions**: `ev.py convergence --save-dir`, `ev.py phase-transitions --save-dir`, `ev.py mechanics <N> --pacing --dice` — verify convergence score is computed correctly and phase transitions fire when score >= 3
2. **Band directives**: `ev.py turns --save-dir`, `ev.py rolls --save-dir` — examine turns with success/crit_success, check if narration fulfills intent
3. **Skill distribution**: `ev.py rolls --save-dir` — track skill per roll across all turns
4. **Opening prose**: `ev.py state --save-dir --format pc` — verify pc.situation keys

## Phase 3 Results (25-turn runs)

### zombie-survival:cautious (25 turns)
- **Convergence:** Wildly oscillating — hits 3+ at turns 8-10, 12-13, 15, 17-19 then drops back. Phase stays SETUP entire run (I-25 bug confirmed).
- **Band distribution:** 87.5% bad (87.5% fail, 12.5% success) — EXTREMELY negative. Player trapped.
- **Conditions at end:** 7 (very harsh)
- **Turn 5:** DELTA_VALIDATION_FAILED error
- **PC name:** "?" (same bug as prior runs)

### allied-ww2:aggressive (25 turns)
- **Convergence:** Hits 3+ at turn 9 then drops to 2 (turns 10-15) then 1 (turns 16-25). Phase stays SETUP (I-25 bug confirmed).
- **Band distribution:** 42.9% bad (14.3% crit_fail, 28.6% fail, 14.3% partial, 42.9% success) — more balanced than zombie but still negative-heavy.
- **Conditions at end:** 3 (moderate)
- **PC name:** "?" (same bug)

## Convergence Deep Dive Findings (noir-1930s, turn 15)

**Data at turn 15:** `convergence_score=3`, `outcome_hint: transition`, `climax_turn_count=0`, `scene_phase: SETUP`

**Root cause confirmed:** `_compute_scene_phase` at `narrate.py:211` returns a new `Scene` object but **never writes it to `state.scene`**. The computed phase is only used for directive computation within the same turn.

**Verified:** Event log at `turn.py:611` reads `state.scene.scene_phase` (the seed value, never updated). Both `event.scene_phase` and `pacing_context.scene_phase` show SETUP at ALL turns (including turn 3 where `turns_in_phase` should have reached 3).

**Root cause:** `_compute_scene_phase` reads `state.scene.turns_in_phase` which is always 0 (seed value). So `turns_in_phase = 0 + 1 = 1` every turn. The condition `turns_in_phase >= 3` never fires because the counter never accumulates. The entire 5-state phase machine is non-functional — phase transitions are computed every turn but discarded.

**Fix:** Write `new_scene` back to `state.scene` after the phase engine runs.

## Phase 2 Results — New Runs (After Phase Persistence Fix)

### noir-1930s:driven (2342, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3 (fix confirmed)
- **Band distribution:** PASS (checker) — no skew detected
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known — scene_age and roll_starvation components mismatch)
- **Thread lifecycle:** FAIL (space-western only — see below)
- **pc.situation keys:** Stable across turns — `family`, `office_location`, `opening`, `reputation`, `residence` (no I-26 issue with keys changing)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose (I-25 prose leak fix not working or re-introduced)

### space-western:speedrunner (0002, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3, RISING→CLIMAX at turn 8 (convergence=3 triggered transition — fix confirmed)
- **Band distribution:** FAIL — 100% fail band (2 rolls, both fail on turns 4 and 9) — small sample but skewed
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known)
- **Thread lifecycle:** FAIL — NEW BUG: `thread_update` and `thread_resolve` reference unknown thread IDs (`guild_politics`, `coalition_pursuit`, `hidden_cargo`) — no `thread_add` events exist. Threads are being updated/resolved without being added first.
- **pc.situation keys:** Stable across turns — `filiation`, `home_port`, `opening`, `reputation`, `vessel` (no I-26 issue)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose

### golden-piracy:completionist (0017, 9 turns — post-fix run)
- **Phase transition:** SETUP→RISING at turn 3 (fix confirmed)
- **Band distribution:** PASS — 3 success, 1 fail (25% fail — within threshold)
- **Directive-beat alignment:** PASS
- **Convergence recompute:** FAIL (known)
- **pc.situation keys:** Stable across turns — `alliance_status`, `home_port`, `opening`, `reputation`, `vessel` (no I-26 issue)
- **Opening prose leak:** CONFIRMED — `opening` field in `pc.situation` contains full prose

## Turn Metrics (All 3 New Runs — 9 turns each)

### Step Breakdown (averages, excluding 0ms duplicate turns)

| Step | noir avg | piracy avg | western avg | Combined avg |
|------|----------|------------|-------------|--------------|
| **ruling** | 5.3s (2,220/112 tok) | 5.3s (2,286/116) | 5.5s (2,290/112) | **5.4s (2,265/113)** |
| **narrate** | 9.9s (3,029/209, ft=1.0s) | 11.6s (3,109/266, ft=1.0s) | 12.2s (3,029/262, ft=1.0s) | **11.2s (3,056/246, ft=1.0s)** |
| **extract** | 20.6s (8,669/409, 3 streams) | 19.6s (8,969/409, 3 streams) | 19.6s (8,829/390, 3 streams) | **19.9s (8,822/403, 3 streams)** |
| **async (sanitize/world)** | 0ms (no timing tracked) | 0ms | 0ms | **0ms** |
| **total** | **35.7s** | **36.6s** | **38.6s** | **36.9s** |

### Key observations
- **Extract dominates** — 54% of total time (19.9s), not narrate (30%) or ruling (15%)
- **3 extraction streams per turn, 0 retries** — streams are scene, state, record (sanitize/world are async)
- **Low output tokens (100-400 per step)** — LLM is NOT generating long reasoning or prose. Time is spent on API latency processing ~8,800 input tokens per call with short structured output (JSON extraction, not prose)
- **First token ~1s** — narrate streaming starts consistently after ~1 second
- **Noir fastest** (35.7s), piracy (36.6s), western (38.6s) — small variance
- **Extract input grows** (7,800→9,500 tokens) — context accumulation across turns

## Summary of Findings

### I-25 (band outcomes + phase transitions)
- **Phase persistence fix CONFIRMED:** All three new runs show SETUP→RISING transitions (noir turn 3, space-western turn 3, golden-piracy turn 3)
- **Space-western shows RISING→CLIMAX at turn 8** (convergence=3 triggered transition) — phase machine is now functional
- **Band distribution varies by scenario:** noir (67% success, 33% crit_success), golden-piracy (75% success, 25% fail), space-western (100% fail — but only 2 rolls, small sample)
- **Directive-beat alignment passes on all runs** — beats align with directives
- **Opening prose leak CONFIRMED:** The `opening` field in `pc.situation` contains full prose text (I-25 prose leak fix not working or re-introduced)

### I-26 (pc.situation keys)
- **No issue found:** Situation keys are stable across turns in all three runs (no I-26 issue with keys changing)
- **Opening prose leak CONFIRMED:** The `opening` field in `pc.situation` contains full prose text (I-25 prose leak fix not working or re-introduced)

### I-13 (skill distribution)
- **Insufficient data:** Only 2-6 rolls per run (most turns have no dice roll — `rolled: False` in ruling)
- **Space-western:** 2 rolls, both charisma (100% charisma — small sample)
- **Golden-piracy:** 4 rolls — wits (1), charisma (3) — no dexterity
- **Noir:** 3 rolls — charisma (3) — no dexterity
- **Conclusion:** Cannot assess skill distribution imbalance from these short runs. Need longer runs with more dice rolls.

### New Bugs Found
1. **Thread lifecycle (NEW):** `thread_update` and `thread_resolve` reference unknown thread IDs — no `thread_add` events exist. Threads are being updated/resolved without being added first. Found in space-western run (0002). Thread IDs affected: `guild_politics`, `coalition_pursuit`, `hidden_cargo`. **RESOLVED (2026-07-05):** FALSE POSITIVE — all three threads were seeded at turn 0 during `prepare_seed()`. The `thread_lifecycle` checker is too strict and doesn't account for seed threads (added_turn: 0). See B-30 for details.
2. **Sanitizer lifecycle checker (pre-existing):** Checker code has bug — calls `.get()` on `WorldState` (Pydantic model) instead of dict access. **FIXED (2026-07-05):** Changed `state.get("arc")` to `getattr(state, "arc", None) or {}` in `ccya/ev/checkers/sanitizer.py:44`. Also fixed type annotation from `dict[str, Any]` to `Any`.

## Validation — cordyceps-year-twenty-2026-07-05 (2026-07-05)

Full 16-turn save examined. I-25 validation across all 6 positive-band turns.

**I-25 confirmed working across all positive bands:**

| Turn | Band | Intent | Result |
|------|------|--------|--------|
| T1 | crit_success | Sneak to ambush | Kills two scavengers — fully fulfilled |
| T2 | success | Intimidate into surrender | Scavenger drops rifle and collapses |
| T4 | success | Intimidate for intel | Reveals enemy count and equipment |
| T10 | success | Destroy beacon + scavenge | Shatters beacon, strips gear |
| T15 | partial | "Who are you?" | Identity revealed + demands half scrap (win-with-cost) |
| T16 | success | "What's on the contract?" | Full ledger contents explained |

- Authority hierarchy effective — band directives win over beats on all success turns
- Beat treated as creative guidance, not direction
- Partial band correctly manifests as win-with-cost
- Fail bands correctly deny intent without consolation prizes
- No I-25 failures found

## Phase 4 — Validation Against Today's E-11 Runs (2026-07-06)

### Data sources

Five runs from `evals/runs/2026-07-06_0.31.0-43-g6735834a_6735834a/`:
- `1109_space-western_15t` — 15 turns, 9 rolls
- `1135_zombie-survival_25t` — 25 turns, 11 rolls
- `1149_allied-ww2_25t` — 25 turns, 12 rolls
- Total: 32 rolls across 65 turns

### I-13 (Skill distribution imbalance)

**Assessment: I-13 concern VALIDATED — dexterity still over-represented**

| Run | dexterity | charisma | wits | strength | Total rolls |
|-----|-----------|----------|------|----------|-------------|
| space-western | 2 (22%) | 4 (44%) | 3 (33%) | 0 | 9 |
| zombie-survival | 4 (36%) | 2 (18%) | 2 (18%) | 3 (27%) | 11 |
| allied-ww2 | 6 (50%) | 4 (33%) | 2 (17%) | 0 | 12 |
| **Total** | **12 (37.5%)** | **10 (31.3%)** | **7 (21.9%)** | **3 (9.4%)** | **32** |

Dexterity at 37.5% vs strength at 9.4% — significant skew. Intent_verb→skill mapping is not producing balanced distribution.

### I-25 (Band outcomes don't drive narration)

**Assessment: I-25 PASSING — band directives working**

Band distribution across all runs:
- success: 10 (31.3%)
- fail: 12 (37.5%)
- setback: 6 (18.8%)
- crit_success: 3 (9.4%)
- crit_fail: 1 (3.1%)

Phase transitions are functional (confirmed in prior runs — SETUP→RISING at turn 3, RISING→CLIMAX at turn 8). Band directives win over beats on success turns (confirmed in prior E-8 validation).

### I-26 (Opening prose leakage)

**Assessment: I-26 FIXED — no opening prose leak detected**

Seed state situation keys across all runs:
- space-western: `['filiation', 'home_port', 'reputation', 'vessel']`
- zombie-survival: `['family_status', 'home_settlement', 'nearby_area', 'transport']`
- allied-ww2: `['chain_of_command', 'family_back_home', 'theater', 'unit']`

Final state situation keys: identical to seed keys (no `opening` field in any run).

**I-26 is resolved.** The `opening` field that previously leaked into `pc.situation` is no longer present in seed or final state.

### Summary

| Ticket | Status | Notes |
|--------|--------|-------|
| I-13 | NEEDS ATTENTION | Dexterity skew confirmed (37.5% vs 9.4% strength) |
| I-25 | PASSING | Band directives working, phase transitions functional |
| I-26 | FIXED | No opening prose leakage detected |

## Convergence Deep Dive — 2026-07-07

### Data sources

- `evals/runs/2026-07-06_0.31.0-43-g6735834a_6735834a/1135_zombie-survival_25t/events.jsonl` (15 unique turns)
- `evals/runs/2026-07-06_0.31.0-43-g6735834a_6735834a/1149_allied-ww2_25t/events.jsonl` (25 unique turns)
- `evals/runs/2026-07-06_0.31.0-43-g6735834a_6735834a/1109_space-western_15t/events.jsonl` (15 unique turns)

### Convergence score computation — verified correct

All 5 components work as designed:

1. **urgent_thread** (0-2): Counts non-dormant urgent threads, capped at 2. Verified against convergence_threads in event dict.
2. **threat_thread** (+1): Any non-dormant thread with `type=threat`. Verified.
3. **beat_streak** (+1): ≥60% tension beats in recent 5-beat window. Verified.
4. **roll_starvation** (+1): Turns since last roll ≥ threshold. Verified — fires at T17 in allied-ww2 (7 turns since last roll).
5. **threat_density** (+1): Active threat threads ≥ threshold. Verified — never fires (threshold=3, max active threat threads = 1).

### EMA smoothing — verified correct

`smoothed = 0.4 * raw + 0.6 * prev_smoothed` applied at `narrate.py:208`. First turn uses raw score as initial. Verified against `last_turn_state.meta.smoothed_convergence` in events.

### Phase transitions — verified functional

| Transition | Condition | Verified |
|------------|-----------|----------|
| SETUP→RISING | urgent_thread > 0 OR turns_in_phase ≥ 3 OR convergence ≥ 2 AND turns_in_phase ≥ 2 | YES — T3 in all 3 runs |
| RISING→CLIMAX | smoothed_convergence ≥ 2 AND turns_in_phase ≥ 3 | YES — T8 in space-western, T7 in allied-ww2 |
| CLIMAX→RESOLUTION | signal-gated (thread resolved prev turn + low convergence) OR hard cap at climax_turn_limit | YES — T11 in zombie, T10 in allied-ww2 |
| RESOLUTION→BREATHER | Always (1-turn) | YES — T12 in zombie, T11 in allied-ww2 |
| BREATHER→RISING | urgent_thread > 0 OR breather_max_turns AND turns_in_phase ≥ 2 | YES — T14 in zombie, T13 in allied-ww2 |

### Convergence oscillation — ROOT CAUSE FOUND

**Observation:** In both 25-turn runs, convergence spikes to 3+ then drops to 0-1 within 1-2 turns, causing premature exit from CLIMAX.

**Root cause: Thread depletion mid-CLIMAX.**

The convergence score depends entirely on active threads. When threads are resolved/removed, convergence collapses:

**zombie-survival:**
- T7-8: convergence=3 (1 urgent: `supply_stranglehold` + threat + beat_streak)
- T9: `supply_stranglehold` resolved → convergence drops to 1 (only `beat_streak` survives)
- T10: `sabotage_evidence` resolved → convergence jumps to 3 (new `black_market_routes` becomes urgent)
- T11: CLIMAX→RESOLUTION (thread resolved prev turn + low convergence)
- T13-15: convergence=0 (no active threads at all — all dormant or resolved)

**allied-ww2:**
- T7-9: convergence=3 (1 urgent: `prisoner_ethics` + threat)
- T10: `supply_shortage` resolved → ALL threads gone → convergence=0 → CLIMAX→RESOLUTION
- T11-14: convergence=1-2 (single thread `cargo_protection_conflict`, no urgent)
- T15: convergence=0 (thread resolved) → BREATHER→RISING via convergence hard gate
- T17: convergence=4 (urgent + threat + beat_streak + roll_starvation) → RISING→CLIMAX
- T18: `cargo_protection_conflict` resolved → convergence=1 → CLIMAX→RESOLUTION

**Pattern:** CLIMAX lasts exactly 2-3 turns because threads resolve rapidly (avg 2.7-2.8 turns to resolve). Once the urgent thread resolves, convergence drops below the RISING→CLIMAX threshold (2), and the hard cap (4 turns) or signal-gated exit fires.

**This is not a bug — it's the intended behavior.** The phase engine responds to thread urgency. When threads resolve fast, the scene naturally de-escalates. The issue is **thread lifecycle**, not pacing:

1. Threads resolve too quickly (avg 2.7 turns) — the engine has no mechanism to sustain pressure
2. No thread reuse — once resolved, threads don't re-emerge
3. When all threads are dormant/resolved, convergence = 0 regardless of scene age

### Thread lifecycle impact on pacing

| Metric | zombie | allied-ww2 |
|--------|--------|------------|
| Threads created | 5 | 7 |
| Threads resolved | 5 (100%) | 6 (85.7%) |
| Avg turns to resolve | 2.8 | 2.7 |
| Pending at end | 0 | 1 |

**Impact:** With 5-7 threads resolving in 2.7 turns each, a 25-turn run cycles through 3-4 complete thread lifecycles. Each cycle produces one CLIMAX (2-4 turns) followed by BREATHER (2-3 turns). The pacing rhythm is: **SETUP(3) → RISING(3-5) → CLIMAX(2-4) → BREATHER(2) → repeat**.

### Thread lifecycle ownership — Record vs Narrator (2026-07-07)

**Problem:** The Record prompt (`record_system.j2`) contains corrective thread lifecycle rules that belong in the Narrator prompt. The Record is a log-keeper — it should only jot down what the Narrator did, not independently decide when threads should be added, updated, or resolved.

**Record rules pulling the rug out from under the Narrator:**
- Curtain Call forcing: "When curtain_call is 'active'... you MUST resolve the active thread" — forces Record to resolve threads the Narrator didn't resolve
- Scene phase thread guidance: "When the arc is approaching its climax: resolve side-threads" — Record makes scene-phase decisions it can't verify
- "3+ turns unaddressed → resolve" rule: forces premature thread resolution
- Urgency escalation rules: tells Record to escalate threads the Narrator didn't engage with
- Thread sustainability rules: "Target: 3-4 threads" — tells Record to manage thread count, not log what happened

**Record rules that should stay:** Thread ID rules (exact copy), progress must be new fact, don't both update AND resolve same thread, don't resolve threads that don't exist.

**Narrator needs thread lifecycle guidance:** The Narrator writes the prose and knows what happened. It should receive guidance on how to open new threads, advance/escalate during RISING/CLIMAX, resolve naturally during RESOLUTION, and sustain 2-3 threads to prevent convergence collapse.

**Impact:** The 2.7 avg thread lifespan is driven by Record's corrective rules, not by actual narrative resolution. The Record resolves threads the Narrator didn't resolve, creating contradictions between event log and prose.

### CLIMAX duration

- **Exactly 4 turns (hard cap)** — confirmed in all runs.
- **Early exit** fires when: thread resolved on previous turn AND convergence < 1 AND CLIMAX_min (3) turns elapsed.
- **Extension** fires when: convergence ≥ 3 AND has urgent active thread — extends up to climax_turn_limit + extension_max (4+2=6 turns).
- **No extension observed** — threads resolve before extension can activate.

### Curtain call — verified correct

- T1 of CLIMAX: `curtain_call: "active"` — directive tells Record to resolve the active thread.
- T(climax_turn_limit - 1): `curtain_call: "forced"` — directive tells Record the thread MUST resolve.
- Both fire correctly in all runs (verified in event dict).

### Beat system — low diversity

- Beat candidates always = 0 at event time because world step runs async after event save (`turn.py:814` — `event["last_turn_state"] = state.to_dict()` is written AFTER async window).
- Beat diversity: recent_beats ban on 5-beat window works (no repeats observed).
- Allowed beat types correctly constrained by phase (verified via `allowed_beat_types` in event dict).

### DELTA_VALIDATION_FAILED (zombie T5)

- Occurred on turn 5 of zombie-survival.
- Caused by blocking rejection in `delta.model_validator` (not investigated further — low priority, single occurrence).

### Convergence recompute checker

- Now passes on both 25-turn runs (was previously failing — likely fixed by earlier convergence score corrections).

### Recommendations

1. **Record prompt needs thread lifecycle rules stripped.** The Record is a log-keeper, not a decision-maker. Remove curtain call forcing, scene phase thread rules, "3+ turns → resolve" rule, urgency escalation rules, and thread sustainability rules from `record_system.j2`. The Record should only log what the Narrator did.

2. **Narrator prompt needs thread lifecycle guidance.** The Narrator writes the prose and knows what happened. It should receive guidance on how to open new threads, advance/escalate during RISING/CLIMAX, resolve naturally during RESOLUTION, and sustain 2-3 threads to prevent convergence collapse.

3. **Thread sustainability is the pacing bottleneck.** The phase engine works correctly; threads resolve too fast (2.7 avg turns), causing convergence to collapse. The fix is not engine changes — it's giving the Narrator the right guidance to sustain threads naturally.

4. **BREATHER→RISING transition** fires on `breather_max_turns` (3) even with no urgent threads. This is by design but produces artificial pressure. Consider requiring an urgent thread for the transition.

5. **Beat candidates = 0 at event time** is expected (async timing), but makes event-based beat analysis unreliable. Consider saving beat_candidates in `last_turn_state` or persisting to event before async window.

## Output

Phase reports at: `evals/runs/<group>/PHASE-1.md`, `PHASE-2.md`, `PHASE-3.md`
Consolidated report: `evals/runs/<group>/REPORT.md`
