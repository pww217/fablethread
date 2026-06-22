# Eval Report: allied-ww2 (20 turns)

**Run:** `1837_allied-ww2_custom_20t`
**Commit:** `47ff6261`
**Date:** 2026-06-21

## Summary

| Metric | Value |
|--------|-------|
| Checkers | 21/24 PASS (87.5%) |
| Average score | 0.88 |
| Failed | `gm_beat_lifecycle`, `npc_presence`, `ruling_reason_quality` |

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
| **npc_presence** | **0.0** | **FAIL** |
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

### gm_beat_lifecycle (12 failures)

Affected turns: T3, T4, T5, T7, T9, T10, T12, T13, T14, T17, T19, T20

Same root cause as noir-1930s: `prompt_context.py` hardcodes `rules_outcome: None`.

### npc_presence (12 failures)

Affected turns: T9-T20

`NPC 'soldier_in_field_jacket' has invalid presence 'archived'`

**Root cause:** `npc_presence.py:11` — `VALID_PRESENCE = {"present", "nearby", "known", "departed", None}` — does not include `"archived"`. The engine transitions departed NPCs to `archived` after `departed_archive_ttl` (default 3 turns, `turn_state.py:670`). This is a legal state but the checker doesn't recognize it.

### ruling_reason_quality (11 failures)

Affected turns: T3, T4, T5, T7, T9, T10, T12, T13, T14, T17, T19

Same root cause as noir-1930s: prompt doesn't require causal keywords.

## Observations

- **Arc resolve frequency:** arcs resolved in 2-4 turns (target 8-15) — no checker tracks this
- **Storytell parse failures:** uppercase thread types, invalid `gm_beat.driver` value `"environment"` (not in valid set)
- **Inventory canonical ID failures:** `garand_rounds`, `scr_58_field_telephone`, `m1_garand` not matching
- **Thread resolution references to unknown IDs** (`enemy_sighting_immediate`, `ridge_skirmish_escalation`, etc.)
- **Seed narrative length:** 409 words (expected 530-930)
- Storytell failed completely on turn 2 (no actions after retries)
