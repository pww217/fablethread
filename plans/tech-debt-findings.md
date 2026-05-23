# Technical Debt & Anti-Pattern Inventory

Validated against source code at commit `HEAD` (2026-05-23). Each finding includes:
- **Severity**: P0 (breaks game) → P4 (cosmetic/polish)
- **Effort**: estimated person-hours to clean up
- **Risk**: what could go wrong during cleanup

---

## P0 — Breaking Bugs

### 1. Unclosed `{% if %}` in `compact_user.j2`

- **File**: `ccya/prompts/compact_user.j2:11`
- **What**: The `{% if arc and (arc.get('threads') or []) -%}` opened at line 11 never gets an `{% endif %}`. All subsequent content (inventory, compendium, conditions) is parsed as inside the unclosed conditional. Jinja raises `"Unexpected end of template"` on every compaction turn.
- **Impact**: T3, T6, T9, T12 all hit TURN_PROCESSING_FAILED. Game breaks on compaction turns.
- **Effort**: 5 minutes — add `{% endif -%}` after line 25.
- **Risk**: None. Straightforward syntax fix.

### 2. `reconcile_delta()` Mutates Parameter In-Place

- **File**: `ccya/state/delta.py:84`
- **What**: Modifies `delta.inventory_add` and `delta.pc_condition_add` in-place while also returning warnings. The caller (`turn.py:1165`) has no way to distinguish between "warnings about what was changed" and "these are the changes" because the return type (`list[str]`) conflates both.
- **Impact**: Makes reasoning about delta application fragile. If the caller later reads delta fields, they reflect the reconciled (mutated) version — not what the LLM originally produced.
- **Effort**: 1 hour — return a new reconciled delta instead of mutating in-place.
- **Risk**: Low — callers already consume warnings independently; only one call site.

### 3. `inventory_remove` Allows Removing Non-Existent Items

- **File**: `ccya/engine/turn.py:1505-1515` (validation produces `warn_missing_item` rejection), but `ccya/state/delta.py:182-185` silently continues when `resolve_inventory_remove_target` returns None
- **What**: The validation in `_validate()` flags missing items as a non-blocking rejection (`kind: warn_missing_item`), and `apply_delta()` (delta.py:182-185) silently skips them. The item is removed from the story but never existed in state — silent state-story desync.
- **Impact**: Allowed the "ledger phantom" bug in the eval run (item added narratively, never in state, removed silently later, re-added later still).
- **Effort**: 2 hours — make `_validate()` return `blocking` for missing inventory removes, or add a pre-check before `apply_delta()` that warns. Also need to fix the actual root cause (extraction misses).
- **Risk**: Medium — changing rejection severity may break existing game saves that rely on the current behavior.

---

## P1 — Structural Decay (Monoliths, Dead Code, Leaky Abstractions)

### 4. `run_turn()` Is an 800-Line Async Generator Monolith

- **File**: `ccya/engine/turn.py:654-1457`
- **What**: `run_turn()` handles: ruling, dice resolution, narration, memory loading, extraction pipeline orchestration, delta application, arc thread management (signals, resolutions, adds), narrator arc update extraction, condition aging, NPC stamping, recently_left decay, persisting (3 file writes), compaction, error recovery, metrics aggregation, and SSE event yielding. ~15 distinct responsibilities.
- **Impact**: Impossible to unit test individual phases. Error recovery (finally block, line 1456) is the only clean boundary. Adding new pipeline steps requires understanding the entire control flow. The `try/except/finally` wrapping the entire body makes partial-failure recovery opaque.
- **Effort**: 8-12 hours — extract each pipeline phase into its own async function, compose in `run_turn()`. Phases: Ruling → Narrate → Extract → ValidateApply → ArcThreads → Persist → Compact.
- **Risk**: High — `run_turn()` has complex control flow with `AsyncIterator` yielding. Refactoring risks breaking the yield protocol that the SSE stream depends on.

### 5. `apply_delta()` Is a 420-Line Function with Nested Closures

