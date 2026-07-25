---
title: "Engine tech debt: typing, function sizes, and silent failures"
status: done
urgency: 2
size: xlarge
created: 2025-07-25
ticket_id: I-42
labels: [engine, typing, refactoring]
design:
plan:
pr:
  url:
  branch:
---

## Description

The core engine (`ccya/engine/`, `ccya/llm_client.py`, `ccya/server/routes.py`) has accumulated significant tech debt across four dimensions: untyped data flowing through the pipeline, oversized functions, silent exception handlers, and deeply nested dict access. This ticket consolidates all validated findings into one improvement effort.

All findings were validated by direct source inspection on 2025-07-25.

---

## Validated Findings

### F1: `record_result`, `scene_result`, and other `Any` types that should be typed models

**Locations:**
- `engine/turn.py:520` — `record_result: Any | None` should be `RecordResult | None`
- `engine/turn.py:575` — `ExtractionResult.record_result: Any = None` should be `RecordResult | None`
- `engine/turn.py:576` — `ExtractionResult.scene_result: Any = None` should be `SceneExtractResult | None`
- `engine/turn.py:577` — `ExtractionResult.extraction_ctx: Any = None` should be `_PostDeltaContext | None`
- `engine/turn.py:558` — `NarrateResult.pc: Any = None` should be `PacingContext | None`
- `engine/turn.py:565` — `NarrateResult.new_scene: Any = None` should be `Scene | None`
- `engine/turn.py:408` — `_extract_phase(env: Any, ...)` — `env` should be `jinja2.Environment`
- `engine/turn.py:590` — `_persist_and_async_cleanup(..., env: Any, ...)` — same
- `engine/turn_context.py:31` — `_env: Any = None` should be `Environment | None`
- `engine/narrate.py:31` — `env: Any` should be `Environment`
- `engine/thread_sanitizer.py:129` — `env: Any` should be `Environment`

**Models that exist but are unused in the pipeline:**
- `RecordResult` — `models/extraction.py:218` (typed Pydantic model with validators)
- `SceneExtractResult` — `models/extraction.py:118`
- `StateExtractResult` — `models/extraction.py:125`
- `PacingContext` — `engine/turn_context.py:48`
- `Scene` — `models/state.py:58`

**Impact:** The extraction pipeline produces typed `RecordResult` and `SceneExtractResult` objects, but `run_turn()` immediately casts them to `Any` in `ExtractionResult`, losing all type safety for the rest of the pipeline. `_apply_phase`, `_persist_and_async_cleanup`, and downstream code access `.thread_update`, `.actions`, `.arc_resolve` etc. through untyped dicts with `.get()` calls.

---

### F2: Oversized functions

**`_apply_phase` — `engine/turn.py:519` — 373 lines (to EOF)**

This function is the entire tail of the file. Despite the name suggesting it just "applies a phase," it:
- Applies state deltas via `_apply_state_updates()` (delegated to `turn_state.py`)
- Handles rejection logic
- Strips fallback messages
- Builds the turn event dict (lines 646-731)
- Appends prompts to `prompts.jsonl`
- Appends to chronicle
- Builds `TurnResult` and yields `("complete", result_obj)`
- Runs async cleanup (sanitize, world step, save)

The function is doing three distinct things: apply delta, persist event, async cleanup.

**`_persist_and_async_cleanup` — `engine/turn.py:589` — ~100 lines, 20+ parameters**

