---
title: "Goal_update format mismatch — Storyteller emits free-form text, sanitizer requires structured dict"
status: done
created: 2026-06-12
labels:
  - Bug
  - World Building
---

## Bug

Storyteller emits `goal_update` as free-form narrative text (e.g., "The community has pivoted from debating medicine scarcity to executing an illicit trade for grain."), but the sanitizer at `ccya/engine/thread_sanitizer.py:217-223` requires it to be a dict with `visible_goal`/`goal_context` fields. The sanitizer silently drops free-form strings, which is why `applied.arc_update` is empty and `visible_goal` never updates from storyteller output.

## Evidence

* T2: storyteller goal_update ≠ state visible_goal (format mismatch, not data mismatch)
* T5: storyteller goal_update ≠ state visible_goal (same root cause)
* T25: storyteller goal_update ≠ state visible_goal (same root cause)

## Scope

* Fix sanitizer to handle free-form goal_update text from storyteller
* Add structured goal_update format to storyteller prompt
* Add validation that goal_update format matches sanitizer expectations

## Files

* `ccya/engine/thread_sanitizer.py` — goal_update handling (lines 217-223)
* `ccya/prompts/storytell_system.j2` — storyteller prompt
* `ccya/ev/checkers/arc_goals.py` — arc goal updates checker

## Validation

**Bug description not confirmed as originally claimed.** Source analysis shows the reported failures (T2, T5, T25) were false positives from the checker, not pipeline bugs:

1. **Root cause mismatch** — The sanitizer at `thread_sanitizer.py:217-223` validates its *own* LLM output, not the storyteller's. The storyteller's `goal_update` bypasses the sanitizer entirely and is applied directly at `turn.py:1195-1196`. No sanitizer drop was occurring.
2. **Checker false positives** — The `arc_goal_updates` checker compared the storyteller's new `goal_update` against `state_snapshot.arc.visible_goal`, but `state_snapshot` is intentionally **pre-turn state** (`turn.py:1391` comment: "Snapshot pre-turn state before overwriting — used by delete_last_turn"). A new goal_update will always differ from the old visible_goal — the checker was flagging legitimate goal updates as failures.
3. **Compaction events** — Sanitizer compaction events (no `state_snapshot` key) sit between turn events in the log. The initial cross-turn fix used `i+1` which landed on compaction events. Fixed to skip events without `state_snapshot` when looking for the next real turn event.

**Fix applied:** Rewrote `arc_goal_updates` in `ccya/ev/checkers/arc_goals.py` to:

* Compare storyteller's `goal_update` at turn T against the *next real turn event's* `state_snapshot` (skipping compaction/sanitizer events)
* Skip verification when `arc_resolve` happened in the same turn (supersedes `goal_update`)
* Verified PASS (score 1.0) against cordyceps save — all 3 goal_updates at T2, T5, T25 correctly propagated to state