- **File**: `ccya/state/delta.py:125-545`
- **What**: Contains 5 closures defined inside the function body (`_by_id`, `_hydrate_npc_text`, `_resolve_npc_id`, `_find_npc_by_name`, `_apply_npc_to_present`) that together handle inventory, location, conditions, scene events, NPCs, and arc updates. NPC scene management alone is ~220 lines (lines 323-539).
- **Impact**: Closures capture `state`, `comp`, and other locals, making the function hard to reason about. The NPC management section is a module-sized block that can't be independently tested.
- **Effort**: 4-6 hours — extract closures to module-level functions with explicit parameters. Split NPC management into `state/npcs.py`.
- **Risk**: Medium — closet functions access enclosing scope variables; extracting them requires threading all dependencies as parameters.

### 6. `apply_thinking()` Is a No-Op Called from 6 Locations

- **File**: `ccya/llm_client.py:142-145` (function body: `return [dict(m) for m in messages]` regardless of `enable` parameter)
- **Call sites**: `ccya/engine/extraction.py:288/321/381`, `ccya/engine/ruling.py:71`, `ccya/engine/narrate.py:122`
- **What**: The function was intended to inject `<think>` XML tags for model reasoning, but the implementation is a no-op that copies messages and ignores the `enable` flag. All 6 call sites pass either `config.enable_extract_thinking`, `config.enable_narrate_thinking`, or hardcoded `False` — all of which are ignored.
- **Impact**: 6 dead code paths. Misleading API surface — any reader would assume thinking injection is functional. Two config keys (`enable_extract_thinking`, `enable_narrate_thinking`) control nothing.
- **Effort**: 30 minutes to remove the no-op and the config keys, or 2-4 hours to actually implement thinking injection.
- **Risk**: Low if removing. Medium if implementing (may change LLM output quality).

### 7. 101 Lines of Mock Infrastructure in Production LLM Client

- **File**: `ccya/llm_client.py:25-126`
- **What**: `_MOCK_MODE` env var gates 101 lines of mock data and mock stream classes mixed directly into the production module. The mock code interleaves with production logic via `if _MOCK_MODE:` checks on lines 218 and 257.
- **Impact**: Increases cognitive load. Breaks the principle that production code shouldn't contain test infrastructure. 33% of the file is dead code during normal operation.
- **Effort**: 1-2 hours to extract mocks into `tests/mocks.py` or a separate `ccya/llm_mock.py`.
- **Risk**: Low — purely mechanical extraction.

### 8. Triple-Duplicated Averaging Functions

- **Files**: `ccya/engine/extraction.py:791-834`, `ccya/engine/ruling.py:123-142`
- **What**: `_avg_narrate_ms()` (extraction.py:791), `_avg_extract_ms()` (extraction.py:814), and `_avg_ruling_ms()` (ruling.py:123) are structurally identical — each reads `events.jsonl`, parses the last N lines, extracts a specific JSON field, and averages. Only the field path differs (`narrate.total_ms`, `extract.total_ms`, `ruling.total_ms`).
- **Impact**: Copy-paste code. Adding a fourth metric type requires duplicating the pattern again. Any bug fix to the averaging logic must be applied to all three.
- **Effort**: 1 hour — parameterize into a single `_avg_event_ms(save_dir, field_path, n=5)` function.
- **Risk**: None — pure mechanical extraction.

### 9. 4 Dead `EngineConfig` Fields

- **File**: `ccya/engine/config.py:67-77`
- **Fields**: `thread_urgency_building_at`, `thread_urgency_immediate_at`, `thread_urgency_immediate_ttl`, `avoidance_decay_per_turn`
- **What**: All four fields are defined in the dataclass, set in `build_engine_config()`, and configurable in `config.yaml`, but **never read** by any application code. They are remnants of the old urgency escalation system, replaced by `ArcThread.urgency` enum values from the storyteller extraction stream.
- **Impact**: Misleading config surface area. Users may set keys that do nothing. Any future refactor must remember to skip these dead fields.
- **Effort**: 30 minutes — remove fields from `EngineConfig`, `build_engine_config()`, and `config.yaml`.
- **Risk**: Low — nothing depends on them.

---

## P2 — Design & Boundary Issues

### 10. Circular Dependency Between `engine` and `state` Packages

