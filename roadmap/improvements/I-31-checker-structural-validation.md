---
title: "Checker structural validation (ev.py check --lint)"
status: canceled
urgency: 3
size: medium
created: 2026-07-06
ticket_id: I-31
labels: [ev-tool, checkers]
---

# I-31: Checker Structural Validation (`ev.py check --lint`)

## Summary

Add `ev.py check --lint` to validate checker logic itself — catch dead code, variable shadowing, logic errors in checkers before they cause false results in eval runs.

## Problem

During E-11 deep dives, `phase_transition_signals` checker had a critical structural bug: a nested `if i > 0:` that shadowed all elif chains, making the elif blocks dead code. Only caught via manual logic tracing, not by running checkers.

This is a systemic risk — checkers are self-documenting code with no validation layer.

## Proposed Solution

`ev.py check --lint` (or `ev.py lint`) that:

1. **Dead code detection** — finds unreachable branches, shadowed variables, dead code in checker logic
2. **Logic validation** — validates checker invariants (e.g., "all phase transitions must be checked", "no silent returns")
3. **Structure checks** — validates checker structure matches expected interface

## Scope

- Static analysis of checker files in `ccya/ev/checkers/`
- Report findings, don't auto-fix
- Low urgency — this is a one-off fix per checker so far

## Related

- E-11: Found `phase_transition_signals` dead code bug
- `ccya/ev/checkers/pacing_convergence.py:113-126` — the dead code example
