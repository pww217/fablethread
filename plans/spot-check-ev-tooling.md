# Spot Check: EV Tooling Design Verification

## Purpose

Verify that all 6 plans from the ev-tooling design (`docs/design/ev-tooling-design.md`) are fully realized by testing each primary capability against the rim save (`saves/the-outer-rim--after-unification-2026-06-08/`, 32 turns) and a live engine play session.

## Problem Statement

Six plans were completed to rebuild `ev.py` into a unified CLI backbone. There is no systematic verification that all capabilities work correctly against real game data. A spot check is needed to confirm: read-only inspection, checker library, play command, eval command, LLM checkers, and documentation cleanup all function as designed.

## Constraints

- Test against `saves/the-outer-rim--after-unification-2026-06-08/` (32 turns, rim save) as the primary dataset.
- Use `source .venv/bin/activate` before any Python invocation.
- Tests are manual CLI commands, not automated tests (tests are deferred per AGENTS.md).
- Do not modify the rim save; it is read-only test data.
- Play command tests create ephemeral sessions in `saves/ev/`.
- Old eval code (`ccya/eval/`) is already empty (only `__pycache__` remains).

## Non-goals

- Full regression suite or automated tests.
- Testing against multiple saves.
- Performance benchmarking.
- Testing server integration (ev.py has no server dependency).
- Testing `--interactive` and `--llm` play modes (requires terminal interaction).

## Solution

Run a structured sequence of CLI commands against the rim save and a live engine play session. Each command tests a specific capability from the design. Failures are noted; no code changes are made in this plan.

## Firm decisions

1. The rim save (`the-outer-rim--after-unification-2026-06-08/`) is the primary test dataset — 32 turns with sanitizer events at turns 5, 10, 15, 20, 25, 30 and condition_expired events at turns 12, 15, 29.
2. `scripts/debug/ev.py` is the entry point — it delegates to `ccya.ev.main()`.
3. `--save-dir` flag is required for checkers that need state access (`sanitizer_lifecycle`).
4. LLM checker tests require a running LLM backend; if the model fails to load, the checker is skipped (not a failure of the framework).
5. Play command tests use ephemeral saves in `saves/ev/` — no pack specified for baseline tests.

## Risks, Ambiguities, and Blockers

- **LLM availability:** Play command and LLM checkers require a running LLM backend. If the model is unavailable, those tests cannot complete. Note as "skipped — no LLM backend" rather than "failed."
- **Rim save state:** The rim save may lack certain fields some checkers require (e.g., `applied.location_change`). Checkers pre-validate and skip with a warning — this is expected behavior, not a failure.
- **`--interactive` mode:** Cannot be tested in this spot check (requires terminal interaction). Deferred.
- **`--llm` play mode:** Cannot be tested in this spot check (requires terminal interaction). Deferred.
- **Eval scenarios:** No YAML scenarios exist in `evals/scenarios/`. Will create a minimal test scenario inline.

## Status

`open`

## Phases

6 phases covering: (1) read-only inspection, (2) deterministic checkers, (3) LLM checkers, (4) play command, (5) eval command, (6) documentation cleanup verification.

---

## Implementation — Phase 1: Read-Only Inspection

### Context files to load
- `saves/the-outer-rim--after-unification-2026-06-08/events.jsonl` (test data)
- `ccya/ev/__init__.py` (dispatch)
- `ccya/ev/inspect.py` (summary, timing, turn, prompt)
- `ccya/ev/deltas.py` (deltas, mechanics)
- `ccya/ev/state_tools.py` (state, diff, trace, search)
- `ccya/ev/events.py` (data access layer)

### Detailed steps

#### Step 1.1 — Summary command

**What:** Run `ev.py summary` against the rim save. Verify it produces a one-line overview showing streams active, tokens, rules intent, and deltas for each turn.

**Validation:** Output shows 32 turns with stream names, token counts, and delta counts. No errors.

**Command:**
```bash
source .venv/bin/activate
python scripts/debug/ev.py summary saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.2 — Timing command

**What:** Run `ev.py timing` against the rim save. Verify it shows token counts and elapsed time per stream for every turn.

**Validation:** Output shows per-turn breakdown of ruling/narrate/scene/state/storytell streams with tokens_in, tokens_out, and timing.

**Command:**
```bash
python scripts/debug/ev.py timing saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.3 — Turn command (text and JSON)

