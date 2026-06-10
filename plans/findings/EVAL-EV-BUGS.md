# EV Tooling & Eval System — Bugs & Issues

> Findings from spot check verification (rim save, 32 turns), eval command verification (phases 4-5), and prior game data analysis (noir 25 turns, byzantium 31 turns).
>
> **Audit 2026-06-10:** All eval checker bugs verified against current source. 11 eval checkers still broken. 2 eval bugs already fixed (Bug 1, Bug 10).

---

## EV Tooling Bugs (from spot check phases 1-5)

These are bugs in the `ev.py` CLI tooling discovered during systematic verification against the rim save (`saves/the-outer-rim--after-unification-2026-06-08/`) and ephemeral play sessions.

### EV-1 — `prompt --system` returns data from a different game

**Severity:** Red (data contamination)

**Symptom:** `ev.py prompt 1 ruling --system` returned output from a noir game featuring "Timothy Ryan" and "Lisamouth Pier 14" — not turn 1 of the rim save which features "Jared Lopez" and "Kelleyborough Orbital Docking Bay".

**Root cause:** The `prompt` command is reading from multiple event sources or there's data contamination across game sessions. The text output for `turn 1` was correct (Jared Lopez), but the `--system` flag returned a different game's data entirely.

**Evidence:** `ev.py turn 1` shows correct rim save data. `ev.py prompt 1 ruling --system` shows noir game data.

**Fix needed:** Investigate how `prompt` command reads events — it appears to be mixing data from different game sessions or using the wrong event source for the `--system` flag.

---

### EV-2 — `source .venv/bin/activate` broken in bash tool

**Severity:** Red (tooling workaround needed)

**Symptom:** `source .venv/bin/activate && python` returns `command not found: python`.

**Root cause:** PATH isn't set after activation in the bash tool shell. The workaround is to use `.venv/bin/python` directly.

**Evidence:** `source .venv/bin/activate && which python` returns `/usr/bin/python` (system Python), not the venv Python. `.venv/bin/python` works correctly.

**Fix needed:** Investigate why PATH isn't set after activation in the bash tool shell. Document workaround: use `.venv/bin/python` as the interpreter directly.

---

### EV-3 — `location_change` checker always fails

**Severity:** Yellow (structural gap)

**Symptom:** `location_change` checker reports `required field 'applied.location_change' not found in any event`. Fails on every turn, every run.

**Root cause:** The checker expects an `applied.location_change` field in events, but this field is not being emitted into the event stream. Either the field isn't being written by the state pipeline, or the checker is looking in the wrong event type.

**Evidence:** `deltas 5` shows state diffs but no `applied.location_change` key. The diff command does show location changes from `applied/changes` in intermediate turns, suggesting the data exists but isn't in the event structure the checker reads.

**Fix needed:** Either emit `applied.location_change` in events when location changes occur, or update the checker to read from the correct event field.

---

### EV-4 — `sanitizer_lifecycle` checker always fails

**Severity:** Yellow (structural gap)

**Symptom:** `sanitizer_lifecycle` checker reports `required field 'threads_updated' not found in any event`. Fails on every turn, every run.

**Root cause:** The checker expects a `threads_updated` field in events, but the sanitizer writes thread operations in a different structure. The `deltas 5` output shows sanitizer does emit `threads_updated: ['logistics_squeeze']` and `threads_added: ['inspector_scrutiny']`, but the checker can't find them — likely a field routing issue between what the sanitizer emits and what the checker reads.

**Evidence:** Turn 5 has a sanitizer event (confirmed by design spec). `deltas 5` shows sanitizer output with thread operations. But the checker pre-validates and fails before running.

**Fix needed:** Align the sanitizer event emission with what the `sanitizer_lifecycle` checker expects, or update the checker to read the actual event structure.

---

### EV-5 — Conditions not mentioned in ruling reason (recurring)

**Severity:** Yellow (quality issue)

**Symptom:** `conditions_lifecycle` checker flags conditions present in state but not mentioned in ruling reason. Occurs on turns 5, 21, 23, 24, 25 in the rim save.

**Conditions flagged:** `cornered` (turn 5), `exhausted` (turn 21), `startled` (turn 23), `wounded` + `winded` (turn 24).

**Root cause:** The ruling pipeline does not reference conditions that are present in the game state when generating its output. This is a quality issue with the ruling prompt/pipeline, not a tooling bug per se — but the ev tooling correctly detects it.

**Fix needed:** Update the ruling pipeline to mention conditions present in state when generating the ruling output. This is an engine/prompt issue, not an ev.py issue.

---

### EV-6 — Turn 24 specific issue: beat_locked but pending_gm_beat.type=None

**Severity:** Yellow (engine quality issue)

**Symptom:** `gm_beat_lifecycle` checker flags turn 24: `beat_locked=True, storytell_type='complication' but pending_gm_beat.type=None (expected 'breathing_room')`.

