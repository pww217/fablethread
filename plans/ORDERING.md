# Master Ordering — All Plans & Efforts

## Purpose

This document orders every active plan, design doc, and finding effort for the ccya repository by dependency and concern. It is not an implementation plan itself; it defines what each phase aims to do, in what order, and why that ordering minimizes wasted effort and merge conflicts.

**Principle: structural removal first, then rebuild on top of new state.**

---

## Resolved Conflicts & Misalignments

### Conflict 1 — `recent_events_compact` vs compactor safety plan (RESOLVED)
- **What:** `world-state-history-redesign-design.md` removes `recent_events_compact` from the compactor. `fix-extraction-context-and-compactor-safety.md` Phase 02 changes `_build_extraction_context()` which reads `scene.recent_events`.
- **Resolution:** Both phases of fix-extraction-context are already implemented in source code (atomic write at `compactor.py:390`, deepcopy+apply_delta at `extraction.py:85-86`). Phase 1b removed from ordering entirely. No conflict remains.

### Conflict 2 — Eval coverage vs recent_events removal
- **What:** `eval-coverage-gaps.md` Phase 1 includes "recent_events turn-stamp auto-checker" which gets deleted by world-state redesign.
- **Resolution:** World-state redesign runs first. The eval-phase-1 step for this checker is removed from the ordering (marked as superseded).

### Conflict 3 — `_apply_thread_signals()` changes overlap (RESOLVED)
- **What:** `02-thread-lifecycle.md` modifies `_apply_thread_signals()` with urgency decay logic; world-state redesign adds outcome processing in a different function.
- **Resolution:** No conflict — these are separate functions. Outcome processing goes into `_apply_thread_resolutions()` at turn.py:360 (processes thread_resolve). Urgency decay stays in `_apply_thread_signals()` at turn.py:159 (handles thread_advance/progress/completion/threshold/cooldown).

### Conflict 4 — `ThreadResolution.outcome` vs thread lifecycle progress tracking
- **What:** Both plans add fields to ArcThread model (`outcome` from world-state, `urgency_set_turn` from thread-lifecycle).
- **Resolution:** No conflict. Different fields on same model; both additive.

---

## Design Decisions Applied (from user review)

1. **No hard cap on `world_state_add` per turn** — never. No Python-level enforcement now or later. Rely solely on prompt constraint.
2. **Completed thread outcomes visible in Narrator prompt** — `narrate_user.j2` renders `arc.completed_threads` with outcome sentences, adding continuity for the narrator at cost of additional tokens. Outcome processing goes into `_apply_thread_resolutions()` (turn.py:360), not `_apply_thread_signals()`.

---

## Ordering Overview

```
Phase 0: World-State History Redesign (structural removal + rebuild)
   │
   ├── Phase 1a: ev1-fixes/03-beat-timing-observability (independent, observability-only)
   ├── Phase 2: ev1-fixes/01-prompt-alignment (builds on new prompt structure from Phase 0)
   │
   Phase 3: Thread Lifecycle Fixes (key-branch + urgency decay — depends on turn.py changes in Phase 0)
   │
   Phase 4: Eval Coverage Gaps (detection layer; runs against fixed code)
   │
   Phase 5: Documentation Cleanup (updates all docs after structural changes are complete)
```

**Total phases:** 6 (1 structural removal, 1 independent observability fix, 1 prompt alignment, 1 thread lifecycle fix cluster, 1 eval harness update, 1 documentation cleanup). Note: `fix-extraction-context-and-compactor-safety.md` changes are already implemented in source code; Phase 1b removed from ordering.

---

## Phase-by-Phase Breakdown

