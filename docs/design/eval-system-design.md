# Eval System Design

## Purpose

This document defines the target state for the CCYA eval system: checkers, CLI tooling, and report generation. It is the design authority for plans implementing checker additions, removals, or structural changes.

**Prerequisite:** The prompt separation design at `docs/design/prompt-separation-design.md` must be implemented first. Checker refactors in sections 1 and 2 depend on Jinja2 re-rendering capability and prompt storage changes defined there.

## Problem Statement

The checker system has 21 checkers covering 14 engine mechanics, but coverage is uneven. Five major systems have no checker coverage (ruling engine, convergence scoring, narration quality, compaction, location/world-state content). Five checkers were removed as obsolete or redundant. The CLI tooling lacks automated baseline comparison and warning storage. Reports are manually written despite an existing Jinja2 template.

## Constraints

- Checkers must be deterministic or LLM-based; no external dependencies beyond the running LLM backend.
- Checkers read from `events.jsonl` and `state.yaml` — they cannot call the engine directly.
- LLM checkers are expensive (~30s each); limit to 3.
- Checkers must use `EngineConfig` or pack-level config for thresholds, not hardcoded values.
- The checker framework uses `@register_checker` decorator with `CheckerResult` return type.

## Non-goals

- This does not cover the game engine mechanics themselves. Only their verification.
- This does not cover the web UI. Web UI changes are handled separately.
- This does not cover prompt template design. Prompt changes are handled separately.
- This does not cover CI/CD integration. That is a future concern.

## Decision Table

| Decision | Status | What | Why |
|---|---|---|---|
| Remove `pacing_directives` phase_constraint | DONE | Delete the phase_constraint check from `pacing_directives`; keep directive rendering checks | `beat_phase_validity` does the same check. Duplicate coverage wastes checker budget. |
| Remove `phase_persistence` | DONE | Delete this checker entirely | It is a regression guard for a specific bug. `phase_transition` already validates the state machine. |
| Remove `action_quality` | DONE | Delete this checker; merge its concerns into a broader `player_input` checker | It only checks for duplicate actions. Too thin to justify a standalone checker. |
| Remove `recent_beats` | DONE | Delete this checker | It only validates list structure (non-empty, max 5 entries). No semantic checking. |
| Remove `scene_age_tracking` | DONE | Delete this checker | `turn_entered` and `location_entered_turn` were removed from state during scene consolidation. The checker validates trivially true properties (turn numbers increment). |
| Add ruling engine checkers | PENDING | `ruling_reason_quality`, `ruling_band_distribution`, `ruling_intent_match` | Ruling is the first pipeline step with zero checker coverage. Biggest gap. |
| Add convergence checker | PENDING | `convergence_components` | Convergence drives CLIMAX transitions but has no checker. Second biggest gap. |
| Add thread sanitizer quality checkers | DEFERRED | `sanitizer_dedup_threshold`, `sanitizer_abandon_rate` | Engine does not emit dedup similarity scores or abandonment data. Cannot implement until engine tracks these. |
| Add state application checkers | PENDING | `location_description_consistency`, `world_state_facts` | State mutations (location, world_state facts) have no checker coverage. |
| Store all warnings in events | DONE | `kind="warning"` events for all warning types | Thread dedup, compendium dedup, seed soft-checks now stored. |
| Use `eval compare` for baseline comparison | DONE | `ev.py eval compare <baseline> <current>` | Implemented. Replaces manual report comparison. |
| Report both LLM and deterministic totals | DONE | "N/N deterministic (100%) + N/N LLM (100%) = N/N (100%)" | Prevents denominator confusion across runs. |

## Resolved Questions

- [RESOLVED: `ruling_intent_match` should be LLM-based. Rationale: semantic intent matching requires LLM; this runs selectively at end-of-session via `--llm-checkers`, not mid-eval. No limit concerns.]
- [RESOLVED: Checker count is not a hard limit. Checkers run piecemeal post-facto with `--checker` filtering. 21 deterministic + 4 LLM is fine.]
- [RESOLVED: Direct import of `EngineConfig` — checkers import it directly, no framework injection needed.]

## Open Questions

- [OPEN: Should we add a `checkers` config section to `EngineConfig` with threshold overrides (min_reason_words, band_skew_ratio, etc.)?]

## Current State — What Exists

### Checker Framework

