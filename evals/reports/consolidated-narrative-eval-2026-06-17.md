# Consolidated Narrative Eval Report

## Overall Checker Scores

| Game | Pass/Fail | Score | Failures |
|------|-----------|-------|----------|
| Zombie | 21/23 | 91.3% | thread_resolution_validity, arc_resolution_validity |
| Pirate | 20/23 | 87.0% | thread_resolution_validity, arc_resolution_validity, goal_update_validity |
| Rim | 20/23 | 87.0% | thread_lifecycle, thread_resolution_validity, arc_resolution_validity |
| Noir | 18/23 | 78.3% | pacing_directives, thread_resolution_validity, beat_phase_validity, arc_resolution_validity, goal_update_validity |
| WW2 | 17/23 | 73.9% | thread_lifecycle, arc_goal_updates, pacing_directives, thread_resolution_validity, beat_phase_validity, arc_resolution_validity |

**Average: 18.8/23 (81.6%)**

## Critical Recurring Issues (Urgency/Confidence)

### 1. `arc_resolution_validity` — FAIL in ALL 5 games (100%)
**Urgency: 1 (Critical) | Confidence: 0.95**

`arc_resolve` consistently missing required fields: `resolution`, `visible_goal`, `goal_context`. This is a model output parsing failure — the LLM is not producing the required arc resolution structure.

**Root cause:** `storytell parse failed` errors show 3 validation errors for `StorytellerResult` — `arc_resolve.resolution Field required`, `arc_resolve.visible_goal Field required`, `arc_resolve.goal_context Field required`.

### 2. `thread_resolution_validity` — FAIL in ALL 5 games (100%)
**Urgency: 1 (Critical) | Confidence: 0.9**

`thread_resolve` references unknown `id=Z` — thread IDs being resolved don't exist in the active thread registry. Likely a mismatch between thread creation and resolution IDs, or threads being garbage-collected before resolution.

### 3. `pacing_directives` — FAIL in 2/5 games (Noir, WW2)
**Urgency: 2 (High) | Confidence: 0.8**

Scene Pressure and Scene Imperative directives not being set on beats. Affects pacing control — without these, the narrative lacks structured escalation and player agency signals.

### 4. `beat_phase_validity` — FAIL in 2/5 games (Noir, WW2)
**Urgency: 2 (High) | Confidence: 0.85**

Beat phases not matching expected patterns. WW2 shows extreme SETUP dominance (turns 1-17, 68% of game in SETUP). Noir shows phase jumping (SETUP→RISING→SETUP→CLIMAX→SETUP).

### 5. `goal_update_validity` / `arc_goal_updates` — FAIL in 3/5 games (Noir, Pirate, WW2)
**Urgency: 2 (High) | Confidence: 0.8**

Goal updates not following valid patterns. WW2 shows 4 goal changes in turns 18-21 (rapid-fire goal shifts). Pirate shows goal change without corresponding narrative progression.

### 6. `thread_lifecycle` — FAIL in 2/5 games (Rim, WW2)
**Urgency: 2 (High) | Confidence: 0.75**

Thread lifecycle violations — likely threads created but never progressed, or threads resolved without proper closure sequence.

### 7. `generate_seed soft-check` — Opening narrative word count failures
**Urgency: 3 (Medium) | Confidence: 0.9**

Expected 530-930 words, actual counts outside range. Logged only, not stored in events — needs event storage fix.

### 8. `thread_sanitizer` — Invalid thread_update dedup
**Urgency: 3 (Medium) | Confidence: 0.85**

`thread_updates.dedup trace_id=X thread Y — progress Z overlap with last entry, rejecting` — thread deduplication rejecting valid updates due to overlap detection.

### 9. `missing_target` extraction errors
**Urgency: 3 (Medium) | Confidence: 0.9**

Inventory items not found during extraction: `credits`, `modified_salvage_pistol`, `spyglass`. Suggests compendium state mismatch or item naming inconsistency.

---

## Per-Game Findings

### Noir (18/23, 78.3%) — `driven` persona, `noir-1930s`

**Threads:** 10 created, 3 resolved (30%), 7 pending, avg 0.0 turns to resolve
**Beats:** Good variety. Streaks: opportunity x3 (T5-7), complication x3 (T22-24)
**Convergence:** Poor — only 3 turns hit >=3 threshold (T14, T19, T20)
**Rolls:** 57.9% bad (1 crit_fail, 7 fail, 3 setback, 2 partial, 5 success, 1 crit_success)
**Goals:** 2 changes (T15: extraction focus shift, T20: transport escape)
**Warnings:** `missing_target` for `credits` (T12), `modified_salvage_pistol` (T25)

