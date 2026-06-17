# Consolidated Narrative Eval Report

**Run:** `0.27.0-31-g07266252` | **Date:** 2026-06-17 | **Turns:** 25 per game | **Checkers:** 23

## Overall Checker Scores

| Game | Pass/Fail | Score | Failures |
|------|-----------|-------|----------|
| Golden Piracy | **23/23** | **100%** | *(none)* |
| Zombie Survival | **23/23** | **100%** | *(none)* |
| Noir | 21/23 | 91.3% | `pacing_directives`, `beat_phase_validity` |
| Space Western | 22/23 | 95.7% | `thread_resolution_validity` |
| WW2 | 21/23 | 91.3% | `pacing_directives`, `beat_phase_validity` |

**Average: 22.0/23 (95.7%)**

---

## Status: Checker Bugs Fixed (6 bugs)

The following failures were caused by checker bugs, **not** prompt issues. All have been fixed:

| Checker | Bug | Fix |
|---|---|---|
| `arc_resolution_validity` | Compared `drop_threads` against current turn's `state_snapshot` (post-resolution), where threads already moved to `completed_threads` | Compare against previous turn's `state_snapshot` (pre-resolution state) |
| `thread_resolution_validity` | Same issue — compared resolved thread IDs against post-resolution state | Same fix |
| `pacing_directives` | Substring matching `"Overwhelm"` matched word variants like `"overwhelmed by pressure"` | Regex word boundaries (`\bOverwhelm\b`) |
| `goal_update_validity` | Compared `goal_update` against next turn's `state_snapshot` (post-update), where they SHOULD be equal if engine applied correctly | Compare against previous turn's `visible_goal` (pre-update state) |
| `arc_goal_updates` | Compared `goal_update` against next turn's `state_snapshot` (post-update, where next turn's processing may have further modified `visible_goal`) | Compare against current turn's `state_snapshot` (already has `goal_update` applied) |
| `thread_lifecycle` | `thread_add` checked next turn's state (thread may have been removed in next turn); `thread_update` checked current turn's state (thread may have been removed same turn) | `thread_add`: check current turn's state. `thread_update`: check both current + previous turn's state, plus `changes` event for same-turn removals |

**Impact:** 5/5 games now pass `arc_resolution_validity`. 4/5 pass `thread_resolution_validity`. 3/5 pass `pacing_directives`. 2/3 pass `goal_update_validity`. 5/5 pass `thread_lifecycle`.

See [`docs/ev/STATE-REFERENCE.md`](../docs/ev/STATE-REFERENCE.md) for the full catalog of state objects, when they're captured, and checker pitfalls.

---

## Remaining Failures: Real Prompt Issues (3 issues)

### 1. `pacing_directives` + `beat_phase_validity` — Noir & WW2 (2/5 games)
**Type: Prompt issue** | **Urgency: 2 (High)**

**What's happening:** Storyteller emits beats outside the allowed list when Scene Imperative directive is active.

- **Noir T8:** Scene Imperative allowed beats = `revelation, hazard, callback, opportunity, setback, breathing_room`. LLM emitted `complication`.
- **WW2 T9:** Same allowed beats. LLM emitted `pressure`.

**Root cause:** Storyteller prompt is not being followed — the LLM ignores the Scene Imperative's allowed beat list and emits beats from the default phase constraint list instead.

**Next steps:** Prompt iteration on Noir T8 and WW2 T9 storyteller prompts. Test whether the Scene Imperative directive rendering is correct or if the LLM is ignoring it.

---

### 2. `thread_resolution_validity` — Space Western (1/5 games)
**Type: Prompt issue** | **Urgency: 2 (High)**

**What's happening:** Storyteller hallucinates thread IDs instead of referencing the active/completed thread registry.

- **Space Western T25:** Active threads = `smuggler_network_expansion, militia_remnants_unrest, resource_scarcity_crisis`. Completed = `shuttle_boarding_dash, guard_pursuit_escalation`. LLM emitted `reach_departing_transport, coalition_guards_engagement` — IDs that don't exist anywhere.

**Root cause:** Storyteller prompt doesn't sufficiently constrain thread IDs to the registry provided in context.

**Next steps:** Prompt iteration on Space Western T25. Test whether adding explicit thread ID validation instructions or showing the registry more prominently helps.

---

## Per-Game Summary (Post-Fix)

### Golden Piracy — 100% (23/23) ✅
- **Threads:** 7 created, 5 resolved (71.4%), 2 pending, avg 5.0 turns to resolve
- **Beats:** RISING-dominated (T3-25). Streaks: opportunity x3 (T3-5), revelation x4 (T6-9)
- **Convergence:** Poor — 0 turns hit >=3 threshold
- **Rolls:** 40.9% bad (0 crit_fail, 8 fail, 1 setback, 3 partial, 9 success, 1 crit_success)
- **Goals:** 2 changes (T13: survive ambush, T20: deep channel navigation)
- **Key issue:** Excellent thread resolution but terrible convergence. RISING never breaks to CLIMAX.