The checker framework lives in `ccya/ev/checkers/`. Checkers are registered via `@register_checker` decorator with metadata (id, type, requires_fields, description). The framework loads checkers lazily, filters events, validates required fields exist, and runs checkers against event lists.

**21 registered checkers (after removals):**

| ID | Type | What it checks | Fields read |
|---|---|---|---|
| `gm_beat_lifecycle` | deterministic | Pending beat consumed, binding present | `extraction.storytell.output.gm_beat`, `meta.pending_gm_beat` |
| `location_change` | deterministic | Location ID changes applied correctly | `extraction.storytell.output.location_change`, `state_snapshot.location` |
| `inventory_integrity` | deterministic | No overdraw, no negative amounts, remove existence | `applied.inventory_remove`, `state_snapshot.inventory` |
| `conditions_lifecycle` | deterministic | Condition dedup | `applied.pc_condition_add`, `state_snapshot.pc.conditions` |
| `thread_lifecycle` | deterministic | thread_add applied, thread_update IDs valid | `extraction.storytell.output.thread_add`, `state_snapshot.arc.threads` |
| `arc_goal_updates` | deterministic | goal_update overwrites visible_goal | `extraction.storytell.output.goal_update`, `state_snapshot.arc.visible_goal` |
| `npc_presence` | deterministic | NPC presence validity, departed field compliance | `state_snapshot.compendium.npcs` |
| `pacing_directives` | deterministic | Directive rendering, removed directives | `pacing_context`, `narrate_prompt.rendered_user`, `extraction.storytell.output.gm_beat` |
| `sanitizer_lifecycle` | deterministic | Sanitizer thread operations valid against state | `sanitizer` events, `state_snapshot.arc.threads` |
| `phase_transition` | deterministic | Phase state machine transitions | `pacing_context.scene_phase` |
| `climax_turn_counting` | deterministic | climax_turn_count increments in CLIMAX, resets on exit | `pacing_context.climax_turn_count`, `pacing_context.scene_phase` |
| `breather_enforcement` | deterministic | breather auto-transitions to RISING after breather_max_turns | `pacing_context.scene_phase`, `pacing_context.breather_turn_count` |
| `roll_band_consistency` | deterministic | Band matches dice roll using rules engine | `ruling.band`, `ruling.rolled` |
| `thread_resolution_validity` | deterministic | thread_resolve entries have valid id/resolution_state/outcome | `extraction.storytell.output.thread_resolve` |
| `new_thread_validity` | deterministic | thread_add entries have id/summary, no duplicates | `extraction.storytell.output.thread_add` |
| `compendium_lifecycle` | deterministic | NPCs added via compendium appear in state | `extraction.scene.output.npcs`, `state_snapshot.compendium.npcs` |
| `beat_phase_validity` | deterministic | gm_beat.type is allowed for current phase | `extraction.storytell.output.gm_beat`, `pacing_context.scene_phase` |
| `arc_resolution_validity` | deterministic | arc_resolve has resolution + visible_goal, drop_threads valid | `extraction.storytell.output.arc_resolve` |
| `goal_update_validity` | deterministic | goal_update is non-empty, differs from previous visible_goal | `extraction.storytell.output.goal_update`, `state_snapshot.arc.visible_goal` |
| `directive_tone_match` | llm | Narration tone matches rules directive | Full event |
| `beat_narrative_chain` | llm | GM beat produces observable narrative consequence | Full event |
| `state_fidelity` | llm | Extraction matches what narration describes | Full event |

**Removed checkers (5):**
- `action_quality` — too thin (duplicate detection only)
- `phase_persistence` — regression guard; `phase_transition` covers state machine
- `recent_beats` — structure-only (non-empty, max 5); no semantic value
- `scene_age_tracking` — `turn_entered`/`location_entered_turn` removed from state during scene consolidation; validated trivially true properties
- `pacing_directives` phase_constraint — redundant with `beat_phase_validity`

### Engine Mechanics

