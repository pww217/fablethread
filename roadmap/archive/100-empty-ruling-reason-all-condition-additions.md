---
title: "100% empty ruling.reason — All condition additions have empty ruling.reason"
status: done
urgency: 3
size: small
created: 2026-06-12
labels:
  - Bug
  - Extraction
---

## Bug

100% of condition additions have empty `ruling.reason` — all 11 condition adds have empty `ruling.reason` text. The ruling prompt requires "Always include `reason` explaining why (≤10 words)" (`ccya/prompts/ruling_system.j2:44,75`). Without reason text, condition IDs can't satisfy the rubric check that "Condition IDs appear in ruling's reason text."

## Evidence

- 11 condition additions in cordyceps-year-twenty-2026-06-11 save
- All 11 have empty ruling.reason
- Violates rubric contract

## Scope

* Investigate why ruling prompt is not generating reason text
* Check if ruling prompt template requires reason correctly
* Add validation in checkers for non-empty ruling.reason

## Files

* `ccya/prompts/ruling_system.j2` — ruling prompt template (lines 44,75)
* `ccya/engine/extraction.py` — ruling extraction
* `ccya/ev/checkers/` — condition lifecycle checker

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §5b` — 100% of condition additions have empty ruling.reason, violating rubric contract.
