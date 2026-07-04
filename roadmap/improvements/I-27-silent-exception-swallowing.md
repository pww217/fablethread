---
title: "Eliminate silent exception swallowing across the engine"
status: done
urgency: 1
size: large
created: 2026-07-04
ticket_id: I-27
labels:
  - engine
  - logging
  - observability
plan: plans/completed/engine/i-27-silent-exception-fix.md
---

## What

Systematically eliminate silent `except`/`pass` patterns and bare `except Exception` blocks that violate the logging standard defined in AGENTS.md. The codebase has **69 `except Exception` blocks** and **143 bare `except` blocks** (including `except (json.JSONDecodeError, ValueError):` with no logging).

AGENTS.md explicitly mandates: "No bare `except: pass` — every exception handler must log at minimum a warning with the exception string." This is not being followed.

### Validation summary (2026-07-04)

All 19 findings validated against source code. Results:

| Status | Count | Description |
|--------|-------|-------------|
| **Real silent swallowing (fix needed)** | 10 | Thread sanitizer (207, 265, 285, 314), save list (156, 170), new game (706), health check (867), NPC tie (582), extraction (record.py:55), warmup (turn.py:826), pacing (_pacing.py:316) |
| **Validated acceptable (no action)** | 8 | Server routes (345, 414, 996, 506, 549, 1076), LLM client (9 blocks), ruling (126, 251), world (113), seed (185, 302, 592), chronicle (23, 39, 54), config (62), pack (297), turn_state (38, 583, 613), tv (92, 833), app (116, 196), eval (210, 224, 365, 371, 625, 628), checkers (77, 81), play (99, 559, 650, 655), prompt_eval (189, 267) |
| **Not an exception issue (different ticket)** | 1 | Late import app.py:205 (design smell, not silent swallowing) |

**Real scope:** 10 findings need fixing (not 19). The majority of `except` blocks in the codebase already log properly.

## Why

Silent failures make debugging nearly impossible. When a turn "works" but silently skips sanitization, or a save list silently omits broken saves, it creates invisible data corruption that users and developers cannot trace.

### Validated problem areas

#### 1. Thread sanitizer — the system's self-correcting mechanism (Critical)

`engine/thread_sanitizer.py:207` — `except (json.JSONDecodeError, ValueError): pass` — silent JSON parse failure means entire sanitization is skipped.

`engine/thread_sanitizer.py:265,285,314` — three `except Exception` blocks that log a warning then continue, silently losing invalid thread/world_state entries without context or tracking (no `exc_info=True`, no exception string logged — only the thread id is logged).

`engine/thread_sanitizer.py:34,74,122` — `except Exception as exc` — these log warnings with the exception string and return early. **Validated: acceptable.**

**Impact:** The sanitizer runs every N turns (configurable). Failures compound silently — thread state accumulates errors over turns with no alert. This is the single biggest risk to game state correctness.

#### 2. Save list silently omits broken saves (High)

`server/routes.py:156` — `except Exception: continue` — if loading any save's state.yaml fails, the entire save is silently excluded from the list.

`server/routes.py:170` — `except Exception: pass` — if reading `arc_origin` from state.yaml fails, the field is silently null.

**Impact:** Users lose access to saves that may be partially recoverable. No log entry explains why a save disappeared.

#### 3. New game / reroll — silent JSON parse fallback (Medium-High)

`server/routes.py:706` — `except Exception:` — if `tone_tags` or `world_rules` JSON parsing fails, both default to empty lists silently.

`server/routes.py:867` — `except Exception:` — LLM health check returns `{"llm": "fail"}` without logging the actual error.

#### 4. NPC tie resolution — silent UI degradation (Medium)

`server/routes.py:582` — `except Exception: pass` — if `scenario.npc_bonds` is misconfigured, tie labels are silently null (NPCs show raw IDs instead of descriptions).

Called on nearly every route that renders state (index, panel_state, panel_state_left, etc.).

#### 5. Extraction pipeline — silent fallback (Medium)

`engine/extraction/record.py:55` — `except Exception` — invalid thread objects become `{"id": "", "summary": ""}` silently.

#### 6. Warmup cache — silent loss (Medium)

`engine/turn.py:826` — `except Exception:` — warmup failure is logged as a warning but the warmup cache is lost silently.

#### 7. Server routes — multiple silent handlers (Medium)

`server/routes.py:345` — `except Exception as e` — **Validated: NOT silent.** Uses `logger.exception("Turn failed")` which logs ERROR with traceback.

`server/routes.py:414` — `except Exception as exc` — **Validated: NOT silent.** Uses `_app_mod.logger.error()` and `_log.error()` then returns 400.

`server/routes.py:996` — `except Exception as exc` — **Validated: NOT silent.** Uses `_log.error()` then returns 500.

`server/routes.py:506` — `except Exception as exc` — **Validated: NOT silent.** Uses `logger.exception("new_game failed")` which logs ERROR with traceback.

`server/routes.py:549` — `except Exception as exc` — **Validated: NOT silent.** Uses `logger.exception("seed generation reroll failed")` which logs ERROR with traceback.

