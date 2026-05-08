# Turn Viewer — Dynamic Engine Mirror

## Status
`open`

## Part of
standalone

## Dependencies
- `narrator-driven-scope.md` — **completed**. Scope now lives at top-level in events.jsonl as `scope: {active_domains, decided_by, skipped_streams}`. This plan may proceed.
- ~~`narration-active-domains.md`~~ — **superseded** by narrator-driven-scope. Ignore.

## Objective
`server/tv.py` hardcodes the names, keys, and structure of every turn pipeline stage. When the engine changes — fields move, new streams are added, output models evolve — tv.py silently breaks or misses data. The fix is to make tv.py drive its display from the engine's own models and a declarative stream registry, the same way `eval/engine_mirror.py` drives eval from live engine constants. After this plan, adding a new extraction stream or moving a field requires changing the engine + its model only; tv.py adapts automatically. Additionally, `scope` (now a first-class top-level block in events.jsonl since narrator-driven-scope) must be rendered explicitly in the viewer.

## Non-goals
- Does NOT change the events.jsonl schema or what the engine writes.
- Does NOT add new debug panels or new routes.
- Does NOT touch eval/ code.
- Does NOT make tv.py aware of every possible field in every Pydantic model — it reflects the JSON keys actually present in events.jsonl per-turn.

## Confirmed events.jsonl structure (verified against live game output)

Top-level keys in each event:
```
ts, trace_id, turn, input,
applied, rejected, actions, scene_tags,
rules           — {intent_verb, intent, rolled, total_ms, tokens_in, tokens_out, skill, difficulty, dice, stat_mod, diff_mod, cond_mod, final_total, band, outcome_summary}
narrate         — {first_token_ms, total_ms, tokens_in, tokens_out}   ← metrics only, no output here
extract         — {total_ms, tokens_in, tokens_out, retries, streams: {scene: {ms, tokens_in, tokens_out, skipped}, state: {..., skipped}, progress: {...}}}
extraction      — {scene: {rendered_system, rendered_user, output: {...}, skipped, attempts, retry_errors, tokens_in, tokens_out, ms, context_meta},
                   state: {skipped: true, tokens_in: 0, tokens_out: 0, ms: 0, attempts: 0, retry_errors: []},
                   progress: {rendered_system, rendered_user, output: {...}, skipped, attempts, retry_errors, tokens_in, tokens_out, ms, context_meta}}
scope           — {active_domains: [...], decided_by: "narrator", skipped_streams: [...]}   ← TOP LEVEL, first-class
changes         — {inventory, player, facts, quests}
failed          — []
rules_prompt    — {rendered_system, rendered_user, output: "...JSON string...", context_meta}
narrate_prompt  — {rendered_system, rendered_user, output: "...prose string...", context_meta}
```

Key observations:
- `narrate` block is **metrics only** — the actual prompt/output is in `narrate_prompt`.
- `narrate_prompt.output` is a **plain prose string**, not a dict.
- `rules_prompt.output` is a **JSON string** (serialized object), not a dict. Parse with `json.loads` before rendering.
- `extraction.*.ms` (not `total_ms`) for per-extraction-stream latency.
- `rules.total_ms` (not `ms`) for the rules stream.
- `scope` is a **top-level sibling** of all streams — NOT nested inside narrate output.
- `extract.streams.*` contains high-level metrics summary; `extraction.*` contains full detail with rendered prompts.
- `state` stream is frequently skipped (skipped: true, all zeros) — display must handle this gracefully.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/server/tv.py` | rewrite | Delete all hardcoded stream/field logic; loop over `_STREAMS`; render scope block; no compat aliases |
| `ccya/server/tv_mirror.py` | create | `StreamDescriptor` dataclass + `_STREAMS` list + `_get_nested` helper |
| `ccya/server/templates/turn_viewer.html` (or `.jinja2`) | modify | Update prompt tab references from named keys to `prompts[key]` dict; add scope display block |
| `docs/REPOMAP/server.md` | update | Document `tv_mirror.py`; update `_turn_viewer_data` description |
| `docs/plans/TODO.md` | update | Add entry under `## Debug / Tooling` |

## Firm decisions

1. **Streams declared in one place (`tv_mirror.py`), never mentioned by name in `tv.py`.** Each descriptor says: key, label, CSS class, dot-path to metrics blob, dot-path to prompt/output blob (if different), output format (text or dict), latency key, upstream inputs.

