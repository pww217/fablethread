# Eval System — Fixes & Auto-Checker Additions

> Auto-checker gaps identified from live game data analysis (noir 25 turns, byzantium 31 turns). These are checks that should be added to `ccya/eval/universal_asserts.py` or the eval runner (`runner.py`) to detect issues the current system misses.
>
> **Root cause**: The sanitizer is an LLM-driven periodic cleanup mechanism (runs every N turns) with no explicit instructions about temporal decay of background threads, and no event-driven goal pivot triggers. The eval system validates mechanical correctness but does NOT measure responsiveness or accumulation over time.

---

## Issue #3 — Goal Stagnation

### What the current system checks
- `check_goal_update_applied` (universal_asserts.py:847) — If storytell emitted a `goal_update`, verifies it appears in state_snapshot.arc.visible_goal. Compares exact string match. Yellow severity.

### What's missing
The only existing check validates that an **emitted** goal update was applied to state. It does NOT detect when the visible_goal should have changed but didn't — i.e., stagnation detection is absent entirely.

### Auto-checker additions needed

#### 3a. `check_goal_stagnation` (Yellow)
Count turns between consecutive sanitizer-driven goal changes from events.jsonl sanitizer records (`goal_changed: true/false`). Flag if lag exceeds threshold (>5 turns). This measures the sanitizer's responsiveness directly from live data, not just validating that emitted updates were applied.

**Implementation**: Parse all `kind: "sanitizer"` events in turn_events, count turns between consecutive `goal_changed: true` records. If gap > 5 turns (configurable), emit warning with detail showing which goal was stale and for how long.

#### 3b. `check_narrative_pivot_goal_lag` (Yellow)
When a major narrative event occurs (location_change, thread_resolve, significant inventory_add with named items like manifests/evidence/weapon), flag if no sanitizer-driven goal_update follows within 2 sanitizer cycles (~10 turns). This is the actual metric that matters for player experience — not whether the sanitizer ran correctly, but whether it was responsive to what happened.

**Implementation**: Track events.jsonl entries with `applied.location_change`, `kind: "sanitizer"` resolved_threads, and significant inventory_adds (items named in narrative like "manifests", "evidence_photo"). Cross-reference against sanitizer turn numbers to compute lag. Flag if > 2 cycles without goal change after pivot event.

#### 3c. Sanitizer event validation
No auto-checker validates sanitizer output structure or correctness at all currently. The sanitizer writes structured records (`{"kind": "sanitizer", ...}`) but nobody checks whether the reported changes actually match what's in state after the sanitizer turn.

**Implementation**: After each sanitizer turn, compare pre-sanitizer and post-sanitizer state snapshots to verify:
- `threads_updated` IDs exist with updated fields in new state
- `threads_resolved` IDs moved from threads[] to completed_threads[]  
- `goal_changed: true` → visible_goal actually changed between turns

---

## Issue #5 — Background Thread Accumulation

### What the current system checks
- `check_thread_update_id_valid` (universal_asserts.py:419) — Validates that thread_update signals from storytell reference IDs existing in state_snapshot.arc.threads. Red severity.
- `check_thread_add_applied` (universal_asserts.py:794) — Verifies that when storytell emits a non-null thread_add, the thread ID appears in next turn's state. Red severity.

### What's missing
No check counts how many inactive (`active=False`) threads accumulate over time, measures average age of stale threads, or validates that background/latent cleanup is happening as expected by the sanitizer design (02-thread-lifecycle.md Steps 2.5-2.6).

### Auto-checker additions needed

#### 5a. `check_inactive_thread_age` (Yellow)
Count threads with `active=False` in the active list (`threads[]`) and flag any older than N turns (configurable, default 8-10). This directly measures the accumulation problem observed in byzantium where `broken_defense`, `looting_scourge`, `coinage_panic` sat inactive for 20+ turns.

**Implementation**: For each turn's state_snapshot.arc.threads, compute age = current_turn - last_updated_turn (or current_turn if last_updated_turn is None). Flag any thread with active=False and age > threshold. Report count of stale threads per game session.

#### 5b. `check_accumulating_threads` (Yellow)
Track the total number of inactive (`active=False`) threads in the active list over time. If this count monotonically increases without ever decreasing, flag as accumulation failure — background thread cleanup is not working at all.

**Implementation**: Maintain a running counter per game session: `inactive_count = sum(1 for t in state.arc.threads if not t.active)`. Flag if the counter never decreases over 20+ turns (i.e., no inactive thread was ever moved to completed_threads or removed). This is what happened with byzantium's three background threads — they went inactive at T5/T10 but were never cleaned up for 31 turns.

#### 5c. `check_thread_cap` (Yellow)
Flag if total active + inactive threads exceed a threshold (e.g., 8-10). This would naturally force the sanitizer to prioritize cleanup over new additions when thread count is high, and gives eval data about whether cap enforcement needs to happen at engine level vs prompt level.

**Implementation**: Compare `len(state.arc.threads) + len(state.arc.completed_threads)` against threshold (default 8-10). Flag if exceeded with detail showing which threads are stale background entries that should have been cleaned up.

---

## General Eval Gaps

### Sanitizer events not validated at all
The sanitizer writes structured records to events.jsonl (`kind: "sanitizer"`) but no universal assert validates them. This is a systemic gap — the sanitizer's internal validation (Pydantic models, warning logs) exists but nobody checks whether its output was correct from an eval perspective.

**Recommendation**: Add `check_sanitizer_event_structure` to validate that sanitizer events have consistent structure (`threads_updated`, `threads_resolved`, `threads_added`, `goal_changed`, `changes_detail`). This is a basic sanity check — if the sanitizer crashes or produces malformed records, it should be caught immediately in eval runs.

### No metric for thread lifecycle health
There's no aggregate view of how well the thread system is managing its state over time:
- How many threads are resolved per 10 turns? (should correlate with new thread creation)
- What's the average age of completed_threads before they're pruned by TTL (`thread_memory_ttl`)?
- Are background/latent demotions happening at expected intervals (5 turns normal→background, 10 background→latent)?

**Recommendation**: Add a post-run analysis step that computes these aggregate metrics and flags games where thread lifecycle health is poor (e.g., resolution rate < new creation rate over 20+ turn sessions).

---

## Related Findings

- **Issue #3 root cause**: [PRIORITIES#3](./PRIORITIES.md#3-g3j--goal-stagnation--sanitizer-too-slow-to-pivot-mh) → [FINDINGS-JUNE-6#G3](./FINDINGS-JUNE-6.md#g2---goal-stagnation--sanitizer-too-slow-to-pivot-confidence-h)
- **Issue #5 root cause**: [PRIORITIES#5](./PRIORITIES.md#5-bz1o4--background-thread-accumulation-without-decay-mh) → [FINDINGS-JUNE-6#BZ1](./FINDINGS-JUNE-6.md#bz1-h-background-threads-accumulate-forever-without-decay) → [BUGS-OBSERVATIONS#O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent)

## What to fix first (engine vs eval)

The root causes identified here are **in the engine/prompt layer**, not the eval layer:
1. Sanitizer template needs explicit cleanup instructions for stale threads (`sanitize_thread.j2`)
2. Goal pivot mechanism may need event-driven triggers, not just periodic sanitizer runs
3. Thread decay mechanisms (02-thread-lifecycle.md) may not be wired correctly

The eval additions above are **diagnostic tools** — they will catch these issues in future game sessions so they don't go unnoticed again. But fixing the root causes requires changes to `thread_sanitizer.py` and its prompt template, plus possibly new pipeline hooks for event-driven goal updates.
