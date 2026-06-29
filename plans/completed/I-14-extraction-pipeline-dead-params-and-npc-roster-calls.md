# Extraction pipeline dead params and npc_roster calls

**Ticket:** `roadmap/improvements/I-14-extraction-pipeline-dead-params-and-npc-roster-calls.md`
**Status:** completed (Phase 01 executed, Phase 2 marked won't do)

## Phase Summary

One phase. Removes dead parameters from the extraction pipeline (`pacing_context`, `rules_outcome` → `band`). Phase 2 (cache `build_npc_roster()`) marked won't do — narrate needs a different roster shape (no personality) than ruling/scene/world, and caching would require passing different versions to different consumers.

---

## Phase 01: Remove dead parameters from extraction pipeline

**Files:** `ccya/engine/turn.py`, `ccya/engine/extraction/pipeline.py`

### What

1. **Remove `pacing_context` from `_run_extraction_pipeline()` signature** (`pipeline.py:46`).
2. **Remove `pacing_context=_pc` from call site** (`turn.py:263`).
3. **Replace `rules_outcome=_outcome` with `band=_band`** — extract `_band = _outcome.band if _outcome and _outcome.rolled else ""` before the pipeline call, pass `band=_band` instead of the full `RulesOutcome` object.
4. **Update `_run_extraction_pipeline()` signature** — remove `rules_outcome: "RulesOutcome | None" = None`, add `band: str = ""`.
5. **Update pipeline internal** — remove `pipeline.py:197` line `_band = (rules_outcome.band if rules_outcome and rules_outcome.rolled else "")`, use the `band` parameter directly.
6. **Keep `intent`** — it is used by `extract_state_user.j2:10-12`.

### Why

`pacing_context` is never consumed by any extraction stream. `record_user.j2` doesn't reference it. World reads `pacing_context` directly from `turn.py`. `rules_outcome` is over-passed — only `band` is extracted, and it's already computed at the call site.

### Validation

- `pipeline.py` has no `pacing_context` parameter.
- `turn.py` doesn't pass `pacing_context` to `_run_extraction_pipeline()`.
- `pipeline.py` uses `band` parameter directly instead of extracting from `rules_outcome`.
- `intent` still flows through pipeline to `_extract_state_messages()`.
- Server still starts and processes turns without errors.

---

## Phase 02: Cache build_npc_roster() in TurnContext

**Files:** `ccya/engine/turn_context.py`, `ccya/engine/turn.py`, `ccya/engine/ruling.py`, `ccya/engine/narrate.py`, `ccya/engine/extraction/scene.py`, `ccya/engine/world.py`

### What

1. **Add `npc_roster` field to `TurnContext`** — a `list[dict[str, Any]] | None` defaulting to `None`.
2. **Compute `npc_roster` once in `run_turn()`** — after ruling phase completes, call `build_npc_roster()` with `personality_registry=ARCHETYPES` and store on `ctx.npc_roster`.
3. **Update ruling phase** — pass `npc_roster=ctx.npc_roster` to `_ruling_messages()` instead of calling `build_npc_roster()` directly.
4. **Update narrate phase** — pass `npc_roster=ctx.npc_roster` to `_narrate_messages()` instead of calling `build_npc_roster()` directly. Remove the default fallback `build_npc_roster()` call in `_narrate_messages()` (line 53).
5. **Update scene extraction** — pass `npc_roster` via `state` or a new parameter. Since scene extraction happens inside the pipeline (not via `TurnContext`), create a `npc_roster` field on `TurnContext` that the pipeline can access, or pass it through `ctx.packing`-style mechanism.
6. **Update world step** — pass `npc_roster` via `state` or a new parameter. Same constraint as scene — world runs inside the pipeline.

### Why

`build_npc_roster()` is called 4 times per turn with identical inputs (filter+sort+score compendium.npcs). Computing once and sharing eliminates redundant work.

### Constraint

Narrate calls `build_npc_roster()` with `personality_registry=None` (line 274) while ruling and scene use `ARCHETYPES`. World also uses `ARCHETYPES`. The narrate call is for the `npc_roster` parameter specifically — it passes `None` for personality_registry. This means the cached roster won't have personality labels resolved for narrate.

**Decision:** Use `ARCHETYPES` for the cached roster. Narrate's `personality_registry=None` was an optimization that avoided personality lookup when not needed — but narrate's template `_npc_roster.j2` does render personality fields when available. Passing `ARCHETYPES` is correct and consistent with all other callers.

### Validation

- `build_npc_roster()` called exactly once per turn in `run_turn()`.
- All 4 consumers (ruling, narrate, scene, world) receive the cached roster.
- Narrate template renders personality fields correctly with `ARCHETYPES`-enriched roster.
- Server still starts and processes turns without errors.

### [QUESTION: Scene and world extraction streams]

Scene extraction (`scene.py:22`) and world (`world.py:46`) run inside the extraction pipeline, which doesn't have direct access to `TurnContext`. Two options:

**Option A (Recommended):** Add `npc_roster` to `TurnContext`, pass it via a new `npc_roster` parameter to `_run_extraction_pipeline()`, then thread it through to `scene.py` and `world.py`. This is the cleanest approach — one parameter addition, minimal refactoring.

**Option B:** Add `npc_roster` to `ctx.packing` dict. This piggybacks on an existing mechanism but pollutes the packing namespace with engine-internal data.

Choose Option A unless there's a reason packing is preferred.

---

## Documentation updates

- `docs/architecture/OVERVIEW.md` — update pipeline I/O table to reflect `pacing_context` removal and `band` direct parameter.
- `docs/architecture/step2d-world.md` — update inputs table to reflect `npc_roster` from `TurnContext` instead of computed internally.
- `docs/architecture/step2a-scene.md` — update inputs table to reflect `npc_roster` from `TurnContext` instead of computed internally.
- `docs/repomap.md` — update `_run_extraction_pipeline()` signature description.
- `docs/architecture/cross-pipeline.md` — update flow diagram if it shows `pacing_context` flowing through extraction pipeline.