**What:** Run `ev.py turn 1` and `ev.py turn 1 --json` against the rim save. Verify text output shows full prompts + outputs for all five streams, and JSON output shows raw event data.

**Validation:** Text output shows ruling/narrate/scene/state/storytell streams. JSON output is valid JSON with all event keys.

**Command:**
```bash
python scripts/debug/ev.py turn 1 saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
python scripts/debug/ev.py turn 1 --json saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.4 — Prompt command

**What:** Run `ev.py prompt 1 ruling user` and `ev.py prompt 1 ruling --system` against the rim save. Verify single field access and optional system prompt inclusion.

**Validation:** Shows the ruling stream's user prompt (or system prompt with `--system` flag).

**Command:**
```bash
python scripts/debug/ev.py prompt 1 ruling user saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
python scripts/debug/ev.py prompt 1 ruling --system saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.5 — Deltas command

**What:** Run `ev.py deltas 5` against the rim save. Verify it shows state mutations, extraction context, and sanitizer events (turn 5 has a sanitizer event).

**Validation:** Three sections separated by dividers: state diffs, extraction context flow, and sanitizer changes. Turn 5 should show sanitizer output.

**Command:**
```bash
python scripts/debug/ev.py deltas 5 saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.6 — Mechanics command with flags

**What:** Run `ev.py mechanics 5 --pacing --dice --sanitize` against the rim save. Verify rules intent, pacing context, dice summary, and sanitizer events.

**Validation:** Shows rules intent, pacing directives, dice results, and sanitizer thread operations.

**Command:**
```bash
python scripts/debug/ev.py mechanics 5 --pacing --dice --sanitize saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.7 — State command

**What:** Run `ev.py state --save-dir saves/the-outer-rim--after-unification-2026-06-08/` in multiple format modes. Verify state.yaml is read correctly.

**Validation:** Shows game state in requested format (full, compact, pc, inventory, location, scene, arc, npcs).

**Command:**
```bash
python scripts/debug/ev.py state --save-dir saves/the-outer-rim--after-unification-2026-06-08/ --format full
python scripts/debug/ev.py state --save-dir saves/the-outer-rim--after-unification-2026-06-08/ --format compact
python scripts/debug/ev.py state --save-dir saves/the-outer-rim--after-unification-2026-06-08/ --format inventory
```

#### Step 1.8 — Diff command

**What:** Run `ev.py diff 1 10` against the rim save. Verify state comparison between turns 1 and 10 shows NPCs, inventory, conditions, location, tags, and applied changes.

**Validation:** Shows differences between turn 1 and turn 10 state snapshots.

**Command:**
```bash
python scripts/debug/ev.py diff 1 10 saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
python scripts/debug/ev.py diff 1 10 saves/the-outer-rim--after-unification-2026-06-08/events.jsonl --section inventory
```

#### Step 1.9 — Trace command

**What:** Run `ev.py trace "momentum" --from 1 --to 10` against the rim save. Verify field tracking across turns with change indicators.

**Validation:** Shows momentum value per turn from 1 to 10, with change indicators where it differs from previous turn.

**Command:**
```bash
python scripts/debug/ev.py trace "pc.momentum" --from 1 --to 10 saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

#### Step 1.10 — Search command

**What:** Run `ev.py search "band:fail"` and `ev.py search "input~spaceport"` against the rim save. Verify cross-turn AND-search works.

**Validation:** Shows turns matching the search criteria.

**Command:**
```bash
python scripts/debug/ev.py search "band:fail" saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
python scripts/debug/ev.py search "input~spaceport" saves/the-outer-rim--after-unification-2026-06-08/events.jsonl
```

---

## Implementation — Phase 2: Deterministic Checkers

### Context files to load
- `ccya/ev/checkers/__init__.py` (registry, run_checker, run_checkers)
- `ccya/ev/check.py` (cmd_check)
- `ccya/ev/checkers/momentum.py`
- `ccya/ev/checkers/gm_beat.py`
- `ccya/ev/checkers/inventory.py`
- `ccya/ev/checkers/conditions.py`
- `ccya/ev/checkers/threads.py`
- `ccya/ev/checkers/arc_goals.py`
- `ccya/ev/checkers/npc_presence.py`
- `ccya/ev/checkers/pacing.py`
- `ccya/ev/checkers/sanitizer.py`

### Detailed steps

#### Step 2.1 — List checkers

**What:** Run `ev.py check --help` to verify checker registry is populated and lists all registered checkers with IDs, types, and descriptions.

**Validation:** Shows all 11 deterministic checkers + 3 LLM checkers with metadata.

**Command:**
```bash
python scripts/debug/ev.py check --help
```

#### Step 2.2 — Single checker on single turn

**What:** Run `ev.py check 5 momentum_lifecycle --save-dir saves/the-outer-rim--after-unification-2026-06-08/` against the rim save. Verify a single checker runs on a single turn with PASS/FAIL output and findings table.

**Validation:** Shows `## momentum_lifecycle: PASS (score: X.X)` or FAIL with findings table.

