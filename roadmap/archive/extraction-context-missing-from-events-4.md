---
title: "extraction_context missing from events — 4 checkers fail on every turn"
status: canceled
created: 2026-06-12
labels:
  - Bug
  - Tooling
---

## Bug

4 checkers fail on every turn because `extraction_context` doesn't exist in this save's events:
- `inventory_integrity` — requires `extraction_context.location_this_turn`
- `conditions_lifecycle` — requires `extraction_context.conditions_this_turn`
- `npc_presence` — requires `extraction_context`
- `pacing_directives` — requires `extraction_context`

This save uses `changes` key instead of `extraction_context`. The `ev.py check --all` command fails for these 4 checkers on every turn with "required field not found."

## Evidence

- 4 checkers fail on every turn in cordyceps-year-twenty-2026-06-11 save
- Save uses `changes` key instead of `extraction_context`
- `ev.py check --all` fails for these 4 checkers

## Scope

* Determine if this is a save format version issue or engine bug
* Update checkers to handle both `changes` and `extraction_context` keys
* Add engine output for `extraction_context` if missing

## Files

* `ccya/ev/checkers/` — checker implementations
* `ccya/engine/extraction.py` — extraction output format
* `ccya/ev/` — [ev.py](<http://ev.py>) check command

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §4` — 4 checkers fail on every turn because extraction_context doesn't exist, save uses changes instead.
