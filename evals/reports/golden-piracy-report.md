# Eval Report: golden-piracy (20 turns)

**Run:** `1850_golden-piracy_custom_20t`
**Commit:** `47ff6261`
**Date:** 2026-06-21

## Summary

| Metric | Value |
|--------|-------|
| Checkers | 22/24 PASS (91.7%) |
| Average score | 0.92 |
| Failed | `gm_beat_lifecycle`, `ruling_reason_quality` |

## Per-Checker Results

| Checker | Score | Result |
|---------|-------|--------|
| arc_goal_updates | 1.0 | PASS |
| arc_resolution_validity | 1.0 | PASS |
| beat_phase_validity | 1.0 | PASS |
| breather_enforcement | 1.0 | PASS |
| climax_turn_counting | 1.0 | PASS |
| compendium_lifecycle | 1.0 | PASS |
| conditions_lifecycle | 1.0 | PASS |
| convergence_components | 1.0 | PASS |
| **gm_beat_lifecycle** | **0.0** | **FAIL** |
| goal_update_validity | 1.0 | PASS |
| inventory_integrity | 1.0 | PASS |
| location_change | 1.0 | PASS |
| location_description_consistency | 1.0 | PASS |
| new_thread_validity | 1.0 | PASS |
| npc_presence | 1.0 | PASS |
| pacing_directives | 1.0 | PASS |
| phase_transition | 1.0 | PASS |
| roll_band_consistency | 1.0 | PASS |
| ruling_band_distribution | 1.0 | PASS |
| **ruling_reason_quality** | **0.0** | **FAIL** |
| sanitizer_lifecycle | 1.0 | PASS |
| thread_lifecycle | 1.0 | PASS |
| thread_resolution_validity | 1.0 | PASS |
| world_state_facts | 1.0 | PASS |

## Failure Details

### gm_beat_lifecycle (16 failures)

Affected turns: T1, T2, T3, T4, T6, T7, T8, T9, T10, T11, T14, T15, T16, T17, T18, T19

Same root cause as other runs: `prompt_context.py` hardcodes `rules_outcome: None`.

### ruling_reason_quality (16 failures)

Affected turns: T1, T2, T3, T4, T6, T7, T8, T9, T10, T11, T14, T15, T16, T17, T18, T19

Same root cause as other runs: prompt doesn't require causal keywords.

## Observations

- **Storytell parse failures:** uppercase thread types, invalid `gm_beat.driver` value `"environment"`
- **Thread sanitizer** skipping invalid thread additions/updates (`naval_confrontation`, `elias_thorne_observation`)
- **Thread resolution references to unknown IDs** (`naval_blockade`)
- **Inventory canonical ID failures:** `pistol` not matching
- **Seed narrative length:** 396 words (expected 530-930)
- Player lost flintlock pistol (turn 3) then attempted to draw it again (turn 5) — inventory consistency was maintained by engine