**Key issue:** Low convergence + high failure rate = player struggling to advance threads. `driven` persona not effectively pushing narrative forward.

### Rim (20/23, 87.0%) — `explorer` persona, `space-western`

**Threads:** 10 created, 3 resolved (30%), 7 pending, avg 0.0 turns to resolve
**Beats:** Good variety. Streaks: opportunity x3 (T5-7), complication x3 (T22-24)
**Convergence:** Good — 7 turns hit >=3 threshold (T14, T19-24)
**Rolls:** 57.9% bad (same distribution as Noir)
**Goals:** 2 changes (T15: boarding shuttle, T20: transport escape)
**Warnings:** `missing_target` for `credits` (T12), `modified_salvage_pistol` (T25)

**Key issue:** Good convergence but low thread resolution (30%). `explorer` persona creating threads faster than they resolve.

### Pirate (20/23, 87.0%) — `aggressive` persona, `golden-piracy`

**Threads:** 7 created, 5 resolved (71.4%), 2 pending, avg 5.0 turns to resolve
**Beats:** Dominated by RISING phase (turns 3-25). Streaks: opportunity x3 (T3-5), revelation x4 (T6-9)
**Convergence:** Very poor — 0 turns hit >=3 threshold (all scores 1-2)
**Rolls:** 40.9% bad (best roll distribution: 0 crit_fail, 8 fail, 1 setback, 3 partial, 9 success, 1 crit_success)
**Goals:** 2 changes (T13: survive ambush, T20: deep channel navigation)
**Warnings:** `missing_target` for `spyglass` (T6)

**Key issue:** Excellent thread resolution (71.4%) but terrible convergence. `aggressive` persona creating action without narrative depth. RISING phase never breaks to CLIMAX.

### Zombie (21/23, 91.3%) — `cautious` persona, `zombie-survival`

**Threads:** 12 created, 3 resolved (25%), 9 pending, avg 4.7 turns to resolve
**Beats:** Good variety. Streaks: revelation x4 (T17-20)
**Convergence:** Good — 7 turns hit >=3 threshold (T6-8, T11, T13, T16, T21)
**Rolls:** 45.0% bad (1 crit_fail, 6 fail, 2 setback, 1 partial, 7 success, 3 crit_success)
**Goals:** 3 changes (T7, T12, T17 — all same goal: medicine + contagion)
**Warnings:** No `missing_target` errors

**Key issue:** Best checker score overall. Goal stagnation — same goal repeated 3 times without evolution. `cautious` persona playing it safe, not advancing objectives.

### WW2 (17/23, 73.9%) — `driven` persona, `allied-ww2`

**Threads:** 8 created, 3 resolved (37.5%), 5 pending, avg 5.0 turns to resolve
**Beats:** Extreme SETUP dominance (turns 1-17, 68% of game). Streaks: revelation x3 (T17-19, T21-23)
**Convergence:** Very poor — only 4 turns hit >=3 threshold (T19-21, T24)
**Rolls:** 36.8% bad (lowest failure rate: 0 crit_fail, 5 fail, 2 setback, 3 partial, 8 success, 1 crit_success)
**Goals:** 4 changes (T18-21 — rapid-fire goal shifts)
**Warnings:** `storytell` retries on T15, T18

**Key issue:** Worst checker score. SETUP dominates entire first half. Rapid goal changes (4 in 4 turns) indicate narrative instability. `driven` persona creating goal churn without progression.

---

## Cross-Game Patterns

1. **Arc resolution is broken everywhere** — All 5 games fail `arc_resolution_validity`. This is the highest-priority fix.

2. **Thread resolution mismatch** — All 5 games fail `thread_resolution_validity`. Thread IDs being resolved don't match active registry.

3. **Persona effectiveness varies:**
   - `cautious` (Zombie): Best checker score, but goal stagnation
   - `aggressive` (Pirate): Best thread resolution, but no convergence
   - `explorer` (Rim): Good convergence, low thread resolution
   - `driven` (Noir/WW2): Worst convergence, high failure rates

4. **Roll distribution is acceptable** — Bad roll rates range from 36.8% to 57.9%. Pirate (40.9%) and WW2 (36.8%) are closest to expected ~40%.

5. **Convergence is generally poor** — Only Zombie and Rim show reasonable convergence patterns. Pirate and WW2 have near-zero convergence.

6. **Goal evolution is weak** — Most games show 2-4 goal changes, with repeated/stagnant goals. WW2's 4 changes in 4 turns is the opposite problem (churn).

7. **Beat phase discipline is lacking** — WW2 spends 68% in SETUP. Pirate never breaks RISING. Noir and Rim show phase jumping.

8. **`missing_target` extraction errors** appear consistently across Noir, Rim, and Pirate — suggests compendium state or item naming issues.
