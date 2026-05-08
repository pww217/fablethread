# Turn Viewer — Dynamic Engine Mirror

## Status
`open`

## Part of
standalone

## Dependencies
- none — but note: `narrator-driven-scope.md` and `narration-active-domains.md` are open plans that will change the narration block and scope placement. This plan must be sequenced AFTER those land (or at least after the narrate_prompt output structure stabilizes), otherwise the scope rendering added here will need re-work.

## Objective
`server/tv.py` hardcodes the names, keys, and structure of every turn pipeline stage. When the engine changes — fields move, new streams are added, output models evolve — tv.py silently breaks or misses data. The narration-driven-scope work is one example: scope moved into the narration block but tv.py still looks for it in old positions. The fix is to make tv.py drive its display from the engine's own models and a declarative stream registry, the same way `eval/engine_mirror.py` drives eval from live engine constants. After this plan, adding a new extraction stream or moving a field requires changing the engine + its model only; tv.py adapts automatically.

## Non-goals
- Does NOT change the events.jsonl schema or what the engine writes.
- Does NOT change the turn_viewer Jinja template structure beyond what's needed to consume the new row shape.
- Does NOT add new debug panels or new routes.
- Does NOT touch eval/ code.
- Does NOT make tv.py aware of every possible field in every Pydantic model — it reflects the JSON keys that are actually present in events.jsonl per-turn, not a static schema.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/server/tv.py` | modify | Replace hardcoded stream list + field extraction with a declarative `_STREAMS` registry and reflection-based output rendering |
| `ccya/server/tv_mirror.py` | create | New module: imports engine stream names from engine_mirror / models; defines `_STREAMS` descriptor list that tv.py consumes |
| `docs/REPOMAP/server.md` | update | Document `tv_mirror.py` and updated `_turn_viewer_data` signature/behavior |
| `docs/plans/TODO.md` | update | Add this plan under a new `## Debug / Tooling` section |

## Firm decisions

1. **Streams are declared in one place (`tv_mirror.py`), not scattered through `tv.py`.** Each stream descriptor says: its key in `events.jsonl`, its display name, its stage CSS class, how to get `tokens_in`/`tokens_out`/`ms` from the event dict, and whether it is an extraction sub-stream. `tv.py` iterates `_STREAMS` — it never mentions individual stream names.

2. **Output blocks are rendered generically.** For each stream, the output blob is extracted from the event dict at the path described in its descriptor (e.g. `extraction.scene.output`, `narrate_prompt.output`). It is then passed to the existing `_tv_dict_to_lines` (if dict) or `_tv_narration_lines` (if string). No per-stream bespoke handling except for the narration text preview, which stays in a helper because it needs char count.

3. **Connector segments are generated from the stream dependency graph, not hardcoded.** Each stream descriptor declares `inputs: list[str]` — the upstream stream names that feed it. `_turn_viewer_data` generates connector segments by iterating those inputs rather than via four separate hardcoded `*_segments` lists.

4. **Scope (and any other field that moves) is located via event JSON traversal, not by hardcoded key path.** The narrate block output is rendered as a string preview (unchanged); if scope appears inside the narration block's JSON output, it will appear there naturally when the block is rendered via `_tv_dict_to_lines`. No special-casing for `scope` anywhere in tv.py.

5. **`_STREAMS` is the only place that needs updating when a stream is added or removed.** It lives in `tv_mirror.py` so it can import from engine modules without pulling FastAPI dependencies into the engine.

6. **Status logic stays in tv.py** as `_tv_extract_stream_status` — it's presentation logic, not engine knowledge.

7. **No backwards-compatibility shims.** Old hardcoded keys are deleted, not wrapped. Events written before this change will render with whatever fields they have; missing fields gracefully produce `∅` via `_tv_dict_to_lines`.

---

## Implementation — Phase 1: `tv_mirror.py` stream registry

### Context files to load
- `ccya/server/tv.py`
- `ccya/eval/engine_mirror.py`
- `ccya/models.py` (skim for `SceneExtractResult`, `StateExtractResult`, `ProgressExtractResult` field names)

### Overview
Create `ccya/server/tv_mirror.py`. It imports `EXTRACT_STREAMS` from `eval/engine_mirror.py` for reference, then defines `_STREAMS: list[StreamDescriptor]` — one entry per turn-pipeline stage. Each descriptor is a typed dataclass. Nothing else is in this file.