**Root cause:** The beat was locked (from a previous turn) but the pending_gm_beat was consumed/cleared, leaving beat_locked=True with no pending beat to match. This is an engine state consistency issue.

**Fix needed:** Investigate the beat locking mechanism in the engine to ensure consistency between `beat_locked` flag and `pending_gm_beat` state.

---

### EV-7 — `pacing_directives` stale tracking

**Severity:** Yellow (timing mismatch)

**Symptom:** Turn 10 and 24 flag: `gm_beat.type='complication' (pressure type) but consecutive_pressure_turns=0 (expected >= 1)` on turn 24. Turn 22: `gm_beat.type=None (not pressure) but consecutive_pressure_turns=5 (expected 0)`.

**Root cause:** Stale consecutive pressure tracking — the counter captures pre-extraction state but is paired with post-extraction gm_beat types.

**Evidence:** `pacing_directives` checker fails on turns 10, 24 with stale counter values.

**Fix needed:** Align the consecutive pressure counter with the gm_beat type at the same point in the event lifecycle.

---

### EV-8 — `input~spaceport` search returns nothing

**Severity:** Informational (design limitation)

**Symptom:** `ev.py search "input~spaceport"` returns no matches, even though the narration clearly mentions "spaceport" (turn 1 user prompt says "Look around the spaceport").

**Root cause:** The search command operates on structured event fields, not raw narration text. The word "spaceport" appears in narration but not in the searchable structured fields.

**Fix needed:** This is likely by design — search is meant for structured data, not full-text search. If full-text search is desired, it would be a new feature, not a bug fix.

---

### EV-9 — LLM checkers can't run (missing `mlx_lm` module)

**Severity:** Red (blocks LLM checker verification)

**Symptom:** `ev.py check --all --llm` fails with `Failed to load checker model: No module named 'mlx_lm'`. Framework correctly warns and removes LLM checkers from the run.

**Root cause:** The `mlx_lm` Python module is not installed in the project venv. Without it, no LLM checkers can run.

**Evidence:** Both `--llm` flag and `--checker-model` flag are accepted correctly (no error on the flags themselves). The framework handles the failure gracefully.

**Fix needed:** Install `mlx_lm` in the venv to enable LLM checker testing. This is an environment/setup issue.

---

### EV-10 — Play command format bug: `:+d` on float momentum_delta

**Severity:** Red (crash on play output)

**Symptom:** `ev.py play "..."` crashes with `ValueError: Unknown format code 'd' for object of type 'float'` when formatting momentum delta.

**Root cause:** `ccya/ev/play.py:185` uses `:+d` (integer format) on `momentum_delta_ruling` which can be a float. Line 194 was fixed to `:+.1f` but line 185 was missed.

**Evidence:** `git diff ccya/ev/play.py` shows line 194 was changed from `:+d` to `:+.1f`, but line 185 still has `:+d`.

**Fix needed:** Change line 185 from `:+d` to `:+.1f` to match line 194.

---

## Eval System Bugs (Assertion False Positives)

> **Status:** These bugs are in the old `ccya/eval/` system which is now empty (only `__pycache__` remains). The ev.py tooling (Phase 2 checkers) has replaced this system. Marked obsolesced pending confirmation that the old eval system is fully retired.

### B11 — Condition schema drift (OBSOLESCED)

**Status:** OBSOLESCED — old eval system retired

**Symptom:** CONDITION_MODS only has 5 entries, LLM-generated conditions become orphaned → 4-5 failures/run.

**Note:** Not a checker bug but confirmed by eval. The new ev.py checkers (conditions_lifecycle) handle this differently.

---

### B12 — actions_quality assertion fires on system events (OBSOLESCED)

**Status:** OBSOLESCED — old eval system retired

**Symptom:** Checks ALL events including `kind="condition_expired"` and `kind="sanitizer"` which have no storytell phase → exactly 3 failures/run.

**Note:** The new ev.py checkers only run on turns with actual storytell events, avoiding this issue.

---

### B13 — consecutive_pressure_tracking timing mismatch (OBSOLESCED)

**Status:** OBSOLESCED — old eval system retired

**Symptom:** Reads storytell.gm_beat.type from THIS event but meta.counter captures pre-extraction state_snapshot → stale values paired with wrong types on multi-event turns.

**Note:** The new ev.py `pacing_directives` checker handles this differently.

---

## Eval Gaps / Auto-Checker Additions (Legacy)

> **Status:** These were gaps in the old `ccya/eval/` system. The new ev.py checkers (Phase 2) partially address some of these concerns (e.g., `sanitizer_lifecycle`, `thread_lifecycle`, `pacing_directives`). Remaining gaps should be evaluated against the new checker framework.

### Goal Stagnation Detection (PARTIALLY ADDRESSED)

The old system had no stagnation detection. The new `pacing_directives` checker validates directive rendering and known values, but does not measure goal change frequency.

