# scope-teardown

## Status
`open`

## Phases

3 phases: Remove the `<scope>` / `active_domains` system end-to-end — prompt, engine parsing, extraction skip logic, test suite, and viewer display.

## Objective

The `<scope>` tail system was designed to let the narrator selectively skip extraction streams (scene, state) when nothing changed. In practice the narrator always emits all domains (prompt says "when in doubt, include the scope"), so the skip logic never fires. The system costs ~250 tokens in the system prompt, ~200 tokens per turn in output, ~50 lines of conditional code in extraction.py, ~30 lines of scope parsing in turn.py, and ~200 lines of scope tests. Tearing it out simplifies the pipeline, removes dead conditional code, and saves ~250 tokens per turn in the system prompt.

## Non-goals

- Do not add new scope logic or a replacement mechanism.
- Do not modify the extractor prompts to always run all streams (they already do).
- Do not change the event schema for existing events — old events with `scope` keys will be ignored gracefully.

## Firm decisions

1. All 3 extraction streams (scene, state, progress) always run every turn.
2. The `<scope>` tag is removed from `narrate_system.j2` entirely — no replacement instruction.
3. `active_domains` is removed from the event dict written to `events.jsonl`.
4. `build_state_slice()` is deleted — it is dead code (never imported or called).
5. `_TRANSFER_VERBS` and `_narration_has_transfer()` are deleted — they were only used to auto-activate the inventory domain.

## Conflicts and overlap

None. This plan touches files not modified by any open plan.

## Implementation — Phase 1: Prompt and engine parsing

### Context files to load
- `ccya/prompts/narrate_system.j2`
- `ccya/engine/turn.py`
- `ccya/engine/extraction.py`
- `ccya/engine/narrate.py`
- `tests/test_engine_smoke.py`
- `tests/test_scope_tail_parser.py`
- `docs/REPOMAP/engine.md`

### Detailed steps

#### Step 1.1 — Remove scope section from narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete lines 113-144 ("## Active scope tail" section). This removes ~32 lines of scope instructions from the system prompt.

**Why:** The narrator no longer needs to emit a `<scope>` tag. The prompt should be shorter and simpler.

**Code Snippet:**
```jinja2
# Delete lines 113-144 entirely:
## Active scope tail
After your prose is complete, on a new line, emit a single line:
<scope>{"active_domains":["..."]}</scope>
Valid domains:
- scene             — scene tags, NPC presence, scene tagline changes
- inventory         — items received, used, dropped, upgraded
- pc_condition      — wounds, fatigue, mental conditions added or resolved
- quest_updates     — quest status or objectives changed
...
The tag and its contents are stripped from the player's view by the engine.
```

**Validation:** File should end at line 112 ("Rules: The tag and its contents are stripped..." removed). No scope references remain in the file.

#### Step 1.2 — Remove scope constants and functions from turn.py

**File:** `ccya/engine/turn.py`

**What:** Remove:
- `_ALL_DOMAINS` (lines 59-67)
- `_DEFAULT_DOMAINS` (lines 69-74)
- `_SCOPE_OPEN`, `_SCOPE_CLOSE`, `_SCOPE_TAIL_RE`, `_SCOPE_TAIL_BUFFER_SIZE` (lines 76-79)
- `_split_scope_tail()` function (lines 82-107)
- `_StreamTailFilter` class (lines 110-163)

**Why:** These are all scope-parsing utilities that are no longer needed.

**Code Snippet:**
```python
# Delete lines 59-163 entirely (from _ALL_DOMAINS through the end of _StreamTailFilter class)
# Keep everything from _compute_ages() onward
```

**Validation:** `grep -c "_SCOPE\|_split_scope\|_StreamTail\|_ALL_DOMAINS\|_DEFAULT_DOMAINS" ccya/engine/turn.py` should return 0.

#### Step 1.3 — Remove scope parsing from run_turn()

**File:** `ccya/engine/turn.py`

