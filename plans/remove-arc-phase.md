# Plan: Remove ArcPhase (campaign phase tracking)

**Status:** Active  
**Date:** 2026-05-17  

---

## Problem

`ArcPhase` is a tracking label with zero downstream effect. The engine never reads `arc.phase` to change any behavior — no different prompts, no mechanical changes, no conditional logic. It's surfaced only in two places:
- A single line in the narrator prompt (`**Phase:** setup`) that gives the LLM context it doesn't use differently based on value.
- The UI state panel for human reading.

The phase never advances because there are no engine-side gates and the LLM instruction ("only include if visibly shifted") provides an easy out every turn. Building advancement logic would just make a more accurate label — nothing else changes.

**Verdict:** Tear it all out. It's tracking theater.

---

## Changes

### 1. `ccya/models.py` — Remove ArcPhase enum and field

- Delete lines 22-27 (`ArcPhase` class with SETUP/PURSUIT/REVERSAL/CRISIS/RESOLUTION)
- Remove `phase: ArcPhase = ArcPhase.SETUP` from `CampaignArc` (line 81)

### 2. `ccya/prompts/sections/_arc.j2` — Remove phase line

Delete line 6:
```jinja2
**Phase:** {{ current_arc.phase or 'setup' }}
```

### 3. `ccya/templates/_state_left.html` — Remove arc phase display

- Delete lines 101 and 104 (the `{% set _arc_phase %}` line and the `<span>Arc: Phase ...</span>` span)

### 4. `ccya/state/delta.py` — Remove phase merge logic

Delete lines 47-49 in `_merge_arc_update()`:
```python
current_phase = arc.get("phase")
if au.phase and au.phase.value != current_phase:
    arc["phase"] = au.phase.value if hasattr(au.phase, "value") else str(au.phase)
```

### 5. `ccya/prompts/generate_seed_system.j2` — Remove phase from schema guidance

- Line 54 (schema): remove `, phase: string` and `hidden_truths: string[], discovered_truths:` → reorder to keep consistent
- Line 58 (arc output schema): same removal  
- Line 120 (`## Campaign Arc Generation`): delete `- phase: always "setup"`

### 6. Tests — Remove `"phase": "setup"` from all fixtures

- `tests/test_compactor.py`: lines 741, 773
- `tests/integration/test_arc.py`: all occurrences (lines 26, 61, 97, 138, 183, 233, 260, 297, 339, 396) — these are all in arc fixture data
- `tests/integration/conftest.py`: line 267

### 7. Any other files that reference ArcPhase or phase on CampaignArc

Search for remaining references and remove. Likely none if #1 is done first (will cause import errors that surface them).

---

## What stays untouched

- **`CampaignArc` model itself** — all fields except `phase` remain. Threads, truths, engagement scoring, visible_goal, thematic_question, pc_drive are all used.
- **Thread lifecycle logic in `engine/turn.py`** — `_apply_thread_signals`, `_candidate_to_latent_thread` — these use arc data but not phase.
- **`tick_arc()` in `ccya/engine/arc.py`** — engagement scoring doesn't depend on phase.
- **Plan 03 (plan_03_arc_health.md)** — about thread staleness tracking, unrelated to phase.

---

## Verification

After changes:
1. `make check` — no import errors for ArcPhase, mypy clean
2. `make test` — all tests pass with `"phase"` removed from fixtures
3. Verify that a fresh seed (new game) generates without any arc phase field in state
4. Verify that an existing save file with `"phase": "setup"` still loads (the merge logic no longer writes it, but old saves may have it — `state/io.py` should tolerate the extra key since CampaignArc validation only applies to narrator-emitted updates, not raw state loading)