### Detailed steps

#### Step 1.1 — Define `StreamDescriptor` and `_STREAMS`

**File:** `ccya/server/tv_mirror.py`

**What:** New module with a `StreamDescriptor` dataclass and the `_STREAMS` list. Each descriptor carries:
- `key: str` — the stream's name (used as dict key in the `streams` dict returned by `_turn_viewer_data`)
- `label: str` — human-readable display name
- `stage_css: str` — CSS class key (maps to `_STAGE_CSS` in tv.py)
- `event_path: str` — dot-separated path into the event dict to reach the stream's metrics/output block (e.g. `"narrate"`, `"extraction.scene"`, `"rules"`)
- `output_subkey: str | None` — if the output is nested under an `output` subkey (extraction streams), set to `"output"`; if the output IS the whole blob (rules event), set to `None`; if the output is a rendered text field in a prompt sub-dict, set to the key name (e.g. `"output"` for narrate_prompt)
- `output_event_path: str | None` — separate dot-path for output if different from metrics path (narrate output lives in `narrate_prompt`, not `narrate`)
- `is_text_output: bool` — True means use `_tv_narration_lines`, False means use `_tv_dict_to_lines`
- `ms_key: str` — key for latency within the metrics blob (default `"ms"`, rules uses `"total_ms"`)
- `inputs: list[str]` — upstream stream keys that feed this stream (drives connector generation)
- `skip_token_display: bool` — if True, token display shows `—` when skipped (extraction streams)

**Why:** Centralizes all stream topology. Adding a new extraction stream is one new `StreamDescriptor` entry.

**Code Snippet**
```python
"""Stream registry for turn viewer — single source of truth for pipeline topology.

Import from here in tv.py. Do not hardcode stream names or event paths in tv.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StreamDescriptor:
    key: str
    label: str
    stage_css: str
    event_path: str
    output_subkey: str | None = "output"
    output_event_path: str | None = None
    is_text_output: bool = False
    ms_key: str = "ms"
    inputs: list[str] = field(default_factory=list)
    skip_token_display: bool = False


_STREAMS: list[StreamDescriptor] = [
    StreamDescriptor(
        key="rules",
        label="rules",
        stage_css="rules",
        event_path="rules",
        output_subkey=None,
        ms_key="total_ms",
        inputs=[],
    ),
    StreamDescriptor(
        key="narrate",
        label="narrate",
        stage_css="narrate",
        event_path="narrate",
        output_subkey=None,
        output_event_path="narrate_prompt",
        is_text_output=True,
        inputs=["rules"],
    ),
    StreamDescriptor(
        key="scene",
        label="scene",
        stage_css="scene",
        event_path="extraction.scene",
        output_subkey="output",
        inputs=["rules", "narrate"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="state",
        label="state",
        stage_css="state",
        event_path="extraction.state",
        output_subkey="output",
        inputs=["rules", "narrate", "scene"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="progress",
        label="progress",
        stage_css="progress",
        event_path="extraction.progress",
        output_subkey="output",
        inputs=["rules", "narrate", "scene", "state"],
        skip_token_display=True,
    ),
]

# Lookup by key — used by tv.py for O(1) descriptor access.
STREAM_BY_KEY: dict[str, StreamDescriptor] = {s.key: s for s in _STREAMS}
```

**Validation:** `python -c "from ccya.server.tv_mirror import _STREAMS, STREAM_BY_KEY; print(len(_STREAMS))"` prints `5`.

---

#### Step 1.2 — Add a `_get_nested` helper

**File:** `ccya/server/tv_mirror.py` (append)

**What:** A small utility that resolves a dot-path into an event dict. Used by tv.py to avoid `event.get("extraction", {}).get("scene", {})` chains.

**Why:** Single utility for path resolution. `tv.py` will call this for every stream's metrics and output blobs.

**Code Snippet**
```python
def _get_nested(d: dict, path: str) -> dict | str | None:
    """Resolve a dot-path into a nested dict. Returns None if any key is missing."""
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur  # type: ignore[return-value]
```

**Validation:** `python -c "from ccya.server.tv_mirror import _get_nested; print(_get_nested({'a': {'b': 1}}, 'a.b'))"` prints `1`.

