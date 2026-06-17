# Logging Framework — Log Levels and Structured Error Instrumentation

## Purpose

This document defines the log level strategy, structured error instrumentation, and error-to-UI surfacing for the ccya engine. It addresses gaps identified in the engine failure points analysis (`docs/findings/logging-framework.md`) that are not covered by the observability design (`docs/design/complete/observability-design.md`). Reference: "This document is the design authority for plans implementing log level changes, error kind additions, and SSE error surfacing."

## Problem Statement

The engine's logging has three categories of problems:

1. **Log level misalignment.** State-damaging failures (inventory corruption, location corruption, state load failure) are logged at DEBUG or WARNING — below the operator's visible threshold. Recoverable failures (ruling exhaustion, extraction stream exhaustion) are logged at ERROR — too severe for non-fatal paths. Routine state mutations (inventory add/remove, condition management, NPC scene management) are logged at DEBUG — invisible to operators who need to audit what changed.

2. **Missing error kinds.** `ccya/errors.py` has no error kinds for state mutation failures (inventory, conditions, location, NPC, arc, thread). When these failures occur, they either crash with a bare `TURN_PROCESSING_FAILED` or are silently swallowed with no structured signal.

3. **TurnResult.errors invisible to UI.** `routes.py:252` iterates `result.errors` and logs them at ERROR, but never yields an SSE `turn_error` event. The player never sees per-stream extraction errors or delta validation rejections. Only the top-level exception path (all 3 streams failed) produces an SSE error event.

## Constraints

- **No new dependencies.** Must use Python stdlib `logging` only.
- **Backward compatible.** Existing log calls without new `extra` fields produce identical output.
- **ErrorKind must remain string constants** (not `Enum`) — `TurnResult.errors` is `list[dict]` used in JSON serialization and Pydantic models.
- **Observability design is the parent.** This doc's error kind taxonomy extends `ccya/errors.py` as defined in `docs/design/complete/observability-design.md`. All decisions here must be consistent with the observability design's visibility convention (ERROR = stderr always visible, WARNING = stdout visible, INFO = file only at WARNING+ StreamHandler, DEBUG = file only).

## Non-goals

- **LLM client typed exceptions.** Covered by observability design (Phase 3).
- **FastAPI middleware for unhandled exceptions.** Covered by observability design (Phase 4).
- **Server error persistence (`server_errors.jsonl`).** Covered by observability design (Phase 4).
- **Turn viewer enrichment.** Covered by observability design (Phase 5).
- **JSONL formatter field extension.** Covered by observability design (Phase 1).
- **Logger naming standardization.** Covered by observability design (Phase 2).
- **Health telemetry logging.** Covered by observability design (Phase 5).

## Decision Table

| Decision | What | Why |
|---|---|---|
| State mutation failures → ERROR | `load_state()` returning default, `save_state()` failure, `events.jsonl`/`chronicle.md` write failure logged at ERROR | Player loses game state or data is corrupted. Must be visible on stderr immediately. |
| Recoverable anomalies → WARNING | LLM retries, parse failures (per attempt), delta reconciliation conflicts, overdraw clamp, fuzzy inventory merge | Operator should see these on stdout but not panic. Retryable, turn continues. |
| Recoverable exhaustion → WARNING | Ruling parse exhaustion, extraction stream exhaustion (all retries failed) | Turn continues with degraded output (no-roll, skipped stream). Not fatal, but significant. |
| Routine state mutations → INFO | Inventory add/remove/update, condition add/remove, location change, arc updates, NPC scene management, thread cap eviction | Operator needs to audit what changed each turn. These are the primary state mutation signals. |
| Esoteric/diagnostic → DEBUG | Per-step timing, LLM call start/end, token counts, conditional branches, inventory resolution traces | Diagnostic detail for debugging. File only. |
| `TurnResult.errors` → SSE events | Yield `turn_error` SSE event for each item in `result.errors` | Player must see per-stream errors and validation rejections. Currently invisible. |
| Structured `extra` dict standard | Every log call includes `{"trace_id": str, "turn": int, "error_kind": str}` when available | Enables log file analysis via field filtering rather than message parsing. Required by observability design's JSONL formatter extension. |
| `inventory_remove`/`inventory_update` already guarded | Code at `delta_builder.py:175-180` and `delta_builder.py:204-205` already does `if not canonical: continue` | The findings doc's primary 500 claims are incorrect — these paths are already handled. No fix needed. |

