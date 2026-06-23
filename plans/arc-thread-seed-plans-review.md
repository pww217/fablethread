# Review: Primitives Clearing Plan

## Summary

This plan aims to delete removed fields (`goal_context`, `chapter_end`, `drop_threads`, `new_threads`, `turns_since` guard, `promote_to_world_state`) from all callsites. The pure-deletion portions (Phases 01-05) are sound and validated against source. However, Phases 06-09 violate the stated Non-goals by adding field renames and new fields. Two of the target field names (`long_term_objective`, `arc_origin`) don't exist in the codebase yet, so executing those phases blindly would break the build.

**Verdict: request changes** — strip Phases 06-09 into a separate plan or remove them entirely; fix Phase 02 to include `extraction.py:237`; remove the `pc_situation_schema` step from Phase 09.

---

## Fixes applied

None. All issues below require a design decision (strip or retarget) that I cannot make unilaterally.

---

## Findings requiring user input

### Blocks execution

- **[blocks-execution]** Phase 06 (ev checkers/tools), Phase 07 (server/engine), Phase 08 (templates) — all rename `visible_goal` → `long_term_objective` and `goal_context` → `arc_origin`. But `long_term_objective` and `arc_origin` **do not exist in the codebase** (grep returns zero matches for both). The plan's Non-goals explicitly say "Field renames (Phase 02 of master plan)" — these phases ARE field renames, violating the stated scope. **Removing them** (deferring renames to a separate pass) or **retargeting to rename `visible_goal` → `long_term_objective`** (accepting scope expansion) is the required decision.

- **[blocks-execution]** Phase 01 step `turn_state.py:534-541` says "update goal_update path (renamed in Phase 02)" — this is a rename (`visible_goal` → `long_term_objective`), not a deletion. Same issue: `long_term_objective` doesn't exist yet.

- **[blocks-execution]** Phase 01 steps `generate_seed_system.j2:37,64`, `_state_left.html:64,109`, `_save_picker.html:29` all say "update to `arc_origin`" — these are renames of `goal_context` → `arc_origin`, which doesn't exist yet. Out of scope per Non-goals.

- **[blocks-execution]** Phase 02: `chapter_end: bool = False` is defined on `StorytellerResult` at `ccya/models/extraction.py:237`, **not** on `CampaignArc` in `state.py`. The plan doesn't list `extraction.py` anywhere. Missing this file means the field stays in the model and the grep validation passes but the model still carries it.

- **[blocks-execution]** Phase 09: `golden-piracy` pack step says "add `pc_situation_schema`". `pc_situation_schema` **does not exist in the codebase** (grep returns zero matches in `ccya/` source files). This is a new field addition, violating Non-goals ("New field additions (Phase 03 of master plan)").

### Execution hazards

- **[execution-hazard]** Phase 08 references "TTL filtering (Phase 04)" at `_arc.j2:18-24` and `_arc.j2:21`. Phase 04 in THIS plan is the `turns_since` warning guard deletion. TTL filtering belongs to the master plan's Phase 04. Executor will look for TTL logic that doesn't exist yet.

- **[execution-hazard]** Phase numbering confusion: Phase 01 step notes say "(renamed in Phase 02)" but this plan's Phase 02 is `chapter_end` deletion. Phase 08 says "(Phase 04)" for TTL filtering but this plan's Phase 04 is `turns_since` guard. These refer to master plan phase numbers, creating ambiguity about what's in scope for this execution.

- **[execution-hazard]** Phase 02: `ccya/pack.py` doesn't have a `chapter_end` field (confirmed by reading `ScenarioBrief` at `pack.py:130-157`). The "if present" hedge on the `state.py` step is technically accurate but the actual location (`extraction.py:237`) is never mentioned.

### Maintainability

- **[maintainability]** Phase 01 step for `turn_state.py:534-541` — this section sets `state["arc"]["visible_goal"]` from `storyteller_result.goal_update`. The plan labels this as a deletion-related change, but no `goal_context` reference exists on those lines. The step is really a rename prep disguised as a cleanup, which is confusing.

- **[maintainability]** Validation greps for phases 06-08 check for `long_term_objective` but that field doesn't exist yet. The validation will pass vacuously (zero matches for `visible_goal` means the rename wasn't done, but also zero matches for `long_term_objective` means nothing was renamed TO it).

---

## Contract checks

