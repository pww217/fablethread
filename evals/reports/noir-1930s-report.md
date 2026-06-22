# Eval Report: noir-1930s (20 turns)

**Run:** `1822_noir-1930s_custom_20t`
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

### gm_beat_lifecycle (13 failures)

All rolled turns failed: `rolled=true but narrate user prompt did not include rules_outcome BINDING block`

Affected turns: T3, T4, T5, T6, T7, T9, T10, T11, T12, T13, T14, T19, T20

**Root cause:** `ccya/ev/prompt_context.py:228` hardcodes `rules_outcome: None` for the "narrate" stream. The checker re-renders `narrate_user.j2` and checks for the BINDING block, but since `rules_outcome` is always None, the block never renders. This is a checker bug, not an engine bug.

### ruling_reason_quality (13 failures)

All rolled turns failed: `ruling.reason lacks causal keyword (because/since/due to/as)`

Affected turns: T3, T4, T5, T6, T7, T9, T10, T11, T12, T13, T14, T19, T20

Example reasons:
- "Checking for detection after a suspicious glance is uncertain."
- "Moving while being watched is a high-stakes stealth attempt."
- "Combat initiation is a major narrative pivot with consequences."

**Root cause:** `ruling_system.j2` says `"Explains the difficulty or impossibility choice in 5-10 words"` but does not require causal keywords. The LLM produces descriptive (not causal) reasons. The checker requires `because/since/due to/as`.

## Observations

- **Storytell parse failures:** LLM returning uppercase thread types (`THREAT`, `REVELATION`) instead of lowercase. Retries succeed.
- **Thread resolution references to unknown IDs** (e.g., `dockside_extortion`, `alleyway_combat`)
- **Seed narrative length:** 430 words (expected 530-930)
- `archived` presence state used by engine but not in checker's VALID_PRESENCE set
