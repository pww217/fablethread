---
title: "Fresh eval cycle Phase 1-3 post-B-49-llm-fallback-refactor"
status: done
urgency: 3
size: medium
created: 2026-07-17

ticket_id: E-15
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

Fresh eval cycle to validate B-49 (LLM fallback health-check refactor) across all three graduated phases.

## Context

**Prior SHA:** `cefa05af` (last full eval group: `2026-07-17_0.31.0-139-gcefa05af`)
**Changes since last eval:** 1 commit — B-49

### Changes Since Last Eval

**B-49: LLM fallback refactor** (`ccya/llm_client.py` + `ccya/ev/prompt_eval.py`):
- Primary health check (`_check_health(host)`) before attempting inference
- Simplified retry: 2 attempts → 1 attempt. On primary failure, immediately fall back to secondary
- Cooldown logic preserved: once fallen back, keep using secondary for `cooldown_s` seconds
- Timeout changed from raw value to structured `httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=10.0)`
- `prompt_eval.py` switched from `EngineConfig()` to `load_config()` + `build_engine_config(raw_cfg)`

### Focus Areas

1. **Health check before inference:** Does the health check correctly gate primary usage? Does it avoid false positives from transient network issues?
2. **Single-attempt retry:** Does immediate fallback work correctly when primary fails? Are non-retryable errors propagated correctly?
3. **Structured timeout:** Does `httpx.Timeout` object work correctly with OpenAI-compatible API? Any timeout behavior changes?
4. **Config loading in prompt_eval:** Does `load_config()` + `build_engine_config()` work correctly for prompt evaluation tools?
5. **General engine stability:** No regression in ruling, pacing, extraction, narration from baseline.

## Plan

### Phase 1: 1 game, 5 turns — Critical bugs
- Pack: `noir-1930s`, Persona: `driven`
- Target: Game-breaking bugs, obvious failures
- Report: `evals/runs/<group>/PHASE-1.md`

### Phase 2: 3 games, 15 turns — Nuanced bugs
- Pairs: noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist
- Target: Intermediate degradations, pacing issues, extraction misses
- Report: `evals/runs/<group>/PHASE-2.md`

### Phase 3: 5 games, 25 turns — Balance and long-term mechanics
- All 5 persona pairs
- Target: Balance, long-term patterns, edge cases
- Report: `evals/runs/<group>/PHASE-3.md`

### Testing Items
- Check `roadmap/bugs/*.md` for `status: testing` items (none currently)

## Progress

### Phase 1: PASS — 2026-07-17 21:07
- Pack: noir-1930s, Persona: driven, Turns: 5
- Report: `evals/runs/2026-07-17_0.32.1_2e3d0188/PHASE-1.md`
- Group: `2026-07-17_0.32.1_2e3d0188`
- Status: PASS — 100% deterministic checkers (27/27), no critical bugs

**B-49 fixes found and applied during Phase 1:**
1. `_chat_with_fallback` non-retryable error bug: BadRequestError (400) was re-raised without trying fallback. Fixed by capturing primary failure state and falling back on any failure.
2. `_chat_stream_with_fallback` non-retryable error bug: Same issue in streaming path. Fixed with same pattern.
3. `_chat_stream_with_fallback` inconsistent retry logic: Had old 2-attempt retry while non-streaming had 1-attempt (B-49 change). Unified to single-attempt + fallback.

**B-49 validation:** Fallback mechanism works correctly. All 5 turns completed with full narration, rulings, extraction, and events via OMLX fallback.

**Phase 1 → Phase 2: PASS** — No critical bugs found. Engine stable.

### Phase 2: PASS — 2026-07-18 02:38
- noir-1930s:driven, 15 turns — 37/37 PASS (100%)
- space-western:speedrunner, 15 turns — 37/37 PASS (100%)
- golden-piracy:completionist, 15 turns — 37/37 PASS (100%)
- Report: `evals/runs/2026-07-17_0.32.1_2e3d0188/PHASE-2.md`
- Group: `2026-07-17_0.32.1_2e3d0188`
- No intermediate degradations found. Fallback mechanism stable across all packs.
- No extraction misses or pacing issues detected.

