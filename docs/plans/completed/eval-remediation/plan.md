# Eval Remediation Plan — Top Wins

**Goal:** Fix the top 2 biggest wins from eval findings, plus eval pack turn-0 start.
**Target:** Improve Mechanical score from 3/5 to 4/5, reduce auto-checker failures.

---

## Phase 1: Compactor recent_events compaction

**Problem:** Compactor does not compact `recent_events`. The ring buffer in `apply_delta()` caps at 20 but does not consolidate — events accumulate verbatim, losing narrative cohesion.

**Full spec:** `[compactor-recent-events.md](compactor-recent-events.md)`

**Summary of changes:**

- **`models.py`** — Add `CompactorRecentEventCompact` model; add `recent_events_compact` field to `CompactorSanitizationResult`
- **`compact_system.j2`** — Add Part 3: recent_events compaction instructions (consolidate similar events, aim to halve count, keep key facts narratively)
- **`compact_user.j2`** — Add `## RECENT EVENTS` section showing current events
- **`compactor.py`** — Pass recent_events to prompt; apply `recent_events_compact` in `maybe_compact()` to replace the entire list
- **`test_compactor.py`** — Remove `test_does_not_touch_recent_events` and `test_no_recent_events_instruction`; add 3 new tests

---

## Phase 2: Enforce quest deduplication in progress extractor

**Problem:** Creates overlapping quest IDs (`deliver_ledger_to_inn`, `caron_debt`, `secure_silk_shipment`) instead of updating existing quests. Splits quest state, dilutes narrative focus.

**Full spec:** `[quest-dedup.md](quest-dedup.md)`

**Summary of changes:**

- **`extract_progress_system.j2`** — Strengthen quest dedup rule (line 23); add explicit "NEVER create" examples with real IDs from eval runs
- **`extract_examples.yaml`** — Add 2 few-shot examples showing correct quest dedup behavior
- **`extract_progress_user.j2`** — No changes needed (active_quests already shown with IDs)

---

## Phase 3: Fix eval pack turn-0 start

**Problem:** Eval pack `seed_state.yaml` has `meta.turn: 1` instead of `meta.turn: 0`. First eval turn is labeled as turn 2.

**Full spec:** `[eval-pack-turn-0.md](eval-pack-turn-0.md)`

**Summary of changes:**

- **`seed_state.yaml`** — Change `meta.turn: 1` to `meta.turn: 0`
