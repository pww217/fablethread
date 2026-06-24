---
title: "3 consecutive escalation beats — Exceeds 2-consecutive-same-type limit"
status: canceled
urgency: 3
size: small
created: 2026-06-12
labels:
  - Bug
  - World Building
---

## Bug

3 consecutive escalation beats at T10, T12, T13 — exceeds the 2-consecutive-same-type limit in the rubric.

## Evidence

Beat emissions from extraction.storytell.output in cordyceps-year-twenty-2026-06-11 save:
- T1: pressure, T2: opportunity, T3: complication, T4: pressure, T5: pressure, T6: pressure, T8: opportunity, T10: escalation, T12: escalation, T13: escalation, T16: complication, T18: pressure, T19: complication, T20: complication, T21: pressure, T27: opportunity

- beat_locked fires correctly at T6 (consecutive pressure: T3-T5 = 3, threshold=3) ✓
- beat_locked fires correctly at T21 (consecutive pressure: T18-T21 = 4) ✓
- **3 consecutive escalation beats at T10, T12, T13** — exceeds the 2-consecutive-same-type limit in the rubric ✓ (flagged)
- Beat variety: pressure=7, escalation=3, complication=3, opportunity=3, null=13 — no single type exceeds 60% ✓
- Null beats (13/33 = 39%) are common — storyteller not emitting beats on most turns

## Scope

* Investigate why 3 consecutive escalation beats fire
* Check if beat variety enforcement is working correctly
* Add checker for consecutive beat type violations

## Files

* `ccya/engine/extraction.py` — beat extraction
* `ccya/prompts/storyteller.j2` — storyteller prompt for beats
* `ccya/ev/checkers/` — GM beat lifecycle checker

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §3` — 3 consecutive escalation beats at T10, T12, T13 exceed 2-consecutive-same-type limit.