- **File**: `ccya/engine/extraction.py:74` — `from ccya.state.delta import apply_delta  # local import to avoid circular deps`
- **Also**: `ccya/engine/turn.py:65` — `from ccya.state.delta import _merge_arc_update` (imports a private function)
- **What**: The engine package imports from state to apply deltas during the extraction pipeline (to simulate state for the storyteller stream). The state package doesn't import from engine, so the circular dependency manifests only in one direction — but the local import is a code smell that the module boundary is wrong.
- **Impact**: The local import pattern breaks at the module level (the function body import works but is non-standard). Importing a private `_merge_arc_update` from another package violates encapsulation.
- **Effort**: 4-6 hours — move `_build_extraction_context()` to `state/` or create a shared `ccya/engine/delta.py` module that both engine and state can import.
- **Risk**: Medium — the extraction context build process (`_build_extraction_context`) is tightly coupled to both engine and state logic.

### 11. Server Routes Tightly Coupled to App Module via `sys.modules`

- **File**: `ccya/server/routes.py:44` — `_app_mod = sys.modules["ccya.server.app"]`
- **What**: Every route handler accesses app globals (`SAVE_DIR`, `engine_config`, `_active_pack`, etc.) through this backdoor reference instead of FastAPI's `app.state` or dependency injection. This creates hard coupling between routes and the app module's internal state.
- **Impact**: Routes can't be tested without the full server bootstrap. Any change to app module's variable names breaks routes silently at runtime (no static type checking because all access is via `_app_mod.X` string attribute access).
- **Effort**: 3-4 hours — move shared state into FastAPI `app.state` on startup, inject via `Request.app.state` in route handlers.
- **Risk**: Low — mechanical refactoring that doesn't change behavior.

### 12. Duplicated Coercion Validators Across Models

- **Files**: `ccya/models.py`
- **What**:
  - `StateDelta._coerce_inventory_remove` (line 240) and `StateExtractResult._coerce_inventory_remove` (line 342) — identical logic
  - `StateDelta._coerce_condition_add` (line 272) and `StateExtractResult._coerce_condition_add` (line 355) — identical logic  
  - `StateDelta._coerce_condition_remove` (line 279) and `StateExtractResult._coerce_condition_remove` (line 362) — nearly identical (differ only in punctuation stripped)
- **Impact**: Fixing a coercion bug requires edits in two places. The condition-remove validators have subtly different punctuation-stripping logic, which is almost certainly a latent bug.
- **Effort**: 1 hour — extract shared validators to module-level functions, reference via `@field_validator(mode="before")` on both models.
- **Risk**: Low — pure mechanical extraction.

### 13. No State Schema Versioning

- **File**: `ccya/state/io.py:28-78`
- **What**: `_default_state()` has no `version` or `schema_version` field. The IO layer already has a backwards-compatibility shim (line 87-92, regex fix for `!!python/object/apply:ccya.models.ThreadState` tags from old YAML dumps), proving the schema has evolved without a versioning mechanism.
- **Impact**: Any future schema change requires more ad-hoc regex fixes. No way to detect or reject incompatible state files. Silent data corruption risk.
- **Effort**: 2-3 hours — add schema version to state, add a migration registry, handle legacy file reading.
- **Risk**: Low — additive change; legacy files without version field can be default-assumed to version 0.

### 14. `NPC_SCENE_CAP` Hardcoded as Local Variable, Not Config Knob

- **File**: `ccya/state/delta.py:324` — `NPC_SCENE_CAP = 8`
- **Also**: `ccya/eval/engine_mirror.py:42` — `SCENE_NAMED_NPC_CAP: int = 8` (duplicates the hardcoded value)
- **What**: The cap is a local variable inside `apply_delta()`, not a module-level constant or config field. The eval mirror duplicates the value as a separate constant.
- **Impact**: Changing the cap requires finding two locations. No config surface for users. The `PC_CONDITIONS_MAX` at delta.py:61 is at least a module-level constant, but also not configurable.
- **Effort**: 30 minutes per constant — move to `EngineConfig`, thread through call chain.
- **Risk**: Low — but will change the `build_engine_config()` signature.

### 15. `_ACTIVE_THREAD_CAP` Duplicated in Engine and Eval Mirror

