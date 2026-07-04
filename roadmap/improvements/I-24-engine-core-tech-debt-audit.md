---
title: "Engine core tech debt — magic strings, dead code, duplicated logic, and fragile patterns"
status: validated
urgency: 3
size: large
created: 2026-07-03
ticket_id: I-24
labels:
  - engine
  - tech-debt
  - code-quality
plan: plans/i-24/01-trivial-cleanup.md
---

## Problem

Audit of the engine codebase (`ccya/engine/`) revealed multiple categories of tech debt that accumulate over time and reduce maintainability, correctness, and developer confidence.

---

### 1. Magic string sentinel for LLM communication

**File:** `ccya/engine/turn.py`

`_FALLBACK_SENTINEL` is a magic string used to signal the LLM to use a fallback value. This is fragile — the LLM could hallucinate the exact string, or a different sentinel could conflict.

**Better:** Use a structured protocol (e.g., a special JSON key or enum) that's unambiguous and validated before the LLM sees it.

---

### 2. Dead code and no-op functions

**File:** `ccya/engine/seed.py`
- `_is_named()` — dead code, never called
- `_soft_validate_seed()` — no-op, always returns `True`

**File:** `ccya/engine/_pacing.py`
- `_recent_turn_count()` — dead code, never called

**Better:** Remove all dead code and no-ops. They add cognitive load without value.

---

### 3. Frozen dataclass mutation via `object.__setattr__`

**File:** `ccya/engine/seed.py`

Uses `object.__setattr__` to mutate a frozen dataclass. This bypasses Python's immutability guarantee and is a code smell.

**Better:** Use `dataclasses.replace()` or redesign the seed as mutable where needed.

---

### 4. Duplicated `_filter_pc_situation`

**Files:** `ccya/engine/ruling.py`, `ccya/engine/narrate.py`

The same `_filter_pc_situation` function is duplicated in two modules.

**Better:** Extract to a shared module (e.g., `ccya/engine/_utils.py` or `ccya/engine/extraction/utils.py`).

---

### 5. Scattered ArcThread coercion

**File:** `ccya/engine/_pacing.py`

`ArcThread` coercion logic is scattered across multiple functions instead of centralized.

**Better:** A single `_to_arc_thread()` helper in the pacing module.

---

### 6. CheckerConfig default mismatch

**File:** `ccya/engine/config.py`

`CheckerConfig` has `n_checkers: int = 5` but the actual default used is `3`.

**Better:** Align the default or document the discrepancy.

---

### 7. Module-level globals for async result passing

**File:** `ccya/engine/extraction/pipeline.py`

Uses module-level globals (`_scene_result`, `_state_result`, `_record_result`) to pass async results between coroutines.

**Better:** Pass results through explicit return values or a context object.

---

### 8. Fragile `_coerce_scene_json`

**File:** `ccya/engine/extraction/utils.py`

`_coerce_scene_json` does manual JSON parsing with error handling that swallows details.

**Better:** Use Pydantic validation with clear error messages.

---

### 9. `_apply_sanitization` never populates `added_ids`

**File:** `ccya/engine/thread_sanitizer.py`

The `added_ids` list in `_apply_sanitization` is never populated, so callers can't know which threads were newly added.

**Better:** Populate `added_ids` or remove the field.

---

### 10. Narrow retry logic in LLM client

**File:** `ccya/llm_client.py`

`_is_retryable` has very narrow retry criteria. Unreachable else clause in `_chat_with_fallback`.

**Better:** Expand retry criteria and remove dead code.

---

## Status Update (2026-07-03)

**I-24 is a tech debt audit.** It catalogs findings from the engine codebase review. Each item above is a candidate for a separate improvement ticket or a combined refactoring effort.

**Priority guidance:**
- **High:** #1 (magic sentinel), #7 (module globals), #4 (duplicated code)
- **Medium:** #3 (frozen dataclass mutation), #8 (fragile coercion), #9 (dead `added_ids`)
- **Low:** #2 (dead code), #5 (scattered coercion), #6 (default mismatch), #10 (narrow retry)

---

## Additional Findings (2026-07-03 audit)

### 11. Inline `import traceback` in exception handlers

**Files:** `ccya/engine/turn.py:256,434`

