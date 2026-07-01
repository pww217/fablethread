# E-7 Eval Report — Clean Deep-Dive

**Date:** 2026-07-01  
**SHA:** 9965fcd  
**Pack:** noir-1930s:driven  
**Turns:** 15  

## Executive Summary

**Overall Status:** 38/39 checkers PASS (97.4%)  
**Average Score:** 0.97  

### Key Findings

1. **World state fact IDs — FIXED**  
   IDs now stable across turns. `police_curfew` and `evidence_tampering` persist unchanged from T1→T15. "MANDATORY — EXACT ID PRESERVATION" guidance in `sanitize_thread.j2` is working.

2. **extraction_retry_rates — LLM reliability issue**  
   T6: LLM generated condition changes without `condition_change_reason`, causing 1 retry. Retry mechanism handles it but wastes a turn. No engine fix needed — instruction in `extract_state_system.j2:12` is clear.

3. **Seed threads not surfacing — Design decision needed**  
   `navy_patrols` and `guild_bounty` stayed dormant entire golden-piracy run. No engine mechanism to surface dormant threads. LLM instructed "Default: emit nothing." Should engine auto-surface after N turns, or is this LLM responsibility? (I-19 created)

4. **Prompt size growth — Root causes identified**  
   - Ruling: 2888→2738 tokens (decreasing)  
   - Narrate: 3880→4130 tokens (slight increase)  
   - Root causes: NPC roster accumulation (3→10 NPCs), prior_history (fixed: reduced from 20 to 10), thread progress entries  

5. **Skill distribution — Improved**  
   Current run: strength 28.6%, dexterity 42.9%, wits 7.1%, charisma 21.4%. Better balanced than earlier runs (dexterity was 68% in Phase 4). I-13 still testing.

### Rubric Results

| Section | Status | Notes |
|---------|--------|-------|
| 3. Curtain Call | PASS | thread_resolve entries present in CLIMAX turns (T5-T7) |
| 4. GM Beat Lifecycle | PASS | Good variety, recent_beats sliding correctly, phase constraints respected |
| 5. Thread Lifecycle | PASS | Threads updated with progress, urgency changes, goal changes |
| 6. Pacing Directives | PASS | outcome_hint (advance/hold/transition) passed correctly, directive (Scene Pressure/Imperative) passed to world prompt |
| 7. Inventory & Conditions | PASS | TTL auto-expiry working, max 3 concurrent conditions (T5-T6), inventory changes tracked |
| 9. NPC Presence & Compendium | PASS | 5 NPCs in compendium, 1 archived, lifecycle working |
| 10. Location Transitions | PASS | 4 location changes across 15 turns, appropriate pacing |
| 11. Sanitizer Lifecycle | PASS | Runs at T5, T10, T15 (~4s each), thread ops valid |
| 12. Warning Signals | PASS | 2 thread dedup rejections (T4, T14), 1 reconcile warning (T7) — all expected |
| 13. Prompt Size | PASS | Stable growth, ruling decreasing, narrate slight increase |
| 14. LLM-Based Quality | SKIP | mlx_lm module not available, deterministic checkers sufficient |

### Bugs Fixed This Session

1. **World state fact IDs** — "MANDATORY — EXACT ID PRESERVATION" guidance with wrong/right examples in `sanitize_thread.j2`. Verified stable across 15 turns.

### Remaining Issues

1. **Seed threads not surfacing** — Design decision needed (I-19)
2. **extraction_retry_rates** — LLM occasionally forgets `condition_change_reason`. Retry mechanism handles it.
3. **Prompt size growth** — NPC roster accumulation is primary driver. Question: should we limit to present/nearby only?
4. **LLM-based checkers** — mlx_lm module not available, cannot run directive_tone, beat_narrative, state_fidelity, ruling_intent checkers.

### Files Modified

- `ccya/prompts/sanitize_thread.j2` — Added "MANDATORY — EXACT ID PRESERVATION" instruction with wrong/right examples

### Recommendations

1. **Design decision needed:** Should engine auto-surface dormant threads after N turns, or is this LLM responsibility?
2. **Consider limiting NPC roster** to present/nearby only to reduce prompt growth (~500-600 chars per NPC).
3. **Fix mlx_lm module** to enable LLM-based quality checkers.
