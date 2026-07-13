# Plan: F-35 — Turn progress stacked cards

## Design Reference

- Design: `docs/design/turn-progress-cards-design.md`
- Ticket: `roadmap/features/F-35-turn-progress-cards.md`

## Problem Statement

The current progress strip (`<div class="progress-strip">`) is a single horizontal bar that replaces its label on every phase event. Users see only one status at a time and have no visual summary of overall progress. This plan replaces it with a two-phase layout: ruling and narration as individual cards (one at a time, same timing as current), followed by an extraction row with three colored bars (scene, state, record) that fill sequentially.

## Firm decisions (from design)

1. Two-phase layout: ruling card → narration card → extraction row (3 bars).
2. Five phase identities: ruling, narration, scene, state, record. Async steps hidden.
3. Ruling card appears on `ruling_start`, fades at `narrate_start`. Narration card appears on `narrate_start`, fades at `narrate_done`. Extraction row appears on `narrate_done`.
4. Each card has its own progress bar, fills at `elapsed / expectedMs`.
5. Extraction row: three bars in shared container, appear together, fill sequentially (one at a time).
6. Progress color palette: ruling=--stage-ruling, narration=--stage-narrate, scene=--stage-scene, state=--stage-state, record=--stage-storytell.
7. Progress bar math: `min(1.0, elapsed / expectedMs)`, capped at 100%. Each bar manages its own timer.
8. ExpectedMs: from `_avg_event_ms()` in events.jsonl (last 5 entries). If no history (first turn), use fallback estimates: ruling 3s, narration 8s, scene 3s, state 3s, record 6s.
9. Roll pill (outcome summary / band badge) appears after extraction row fades — same existing behavior.
10. Roll pill never shown inside any card.

## Scope

- **Phase 01:** Backend — per-sub-stream expected_ms in phase events
- **Phase 02:** Frontend — ruling/narration cards + extraction row
- **Phase 03:** CSS — card styling, extraction row container, progress animations
- **Phase 04:** Documentation — repomap, architecture docs, AGENTS.md

---

## Phase 01: Backend — per-sub-stream expected_ms

### Depends on

None

### Context files to load

- `ccya/engine/ruling.py:157` — `exp_ruling_ms` from `_avg_event_ms()` and emitted in `ruling_start` event
- `ccya/engine/turn.py:304` — `exp_narrate_ms` from `_avg_event_ms()` and emitted in `narrate_start` event
- `ccya/engine/extraction/pipeline.py:65` — `_run_extraction_stream` emits `extract_stream_start` / `extract_stream_done` events (no expected_ms currently)
- `ccya/engine/extraction/utils.py:228` — `_avg_event_ms(save_dir, field_path, n=5)` reads events.jsonl, averages values for field path
- `ccya/engine/turn.py:664-666` — Main event written to events.jsonl with `narrate.total_ms`, `extract.total_ms`, `extraction.scene.ms`, etc.
- `ccya/ev/events.py:29` — `events.jsonl` line structure: one JSON object per line, includes `type`, `turn`, per-phase data fields

### What changes

### 1. Update events.jsonl event structure — add `scene.total_ms`, `state.total_ms`, `record.total_ms` at top level (CCYA,ALL)

In `_persist_and_async_cleanup()` around line 629-666 of `ccya/engine/turn.py`, when the main event dict is constructed, add `scene.total_ms`, `state.total_ms`, `record.total_ms` fields extracted from `extraction_event` and `ext_metrics`.

**Where to change**

`ccya/engine/turn.py:664-666` — after `"narrate"` is set and before `"extract"` is set

**Before:**
```python
        "narrate": {**narr_metrics, "prose": narrative},
        "extraction": extraction_event,
        ...
```

**After:**
```python
        "narrate": {**narr_metrics, "prose": narrative},
        "scene": {"total_ms": round(extraction_event.get("scene", {}).get("ms", 0), 1)},
        "state": {"total_ms": round(extraction_event.get("state", {}).get("ms", 0), 1)},
        "record": {"total_ms": round(extraction_event.get("record", {}).get("ms", 0), 1)},
        "extract": ext_metrics,
        "extraction": extraction_event,
        ...
```

**Why:** Enables `_avg_event_ms(save_dir, "scene.total_ms")` to read per-sub-stream durations directly from events.jsonl. The existing `extraction.scene.ms` path works with `_avg_event_ms` but the naming `ms` is inconsistent with the existing `ruling.total_ms` and `narrate.total_ms` pattern. Adding top-level `scene.total_ms`, `state.total_ms`, `record.total_ms` creates a consistent naming convention across all pipeline stages.

