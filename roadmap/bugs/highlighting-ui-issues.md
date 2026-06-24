---
title: "[User-Reported] Highlighting/UI Rendering Issues"
status: new
created: 2026-06-24
labels:
  - ui
  - highlighting
  - frontend
---
## Problem

Multiple highlighting/rendering issues in the turn viewer:

1. **Seed narration highlighting broken** — Seed turn narration not being highlighted at all
2. **Character names lowercased in narration** — Named characters appear lowercased in turn narration (should preserve proper casing)
3. **Non-roll check reason tooltip broken** — Ruling reason for non-roll checks renders outside tooltip (not as tooltip, visible inline)

## Root Cause Estimate

- Highlighting pipeline (`ccya/server/turn_reviewer.py` or frontend highlighter) not running on seed turn
- Character name casing lost during narration generation or rendering pipeline
- Tooltip rendering logic for non-roll rulings placing content in wrong DOM position

## Impact

- Poor first-turn UX (no highlighting, lowercased names)
- Ruling reasons for non-roll checks hard to read / visually broken

## Suggested Fix

1. Ensure seed turn narration passes through same highlighting pipeline as storyteller turns
2. Preserve character name casing through narration generation → rendering pipeline
3. Fix tooltip positioning for non-roll ruling reasons (likely CSS or template issue in turn reviewer)