## Current State — What Exists

### Log Level Inventory (Verified Against Source)

**INFO level (visible on stdout at default config):**
- Ruling call start (`ruling.py:83-87`)
- Thread updates applied, auto-latent, urgency decay (`turn.py:195-196, 212-215, 238-241`)
- Arc resolve applied (`turn.py:302-306`)
- Thread cap eviction (`turn.py:1284-1288`)
- `goal_update` visible_goal changes (`turn.py:1221-1225`)
- `inventory fuzzy merge` (`delta_builder.py:162-166`)
- `Applied N Storyteller Actions` (`delta_builder.py:286-289`)
- `archived_departed_npcs` (`turn.py:1320-1323`)
- Server app startup (pack loaded, model warmup, save resumed)
- Server routes errors: pack load failure, new_game failure, generate_seed reroll failure

**DEBUG level (file-only):**
- `load_state` default state returns (`io.py:115, 125`)
- Inventory resolution traces (canonical ID lookups, fuzzy matches) (`inventory.py:49, 53, 55, 72, 107`)
- `strip_npcs_notes` (`npcs.py:172-182` — no log at all currently)
- `build_npc_alias_map` (`npcs.py:72`)
- `touch_compendium_order` (`npcs.py:118`)
- `apply_npc_scene_management` details (`npcs.py:196-200, 231-234, 287-290`)
- Per-stream extraction results (`extraction.py:584, 632, 721, 743-746, 753-754, 785`)
- Per-stream merge/dedup (`extraction.py:724, 743-746`)
- Condition aging pass (`turn.py:1066-1084` — no log at all currently)
- Persist calls (append_event, append_chronicle) (`chronicle.py:18, 26`)
- `inventory_remove target not found` (`delta_builder.py:176-179`)
- `inventory_remove amount coerced` (`delta_builder.py:187-191`)
- `resolve_inventory_canonical_id` no match (`inventory.py:55`)
- `_fuzzy_match_inventory` results (`inventory.py:107`)

**WARNING level:**
- Delta reconciliation conflicts (`delta_builder.py:88, 100, 111`)
- Thread progress dedup rejections (`turn.py:168-171`)
- Stream parse failures (per attempt) (`extraction.py:485-492`)
- Ruling parse failures (per attempt) (`ruling.py:131-137`)
- Stream timeout/LLM errors (per stream) (`extraction.py:576, 622, 711`)
- Ruling failure exhausted (`ruling.py:146-149`) — **ERROR, not WARNING**
- `resolve_check` failure (`turn.py:646-648`)
- Config warnings
- `thread_sanitizer` failures
- `cancel_turn` state_snapshot missing (`routes.py:319, 332`)
- `delete_last_turn` state_snapshot missing (`routes.py:363`)
- YAML parse errors (`io.py:122`)
- Schema version mismatch (`io.py:131-134`)
- Prompts log write failure (`ruling.py:188-189`)

**ERROR level:**
- `run_turn` extraction pipeline error (top-level) (`turn.py:1043-1044`)
- `run_turn` LLM timeout (`turn.py:1474-1477`)
- `run_turn` LLM error (`turn.py:1480-1483`)
- `run_turn` generic exception (`turn.py:1488-1491`)
- Routes: Turn failed (exception) (`routes.py:302`)
- Routes: Pack load failed (`routes.py:385`)
- Routes: new_game failed (`routes.py:452`)
- Routes: generate_seed reroll failed (`routes.py:473`)
- `turn_result.errors` loop iteration (route level) (`routes.py:253`)
- Switch_save load failure (`routes.py:876`)
- Delete_save OSError (`routes.py:930`)
- Ruling call failed after all attempts (`ruling.py:146-149`)

### Problems with Current State