### 2. Thread `save_dir` through `_run_extraction_stream` (CCYA,ALL)

Add `save_dir: Path` parameter to `_run_extraction_pipeline` (at end of keyword-only line), `_scene_stream`, `_state_stream`, `_record_stream`, and `_run_extraction_stream`. Pass `save_dir` through the call chain.

**Where to change:** `ccya/engine/extraction/pipeline.py`

- `_run_extraction_pipeline()` — add `save_dir: Path` to keyword-only params (after `packing`)
- `_scene_stream()` — add `save_dir: Path`, pass to `_run_extraction_stream(..., save_dir=save_dir)`
- `_state_stream()` — add `save_dir: Path`, pass to `_run_extraction_stream(..., save_dir=save_dir)`
- `_record_stream()` — add `save_dir: Path`, pass to `_run_extraction_stream(..., save_dir=save_dir)`
- `_run_extraction_stream()` — add `save_dir: Path` to keyword-only params (after `container`)

**Signature changes:**

```python
# Before — _run_extraction_pipeline
async def _run_extraction_pipeline(
    env: "Environment",
    state: WorldState,
    narration: str,
    *,
    intent: "IntentEnvelope | None" = None,
    ...
    packing: dict[str, Any] | None = None,
) -> "AsyncIterator[tuple[str, Any] | ...]":

# After
async def _run_extraction_pipeline(
    env: "Environment",
    state: WorldState,
    narration: str,
    *,
    intent: "IntentEnvelope | None" = None,
    ...
    packing: dict[str, Any] | None = None,
    save_dir: Path = Path("."),
) -> "AsyncIterator[tuple[str, Any] | ...]":
```

_@_scene_stream, _@_state_stream, _@_record_stream: add `save_dir: Path = Path(".")` as last positional param._

_Call in `_extract_phase` (turn.py line 429): add `save_dir=ctx.save_dir` to `_run_extraction_pipeline(` call._

**Why:** `_run_extraction_stream` needs access to `save_dir` so it can compute per-sub-stream expected_ms from historical data.

### 3. Emit per-sub-stream expected_ms in `extract_stream_done` event (CCYA,ALL)

In `_run_extraction_stream()`, after computing the extraction result, calculate `expected_ms` from historical sub-stream data and include it in the `extract_stream_done` phase event.

**Where to change:** `ccya/engine/extraction/pipeline.py:110` — the `extract_stream_done` yield

**Before:**
```python
    yield ("phase", {"phase": "extract_stream_done", "stream": variant.name})
```

**After:**
```python
    exp_ms = _avg_event_ms(save_dir, f"{variant.name}.total_ms")
    yield ("phase", {"phase": "extract_stream_done", "stream": variant.name, "expected_ms": exp_ms})
```

**Why:** Sends per-sub-stream `expected_ms` in terminal phase events so the frontend can use it for progress bar calculation. The `_avg_event_ms(save_dir, "scene.total_ms")` will read from the new `scene.total_ms` top-level field added in step 1.

### Validation

- `make check` passes (lint + typecheck)
- `_avg_event_ms(save_dir, "scene.total_ms")` returns correct values by reading the new top-level fields from `events.jsonl`
- Per-phase events now include `expected_ms` for: `ruling_start`, `narrate_start`, `extract_stream_done(scene)`, `extract_stream_done(state)`, `extract_stream_done(record)`
- Events written to `events.jsonl` after a turn include `scene.total_ms`, `state.total_ms`, `record.total_ms`

---

## Phase 02: Frontend — ruling/narration cards + extraction row

### Depends on

Phase 01

### Context files to load

- `ccya/static/game-utils.js` — `_progressStripHTML()` (line 263), `_setProgressFromPhase()` (line 367), `_clearProgressStrip()` (line 431), `_bindProgressTimer()` (line 439)
- `ccya/static/game.js` — EventSource phase handler at line 878-899, `_setProgressFromPhase(strip, payload)` call at line 921, `world_done` handler at line 899
- `ccya/static/tokens.css` — `--stage-*` color variables (line 39-44)

### What changes

### 1. Create ruling and narration card HTML (CCYA,ALL)

Add `_createProgressCardHTML(phase, expected_ms)` in `game-utils.js`. Produces a card with: `<div class="progress-card progress-card--{phase}">` containing spinner, label, progress bar, elapsed.

### 2. Establish ruling card lifecycle (CCYA,ALL)

