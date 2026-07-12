# Turn Progress Stacked Cards — Design Document

> **Status:** implemented
> **Related tickets:**
> - [F-35: Stacked turn progress-bar UI with per-phase cards](../../roadmap/features/F-35-turn-progress-cards.md)

## Problem

The current turn progress indicator (`<div class="progress-strip" data-phase="...">`) is a single horizontal bar that replaces its label text on every phase event. During a turn — which can take 10–60 seconds — the user sees only one status at a time, cycling through: "Determining outcome…" → "Composing narrative…" → "Refreshing scene…" → "Updating state…" → "Recording Outcome…" → "Saving…" → "Sanitizing state…" → empty for async steps. There is no visual summary of overall progress, no way to estimate remaining time beyond the stale ETA, and no indication that multiple steps have already completed.

## Firm Decisions

1. **Two-phase layout.** The turn progress UI has two distinct phases:
   - **Pre-narration (one-at-a-time):** Ruling card → Narration card. Each appears, fills, disappears. Exactly as the current strip works, but with individual animated cards.
   - **Post-narration (extraction row):** Scene, state, record bars shown together in a single spatial area. All three appear together; each fills independently in its own color as it processes. When the last bar (record) fills, the extraction row disappears and the roll pill (outcome summary badges/band result) appears — same behavior as now.

2. **Five phase identities.** The progress system uses exactly five phase identities: ruling, narration, scene, state, record. No async card; async steps (sanitize, world from `turn.py:760-855`) run silently in the background and get no UI representation.

3. **Roll pill timing.** The roll pill (outcome summary / band result badge) appears when the extraction row fades — exactly like the current flow where `turn_complete` reveals the narrative text. The roll pill is never shown inside a card.

4. **Bits extraction row cards.** Three extraction elements are reserved in advance as thin horizontal bars (a "progress row", not stacked cards). They share a common visual container. Each fills independently in its own color. They do NOT slide in one-at-a-time — they appear together when narration completes.

5. **Progress bar from elapsed / expected.** Each bar fills smoothly based on `actualElapsed / expectedMs`, capped at 100%. Only one bar is actively filling at a time. Once a bar fills to 100%, it locks solid and the next bar becomes active.