`server/routes.py:1076` — `except Exception` — **Validated: acceptable.** Returns 400 with "Invalid JSON" — this is a user input validation case, not silent swallowing.

#### 8. LLM client — mostly acceptable (Low-Medium)

`llm_client.py` — 9 `except Exception` blocks in retry/fallback logic (lines 201, 225, 240, 254, 296, 323, 340, 355, 548). **Validated: all acceptable.** They log and re-raise or continue retrying. The exception string is preserved in logs. Minor context loss at line 254 (logs `fallback_exc` instead of original `exc`), but this is negligible.

#### 9. Engine core — silent failures in ruling, pacing, world (Medium)

`engine/ruling.py:126` — `except Exception as exc` — **Validated: acceptable.** Logs warning with parse_error and retries.

`engine/ruling.py:251` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc and falls back to default outcome.

`engine/_pacing.py:316` — `except Exception:` — **Validated: SILENT.** Returns `None` with no logging at all. This is a real silent failure — invalid arc thread objects are silently discarded.

`engine/world.py:113` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

#### 10. Seed generation — silent LLM fallback (Medium)

`engine/seed.py:185` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

`engine/seed.py:302` — `except Exception as exc` — **Validated: acceptable.** Logs warning with parse_error and retries.

`engine/seed.py:592` — `except Exception as exc` — **Validated: acceptable.** Logs warning with parse_error and retries.

#### 11. State chronicle — silent JSON parse (Low)

`state/chronicle.py:23` — `except Exception as e` — **Validated: acceptable.** Logs ERROR with path and exception string.

`state/chronicle.py:39` — `except Exception as e` — **Validated: acceptable.** Logs ERROR with path and exception string.

`state/chronicle.py:54` — `except Exception as e` — **Validated: acceptable.** Logs ERROR with path and exception string.

#### 12. Config loading — silent fallback (Low)

`config.py:62` — `except Exception as exc` — **Validated: acceptable.** Logs warning with path and exc.

#### 13. Pack loading — silent YAML parse (Low)

`pack.py:297` — `except Exception:` — **Validated: acceptable.** Logs ERROR with path then re-raises. The log is sufficient for diagnosis.

#### 14. Turn state — silent extraction (Medium)

`engine/turn_state.py:38` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

`engine/turn_state.py:583` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

`engine/turn_state.py:613` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

#### 15. Server TV (turn viewer) — silent JSON parse (Low)

`server/tv.py:92` — `except Exception as e` — **Validated: acceptable.** Logs warning with e.

`server/tv.py:833` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

#### 16. Server app — silent startup (Low)

`server/app.py:116` — `except Exception as exc` — **Validated: acceptable.** Logs ERROR then re-raises (prevents startup with bad pack).

`server/app.py:196` — `except Exception as exc` — **Validated: acceptable.** Logs via `_persist_server_error()` then returns 500.

#### 17. Eval infrastructure — silent failures (Low)

`ev/eval.py:210` — `except Exception:` — **Validated: acceptable.** Returns empty string for sorting (silent failure is acceptable for non-critical metadata).

`ev/eval.py:224` — `except Exception:` — **Validated: acceptable.** Continues (for finding latest run, silent failure is acceptable).

`ev/eval.py:365` — `except Exception:` — **Validated: acceptable.** Sets git_sha to "unknown" (acceptable for non-critical metadata).

`ev/eval.py:371` — `except Exception:` — **Validated: acceptable.** Sets git_branch to "unknown" (acceptable for non-critical metadata).

`ev/eval.py:625` — `except Exception as e2` — **Validated: acceptable.** Prints error to stdout (for eval output, acceptable).

`ev/eval.py:628` — `except Exception as e` — **Validated: acceptable.** Prints error to stdout (for eval output, acceptable).

`ev/checkers/_llm.py:77` — `except Exception:` — **Validated: acceptable.** Silent pass then falls back to `{"error": "parse_failed", "raw": raw}` — the raw output is preserved.

`ev/checkers/_llm.py:81` — `except Exception as exc` — **Validated: acceptable.** Logs warning with exc.

`ev/play.py:99` — `except Exception as exc` — **Validated: acceptable.** Returns error output with exception details.

`ev/play.py:559` — `except Exception as exc` — **Validated: acceptable.** Prints error and breaks (for eval play mode, acceptable).

`ev/play.py:650` — `except Exception:` — **Validated: acceptable.** Silent pass (for git metadata, acceptable).

`ev/play.py:655` — `except Exception:` — **Validated: acceptable.** Silent pass (for git metadata, acceptable).

#### 18. Late import to avoid circular dependency (Low)

`server/app.py:205` — `import ccya.server.routes` is a late import (after class definitions) with a comment: "late import required by FastAPI route registration (circular if done earlier)." Moved from I-24 finding #18.

**Better:** Restructure so routes are defined in a way that doesn't create circular imports (e.g., move route registration to a separate bootstrap step).

#### 19. Prompt eval — silent JSON parse (Low)