`import traceback` is imported inside `except` blocks rather than at module level. This is an anti-pattern — imports should be at the top of the file for readability and to avoid import cost on error paths (where they're least likely to matter).

**Better:** Move `import traceback` to the top of `turn.py`.

---

### 12. Inline `import json` scattered across server modules

**Files:** `ccya/server/panels.py:32,104,152`, `ccya/server/routes.py:707`

`import json` appears inline inside functions rather than at module level. `json` is a stdlib module so import cost is negligible, but it breaks the convention that all imports are at the top of files.

**Better:** Move all `import json` to module-level in `panels.py` and `routes.py`.

---

### 13. Dead file: `ccya/mysession_types.txt`

**File:** `ccya/mysession_types.txt`

Contains exactly one line: `zsh:1: command not found: python`. This is a stray shell error capture with no purpose.

**Better:** Delete the file.

---

### 14. Dormant module: `ccya/models/compactor.py`

**File:** `ccya/models/compactor.py`

The entire module is dormant — no callers anywhere in the codebase. The docstring says "Dormant compactor models — schema ready for future batch compaction." The `CompactorSanitizationResult` model and its validator are never instantiated.

**Better:** Either remove the module entirely, or if it's planned for future use, move it to a `dormant/` or `experimental/` directory with a clear activation plan.

---

### 15. `Bond` field dead code in compendium models

**Files:** `ccya/models/state.py:87` (NPCEntry has `tie` but `CompendiumEntry` in `pack.py` uses `bond`), `ccya/models/extraction.py`

The `Bond` field (via `CompendiumEntry.bond` in `pack.py`) is never used at runtime. Runtime code uses `CompendiumNpcUpdate.tie` (the rename happened but seed-time model still uses `bond`). The `Bond` field in `CompendiumEntry` is dead code.

**Better:** Either remove `Bond` from `CompendiumEntry` or wire it through so seed-time `bond` maps to runtime `tie`.

---

### 16. `copy.deepcopy` used where `model_copy` would be idiomatic

**Files:** `ccya/state/delta_builder.py:74`, `ccya/engine/extraction/context.py:57`, `ccya/engine/extraction/pipeline.py:110,261,285`

The codebase uses Pydantic's `model_copy()` for immutable state mutations (documented in `models/state.py:157-160` as the preferred pattern), but `copy.deepcopy` is used in three files. `copy.deepcopy` on Pydantic models is slower and bypasses Pydantic's validation/coercion layer.

**Better:** Replace `copy.deepcopy(state)` with `state.model_copy()` where `state` is a `WorldState` or other Pydantic model.

---

### 17. `global` declarations creating hidden shared state

**Files:** `ccya/ev/checkers/llm_checkers.py:260,268`, `ccya/ev/play.py:29`, `ccya/server/app.py:35,43,150`, `ccya/llm_client.py:156,364`, `ccya/engine/names.py:54`

Multiple modules use `global` declarations for shared mutable state. While some are legitimate (caching `_kakasi` in `names.py:54`), others represent hidden coupling between callers and callers' callers.

**Better:** Where `global` is used for caching (like `_kakasi`), that's acceptable. Where it's used for shared mutable state (like `_engine_config` in llm_checkers), consider dependency injection or a config registry.

---

### 18. Late import to avoid circular dependency

**File:** `ccya/server/app.py:205`

`import ccya.server.routes` is a late import (after class definitions) with a comment: "late import required by FastAPI route registration (circular if done earlier)." This is a code smell — circular import avoidance via late imports is fragile and hard to reason about.

**Better:** Restructure so routes are defined in a way that doesn't create circular imports (e.g., move route registration to a separate bootstrap step).

---

### 19. `import random` shadows module with instance

**File:** `ccya/engine/names.py:11,74`

`import random` at line 11, then `rng = random.Random(seed)` at line 74 creates an instance that shadows the module. This is confusing — `random` is used as both a module (via `random.Random()`) and an instance (via `rng`).

**Better:** Rename to `import random as _random` and use `_random.Random(seed)`.

---

## Validation (2026-07-03)

Each finding verified against current source. Status: **validated** (true), **invalid** (no longer present or incorrect premise), or **needs more investigation**.

### Validated findings

- **#1** Magic string sentinel `_FALLBACK_SENTINEL` — **validated**. Exists in `turn.py:367`.
- **#2** Dead code: `_is_named()` (seed.py:25), `_soft_validate_seed()` (seed.py:205), `_recent_turn_count()` (_pacing.py:325) — **validated**. Zero callers for all three. `_recent_turn_count()` returns hardcoded `1`.
- **#4** Duplicated `_filter_pc_situation` — **validated**. Identical implementations in `ruling.py:20-27` and `narrate.py:22-29`.
- **#5** Scattered ArcThread coercion — **validated**. Identical `isinstance(t, ArcThread)` + `ArcThread.model_validate(t)` pattern at `_pacing.py:239-247` and `narrate.py:191-203`.
- **#7** Module-level globals for async result passing — **validated**. `_scene_result_holder`, `_state_result_holder`, `_record_result_holder`, `_extraction_ctx_holder` at `pipeline.py:36-39`.
- **#9** `added_ids` never populated — **validated**. `added_ids: list[str] = []` declared at `thread_sanitizer.py:354` but never appended to anywhere in the file.
- **#10** Narrow retry logic + unreachable else — **validated**. `_is_retryable` (llm_client.py:137-141) only retries `TimeoutError`. Unreachable `for...else` at llm_client.py:210-212 (loop always exits via `return`/`break`/`raise`).
- **#11** Inline `import traceback` — **validated**. `import traceback` at `turn.py:256,434` inside `except` blocks.
- **#12** Inline `import json` — **validated**. `panels.py:32,104,152` and `routes.py:707`. (routes.py:6 is module-level, fine.)
- **#13** Dead file `mysession_types.txt` — **validated**. Contains exactly `zsh:1: command not found: python`.
- **#14** Dormant `compactor.py` — **validated**. Zero callers. Docstring: "Dormant compactor models."
- **#16** `copy.deepcopy` where `model_copy` would be idiomatic — **validated**. `WorldState` (state.py:115) and `StateDelta` (extraction.py:84) are Pydantic `BaseModel`s. `copy.deepcopy` at context.py:57, pipeline.py:110/261/285. delta_builder.py:74 is a special case — doc says "creates a copy" so deepcopy is intentional.
- **#18** Late import to avoid circular dependency — **validated**. `import ccya.server.routes` at `app.py:205` with explicit comment "late import required by FastAPI route registration (circular if done earlier)."

### Invalid findings

- **#3** Frozen dataclass mutation — **invalid**. `SeedState` (pack.py:60) and `ArcThread` (state.py:269) are Pydantic `BaseModel`s, not frozen dataclasses. No `frozen=True` anywhere. `object.__setattr__` still bypasses Pydantic validation (code smell), but the finding's premise is wrong.
- **#6** CheckerConfig default mismatch — **invalid**. `CheckerConfig` (config.py:17) has no `n_checkers` field. The field doesn't exist in current code.
- **#8** Fragile `_coerce_scene_json` — **invalid**. The function (utils.py:109-140) does NOT do JSON parsing — it takes an already-parsed `dict`. It also has zero `try/except` blocks. The coercion is called from `_parse_stream_result` (line 153) which re-raises with context at line 154-155. Finding's diagnosis is wrong; recommendation (use Pydantic) is reasonable but not actionable as stated.
- **#15** `Bond` field dead code — **invalid**. `CompendiumEntry` (pack.py:38) has `tie` (line 43), not `bond`. No `Bond` type or `.bond` field exists anywhere in the codebase.
- **#19** `import random` shadows module — **invalid**. `rng` and `random` are different variable names at names.py:10 and line 74. No shadowing occurs. Finding confused the instance name with the module name.

### Needs more investigation

- **#17** `global` declarations — **validated with nuance**. See deep dive below.

---

### #17 Deep dive (2026-07-03)

All `global` declarations in the codebase, categorized:

**Legitimate caching (no change needed):**

| File | Variable | Pattern | Verdict |
|------|----------|---------|---------|
| `names.py:54` | `_kakasi` | Lazy init, single `Kakasi()` instance | OK |
| `llm_client.py:156` | `_last_fallback_time` | Cooldown timer scalar | OK |
| `llm_client.py:364` | `_client` | Dict-based connection pool cache | OK |
| `ev/play.py:29` | `_play_loop` | Event loop singleton | OK |

**Acceptable but worth noting:**

| File | Variable | Pattern | Verdict |
|------|----------|---------|---------|
| `server/app.py:35,43` | `_turn_lock, _cancel_event, _turn_done_event` | Turn coordination state (init/torn down per-turn) | OK for server lifecycle |
| `server/app.py:150` | `_errors_file_path` | Lazy file path init | OK |

**Questionable — needs action:**

| File | Variable | Issue |
|------|----------|-------|
| `ev/checkers/llm_checkers.py:251,260,268` | `_engine_config` | Hidden coupling — config is set once by check command, read by any LLM checker caller without it being in the function signature. Makes testing harder and callers implicitly depend on external setup. |

**Verdict:** Only `ev/checkers/llm_checkers.py:_engine_config` is worth acting on. It should be passed as a function argument or via a proper config registry rather than a module-level singleton.

## Alternatives considered

### Combine all into one ticket
- Pros: One PR, complete sweep
- Cons: Large diff, harder to review, higher merge risk

### Separate into individual tickets
- Pros: Small diffs, easy to review, each is independently valuable
- Cons: More tickets, more PRs to manage

### Combine into a single "engine core cleanup" sprint
- Pros: Focused effort, batched review
- Cons: Requires coordination, may not fit in a single cycle

## Success criteria

- All dead code removed
- Magic sentinel replaced with structured protocol
- Duplicated code consolidated
- Module-level globals eliminated
- All improvements pass existing test suite

## Related

- `I-17` — engine core tech debt audit and cleanup (archived)
- `I-23` — engine core tech debt consolidation (archived)
- `F-6` — tech debt: dead imports, parity gaps sweep
- `I-21` — decouple thread sanitizer from raw dict state
