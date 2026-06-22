# Eval Harness Strengthening

## Purpose

Make the eval harness catch more real bugs and surface regressions across runs, with minimal changes to existing infrastructure.

## Problem Statement

The eval harness runs 13-turn scenarios, generates judge scores, and produces a REPORT.md. But it has three structural gaps: (1) judge outputs can silently contain wrong data that the meta judge passes through without flagging, (2) there is no cross-run score comparison — only token regressions are tracked, so a mechanical_score drop from 5→4 is invisible, and (3) structural invariants like "inventory_remove targets items that exist" are checked per-turn but never aggregated at the run level, making the final state unvalidated.

## Constraints

- No new dependencies. Use existing YAML, json, and Path infrastructure.
- Changes must be backwards-compatible with existing eval run directories.
- Universal assert changes must not break the existing 21 checkers or their return contract.
- No judge model changes — only validation and reporting logic.

## Non-goals

- Expanding the eval to multiple scenarios (separate effort).
- Changing judge models, prompt templates, or trace building.
- Modifying the turn pipeline or engine code.
- Adding a pre-commit hook (separate effort).

## Solution

Add three orthogonal improvements: (A) validate domain judge output format before feeding to meta judge, (B) track all score deltas (not just mechanical) across runs and surface regressions as flags, (C) add structural invariant universal asserts that catch phantom inventory removals and orphan thread references, and (D) compare final state.yaml structural integrity across runs via a deterministic state diff.

## Firm decisions

1. Judge validation rejects domain judges with missing/empty body text — flags them in the report but does NOT skip the meta judge (meta judge sees what it gets, but the flag makes the problem visible).
2. Score regression tracking applies to all 6 score keys (mechanical, narrative, system_cohesion, prompt_quality, state_fidelity, prompt_adherence), not just mechanical.
3. New universal asserts use severity "red" for structural violations (phantom inventory, orphan threads) and "yellow" for behavioral warnings.
4. Golden-state comparison runs after the run completes, comparing the final state.yaml's structural shape (inventory IDs, thread IDs, condition IDs) against the previous run's final state — not against a fixed reference.
5. The `flag_at_top` list in `evals/config.yaml` gains two new kinds: `judge_output_suspicious` and `score_regression`.

## Risks, Ambiguities, and Blockers

- **R1**: Judge output validation may false-positive on a legitimate short response. Mitigate by only flagging when body_md is empty AND scores is empty — if scores parsed, the response is valid even if the body is terse.
- **R2**: Golden-state comparison depends on `state_snapshot` being present in events. The runner already injects `state_snapshot` into events at line 501-503 of runner.py, so this is reliable for the final turn.
- **R3**: Score regression flags depend on `previous_scores` being available from the previous run's judge.md files. The judge system already loads these at judge.py:1086-1094.

## Status
`completed`

## Phases

4 phases: Judge validation, Score regression tracking, Universal asserts expansion, Golden-state comparison.

---

## Implementation — Phase 1: Judge output validation

### Context files to load

- `ccya/eval/judge.py` lines 960-1020 (`_run_single_judge`)
- `ccya/eval/judge.py` lines 1134-1200 (domain judge result collection + meta judge call)
- `ccya/eval/report.py` lines 297-316 (judge_score_drop flag)

### Detailed steps

#### Step 1.1 — Add suspicious-output detection to _run_single_judge

**File:** `ccya/eval/judge.py`

**What:** After `parse_judge_response()` at line ~968, add a validation check on the returned `scores` dict and `body_md` string. If `scores` is empty (no score fields parsed) AND `body_md` is empty or whitespace-only, set `result.suspicious = True` on the `JudgeResult`. Add a `suspicious: bool = False` field to the `JudgeResult` dataclass at line 60.

**Why:** The prompt_pipeline judge returned only 179 bytes of YAML front matter with no analysis text and no valid scores. This should be flagged so the meta judge's synthesis can be flagged as unreliable.

**Validation:** Run `make check`. Manually inspect that a JudgeResult with empty body and empty scores gets `suspicious=True`, and a normal result stays `False`.

#### Step 1.2 — Add judge_output_suspicious flag to _collect_flags

**File:** `ccya/eval/report.py`

