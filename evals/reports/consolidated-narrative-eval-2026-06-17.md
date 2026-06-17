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

## Prompt Fixes Applied (verified with Gemma4)

The following prompt fixes were applied and verified against the actual problematic turns using `ev.py prompt-eval call`:

### 1. Thread ID hallucination — Space Western T25 ✅ FIXED

**Root cause:** `ccya/prompts/sections/_arc.j2` showed completed thread summaries but NOT their IDs:
```
- Reach the departing transport ship before customs agents intercept [urgency:urgent] resolved turn 23
```
The LLM hallucinated IDs (`reach_departing_transport`, `coalition_guards_engagement`) from the summaries.

**Fix:** Added `{{ ct.id }}` to the completed threads listing:
```
- `shuttle_boarding_dash`: Reach the departing transport ship...
```

**Result:** LLM now resolves correct thread IDs (`docking_bay_standoff` from active threads) and no longer hallucinates IDs.

### 2. Scene Imperative beat constraint — Noir T8 & WW2 T9 ✅ FIXED

**Root cause:** Two issues conspired:
- The system prompt listed ALL 9 beat types including the forbidden ones (`pressure`, `complication`, `escalation`, `twist`), creating a "forbidden fruit" anchoring effect
- The constraint was early in the prompt, far from the output point

**Fixes:**
1. `storytell_system.j2`: Replaced full types list with "See `allowed_beat_types` in the user prompt". Removed the types table, directive override section (with its NEV

ER lists), and specific beat names from the roll band table. Replaced with general guidance referencing the user prompt's allowed list.
2. `storytell_user.j2`: Added a constraint line at the **very end** of the user prompt (after `END CURRENT TURN NARRATION`), putting it in the LLM's recent attention window at the point of output generation.

**Result:** Both Noir T8 (was `complication` → now `revelation`) and WW2 T9 (was `pressure` → now `revelation`) emit valid allowed beats.

### 3. Tooling fixes

- `prompt-eval call` now prints LLM output before running checks (was missing output display)
- `build_prompt_context` fixed to read `band` from `event.ruling.band`, `pending_beat`/`recent_beats` from previous turn's state_snapshot (pre-turn), and build NPC roster from compendium

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

1. **Two perfect games** (Golden Piracy, Zombie Survival) — all checkers pass.

2. **Scene Imperative ignored** (Noir, WW2) — **Fixed!** Post-narration constraint reminder resolves this.

3. **Thread ID hallucination** (Space Western) — **Fixed!** Completed thread IDs now shown.

4. **Persona effectiveness varies:**
   - `cautious` (Zombie): Best checker score, goal stagnation
   - `aggressive` (Pirate): Best thread resolution, no convergence
   - `explorer` (Space Western): Good convergence
   - `driven` (Noir/WW2): Worst convergence

5. **Roll distribution acceptable** — Bad rates: 36.8%–57.9%.

6. **Convergence generally poor** — Only Zombie and Space Western show reasonable patterns.

7. **Goal evolution weak** — Repeated/stagnant goals in most games. WW2's 4 changes in 4 turns is churn.

---

## Tooling Issues Found & Fixed

### Fixed in this session

| Issue | File | Fix |
|---|---|---|
| `prompt-eval call` didn't print LLM output | `ccya/ev/prompt_eval.py` | Added output printing before checks |
| `build_prompt_context` used post-turn state for pre-turn fields | `ccya/ev/prompt_eval.py` | Use previous turn's state_snapshot for `pending_beat`, `recent_beats` |
| `build_prompt_context` had `band=""` | `ccya/ev/prompt_eval.py` | Read `band` from `event.ruling.band` |
| `build_prompt_context` had empty NPC roster | `ccya/ev/prompt_eval.py` | Build from compendium with `_build_npc_roster()` |
| `build_prompt_context` had `curtain_call=""` | `ccya/ev/prompt_eval.py` | Compute from scene data like the engine |

### Remaining tooling limitations

- **No `--model` flag for `prompt-eval call`:** Model must be specified in the scenario YAML. No CLI override available.
- **`build_prompt_context` still has post-turn vs pre-turn drift:** `conditions` and `inventory` reflect post-storytell state (from `state_snapshot`). True pre-storytell state requires parsing the extraction output before storytell changes were applied.
- **NPC roster lacks personality archetype enrichment:** `_build_npc_roster()` in `prompt_eval.py` doesn't have access to the `PERSONALITY_ARCHETYPES` registry, so NPC personality labels/traits/speech hints are missing.
- **`rules_outcome` not stored in events:** The `rules_outcome` dict is empty `{}` in all events. `band` is only available in `event.ruling.band`.
- **Allowed beat types field stored in events but undocumented:** `event.allowed_beat_types` exists and is correct but is not part of any documented schema.

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
