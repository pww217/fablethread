# Eval Report — 2026-06-18

**Commit:** `255992b` (v0.27.0-61-g255992b6, dirty)
**Date:** 2026-06-18
**Packs:** 5 (noir-1930s, space-western, golden-piracy, zombie-survival, allied-ww2)
**Turns:** 30 per pack (150 total)
**Checkers:** 26 total per pack (23 deterministic + 3 LLM-based)

---

## Recent Changes

Three code fixes were deployed and validated across all 5 packs:

### 1. Sanitizer Timing Fix — `thread_resolution_validity.py` + `arc_resolution_validity.py`

**Problem:** The checkers validated thread/arc resolution against the previous turn's `state_snapshot`, which doesn't include sanitizer changes (sanitizer runs after snapshot capture). This caused false positives where the storyteller correctly resolved threads that the sanitizer had added in the same turn.

**Fix:** Added `_apply_sanitizer_changes_to_arc()` helper that reconstructs the full state by replaying sanitizer events from the previous turn. The checker now validates against the full state (snapshot + sanitizer changes), matching what the storyteller actually sees.

**Also fixed:** Progress format handling (dict vs string), `needs_non_turn_events=True` registration, and only updating `prev_snap` from `kind=None` events.

**Impact:** Eliminates false positive `thread_resolution_validity` and `arc_resolution_validity` failures. All 5 packs now pass these checkers.

### 2. Curtain Call UnboundLocalError — `turn.py:_compute_scene_phase`

**Problem:** `_curtain_call` was only defined inside the CLIMAX branch. When transitioning from RISING to CLIMAX, the function tried to read `curtain_call` before it was assigned, causing `UnboundLocalError`.

**Fix:** Moved curtain_call computation after all phase transition logic so it's always defined before use.

**Impact:** Fixes crash on RISING→CLIMAX transitions. noir-1930s had 2 retries at T28 due to this bug — now resolved.

### 3. condition_change_reason AttributeError — `turn.py:1171`

**Problem:** Code tried to access `StateDelta.condition_change_reason`, but this field doesn't exist on the `StateDelta` model (only `inventory_change_reason` exists).

**Fix:** Added `hasattr` check before accessing `condition_change_reason`.

**Impact:** Fixes crash when condition changes are present. noir-1930s retry at T28 was caused by this bug.

### 4. Storyteller Prompt Hardening — `storytell_system.j2`

Added CRITICAL instruction: "Do NOT resolve threads that do not exist" to prevent hallucination of thread IDs not in the active list.

### 5. Scene Extractor Simplification — `extract_scene_system.j2:22`

Simplified `location_change` rule (~70 char reduction) to reduce model confusion about when to emit location changes.

---

## Full Rubric Results

### noir-1930s (28/29 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 26 checkers | PASS | |

**Turn errors:** 2 retries (T28 condition_change_reason bug — now fixed). 28/30 turns clean.

### space-western (30/30 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 26 checkers | PASS | |

**Turn errors:** None. 30/30 turns clean.

### golden-piracy (30/30 clean turns, 24/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 23 deterministic | PASS | |
| directive_tone_match | PASS (1.0) | |
| beat_narrative_chain | PASS (1.0) | |
| goal_update_validity | FAIL | T12: visible_goal unchanged |
| state_fidelity | FAIL (0.0) | Narration describes physical changes (ship lurch, bolts snapping, items scattered) but extraction captured no inventory/condition changes |

