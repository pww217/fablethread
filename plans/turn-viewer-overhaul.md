# Turn Viewer Overhaul

## Status
`reviewed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Pipeline spine layout | Replace connector cards with inline input blocks; surface total turn latency; remove scope from top-level |
| 02 | State diff right panel | Two-column layout; compute and expose per-turn state diff; surface all errors/rejections/retries inline |
| 03 | Compaction rows | Emit compaction events to events.jsonl; render compaction rows in turn viewer; guard metrics.py |
| 04 | Polish and cleanup | Filter bar improvements; j/k nav; scroll-lock on live update; prune dead connector-card code |

## Objective
The turn viewer is the primary debugging surface for understanding what the engine did on each turn. The current layout has two problems: (1) connector cards between stages duplicate upstream output for every downstream consumer, making the pipeline hard to read; (2) the right side of the screen is empty — there is no state diff, no compaction visibility, and no structured error surface. This plan restructures the viewer into a two-column layout (pipeline spine left, state diff right), replaces the connector-card model with inline "received from" blocks inside each stage, surfaces all failure modes (retries, rejections, Pydantic validation errors, LLM errors) prominently, adds a total turn latency display, and makes compaction runs visible as first-class rows.

## Non-goals
- Do not add a new route or page — all changes are within `/turn_viewer` and its supporting files.
- Do not modify prompts, engine logic, or state application — read-only surface only.
- Do not replicate the scope/active-domains display prominently — it may be removed in a future plan; do not invest in it.
- Do not add narration full text to the home view of a turn — full text remains behind the Output tab.
- Do not add streaming/live-highlight of mid-turn phases — static per-turn rows only.

## Review findings summary
- 3 BLOCKERs fixed: CSS variables don't exist in the codebase (Phase 02), keyboard nav element IDs don't match template (Phase 04), metrics.py guard not explicit enough (Phase 03).
- 5 WARNINGs/SUGGESTIONs noted but not blocking.
- All file paths, function names, and symbol references verified correct.
- No phases implemented.

---

## Implementation — Phase 01: Pipeline spine layout

### Files to pull for context
- `ccya/templates/_turn_viewer.html`
- `ccya/server/tv.py`
- `ccya/server/tv_mirror.py`
- `ccya/static/app.src.css` (turn viewer section)

### Detailed steps

#### Step 1.1 — Add total turn latency to row dict

**File:** `ccya/server/tv.py`

**What:** `_turn_viewer_data` already computes `total_tt_ms` at lines 251-255 but only formats it as `total_tt`. Add `total_tt_ms_raw: int` to the row dict so the template can use it for percentage-width bars, and ensure `total_tt` (formatted string) is always present. Also add `row_kind: "turn"` to distinguish turn rows from compaction rows (Phase 03).

**Why:** The latency waterfall in Phase 01 needs raw ms values per stream and a total to compute bar widths. `row_kind` is needed for the template to branch between turn and compaction row rendering.

**Code Snippet**
```python
# In the rows.append(...) block at line 352, add alongside total_tt at line 364:
"row_kind": "turn",
"total_tt_ms_raw": int(total_tt_ms),
```

Also add `ms_raw` for each stream in the streams dict — add after line 228 where the stream dict is populated:
```python
# After line 228 in the per-stream block, after ms_val is resolved:
streams[sd.key]["ms_raw"] = int(ms_val) if ms_val is not None else 0
```

**Validation:** `_turn_viewer_data` returns rows where each row has `total_tt_ms_raw` (int) and each stream has `ms_raw` (int). Verify with a one-off `python -c` against a real events.jsonl.

---

#### Step 1.2 — Add per-stream "inputs snapshot" to row dict

**File:** `ccya/server/tv.py`

**What:** For each stream, add an `inputs_snapshot` dict keyed by upstream stream key → summary lines (same `_tv_dict_to_lines` / `_tv_narration_lines` output already computed in connector generation). This replaces the current connector-card model: instead of floating cards between stages, the data lives inside the downstream stage's dict.

**Why:** The template will render "received from: rules (5 fields)" as a collapsed block at the top of each expanded stage body, eliminating the duplicated cross-stage cards.

**Code Snippet**
```python
# After the connector generation block ends at line 326 (after connectors.append(...)), add:
inputs_snapshot: dict[str, list[dict]] = {}
for sd in _STREAMS:
    if not sd.inputs:
        continue
    snap: dict[str, list[dict]] = {}
    for inp_key in sd.inputs:
        inp_sd = STREAM_BY_KEY.get(inp_key)
        if inp_sd is None:
            continue
        inp_p_path = inp_sd.prompt_path or inp_sd.metrics_path
        inp_p_blob = _get_nested(ev, inp_p_path) or {}
        if not isinstance(inp_p_blob, dict):
            inp_p_blob = {}
        raw_out = inp_p_blob.get(inp_sd.output_subkey) if inp_sd.output_subkey else inp_p_blob
        if inp_sd.is_text_output:
            seg_lines = _tv_narration_lines(str(raw_out or ""))
        elif inp_sd.output_is_json_string and isinstance(raw_out, str):
            try:
                parsed = _json.loads(raw_out)
                seg_lines = _tv_dict_to_lines(parsed) if isinstance(parsed, dict) else [{"k": "_", "v": str(raw_out), "dim": False}]
            except Exception:
                seg_lines = [{"k": "_", "v": str(raw_out), "dim": False}]
        elif isinstance(raw_out, dict):
            seg_lines = _tv_dict_to_lines(raw_out)
        else:
            seg_lines = [{"k": "_", "v": str(raw_out), "dim": False}] if raw_out else []
        snap[inp_key] = seg_lines
    inputs_snapshot[sd.key] = snap  # type: ignore[assignment]