- **Files**: `ccya/engine/turn.py:84` and `ccya/eval/engine_mirror.py:22`
- **What**: The thread cap constant is separately defined in turn.py and the eval mirror. Similarly `_EXPIRE_SILENT_TURNS` (turn.py:87 vs mirror.py:23) and `_PROMOTION_COOLDOWN_TURNS` (turn.py:90 vs mirror.py:24).
- **Impact**: Changing a thread lifecycle constant requires updating two files. The eval mirror is supposed to be a read-only snapshot but has no automated sync mechanism.
- **Effort**: 30 minutes — export constants from `turn.py` as module-level public names, import into eval mirror.
- **Risk**: Low.

### 16. `_fuzzy_match_inventory` Exported in `__all__` Despite Being Private

- **File**: `ccya/state/__init__.py:35` — `"_fuzzy_match_inventory"` in `__all__`
- **What**: A function with underscore prefix (convention for private) is exported in `__all__`. No external code imports it from the package — `eval/engine_mirror.py` imports from `state.delta` directly.
- **Impact**: Misleading API surface. Suggests the function is part of the public contract when it's internal-only.
- **Effort**: 5 minutes — remove from `__all__`.
- **Risk**: None.

### 17. `warmup_on_start` Config Default Mismatch

- **Files**: `config.yaml:22` (says `false`) vs `ccya/server/app.py:56` (reads with `default=True`)
- **What**: The config file explicitly sets `warmup_on_start: false`, but the code default assumes `True`. The file value wins at runtime, so the actual behavior is `false` — but if someone removes the key from config, warmup suddenly enables.
- **Impact**: Silent behavior change when editing config. The code and config disagree on intent.
- **Effort**: 5 minutes — make both agree. Either change config to `true` or the code default to `false`.
- **Risk**: None.

### 18. `setting_pack` Config Key Explicitly Marked Legacy But Still Used

- **File**: `config.yaml:18` — `setting_pack: zombie-survival # Remove this, legacy`
- **Also**: `ccya/server/app.py:37` reads it: `_pack_id: str = config.get("game", {}).get("setting_pack", "expanse-belter")`
- **What**: The comment says "Remove this, legacy" but the field is still actively read and used to set the active pack. The code default doesn't match the config value (code defaults to `"expanse-belter"`, config says `"zombie-survival"`).
- **Impact**: Config surface is misleading. The "legacy" label suggests removal is safe, but removing it would change the active pack silently.
- **Effort**: 10 minutes — either remove the comment (if the key is intentional) or remove the key and update the code default.
- **Risk**: Low.

---

## P3 — Code Quality & Fragile Patterns

### 19. Fragile `dir()` Check for Local Variable Existence

- **File**: `ccya/engine/turn.py:352` — `if any_found and 'remaining_completed' in dir():`
- **What**: Uses `dir()` (no arguments) to check whether the local variable `remaining_completed` was defined in the loop above (line 342). The variable only gets defined inside `for res in storyteller_result.thread_resolve:` when `thread.id in completed_by_id`. The entire dedup flow depends on this runtime inspection.
- **Impact**: Fragile — if the loop executes zero iterations or finds an early match, the variable may or may not exist. Refactoring the loop would break this check silently. Line 364 has a mirror check: `if not any_found and 'remaining_completed' not in dir():`.
- **Effort**: 30 minutes — use a boolean flag or sentinel instead of `dir()` introspection.
- **Risk**: Low — the logic works currently, but resting on `dir()` is one bad day away from a bug.

### 20. Event Corruption Recovery with Silent Data Loss

- **File**: `ccya/state/delta.py:270-281`
- **What**: Drops non-dict entries from `recent_events` with a warning log. Handles historical corruption from old string-format events. However, the events that were corrupted are silently dropped with no way to recover.
- **Impact**: Silent data loss — the narrative record is truncated without the player knowing. This is a bandaid for a past migration that may not be complete.
- **Effort**: 1 hour — add a structured event for each dropped entry so the player can see what was lost.
- **Risk**: Low.

### 21. `_load_state()` Uses Regex to Fix YAML Corruption from Old Serialization