1. **`load_state()` returns default at DEBUG level** (`io.py:115, 125`). Player loses entire game state with no warning visible on stdout. Should be ERROR.

2. **Ruling exhaustion at ERROR** (`ruling.py:146-149`). Recoverable failure — turn continues with no-roll. Should be WARNING.

3. **Inventory/condition/NPC resolution failures at DEBUG** (`delta_builder.py:176-179`, `inventory.py:55`, `npcs.py:72, 118, 196-200, 231-234, 287-290`). These affect game state but are invisible to operators. Should be WARNING (failures) or INFO (successful mutations). Resolution success traces (`inventory.py:49, 53`) stay at DEBUG to avoid noise.

4. **Overdraw clamp at WARNING** (`turn.py:1156-1161`). Non-blocking state change — item removed despite insufficient quantity. Player never knows. Should be INFO (operator-visible state mutation).

5. **TurnResult.errors never sent to UI** (`routes.py:252`). Logged at ERROR but no SSE event. Player never sees per-stream errors or validation rejections.

7. **Missing error kinds** (`ccya/errors.py`). No error kinds for inventory failures, condition failures, location failures, NPC failures, arc/thread failures, state save/append failures.

8. **Condition aging pass has no logging** (`turn.py:1066-1084`). Conditions expire silently. Should log at INFO when expired.

9. **`_coerce_scene_json()` incomplete** (`extraction.py:399`). Hand-written coercion handles string→dict for npc_update and malformed thread_add, but any other shape mismatch from the LLM crashes through to stream skip. No structured error kind for coercion failures.

10. **`strip_npcs_notes()` has no logging** (`npcs.py:172-182`). Silent operation. Should log at DEBUG (already is diagnostic, but currently has no log at all).

### Verified: Incorrect Claims in Findings Doc

The findings doc (`docs/findings/logging-framework.md`) makes several claims about crash paths that are **already handled in the code**:

- **`inventory_remove` KeyError at `delta_builder.py:181`** — Code at line 175-180 does `if not canonical: ... continue`. No crash.
- **`inventory_update` KeyError at `delta_builder.py:206`** — Code at line 204-205 does `if not canonical: continue`. No crash.
- **`_validate()` KeyError at line 1547** — Code at line 1539 checks `if canonical is None: rejections.append(...); continue` and line 1547 uses `.get(canonical)` not `[]`. Already handled.

These are false positives in the findings doc. No fix needed.

## Proposed Solution

### Core Changes

#### 1. Log Level Corrections

| Current | Target | Location | Reason |
|---|---|---|---|
| `load_state()` default returns (DEBUG) | ERROR | `io.py:115, 122, 125` | Player lost game state |
| Ruling exhaustion (ERROR) | WARNING | `ruling.py:146-149` | Recoverable — turn continues |
| Inventory resolution failures (DEBUG) | WARNING | `inventory.py:55`, `delta_builder.py:176-179` | Operator-visible state impact |
| Inventory resolution success traces (DEBUG) | Keep DEBUG | `inventory.py:49, 53` | Per-item noise; mutation outcomes logged at INFO |
| Inventory resolution success (none) | INFO | `delta_builder.py:132-171` | Routine state mutation |
| Condition add/remove (none) | INFO | `delta_builder.py:237-264` | Routine state mutation |
| Location change (none) | INFO | `delta_builder.py:215-233` | Routine state mutation |
| NPC scene management (DEBUG) | INFO | `npcs.py:196-200, 231-234, 287-290` | Routine state mutation |
| Overdraw clamp (WARNING) | INFO | `turn.py:1156-1161` | Operator-visible state mutation |
| Condition aging expiry (none) | INFO | `turn.py:1075-1080` | Routine state mutation |
| `strip_npcs_notes()` (none) | DEBUG | `npcs.py:172-182` | Diagnostic trace |
| Persist calls (DEBUG) | Keep DEBUG | `chronicle.py:18, 26` | Diagnostic trace |
| Per-stream extraction (DEBUG) | Keep DEBUG | `extraction.py:584, 632, 721, 785` | Diagnostic trace |

#### 2. New ErrorKinds