```

Add `inputs_snapshot` to the row dict in `rows.append` at line 352:
```python
"inputs_snapshot": inputs_snapshot,
```

**Note:** This code duplicates the connector generation logic at lines 289-326. Both iterate `sd.inputs`, call `_get_nested`, resolve `raw_out`, and produce `seg_lines`. The duplication is intentional — the connector data stays for the template transition period, and `inputs_snapshot` is the new structure. The executor may refactor to share the inner loop later.

**Validation:** Row dict has `inputs_snapshot["scene"]` = `{"rules": [...], "narrate": [...]}`. Verify field counts match current connector card counts.

---

#### Step 1.3 — Replace connector cards with inline input blocks in template

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove the entire `<template x-for="(c, ci) in connectorsBefore(t, stage)">` block (lines 81-105) and the `connectorsBefore` JS method (line 343). Inside the expanded stage body (`tv-stage-body`), prepend a new "inputs" section that renders `t.inputs_snapshot[stage]` as collapsed pills — one per upstream key, labeled `"← rules"`, `"← narrate"`, etc. Each pill expands to show the KV lines on click (same expand pattern as current flow pills). Place this block before the error/rejection banners (before line 127).

**Why:** One card per upstream source, living inside the stage that consumed it, eliminates duplication and makes the data flow obvious: you are looking at SCENE, you see what SCENE received.

**Code Snippet**
```html
<!-- Inside tv-stage-body, before the rejection banner at line 127 -->
<template x-if="t.inputs_snapshot && t.inputs_snapshot[stage] && Object.keys(t.inputs_snapshot[stage]).length">
  <div class="tv-inputs-row">
    <template x-for="(lines, srcKey) in Object.entries(t.inputs_snapshot[stage])" :key="srcKey">
      <div class="tv-input-pill" :class="'tv-stage-' + srcKey">
        <div class="tv-input-pill-header" @click="toggleInputPill(t.turn, stage, srcKey)">
          <span class="tv-input-pill-arrow">←</span>
          <span class="tv-input-pill-label" x-text="srcKey"></span>
          <span class="tv-input-pill-count" x-text="'(' + lines.length + ')'"></span>
        </div>
        <div class="tv-input-pill-body" x-show="isInputPillOpen(t.turn, stage, srcKey)">
          <template x-for="ln in lines" :key="ln.k">
            <div class="tv-flow-kv-item" :class="{ dim: ln.dim }">
              <span class="k" x-text="ln.k"></span>
              <span class="v" x-text="ln.v"></span>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>
```

Add to Alpine `tvRoot` data object (after `flowOpen: {}` at line 266):
```javascript
inputPillOpen: {},
isInputPillOpen(turn, stage, src) {
    return !!this.inputPillOpen['t' + turn + '-' + stage + '-' + src];
},
toggleInputPill(turn, stage, src) {
    var k = 't' + turn + '-' + stage + '-' + src;
    this.inputPillOpen[k] = !this.inputPillOpen[k];
},
```

Remove `connectorsBefore` method (line 343) and `flowOpen` / `isFlowOpen` / `toggleFlow` state (lines 266, 330-341) and all usages.

**Validation:** Turn viewer renders without connector cards. Expanding SCENE shows `← rules` and `← narrate` pills. Clicking expands KV lines.

---

#### Step 1.4 — Add total latency bar and latency waterfall per stage

**File:** `ccya/templates/_turn_viewer.html`

**What:** In `tv-turn-header`, replace the current token display with: total time (`t.total_tt`), total tokens in/out, and a small horizontal waterfall bar showing each stage as a proportional colored segment. Each segment's width = `stage.ms_raw / total_tt_ms_raw * 100%`, colored by stage CSS var.

Per-stage badge: add `ms_raw`-based width bar alongside the existing token bar.

**Why:** Total turn time was already computed but not shown. The waterfall lets you immediately see which stage was the bottleneck.

**Code Snippet**
```html
<!-- In tv-turn-header, replace the token spans (lines 48-49) with: -->
<div class="tv-turn-timing">
  <span class="tv-turn-total-tt" x-text="t.total_tt"></span>
  <span class="tv-turn-tokens" x-text="t.total_tokens_in_display + ' in / ' + t.total_tokens_out_display + ' out'"></span>
  <div class="tv-latency-waterfall">
    <template x-for="stage in stages" :key="'wf-' + t.turn + '-' + stage">
      <div
        class="tv-wf-segment"
        :class="t.streams[stage].stage_class"
        :style="'width:' + (t.total_tt_ms_raw > 0 ? Math.round(100 * (t.streams[stage].ms_raw || 0) / t.total_tt_ms_raw) : 0) + '%'"
        :title="stage + ': ' + t.streams[stage].tt"
      ></div>
    </template>
  </div>
