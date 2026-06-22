---
title: "[State] Remove PLAYER_CONDITIONS_MAX mechanic"
status: done
created: 2026-06-17
labels:
  - Improvement
  - Tech Debt
---

PC_CONDITIONS_MAX (set to 5) caps concurrent player conditions by silently dropping the oldest when the cap is exceeded. This happens in delta_builder.py:264 with a hard slice `existing_conds[-PC_CONDITIONS_MAX:]` with no logging or user signal.

The mechanic is referenced across 6+ files: delta_builder.py, [audit.py](<http://audit.py>), conditions checker, repomap, rubric, checker docs, and multiple plan docs. Removing it eliminates silent data loss and simplifies the conditions pipeline.