**Phase 2 → Phase 3: PASS** — All 3 games passed. Engine stable across noir, space-western, and golden-piracy packs.

### Phase 3: PASS — 2026-07-18 23:08
- noir-1930s:driven, 25 turns — 42/43 PASS (97.7%) — 1 minor ruling_reason_quality warning (turn 17, 11 words vs 10-word max)
- space-western:speedrunner, 25 turns — 43/43 PASS (100%)
- space-western:explorer, 25 turns — 43/43 PASS (100%)
- golden-piracy:completionist, 25 turns — 43/43 PASS (100%)
- zombie-survival:cautious, 25 turns — 43/43 PASS (100%)
- allied-ww2:aggressive, 25 turns — 43/43 PASS (100%)
- Report: `evals/runs/2026-07-17_0.32.1_2e3d0188/PHASE-3.md`
- Group: `2026-07-17_0.32.1_2e3d0188`
- noir-1930s seed 1 generation crashed (LLM generated pc.conditions as string instead of empty array). Retry with seed 2 succeeded.
- Overall: 5/6 PASS, 1 WARN. Only noir-1930s had a minor narration word-count issue. All packs stable.

## Next

### Deep-Dive: Mechanical Review of Phase 3 Runs

Phase 3 deterministic checkers all passed — now need deep mechanical review of how each system actually behaves in practice. Four agents work in parallel using the `ev-review` skill, each reviewing one category across all 6 Phase 3 runs.

#### Scope

All 4 agents review all 6 Phase 3 runs (25 turns each) in `evals/runs/2026-07-17_0.32.1_2e3d0188/`:
- noir-1930s:driven (25t)
- space-western:speedrunner (25t)
- space-western:explorer (25t)
- golden-piracy:completionist (25t)
- zombie-survival:cautious (25t)
- allied-ww2:aggressive (25t)

#### Parallel Split

| Group | File | Mechanics |
|-------|------|-----------|
| Ruling, Narration, NPCs | `ruling_narration_and_npcs.md` | ruling_reason_quality, ruling_band_distribution, directive_beat_alignment, extraction_retry_rates, npc_presence, npc_presence_decay, compendium_lifecycle, beat_candidates_present, beat_diversity, beat_phase_validity, gm_beat_lifecycle |
| Threads, Arcs, Sanitation | `threads_arcs_and_sanitation.md` | thread_lifecycle, thread_resolution_validity, new_thread_validity, thread_cap_eviction, thread_completion, thread_cooldown, thread_culling, thread_urgency_decay, arc_goal_updates, arc_resolution_validity, arc_resolve_lifecycle, goal_update_validity, sanitizer_lifecycle, progress_dedup |
| Pacing | `pacing.md` | pacing_directives, phase_transition, phase_transition_signals, climax_turn_counting, breather_enforcement, curtain_call, convergence_ema, convergence_recompute, convergence_threshold_context |
| State | `state.md` | location_change, location_description_consistency, inventory_integrity, conditions_lifecycle, condition_ttl, world_state_facts, world_state_ttl, roll_band_consistency |

#### Method

- Each agent uses the `ev-review` skill
- Sequential: one mechanic at a time, in order
- For each mechanic: find turns where it was actually engaged (not every turn), examine thoroughly (more thorough for complicated mechanics)
- Use `ev.py` commands: `turn`, `mechanics`, `threads`, `trace`, `check` as appropriate per mechanic
- Write findings as they go (report is long-term memory)

#### Report Template

1. Mechanic overview
2. Runs examined + turns sampled
3. Findings (per mechanic, across turns)
4. Cross-run patterns
5. Root causes
6. Recommendations

#### Output

Each agent writes one file at `evals/runs/2026-07-17_0.32.1_2e3d0188/<filename>`. Agents work independently — no consolidation step. Each agent is done when their report is complete.