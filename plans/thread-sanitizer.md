# Thread Sanitizer — implementation plan

## Purpose

Implementation plan for the thread sanitizer: a batch process that periodically reviews narrative evidence and fixes `arc.threads[]` state. Governed by `docs/design/thread-sanitizer-design.md`.

## Problem Statement

Threads accumulate without correction. The storyteller never retroactively removes or consolidates threads. Over time threads linger as active after narrative resolution, urgency levels drift, progress entries pile up, and `visible_goal` ossifies. The old compactor was removed in `be8113f1`; no replacement exists.

## Constraints

- Zero changes to extraction, storyteller, narrate, or ruling prompts
- Must not rewrite chronicle.md, touch prior_history, or modify state outside `arc`
- Runs synchronously (blocking), matching old compactor behavior
- Must reuse existing CSS classes (`tv-compaction-*` in `app.src.css:2563-2611`)
- Must follow old compactor's SSE phase event shape: `{"phase": "sanitize_start", "expected_ms": 0}`
- No new Pydantic models; reuse `ArcThread`, `ThreadUpdate`, `ThreadResolution` from `models.py`

## Non-goals

- World state, NPC, inventory, or condition cleanup
- Chronicle rewriting
- Per-turn incremental correctness

## Solution

Add a `ccya/engine/thread_sanitizer.py` module that every `sanitize_every` turns (default 5) calls the LLM with current arc state + narrative evidence, applies thread changes, logs to events.jsonl, and yields SSE phase events. Three phases: (1) config + module + prompt, (2) pipeline hook, (3) frontend (UI + turn viewer).

## Firm decisions

1. Delta-based output — LLM names threads to update/add/resolve/remove; unmentioned threads survive
2. Blocking synchronous call between prior_history append and `yield("complete")` in `turn.py`
3. Prose-only prompt — no inventory, NPC sheet, conditions, or world state
4. Thread-first ordering in prompt (arc/thread state before narrative evidence)
5. `_checklist` rubric in prompt to force explicit category review
6. Reuse `sections/_thread_list.j2` for thread rendering
7. Reuse `tv-compaction-*` CSS — no new classes
8. Phase label `sanitize_done` → "Saving…" (matches extract_done/persist), not old compactor's "Cleaning up…"

## Risks, Ambiguities, and Blockers

- Module imports `load_last_narration` from `ccya.state.chronicle` — no circular import risk (chronicle has no engine imports)
- `_thread_list.j2` expects `turn_no` variable — sanitizer will provide `turn_no` from `state["meta"]["turn"]`; `gate` variable is undefined but Jinja2 treats undefined as falsy in `{% if gate and gate == "block_escalate" %}`, safe
- Sanitizer module must catch ALL exceptions internally so a failed sanitization never crashes the turn

## Status

`open`

## Phases

3 phases: (1) config + module + prompt, (2) pipeline hook, (3) frontend.

---

## Implementation — Phase 1: Config + module + prompt

### Context files to load

| File | Why |
|---|---|
| `ccya/engine/config.py:92-165` | EngineConfig dataclass — add fields |
| `ccya/engine/config.py:175-266` | `build_engine_config()` — add mappings |
| `ccya/models.py:34-69` | `ArcThread`, `CampaignArc` — for output validation |
| `ccya/models.py:389-403` | `ThreadUpdate`, `ThreadResolution` — for output validation |
| `ccya/state/chronicle.py:45-65` | `load_last_narration()` — reads full turns from chronicle |
| `ccya/prompts/sections/_thread_list.j2` | Shared template — include in sanitizer prompt |
| `ccya/engine/turn.py:144-213` | `_apply_thread_updates()` — reference for apply logic |
| `ccya/engine/turn.py:332-390` | `_apply_thread_resolutions()` — reference for resolve logic |
| `git show be8113f1^:ccya/engine/compactor.py` | Old compactor — reference for LLM call pattern, trigger logic, event logging |
| `git show be8113f1^:ccya/prompts/compact_system.j2` | Old compactor system prompt — reference for `_checklist` rubric style |

### Detailed steps

#### Step 1.1 — Add config fields to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add two fields to the `EngineConfig` dataclass after `thread_max_active` (line 164), before `_resolve_difficulty_modifiers` (line 166):

```python
    # Thread sanitizer: batch arc/thread cleanup every N turns
    sanitize_every: int = 5       # 0 = disabled
    sanitize_temperature: float = 0.3
```

**Why:** Design doc Decision Table requires configurable interval and temperature for the sanitizer LLM call.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.sanitize_every == 5; assert c.sanitize_temperature == 0.3"`

#### Step 1.2 — Add mappings in build_engine_config()

**File:** `ccya/engine/config.py`