**What:** In `_collect_flags()`, after the existing judge_score_drop block (line 297-315), add a new block that checks each JudgeResult for `suspicious=True`. If any are suspicious, append a Flag with `kind="judge_output_suspicious"`, summary listing the suspicious judge IDs, detail explaining why (empty body + empty scores).

**Why:** Makes the validation visible in the report's flag block.

**Validation:** Run `make check`. Confirm the flag appears when a judge returns minimal output.

#### Step 1.3 — Add judge_output_suspicious to flag_at_top in config

**File:** `evals/config.yaml`

**What:** Add `judge_output_suspicious` to the `flag_at_top` list in the report section.

**Why:** Ensures the flag appears at the top of the report, not buried.

**Validation:** `grep judge_output_suspicious evals/config.yaml` confirms it's in the list.

---

## Implementation — Phase 2: Score regression tracking

### Context files to load

- `ccya/eval/report.py` lines 130-147 (StreamRegression, Flag dataclasses)
- `ccya/eval/report.py` lines 297-316 (existing judge_score_drop block)
- `ccya/eval/report.py` lines 358-426 (_render_judge_summary)
- `ccya/eval/report.py` lines 714-813 (write_full_report)

### Detailed steps

#### Step 2.1 — Extend _render_judge_summary to show all score deltas

**File:** `ccya/eval/report.py`

**What:** In `_render_judge_summary()`, lines 408-416 currently only show `previous机械_score` and `previous_narrative` if they differ. Extend this to show ALL 6 score keys from `meta.previous_scores`, with delta notation: `**Narrative:** 4/5 (was 5, ▼1)`. Use `_fmt_score` for int scores and `_fmt_rate` for float rates. Only show the delta when the previous value exists and differs from current.

**Why:** Currently you have to dig into the report to see if a score changed. This makes regressions immediately visible in the judge summary section.

**Validation:** Run `make check`. Confirm the judge summary section shows deltas when scores differ.

#### Step 2.2 — Add score_regression flag kind

**File:** `ccya/eval/report.py`

**What:** In `_collect_flags()`, after the existing `judge_score_drop` block, add a new block that iterates ALL 6 score keys. For each key where both current and previous values exist and current < previous, create a Flag with `kind="score_regression"`. If multiple scores regressed, aggregate into one flag with per-score details.

**Why:** The existing `judge_score_drop` only checks mechanical_score. A regression in system_cohesion or state_fidelity would be invisible.

**Validation:** Run `make check`. Confirm the flag fires when any score drops.

#### Step 2.3 — Add score_regression to flag_at_top in config

**File:** `evals/config.yaml`

**What:** Add `score_regression` to the `flag_at_top` list.

**Why:** Score regressions are the most actionable signal and should be prominent.

**Validation:** `grep score_regression evals/config.yaml` confirms it's in the list.

---

## Implementation — Phase 3: Universal asserts expansion

### Context files to load

- `ccya/eval/universal_asserts.py` lines 1-30 (imports, MOMENTUM_DELTA, MOMENTUM_MIN)
- `ccya/eval/universal_asserts.py` lines 493-514 (check_zero_stack_overdraw — model for inventory checks)
- `ccya/eval/universal_asserts.py` lines 653-698 (check_arcthread_key_dedup — model for thread checks)
- `ccya/eval/universal_asserts.py` lines 1057-1086 (run_all_universal_asserts — registration)

### Detailed steps

#### Step 3.1 — Add inventory_remove_existence assert

**File:** `ccya/eval/universal_asserts.py`

**What:** Add a new function `check_inventory_remove_existence(event, prev_event)` that:
- Reads `inventory_remove` from `event["applied"]`
- Reads `inventory` from `prev_event["state_snapshot"]`
- For each removed item ID, checks that it exists in the previous inventory with amount > 0
- Returns assertion `"universal.inventory.remove_existence"` with severity "red"
- Pattern follows `check_zero_stack_overdraw` exactly

**Why:** The T7 phantom inventory removals (ledger, merchant_seal removed but never added) are the #1 structural bug the eval found. This assert catches them per-turn.

**Validation:** `uv run python -c "from ccya.eval.universal_asserts import check_inventory_remove_existence"` imports cleanly.

#### Step 3.2 — Add thread_update_id_valid assert

