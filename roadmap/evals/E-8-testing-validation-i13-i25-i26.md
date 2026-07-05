---
title: "Eval — I-13, I-25, I-26 testing validation"
status: new
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

## Output

Phase reports at: `evals/runs/<group>/PHASE-1.md`, `PHASE-2.md`, `PHASE-3.md`
Consolidated report: `evals/runs/<group>/REPORT.md`
