# Turn Progress Extraction Row — Design Document

> **Status:** implemented
> **Related tickets:**
> - [F-35: Turn progress extraction row](../../roadmap/features/F-35-turn-progress-cards.md)
>
> **Note (2026-07-12):** Ruling and narration progress cards were removed after testing showed these phases complete too quickly to be useful. Only the post-narration extraction row remains.

## Problem

The current turn progress indicator (`<div class="progress-strip" data-phase="...">`) is a single horizontal bar that replaces its label text on every phase event. During a turn — which can take 10–60 seconds — the user sees only one status at a time, cycling through: "Determining outcome…" → "Composing narrative…" → "Refreshing scene…" → "Updating state…" → "Recording Outcome…" → "Saving…" → "Sanitizing state…" → empty for async steps. There is no visual summary of overall progress, no way to estimate remaining time beyond the stale ETA, and no indication that multiple steps have already completed.

## Firm Decisions

1. **Single-phase extraction row.** The turn progress UI shows only the post-narration extraction row. Ruling and narration phases run without dedicated progress UI because they complete too quickly to be meaningful.

2. **Three phase identities.** The progress system uses exactly three phase identities: scene, state, record. No ruling card, no narration card, and no async card; async steps (sanitize, world from `turn.py:760-855`) run silently in the background and get no UI representation.

3. **Roll pill timing.** The roll pill (outcome summary / band result badge) appears when the extraction row fades — exactly like the current flow where `turn_complete` reveals the narrative text.

4. **Extraction row layout.** Three extraction elements are reserved in advance as thin horizontal bars. They share a common visual container. Each fills independently in its own color. They do NOT slide in one-at-a-time — they appear together when narration completes.

5. **Progress bar from elapsed / expected.** Each bar fills smoothly based on `actualElapsed / expectedMs`, capped at 100%. Only one bar is actively filling at a time. Once a bar fills to 100%, it locks solid and the next bar becomes active.

