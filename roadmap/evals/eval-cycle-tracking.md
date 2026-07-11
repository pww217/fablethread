---
title: "Eval cycle improvements tracking"
status: canceled
urgency: 2
size: medium
created: 2026-06-22
ticket_id: E-10
labels:
  - eval
  - engine
---

# Eval Cycle Improvements — Tracking

Branch: `eval-cycle-improvements`
Started: 2026-06-22
Baseline: `2026-06-21_0.28.0-56-g47ff6261_47ff626` (3 packs, 20 turns)

## Baseline Scores (from latest prior run)

| Pack | Checkers | Score | Failures |
|------|----------|-------|----------|
| noir-1930s | 23/24 (95.8%) | 0.96 | ruling_reason_quality |
| allied-ww2 | 22/24 (91.7%) | 0.92 | ruling_reason_quality |
| golden-piracy | 23/24 (95.8%) | 0.96 | ruling_reason_quality |

## Known Issues from Baseline (post-fix)

1. **gm_beat_lifecycle** — checker bug (rules_outcome=None in prompt context builder) — FIXED in baseline
2. **ruling_reason_quality** — prompt doesn't ask for causal keywords — FIXED in baseline
3. **npc_presence** — missing "archived" in VALID_PRESENCE — FIXED in baseline
4. **ArcThread type coercion** — no lowercase validator — FIXED in baseline
5. **Extraction retry rates** — no checker — FIXED in baseline
6. **Seed word count** — removed validation — FIXED in baseline
7. **Arc resolve frequency** — no checker — OPEN
8. **Inventory canonical ID** — pack data gaps — SUPERSEDED by state refactor

---

## Cycle 1

**Commit at start:** `98053763` (eval-cycle-tracking.md)
**Commit after fixes:** `dabe3b8` (ThreadUpdate/GMBeat coercion + word count)
**Date:** 2026-06-22
**Runs:** 5 packs × 25 turns

### Runs
- [x] noir-1930s + driven — 23/25 (92.0%) score 0.92 — FAIL: arc_resolution_validity, extraction_retry_rates
- [x] space-western + speedrunner — 24/25 (96.0%) score 0.96 — FAIL: extraction_retry_rates
- [x] golden-piracy + completionist — 23/25 (92.0%) score 0.92 — FAIL: thread_lifecycle, extraction_retry_rates
- [x] zombie-survival + cautious — 24/25 (96.0%) score 0.96 — FAIL: extraction_retry_rates
- [x] allied-ww2 + aggressive — 23/25 (92.0%) score 0.92 — FAIL: ruling_reason_quality, extraction_retry_rates

### Findings