**What:** After line 265 (`thread_max_active=int(game.get(...))`), before the closing `)` on line 266, add:

```python
        sanitize_every=int(game.get("sanitize_every", 5)),   # 0 = disabled
        sanitize_temperature=float(
            llm.get("sanitize", {}).get("temperature", 0.3)
        ),
```

**Why:** Maps config.yaml keys to EngineConfig fields, matching existing pattern for game/llm config sections.

**Validation:** Verify defaults: `python -c "from ccya.engine.config import build_engine_config; c = build_engine_config({'llm': {}, 'game': {}}); assert c.sanitize_every == 5; assert c.sanitize_temperature == 0.3"`

#### Step 1.3 — Create `ccya/engine/thread_sanitizer.py`

**File:** `ccya/engine/thread_sanitizer.py` (new)

**What:** Module with four functions:

```python
async def sanitize_threads(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
    trace_id: str = "",
) -> tuple[dict[str, Any], bool]:
    """Run thread sanitization if current turn triggers it.
    
    Returns:
        (state, sanitize_ran) — sanitize_ran is True when any thread
        changes were applied. state is mutated in place.
    """
```

**`sanitize_threads()` logic** (mirror old compactor `compactor.py:22-145`):
1. If `config.sanitize_every <= 0` or `current_turn == 0` or `current_turn % config.sanitize_every != 0` → return `(state, False)`
2. Load 5 recent full turns via `load_last_narration(save_dir, 5)`
3. Pull prior_history from `state["meta"]["prior_history"]`
4. Build Jinja env (same pattern as `_build_jinja_env` in config.py, template_dir=`ccya/prompts`)
5. Build messages via `_build_messages(env, state, recent_turns, prior_history, turn_no)`
6. Call LLM via `llm_chat()` with `temperature=config.sanitize_temperature`, `timeout=config.request_timeout_s`
7. Parse response via `_parse_response(response_text)` → dict or None
8. If parsed and non-empty, call `_apply_sanitization(state, parsed, current_turn)` → bool
9. If changes applied, write events.jsonl record
10. Return `(state, changes_made)`

**`_build_messages()` logic** (mirror old `_build_compact_messages()` at `compactor.py:79-99`):
- Render `sanitize_thread.j2` system section
- Render user section with: arc state, threads (via `_thread_list.j2` include), completed threads, 5 recent full turns, prior_history bullets, instructions
- Return `[system_msg, user_msg]`

