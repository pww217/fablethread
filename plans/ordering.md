# Plan Execution Order

Plans in `/plans/` should be executed in this order. Each plan's own document has been updated to mark superseded/abandoned steps to avoid duplicate work.

## Execution Order

| # | Plan | Depends On | Notes |
|---|---|---|---|
| 1 | `world-seed-char-creation.md` | none | Standalone. Fixes seed generation prompts. Run first because broken seeds corrupt every subsequent eval run. |
| 2 | `prompt-quality-remediation-20260512.md` | none | Standalone. Fixes prompt defects across rules, narrate, and extractors. Changes what extractors emit, which downstream plans depend on. |
| 3 | `mechanical_remediation_eval_run_20260512t154142z_uufm2ojg.md` | prompt-quality (for full effectiveness) | ✅ completed. Fixes engine-level mechanical failures. Primary implementation for momentum, quest terminal-state guard, and ghost NPC cycle detection. |
| 4 | `state-fidelity-remediation-20260512t154142z_uufm2ojg.md` | mechanical, prompt-quality | ✅ completed. Fixes state-level issues. Several steps are superseded by mechanical plan (see conflicts below). |
| 5 | `system-cohesion-remediation-20260512t154142z-uufm2ojg.md` | mechanical, state-fidelity | ✅ completed. Fixes integration-seam failures. Momentum phase is fully superseded by mechanical plan (see conflicts below). |
| 6 | `eval-harness-reviewed.md` | mechanical (for momentum telemetry in events.jsonl) | Fixes eval harness auto-checkers and judge trace. Runs last — validates all other plans' work. Two steps (4.2, 4.3) are self-cancelling (no change needed). |

## Conflicts & Superseded Steps

These were identified and resolved by updating the plan documents themselves. Each superseded step is marked `ABANDONED` or `SUPERSEDED` in the source plan.

### Factions/locations system template block (prompt-hygiene vs wire-scenario)
- **Prompt-hygiene plan** referenced removing a `{% if world_factions or world_locations %}` block from `narrate_system.j2` in Step 1.1 and Risk #1.
- **Wire-scenario plan** wires `world_factions`/`world_locations` through the turn pipeline to make the blocks functional.
- **Resolution:** The block does not exist in `narrate_system.j2` — it only exists in `narrate_user.j2`. Prompt-hygiene Step 1.1 is **SUPERSEDED** for the system template portion. Wire-scenario plan is the correct implementation. Prompt-hygiene's Risk #1 and Ambiguity #3 updated to reflect this.

### Momentum telemetry (Mechanical Phase 05 vs System Cohesion Phase 04)
- **Mechanical plan** adds `momentum_before`/`momentum_after`/`momentum_delta` to events.jsonl rules event and to `summarize_changes`/`format_change_lines`.
- **System cohesion plan** would add a top-level `event["momentum"]` block and momentum to `summarize_changes`.
- **Resolution:** System cohesion Phase 04 is **ABANDONED**. Execute mechanical plan's momentum phases (Steps 5.1 and 5.2) only. If additional momentum-band coherence checks are needed (e.g., `check_momentum_band_delta` in universal asserts), add them as a follow-up.

### Quest terminal-state guard (Mechanical Phase 03 vs State Fidelity Phase 02.2)
- **Mechanical plan** adds a terminal-state guard in `apply_delta`'s quest upsert loop: checks if quest already has `status == "completed"` or `"failed"` and skips the upsert with a structured log warning.
- **State fidelity plan** would add a similar guard at status-reassignment time.
- **Resolution:** State fidelity Step 2.2 is **ABANDONED**. Execute mechanical plan's Step 3.1 only. State fidelity's Step 2.1 (quest alias detection via title normalization) is independent and should still be executed.

### Pressure TTL (State Fidelity Phase 04.1 vs System Cohesion Phase 03)
- **State fidelity plan** analyzed pressure TTL logic in `pressure.py` and hypothesized the root cause (pressures with high `max_turns` or old `turn_added` may not expire).
- **System cohesion plan** has the implementation steps to audit and fix the write-back path.
- **Resolution:** State fidelity Step 4.1 is **ANALYSIS ONLY** — implementation deferred to system cohesion Phase 03. State fidelity's test `tests/test_pressure_ttl.py` is deferred to system cohesion's `tests/test_pressure.py`.

### Ghost NPCs (Mechanical Phase 02 vs State Fidelity Phase 03)
- **Mechanical plan** adds cycle detection in the extraction pipeline (`_check_npc_ghost_cycle`).
- **State fidelity plan** treats NPC removal as explicit-only in `apply_delta`, but notes "no code change needed" — the issue is in extraction, not state delta.
- **Resolution:** No conflict. Mechanical plan's extraction-level guard is the real fix. State fidelity's Phase 03 is verification/observability only.

### Momentum telemetry (Eval Harness Phase 03.2 vs Mechanical/System Cohesion)
- **Eval harness plan** originally referenced "system-cohesion Phase 04" for momentum telemetry source. System cohesion Phase 04 is ABANDONED.
- **Resolution:** Eval harness plan updated to reference "mechanical plan Phase 05" instead. The mechanical plan adds momentum to events.jsonl; the eval harness plan surfaces it in the judge trace metrics table. Complementary, not conflicting.

## What Changed

All plan documents have been updated to mark superseded steps:

- **`wire-scenario-factions-locations-to-narrator.md`**: Updated to reflect that factions/locations blocks only exist in `narrate_user.j2` (not `narrate_system.j2`). Added Step 1.4 to enhance location block with `type` field. Marked prompt-hygiene Step 1.1 as SUPERSEDED.
- **`prompt-hygiene-corrected.md`**: Step 1.1 marked SUPERSEDED by wire-scenario plan. Risk #1 and Ambiguity #3 updated to reflect that the `{% if world_factions or world_locations %}` block does not exist in `narrate_system.j2`.
- **`system-cohesion-remediation-20260512t154142z-uufm2ojg.md`**: Phase 04 (momentum) marked `SUPERSEDED` in phase guide and `ABANDONED` in implementation body. Ambiguity #3 crossed out and resolved by reference to mechanical plan.
- **`state-fidelity-remediation-20260512t154142z_uufm2ojg.md`**: Phase 02 step 02.2 (terminal-state guard) marked `ABANDONED` with reference to mechanical plan Phase 03 Step 3.1. Phase 04 step 04.1 (pressure TTL) marked `ANALYSIS ONLY` with implementation deferred to system-cohesion plan. Ambiguities #2 and #4 crossed out and resolved.
- **`eval-harness-reviewed.md`**: Rewritten with proper markdown formatting (was unformatted plain text). Phase 03 Step 3.2 updated to reference "mechanical plan Phase 05" instead of abandoned "system-cohesion Phase 04". Steps 4.2 and 4.3 marked `ABANDONED` (self-cancelling — no change needed).