---

### Tests to write or update
No new tests needed for this phase — `tv_mirror.py` has no logic beyond data definitions and a trivial dict traversal. `test_eval_schema.py` is unaffected. A brief smoke test is sufficient at integration time (Phase 2 validation).

### REPOMAP updates required
Deferred to end of Phase 2 (single update when both phases are complete).

### Risks
1. `output_event_path` vs `event_path` duality is a footgun if a future stream has a third path for output. Mitigation: if that case ever arises, add an `output_keys_path: str | None` field then; for now the two-path model covers all current streams cleanly.

---

## Implementation — Phase 2: Rewrite `tv.py` to use `tv_mirror`

### Context files to load
- `ccya/server/tv.py` (full file)
- `ccya/server/tv_mirror.py` (just created)
- `ccya/server/metrics.py` (for `_fmt_tokens_exact` import)

### Overview
Replace the hardcoded per-stream blocks in `_turn_viewer_data` with a loop over `_STREAMS`. The connector generation loop replaces the four bespoke `*_segments` lists. The `stream_dict` per event is built once generically. Bespoke helpers (`_tv_narration_lines`, `_tv_dict_to_lines`, `_tv_extract_stream_status`) are retained unchanged.

### Detailed steps

#### Step 2.1 — Replace stream metric collection

**File:** `ccya/server/tv.py`

**What:** Replace the four bespoke blocks that build `streams["rules"]`, `streams["narrate"]`, `streams["scene/state/progress"]` with a single loop over `_STREAMS`.

**Why:** Removing the hardcoded stream names makes the loop automatically cover new streams.

**Code Snippet**
```python
# At top of file, add:
from .tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested

# In _turn_viewer_data, replace the per-stream build blocks with:
streams: dict[str, dict[str, Any]] = {}
for sd in _STREAMS:
    blob = _get_nested(ev, sd.event_path) or {}
    if not isinstance(blob, dict):
        blob = {}
    t_in = blob.get("tokens_in")
    t_out = blob.get("tokens_out")
    ms_val = blob.get(sd.ms_key)
    skipped = bool(blob.get("skipped", False))
    error = blob.get("error")
    error_s = str(error) if error else None
    attempts = int(blob.get("attempts") or 1)
    retry_errors = blob.get("retry_errors") or []
    status = _tv_extract_stream_status(
        sd.key,
        skipped=skipped,
        error=error_s,
        attempts=attempts,
        rejected=rej if isinstance(rej, list) else [],
    )
    streams[sd.key] = {
        "tt": "—" if (skipped and sd.skip_token_display) else _fmt_ms(ms_val),
        "tokens_in": t_in,
        "tokens_out": t_out,
        "tokens_in_display": "—" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_in),
        "tokens_out_display": "—" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_out),
        "skipped": skipped,
        "error": error_s,
        "attempts": attempts,
        "retry_errors": retry_errors,
        "status": status,
        "status_class": _STATUS_CSS.get(status, "tv-sts-ok"),
        "stage_class": _STAGE_CSS.get(sd.stage_css, ""),
    }
```

**Validation:** Server starts, `/turn_viewer` loads, stream cards appear for rules/narrate/scene/state/progress.

---

#### Step 2.2 — Replace token sum and bar pct calculation

**File:** `ccya/server/tv.py`

**What:** Replace the hardcoded `for stg in ("rules", "narrate", "scene", "state", "progress")` loop with `for sd in _STREAMS`.

**Code Snippet**
```python
token_sums: list[int] = []
for sd in _STREAMS:
    tin = streams[sd.key].get("tokens_in") or 0
    tout = streams[sd.key].get("tokens_out") or 0
    sm = int(tin) + int(tout)
    token_sums.append(sm)
    streams[sd.key]["token_sum"] = sm
max_sum = max(token_sums) if token_sums else 1
if max_sum < 1:
    max_sum = 1
for sd in _STREAMS:
    sm = int(streams[sd.key]["token_sum"])
    streams[sd.key]["token_bar_pct"] = round(100.0 * sm / float(max_sum), 1)
```

**Validation:** Token bars render with correct proportions.

---

#### Step 2.3 — Replace connector generation

**File:** `ccya/server/tv.py`

**What:** Replace the four hardcoded `*_segments` lists + `connectors.append(...)` calls with a loop over `_STREAMS` that uses `sd.inputs` to derive segments.

