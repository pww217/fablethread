# Extraction stream labels, debug panel metrics, and compaction label

## Status
`completed`

## Phases

3 phases covering: (1) per-stream extraction phase signals + UI labels, (2) debug panel metrics simplification, (3) compaction label change.

## Objective

Improve the turn pipeline UX and debug visibility: show per-extraction-stream labels in the progress pill, simplify the debug panel metrics table by removing redundant TTFT columns (keeping only narration's TTFT/Total split), and change the compaction phase label from "Saving…" to "Cleaning up…".

## Non-goals

- Do not change the turn viewer (tv.py / tv_mirror.py) — only the debug panel.
- Do not change the in-turn metrics row displayed after turn_complete (`_formatMetricsRow`).
- Do not add new config keys or models.
- Do not change extraction pipeline logic, ordering, or behavior.

## Firm decisions

1. Extraction streams (scene, state, progress) each get their own phase signal (`extract_stream_start` / `extract_stream_done`) emitted from `_run_extraction_pipeline` in `engine/extraction.py`.
2. The phase column header in the debug panel changes from "pipe" to show stream names matching the new phase signals.
3. TTFT column is removed from all streams except narration. Narration shows a combined "TTFT / Total" cell.
4. The progress pill label in `_setProgressFromPhase` is updated for `extract_stream_start`/`extract_stream_done` phases.
5. The `compact_done` phase label changes from "Saving…" to "Cleaning up…".

## Conflicts and overlap

None. These changes touch distinct files: `extraction.py`, `_debug.html`, `metrics.py`, `index.html`. No model or config changes.

## Implementation — Phase 1: Per-stream extraction phase signals + UI labels

### Context files to load
- `ccya/engine/extraction.py` — `_run_extraction_pipeline`, `_call_stream`
- `ccya/engine/turn.py` — `run_turn`, `run_turn_retry` (extraction pipeline calls)
- `ccya/templates/index.html` — `_setProgressFromPhase`, `_progressStripHTML`

### Detailed steps

#### Step 1.1 — Add per-stream phase signals to `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** Modify `_run_extraction_pipeline` to accept an optional `yield_fn` callback parameter and emit phase signals for each stream. The function is called from `run_turn` and `run_turn_retry` which pass a yield function.

**Why:** The progress pill needs to show which extraction stream is currently running. Currently it only shows "Updating game state…" for the entire extraction block.

**Code Snippet:**

```python
# In _run_extraction_pipeline signature, add yield_fn parameter:
async def _run_extraction_pipeline(
    env, state, narration, *, rules_outcome=None, intent=None, config, trace_id, turn_no,
    deescalate=0.0, quest_ages=None, recent_turns=None,
    yield_fn=None,
) -> tuple[StateDelta, list[str], str, dict, ProgressExtractResult, SceneExtractResult]:
```

Then in the function body, after each stream completes, emit phase signals:

```python
# Before calling scene stream:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_start", "stream": "scene"}))

# ... scene stream call ...

# After scene stream completes:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_done", "stream": "scene"}))

# Before calling state stream:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_start", "stream": "state"}))

# ... state stream call ...

# After state stream completes:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_done", "stream": "state"}))

# Before calling progress stream:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_start", "stream": "progress"}))

# ... progress stream call ...

# After progress stream completes:
if yield_fn:
    yield_fn(("phase", {"phase": "extract_stream_done", "stream": "progress"}))
```

**Validation:** Run `make check` to verify no type errors. The `yield_fn` is optional so existing callers that don't pass it still work.

#### Step 1.2 — Wire yield_fn from run_turn and run_turn_retry

**File:** `ccya/engine/turn.py`

**What:** Pass `yield_fn` to `_run_extraction_pipeline` in both `run_turn` and `run_turn_retry`.

**Why:** The phase signals need to flow through to the SSE client.

**Code Snippet:**

In `run_turn`, find the call to `_run_extraction_pipeline` and add `yield_fn=yield`:

```python
delta, actions, outcome_summary, extraction_event, progress_result, scene_result = (
    await _run_extraction_pipeline(
        env, state, narrative,
        rules_outcome=outcome,
        intent=intent,
        config=config,
        trace_id=trace_id,
        turn_no=turn_no,
        deescalate=deescalate,
        quest_ages=quest_ages,
        recent_turns=recent_turns,
        yield_fn=yield,
    )
)
```

Same change in `run_turn_retry`.

**Validation:** The `yield` keyword is a valid callable in async generators — it can be passed as a function reference.

#### Step 1.3 — Update `_setProgressFromPhase` in index.html

**File:** `ccya/templates/index.html`

**What:** Add handlers for `extract_stream_start` and `extract_stream_done` phases in `_setProgressFromPhase`.

**Why:** The progress pill needs to show per-stream labels during extraction.

**Code Snippet:**

In `_setProgressFromPhase`, add after the existing `extract_start`/`extract_done` handlers:

```javascript
} else if (p === 'extract_stream_start') {
    const stream = (payload && payload.stream) || '';
    if (stream === 'scene') {
        label.textContent = 'Refreshing scene…';
    } else if (stream === 'state') {
        label.textContent = 'Updating state…';
    } else if (stream === 'progress') {
        label.textContent = 'Writing the next page…';
    } else {
        label.textContent = 'Updating game state…';
    }
    strip._phaseStart = Date.now();
    if (eta) eta.textContent = '';
} else if (p === 'extract_stream_done') {
    // Keep current label, just reset ETA
    if (eta) eta.textContent = '';
}
```

Also update `compact_done`:

```javascript
} else if (p === 'compact_done') {
    label.textContent = 'Cleaning up…';
    if (eta) eta.textContent = '';
}
```

**Validation:** The phase names match what's emitted from the engine. The timer continues from the existing `_phaseStart` set on `extract_stream_start`.

## Implementation — Phase 2: Debug panel metrics simplification

### Context files to load
- `ccya/templates/_debug.html` — debug panel template
- `ccya/server/metrics.py` — `_recent_turn_metrics`

### Detailed steps

#### Step 2.1 — Update `_debug.html` template

**File:** `ccya/templates/_debug.html`

**What:** Remove the TTFT column from the debug panel table. Change narration's cell to show "TTFT / Total" in a single cell. Update column headers.

**Why:** TTFT is only meaningful for narration (streaming). Other streams are non-streaming JSON calls where TTFT is the same as total time.

**Code Snippet:**

Change the table header from:
```html
<thead>
    <tr>
        <th style="text-align:left">pipe</th>
        <th>ttft</th>
        <th>tt</th>
        <th>tok</th>
    </tr>
</thead>
```

To:
```html
<thead>
    <tr>
        <th style="text-align:left">pipe</th>
        <th>narrate ttft/total</th>
        <th>tt</th>
        <th>tok</th>
    </tr>
</thead>
```

Change the narration row from:
```html
<tr class="{% if t.has_rejections %}debug-turn-row-warn{% endif %}">
    <td style="text-align:left">N</td>
    <td>{{ t.streams.N_ttft }}</td>
    <td>{{ t.streams.N_tt }}</td>
    <td>{{ t.streams.N_tok }}</td>
</tr>
```

To:
```html
<tr class="{% if t.has_rejections %}debug-turn-row-warn{% endif %}">
    <td style="text-align:left">N</td>
    <td>{{ t.streams.N_ttft }} / {{ t.streams.N_tt }}</td>
    <td>—</td>
    <td>{{ t.streams.N_tok }}</td>
</tr>
```

Remove the TTFT column from scene, state, and progress rows:
```html
<tr class="{% if t.has_rejections %}debug-turn-row-warn{% endif %}">
    <td style="text-align:left">Sc</td>
    <td>{{ t.streams.Sc_tt }}</td>
    <td>{{ t.streams.Sc_tok }}</td>
</tr>
<tr class="{% if t.has_rejections %}debug-turn-row-warn{% endif %}">
    <td style="text-align:left">St</td>
    <td>{{ t.streams.St_tt }}</td>
    <td>{{ t.streams.St_tok }}</td>
</tr>
<tr class="{% if t.has_rejections %}debug-turn-row-warn{% endif %}">
    <td style="text-align:left">P</td>
    <td>{{ t.streams.P_tt }}</td>
    <td>{{ t.streams.P_tok }}</td>
</tr>
```

Update the Total row similarly:
```html
<tr class="debug-turn-total">
    <td style="text-align:left;font-weight:600">Total</td>
    <td>—</td>
    <td>{{ t.total_tt }}</td>
    <td>{{ t.total_tok }}</td>
</tr>
```

**Why:** The table now has 3 columns instead of 4. Narration shows its TTFT/Total split in one cell. Other streams show only total time.

#### Step 2.2 — Simplify `_recent_turn_metrics` in metrics.py

**File:** `ccya/server/metrics.py`

**What:** Remove the TTFT-related fields from the returned dict. Keep only what the template needs.

**Why:** Clean up unused data. The template no longer references `*_ttft` fields except for narration.

**Code Snippet:**

In the `streams` dict, remove all `*_ttft` keys and keep only `*_tt` and `*_tok`:

```python
"streams": {
    "R_tt": _fmt_ms_seconds(rules_ev.get("total_ms")),
    "R_tok": _tok(rules_ev.get("tokens_in"), rules_ev.get("tokens_out")),
    "N_ttft": _fmt_ms_seconds(narr.get("first_token_ms")),
    "N_tt": _fmt_ms_seconds(narr.get("total_ms")),
    "N_tok": _tok(n_in, n_out),
    "Sc_tt": _fmt_ms_seconds(raw_streams["scene"]["ms"]) if not raw_streams["scene"]["skipped"] else "\u2014",
    "Sc_tok": _tok(raw_streams["scene"]["tokens_in"], raw_streams["scene"]["tokens_out"]) if not raw_streams["scene"]["skipped"] else "\u2014",
    "St_tt": _fmt_ms_seconds(raw_streams["state"]["ms"]) if not raw_streams["state"]["skipped"] else "\u2014",
    "St_tok": _tok(raw_streams["state"]["tokens_in"], raw_streams["state"]["tokens_out"]) if not raw_streams["state"]["skipped"] else "\u2014",
    "P_tt": _fmt_ms_seconds(raw_streams["progress"]["ms"]) if not raw_streams["progress"]["skipped"] else "\u2014",
    "P_tok": _tok(raw_streams["progress"]["tokens_in"], raw_streams["progress"]["tokens_out"]) if not raw_streams["progress"]["skipped"] else "\u2014",
},
```

Remove `total_ttft`, `total_ttft_ms`, and `first_s` from the row dict. Remove `_ttft` helper function if unused elsewhere.

**Why:** The template no longer references these fields. Keep `N_ttft` because the template shows narration's TTFT.

**Validation:** Run `make check` to verify no references to removed fields.

## Implementation — Phase 3: Compaction label change

### Context files to load
- `ccya/templates/index.html` — `_setProgressFromPhase`

### Detailed steps

#### Step 3.1 — Change compact_done label

**File:** `ccya/templates/index.html`

**What:** In `_setProgressFromPhase`, change the `compact_done` label from "Saving…" to "Cleaning up…".

**Why:** The user wants a more descriptive label for the compaction phase.

**Code Snippet:**

Already covered in Phase 1, Step 1.3 above:

```javascript
} else if (p === 'compact_done') {
    label.textContent = 'Cleaning up…';
    if (eta) eta.textContent = '';
}
```

## Ambiguities requiring resolution before execution

1. **Should the `extract_stream_start`/`extract_stream_done` phase signals also appear in the turn viewer?** — Currently the plan only affects the main game UI progress pill. The turn viewer shows the extraction as a single block. If the user wants per-stream visibility in the turn viewer, that's a separate enhancement.

2. **The debug panel table now has 3 columns for non-rules rows but 4 for the narration row (TTFT/Total counts as 1 cell).** — The narration row's "TTFT/Total" cell spans the visual width of two columns. This is intentional and matches the user's request for "TTFT/Total time in one column".

3. **Should the total row show a combined total time?** — Currently it shows `total_tt` which is the sum of all stream times. This is preserved as-is.
