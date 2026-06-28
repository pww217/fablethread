---
title: "[User-Reported] Highlighting/UI Rendering Issues"
status: testing
urgency: 4
size: small
created: 2026-06-24
ticket_id: B-10
labels:
  - ui
  - highlighting
  - frontend
---

## Problem

Multiple highlighting/rendering issues in the main game UI:

1. **Seed narration highlighting broken** — Seed turn narration not being highlighted at all
2. **Character names lowercased in narration** — Named characters appear lowercased in turn narration (should preserve proper casing)
3. **Non-roll check reason tooltip broken** — Ruling reason for non-roll checks renders outside tooltip (not as tooltip, visible inline)
4. **Numeric words in NPC names highlighted** — "Two dockworkers" highlights "Two" as NPC partial match (should exempt one..ten)

## Root Cause (Issue 1 & 4)

**Jinja2 operator precedence bug** in `ccya/templates/index.html:2596`:

```jinja
{{ state if state else {} | tojson | safe }}
```

Parses as: `state if state else ({} | tojson) | safe` — when `state` is truthy, outputs **raw Python dict** (single quotes, `True`/`False`/`None`) instead of valid JSON.

`JSON.parse()` fails silently in try/catch, so `_highlightEntities()` never runs on **any** narrative (seed or regular turns).

This was introduced in PR4 (`7bc2bb1`) when the template was modified.

## Fix Applied (Issue 1 & 4)

**JSON bug:** Changed line 2596 to:
```jinja
{{ (state if state else {}) | tojson | safe }}
```

**Numeric words exemption:** Added `numericWords` Set in `_highlightEntities()` (`index.html:2168`) to skip partial matches for "one" through "ten" when splitting NPC/PC names into first/last parts. Full names still match (e.g., "Two dockworkers" matches, but "Two" alone doesn't).

## Consolidation

The highlighting pipeline is **already consolidated** — both seed opening narration and regular turn narrations use the same `_highlightEntities()` function via `initial-state` JSON:
- **Seed/opening**: `DOMContentLoaded` handler + HTMX `afterSwap` for `#opening-block`
- **Regular turns**: streaming (`narrative_token`), `phase` (`narrate_done`), `turn_complete` event

No duplication exists — both paths were broken by the same JSON bug.

## Impact

- Fixes highlighting for NPCs (red), inventory items (blue), PC name (green), locations (orange) in **all** narrative blocks
- Partial matching for NPC/PC names (first/last name) preserved
- Full-name matching for items/locations preserved
- Numeric words (one..ten) no longer trigger partial NPC/PC highlights

## Fix Applied (Issue 2 — Character name lowercasing)

**Reproduced in narration output:** Model uses lowercase descriptive forms ("the notched-ear marine", "the old navigator") instead of proper names from state ("Notched-Ear Marine", "Old Navigator").

**Prompt fix:** Strengthened `narrate_system.j2` NPC NAMING rule to require exact proper name capitalization from Characters section, forbid lowercase descriptive aliases.

## Remaining (Separate Issue)

Item 3 in original ticket is **unrelated**:
- Non-roll tooltip — CSS/template issue in ruling display