- **File**: `ccya/state/io.py:87-92`
- **What**: `re.sub()` on line 88 fixes `!!python/object/apply:ccya.models.ThreadState` tags from old YAML dumps. This is a backwards-compatibility shim for a schema migration where `ThreadState` enum was replaced.
- **Impact**: The regex approach is fragile — it assumes a specific indentation pattern (`\s+-\s+`). If YAML indentation changes (e.g., different `yaml.dump` settings), the regex silently fails to match and the old state file crashes on load.
- **Effort**: 30 minutes — replace with a structured migration function that deserializes the old format explicitly and raises clear errors on failure.
- **Risk**: Low — only affects loading old state files with the `ThreadState` pattern.

### 22. `_capitalize_inventory_names()` Mutates Parameters In-Place

- **File**: `ccya/engine/extraction.py:154-169`
- **What**: Capitalizes the first letter of inventory item names by modifying the objects in-place and returning them. Called at lines 744-745 where the return value is ignored — the mutation happens to the original `state_result.inventory_add` / `state_result.inventory_update` lists.
- **Impact**: Side-effectful function that appears pure (returns a value). Violates the principle of least surprise. If the caller later passes the same list to another function, the items have been silently mutated.
- **Effort**: 30 minutes — use `model_copy(update=...)` on Pydantic items or explicitly return new dicts.
- **Risk**: Low.

### 23. Inline Async Generators for Error Responses

- **File**: `ccya/server/routes.py:88-101`
- **What**: `_empty()` and `_busy()` are structurally identical inline async generators (differ only in error message). Defined inside the route handler function body.
- **Impact**: Duplicate code pattern. The functions are recreated on every request. Obscures the route handler's control flow.
- **Effort**: 15 minutes — extract to module-level async generator with a parameter.
- **Risk**: None.

### 24. `load_config()` Has No Error Handling

- **File**: `ccya/models.py:523-529`
- **What**: Opens and parses the config file. If the file is missing, permissions are wrong, or YAML is malformed, it raises a raw exception with a vague message: `config.yaml must contain a mapping at top level` — which is misleading for file-not-found or YAML-syntax errors.
- **Impact**: Users get confusing error messages during startup. The error type is the wrong error (ValueError instead of FileNotFoundError).
- **Effort**: 15 minutes — add proper exception handling with clear per-failure messages.
- **Risk**: None.

---

## P4 — Minor / Cosmetic

### 25. `_coerce_enums()` in IO Layer Is Defensive Against Pydantic/YAML Compatibility

- **File**: `ccya/state/io.py:17-25`
- **What**: Recursively converts Enum values to strings before YAML serialization. This exists because the state is stored as raw dicts, not Pydantic models, and `yaml.dump()` on Pydantic v1 style enum fields can emit Python-specific YAML tags.
- **Impact**: Adds a full-tree traversal on every save_state call. Small performance cost, no correctness impact.
- **Effort**: Pain to remove — would require switching state to Pydantic-native serialization. Not worth it currently.
- **Risk**: Very low.

### 26. 16 `# type: ignore` / `# noqa` Suppressions in Production Code

- **Files**: Across `ccya/` (excluding `tests/`): `turn.py:1077`, `extraction.py:779`, `names.py:33/34/56`, `app.py:125`, `judge.py:1046`, `tv_mirror.py:113`, `eval/cli.py:333/334`, `rules.py:178`
- **What**: 10 `# type: ignore` and 1 `# noqa` in production code. Most are for mypy strict-mode violations. Some are legitimate (FastAPI untyped decorators), others are avoidable.
- **Most avoidable**: `eval/cli.py:333-334` — `return asyncio.run(args.func(args))  # type: ignore[no-any-return]` — the function has no return type annotation, so mypy can't infer it.
- **Impact**: Suppressions mask real typing issues. New contributors cargo-cult `# type: ignore` without understanding why.
- **Effort**: 1 hour to audit and fix the avoidable ones.
- **Risk**: Low — but each fix requires proper type annotation.

### 27. `pyproject.toml` Has Unused Mypy Override for `rules.py`

- **File**: `pyproject.toml:57-59` — overrides `name-defined` error code for `ccya.rules`
- **What**: The override disables `name-defined` which is a mypy error for using undefined names. There's a `# noqa: F821` on `rules.py:178`. The mypy override is redundant with the `# noqa`.
- **Impact**: Unnecessary configuration that may hide real undefined-name bugs in rules.py.
- **Effort**: 5 minutes to check if the override is still needed (test with `mypy ccya/rules.py`).
- **Risk**: Low.