</div>
```

CSS for waterfall (add to `app.src.css` turn viewer section):
```css
.tv-latency-waterfall {
  display: flex;
  height: 4px;
  border-radius: 2px;
  overflow: hidden;
  background: var(--bg-base);
  min-width: 80px;
}
.tv-wf-segment {
  height: 100%;
  min-width: 2px;
  transition: width 0.2s;
}
/* Stage colors reuse existing --stage-* vars defined at app.src.css:35-39 */
.tv-wf-segment.tv-stage-rules   { background: var(--stage-rules); }
.tv-wf-segment.tv-stage-narrate { background: var(--stage-narrate); }
.tv-wf-segment.tv-stage-scene   { background: var(--stage-scene); }
.tv-wf-segment.tv-stage-state   { background: var(--stage-state); }
.tv-wf-segment.tv-stage-progress{ background: var(--stage-progress); }
```

**Validation:** Turn header shows total time (e.g. "17.4s") and a 4px waterfall bar with colored stage segments. Hovering a segment shows tooltip with stage name and time.

---

#### Step 1.5 — Remove scope and state_rejections display

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove the `tv-scope-block` template block (lines 66-80) that renders before the SCENE stage. Remove `scope_block` from `rows.append` in `tv.py` (line 363). Remove the scope_block construction block (lines 329-332). Remove `scope` key from the Alpine `t` object references — specifically the `x-if="t.scope"` checks at lines 166 and 198. Also remove `state_rejections` from `rows.append` in `tv.py` (line 371) — it is superseded by the `failures` list in Phase 02. Remove the `tv-rejection-banner` block (lines 127-133) which references `t.state_rejections`.

**Why:** Scope system may be removed. Don't surface something you don't trust. `state_rejections` is superseded by the structured `failures` list.

**Code Snippet**
```python
# In rows.append(...) at line 352, remove:
# "scope": scope_block,
# "state_rejections": state_rej,
# Also remove the scope_block construction block at lines 329-332.
```

**Validation:** No scope block appears in the rendered viewer. No JS errors for missing `t.scope` or `t.state_rejections` references (ensure all template `x-if` on these are removed).

### Tests to write or update
- `tests/test_turn_viewer.py`: assert `_turn_viewer_data` returns rows with `total_tt_ms_raw` (int), `ms_raw` per stream (int), and `inputs_snapshot` dict. Assert `scope` and `state_rejections` keys are absent.

### REPOMAP and architecture updates
- `docs/REPOMAP/server.md`: update `_turn_viewer_data` docstring entry to note `inputs_snapshot`, `total_tt_ms_raw`, `ms_raw` per stream; remove `scope_block` mention.

### Risks
1. `connectorsBefore` removal breaks existing CSS that styles the flow segments — audit `app.src.css` for `.tv-flow-*` selectors and remove them, or they will remain as dead CSS. Mitigation: grep for `.tv-flow-` before removing. (Done in Phase 04.)
2. `ms_raw` is 0 for skipped streams — the waterfall segments will be 0-width. This is correct behavior (skipped = no time), but verify it doesn't make the bar look broken for turns with many skipped stages.

---

## Implementation — Phase 02: State diff right panel

### Files to pull for context
- `ccya/server/tv.py`
- `ccya/server/tv_mirror.py`
- `ccya/templates/_turn_viewer.html`
- `ccya/static/app.src.css`
- `ccya/state/delta.py` — understand what apply_delta touches
- `ccya/models.py` — TurnResult, delta field names

### Detailed steps

#### Step 2.1 — Extract state diff from events.jsonl

**File:** `ccya/server/tv.py`

**What:** Add a `_tv_state_diff(ev: dict) -> list[dict]` function that reads the extraction outputs from a single event and produces a flat list of change entries. Each entry:
```python
{
  "domain": str,       # "scene", "state", "progress"
  "op": str,           # "add", "remove", "update", "set"
  "field": str,        # human-readable field name or item id
  "value": str,        # brief string summary of new value
  "rejected": bool,    # True if this change appears in ev["rejected"]
  "from_stream": str,  # which extraction stream produced it ("scene", "state", "progress")
}
```

Source for the diff is the `output` JSON from each extraction stream (`extraction.scene.output`, `extraction.state.output`, `extraction.progress.output`). Parse the JSON blob for each stream and enumerate top-level keys that are non-null and non-empty. Cross-reference against `ev.get("rejected") or []` to mark rejected entries.

**Why:** This is the "what did this turn actually do" panel. It answers whether the game state changed and how, without requiring the user to open each stream's output tab.

**Code Snippet**
```python
def _tv_state_diff(ev: dict[str, Any]) -> list[dict[str, Any]]:
    """Produce a flat list of state-change entries from extraction outputs.

    Reads scene/state/progress extraction outputs and flattens them into
    labelled change entries for the diff right panel.
    """
    rejected_set: set[str] = set()
    for r in (ev.get("rejected") or []):
        if isinstance(r, dict) and r.get("field"):
            rejected_set.add(str(r["field"]))

    changes: list[dict[str, Any]] = []

    _EXTRACTION_STREAMS = [
        ("scene",    "extraction.scene"),
        ("state",    "extraction.state"),
        ("progress", "extraction.progress"),
    ]

    for stream_key, path in _EXTRACTION_STREAMS:
        blob = _get_nested(ev, path) or {}
        if not isinstance(blob, dict):
            continue
        raw_out = blob.get("output")
        if not raw_out:
            continue
        parsed: dict[str, Any] | None = None
        if isinstance(raw_out, str):
            parsed = _tv_parse_json_blob(raw_out)
        elif isinstance(raw_out, dict):
            parsed = raw_out
        if not parsed:
            continue
        for field_key, val in parsed.items():
            if val is None:
                continue
            if isinstance(val, list) and not val:
                continue
            if isinstance(val, dict) and not val:
                continue
            # Determine op from field name conventions
            if field_key.endswith("_add") or field_key.endswith("_update"):
                op = "add" if field_key.endswith("_add") else "update"
            elif field_key.endswith("_remove"):
                op = "remove"
            else:
                op = "set"
            # Derive a brief value summary
            if isinstance(val, list):
                if all(isinstance(x, dict) for x in val):
                    def _label(x: dict[str, Any]) -> str:
                        for k in ("id", "name", "text", "label"):
                            v = x.get(k)
                            if v and isinstance(v, str):
                                return v[:60]
                        return ""
                    summary = ", ".join(_label(x) for x in val if _label(x))
                    value_str = f"[{len(val)}] {summary}" if summary else f"[{len(val)}]"
                else:
                    value_str = ", ".join(str(x) for x in val[:4])
                    if len(val) > 4:
                        value_str += "\u2026"
            elif isinstance(val, dict):
                value_str = _json.dumps(val)[:120]
            elif isinstance(val, str):
                value_str = val[:120] + ("\u2026" if len(val) > 120 else "")
            else:
                value_str = str(val)
            changes.append({
                "domain": stream_key,
                "op": op,
                "field": field_key,
                "value": value_str,
                "rejected": field_key in rejected_set,
                "from_stream": stream_key,
            })
    return changes