**Why:** When a new stream is added with `inputs=["rules", "narrate", "scene"]`, its connector panel appears with zero changes to tv.py.

**Code Snippet**
```python
connectors: list[dict[str, Any]] = []
for sd in _STREAMS:
    if not sd.inputs:
        continue
    segments: list[dict[str, Any]] = []
    for inp_key in sd.inputs:
        inp_sd = STREAM_BY_KEY.get(inp_key)
        if inp_sd is None:
            continue
        inp_blob = _get_nested(ev, inp_sd.event_path) or {}
        if not isinstance(inp_blob, dict):
            inp_blob = {}
        # Resolve output for this upstream stream
        out_path = inp_sd.output_event_path or inp_sd.event_path
        out_blob = _get_nested(ev, out_path) or {}
        if not isinstance(out_blob, dict):
            out_blob = {}
        if inp_sd.output_subkey:
            out_val = out_blob.get(inp_sd.output_subkey) if isinstance(out_blob, dict) else None
        else:
            out_val = out_blob  # the whole blob is the output (rules)
        if inp_sd.is_text_output:
            out_text = str(out_blob.get("output") or "") if isinstance(out_blob, dict) else ""
            lines = _tv_narration_lines(out_text)
        elif isinstance(out_val, dict):
            lines = _tv_dict_to_lines(out_val)
        else:
            lines = _tv_dict_to_lines(
                {k: v for k, v in out_blob.items()
                 if k not in ("tokens_in", "tokens_out", "total_ms", "ms")}
            ) if isinstance(out_blob, dict) else []
        segments.append({
            "from": inp_key,
            "label": f"{inp_key} → {sd.key}",
            "lines": lines,
            "anchor": inp_key,
            "upstream_status": streams[inp_key]["status"],
            "upstream_status_class": streams[inp_key]["status_class"],
        })
    connectors.append({"before_stage": sd.key, "segments": segments})
```

**Validation:** Connector panels render. Rules → narrate connector shows intent envelope. Narrate → scene/state/progress shows narration preview. Scene → state, scene → progress, state → progress show output dicts.

---

#### Step 2.4 — Replace per-stream prompt dict building in the row

**File:** `ccya/server/tv.py`

**What:** Replace the six hardcoded `*_prompt` keys in the `rows.append(...)` dict with a generic `prompts` dict keyed by stream name.

**Why:** New streams automatically get a prompt tab in the viewer.

**Code Snippet**
```python
# Build prompts dict generically
prompts: dict[str, dict[str, str]] = {}
for sd in _STREAMS:
    prompt_path = sd.output_event_path or sd.event_path
    prompt_blob = _get_nested(ev, prompt_path) or {}
    if not isinstance(prompt_blob, dict):
        prompt_blob = {}
    out_val = prompt_blob.get("output") if isinstance(prompt_blob, dict) else None
    if isinstance(out_val, dict):
        out_str = json.dumps(out_val, indent=2)
    else:
        out_str = str(out_val or "")
    # For extraction streams, suppress output display when skipped
    if sd.skip_token_display and streams[sd.key].get("skipped"):
        out_str = ""
    prompts[sd.key] = {
        "system": prompt_blob.get("rendered_system", "") if isinstance(prompt_blob, dict) else "",
        "user": prompt_blob.get("rendered_user", "") if isinstance(prompt_blob, dict) else "",
        "output": out_str,
    }

# In rows.append({...}), replace the six *_prompt keys with:
# "prompts": prompts,
# Keep backwards-compat keys for template until template is updated:
# "rules_prompt": prompts["rules"],
# "narrate_prompt": prompts["narrate"],
# "scene_prompt": prompts["scene"],
# "state_prompt": prompts["state"],
# "progress_prompt": prompts["progress"],
```

**Note:** Keep the five named keys in the row dict alongside `prompts` until the Jinja template is confirmed to use `prompts[key]` notation. Remove them in a follow-up cleanup once the template is updated.

**Validation:** Prompt tabs in the turn viewer show system/user/output for all five streams.

---

#### Step 2.5 — Delete hardcoded remnants

**File:** `ccya/server/tv.py`