**What:** In `run_turn()` (around lines 543-625):
1. Remove `scope_filter = _StreamTailFilter()` (line 553)
2. Replace the streaming loop to pass chunks directly without filtering:
```python
# Before:
scope_filter = _StreamTailFilter()
first_visible = True
async for chunk in llm_chat_stream(...):
    visible = scope_filter.feed(chunk)
    if visible:
        if first_visible:
            first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            first_visible = False
        yield ("token", visible)
tail = scope_filter.flush()
if tail:
    if first_visible:
        first_ms = (asyncio.get_event_loop().time() - t0) * 1000
    yield ("token", tail)

# After:
first_visible = True
async for chunk in llm_chat_stream(...):
    narrative_chunks.append(chunk)  # Collect for error fallback
    if first_visible:
        first_ms = (asyncio.get_event_loop().time() - t0) * 1000
        first_visible = False
    yield ("token", chunk)
```
3. Remove `narrative_chunks[:] = [scope_filter.full_text()]` and `full_with_tail = strip_thinking(scope_filter.full_text())` and `_split_scope_tail()` call
4. Replace with:
```python
narrative = strip_thinking("".join(narrative_chunks))
```
5. Remove the `scope` key from the event dict (lines 845-848)
6. Remove `active_domains=_active_domains` from `_run_extraction_pipeline()` call

**Why:** The stream filter and scope parsing are no longer needed. The narrative is the raw LLM output.

**Code Snippet:**
```python
# Around line 543-582, replace the scope_filter block:
        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_request",
                messages=narr_messages,
                max_chars=config.log_llm_io_max_chars,
            )
        first_visible = True
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            narrative_chunks.append(chunk)
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                first_visible = False
            yield ("token", chunk)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        narrative = strip_thinking("".join(narrative_chunks))
```

**Validation:** `grep -c "scope_filter\|_split_scope_tail\|scope_decided_by\|_active_domains" ccya/engine/turn.py` should return 0.

#### Step 1.4 — Same changes in run_turn_retry()

**File:** `ccya/engine/turn.py`

**What:** Apply the same streaming loop and scope parsing removal in `run_turn_retry()` (around lines 1199-1279). Same pattern as Step 1.3.

**Why:** `run_turn_retry()` has the same scope parsing code.

**Code Snippet:** Same as Step 1.3 streaming replacement.

**Validation:** Same grep check as Step 1.3.

### Tests to write or update
- Delete `tests/test_scope_tail_parser.py` entirely (115 lines)
- Delete `TestExtractionStreamSkip` class from `tests/test_engine_smoke.py` (~260 lines)
- Delete `TestNarrationScopeTailFilter` class from `tests/test_engine_smoke.py` (~75 lines)
- Update `tests/test_turn_viewer.py`: remove `"scope": {...}` from test event dicts in `TestTurnViewerDataMinimalEvent` and `TestTurnViewerDataRealEvent`

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Remove `_ALL_DOMAINS`, `_DEFAULT_DOMAINS`, `_SCOPE_*` constants, `_split_scope_tail()`, `_StreamTailFilter` from turn.py section. Remove scope parsing from pipeline description. Remove `scope` key from events.jsonl description. Remove stream skipping description.
- `docs/REPOMAP/prompts.md`: Remove scope section from narrate_system.j2 description.

### Risks
1. **Old events.jsonl with `scope` keys** — The viewer code reads `ev.get("scope")` which returns `None` for old events without scope. This is safe.
2. **Error fallback uses `narrative_chunks`** — The streaming code previously used `scope_filter.full_text()` for the fallback. After removal, `narrative_chunks` collects all chunks during streaming, so the fallback still works.

