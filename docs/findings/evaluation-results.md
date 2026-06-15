# Evaluation Results: Storytelling Mechanics Across Personas & Scenarios

**Date:** 2026-06-15
**Runs:** 3 × 20 turns (zombie-survival/explorer, space-western/driven, sengoku-japan/aggressive)
**Flags:** `--no-sanitize`

---

## Executive Summary

All three runs exhibit systemic issues with pacing directive stripping, thread resolution bugs, and beat repetition risk. The `driven` persona (space-western) produced the cleanest run with only one checker failure. The `explorer` and `aggressive` personas showed more severe issues with phase transitions and beat patterns.

No doom spirals were detected in any run, despite several runs showing conditions that should have triggered them (consecutive pressure beats, rising tension, thread stagnation).

---

## Checker Results Comparison

| Checker | Run 1 (zombie/explorer) | Run 2 (western/driven) | Run 3 (sengoku/aggressive) |
|---|---|---|---|
| `phase_transitions` | PASS | PASS | PASS |
| `crisis_counting` | PASS | PASS | PASS |
| `crisis_breather_max` | PASS | PASS | PASS |
| `crisis_breather_count` | PASS | PASS | PASS |
| `crisis_breather_types` | **FAIL** | PASS | **FAIL** |
| `pacing_directives` | **FAIL** | **FAIL** | **FAIL** |
| `sanitizer_lifecycle` | PASS | PASS | PASS |
| `beat_lifecycle` | PASS | PASS | PASS |
| `beat_phase_alignment` | PASS | PASS | PASS |
| `beat_streaks` | PASS | PASS | PASS |
| `beat_surface_validity` | PASS | PASS | PASS |
| `beat_tension_alignment` | PASS | PASS | PASS |
| `tension_monotonicity` | PASS | PASS | **FAIL** |
| `roll_consistency` | PASS | PASS | PASS |
| `inventory_integrity` | PASS | PASS | PASS |
| `conditions_lifecycle` | PASS | PASS | PASS |
| `npc_presence` | PASS | PASS | PASS |
| `location_change` | PASS | PASS | PASS |
| `arc_resolve_validity` | **FAIL** | PASS | PASS |
| `thread_lifecycle` | **FAIL** | PASS | PASS |
| `thread_resolution_validity` | **FAIL** | PASS | PASS |
| `spiral_detected` | PASS | PASS | PASS |
| `compat` | PASS | PASS | PASS |
| `state_fidelity` | PASS | PASS | PASS |
| `directive_tone_match` | PASS | PASS | PASS |

**Total failures:** Run 1: 6 | Run 2: 1 | Run 3: 2

---

## Pacing Phase Behavior

### Run 1 (zombie-survival / explorer)
**Phase sequence:** OPENING → CRISIS (turns 2-15) → RESOLUTION (turns 16-20)

- CRISIS lasted 14 turns (turns 2-15), which is long but not unusual
- Phase transition at turn 16 was clean (crisis_breather_count reached)
- **Issue:** `breathing_room` beat appeared in CRISIS at turn 15 (not allowed types: `['pressure', 'escalation', 'complication']`)
- **Issue:** Overwhelm directive stripped from turns 12-13 (storytell/narrate)

### Run 2 (space-western / driven)
**Phase sequence:** OPENING → CRISIS (turns 2-20)

- CRISIS lasted all 19 turns — no phase transition occurred
- No `breathing_room` beats in CRISIS (clean)
- **Issue:** Overwhelm directive stripped from turns 2-13 (storytell/narrate) — 12 consecutive turns of stripped directives

### Run 3 (sengoku-japan / aggressive)
**Phase sequence:** OPENING → CRISIS (turns 2-20)

- CRISIS lasted all 19 turns — no phase transition occurred
- **Issue:** `breathing_room` beat appeared in CRISIS (not allowed types)
- **Issue:** Overwhelm directive stripped from turns 2-13 (storytell/narrate) — 12 consecutive turns of stripped directives
- **Issue:** `tension_monotonicity` failed at turn 8 (BREATHER with `escalates` delta)

