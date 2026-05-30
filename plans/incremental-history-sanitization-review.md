# Plan Review: Incremental History + Compactor Removal

## Summary

The plan replaces batch compaction with per-turn `history_bullet` from the storyteller, removes the compactor entirely, and adds a `reason` field to `CompactorSanitizationAction` for future use. Phase ordering is correct, interface contracts are mostly accurate, and the approach is sound. However, there are **5 blocks-execution issues** that will cause import errors or runtime failures if followed blindly, plus several execution-hazards that will waste the executor's time. Verdict: **request changes**.

## Issues — blocks-execution

### Step 2.2: Deleting `compaction_signals.py` breaks `judge.py` and `universal_asserts.py`
- **[blocks-execution]** `ccya/eval/judge.py` imports `render_compaction_section` and `compute_compaction_signals` from `compaction_signals.py` (lines 728, 1157). `ccya/eval/universal_asserts.py` calls `_assert_compactor_sanitization_nonzero` (line 1099) which reads `applied.compaction` from event data. Deleting `compaction_signals.py` without updating these files will cause `ImportError` at eval/judge startup. The `judge.py` compaction-specific dataclasses and the `_is_compaction_turn` / `_select_compaction_events` helper functions also reference compaction concepts throughout (lines 177-235). Fix: Step 2.2 must also gut or remove the compaction judge in `judge.py` and the `_assert_compactor_sanitization_nonzero` call in `universal_asserts.py`.

### Step 2.4: Renaming `load_recent_chronicle_turns` without updating `panels.py`
- **[blocks-execution]** `ccya/server/panels.py` line 12 imports `load_recent_chronicle_turns` and line 58 calls it. The plan only mentions `chronicle.py`, `__init__.py`, and `turn.py` as call sites. If the function is renamed to `load_last_narration` in `chronicle.py` and `__init__.py` but `panels.py` still imports the old name, the server will crash on startup. Fix: Add `ccya/server/panels.py` to Step 2.4's file list and update import/call.

### Step 1.5: `_compute_recent_window` tuple destructure not fully specified
- **[blocks-execution]** `_compute_recent_window` returns `(desired_recent, last_compacted_turn)` and is destructured at turn.py line 1089 as `desired_recent, last_compacted_turn = _compute_recent_window(state, config)`. The plan says to rename it to `_recent_turn_count` returning a single `int`, but Step 1.5 doesn't mention updating the destructuring call at line 1089 or the `load_recent_chronicle_turns` call at line 1090-1094 that passes `min_turn_exclusive=last_compacted_turn`. Removing `last_compacted_turn` without updating these call sites will cause `ValueError: too many values to unpack` or `NameError`. Fix: Step 1.5 must explicitly list updating the call site at turn.py lines 1089-1099.

### Step 1.5: `load_recent_chronicle_turns` `min_turn_exclusive` parameter
- **[blocks-execution]** The call at turn.py line 1090-1094 passes `min_turn_exclusive=last_compacted_turn` to `load_recent_chronicle_turns`. Step 2.4 says to remove this parameter when renaming to `load_last_narration`, but Step 1.5 (which runs first) doesn't touch it. This means during Phase 1, the function still has the old signature with `min_turn_exclusive`. The plan must either: (a) simplify the signature in Phase 1 Step 1.5 (remove `min_turn_exclusive` and the `last_compacted_turn` variable together), or (b) defer the rename to Phase 2 and handle both in one step. Fix: Move the `_compute_recent_window` simplification, the `load_recent_chronicle_turns` → `load_last_narration` rename, and the `min_turn_exclusive` removal into a single coherent step, either in Phase 1 or Phase 2.

### Step 2.5: TV viewer compaction event line range is wrong
- **[blocks-execution]** Plan says "lines 376-392" for tv.py compaction event handling, but the actual range is lines 376-393 (the `continue` at line 393 is part of the `if` block). If the executor only removes 376-392, line 393 (`continue`) will be orphaned and cause a syntax error. Fix: Update the line range to 376-393.

## Issues — execution-hazard

### Phase 1 Context files missing `ccya/prompts/context.py`
- **[execution-hazard]** `context.py` defines `NarratorBoundary` with `prior_history: list[str]` (line 227), `recent_turns: list[ChronicleEntryBlock]` (line 226), and `StorytellerBoundary` with `recent_turns` (line 283). Step 1.5 changes the recent_turns semantics to always-1 but doesn't mention updating these boundary models. While they're documentation models (not enforced at runtime by Pydantic for template rendering), they should stay in sync with actual data flow. Fix: Add `ccya/prompts/context.py` to Phase 1 context files and note that `NarratorBoundary` and `StorytellerBoundary` boundary docs may need updating.

### Step 1.3: Missing `history_bullet` extraction path
- **[execution-hazard]** Step 1.3 says to format and append `history_bullet` to `prior_history` at turn.py, but Step 1.2 only adds the field to the prompt template and `StorytellerResult` model. The extraction pipeline at `extraction.py` line 653 yields `storytell_result.outcome_summary` — Step 1.3 doesn't specify how `history_bullet` flows from the storyteller LLM output through extraction to turn.py. The `StorytellerResult` model will pick it up via Pydantic parsing, but the yield tuple at extraction.py line 650-658 doesn't include it. The executor needs to know to extract `storytell_result.history_bullet` alongside `storytell_result.outcome_summary`. Fix: Step 1.3 should specify adding `history_bullet` to the extraction pipeline yield at extraction.py.