**`_parse_response()` logic** (mirror old `_parse_compact_response()` at `compactor.py:99-130`):
- Extract JSON from `<sanitize>...</sanitize>` tags (regex or brace matching like old code's `_find_json` in `config.py:297`)
- Validate: `goal_update` (if present, must have `visible_goal` and/or `goal_context`), `thread_updates` (each validated against `ThreadUpdate`), `resolved_threads` (each validated against `ThreadResolution`), `removed_threads` (each must have `id` + `reason`), `new_threads` (each validated against `ArcThread`)
- Skip entries with unknown thread IDs (log warning)
- Return parsed dict or `None` on failure

**`_apply_sanitization()` logic** (design doc §"Apply logic"):
1. `goal_update`: replace `state.arc.visible_goal`, `state.arc.goal_context` if non-null
2. `thread_updates`: for each, find thread by ID in `state.arc.threads[]`, apply non-null fields (same pattern as `_apply_thread_updates()` in `turn.py:144`)
3. `resolved_threads`: for each, find thread by ID in `state.arc.threads[]`, set `resolution_state`/`outcome`/`resolved_turn`/`active: false`, move to `state.arc.completed_threads[]` (same pattern as `_apply_thread_resolutions()` in `turn.py:332`)
4. `removed_threads`: remove by ID from both `threads[]` and `completed_threads[]`
5. `new_threads`: validate each as `ArcThread`, append to `threads[]`, set `last_thread_created_turn`
6. Return `True` if any change was applied, else `False`

**Event record** (design doc §"Events.jsonl record shape"):
```python
{
    "kind": "sanitizer",
    "turn": current_turn,
    "trace_id": trace_id,
    "ms": round(elapsed_ms, 1),
    "tokens_in": int(usage.get("prompt_tokens", 0)),
    "tokens_out": int(usage.get("completion_tokens", 0)),
    "threads_updated": [str],
    "threads_removed": [str],
    "threads_resolved": [str],
    "threads_added": [str],
    "goal_changed": bool,
    "changes_detail": {
        "updated": {id: {changed_fields...}},
        "removed": [...],
        "resolved": [...],
        "added": [...],
        "goal": {"before": str|None, "after": str|None},
    },
}
```

Write via `append_event(save_dir, record)` from `ccya.state.chronicle`.

**Logging:** Use `logging.getLogger(__name__)` per repo convention. Log warning on LLM failure, info on each sanitize run.

**Imports needed:**
```python
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _build_jinja_env
from ccya.llm_client import chat as llm_chat
from ccya.models import ArcThread, ThreadUpdate, ThreadResolution
from ccya.state.chronicle import load_last_narration, append_event
```

**Why:** Core module implementing the design doc's Proposed Solution, matching old compactor's patterns for trigger, LLM call, parse, apply, and event logging.

**Validation:** `python -c "from ccya.engine.thread_sanitizer import sanitize_threads, _build_messages, _parse_response, _apply_sanitization"` imports cleanly. Temporarily call with `sanitize_every=0` and confirm it returns `(state, False)` with no errors.

#### Step 1.4 — Create prompt file

**File:** `ccya/prompts/sanitize_thread.j2` (new)

**What:** Single Jinja2 file with `[SYSTEM]` and `[USER]` sections, using the exact template from the design doc §"Prompt design" with these variables:

| Variable | Source | Notes |
|---|---|---|
| `visible_goal` | `state.arc.visible_goal` | |
| `goal_context` | `state.arc.get("goal_context", "")` | |
| `resolution` | `state.arc.get("resolution")` | None if unresolved |
| `threads` | `state.arc.threads` | All threads (including latent) — consumed by `_thread_list.j2` include |
| `completed_threads` | `state.arc.completed_threads` | All completed threads (no TTL filter) |
| `turn_no` | `state.meta.turn` | For `_thread_list.j2` "turns ago" calculation |
| `recent_turns` | `load_last_narration(save_dir, 5)` | List of `{turn, input, narrative}` dicts |
| `prior_history` | `state.meta.prior_history` | List of `- [T{n}] ...` strings |

Include `sections/_thread_list.j2` for thread rendering.

**Why:** Core prompt driving the sanitizer LLM call. Reuses shared template.

**Validation:** Render from Python: `env.get_template("sanitize_thread.j2").render(...)`, verify no template errors.

### Tests to write or update

Tests are temporarily removed during refactor (per local AGENTS.md). Skip for all phases.

### Documentation to update

- `docs/repomap.md`: Add entry for `ccya/engine/thread_sanitizer.py` in module index table + public API section listing `sanitize_threads()`.

---

## Implementation — Phase 2: Pipeline hook

### Context files to load

| File | Why |
|---|---|
| `ccya/engine/turn.py:1406-1434` | Exact hook point |
| `ccya/engine/turn.py:36-60` | Existing imports (add new import line) |
| `git show be8113f1^:ccya/engine/turn.py` lines 1596-1602 | Old compactor hook — exact pattern to replicate |

### Detailed steps

#### Step 2.1 — Import `sanitize_threads` in turn.py

**File:** `ccya/engine/turn.py`

**What:** Add import line in the existing block of engine imports (after line 27 or alongside other engine imports). Use relative import: `from ccya.engine.thread_sanitizer import sanitize_threads`.

**Why:** turn.py needs to call the sanitizer. No circular import risk — thread_sanitizer imports only from `config.py`, `llm_client.py`, `models.py`, and `state.chronicle`. None of those import from `turn.py`.

**Validation:** `python -c "from ccya.engine.turn import run_turn"` — no import error.

#### Step 2.2 — Add sanitizer hook + SSE phase events

**File:** `ccya/engine/turn.py`

**What:** Insert between line 1415 (end of prior_history append) and line 1417 (start of `result_obj = TurnResult(...)`). The text to insert:

```python

        # === Thread sanitizer (after prior_history, before yield complete) ===
        if config.sanitize_every > 0:
            t_sanitize = asyncio.get_running_loop().time()
            state, sanitize_ran = await sanitize_threads(
                save_dir, state, config, trace_id=trace_id,
            )
            if sanitize_ran:
                yield ("phase", {"phase": "sanitize_start", "expected_ms": 0})
                yield ("phase", {"phase": "sanitize_done", "ms": round(
                    (asyncio.get_running_loop().time() - t_sanitize) * 1000, 1
                )})
            save_state(save_dir, state)

```

**Why:** Design doc specifies exact position and shape. Mirrors old compactor hook at `be8113f1^:turn.py:1596-1602`.

**Validation:** Run `make check` — lint and typecheck pass. Temporarily set `sanitize_every=0` in config and run a turn; confirm no change in behavior.

### Tests to write or update

None (tests removed during refactor).

### Documentation to update

- `docs/repomap.md`: In the 5-call pipeline section, add a 6th step or note after extraction describing the sanitizer phase. Reference the new module.

---

## Implementation — Phase 3: Frontend (UI + turn viewer)

### Context files to load

| File | Why |
|---|---|
| `ccya/templates/index.html:755-779` | Phase label handler — add sanitizer branches |
| `ccya/server/tv.py:374-400` | Turn viewer row builder — add sanitizer handler |
| `ccya/templates/_turn_viewer.html:47-129` | Turn viewer template — add sanitizer row block, update catch-all and filter |
| `git show be8113f1^:ccya/templates/index.html:540-560` | Old compact phase labels — reference shape |
| `git show be8113f1^:ccya/server/tv.py:370-400` | Old compaction handler — reference row dict shape |
| `git show be8113f1^:ccya/templates/_turn_viewer.html:71-130` | Old compaction template — reference block shape |

### Detailed steps

#### Step 3.1 — Add phase label handlers in index.html

**File:** `ccya/templates/index.html`

**What:** After line 779 (closing `}` of the `persist` handler), before line 780 (blank line before `function _clearProgressStrip`), insert:

```javascript
    } else if (p === 'sanitize_start') {
        label.textContent = 'Sanitizing state…';
        if (eta) eta.textContent = '';
    } else if (p === 'sanitize_done') {
        label.textContent = 'Saving…';
        if (eta) eta.textContent = '';
    }
```

**Why:** Design doc §"UI — phase labels". Mirrors old compactor's `compact_start`/`compact_done` shape at `be8113f1^:index.html:546-550` with updated labels.

**Validation:** Load game in browser, trigger a sanitize turn, verify the progress strip shows "Sanitizing state…" then "Saving…".

#### Step 3.2 — Add sanitizer row handler in tv.py

**File:** `ccya/server/tv.py`

**What:** After line 383 (JSON decode), before turn-level event processing, insert:

```python
        if ev.get("kind") == "sanitizer":
            chg = ev.get("changes_detail") or {}
            rows.append({
                "row_kind": "sanitizer",
                "turn": int(ev.get("turn") or 0),
                "ms": round(float(ev.get("ms", 0)), 1),
                "tokens_in": int(ev.get("tokens_in", 0)),
                "tokens_out": int(ev.get("tokens_out", 0)),
                "threads_updated": list(ev.get("threads_updated", [])),
                "threads_removed": list(ev.get("threads_removed", [])),
                "threads_resolved": list(ev.get("threads_resolved", [])),
                "threads_added": list(ev.get("threads_added", [])),
                "goal_changed": bool(ev.get("goal_changed")),
                "changes_detail": chg,
                "has_changes": bool(
                    chg.get("updated")
                    or chg.get("removed")
                    or chg.get("resolved")
                    or chg.get("added")
                    or chg.get("goal")
                ),
            })
            continue
```

**Why:** Design doc §"Turn viewer — sanitizer row". Mirrors old compaction handler at `be8113f1^:tv.py:376-392`.

**Validation:** `python -c "from ccya.server.tv import _turn_viewer_data"` — no import error. Sanitizer events in events.jsonl produce `row_kind: "sanitizer"` rows.

#### Step 3.3 — Add sanitizer row template block in _turn_viewer.html

**File:** `ccya/templates/_turn_viewer.html`

**What:** After the seed block's closing `</template>` (line 69), before the catch-all `<template x-if="t.row_kind !== 'seed'">` (line 71), insert the sanitizer row block from the design doc §"Turn viewer — sanitizer row" (the full `<template x-if="t.row_kind === 'sanitizer'">...</template>` block).

**Why:** Design doc specifies exact template structure matching old compaction block at `be8113f1^:_turn_viewer.html:71-130`.

**Validation:** Visual — open turn viewer after a sanitizer event, see a collapsible "Thread Sanitizer" card between seed and turn rows.

#### Step 3.4 — Update catch-all and visibleTurns filter

**File:** `ccya/templates/_turn_viewer.html`

**What — catch-all (line 71):**
Change:
```html
<template x-if="t.row_kind !== 'seed'">
```
To:
```html
<template x-if="t.row_kind !== 'seed' && t.row_kind !== 'sanitizer'">
```

**What — visibleTurns() (line 457):**
Change:
```javascript
if (t.row_kind === 'seed') return true;
```
To:
```javascript
if (t.row_kind === 'seed' || t.row_kind === 'sanitizer') return true;
```

**Why:** Sanitizer rows (like seed rows) must always be visible regardless of filter state, and must be excluded from the catch-all turn card template.

**Validation:** Sanitizer row appears in turn viewer with all filter combinations; is not duplicated by the catch-all template.

### Tests to write or update

None (tests removed during refactor).

### Documentation to update

- `docs/repomap.md`: If the pipeline section has SSE phase events documented, add `sanitize_start`/`sanitize_done` to the list.
- `docs/architecture/narration-ui.md`: The SSE event table lists `compact_start` — remove that stale entry and add `sanitize_start`/`sanitize_done` at the end.
