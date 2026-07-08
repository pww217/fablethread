# Eval Report — Phase 2 (15-turn)

**Date:** 2026-07-07
**Git SHA:** cadbf0a4
**Branch:** main
**Runs:** 3 (noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist)
**Total turns:** 45

---

## Executive Summary

1. **Thread urgency decay not firing** — All 3 runs show threads stuck at `urgency=normal` for 8-30 turns. This is the most impactful finding; it means the urgency decay mechanic is broken, leaving stale threads visible in state.
2. **Convergence roll_starvation mismatch** — All 3 runs show `roll_starvation: stored=0, recomputed=1`. The convergence component is not being persisted correctly during initial computation.
3. **GM beat lifecycle** — noir-1930s showed a beat persisting unchanged across 3 turns (T6-T8), violating the 2-turn TTL.
4. **Location change emission mismatch** — space-western T12 emitted a location_change event but the state did not reflect the change.
5. **No critical/game-breaking bugs** — All checkers pass at 92-95%. The engine is stable.

---

## Checker Scores by Run

### noir-1930s:driven — 36/39 PASS (92.3%)

| Category | Pass | Total | Issues |
|----------|------|-------|--------|
| Beats | 1 | 2 | gm_beat_lifecycle |
| Goals | 2 | 2 | — |
| Other | 1 | 12 | thread_urgency_decay |
| Pacing | 8 | 9 | convergence_recompute |
| Ruling | 2 | 2 | — |
| State | 7 | 7 | — |
| Threads | 5 | 5 | — |

### space-western:speedrunner — 36/39 PASS (92.3%)

| Category | Pass | Total | Issues |
|----------|------|-------|--------|
| Beats | 2 | 2 | — |
| Goals | 2 | 2 | — |
| Other | 1 | 12 | thread_urgency_decay |
| Pacing | 8 | 9 | convergence_recompute |
| Ruling | 2 | 2 | — |
| State | 6 | 7 | location_change |
| Threads | 5 | 5 | — |

### golden-piracy:completionist — 37/39 PASS (94.9%)

| Category | Pass | Total | Issues |
|----------|------|-------|--------|
| Beats | 2 | 2 | — |
| Goals | 2 | 2 | — |
| Other | 1 | 12 | thread_urgency_decay |
| Pacing | 8 | 9 | convergence_recompute |
| Ruling | 2 | 2 | — |
| State | 7 | 7 | — |
| Threads | 5 | 5 | — |

### Aggregate: 109/117 PASS (93.2%)

---

## Issues by Rubric Area

### Thread Urgency Decay (all 3 runs)

Threads remain at `urgency=normal` for 8+ turns without being demoted to `background`. The urgency decay mechanic should automatically demote threads that haven't been updated within 8 turns.

**Affected threads across runs:**
- noir-1930s: `political_instability`, `unlikely_ally`, `judicial_rigging`
- space-western: `corporate_encroachment`, `rim_resistance`
- golden-piracy: `crew_mutiny`, `governor_secret`

### Convergence Recompute — roll_starvation (all 3 runs)

The `roll_starvation` convergence component is stored as 0 but recomputed as 1. This affects the convergence score accuracy. The stored components don't match the formula.

### GM Beat Lifecycle (noir-1930s)

Beat `pressure` with effect `[npcs: silas] [highlight: fear]` persisted unchanged across T6-T8. The beat TTL (2 turns) was not enforced.

### Location Change (space-western)

T12: `location_change` emitted but post-turn `location.id` unchanged. Extraction emitted a location change that was not applied to state.

---

## Changes Since Last Eval (SHA 6735834a)

- `cadbf0a4` fix: PacingContext.directive naming mismatch
- `3335f03a` I-29: Engine model and pipeline naming audit (#13)
- `a1d05285` thread-lifecycle: restructure Record vs Narrator prompt ownership
- `354d5d20` B-36: remove thread_creation_cooldown, fix type errors
- `deed99e4` fix: dead code in phase_transition_signals checker
- `14ab282e` B-37: persist beat_candidates at event top level
- `0d0187b2` fix: circular import and LLM client renaming
- `d00ea66d` eval: fresh cycle results

---

## Testing Items

No bugs with `status: testing` found in roadmap.

---

## Phase Gate

**No critical bugs.** All failures are intermediate severity. Thread urgency decay and convergence recompute are systematic issues that should be addressed before Phase 3.