In `game.js` phase handler:
- `ruling_start` → call `_createRulingCard()` with `expected_ms` from payload
- `narrate_start` → call `_fadeOutCard(rulingCard)`, then `_createNarrationCard()` with `expected_ms` from payload

### 3. Narration card lifecycle (CCYA,ALL)

In `game.js` phase handler:
- `narrate_start` → calls `_createNarrationCard()` (done above in step 2)
- `narrate_done` → calls `_fadeOutCard(narrationCard)`, then `_showExtractionRow()`

### 4. Extraction row lifecycle (CCYA,ALL)

In `game.js` phase handler:
- `narrate_done` → calls `_showExtractionRow()` (done above in step 3)
- `extract_stream_done(scene)` → calls `_completeExtractionBar("scene")`
- `extract_stream_done(state)` → calls `_completeExtractionBar("state")`
- `extract_stream_done(record)` → calls `_completeExtractionBar("record")`
- `turn_complete` → calls `_dismissExtractionRow()`

### 5. Update phase event handler in game.js (CCYA,ALL)

In `game.js`, replace the existing `phase` handler at line 878-899 with the new card-based lifecycle. The new handler must:
- Filter out `sanitize_start`, `sanitize_done`, `world_start`, `world_done` from card updating (no card for these)
- Route `ruling_start`, `ruling_done`, `narrate_start`, `narrate_first_token`, `narrate_done` to card lifecycle
- Route `extract_stream_done(scene)`, `extract_stream_done(state)`, `extract_stream_done(record)` to bar lifecycle
- Handle `turn_complete` to dismiss extraction row

**Filtering phase events**

The handler will dispatch the event by phase name and check if we already know this event stage.

**Event dispatch:**

```javascript
// Rule: sanitize_start, sanitize_done, world_start, world_done → no card update
// Ruling: ruling_start → create ruling card, ruling_done → card continues filling with spinning
// Narration: narrate_start → fade ruling, create narration, narrate_first_token → do nothing, narrate_done → fade narration, show extraction row
// Extract: extract_stream_done(scene) → complete scene bar, extract_stream_done(state) → complete state bar, extract_stream_done(record) → complete record bar
// turn_complete → dismiss extraction row
```

### 6. Update SSE `world_done` handler to no longer call `_setProgressFromPhase`

The `world_done` handler at line 899 should continue to refresh right panel and close the EventSource, but `_setProgressFromPhase` is no longer called there. The existing `_setProgressFromPhase` function should be left as dead code and deprecated in the next iteration.

### 7. Create progress card utility functions in `game-utils.js` (CCYA,ALL)

- `_createProgressCardHTML(phase, expectedMs)` — HTML for card
- `_createRulingCard(expectedMs)` — creates ruling card, returns element, adds to DOM
- `_createNarrationCard(expectedMs)` — creates narration card
- `_fadeOutCard(cardElement)` — fades card out via CSS anim, removes from DOM after anim
- `_showExtractionRow()` — shows extraction row with 3 bars
- `_completeExtractionBar(streamName)` — completes the named bar
- `_dismissExtractionRow()` — dismisses the extraction row with fade

**Interface contracts (only — no method bodies):**

```javascript
function _createProgressCardHTML(phaseName, expectedMs)
// Returns HTML string for a progress card. phaseName: "ruling" | "narration" | "scene" | "state" | "record". expectedMs: number in ms.

function _showProgressCard(cardPhase, expectedMs)
// Creates and inserts a progress card for the given phase. Returns the card element.

function _fadeOutCard(cardElement)
// Animates the card out and removes from DOM.

function _showExtractionRow()
// Shows the extraction row container with 3 horizontal bars (scene, state, record).

function _completeExtractionBar(streamName)
// Marks the bar for `streamName` as complete (fills to 100%, locks solid).

function _dismissExtractionRow()
// Dismisses the entire extraction row as a single unit (fade out animation).
```

### Validation

- `make check` passes
- Ruling card appears on `ruling_start`, valued from 0 to 100% as ruling completes
- Narration card appears at `narrate_start`, fades ruling; fades at `narrate_done`
- Extraction row appears at `narrate_done`, scene bar fills green, state bar fills amber, record bar fills pink
- Turn complete: extraction row dismisses, outcome summary appears
- Phase events `sanitize_start`, `sanitize_done`, `world_start`, `world_done` cause no card updates

---

## Phase 03: CSS — card styling, extraction row

### Depends on

Phase 02

### Context files to load

- `ccya/static/app-shell.css:276-312` → existing `.progress-strip` CSS, `.progress-spinner`, `.progress-label`, `.progress-elapsed`
- `ccya/static/tokens.css:39-44` → `--stage-*` color variables

