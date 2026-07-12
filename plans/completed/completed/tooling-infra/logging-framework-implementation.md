# Logging Framework — Log Levels and Structured Error Instrumentation

## Status
`completed`
**Created:** 2026-06-17
**Design doc:** `docs/design/complete/logging-framework-design.md`

---

## Problem Summary

The engine's logging has three categories of problems:

1. **Log level misalignment.** State-damaging failures (inventory corruption, location corruption, state load failure) are logged at DEBUG or WARNING — below the operator's visible threshold. Recoverable failures (ruling exhaustion, extraction stream exhaustion) are logged at ERROR — too severe for non-fatal paths. Routine state mutations (inventory add/remove, condition management, NPC scene management) are logged at DEBUG — invisible to operators who need to audit what changed.

2. **Missing error kinds.** `ccya/errors.py` has no error kinds for state mutation failures (inventory, conditions, location, NPC, arc, thread). When these failures occur, they either crash with a bare `TURN_PROCESSING_FAILED` or are silently swallowed with no structured signal.

3. **TurnResult.errors invisible to UI.** `routes.py:252` iterates `result.errors` and logs them at ERROR, but never yields an SSE `turn_error` event. The player never sees per-stream extraction errors or delta validation rejections. Only the top-level exception path (all 3 streams failed) produces an SSE error event.

---

## Constraints

- **No new dependencies.** Must use Python stdlib `logging` only.
- **Backward compatible.** Existing log calls without new `extra` fields produce identical output.
- **ErrorKind must remain string constants** (not `Enum`).
- **StreamHandler → WARNING prerequisite.** Must be done in the same implementation wave (observability design Phase 2).
- **Design doc is the authority.** `docs/design/complete/logging-framework-design.md` defines all decisions.

---

## Phases Overview

| Phase | Title | What changes | Why this grouping |
|-------|-------|-------------|-------------------|
| 1 | ErrorKind additions | Add 20 new error kind constants to `ccya/errors.py` | Single file change; all downstream phases depend on these constants |
| 2 | Log level corrections (core) | Promote `load_state()` defaults to ERROR, demote ruling exhaustion to WARNING | Two files, two log level changes; no new code |
| 3 | State mutation logging | Add INFO logs for inventory/condition/location/NPC mutations, WARNING for failures | `delta_builder.py` + `npcs.py` + `inventory.py` — all state mutation paths |
| 4 | Turn-level logging | Add condition aging expiry log, promote overdraw clamp to INFO | Single file `turn.py` — two log additions |
| 5 | Chronicle persistence error kinds | Add try/except wrappers with error kinds in `chronicle.py` | Single file — two append functions need error handling |
| 6 | Extraction coercion error kind | Add try/except with error kind in `extraction.py` coercion path | Single file — `_coerce_scene_json()` path |
| 7 | Exhaustion error kinds | Add error kinds at ruling/extraction exhaustion points | Two files — `ruling.py:146`, `extraction.py:505` |
| 8 | SSE error surfacing | Extend `routes.py:252` to yield `turn_error` SSE events for all `result.errors` | Single file — SSE endpoint |
| 9 | StreamHandler → WARNING | Change StreamHandler default level in `logging_setup.py` | Prerequisite for Phase 3; must be done alongside |
| 10 | Documentation updates | Update `docs/architecture/`, `docs/repomap.md`, `AGENTS.md` | Final cleanup |

---

## Phase 1: ErrorKind Additions

**What changes:** Add 20 new error kind constants to `ccya/errors.py`.

### Files to read
- `ccya/errors.py` — existing ErrorKind constants and LlmcError hierarchy

### Context
- ErrorKind values are string constants (not Enum), following the existing pattern.
- 20 new constants to add:

```python
# State mutation errors (new)
INVENTORY_REMOVE_FAILED     = "INVENTORY_REMOVE_FAILED"
INVENTORY_UPDATE_FAILED     = "INVENTORY_UPDATE_FAILED"
INVENTORY_ADD_FAILED        = "INVENTORY_ADD_FAILED"
DELTA_VALIDATION_FAILED     = "DELTA_VALIDATION_FAILED"
LOCATION_CHANGE_INVALID     = "LOCATION_CHANGE_INVALID"
NPC_SCENE_MANAGEMENT_FAILED = "NPC_SCENE_MANAGEMENT_FAILED"
THREAD_UPDATE_INVALID       = "THREAD_UPDATE_INVALID"
ARC_RESOLVE_INVALID         = "ARC_RESOLVE_INVALID"
THREAD_RESOLVE_INVALID      = "THREAD_RESOLVE_INVALID"
EXTRACTION_CONTEXT_BUILD_FAILED = "EXTRACTION_CONTEXT_BUILD_FAILED"
EXTRACTION_COERCION_FAILED  = "EXTRACTION_COERCION_FAILED"
INVENTORY_NORMALIZE_FAILED  = "INVENTORY_NORMALIZE_FAILED"
FUZZY_MATCH_FAILED          = "FUZZY_MATCH_FAILED"
NPC_NAME_LOOKUP_FAILED      = "NPC_NAME_LOOKUP_FAILED"

# State persistence errors (new)
STATE_LOAD_FAILED           = "STATE_LOAD_FAILED"
STATE_SAVE_FAILED           = "STATE_SAVE_FAILED"
EVENT_APPEND_FAILED         = "EVENT_APPEND_FAILED"
CHRONICLE_APPEND_FAILED     = "CHRONICLE_APPEND_FAILED"

# Exhaustion errors (new)
RULING_PARSE_FAILED         = "RULING_PARSE_FAILED"
EXTRACTION_PARSE_FAILED     = "EXTRACTION_PARSE_FAILED"
```

### Done when
- All 20 constants added to `ccya/errors.py` in the appropriate section.
- `make check` passes (lint + typecheck).

---

## Phase 2: Log Level Corrections (Core)

**What changes:** Promote `load_state()` default returns to ERROR, demote ruling exhaustion from ERROR to WARNING.

### Files to read
- `ccya/state/io.py:112-135` — `load_state()` default returns
- `ccya/engine/ruling.py:140-150` — ruling exhaustion logging

### Changes

#### `io.py:115` — load_state returns default (file not found)
```python
# Before:
_log.debug("load_state file not found — returning default state: %s", save_dir)

# After:
_log.error("load_state file not found — returning default state: %s", save_dir,
           extra={"error_kind": "STATE_LOAD_FAILED"})
```

#### `io.py:122` — load_state YAML parse error
```python
# Before:
_log.warning("load_state malformed YAML — returning default state: %s", save_dir, exc_info=True)

# After:
_log.error("load_state malformed YAML — returning default state: %s", save_dir,
           extra={"error_kind": "STATE_LOAD_FAILED"}, exc_info=True)
```

#### `io.py:125` — load_state unexpected error
```python
# Before:
_log.debug("load_state unexpected error — returning default state: %s: %s", save_dir, exc)

# After:
_log.error("load_state unexpected error — returning default state: %s: %s", save_dir, exc,
           extra={"error_kind": "STATE_LOAD_FAILED"}, exc_info=True)
```

#### `ruling.py:146-149` — ruling exhaustion
```python
# Before:
_log.error("ruling call failed after %d attempts: %s", config.max_llm_retries + 1, exc)

# After:
_log.warning("ruling call failed after %d attempts: %s", config.max_llm_retries + 1, exc,
             extra={"error_kind": "RULING_PARSE_FAILED"})
```

### Done when
- All 4 log calls updated with correct level and `extra` dict.
- `make check` passes.

---

## Phase 3: State Mutation Logging

**What changes:** Add INFO logs for successful inventory/condition/location/NPC mutations, WARNING for failures.

### Files to read
- `ccya/state/delta_builder.py:117-291` — `apply_delta()` function
- `ccya/state/inventory.py:34-108` — inventory normalization and resolution
- `ccya/state/npcs.py:184-325` — NPC scene management

### Prerequisite: Add trace_id to apply_delta signature

`apply_delta()` doesn't currently accept `trace_id`. Add it as an optional parameter. `turn_no` is already derived from `state["meta"]["turn"]` at line 235 (`current_turn`), so no new parameter needed for that.

```python
# Before (delta_builder.py:117-119):
def apply_delta(
    state: dict[str, Any], delta: StateDelta,
) -> dict[str, Any]:

# After:
def apply_delta(
    state: dict[str, Any], delta: StateDelta,
    *, trace_id: str | None = None,
) -> dict[str, Any]:
```