2. **Output blocks rendered generically.** `narrate_prompt.output` → `_tv_narration_lines` (text). `rules_prompt.output` → `json.loads` then `_tv_dict_to_lines` (dict). `extraction.*.output` → `_tv_dict_to_lines` (dict). No per-stream bespoke rendering.

3. **Scope is rendered as a dedicated display block** — not buried in narrate output. It is a top-level key and must be visually present. Render `active_domains` as a tag list, `decided_by` as a label, `skipped_streams` as a muted list.

4. **No backwards-compatibility shims, no dead code.** Old named keys (`rules_prompt`, `narrate_prompt`, etc.) are deleted from the row dict entirely. Template is updated in the same phase. If it wasn't in use, it's gone.

5. **Connector segments generated from `sd.inputs`, not hardcoded.** New stream = new `StreamDescriptor` with `inputs=[...]`; connector appears automatically.

6. **`_tv_extract_stream_status` stays in tv.py** — it's presentation logic.

7. **`state` stream skipped display.** When `extraction.state.skipped == True`, show a `skipped` badge instead of token counts. Zero-value tokens should not be rendered as `0 / 0`.

---

## Implementation — Phase 1: `tv_mirror.py` stream registry

### Context files to load
- `ccya/server/tv.py`
- `ccya/eval/engine_mirror.py`
- `ccya/models.py` (skim for field names)

### Overview
Create `ccya/server/tv_mirror.py`. Defines `StreamDescriptor`, `_STREAMS`, `STREAM_BY_KEY`, and `_get_nested`. Nothing else.

### Detailed steps

#### Step 1.1 — Create `tv_mirror.py`

**File:** `ccya/server/tv_mirror.py`

**What:** New module. `StreamDescriptor` is a frozen dataclass. `_STREAMS` is the authoritative list of all turn-pipeline stages, in execution order. Paths are verified against the confirmed events.jsonl structure above.

**Why:** Single source of truth for pipeline topology. tv.py iterates this list — never mentions stream names.

**Code Snippet**
```python
"""Stream registry for turn viewer — single source of truth for pipeline topology.

All dot-paths are verified against live events.jsonl output.
Import _STREAMS and _get_nested in tv.py. Do not reference stream names directly there.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StreamDescriptor:
    key: str
    label: str
    stage_css: str
    # dot-path to the metrics blob (tokens_in, tokens_out, latency)
    metrics_path: str
    # dot-path to the prompt/output blob (rendered_system, rendered_user, output)
    # if None, same as metrics_path
    prompt_path: str | None = None
    # subkey within the prompt blob for the output value (None = use whole blob minus meta)
    output_subkey: str | None = "output"
    # True  → output is a prose string  → _tv_narration_lines
    # False → output is a dict (or JSON string to parse) → _tv_dict_to_lines
    is_text_output: bool = False
    # True  → output is a JSON string that must be json.loads'd before rendering
    output_is_json_string: bool = False
    # key within metrics blob for latency (rules uses total_ms; extraction streams use ms)
    ms_key: str = "ms"
    # upstream stream keys that feed this stream — drives connector generation
    inputs: list[str] = field(default_factory=list)
    # when True: show '—' for tokens when stream is skipped (extraction streams)
    skip_token_display: bool = False


_STREAMS: list[StreamDescriptor] = [
    StreamDescriptor(
        key="rules",
        label="rules",
        stage_css="rules",
        metrics_path="rules",
        prompt_path="rules_prompt",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=True,  # rules_prompt.output is a serialized JSON string
        ms_key="total_ms",
        inputs=[],
    ),
    StreamDescriptor(
        key="narrate",
        label="narrate",
        stage_css="narrate",
        metrics_path="narrate",          # metrics only (total_ms, tokens_in, tokens_out)
        prompt_path="narrate_prompt",    # prompt + output live here
        output_subkey="output",
        is_text_output=True,             # narrate_prompt.output is prose
        ms_key="total_ms",
        inputs=["rules"],
    ),
    StreamDescriptor(
        key="scene",
        label="scene",
        stage_css="scene",
        metrics_path="extraction.scene",
        prompt_path="extraction.scene",
        output_subkey="output",
        is_text_output=False,
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
        ms_key="ms",
        inputs=["rules", "narrate", "scene", "state"],
        skip_token_display=True,
    ),
]

# O(1) lookup by key — used by tv.py connector generation
STREAM_BY_KEY: dict[str, StreamDescriptor] = {s.key: s for s in _STREAMS}


def _get_nested(d: dict, path: str) -> dict | str | list | None:
    """Resolve a dot-separated path into a nested dict.

    Returns None if any key is missing or an intermediate value is not a dict.
    """
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur  # type: ignore[return-value]
```

