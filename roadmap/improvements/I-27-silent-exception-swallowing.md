---
title: "Eliminate silent exception swallowing across the engine"
status: new
urgency: 1
size: large
created: 2026-07-04
ticket_id: I-27
labels:
  - engine
  - logging
  - observability
---

## What

Systematically eliminate silent `except`/`pass` patterns and bare `except Exception` blocks that violate the logging standard defined in AGENTS.md. The codebase has **69 `except Exception` blocks** and **143 bare `except` blocks** (including `except (json.JSONDecodeError, ValueError):` with no logging).

AGENTS.md explicitly mandates: "No bare `except: pass` — every exception handler must log at minimum a warning with the exception string." This is not being followed.

## Why

Silent failures make debugging nearly impossible. When a turn "works" but silently skips sanitization, or a save list silently omits broken saves, it creates invisible data corruption that users and developers cannot trace.

### Validated problem areas

#### 1. Thread sanitizer — the system's self-correcting mechanism (Critical)

`engine/thread_sanitizer.py:207` — `except (json.JSONDecodeError, ValueError): pass` — silent JSON parse failure means entire sanitization is skipped.

`engine/thread_sanitizer.py:265,285,314` — three `except Exception` blocks that log a warning then continue, silently losing invalid thread/world_state entries without context or tracking.

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

`server/routes.py:345,414,996` — `except Exception` blocks that swallow errors in route handlers.

#### 8. LLM client — mostly acceptable but some context loss (Low-Medium)

`llm_client.py` — 16 `except Exception` blocks in retry/fallback logic. Most are acceptable (they log and re-raise or continue retrying), but some lose the original exception context.

#### 9. Engine core — silent failures in ruling, pacing, world (Medium)

`engine/ruling.py:126,251` — `except Exception` blocks.
`engine/_pacing.py:316` — `except Exception:` — silent pacing failure.
`engine/world.py:113` — `except Exception` — silent world step failure.

#### 10. Seed generation — silent LLM fallback (Medium)

`engine/seed.py:185,302,592` — `except Exception` blocks that silently fall back to defaults during dynamic seed generation.

#### 11. State chronicle — silent JSON parse (Low)

`state/chronicle.py:23,39,54` — `except Exception` blocks that silently skip chronicle entries.

#### 12. Config loading — silent fallback (Low)

`config.py:62` — `except Exception` — silent config loading fallback.

#### 13. Pack loading — silent YAML parse (Low)

`pack.py:297` — `except Exception:` — silent YAML parse in pack loading (re-raises after logging, but the initial log is insufficient for diagnosis).

#### 14. Turn state — silent extraction (Medium)

`engine/turn_state.py:38,583,613` — `except Exception` blocks in turn state processing.

#### 15. Server TV (turn viewer) — silent JSON parse (Low)

`server/tv.py:92,833` — `except Exception` blocks in turn viewer.

#### 16. Server app — silent startup (Low)

`server/app.py:116,196` — `except Exception` blocks during server startup.

#### 17. Eval infrastructure — silent failures (Low)

`ev/eval.py:210,224,365,371` — `except Exception` blocks in eval runner.
`ev/checkers/_llm.py:77,81` — `except Exception` blocks in LLM checker.
`ev/play.py:99,559,650,655` — `except Exception` blocks in eval play mode.

#### 18. Late import to avoid circular dependency (Low)

`server/app.py:205` — `import ccya.server.routes` is a late import (after class definitions) with a comment: "late import required by FastAPI route registration (circular if done earlier)." Moved from I-24 finding #18.

**Better:** Restructure so routes are defined in a way that doesn't create circular imports (e.g., move route registration to a separate bootstrap step).

#### 18. Prompt eval — silent JSON parse (Low)

`ev/prompt_eval.py:189,267` — `except Exception` blocks.

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

3. **Categorize by severity:**
   - **Critical (fix first):** Thread sanitizer silent failures — these are the single biggest risk to game state correctness
   - **High:** Save list silent exclusion, new game silent fallbacks
   - **Medium:** NPC tie resolution, extraction pipeline, warmup cache, ruling/pacing/world silent failures
   - **Low:** Config loading, pack loading, chronicle, eval infrastructure (these are less critical but still violate the standard)

4. **Add a lint rule** — consider adding a ruff rule (e.g., `BLE001` for bare `except`, or a custom rule) to prevent silent exception swallowing in the future.

5. **Add structured logging for silent failures** — for cases where silent degradation is intentional (e.g., optional features), use a structured log field like `"silent_degradation": true` to make these explicit and filterable.

### Specific fixes per file

- `engine/thread_sanitizer.py` — Add logging with `exc_info=True` for all silent failures. Consider tracking failure count and alerting after N consecutive failures.
- `server/routes.py` — Add logging for save list exclusion, arc_origin read failure, JSON parse fallback, health check failure, NPC tie resolution failure.
- `engine/extraction/record.py` — Add logging for invalid thread objects.
- `engine/turn.py` — Add logging for warmup cache loss.
- `engine/ruling.py` — Add logging for silent ruling failures.
- `engine/_pacing.py` — Add logging for silent pacing failures.
- `engine/world.py` — Add logging for silent world step failures.
- `engine/seed.py` — Add logging for silent LLM fallback during seed generation.
- `state/chronicle.py` — Add logging for silent chronicle entry skips.
- `config.py` — Add logging for silent config loading fallback.
- `pack.py` — Improve logging for silent YAML parse (currently re-raises but initial log is insufficient).
- `engine/turn_state.py` — Add logging for silent turn state processing failures.
- `llm_client.py` — Review for context loss in exception handling (most are acceptable but some lose original exception context).
- `ev/` — Add logging for silent eval infrastructure failures (lower priority, but still violates standard).
