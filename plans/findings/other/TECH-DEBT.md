# Engine Tech Debt & Dead Code Inventory

**Generated:** June 3, 2026  
**Scope:** `ccya/engine/` + `pyproject.toml` dependencies

---

## Bugs

### `_cancel_requested` Event objects never created — cancel signal dead

`ccya/engine/config.py:36,46-54`

`_cancel_requested` is typed `dict[str, asyncio.Event]` but no code ever populates it with an Event object. `request_cancel()` writes `_cancel_requested[save_dir].set()` via `.get()` (line 47), which silently no-ops on `None`. `is_cancel_requested()` always returns `None` (falsy). The entire cancel-turn feature is mechanically dead — signals are never deliverable.

### `momentum_ceiling` config setting silently ignored

`ccya/engine/config.py:121,150-213`

`EngineConfig.momentum_ceiling` defaults to `3`, but `build_engine_config()` never reads `game.momentum_ceiling` from the config dict. Any user config file setting is silently ignored.

### Ellipsis truncation indicator never fires

`ccya/engine/changes.py:40`

```python
short = str(text)[:56]
lines.append(f"+ {short}{'…' if len(short) > 56 else ''}")
```

`len(short)` can never exceed 56 because the string was already sliced. The ellipsis branch is dead. Compare with the correct pattern on line 43 of the same function which checks `len(f) > 40` on the untruncated string.

### No-op loop in `_apply_arc_resolve` — likely unset `resolved_turn`

`ccya/engine/turn.py:252-254`

```python
for t in old_arc.threads:
    if t.resolved_turn is None:
        pass  # keep existing value or None
```

Iterates threads, does nothing. The comment on line 248 says `"resolved_turn": None,  # set below after threads are processed` but no assignment was ever written. The resolved arc entry's `resolved_turn` is permanently `None`.

---

## Dead Code — Unused Fields, Params, Functions

### `TurnContext` — 22 dead dataclass fields

`ccya/engine/turn.py:85-120`

| Field | Lines | Status |
|---|---|---|
| `_narr_system`, `_narr_user`, `_narr_trimmed`, `_narr_trimmed_chars` | 85-88 | declared, never set, never read |
| `_rendered_narr_system`, `_rendered_narr_user` | 89-90 | set (896-897), never read |
| `_momentum_before`, `_momentum_after` | 92-93 | declared, never set, never read |
| `_npc_name_pool` | 95 | set (757), never read |
| `_pending_gm_beat` | 96 | set (758), never read |
| `pending_gm_beat`, `narrative`, `narrative_chunks`, `extraction_result`, `delta`, `actions`, `outcome_summary`, `extraction_event`, `storyteller_result`, `scene_result`, `extraction_ctx`, `errors`, `metrics`, `ruling_metrics`, `narr_metrics`, `ext_metrics`, `applied`, `rejected` | 100-120 | declared, never set, never read |

Only `intent`, `outcome`, and `pacing_ctx` from phase outputs are alive.

### `PacingContext.neutral()` — never called

`ccya/engine/turn.py:131-134`

Static factory method defined but zero call sites in the codebase.

### `_check_npc_ghost_cycle` — identity stub

`ccya/engine/extraction.py:103-110`

Returns input unchanged. Parameters `state`, `trace_id`, `turn_no` accepted but never read. Called at line 435 — produces zero behavior. Ghost-cycle detection was never implemented.

### `scene_result` local variable — set but never read

`ccya/engine/turn.py:996`

Unpacked from extraction pipeline output but never referenced afterward.

### `state_result` parameter in `_storytell_messages` — never read

`ccya/engine/extraction.py:231`

Accepted in signature and passed at call site (line 518), but never referenced in the function body. Stale parameter from earlier design.

### `_applied` parameter in `summarize_changes` — never read

`ccya/engine/changes.py:83`

Accepted in signature and passed at call site (`turn.py:1195`), but never referenced in the function body. Vestigial.

### `_strip_turn_prefix` Jinja filter — registered but never invoked

`ccya/engine/config.py:217,228`

Registered as `env.filters["strip_turn_prefix"]` but no `.j2` template in `ccya/prompts/` uses `|strip_turn_prefix`. Also never called as a plain Python function.

### `pop_persist_started` — return value never consumed, vestigial

`ccya/engine/config.py:61-62,78`

Exported via `__init__.py` but the cancel endpoint now reads `state_snapshot` from events instead. `signal_turn_done` calls it at line 78 and discards the return. No external consumer reads its value.

### `narrate_summary` and `extraction_context` event fields — written, never consumed

`ccya/engine/turn.py:1253-1265`

Written into every turn event dict. No server code reads them (tv.py, routes.py, metrics.py, panels.py all checked).

---

## Duplicated Code

### `_strip_non_ascii` — 5 identical definitions

| File | Line |
|---|---|
| `ccya/engine/seed.py` | 25 |
| `ccya/engine/generate_pack.py` | 21 |
| `ccya/engine/npc_roster.py` | 71 |
| `ccya/state/npcs.py` | 46 |
| `ccya/state/delta_builder.py` | 27 |

Each compiles the same regex `re.compile(r"[^\x00-\x7F]")` and calls `.sub("", text).strip()`. Should be a shared utility.

### `_log` logger — duplicated in seed.py

`ccya/engine/seed.py:16,131`

