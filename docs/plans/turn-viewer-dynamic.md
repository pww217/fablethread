# Turn Viewer — Dynamic Engine Mirror

## Status
`open`

## Part of
standalone

## Dependencies
- `narrator-driven-scope.md` — **completed**. Scope now lives at top-level in events.jsonl as `scope: {active_domains, decided_by, skipped_streams}`. This plan may proceed immediately.
- ~~`narration-active-domains.md`~~ — **superseded** by narrator-driven-scope. Ignore.

## Objective
`server/tv.py` hardcodes the names, keys, connector topology, and output shapes of every turn pipeline stage. When the engine changes — fields move, streams are added, output models evolve — tv.py silently breaks or misses data. The fix is to make tv.py drive its display from a declarative stream registry (`tv_mirror.py`), the same way `eval/engine_mirror.py` drives eval from live engine constants. After this plan: adding a new extraction stream requires adding one `StreamDescriptor` entry; tv.py, connectors, and pills all adapt automatically. Additionally, `scope` (a first-class top-level block in events.jsonl since narrator-driven-scope) is rendered as a dedicated display block. Pills between stages are driven by `sd.inputs` — they show the actual outputs of each upstream stream, not hardcoded field lists. The Alpine `stages` array is driven from the server, not hardcoded in the template JS.

## Non-goals
- Does NOT change the events.jsonl schema or what the engine writes.
- Does NOT add new debug panels or new routes.
- Does NOT touch eval/ code.
- Does NOT add backwards-compatibility aliases for any deleted keys.

## Confirmed events.jsonl structure (verified against live game output with narrator-driven-scope)

Top-level keys in each event:
```
ts, trace_id, turn, input,
applied, rejected, actions, scene_tags,
rules           — {intent_verb, intent, rolled, total_ms, tokens_in, tokens_out, skill, difficulty,
                   dice, stat_mod, diff_mod, cond_mod, final_total, band, outcome_summary}
narrate         — {first_token_ms, total_ms, tokens_in, tokens_out}   ← METRICS ONLY, no output here
extract         — {total_ms, tokens_in, tokens_out, retries,
                   streams: {scene: {ms, tokens_in, tokens_out, skipped},
                             state: {...}, progress: {...}}}
extraction      — {scene:    {rendered_system, rendered_user, output: {...}, skipped, attempts,
                              retry_errors, tokens_in, tokens_out, ms, context_meta},
                   state:    {skipped: true, tokens_in: 0, tokens_out: 0, ms: 0, attempts: 0,
                              retry_errors: []},
                   progress: {rendered_system, rendered_user, output: {...}, skipped, attempts,
                              retry_errors, tokens_in, tokens_out, ms, context_meta}}
scope           — {active_domains: [...], decided_by: "narrator", skipped_streams: [...]}
                  ← TOP LEVEL SIBLING — NOT nested inside any stream
changes         — {inventory, player, facts, quests}
failed          — []
rules_prompt    — {rendered_system, rendered_user, output: "...JSON string...", context_meta}
                  ← output is a SERIALIZED JSON STRING, requires json.loads before rendering
narrate_prompt  — {rendered_system, rendered_user, output: "...prose string...", context_meta}
                  ← output is PLAIN PROSE TEXT
```

Key facts the executor must not re-derive:
- `narrate` block = metrics only. Prose lives in `narrate_prompt.output`.
- `rules_prompt.output` = JSON string. Must `json.loads` before rendering as dict.
- `narrate_prompt.output` = plain string. Pass to `_tv_narration_lines`.
- `extraction.*.ms` (not `total_ms`) for per-extraction-stream latency.
- `rules.total_ms` (not `ms`) for the rules stream.
- `extraction.scene.output`, `extraction.state.output`, `extraction.progress.output` are Python dicts (already parsed), not JSON strings.
- `extract.streams.*` is a summary blob used only to compute `total_tt_ms`. It is NOT rendered anywhere in the template and does NOT need a `StreamDescriptor`.
- `state` stream is frequently skipped (`skipped: true`, all zeros). Display must show `—` for tokens and time.

## Resolved ambiguities (from source inspection — no open questions)

1. **`_tv_extract_stream_status` hardcodes `name == "state"`** for the inventory-rejection special case. This is intentional presentation logic. It stays in tv.py as-is, with a comment: `# NOTE: stream key "state" hardcoded; if stream is renamed, update this check`.

2. **Template path is `ccya/templates/_turn_viewer.html`** (not `ccya/server/templates/`). Confirmed from `app.py`: `TEMPLATES_DIR = BASE_DIR.parent / "templates"` where `BASE_DIR = Path(__file__).resolve().parent` (i.e., `ccya/server/`). Template is `ccya/templates/_turn_viewer.html`.

3. **`extract.streams.*`** is used only for `ext.get("total_ms")` in the total time calculation. Not rendered in the template. No descriptor needed. Keep the `ev.get("extract") or {}` call only for `total_tt_ms`.