**File:** `ccya/eval/universal_asserts.py`

**What:** Add a new function `check_thread_update_id_valid(event)` that:
- Reads `thread_update` from the storyteller extraction output
- Reads `threads` from `event["state_snapshot"]["arc"]["threads"]`
- For each thread_update signal, checks the thread ID exists in state
- Returns assertion `"universal.thread_update.valid_id"` with severity "red"

**Why:** The eval found `thread_updates.unknown_id` warnings for threads referenced in signals but not in state. This catches them structurally.

**Validation:** `uv run python -c "from ccya.eval.universal_asserts import check_thread_update_id_valid"` imports cleanly.

#### Step 3.3 — Register new asserts in run_all_universal_asserts

**File:** `ccya/eval/universal_asserts.py`

**What:** Add the two new functions to the hardcoded list in `run_all_universal_asserts()` (lines 1060-1082). Place them after the existing inventory checks (after `check_no_negative_inventory`).

**Why:** Assertions must be registered to run during the eval.

**Validation:** `make check` passes. The assert count in the eval output increases from 21 to 23.

---

## Implementation — Phase 4: Golden-state comparison

### Context files to load

- `ccya/eval/runner.py` lines 547-568 (run_result serialization, note about state.yaml)
- `ccya/eval/report.py` lines 595-654 (_compute_pacing_metrics — model for state-level aggregation)
- `ccya/eval/report.py` lines 714-743 (write_full_report — where prev_run data is loaded)

### Detailed steps

#### Step 4.1 — Copy state.yaml to artifacts directory

**File:** `ccya/eval/runner.py`

**What:** After the run completes (around line 547, where the comment says "state.yaml is intentionally NOT copied"), add logic to copy `save_dir / "state.yaml"` to `artifacts_dir / f"{scenario.id}.state.yaml"`. This is needed so the report can compare states without accessing the save directory.

**Why:** The report module reads from artifacts, not save directories. State needs to be in artifacts for cross-run comparison.

**Validation:** Run a test eval. Confirm `state.yaml` appears in the artifacts directory.

#### Step 4.2 — Add _compare_state_structures function to report.py

**File:** `ccya/eval/report.py`

**What:** Add a new function `_compare_state_structures(cur_state: dict, prev_state: dict) -> list[dict]` that compares structural (non-narrative) fields between two state dicts. Compare:
- Inventory: set of item IDs (not amounts or descriptions)
- Threads: set of thread IDs + their active/urgency status
- Conditions: set of condition IDs
- Quests: set of quest IDs + status
- NPC compendium: set of NPC IDs

Return a list of diffs: `{"field": "inventory.ids", "added": [...], "removed": [...]}`.

**Why:** Structural state comparison catches silent corruption (phantom inventory items appearing, threads vanishing) that per-turn asserts miss.

**Validation:** `uv run python -c "from ccya.eval.report import _compare_state_structures"` imports cleanly.

#### Step 4.3 — Render state comparison in write_full_report

**File:** `ccya/eval/report.py`

**What:** In `write_full_report()`, after the pacing metrics section (line 797) and before the Turn Metrics section (line 798), load `cur_state.yaml` and `prev_state.yaml` from artifacts and call `_compare_state_structures()`. Render as a "## State Comparison" section with a table of structural diffs. Only render if a previous run exists.

**Why:** Surfaces state-level regressions directly in the report.

**Validation:** `make check` passes. Report includes a State Comparison section when a previous run exists.

#### Step 4.4 — Add state_comparison_diff flag kind

**File:** `ccya/eval/report.py`

**What:** In `_collect_flags()`, add a block that calls `_compare_state_structures()` if prev_state is available. If any field has items removed from inventory or threads that were active in the previous run, create a Flag with `kind="state_comparison_diff"` and severity based on whether items/threads were added vs removed.

**Why:** Structural state diffs that remove items or threads are regressions that should be flagged prominently.

**Validation:** Run `make check`. Confirm the flag fires when structural state changes between runs.

### Tests to write or update

No new test files. The existing universal asserts framework provides verification:
- Each new assert function can be tested by constructing a mock event dict and calling the function directly
- The report functions can be verified by running `make eval` and inspecting REPORT.md