| Mechanic | Module | State mutated | Checker coverage |
|---|---|---|---|
| **Ruling** | `engine/ruling.py` | `ruling` event (band, outcome, reason, intent) | **NONE** |
| **Narration** | `engine/narrate.py` | `narrate_prompt`, `pacing_context` | LLM only (3 checkers) |
| **Phase engine** | `engine/_pacing.py` | `pacing_context.scene_phase`, `convergence_score` | `phase_transition`, `climax_turn_counting`, `breather_enforcement` |
| **Convergence** | `engine/_pacing.py` | `pacing_context.convergence_score`, `convergence_components` | **NONE** |
| **GM Beats** | `engine/_pacing.py`, `engine/turn.py` | `meta.pending_gm_beat`, `pacing_context.recent_beats` | `gm_beat_lifecycle`, `beat_phase_validity` |
| **Threads** | `engine/thread_sanitizer.py` | `arc.threads`, `arc.completed_threads` | `thread_lifecycle`, `thread_resolution_validity`, `new_thread_validity`, `sanitizer_lifecycle` |
| **Arcs** | `engine/turn.py` | `arc.visible_goal`, `arc.threads`, `resolved_arcs` | `arc_goal_updates`, `arc_resolution_validity`, `goal_update_validity` |
| **Inventory** | `engine/turn_state.py` | `state.inventory` | `inventory_integrity` |
| **Conditions** | `engine/turn_state.py` | `state.pc.conditions` | `conditions_lifecycle` |
| **NPCs** | `engine/extraction/pipeline.py` | `state.compendium.npcs` | `npc_presence`, `compendium_lifecycle` |
| **Location** | `engine/extraction/pipeline.py` | `state.location` | `location_change` |
| **Rolls** | `engine/ruling.py` | `ruling.band`, `ruling.rolled` | `roll_band_consistency` |
| **Sanitizer** | `engine/thread_sanitizer.py` | `arc.threads` (dedup, abandon) | `sanitizer_lifecycle` |
| **Compaction** | `engine/turn.py` | `events.jsonl` (compaction entries) | **NONE** |

### CLI Tooling

- `ev.py play` — Run game turns with LLM or interactive input
- `ev.py check` — Run checkers against events
- `ev.py eval run` — Batch scenario runner (YAML scenarios → checkers → report)
- `ev.py eval list` — List available scenarios
- `ev.py eval compare` — Cross-run checker comparison (new)
- `ev.py warnings` — Show retry/dedup/rejection warnings
- `ev.py convergence` — Show convergence score per turn
- `ev.py prompt-eval` — Fast prompt testing (render only or render + LLM)

### Report Generation

- Reports are manually written markdown files in `evals/runs/<commit>/`
- Template exists at `evals/ev-tooling/templates/report.md.j2` but is not used automatically
- Each eval session requires manual report writing (CONSOLIDATED-REPORT.md + META-REPORT.md)

### Problems with Current State

1. **Ruling engine has zero checker coverage.** The first pipeline step (intent classification, band determination, reason generation) is completely unchecked. This is the most critical gap.

2. **Convergence scoring has zero checker coverage.** The core mechanic driving RISING→CLIMAX transitions is not verified. No checker validates the 5-component formula or that it actually drives transitions.

3. **Narration quality relies solely on LLM checkers.** Three LLM checkers cover narration, but they are expensive (~30s each) and non-deterministic. No deterministic fallback exists. Mitigation: LLM checkers run selectively at end-of-session via `--llm-checkers`, not mid-eval.

4. **Compaction is completely unchecked.** No checker verifies compaction happens at right intervals or preserves data.

5. **State application gaps.** `location_description`, `world_state` facts, `pc.stats` changes have no checkers.

6. **Thread sanitizer quality unchecked.** `sanitizer_lifecycle` checks validity but not quality (dedup similarity thresholds, abandonment rates).

7. **Five obsolete checkers removed.** `action_quality` (too thin), `phase_persistence` (regression guard), `recent_beats` (structure-only), `scene_age_tracking` (trivially true post-consolidation), `pacing_directives` phase_constraint (redundant with `beat_phase_validity`). Net: 26→21 checkers.

8. **Warning storage gaps.** Three warning types (`generate_seed soft-check`, thread dedup, compendium dedup) are now stored in events. This was fixed in the June 20 runs.

9. **No automated baseline comparison.** Each eval run produces raw scores but no comparison to previous runs. `ev.py eval compare` was added to address this.

10. **Reports are manually written.** Despite an existing Jinja2 template, reports are hand-written. This is error-prone and time-consuming.

11. **Hardcoded thresholds.** Checkers use hardcoded values (e.g., `breather_max_turns=3`, `climax_turn_limit=4`, `VALID_TRANSITIONS` set) instead of reading from `EngineConfig`. This makes them brittle when mechanics change.

## Proposed Solution

### Core Changes

#### 1. New Checkers