4. **Template references all five prompt keys by name** using Alpine bracket notation: `t[stage + '_prompt']`, i.e. `t.rules_prompt`, `t.narrate_prompt`, `t.scene_prompt`, `t.state_prompt`, `t.progress_prompt`. These must ALL be replaced with `t.prompts[stage]` in the template, and the old keys removed from the row dict entirely.

5. **Alpine `stages` array** is currently hardcoded in the template JS as `stages: ['rules', 'narrate', 'scene', 'state', 'progress']`. This must be replaced with a server-emitted `stage_order` list on each turn row, so adding a stream requires zero JS changes. See Step 2.8.

6. **Pills are already dynamically rendered** — the template loops `seg.lines` and renders whatever keys the server sends. The only change needed is that the server now builds `seg.lines` from descriptor-driven upstream output instead of hardcoded field paths. No new template pill code is needed.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/server/tv_mirror.py` | create | `StreamDescriptor` dataclass + `_STREAMS` list + `STREAM_BY_KEY` + `_get_nested` |
| `ccya/server/tv.py` | rewrite | Delete all hardcoded stream/field logic; loop over `_STREAMS`; build `prompts` dict; `scope` block; `stage_order` list; no compat aliases |
| `ccya/templates/_turn_viewer.html` | modify | Replace `t[stage+'_prompt']` → `t.prompts[stage]`; replace hardcoded `stages` array → `t.stage_order`; add scope display block |
| `docs/REPOMAP/server.md` | update | Document `tv_mirror.py`; update `_turn_viewer_data` description |
| `docs/plans/TODO.md` | update | Mark entry updated with scope/pills note |

## Firm decisions

1. **One place for pipeline topology: `tv_mirror.py`.** tv.py iterates `_STREAMS`; never references a stream key by string literal (except the `_tv_extract_stream_status` carve-out noted above).

2. **`prompts` dict replaces all named prompt keys.** Row dict has `prompts: {"rules": {...}, "narrate": {...}, ...}`. No `rules_prompt`, `narrate_prompt`, etc. anywhere.

3. **`stage_order` list emitted per row** — `[sd.key for sd in _STREAMS]`. Template replaces its hardcoded JS `stages` array with `t.stage_order`.

4. **Connector segments derived entirely from `sd.inputs`.** Each segment's `lines` content = actual upstream output resolved via `inp_sd.prompt_path`. Pills are populated with real output content, not placeholder labels.

5. **Scope rendered as a dedicated block** between the narrate stage and the scene connector. Not inside narrate output. Not inside rules output.

6. **No backwards-compatibility.** Old named prompt keys are gone. Dead variables are deleted. `make check` must pass clean.

7. **`_tv_extract_stream_status` unchanged** except for a clarifying comment.

8. **`extract.streams.*` used only for `total_tt_ms` total time.** Not displayed as a stream card.

---

## Implementation — Phase 1: Create `tv_mirror.py`

### Context files to load
- `ccya/server/tv.py` (current full file — read before touching anything)
- `ccya/eval/engine_mirror.py` (for structural reference)

### Overview
Create `ccya/server/tv_mirror.py`. This is the single source of truth for pipeline topology. Nothing else goes in this file.

### Detailed steps

#### Step 1.1 — Create `ccya/server/tv_mirror.py`

**File:** `ccya/server/tv_mirror.py`

**What:** New module. Copy the snippet below verbatim. Do not add any other functions or imports beyond what is shown.

**Why:** Declaring topology here means tv.py loops a list instead of naming streams.

**Code Snippet**
```python
"""Stream registry for the turn viewer.

Single source of truth for pipeline topology.
Add a StreamDescriptor here to add a new stream to the viewer.
Do not reference stream key strings in tv.py (except _tv_extract_stream_status).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StreamDescriptor:
    key: str
    """Short identifier matching the events.jsonl key (e.g. 'rules', 'scene')."""
    label: str
    """Display label shown in the stage card header."""
    stage_css: str
    """CSS class suffix — must exist in _STAGE_CSS in tv.py."""
    metrics_path: str
    """Dot-separated path into the event dict where tokens/latency live.
    E.g. 'rules', 'narrate', 'extraction.scene'.
    """
    prompt_path: str | None
    """Dot-separated path where rendered_system/rendered_user/output live.
    If None, falls back to metrics_path. Separate from metrics_path because
    'narrate' splits metrics (ev['narrate']) from prompts (ev['narrate_prompt']).
    """
    output_subkey: str | None
    """Key within the prompt blob to find the output value. Typically 'output'."""
    is_text_output: bool
    """True → output is a prose string → pass to _tv_narration_lines.
    False → output is a dict (or JSON string) → pass to _tv_dict_to_lines.
    """
    output_is_json_string: bool
    """True → output_subkey value is a serialized JSON string, json.loads it first.
    Only rules_prompt.output requires this.
    """
    ms_key: str
    """Key within the metrics blob for latency. 'total_ms' for rules/narrate, 'ms' for extraction streams."""
    inputs: list[str]
    """Keys of upstream streams that feed this stream, in order.
    Drives connector segment generation — one pill per entry.
    Must only reference keys with a lower index in _STREAMS (no cycles).
    """
    skip_token_display: bool
    """True → show '—' for tokens/time when stream is skipped (extraction streams only)."""


_STREAMS: list[StreamDescriptor] = [
    StreamDescriptor(
        key="rules",
        label="rules",
        stage_css="rules",
        metrics_path="rules",
        prompt_path="rules_prompt",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=True,   # rules_prompt.output is a serialized JSON string
        ms_key="total_ms",
        inputs=[],
        skip_token_display=False,
    ),
    StreamDescriptor(
        key="narrate",
        label="narrate",
        stage_css="narrate",
        metrics_path="narrate",        # metrics only: total_ms, tokens_in, tokens_out
        prompt_path="narrate_prompt",  # rendered_system, rendered_user, output (prose) here
        output_subkey="output",
        is_text_output=True,           # narrate_prompt.output is plain prose
        output_is_json_string=False,
        ms_key="total_ms",
        inputs=["rules"],
        skip_token_display=False,
    ),
    StreamDescriptor(
        key="scene",
        label="scene",
        stage_css="scene",
        metrics_path="extraction.scene",
        prompt_path="extraction.scene",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=False,   # extraction.scene.output is already a dict
        ms_key="ms",
        inputs=["rules", "narrate"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="state",
        label="state",
        stage_css="state",
        metrics_path="extraction.state",
        prompt_path="extraction.state",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=False,
        ms_key="ms",
        inputs=["rules", "narrate", "scene"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="progress",
        label="progress",
        stage_css="progress",
        metrics_path="extraction.progress",
        prompt_path="extraction.progress",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=False,
        ms_key="ms",
        inputs=["rules", "narrate", "scene", "state"],
        skip_token_display=True,
    ),
]

# O(1) lookup by key. Used by connector generation in tv.py.
STREAM_BY_KEY: dict[str, StreamDescriptor] = {s.key: s for s in _STREAMS}


def _get_nested(d: dict, path: str) -> object:
    """Resolve a dot-separated path into a nested dict.

    Returns None if any key is missing or an intermediate value is not a dict.

    Examples:
        _get_nested({'extraction': {'scene': {'ms': 42}}}, 'extraction.scene') -> {'ms': 42}
        _get_nested({'extraction': {'scene': {'ms': 42}}}, 'extraction.scene.ms') -> 42
        _get_nested({}, 'extraction.scene') -> None
        _get_nested({'a': 'not-a-dict'}, 'a.b') -> None
    """
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)  # type: ignore[union-attr]
    return cur
```

**Validation:**
```bash
python -c "
from ccya.server.tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested
print(len(_STREAMS))          # → 5
print(list(STREAM_BY_KEY))    # → ['rules', 'narrate', 'scene', 'state', 'progress']
print(_get_nested({'extraction': {'scene': {'ms': 42}}}, 'extraction.scene.ms'))  # → 42
print(_get_nested({}, 'extraction.scene'))  # → None
print(_get_nested({'a': 'str'}, 'a.b'))     # → None
"
```
All five assertions must match the expected values shown in comments before proceeding to Phase 2.

### Tests to write or update
Deferred to Phase 2 test file — covered by `test_tv_mirror_completeness` and `test_get_nested_cases`.

### REPOMAP updates required
Deferred to end of Phase 2.

### Risks
1. If a future stream has metrics at one path and prompts at a third path (neither `metrics_path` nor `prompt_path`), the descriptor needs a new slot. Acceptable — add it then. All current streams fit the two-path model.

---

## Implementation — Phase 2: Rewrite `tv.py` + update template

### Context files to load
- `ccya/server/tv.py` (full file — rewrite target)
- `ccya/server/tv_mirror.py` (just created in Phase 1)
- `ccya/templates/_turn_viewer.html` (full file — template update target)
- `ccya/server/metrics.py` (for `_fmt_tokens_exact` signature)

### Overview
Completely rewrite `_turn_viewer_data` in `tv.py` to loop over `_STREAMS`. Delete every hardcoded per-stream variable. Build `prompts` dict, `stage_order` list, and `scope` block. Update the template to consume the new shape. No compat aliases anywhere. All changes land in one PR.

### Detailed steps

#### Step 2.1 — Add import of tv_mirror at top of `tv.py`

**File:** `ccya/server/tv.py`

**What:** Add import after existing imports. Do not remove any existing imports yet — delete dead ones in Step 2.6.

**Code Snippet**
```python
import json as _json
from .tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested
```

**Validation:** `python -c "from ccya.server import tv"` — no ImportError.

---

#### Step 2.2 — Replace stream metric collection loop

**File:** `ccya/server/tv.py`, inside `_turn_viewer_data`, inside the `for line in lines:` event loop.

**What:** Delete these variables entirely (they are replaced by the loop below):
- `narr = ev.get("narrate") or {}`
- `ext = ev.get("extract") or {}`  ← keep only for `ext.get("total_ms")` — see Step 2.3
- `extraction = ev.get("extraction") or {}`
- `rules_ev = ev.get("rules") or {}`
- `rules_prompt = ev.get("rules_prompt") or {}`
- `narr_prompt = ev.get("narrate_prompt") or {}`
- `rules_ev_d = rules_ev if isinstance(rules_ev, dict) else {}`
- `scene_blk`, `state_blk`, `prog_blk`, `scene_out`, `state_out`, `prog_out`
- `raw_streams` dict
- `r_in`, `r_out`, `r_ms`, `n_in`, `n_out`, `n_ms`
- `rules_status`

Replace with:

**Code Snippet**
```python
def _fmt_ms(ms: object) -> str:
    if ms is None:
        return "\u2014"
    try:
        return f"{float(ms) / 1000.0:.1f}s"  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "\u2014"

ej = ev  # alias for clarity — ev is the parsed event dict
rej: list = ej.get("rejected") or []

streams: dict[str, dict] = {}
for sd in _STREAMS:
    blob = _get_nested(ej, sd.metrics_path)
    if not isinstance(blob, dict):
        blob = {}
    t_in = blob.get("tokens_in")
    t_out = blob.get("tokens_out")
    ms_val = blob.get(sd.ms_key)
    skipped = bool(blob.get("skipped", False))
    error = blob.get("error")
    error_s = str(error) if error else None
    attempts = int(blob.get("attempts") or 1)
    retry_errors: list = blob.get("retry_errors") or []
    status = _tv_extract_stream_status(
        sd.key,
        skipped=skipped,
        error=error_s,
        attempts=attempts,
        rejected=rej,
    )
    tok_in_disp = "\u2014" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_in)
    tok_out_disp = "\u2014" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_out)
    streams[sd.key] = {
        "tt": "\u2014" if (skipped and sd.skip_token_display) else _fmt_ms(ms_val),
        "tokens_in": t_in,
        "tokens_out": t_out,
        "tokens_in_display": tok_in_disp,
        "tokens_out_display": tok_out_disp,
        "skipped": skipped,
        "error": error_s,
        "attempts": attempts,
        "retry_errors": retry_errors,
        "status": status,
        "status_class": _STATUS_CSS.get(status, "tv-sts-ok"),
        "stage_class": _STAGE_CSS.get(sd.stage_css, ""),
    }
```

Note: `_fmt_ms` was previously defined inline inside `_turn_viewer_data` as a nested function. It stays there (same location in the event loop).

**Validation:** Server starts. All five stage cards appear in the turn viewer with non-empty status badges.

---

#### Step 2.3 — Token bar calculation

**File:** `ccya/server/tv.py`

**What:** Replace any hardcoded stream-name list in the token bar loop with `for sd in _STREAMS`.

**Code Snippet**
```python
token_sums: list[int] = []
for sd in _STREAMS:
    tin = int(streams[sd.key].get("tokens_in") or 0)
    tout = int(streams[sd.key].get("tokens_out") or 0)
    sm = tin + tout
    streams[sd.key]["token_sum"] = sm
    token_sums.append(sm)
max_sum = max(token_sums, default=1) or 1
for sd in _STREAMS:
    sm = streams[sd.key]["token_sum"]
    streams[sd.key]["token_bar_pct"] = round(100.0 * sm / float(max_sum), 1)
```

**Also update `total_tt_ms` and totals:**
```python
ext_blob = ej.get("extract") or {}
total_tt_ms = sum(
    ((_get_nested(ej, sd.metrics_path) or {}).get(sd.ms_key) or 0)
    for sd in _STREAMS
)
# total_in / total_out: sum tokens across all streams
total_in = sum(int(streams[sd.key].get("tokens_in") or 0) for sd in _STREAMS)
total_out = sum(int(streams[sd.key].get("tokens_out") or 0) for sd in _STREAMS)
```

Delete the old `ext.get("total_ms")` usage and the manual `(r_ms or 0) + (n_ms or 0) + ...` lines.

**Validation:** Total time and token counts in the turn card header are correct.

---

#### Step 2.4 — Build `prompts` dict

**File:** `ccya/server/tv.py`

**What:** Build `prompts: dict[str, dict[str, str]]` keyed by stream key. This replaces `rules_prompt`, `narrate_prompt`, `scene_prompt`, `state_prompt`, `progress_prompt` in the row dict — those keys are deleted entirely.

**Code Snippet**
```python
prompts: dict[str, dict[str, str]] = {}
for sd in _STREAMS:
    p_path = sd.prompt_path if sd.prompt_path is not None else sd.metrics_path
    p_blob = _get_nested(ej, p_path)
    if not isinstance(p_blob, dict):
        p_blob = {}
    raw_out = p_blob.get(sd.output_subkey) if sd.output_subkey else None

    if streams[sd.key]["skipped"] and sd.skip_token_display:
        out_str = ""
    elif sd.is_text_output:
        out_str = str(raw_out or "")
    elif sd.output_is_json_string and isinstance(raw_out, str):
        try:
            parsed = _json.loads(raw_out)
            out_str = _json.dumps(parsed, indent=2) if isinstance(parsed, dict) else raw_out
        except Exception:
            out_str = raw_out
    elif isinstance(raw_out, dict):
        out_str = _json.dumps(raw_out, indent=2)
    else:
        out_str = str(raw_out or "")

    prompts[sd.key] = {
        "system": p_blob.get("rendered_system") or "",
        "user": p_blob.get("rendered_user") or "",
        "output": out_str,
    }
```

**Validation:** Prompt tabs render for all five stages. Rules output tab shows formatted JSON. Narrate output tab shows prose. Extraction output tabs show indented JSON dicts.

---

#### Step 2.5 — Connector generation from `sd.inputs`

**File:** `ccya/server/tv.py`

**What:** Delete the four hardcoded `*_segments` lists and the `_rules_seg` inner function. Replace with a loop over `_STREAMS`.

Each segment's `lines` content is the actual output of the upstream stream, rendered the same way the prompts builder works.

**Code Snippet**
```python
connectors: list[dict] = []
for sd in _STREAMS:
    if not sd.inputs:
        continue
    segments: list[dict] = []
    for inp_key in sd.inputs:
        inp_sd = STREAM_BY_KEY.get(inp_key)
        if inp_sd is None:
            continue
        # Resolve upstream output for display in the pill
        inp_p_path = inp_sd.prompt_path if inp_sd.prompt_path is not None else inp_sd.metrics_path
        inp_p_blob = _get_nested(ej, inp_p_path)
        if not isinstance(inp_p_blob, dict):
            inp_p_blob = {}
        raw_out = inp_p_blob.get(inp_sd.output_subkey) if inp_sd.output_subkey else None

        if inp_sd.is_text_output:
            lines = _tv_narration_lines(str(raw_out or ""))
        elif inp_sd.output_is_json_string and isinstance(raw_out, str):
            try:
                parsed = _json.loads(raw_out)
                lines = _tv_dict_to_lines(parsed) if isinstance(parsed, dict) else []
            except Exception:
                lines = []
        elif isinstance(raw_out, dict):
            lines = _tv_dict_to_lines(raw_out)
        else:
            lines = []

        segments.append({
            "from": inp_key,
            "label": f"{inp_key} \u2192 {sd.key}",
            "lines": lines,
            "anchor": inp_key,
            "upstream_status": streams[inp_key]["status"],
            "upstream_status_class": streams[inp_key]["status_class"],
        })
    if segments:
        connectors.append({"before_stage": sd.key, "segments": segments})
```

**Validation:** Connector pills appear between all stages. Narrate connector pill shows rules intent JSON keys. Scene connector shows both rules and narrate pills. State connector shows three pills. Progress connector shows four pills.

---

#### Step 2.6 — Scope block

**File:** `ccya/server/tv.py`

**What:** Extract `scope` from the top-level event and build a structured display block.

**Code Snippet**
```python
raw_scope = ej.get("scope") or {}
scope_block: dict[str, object] = {
    "active_domains": raw_scope.get("active_domains") or [],
    "decided_by": raw_scope.get("decided_by") or "\u2014",
    "skipped_streams": raw_scope.get("skipped_streams") or [],
}
```

Include `"scope": scope_block` and `"stage_order": [sd.key for sd in _STREAMS]` in `rows.append({...})`. Also include `"prompts": prompts` and remove ALL five named `*_prompt` keys. The `rows.append` block should look like:

```python
rows.append({
    "turn": ej.get("turn", 0),
    "trace_id": tid[:8] if len(tid) >= 8 else tid,
    "trace_id_full": tid,
    "has_rejections": bool(rej),
    "has_retries": has_retries,
    "has_errors": has_errors,
    "has_skipped": has_skipped,
    "streams": streams,
    "connectors": connectors,
    "prompts": prompts,          # NEW — replaces rules_prompt, narrate_prompt, etc.
    "stage_order": [sd.key for sd in _STREAMS],   # NEW — drives Alpine stages array
    "rules_event": rules_ev_d if 'rules_ev_d' in dir() else {},  # see Step 2.7
    "rules_intent": rules_intent,
    "state_rejections": state_rej,
    "scope": scope_block,         # NEW
    "total_tt": _fmt_ms(total_tt_ms),
    "total_tokens_in": total_in,
    "total_tokens_out": total_out,
    "total_tokens_in_display": _fmt_tokens_exact(total_in),
    "total_tokens_out_display": _fmt_tokens_exact(total_out),
    "user_input": ej.get("input", ""),
})
```

Note: `rules_ev_d` (used by `rules_event` and `rules_intent`) must still be set before this block. Set it as:
```python
rules_raw = _get_nested(ej, "rules")
rules_ev_d: dict = rules_raw if isinstance(rules_raw, dict) else {}
rules_intent = _tv_parse_json_blob(prompts["rules"]["output"])
```

`state_rej` and `has_*` flags use the same logic as before, but replace the hardcoded stream name lists with `_STREAMS` loops:
```python
state_rej = [
    r for r in rej
    if isinstance(r, dict) and r.get("field") == "inventory_remove"
]
has_retries = any(int(streams[sd.key].get("attempts") or 1) > 1 for sd in _STREAMS)
has_errors = any(bool(streams[sd.key].get("error")) for sd in _STREAMS)
has_skipped = any(streams[sd.key].get("skipped") for sd in _STREAMS)
```

**Validation:** Row dict has `prompts`, `stage_order`, `scope` keys. No `rules_prompt`, `narrate_prompt`, `scene_prompt`, `state_prompt`, `progress_prompt` keys anywhere in the row dict.

---

#### Step 2.7 — Delete all dead code from `tv.py`

**File:** `ccya/server/tv.py`

**What:** After Steps 2.1–2.6, the following must not exist anywhere in the file:
- Variables: `narr`, `narr_text`, `narr_prompt`, `rules_prompt`, `scene_blk`, `state_blk`, `prog_blk`, `scene_out`, `state_out`, `prog_out`, `raw_streams`, `r_in`, `r_out`, `r_ms`, `n_in`, `n_out`, `n_ms`, `rules_status`, `ext` (beyond the delete in 2.3)
- Inner functions: `_rules_seg` (if still present)
- Any named connector list: `scene_segments`, `state_segments`, `progress_segments`
- Old `rows.append({...})` keys: `rules_prompt`, `narrate_prompt`, `scene_prompt`, `state_prompt`, `progress_prompt`

**Why:** Dead code policy. Ruff `F841` will catch unused variable assignments. `make check` must pass clean.

**Validation:** Run `make check`. Zero ruff errors. Zero mypy errors. If any `F841` or undefined name errors appear, fix them before proceeding.

---

#### Step 2.8 — Update `ccya/templates/_turn_viewer.html`

**File:** `ccya/templates/_turn_viewer.html`

**What:** Three changes to the template:

**Change A — Replace hardcoded `stages` array in Alpine JS with server-driven `stage_order`.**

Find this line in the `tvRoot` function:
```javascript
stages: ['rules', 'narrate', 'scene', 'state', 'progress'],
```
Replace with:
```javascript
stages: (initialTurns && initialTurns.length ? initialTurns[0].stage_order : ['rules', 'narrate', 'scene', 'state', 'progress']),
```
The fallback array is a safety net for the empty-turns case. It will never be used in practice.

**Change B — Replace all `t[stage + '_prompt']` references with `t.prompts[stage]`.**

The template uses `t[stage + '_prompt']` in several places:
1. The outer `x-show` guard: `t[stage + '_prompt'] && (t[stage + '_prompt'].system || ...)` → `t.prompts[stage] && (t.prompts[stage].system || ...)`
2. Prompt tab buttons visibility check: same pattern — replace.
3. System prompt block: `t[stage + '_prompt'].system` → `t.prompts[stage].system`
4. User prompt block: `t[stage + '_prompt'].user` → `t.prompts[stage].user`
5. `mdNarrative(t)` function in JS: `t.narrate_prompt && t.narrate_prompt.output` → `t.prompts && t.prompts.narrate && t.prompts.narrate.output`
6. Output tab: `t[stage + '_prompt'].output` → `t.prompts[stage].output`
7. No-data guard: `!t[stage + '_prompt'] || ...` → `!t.prompts[stage] || ...`

Search for every occurrence of `_prompt` in the template and replace. There must be zero remaining occurrences of `_prompt` after this step.

**Change C — Add scope display block between narrate stage and first extraction connector.**

The scope block belongs after the narrate stage card renders and before the scene connector pills. The `x-for="stage in stages"` loop already handles ordering — scope is NOT a stage, so it must be injected as a conditional block inside the loop.

Inside the `<template x-for="stage in stages">` loop, after the stage card `<div class="tv-pipeline-stage" ...>` closes, add:

```html
<template x-if="stage === 'narrate' && t.scope">
    <div class="tv-scope-block">
        <div class="tv-scope-header">scope</div>
        <div class="tv-scope-row">
            <span class="tv-scope-label">decided_by</span>
            <span class="tv-scope-value" x-text="t.scope.decided_by"></span>
        </div>
        <div class="tv-scope-row" x-show="t.scope.active_domains && t.scope.active_domains.length">
            <span class="tv-scope-label">active_domains</span>
            <span class="tv-scope-value">
                <template x-for="d in t.scope.active_domains" :key="d">
                    <span class="tv-scope-tag" x-text="d"></span>
                </template>
            </span>
        </div>
        <div class="tv-scope-row" x-show="t.scope.skipped_streams && t.scope.skipped_streams.length">
            <span class="tv-scope-label">skipped</span>
            <span class="tv-scope-value tv-scope-muted" x-text="t.scope.skipped_streams.join(', ')"></span>
        </div>
    </div>
</template>
```

The CSS classes `tv-scope-block`, `tv-scope-header`, `tv-scope-row`, `tv-scope-label`, `tv-scope-value`, `tv-scope-tag`, `tv-scope-muted` must either already exist in `app.css` or be added. If they do not exist, add minimal styles in a `<style>` block at the top of the template or add them to `app.css`. The block should visually resemble the existing connector pill blocks — compact, labeled, muted border.

**Validation:**
1. Load the turn viewer. No Jinja `UndefinedError`.
2. All five stage cards have working Prompt / Output tabs.
3. Scope block appears between narrate card and scene connector pills, showing `decided_by`, `active_domains` tags, and `skipped` streams.
4. Search the rendered HTML source for `_prompt` — must be zero occurrences.
5. `stage_order` from the row drives the stage list — if you temporarily add a sixth descriptor to `_STREAMS` in tv_mirror.py, a sixth card appears without any JS change (then revert).

---

### Tests to write or update

**File:** `tests/test_turn_viewer.py` (create)

**`test_tv_mirror_completeness`**
```python
from ccya.server.tv_mirror import _STREAMS, STREAM_BY_KEY

def test_tv_mirror_completeness():
    assert len(_STREAMS) == 5
    assert list(STREAM_BY_KEY) == [s.key for s in _STREAMS]
    assert len(set(s.key for s in _STREAMS)) == len(_STREAMS)  # no duplicates
```

**`test_get_nested_cases`**
```python
from ccya.server.tv_mirror import _get_nested

def test_get_nested_cases():
    d = {"a": {"b": {"c": 99}}}
    assert _get_nested(d, "a.b.c") == 99
    assert _get_nested(d, "a.b") == {"c": 99}
    assert _get_nested(d, "a.x") is None
    assert _get_nested(d, "z") is None
    assert _get_nested({}, "a.b") is None
    assert _get_nested({"a": "not-a-dict"}, "a.b") is None
    assert _get_nested({"a": 1}, "a") == 1
```

**`test_tv_mirror_inputs_acyclic`**
```python
def test_tv_mirror_inputs_acyclic():
    keys = [s.key for s in _STREAMS]
    for i, sd in enumerate(_STREAMS):
        assert sd.key not in sd.inputs, f"{sd.key} references itself"
        for inp in sd.inputs:
            assert inp in keys, f"{sd.key} input '{inp}' not in _STREAMS"
            assert keys.index(inp) < i, f"{sd.key} input '{inp}' has higher index (cycle)"
```

**`test_turn_viewer_data_empty`**
```python
from pathlib import Path
from ccya.server.tv import _turn_viewer_data

def test_turn_viewer_data_empty(tmp_path):
    rows, no_events = _turn_viewer_data(tmp_path)
    assert rows == []
    assert no_events is True
```

**`test_turn_viewer_data_minimal_event`**
```python
import json

def test_turn_viewer_data_minimal_event(tmp_path):
    ev = {
        "turn": 1, "trace_id": "abcdef1234567890", "input": "go north",
        "rejected": [], "scope": {"active_domains": [], "decided_by": "narrator", "skipped_streams": []},
    }
    (tmp_path / "events.jsonl").write_text(json.dumps(ev) + "\n")
    rows, no_events = _turn_viewer_data(tmp_path)
    assert no_events is False
    assert len(rows) == 1
    row = rows[0]
    assert set(row["streams"].keys()) == {"rules", "narrate", "scene", "state", "progress"}
    for key in ("rules", "narrate", "scene", "state", "progress"):
        assert "status" in row["streams"][key]
        assert "status_class" in row["streams"][key]
        assert "stage_class" in row["streams"][key]
    assert "prompts" in row
    assert set(row["prompts"].keys()) == {"rules", "narrate", "scene", "state", "progress"}
    assert row["scope"]["active_domains"] == []
    assert row["scope"]["decided_by"] == "narrator"
    assert row["stage_order"] == ["rules", "narrate", "scene", "state", "progress"]
```

**`test_turn_viewer_data_scope_and_skipped`**
```python
def test_turn_viewer_data_scope_and_skipped(tmp_path):
    ev = {
        "turn": 1, "trace_id": "aaaa1111bbbb2222", "input": "look around",
        "rejected": [],
        "rules": {"total_ms": 800, "tokens_in": 1000, "tokens_out": 50},
        "narrate": {"total_ms": 1200, "tokens_in": 2000, "tokens_out": 300},
        "narrate_prompt": {"rendered_system": "sys", "rendered_user": "usr", "output": "You look around."},
        "extraction": {
            "scene": {"ms": 500, "tokens_in": 800, "tokens_out": 100, "skipped": False, "attempts": 1, "retry_errors": [], "output": {"location": "docks"}},
            "state": {"ms": 0, "tokens_in": 0, "tokens_out": 0, "skipped": True, "attempts": 0, "retry_errors": [], "output": {}},
            "progress": {"ms": 400, "tokens_in": 700, "tokens_out": 80, "skipped": False, "attempts": 1, "retry_errors": [], "output": {"quests": []}},
        },
        "scope": {"active_domains": ["scene", "progress"], "decided_by": "narrator", "skipped_streams": ["state"]},
    }
    (tmp_path / "events.jsonl").write_text(json.dumps(ev) + "\n")
    rows, _ = _turn_viewer_data(tmp_path)
    row = rows[0]
    # State is skipped — tokens should display as em-dash
    assert row["streams"]["state"]["skipped"] is True
    assert row["streams"]["state"]["tokens_in_display"] == "\u2014"
    # Scope populated correctly
    assert row["scope"]["active_domains"] == ["scene", "progress"]
    assert row["scope"]["skipped_streams"] == ["state"]
    # Connectors: 4 entries (narrate, scene, state, progress each have inputs)
    assert len(row["connectors"]) == 4
    # Narrate connector: one segment from rules
    narrate_conn = next(c for c in row["connectors"] if c["before_stage"] == "narrate")
    assert len(narrate_conn["segments"]) == 1
    assert narrate_conn["segments"][0]["from"] == "rules"
    # Scene connector: two segments — rules and narrate
    scene_conn = next(c for c in row["connectors"] if c["before_stage"] == "scene")
    assert [s["from"] for s in scene_conn["segments"]] == ["rules", "narrate"]
    # Narrate prompt output in prompts dict
    assert row["prompts"]["narrate"]["output"] == "You look around."
```

### REPOMAP updates required

**`docs/REPOMAP/server.md`** — add/update:
- `tv_mirror.py`: exports `StreamDescriptor` (frozen dataclass with fields: `key`, `label`, `stage_css`, `metrics_path`, `prompt_path`, `output_subkey`, `is_text_output`, `output_is_json_string`, `ms_key`, `inputs`, `skip_token_display`); exports `_STREAMS` (list of 5 descriptors in pipeline order); `STREAM_BY_KEY` (O(1) dict); `_get_nested(d, path)` (dot-path resolver)
- `tv.py` / `_turn_viewer_data`: update description to: "builds `streams` dict by iterating `_STREAMS`; `prompts` dict keyed by stream key replaces all named `*_prompt` keys; `scope` block from top-level event key; `stage_order` list emitted per row; connectors derived from `sd.inputs`"

### Risks
1. **Template update and tv.py rewrite must land in the same commit.** If tv.py is pushed first without the template update, the server 500s on turn viewer load because `t[stage + '_prompt']` references undefined keys. Mitigation: use `push_files` to commit both files atomically.
2. **`_tv_extract_stream_status` hardcodes the string `"state"`.** This is the only remaining hardcoded stream name in tv.py. Add comment: `# NOTE: stream key "state" hardcoded here; if renamed, update this check`. Do not generalize it — the logic is specific to state stream inventory rejection semantics.
3. **Alpine `mdNarrative` function** accesses `t.narrate_prompt.output` directly by name. This is in the JS block, not a Jinja template expression. It must be updated to `t.prompts.narrate.output` in the same Step 2.8 pass. Search for `narrate_prompt` in the `<script>` block specifically.
4. **`rules_event` in the template** — the template renders `t.rules_event` (the raw rules dict) and `t.rules_intent` (parsed JSON). These are kept in the row dict unchanged. The `rules_ev_d` variable is still needed; Step 2.6 shows how to set it via `_get_nested`.

## Ambiguities requiring resolution before execution
None. All ambiguities from prior drafts have been resolved by reading source. See the "Resolved ambiguities" section above.

## TODO.md update

The entry already exists under `## Debug / Tooling`. Update it to:

```
- [ ] **Turn viewer dynamic mirror** — schema-driven tv.py; stream registry in `tv_mirror.py`; connectors + pills from `sd.inputs`; scope block; `stage_order` drives Alpine — see [`turn-viewer-dynamic.md`](turn-viewer-dynamic.md)
```