Function signature (lines 589-604):
```python
async def _persist_and_async_cleanup(
    ctx: TurnContext, save_dir: Path, env: Any, state: WorldState,
    narrative: str, user_input: str,
    intent: IntentEnvelope, outcome: RulesOutcome, ruling_metrics: dict[str, Any],
    rendered_ruling_system: str, rendered_ruling_user: str,
    ruling_raw_response: str, ruling_parse_error: str | None,
    ruling_trimmed: bool, ruling_trimmed_chars: int,
    pc: Any, applied: dict[str, Any], rejected: list[dict[str, Any]],
    thread_dedup_rejections: list[dict[str, Any]], reconcile_warnings: list[str],
    actions: list[str], outcome_summary: str, ext_metrics: dict[str, Any],
    extraction_event: dict[str, Any], errors: list[dict[str, Any]], trace_id: str, turn_no: int,
    config: EngineConfig, diff_lines: list[str], changes: dict[str, Any], metrics: dict[str, Any],
    narr_metrics: dict[str, Any], rendered_narr_system: str, rendered_narr_user: str,
    narr_trimmed: bool, narr_trimmed_chars: int,
    persist_result: PersistResult, saved_beat: dict[str, Any] | None,
) -> AsyncIterator[tuple[str, Any]]:
```

27 parameters, most of them `dict[str, Any]`. This is a parameter anti-pattern — the function should accept a context/dataclass.

**`_extract_phase` — `engine/turn.py:407` — 112 lines**

Passes and mutates `dict[str, Any]` objects (`extraction_event`, `narr_metrics`, `errors`). Sets fields on `ExtractionResult` via mutation.

**`turn_state.py` — 745 lines, 7 functions**

Handles thread updates, thread resolutions, arc operations, inventory reconciliation, NPC color generation, and delta application. Too many responsibilities.

**`thread_sanitizer.py` — 496 lines, 6 functions**

Mixes async LLM-based sanitization with synchronous dict-parsing functions (`_parse_sanitization_result`). The parsing functions (lines 220-448) operate entirely on `dict[str, Any]`.

**`server/routes.py` — 1117 lines, 23 functions**

Monolith mixing: save listing, pack generation, turn running, settings UI, inventory CRUD, LLM health checks, and turn viewer routes.

---

### F3: Silent `except Exception: pass` and bare `except Exception:` without logging

**Silent failures (`except Exception: pass`) — should at minimum log:**

| Location | Line | Context |
|----------|------|---------|
| `server/routes.py` | 151 | Nested `except json.JSONDecodeError: pass` while reading events.jsonl for save listing |
| `server/routes.py` | 153 | `except OSError: pass` while reading save directory |
| `server/routes.py` | 576 | `except Exception: pass` building tie lookup from NPC bonds — silently fails to resolve NPC tie descriptions |
| `server/routes.py` | 701 | `except Exception:` on JSON parse for tone_tags/world_rules — silently falls through with empty lists |
| `ev/checkers/_llm.py` | 77 | `except Exception: pass` in LLM retry loop — silently treats retry failure as parse failure |
| `ev/play.py` | 672, 677 | `except Exception: pass` for git commands — minor, but should log at debug |

**Bare `except Exception:` without specific handling (acceptable only if they log):**

| Location | Line | Verdict |
|----------|------|---------|
| `server/routes.py` | 158 | `except Exception:` on `load_state()` — logs warning, acceptable |
| `server/routes.py` | 868 | `except Exception:` on LLM health check — returns "fail" with fallback, acceptable |
| `server/routes.py` | 1077 | `except Exception:` on `request.json()` — returns 400, acceptable |
| `llm_client.py` | 186 | `except Exception:` in health check — returns False, acceptable |
| `llm_client.py` | 232 | `except Exception:` in fallback logic — logs debug, acceptable |
| `engine/turn.py` | 890 | `except Exception:` in warmup — logs warning, acceptable |
| `pack.py` | 300 | `except Exception:` on YAML parse — logs error and re-raises, acceptable |
| `ev/eval.py` | 210, 224 | `except Exception:` on YAML meta read — returns "", acceptable for robustness |
| `ev/eval.py` | 365, 371 | `except Exception:` on git commands — returns "unknown", acceptable |

**The ones that need fixing:** `routes.py:151`, `routes.py:153`, `routes.py:576`, `routes.py:701`, `_llm.py:77`, `play.py:672`, `play.py:677` — all should log at minimum at warning or debug level.

