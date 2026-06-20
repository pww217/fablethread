# Eval System Design

## Purpose

This document defines the target state for the CCYA eval system: checkers, CLI tooling, and report generation. It is the design authority for plans implementing checker additions, removals, or structural changes.

## Problem Statement

The checker system has 27 checkers covering 14 engine mechanics, but coverage is uneven. Four major systems have no checker coverage (ruling engine, convergence scoring, narration quality, compaction). Three checkers overlap with existing ones. The CLI tooling lacks automated baseline comparison and warning storage. Reports are manually written despite an existing Jinja2 template.

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

| Decision | What | Why |
|---|---|---|
| Remove `pacing_directives` phase_constraint | Delete the phase_constraint check from `pacing_directives`; keep directive rendering checks | `beat_phase_validity` does the same check. Duplicate coverage wastes checker budget. |
| Remove `phase_persistence` | Delete this checker entirely | It is a regression guard for a specific bug. `phase_transition` already validates the state machine. |
| Remove `action_quality` | Delete this checker; merge its concerns into a broader `player_input` checker | It only checks for duplicate actions. Too thin to justify a standalone checker. |
| Remove `recent_beats` | Delete this checker | It only validates list structure (non-empty, max 10 entries). No semantic checking. |
| Add ruling engine checkers | `ruling_reason_quality`, `ruling_band_distribution`, `ruling_intent_match` | Ruling is the first pipeline step with zero checker coverage. Biggest gap. |
| Add convergence checker | `convergence_components` | Convergence drives CLIMAX transitions but has no checker. Second biggest gap. |
| Add thread sanitizer quality checkers | `sanitizer_dedup_threshold`, `sanitizer_abandon_rate` | Sanitizer lifecycle is checked but quality is not. |
| Add state application checkers | `location_description_consistency`, `world_state_facts` | State mutations (location, world_state facts) have no checker coverage. |
| Store all warnings in events | `kind="warning"` events for all warning types | Three warning types are currently logged but not stored, making them invisible to checkers. |
| Use `eval compare` for baseline comparison | `ev.py eval compare <baseline> <current>` | Implemented. Replaces manual report comparison. |
| Report both LLM and deterministic totals | "23/23 deterministic (100%) + 3/3 LLM (100%) = 26/26 (100%)" | Prevents denominator confusion across runs. |

## Open Questions

- [OPEN: Should `ruling_intent_match` be deterministic or LLM-based? A deterministic check could verify `possible`/`impossible` classification against keyword patterns, but semantic intent matching requires LLM.]
- [OPEN: What is the target number of checkers? Current is 27. Adding 8 would make 35. Is there a practical limit?]
- [OPEN: Should checkers read from `EngineConfig` directly, or should we pass config through the checker framework? Currently checkers import `EngineConfig` directly.]

## Current State — What Exists

### Checker Framework

The checker framework lives in `ccya/ev/checkers/`. Checkers are registered via `@register_checker` decorator with metadata (id, type, requires_fields, description). The framework loads checkers lazily, filters events, validates required fields exist, and runs checkers against event lists.

**27 registered checkers:**

| ID | Type | What it checks | Fields read |
|---|---|---|---|
| `gm_beat_lifecycle` | deterministic | Pending beat consumed, binding present | `extraction.storytell.output.gm_beat`, `meta.pending_gm_beat` |
| `location_change` | deterministic | Location ID changes applied correctly | `extraction.storytell.output.location_change`, `state_snapshot.location` |
| `inventory_integrity` | deterministic | No overdraw, no negative amounts, remove existence | `applied.inventory_remove`, `state_snapshot.inventory` |
| `conditions_lifecycle` | deterministic | Condition dedup | `applied.pc_condition_add`, `state_snapshot.pc.conditions` |
| `thread_lifecycle` | deterministic | thread_add applied, thread_update IDs valid | `extraction.storytell.output.thread_add`, `state_snapshot.arc.threads` |
| `arc_goal_updates` | deterministic | goal_update overwrites visible_goal | `extraction.storytell.output.goal_update`, `state_snapshot.arc.visible_goal` |
| `npc_presence` | deterministic | NPC presence validity, departed field compliance | `state_snapshot.compendium.npcs` |
| `pacing_directives` | deterministic | Directive rendering, removed directives, phase_constraint, beat_type_variety, surface_as_consistency | `pacing_context`, `narrate_prompt.rendered_user`, `extraction.storytell.output.gm_beat` |
| `action_quality` | deterministic | Action count, distinctness | `actions`, `ruling` |
| `sanitizer_lifecycle` | deterministic | Sanitizer thread operations valid against state | `sanitizer` events, `state_snapshot.arc.threads` |
| `phase_transition` | deterministic | Phase state machine transitions | `pacing_context.scene_phase` |
| `recent_beats` | deterministic | recent_beats list structure (non-empty, max 10) | `pacing_context.recent_beats` |
| `phase_persistence` | deterministic | Scene phase persists across turns (regression guard) | `pacing_context.scene_phase` |
| `scene_age_tracking` | deterministic | scene_age increments, resets on RESOLUTION/BREATHER | `pacing_context.scene_age`, `pacing_context.scene_phase` |
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

### Engine Mechanics