6. **Visual palette from `tokens.css` `--stage-*`.** Every phase uses the turn-viewer color schema:
   - Ruling: `--stage-ruling` (#8b5cf6 violet)
   - Narration: `--stage-narrate` (#3b82f6 blue)
   - Scene: `--stage-scene` (#10b981 green)
   - State: `--stage-state` (#f59e0b amber)
   - Record: `--stage-storytell` (#ec4899 pink)

7. **Ruling card fades when narration begins.** The ruling card fades out at `narrate_start` (not at `narrate_done`). The narration card fades at `narrate_done`. This gives ruling the visual distinction the user wants while keeping the "pre-narration" behavior.

8. **ExpectedMs from history, fallback to initial estimates.** Ruling/narration `expectedMs` comes from `_avg_event_ms()` in `events.jsonl` (last 5 entries). Extraction sub-streams each send their own `expected_ms` from the backend. If no history exists (first turn), use hard-coded fallback estimates to avoid showing progress at 100% prematurely:
   - Ruling: 3s, Narration: 8s, Scene: 3s, State: 3s, Record: 6s
   - `_avg_event_ms()` takes over after events start accumulating.

9. **Roll pill clarification.** The "roll pill" is the outcome summary / band result badges that appear at the end of a turn (same mechanism as current `turn_complete`). It is never shown inside a card — it appears only after the extraction row fades, exactly like the current flow.

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
  <div class="progress-stack">
    <!-- Phase 1: Ruling (appears, fills, fades at narrate_start) -->
    <div class="progress-card progress-card--ruling" data-phase="ruling">
      <span class="progress-spinner"></span>
      <span class="progress-label">Determining outcome…</span>
      <progress class="progress-bar" value="1" max="1"></progress>
      <span class="progress-elapsed">3.2s</span>
    </div>

    <!-- Phase 2: Narration (appears, fills, fades at narrate_done) -->
    <div class="progress-card progress-card--narrate" data-phase="narrate">
      <span class="progress-spinner"></span>
      <span class="progress-label">Composing narrative…</span>
      <progress class="progress-bar" value="0.5" max="1"></progress>
      <span class="progress-elapsed">2.1s</span>
    </div>

    <!-- Phase 3-5: Extraction row (all three appear together at narrate_done, fill sequentially) -->
    <div class="extraction-row">
      <div class="extraction-bar extraction-bar--scene" data-phase="extract-scene">
        <span class="progress-spinner"></span>
        <span class="progress-label">Refreshing scene…</span>
        <progress class="progress-bar" value="0" max="1"></progress>
        <span class="progress-elapsed">0.0s</span>
      </div>
      <div class="extraction-bar extraction-bar--state" data-phase="extract-state">
        <span class="progress-spinner"></span>
        <span class="progress-label">Updating state…</span>
        <progress class="progress-bar" value="0" max="1"></progress>
        <span class="progress-elapsed">0.0s</span>
      </div>
      <div class="extraction-bar extraction-bar--record" data-phase="extract-record">
        <span class="progress-spinner"></span>
        <span class="progress-label">Recording Outcome…</span>
        <progress class="progress-bar" value="0" max="1"></progress>
        <span class="progress-elapsed">0.0s</span>
      </div>
    </div>
  </div>
</div>
```

### Phase 1: Pre-narration (ruling + narration) — one-at-a-time

These behave like the current progress strip: one visible card at a time, each fills, then disappears. Narration uses the new animated card style and `--stage-narrate` blue color (same timing, different visual).

**Ruling** (`ruling_start` → `ruling_done`):
- Card appears, violet theme (`--stage-ruling`), spinner active, progress fills.
- No roll pill shown.
- **Card fades out at `narrate_start`** (when narration begins).

**Narration** (`narrate_start` → `narrate_done`):
- Card appears below ruling, blue theme (`--stage-narrate`), spinner active.
- Progress fills at `elapsed / expectedMs`. First token (`narrate_first_token`) does NOT fill the card — it just updates the label "Composing narrative…".
- Narrative text streams (`data-narrative-text`) below the card.
- **Card fades out at `narrate_done`**.

### Phase 2: Post-narration (extraction row) — three bars, all visible

All three extraction bars appear at once when narration completes. No sliding. Each fills sequentially — the user can see each bar fill up one by one until all three are complete.

**At narrate_done:**
- Ruling card fades. Narration card fades.
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
- All progress cards and bars are gone.
- What remains on screen: narration text (main narrative block), outcome summary (band result badge), and band summary — exactly what shows now at end of turn. Input box with choices sits below.

### Card and bar animation

**Card appearance (ruling / narration):** Each card appears with `opacity: 0 → 1` (no sliding — just fade-in) over 200ms ease-out.

**Card disappearance (ruling / narration):**
- Ruling card fades at `narrate_start` using `opacity: 1 → 0` + `transform: translateY(-12px)` over 300ms ease-out.
- Narration card fades at `narrate_done` using the same transition.

**Extraction row appearance:** fadeIn animation where all three bars appear together (opacity starts at 0, goes to 1 over ~300ms). No stagger — all appear in a batched appearance to conserve the not push layout about layout shifting.

**Active-to-completed transition:** When an extraction bar fills to 100%:
- Animation stops at `progress.value = 1`.
- Spinner hides.
- Border color solidifies.
- Label may get a "✓" or "Completed" adornment.
- Lower opacity or a solid outline for non-active bars — only the active card is in full fidelity.

**Final dismissal (on `turn_complete`):** The entire extraction row fades as a single unit: `opacity 0.3s ease-out` to reveal the narrative text + band/result summary badges. This is a grouped transition, not staggered individually.

### Progress bar math

- `progress = min(1.0, elapsedSincePhaseStart / expectedMs)` (capped at 1.0).
- `elapsedSincePhaseStart` updated every 250ms per card/box via `setInterval`.
- `expectedMs` comes from `_avg_event_ms()` in `events.jsonl` (last 5 entries per phase for ruling/narration, per sub-stream for extraction).
- Backend: extraction pipeline must emit `expected_ms` per sub-stream (`scene.total_ms`, `state.total_ms`, `record.total_ms`) for accurate first-turn timings.
- If `expectedMs` is 0 (first turn, no history): use hard-coded initial fallback estimates.

### Initial fallback estimates

Used only when no history exists in events.jsonl (first turn):

| Phase      | Fallback estimate |
|------------|-------------------|
| Ruling     | 3s                |
| Narration  | 8s                |
| Scene      | 3s                |
| State      | 3s                |
| Record     | 2s                |

Once events.jsonl has history, `_avg_event_ms()` takes over and estimates become dynamic.

### Styling details — Extraction row

- The extraction row is a container (`<div class="extraction-row">`) respecting a defined row. Rather than stacked, each bar is a thin row.
- All three bars have the same fixed `height` (e.g. `32px` minimum) so the row layout is ready on a thin single layout.
- Each bar has `background: var(--stage-*文化交流) 15% rgba` to the passive bar has `--stage-* 15% rgba`. Active bars have `--stage-* 50% rgba`. Completed bars have `--stage-* 100% rgba`.
- `data-phase="${stream}"` on each node for selection: `.extraction-bar--scene`, `.extraction-bar--state`, `.extraction-bar--record`.
- Label texts carry the same labels that the current strip uses: "Refreshing scene…", "Updating state…", "Recording Outcome…".
- Elapsed time in monospace, right-aligned.

## Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| `_setProgressFromPhase` (game-utils.js:367) | Mutates the strip's label/eta on every phase event. | Replaced by `_createCard()` (ruling/narration) → `_completeCard()` → `_fadeOutCard()` and extraction row functions: `_showExtractionRow()`, `_activateExtractionBar()`, `_completeExtractionBar()`, `_dismissExtractionRow()`. Old function kept as dead code until strip UI is verified unused. |
| `_progressStripHTML` / strip CSS (app-shell.css:276-312) | Existing DOM and CSS for the single horizontal progress strip. | Entirely replaced. `.progress-spinner`, `.progress-label`, `.progress-elapsed` CSS reused. The strip itself is removed. Extraction row gets its own CSS classes. |
| `progress-strip[data-phase="extract_retry"]` (app-shell.css:312) | `extract_retry` is dead code (no backend emits it), but CSS rule exists. | Leave rule as harmless dead code. |
| `_bindProgressTimer` (game-utils.js:439-446) | Single `setInterval` shared across phases for the strip. | Each card manages its own `setInterval` based elapsed timer independently. |
| SSE handler at game.js:878-899 | Handles `phase`, `turn_complete`, `turn_error`, `panel_update`. | Same `EventSource` setup; new logic inside. `narrate_done` `stopDisplayDrain()` still applies. |
| "Narrative block" structure | Currently: `narrative-echo` → `narrative-text` → `progress-strip`. | `narrative-echo` → `narrative-text` → `progress-stack` (with ruling card + narration card + extraction row). Narrative text position is unchanged by extraction row. |
| Turn log overlay | Turn log shows past turns. Should it show progress cards? | **Out of scope.** Cards/bar are live-only and disappear on turn completion. |

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

- **Roll pill migration to ruling card position.** If future iterations want the roll pill displayed inside the ruling card (e.g., after the ruling is resolved while the narrator card is still chaining), that's a follow-up design.
- **Card color customization (post-MVP).** Custom color mappings (e.g., "red for error", "gray for skipped") deferred to follow-up. Current design uses the existing `--stage-*` palette.

## Open Questions

- **[CLOSED]** Extraction row layout: shared container with border/background around all three bars. The extraction row sits inside a `<div class="extraction-row">` with its own styling (border, background, padding) so it appears and fades as a unified panel.
- **[CLOSED]** Waiting bars: all three remain visible at all times with empty progress bars when waiting. Confirmed by user — "all three should be present, we should be able to see each one fill up until all three are filled."
- **[CLOSED]** End-of-turn after turn is over. What remains after the turn is done: the narration text (main block), outcome summary, and band summary — exactly what shows now. All progress cards and bars are gone. The input box with choices sits below. Nothing else remains.

## What an Implementer Needs to Read

**Frontend:**
- `ccya/static/game-utils.js` — `_progressStripHTML()` (line 263), `_setProgressFromPhase()` (line 367), `_clearProgressStrip()` (line 431), `_bindProgressTimer()` (line 439). New functions: `_createRulingCard()`, `_createNarrationCard()`, `_fadeInExtractionBar()`, `_fillExtractionBar()`, `_dismissExtractionRow()`.
- `ccya/static/game.js` — `submitTurn()` (line 785+), `EventSource` handlers (line 878-899), `_turnCancel` (line 810).
- `ccya/static/app-shell.css` — `.progress-strip` (line 276-312), `@keyframes spin`, mobile media query (line 1626).
- `ccya/static/tokens.css` — `--stage-*` color variables (line 39-44).

**Backend (referential):**
- `ccya/engine/ruling.py:_ruling_phase()` — `ruling_start`, `ruling_done`. `exp_ruling_ms` source.
- `ccya/engine/turn.py:_narrate_phase()` — `narrate_start`, `narrate_done`. Source of `exp_narrate_ms`.
- `ccya/engine/extraction/pipeline.py:_run_extraction_stream()` — `extract_stream_start` / `extract_stream_done` per stream. Source of per-stream timing.
- `ccya/engine/extraction/utils.py:_avg_event_ms()` — reads last 5 entries from `events.jsonl` per phase field.