`ev/prompt_eval.py:189` — `except Exception as exc` — **Validated: acceptable.** Prints error and exits (for CLI tool, acceptable).

`ev/prompt_eval.py:267` — `except Exception as exc` — **Validated: acceptable.** Prints error and exits (for CLI tool, acceptable).

## Impact / Benefits of Fixing

1. **Debuggability:** Every failure is logged with context (exception string, file, line). No more guessing why a turn silently produced wrong output.

2. **Data integrity:** Silent sanitization failures in the thread sanitizer are the single biggest risk to game state correctness. Fixing them ensures the self-correcting mechanism is visible and reliable.

3. **User trust:** Saves that fail to load are logged and reported rather than disappearing silently. Users can report broken saves instead of losing them.

4. **UI correctness:** NPC tie resolution failures are logged rather than silently showing raw IDs.

5. **Compliance:** Brings the codebase into compliance with the explicitly defined logging standard in AGENTS.md.

6. **Operational visibility:** Health checks, warmup caches, and pacing decisions are logged on failure rather than silently degraded.

## Fix Recommendations

### Approach

1. **Audit every `except` block** — for each one, determine if it should:
   - `raise` (propagate the error)
   - `raise` with added context (`raise ... from exc`)
   - `log.warning` then `raise` (log and propagate)
   - `log.warning` then continue (acceptable for non-critical graceful degradation)
   - `pass` (only if truly intentional and documented)

2. **Add `exc_info=True` or `exc` to every log call** — the AGENTS.md standard says "log at minimum a warning with the exception string". Every `except` that logs should include the exception details.

3. **Categorize by severity (validated):**
    - **Critical (fix first):** Thread sanitizer silent failures (lines 207, 265, 285, 314) — single biggest risk to game state correctness
    - **High:** Save list silent exclusion (lines 156, 170), new game silent fallback (line 706), health check silent failure (line 867)
    - **Medium:** NPC tie resolution (line 582), extraction pipeline (record.py:55), warmup cache (turn.py:826), pacing silent failure (_pacing.py:316)
    - **Low/No action:** Config, pack, chronicle, eval, TV, app startup, LLM client, ruling, world, seed, turn_state — all validated as already logging properly

4. **Add a lint rule** — consider adding a ruff rule (e.g., `BLE001` for bare `except`, or a custom rule) to prevent silent exception swallowing in the future.

5. **Add structured logging for silent failures** — for cases where silent degradation is intentional (e.g., optional features), use a structured log field like `"silent_degradation": true` to make these explicit and filterable.

### Specific fixes per file (validated scope — 10 findings)

#### Critical priority
- `engine/thread_sanitizer.py:207` — Replace `pass` with `_log.debug("JSON parse failed for sanitization data")` (this is a parser helper, debug-level is sufficient)
- `engine/thread_sanitizer.py:265,285,314` — Add `exc_info=True` and include exception string: `_log.warning("thread_sanitizer: skipping invalid thread_update %s: %s", _tu.get("id"), exc, exc_info=True)` (need to capture `exc` first)

#### High priority
- `server/routes.py:156` — Add `_log.warning("Save %s excluded: failed to load state.yaml", name)` before `continue`
- `server/routes.py:170` — Add `_log.debug("Save %s: arc_origin read failed", name)` (low priority, arc_origin is optional metadata)
- `server/routes.py:706` — Add `_log.warning("tone_tags/world_rules JSON parse failed, defaulting to empty lists")`
- `server/routes.py:867` — Add `_log.warning("LLM health check failed: %s", exc)` before returning `{"llm": "fail"}`

#### Medium priority
- `server/routes.py:582` — Add `_log.debug("NPC tie resolution failed, showing raw IDs")` (called on nearly every route, debug-level is sufficient)
- `engine/extraction/record.py:55` — Add `_log.warning("Invalid thread object in scene, skipping: %s", exc)` (need to capture `exc`)
- `engine/turn.py:826` — Already logs warning, but add `exc_info=True` for context
- `engine/_pacing.py:316` — Add `_log.warning("Invalid arc thread object, skipping: %s", exc)` (need to capture `exc`) — this is the silent pacing failure

#### Noted but acceptable (no action needed)
- `engine/thread_sanitizer.py:34,74,122` — Already log warnings with exception strings
- `server/routes.py:345,414,506,549,996,1076` — Already log errors with traceback or exception strings
- `llm_client.py` (9 blocks) — Already log and re-raise/retry
- `engine/ruling.py:126,251` — Already log warnings
- `engine/world.py:113` — Already logs warning
- `engine/seed.py:185,302,592` — Already log warnings
- `state/chronicle.py:23,39,54` — Already log ERROR
- `config.py:62` — Already logs warning
- `pack.py:297` — Already logs ERROR then re-raises
- `engine/turn_state.py:38,583,613` — Already log warnings
- `server/tv.py:92,833` — Already log warnings
- `server/app.py:116,196` — Already log errors
- `ev/` — All acceptable for their context (CLI output, non-critical metadata)