**Command:**
```bash
python scripts/debug/ev.py check 5 momentum_lifecycle --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

#### Step 2.3 — Multiple checkers on single turn

**What:** Run `ev.py check 5 momentum_lifecycle gm_beat_lifecycle inventory_integrity --save-dir saves/the-outer-rim--after-unification-2026-06-08/`. Verify multiple checkers run on a single turn.

**Validation:** Shows results for all three checkers with PASS/FAIL and findings.

**Command:**
```bash
python scripts/debug/ev.py check 5 momentum_lifecycle gm_beat_lifecycle inventory_integrity --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

#### Step 2.4 — All deterministic checkers on single turn

**What:** Run `ev.py check 5 --all --save-dir saves/the-outer-rim--after-unification-2026-06-08/`. Verify all 11 deterministic checkers run on turn 5.

**Validation:** Shows results for all deterministic checkers. Some may be inconclusive if required fields are absent — this is expected.

**Command:**
```bash
python scripts/debug/ev.py check 5 --all --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

#### Step 2.5 — All checkers on all turns

**What:** Run `ev.py check --all --save-dir saves/the-outer-rim--after-unification-2026-06-08/`. Verify all deterministic checkers run across all 32 turns.

**Validation:** Shows per-turn results for all checkers. Sanitizer_lifecycle should work because rim save has sanitizer events at turns 5, 10, 15, 20, 25, 30.

**Command:**
```bash
python scripts/debug/ev.py check --all --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

#### Step 2.6 — Sanitizer lifecycle checker

**What:** Run `ev.py check 5 sanitizer_lifecycle --save-dir saves/the-outer-rim--after-unification-2026-06-08/`. Verify the sanitizer_lifecycle checker works with non-turn events and state access.

**Validation:** Shows sanitizer_lifecycle result. Turn 5 has a sanitizer event, so this should produce a meaningful result (not inconclusive).