```

Call this in `_turn_viewer_data` and add to row dict:
```python
"state_diff": _tv_state_diff(ev),
```

**Validation:** Row dict has `state_diff` as a list. A turn that added an inventory item has an entry `{"domain": "state", "op": "add", "field": "inventory_add", ...}`. A rejected inventory_remove shows `"rejected": True`.

---

#### Step 2.2 — Collect all error/rejection/retry data into a structured `failures` list

**File:** `ccya/server/tv.py`

**What:** Add `_tv_failures(ev: dict, streams: dict) -> list[dict]` that collects ALL failure signals from a turn event into a flat list:
- LLM call errors per stream (`streams[key]["error"]`)
- Retry errors per stream (`streams[key]["retry_errors"]`)
- Pydantic/validation rejections from `ev["rejected"]`
- Any `error` field at top level of `ev`

Each entry:
```python
{
  "kind": str,    # "llm_error", "retry", "rejection", "top_level_error"
  "stream": str,  # stream key or "" for top-level
  "message": str, # human-readable error text
  "attempt": int | None,  # for retry entries, which attempt (1-indexed)
}
```

**Why:** Currently failures are scattered: rejections in `tv-rejection-banner`, errors in `tv-error-banner`, retry errors in `tv-retry-errors` — all inside the stage body. The right panel needs a consolidated view so you can see at a glance "this turn had 2 retry errors in state + 1 rejection" without expanding any stages.

**Code Snippet**
```python
def _tv_failures(
    ev: dict[str, Any],
    streams: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    top_err = ev.get("error")
    if top_err:
        failures.append({"kind": "top_level_error", "stream": "", "message": str(top_err), "attempt": None})
    for key, s in streams.items():
        if s.get("error"):
            failures.append({"kind": "llm_error", "stream": key, "message": str(s["error"]), "attempt": None})
        for i, re_msg in enumerate(s.get("retry_errors") or []):
            failures.append({"kind": "retry", "stream": key, "message": str(re_msg), "attempt": i + 1})
    for r in (ev.get("rejected") or []):
        if isinstance(r, dict):
            msg = f"{r.get('field', '')}: {r.get('reason', '')}".strip(": ")
            failures.append({"kind": "rejection", "stream": "state", "message": msg, "attempt": None})
    return failures
```

Call in `_turn_viewer_data`, add to row:
```python
row_failures = _tv_failures(ev, streams)
"failures": row_failures,
```

Update `has_errors`, `has_retries`, `has_rejections` to derive from `failures` list for consistency:
```python
has_retries = any(f["kind"] == "retry" for f in row_failures)
has_errors = any(f["kind"] in ("llm_error", "top_level_error") for f in row_failures)
has_rejections = any(f["kind"] == "rejection" for f in row_failures)
```

**Validation:** Row has `failures` list. A turn with a retry shows `{"kind": "retry", "stream": "state", "attempt": 1, "message": "..."}`. A clean turn has `failures = []`.

---

#### Step 2.3 — Two-column layout in template

**File:** `ccya/templates/_turn_viewer.html`

**What:** When a turn is expanded, render a two-column flex container: `tv-pipeline` on the left (existing, width ~56%), `tv-diff-panel` on the right (new, width ~44%). The right panel is always rendered when the turn is expanded; it is not gated on having any diffs.

Right panel structure (top to bottom):
1. **Failures block** — shown only if `t.failures.length > 0`. Each failure as a tagged row: `[stream] [kind] message`. Color: errors red (`--status-error`), retries orange (`--status-retried`), rejections amber (`--status-rejected`).
2. **State diff block** — list of change entries grouped by domain. Each row: op badge (`+ add`, `- remove`, `~ update`, `= set`) + field name + value. Rejected entries get a strikethrough and a `rejected` badge.
3. **Empty state** — if `failures.length === 0 && state_diff.length === 0`: show `"No changes this turn"`.

**Why:** The right panel answers "what happened" at a glance; the left pipeline answers "how it happened" on drill-down.

**Code Snippet**
```html
<!-- Replace the current tv-pipeline standalone div (line 57) with: -->
<div class="tv-turn-columns" x-show="!isTurnCollapsed(t.turn)">

  <!-- LEFT: pipeline -->
  <div class="tv-pipeline">
    <!-- existing pipeline content unchanged -->
  </div>

  <!-- RIGHT: diff panel -->
  <div class="tv-diff-panel">
    <template x-if="t.failures && t.failures.length">
      <div class="tv-diff-section">
        <div class="tv-diff-section-label">Failures</div>
        <template x-for="(f, fi) in t.failures" :key="fi">
          <div class="tv-failure-row" :class="'tv-failure-' + f.kind">
            <span class="tv-failure-stream" x-text="f.stream || '—'"></span>
            <span class="tv-failure-kind" x-text="f.kind + (f.attempt != null ? ' #' + f.attempt : '')"></span>
            <span class="tv-failure-msg" x-text="f.message"></span>
          </div>
        </template>
      </div>
    </template>

    <template x-if="t.state_diff && t.state_diff.length">
      <div class="tv-diff-section">
        <div class="tv-diff-section-label">State changes</div>
        <template x-for="(ch, chi) in t.state_diff" :key="chi">
          <div class="tv-diff-row" :class="{ 'tv-diff-rejected': ch.rejected, 'tv-diff-op-remove': ch.op === 'remove' }">
            <span class="tv-diff-op" :class="'tv-diff-op--' + ch.op" x-text="ch.op === 'add' ? '+' : ch.op === 'remove' ? '-' : ch.op === 'update' ? '~' : '='"></span>
            <span class="tv-diff-field" x-text="ch.field"></span>
            <span class="tv-diff-value" x-text="ch.value"></span>
            <span class="tv-diff-rejected-badge" x-show="ch.rejected">rejected</span>
          </div>
        </template>
      </div>
    </template>

    <template x-if="(!t.failures || !t.failures.length) && (!t.state_diff || !t.state_diff.length)">
      <div class="tv-diff-empty">No changes this turn</div>
    </template>
  </div>
</div>
```

CSS additions to `app.src.css`:
```css
/* NOTE: CSS variables below use the existing design tokens from app.src.css:9-40.
   --bg-surface, --border-subtle, --text-muted, --status-ok, --status-error,
   --status-retried, --status-rejected, --accent-success, --accent-error,
   --accent, --radius, --radius-sm, --text-primary are all defined.
   NOTE: --radius-md does not exist; use --radius (8px) instead. */

.tv-turn-columns {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.tv-pipeline { flex: 0 0 56%; min-width: 0; }
.tv-diff-panel {
  flex: 0 0 44%;
  min-width: 0;
  position: sticky;
  top: 16px;
  max-height: 80vh;
  overflow-y: auto;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 16px;
}
.tv-diff-section { margin-bottom: 16px; }
.tv-diff-section-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.tv-diff-row {
  display: grid;
  grid-template-columns: 1.2em 1fr 2fr auto;
  gap: 8px;
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  padding: 2px 0;
  align-items: baseline;
}
.tv-diff-rejected { opacity: 0.5; text-decoration: line-through; }
.tv-diff-op { font-weight: 700; }
.tv-diff-op--add    { color: var(--accent-success); }
.tv-diff-op--remove { color: var(--accent-error); }
.tv-diff-op--update { color: var(--accent); }
.tv-diff-op--set    { color: var(--text-muted); }
.tv-diff-rejected-badge {
  font-size: 0.65rem;
  background: var(--status-rejected);
  color: var(--text-primary);
  padding: 1px 4px;
  border-radius: var(--radius-sm);
}
.tv-failure-row {
  display: grid;
  grid-template-columns: 5em 7em 1fr;
  gap: 8px;
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  padding: 2px 0;
  align-items: baseline;
}
.tv-failure-llm_error, .tv-failure-top_level_error { color: var(--status-error); }
.tv-failure-retry    { color: var(--status-retried); }
.tv-failure-rejection{ color: var(--status-rejected); }
.tv-diff-empty { color: var(--text-muted); font-size: 11px; padding: 8px 0; }
```

**Validation:** Expanded turn shows two columns. Right panel shows failures at top (if any), then state diff rows with op badges. Rejected entries are struck through. A clean turn shows "No changes this turn".

---

#### Step 2.4 — Remove inline error/rejection banners from stage bodies

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove `tv-rejection-banner` (lines 127-133), `tv-error-banner` (lines 135-140), and `tv-retry-errors` (lines 142-152) blocks from the stage body — they are now surfaced in the right panel. Keep `tv-skipped` block ("Skipped" label when a stream is skipped) since that is still useful inline.

**Why:** Reduce stage body clutter; failures are now consolidated in one place.

**Validation:** No duplicate error display. Expanding a retried stage no longer shows retry error list inside it — that info is on the right.

### Tests to write or update
- `tests/test_turn_viewer.py`: assert `_tv_state_diff` returns correct entries for a fixture event with inventory_add and a rejection. Assert `_tv_failures` returns correct entries for retry_errors and rejected fields. Assert `state_rejections` key is absent from rows (it is superseded by `failures`).

### REPOMAP and architecture updates
- `docs/REPOMAP/server.md`: add `_tv_state_diff`, `_tv_failures` to `server/tv.py` internal functions table.

### Risks
1. Field names in extraction output do not all follow `_add`/`_remove`/`_update` suffix convention — the op inference in `_tv_state_diff` may misclassify some fields as `set`. Mitigation: default to `set`; it is always safe to display. Review `models.py` extraction delta field names before finalizing the op map.
2. `state_rejections` is currently referenced in `_tv_extract_stream_status` (hardcoded `"state"` key check at tv.py:146-148). After this phase, rejections come from `failures`. Verify `_tv_extract_stream_status` still works correctly for the status badge on the stage row (it does — it uses `ev["rejected"]` directly, unaffected).

---

## Implementation — Phase 03: Compaction rows

### Files to pull for context
- `ccya/engine/compactor.py`
- `ccya/engine/turn.py` (or wherever `maybe_compact` is called)
- `ccya/state/chronicle.py`
- `ccya/server/tv.py`
- `ccya/templates/_turn_viewer.html`
- `ccya/models.py` — CompactorSanitizationResult (defined at models.py:368)

### Detailed steps

#### Step 3.1 — Emit a compaction event to events.jsonl

**File:** `ccya/engine/compactor.py`

**What:** At the end of `maybe_compact`, when `compaction_ran is True`, write a compaction event record to `save_dir / "events.jsonl"`. The record must be distinguishable from a normal turn event. Structure:

```python
{
  "kind": "compaction",
  "turn": current_turn,          # turn that triggered compaction
  "compact_start": compact_start,
  "compact_end": compact_end,
  "bullets_count": len(new_bullets),
  "sanitization": {              # null if no sanitization ran
    "npc_merge": [...],          # raw dicts, not Pydantic objects
    "inventory_remove": [...],
    "quest_close": [...],
    "pressure_remove": [...],
    "condition_remove": [...],
    "recent_events_compact_count": int   # len of compacted recent_events
  } | None,
  "bullets_preview": [first 3 bullet strings],  # for quick preview in viewer
}
```

Write this after `state.setdefault("meta", {})["last_compacted_turn"] = compact_end` at line 129 and before the `return` at line 131.

**Why:** Compaction is invisible right now. It modifies state, prunes history, and merges NPCs — all silently. Emitting an event record is the minimum viable observability surface without coupling compactor to the viewer.

**Code Snippet**
```python
# After line 129 (last_compacted_turn), before the return at line 131:
san_payload: dict[str, Any] | None = None
if sanitization is not None:
    san_payload = {
        "npc_merge": [m.model_dump() for m in (sanitization.npc_merge or [])],
        "inventory_remove": [i.model_dump() for i in (sanitization.inventory_remove or [])],
        "quest_close": [q.model_dump() for q in (sanitization.quest_close or [])],
        "pressure_remove": [p.model_dump() for p in (sanitization.pressure_remove or [])],
        "condition_remove": [c.model_dump() for c in (sanitization.condition_remove or [])],
        "recent_events_compact_count": len(sanitization.recent_events_compact or []),
    }

compaction_record: dict[str, Any] = {
    "kind": "compaction",
    "turn": current_turn,
    "compact_start": compact_start,
    "compact_end": compact_end,
    "bullets_count": len(new_bullets),
    "sanitization": san_payload,
    "bullets_preview": new_bullets[:3],
}
events_path = save_dir / "events.jsonl"
try:
    with events_path.open("a", encoding="utf-8") as _f:
        _f.write(json.dumps(compaction_record) + "\n")
except OSError as exc:
    _log.warning("compactor: failed to write event record: %s", exc)
```

`json` is already imported at compactor.py:5.

**Validation:** After a turn that triggers compaction, `events.jsonl` has a new line with `"kind": "compaction"`. Run a game to turn `compact_every` and inspect the file.

---

#### Step 3.2 — Parse compaction events in _turn_viewer_data

**File:** `ccya/server/tv.py`

**What:** In `_turn_viewer_data`, when parsing each line of `events.jsonl`, check `ev.get("kind") == "compaction"`. If so, build a compaction row dict instead of a normal turn row dict:

```python
{
  "row_kind": "compaction",
  "turn": int,                   # the turn that triggered it
  "compact_start": int,
  "compact_end": int,
  "bullets_count": int,
  "bullets_preview": list[str],
  "sanitization": dict | None,   # raw, passed to template
  "has_sanitization": bool,
}
```

Normal turn rows get `"row_kind": "turn"`. The template uses `row_kind` to decide which row variant to render.

**Code Snippet**
```python
# At the top of the per-line loop in _turn_viewer_data (after the json.loads at line 179), add:
if ev.get("kind") == "compaction":
    san = ev.get("sanitization")
    rows.append({
        "row_kind": "compaction",
        "turn": int(ev.get("turn") or 0),
        "compact_start": int(ev.get("compact_start") or 0),
        "compact_end": int(ev.get("compact_end") or 0),
        "bullets_count": int(ev.get("bullets_count") or 0),
        "bullets_preview": list(ev.get("bullets_preview") or []),
        "sanitization": san,
        "has_sanitization": bool(san and any(
            san.get(k) for k in (
                "npc_merge", "inventory_remove", "quest_close",
                "pressure_remove", "condition_remove"
            )
        )),
    })
    continue
```

All existing rows.append logic runs only for normal turn events (falls through after the `continue`).

**Also required — guard metrics.py:** Both `_recent_turn_metrics` (line 56) and `_turn_log_entries` (line 177) in `server/metrics.py` iterate `events.jsonl` without checking `ev.get("kind")`. Add a guard at the top of each per-line loop:

```python
# In _recent_turn_metrics, after json.loads (line 58):
if ev.get("kind") == "compaction":
    continue

# In _turn_log_entries, after json.loads (line 179):
if ev.get("kind") == "compaction":
    continue
```

**Validation:** A compaction event in events.jsonl produces a row with `row_kind="compaction"` in the data. Normal turn rows have `row_kind="turn"`. Both appear in the sorted row list. Metrics functions skip compaction rows.

---

#### Step 3.3 — Render compaction rows in template

**File:** `ccya/templates/_turn_viewer.html`

**What:** In the `x-for` over `visibleTurns()`, branch on `t.row_kind`. Normal turns render as before. Compaction rows render a distinct, visually compressed card:

- Left stripe accent in a neutral/purple color (distinct from stage colors)
- Header: `"⟳ Compaction — Turns [compact_start]–[compact_end] → [bullets_count] bullets"`
- Expandable body with:
  - Bullet previews (first 3, truncated)
  - Sanitization summary table if `has_sanitization`: rows for each non-empty sanitization list ("NPCs merged: 2", "Items removed: 1", etc.)
  - "No sanitization changes" if `has_sanitization` is false

Filter bar: add a `onlyCompaction` toggle that shows only compaction rows. Compaction rows are excluded from `onlyRejected`/`onlyRetried`/`onlyErrors`/`onlySkipped` filters (those apply to turn rows only).

**Code Snippet**
```html
<!-- In the x-for loop over visibleTurns() (line 41), wrap the existing tv-turn-card in a conditional and add the compaction variant: -->
<template x-if="t.row_kind === 'compaction'">
  <div class="tv-compaction-card">
    <div class="tv-compaction-header" @click="toggleTurnCollapsed('c-' + t.turn)">
      <span class="tv-compaction-icon">⟳</span>
      <span class="tv-compaction-title">Compaction</span>
      <span class="tv-compaction-range" x-text="'Turns ' + t.compact_start + '\u2013' + t.compact_end"></span>
      <span class="tv-compaction-bullets" x-text="t.bullets_count + ' bullets'"></span>
      <span x-show="t.has_sanitization" class="tv-compaction-san-badge">sanitized</span>
      <span class="tv-stage-chevron" :class="{ open: !isTurnCollapsed('c-' + t.turn) }">▶</span>
    </div>
    <div class="tv-compaction-body" x-show="!isTurnCollapsed('c-' + t.turn)">
      <template x-for="(b, bi) in t.bullets_preview" :key="bi">
        <div class="tv-compaction-bullet" x-text="b"></div>
      </template>
      <template x-if="t.bullets_count > 3">
        <div class="tv-compaction-more" x-text="'\u2026 ' + (t.bullets_count - 3) + ' more bullets'"></div>
      </template>
      <template x-if="t.has_sanitization && t.sanitization">
        <div class="tv-compaction-san">
          <div class="tv-diff-section-label">Sanitization</div>
          <template x-if="t.sanitization.npc_merge && t.sanitization.npc_merge.length">
            <div class="tv-compaction-san-row">NPCs merged: <span x-text="t.sanitization.npc_merge.length"></span></div>
          </template>
          <template x-if="t.sanitization.inventory_remove && t.sanitization.inventory_remove.length">
            <div class="tv-compaction-san-row">Items removed: <span x-text="t.sanitization.inventory_remove.length"></span></div>
          </template>
          <template x-if="t.sanitization.quest_close && t.sanitization.quest_close.length">
            <div class="tv-compaction-san-row">Quests closed: <span x-text="t.sanitization.quest_close.length"></span></div>
          </template>
          <template x-if="t.sanitization.pressure_remove && t.sanitization.pressure_remove.length">
            <div class="tv-compaction-san-row">Pressures removed: <span x-text="t.sanitization.pressure_remove.length"></span></div>
          </template>
          <template x-if="t.sanitization.condition_remove && t.sanitization.condition_remove.length">
            <div class="tv-compaction-san-row">Conditions removed: <span x-text="t.sanitization.condition_remove.length"></span></div>
          </template>
          <template x-if="t.sanitization.recent_events_compact_count">
            <div class="tv-compaction-san-row">Recent events compacted to: <span x-text="t.sanitization.recent_events_compact_count"></span></div>
          </template>
        </div>
      </template>
      <template x-if="!t.has_sanitization">
        <div class="tv-compaction-no-san">No sanitization changes</div>
      </template>
    </div>
  </div>
</template>

<template x-if="t.row_kind !== 'compaction'">
  <!-- existing tv-turn-card markup (lines 42-216) -->
</template>
```

Add to `visibleTurns()` filter:
```javascript
// In visibleTurns(), before the existing filter checks:
var onlyC = this.onlyCompaction;
if (onlyC) return t.row_kind === 'compaction';
// existing filters apply only to non-compaction rows:
if (t.row_kind === 'compaction') return true;
```

Add `onlyCompaction: false` to Alpine data object and a filter checkbox in `tv-filter-bar`:
```html
<label class="tv-filter-toggle"><input type="checkbox" x-model="onlyCompaction"> compaction</label>
```

CSS:
```css
.tv-compaction-card {
  border-left: 3px solid var(--accent-blue);
  background: var(--bg-surface);
  border-radius: var(--radius);
  margin-bottom: 8px;
  padding: 0;
}
.tv-compaction-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
}
.tv-compaction-icon { color: var(--accent-blue); font-size: 1.1em; }
.tv-compaction-title { font-weight: 600; color: var(--text-primary); }
.tv-compaction-range, .tv-compaction-bullets { color: var(--text-muted); font-size: 11px; }
.tv-compaction-san-badge {
  font-size: 0.65rem;
  background: var(--accent-blue);
  color: var(--text-primary);
  padding: 1px 5px;
  border-radius: 9999px;
}
.tv-compaction-body {
  padding: 12px 16px 16px;
  border-top: 1px solid var(--border-subtle);
}
.tv-compaction-bullet {
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--text-muted);
  padding: 2px 0;
}
.tv-compaction-more { font-size: 11px; color: var(--text-muted); padding: 2px 0; }
.tv-compaction-san { margin-top: 12px; }
.tv-compaction-san-row { font-size: 11px; color: var(--text-primary); padding: 2px 0; }
.tv-compaction-no-san { font-size: 11px; color: var(--text-muted); padding: 8px 0; }
```

**Validation:** After triggering a compaction, the turn viewer shows a blue-striped compaction card between the turn rows at the correct turn number. Expanding it shows bullet previews and sanitization summary. "Compaction" filter checkbox in the filter bar hides/shows only compaction rows.

### Tests to write or update
- `tests/test_compactor.py`: assert `maybe_compact` writes a `"kind": "compaction"` line to `events.jsonl` when compaction runs; assert it does NOT write when `compaction_ran` is False.
- `tests/test_turn_viewer.py`: assert `_turn_viewer_data` correctly parses a mixed events.jsonl with turn rows and a compaction row; assert compaction row has `row_kind="compaction"` and correct fields.

### REPOMAP and architecture updates
- `docs/REPOMAP/server.md`: note that `_turn_viewer_data` handles `"kind": "compaction"` rows.
- `docs/REPOMAP/engine.md`: note that `maybe_compact` emits a compaction event to `events.jsonl`.

### Risks
1. File append in `compactor.py` is synchronous. The compactor runs in an async context (`maybe_compact` is `async`). Synchronous append is acceptable since the compactor already does synchronous file writes (`_write_compacted_block`). If blocking I/O becomes a concern later, wrap in `asyncio.get_event_loop().run_in_executor`.

---

## Implementation — Phase 04: Polish and cleanup

### Files to pull for context
- `ccya/templates/_turn_viewer.html`
- `ccya/static/app.src.css`
- `ccya/server/tv.py`

### Detailed steps

#### Step 4.1 — Keyboard navigation (j/k between turns)

**File:** `ccya/templates/_turn_viewer.html`

**What:** Add `@keydown.j.window` and `@keydown.k.window` handlers to `tvRoot` that move a `focusedTurnIdx` cursor through `visibleTurns()`. The focused turn is auto-expanded; others are collapsed. Focused turn gets a `tv-turn-focused` CSS class for a visible outline.

**Code Snippet**
```javascript
// Add to tvRoot data object:
focusedTurnIdx: 0,
onlyCompaction: false,
navToIdx(idx) {
    var vt = this.visibleTurns();
    if (!vt.length) return;
    idx = Math.max(0, Math.min(idx, vt.length - 1));
    this.focusedTurnIdx = idx;
    var t = vt[idx];
    var key = t.row_kind === 'compaction' ? 'c-' + t.turn : t.turn;
    // Collapse all non-compaction turns to avoid losing compaction expansion
    this.turns.forEach(function(tr) {
        if (tr.row_kind !== 'compaction') {
            this.turnCollapsed[tr.turn] = true;
        }
    }.bind(this));
    this.turnCollapsed[key] = false;
    this.$nextTick(function() {
        // The turn card div needs an id attribute for scrollIntoView to work.
        // Add id="tv-turn-{turn}" to the tv-turn-card div (line 42) in the template.
        var el = document.getElementById('tv-turn-' + key);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
},
// In init(), add keydown handlers:
this.$watch('turns', function() { this.$nextTick(function() { self.hlAllVisibleJson(); }); });
// Add to the root div's x-init or as separate handlers:
// @keydown.j.window="if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') navToIdx(focusedTurnIdx + 1)"
// @keydown.k.window="if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') navToIdx(focusedTurnIdx - 1)"
```

**BLOCKER fix:** The original plan referenced `document.getElementById('tv-turn-' + key)` but the template uses `class="tv-turn-card"` with no `id` attribute. Add `:id="'tv-turn-' + (t.row_kind === 'compaction' ? 'c-' + t.turn : t.turn)"` to the `tv-turn-card` div at line 42.

**Validation:** Pressing `j` collapses current turn and expands the next; `k` goes back. Focus indicator visible.

---

#### Step 4.2 — Scroll-lock on live update

**File:** `ccya/templates/_turn_viewer.html`

**What:** In `mergeTurnsFromServer`, before prepending new turns, record whether the user is scrolled near the top of `#tv-body` (within 100px). After merge, only scroll to top if the user was already at the top.

**Code Snippet**
```javascript
mergeTurnsFromServer(newTurns) {
    var body = document.getElementById('tv-body');
    var atTop = body ? body.scrollTop < 100 : true;
    // ... existing merge logic ...
    if (prepend.length && atTop) {
        this.$nextTick(function() {
            if (body) body.scrollTop = 0;
        });
    }
},
```

**Validation:** While reading turn N in the viewer, a new turn arrives — the view does not jump.

---

#### Step 4.3 — Remove dead connector-card CSS

**File:** `ccya/static/app.src.css`

**What:** Remove all CSS rules for `.tv-flow-block`, `.tv-flow-segment`, `.tv-flow-segment--narrate`, `.tv-flow-pill`, `.tv-flow-pill-label`, `.tv-flow-kv-grid`, `.tv-flow-kv-item`, `.tv-flow-expand-hint`, `.tv-flow-line`, `.tv-flow-line--*`. These are replaced by `.tv-input-pill` styles added in Phase 01.

**Validation:** `grep -r 'tv-flow-' ccya/static/app.src.css` returns no results. Run `make css`. No visual regressions.

---

#### Step 4.4 — Add `onlyCompaction` filter

**File:** `ccya/templates/_turn_viewer.html`

**What:** Update filter bar label for the compaction checkbox. The `onlyCompaction` data property and `visibleTurns()` filter logic were added in Phase 03 Step 3.3 — this step ensures the filter bar checkbox is present and the label is clear.

**Validation:** Checking "compaction only" hides all turn rows and shows only compaction cards.

---

#### Step 4.5 — Final make check && make test

**What:** Run `make check && make test`. Fix any ruff/mypy errors introduced by the new functions (`_tv_state_diff`, `_tv_failures`). Verify all new test functions pass.

**Validation:** `make check` exits 0. `make test` exits 0 with all new tests passing.

### Tests to write or update
- No new tests in Phase 04. Verify existing tests still pass after CSS and JS cleanup.

### REPOMAP and architecture updates
- `docs/REPOMAP/frontend.md`: update turn viewer CSS token table to remove `.tv-flow-*` entries; add `.tv-input-pill`, `.tv-diff-panel`, `.tv-compaction-card`.

### Risks
1. Removing `.tv-flow-*` CSS before verifying Phase 01 template is live could leave a blank viewer. Mitigation: do Phase 04 CSS cleanup only after Phase 01 template changes are committed and tested.
2. `j`/`k` key handlers conflict if user is typing in an input field. Mitigation: guard with `if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;` as shown in the code snippet above.

---

## Ambiguities resolved

1. **metrics.py iteration guard:** Confirmed `_recent_turn_metrics` (line 56) and `_turn_log_entries` (line 177) in `server/metrics.py` iterate `events.jsonl` without checking `ev.get("kind")`. Resolved: added explicit guard steps in Phase 03 Step 3.2. Both functions must skip `"kind": "compaction"` lines.

2. **Two-column layout at narrow viewport:** Resolved to option A (two-column always) — turn viewer is desktop-only per non-goals. No responsive breakpoint needed.

3. **`row_kind` field on existing rows:** Resolved to do both — set `row_kind: "turn"` in all turn rows in Python and use `t.row_kind !== 'compaction'` in template (safe when field is undefined). The template guard handles SSE-streamed data that may lack the field.

4. **CSS variable names:** The original plan used non-existent CSS variables (`--color-surface`, `--color-border`, `--color-text-muted`, `--color-success`, `--color-error`, `--color-gold`, `--color-warning`, `--color-text-inverse`, `--color-text-faint`, `--color-purple`, `--space-2`, `--space-3`, `--space-4`, `--text-xs`, `--text-sm`). Resolved to use the actual design tokens defined in `app.src.css`: `--bg-surface`, `--border-subtle`, `--text-muted`, `--accent-success`, `--accent-error`, `--accent`, `--bg-base`, `--status-ok`, `--status-error`, `--status-retried`, `--status-rejected`, `--accent-blue`, `--radius`, `--radius-sm`, `--text-primary`. All CSS snippets in the plan have been updated — `--radius-md` replaced with `--radius` (8px). References to existing variables are verified against the codebase.

5. **Keyboard nav element IDs:** The original plan referenced `document.getElementById('tv-turn-' + key)` but the template uses `class="tv-turn-card"` with no `id` attribute. Resolved: add `:id="'tv-turn-' + key"` to the turn card div in the template.