Add to `ccya/errors.py`:

```
INVENTORY_REMOVE_FAILED     — canonical not found in inventory
INVENTORY_UPDATE_FAILED     — canonical not found for update
INVENTORY_ADD_FAILED        — type error in item_to_dict (non-string ID)
DELTA_VALIDATION_FAILED     — blocking rejections from _validate()
LOCATION_CHANGE_INVALID     — None id/name on location_change
STATE_LOAD_FAILED           — load_state() returned default state
STATE_SAVE_FAILED           — yaml dump/replace error
EVENT_APPEND_FAILED         — JSON serialization error in append_event
CHRONICLE_APPEND_FAILED     — file write error in append_chronicle
THREAD_UPDATE_INVALID       — ArcThread.model_validate fails
ARC_RESOLVE_INVALID         — CampaignArc.model_validate fails
THREAD_RESOLVE_INVALID      — promote_to_world_state type error
EXTRACTION_CONTEXT_BUILD_FAILED — apply_delta fails in _build_extraction_context
EXTRACTION_COERCION_FAILED  — _coerce_scene_json shape mismatch (LLM returns unexpected type)
INVENTORY_NORMALIZE_FAILED  — None input to normalize_inventory_id
FUZZY_MATCH_FAILED          — None input to _fuzzy_match_inventory
NPC_NAME_LOOKUP_FAILED      — None name in _find_npc_by_name
RULING_PARSE_FAILED         — ruling exhaustion after all retries
EXTRACTION_PARSE_FAILED     — extraction stream exhaustion after all retries
```

#### 3. SSE Error Surfacing

In `routes.py:251-270`, after the existing `result.errors` loop:

```python
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
```

This yields an SSE `turn_error` event for every error in `TurnResult.errors`, not just the all-streams-failed case. The SSE handler at `routes.py:262-269` already yields `turn_error` events for the all-streams-failed case; this extends it to all per-stream errors. Errors already carry structured metadata at their creation site (e.g., `turn.py:1044`), so the SSE handler does not re-log — it only yields the event. The frontend must handle `turn_error` events with the `kind` field for classification.

#### 4. Structured Logging Standard

Every log call in the engine must follow this pattern:

```python
_log.info("inventory_add.applied item=%s amount=%d", item_id, amount,
          extra={"trace_id": trace_id, "turn": turn_no})

_log.warning("inventory_remove.target_not_found item=%s", item_id,
             extra={"trace_id": trace_id, "turn": turn_no, "error_kind": "INVENTORY_REMOVE_FAILED"})

_log.error("state_load.default_returned save_dir=%s reason=%s", save_dir, reason,
           extra={"error_kind": "STATE_LOAD_FAILED"})
```

**Rules:**
- `trace_id` is always included when available (turn context).
- `turn` is included for turn-scoped events.
- `error_kind` is included for all WARNING and ERROR calls that represent a classified error.
- No bare `except: pass` — every exception handler must log at minimum a warning with the exception string.
- Use `_log.exception()` only in `except` blocks where you cannot recover.

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Keep DEBUG for inventory/condition/NPC failures | Operators cannot audit state changes without grep. These are the primary mutation signals. |
| Keep ERROR for ruling/extraction exhaustion | These are recoverable — the turn continues with degraded output. ERROR implies something is broken. |
| Keep `TurnResult.errors` as log-only | Player never sees per-stream errors or validation rejections. The all-streams-failed SSE event is the only error signal, which is too coarse. |
| Use `Enum` for ErrorKind | `TurnResult.errors` is `list[dict]` used in JSON serialization and Pydantic models. String constants avoid serialization issues. |
| Add a new SSE event type for errors | The UI already handles `turn_error` events. Adding a new event type would require UI changes. |
| Keep `CONDITION_OVERFLOW` error kind | No overflow scenarios exist. Dead code. |
| Re-log `TurnResult.errors` at SSE handler | Errors already carry structured metadata at creation site. Re-logging duplicates and risks misclassification. |

## Failure Modes and Risks