**Command:**
```bash
python scripts/debug/ev.py check 5 sanitizer_lifecycle --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

---

## Implementation — Phase 3: LLM Checkers

### Context files to load
- `ccya/ev/checkers/_llm.py` (LLM infrastructure)
- `ccya/ev/checkers/llm_checkers.py` (directive_tone_match, beat_narrative_chain, state_fidelity)

### Detailed steps

#### Step 3.1 — LLM checkers appear in registry

**What:** Run `ev.py check --help` and verify the 3 LLM checkers (`directive_tone_match`, `beat_narrative_chain`, `state_fidelity`) appear with type "llm".

**Validation:** Shows all 3 LLM checkers in the registry listing.

**Command:**
```bash
python scripts/debug/ev.py check --help
```

#### Step 3.2 — Run LLM checkers on a turn

**What:** Run `ev.py check 5 --all --llm --save-dir saves/the-outer-rim--after-unification-2026-06-08/`. Verify LLM checkers run alongside deterministic checkers. If model fails to load, note as "skipped — model unavailable" rather than "failed."

**Validation:** Shows all deterministic checkers + 3 LLM checkers. LLM checkers may take longer due to model loading.

**Command:**
```bash
python scripts/debug/ev.py check 5 --all --llm --save-dir saves/the-outer-rim--after-unification-2026-06-08/
```

#### Step 3.3 — LLM checker model override

**What:** Run `ev.py check 5 directive_tone_match --llm --checker-model "some-model"`. Verify the `--checker-model` flag is accepted and used for LLM checker calls.

**Validation:** If model is available, runs with that model. If not, shows warning and continues without LLM checkers (as designed).

**Command:**
```bash
python scripts/debug/ev.py check 5 directive_tone_match --llm --checker-model "qwen3-35b"
```

---

## Implementation — Phase 4: Play Command

### Context files to load
- `ccya/ev/play.py` (play_turn, cmd_play, format_play_output, format_error_output)
- `ccya/engine/turn.py` (run_turn)
- `ccya/models.py` (TurnResult)

### Detailed steps

#### Step 4.1 — Single turn play

**What:** Run `ev.py play "Look around the spaceport"` to play a single turn via the engine. Verify structured output matches the design spec: Turn/trace header, ruling, narrative, momentum, actions, scene, deltas, errors, tokens.

**Validation:** Output shows all expected sections. Events file created in `saves/ev/<session>/events.jsonl`. Symlink `saves/ev/latest` points to the session.

**Command:**
```bash
python scripts/debug/ev.py play "Look around the spaceport"
```

#### Step 4.2 — Play with --no-sanitize

**What:** Run `ev.py play "Attack the guard" --no-sanitize`. Verify play works with sanitizer disabled.

**Validation:** Output shows no sanitizer events. Config sets `sanitize_every = 0`.

**Command:**
```bash
python scripts/debug/ev.py play "Attack the guard" --no-sanitize
```

#### Step 4.3 — Play session persistence

**What:** Verify that after a play session, events are written to `saves/ev/<session>/events.jsonl` and `saves/ev/latest` symlink exists.

**Validation:** `ls saves/ev/` shows a timestamped session directory and a `latest` symlink pointing to it.

**Command:**
```bash
ls -la saves/ev/
```

#### Step 4.4 — Play error handling

**What:** Run `ev.py play "I do nothing"` and verify structured error output if the engine encounters an issue. Verify non-zero exit code on errors.

**Validation:** If error occurs, output shows `Errors:` section with structured error info, not a raw traceback. Exit code is non-zero.

**Command:**
```bash
python scripts/debug/ev.py play "I do nothing"
echo "Exit code: $?"
```

---

## Implementation — Phase 5: Eval Command

### Context files to load
- `ccya/ev/eval.py` (cmd_eval_run, cmd_eval_list)
- `ccya/ev/scenario.py` (Scenario, ScenarioTurn, TurnAssert, load_scenario, discover_scenarios)

### Detailed steps

#### Step 5.1 — List scenarios

**What:** Run `ev.py eval list`. Verify it reports no scenarios found (since `evals/scenarios/` doesn't exist) or lists any existing scenarios.

**Validation:** Reports "No YAML scenarios found in evals/scenarios/" or lists available scenarios.

**Command:**
```bash
python scripts/debug/ev.py eval list
```

#### Step 5.2 — Create minimal test scenario

**What:** Create a minimal YAML scenario file at `evals/scenarios/test-spot-check.yaml` with 2 turns for testing.

**Validation:** File is valid YAML with required fields (id, pack, description, turns).

**Command:**
```bash
mkdir -p evals/scenarios
cat > evals/scenarios/test-spot-check.yaml << 'EOF'
id: spot-check
pack: default
description: Spot check scenario for ev-tooling verification
seed_overrides:
  meta.momentum: 0
turns:
  - input: "Look around the area"
    expects:
      - "explore"
  - input: "Try to pick the lock"
    expects:
      - "roll"
      - "dexterity"
