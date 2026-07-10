# Phase 2 Report — 15-turn runs

**Date:** 2026-07-07
**Git SHA:** cadbf0a4
**Runs:** noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist

---

## Summary

| Run | Pass Rate | Issues |
|-----|-----------|--------|
| noir-1930s:driven | 36/39 (92.3%) | gm_beat_lifecycle, thread_urgency_decay, convergence_recompute |
| space-western:speedrunner | 36/39 (92.3%) | location_change, thread_urgency_decay, convergence_recompute |
| golden-piracy:completionist | 37/39 (94.9%) | thread_urgency_decay, convergence_recompute |

**Overall: 109/117 checkers pass (93.2%). All failures are intermediate severity.**

---

## Issues by Category

### 1. Thread Urgency Decay — FAIL (all 3 runs)

**Severity:** Intermediate

Threads remain at `urgency=normal` for 8+ turns without being demoted to `background`. This is a systematic issue affecting all scenarios.

**Affected threads:**
- noir-1930s: `political_instability`, `unlikely_ally`, `judicial_rigging` (10-30 turns at normal)
- space-western: `corporate_encroachment`, `rim_resistance` (11-30 turns at normal)
- golden-piracy: `crew_mutiny`, `governor_secret` (10-30 turns at normal)

**Impact:** Long-running threads that are no longer actively pursued remain visible as "normal urgency" cluttering the thread state. The urgency decay mechanic is not firing.

### 2. Convergence Recompute — roll_starvation mismatch — FAIL (all 3 runs)

**Severity:** Intermediate

The `convergence_recompute` checker detects that `roll_starvation` is stored as 0 but recomputed as 1 across all turns. The stored convergence components don't match the recomputed formula.

**Pattern:** Every turn shows `roll_starvation: stored=0, recomputed=1` with expected vs actual diff of 1.00.

**Impact:** The convergence score computation is inconsistent between what's stored in events and what the formula recomputes. This suggests the `roll_starvation` component is not being persisted correctly during the initial computation.

### 3. GM Beat Lifecycle — FAIL (noir-1930s only)

**Severity:** Intermediate

A `pressure` beat with effect `[npcs: silas] [highlight: fear]` persisted unchanged across T6-T8 without being consumed or updated.

**Impact:** The beat TTL mechanism did not expire or consume this beat within the expected 2-turn window.

### 4. Location Change — FAIL (space-western only)

**Severity:** Intermediate

T12: `location_change` emitted but post-turn `location.id` unchanged (`unregistered_docking_ring`). The extraction emitted a location change event but the actual state did not reflect a new location.

**Impact:** Indicates a mismatch between extraction output and applied state — the engine may have rejected the location change or the extraction emitted it incorrectly.

---

## Changes Since Last Eval (SHA 6735834a)

- `cadbf0a4` fix: PacingContext.directive naming mismatch — pc.directives → pc.directive
- `3335f03a` I-29: Engine model and pipeline naming audit (#13)
- `a1d05285` thread-lifecycle: restructure Record vs Narrator prompt ownership
- `354d5d20` B-36: remove thread_creation_cooldown, fix turn.py/world.py/narrate.py type errors
- `deed99e4` fix(pacing_convergence): fix dead code in phase_transition_signals checker
- `14ab282e` B-37: persist beat_candidates at event top level
- `0d0187b2` fix: Resolve circular import and LLM client renaming + routes cleanup
- `d00ea66d` eval: fresh cycle results — checker fixes, engine findings, E-11 completion

Notable: The thread_urgency_decay failures are new (or at least more visible now) — the thread lifecycle prompt restructure and thread_creation_cooldown removal may have affected urgency decay behavior.

---

## Phase Gate Assessment

**No critical bugs found.** All failures are intermediate severity.

- Thread urgency decay needs investigation — likely related to the thread lifecycle prompt restructure (a1d05285) or thread_creation_cooldown removal (354d5d20)
- Convergence roll_starvation mismatch is systematic across all runs — needs formula/persistence audit
- GM beat lifecycle and location_change are isolated to single runs

**Recommendation:** Proceed to Phase 3 if thread urgency decay and convergence recompute are acceptable as known issues, or fix these two first before Phase 3.