| Mechanic | Module | State mutated | Checker coverage |
|---|---|---|---|
| **Ruling** | `engine/ruling.py` | `ruling` event (band, outcome, reason, intent) | **NONE** |
| **Narration** | `engine/narrate.py` | `narrate_prompt`, `pacing_context` | LLM only (3 checkers) |
| **Phase engine** | `engine/_pacing.py` | `pacing_context.scene_phase`, `convergence_score` | `phase_transition`, `phase_persistence`, `scene_age_tracking`, `climax_turn_counting`, `breather_enforcement` |
| **Convergence** | `engine/_pacing.py` | `pacing_context.convergence_score`, `convergence_components` | **NONE** |
| **GM Beats** | `engine/_pacing.py`, `engine/turn.py` | `meta.pending_gm_beat`, `pacing_context.recent_beats` | `gm_beat_lifecycle`, `beat_phase_validity`, `recent_beats` |
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

3. **Narration quality relies solely on LLM checkers.** Three LLM checkers cover narration, but they are expensive (~30s each) and non-deterministic. No deterministic fallback exists.

4. **Compaction is completely unchecked.** No checker verifies compaction happens at right intervals or preserves data.

5. **State application gaps.** `location_description`, `world_state` facts, `pc.stats` changes have no checkers.

6. **Thread sanitizer quality unchecked.** `sanitizer_lifecycle` checks validity but not quality (dedup similarity thresholds, abandonment rates).

7. **Three redundant checkers.** `pacing_directives` phase_constraint overlaps with `beat_phase_validity`. `phase_persistence` is a regression guard with low standalone value. `action_quality` is too thin (duplicate detection only). `recent_beats` validates structure only.

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
- This is the only LLM checker that should be added (3 LLM limit already at capacity)

**`convergence_components`** (deterministic)
- Verifies the 5-component convergence score matches the documented formula
- Reads: `pacing_context.convergence_components`, `pacing_context.convergence_score`, `state_snapshot.arc.threads`, `pacing_context.scene_age`, `pacing_context.recent_beats`, `ruling.band`
- Checks: each component (thread_weight, urgency_depth, scene_age, beat_streak, dice_weight) is correctly computed from state
- Also checks: RISING→CLIMAX only happens when score >= threshold

**`sanitizer_dedup_threshold`** (deterministic)
- Verifies thread dedup similarity is reasonable (not deduping unrelated threads)
- Reads: sanitizer events with `similarity` field
- Threshold: similarity below 0.7 should not trigger dedup

**`sanitizer_abandon_rate`** (deterministic)
- Detects excessive thread abandonment
- Reads: sanitizer events with `abandoned` field
- Threshold: more than 50% of threads abandoned in a session is flagged

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

#### 3. Config-Driven Thresholds

All checkers should read thresholds from `EngineConfig` instead of hardcoding them. This requires:

- Adding a `checkers` section to `EngineConfig` with configurable thresholds
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

1. **Checker bloat.** Adding 8 checkers while removing 4 results in a net +4. The checker system could become slow to run. Mitigation: limit to deterministic checkers for speed; keep LLM checkers at 3.

2. **Config drift.** If `EngineConfig` thresholds change but checkers are not updated, checkers will produce false positives. Mitigation: document the relationship between engine config and checker thresholds.

3. **Event schema changes.** Checkers read from `events.jsonl` fields. If the event schema changes (e.g., `ruling.reason` renamed), checkers will break. Mitigation: use `extract_field()` with dotpath access (already done) and validate required fields before running.

4. **LLM checker non-determinism.** LLM checkers can produce different results on different runs. Mitigation: use `--checker-model` flag to pin the model; document that LLM checker results are approximate.

5. **Threshold tuning.** New checkers need threshold tuning. What works for one pack may not work for another. Mitigation: use pack-level config overrides.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `pacing_directives` phase_constraint | `ccya/ev/checkers/pacing.py` | Covered by `beat_phase_validity` |
| `phase_persistence` | `ccya/ev/checkers/phase_persistence.py` | Deleted with no replacement |
| `action_quality` | `ccya/ev/checkers/pacing.py` | Deleted with no replacement |
| `recent_beats` | `ccya/ev/checkers/pacing.py` | Deleted with no replacement |

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
- `EngineConfig` — checker thresholds will be added as a new section, not a replacement

## New Model Shapes

No new data models required. New checkers use existing event fields and `CheckerResult`.

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/ev/checkers/__init__.py` | Checker framework: registration, execution, `CheckerResult` | Base framework all new checkers use |
| `ccya/ev/check.py` | `cmd_check` — checker execution and output formatting | How checkers are invoked and results displayed |
| `ccya/ev/checkers/pacing.py` | `pacing_directives`, `action_quality` — to be modified/removed | Files to edit for removals |
| `ccya/ev/checkers/phase_persistence.py` | `phase_persistence` — to be removed | File to delete |
| `ccya/ev/events.py` | `extract_field()` — dotpath field access from events | How checkers read event data |
| `ccya/engine/_pacing.py` | Convergence scoring, phase engine, beat constraints | Source for convergence checker logic |
| `ccya/engine/ruling.py` | Ruling LLM call, band determination, intent classification | Source for ruling checker logic |
| `ccya/engine/turn.py` | Turn orchestrator, compaction logic | Source for compaction checker (future) |
| `ccya/engine/turn_state.py` | State application, inventory/condition mutations | Source for state application checkers |
| `ccya/engine/thread_sanitizer.py` | Thread dedup, abandonment logic | Source for sanitizer quality checkers |
| `ccya/engine/config.py` | `EngineConfig` — configuration schema | Where checker thresholds will be added |
| `ccya/ev/eval.py` | `cmd_eval_compare` — cross-run comparison | Reference for report automation |
| `ccya/ev/warnings.py` | `cmd_warnings` — warning display | Reference for warning storage |
| `docs/ev/RUBRIC.md` | Full rubric with checker recommendations | Context for what should be checked |
| `docs/ev/CHECKERS.md` | Checker documentation | Context for existing checker behavior |