EOF
```

#### Step 5.3 — Run eval scenario

**What:** Run `ev.py eval run evals/scenarios/test-spot-check.yaml`. Verify batch play of scenario turns, checker aggregation, and Markdown report output.

**Validation:** Report shows scenario metadata, checker results (PASS/FAIL), and session path. No raw tracebacks.

**Command:**
```bash
python scripts/debug/ev.py eval run evals/scenarios/test-spot-check.yaml
```

#### Step 5.4 — Eval with report file

**What:** Run `ev.py eval run evals/scenarios/test-spot-check.yaml --report /tmp/spot-check-report.md`. Verify report is written to file.

**Validation:** `/tmp/spot-check-report.md` exists and contains the Markdown report.

**Command:**
```bash
python scripts/debug/ev.py eval run evals/scenarios/test-spot-check.yaml --report /tmp/spot-check-report.md
cat /tmp/spot-check-report.md
```

#### Step 5.5 — Eval with specific checkers

**What:** Run `ev.py eval run evals/scenarios/test-spot-check.yaml --checkers "momentum_lifecycle,inventory_integrity"`. Verify only specified checkers run.

**Validation:** Report shows only momentum_lifecycle and inventory_integrity results.

**Command:**
```bash
python scripts/debug/ev.py eval run evals/scenarios/test-spot-check.yaml --checkers "momentum_lifecycle,inventory_integrity"
```

#### Step 5.6 — Cleanup test scenario

**What:** Remove the test scenario file.

**Validation:** `evals/scenarios/test-spot-check.yaml` no longer exists.

**Command:**
```bash
rm evals/scenarios/test-spot-check.yaml
```

---

## Implementation — Phase 6: Documentation Cleanup Verification

### Context files to load
- `scripts/debug/README.md`
- `docs/ev/CHECKERS.md`
- `docs/repomap.md`
- `ccya/eval/` (should be empty)
- `~/.config/opencode/skills/ev/` (should be a thin pointer or deleted)

### Detailed steps

#### Step 6.1 — Verify old eval dir is empty

**What:** Verify `ccya/eval/` contains only `__pycache__` (no Python source files). Verify `evals/rubrics/` is deleted. Verify `evals/scenarios/` Python files are deleted.

**Validation:** `ccya/eval/` has no `.py` files. `evals/rubrics/` does not exist.

**Command:**
```bash
find ccya/eval/ -name "*.py" -type f
find evals/rubrics/ -type f 2>/dev/null || echo "evals/rubrics/ does not exist (correct)"
```

#### Step 6.2 — Verify README.md covers new commands

**What:** Verify `scripts/debug/README.md` documents all 13 commands (summary, timing, turn, prompt, deltas, mechanics, state, diff, trace, search, play, check, eval) with usage examples.

**Validation:** README has sections for play, check, and eval commands with usage examples.

**Command:**
```bash
grep -c "ev.py play\|ev.py check\|ev.py eval" scripts/debug/README.md
```

#### Step 6.3 — Verify CHECKERS.md documents all checkers

**What:** Verify `docs/ev/CHECKERS.md` documents all 11 deterministic checkers + 3 LLM checkers with ID, type, fields, description, CLI examples, and caveats.

**Validation:** All 14 checkers documented. Each has type, fields, what it checks, CLI usage, and caveats.

**Command:**
```bash
grep -c "^### " docs/ev/CHECKERS.md
```

#### Step 6.4 — Verify repomap reflects ccya/ev/ structure

**What:** Verify `docs/repomap.md` documents the `ccya/ev/` package structure with all modules and their public APIs.

**Validation:** Repomap has entries for `ccya/ev/events.py`, `ccya/ev/inspect.py`, `ccya/ev/deltas.py`, `ccya/ev/state_tools.py`, `ccya/ev/play.py`, `ccya/ev/check.py`, `ccya/ev/eval.py`, `ccya/ev/scenario.py`, `ccya/ev/__init__.py`, `ccya/ev/checkers/__init__.py`, and all checker modules.

**Command:**
```bash
grep "ccya/ev/" docs/repomap.md | wc -l
```

#### Step 6.5 — Verify skill is a thin pointer or deleted

**What:** Verify `~/.config/opencode/skills/ev/` is either a thin pointer (pointing to repo docs) or deleted entirely.

**Validation:** If the directory exists, its content is a pointer to repo docs (`scripts/debug/README.md`, `docs/ev/CHECKERS.md`, `docs/architecture/ev-tooling.md`). If deleted, no error.

**Command:**
```bash
ls -la ~/.config/opencode/skills/ev/ 2>/dev/null || echo "ev skill dir does not exist"
```

---

## Status

`open`

## Notes for executor

- Run phases in order (1 through 6). Each phase is independent but earlier phases exercise infrastructure that later phases depend on.
- If an LLM backend is unavailable, skip Phase 3 steps 3.2 and 3.3, and note "skipped — no LLM backend."
- If the play command fails because no LLM is configured, note "skipped — no LLM configured" for Phase 4.
- Clean up any ephemeral test files created during testing (`saves/ev/` sessions, `evals/scenarios/test-spot-check.yaml`, `/tmp/spot-check-report.md`).
- Record results as PASS/FAIL/SKIPPED for each step. Do not modify code in this plan.