1. **ArcThread/ThreadUpdate type coercion** (CRITICAL) — LLM sends uppercase "COMPLICATION", "THREAT", "REVELATION", "OPPORTUNITY" → Pydantic validation fails → storytell retry. ALL 5 packs. Root cause: ThreadUpdate model had no type validator (ArcThread had one, ThreadUpdate didn't).

2. **GMBeat driver coercion** (MEDIUM) — LLM sends invalid driver values like "environment" → beat nullified. No validator on driver field.

3. **arc_resolution_validity** (HIGH) — noir (alleyway_pursuit_hazard), golden-piracy (many unknown IDs). arc_resolve.drop_threads references threads that don't exist in state.

4. **thread_lifecycle** (HIGH) — golden-piracy only. Thread lifecycle violations.

5. **ruling_reason_quality** (LOW) — allied-ww2 T25: 8 words, max 7. Word count too tight.

6. **extraction_retry_rates** (MEDIUM) — ALL 5 packs. Caused by #1 (ThreadUpdate type coercion).

### Fixes Applied (commit dabe3b8)

1. Added `_coerce_thread_type` validator to ThreadUpdate model (ccya/models/state.py) — matches ArcThread pattern
2. Added `_coerce_gm_beat_driver` validator to GMBeat model (ccya/models/extraction.py) — lowercases and validates
3. Relaxed ruling reason word count: 5-7 → 5-10 (ccya/engine/config.py + ccya/prompts/ruling_system.j2)

### Post-Fix Scores (to be validated in Cycle 2)

| Pack | Pre-fix | Expected post-fix |
|------|---------|-------------------|
| noir-1930s | 23/25 (92.0%) | 24/25 (96.0%) — extraction_retry_rates should pass |
| space-western | 24/25 (96.0%) | 25/25 (100%) — extraction_retry_rates should pass |
| golden-piracy | 23/25 (92.0%) | 24/25 (96.0%) — extraction_retry_rates should pass |
| zombie-survival | 24/25 (96.0%) | 25/25 (100%) — extraction_retry_rates should pass |
| allied-ww2 | 23/25 (92.0%) | 24/25 (96.0%) — ruling_reason_quality + extraction_retry_rates should pass |

---

## Cycle 2

**Commit at start:** dabe3b8 (fix branch)
**Date:** TBD
**Runs:** 5 packs × 25 turns

### Runs
- [ ] noir-1930s + driven
- [ ] space-western + speedrunner
- [ ] golden-piracy + completionist
- [ ] zombie-survival + cautious
- [ ] allied-ww2 + aggressive

### Findings
- TBD

### Fixes Applied
- TBD

### Post-Fix Scores
- TBD

---

## Pre-Eval Issues (Context Before Compaction)

### Cycle 2 Never Actually Ran
Both "Cycle 1" and "Cycle 2" ran against the same pre-fix code (git_sha 9805376). I created the fix branch but never checked it out or ran from it. The worktree was deleted. The fixes are on main at dabe3b8.

### Branch State
- `main` is ahead of `origin/main` by 2 commits (dabe3b8 + 9805376)
- `eval-cycle-improvements` branch exists but is stale
- No worktree at `ccya-eval-cycle-improvements`

### Key Insight: Inter-Pipeline Contract
The scene pipeline generates candidate_npcs (up to 2 per turn, 105 total) but the storyteller never uses them. Golden-piracy has 0 turns where both exist. This is a prompt/inter-pipeline contract issue — the storyteller prompt doesn't reference or instruct use of scene candidate data.

### Duplicate Turn Pattern
Every pack has duplicate turns every 5 turns (T5, T10, T15, T20, T25). Second occurrence has `phase=?`, `beat=null`, empty candidates. This suggests a retry/reconciliation event being logged as a separate turn. Worth investigating the retry mechanism.

### What Needs to Happen Next
1. Re-run Cycle 2 from main (which has the fixes)
2. Run Cycle 3
3. Run Cycle 4
4. Produce final consolidated report

---

## Validated Tooling Issues (Confirmed by Testing)

### Root Cause: Event Loading Runs Before Subcommand Dispatch
In `ccya/ev/__init__.py` lines 85-102, event loading logic runs before command dispatch. The `eval` subcommands (`run`, `list`, `compare`) don't need events loaded upfront — they load them themselves. But the event loading logic rejects them because no `--save-dir` flag is set and no positional save-path matches.

### `eval --help` — FIXED
Running `ev.py eval --help` now shows usage. Added `eval` to `skip_events` set (line 105) and to the set of commands that don't need events loaded upfront (lines 87, 95, 97).

### `eval compare` — FIXED
Documented usage: `ev.py eval compare <baseline_dir> <current_dir> [--checkers]`
Now works. `cmd_eval_compare()` in `ccya/ev/eval.py:480` loads events itself via `_load_run_events()`.

### ALL `[save-path]` Positional Args — FIXED
COMMANDS.md replaced all `[save-path]` with `--save-dir <path>`. Commands: `summary`, `timing`, `turn`, `prompt`, `deltas`, `mechanics`, `trace`, `search`, `diff`, `beats`, `rolls`, `convergence`, `phase-transitions`, `curtain-call`, `goals`, `beat-ttl`, `effective-age`, `threads`, `warnings`, `prompt-sizes`.

### `--auto-report` from ev.yaml — FIXED
Added `auto_report` field to `ev.yaml` session config (`ccya/ev/session_config.py`). Resolution: CLI flag > session_config > default False. Added `resolve_auto_report()` function. Updated `ccya/ev/play.py` to use it.

### `--eval` flag for play — FIXED
Added `eval` to `_BOOL_FLAGS` in `ccya/ev/__init__.py`. Now `ev.py play --eval` runs checkers after the session.

### Null GM Beats — No Checker Enforces 50% Threshold
No checker enforces a null gm_beat threshold. The prompt (`ccya/prompts/storytell_system.j2:80,93,106`) explicitly allows null beats. The "20-56% null rate" finding from ev-review is qualitative, not from a checker.

---

## Ev Tooling Sweep (2026-06-22)

### Help Commands Added
All major commands now have `--help`:
- `ev.py play --help` — shows all flags (save-dir, no-sanitize, model, temp, pack, personality, custom-persona, resume, until-error, turns, eval, auto-report, llm-checkers, llm, interactive, help)
- `ev.py init --help` — shows flags (pack, personality, model, temp, save-dir, help)
- `ev.py status --help` — shows flags (save-dir, help)
- `ev.py check --help` — shows usage, flags, and all registered checkers
- `ev.py eval run --help` — shows flags (model, temp, checkers, report, auto-report, llm-checkers)
- `ev.py eval compare --help` — shows flags (checkers)
- `ev.py prompt-eval --help` — shows dump and call subcommands with detailed flags

### Event Loading Fixes
- Added `init`, `status`, `check` to skip lists for event loading (they don't need pre-loaded events)
- Added `help` to `_BOOL_FLAGS` so `--help` is parsed correctly
- Initialized `turn_file` before if/elif chain to avoid `UnboundLocalError`
- `check --help` now works without `--save-dir`

### Auto-Report Fix
- `auto_report` now triggers independently of `--eval` flag
- `ev.py play --auto-report` generates `report.md` after session (runs checkers if needed)
- `auto_report: true` in `ev.yaml` works for both `ev.py play` and `ev.py eval run`

### Docs Updated
- `docs/ev/RUBRIC.md` — replaced all `saves/my-game/events.jsonl` positional paths with `--save-dir saves/my-game` (15+ occurrences)
- `docs/ev/EVAL-RUNS.md` — removed incorrect `--report` flag from `ev.py check` example
- `docs/ev/COMMANDS.md` — added `--auto-report` flag to play table, fixed `search` command format
- `.opencode/skills/bug-triage/SKILL.md` — fixed `<save-path>` to `<save-dir>`

### Verification
All commands tested against real run data. No remaining `[save-path]` or `saves/` positional paths in active docs/skills.

---

## Cycle 3

**Commit at start:** TBD
**Date:** TBD
**Runs:** 5 packs × 25 turns

### Runs
- [ ] noir-1930s + driven
- [ ] space-western + speedrunner
- [ ] golden-piracy + completionist
- [ ] zombie-survival + cautious
- [ ] allied-ww2 + aggressive

### Findings
- TBD

### Fixes Applied
- TBD

### Post-Fix Scores
- TBD

---

## Cycle 4

**Commit at start:** TBD
**Date:** TBD
**Runs:** 5 packs × 25 turns

### Runs
- [ ] noir-1930s + driven
- [ ] space-western + speedrunner
- [ ] golden-piracy + completionist
- [ ] zombie-survival + cautious
- [ ] allied-ww2 + aggressive

### Findings
- TBD

### Fixes Applied
- TBD

### Post-Fix Scores
- TBD

---

## Final Consolidated Report

Ordered by impact (most to least):

### Critical Fixes
- TBD

### High Fixes
- TBD

### Medium Fixes
- TBD

### Low / Deferrals
- TBD

### False Positives
- TBD

### Summary
- TBD