1. **SSE event flooding.** If a turn has many small errors (e.g., 5 inventory rejections), the UI receives 5 SSE events. Mitigation: the UI already batches error display; this is the desired behavior — the player should see all rejections.

2. **Log file noise.** Promoting inventory/condition/NPC mutations to INFO means the JSONL log file will have many more entries per turn. Mitigation: StreamHandler is changed to WARNING in the same implementation wave (observability design Phase 2), so stdout is not flooded. The JSONL log file is the source of truth for audit anyway.

3. **Backward compatibility with existing log consumers.** Adding new `extra` fields (`error_kind`, `turn`) to log records is backward compatible — the JSONL formatter already iterates over all attributes on the record (logging_setup.py:57-61). Existing consumers that don't read these fields will see identical output.

4. **TurnResult.errors already contains unstructured messages.** Some error entries (e.g., delta validation rejections at `turn.py:1138-1143`) use raw strings without `error_kind`. Adding `error_kind` to these paths is part of the structured logging standard but requires updating the error construction sites.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `load_state()` DEBUG logs for default returns | `io.py:115, 125` | Promoted to ERROR |
| `load_state()` WARNING for YAML parse error | `io.py:122` | Promoted to ERROR |
| Ruling exhaustion ERROR | `ruling.py:146-149` | Demoted to WARNING |
| Overdraw clamp WARNING | `turn.py:1156-1161` | Promoted to INFO |
| Inventory resolution DEBUG logs | `inventory.py:55` | Promoted to WARNING (failures only) |
| Inventory resolution success traces | `inventory.py:49, 53` | Keep DEBUG (per-item noise) |
| `inventory_remove` target not found DEBUG | `delta_builder.py:176-179` | Promoted to WARNING with error_kind |
| `inventory_remove` amount coerced WARNING | `delta_builder.py:187-191` | Keep WARNING (already correct level) |
| NPC scene management DEBUG logs | `npcs.py:196-200, 231-234, 287-290` | Promoted to INFO |
| Condition aging pass (no log) | `turn.py:1066-1084` | Add INFO log for expired conditions |
| `strip_npcs_notes()` (no log) | `npcs.py:172-182` | Add DEBUG log |

## What Is Unchanged

- **`_JsonFormatter` base schema** (`ts`, `level`, `message`, `logger`, trace_id, exception) — all existing fields preserved exactly as-is. The formatter already iterates over all attributes on the record (logging_setup.py:57-61), so new `extra` fields appear automatically.
- **RotatingFileHandler configuration** (5MB × 3 rotations, JSONL format) — unchanged.
- **StreamHandler default level** — Phase 2 (StreamHandler → WARNING) is a prerequisite, done in the same implementation wave. No stdout noise from promoted INFO logs.
- **TurnResult.errors structure** — now includes `error_kind` (ErrorKind constant) alongside `message` keys. Classification moves from logs-only into the data model.
- **`_ERRORS_LOG` deque** in app.py — structure enriched but container unchanged.
- **Turn viewer `_tv_failures()` function** — existing failure extraction from events.jsonl preserved.
- **LLM client `chat()` and `chat_stream()` public API signatures** — exception types change but call sites catch broadly anyway.
- **Delta validation `_validate()` function** — already correctly guards against `None` canonical (line 1539) and uses `.get()` (line 1547). No structural changes needed.
- **`_coerce_scene_json()` coercion logic** — incomplete coercion is a known limitation. Adding error kinds for coercion failures is sufficient; no restructuring of the coercion function.
- **Observability design's Phase 1-5 migration plan** — this design's changes are additive to the observability design's migration phases. Log level corrections and error kind additions can be done in Phase 1-2 alongside the foundation work.

## New Model Shapes

### ErrorKind Additions (`ccya/errors.py`)