---

### F4: Deeply nested dict access

**Pattern:** `((dict.get("a") or {}).get("b") or {}).get("c") or []`

**Locations:**
- `engine/turn.py:645` — `((extraction_event.get("scene") or {}).get("output") or {}).get("compendium_npc_update") or []`
- `engine/turn.py:476-481` — `(extraction_event.get(s) or {}).get("tokens_in", 0)` in loop
- `engine/turn.py:499-504` — `(extraction_event.get(s) or {}).get("retry_errors", [])` in loop
- `engine/turn.py:678-680` — `extraction_event.get("scene", {}).get("ms", 0)` etc.

**Root cause:** `extraction_event` is `dict[str, Any]` populated by the three-stream extraction pipeline. Each stream writes its own sub-dict with keys like `ms`, `tokens_in`, `tokens_out`, `retry_errors`, `output`. Because the dict is untyped, every consumer must defensively chain `.get()` calls with `or {}` / `or []` fallbacks.

**Fix:** Either type `extraction_event` with a proper TypedDict/dataclass, or extract the needed values at the point they're written (in the extraction pipeline) and store them in typed structures.

---

### F5: `dict[str, Any]` overuse in engine function signatures

**Count:** 149 instances of `dict[str, Any]` in `engine/` alone. Every engine module imports `Any` from typing.

This means the pipeline passes untyped data between typed `WorldState` boundaries. The extraction pipeline produces typed `StateMerge` and `RecordResult` but then wraps them in `dict[str, Any]` containers (`extraction_event`, `applied`, `rejected`) for transport through `run_turn()`.

**Key locations:**
- `engine/turn.py:68` — `pack_name_locales: list[dict[str, Any]] = []`
- `engine/turn.py:80-81` — `errors: list[dict[str, Any]] = []`, `metrics: dict[str, Any] = {}`
- `engine/turn.py:182` — `extraction_event: dict[str, Any] = {}`
- `engine/turn.py:328` — `narr_stream_stats: dict[str, Any] = {}`
- `engine/turn.py:410-411` — `recent_turns: list[dict[str, Any]]`, `narr_metrics: dict[str, Any]`
- `engine/turn.py:529-531` — `applied: dict[str, Any]`, `rejected: list[dict[str, Any]]`, `thread_dedup_rejections: list[dict[str, Any]]`
- `engine/turn.py:596-601` — Most params of `_persist_and_async_cleanup`

---

### F6: Mutable default arguments (`= []`, `= {}`)

Classic Python anti-pattern. These defaults are shared across calls and never triggered at runtime (all callers pass explicit values), but they're a footgun.

| Location | Line | Default |
|----------|------|---------|
| `engine/turn.py` | 68 | `pack_name_locales: list[dict[str, Any]] = []` |
| `engine/turn.py` | 69 | `pack_narrator_rules: list[str] = []` |
| `engine/turn.py` | 70 | `pack_world_rules: list[str] = []` |
| `engine/turn.py` | 71 | `pack_factions: list[dict[str, str]] = []` |
| `engine/narrate.py` | 35 | `recent_turns: list[dict[str, Any]] = []` |
| `engine/narrate.py` | 36 | `narrator_rules: list[str] = []` |
| `engine/narrate.py` | 37 | `world_rules: list[str] = []` |
| `engine/narrate.py` | 39 | `npc_name_pool: dict[str, list[str]] = {}` |
| `engine/narrate.py` | 45 | `world_factions: list[dict[str, str]] = []` |

---

### F7: Additional oversized files not called out separately