**Remaining gap:** No checker counts turns between consecutive sanitizer-driven goal changes or flags when the visible_goal should have changed but didn't.

---

### Background Thread Accumulation (PARTIALLY ADDRESSED)

The old system had no thread age or accumulation checks. The new `thread_lifecycle` checker validates thread_add applied and thread_update IDs valid, but does not count inactive threads or measure their age.

**Remaining gap:** No checker counts threads with `active=False` in the active list, measures average age of stale threads, or validates that background/latent cleanup is happening as expected.

---

### Sanitizer Event Validation (NOT ADDRESSED)

The old system had no sanitizer event validation. The new `sanitizer_lifecycle` checker exists but currently fails (EV-2 above) because it can't find the expected fields.

**Remaining gap:** Once EV-2 is fixed, the `sanitizer_lifecycle` checker should validate sanitizer output structure and correctness. Until then, sanitizer events are not validated by any checker.

---

## Eval System Verification (Phase 5)

> **Status:** The `ev.py eval` command works correctly end-to-end. Batch play of scenario turns, checker aggregation, and Markdown report output all function as designed.

### What works:
- `ev.py eval list` — reports "No YAML scenarios found" when directory is empty
- `ev.py eval run <scenario>` — creates ephemeral sessions, runs all checkers, produces report
- `ev.py eval run --report <file>` — writes Markdown report to file
- `ev.py eval run --checkers "a,b"` — runs only specified checkers

### Checker failures in eval (expected data-shape issues):
When running against ephemeral play sessions, 6 of 12 checkers fail because the events don't populate `extraction_context` fields:
- `location_change`, `inventory_integrity`, `conditions_lifecycle` — missing `extraction_context.*_this_turn`
- `npc_presence`, `pacing_directives` — missing `extraction_context`
- `sanitizer_lifecycle` — missing `threads_updated`

These are **not eval system bugs** — they're pre-existing field-mapping issues (EV-3, EV-4 above) that the eval system correctly surfaces. The eval system works; it's detecting real engine issues.

### Mechanical changes needed:
The eval system was planned around a specific event schema. As the engine evolves (mechanical changes to event structure), the checkers it runs may need adaptation to match new field names or structures. This is a maintenance concern, not a bug.

---

## What to Fix First

### Eval Checkers (high priority — break testing infrastructure)
1. **Bug 6:** Fix `gm_beat_lifecycle` — add `triggered_by_momentum` guard to match engine at `turn.py:1091-1106`
2. **Bug 3:** Remove `ruling.band` from `momentum_lifecycle` requires_fields — internal guard already skips non-rolled turns
3. **Bug 9:** Remove `threads_removed` from `sanitizer_lifecycle` requires_fields — events use `threads_resolved` instead
4. **Bug 8:** Add `extraction_context` to events or remove from requires_fields in 7 affected checkers
5. **Bug 4:** Use `momentum_after` instead of `state_snapshot` for floor streak detection in `momentum_lifecycle`
6. **Bug 5:** Replace `break` with `continue` in floor streak loop to track all floor episodes
7. **EV-4:** Fix `sanitizer_lifecycle` checker — align event emission with checker expectations

### EV Tooling (medium priority)
8. **EV-1:** Fix `prompt --system` data contamination — critical reliability issue
9. **EV-10:** Fix play command `:+d` format bug on line 185 — crashes on float momentum_delta
10. **EV-2:** Fix `source .venv/bin/activate` workaround — document `.venv/bin/python` usage
11. **EV-3:** Fix `location_change` checker — align event emission with checker expectations
12. **EV-9:** Install `mlx_lm` to enable LLM checker testing

### Engine/Prompt (low priority)
13. **EV-5:** Update ruling pipeline to mention conditions present in state
14. **EV-6:** Investigate beat locking consistency between `beat_locked` and `pending_gm_beat`
15. **EV-7:** Align consecutive pressure counter with gm_beat type timing

### Eval Gaps (low priority — evaluate against new framework)
16. Add goal stagnation detection (new checker or enhancement to existing)
17. Add background thread age/accumulation checks (new checker or enhancement to existing)

---

## Related Findings

- **Goal stagnation root cause:** [PRIORITIES#3](./PRIORITIES.md#3-g3j--goal-stagnation--sanitizer-too-slow-to-pivot-mh) → [FINDINGS-JUNE-6#G3](./FINDINGS-JUNE-6.md#g2---goal-stagnation--sanitizer-too-slow-to-pivot-confidence-h)
- **Thread accumulation root cause:** [PRIORITIES#5](./PRIORITIES.md#5-bz1o4--background-thread-accumulation-without-decay-mh) → [FINDINGS-JUNE-6#BZ1](./FINDINGS-JUNE-6.md#bz1-h-background-threads-accumulate-forever-without-decay) → [BUGS-OBSERVATIONS#O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent)