```
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

### SSE turn_error Event Payload

```json
{
    "error": "Item 'wooden sword' not found in inventory",
    "kind": "INVENTORY_REMOVE_FAILED",
    "trace_id": "a1b2c3d4"
}
```

### JSONL Log Record Examples

**Inventory removal failure (WARNING):**
```json
{
    "ts": "2025-01-15T14:30:00.123",
    "level": "WARNING",
    "message": "inventory_remove target not found item=wooden_sword",
    "logger": "ccya.state.delta_builder",
    "trace_id": "a1b2c3d4",
    "turn": 47,
    "error_kind": "INVENTORY_REMOVE_FAILED"
}
```

**State load failure (ERROR):**
```json
{
    "ts": "2025-01-15T14:30:00.123",
    "level": "ERROR",
    "message": "load_state malformed YAML — returning default state: ...",
    "logger": "ccya.state.io",
    "error_kind": "STATE_LOAD_FAILED"
}
```

**Inventory add success (INFO):**
```json
{
    "ts": "2025-01-15T14:30:00.123",
    "level": "INFO",
    "message": "inventory_add.applied item=wooden_sword amount=1",
    "logger": "ccya.state.delta_builder",
    "trace_id": "a1b2c3d4",
    "turn": 47
}
```

## Decisions (from review)

1. **StreamHandler prerequisite.** Phase 2 (StreamHandler → WARNING) must be done in the same implementation wave as log level corrections. No stdout noise.

2. **Inventory resolution traces.** Keep `resolve_inventory_canonical_id` success traces at DEBUG (`inventory.py:49, 53`). Only mutation outcomes (add/remove/apply at `delta_builder.py`) go to INFO.

3. **CONDITION_OVERFLOW removed.** No overflow scenarios exist. Error kind removed from the taxonomy.

4. **TurnResult.errors re-logging.** SSE handler does not re-log errors. Errors already carry structured metadata at creation site. Handler only yields SSE events.

5. **Frontend `turn_error` kind handling.** Assume frontend already handles `turn_error` events with `kind` field. No UI changes required.

6. **`EXTRACTION_COERCION_FAILED` naming.** Renamed from `SCENE_DEDUP_FAILED` to accurately reflect where coercion failures occur in `_coerce_scene_json()` (`extraction.py:470-479`).

## Context for Implementing LLMs

Files to read before starting any plan. One line per file: what it contains and why it matters.

- **`ccya/logging_setup.py`** — Current logging infrastructure; `_JsonFormatter` already iterates over all record attributes (line 57-61), so new `extra` fields appear automatically. No formatter changes needed.
- **`ccya/errors.py`** — ErrorKind constants and LlmcError exception hierarchy. Must add 20 new error kinds.
- **`ccya/state/io.py:112-135`** — `load_state()` returns default at DEBUG/WARNING. Must promote to ERROR.
- **`ccya/state/delta_builder.py:117-291`** — `apply_delta()` has inventory/condition/location/NPC mutation logic. Must add INFO logs for successful mutations, WARNING for failures.
- **`ccya/state/inventory.py:34-108`** — Inventory normalization and resolution. Must promote DEBUG logs to WARNING for failures only (`inventory.py:55`); success traces (`inventory.py:49, 53`) stay DEBUG.
- **`ccya/state/npcs.py:184-325`** — NPC scene management. Must promote DEBUG logs to INFO.
- **`ccya/engine/turn.py:1066-1084, 1138-1161, 1473-1508`** — Condition aging, overdraw clamp, error handling. Must add INFO logs, promote overdraw to INFO.
- **`ccya/engine/ruling.py:69-150`** — Ruling call with retry. Must demote exhaustion from ERROR to WARNING, add RULING_PARSE_FAILED error_kind.
- **`ccya/engine/extraction.py:441-505`** — Extraction stream retry logic. Must add EXTRACTION_PARSE_FAILED error_kind for exhaustion.
- **`ccya/server/routes.py:251-270`** — `/turn` SSE endpoint. Must yield `turn_error` events for all `result.errors`, not just all-streams-failed.
- **`ccya/state/chronicle.py:16-30`** — Event/chronicle append. Must add error kinds for write failures (currently unhandled — exceptions propagate).
- **`docs/design/complete/observability-design.md`** — Parent observability design. Must be consistent with its visibility convention and migration phases.
- **`docs/findings/logging-framework.md`** — Source of the failure mode analysis. Contains verified incorrect claims (inventory_remove/update KeyError paths already guarded).