**`ruling_reason_quality`** (deterministic)
- Checks `ruling.reason` is non-empty and substantive (not just "ok", "yes", "no", or single word)
- Reads: `ruling.reason`
- Threshold: minimum 3 words or contains a reason keyword (because, since, due to, as)

**`ruling_band_distribution`** (deterministic)
- Checks dice band distribution is not extremely skewed over a session
- Reads: `ruling.band` across all events
- Threshold: configurable via `EngineConfig.ruling.band_skew_threshold` (default: no more than 80% of rolls in a single band)

**`ruling_intent_match`** (LLM)
- Checks ruling's `possible`/`impossible` classification matches player input semantics
- Reads: `ruling.intent`, `ruling.possible`, player input text
- Runs selectively at end-of-session via `--llm-checkers`, not mid-eval (existing LLM checkers use the same mechanism)

**`convergence_components`** (deterministic)
- Verifies the 5-component convergence score matches the documented formula
- Reads: `pacing_context.convergence_components`, `pacing_context.convergence_score`, `state_snapshot.arc.threads`, `pacing_context.scene_age`, `pacing_context.recent_beats`, `ruling.band`
- Checks: each component (thread_weight, urgency_depth, scene_age, beat_streak, dice_weight) is correctly computed from state
- Also checks: RISING→CLIMAX only happens when score >= threshold

**`sanitizer_dedup_threshold`** (deterministic) — **DEFERRED**
- Verifies thread dedup similarity is reasonable (not deduping unrelated threads)
- Reads: sanitizer events with `similarity` field — engine does not currently emit this
- Requires engine change to track and emit dedup similarity scores
- Blocked until engine emits the necessary data

**`sanitizer_abandon_rate`** (deterministic) — **DEFERRED**
- Detects excessive thread abandonment
- Reads: sanitizer events with `abandoned` field — engine does not currently emit this
- Requires engine change to track and emit abandonment metadata
- Blocked until engine emits the necessary data

**`location_description_consistency`** (deterministic)
- Checks extracted location description is non-empty and substantive
- Reads: `extraction.scene.output.location_description`
- Threshold: minimum 2 sentences or 30 words

**`world_state_facts`** (deterministic)
- Checks world_state facts are non-empty strings with content
- Reads: `state_snapshot.scene.world_state`
- Threshold: facts should have non-empty `text` field

#### 2. Checkers to Remove

| Removed | From | Notes |
|---|---|---|
| `pacing_directives` phase_constraint | `ccya/ev/checkers/pacing.py` | Covered by `beat_phase_validity`. Keep directive rendering checks. |
| `phase_persistence` | `ccya/ev/checkers/phase_persistence.py` | Regression guard. `phase_transition` already validates state machine. |
| `action_quality` | `ccya/ev/checkers/pacing.py` | Too thin (duplicate detection only). |
| `recent_beats` | `ccya/ev/checkers/pacing.py` | Structure-only check. No semantic value. |
| `scene_age_tracking` | `ccya/ev/checkers/scene_age_tracking.py` | `turn_entered`/`location_entered_turn` removed from state during scene consolidation. |

#### 3. Config-Driven Thresholds — PENDING

All checkers should read thresholds from `EngineConfig` instead of hardcoding them. This requires:

- Adding a `checkers` section to `EngineConfig` with configurable thresholds (e.g., `min_reason_words`, `band_skew_ratio`)
- Checkers import `EngineConfig` and read from it
- Pack-level overrides via `pack.yaml` checker config

#### 4. Report Automation

- Use the existing `report.md.j2` template for automated report generation
- `ev.py eval run` should generate reports automatically with `--report auto`
- `ev.py eval compare` output should be saved to `COMPARISON.md` in the run directory

#### 5. Warning Storage

All warning types should be stored as events with `kind="warning"`. This was partially fixed (thread dedup, compendium dedup, seed soft-checks are now stored). Remaining warnings to store:

- `ruling` warnings (band skew, reason quality)
- `convergence` warnings (score anomalies)
- `sanitizer` warnings (dedup quality, abandonment rate)

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Make all checkers LLM-based | Too expensive. LLM checkers cost ~30s each. 27 LLM checkers would make a 30-turn session take hours. |
| Create a single "comprehensive" checker | Too monolithic. The rubric's modular approach (check one area at a time) produces more accurate findings. |
| Store warnings as log entries only | Logs are lost after the run. Events are persistent and analyzable. |
| Use a separate test framework | The checker framework is already sufficient. Adding a new framework adds complexity without benefit. |
| Hardcode checker thresholds in a constants file | `EngineConfig` is the single source of truth for engine behavior. Checkers should read from it. |

