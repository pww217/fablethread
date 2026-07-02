---
title: "Engine core tech debt consolidation (I-17 follow-up)"
status: implemented
urgency: 2
size: large
created: 2026-07-02
ticket_id: I-23
labels:
  - engine
  - tech-debt
  - refactoring
---

# I-23: Engine core tech debt consolidation

## Summary

Consolidate remaining I-17 tech debt findings into a single execution ticket. I-17 was a comprehensive audit; most findings are done or blocked. This ticket executes the remaining items in dependency order.

Excluded (design changes, not tech debt): I-4 (difficulty frequency), I-22 (world beats on phase transitions), I-20 (NPC roster personality), I-19 (seed threads).

## Remaining findings from I-17 audit

### 6. Jinja env caching (independent, low risk)

`_build_jinja_env` creates a fresh `Environment` + `FileSystemLoader` every call. Called in `turn.py:77` (every turn), `seed.py:226,573`, `generate_pack.py:68`, `thread_sanitizer.py:61`, eval checkers, ev/prompt_eval.py. `_env` passed as `Any` across `turn.py`, `ruling.py`, `narrate.py`, `world.py`.

**Fix:** Cache per `template_dir` using a module-level dict keyed by path. Type as `jinja2.Environment`.

### 9. LLM client parameter duplication (independent, low risk)

`_chat_openai_compat`, `_chat_ollama_native`, `_chat_stream_ollama_native` all build parameter dicts with identical parameters (temperature, top_p, frequency_penalty, seed, num_ctx).

**Fix:** Extract `_build_chat_kwargs` helper that takes the common params and returns the dict.

### 11. Hardcoded magic numbers (independent, low risk)

`dormant_threshold = 8` hardcoded in `turn_state.py:116`. `thread_max_active` and `recent_beats_max` are already in `EngineConfig` (config.py:182, 149).

**Fix:** Move `dormant_threshold` to `EngineConfig` as `thread_dormant_threshold`, replace the local constant in `turn_state.py:116`.

### 13. State mutation patterns (low risk, limited scope)

`setdefault` used in 34 locations. Most are in `ev/` scripts (config building, audit data) or `server/routes.py` (seed state building). Engine core has only 1 usage: `turn.py:825` (`final_metrics.setdefault(...)`).

**Fix:** The engine core usage is already clean (metrics dict, not state dict). The ev/ and server/ usages are config/seed building, not engine state mutation. No engine core changes needed.

### 2. Global mutable state (medium risk, highest impact)

`config.py:32-34` holds `_inflight`, `_cancel_requested`, `_turn_done` as module-level dicts/events keyed by save_dir. Server only manages one save at a time (`SAVE_DIR` global in `server/app.py:28`), so there are no actual concurrency issues in production. Stale entries accumulate if `signal_turn_done` not called on crash.

**Fix:** Move state from `config.py` to `server/app.py` (server owns state). Pass cancel signal via `TurnContext._cancel_event` to engine. See plan: `plans/I-23-global-state-migration-plan.md`. Eliminates 97 lines from config.py, removes 15+ engine state access call sites.

### 7. Extraction pipeline DRY (blocked on WorldState, medium risk)

`pipeline.py` 352 lines, 3 near-identical stream blocks (scene, state, record). Each: build messages → trim → `_call_stream()` → yield phase_done + panel_update → build `_preview` via `copy.deepcopy` + `apply_delta`. Only differences: message builder function, result type, delta fields.

**Fix:** Extract generic `_run_extraction_stream` function + `_ExtractionVariant` dataclass. See plan: `plans/I-23-extraction-pipeline-dry-plan.md`. Reduces pipeline.py from 352 to ~110 lines.

### 8. NPC personality field (low risk, medium scope)

`personality` field on `NPCEntry` (plus `personality_label`, `personality_traits`) is a label that duplicates what motivation/fear/leverage/ties already express. Costs ~100-200 tokens/turn in roster context plus extraction overhead. The `personality.py` module (203 lines) assigns archetypes based on motivation+fear keyword matching — the behavioral drivers *are* the personality.