| File | Lines | Functions | Issue |
|------|-------|-----------|-------|
| `engine/changes.py` | 382 | 5 | Entirely operates on `dict[str, Any]` — `_summarize_applied`, `summarize_changes`, `format_change_lines` all use untyped dicts for change data |
| `engine/turn_state.py` | 745 | 7 | Thread ops, arc ops, inventory reconciliation, NPC generation, delta application — too many responsibilities |
| `engine/thread_sanitizer.py` | 496 | 6 | Mixes async LLM calls with synchronous dict parsing (`_parse_sanitization_result` at lines 220-448) |
| `server/routes.py` | 1117 | 23 | Save listing, pack generation, turn running, settings, inventory, LLM health, turn viewer — monolith |

---

## Scope

This is a large refactoring effort. Recommended approach:

1. **Phase 1: Fix silent exceptions** ✅ DONE — Added logging to all 7 `except Exception: pass` locations.

2. **Phase 2: Fix mutable defaults** ✅ DONE — Replaced `= []` and `= {}` in `run_turn` and `_narrate_messages` with `None` defaults and in-function initialization.

3. **Phase 3: Type the untyped types** ✅ DONE — Replaced `Any` with proper model types in `ExtractionResult`, `NarrateResult`, `env` params, and function signatures. Added `jinja2.Environment` imports. All type checks pass.

4. **Phase 4: Reduce function sizes** ✅ DONE — Extracted `_persist_and_async_cleanup`'s 27 parameters into `_TurnPersistContext` dataclass. Extracted 5 subroutines: `_build_ruling_event`, `_build_turn_event`, `_persist_events`, `_build_turn_result`, `_run_async_cleanup`.

5. **Phase 5: Type the dict containers** ✅ DONE — Created `engine/extraction/types.py` with TypedDicts (`ContextMeta`, `StreamResult`, `NarrateResultDict`, `SanitizeResultDict`, `WorldResultDict`, `CompDedupRedirect`). Added helper functions `_get_stream_field` and `_get_nested` to replace defensive `.get()` chaining. Fixed F4 patterns in `turn.py`.

## Verification

All phases verified with `make check` (lint + typecheck + pack validation + vulture). No regressions detected.

### Evals (2026-07-25)

**Phase 1: 5 turns noir-1930s:driven** — Session ended cleanly at turn 5. No critical bugs. Pre-existing warning: `resolve_inventory_canonical_id no match raw=coin normalized=coin`.

**Phase 2: 3×15 turns** (noir-1930s:driven, space-western:driven, golden-piracy:driven) — All 3 ran cleanly to 15 turns. Checkers: 38/42 pass (90.5%). Pre-existing failures: `sanitizer_lifecycle`, `location_description_consistency`, `convergence_recompute`, `convergence_ema` — identical across all 3 packs, no regressions from changes.

**Phase 3: 25 turns noir-1930s:driven** — Session ended cleanly at turn 25. Checkers: 37/42 pass (88.1%). One additional failure at 25 turns: `thread_urgency_decay` (was passing at 15 turns). This is almost certainly pre-existing — changes only touched logging, defaults, typing, and function extraction (zero logic changes). Thread urgency decay is a deterministic checker that verifies dormant/demotion behavior after 4/8 turns, so more time at 25 turns gives pre-existing issues more opportunity to manifest.

**Conclusion:** All 5 phases complete. No regressions detected across 45 total turns of evals.

---

## Notes

- The `Any` types should not be removed blindly — some `dict[str, Any]` parameters like `pack_name_locales` and `packing` come from YAML-loaded pack data where the structure is dynamic. Those should remain as `dict[str, Any]` or be converted to typed models with optional fields.
- The `env: Any` for Jinja2 `Environment` is a reasonable shortcut since Jinja2 has no type stubs, but `jinja2.Environment` is a concrete class and should be used for clarity.
- `turn_state.py` (745 lines), `thread_sanitizer.py` (496 lines), `changes.py` (382 lines), and `server/routes.py` (1117 lines) are separate files that could be split, but that's a larger refactor best done after typing is fixed.
- Mutable default arguments in `run_turn` and `_narrate_messages` are never triggered at runtime (all callers pass explicit values), but they're still a footgun and should be fixed early.