---

## Cross-Cutting Observations

### File Size Anomalies

| File | Lines | Problem |
|---|---|---|
| `ccya/engine/turn.py` | 1565 | Single orchestrator monolith |
| `ccya/state/delta.py` | 545 | 420-line apply_delta with nested closures |
| `ccya/engine/extraction.py` | 834 | Three ~250-line extraction streams with duplication |
| `ccya/models.py` | 530 | All Pydantic models in one file |
| `ccya/server/routes.py` | 557 | 25 route handlers in one file |

### Constant Duplication Chain

```
turn.py:84      _ACTIVE_THREAD_CAP = 3          (source of truth)
eval/engine_mirror.py:22  _ACTIVE_THREAD_CAP: int = 3   (duplicate)

delta.py:324    NPC_SCENE_CAP = 8               (local variable in function)
eval/engine_mirror.py:42  SCENE_NAMED_NPC_CAP: int = 8  (duplicate)

delta.py:61     PC_CONDITIONS_MAX: int = 5       (module-level, not configurable)
eval/engine_mirror.py:11  imports PC_CONDITIONS_MAX     (correct re-use)
```

### Config Surface Dead Fields

Config keys in `config.yaml` that control nothing (no code reads them):
- `thread_urgency_building_at` (read in `build_engine_config()` but never consumed)
- `thread_urgency_immediate_at` (same)
- `thread_urgency_immediate_ttl` (same)
- `avoidance_decay_per_turn` (same)

Config keys hardcoded in code but not in config:
- `_ACTIVE_THREAD_CAP = 3` (turn.py:84)
- `_EXPIRE_SILENT_TURNS = 5` (turn.py:87)
- `_PROMOTION_COOLDOWN_TURNS = 3` (turn.py:90)

### Eval Findings (from `plans/EVAL-FINDINGS.md`) That Are Also Code Quality Issues

| Eval Finding | Code Issue | File |
|---|---|---|
| #1 Jinja syntax error | Unclosed `{% if %}` | `compact_user.j2:11` |
| #3 Phantom item lifecycle | `inventory_remove` doesn't reject non-existent items | `turn.py:1505-1515`, `delta.py:182-185` |
| #5 NPC dedup failure | No cross-reference prep in extractor call | `extract_scene_system.j2:79-84` (prompt issue) |
| #7 Scene tag assertions | Exact-string matching vs semantic equivalence | `eval/runner.py:276-279` |

---

## Recommended Cleanup Order

1. **Fix the `compact_user.j2` bug** (P0, 5 min) — unblocks all compaction turns
2. **Warn on missing inventory remove** (P0, 2 hr) — prevents phantom item lifecycle
3. **Remove `apply_thinking()` and dead config keys** (P1, 30 min) — clears config surface
4. **Parameterize averaging functions** (P1, 1 hr) — reduces duplication
5. **Fix `warmup_on_start` default mismatch** (P2, 5 min) — no more silent behavior change
6. **Fix `dir()` check in `_apply_thread_resolutions`** (P3, 30 min) — fragile pattern
7. **Extract mock code from `llm_client.py`** (P1, 1-2 hr) — cleans up production module
8. **Remove `setting_pack` legacy comment or field** (P2, 10 min) — config hygiene
9. **Deduplicate coercion validators** (P2, 1 hr) — prevents latent bugs
10. **Fix `reconcile_delta()` in-place mutation** (P0, 1 hr) — makes contract explicit
11. **Export thread constants from turn.py** (P2, 30 min) — stops eval mirror drift
12. **Module boundary: fix circular import in extraction.py** (P2, 4-6 hr) — architectural fix
13. **Refactor `run_turn()` into phases** (P1, 8-12 hr) — biggest ROI for testability
14. **Refactor `apply_delta()` and extract NPC management** (P1, 4-6 hr) — companion to run_turn
15. **Add state schema versioning** (P2, 2-3 hr) — future-proofs against more migrations
16. **Switch routes from `sys.modules` to `app.state`** (P2, 3-4 hr) — enables route testing

Steps 1-11 are safe, independent, and could each be done in a single session.
Steps 12-16 are architectural and should be planned as dedicated refactor phases.
