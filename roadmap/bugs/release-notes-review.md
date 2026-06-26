---
title: "Release Notes Need Review — Wrong Game Name, Accuracy Check"
status: new
urgency: 2
size: medium
created: 2026-06-26
labels:
  - docs
  - release
---

## Problem

The release notes at `docs/releases/0.29.0.md` need review for two issues:

1. **Wrong game name.** CCYA is a codename. The release notes use CCYA (and presumably other codename-derived names) where the actual game name should appear. Find and fix all instances.

2. **Accuracy check.** The notes were auto-generated from commit messages and may mischaracterize changes, miss important context, or contain errors. Verify each section against the actual code changes.

## Files to Touch

- `docs/releases/0.29.0.md` — fix game name, correct inaccuracies

## Progress

All 35 release notes (0.1.0 → 0.30.0) regenerated via script on 2026-06-26 with:
- Correct release dates from git tag creation dates
- Correct git range filtering (prev_tag..tag) instead of all commits up to tag
- Deduplication within each file
- Internal/doc-only commit filtering (merge commits, plan cleanups, chore:, docs:)

### Notes
- No game name to use — just omit it or say "the game"
- Regeneration script saved at `/tmp/regenerate_releases.py` (reusable for future corrections)