6. **Visual palette from `tokens.css` `--stage-*`.** Extraction phases use the turn-viewer color schema:
   - Scene: `--stage-scene` (#10b981 green)
   - State: `--stage-state` (#f59e0b amber)
   - Record: `--stage-storytell` (#ec4899 pink)

7. **ExpectedMs from history, fallback to initial estimates.** Extraction sub-streams each send their own `expected_ms` from the backend. If no history exists (first turn), use hard-coded fallback estimates to avoid showing progress at 100% prematurely:
   - Scene: 3s, State: 3s, Record: 6s
   - `_avg_event_ms()` takes over after events start accumulating.

8. **Roll pill clarification.** The "roll pill" is the outcome summary / band result badges that appear at the end of a turn (same mechanism as current `turn_complete`). It appears only after the extraction row fades, exactly like the current flow.

## Design Principles

- **Progress visibility.** The user should always see how many steps have completed and which one is in-flight.
- **No visual noise.** Sync events (token streaming, panel updates) do not animate cards.
- **Reuse, don't duplicate.** Spinner animation, label typography, and elapsed-time font inherit from existing `.progress-spinner`, `.progress-label`, `.progress-elapsed` CSS classes where possible.
- **Separation of concern.** Phase cards/bars show pipeline progress. Roll pills are reserved for the turn result. Don't mix them.

## Target State

### Layout

```html
<div class="narrative-block">
  <div class="narrative-echo">...</div>
  <div class="narrative-text">...</div>  <!-- streams during narration -->

  <!-- Extraction row (appears at narrate_done, fills sequentially) -->
  <div class="extraction-row">
    <div class="extraction-bar extraction-bar--scene" data-phase="extract-scene">
      <span class="progress-label">Refreshing scene…</span>
      <span class="progress-metas">
        <span class="progress-eta">~3s avg</span>
        <span class="progress-elapsed">0.0s</span>
      </span>
      <div class="progress-bar progress-bar--scene">
        <div class="progress-bar-fill"></div>
      </div>
    </div>
    <div class="extraction-bar extraction-bar--state" data-phase="extract-state">
      <span class="progress-label">Updating state…</span>
      <span class="progress-metas">
        <span class="progress-eta">~3s avg</span>
        <span class="progress-elapsed">0.0s</span>
      </span>
      <div class="progress-bar progress-bar--state">
        <div class="progress-bar-fill"></div>
      </div>
    </div>
    <div class="extraction-bar extraction-bar--record" data-phase="extract-record">
      <span class="progress-label">Recording Outcome…</span>
      <span class="progress-metas">
        <span class="progress-eta">~6s avg</span>
        <span class="progress-elapsed">0.0s</span>
      </span>
      <div class="progress-bar progress-bar--record">
        <div class="progress-bar-fill"></div>
      </div>
    </div>
  </div>
</div>
```

### Pre-narration

No progress UI is shown during ruling or narration. Narrative text streams normally during narration.

### Post-narration (extraction row) — three bars, all visible

All three extraction bars appear at once when narration completes. No sliding. Each fills sequentially — the user can see each bar fill up one by one until all three are complete.

**At narrate_done:**
- Extraction row appears (opacity 0 → 1, fast fade). All three bars visible, each at 0% fill.

**Scene extraction** (`extract_stream_start(scene)` → `extract_stream_done(scene`):
- Scene bar becomes **active** — spinner starts, progress fills in green (`--stage-scene`).
- State bar remains visible and empty (thin outline).
- Record bar remains visible and empty (thin outline).
- Scene fills to 100%, locks solid green.

**State extraction** (`extract_stream_start(state)` → `extract_stream_done(state)`):
- Scene bar stays at 100% filled (locked).
- State bar becomes **active** — spinner starts, progress fills in amber (`--stage-state`).
- Record bar remains visible and empty (thin outline).
- State fills to 100%, locks solid amber.

**Record extraction** (`extract_stream_start(record)` → `extract_stream_done(record)`):
- Scene stays at 100%, state stays at 100%.
- Record bar becomes **active** — spinner starts, progress fills in pink (`--stage-storytell`).
- Record fills to 100%, locks solid pink. All three complete.

**Turn completion** (`turn_complete`):
- All three extraction bars appear "locked solid" in their respective colors.
- Extraction row fades out (`opacity 0.3s ease-out`).
- All progress bars are gone.
- What remains on screen: narration text (main narrative block), outcome summary (band result badge), and band summary — exactly what shows now at end of turn. Input box with choices sits below.

### Bar animation

**Extraction row appearance:** All three bars appear together (opacity starts at 0, goes to 1 over ~300ms). No stagger — all appear in a batched appearance to avoid layout shifting.

**Active-to-completed transition:** When an extraction bar fills to 100%:
- Animation stops at `progress.value = 1`.
- Border color solidifies.
- Label may get a "✓" or "Completed" adornment.
- Lower opacity or a solid outline for non-active bars — only the active bar is in full fidelity.

**Final dismissal (on `turn_complete`):** The entire extraction row fades as a single unit: `opacity 0.3s ease-out` to reveal the narrative text + band/result summary badges. This is a grouped transition, not staggered individually.

### Progress bar math

- `progress = min(1.0, elapsedSincePhaseStart / expectedMs)` (capped at 1.0).
- `elapsedSincePhaseStart` updated every 250ms per bar via `setInterval`.
- `expectedMs` comes from `_avg_event_ms()` in `events.jsonl` (per sub-stream for extraction).
- Backend: extraction pipeline must emit `expected_ms` per sub-stream (`scene.total_ms`, `state.total_ms`, `record.total_ms`) for accurate first-turn timings.
- If `expectedMs` is 0 (first turn, no history): use hard-coded initial fallback estimates.

### Initial fallback estimates

Used only when no history exists in events.jsonl (first turn):

| Phase      | Fallback estimate |
|------------|-------------------|
| Scene      | 3s                |
| State      | 3s                |
| Record     | 6s                |

Once events.jsonl has history, `_avg_event_ms()` takes over and estimates become dynamic.

### Styling details — Extraction row

- The extraction row is a container (`<div class="extraction-row">`) with a defined row layout.
- All three bars have the same fixed `height` (`32px` minimum) so the row layout is stable.
- Each bar has a background tinted with its stage color at 15% opacity.
- `data-phase="${stream}"` on each node for selection: `.extraction-bar--scene`, `.extraction-bar--state`, `.extraction-bar--record`.
- Label texts carry the same labels that the current strip uses: "Refreshing scene…", "Updating state…", "Recording Outcome…".
- Elapsed time in monospace, right-aligned.

## Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| `_setProgressFromPhase` (game-utils.js:367) | Mutates the strip's label/eta on every phase event. | Removed. Replaced by extraction row functions: `_showExtractionRow()`, `_activateExtractionBar()`, `_completeExtractionBar()`, `_dismissExtractionRow()`. |
| `_progressStripHTML` / strip CSS (app-shell.css:276-312) | Existing DOM and CSS for the single horizontal progress strip. | Removed. `.progress-label`, `.progress-metas`, `.progress-elapsed` CSS reused in extraction bars. The strip itself is gone. |
| `progress-strip[data-phase="extract_retry"]` (app-shell.css:312) | `extract_retry` is dead code (no backend emits it), but CSS rule exists. | Removed along with the rest of `.progress-strip` rules. |
| `_bindProgressTimer` (game-utils.js:439-446) | Single `setInterval` shared across phases for the strip. | Removed. Each extraction bar manages its own `setInterval` based elapsed timer independently. |
| SSE handler at game.js:878-899 | Handles `phase`, `turn_complete`, `turn_error`, `panel_update`. | Same `EventSource` setup; new logic inside. `narrate_done` `stopDisplayDrain()` still applies and shows the extraction row. |
| "Narrative block" structure | Currently: `narrative-echo` → `narrative-text` → `progress-strip`. | `narrative-echo` → `narrative-text` → extraction row. Narrative text position is unchanged by extraction row. |
| Turn log overlay | Turn log shows past turns. Should it show progress bars? | **Out of scope.** Extraction bars are live-only and disappear on turn completion. |

## Risks

1. **Risk:** Prolonged narration phase makes the narrative block feel visually busy with a card while text streams. **Mitigation:** Ruling card fades at `narrate_start` (midway through). Narration card sits thin above text, does not cover text. Extraction row only appears after narration is done.

2. **Risk:** Extraction sub-streams vary wildly in duration (100ms–5s). Backend sends `expected_ms` = 0. **Mitigation:** Progress bar clamps to 100%. If `expected_ms` is 0, bar appears "completed" immediately (progress = 1.0, filled bar) with the active roll.

3. **Risk:** Individual `expected_ms` requires backend changes to extraction pipeline. **Mitigation:** Separate calcs are confirmed as decision #1.

4. **Risk:** Extraction row appears/bars appear together. If one bar processes instantly vs. another is really fast, does the row look awkward (one instant fill, two empty)? **Mitigation:** Non-active bars are rendered with reduced opacity / placeholder styling so fast fills look like completion and not an oversight.

5. **Risk:** `world_start` and `world_done` events leak through. **Mitigation:** These events are filtered entirely from the progress-stack handler — no card or bar is created for `sanitize_start`, `sanitize_done`, `world_start`, or `world_done`. They continue to run silently as they did before.

## Rejected Alternatives

1. **Ruling + Narration = 1 card.** Rejected: user wants ruling to have "the same kind of animation and better color" as a distinct visual experience. Two separate ruling card at a time is the design.

2. **Async card with green fill.** Rejected: 3% marginal UX gain vs. UI complexity. User said "We don't need async either."

3. **Roll pill inside ruling card.** Rejected: user explicitly said "We definitely don't want to show the roll before the turn is over."

4. **Div-based CSS progress bar (no `<progress>` element).** Rejected: `<progress>` is semantically `aria`-correct, built-in, and cross-browser. Styled with CSS `--stage-*` colors instead.

5. **Extraction bars sliding in one-at-a-time.** Rejected: user explicitly said "three rows that are like reserved and then they fill up individually." No sliding. All appearance together that reserves the row container's sizing.

6. **Staggered extraction bar dismissal.** Rejected: user said "when the last bar which is record is filled then it will fade away and we'll get the outcome summary." The entire row dismisses as one unit, not individually staggered.

## End state after turn completion

At end of turn, what remains visible in the narrative column:
1. Narrative text (the full narration from the turn)
2. Outcome summary / band result badge (the "roll pill" the user calls it)
3. Band summary

The input box with choices sits below. No progress cards, no extraction row — everything transient is gone. This is identical to the current end-of-turn state.

## Deferred Items

- **Ruling/narration progress UI.** If future iterations want to reintroduce cards for ruling or narration, that's a follow-up design. Removed because these phases complete too quickly to be useful.
- **Bar color customization (post-MVP).** Custom color mappings (e.g., "red for error", "gray for skipped") deferred to follow-up. Current design uses the existing `--stage-*` palette.

## Open Questions

- **[CLOSED]** Extraction row layout: shared container with border/background around all three bars. The extraction row sits inside a `<div class="extraction-row">` with its own styling (border, background, padding) so it appears and fades as a unified panel.
- **[CLOSED]** Waiting bars: all three remain visible at all times with empty progress bars when waiting. Confirmed by user — "all three should be present, we should be able to see each one fill up until all three are filled."
- **[CLOSED]** End-of-turn after turn is over. What remains after the turn is done: the narration text (main block), outcome summary, and band summary — exactly what shows now. All extraction bars are gone. The input box with choices sits below. Nothing else remains.

## What an Implementer Needs to Read

**Frontend:**
- `ccya/static/game-utils.js` — `_showExtractionRow()`, `_activateExtractionBar()`, `_completeExtractionBar()`, `_dismissExtractionRow()`.
- `ccya/static/game.js` — `submitTurn()`, `EventSource` phase handlers, `_turnCancel()`.
- `ccya/static/app.src.css` — extraction row styles (source for the loaded `app.css`).
- `ccya/static/app-shell.css` — mirror of the above styles (kept in sync with `app.src.css`).
- `ccya/static/tokens.css` — `--stage-*` color variables (line 39-44).

**Backend (referential):**
- `ccya/engine/ruling.py:_ruling_phase()` — `ruling_start`, `ruling_done`. No UI consumed.
- `ccya/engine/turn.py:_narrate_phase()` — `narrate_start`, `narrate_done`. Triggers extraction row at `narrate_done`.
- `ccya/engine/extraction/pipeline.py:_run_extraction_stream()` — `extract_stream_start` / `extract_stream_done` per stream. Source of per-stream timing.
- `ccya/engine/extraction/utils.py:_avg_event_ms()` — reads last 5 entries from `events.jsonl` per phase field.