### Pattern: Overwhelm Directive Stripping
All three runs show systematic stripping of the `Overwhelm` directive from both `storytell` and `narrate` outputs. This is not a persona-specific issue — it occurs across all three packs and personalities. The stripping happens during sanitization, which was disabled with `--no-sanitize`, suggesting the stripping occurs earlier in the pipeline (likely in the narrate/scene extraction phase).

---

## Doom Spiral Analysis

### Definition
A doom spiral occurs when consecutive pressure/escalation beats compound tension without resolution, creating a narrative feedback loop that becomes impossible to escape.

### Findings
**No doom spirals were detected in any run.** The `spiral_detected` field in `pacing_context` was `false` for all turns across all three runs.

### Conditions That Should Have Triggered Spirals

**Run 1:**
- Turns 5-8: `revelation` x4 streak (should increase spiral risk)
- Turns 12-13: Overwhelm stripped, tension rising
- Thread `supply_line_sabotage` unresolved through turn 10

**Run 2:**
- Turns 15-17: `complication` x3 streak
- 12 consecutive turns of stripped Overwhelm directives
- No phase transition (CRISIS maintained throughout)

**Run 3:**
- Turns 14-19: `revelation` x6 streak (severe repetition risk)
- Turns 2-13: Overwhelm stripped
- Turn 8: BREATHER with `escalates` delta (contradictory)

### Why Spirals Were Missed
The `spiral_detected` flag appears to be set internally by the engine but not exposed to EV commands. There's no `ev.py spiral-risk` command to independently analyze spiral conditions (consecutive pressure beats, rising tension, thread stagnation). The binary flag may use thresholds that these runs don't meet, or the detection logic may have gaps.

---

## Beat Repetition Patterns

### Run 1: `revelation` x4 (turns 5-8)
- Four consecutive `revelation` beats in CRISIS phase
- Surface: `storytell` for all four
- This creates a "info dump" pattern where the narrative becomes exposition-heavy
- Risk: Player fatigue from repeated revelation without resolution

### Run 2: `complication` x3 (turns 15-17)
- Three consecutive `complication` beats
- Surface: `storytell` for all three
- Less severe than Run 1's streak (shorter, later in session)
- Risk: Escalation fatigue if complications don't lead to resolution

### Run 3: `revelation` x6 (turns 14-19)
- **Six consecutive `revelation` beats** — the most severe repetition across all runs
- Surface: `storytell` for all six
- This is a critical narrative failure: the story becomes a series of reveals with no action, pressure, or resolution
- Risk: Complete loss of player engagement; the narrative becomes a lecture

### Beat Type Distribution Across Runs

| Beat Type | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `revelation` | 4 (streak) | 2 | 6 (streak) |
| `complication` | 2 | 3 (streak) | 1 |
| `breathing_room` | 2 | 1 | 1 |
| `pressure` | 3 | 2 | 2 |
| `escalation` | 2 | 1 | 1 |
| `action` | 4 | 5 | 4 |
| `consequence` | 2 | 3 | 2 |
| `setup` | 1 | 1 | 1 |

**Observation:** `revelation` and `action` are the most common beats across all runs. `breathing_room` appears infrequently and often in inappropriate phases (CRISIS).

---

## Thread Lifecycle Issues

### Run 1: Critical Thread Resolution Bugs

**`thread_lifecycle: FAIL`** — Turn 16 references unknown thread `council_detention`
- The storytell output at turn 16 contains `thread_updates` referencing `council_detention`
- This thread was never created in any previous turn's extraction
- The thread appears to be hallucinated or pulled from a different narrative context

**`thread_resolution_validity: FAIL`** — Turn 10 resolves unknown thread `supply_line_sabotage`
- The storytell output at turn 10 contains `thread_updates` with `kind: resolve` for `supply_line_sabotage`
- This thread was never created in any previous turn's extraction
- Same pattern as `council_detention`: thread resolution without prior thread creation

**Root Cause:** The storyteller is resolving threads that don't exist in the active thread pool. This suggests:
1. The storyteller prompt includes thread context that the extractor doesn't capture
2. The storyteller is hallucinating thread IDs from training data or narrative templates
3. There's a mismatch between what the storyteller sees and what the extractor records

### Run 2 & 3: Clean Thread Lifecycle
Both runs passed all thread-related checkers. Threads were created, progressed, and resolved in proper sequence. This suggests the issue is persona/pack-specific, not systemic.

