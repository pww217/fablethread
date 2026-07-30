---
title: "Pre-Stream Progress Bar (Ruling + Narration Ttft)"
status: done
urgency: 3
size: medium
created: 2026-07-26
ticket_id: I-44
labels:
  - ui
  - progress
  - turn-pipeline
design:
plan: plans/I-44-pre-stream-progress-bar-plan.md
pr:
  url:
  branch:
---

## Problem

The in-turn progress UI only shows the three extraction bars (scene / state / record). The user has no visual feedback for the two preceding phases — **ruling** (which can be 2-6+ seconds) and **narration time-to-first-token** (typically 1-3 seconds). The user sees a frozen "empty" turn block until the first narration token streams in, then the extraction row appears.

Both phases are real work — ruling does a dice-check / outcome-band LLM call, narration is waiting on the LLM to begin streaming. A progress bar that covers the combined pre-stream latency would give the user a real signal that the turn is making progress, using the same visual language as the extraction bars below it.

## Decisions

1. **One blue bar, not two.** Single inline bar covering the combined ruling + narrate-TTFT window. Uses `--stage-narrate` (#3b82f6) — the same blue used by the narrate row in the turn viewer.
2. **Bar lifecycle:**
   - Show at `ruling_start` (start filling).
   - Continue filling through narrate setup and LLM warm-up.
   - Fill to 100% on the first narration token (`narrate_first_token` phase event — already emitted by the backend).
   - Dismiss when the extraction row appears at `narrate_done`.
3. **Label:** `Determining Outcome…` (matches the conversational tone of the extraction labels).
4. **Expected duration metric:** same model as the extraction bars — fixed fallback for turn 1, then `_avg_event_ms(...)` over the last 5 turns. We sum two existing metrics:
   - `ruling.total_ms` (already tracked per turn in `events.jsonl`)
   - `narrate.first_token_ms` (already tracked per turn under `event.narrate.first_token_ms`)
   - Backend computes `pre_stream_expected_ms = ruling_avg + ttft_avg` and ships it on the `ruling_start` phase event.
5. **Client fallback** when `pre_stream_expected_ms == 0` (turn 1, no history): use 5000ms (covers a typical ruling + TTFT cycle).
6. **Layout:** standalone single-bar block, not part of the 3-row extraction table. Lives in the same per-turn block, inserted before the extraction row.

## Validation

- Turn 1: bar appears with "Determining Outcome…" label, ~5s fallback expected, fills smoothly, completes on first token, dismisses when extraction row appears.
- Turn 2+: bar uses sum of last-5-turn averages for ruling + first_token_ms.
- Bar dismisses on `turn_error` and on `es.onerror` (defensive — no stale state).
- Bar color matches `--stage-narrate` blue used elsewhere in the UI.
