---
title: "Full prompt audit: verify all system/user prompt pairs across pipeline steps"
status: new
urgency: 3
size: medium
created: 2026-07-19
ticket_id: E-16
labels: []
design:
plan:
pr:
  url:
  branch:
---

## PURPOSE

This ticket is the **working memory and home for updates** for the full prompt audit. It tracks progress, documents findings, and serves as long-term memory between compactions. Every session that continues this audit will load this ticket as its primary context. Write with intention: include specific observations, turn numbers, and reasoning. Vague notes are as bad as no notes.

## Status

| Field | Value |
|-------|-------|
| Total pairs | 9 (18 templates + 10 shared sections) |
| Completed | 9 |
| In progress | — |
| Overall status | **COMPLETE** |

## Quick status table

| # | Step | System | User | Status | Issues |
|---|------|--------|------|--------|--------|
| 1 | Generate Pack | `generate_pack_system_wb.j2` | `generate_pack_user_wb.j2` | ❌ | 8 |
| 2 | Prepare Seed | `prepare_seed_system.j2` | `prepare_seed_user.j2` | ✅ | 0 |
| 3 | Narrate Seed | `narrate_seed_system.j2` | (none, system-only) | ✅ | 0 |
| 4 | Ruling | `ruling_system.j2` | `ruling_user.j2` | ❌ | 1 |
| 5 | Narrate | `narrate_system.j2` | `narrate_user.j2` | ❌ | 3 |
| 6 | Scene Extract | `extract_scene_system.j2` | `extract_scene_user.j2` | ✅ | 0 |
| 7 | State Extract | `extract_state_system.j2` | `extract_state_user.j2` | ❌ | 1 |
| 8 | Record | `record_system.j2` | `record_user.j2` | ❌ | 1 |
| 9 | World | `world_system.j2` | `world_user.j2` | ❌ | 2 |

## Description

Systematic audit of every prompt pair (system + user templates) across the full CCYA turn pipeline. For each step, render actual prompts against live eval data, verify inputs/outputs match the architectural design, and check for duplication, conflicts, missing context, or confusion in system prompts.

## Process

1. **Render prompts** using `ev.py prompt-eval dump <save-dir> --turn N --stream <stream> [--from-events]` against recent eval runs
2. **Examine each system/user pair** sequentially — never in parallel, one at a time
3. **Verify against architecture docs** in `docs/architecture/step*.md` for intended design
4. **Check system prompts** have all required guidance, no duplication/conflicts/contradictions
5. **Check user prompts** render every input correctly with all context the system prompt needs
6. **Track progress in ticket body** after each prompt pair — this ticket is long-term memory between compactions
7. **Note difficulties** encountered in the process for future process documentation

## Scope — Pipeline Steps (sequential order)

### Generation (new game)
1. `generate_pack_system_wb.j2` + `generate_pack_user_wb.j2` — ScenarioBrief generation
2. `prepare_seed_system.j2` + `prepare_seed_user.j2` — SeedState generation
3. `narrate_seed_system.j2` — Opening narrative generation

### Per-turn pipeline
4. `ruling_system.j2` + `ruling_user.j2` — Step 0: Ruling/Intent
5. `narrate_system.j2` + `narrate_user.j2` — Step 1: Narration
6. `extract_scene_system.j2` + `extract_scene_user.j2` — Step 2a: Scene Extract
7. `extract_state_system.j2` + `extract_state_user.j2` — Step 2b: State Extract
8. `record_system.j2` + `record_user.j2` — Step 2c: Record
9. `world_system.j2` + `world_user.j2` — Step 2d: World (async)

## Sources

- Architecture docs: `docs/architecture/step0-ruling.md`, `step1-narrate.md`, `step2a-scene.md`, `step2b-state.md`, `step2c-record.md`, `step2d-world.md`
- Prompt templates: `ccya/prompts/` (all `.j2` files + `sections/` + `context.py`)
- Recent eval runs: `evals/runs/2026-07-17_0.32.1_2e3d0188/` (2026-07-17 run with multiple packs/turns) and `evals/runs/latest/`
- Shared sections: `ccya/prompts/sections/` (10 include templates)

## Recommended run for auditing

- `evals/runs/2026-07-17_0.32.1_2e3d0188/2145_noir-1930s_25t/` — 25-turn noir run, good coverage
- `evals/runs/2026-07-17_0.32.1_2e3d0188/2100_noir-1930s_5t/` — short run, good for generation/seed prompts
- `evals/runs/latest/` — most recent save, good for quick renders