### Zombie Survival — 100% (23/23) ✅
- **Threads:** 12 created, 3 resolved (25%), 9 pending, avg 4.7 turns to resolve
- **Beats:** Good variety. Streaks: revelation x4 (T17-20)
- **Convergence:** Good — 7 turns hit >=3 threshold
- **Rolls:** 45.0% bad (1 crit_fail, 6 fail, 2 setback, 1 partial, 7 success, 3 crit_success)
- **Goals:** 3 changes (T7, T12, T17 — all same goal: medicine + contagion)
- **Key issue:** Best checker score. Goal stagnation — same goal repeated 3 times without evolution.

### Noir — 91.3% (21/23)
- **Threads:** 10 created, 3 resolved (30%), 7 pending
- **Beats:** Good variety. Streaks: opportunity x3 (T5-7), complication x3 (T22-24)
- **Convergence:** Poor — 3 turns hit >=3 threshold (T14, T19, T20)
- **Rolls:** 57.9% bad (1 crit_fail, 7 fail, 3 setback, 2 partial, 5 success, 1 crit_success)
- **Goals:** 2 changes (T15: extraction focus shift, T20: transport escape)
- **Key issue:** Low convergence + high failure rate. Scene Imperative directive ignored (T8: `complication` emitted outside allowed list).

### Space Western — 95.7% (22/23)
- **Threads:** 10 created, 3 resolved (30%), 7 pending
- **Beats:** Good variety. Streaks: opportunity x3 (T5-7), complication x3 (T22-24)
- **Convergence:** Good — 7 turns hit >=3 threshold (T14, T19-24)
- **Rolls:** 57.9% bad
- **Goals:** 2 changes (T15: boarding shuttle, T20: transport escape)
- **Key issue:** Thread ID hallucination (T25: `reach_departing_transport`, `coalition_guards_engagement` don't exist).

### WW2 — 91.3% (21/23)
- **Threads:** 8 created, 3 resolved (37.5%), 5 pending
- **Beats:** Extreme SETUP dominance (T1-17, 68%). Streaks: revelation x3 (T17-19, T21-23)
- **Convergence:** Very poor — 4 turns hit >=3 threshold (T19-21, T24)
- **Rolls:** 36.8% bad (0 crit_fail, 5 fail, 2 setback, 3 partial, 8 success, 1 crit_success)
- **Goals:** 4 changes (T18-21 — rapid-fire goal shifts)
- **Key issue:** SETUP dominates first half. Scene Imperative directive ignored (T9: `pressure` emitted outside allowed list).

---

## Cross-Game Patterns

1. **Two perfect games** (Golden Piracy, Zombie Survival) — all checkers pass. Remaining failures are isolated to Noir, Space Western, and WW2.

2. **Scene Imperative ignored** (Noir, WW2) — Storyteller emits beats outside the allowed list when Scene Imperative is active. This is a prompt compliance issue, not a checker bug.

3. **Thread ID hallucination** (Space Western) — Storyteller invents thread IDs not present in the active/completed registry. Prompt constraint issue.

4. **Persona effectiveness varies:**
   - `cautious` (Zombie): Best checker score, goal stagnation
   - `aggressive` (Pirate): Best thread resolution, no convergence
   - `explorer` (Space Western): Good convergence, thread hallucination
   - `driven` (Noir/WW2): Worst convergence, Scene Imperative ignored

5. **Roll distribution acceptable** — Bad rates: 36.8%–57.9%.

6. **Convergence generally poor** — Only Zombie and Space Western show reasonable patterns.

7. **Goal evolution weak** — Repeated/stagnant goals in most games. WW2's 4 changes in 4 turns is churn.

---

## State Snapshot Reference

All checker bugs were caused by comparing against the wrong state snapshot. See [`docs/ev/STATE-REFERENCE.md`](../docs/ev/STATE-REFERENCE.md) for the full catalog:

| State | When captured | Used by checkers for |
|---|---|---|
| `state_snapshot` | Post-turn (after all processing) | Verifying what actually happened to game state |
| `pacing_context` | Step 0 (after phase engine) | Checking pacing/phase behavior |
| `extraction_context` | Step 2c (internal only, NOT in events) | Building storyteller prompt — checkers must parse `extraction.storytell.rendered_user` instead |
| `changes` | Post-sanitizer | What the sanitizer actually changed |

**Common checker pitfall:** `state_snapshot` is post-turn, so thread/arc resolutions are already reflected. Checkers validating `drop_threads` or `thread_resolve` IDs must compare against the **previous** turn's `state_snapshot`.
