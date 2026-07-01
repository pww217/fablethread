---
title: "Engine core tech debt audit and cleanup"
status: up-next
urgency: 2
size: xlarge
created: 2026-06-29
ticket_id: I-17
labels:
  - engine
  - refactoring
  - type-safety
plan: plans/completed/state/i17-3-worldstate-plan.md
---

## Summary

Comprehensive audit of engine core (`ccya/engine/`, `ccya/state/`, `ccya/models/`, `ccya/llm_client.py`, `ccya/rules.py`) identified structural cleanup priorities. Each finding below is a separate investigation item to be labeled validated, false positive, or needs more investigation.

## Findings

### Critical

1. **Duplicated utilities** — `_strip_non_ascii` + `_NAME_RE` in `seed.py`, `generate_pack.py`, `delta_builder.py`. `_is_named` in `seed.py`, `npc_roster.py`, `state/npcs.py`. Consolidate into shared `ccya/utils.py`.

2. **Global mutable state** — `config.py` holds `_inflight`, `_cancel_requested`, `_turn_done` as module-level dicts/events. Couples save directories to global state, complicates concurrency and testing. Migrate to instance-scoped `TurnCoordinator`.

3. **`dict[str, Any]` state everywhere** — Pydantic models parsed but immediately cast to dicts. State access via `state.get("arc") or {}`, `state.get("meta", {}).get("turn", 0)`. Replace with structured `WorldState` model.

4. **Circular import workaround** — `state/delta.py` exists solely to re-export from `state/delta_builder.py`. Remove re-export layer, import directly.

5. **Boundary model gaps** — Every boundary model in `context.py` is out of sync with what templates actually consume. See I-18 for full list. Root cause is #3 (untyped dicts) — fields injected via dicts bypass type checking.

### Medium

6. **Jinja env caching** — `_build_jinja_env` called fresh every turn. `_env` passed as `Any` across `turn.py`, `ruling.py`, `narrate.py`, `world.py`. Cache per template_dir, type as `Environment`.

7. **Extraction pipeline DRY** — `pipeline.py` 351 lines, 3 near-identical stream blocks. Extract common pattern. Blocked on I-17 #3.