**Fix:** Remove personality from state model, delete `personality.py` module, update all prompts/templates/ev scripts. See plan: `plans/I-24-remove-npc-personality-field-plan.md`. Eliminates 203 lines + ~500 tokens/turn.

## Execution order

### Phase 1: Independent, low-risk (no behavioral change)

1. **Jinja env caching** — module-level dict keyed by template_dir path, type as `Environment`. Zero behavioral change.
2. **LLM client param duplication** — extract `_build_chat_kwargs` helper. Zero behavioral change.
3. **Hardcoded magic numbers** — add `thread_dormant_threshold` to `EngineConfig`, replace local constant in `turn_state.py`. Zero behavioral change.

### Phase 2: Medium-risk (careful testing needed)

4. **Global mutable state** — choose approach A or B. This is the highest-impact change. Approach B (TurnContext) is safer for a first pass.

### Phase 3: Structural refactor

5. **Extraction pipeline DRY** — extract `_run_extraction_stream` from `pipeline.py`. Requires understanding all 3 stream variants. WorldState model is already in place.

## Files touched

| Phase | Files |
|-------|-------|
| 1 | `config.py` (Jinja cache + new config field), `llm_client.py` (helper), `turn_state.py` (remove local constant) |
| 2 | `config.py` (remove module-level state), `turn_context.py` (add state fields), `turn.py` + callers |
| 3 | `extraction/pipeline.py` (extract common pattern) |

## Done when

- All 5 phases implemented
- `make check` passes (lint + typecheck)
- Server starts and `/`, `/turn_viewer`, `/turn_viewer/stream` return 200
- `docs/repomap.md` updated if any module boundaries change
- `AGENTS.md` updated if any signatures change
- `/ev-run` cycle completes (1-5 turns critical) — report findings, fix minor things, watch for code bloat
- UI verification: main page (`/`) loads correctly including CSS and JS
- UI verification: turn viewer (`/turn_viewer`) loads correctly including CSS and JS
- API verification: all server routes return valid responses (no 500s)

## Evals & Review Process

Evals will run continuously until all features are stable and prompt input/output flow is confirmed correct — especially user prompts rendering correctly. Use the EV tool (`ev.py`) for this.

**Rules:**
- No major design overhauls during evals
- Core mechanical changes: yes
- Feature work: yes
- Bug fixes: yes
- Fine-tuning/balancing: yes
- Focus on pipeline and core engine above all, especially narrative mechanics
- Fix every kind of issue seen on the rubric
- Don't trust checkers blindly — they can be false positives
- Use `/ev-review` on existing saves for deep dives into problem areas — comprehensive, every nook and cranny
- Take your time

**Review before evals:** Each change (I-23 phases, I-24) must be reviewed before running evals. Use `ev-review` skill for focused deep-dives.

## TODO

- [x] Phase 1.1: Jinja env caching
- [x] Phase 1.2: LLM client param duplication
- [x] Phase 1.3: Hardcoded magic numbers
- [x] Phase 2: Global mutable state (plan: `plans/I-23-global-state-migration-plan.md`)
- [x] Phase 3: Extraction pipeline DRY (plan: `plans/I-23-extraction-pipeline-dry-plan.md`)
- [x] Phase 4: NPC personality field removal (plan: `plans/I-24-remove-npc-personality-field-plan.md`)
- [ ] Review each change before evals (use ev-review skill)
- [ ] Run `/ev-run` cycle (1-5 turns critical)
- [ ] Verify main UI loads (CSS + JS)
- [ ] Verify turn viewer loads (CSS + JS)
- [ ] Verify all API endpoints work
- [ ] Continuous evals until features stable (focus: pipeline, core engine, narrative mechanics)
- [ ] Fix all rubric issues (don't trust checkers blindly, use ev-review for deep dives)
