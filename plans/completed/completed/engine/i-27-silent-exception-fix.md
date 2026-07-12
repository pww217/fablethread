# I-27: Eliminate silent exception swallowing — implementation plan

**Depends on:** None
**Ticket:** I-27
**Status:** completed

## Design Reference

N/A — this is a direct implementation of the validated findings in I-27.

## Phase summary

Three phases, ordered by priority (Critical → High → Medium). Each phase is grouped by shared file to minimize file churn. Phase 01 fixes thread sanitizer (the single biggest risk to game state correctness). Phase 02 fixes server routes (save list, new game, health check, NPC tie resolution). Phase 03 fixes remaining engine silent failures (extraction, pacing, warmup). All phases are independently executable with no dependencies on each other.

---

## Phase 01: Thread sanitizer logging (Critical)

**File:** `ccya/engine/thread_sanitizer.py`
**Findings:** Lines 207, 265, 285, 314

### Task 01-01: Add debug log to `_try_parse_json` (line 207)

**What:** Replace `except (json.JSONDecodeError, ValueError): pass` with `except (json.JSONDecodeError, ValueError): _log.debug("JSON parse failed for sanitization data")`

**Why:** `_try_parse_json` is a parser helper that returns `None` on failure. The caller (`_parse_response`) already handles `None` by logging a warning. A debug-level log here is sufficient — this is expected behavior for non-JSON text.

**Validation:** `rg -n "except (json.JSONDecodeError, ValueError):" ccya/engine/thread_sanitizer.py` returns no results. The line should read `except (json.JSONDecodeError, ValueError): _log.debug("JSON parse failed for sanitization data")`.

### Task 01-02: Add exception string and `exc_info=True` to `_validate_parsed` (lines 265, 285, 314)

**What:** Change each of the three `except Exception:` blocks to `except Exception as exc:` and update the log call to include the exception string and `exc_info=True`:

```python
# line 265
except Exception as exc:
    _log.warning("thread_sanitizer: skipping invalid thread_update %s: %s", _tu.get("id"), exc, exc_info=True)

# line 285
except Exception as exc:
    _log.warning("thread_sanitizer: skipping invalid resolved_thread %s: %s", _rt.get("id"), exc, exc_info=True)

# line 314
except Exception as exc:
    _log.warning("thread_sanitizer: skipping invalid world_state entry %s: %s", _ws.get("id"), exc, exc_info=True)
```

**Why:** The current code logs a warning but loses the exception string and traceback — you can't tell *why* the entry was invalid. Adding `exc_info=True` gives the full traceback. Adding `exc` gives the exception string in the log message.

**Validation:** `rg -n "except Exception:$" ccya/engine/thread_sanitizer.py` returns no results (no bare `except Exception:` lines remaining in `_validate_parsed`). Each of the three blocks should have `exc` in the log call and `exc_info=True`.

### Phase 01 verification

Run `make check` — lint + typecheck must pass.

---

## Phase 02: Server routes logging (High/Medium)

**File:** `ccya/server/routes.py`
**Findings:** Lines 156, 170, 582, 706, 867

### Task 02-01: Log save exclusion (line 156)

**What:** Add `_log.warning("Save %s excluded: failed to load state.yaml", name)` before `continue` in the `except Exception:` block.

**Why:** Users lose saves with no log explaining why. The `name` variable is available in scope (set earlier from `entry.name`).

**Validation:** The `except Exception:` at line 156 should be followed by a `_log.warning` call with the save name and "excluded" or "failed to load" in the message.

### Task 02-02: Log arc_origin read failure (line 170)

**What:** Add `_log.debug("Save %s: arc_origin read failed", name)` before `pass` in the `except Exception:` block.

**Why:** Violates logging standard. Low priority (arc_origin is optional metadata) but debug-level is sufficient.

**Validation:** The `except Exception:` at line 170 should be followed by a `_log.debug` call with the save name.

### Task 02-03: Log NPC tie resolution failure (line 582)

**What:** Add `_log.debug("NPC tie resolution failed, showing raw IDs")` before `pass` in the `except Exception:` block.

**Why:** Called on nearly every route that renders state. Debug-level is sufficient — this is a graceful degradation path for misconfigured npc_bonds.

**Validation:** The `except Exception:` at line 582 should be followed by a `_log.debug` call.

### Task 02-04: Log tone_tags/world_rules JSON parse failure (line 706)

**What:** Add `_log.warning("tone_tags/world_rules JSON parse failed, defaulting to empty lists")` inside the `except Exception:` block.

**Why:** User input (tone_tags, world_rules) is silently discarded. A warning is appropriate — this affects game setup.

**Validation:** The `except Exception:` at line 706 should be followed by a `_log.warning` call mentioning JSON parse failure.

### Task 02-05: Log LLM health check failure (line 867)

**What:** Add `_log.warning("LLM health check failed: %s", exc)` inside the `except Exception:` block (change to `except Exception as exc:`).

**Why:** Health check returns `{"llm": "fail"}` with no logged reason. The operator has no visibility into *why* the LLM is failing.

**Validation:** The `except Exception:` at line 867 should be `except Exception as exc:` and include `_log.warning` with the exception string.

### Phase 02 verification

Run `make check` — lint + typecheck must pass.

---

## Phase 03: Engine silent failures (Medium)

**Files:** `ccya/engine/extraction/record.py`, `ccya/engine/turn.py`, `ccya/engine/_pacing.py`
**Findings:** record.py line 55, turn.py line 826, _pacing.py line 316

### Task 03-01: Log invalid thread object in extraction (record.py line 55)

**What:** Change `except Exception:` to `except Exception as exc:` and add `_log.warning("Invalid thread object in scene, skipping: %s", exc)` before the silent fallback `all_threads.append({"id": "", "summary": ""})`.

**Why:** Invalid thread objects silently become empty placeholders. A warning with the exception string enables diagnosis of bad data.

**Validation:** The `except Exception:` at record.py line 55 should be `except Exception as exc:` and include a `_log.warning` call with the exception string.

### Task 03-02: Add `exc_info=True` to warmup failure (turn.py line 826)

**What:** Change `except Exception:` to `except Exception as exc:` and update the log call to include `exc_info=True`:

```python
except Exception as exc:
    _log.warning("Warmup LLM call failed — continuing without warmup cache: %s", exc, exc_info=True)
```

**Why:** The warmup failure is already logged as a warning but lacks `exc_info=True` and the exception string in the message.

**Validation:** The `except Exception:` at turn.py line 826 should be `except Exception as exc:` and the log call should include `exc_info=True` and `exc` in the message.

### Task 03-03: Log invalid arc thread in pacing (_pacing.py line 316)

**What:** Change `except Exception:` to `except Exception as exc:` and add `_log.warning("Invalid arc thread object, skipping: %s", exc)` before `return None`.

**Why:** This is the silent pacing failure — invalid arc thread objects are silently discarded with no logging at all. A warning is appropriate.

**Validation:** The `except Exception:` at _pacing.py line 316 should be `except Exception as exc:` and include a `_log.warning` call with the exception string.

### Phase 03 verification

Run `make check` — lint + typecheck must pass.

---

## Documentation updates (after all phases)

Update `docs/repomap.md` if any module boundaries or signatures changed (they won't — only logging calls changed).

Update `AGENTS.md` if logging standards need revision (they don't — this brings the codebase into compliance with existing standards).
