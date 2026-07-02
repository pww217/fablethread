# Review: I-19 Extract phased subroutines from run_turn

## Verdict
ready with notes

## TL;DR
3 blockers auto-fixed (missing `delta` in `_apply_phase` return, invalid `ruling_data` parameter in `_persist_and_async_cleanup`, async generator can't return values). 0 remaining questions. Plan is ready to execute after fixes.

## Needs your input
- None

## Auto-fixed
- [plans/I-19-extract-phased-subroutines.md:52-59] `_apply_phase` return tuple was `tuple[WorldState, dict, list, list, list]` (5 elements) but `_apply_state_updates` returns 6 values including `delta`. Fixed to `tuple[WorldState, StateDelta | None, dict, list, list, list]` — added `delta` to both signature and return doc.

- [plans/I-19-extract-phased-subroutines.md:61-74] `_persist_and_async_cleanup` had `ruling_data: dict[str, Any]` parameter that doesn't exist in the source. Ruling data is spread across 9 individual variables (`_intent`, `_outcome`, `ruling_metrics`, `rendered_ruling_system`, `rendered_ruling_user`, `ruling_raw_response`, `ruling_parse_error`, `ruling_trimmed`, `ruling_trimmed_chars`). Replaced `ruling_data` with all 9 individual parameters.

- [plans/I-19-extract-phased-subroutines.md:61-74] `_persist_and_async_cleanup` was declared as `async def` returning `tuple[TurnResult, dict, WorldState]` but contains `yield` statements — an async generator can't return values that callers access. Fixed to `-> None` with a `persist_result` dataclass parameter that the function mutates. Caller reads `persist_result.result_obj`, `persist_result.final_metrics`, `persist_result.final_state` after the call.

- [plans/I-19-extract-phased-subroutines.md:180] Phase 04 step 1 parameter list updated to match fixed signature (replaced `ruling_data` with 9 individual ruling variables + `persist_result`).

- [plans/I-19-extract-phased-subroutines.md:198-200] Phase 04 steps 2-3 updated: instead of "return tuple", now defines `PersistResult` dataclass and mutates it. Caller reads from `persist_result` after the call.

- [plans/I-19-extract-phased-subroutines.md:204] Phase 04 validation updated to match new approach.

- [plans/I-19-extract-phased-subroutines.md:218] Risk assessment updated: "PersistContext dataclass" → "PersistResult dataclass for return values".

- [plans/I-19-extract-phased-subroutines.md:228-230] Documentation Updates: Added `docs/architecture/` update (mandatory per plan skill). Was missing — only had repomap and AGENTS.md.

## Non-blocking concerns
- Phase 04 has 22+ parameters — the plan acknowledges this risk. The `PersistResult` dataclass reduces one return-value parameter but doesn't address the input parameter count. Consider whether some parameters could be derived from `ctx` (e.g., `trace_id`, `turn_no`, `config`, `save_dir`) to reduce the signature.

- `_extract_phase` has a `yield` inside (line 248 in source: `yield _evt` from the extraction pipeline iteration). The plan correctly declares it as `async def` which handles this. No fix needed — just confirming the plan accounts for it.

- `_narrate_phase` has 5 yield statements (narrate_start, narrate_first_token, token × N, narrate_done, extract_start). All correctly handled as async generator.

- The plan's line number references are approximate (e.g., "lines 147-212" is actually 66 lines, not 65). This is cosmetic — the extraction boundaries are correct.

## Contract checks

| Check | Status |
|---|---|
| `_narrate_setup` exists in `narrate.py` | PASS |
| `_apply_state_updates` exists in `turn_state.py:418`, returns 6-tuple | PASS (fixed plan to match) |
| `_run_extraction_pipeline` exists in `extraction/pipeline.py:36`, takes `band`, `packing` as kwargs | PASS (plan has `ctx` + `outcome` from which these are derived) |
| `_run_world_step` exists in `world.py` | PASS (not extracted, stays as-is) |
| `sanitize_threads` exists in `thread_sanitizer.py` | PASS (not extracted, stays as-is) |
| `TurnContext` has fields used by plan (`state`, `packing`, `_selected_beat`, etc.) | PASS |
| `PacingContext` has fields used by plan (`directive`, `outcome_hint`, `summary`, etc.) | PASS |
| `WorldState` has methods used by plan (`set_turn`, `expire_world_state_facts`, `add_recent_roll`, etc.) | PASS (I-17 #3 implemented these) |
| `StateDelta` imported in `turn.py` | PASS |
| `TurnResult` imported in `turn.py` | PASS |

## Scope check

Plan's stated scope: Extract 4 inline sections from `run_turn` into private functions in `turn.py`. All in the same file.

Non-goals (implicit): No new modules, no behavioral change, no changes to extracted modules (ruling.py, narrate.py, turn_state.py, world.py, thread_sanitizer.py).

| Scope item | Status |
|---|---|
| Only touches `turn.py` | PASS |
| No new modules/files created | PASS |
| No behavioral change | PASS (extraction is mechanical) |
| Doesn't modify extracted modules | PASS |
| Doc updates included | PASS (architecture, repomap, AGENTS.md) |

## Phase ordering check

| Phase | Dependency | Resolvable |
|---|---|---|
| 01 — `_narrate_phase` | None | PASS |
| 02 — `_extract_phase` | Pattern from 01 | PASS |
| 03 — `_apply_phase` | Pattern from 02 | PASS |
| 04 — `_persist_and_async_cleanup` | Pattern from 01-03 | PASS |

Order is correct — each phase builds on the extraction pattern of the previous one. No circular dependencies.