**What:** Delete the now-dead variables: `rules_ev_d`, `scene_blk`, `state_blk`, `prog_blk`, `scene_out`, `state_out`, `prog_out`, `raw_streams`, `r_in`, `r_out`, `r_ms`, `n_in`, `n_out`, `n_ms`, `rules_status`, `narr_text` (unless still needed for total calc), and the `_rules_seg` inner function.

**Why:** Dead code policy — remove it rather than leave it.

**What to keep:** `narr` (still used for total_in/total_out calc), the total token sum computation (which should now iterate `_STREAMS` anyway after Step 2.2).

**Validation:** `make check` passes (ruff + mypy). No `F841` unused variable warnings.

---

### Tests to write or update

**File:** `tests/test_turn_viewer.py` (create if it doesn't exist)

**Test: `test_tv_mirror_stream_count`**
Assert `len(_STREAMS) == 5` and all five keys are present in `STREAM_BY_KEY`.

**Test: `test_get_nested`**
Unit test `_get_nested` with: normal path, missing key, non-dict intermediate, empty path.

**Test: `test_turn_viewer_data_empty`**
Assert `_turn_viewer_data(tmp_path)` returns `([], True)` when `events.jsonl` does not exist.

**Test: `test_turn_viewer_data_minimal_event`**
Write a minimal event JSON (just `turn`, `trace_id`, no extraction) to a temp `events.jsonl`.
Assert the returned row has `streams` with all five keys, and each has `status`, `status_class`, `stage_class`.

**Test: `test_turn_viewer_data_connectors`**
Write an event with a populated `rules` dict and a populated `extraction.scene.output` dict.
Assert `connectors` has one entry for each stream with at least one input (narrate, scene, state, progress).
Assert the narrate connector contains a segment with `from == "rules"`.
Assert the scene connector contains segments `from == "rules"` and `from == "narrate"`.

**Test: `test_tv_mirror_stream_inputs_acyclic`**
For each stream, assert none of its `inputs` are itself and all inputs reference streams with lower indices in `_STREAMS` (i.e. no forward references that would create cycles or undefined upstream state).

### REPOMAP updates required

**`docs/REPOMAP/server.md`** — under `server/tv.py` section:
- Add `tv_mirror.py`: `StreamDescriptor`, `_STREAMS`, `STREAM_BY_KEY`, `_get_nested`
- Update `_turn_viewer_data` description to note: "builds stream dict by iterating `_STREAMS`; connector segments derived from `sd.inputs`; `prompts` dict keyed by stream name"
- Remove the bespoke `_tv_narration_lines` description detail about "narrate" specifically — it's now a generic text-output renderer.

### Risks
1. **Template uses named keys.** The Jinja turn_viewer template currently references `row.rules_prompt`, `row.narrate_prompt`, etc. Step 2.4 keeps those keys in the row alongside `prompts` until confirmed the template works. Risk: stale named keys outlive their usefulness. Mitigation: template update is low-risk (grep for `_prompt` in templates, update references to `prompts.*`), tracked as a cleanup note.
2. **`_tv_extract_stream_status` special-cases `"state"` stream by name.** This is fine for now since the logic is intrinsically about inventory_remove. If streams are renamed, this breaks. Mitigation: the key `"state"` in that function is now the only hardcoded stream name in tv.py — flag it with a comment referencing `_STREAMS`.
3. **Events written before scope-in-narration-block will render scope as absent in the narrate connector.** This is correct — those events genuinely don't have it. No silent corruption.

## Ambiguities requiring resolution before execution

1. Does the turn_viewer Jinja template directly render `row.rules_prompt`, `row.narrate_prompt`, etc., or does it already iterate over a dict? **Options:** A) It uses named keys (common) — keep compat aliases in Step 2.4. B) It already iterates a dict — remove named keys immediately. Executor must check the template before Step 2.4.

2. Does `narrate_prompt` in events.jsonl contain `rendered_system` and `rendered_user`, or just `output`? Executor must check a real events.jsonl entry for `narrate_prompt` key structure before assuming the path in Step 2.3.

## TODO.md update

Add under a new section `## Debug / Tooling` (after P4):

```
## Debug / Tooling

- [ ] **Turn viewer dynamic mirror** — schema-driven tv.py; stream registry in `tv_mirror.py`; connectors from `sd.inputs` — see [`turn-viewer-dynamic.md`](turn-viewer-dynamic.md)
```
