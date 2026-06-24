---
title: "[UI] Unify roll and non-roll outcome badges into single element"
status: done
urgency: 4
size: medium
created: 2026-06-15
labels:
  - Improvement
  - UI
---

## Detail

The turn log renders two separate outcome elements:

1. **Roll outcome badge** (function `_buildRollBadge` / `_turn_log.html:11-40`): When `ruling.rolled` is true - shows dice, skill, difficulty, math, band result, and optional outcome_summary
2. **Non-roll outcome badge** (inline at `index.html:1827-1843` / `_turn_log.html:203-207`): When `ruling.rolled` is false but `outcome_summary` exists - shows just outcome_summary in a `roll-badge--outcome` with optional tooltip

These should be a single unified outcome element that handles both rolled and non-roll cases.

## Scope

* **In scope:** Merge the two outcome rendering paths into one element
  * Server-rendered: `_turn_log.html` and `index.html` Jinja templates
  * Client-rendered: `_buildRollBadge()` and the inline non-roll outcome block in `index.html`
  * CSS: consolidate `.roll-badge--outcome` and `.roll-outcome--large` into the unified element
* **Out of scope:** Changes to ruling data model, prompt changes

## Systems Affected

* `ccya/templates/_turn_log.html` - server-rendered turn log
* `ccya/templates/index.html` - server-rendered narrative + client-side `_buildRollBadge()` and inline outcome
* `ccya/static/app.src.css` - outcome badge styling (lines 1771-1775+)