## Failure Modes and Risks

1. **Checker bloat.** Adding 6 checkers while removing 5 results in a net +1 (21→22). The checker system stays lean. Deterministic checkers are fast (~ms each); LLM checkers run selectively at end-of-session.

2. **Config drift.** If `EngineConfig` thresholds change but checkers are not updated, checkers will produce false positives. Mitigation: document the relationship between engine config and checker thresholds.

3. **Event schema changes.** Checkers read from `events.jsonl` fields. If the event schema changes (e.g., `ruling.reason` renamed), checkers will break. Mitigation: use `extract_field()` with dotpath access (already done) and validate required fields before running.

4. **LLM checker non-determinism.** LLM checkers can produce different results on different runs. Mitigation: use `--checker-model` flag to pin the model; document that LLM checker results are approximate.

5. **Threshold tuning.** New checkers need threshold tuning. What works for one pack may not work for another. Mitigation: use pack-level config overrides.

## What Is Removed (all DONE)

| Removed | From | Notes |
|---|---|---|
| `pacing_directives` phase_constraint | `ccya/ev/checkers/pacing.py` | Covered by `beat_phase_validity` |
| `phase_persistence` | `ccya/ev/checkers/phase_persistence.py` | Deleted with no replacement |
| `action_quality` | `ccya/ev/checkers/pacing.py` | Deleted with no replacement |
| `recent_beats` | `ccya/ev/checkers/recent_beats.py` | Deleted with no replacement |
| `scene_age_tracking` | `ccya/ev/checkers/scene_age_tracking.py` | `turn_entered`/`location_entered_turn` removed from state during scene consolidation; checker validates trivially true properties |
| `phase_persistence.py` (file) | `ccya/ev/checkers/phase_persistence.py` | Full file deleted |
| `recent_beats.py` (file) | `ccya/ev/checkers/recent_beats.py` | Full file deleted |
| `scene_age_tracking.py` (file) | `ccya/ev/checkers/scene_age_tracking.py` | Full file deleted |
| Stale `archived` from `VALID_PRESENCE` | `ccya/ev/checkers/npc_presence.py` | Not a valid `NpcPresence` enum value |

## What Is Unchanged

- Checker framework (`ccya/ev/checkers/__init__.py`) — registration, execution, result format
- `CheckerResult` dataclass — fields (checker_id, passed, score, detail, findings, ms)
- `@register_checker` decorator — signature and behavior
- `ev.py` CLI dispatch — command routing, flag handling
- `ev.py play` — turn execution, LLM integration
- `ev.py eval run` — scenario execution, checker running, report generation
- `ev.py eval compare` — cross-run comparison (already implemented)
- `ev.py warnings` — warning display (already updated with thread/compendium dedup columns)
- LLM checkers (`directive_tone_match`, `beat_narrative_chain`, `state_fidelity`) — unchanged
- Event schema — checkers read from existing fields; no schema changes required

## New Model Shapes

No new data models required. New checkers use existing event fields and `CheckerResult`.

## Context for Implementation

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/ev/checkers/__init__.py` | Checker framework: registration, execution, `CheckerResult` | Base framework all new checkers use |
| `ccya/ev/check.py` | `cmd_check` — checker execution and output formatting | How checkers are invoked and results displayed |
| `ccya/ev/events.py` | `extract_field()` — dotpath field access from events | How checkers read event data |
| `ccya/ev/checkers/_llm.py` | `_call_llm_checker()`, `_result_from_llm_output()` | Shared utilities for LLM checkers |
| `ccya/ev/checkers/llm_checkers.py` | Existing LLM checkers + `set_checker_config()` | Pattern to follow for new LLM checkers |
| `ccya/engine/_pacing.py` | `compute_convergence_score()` — 5-component formula | Source for convergence checker logic |
| `ccya/engine/ruling.py` | Ruling LLM call, band determination, intent classification | Source for ruling checker logic |
| `ccya/engine/config.py` | `EngineConfig` — configuration schema | Where checker thresholds would be added |
| `docs/ev/CHECKERS.md` | Checker documentation | Context for existing checker behavior |
| `docs/ev/RUBRIC.md` | Full rubric with checker recommendations | Context for what should be checked |