### Phase 0: World-State History Redesign
**Source:** `plans/completed/world-state-history-redesign/`
**Status:** committed — 3 sub-phases (A/B/C) implemented.
**What it does:**
- Removes `recent_events` entirely (~20 removals across models, state, delta logic, compaction, prompts, UI) — old save files with this key do not load; no migration function
- Promotes `world_state` to mutable tiered structure (`WorldStateFact` with `permanent`/`persistent` tiers). Currently world state is a static dict set at seed time that cannot be modified after initialization. Now individual facts can be added/modified without overwriting the entire state. Tier rules: permanent facts come from seed generation and persist indefinitely (immutable, never touched by LLM or apply_delta); persistent facts are set by engine/LLMs during play and survive compaction indefinitely — LLM removes stale facts via world_state_remove when no longer relevant.
- Adds mandatory `outcome: str` field to `ThreadResolution`, stored on completed threads. One sentence per outcome is sufficient — no need for multi-sentence summaries or structured resolution data. Old save files with threads lacking this field fail validation on load; no migration function.
- Makes completed thread outcomes visible in both Storyteller and Narrator prompts (user decision #2)
- Removes inventory durability gate (was `recent_events_add OR actions`, now removed entirely — had more false positives than true positives)
- Always shows world_state to Storyteller (removes `{% if not all_threads %}` gate)

**Why first:** This is a structural removal that changes model shapes, state schema, and prompt templates. All other plans either depend on the new state shape or fight over fields this plan removes.

### Phase 1a: Beat Timing Observability (independent of world-state changes)
**Source:** `plans/completed/ev1-fixes/03-beat-timing-observability.md`
**Status:** committed in 0496f92.
**What it does:**
- Documents one-turn beat lag as intentional design in `_narrate_setup()` comment
- Adds `"raw_total"` to events.jsonl ruling dict serialization (turn.py)
- Adds `dice` subcommand to ev.py CLI tool with formatted dice table and summary row

**Why independent:** No model changes, no state schema changes. Pure observability/debugging improvements.
**Can run in parallel with Phase 0.**

### Phase 2: Prompt Alignment for Beat Type Selection, Null Emission, and Fail Near-Miss Guidance (builds on new prompt structure)
**Source:** `plans/completed/ev1-fixes/01-prompt-alignment.md`
**Status:** committed in bf91554.
**What it does:**
- Documents directive/band priority rule at top of band-aligned beat selection section in storyteller_system.j2
- Adds near-miss exception to fail/setback beat guidance (storytell_system.j2)
- Adds null emission cadence guidance — at least once per 4 turns (storytell_system.j2)
- Adds null-beat fallback instruction to narrator prompt (narrate_system.j2, _arc.j2)

**Why after Phase 0:** World-state redesign changes storyteller_system.j2 JSON schema and adds completed_threads section. Prompt alignment should build on the new structure rather than fight over old template state.

### Phase 3: Thread Lifecycle Fixes — Key-Branch Black Hole + Urgency Decay + Scene-Scoped Management (partial dependency on world-state changes)
**Source:** `plans/completed/ev1-fixes/02-thread-lifecycle.md`
**Status:** committed in 2eaf4af.
**What it does:**
- **Step 3.0 — Key-branch fix (can run in parallel with Phase 0):** Add fallthrough after the collision check at `turn.py:1275-1295` inline in `run_turn()`, so scene-scoped threads with keys that pass the collision check proceed to normal thread-add logic at line 1301. This step is independent of world-state redesign — it fixes a critical bug in a different code section of turn.py.
- **Step 3.1:** Add `urgency_set_turn: int | None = None` field to ArcThread model; assign during seed generation and LLM thread_add
- **Step 3.2:** Extend progress tracking to scene-scoped threads (remove scope=arc filter in `_apply_thread_signals()`)
- **Step 3.3:** Wire urgency decay into `_apply_thread_signals()` — demote urgent→normal→background after threshold turns; add silent expiration for stale scene threads

**Why Phase 0 first, except Step 3.0:** Steps 3.1-3.3 depend on world-state redesign because ArcThread model changes (outcome field) and `_apply_thread_resolutions()` modifications must be in place before urgency decay logic is layered on top of the same function family. Note: outcome processing goes into `_apply_thread_resolutions()` at turn.py:360, not `_apply_thread_signals()` — these are separate functions handling different concerns.
**Resolves C1, C2, C3, C4, C7.**

### Phase 4: Eval Coverage Gaps — Detection Layer Against Fixed Code (runs against fixed state)
**Source:** `plans/completed/eval-coverage-gaps.md`
**Status:** committed in ccfc8da.
**What it does:**
- **Phase 1 (modified):** Universal asserts for orphan conditions, thread_add→state application check, beat-type variety warning, surface_as consistency. *Supersedes:* recent_events turn-stamp auto-checker (removed — superseded by world-state redesign).
- **Phase 2:** Judge rubrics additions: surface flag consistency section, verb variety assessment, skill coverage assessment, thread progress cross-reference table.
- **Phase 3:** Dedicated eval scenario exercising ev1/ev2 findings with seed_overrides and turn definitions.

**Why last:** Detection layer should run against fixed code to validate that fixes actually resolved the issues. No production code changes — purely harness updates.

### Phase 5: Documentation Cleanup (runs after all phases complete)
**Source:** `plans/completed/05-documentation-cleanup.md`
**Status:** completed — all 9 doc files updated and committed in 4733979.
**What it does:** One pass over docs/repomap.md, docs/architecture/OVERVIEW.md, and architecture subdocs (delta-validate.md, step2c-progress.md, out-of-band.md, campaign-arcs.md) plus AGENTS.md "Navigation path" — remove references to deleted fields (`recent_events`, `recent_events_evicted`), update ArcThread model description (add urgency_set_turn, two-stage latency for scene threads), update world_state tiered structure, fix apply_delta return type.

**Why last:** Documentation depends on knowing what changed across ALL phases. Running it earlier risks missing cross-phase documentation updates or updating docs for code that hasn't been committed yet.

## Dependency Graph (textual)

```
world-state-history-redesign ──┐
                               ├──► beat-timing-observability (independent, parallel with Phase 0)
                               │   ├──► key-branch fix (turn.py:1275 — independent of world-state changes)
                               │   └──► urgency decay + scene-scoped management (depends on ArcThread changes from Phase 0)
                               │
                               ├──► prompt-alignment (builds on new storyteller_system.j2 structure)
                               │
                                └──► eval-coverage-gaps (detection against fixed code; recent_events step removed)
```

---

## What Each Phase Resolves (Finding Mapping)

| Finding | Severity | Addressed By |
|---|---|---|
| C1 — Key-branch black hole | CRITICAL | Phase 3, Step 3.0 |
| C2 — Progress=0 scene-only | MEDIUM-HIGH | Phase 3, Step 3.2 |
| C3 — Missing added_turn on seeded threads | HIGH | Phase 3, Step 3.1 |
| C4 — Urgency never auto-decays | HIGH | Phase 3, Step 3.3 |
| C5 — Band-beat misalignment on PARTIAL outcomes | CRITICAL | Phase 2 (directive/band priority rule) + Phase 0 (completed thread outcomes improve context) |
| C6 — Fail near-miss prompt contradiction | MEDIUM | Phase 2 (near-miss exception guidance) |
| C7 — Scene threads excluded from lifecycle management | MEDIUM-HIGH | Phase 3, Steps 3.2+3.3 |
| C8 — Beat expiration dead code | MEDIUM | No fix planned; deferred |
| C9 — Compacted bullets reference removed threads | MEDIUM | Addressed implicitly by Phase 3 key-branch fix + compactor changes in Phase 0 |
| C10 — One-turn beat lag | LOW-MEDIUM | Addressed as intentional design (documented, not fixed) in Phase 1a |
| C11 — raw_total not persisted | LOW | **Phase 1a** (adds `raw_total` to events.jsonl ruling dict serialization) |
| C12 — Compactor thread removal semantics undocumented | MEDIUM | Addressed by Phase 0 world_state section rendering improvements |
| C13 — Silent directive degradation post-compaction | HIGH | Addressed implicitly by Phase 3 (threads won't be silently dropped) + Phase 0 completed threads provide fallback context |
| C14/C2 — Compactor removes seeded thread | MEDIUM-HIGH | Addressed implicitly by Phase 3 key-branch fix |
| C15/C17 — Narrator blind to recent_events | CRITICAL | **Phase 0** (resolved by removal; completed thread outcomes visible in narrator prompt provide continuity) |
| C16/C18 — Storytell blind to world_state | HIGH | **Phase 0** (world_state always shown, conditional gate removed) |

---

## Out-of-Scope Findings (No Plan Exists)

The following ev2 findings have no corresponding plan and are not addressed by any phase above:
- **C8 — Beat expiration dead code:** Zero null beats observed; fixing requires storyteller to emit `gm_beat: null` which is a prompt change with unknown downstream effects. Deferred.

---

## Conflict Resolution Summary

| Original Conflict | Resolution |
|---|---|
| `recent_events_compact` removal vs compactor safety plan reads recent_events | fix-extraction-context changes already implemented in source (compactor.py:390, extraction.py:85-86); Phase 1b removed from ordering entirely. Plan doc status mismatch noted — should be moved to `/plans/completed/`. |
| Eval coverage step checks recently removed field | Superseded step removed from Phase 4 ordering |
| `_apply_thread_signals()` changes overlap between plans | No conflict — outcome processing goes into `_apply_thread_resolutions()` at turn.py:360; urgency decay stays in `_apply_thread_signals()` at turn.py:159. These are separate functions handling different concerns. |
| ArcThread model changes from multiple plans | No conflict — different fields (`outcome` vs `urgency_set_turn`) both additive |

## Execution Risks (Not Conflicts)

### fix-extraction-context status mismatch (informational)
- **What:** `fix-extraction-context-and-compactor-safety.md` has status `open`, but changes are already present in source code: atomic write at `compactor.py:390`, deepcopy+apply_delta pattern at `extraction.py:85-86`. Phase 1b was removed from ordering entirely.
- **Action:** Plan doc should be moved to `/plans/completed/` or status updated to reflect implementation is done.

### apply_delta return value change (blocks-execution in Phase 0)
- **What:** `turn.py:1203` unpacks as `state, recent_events_evicted = apply_delta(...)` expecting `(dict, bool)`. World-state redesign removes the evicted boolean from both `delta_builder.apply_delta()` and `delta.apply_delta()`, changing return to just `dict`.
- **Affected call sites (all must be updated):**

| Location | Line(s) | Current usage | Required change |
|---|---|---|---|
| `ccya/state/delta.py` | 30+ | `apply_delta()` returns `(state, recent_events_evicted)` | Return just `dict` |
| `ccya/state/delta_builder.py` | 123+, 362 | `apply_delta()` returns `(state, evicted)` | Return just `dict` |
| `ccya/engine/turn.py` | 965-966 | Local vars: `recent_events: list[...] = []`, `recent_events_evicted: bool = False` | Remove both declarations |
| `ccya/engine/turn.py` | 1203 | Unpacking: `state, recent_events_evicted = apply_delta(...)` | Single assignment: `state = apply_delta(...)` |
| `ccya/engine/turn.py` | 1536-1543 | Passes both `recent_events=...` and `recent_events_evicted=...` to TurnResult constructor | Remove both arguments (and the local var at line 965) |
| `ccya/engine/extraction.py` | 86 | Unpacking: `post_state, _evicted = apply_delta(...)` | Single assignment: `post_state = apply_delta(...)` |
| `ccya/models.py` | 437, 450 | Dataclass fields: `recent_events`, `recent_events_evicted` | Delete both from TurnResult dataclass |
| `ccya/server/routes.py` | 189 | JSON response includes `result.recent_events_evicted` only (not the full recent_events list) | Remove evicted field from JSON payload |
| `templates/index.html` | 1396-1408 | If evicted: show prune warning toast. Else: render `_buildTurnChanges()`. Both branches affect UI flow after outcome badges. | Restructure to always render changes (remove the if/else on evicted flag); also remove recent_events rendering logic since it no longer exists in state |

### apply_delta parameter removal (blocks-execution in Phase 0)
- **What:** `turn.py:1205` passes `recent_events_max=config.recent_events_max` to apply_delta(). World-state redesign removes this parameter and the config key simultaneously.

### recent_events UI rendering removals (blocks-execution in Phase 0)
- **What:** Several templates render deleted fields that must be removed alongside apply_delta changes:
| Location | Line(s) | Current usage | Required change |
|---|---|---|---|
| `ccya/templates/_state_right.html` | 2 | `{% set _recent = state.scene.recent_events or [] %}` — renders recent events in state sidebar | Delete the variable and all downstream rendering using `_recent` |
| `ccya/templates/_turn_viewer.html` | 100-101 | Shows `t.sanitization.recent_events_compact_count` compaction info row | Remove entire `<template x-if>` block (compaction field deleted) |

### recent_events_compact removal (blocks-execution in Phase 0)
- **What:** Compactor has dedicated logic for merging similar events (`recent_events_compact`). This is a separate data structure from `scene.recent_events` but both get deleted. Remove this aspect of compaction entirely — chronicling-based compaction stays:
| Location | Line(s) | Current usage | Required change |
|---|---|---|---|
| `ccya/models.py` | 346 | `recent_events_compact: list[CompactorRecentEventCompact] = Field(default_factory=list)` in CompactorSanitization dataclass | Delete field (and the CompactorRecentEventCompact model if unused elsewhere) |
| `ccya/engine/compactor.py` | 120, 128, 133, 154 | Reads/writes sanitization.recent_events_compact; logs compact count in sanitization dict | Remove compaction logic and the "recent_events_compact_count" key from sanitization output. Do NOT remove chronicling-based compaction — that stays intact. |
| `ccya/prompts/compact_system.j2` | 58, 74, 80, 129-132 | Prompt instructs LLM to produce recent_events_compact JSON; includes example output with this field | Remove all references and examples for recent_events_compact from prompt. Do NOT remove chronicling compaction instructions — those stay intact. |