`_log = logging.getLogger(__name__)` reassigned at line 131, shadowing the original from line 16.

### 3 near-identical stream blocks in `_run_extraction_pipeline`

`ccya/engine/extraction.py:415-460 (scene), 463-508 (state), 511-591 (storytell)`

Same structure: build messages → trim → call LLM → capture usage → build event dict → log. Only variable names and a few args differ. The 3 exception-handler pairs (448-455, 496-503, 579-586) are also copy-paste identical.

---

## Overly Long Functions

| Function | Location | Lines | Concern |
|---|---|---|---|
| `run_turn()` | `turn.py:818-1363` | ~545 | Orchestration, state mutation, 5 LLM calls, error handling, persist |
| `_run_extraction_pipeline()` | `extraction.py:380-655` | ~275 | 3 near-identical boilerplate stream blocks |
| `summarize_changes()` | `changes.py:80-318` | ~238 | 6 distinct sections in one function |
| `_ruling_phase()` | `turn.py:569-727` | ~158 | Avoidance, dice, momentum, de-escalate combined |

---

## Dead Parameters

| Parameter | Function | File:Line | Issue |
|---|---|---|---|
| `turn` (default `0`) | `_call_ruling()` | `ruling.py:52` | Never passed at sole call site (`turn.py:609`); all ruling logs log `turn=0` |
| `n` (default `5`) | `_avg_event_ms()` | `extraction.py:658` | Never overridden at any of 3 call sites |
| `state_result` | `_storytell_messages()` | `extraction.py:231` | Never referenced in function body |
| `_applied` | `summarize_changes()` | `changes.py:83` | Never referenced in function body |

---

## Memory & Resource Leaks

### `_turn_done` / `_persist_started` entries leak on await timeout

`ccya/engine/config.py:73-89`

If `await_turn_done` times out (30s in routes.py), the generator's `finally` block never runs, so `signal_turn_done` never fires. Entries in `_turn_done` and `_persist_started` accumulate per save_dir indefinitely.

### `_EventLock._locks` entries accumulate

`ccya/engine/config.py:19-31`

Entries are never removed. Benign for single save_dir, grows monotonically for multi-save scenarios.

---

## Configuration & Consistency Issues

### Narrate `_log_llm_io` phase strings lack `_attempt_0` suffix

`ccya/engine/config.py:309` / `ccya/engine/turn.py:912,945`

Every other phase uses `f"{phase}_request_attempt_{attempt}"` / `f"{phase}_response_attempt_{attempt}"`. Narrate uses bare `"narrate_request"` / `"narrate_response"` — no attempt number. Makes narrative LLM retry tracking impossible in log analysis.

### `_PROMPTS_LOG_PATH` uses relative CWD path

`ccya/engine/config.py:241`

`Path("logs/prompts.log")` resolves relative to process CWD. If the server starts outside the project root, writes go to the wrong location. Both `config.py:351` and `ruling.py:162` write to it.

### Hardcoded timeout in `generate_pack_from_brief`

`ccya/engine/generate_pack.py:106`

```python
timeout=300.0
```

Hardcoded instead of reading from `config.request_timeout_s`. Inconsistent with regular LLM calls that use the config value.

### Hardcoded surname pool in `seed.py`

`ccya/engine/seed.py:50`

```python
surnames_pool = ["Smith", "Jones", "Black", "Stone", "Fox", "Wolf", "Hawk", "Knight"]
```

Western-centric, ignores pack locale configuration.

---

## Naming & Style Issues

| Symbol | File:Line | Problem |
|---|---|---|
| `_ensure_ascii()` | `names.py:44` | Name says "ensure ascii" but doesn't strip non-ASCII; docstring says "keep as-is, unicode is valid" |
| `_pending_gm_beat` / `pending_gm_beat` | `turn.py:96,100` | Two fields for same concept; only private one is used |
| `_coerce_scene_json()` | `extraction.py:277` | Applies to all 3 stream results, not just scene |
| `_sanitize_brief()` | `generate_pack.py:28` | Name suggests broad sanitization; only strips ASCII on 2 fields |

---

## `generate_pack.py` Error Handling Gaps

`ccya/engine/generate_pack.py:169-187`

- No `exc_info=True` on any except log call — traceback lost on retry failures
- `except Exception` retries everything including permanent failures (YAML parse errors, Pydantic validation failures) — wastes 300s LLM call per attempt
- `exc` never referenced except via `str(exc)` — can't distinguish error types without string parsing
- Empty `parse_error` possible if `str(exc)` yields `""`

---

## `_find_json` Edge Cases

`ccya/engine/config.py:244-298`

Logic is mostly robust, but the depth-counting brace match (path 3) can produce false positives if non-JSON text has balanced braces before the JSON block. The first-to-last fallback (path 4) has lowest reliability. Handles ````json fences correctly. Callers (`ruling.py:94`, `seed.py:274`, `extraction.py:310`) all apply `strip_thinking()` first — correct.

---

## `_render` Error Handling

`ccya/engine/config.py:232-233`

No error handling. All 15 call sites across 6 files risk uncaught `TemplateNotFound` / `UndefinedError`.

---

## Unused Dependencies

### `python-multipart`

Listed in `pyproject.toml` but never imported anywhere. No endpoint uses `Form`, `File`, or `UploadFile`. Safe to remove.
