# EV Tool Meta-Findings: UX Issues and Improvements

## Overview

During a full rubric-based evaluation of `saves/santa-monica-zero-hour-2026-06-15`, I ran every EV command and identified UX problems: repetition in output, bloat from compaction events, missing aggregate commands, and minor formatting bugs. This doc catalogs what to fix.

---

## Issue 1: `check --all` Output Repeats

**What happened:** Running `check --all` produced the full output ~15 times instead of once. Each checker's result section (PASS/FAIL + table) was printed verbatim on every repeat. The total output was ~500 lines for 27 checkers.

**Root cause:** Likely the checker runner iterates all checkers inside a nested loop that also iterates all checkers again, or the `--all` flag triggers multiple aggregation passes. Not investigated in depth.

**Fix:** The `check --all` path should run each checker once and accumulate results, printing a single summary table. Format:

```
Checkers: 24/27 PASS (88.9%)
FAIL: thread_lifecycle, sanitizer_lifecycle, goal_update_validity
```
Plus an optional `--verbose` flag for per-checker detail.

---

## Issue 2: Compaction Events Bleed into All Commands

**What happened:** Compaction events (empty `ruling`, empty `narrate`, empty `scene_phase`) appear as separate rows in every tabular command. Examples:

- `prompt-sizes`: Shows rows with all-zeros for compaction events (T3, T5, T8, T9, T10, T13, T14, T15 — 8 of 29 events are compaction noise)
- `convergence`: Used to show empty-phase rows (fixed in this session)
- `phase-transitions`: Used to show transitions to/from empty phase (fixed in this session)

**Fix:** All EV commands should filter compaction events by default (events where `ruling` is empty dict or `tokens_in == 0`). Add a `--include-compaction` flag if users want to see them.

---

## Issue 3: No Checker Summary at a Glance

**What happened:** `check --all` prints each checker's result on its own line, but there's no:
- PASS/FAIL count
- Score average
- Grouping by domain (beats, threads, pacing, NPCs, etc.)

I had to manually count PASS/FAIL from the output.

**Fix:** Add a summary header to `check --all`:
```
Checkers: 24/27 PASS (88.9%)  |  Average score: 0.89
  Pacing:     6/6 PASS
  Threads:    2/5 FAIL (thread_lifecycle, sanitizer_lifecycle)
  Inventory:  2/2 PASS
  Beats:      2/2 PASS
  ...
```

---

## Issue 4: `rolls` Shows Dead Momentum Column

**What happened:** The `rolls` command shows a `Momentum` column that always displays `?` for convergence-era saves. Momentum was removed from the engine — this column is dead weight.

**Fix:** Remove the momentum column from `cmd_rolls`. The command should show: `Turn | Band | Raw | Final | Difficulty`. A `--legacy` flag could restore momentum for old saves.

---

## Issue 5: No Band Distribution Summary

**What happened:** To get roll band distribution (how many crit_fail/fail/setback/partial/success/crit_success), I had to write a Python script. Neither `rolls` nor any other command provides a summary.

**Fix:** Add a `rolls --summary` flag that prints:
```
Band distribution (17 rolls):
  crit_fail:   1  (5.9%)
  fail:        6  (35.3%)
  setback:     4  (23.5%)
  partial:     2  (11.8%)
  success:     4  (23.5%)
  crit_success: 0  (0.0%)
Bad total: 64.7%
```

---

## Issue 6: `convergence` Can't Retro-Compute Score

**What happened:** For pre-convergence saves (no `convergence_components`), the command shows `?` for all components. The score is present in events (from old engine) but components aren't. There's no way to retroactively compute what the components *would* have been — I had to do it manually for the report.

**Fix:** Add a `--estimate` mode to `convergence` that computes the 5 components from available event data (thread_urgency_count, scene_age, recent_beats, ruling.band) for saves that lack `convergence_components`. This lets users see how convergence would have behaved on old saves.

---

## Issue 7: No Thread Resolution Rate Command

**What happened:** To get "threads resolve in 2.3 turns avg with 85.7% resolution rate," I had to write custom Python. No EV command gives a thread lifecycle summary.

**Fix:** Add a `threads --summary` flag that computes:
- Total threads created / resolved
- Average turns from creation to resolution
- Threads hallucinated (updated but never created)
- Threads pending (created but not yet resolved)

---

## Issue 8: `goals` Formatting

**What happened:** The `goals` command output is sparse — it shows `(no goal changes found)` when no sanitizer events have goal changes, but the extraction fallback (added in this session) does produce output. When it does produce output, the formatting is wide and hard to scan:

```
   14 | 
      → Navigate toward the Wilshire Blvd perimeter...
```

The empty `before` column is from the extraction fallback path — it always shows blank because extraction doesn't have a "before" value.

**Fix:** For extraction-fallback goals (no `before`), show the source turn in the goal text: `[T14 extraction] → Navigate toward...`

---

## Issue 9: `check --list` Requires a Save

**What happened:** `ev.py check --list` exits with `Error: saves/default/events.jsonl not found` because it tries to load a default save. The `--list` flag should just list checkers from the registry without loading any data.

**Fix:** `--list` should early-return after printing the registry. It doesn't need events to enumerate checkers.

---

## Issue 10: No Per-Scene or Per-Phase Aggregation

**What happened:** To understand CLIMAX duration, thread resolution by scene, or phase timing, I had to manually map turn numbers to scenes. No command provides scene-level aggregation.

**Fix:** Add `--by-scene` flag to relevant commands (`convergence`, `phase-transitions`, `curtain-call`) that groups output by scene (detected by location changes or phase resets).

---

## Summary

| # | Issue | Severity | Status | Fix |
|---|---|---|---|---|
| 1 | `check --all` output repeats | HIGH | **RESOLVED** | Single pass, summary header with domain breakdown |
| 2 | Compaction events in tabular output | HIGH | **PENDING** | Filter by default, `--include-compaction` flag |
| 3 | No checker summary | MEDIUM | **RESOLVED** | PASS/FAIL count, domain breakdown, avg score in `check --all` |
| 4 | `rolls` momentum column dead | LOW | **RESOLVED** | Removed column |
| 5 | No band distribution summary | MEDIUM | **RESOLVED** | Added `rolls --summary` |
| 6 | No retroactive convergence estimation | LOW | **RESOLVED** | Added `convergence --estimate` |
| 7 | No thread resolution rate | MEDIUM | **RESOLVED** | Added `threads --summary` |
| 8 | `goals` formatting sparse | LOW | **RESOLVED** | Shows `[extraction]` label for fallback goals |
| 9 | `check --list` requires save | HIGH | **RESOLVED** | Early return without data loading |
| 10 | No per-scene aggregation | LOW | **PENDING** | Add `--by-scene` flag |

Total: 10 issues (8 RESOLVED, 2 PENDING)
