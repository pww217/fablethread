# Phase 1: noir-1930s:driven, 5 turns

**Date:** 2026-07-07
**Group:** `evals/runs/2026-07-07_0.31.0-54-g2bc68d2f_2bc68d2f/1534_noir-1930s_5t`
**Purpose:** Verify post-refactor engine stability — critical/game-breaking bugs

## Changes Since Last Eval (SHA 6735834a)

11 commits on main:
- `I-29: Engine model and pipeline naming audit (#13)` — core refactoring renames
- `Merge main: resolve conflicts from incoming updates` — merge conflict resolution
- `thread-lifecycle: restructure Record vs Narrator prompt ownership`
- `B-36: remove thread_creation_cooldown, fix turn.py/world.py/narrate.py type errors`
- `fix(pacing_convergence): fix dead code in phase_transition_signals checker`
- `B-37: persist beat_candidates at event top level`
- `fix: Resolve circular import and LLM client renaming + routes cleanup`
- `eval: fresh cycle results`

## Issues Found

### CRITICAL: `PacingContext.directive` vs `PacingContext.directives` mismatch

**Severity:** CRITICAL — every turn crashed during `_persist_and_async_cleanup`

**Symptom:** `AttributeError: 'PacingContext' object has no attribute 'directives'`

**Root cause:** Phase 5 rename changed `PC.directive` → `PC.directives` (Player Character model) but missed `PacingContext.directive` (separate dataclass in `turn_context.py`). The code in `turn.py:634,649` referenced `pc.directives` on the `PacingContext` object.

**Fix:** Changed `pc.directives` → `pc.directive` in `turn.py:634,649` to match the actual `PacingContext.directive` field name.

### MINOR: `prepare_seed` / `narrate_seed` first-attempt failures

**Severity:** LOW — auto-retries succeeded

**Symptom:** First attempt at `prepare_seed` returned "No JSON found"; first attempt at `narrate_seed` also failed. Second attempts succeeded.

**Impact:** Adds ~25s delay to seed phase. May indicate prompt/LLM instability during seed generation.

### MINOR: Pydantic serialization warning

**Severity:** LOW — non-fatal

**Symptom:** `PydanticSerializationUnexpectedValue(Expected enum - serialized value may not be as expected [field_name='presence', input_value='present', input_type=str])`

**Impact:** The `presence` field expects an enum but receives a string. May cause downstream issues if enum validation is strict.

### MINOR: `convergence_recompute` checker mismatches

**Severity:** LOW — minor consistency issue

**Symptom:** At turns 4, 8, 10: `roll_starvation: stored=0, recomputed=1` and `expected 2, got 1`

**Impact:** Stored convergence components don't match recomputed values. Game still functions correctly.

## Checker Summary

| Rubric | Issues |
|--------|--------|
| Ruling | All PASS |
| Narration | All SKIP |
| Pacing | All PASS except `convergence_recompute` (6 minor warnings) |
| State | All PASS |
| Threads | All PASS |
| Arcs | All PASS |
| NPCs | All PASS |
| GM Beats | All PASS |
| Rolls | All PASS |

**Overall pass rate: 97.4%**

## Verdict

**Phase 1 PASS.** The critical bug was caused by the I-29 refactoring (PacingContext.directive naming mismatch). All other issues are minor. Engine is stable. Proceed to Phase 2.