### What changes

### 1. Add `.progress-card` styles (CCYA,ALL)

Create styled cards: same height as `.progress-strip`, 8px padding, `--stage-*` border-left accent color per phase, `.progress-bar--spin` animation active over the duration of progression.

`.progress-card` progress card CSS rules:
```css
.progress-card {
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--stage-ruling);
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  transition: opacity 0.3s ease-out;
}
```

### 2. Styling per phase variants

Per-phase border-left colors:
- `.progress-card--ruling` → `border-left-color: var(--stage-ruling);`
- `.progress-card--narration` → `border-left-color: var(--stage-narration);`
- `.progress-bar--scene` → `border-left-color: var(--stage-scene);`
- `.progress-bar--state` → `border-left-color: var(--stage-state);`
- `.progress-bar--record` → `border-left-color: var(--stage-storytell);`

### 3. Add `.extraction-row` container styles (CCYA,ALL)

Extraction row: shared container with border, background, padding. Contains 3 extraction bars stacked vertically.

```css
.extraction-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  margin-top: 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  transition: opacity 0.3s ease-out;
}
.extraction-bar {
  /* thin horizontal bar, ~32px height */
  height: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  border-radius: 4px;
  background: var(--stage-scene, 15% rgba);  /* per-phase color at low opacity */
}
```

### 4. Add `.progress-bar` CSS and `.progress-bar-fill` styling (CCYA,ALL)

Native `<progress>` element styled with CSS:
```css
.progress-bar {
  height: 4px;
  width: 60px;
  background: transparent;
  border: 1px solid var(--stage-scene);
  border-radius: 2px;
  overflow: hidden;
}

/* Fill animation (fills left to right, 0→100%) */
.progress-bar-fill {
  height: 100%;
  width: 0%;
  background: var(--stage-scene);
  transition: width 0.5s ease-out;
}
```

### 5. Add @keyframes animation for fading card (CCYA,ALL)

Fade-out for ruling/narration cards and extraction row: `opacity: 1 → 0`.

```css
@keyframes fadeOutCard {
  from { opacity: 1; transform: translateY(-8px); }
  to   { opacity: 0; transform: translateY(-12px); }
}
```

### Validation

- `make check` passes
- Cards appear with correct border-left color per phase
- Extraction row appears as a unified container at `narrate_done`
- Bars fill sequentially in their phase colors
- Cards fade out with correct animation timing

---

## Phase 05: Testing & Validation

### Depends on

Phase 04

### What changes

Manual visual testing via browser against running server. Automated correctness: `make check`.

### Test scenarios

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| 1 | First turn (no events.jsonl) | Fallback expected_ms used |
| 2 | Subsequent turn (1+ history) | Historical avg expected_ms used |
| 3 | Slow LLM response | Card fills >100% → caps at 100% |
| 4 | Fast LLM response | Card fills <100%, fades when phase completes → bar shows partial fill |
| 5 | All phase events fire | ruling→narration→transition→extraction → turn_complete → dismiss |
| 6 | `sanitize_start` fires during ruling | No card change — ruling card continues |
| 7 | `world_done` fires | Panel refresh, EventSource closes — no card impact |

### Validation

- `make check` passes
- All test scenarios pass visually in browser
- No regressions in existing turn pipeline behavior

---

## Phase 04: Documentation

### Depends on

Phase 03

### What changes

### 1. Update repomap.md (CCYA,ALL)

Add new public API entries for the `game-utils.js` functions. Add notes about the new progress card system.

### 2. Update architecture docs (CCYA,ALL)

Update `docs/architecture/step1-narrate.md` with updated `exp_narrate_ms` usage. Update `docs/architecture/step2c-record.md` with per-sub-stream expected_ms.

### 3. Update AGENTS.md (CCYA,ALL)

Add new entries in the "fast prompt testing" section for progress card behavior. Also add progress card as new conversation with progress cards.

---

## Documentation updates

- `docs/architecture/` — Add notes about progress card lifecycle in ruling, narrate, and extraction phase docs
- `docs/repomap.md` — Add new `ccya/static/game-utils.js` functions to the table
- `AGENTS.md` — Update `Fast prompt testing` section to reference progress card behavior for first-turn expectedMs fallback estimates
- `docs/design/turn-progress-cards-design.md` — Update "Open Questions" with closed decisions
- `roadmap/features/F-35-turn-progress-cards.md` — Update `plan` field with link to this plan

## Status: completed
