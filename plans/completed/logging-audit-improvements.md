# Logging Audit & Major Improvements

## Status
`open`

## Phases

6 phases: infrastructure → engine pipeline → state modules → server UI → eval modules → cross-cutting

## Issue

Logging across the codebase is uneven and insufficient for debugging regressions, which are the most common bug type. 15 modules have zero logging whatsoever, 6 modules declare a logger but never use it, and 8+ sites use `except: pass` to silently swallow failures. The state layer — where most mutation bugs live — is entirely silent. Server UI modules swallow every JSON parse error, letting stale/empty data masquerade as correct output. The eval CLI sets up its own ad-hoc handler instead of using shared infrastructure. There is no documented convention for what level to use where.

## Solution

Add comprehensive logging to all under-logged modules, activate all dead loggers, replace every silent failure path with at minimum a warning log, and document explicit log-level conventions. Per-module loggers (`logging.getLogger(__name__)`) are the right pattern — they enable hierarchical filtering under the `ccya` root and cost nothing. Phases are ordered by regression-debugging impact: engine pipeline first, then state, server, eval.

## Firm decisions

1. **Keep per-module loggers** — `_log = logging.getLogger(__name__)` is the standard. They enable filtering (`ccya.engine.turn`, `ccya.state.delta`) at no cost. All new modules must follow this pattern.
2. **Log level conventions**:
   - `DEBUG` — detailed trace: per-step timing, LLM call start/end, token counts, conditional branches, truncation details
   - `INFO` — phase boundaries: pipeline start/end per turn, compaction trigger, state save/load, server startup
   - `WARNING` — recoverable anomalies: malformed data that can be skipped, non-critical parse failures, deprecated paths, LLM retries
   - `ERROR` — definitive failures: LLM call hard failure, state load failure, migration failure, critical parse failures
   - `EXCEPTION` — exception with traceback: use `_log.exception()` in all `except` blocks where we cannot recover
3. **No bare `except: pass`** — every exception handler must log at minimum a warning with the exception string. Use `_log.exception()` when the exception info should propagate to JSONL.
4. **Structured context fields** — pipeline code must include `extra={"trace_id": ..., "turn": ...}` on every log call. State code must include `extra={"save_dir": ...}`. Server code must include `extra={"save": ..., "turn": ...}` where available.
5. **All dead loggers get activated** — add real logging calls. If a module truly has nothing to log, remove the dead logger line.
6. **`setup_logging()` must be called from every entry point** — currently only `server/app.py` does this. Fix `__main__.py`, `cli.py`, `eval/cli.py`.

## Non-goals

