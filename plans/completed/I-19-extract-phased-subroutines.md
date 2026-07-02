# I-19: Extract phased subroutines from run_turn

**Ticket:** I-19 — Extract phased subroutines from monolithic run_turn
**Status:** up-next
**Size:** large
**Risk:** low — mechanical extraction, no behavioral change

---

## Design Reference

Discovery doc: `roadmap/improvements/I-19-extract-phased-subroutines-from-run-turn.md`

---

## Problem

`turn.py` is 667 lines. `run_turn` (line 58) is a monolithic async generator handling the full turn lifecycle. Most phases are already extracted to separate modules (`_ruling_phase` → `ruling.py`, `_narrate_setup` → `narrate.py`, `_apply_state_updates` → `turn_state.py`, `_run_world_step` → `world.py`), but significant inline glue remains:

- **Narration streaming** (lines 147-212): LLM streaming, token yielding, metrics collection — 65 lines
- **Extraction + metrics** (lines 214-309): Pipeline orchestration, per-stream aggregation — 95 lines
- **Apply + rejection** (lines 311-343): Delta application, blocking rejection handling — 32 lines
- **Persistence + async cleanup** (lines 345-594): Event building, prompt logging, chronicle, sanitize, world, save, final metrics — 250 lines

Total inline glue: ~442 lines in a single function. Hard to read, hard to locate specific phase logic.

---

## Solution

Extract 4 inline sections into private functions in `turn.py`. All in the same file — no new modules.

### Extracted function signatures

```python
async def _narrate_phase(ctx: TurnContext) -> tuple[Any, str, dict[str, Any], str, str, str, int]:
    """Run narration: setup + streaming + metrics.
    
    Returns: (pc, narrative, narr_metrics, rendered_system, rendered_user, narr_trimmed, narr_trimmed_chars)
    """

async def _extract_phase(
    env: Any, state: WorldState, narrative: str, ctx: TurnContext,
    intent: IntentEnvelope, outcome: RulesOutcome, config: EngineConfig,
    trace_id: str, turn_no: int, recent_turns: list[dict[str, Any]],
) -> tuple[StateDelta | None, list[str], str, dict[str, Any], Any, Any, Any | None]:
    """Run extraction pipeline + build metrics.
    
    Returns: (delta, actions, outcome_summary, extraction_event, record_result, scene_result, extraction_ctx)
    """

def _apply_phase(
    state: WorldState, delta: StateDelta | None, record_result: Any | None,
    config: EngineConfig, trace_id: str, turn_no: int, save_dir_str: str,
) -> tuple[WorldState, StateDelta | None, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Apply delta + rejection handling.
    
    Returns: (state, delta, applied, rejected, thread_dedup_rejections, reconcile_warnings)
    """

async def _persist_and_async_cleanup(
    ctx: TurnContext, save_dir: Path, env: Any, state: WorldState,
    narrative: str, user_input: str,
    intent: IntentEnvelope, outcome: RulesOutcome, ruling_metrics: dict,
    rendered_ruling_system: str, rendered_ruling_user: str,
    ruling_raw_response: str, ruling_parse_error: str | None,
    ruling_trimmed: str, ruling_trimmed_chars: int,
    pc: Any, applied: dict, rejected: list,
    thread_dedup_rejections: list, reconcile_warnings: list,
    actions: list[str], outcome_summary: str, ext_metrics: dict,
    extraction_event: dict, errors: list[dict], trace_id: str, turn_no: int,
    config: EngineConfig,
    persist_result: dataclass,
) -> None:
    """Build event, yield complete, run async cleanup (sanitize + world + save).
    
    Yields: ("complete", TurnResult), ("phase", {...})
    Mutates persist_result with (result_obj, final_metrics, final_state).
    """
```

---

## Phases

### Phase 01: Extract `_narrate_phase`

**Goal:** Extract narration streaming (lines 147-212) into `_narrate_phase(ctx)`.

**Files:** `ccya/engine/turn.py`

**What:**

1. Create `_narrate_phase(ctx: TurnContext)` that encapsulates:
   - Phase yield (`narrate_start`)
   - Cancel check
   - `_narrate_setup(ctx)` call (already extracted)
   - Message trimming + rendering capture
   - LLM streaming loop with token yielding + first-token tracking
   - Cancel checks during streaming
   - Metrics collection (`narr_metrics`)
   - Phase yield (`narrate_done`)
   - Logging
   - Extract phase yield (`extract_start`)

2. Return tuple: `(pc, narrative, narr_metrics, rendered_system, rendered_user, narr_trimmed, narr_trimmed_chars)`

3. Update `run_turn` to call `_narrate_phase(ctx)` and unpack the tuple.

**Why:** Removes 65 lines of streaming logic from `run_turn`. The streaming loop has its own cancel checks, timing, and yielding — it's a distinct phase.

**Validation:** `make typecheck` passes. `run_turn` calls `_narrate_phase(ctx)` and unpacks the same tuple values. No behavioral change.

---

### Phase 02: Extract `_extract_phase`

**Goal:** Extract extraction pipeline + metrics aggregation (lines 214-309) into `_extract_phase(...)`.

**Files:** `ccya/engine/turn.py`

**What:**

1. Create `_extract_phase(env, state, narrative, ctx, intent, outcome, config, trace_id, turn_no, recent_turns)` that encapsulates:
   - Initialization of extraction variables (delta, actions, outcome_summary, extraction_event, etc.)
   - Narrate extraction event population
   - `_run_extraction_pipeline()` async iteration with event yielding + error handling
   - Result unpacking
   - Phase yield (`extract_done`)
   - Per-stream token count aggregation
   - Per-stream breakdown building
   - `ext_metrics` construction
   - `metrics` dict construction (ruling + narrate + extract)
   - Extraction complete logging