**Validation:**
```bash
python -c "from ccya.server.tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested; print(len(_STREAMS)); print(list(STREAM_BY_KEY)); print(_get_nested({'extraction': {'scene': {'ms': 42}}}, 'extraction.scene.ms'))"
# → 5
# → ['rules', 'narrate', 'scene', 'state', 'progress']
# → 42
```

---

### Tests to write or update
No logic beyond data definitions + trivial traversal — covered by Phase 2 integration tests.

### REPOMAP updates required
Deferred to end of Phase 2.

### Risks
1. If a future stream has metrics at one path and prompt at a third path (not metrics_path, not prompt_path), the two-path model needs a third slot. Mitigation: add a field then; current streams are fully covered.

---

## Implementation — Phase 2: Rewrite `tv.py` + update template

### Context files to load
- `ccya/server/tv.py` (full file)
- `ccya/server/tv_mirror.py` (just created)
- `ccya/server/templates/turn_viewer.html` (or `.jinja2`) — full file to find all `_prompt` references
- `ccya/server/metrics.py` (for `_fmt_tokens_exact`)

### Overview
Completely rewrite `_turn_viewer_data` to loop over `_STREAMS`. Delete all hardcoded stream/field blocks. Build a `prompts` dict keyed by stream name; update the template to consume it. Add a `scope` block to both the row dict and the template. No compat aliases anywhere.

### Detailed steps

#### Step 2.1 — Replace stream metric collection in `_turn_viewer_data`

**File:** `ccya/server/tv.py`

**What:** Delete all bespoke per-stream variable assignments (`rules_ev_d`, `scene_blk`, etc.). Replace with a single loop over `_STREAMS` that builds `streams[sd.key]` for each.

**Why:** Makes the stream card list automatically reflect `_STREAMS`.

**Code Snippet**
```python
import json as _json
from .tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested

# inside _turn_viewer_data, per-event processing:
rej: list = ev.get("rejected") or []

streams: dict[str, dict] = {}
for sd in _STREAMS:
    blob = _get_nested(ev, sd.metrics_path) or {}
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
    tok_in_display = "—" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_in)
    tok_out_display = "—" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_out)
    streams[sd.key] = {
        "tt": "—" if (skipped and sd.skip_token_display) else _fmt_ms(ms_val),
        "tokens_in": t_in,
        "tokens_out": t_out,
        "tokens_in_display": tok_in_display,
        "tokens_out_display": tok_out_display,
        "skipped": skipped,
        "error": error_s,
        "attempts": attempts,
        "retry_errors": retry_errors,
        "status": status,
        "status_class": _STATUS_CSS.get(status, "tv-sts-ok"),
        "stage_class": _STAGE_CSS.get(sd.stage_css, ""),
    }
```

**Validation:** Server starts, turn viewer loads, all five stream cards appear.

---

#### Step 2.2 — Token bar calculation

**File:** `ccya/server/tv.py`

**What:** Replace any hardcoded stream-name list in the token bar pct loop with `for sd in _STREAMS`.

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

**Validation:** Token bars render with correct relative heights.

---

#### Step 2.3 — Prompts dict (replaces all named `*_prompt` keys)

**File:** `ccya/server/tv.py`

**What:** Build a `prompts: dict[str, dict]` keyed by stream key. Delete all named `rules_prompt`, `narrate_prompt`, `scene_prompt`, `state_prompt`, `progress_prompt` keys from the row dict. No compat aliases.

**Why:** Template will be updated in Step 2.5 to use `prompts[key]`. No stale named keys left in the codebase.

