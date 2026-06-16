# Eval Report: Pirate (golden-piracy)
**Date:** 2026-06-16 | **Turns:** 20 | **Personality:** driven
**Save:** `saves/ev/20260616_020056_59afc7/`
**Checker pass rate:** 82.6% (19/23) — avg score 0.83

## Failures
- `arc_goal_updates`: FAIL
- `pacing_directives`: 6/7 FAIL
- `thread_resolution_validity`: FAIL
- `arc_resolution_validity`: FAIL

## Narrative Mechanics Assessment

### Scene/Location Imperatives — WORKING
Scene taglines show good social tension progression: `Cargo hold — slick floors, feverish sailors` → `Cargo Hold — tense standoff near hatchway` → `Cargo Hold — tense standoff, sickness spreading` → `Mid-deck — dim lantern light, searching for medicine` → `Cargo Hold — stagnant air, tense shadows` → `Cargo Hold — heavy tension, shared secrets` → `Mid-deck — blocked by crewmen` → `Mid-deck — standoff at the railing` → `Mid-deck — pinned against railing, surrounded`. Location transitions between cargo hold and mid-deck are logical.

### Social/Combat Mix — WORKING
This pack has the best social dynamics. The player navigates between persuasion, intimidation, and stealth — Silas Vane emerges as a compelling NPC antagonist. The progression from tension → intimidation → gold seizure → escape attempt → being surrounded feels narratively rich. Conditions track: `startled` → `focused` → `determined` → `watched` → `focused` → `exhausted` → `pinned` → `rattled`.

### Thread Management — BROKEN
`thread_updates.dedup` on `fever_escalation` (turn 2). `thread_resolutions` reference unknown ID `cargo_theft_tension` (T18).

### State Extraction — FIXED (2026-06-16)
`extraction.state.empty` on 9/20 turns (1,3,4,7,8,10,11,12,13).

Fix: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run on 2026-06-16 confirmed fix works.

### Storyteller/State Parse — BROKEN
Turn 12: `extract_state parse failed` x2 — `inventory_change_reason is required when inventory changes are present`. The LLM adds `stolen_manifest` to inventory but doesn't provide a `reason` field. `storytell parse failed` x2 — `arc_resolve.resolution`, `arc_resolve.visible_goal`, `arc_resolve.goal_context` all missing.

### Other Bugs
- `reconcile_delta duplicate condition add ignored: ['watched']` — condition `watched` attempted to be added twice in turn 16
- `generate_seed soft-check`: Opening narrative 519 words (expected 530-930) — just under minimum
- Many `skill: ?` in rulings
