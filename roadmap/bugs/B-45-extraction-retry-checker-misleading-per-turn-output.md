---
title: "extraction_retry_rates falsely flags every turn — session-level metric duplicated per-turn"
status: done
urgency: 2
size: xs
created: 2026-07-13
ticket_id: B-45
labels: ["checker"]
design:
plan:
pr:
  url:
  branch:
---

## Description

`extraction_retry_rates` is a session-level checker (it requires all events to compute a retry rate across the full run). When `ev.py check <save-dir> 1 --all` runs, `cmd_check` passes the full events list to ALL checkers for each turn. The checker finds retries in the T21 event and returns a FAIL result. Since `cmd_check` runs the same checkers for each turn in `--all` mode, the SAME global result gets displayed under every turn number.

Result: `extraction_retry_rates` appears as FAIL under T1, T2, T3... T25 — identical result every time, even though only T21 had a real retry.

## Root Cause

`cmd_check` (check.py) iterates all events for every turn in `--all` mode, but `extraction_retry_rates` is inherently session-level and needs the full event list. The metadata system had no way to mark this distinction.

## Fix

Added `requires_all_events` flag to checker metadata (`ccya/ev/checkers/__init__.py`). Checkers marked with this flag are skipped when running `ev.py check <turn> --all` (since the per-turn display would be misleading). The checker still runs and shows correctly when checking the full session without specifying a turn.

- `ccya/ev/checkers/__init__.py`: Added `requires_all_events` to `CheckerMeta`, `register_checker()`
- `ccya/ev/check.py`: Filter out `requires_all_events` checkers when `turn is not None and checker_ids is None`
- `ccya/ev/checkers/extraction_retry_rates.py`: Marked with `requires_all_events=True`

## Verification

- Checked T21 with `--all`: 38 checkers shown (extraction_retry_rates hidden), all PASS
- Checked full session with `--all` (no turn): 39 checkers shown, extraction_retry_rates appears correctly
- Listed checkers: `ev.py check --list` includes `requires_all_events` metadata

### Live verification (B-45)

- Noir-1930s 5-turn run: per-turn `--all` shows 38 checkers, extraction_retry_rates hidden ✓
- Full session `--all` shows 39 checkers, extraction_retry_rates shown and PASS ✓
- No extraction retries in this run (38/39 PASS except ruling_band_distribution, expected for 5 turns)