---

## Arc Resolution Issues

### Run 1: `arc_resolution_validity: FAIL`
- Same turn 10 issue as `thread_resolution_validity`
- The storyteller resolved `supply_line_sabotage` which was never created
- This creates an arc resolution with no corresponding arc, breaking the narrative contract

### Runs 2 & 3: Clean Arc Resolution
Both runs passed `arc_resolve_validity`. Arcs were created and resolved in proper sequence.

---

## Tension Monotonicity

### Run 3: `tension_monotonicity: FAIL` — Turn 8
- Turn 8 is a `BREATHER` beat (should decrease or maintain tension)
- The `tension_delta` is `escalates` (should be `deescalates` or `stable` for BREATHER)
- This is a contradiction: the beat type says "breather" but the tension trajectory says "escalate"
- Likely causes:
  1. The storyteller is misclassifying the beat type
  2. The tension calculation is not accounting for the beat type
  3. There's a mismatch between the pacing context and the actual tension roll

---

## Extraction Format Issues

### `changes` vs `extraction_context`
All three runs use `.extraction.changes` only, not `.extraction_context`. The `compat` command shows:
- Run 1: "Uses neither: 26/28"
- Run 2: "Uses neither: 28/28"
- Run 3: "Uses neither: 27/28"

This means the `changes` field is not recognized as a valid extraction format by the compat checker. Yet checkers like `inventory_integrity`, `conditions_lifecycle`, and `npc_presence` report PASS — they're reading from `.applied` and `.state_snapshot` instead of `extraction_context`.

### Silent Fallback
The checkers silently fall back to reading from `.applied` and `.state_snapshot` when `extraction_context` is empty. This masks the format mismatch and gives false confidence that extraction is working correctly.

---

## Goals Command Gap

**All runs:** `ev.py goals` returned `(no goal changes found)`

However, `arc_resolve.visible_goal` clearly changed in storytell output:
- Run 1 turn 10: `"visible_goal": "Secure the primary medical transport route through the South Charles pass."`

The `goals` command reads from `extraction.storytell.output.goal_update` specifically, not from `arc_resolve.visible_goal`. When the storyteller emits an arc_resolve with a new visible_goal but no separate goal_update string, the goals command misses it entirely.

---

## Timing Performance

### Run 1 (zombie-survival / explorer)
- Average turn time: ~27 seconds
- Fastest: Turn 1 (16.2s)
- Slowest: Turn 20 (34.1s)
- Scene extraction: 7-12s per turn
- State extraction: 1.8-2.1s per turn
- Storytell: 5.5-6.5s per turn

### Run 2 (space-western / driven)
- Average turn time: ~28 seconds
- Fastest: Turn 1 (14.5s)
- Slowest: Turn 20 (38.2s)
- Scene extraction: 7-13s per turn
- State extraction: 1.8-2.1s per turn
- Storytell: 5.7-6.8s per turn

### Run 3 (sengoku-japan / aggressive)
- Average turn time: ~52 seconds (significantly slower)
- Fastest: Turn 1 (14.5s)
- Slowest: Turn 20 (109.4s)
- Scene extraction: 7-30s per turn (massive growth)
- State extraction: 1.8-2.1s per turn (consistent)
- Storytell: 5.7-11.4s per turn (growing)

**Critical finding:** Run 3 shows severe performance degradation from turn 17 onward (70-109s per turn). Scene extraction took 20-30 seconds per turn, suggesting context bloat is causing the LLM to process increasingly large prompts.

---

## Narrate Word Count Issues

All three first-turn narrations were far below the 530-930 word target:
- Run 1: 194 words (63% below minimum)
- Run 2: 167 words (68% below minimum)
- Run 3: 172 words (67% below minimum)

The `generate_seed soft-check: Opening narrative <450> words` warning appears in raw output but is not captured in any structured field. This is a systemic issue with the narrate prompt or the LLM's adherence to word count constraints.

---

## Condition Distribution Analysis

All three runs show the same pattern: conditions are overwhelmingly negative and accumulate over time.