2. Return tuple: `(delta, actions, outcome_summary, extraction_event, record_result, scene_result, extraction_ctx)`

3. Update `run_turn` to call `_extract_phase(...)` and unpack the tuple.

**Why:** Removes 95 lines of extraction orchestration and metrics aggregation. The extraction phase has its own error handling, streaming, and metrics — distinct from ruling and apply.

**Validation:** `make typecheck` passes. `run_turn` calls `_extract_phase(...)` and unpacks the same tuple values. No behavioral change.

---

### Phase 03: Extract `_apply_phase`

**Goal:** Extract delta application + rejection handling (lines 311-343) into `_apply_phase(...)`.

**Files:** `ccya/engine/turn.py`

**What:**

1. Create `_apply_phase(state, delta, record_result, config, trace_id, turn_no, save_dir_str)` that encapsulates:
   - `state.model_copy()` for pre-apply snapshot
   - Initialization of applied/rejected/thread_dedup_rejections/reconcile_warnings
   - `_apply_state_updates()` call (already extracted)
   - Blocking rejection filtering
   - Blocking error append + narrative injection
   - `_strip_fallback()` call

2. Return tuple: `(state, applied, rejected, thread_dedup_rejections, reconcile_warnings)`

3. Update `run_turn` to call `_apply_phase(...)` and unpack the tuple.

**Why:** Removes 32 lines. Small extraction but isolates the delta validation/apply logic from the surrounding event-building code.

**Validation:** `make typecheck` passes. `run_turn` calls `_apply_phase(...)` and unpacks the same tuple values. No behavioral change.

---

### Phase 04: Extract `_persist_and_async_cleanup`

**Goal:** Extract persistence + async cleanup (lines 345-594) into `_persist_and_async_cleanup(...)`.

**Files:** `ccya/engine/turn.py`

**What:**

1. Create `_persist_and_async_cleanup(ctx, save_dir, env, state, narrative, user_input, intent, outcome, ruling_metrics, rendered_ruling_system, rendered_ruling_user, ruling_raw_response, ruling_parse_error, ruling_trimmed, ruling_trimmed_chars, pc, applied, rejected, thread_dedup_rejections, reconcile_warnings, actions, outcome_summary, ext_metrics, extraction_event, errors, trace_id, turn_no, config, persist_result)` that encapsulates:
   - Turn increment (`state.set_turn(...)`)
   - Phase yield (`persist`)
   - Ruling event dict construction
   - Event dict construction (all fields: ts, trace_id, turn, input, applied, rejected, ruling, pacing_context, etc.)
   - Prompts list construction (ruling + narrate + extraction streams)
   - `append_prompts()` call
   - `append_chronicle()` call
   - Prior history bullet addition
   - `TurnResult` construction
   - `yield ("complete", result_obj)`
   - Async window: sanitize phase (with timing, error handling, metrics)
   - Async window: world phase (with timing, error handling, beat candidates)
   - World extraction event + prompts append
   - Event save (`append_event`) + state save (`save_state`)
   - Final metrics construction (world + sanitize)
   - Phase yield (`world_done`) with final_metrics and state

2. Define a `PersistResult` dataclass with fields `result_obj: TurnResult | None`, `final_metrics: dict[str, Any] | None`, `final_state: WorldState | None`. Pass it to the function and mutate it inside.

3. Update `run_turn` to create a `PersistResult()`, call `_persist_and_async_cleanup(..., persist_result)`, then read `persist_result.result_obj`, `persist_result.final_metrics`, `persist_result.final_state` after the call.

**Why:** Removes 250 lines — the largest inline section. This is the persistence and async cleanup phase, which has distinct concerns (event building, prompt logging, async sanitize/world, final save). Extracting it makes `run_turn` a clear sequence of phase calls.

**Validation:** `make typecheck` passes. `run_turn` creates a `PersistResult`, calls `_persist_and_async_cleanup(...)`, then reads `persist_result.result_obj`, `persist_result.final_metrics`, `persist_result.final_state`. No behavioral change.

---

## Execution Order

1. **Phase 01** — `_narrate_phase` (65 lines, no state mutation, safest)
2. **Phase 02** — `_extract_phase` (95 lines, no state mutation, depends on Phase 01's pattern)
3. **Phase 03** — `_apply_phase` (32 lines, has state mutation, depends on Phase 02's pattern)
4. **Phase 04** — `_persist_and_async_cleanup` (250 lines, has state mutation + async, depends on all prior)

Each phase is independently verifiable via `make typecheck`. Phase 04 is the largest but is mechanical — just moving code and passing parameters.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Parameter passing complexity in Phase 04 | Medium | Phase 04 has many parameters — use a `PersistResult` dataclass for return values, pass remaining values individually |
| Yield behavior change | Low | All `yield` statements move into the extracted function — no change in when/how they fire |
| State mutation tracking | Medium | State is passed as a parameter, returned as part of tuple — explicit, easier to track than implicit ctx.state updates |
| Cancel check placement | Low | All cancel checks move into extracted functions — same placement, same behavior |

---

## Documentation Updates Required

After implementation:
1. **`docs/architecture/`** — Update pipeline flow doc to list extracted subroutines
2. **`docs/repomap.md`** — Update `turn.py` section to reflect extracted subroutines
3. **`AGENTS.md`** — Update turn pipeline description to list extracted phases

---

## Done When

- `run_turn` is under 250 lines (down from 667)
- 4 extracted functions exist: `_narrate_phase`, `_extract_phase`, `_apply_phase`, `_persist_and_async_cleanup`
- `make typecheck` passes
- No behavioral change — same yields, same state mutations, same error handling
