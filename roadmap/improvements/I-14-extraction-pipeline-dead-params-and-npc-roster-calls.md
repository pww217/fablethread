---
title: "Extraction pipeline dead parameters and redundant npc_roster calls"
status: done
urgency: 3
size: small
created: 2026-06-28
ticket_id: I-14
labels:
  - tech-debt
plan: plans/I-14-extraction-pipeline-dead-params-and-npc-roster-calls.md
---

## Problem

The extraction pipeline passes parameters that are never consumed, and `build_npc_roster()` is called 4 times per turn with identical inputs. These are low-risk cleanup items that reduce cognitive overhead and wasted computation.

## Findings

### Dead parameters in `_run_extraction_pipeline()`

Three parameters are passed through the pipeline but never consumed by any extraction stream:

1. **`pacing_context`** — passed to `_run_extraction_pipeline()` but never used by scene, state, or record streams. `record_user.j2` doesn't reference it. World reads `pacing_context` directly from `turn.py`, not from the pipeline.

2. **`intent`** — passed to `_run_extraction_pipeline()` and forwarded to `_extract_state_messages()`, but actually **used** by `extract_state_user.j2:10-12` to render `intent_verb: intent`. Keep this one.

### Over-passed parameter

3. **`rules_outcome`** — full `RulesOutcome` object passed through pipeline, but only `band` is extracted (`pipeline.py:197`). Pass `band: str` directly instead.

### Redundant computation (won't do)

4. **`build_npc_roster()` called 4 times per turn** — `ruling.py:223`, `narrate.py:274`, `scene.py:22`, `world.py:46`. Same computation (filter+sort+score compendium.npcs) repeated. Narrate is the wall — it needs a slim roster (no personality labels) while ruling/scene/world use `ARCHETYPES`. Caching would require passing different versions to different consumers. Marked won't do.

### Not actionable

5. **`_ExtractionContext` deep-copy pattern** — intentional. Record needs to see post-delta state matching what `apply_delta()` will write, including validation rejections. Don't change.

## Plan

See `plans/I-14-extraction-pipeline-dead-params-and-npc-roster-calls.md`