| Metric | Run 1 (zombie) | Run 2 (western) | Run 3 (sengoku) |
|---|---|---|---|
| Conditions added | 12 | 14 | 12 |
| Conditions removed | 8 | 4 | 6 |
| Net accumulation | +4 | +10 | +6 |
| Active per turn (avg) | 0.8 | 0.9 | 0.8 |
| Distinct negative types | 7 | 11 | 7 |
| Distinct positive types | 1 (chemically_stimulated) | 0 | 0 |

**Negative:Positive ratio: 18:1** across all runs.

**Impact on difficulty:** 64% of all roll reasons (36/56) explicitly cite a condition as justification for hard difficulty. With 55% of rolls at hard (mod=-1), the effective distribution is meaningfully left-shifted. This is a primary driver of the failure feedback loop: fail → gain condition → harder next roll → more failures.

**Fix applied:** Band rebalancing in `rules.py` shifts partial threshold from ≤8 to ≤7, compensating for the conditions bias. See `docs/design/convergence-scoring-design.md` (Supporting Changes section).

---

## State Extraction Empty Warnings

All three runs show `extraction.state.empty` warnings:
- "state has no inventory or condition changes after retries"

This appears on multiple turns across all runs. The state extractor is failing to find changes, which means:
1. The inventory/conditions are not changing (stale state)
2. The extraction prompt is not effectively querying for changes
3. The retry logic is not improving extraction quality

---

## Thread Dedup Rejections

All three runs show `thread_updates.dedup` warnings:
- "thread <id> — progress <X.XX> overlap with last entry, rejecting"

This indicates the LLM is producing tiny progress increments (0.50, 0.53, 0.56) that are too close to previous entries. The dedup logic rejects these, which means thread progress is not advancing as intended.

---

## Recommendations

### High Priority (Decided — see convergence-scoring-design.md)
1. **Fix `tension_monotonicity`** — `tension_delta` removed from phase logic in convergence design. Ruling prompt change (Supporting Change A) also provides a fix.
2. **Fix `breathing_room` in CRISIS** — Scene Imperative allowed list updated in convergence design to restrict beat types by phase.
3. **Fix band rebalancing** — One-line `rules.py` change (partial ≤8 → ≤7) compensates for conditions bias. DECIDED.
4. **Fix roll frequency** — Ruling prompt criteria tightened + thread context added. DECIDED.
5. **Fix positive condition extraction** — State extractor prompt updated with success-guarded positive heuristics. DECIDED.

### Medium Priority (Deferred)
6. **Fix thread resolution bugs** — Storyteller resolving threads that don't exist. Needs separate investigation.
7. **Add doom spiral detection** — Implement `ev.py spiral-risk` command.
8. **Add warning summary command** — Surface soft-check, dedup, and extraction warnings.

### Low Priority (Deferred)
9. **Reduce context bloat** — Implement prompt truncation or summarization for storytell prompts.
10. **Fix thread dedup** — Improve thread progress granularity to avoid tiny increments.
11. **Fix extraction format** — Standardize on `extraction_context` or update compat checker to recognize `changes`.
12. **Fix `goals` command** — Read from `arc_resolve.visible_goal` in addition to `goal_update`.

---

## Persona-Specific Observations

### Explorer (zombie-survival)
- Most checker failures (6 total)
- Thread resolution bugs (unknown threads)
- `revelation` x4 streak (turns 5-8)
- `breathing_room` in CRISIS (turn 15)
- Clean phase transitions despite issues

### Driven (space-western)
- Cleanest run (1 failure only)
- No thread resolution bugs
- No `breathing_room` in CRISIS
- No tension monotonicity failures
- Overwhelm stripping still present (turns 2-13)
- `complication` x3 streak (turns 15-17) — minor issue

### Aggressive (sengoku-japan)
- Moderate failures (2 total)
- `revelation` x6 streak (turns 14-19) — severe repetition risk
- `tension_monotonicity` failure (turn 8)
- Severe performance degradation (turns 17-20: 70-109s)
- Overwhelm stripping present (turns 2-13)

**Conclusion:** The `driven` persona produces the most narratively coherent output with the fewest mechanical issues. The `explorer` persona has the most thread resolution bugs. The `aggressive` persona has the most severe beat repetition risk and performance issues.