## Audit checklist per prompt pair

- [ ] System prompt has all guidance described in architecture docs
- [ ] No duplicate/conflicting instructions within system prompt
- [ ] No contradictions between system prompt and architecture
- [ ] User prompt renders all inputs the system prompt references
- [ ] User prompt includes all contextual data described in architecture
- [ ] Shared sections render correctly (check rendered output)
- [ ] Template variables match what context.py boundary models provide
- [ ] Output schema in system prompt matches actual extraction model
- [ ] Field rules in system prompt are actionable and unambiguous
- [ ] No dead/unused variables in user prompt
- [ ] No missing variables that would cause Jinja errors

## Progress tracking format

After each prompt pair, append a timestamped entry:

```
### [HH:MM] <step_name> — <system.j2 + user.j2>
- Status: PASS / ISSUES FOUND
- Issues: <list any problems found>
- Notes: <any observations about rendering, missing context, conflicts>
- Difficulty: <any process difficulties encountered>
```

## Difficulties to document

- Template rendering issues (Jinja errors, missing variables)
- Ambiguity in architecture docs vs actual templates
- Inconsistencies between system prompt and user prompt data
- Shared section rendering problems
- Any process friction that makes future audits harder

## Shared sections mapping

Which templates include which shared sections (from `ccya/prompts/sections/`):

| Section | Used by | Purpose |
|---------|---------|---------|
| `_pc_header.j2` | ruling_user, narrate_user | PC name, tagline, stats |
| `_conditions.j2` | ruling_user, narrate_user, extract_state_user | Active conditions with TTL/age |
| `_inventory.j2` | ruling_user, narrate_user, extract_state_user | Inventory list |
| `_location.j2` | narrate_user | Current location name/description |
| `_npc_roster.j2` | ruling_user, narrate_user, extract_scene_user | NPC roster with presence/bio/mfl |
| `_thread_list.j2` | narrate_user, record_user | Active + dormant threads |
| `_world_state.j2` | narrate_user | Scene world_state facts |
| `_arc.j2` | narrate_user | Campaign arc goal + resolved arcs |
| `_recent_turns.j2` | ruling_user, narrate_user, record_user | Last turn's narration |
| `_npc_names.j2` | (check usage) | NPC name pool |

## Data flow between steps

What each step receives and produces (for cross-reference):

| Step | Receives from | Produces for |
|------|--------------|--------------|
| Generate Pack | User concept + pack config | `ScenarioBrief` JSON |
| Prepare Seed | ScenarioBrief + overrides | `SeedState` JSON |
| Narrate Seed | SeedState | Opening narrative + actions |
| Ruling | `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input`, `arc.threads` (urgent), `beat_candidates` | `IntentEnvelope`, `RulesOutcome`, `pending_gm_beat` |
| Narrate | Full `state`, `prior_history[-10]`, `recent_turns[-1:]`, `pacing_context`, `pending_gm_beat`, `npc_roster`, `world_factions` | `narrative` prose |
| Scene Extract | `narration`, `pc_name`, `npc_roster` | `SceneExtractResult` (compendium updates, candidate_npcs) |
| State Extract | `narration`, `pc_name`, `conditions`, `inventory`, `location`, `intent` | `StateExtractResult` (inventory/condition/location deltas) |
| Record | `narration`, `pc_name`, `arc.threads[]`, `band`, `world_state`, `prior_history` | `StorytellerResult` (thread ops, goal_update, actions, outcome_summary) |
| World | `npc_roster`, `arc.threads[]`, `pacing_context`, `recent_beats`, `allowed_beat_types`, `narration` | `beat_candidates` (0-3 GMBeat dicts) |

## Template-to-boundary-model mapping

From `ccya/prompts/context.py` — which boundary model feeds each user template:

| User Template | Boundary Model | Key fields |
|--------------|----------------|------------|
| `ruling_user.j2` | `RulingBoundary` | `pc`, `location`, `user_input`, `meta`, `npc_roster`, `recent_turns`, `inventory`, `urgent_threads` |
| `narrate_user.j2` | `NarratorBoundary` | `pc`, `current_objective`, `state`, `npc_roster`, `pacing_context`, `recent_turns`, `prior_history`, `rules_outcome`, `user_input`, `pending_beat`, `meta`, `world_factions`, `npc_name_pool` |
| `extract_scene_user.j2` | `SceneExtractBoundary` | `narration`, `npc_roster`, `pc_name`, `turn_no` |
| `extract_state_user.j2` | `StateExtractBoundary` | `conditions`, `inventory`, `location`, `intent`, `turn_no`, `narration`, `pc_name`, `pack_inventory` |
| `record_user.j2` | (no boundary model — built ad-hoc) | `pc_name`, `all_threads`, `world_state`, `band`, `scene_phase`, `prior_history`, `recent_turns`, `narration`, `turn_no` |
| `world_user.j2` | (no boundary model — built ad-hoc) | `npc_roster`, `arc`, `pacing_context`, `recent_beats`, `allowed_beat_types`, `rules_outcome`, `narration` |

**Note:** Record and World have no boundary model in `context.py`. Check their rendering code directly in `engine/` for what context they pass to templates.

## Known issues / discovered bugs

Document any bugs or issues found during the audit here. Link to roadmap bug tickets if created.

| ID | Description | Severity | Found at | Ticket |
|----|-------------|----------|----------|--------|
| 1 | CRITICAL — Output format contradiction: system says "JSON", code expects YAML | High | generate_pack | — |
| 2 | Schema missing currency_id/start_currency_amount fields | Low | generate_pack | — |
| 3 | User prompt missing 4 WorldBrief fields (geography, power, daily_life, player_hint) | Medium | generate_pack | — |
| 4 | Archetype pools count mismatch (7 vs 8) | Low | generate_pack | — |
| 5 | Generic output discipline section inappropriate for generation | Low | generate_pack | — |
| 6 | Dead code: allowed_beat_types rendered but never passed | Low | ruling_user | — |
| 7 | "Five behavioral drivers" but only 4 listed | Medium | narrate_system | — |
| 8 | Dead fields in NarratorBoundary: ages, resolved_arcs | Low | narrate_user | — |
| 9 | curtain_call not in NarratorBoundary (ad-hoc field) | Low | narrate_user | — |
| 10 | canonical_id not in InventoryItem model — silently dropped | High | extract_state | — |
| 11 | System prompt schema incomplete for inventory_remove (missing amount) | Low | extract_state | — |
| 12 | curtain_call passed to record_user but never rendered | Low | record_user | — |
| 13 | Highlight fields contradiction: 13 listed, only 5 available | Medium | world_system | — |
| 14 | Environmental beats allowed by model validation but forbidden by prompt | Low | world_system | — |

## Difficulties encountered

Process friction, tooling issues, ambiguities, and anything that makes future audits harder.

- (start empty)

## Audit progress

All 9 prompt pairs audited across the full pipeline. 4 pairs clean, 5 pairs with issues. 14 total issues found (2 high, 3 medium, 9 low).

### Generation phase

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | generate_pack | ❌ 8 issues | Critical: JSON/YAML output contradiction (prompt says JSON, code parses YAML). 4 WorldBrief fields missing from user prompt. Schema missing currency fields. |
| 2 | prepare_seed | ✅ | Clean. All guidance, schema, and context verified. |
| 3 | narrate_seed | ✅ | Clean. System-only prompt, all guidance verified. |

### Per-turn pipeline

| # | Step | Status | Notes |
|---|------|--------|-------|
| 4 | ruling | ❌ 1 issue | Dead code: `allowed_beat_types` rendered in user prompt but never passed. |
| 5 | narrate | ❌ 3 issues | "Five behavioral drivers" but only 4 listed. Dead fields in NarratorBoundary (`ages`, `resolved_arcs`). `curtain_call` not in boundary model. |
| 6 | scene extract | ✅ | Clean. CompendiumNpcUpdate schema verified, all context correct. |
| 7 | state extract | ❌ 1 issue | `canonical_id` not in InventoryItem model — silently dropped by Pydantic `extra: "ignore"`. |
| 8 | record | ❌ 1 issue | `curtain_call` passed to template but never rendered. |
| 9 | world | ❌ 2 issues | Highlight fields contradiction (13 listed, 5 available). Environmental beats allowed by model but forbidden by prompt. |

---

## Done when

All 9 prompt pairs (18 templates + 10 shared sections) have been audited, progress recorded in ticket body, and issues documented.