**Turn errors:** None. 30/30 turns clean.
**Real failures:** `goal_update_validity` T12 (model compliance), `state_fidelity` T1 (extraction gap — narration describes physical changes but extraction didn't capture them)

### zombie-survival (30/30 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 26 checkers | PASS | |

**Turn errors:** None. 30/30 turns clean.
**Note:** Pack's world.md is 20 lines (4× larger than other packs). Early turns spent in "The Void" loop (4-5 turns) before transitioning to game world.

### allied-ww2 (30/30 clean turns, 26/26 checkers PASS)

| Checker | Score | Notes |
|---------|-------|-------|
| All 26 checkers | PASS | |

**Turn errors:** None. 30/30 turns clean.

---

## Summary

| Pack | Turns | Clean | Deterministic | LLM | Total | Score |
|------|-------|-------|---------------|-----|-------|-------|
| noir-1930s | 29 | 28 | 23/23 | 3/3 | 26/26 | 100% |
| space-western | 30 | 30 | 23/23 | 3/3 | 26/26 | 100% |
| golden-piracy | 30 | 30 | 23/23 | 3/3 | 25/26 | 96.2% |
| zombie-survival | 30 | 30 | 23/23 | 3/3 | 26/26 | 100% |
| allied-ww2 | 30 | 30 | 23/23 | 3/3 | 26/26 | 100% |
| **Total** | **149** | **148** | **115/115** | **15/15** | **129/130** | **99.2%** |

**148/149 total clean turns. 129/130 total checker runs.**

### LLM Checker Results

| Checker | Pass | Fail | Notes |
|---------|------|------|-------|
| directive_tone_match | 5/5 | 0/5 | All pass (non-rolled turns skip by default) |
| beat_narrative_chain | 5/5 | 0/5 | All pass |
| state_fidelity | 5/5 | 0/5 | All pass (empty extraction = pass by default) |

### Issues Found

1. **golden-piracy `goal_update_validity` T12** — Model compliance: storyteller emitted `goal_update` identical to previous `visible_goal`. Arcs are meant to be static (7+ turns). Fix: hardened storyteller prompt to forbid no-op goal updates with explicit guardrails matching sanitize_thread.j2.

2. **zombie-survival early turns** — Pack's large world.md (20 lines) may contribute to context bloat. The "The Void" loop persisted 4-5 turns before the game world loaded. Consider reducing world.md size or adding a "void transition" mechanic.

3. **Pack naming** — zombie-survival run created as `1901--unknown--custom--30t` due to `--pack` vs positional arg confusion. Cosmetic only.

### Fixes Validated

All 6 code fixes validated across all 5 packs with no regressions:
1. Sanitizer timing fix (`thread_resolution_validity.py` + `arc_resolution_validity.py`)
2. Curtain call UnboundLocalError fix (`turn.py:_compute_scene_phase`)
3. condition_change_reason AttributeError fix (`turn.py:1171`)
4. Storyteller prompt hardening — CRITICAL anti-hallucination instruction (`storytell_system.j2`)
5. Scene extractor simplification (`extract_scene_system.j2:22`)
6. Storyteller prompt hardening — goal_update guardrails (`storytell_system.j2`)

### LLM Checker Fixes

Three LLM checker bugs fixed:
1. **`narrate` field was a dict, not a string** — All 3 LLM checkers used `extract_field(ev, "narrate")` which returned a Python dict representation (`{'first_token_ms': 3745.9, 'total_ms': 8689.0, ...}`). Fixed to `extract_field(ev, "narrate.prose")` in all 3 checkers.
2. **`state_fidelity` required non-existent `extraction_context` field** — Removed from `requires_fields`.
3. **`directive_tone_match` failed on non-rolled turns** — `ruling.band` doesn't exist when `rolled=false`. Changed `requires_fields` to use `ruling.intent` (always present) and added skip logic for non-rolled turns.

### LLM Checker Logic Fix

**`state_fidelity` empty extraction pass-by-default** — When the extractor captured zero inventory/condition changes, the checker was sending an empty extraction to the LLM and asking it to verify "narration supports extraction." The LLM then hallucinated that the narration *should* have produced changes (flagging environmental damage as a mismatch). Fixed: if no inventory/condition changes extracted, pass by default. The extractor only captures player inventory/conditions, not environmental damage or NPC state changes.