### Step 2.2: `CompactorNpcMerge` model will remain orphaned
- **[execution-hazard]** `CompactorNpcMerge` (models.py line 314) is only referenced in `CompactorSanitizationResult` (line 339). After `compactor.py` is deleted, these models are unused. The plan says to keep `CompactorSanitizationResult` and sub-models for future sanitization work, which is fine, but the REPOMAP section doesn't note this. Fix: Add a note to Step 2.2 that `CompactorNpcMerge` and `CompactorSanitizationResult` are intentionally kept as model definitions for future sanitization use.

### Step 2.4: `remove_last_chronicle_turn` references unknown
- **[execution-hazard]** The plan says "Remove `remove_last_chronicle_turn` if it's only used by the compactor." The executor needs to verify this before deleting. A grep shows it's defined at chronicle.py line 125 but its call sites should be checked. Fix: Executor should `grep -rn "remove_last_chronicle_turn" ccya/` before deleting.

### Step 2.3: Validation grep will also match `CompactorSanitizationResult`
- **[execution-hazard]** The validation check `grep -r "maybe_compact\|compactor\|compact_system\|compact_user" ccya/` will match `CompactorSanitizationResult`, `CompactorSanitizationAction`, and `CompactorNpcMerge` which are intentionally kept. Fix: Change the validation to exclude models: `grep -r "maybe_compact\|compact_system\|compact_user" ccya/` and separately verify `compactor\.py` is deleted.

## Issues — maintainability

### `eval/judge.py` compaction judge needs full removal, not just import
- **[maintainability]** Beyond the `compaction_signals` import, `judge.py` has substantial compaction-specific code: `_is_compaction_turn()` (line 177), `_select_compaction_events()` (line 195), `compaction_signals` parameter on dataclasses (lines 219, 243, 258, 270, 281, 452), and `compaction` as a judge domain (lines 49, 109, 123). Removing just the import will leave dead code throughout. Fix: Step 2.2 should specify removing the `compaction` judge domain from `judge.py` entirely, or marking it as disabled.

### `universal_asserts.py` `_assert_compactor_sanitization_nonzero` should be removed
- **[maintainability]** This function checks for compaction events in event data. After compactor removal, no compaction events will ever appear, making this assertion always pass vacuously. It should be removed. Fix: Add to Step 2.2: remove `_assert_compactor_sanitization_nonzero` from `universal_asserts.py` and its call at line 1099.

## Contract checks

- [x] `StorytellerResult` at models.py line 382 — correct, `history_bullet` will be added after `outcome_summary` at line 384
- [x] `CompactorSanitizationAction` at models.py line 320 — correct, `reason: str | None = None` will be added
- [x] `TurnContext.chronicle_tail` at turn.py line 78 — **confirmed**, Step 3.4 correctly targets this field
- [x] Template variables in `narrate_user.j2` — `prior_history` (line 50-51) and `recent_turns` (lines 56-61) are both provided by `narrate.py` (lines 83-84). Adding `history_bullet` to storyteller prompt schema requires updating `storytell_system.j2` (Step 1.2) and the JSON example — **confirmed**
- [x] Storyteller JSON schema at storytell_system.j2 lines 5-15 — `history_bullet` needs to be added after `outcome_summary` at line 8. Step 1.2 mentions this but doesn't specify the JSON example update explicitly. **MISMATCH**: Step 1.2 should specify adding `"history_bullet": "",` to the JSON schema example block at lines 5-15
- [ ] `load_recent_chronicle_turns` call at panels.py line 58 — **NOT MENTIONED** in plan. Will break if renamed without updating
- [ ] `_compute_recent_window` return value destructure at turn.py 1089 — **NOT MENTIONED** in Step 1.5. Will break if return type changes from tuple to int without updating call site

## Scope violations

None found. The plan correctly scopes Phase 2 as "remove compactor + add reason field" without adding deterministic sanitization (which is explicitly a non-goal per Firm Decision #4).

## Format issues

1. **Step 1.2** doesn't explicitly mention updating the JSON schema example in `storytell_system.j2` (lines 5-15). It mentions guidance text but the JSON example block at lines 5-15 also needs `"history_bullet": ""` added. The step should specify this.
2. **Step 1.3** references "around line 1200-1240" for `outcome_summary` flow, but the actual extraction yield is at `extraction.py` line 653. The step should specify the extraction pipeline yield tuple location more precisely.
3. **Phase 2 Step 2.5** line range for tv.py compaction event is 376-393, not 376-392 as stated.

## Additional items the plan should cover but doesn't

1. **`docs/repomap.md`** — The repomap documents `maybe_compact`, `compactor.py`, `compact_every`, `recent_turns_min`, `window_turns`, `chronicle_prefix_budget_tokens`, `last_compacted_turn`, and the compaction pipeline. These sections need updating after Phase 2. The plan's REPOMAP sections mention what changes but don't explicitly call out the repomap file as needing an update.
2. **`scripts/debug/ev.py`** — This script has a `compact` command and compaction-related display logic. It references `compaction`, `compact_start`, `compact_end`, `sanitization` extensively. After compactor removal, this script needs updating or the `compact` command needs removal.
3. **`ccya/eval/judge.py`** — As detailed above, has compaction judge domain code that needs removal alongside compactor deletion.
4. **`ccya/eval/universal_asserts.py`** — As detailed above, `_assert_compactor_sanitization_nonzero` needs removal.
5. **`ccya/tests/`** — Multiple test files reference `compact_every`, `recent_events`, `CompactorSanitizationResult`, `load_chronicle_tail`, etc. These need updating. The plan should note this even though tests are "temporarily removed during refactor" per AGENTS.md.
6. **`ccya/server/panels.py`** — As detailed above, imports and calls `load_recent_chronicle_turns`.