8. **Pacing consolidation** — `_pacing.py` 318 lines, one file doing one job. Real problem: dict coupling (#3). After #3, 318 lines is fine.

9. **LLM client parameter duplication** — `_chat_openai_compat`, `_chat_ollama_native`, `_chat_stream_ollama_native` all build parameter dicts with identical parameters. Extract common parameter building.

10. **Thread sanitizer coupling** — `thread_sanitizer.py` 505 lines, tightly coupled to raw dict state. Re-implements `_find_json` from config.py. See I-21 for dedicated ticket.

### Low

11. **Hardcoded magic numbers** — `dormant_threshold = 8`, `thread_max_active = 5`, `recent_beats_max = 5`. Move to config or constants module.

12. **Event logging scattered** — `append_event`, `append_prompts`, `append_chronicle` called at multiple lines in `turn.py`. Extract into `_persist_turn`.

13. **State mutation patterns** — `state.setdefault("meta", {})["turn"] = ...` in 10+ places. Define state accessors/mutators or use a state wrapper.

## Investigation Results

### Critical

1. **Duplicated utilities — VALIDATED**
    - `_strip_non_ascii` + `_NAME_RE` identically duplicated in `seed.py:22,37`, `generate_pack.py:18,21`, `delta_builder.py:21,27`. Also different implementations in `npc_roster.py:135` and `state/npcs.py:38`.
    - `_is_named` identically duplicated in `seed.py:25`, `npc_roster.py:14`, `state/npcs.py:15`.
    - Impact: Maintenance burden, risk of divergence. No bugs observed.
    - Fix: Consolidate into `ccya/engine/utils.py`.

2. **Global mutable state — VALIDATED (with nuance)**
    - `_inflight`, `_cancel_requested`, `_turn_done` are module-level dicts in `config.py:31-34`. Keyed by save_dir.
    - Server only manages one save at a time (`SAVE_DIR` global in `server/app.py:28`).
    - Impact: Hard to test (global state), stale entries accumulate if `signal_turn_done` not called on crash. No actual concurrency issues in production.
    - Fix: Move to instance-scoped `TurnCoordinator` or pass via `TurnContext`.

3. **`dict[str, Any]` state everywhere — DONE (2026-07-01)**
    - State accessed via `state.get("arc") or {}`, `state.get("meta", {}).get("turn", 0)` in 100+ locations.
    - Pydantic models in `models/state.py` and `models/extraction.py` parsed but immediately cast to dicts.
    - Impact: No type safety, no validation, easy to introduce bugs with typos.
    - Fix: Create structured `WorldState` Pydantic model for engine-internal use.
    - **Result:** See [Result: I-17 #3 WorldState Migration](#result-i-17-3-worldstate-migration) below. 7 commits, 5 phases, plan in `plans/completed/state/i17-3-worldstate-plan.md`.

4. **Circular import workaround — RESOLVED**
    - `state/delta.py` was 38 lines of lazy re-exports from `state/delta_builder.py`.
    - Removed `state/delta.py`, updated `state/__init__.py` to import directly from `delta_builder.py`.
    - Impact: Eliminated unnecessary indirection layer.
    - Fix: Done — `state/delta.py` deleted, `state/__init__.py` updated.

5. **Boundary model gaps — VALIDATED (symptom of #3)**
    - Every boundary model in `context.py` is out of sync with what templates actually consume. See I-18 for full list.
    - Root cause: fields injected via dicts bypass type checking. Fixing #3 will naturally resolve many of these.
    - Impact: Type safety promises are broken — dead/missing fields never caught by mypy.
    - Fix: Create `WorldState` model (#3), wire boundary models through it. I-18 handles the audit; I-17 #3 resolves the root cause.

### Medium

6. **Jinja env caching — VALIDATED**
    - `_build_jinja_env` creates fresh `Environment` + `FileSystemLoader` every call. Called in `turn.py:75` (every turn), `seed.py:226,558`, `generate_pack.py:68`, `thread_sanitizer.py:62`, eval checkers.
    - `_env` passed as `Any` across `turn.py`, `ruling.py`, `narrate.py`, `world.py`.
    - Impact: Unnecessary object creation every turn. No functional bug.
    - Fix: Cache per `template_dir`, type as `Environment`.

7. **Extraction pipeline DRY — VALIDATED**
    - `pipeline.py` 351 lines, 3 near-identical stream blocks (lines 71-123, 126-191, 194-276). Each: build messages → trim → `_call_stream()` → yield phase_done + panel_update → build `_preview` via `copy.deepcopy` + `apply_delta`.
    - Only differences: message builder function, result type, delta fields.
    - Impact: Hard to add new streams, hard to test individual streams. Not a bug — just 3x copy-paste.
    - Fix: Extract generic `_run_extraction_stream` function. Blocked on I-17 #3 (typed state makes streams cleaner).

8. **Pacing consolidation — VALIDATED**
    - `_pacing.py` 318 lines: `_compute_scene_phase()` (95-line if/elif chain), `_compute_pacing_context()` (46 lines), `compute_convergence_score()` (77 lines), `_compute_narration_directive()` (24 lines).
    - Not actually scattered — `_pacing.py` is the canonical home. Only "scattered" part is 6 lines of EMA smoothing in `narrate.py:209-215`.
    - Real problem: `_compute_scene_phase()` reads `state.get("arc") or {}` directly (lines 236-248). Tightly coupled to dict state.
    - Impact: After I-17 #3, this becomes a pure function on typed models and 318 lines is fine.
    - Fix: Create `WorldState` model (#3), then `_compute_scene_phase` takes `Scene` and `Arc` models.

9. **LLM client parameter duplication — VALIDATED**
    - `_chat_openai_compat`, `_chat_ollama_native`, `_chat_stream_ollama_native` all build parameter dicts with identical parameters (temperature, top_p, frequency_penalty, seed, num_ctx).
    - Impact: Minor maintenance burden. No bugs.
    - Fix: Extract `_build_chat_kwargs` helper.

10. **Thread sanitizer coupling — VALIDATED**
    - `thread_sanitizer.py` 505 lines, takes `state: dict[str, Any]`, accesses `state.get("meta")`, `state.get("arc")`, `state.get("world_state_candidates")`, `state.get("scene", {}).get("world_state")`.
    - Re-implements `_find_json` from config.py.
    - Impact: Tightly coupled to dict structure, hard to test in isolation. Self-contained module with real maintenance burden.
    - Fix: Pass structured `LongTermObjective` and `ArcThread` models. See I-21 for dedicated ticket.

### Low

11. **Hardcoded magic numbers — PARTIALLY VALIDATED**
    - `dormant_threshold = 8` in `turn_state.py:116` is hardcoded. Should be in config.
    - `recent_beats_max` and `thread_max_active` are in config with defaults, but `ruling.py:225` has redundant fallback `or 5`.
    - Impact: Minor config inconsistency.
    - Fix: Move `dormant_threshold` to config, remove redundant `or 5` fallbacks.

12. **Event logging scattered — VALIDATED**
    - `append_prompts` at lines 461, 577; `append_chronicle` at 463; `append_event` at 581; `save_state` at 582.
    - Comment at line 480 notes deferred persistence.
    - Impact: Hard to follow persistence logic, risk of missing a write.
    - Fix: Extract into `_persist_turn`.

13. **State mutation patterns — VALIDATED**
    - `state.setdefault(...)` used in 41+ locations. Patterns: `state.setdefault("meta", {})["turn"] = ...`, `state.setdefault("scene", {})["world_state"] = ...`, `state.setdefault("arc", {})`.
    - Impact: Repetitive, error-prone, easy to introduce bugs with typos.
    - Fix: Define state accessors/mutators or use a state wrapper.

## Cross-ticket links

### I-17 #3 ↔ I-2 (boundary model gaps)

I-17 #3 (`dict[str, Any]` state) is the root cause of I-2's boundary model findings. I-2 identified dead/missing fields in every boundary model:

- `RulingBoundary`: dead `scene_phase`, missing `pc_situation`/`beat_candidates`
- `NarratorBoundary`: dead `ages`, `resolved_arcs`, `arc_hint_text`, `arc_pressure_score`; `curtain_call` not rendered
- `SceneExtractBoundary`: missing `show_all_fields`; `NPCRosterEntryBlock` type mismatch (5 missing fields)
- `StateExtractBoundary`: missing `pc_name`, `pack_inventory`
- `StorytellerBoundary`: 11 dead fields
- `WorldBoundary`: doesn't exist

These are symptoms of I-17 #3 — the boundary models are typed Pydantic models but fields are injected via dicts outside the boundary system, so type checking never catches the mismatches.

### I-17 #7 ↔ I-19 (extraction pipeline)

I-17 #7 (extraction pipeline, 351 lines) is a DRY violation — 3 near-identical stream blocks. It's not a separate ticket; after I-17 #3 the common pattern extraction is straightforward.

### I-17 #10 ↔ I-21 (thread sanitizer)

I-17 #10 (thread sanitizer, 505 lines) is a separate ticket I-21 because it's a self-contained module with real maintenance burden. It's tightly coupled to dict state (#3) and would benefit from the `WorldState` model.

### I-17 #8 (pacing)

I-17 #8 (pacing consolidation, 318 lines) is not a separate ticket. It's one file doing one job. After I-17 #3, `_compute_scene_phase` becomes a pure function on typed models and the 318 lines are fine.

**Execution order:** I-18 first (prompt-only, low risk). I-17 #3 (root cause for boundary models). I-19 (phased subroutines) after #3. I-17 #5 (Jinja caching) is independent and can run in parallel. I-21 (thread sanitizer) can run after #3. I-17 #7 (pipeline DRY) and #8 (pacing) are mechanical refactors after #3.

---

## Result: I-17 #3 WorldState Migration

**Completed:** 2026-07-01. **Branch:** `i17-3-worldstate`. **Plan:** `plans/completed/state/i17-3-worldstate-plan.md`.

### What was built

- **`WorldState` Pydantic model** in `ccya/models/state.py` — typed root model with section models (`Meta`, `PC`, `Scene`, `NPCEntry`, `Compendium`, `LongTermObjective`, `World`). `from_dict()` / `to_dict()` for YAML round-trip. `seed_meta` field added (renamed from `__seed_meta__`).
- **21 typed mutators** on `WorldState` — immutable pattern, each returns new `WorldState`. Covers turns, beats, rolls, history, compendium, conditions, world_state, NPC lifecycle.
- **I/O** — `load_state()` / `save_state()` / `init_save_dir()` / `default_world_state()` in `ccya/state/io.py`.
- **Engine migration** — 51+ functions across `engine/turn.py`, `engine/turn_state.py`, `engine/narrate.py`, `engine/ruling.py`, `engine/world.py`, `engine/thread_sanitizer.py`, `engine/extraction/`, `state/delta_builder.py`, `state/npcs.py` now take `WorldState` (not `dict[str, Any]`).

### Pre-existing bugs found and fixed

- **`world_state_candidates` nested in `meta`** — was written to `state.meta.world_state_candidates` in `turn_state.py` and `thread_sanitizer.py`; it's a top-level `WorldState` field. Data was lost every turn. Fixed.
- **`isinstance(entry, dict)` guards always False** — NPC decay/archive and location-change logic guarded on dict but received typed `NPCEntry` models. The logic never ran. Fixed.
- **`presence: "archived"` not in `NpcPresence` enum** — used as raw string, would have failed validation. Added `ARCHIVED` value.
- **Stale `comp` reference in `turn_state.py:480`** — captured before loop, not refreshed after `add_npc()`/`update_npc()`. Duplicate NPC IDs would re-add instead of update. Fixed during Phase 04 review.
- **`__seed_meta__` → `seed_meta`** — renamed; old name was dunder-style and bypassed type checking. Updated both seed builders and all readers (`panels.py`, `routes.py`, `tv.py`).

### Runtime gaps found via eval (post-cleanup)

- **`WorldState.from_dict` set `{}` for list fields** — `resolved_arcs` and `world_state_candidates` got empty dicts instead of empty lists when `SeedState.model_dump()` was passed through. Caused `ValidationError`. Fixed.
- **Jinja templates received Pydantic models** — `_inventory.j2` uses `.get()` which fails on Pydantic models. Dumped to dicts at template boundary in `narrate.py`.
- **`event["last_turn_state"]` stored Pydantic model** — `json.dumps` with `default=str` fell back to `str(state)`. Downstream consumers expected dict. Fixed in `turn.py`.

### Commits

| Commit | Phase |
|--------|-------|
| `2c46be3` | Phase 01: `WorldState` model + section models |
| `8edbef9` | Phase 03: migrate read access to `WorldState` |
| `d1cf461` | Phase 04: 21 typed mutators |
| `5ae396c` | Plan housekeeping |
| `6abf413` | Phase 04 review: fix stale `comp` reference |
| `082f2dd` | Phase 05: cleanup (rename `_default_state` → `default_world_state`) |
| `a881f14` | Phase 05 review: fix 3 runtime gaps found via eval |

### Verified

- `make check` passes (ruff + mypy + pack YAML + vulture, 100 files).
- 2 successful 3-turn LLM evals (noir:driven, space-western:speedrunner). No runtime errors.

### Docs updated

- `docs/architecture/state-models.md` — `WorldState` model entry, typed mutator table, I/O section. Fixed `__seed_meta__` → `seed_meta`, corrected `NpcPresence` description.
- `docs/repomap.md` — `ccya/state/io.py` entry includes `default_world_state()`.
- `AGENTS.md` — State model signpost (immutable, typed mutators).

### Remaining

- **No PR yet** — branch `i17-3-worldstate` ready for PR to `main`.
- **Other I-17 findings (#1, #2, #6–#13) remain open** — see Findings section above. Finding #3 was the root cause for I-2 (boundary model gaps) per cross-ticket links.