## Implementation — Phase 2: Extraction skip logic

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/engine/narrate.py`
- `ccya/engine/__init__.py`
- `docs/REPOMAP/engine.md`

### Detailed steps

#### Step 2.1 — Remove active_domains param from _run_extraction_pipeline

**File:** `ccya/engine/extraction.py`

**What:**
1. Remove `active_domains: list[str]` from `_run_extraction_pipeline()` signature
2. Remove `active = set(active_domains)` line
3. Remove `_SKIPPED` dict (no longer needed — streams never skip)
4. Remove `run_scene = bool(scene_domains & active)` and the `if run_scene:` / `else:` branching — always run scene stream
5. Remove `run_state = bool({"inventory", "pc_condition"} & active)` and the `if run_state:` / `else:` branching — always run state stream
6. Remove the transfer-verb scan block (lines 681-688)
7. Remove `scene_result = SceneExtractResult()` and `state_result = StateExtractResult()` defaults (no longer needed)
8. Remove `"skipped": True` from extraction_event entries — always set `"skipped": False`

**Why:** All 3 streams always run. The skip logic is dead code.

**Code Snippet:**
```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> tuple["StateDelta", list[str], str, dict[str, Any], "ProgressExtractResult", "SceneExtractResult"]:
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, per_stream_event_data, progress_result, scene_result)
    """
    extraction_event: dict[str, Any] = {}

    # --- Stream 1: Scene (always runs) ---
    t_scene = asyncio.get_event_loop().time()
    scene_msgs = _extract_scene_messages(
        env, narration, state,
        enable_thinking=config.enable_extract_thinking,
        recent_turns=(recent_turns or [])[-1:],
        turn_no=turn_no,
    )
    # Capture pre-trim content for context_meta so the judge sees original sizes
    rendered_scene_system = scene_msgs[0]["content"] if scene_msgs else ""
    rendered_scene_user = scene_msgs[-1]["content"] if scene_msgs else ""
    strip_trace_markers_in_messages(scene_msgs)
    scene_msgs, scene_trimmed, scene_trimmed_chars = trim_messages(scene_msgs, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(turn_no, "extract_scene", scene_msgs)

    try:
        scene_result, scene_usage, scene_attempts, scene_retry_errors = await _call_stream(
            scene_msgs, config, trace_id, "extract_scene", SceneExtractResult
        )
        scene_result = _check_npc_ghost_cycle(scene_result, state, trace_id=trace_id, turn_no=turn_no)
        extraction_event["scene"] = {
            "rendered_system": rendered_scene_system,
            "rendered_user": rendered_scene_user,
            "output": scene_result.model_dump(exclude_none=True),
            "skipped": False,
            "attempts": scene_attempts,
            "retry_errors": scene_retry_errors,
            "tokens_in": scene_usage.get("prompt_tokens", 0),
            "tokens_out": scene_usage.get("completion_tokens", 0),
            "ms": round((asyncio.get_event_loop().time() - t_scene) * 1000, 1),
            "context_meta": _context_meta(rendered_scene_system, rendered_scene_user, scene_trimmed, scene_trimmed_chars),
        }
    except Exception as exc:
        _log.warning("extract_scene failed: %s", exc, extra={"trace_id": trace_id})
        extraction_event["scene"] = {"skipped": True, "error": str(exc), "tokens_in": 0, "tokens_out": 0, "ms": 0, "attempts": 0, "retry_errors": []}
```

Similar pattern for state stream (always run, no `if run_state:` check).

**Validation:** `grep -c "active_domains\|_SKIPPED\|run_scene\|run_state\|_TRANSFER_VERBS\|_narration_has_transfer" ccya/engine/extraction.py` should return 0.

#### Step 2.2 — Remove _TRANSFER_VERBS and _narration_has_transfer

**File:** `ccya/engine/extraction.py`

**What:** Delete `_TRANSFER_VERBS` frozenset (lines 246-261) and `_narration_has_transfer()` function (lines 262-265).

**Why:** These were only used to auto-activate the inventory domain, which is no longer needed.

**Validation:** Same grep check as Step 2.1.

#### Step 2.3 — Remove build_state_slice from narrate.py

**File:** `ccya/engine/narrate.py`

**What:** Delete `build_state_slice()` function (lines 130-175).

**Why:** It is dead code — never imported or called anywhere in the codebase.

**Validation:** `grep -c "build_state_slice" ccya/engine/narrate.py` should return 0.

#### Step 2.4 — Update _run_extraction_pipeline call sites in turn.py

**File:** `ccya/engine/turn.py`

**What:** Remove `active_domains=_active_domains` from both `_run_extraction_pipeline()` calls (in `run_turn()` and `run_turn_retry()`).

**Why:** The function no longer accepts `active_domains`.

**Validation:** `grep -c "active_domains" ccya/engine/turn.py` should return 0.

### Tests to write or update
- Update `tests/test_engine_smoke.py`: The `TestExtractionStreamSkip` class is deleted in Phase 1. No new tests needed — the existing smoke tests already exercise the full pipeline with all streams running.
- Update `tests/test_turn_viewer.py`: Remove `"scope": {...}` from test event dicts.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Update `_run_extraction_pipeline` signature to remove `active_domains` param. Remove skip logic description. Remove `_TRANSFER_VERBS` and `_narration_has_transfer` from function list. Remove `build_state_slice` from narrate.py section.

### Risks
1. **Latency increase** — All 3 extractors now run every turn instead of conditionally. This is the intended tradeoff for simplicity.
2. **Transfer-verb scan removed** — The inventory domain was auto-activated when narration contained transfer verbs (give, take, drop, etc.). Without it, the state extractor always runs anyway, so this has no functional impact.

## Implementation — Phase 3: Tests, viewer, and cleanup

### Context files to load
- `tests/test_engine_smoke.py`
- `tests/test_scope_tail_parser.py`
- `tests/test_turn_viewer.py`
- `ccya/server/tv.py`
- `ccya/templates/_turn_viewer.html`
- `ccya/static/app.src.css`
- `docs/REPOMAP/engine.md`
- `docs/REPOMAP/server.md`
- `docs/REPOMAP/prompts.md`

### Detailed steps

#### Step 3.1 — Delete scope test files and classes

**Files:**
- `tests/test_scope_tail_parser.py` — delete entire file
- `tests/test_engine_smoke.py` — delete `TestExtractionStreamSkip` class (~260 lines) and `TestNarrationScopeTailFilter` class (~75 lines)

**Why:** These tests exercise scope parsing and skip logic that no longer exists.

**Validation:** `make test` passes with no scope-related test failures.

#### Step 3.2 — Update test_turn_viewer.py event dicts

**File:** `tests/test_turn_viewer.py`

**What:** Remove `"scope": {...}` entries from test event dicts in:
- `TestTurnViewerDataMinimalEvent.test_minimal_event()` (lines 224-226)
- `TestTurnViewerDataRealEvent.test_realistic_event()` (lines 262-264)

**Why:** The event dict no longer includes `scope`.

**Code Snippet:**
```python
# Before:
event = {
    "turn": 1,
    "trace_id": "abc123",
    "scope": {
        "active_domains": [],
    },
}

# After:
event = {
    "turn": 1,
    "trace_id": "abc123",
}
```

**Validation:** `grep -c '"scope"' tests/test_turn_viewer.py` should return 0.

#### Step 3.3 — Remove active_domains from turn viewer

**File:** `ccya/server/tv.py`

**What:** Remove the scope/active_domains parsing from `_turn_viewer_data()`:
```python
# Delete these lines:
# Scope / active domains from narrator
scope = ev.get("scope") or {}
active_domains = scope.get("active_domains") or []
```

**Why:** The event dict no longer has `scope` keys (new events). Old events with `scope` keys are ignored gracefully by `ev.get("scope")` returning `None`.

**Validation:** `grep -c "active_domains\|scope" ccya/server/tv.py` should return 0 (except in comments).

#### Step 3.4 — Remove active domains section from template

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove the active domains section from the diff panel:
```html
<!-- Delete: -->
<template x-if="t.active_domains && t.active_domains.length">
    <div class="tv-diff-section">
        <div class="tv-diff-section-label">Active domains</div>
        <template x-for="domain in t.active_domains" :key="domain">
            <div class="tv-domain-pill" x-text="domain"></div>
        </template>
    </div>
</template>
```

**Why:** No more active domains to display.

**Validation:** Template renders without errors.

#### Step 3.5 — Remove .tv-domain-pill CSS

**File:** `ccya/static/app.src.css`

**What:** Delete the `.tv-domain-pill` CSS class block.

**Why:** No more domain pills to style.

**Validation:** `grep -c "tv-domain-pill" ccya/static/app.src.css` should return 0.

### Tests to write or update
- `make test` — all tests should pass
- `make check` — lint and typecheck should pass

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Update all scope references as noted in Phase 1 and Phase 2.
- `docs/REPOMAP/server.md`: Remove `active_domains` from `_turn_viewer_data` description.
- `docs/REPOMAP/prompts.md`: Remove scope section from narrate_system.j2 description.

### Risks
1. **Existing save dirs with scope in events.jsonl** — The viewer code reads `ev.get("scope")` which returns `None` for old events. The template check `t.active_domains && t.active_domains.length` will be falsy for `undefined`, so no rendering error.
2. **Regression in smoke tests** — The smoke tests exercise the full pipeline. After removal, all 3 extractors always run. This is the intended behavior.

## Ambiguities requiring resolution before execution

None. All scope references have been identified and the removal path is clear.