- [PASS] Signature of `CampaignArc` field `goal_context: str = ""` at `state.py:81` — matches plan's Phase 01 claim.
- [PASS] `ArcResolution.goal_context: str` at `state.py:186` — matches plan.
- [PASS] `turn_state.py:249` `"goal_context": resolution.goal_context` — matches.
- [PASS] `turn_state.py:266` `goal_context=resolution.goal_context` — matches.
- [PASS] `thread_sanitizer.py:143,150` `goal_context` in `_build_messages` — matches.
- [PASS] `thread_sanitizer.py:219-222` `goal_context` in `_validate_parsed` — matches.
- [PASS] `thread_sanitizer.py:340-345` `goal_context` in `_apply_sanitization` — matches.
- [PASS] `state/io.py:93` `"goal_context": ""` — matches.
- [PASS] `prompts/storytell_system.j2:14` `goal_context` in schema — matches.
- [PASS] `prompts/sanitize_thread.j2:15,86` `goal_context` — matches.
- [PASS] `prompts/generate_seed_system.j2:37,64` `goal_context` — matches.
- [PASS] `templates/_state_left.html:64,109` `goal_context` — matches.
- [PASS] `ev/checkers/arc_resolution_validity.py:64-69` `goal_context` — matches.
- [PASS] `ev/audit.py:312,321,325` `goal_context` — matches.
- [PASS] `templates/_save_picker.html:29` `save.visible_goal` — matches reference (but step is a rename, not deletion).
- [PASS] `chapter_end` references in `turn_state.py:516-522` — matches plan's Phase 02.
- [PASS] `chapter_end` in `storytell_system.j2:16,72,74` — matches.
- [PASS] `turns_since` guard at `turn_state.py:225-233` — matches Phase 04.
- [PASS] `promote_to_world_state` at `state.py:161` and `turn_state.py:341,343` — matches Phase 05.
- [PASS] `drop_threads`/`new_threads` at `state.py:187-188`, `turn_state.py:235-243,257-258,263-270` — matches Phase 03.
- **MISSING** `extraction.py:237` `chapter_end: bool = False` — not referenced by Phase 02.
- **MISSING** `long_term_objective` — zero matches in source. Phases 06-08 reference it as rename target.
- **MISSING** `arc_origin` — zero matches in source. Phase 01/08 reference it as rename target.

---

## Scope violations

- Phase 06: "Update ev tools references to use new field names" — **violates Non-goals:** "Field renames (Phase 02 of master plan)". All 5 file references rename `visible_goal` → `long_term_objective`.
- Phase 07: "Update remaining references to use new field names" — same violation. All 5 file references rename `visible_goal` → `long_term_objective`.
- Phase 08: "Update all template references to use new field names" — same violation. All 5 file references rename `visible_goal` → `long_term_objective` or `goal_context` → `arc_origin`.
- Phase 09: "`golden-piracy` pack — add `pc_situation_schema`" — **violates Non-goals:** "New field additions (Phase 03 of master plan)". `pc_situation_schema` is a new field that doesn't exist yet.
- Phase 01 sub-steps: `generate_seed_system.j2:37,64`, `_state_left.html:64,109`, `_save_picker.html:29` — rename `goal_context` → `arc_origin`, violating Non-goals.
- Phase 01 sub-step: `turn_state.py:534-541` — "update goal_update path (renamed in Phase 02)" — this is a rename, not a deletion.

---

## Format issues

- **Section ordering:** The plan follows the required format (Purpose → Problem → Out of Scope → Firm Decisions → Risks → Phases → Verification). Correct.
- **Phase format:** Each phase has Files/What/Why/Validation. Correct.
- **Missing:** The plan doesn't include a `Tests required` field per phase, though tests are temporarily disabled per the project's current state. Acceptable given the local AGENTS.md says "Tests are temporarily removed during refactor. Do not write or reference tests until this phase is complete."
- **Missing:** Documentation updates (`docs/architecture/`, `docs/repomap.md`, `AGENTS.md`). The local AGENTS.md requires doc updates alongside code changes: "Documentation — mandatory: Any code change touching a module, config key, model field, prompt, or public API requires corresponding updates." The plan doesn't include a documentation phase or mention doc updates. **[QUESTION: should a doc-update phase be added, or is it intentionally deferred?]**

---

## Risk assessment

- **blocks-execution:** Executing Phases 06-08 as-written will introduce references to `long_term_objective` and `arc_origin` that don't exist, breaking `make check`. Resolve by either removing these phases or retargeting them as pure deletions of `goal_context`/`visible_goal` references (with renames deferred).
- **blocks-execution:** Not deleting `StorytellerResult.chapter_end` in `extraction.py:237` means the model still carries the field — `grep -r "chapter_end" ccya/` will still match.
- **blocks-execution:** Adding `pc_situation_schema` before it's defined means the import/model won't validate.
