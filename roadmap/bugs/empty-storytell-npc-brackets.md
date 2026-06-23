---
title: Empty NPC presence brackets in storytell stream
status: validated
created: 2026-06-23
resolved: 2026-06-23
labels:
  - eval
  - prompt
  - engine
---
**Reproduction context:** `evals/runs/latest` (noir-1930s, opportunist, 25 turns). All 37 NPC entries across all 25 turns in the storytell stream render as `**Name** []` instead of `**Name** [PRESENT]`.

**Root cause:** `build_npc_roster()` in `npc_roster.py:72` with `slim=True` omitted the `presence` field from the NPC dict. The `_npc_roster.j2` template unconditionally renders `[{{ n.presence | upper }}]`, so the bracket was empty.

**Fix:** Added `"presence": presence` to the slim-mode dict at `npc_roster.py:77`. Docstring updated to reflect the change.