**Code Snippet**
```python
prompts: dict[str, dict[str, str]] = {}
for sd in _STREAMS:
    p_path = sd.prompt_path or sd.metrics_path
    p_blob = _get_nested(ev, p_path) or {}
    if not isinstance(p_blob, dict):
        p_blob = {}
    raw_out = p_blob.get(sd.output_subkey) if sd.output_subkey else None

    # Normalize output to a display string
    if streams[sd.key]["skipped"] and sd.skip_token_display:
        out_str = ""
    elif sd.is_text_output:
        out_str = str(raw_out or "")
    elif sd.output_is_json_string and isinstance(raw_out, str):
        try:
            parsed = _json.loads(raw_out)
            out_str = _json.dumps(parsed, indent=2)
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

**Validation:** Prompt tabs show system/user/output for all five streams. rules output tab shows formatted JSON. narrate output tab shows prose text.

---

#### Step 2.4 — Connector generation from `sd.inputs`

**File:** `ccya/server/tv.py`

**What:** Delete the four hardcoded `*_segments` lists. Replace with a loop over `_STREAMS` that derives segments from `sd.inputs`.

**Why:** New stream = new descriptor with `inputs=[...]`; connector appears with zero changes to tv.py.

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
        # Get the output value for this upstream stream
        inp_p_path = inp_sd.prompt_path or inp_sd.metrics_path
        inp_p_blob = _get_nested(ev, inp_p_path) or {}
        if not isinstance(inp_p_blob, dict):
            inp_p_blob = {}
        raw_out = inp_p_blob.get(inp_sd.output_subkey) if inp_sd.output_subkey else inp_p_blob

        if inp_sd.is_text_output:
            lines = _tv_narration_lines(str(raw_out or ""))
        elif inp_sd.output_is_json_string and isinstance(raw_out, str):
            try:
                parsed = _json.loads(raw_out)
                lines = _tv_dict_to_lines(parsed) if isinstance(parsed, dict) else [str(raw_out)]
            except Exception:
                lines = [str(raw_out)]
        elif isinstance(raw_out, dict):
            lines = _tv_dict_to_lines(raw_out)
        else:
            lines = [str(raw_out)] if raw_out else []

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

**Validation:** Connector panels appear between all stages. Narrate connector shows rules intent JSON. Scene connector shows narration preview + rules intent. State/progress connectors show their full upstream chain.

---

#### Step 2.5 — Add `scope` block to row dict

**File:** `ccya/server/tv.py`

**What:** Extract the top-level `scope` key from the event and include it in the row dict as a structured display block.

**Why:** `scope` is now a first-class output of the narrate stage (emitted as `<scope>{...}</scope>` tag, stripped and parsed by the engine). It belongs in the viewer as its own labeled section, not buried in narrate output.

**Code Snippet**
```python
raw_scope: dict = ev.get("scope") or {}
scope_block = {
    "active_domains": raw_scope.get("active_domains") or [],
    "decided_by": raw_scope.get("decided_by") or "—",
    "skipped_streams": raw_scope.get("skipped_streams") or [],
}
```

Include `"scope": scope_block` in `rows.append({...})`.

**Validation:** Scope block in row dict has all three keys for both turns in the test events.jsonl. Turn 1: `active_domains: ["scene", "compendium_npc"]`, `decided_by: "narrator"`, `skipped_streams: ["state"]`.

---

#### Step 2.6 — Delete all hardcoded remnants

**File:** `ccya/server/tv.py`

**What:** Delete every variable that is now dead:
- `rules_ev_d`, `scene_blk`, `state_blk`, `prog_blk`
- `scene_out`, `state_out`, `prog_out`
- `raw_streams`, `r_in`, `r_out`, `r_ms`
- `n_in`, `n_out`, `n_ms`
- `rules_status` (now inside the loop)
- `_rules_seg` inner function (if it exists)
- Any `narrate_ev_d` or equivalent
- All named `*_prompt` variables/keys that were in `rows.append({...})`

**Why:** Dead code policy — no commented-out code, no unused variables.

**Validation:** `make check` passes with zero ruff `F841` warnings. `mypy` clean.

---

#### Step 2.7 — Update Jinja template

**File:** `ccya/server/templates/turn_viewer.html` (or `.jinja2`)

**What:**
1. Replace all `row.rules_prompt`, `row.narrate_prompt`, `row.scene_prompt`, `row.state_prompt`, `row.progress_prompt` references with `row.prompts.rules`, `row.prompts.narrate`, etc. (or `row.prompts[key]` if iterating).
2. Add a scope display block: render `row.scope.active_domains` as a tag list, `row.scope.decided_by` as a small label, `row.scope.skipped_streams` as a muted list.
3. Scope block placement: between the narrate stage card and the first extraction connector, since scope is the narrate stage's decision.

**Why:** Template must consume the new row shape. No named prompt keys exist in the row any more — template will 500 if not updated.

**Validation:** Full turn viewer renders without Jinja `UndefinedError`. Scope block appears between narrate and scene stages showing correct domains.

---

### Tests to write or update

**File:** `tests/test_turn_viewer.py` (create)

**`test_tv_mirror_completeness`**
Assert `len(_STREAMS) == 5`, all keys in `STREAM_BY_KEY`, no duplicate keys.

**`test_get_nested_cases`**
Unit test `_get_nested`:
- normal path → returns value
- missing intermediate key → returns None
- non-dict intermediate → returns None
- single-segment path → returns top-level value
- empty dict → returns None

**`test_tv_mirror_inputs_acyclic`**
For each stream, assert: (a) key not in its own inputs, (b) all inputs reference streams with lower index in `_STREAMS`.

**`test_turn_viewer_data_empty`**
`_turn_viewer_data(tmp_path)` with no events.jsonl → `([], True)`.

**`test_turn_viewer_data_minimal_event`**
Write a minimal event (just `turn`, `trace_id`, `scope: {active_domains: [], decided_by: "narrator", skipped_streams: []}`) to temp events.jsonl.
Assert returned row has: `streams` with all 5 keys, each with `status`/`status_class`/`stage_class`; `scope` block with `active_domains`, `decided_by`, `skipped_streams`; `prompts` dict with all 5 keys.

**`test_turn_viewer_data_real_event`**
Write the turn-1 event from the verified events.jsonl sample (above) to temp events.jsonl.
Assert:
- `streams["rules"]["tt"]` is not empty
- `streams["state"]["skipped"] == True`
- `streams["state"]["tokens_in_display"] == "—"`
- `scope_block["active_domains"] == ["scene", "compendium_npc"]`
- `scope_block["decided_by"] == "narrator"`
- `scope_block["skipped_streams"] == ["state"]`
- `prompts["narrate"]["output"]` contains "unmarked crate" (substring of narration)
- `connectors` has 4 entries (one per stream with inputs)
- narrate connector has one segment with `from == "rules"`
- scene connector has segments for both "rules" and "narrate"

### REPOMAP updates required

**`docs/REPOMAP/server.md`** — under `server/` section:
- Add `tv_mirror.py`: exports `StreamDescriptor`, `_STREAMS`, `STREAM_BY_KEY`, `_get_nested`; describe each field of `StreamDescriptor`; note that `metrics_path` and `prompt_path` are separately tracked because `narrate` splits its metrics blob from its prompt blob
- Update `tv.py` / `_turn_viewer_data`: "builds `streams` dict by looping `_STREAMS`; connector segments derived from `sd.inputs`; `prompts` dict keyed by stream name; `scope` block from top-level event key"
- Note that named prompt keys (`rules_prompt`, etc.) no longer exist in the row dict

### Risks
1. **Template breakage.** The template update (Step 2.7) must happen in the same PR as the tv.py rewrite, or the server 500s on turn viewer load. Mitigation: Steps 2.6 and 2.7 are in the same phase.
2. **`_tv_extract_stream_status` hardcodes `"state"` stream name** for the inventory-related skipped logic. This is the only remaining hardcoded stream name in tv.py after this plan — flag it with `# NOTE: stream key hardcoded; see _STREAMS in tv_mirror.py`.
3. **`rules_prompt.output` is a JSON string, not a dict.** Forgetting `json.loads` here produces a blob of escaped JSON text in the output tab. Mitigation: `output_is_json_string=True` flag on the rules descriptor; the `prompts` builder in Step 2.3 handles it.
4. **`narrate` metrics blob has no output.** `narrate.output` doesn't exist — only `narrate_prompt.output`. The `prompt_path` separation handles this, but the connector code must also resolve output from `prompt_path`, not `metrics_path`. Step 2.4 does this correctly via `inp_p_path = inp_sd.prompt_path or inp_sd.metrics_path`.

## Ambiguities requiring resolution before execution

1. Does `_tv_extract_stream_status` check stream name `"state"` specifically, or does it check a field in the event? Executor must read its current implementation before Phase 2 to understand what to preserve.

2. Exact template file path — executor must `find ccya/server/templates -name "*turn*"` to locate it before Step 2.7.

3. Does `extract.streams.*` (the summary block, not `extraction.*`) get rendered anywhere in the current viewer? If so, decide whether to keep it as a separate "totals" block or remove it. If it's rendered, it needs a path in the plan. Executor: grep for `extract.streams` in the template before proceeding.

## TODO.md update

Add under a new section `## Debug / Tooling` (after P4):

```
## Debug / Tooling

- [ ] **Turn viewer dynamic mirror** — schema-driven tv.py; stream registry in `tv_mirror.py`; connectors from `sd.inputs`; scope block from narrator — see [`turn-viewer-dynamic.md`](turn-viewer-dynamic.md)
```