- Not restructuring the logging infrastructure (JSONL file handler + console handler stays)
- Not adding metrics/monitoring infrastructure
- Not changing the eval CLI `print()` output protocol (that's intentional output, not logging)
- Not adding logging to test files or `llm_mock.py`
- "Pedantic" doesn't exist in the codebase yet — not planned
- Not refactoring or restructuring any business logic

## Risks, Ambiguities, and Blockers

- `eval/cli.py` uses `print()` to stderr for protocol output. Adding `_log.debug()` calls may create confusion between protocol output and diagnostic logging. Must keep them separate.
- Server UI modules (`tv.py`, `panels.py`, `metrics.py`) swallow JSON parse errors because events.jsonl lines can be corrupted by concurrent writes. Logging these as warnings may produce noise during normal operation. Need to verify whether corruption is truly expected or a bug itself.
- `engine/turn.py:warmup()` has `except Exception: pass` at line 1719 — this may be intentional (non-critical warmup). Must preserve non-blocking behavior while adding logging.

## Implementation — Phase 1: Logging Conventions & Infrastructure

### Context files to load
- `ccya/logging_setup.py`
- `ccya/__main__.py`
- `ccya/cli.py`
- `ccya/eval/cli.py`
- `AGENTS.md`

### Detailed steps

#### Step 1.1 — Document log level conventions in AGENTS.md

**File:** `AGENTS.md`

**What:** Add a new "Logging standards" subsection to the Clean Code Rules section. Document the level conventions from Firm Decision #2: DEBUG=trace, INFO=phase, WARNING=recoverable, ERROR=failure, EXCEPTION=traceback. Specify required `extra` context fields per module category (pipeline: trace_id+turn, state: save_dir, server: save+turn).

**Why:** Makes conventions discoverable without reading docs/architecture docs.

**Validation:** `grep "Logging standards" AGENTS.md` returns content.

#### Step 1.2 — Ensure `setup_logging()` is called from all entry points

**File:** `ccya/__main__.py`

**What:** Add `from ccya.logging_setup import setup_logging` and call `setup_logging()` at module level before the `if __name__ == "__main__":` guard. Wrap in a try/except (logging setup should not crash the app).

**File:** `ccya/cli.py`

**What:** Same — import and call `setup_logging()` at the top of the module, before any CLI dispatch.

**Why:** Currently only `server/app.py` calls `setup_logging()`. The CLI and eval entry points run without proper logging infrastructure.

**Validation:** Run `python -m ccya --help` (or equivalent) and verify `logs/` directory is created with `llm-g.log`.

#### Step 1.3 — Consolidate eval CLI logging onto shared infrastructure

**File:** `ccya/eval/cli.py`

**What:** Remove the ad-hoc StreamHandler setup (the block that creates and adds a StreamHandler to `_log`). Replace with a call to `setup_logging()` at module level. Keep the existing `_log.debug()` calls. Keep `print()` to stderr for protocol output (non-goal).

**Why:** Eliminates duplicate handler setup. Eval CLI should use the same JSONL+console infrastructure as the server.

**Validation:** `rg "StreamHandler" ccya/eval/cli.py` returns nothing.

### Tests to write or update

Tests are temporarily removed during refactor (per AGENTS.md). Skip.

### REPOMAP updates required

None. No public API changes.

---

## Implementation — Phase 2: Engine Pipeline Deep Logging

### Context files to load
- `ccya/engine/narrate.py`
- `ccya/engine/changes.py`
- `ccya/engine/markers.py`
- `ccya/engine/names.py`
- `ccya/engine/npc_roster.py`
- `ccya/engine/generate_pack.py`
- `ccya/engine/ruling.py`
- `ccya/engine/seed.py`
- `ccya/engine/turn.py`
- `ccya/engine/config.py`
- `ccya/engine/extraction.py`
- `ccya/engine/compactor.py`

### Detailed steps

#### Step 2.1 — Activate dead loggers in engine modules

**File:** `ccya/engine/narrate.py`

**What:** This module has `_log = logging.getLogger(__name__)` (line 13) but zero `_log.*` calls. Add logging:
- `_log.debug` at function entry for `_narrate_messages()` showing number of messages and presence of NPC roster
- `_log.info` at completion showing final message count
- `_log.warning` if `_narrate_messages()` receives empty messages list
- `_log.exception` in any uncovered `except` blocks (inspect for error handling)

**Why:** Narrate is a core pipeline phase; entry/exit logging with message count enables regression detection when narrative structure changes.

#### Step 2.2 — Activate dead logger in changes.py

**File:** `ccya/engine/changes.py`

**What:** Add logging:
- `_log.debug` in `summarize_changes()` and `format_change_lines()` showing pre/post field diffs
- `_log.debug` showing number of change lines generated

**Why:** Changes module is the diff layer between turn states; regressions here manifest as incorrect UI display.

#### Step 2.3 — Activate dead logger in markers.py

**File:** `ccya/engine/markers.py`

**What:** Add logging:
- `_log.debug` at entry showing action list and character name
- `_log.info` showing which marker verdicts were assigned (if any)
- `_log.warning` if no markers matched at all

**Why:** Marker matching determines which NPCs appear; regressions cause missing/extra characters.

#### Step 2.4 — Activate dead logger in names.py

**File:** `ccya/engine/names.py`

**What:** Add logging:
- `_log.debug` on name pool generation showing count per category (pc/npc/location)
- `_log.warning` if generation returns fewer names than requested

**Why:** Name pool depletion causes silent fallback behavior.

#### Step 2.5 — Activate dead logger in npc_roster.py

**File:** `ccya/engine/npc_roster.py`

**What:** Add logging:
- `_log.debug` at entry showing scene_npcs list length and present/known NPC counts
- `_log.info` showing merged roster size
- `_log.warning` if roster exceeds expected NPC caps

**Why:** NPC roster merges across sources; regressions cause character duplication or disappearance.

#### Step 2.6 — Upgrade generate_pack.py logging (minor gaps)

**File:** `ccya/engine/generate_pack.py`

**What:** Module already has `_log` (line 16) with 6 calls (info/warning/debug with trace_id and pack context). It's already well-logged. Add:
- `_log.debug` at start showing input size (concept length, tone tag count)
- `_log.info` on completion showing output field counts (factions, locations)

**Why:** Pack generation is a complex LLM flow; already well-covered but input size visibility helps debugging.

#### Step 2.7 — Upgrade ruling.py logging

**File:** `ccya/engine/ruling.py`

**What:** Currently has `_log` (line 13) with 3 warning calls. Already uses `extra={"trace_id": ...}` (lines 106, 117, 158). Add:
- `_log.info` at entry showing number of rules questions
- `_log.debug` per ruled outcome
- Add `"turn"` to existing `extra` dicts on retries and final failure
- `_log.error` if ruling LLM call fails after all retries (currently only warning)

**Why:** Ruling retries are critical regression indicators; turn context missing from existing trace_id calls.

#### Step 2.8 — Upgrade seed.py logging

**File:** `ccya/engine/seed.py`

**What:** Currently has adequate error/warning logging (7 calls). Add:
- `_log.debug` at start showing pack slug, timeout config, and any overrides
- `_log.info` on successful seed generation showing resulting character count
- `_log.debug` per LLM call chunk/stream event

**Why:** Seed generation failures are hard to reproduce; entry/exit logging enables debugging.

#### Step 2.9 — Fix silent passes and add logging in turn.py

**File:** `ccya/engine/turn.py`

**What:** Three silent failure sites:
- Lines 975-976 (`except Exception: pass` during ArcThread parsing): change to `_log.warning("Malformed ArcThread entry: %s", entry, extra={...})`
- Lines 1626-1627 (`except Exception: arc_dict = None` during arc_update JSON parse): change to `_log.warning("Failed to parse arc_update: %s", err, extra={...})`
- Lines 1719-1720 (`except Exception: pass` during warmup): change to `_log.warning("Warmup LLM call failed: %s", err, extra={...})` — preserve non-blocking behavior

Note: line 1413 has `except Exception:` that is already logged (`_log.warning` with trace_id) — do not touch it.

Also audit for any other `except: pass` or bare `except:` in the file.

**Why:** These silent swallows mask warmup failures, narrative arc corruption, and thread parsing bugs — exactly the kind of regression that's hard to find.

#### Step 2.10 — Add config.py logging for dynamic config loading paths

**File:** `ccya/engine/config.py`

**What:** Currently has 2 log calls for llm_io and prompts.log. Add:
- `_log.debug` showing config overrides applied per turn
- `_log.warning` if config fields are missing or defaulting

**Why:** Config changes between runs are a common source of behavioral regressions.

#### Step 2.11 — Upgrade extraction.py logging (minor gaps)

**File:** `ccya/engine/extraction.py`

**What:** Already well-logged (18 calls). Add:
- `_log.debug` per extraction stream (scene/state/storytell) showing input token count
- `_log.warning` if stream returns empty content after retries

**Why:** Extraction is already well-covered but stream-level token visibility helps regression debugging.

#### Step 2.12 — Upgrade compactor.py logging

**File:** `ccya/engine/compactor.py`

**What:** Already good (13 calls). Add:
- `_log.debug` showing pre/post state size deltas after compaction
- `_log.info` showing compaction skipped reason (not due yet, etc.)

**Why:** Compaction changes are high-risk for state regressions; pre/post size data helps.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

### REPOMAP updates required

None.

---

## Implementation — Phase 3: State Module Logging

### Context files to load
- `ccya/state/delta.py`
- `ccya/state/chronicle.py`
- `ccya/state/inventory.py`
- `ccya/state/momentum.py`
- `ccya/state/npcs.py`
- `ccya/state/io.py`
- `ccya/state/delta_builder.py`

### Detailed steps

#### Step 3.1 — Add logging to delta.py

**File:** `ccya/state/delta.py`

**What:** Module has zero logging. Add `_log = logging.getLogger(__name__)` at module level. Add logging:
- `_log.debug` in `apply_delta()` showing count of keys changed and whether eviction occurred
- `_log.info` at completion showing new field count
- `_log.warning` if delta contains unexpected fields not in state schema
- `_log.debug` in `reconcile_delta()` showing duplicates removed and resolution applied

**Why:** State deltas are the core mutation mechanism; zero logging means every state bug requires manual diff tracing.

#### Step 3.2 — Add logging to chronicle.py

**File:** `ccya/state/chronicle.py`

**What:** Module has zero logging. Add `_log = logging.getLogger(__name__)`. Add logging:
- `_log.info` on `append_event()` showing event count and file size
- `_log.debug` on `append_chronicle()` showing narrative length
- `_log.debug` on `load_chronicle_tail()` showing lines loaded
- `_log.warning` on file write failures

**Why:** Chronicle append failures mean lost turn history; silent truncation means lost debugging data.

#### Step 3.3 — Add logging to inventory.py

**File:** `ccya/state/inventory.py`

**What:** Module has zero logging. Add `_log = logging.getLogger(__name__)`. Add logging:
- `_log.debug` in `normalize_inventory_id()` showing input and resolved result
- `_log.debug` in fuzzy match helpers showing match score and threshold
- `_log.warning` if fuzzy match falls below a quality threshold

**Why:** Inventory resolution ambiguities cause item duplication/loss — a common regression.

#### Step 3.4 — Add logging to momentum.py

**File:** `ccya/state/momentum.py`

**What:** Module has zero logging. Add `_log = logging.getLogger(__name__)`. Add logging:
- `_log.debug` showing input stats and calculated momentum band
- `_log.info` showing final momentum value (clamped)

**Why:** Momentum affects all check outcomes; silent clamping can confuse debugging.

#### Step 3.5 — Add logging to npcs.py

**File:** `ccya/state/npcs.py`

**What:** Module has zero logging. Add `_log = logging.getLogger(__name__)`. Add logging:
- `_log.debug` in `build_npc_alias_map()` showing alias count and collisions
- `_log.debug` in `touch_compendium_order()` showing ordering changes
- `_log.warning` on alias collision

**Why:** NPC alias resolution failures cause duplicate NPC entries.

#### Step 3.6 — Upgrade io.py logging

**File:** `ccya/state/io.py`

**What:** Currently has 1 warning for schema version mismatch. Add:
- `_log.info` on successful load showing save slug and turn count
- `_log.debug` on save showing file size
- `_log.error` on load failure with exception details
- `_log.warning` in `_migrate_state()` showing what migration was applied

**Why:** State load/save failures are catastrophic; zero detail on current logging makes debugging impossible.

#### Step 3.7 — Upgrade delta_builder.py logging

**File:** `ccya/state/delta_builder.py`

**What:** Currently adequate (7 calls). Add:
- `_log.debug` showing input delta dict size and key count
- `_log.warning` on unexpected field values or types

**Why:** Minor gap — delta builder transforms LLM extraction output; type mismatches here cause downstream crashes.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

### REPOMAP updates required

None.

---

## Implementation — Phase 4: Server UI Module Logging

### Context files to load
- `ccya/server/panels.py`
- `ccya/server/tv.py`
- `ccya/server/metrics.py`
- `ccya/server/routes.py`
- `ccya/server/app.py`

### Detailed steps

#### Step 4.1 — Add logging and fix silent swallows in panels.py

**File:** `ccya/server/panels.py`

**What:** Module has no logger. Add `_log = logging.getLogger(__name__)`. Fix:
- Line 39-40 `except json.JSONDecodeError: continue`: add `_log.warning("Skipping malformed events.jsonl line %d: %s", i, err)`
- Line 76-77 `except (json.JSONDecodeError, KeyError): return []`: add `_log.warning("Failed to parse last action from events.jsonl: %s", err)`
- Add `_log.debug` in all `_load_*` helpers showing file size and entry count
- Add `_log.info` in `_debug_context()` showing what debug data was loaded

**Why:** JSON decode failures are silently returning empty data to the UI with no indication to the operator.

#### Step 4.2 — Add logging and fix silent swallows in tv.py

**File:** `ccya/server/tv.py`

**What:** Module has no logger. Add `_log = logging.getLogger(__name__)`. Fix ALL silent JSON parse sites:
- Line 63: `except _json.JSONDecodeError: return None` → log warning with line snippet
- Line 69: `except _json.JSONDecodeError: return None` → log warning
- Line 82-83: `except Exception: return [...]` → log error with full exception
- Line 351-352: `except _json.JSONDecodeError: continue` → log warning
- Line 367-368: `except _json.JSONDecodeError: continue` → log warning
- Line 394: `except (TypeError, ValueError): return "\u2014"` → add `_log.debug` (benign formatting failure)
- Line 482: `except Exception: out_str = raw_out` → log warning with exception

**Why:** Turn viewer shows stale/empty data silently. Every failed parse is a lost debugging opportunity.

#### Step 4.3 — Add logging to metrics.py

**File:** `ccya/server/metrics.py`

**What:** Module has no logger. Add `_log = logging.getLogger(__name__)`. Fix:
- Lines 17-18, 26-27, 39-40: `except (TypeError, ValueError): return "—"` → add `_log.debug` (benign formatting failures, not worth warning)
- Line 59-60: `except json.JSONDecodeError: continue` → add `_log.warning` (data corruption)
- Line 171-172: `except json.JSONDecodeError: continue` → add `_log.warning` (data corruption)

**Why:** Metrics formatting failures are generally benign but data line parse failures are not.

#### Step 4.4 — Upgrade routes.py logging

**File:** `ccya/server/routes.py`

**What:** Currently has 5 log calls. Add:
- `_log.info` at start of each major route handler showing request params (sanitized)
- `_log.exception` in all uncovered `except` blocks
- `_log.warning` with `extra={"error_kind": ...}` on user input validation failures
- `_log.error` on route handler failures that return error responses

**Why:** Route handlers are the first point of contact; unlogged failures here mean the operator can't distinguish client errors from server errors.

#### Step 4.5 — Upgrade app.py logging

**File:** `ccya/server/app.py`

**What:** Currently adequate (5 calls). Add:
- `_log.info` during startup showing middleware registration and save count
- `_log.warning` if pack loading partially fails

**Why:** Minor gap — startup failures of individual packs are currently silent.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

### REPOMAP updates required

None.

---

## Implementation — Phase 5: Eval Module Logging

### Context files to load
- `ccya/eval/scenario.py`
- `ccya/eval/config.py`
- `ccya/eval/engine_mirror.py`
- `ccya/eval/pack_utils.py`
- `ccya/eval/redundancy.py`
- `ccya/eval/compaction_signals.py`
- `ccya/eval/universal_asserts.py`
- `ccya/eval/report.py`
- `ccya/eval/judge.py`
- `ccya/eval/runner.py`

### Detailed steps

#### Step 5.1 — Add logging to eval/scenario.py

**File:** `ccya/eval/scenario.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` in Scenario init showing seed_overrides and assertion count
- `_log.info` showing scenario slug on load

#### Step 5.2 — Add logging to eval/config.py

**File:** `ccya/eval/config.py`

**What:** No logger. Has `LoggingConfig` dataclass but no runtime logging. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` showing loaded config fields
- `_log.info` showing number of judges configured

#### Step 5.3 — Add logging to eval/engine_mirror.py

**File:** `ccya/eval/engine_mirror.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` on constants access showing version check

#### Step 5.4 — Add logging to eval/pack_utils.py

**File:** `ccya/eval/pack_utils.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` showing pack loading and scenario matching

#### Step 5.5 — Add logging to eval/redundancy.py

**File:** `ccya/eval/redundancy.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` showing redundancy check results per turn
- `_log.info` showing overall redundancy score

#### Step 5.6 — Add logging to eval/compaction_signals.py

**File:** `ccya/eval/compaction_signals.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` showing compaction signal values per event

#### Step 5.7 — Add logging to eval/universal_asserts.py

**File:** `ccya/eval/universal_asserts.py`

**What:** No logger. Add `_log = logging.getLogger(__name__)`. Add:
- `_log.debug` showing each auto-checker result (pass/fail)
- `_log.info` showing total passes and failures

#### Step 5.8 — Activate dead logger in eval/report.py

**File:** `ccya/eval/report.py`

**What:** Has `_log` (line 22) with zero calls. Add:
- `_log.info` at report write start/end showing file path and size
- `_log.warning` if judge results are missing or empty

#### Step 5.9 — Fix silent swallows in eval/judge.py

**File:** `ccya/eval/judge.py`

**What:** Fix at line 851-852 (`except (ValueError, TypeError): pass`):
- Change to `_log.warning("Failed to convert score field '%s': %s", field_name, err)`

Already well-logged otherwise (6 info/warning calls).

#### Step 5.10 — Fix silent swallows in eval/runner.py

**File:** `ccya/eval/runner.py`

**What:** Fix at line 510-511 (`except Exception: pass` during turn readback):
- Change to `_log.warning("Turn readback failed for turn %d: %s", turn_num, err)`

#### Step 5.11 — Upgrade eval/cli.py logging

**File:** `ccya/eval/cli.py`

**What:** Already uses `_log.debug` (3 calls). Add:
- `_log.info` at start/end of eval run showing config path and scenario count
- `_log.debug` per completed scenario showing pass/fail counts

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

### REPOMAP updates required

None.

---

## Implementation — Phase 6: Cross-Cutting Fixes

### Context files to load
- `ccya/pack.py`
- `ccya/llm_client.py`
- `ccya/models.py`
- `ccya/prompts/context.py`

### Detailed steps

#### Step 6.1 — Fix pack.py silent except:pass

**File:** `ccya/pack.py`

**What:** Line 362-363 `except Exception: pass` during pack manifest loading. Add `_log = logging.getLogger(__name__)`. Change to:
- `_log.warning("Skipping invalid pack manifest at %s: %s", manifest_path, err)`

**Why:** Invalid pack manifests are silently skipped, making packs disappear from the UI with no indication.

#### Step 6.2 — Add logging to llm_client.py

**File:** `ccya/llm_client.py`

**What:** Currently adequate (3 calls). Fix:
- Line 88: silent skip when `head_keep + tail_keep >= len(content)` → add `_log.debug("Truncation skipped: content fits within budget (%d <= %d)", total, budget)`
- Lines 186-196: error reclassification without logging original → add `_log.debug("LLM error reclassified: %s -> %s", type(e).__name__, target_type)` in each branch
- Line 200-206: bare `except Exception` → narrow to specific exception types, or add `_log.exception` if truly necessary

**Why:** LLM client is the integration boundary; silent skips and error reclassification without logging make it hard to distinguish network errors from rate limits from API errors.

#### Step 6.3 — Remove dead logger from prompts/context.py

**File:** `ccya/prompts/context.py`

**What:** Module has `_log = logging.getLogger(__name__)` (line 26) with zero `_log.` calls. It's a pure data-model module (Pydantic BaseModel classes and factory methods) with no runtime error paths, no conditionals, and nothing meaningful to log. Remove the dead logger line. Re-add if future business logic is added.

**Why:** Per Firm Decision #5 — modules with nothing to log should not carry dead logger declarations.

#### Step 6.4 — Activate models.py dead logger

**File:** `ccya/models.py`

**What:** `_log` declared (line 13) with 1 call (`_log.debug`) for empty actions. Either add more logging (e.g., on model load, validation failures) or remove the dead logger if the module truly has nothing to log. Given it has one call, keep and activate with:
- `_log.debug` showing model configuration on load
- `_log.warning` on validation warnings

**Why:** Model validation warnings are currently silent.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

### REPOMAP updates required

None.