The `delta.py` wrapper doesn't need changes — it delegates to `delta_builder.apply_delta` and the new parameter defaults to `None`.

In `turn.py:1150-1152`, pass the parameter:
```python
state = apply_delta(
    state, delta, trace_id=trace_id,
)
```

In `extraction.py:117`, leave as-is (trace_id defaults to None; logs won't have trace_id in extraction context builder, which is acceptable per the structured logging standard: "`trace_id` is always included when available").

All logs in `apply_delta` use `current_turn` (already computed at line 235 from `state["meta"]["turn"]`) for the `turn` field.

### Changes

#### `delta_builder.py:132-171` — inventory add success
Add INFO log after each successful inventory add (after line 170 where `inv.append(d)` completes):
```python
_log.info("inventory_add.applied item=%s amount=%d", d["id"], d["amount"],
          extra={"trace_id": trace_id, "turn": current_turn})
```

#### `delta_builder.py:176-179` — inventory_remove target not found
```python
# Before:
_log.debug("inventory_remove target not found item=%s", rem.id)

# After:
_log.warning("inventory_remove target not found item=%s", rem.id,
             extra={"trace_id": trace_id, "turn": current_turn, "error_kind": "INVENTORY_REMOVE_FAILED"})
```

#### `delta_builder.py:187-191` — inventory_remove amount coerced (keep WARNING, add error_kind)
```python
# Before:
_log.warning("inventory_remove amount coerced to 0 item=%s", rem.id)

# After:
_log.warning("inventory_remove amount coerced to 0 item=%s", rem.id,
             extra={"trace_id": trace_id, "turn": current_turn, "error_kind": "INVENTORY_REMOVE_FAILED"})
```

#### `delta_builder.py:204-205` — inventory_update target not found
```python
# Before:
_log.debug("inventory_update target not found item=%s", upd.id)

# After:
_log.warning("inventory_update target not found item=%s", upd.id,
             extra={"trace_id": trace_id, "turn": current_turn, "error_kind": "INVENTORY_UPDATE_FAILED"})
```

#### `delta_builder.py:215-233` — location change success
Add INFO log after successful location change (after line 233 where `state["location"]` is set):
```python
_log.info("location_change.applied location=%s name=%s", loc.id, loc.name,
          extra={"trace_id": trace_id, "turn": current_turn})
```

#### `delta_builder.py:237-264` — condition add/remove success
Add INFO log after each condition mutation (after line 264 where conditions are modified):
```python
_log.info("condition_change.applied action=%s name=%s", action, cond_name,
          extra={"trace_id": trace_id, "turn": current_turn})
```

#### `delta_builder.py:213-214` — location change invalid (keep WARNING, add error_kind)
```python
# Before:
_log.warning("location_change invalid: missing id or name")

# After:
_log.warning("location_change invalid: missing id or name",
             extra={"trace_id": trace_id, "turn": current_turn, "error_kind": "LOCATION_CHANGE_INVALID"})
```

#### `inventory.py:55` — resolve_inventory_canonical_id no match
```python
# Before:
_log.debug("resolve_inventory_canonical_id raw=%s normalized=%s no match", raw_id, want)

# After:
_log.warning("resolve_inventory_canonical_id no match raw=%s normalized=%s", raw_id, want,
             extra={"error_kind": "INVENTORY_NORMALIZE_FAILED"})
```

#### `npcs.py:184-188` — Add trace_id parameter to apply_npc_scene_management
```python
# Before:
def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
) -> dict[str, Any]:

# After:
def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
```

#### `npcs.py:196-200` — NPC scene management personality
```python
# Before:
_log.debug("apply_npc_scene_management npc=%s personality=%s", resolved_id, comp_upd.personality)

# After:
_log.info("npc_scene_management.applied npc=%s personality=%s", resolved_id, comp_upd.personality,
          extra={"trace_id": trace_id, "turn": current_turn_no})
```

#### `npcs.py:231-234` — NPC scene management presence
```python
# Before:
_log.debug("apply_npc_scene_management npc=%s presence=%s", resolved_id, comp_upd.presence)

# After:
_log.info("npc_scene_management.applied npc=%s presence=%s", resolved_id, comp_upd.presence,
          extra={"trace_id": trace_id, "turn": current_turn_no})
```

#### `npcs.py:287-290` — NPC scene management personality (comp_upd path)
```python
# Before:
_log.debug("apply_npc_scene_management npc=%s personality=%s", resolved_id, comp_upd.personality)

# After:
_log.info("npc_scene_management.applied npc=%s personality=%s", resolved_id, comp_upd.personality,
          extra={"trace_id": trace_id, "turn": current_turn_no})
```

#### `delta_builder.py:271-276` — Pass trace_id to apply_npc_scene_management
```python
# Before:
state = apply_npc_scene_management(state, SceneExtractResult(
    compendium_npc_update=delta.compendium_npc_update or [],
    scene_tagline=delta.scene_tagline,
    location_change=delta.location_change,
    location_description=delta.location_description,
), current_turn_no=current_turn)

# After:
state = apply_npc_scene_management(state, SceneExtractResult(
    compendium_npc_update=delta.compendium_npc_update or [],
    scene_tagline=delta.scene_tagline,
    location_change=delta.location_change,
    location_description=delta.location_description,
), current_turn_no=current_turn, trace_id=trace_id)
```

#### `npcs.py:172-182` — strip_npcs_notes (add DEBUG log)
Add DEBUG log at the start of the function:
```python
_log.debug("strip_npcs_notes count=%d", len(npcs))
```

### Done when
- All log calls updated with correct level and `extra` dict.
- `make check` passes.

---

## Phase 4: Turn-Level Logging

**What changes:** Add condition aging expiry log at INFO, promote overdraw clamp from WARNING to INFO.

### Files to read
- `ccya/engine/turn.py:1066-1084` — condition aging pass
- `ccya/engine/turn.py:1156-1161` — overdraw clamp

### Changes

#### `turn.py:1075-1080` — condition aging expiry
Add INFO log when conditions expire:
```python
_log.info("condition_aging.expired conditions=%s turn=%d", expired, turn_no,
          extra={"trace_id": trace_id, "turn": turn_no})
```

#### `turn.py:1156-1161` — overdraw clamp
```python
# Before:
_log.warning("overdraw clamp: removing %s (amount %d exceeds owned %d)", item_id, amount, owned)

# After:
_log.info("overdraw.clamped item=%s amount=%d owned=%d", item_id, amount, owned,
          extra={"trace_id": trace_id, "turn": turn_no})
```

### Done when
- Both log calls updated.
- `make check` passes.

---

## Phase 5: Chronicle Persistence Error Kinds

**What changes:** Add try/except wrappers with error kinds in `chronicle.py` append functions.

### Files to read
- `ccya/state/chronicle.py:16-30` — `append_event` and `append_chronicle`

### Changes

#### `chronicle.py:16-20` — append_event
```python
# Before:
def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    _log.debug("append_event turn=%d", event.get("turn", 0))
    path = save_dir / "events.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")

# After:
def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    _log.debug("append_event turn=%d", event.get("turn", 0))
    path = save_dir / "events.jsonl"
    try:
        with open(path, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        _log.error("event_append_failed turn=%d: %s", event.get("turn", 0), exc,
                   extra={"error_kind": "EVENT_APPEND_FAILED"}, exc_info=True)
        raise
```

#### `chronicle.py:23-30` — append_chronicle
```python
# Before:
def append_chronicle(save_dir: Path, entry: str) -> None:
    _log.debug("append_chronicle length=%d", len(entry))
    path = save_dir / "chronicle.md"
    with open(path, "a") as f:
        f.write(entry + "\n")

# After:
def append_chronicle(save_dir: Path, entry: str) -> None:
    _log.debug("append_chronicle length=%d", len(entry))
    path = save_dir / "chronicle.md"
    try:
        with open(path, "a") as f:
            f.write(entry + "\n")
    except Exception as exc:
        _log.error("chronicle_append_failed length=%d: %s", len(entry), exc,
                   extra={"error_kind": "CHRONICLE_APPEND_FAILED"}, exc_info=True)
        raise
```

### Done when
- Both append functions wrapped with try/except.
- `make check` passes.

---

## Phase 6: Extraction Coercion Error Kind

**What changes:** Add try/except with error kind in `extraction.py` coercion path.

### Files to read
- `ccya/engine/extraction.py:399-438` — `_coerce_scene_json` and `_parse_stream_output`

### Changes

#### `extraction.py:430-438` — _parse_stream_output coercion
```python
# Before:
def _parse_stream_output(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    # Coerce LLM output to match Pydantic model expectations
    return model_cls(**_coerce_scene_json(j))

# After:
def _parse_stream_output(raw: str, model_cls: type, strip_keys: tuple[str, ...] = ("_reasoning",)) -> Any:
    """Parse JSON from LLM output, strip internal keys, validate with model_cls."""
    cleaned = strip_thinking(raw)
    j = _find_json(cleaned)
    if j is None:
        raise ValueError("No JSON found in response")
    for k in strip_keys:
        j.pop(k, None)
    try:
        # Coerce LLM output to match Pydantic model expectations
        return model_cls(**_coerce_scene_json(j))
    except Exception as exc:
        raise ValueError(f"Coercion failed: {exc}") from exc
```

Note: The coercion error is re-raised as `ValueError` to maintain the existing retry logic in `_call_stream`. The error kind is tracked via the retry error message (already captured in `retry_errors` list at line 485-492).

### Done when
- Coercion path wrapped with try/except.
- `make check` passes.

---

## Phase 7: Exhaustion Error Kinds

**What changes:** Add error kinds at ruling/extraction exhaustion points.

### Files to read
- `ccya/engine/ruling.py:140-150` — ruling exhaustion
- `ccya/engine/extraction.py:480-505` — extraction stream exhaustion

### Changes

#### `ruling.py:146-149` — already handled in Phase 2 (demote to WARNING, add RULING_PARSE_FAILED)

#### `extraction.py:505` — extraction stream exhaustion
```python
# Before:
raise ValueError(f"All {config.max_llm_retries + 1} attempts failed for {phase}: {retry_errors_str}")

# After:
raise ValueError(f"EXTRACTION_PARSE_FAILED: All {config.max_llm_retries + 1} attempts failed for {phase}: {retry_errors_str}")
```

The error kind string is prepended to the message so callers can classify it. The retry error list already captures per-attempt failures at line 485-492.

### Done when
- Exhaustion points enriched with error kind strings.
- `make check` passes.

---

## Phase 8: SSE Error Surfacing

**What changes:** Extend `routes.py:252` to yield `turn_error` SSE events for all `result.errors`.

### Files to read
- `ccya/server/routes.py:251-270` — `/turn` SSE endpoint error handling

### Changes

#### `routes.py:251-270` — extend error SSE events
```python
# Before (lines 251-269):
for err in result.errors:
    _log.error("turn_result error: %s", err)

# ... (all-streams-failed SSE event at lines 262-269)

# After:
for err in result.errors:
    kind = err.get("error_kind", "") or err.get("kind", "")
    yield {
        "event": "turn_error",
        "data": json.dumps({
            "error": err.get("message", ""),
            "kind": kind,
            "trace_id": result.trace_id,
        }),
    }

# ... (all-streams-failed SSE event at lines 262-269 — keep as-is, it's the fallback)
```

**Note:** The SSE handler does NOT re-log errors. Errors already carry structured metadata at creation site. Handler only yields SSE events.

### Done when
- SSE error events yielded for all `result.errors`.
- `make check` passes.

---

## Phase 9: StreamHandler → WARNING

**What changes:** Change StreamHandler default level from INFO to WARNING in `logging_setup.py`.

### Files to read
- `ccya/logging_setup.py:35-45` — StreamHandler setup

### Changes

#### `logging_setup.py:40` — StreamHandler level
```python
# Before:
stream_handler.setLevel(logging.INFO)

# After:
stream_handler.setLevel(logging.WARNING)
```

This is the prerequisite for Phase 3 — without this change, promoting inventory/condition/NPC mutations to INFO would flood the server console.

### Done when
- StreamHandler level changed to WARNING.
- `make check` passes.

---

## Phase 10: Documentation Updates

**What changes:** Update `docs/architecture/`, `docs/repomap.md`, `AGENTS.md` to reflect new logging standards.

### Files to read
- `docs/architecture/logging-standards.md` — if exists, update log level conventions
- `docs/repomap.md` — update module descriptions for logging changes
- `AGENTS.md` — update logging section if needed

### Changes

1. **`docs/architecture/logging-standards.md`** (create if doesn't exist): Document the log level conventions:
   - ERROR: state-damaging failures (load failure, save failure, append failure)
   - WARNING: recoverable anomalies (parse failures, resolution failures, exhaustion)
   - INFO: routine state mutations (inventory, conditions, location, NPC, thread, arc)
   - DEBUG: diagnostic traces (resolution success, per-step timing, LLM I/O)

2. **`docs/repomap.md`**: Update module descriptions for:
   - `ccya/errors.py`: list all 20 new error kinds
   - `ccya/state/delta_builder.py`: note INFO/WARNING logging for mutations
   - `ccya/state/chronicle.py`: note try/except wrappers
   - `ccya/server/routes.py`: note SSE error surfacing

3. **`AGENTS.md`**: Update logging section if log level standards need updating.

### Done when
- All documentation updated.
- `make check` passes.

---

## Execution Order

1. **Phase 1** (ErrorKind additions) — must be first; all downstream phases depend on these constants
2. **Phase 2** (Log level corrections core) — independent, can run in parallel with Phase 1
3. **Phase 3** (State mutation logging) — depends on Phase 1 (ErrorKind constants)
4. **Phase 4** (Turn-level logging) — depends on Phase 1
5. **Phase 5** (Chronicle persistence) — depends on Phase 1
6. **Phase 6** (Extraction coercion) — depends on Phase 1
7. **Phase 7** (Exhaustion error kinds) — Phase 2 already handles ruling exhaustion; extraction exhaustion is independent
8. **Phase 8** (SSE error surfacing) — depends on Phase 1 (ErrorKind constants for `error_kind` field)
9. **Phase 9** (StreamHandler → WARNING) — must be done alongside Phase 3 (prerequisite); can run anytime after Phase 1
10. **Phase 10** (Documentation) — must be last

**Recommended execution order:** 1 → 2 → 3+9 → 4 → 5 → 6 → 7 → 8 → 10

Phases 3 and 9 should be committed together (StreamHandler change is prerequisite for INFO-level mutations).

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
2. Run a few turns with `ev.py play` — verify:
   - State load failures appear at ERROR level
   - Inventory/condition/NPC mutations appear at INFO level
   - Ruling/extraction exhaustion appears at WARNING level
   - SSE `turn_error` events appear in browser devtools for per-stream errors
   - StreamHandler only shows WARNING+ on server console (no INFO noise)
3. Check JSONL log file for `error_kind` field in WARNING/ERROR records

---

## Context for Implementing LLMs

Files to read before starting any phase. One line per file: what it contains and why it matters.

- **`ccya/logging_setup.py`** — Current logging infrastructure; `_JsonFormatter` already iterates over all record attributes (line 57-61), so new `extra` fields appear automatically. Phase 9 changes StreamHandler level.
- **`ccya/errors.py`** — ErrorKind constants and LlmcError exception hierarchy. Phase 1 adds 20 new error kinds.
- **`ccya/state/io.py:112-135`** — `load_state()` returns default at DEBUG/WARNING. Phase 2 promotes to ERROR.
- **`ccya/state/delta_builder.py:117-291`** — `apply_delta()` has inventory/condition/location/NPC mutation logic. Phase 3 adds INFO/WARNING logs.
- **`ccya/state/inventory.py:34-108`** — Inventory normalization and resolution. Phase 3 promotes DEBUG to WARNING for failures only.
- **`ccya/state/npcs.py:184-325`** — NPC scene management. Phase 3 promotes DEBUG to INFO.
- **`ccya/engine/turn.py:1066-1084, 1138-1161, 1473-1508`** — Condition aging, overdraw clamp, error handling. Phase 4 adds/promotes logs.
- **`ccya/engine/ruling.py:69-150`** — Ruling call with retry. Phase 2 demotes exhaustion to WARNING.
- **`ccya/engine/extraction.py:441-505`** — Extraction stream retry logic. Phase 6/7 add error kinds.
- **`ccya/server/routes.py:251-270`** — `/turn` SSE endpoint. Phase 8 yields `turn_error` events for all `result.errors`.
- **`ccya/state/chronicle.py:16-30`** — Event/chronicle append. Phase 5 adds try/except wrappers.
- **`docs/design/complete/logging-framework-design.md`** — Design authority. All decisions must be consistent with this doc.
