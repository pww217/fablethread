# Multi-Judge Eval Rubric Split

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Config & data model | Add `JudgeSpec` list to config; extend `JudgeResult`; update `load_eval_config` |
| 02 | Trace filtering | Add `build_trace_for_judge(judge_id, events, ...)` that produces per-judge filtered traces |
| 03 | Rubric files | Write the 4 focused rubrics + 1 meta-rubric as markdown files |
| 04 | Parallel judge runner | Replace single `run_judge_streaming` call with parallel fan-out + meta-judge sequenced after |
| 05 | Report assembly | Update `report.py` to accept `list[JudgeResult]` and merge scores for summary |
| 06 | CLI wiring | Update `cli.py` and `judge-only` subcommand for multi-judge |
| 07 | Tests & REPOMAP | Update tests, eval REPOMAP, and config docs |

## Objective
The current eval harness sends one monolithic 31KB rubric to a single 35B MoE judge that reads the entire trace (13 turns × 5 pipelines = ~200KB of context) and is asked to produce calibrated scores across 12 sections and 40+ sub-criteria in one forward pass. The result is shallow, inconsistent scores that don't reliably detect regressions. This plan replaces the single judge with 4 focused parallel judges — each receiving a filtered trace scoped to its domain — plus a lightweight meta-judge that synthesizes their scores into a final verdict. The primary goal is reliable mechanical and state-correctness scores that catch real engine regressions.

## Non-goals
- This plan does not change `universal_asserts.py`, the runner, or the engine pipeline.
- This plan does not change how `events.jsonl` is produced.
- This plan does not change scenario files.
- This plan does not add a new LLM model or endpoint; all judges use the same configured model.
- This plan does not implement parallel async execution at the OS/process level — uses `asyncio.gather`.
- This plan does not remove `default.md` immediately; it is superseded but kept as reference until Phase 07.

---

## Implementation — Phase 01: Config & data model

### Files to pull for context
- `ccya/eval/config.py`
- `evals/config.yaml`
- `ccya/eval/judge.py` (the `JudgeResult` dataclass and `_normalize_scores`)

### Detailed steps

#### Step 1.1 — Add `JudgeSpec` and `JudgesConfig` to `config.py`

**File:** `ccya/eval/config.py`

**What:** Replace the single `JudgeConfig` with a `JudgeSpec` (one entry per judge) and a `JudgesConfig` wrapper that holds a list of specs plus the shared `TraceConfig`. Keep backward-compat: if the YAML still has the old flat `judge:` block, parse it as a single spec with `id: "default"`.

**Why:** Each of the 5 judges (4 domain judges + 1 meta) has its own `rubric_path`, `model` (potentially different), and `max_tokens`. They share `temperature`, `timeout_s`, and trace dedup settings.

**Code Snippet**
```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class InferenceConfig:
    temperature_override: float | None = None
    cache: bool = False


@dataclass
class TraceConfig:
    dedup_immutable_sections: bool = True
    state_as_diff: bool = True


@dataclass
class JudgeSpec:
    id: str
    rubric_path: str
    model: str | None = None
    temperature: float = 0.3
    timeout_s: float | None = None
    max_tokens: int = 64000


@dataclass
class JudgesConfig:
    enabled: bool = True
    specs: list[JudgeSpec] = field(default_factory=list)
    trace: TraceConfig = field(default_factory=TraceConfig)


@dataclass
class ReportConfig:
    token_warn_pct: float = 10.0
    token_fail_pct: float = 25.0
    flag_at_top: list[str] = field(default_factory=list)


@dataclass
class LoggingConfig:
    level: str = "WARNING"


@dataclass
class EvalConfig:
    default_pack: str = "eval-pack"
    default_scenario: str = "full_cycle"
    pack_dirs: list[str] = field(default_factory=lambda: ["evals/packs", "packs/default", "packs/custom"])
    default_save_root: str = "~/.cache/ccya-eval"
    runs_dir: str = "evals/runs"
    num_turns: int = 10
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    judges: JudgesConfig = field(default_factory=JudgesConfig)
    report: ReportConfig = field(default_factory=ReportConfig)

    @property
    def judge(self) -> JudgesConfig:
        """Back-compat alias."""
        return self.judges


_DEFAULT_PATH = Path("evals/config.yaml")


def _parse_judge_spec(raw: dict[str, Any], spec_id: str) -> JudgeSpec:
    return JudgeSpec(
        id=spec_id,
        rubric_path=str(raw.get("rubric_path", "evals/rubrics/default.md")),
        model=raw.get("model"),
        temperature=float(raw.get("temperature", 0.3)),
        timeout_s=raw.get("timeout_s"),
        max_tokens=int(raw.get("max_tokens", 64000)),
    )


def load_eval_config(path: str | Path | None = None) -> EvalConfig:
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        raise FileNotFoundError(f"eval config not found: {p}")
    with open(p) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    inf_raw = raw.get("inference") or {}
    rpt_raw = raw.get("report") or {}
    log_raw = raw.get("logging") or {}

    # Support both old flat `judge:` and new `judges:` with a `specs:` list.
    judges_raw = raw.get("judges") or {}
    judge_raw = raw.get("judge") or {}  # legacy fallback

    trace_source = judges_raw.get("trace") or judge_raw.get("trace") or {}
    trace_cfg = TraceConfig(
        dedup_immutable_sections=bool(trace_source.get("dedup_immutable_sections", True)),
        state_as_diff=bool(trace_source.get("state_as_diff", True)),
    )

    specs: list[JudgeSpec] = []
    if "specs" in judges_raw:
        for spec_raw in judges_raw["specs"]:
            specs.append(_parse_judge_spec(spec_raw, spec_raw.get("id", "unknown")))
    elif judge_raw:
        # Legacy single-judge config: wrap as single spec with id="default"
        specs.append(_parse_judge_spec(judge_raw, "default"))

    enabled = bool(judges_raw.get("enabled", judge_raw.get("enabled", True)))

    return EvalConfig(
        default_pack=str(raw.get("default_pack", "eval-pack")),
        default_scenario=str(raw.get("default_scenario", "full_cycle")),
        pack_dirs=list(raw.get("pack_dirs") or ["evals/packs", "packs/default", "packs/custom"]),
        default_save_root=str(raw.get("default_save_root", "~/.cache/ccya-eval")),
        runs_dir=str(raw.get("runs_dir", "evals/runs")),
        num_turns=int(raw.get("num_turns", 10)),
        logging=LoggingConfig(level=str(log_raw.get("level", "WARNING"))),
        inference=InferenceConfig(
            temperature_override=inf_raw.get("temperature_override"),
            cache=bool(inf_raw.get("cache", False)),
        ),
        judges=JudgesConfig(
            enabled=enabled,
            specs=specs,
            trace=trace_cfg,
        ),
        report=ReportConfig(
            token_warn_pct=float(rpt_raw.get("token_warn_pct", 10.0)),
            token_fail_pct=float(rpt_raw.get("token_fail_pct", 25.0)),
            flag_at_top=list(rpt_raw.get("flag_at_top") or []),
        ),
    )
```

**Validation:** `python -c "from ccya.eval.config import load_eval_config; c = load_eval_config(); print(c.judges)"` with both old and new `evals/config.yaml` formats.

---

#### Step 1.2 — Extend `JudgeResult` to carry `judge_id`

**File:** `ccya/eval/judge.py`

**What:** Add `judge_id: str = "default"` field to `JudgeResult`. Update `_normalize_scores` to be tolerant of partial score sets (already is via `if k in fm`, confirm no change needed). Add `JUDGE_SCORE_KEYS` constant mapping each judge id to its expected score keys.

**Why:** `report.py` needs to know which judge produced which scores when merging. `_collect_flags` needs to know which judge owns `mechanical_score` for regression detection.

**Code Snippet**
```python
# Add to judge.py after existing imports

JUDGE_SCORE_KEYS: dict[str, list[str]] = {
    "state_correctness": ["state_fidelity_rate", "extraction_accuracy_score", "mechanic_lifecycle_score"],
    "narrative_interplay": ["narrative_score", "system_cohesion_score"],
    "prompt_pipeline": [
        "prompt_quality_score", "prompt_adherence_rate",
        "pipeline_scores",  # nested dict
    ],
    "compaction": ["compaction_score", "sanitization_fidelity_rate"],
    "meta": ["mechanical_score", "narrative_score", "system_cohesion_score",
             "prompt_quality_score", "compaction_score",
             "state_fidelity_rate", "prompt_adherence_rate"],
    "default": [  # legacy single-judge
        "mechanical_score", "narrative_score", "system_cohesion_score",
        "prompt_quality_score", "compaction_score",
        "state_fidelity_rate", "prompt_adherence_rate", "pipeline_scores",
    ],
}


@dataclass
class JudgeResult:
    """Structured result of one judge invocation."""
    raw_response: str
    body_md: str
    scores: dict[str, Any]
    rubric_path: str
    model: str
    judge_id: str = "default"
    trace_md_path: str = ""
    judge_md_path: str = ""
    previous_scores: dict[str, Any] | None = None
```

**Validation:** Import succeeds; existing tests that construct `JudgeResult` without `judge_id` still work (default value).

---

#### Step 1.3 — Update `evals/config.yaml`

**File:** `evals/config.yaml`

**What:** Replace the flat `judge:` block with a `judges:` block containing `specs:` list for the 5 judges. Keep the old block commented out as reference until Phase 07.

**Why:** New config schema drives the new multi-judge flow.

**Code Snippet**
```yaml
# Eval harness configuration. Loaded by ccya.eval.config.load_eval_config().

default_pack: eval-pack
default_scenario: full_cycle
pack_dirs:
  - evals/packs
  - packs/default
  - packs/custom
default_save_root: ~/.cache/ccya-eval
runs_dir: evals/runs
num_turns: 13

logging:
  level: DEBUG

inference:
  temperature_override: null
  cache: false

judges:
  enabled: true
  trace:
    dedup_immutable_sections: true
    state_as_diff: true

  specs:
    - id: state_correctness
      rubric_path: evals/rubrics/state_correctness.md
      model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit
      temperature: 0.3
      max_tokens: 32000

    - id: narrative_interplay
      rubric_path: evals/rubrics/narrative_interplay.md
      model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit
      temperature: 0.3
      max_tokens: 32000

    - id: prompt_pipeline
      rubric_path: evals/rubrics/prompt_pipeline.md
      model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit
      temperature: 0.3
      max_tokens: 48000

    - id: compaction
      rubric_path: evals/rubrics/compaction.md
      model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit
      temperature: 0.3
      max_tokens: 16000

    - id: meta
      rubric_path: evals/rubrics/meta.md
      model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit
      temperature: 0.2
      max_tokens: 8000

report:
  token_warn_pct: 10
  token_fail_pct: 25
  flag_at_top:
    - tokens_regression
    - extraction_retries
    - extraction_failures
    - judge_score_drop
    - rejected_deltas
```

**Validation:** `load_eval_config()` parses without error; `c.judges.specs` has 5 entries with correct ids.

### Tests to write or update
- `tests/test_eval.py`: update `test_load_eval_config` to assert `len(cfg.judges.specs) == 5` and that the legacy single-judge format still parses into one spec with `id="default"`.

### Risks
1. Any code that accesses `eval_cfg.judge.rubric_path` or `eval_cfg.judge.model` directly will break. Mitigation: audit all call sites before merging — covered in Phase 04 and 06 steps.

---

## Implementation — Phase 02: Trace filtering

### Files to pull for context
- `ccya/eval/judge.py` — full file, especially `build_trace`, `_render_static_context`, `_render_turn_context`, `_render_deterministic_signals`

### Detailed steps

#### Step 2.1 — Add `build_trace_for_judge` routing function

**File:** `ccya/eval/judge.py`

**What:** Add a new public function `build_trace_for_judge(judge_id, events, *, options, auto_checker_failures, metrics_rows, redundancy_signals, compaction_signals, arch_context)` that calls `build_trace` with a filtered view of the event data according to the judge's domain. The existing `build_trace` is unchanged and remains the full-trace builder.

**Why:** Each judge only needs a subset of the trace. Sending less context means the model's attention is not diluted by irrelevant data. Trace size directly affects quality of output for a 35B model.

**Code Snippet**
```python
# ---- Per-judge trace field masks ----------------------------------------

# Fields kept in each per-turn event dict for each judge.
# Keys reference top-level event keys. "extraction.*" means sub-keys of event["extraction"].
_JUDGE_EVENT_FIELDS: dict[str, set[str]] = {
    "state_correctness": {
        # needs: state diffs, applied/rejected deltas, rules output (parsed only), extractor outputs
        "turn", "input",
        "rules",                    # parsed rules output (band, stakes, etc.)
        "applied", "rejected",
        "extraction",               # all 3 streams, outputs only
        "state_snapshot",
        # no narrate_prompt, no rules_prompt text, no user prompts
    },
    "narrative_interplay": {
        "turn", "input",
        "rules",                    # band, directive, stakes
        "narrate_prompt",           # output (narration text) only — not rendered_user/system
        "extraction",               # scene/state/progress outputs only (for NPC/beat/pressure fields)
        "state_snapshot",           # mechanic fields only (meta, scene, pc.conditions)
        "applied",
    },
    "prompt_pipeline": {
        "turn", "input",
        "rules_prompt",             # full: rendered_system, rendered_user, output, parse_error
        "narrate_prompt",           # full: rendered_system, rendered_user, output
        "extraction",               # full: rendered_system, rendered_user, output per stream
        "rejected",
        # no state_snapshot, no narrate text (it's in narrate_prompt.output)
    },
    "compaction": {
        "turn", "input",
        "extraction",               # progress stream only (compaction fires here)
        "applied", "rejected",
        "state_snapshot",           # full — compaction judge needs complete pre/post state
    },
    # meta judge receives no events.jsonl trace at all — it receives prior judge summaries
}

# Which extraction sub-streams each judge needs
_JUDGE_EXTRACTION_STREAMS: dict[str, set[str]] = {
    "state_correctness": {"scene", "state", "progress"},
    "narrative_interplay": {"scene", "state", "progress"},
    "prompt_pipeline": {"scene", "state", "progress"},
    "compaction": {"progress"},
}

# For narrative_interplay: which state_snapshot top-level keys to keep
_NARRATIVE_SNAPSHOT_KEYS = {"meta", "scene", "pc", "location"}

# For compaction: only include events at or adjacent to compaction turns
# (compaction fires when turn % compact_every == 0; we include ±1 turns)
_COMPACTION_WINDOW = 1


def _filter_event_for_judge(judge_id: str, ev: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ev with only the fields relevant to judge_id."""
    if judge_id not in _JUDGE_EVENT_FIELDS:
        return ev  # unknown judge gets full event

    keep = _JUDGE_EVENT_FIELDS[judge_id]
    out: dict[str, Any] = {}

    for key in keep:
        if key not in ev:
            continue
        if key == "narrate_prompt" and judge_id == "narrative_interplay":
            # narrative judge only needs the output text, not the full prompt structure
            np = ev["narrate_prompt"] or {}
            out["narrate_prompt"] = {"output": np.get("output", "")}
        elif key == "extraction":
            streams_needed = _JUDGE_EXTRACTION_STREAMS.get(judge_id, set())
            ext = ev.get("extraction") or {}
            filtered_ext: dict[str, Any] = {}
            for stream in streams_needed:
                if stream not in ext:
                    continue
                s = ext[stream]
                if judge_id == "prompt_pipeline":
                    # full stream data
                    filtered_ext[stream] = s
                else:
                    # output + skipped only
                    filtered_ext[stream] = {
                        "output": s.get("output"),
                        "skipped": s.get("skipped", False),
                        "attempts": s.get("attempts", 1),
                    }
            out["extraction"] = filtered_ext
        elif key == "state_snapshot" and judge_id == "narrative_interplay":
            snap = ev.get("state_snapshot") or {}
            out["state_snapshot"] = {k: snap[k] for k in _NARRATIVE_SNAPSHOT_KEYS if k in snap}
        else:
            out[key] = ev[key]

    return out


def _is_compaction_turn(ev: dict[str, Any], all_events: list[dict[str, Any]]) -> bool:
    """Detect if a turn had compaction activity by checking applied deltas for compaction markers."""
    applied = ev.get("applied") or {}
    # Compaction produces chronicle entries and recent_events pruning
    if applied.get("chronicle_append") or applied.get("recent_events_compact"):
        return True
    # Also check progress extraction output for compaction_fired signal if present
    ext_progress = ((ev.get("extraction") or {}).get("progress") or {}).get("output") or {}
    return bool(ext_progress.get("compaction_fired"))


def _select_compaction_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """For compaction judge: return only turns at/around compaction events."""
    compaction_turns: set[int] = set()
    for ev in events:
        if _is_compaction_turn(ev, events):
            t = int(ev.get("turn", 0))
            for offset in range(-_COMPACTION_WINDOW, _COMPACTION_WINDOW + 1):
                compaction_turns.add(t + offset)

    if not compaction_turns:
        # No compaction detected — return all events so judge can report absence
        return events

    return [ev for ev in events if int(ev.get("turn", 0)) in compaction_turns]


def build_trace_for_judge(
    judge_id: str,
    events: list[dict[str, Any]],
    *,
    options: TraceOptions | None = None,
    auto_checker_failures: list[dict[str, Any]] | None = None,
    metrics_rows: list[dict[str, Any]] | None = None,
    redundancy_signals: dict[str, Any] | None = None,
    compaction_signals: dict[str, Any] | None = None,
    arch_context: str = "",
) -> str:
    """Build a filtered trace for a specific judge id.

    Filters event fields and (for compaction judge) event selection before
    delegating to build_trace(). The meta judge receives an empty string —
    its input is assembled separately from prior judge outputs.
    """
    if judge_id == "meta":
        return ""  # meta judge input is assembled in run_judges(), not here

    options = options or TraceOptions()
    metadata, turn_events = _split_metadata(events)

    if judge_id == "compaction":
        turn_events = _select_compaction_events(turn_events)
        # Compaction judge gets deterministic signals focused on compaction only
        return build_trace(
            [metadata] + turn_events if metadata else turn_events,
            options=options,
            auto_checker_failures=None,   # not relevant
            metrics_rows=None,
            redundancy_signals=None,
            compaction_signals=compaction_signals,
            arch_context="",              # no arch context needed
        )

    filtered_events = [_filter_event_for_judge(judge_id, ev) for ev in turn_events]
    all_filtered = ([metadata] + filtered_events) if metadata else filtered_events

    # state_correctness gets deterministic signals (auto-checker + metrics), no redundancy
    if judge_id == "state_correctness":
        return build_trace(
            all_filtered,
            options=options,
            auto_checker_failures=auto_checker_failures,
            metrics_rows=metrics_rows,
            redundancy_signals=None,
            compaction_signals=None,
            arch_context=arch_context,
        )

    # prompt_pipeline gets redundancy signals
    if judge_id == "prompt_pipeline":
        return build_trace(
            all_filtered,
            options=options,
            auto_checker_failures=None,
            metrics_rows=metrics_rows,   # token counts relevant to prompt audit
            redundancy_signals=redundancy_signals,
            compaction_signals=None,
            arch_context=arch_context,
        )

    # narrative_interplay: narration + mechanic state, no signals
    return build_trace(
        all_filtered,
        options=options,
        auto_checker_failures=None,
        metrics_rows=None,
        redundancy_signals=None,
        compaction_signals=None,
        arch_context="",
    )
```

**Validation:** For each judge_id in `["state_correctness", "narrative_interplay", "prompt_pipeline", "compaction"]`, call `build_trace_for_judge(judge_id, events)` with a sample events list and confirm: (a) no KeyError, (b) returned string does not contain sections it shouldn't (e.g., state_correctness trace has no `### Narrate User Prompt` blocks), (c) compaction judge with no compaction events returns full event list.

---

#### Step 2.2 — Add `_build_meta_judge_input` function

**File:** `ccya/eval/judge.py`

**What:** Add a function that takes a list of `JudgeResult` objects (the 4 domain judges) and assembles the meta-judge's user message: YAML scores from each judge + their Key Findings / Actionable Issues section text (extracted from `body_md`).

**Why:** The meta-judge does not read `events.jsonl`. It synthesizes the domain judges' outputs. It needs scores and the specific sections that contain actionable findings, not the full 30KB body.

**Code Snippet**
```python
import re as _re

_SECTION_HEADING_RE = _re.compile(r"^#{1,3} .+", _re.MULTILINE)

def _extract_section(body_md: str, heading_fragment: str) -> str:
    """Extract the content of the first section whose heading contains heading_fragment.

    Returns empty string if not found. Strips the heading line itself.
    Content ends at the next same-or-higher-level heading or end of string.
    """
    lines = body_md.splitlines()
    capture = False
    heading_level = 0
    out: list[str] = []
    for line in lines:
        m = _SECTION_HEADING_RE.match(line)
        if m:
            level = len(line) - len(line.lstrip("#"))
            if heading_fragment.lower() in line.lower():
                capture = True
                heading_level = level
                continue
            elif capture and level <= heading_level:
                break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def _build_meta_judge_input(judge_results: list["JudgeResult"]) -> str:
    """Assemble meta-judge user message from domain judge outputs.

    Structure:
      # Domain Judge Scores
      (YAML block with all scores merged)

      # Judge Summaries
      ## [judge_id]
      (Key Findings + Actionable Issues sections from body_md)
    """
    parts: list[str] = ["# Domain Judge Scores\n\n```yaml"]
    merged: dict[str, Any] = {}
    for jr in judge_results:
        if jr.scores:
            merged[jr.judge_id] = jr.scores
    parts.append(_yaml_dump(merged))
    parts.append("```\n")

    parts.append("# Judge Summaries\n")
    for jr in judge_results:
        parts.append(f"## {jr.judge_id}\n")
        for fragment in ("Key Findings", "Actionable Issues", "Verdict", "Issues"):
            section = _extract_section(jr.body_md, fragment)
            if section:
                parts.append(f"### {fragment}\n\n{section}\n")
        parts.append("")

    return "\n".join(parts)


def _yaml_dump(d: Any) -> str:
    """Safe YAML dump without external deps beyond already-imported yaml."""
    import yaml as _yaml
    return _yaml.dump(d, default_flow_style=False, allow_unicode=True)
```

**Validation:** Call `_build_meta_judge_input([jr1, jr2])` with mock `JudgeResult` objects and confirm output contains the YAML scores block and at least one summary section.

### Tests to write or update
- `tests/test_eval.py`: add `test_build_trace_for_judge_state_correctness` — asserts no `Narrate User Prompt` heading in output.
- `tests/test_eval.py`: add `test_build_trace_for_judge_prompt_pipeline` — asserts `Prompt Redundancy` section present if redundancy signals passed.
- `tests/test_eval.py`: add `test_build_meta_judge_input` — asserts YAML block present and at least one `##` heading per judge result.

### Risks
1. `_is_compaction_turn` may fail to detect compaction if the applied delta keys differ from what's checked. Mitigation: check actual events.jsonl from a recent run before finalizing key names; fall back to returning all events if detection fails (already handled).
2. Filtering `narrate_prompt` to output-only for narrative_interplay may lose system prompt data the rubric needs. Mitigation: narrative_interplay rubric explicitly does not audit prompt structure — it reads narration text only. If that changes, update the filter mask.

---

## Implementation — Phase 03: Rubric files

### Files to pull for context
- `evals/rubrics/default.md` — full file
- `ccya/eval/engine_mirror.py` — for constants referenced in rubrics

### Detailed steps

#### Step 3.1 — Write `evals/rubrics/state_correctness.md`

**File:** `evals/rubrics/state_correctness.md`

**What:** A focused rubric for Judge 1. Input is deterministic signals + state snapshots + applied/rejected deltas + parsed rules output. No prose, no prompts.

**Why:** This is the highest-priority judge. It should be unambiguous — the model is comparing structured JSON against structured JSON. Every criterion is verifiable.

**Code Snippet**
```markdown
***
state_fidelity_rate: <float 0.0-1.0>
extraction_accuracy_score: <int 1-5>
mechanic_lifecycle_score: <int 1-5>
***

# ccya Eval — State Correctness Judge

You are a mechanical correctness auditor for the ccya game engine.
You receive a structured trace of engine events. Your job is to verify
that game state evolved correctly and that the extraction pipelines
emitted accurate deltas. You do not evaluate prose or prompt quality.

Every finding must cite a specific turn number and field name.
Every score must be derivable from your evidence — do not guess.

Scoring philosophy:
- 5/5: No extraction misses, no state drift, all mechanics tracking correctly.
- 3/5: Minor misses (1–2 turns), no critical state corruption.
- 1–2/5: Repeated extraction failures, state fields diverging from narrated events,
  or a mechanic class entirely absent.

***

## HOW TO READ YOUR TRACE

You receive:
- **Static Context**: Seed State, Engine Constants (momentum range, pressure urgency levels, beat types).
- **Per-turn blocks**: Input, Engine Outputs (rules parsed JSON + extractor outputs), Applied Deltas, Rejected Deltas, State After Turn (diff or full snapshot).
- **Deterministic Signals**: Auto-Checker Failures table, Metrics table (token counts, parse failures, retries).

The Auto-Checker Failures are authoritative. Do not re-derive pass/fail for any
assertion that already appears in that table. Your job is to explain *why* each
failure occurred and whether it represents a true failure or checker noise.

***

## SECTION 1 — Mechanic Lifecycle Tables

Construct compact tables from the event data. Keep each cell to ≤10 words.

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Flag |
|------|-----------|------------|-------------------|------|

Flag values: `WRONG_DIR` (momentum moved opposite to band), `FLAT` (roll occurred but no change), `—` for clean.

After the table: Is momentum responding correctly to dice rolls across the run?

### 1B — GM Beat Lifecycle Table

| Generated (Tn) | Beat Type | Disposition Emitted | State After | TTL Respected? | Flag |
|----------------|-----------|---------------------|-------------|----------------|------|

Flags: `ORPHANED` (generated, never consumed/expired), `CARRY_FAIL` (carry disposition but beat cleared), `REPLACE_FAIL` (replace disposition but beat unchanged), `TTL_EXCEEDED`.

### 1C — Scene Pressure Lifecycle Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|----|------------|---------|------------|---------------|----------|------|

Flags: `INERT` (no escalation or resolution across ≥3 turns), `OVERLONG`, `UNRESOLVED_AT_END`.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Resolved (Tm) | Duration | Flag |
|----|------------|--------|---------------|----------|------|

Source: `roll` / `narrative` / `engine`.
Flags: `SILENT_DROP`, `OVERLONG` (active >5 turns), `DUPLICATE`.

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|---------------|---------|------|

Flags: `PREMATURE_COMPLETE`, `DUPLICATE_ID`, `ORPHANED`, `INCOMPLETE_CLOSE`.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty Extracted | Rejected? | Flag |
|------|--------|------|---------------|-----------|------|

Flags: `AMOUNT_MISMATCH` (extracted qty differs from applied delta), `SPENDING_MISS`.

***

## SECTION 2 — State Fidelity Assessment

### 2A — State Coherence
Do inventory, conditions, quests, pressures, and NPCs agree with each other across turns?
Cite specific turns and fields where they diverge.

### 2B — Extraction Drift
For each turn where a delta was rejected OR where state did not change but should have:
identify the responsible pipeline (scene/state/progress) and the field that drifted.
Distinguish: extraction failure (pipeline emitted nothing) vs. schema mismatch (pipeline
emitted wrong structure) vs. validation rejection (engine rejected a valid-looking delta).

### 2C — State Fidelity Rate Calculation
Count: turns where (no rejected deltas AND no Auto-Checker failures AND no detected drift) / total turns.
Show the arithmetic. This value goes in the YAML front matter.

***

## SECTION 3 — Auto-Checker Failure Analysis

For EACH failure in the Deterministic Signals Auto-Checker table:

1. True failure or checker noise (false positive)?
   - If noise: explain why. Recommend a checker fix if the false positive is systematic.
   - If true failure: proceed.
2. Root cause. Which pipeline produced (or failed to produce) the relevant delta?
3. Remediation tag: `extraction_miss | schema_drift | wrong_pipeline | engine_bug | scope_violation | stale_context`.

If none: write `None.`

***

## SECTION 4 — Scores

### Extraction Accuracy Score (1–5)
Based on Sections 2B and 3. Major extraction failures cap at 2. State cap reason explicitly.
Score 1–5.

### Mechanic Lifecycle Score (1–5)
Based on Section 1 tables. Count flags: >4 red flags across all tables caps at 2.
Score 1–5.

***

## SECTION 5 — Actionable Issues

Group as **Critical** / **Major** / **Minor**.

- **<description>** (turns: <list>) — Tag: `<remediation_tag>`. Fix: <what to change in data flow or extraction prompt>.

Critical = breaks engine or corrupts state.
Major = degrades quality, does not break.
Minor = edge case or cosmetic.
```

**Validation:** Read the rubric manually and verify: (a) no sections reference prompt text or narration prose, (b) all score keys match `JUDGE_SCORE_KEYS["state_correctness"]` in `judge.py`, (c) YAML front matter keys match `_normalize_scores` handling (add `extraction_accuracy_score` and `mechanic_lifecycle_score` to `_normalize_scores` — see Step 3.6).

---

#### Step 3.2 — Write `evals/rubrics/narrative_interplay.md`

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Rubric for Judge 2. Input is narration text + rules output (band/directive/stakes) + mechanic state fields (beats, pressures, conditions, quests from extractor outputs) + state diffs (mechanic fields only).

**Code Snippet**
```markdown
***
narrative_score: <int 1-5>
system_cohesion_score: <int 1-5>
***

# ccya Eval — Narrative & Mechanic Interplay Judge

You are evaluating whether the ccya engine's narrative output correctly reflects
and responds to its mechanical state. You are NOT auditing prompt architecture
or extraction schema correctness — those are handled by other judges.

Your trace contains:
- Narration text per turn (the actual prose shown to players)
- Rules output: roll band, directive, stakes, intent per turn
- Mechanic state fields per turn: momentum, GM beats, scene pressures, conditions, quests, NPCs
- State diffs (mechanic-relevant fields only)

Every finding must cite a specific turn and field.

Scoring philosophy:
- 5/5: Narration consistently honors directives, tone matches momentum, every beat/pressure
  creates observable story consequence.
- 3/5: Minor disconnects (1–2 turns), no systematic failures.
- 1–2/5: Directives routinely ignored, tone disconnected from momentum band, mechanics
  create no story consequence.

***

## HOW TO READ YOUR TRACE

Per-turn blocks contain:
- **Rules output**: `band`, `directive`, `stakes`, `intent`, `roll` (if present)
- **Narration**: the prose output
- **Extraction outputs**: scene (NPCs, location), state (inventory, conditions), progress (quests, pressures, beats)
- **State diff**: changes to `meta.momentum`, `scene`, `pc.conditions`

You do NOT have access to the system or user prompts — do not comment on prompt architecture.

***

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Momentum→Directive→Tone

For each turn with a roll:

| Turn | Band | Directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------|-------------|---------------------------|------|

Flag: `TONE_MISMATCH` (narration tone contradicts band), `DIRECTIVE_IGNORED` (directive issued but prose ignores it).

After the table: Does band progression feel too fast, too slow, or appropriate? Was there a coherent momentum arc across the run (low→build→peak or similar)?

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|

Flag: `NO_EFFECT` (beat present in state but narration unchanged), `WRONG_EFFECT` (beat type=revelation but narration shows complication).

After the table: Are beats creating meaningful story pivots or are they mechanical noise?

### 1C — Pressure→Stakes→Consequence Chain

For each `scene_pressure_add` event:

| Pressure ID | Added (Tn) | Stakes Named? | Consequence Extracted? | Chain Complete? | Flag |
|-------------|------------|---------------|------------------------|-----------------|------|

Flag: `INERT_PRESSURE` (pressure exists in state, never feeds stakes), `STAKES_WITHOUT_CONSEQUENCE` (stakes named, roll setback, no consequence extracted).

### 1D — Condition→Narrative Callback

For each active condition per turn: was it referenced in narration or did it affect a roll directive?

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|

Flag: `PHANTOM` (in state, never mentioned in prose, never affected anything).

***

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
Did narration describe NPC entry/exit before or at the same turn the extractor recorded it?
Flag any NPC that left the scene but reappeared without a re-entry narration.
Flag any NPC present in state but never mentioned in narration (ghost NPC).

### 2B — Player Intent Fidelity
For each turn: did the narration process the player's stated action, or redirect/reinterpret it?
Flag turns where the narration output ignores or contradicts the player's stated input.

Verdict: tight / loose / broken.

***

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns**: count each. Flag if >4 consecutive immediate-pressure turns.
- **Momentum arc**: did the run have a discernible arc? Or random oscillation?
- **Beat type variety**: count beat types. Flag if >60% are the same type.
- **Escape paths**: when player was in a bad situation (negative momentum, immediate pressure),
  were there viable choices to improve it? Assess from narration content.

***

## SECTION 4 — Scores

### Narrative Score (1–5)
Based on Sections 1–3. Does mechanics produce good fiction? A 5 requires beats, pressures,
and momentum all producing observable story consequence. A 1–2 means mechanics are decorative.
Score 1–5.

### System Cohesion Score (1–5)
Based on Section 1 chain analyses. Is the engine behaving as a system (mechanics→narrative→state→mechanics)
or as isolated components? Score 1–5.

***

## SECTION 5 — Actionable Issues

Group as **Critical** / **Major** / **Minor**.

- **<description>** (turns: <list>) — Tag: `<tone_mismatch|directive_ignored|inert_mechanic|npc_ghost|intent_redirect>`. Fix: <what narrative or mechanic behavior to change>.
```

**Validation:** Verify score keys match `JUDGE_SCORE_KEYS["narrative_interplay"]`.

---

#### Step 3.3 — Write `evals/rubrics/prompt_pipeline.md`

**File:** `evals/rubrics/prompt_pipeline.md`

**What:** Rubric for Judge 3. Input is all 5 system prompts + per-turn user prompts (deduped) + extractor JSON outputs + redundancy signals + token metrics.

**Code Snippet**
```markdown
***
prompt_quality_score: <int 1-5>
prompt_adherence_rate: <float 0.0-1.0>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
***

# ccya Eval — Prompt Architecture & Pipeline Judge

You are auditing the prompt architecture and pipeline output quality of the ccya game engine.
You receive:
- All 5 system prompts (static, appears once in Static Context)
- Per-turn user prompts for all 5 pipelines (deduped: immutable sections omitted after turn 1)
- Per-turn extractor JSON outputs (rules, scene, state, progress)
- Prompt Redundancy signals (cross-stream block duplication detected by harness)
- Per-turn token counts

You are NOT evaluating narration quality or state correctness — those are other judges.
Your question: are the prompts well-structured, and did each pipeline obey its own instructions?

Every finding must cite a specific turn and pipeline.

***

## HOW TO READ YOUR TRACE

**Static Context** contains 5 system prompts. These are the standing instructions each pipeline receives every turn.

**Per-turn blocks** contain user prompts (with immutable sections replaced by a placeholder after T1) and extractor JSON outputs. The narrate pipeline output is present but you are evaluating whether it *followed instructions*, not whether it produced good prose.

**Deterministic Signals** contains:
- Prompt Redundancy table: cross-stream block duplication detected by the harness
- Metrics table: per-turn token counts per pipeline

***

## SECTION 1 — Per-Pipeline Prompt Audit

For each pipeline, evaluate criteria below. Score each: `Y` / `N` / `PARTIAL`.

### Criteria

| # | Criterion | What to check |
|---|-----------|---------------|
| P1 | **System/User separation** | Is system prompt static instructions only? Is user prompt purely turn-variable data? Flag instruction text in user prompt or turn-variable data in system prompt. |
| P2 | **User prompt mechanical sense** | Does user prompt contain the right inputs for this pipeline's role and nothing extra? |
| P3 | **No unintentional cross-pipeline redundancy** | Block appearing verbatim in this pipeline AND another where it shouldn't. Reference Prompt Redundancy signals. |
| P4 | **Schema vs guidance separation** | JSON schema section defines syntax only. Guidance section provides behavioral direction only. No overlap. |
| P5 | **No contradictions** | Instructions that say both X and not-X? Ambiguous conditionals? |
| P6 | **Terse without loss of intent** | Multi-sentence explanations reducible to one? Same rule stated 3 ways? Identify specific passages. |
| P7 | **LLM parse-friendly formatting** | Sections clearly delimited? Priority rules numbered? |
| P8 | **Prompt adherence** | Did this pipeline's outputs comply with its system prompt this run? A rule violated ≥2 turns = FAIL. Cite turns and rules. |
| P9 | **Few-shot examples needed?** | For failure modes observed this run: would a concrete example have prevented the failure? |

### 1A — Rules Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
(fill all P1–P9)

**Remediation summary:** bullet list — what is wrong → what to change → expected outcome.

### 1B — Narrate Pipeline
(same format)

### 1C — Extract Scene Pipeline
(same format)

### 1D — Extract State Pipeline
(same format)

### 1E — Extract Progress Pipeline
(same format)

***

## SECTION 2 — Mechanic Ownership Check

For each turn, verify each mechanic is emitted by the correct stream.

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `quest_updates` | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` | progress |
| `gm_beat`, `beat_disposition` | progress |
| `actions`, `outcome_summary` | progress |

List any misplaced mechanics: turn, field, actual stream, correct stream.

***

## SECTION 3 — Cross-Pipeline I/O Relevance

For each pipeline, assess whether its inputs are focused:

**Rules**: inputs should be limited to pc, location, present_npcs, scene_pressure, recent_turns[-1:], user_input. Flag unnecessary context.

**Narrate**: richest inputs are justified — assess whether every input contributes. Flag inputs the narrator clearly doesn't use (cite turn where the input was present but had no effect on output).

**Extract Scene**: should receive narrative, pc/location, present_npcs, conditions, known_characters, rules_outcome. Flag if it receives inventory or quest data.

**Extract State**: should receive narrative, pc, inventory, rules_outcome, stakes, band, scene_result. Flag if it receives quest data, recent_events, or pressure data.

**Extract Progress**: richest extractor — assess whether every input enables a specific output. Flag inputs that appear unused.

***

## SECTION 4 — Prompt Redundancy Analysis

Reference the Prompt Redundancy signals in Deterministic Signals.

For each confirmed duplicate block:
1. Is it intentional? (Narration fed to all extractors is by design.)
2. If unintentional: which pipeline owns it? How should others access a summary?
3. Estimated token waste per turn.

**Top 3 dedup opportunities** — concrete remediations only.

***

## SECTION 5 — Prompt Adherence Rate

For each pipeline per turn: PASS (followed all system prompt rules) or FAIL (violated ≥1 rule).
Show: `(total PASS instances) / (5 pipelines × N turns)`.
This value goes in YAML front matter as `prompt_adherence_rate`.

***

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
Rules, Narrate, Extract Scene, Extract State, Extract Progress.
Major adherence failures cap at 2. State cap reason explicitly.

### Prompt Quality Score (1–5)
Synthesis of Section 1 audit results and Section 4 redundancy findings.
Which pipeline has the worst prompt architecture? What is the highest-priority fix?

***

## SECTION 7 — Actionable Issues

Group as **Critical** / **Major** / **Minor**.

- **<description>** (pipeline: <name>, turns: <list>) — Tag: `<bad_prompt|schema_drift|cross_pipeline_redundancy|instruction_ignored|wasted_tokens|misplaced_mechanic>`. Fix: <what to change in the prompt or data flow>.
```

**Validation:** Verify score keys and `pipeline_scores` structure match `JUDGE_SCORE_KEYS["prompt_pipeline"]` and `_normalize_scores`.

---

#### Step 3.4 — Write `evals/rubrics/compaction.md`

**File:** `evals/rubrics/compaction.md`

**What:** Rubric for Judge 4. Input is compaction-adjacent turns only: state snapshots at compaction turns (full), chronicle entries, progress extractor outputs, compaction signals block.

**Code Snippet**
```markdown
***
compaction_score: <int 1-5>
sanitization_fidelity_rate: <float 0.0-1.0>
***

# ccya Eval — Compaction Judge

You are evaluating the quality and correctness of the ccya compactor.
Compaction fires every N turns (typically every 6 turns in a 13-turn run, at T6 and T12).

You receive:
- State snapshots at and around compaction turns (full JSON, not diffs)
- Progress extractor outputs at compaction turns (which include chronicle bullets)
- Compaction signals block from the harness (per-capability observability)

If no compaction occurred in this run, state that and score 3/5 (neutral — cannot assess).

***

## SECTION 1 — Chronicle Quality

For each compaction pass (identify turns from the state_snapshot changes):

### Pass at Turn N
- List the chronicle bullets generated and the turns they cover.
- For each bullet:
  - Does it accurately represent named entities (NPCs, items, locations, quest IDs) from that turn?
  - Is it specific enough to distinguish this turn from any other?
  - Flag: `GENERIC` (could describe any turn), `INACCURATE` (wrong entity or inverted event), `MISSING_ENTITY` (named entity from turn omitted).

Score each pass: `[OK]` / `[PARTIAL]` / `[FAIL]`.

***

## SECTION 2 — Sanitization Fidelity

After each compaction pass, check:

| Field | Expected | Actual | Score |
|-------|----------|--------|-------|
| `quest_close` | completed/failed quests closed | | `[OK]`/`[FAIL]`/`[NA]` |
| `condition_remove` | resolved/expired conditions removed | | |
| `pressure_remove` | resolved pressures removed | | |
| `inventory_remove` | depleted items cleaned | | |
| `recent_events_compact` | recent_events entries for compacted turns consolidated | | |

**Sanitization Fidelity Rate:** (fields scored OK) / (fields scored OK + FAIL). Show arithmetic.
This value goes in YAML front matter.

***

## SECTION 3 — Compaction Score (1–5)

- 5: All bullets accurate, all sanitization fields OK.
- 4: Bullets OK, one sanitization miss.
- 3: Bullets partially generic or one PARTIAL pass, sanitization mostly OK.
- 2: Bullets inaccurate on ≥1 pass OR sanitization has ≥2 FAILs.
- 1: Bullets entirely inaccurate OR sanitization entirely absent.

***

## SECTION 4 — Actionable Issues

- **<description>** (turn: <N>) — Tag: `<generic_bullet|missing_entity|sanitization_miss|compaction_absent>`. Fix: <what to change in the compactor prompt or sanitization logic>.
```

**Validation:** Verify score keys match `JUDGE_SCORE_KEYS["compaction"]`.

---

#### Step 3.5 — Write `evals/rubrics/meta.md`

**File:** `evals/rubrics/meta.md`

**What:** Rubric for the meta-judge. Input is scores + key findings from all 4 domain judges. No raw trace data.

**Code Snippet**
```markdown
***
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
system_cohesion_score: <int 1-5>
prompt_quality_score: <int 1-5>
compaction_score: <int 1-5>
state_fidelity_rate: <float 0.0-1.0>
prompt_adherence_rate: <float 0.0-1.0>
***

# ccya Eval — Meta Judge (Synthesis)

You receive the scores and key findings from 4 focused domain judges:
- **state_correctness**: mechanic lifecycle tables, state fidelity, extraction accuracy
- **narrative_interplay**: narration tone, beat/pressure/condition story chains, system cohesion
- **prompt_pipeline**: prompt architecture, pipeline adherence, cross-pipeline redundancy
- **compaction**: chronicle quality, sanitization fidelity

Your job is synthesis, not new analysis. Do not re-examine the raw trace.
Identify contradictions between judges. Compute final composite scores.
Produce the single highest-priority fix.

***

## SECTION 1 — Score Synthesis

For each output score:

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | `extraction_accuracy_score` + `mechanic_lifecycle_score` avg | | |
| `narrative_score` | narrative_interplay | `narrative_score` | | |
| `system_cohesion_score` | narrative_interplay | `system_cohesion_score` | | |
| `prompt_quality_score` | prompt_pipeline | `prompt_quality_score` | | |
| `compaction_score` | compaction | `compaction_score` | | |
| `state_fidelity_rate` | state_correctness | `state_fidelity_rate` | | |
| `prompt_adherence_rate` | prompt_pipeline | `prompt_adherence_rate` | | |

Meta adjustment: if domain judges contradict each other on a shared concern, adjust with reasoning. Otherwise, pass through domain values unchanged. Do not inflate.

***

## SECTION 2 — Inter-Judge Contradiction Check

For each pair of judges that touch overlapping concerns:
- **state_correctness vs narrative_interplay**: state_correctness says state is clean but narrative_interplay says mechanics produce no story consequence — contradiction? Why?
- **state_correctness vs prompt_pipeline**: state_correctness says extraction is failing but prompt_pipeline rates the extraction prompts highly — contradiction? Why?
- **narrative_interplay vs prompt_pipeline**: narrative says directives are ignored but prompt_pipeline says narrate prompt adherence is good — which is right?

If no contradiction: write `None.`

***

## SECTION 3 — Trace Quality Synthesis

Based on domain judge findings (Section 11 or equivalent in their outputs):
1. What data was missing from the trace that would have improved assessment quality?
2. Is there a systematic gap (e.g., a field that all judges noted as absent)?
3. Recommendation for trace improvement.

***

## SECTION 4 — Final Verdict

### Highest-Priority Fix
One sentence. The single change to the engine (prompt, data flow, or mechanic) that would most improve the next run. Cite the domain judge and section that surfaced it.

### Key Findings
3–5 bullet points. Each cites a domain judge, section, and turn number.

### Regression Check
Compare domain scores against previous run scores (if provided in your input). Flag any score that dropped by ≥1. State whether the drop is consistent across judges or isolated.
```

**Validation:** Verify all 7 score keys in YAML front matter match `JUDGE_SCORE_KEYS["meta"]` and `_normalize_scores` in `judge.py`.

---

#### Step 3.6 — Extend `_normalize_scores` to handle new score keys

**File:** `ccya/eval/judge.py`

**What:** Add `extraction_accuracy_score`, `mechanic_lifecycle_score`, `sanitization_fidelity_rate` to `_normalize_scores`. These are emitted by the domain judges and need coercion to the right types.

**Why:** `_normalize_scores` is the single place where score values are validated and clamped. Any key not listed here passes through as raw YAML, which breaks `_fmt_score` / `_fmt_rate` in `report.py`.

**Code Snippet**
```python
def _normalize_scores(fm: dict[str, Any]) -> dict[str, Any]:
    def _coerce_int(v: Any) -> int | None:
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return None
        return max(1, min(5, n))

    def _coerce_rate(v: Any) -> float | None:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, f))

    out: dict[str, Any] = {}
    for k in (
        "mechanical_score", "narrative_score", "system_cohesion_score",
        "prompt_quality_score", "compaction_score",
        "extraction_accuracy_score", "mechanic_lifecycle_score",  # new
    ):
        if k in fm:
            out[k] = _coerce_int(fm[k])
    for k in ("state_fidelity_rate", "prompt_adherence_rate", "sanitization_fidelity_rate"):  # new
        if k in fm:
            out[k] = _coerce_rate(fm[k])
    ps = fm.get("pipeline_scores") or {}
    if isinstance(ps, dict):
        out["pipeline_scores"] = {
            k: _coerce_int(v) for k, v in ps.items()
            if k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress")
        }
    return out
```

**Validation:** Unit test: `_normalize_scores({"extraction_accuracy_score": 3, "sanitization_fidelity_rate": 0.8})` returns `{"extraction_accuracy_score": 3, "sanitization_fidelity_rate": 0.8}`.

### Tests to write or update
- `tests/test_eval.py`: `test_normalize_scores_new_keys` — assert `extraction_accuracy_score` and `sanitization_fidelity_rate` are coerced correctly and clamped at bounds.

### Risks
1. Rubric instructions may be interpreted inconsistently by the model across runs, especially for lifecycle tables. Mitigation: rubric language is prescriptive (exact column headers, exact flag values). Consistency improves with focused context vs. the current sprawling rubric.
2. The meta-judge's `_extract_section` regex may miss section headings if domain judges use non-standard heading levels. Mitigation: `_extract_section` searches case-insensitively by fragment; robust to minor formatting variation.

---

## Implementation — Phase 04: Parallel judge runner

### Files to pull for context
- `ccya/eval/judge.py` — full file
- `ccya/eval/cli.py` — `_run_one_scenario` function

### Detailed steps

#### Step 4.1 — Add `run_judges` orchestrator to `judge.py`

**File:** `ccya/eval/judge.py`

**What:** Add `run_judges(events_path, *, eval_cfg, output_dir, scenario_id, on_judge_complete, previous_run_dir)` that:
1. Builds shared pre-computed inputs (metrics_rows, failures, redundancy, compaction signals, arch_context) once.
2. Fans out to 4 domain judges in parallel via `asyncio.gather`.
3. Sequences the meta-judge after all 4 complete, passing their results via `_build_meta_judge_input`.
4. Returns `list[JudgeResult]` (4 domain + 1 meta = 5 total).

**Why:** Building shared signals once avoids redundant computation. Parallel execution of the 4 domain judges minimizes wall-clock time. The meta-judge must be sequential (depends on domain outputs).

**Code Snippet**
```python
from typing import Callable


async def _run_single_judge(
    spec: "JudgeSpec",
    trace: str,
    *,
    host: str,
    arch_context: str,
    output_dir: Path,
    scenario_id: str,
    on_chunk: Callable[[str, str], None],
    previous_scores: dict[str, Any] | None,
) -> "JudgeResult":
    """Run one judge spec against a pre-built trace string."""
    from ccya.llm_client import chat_stream

    rubric_path = Path(spec.rubric_path)
    if not rubric_path.is_absolute():
        rubric_path = REPO_ROOT / rubric_path
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")
    rubric_text = rubric_path.read_text()
    system_text = (rubric_text + "\n\n" + arch_context) if arch_context and spec.id != "meta" else rubric_text

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": trace},
    ]

    judge_model = spec.model
    if not judge_model:
        raise ValueError(f"judge model not set for spec {spec.id!r}")

    _log.info("judge[%s]: model=%s trace_chars=%d", spec.id, judge_model, len(trace))
    t0 = time.monotonic()
    chunks: list[str] = []
    try:
        async for chunk in chat_stream(
            host=host,
            model=judge_model,
            messages=messages,
            temperature=spec.temperature,
            timeout=spec.timeout_s or 180.0,
            max_tokens=spec.max_tokens,
        ):
            chunks.append(chunk)
            on_chunk(spec.id, chunk)
    except TypeError:
        async for chunk in chat_stream(
            host=host,
            model=judge_model,
            messages=messages,
            temperature=spec.temperature,
            timeout=spec.timeout_s or 180.0,
        ):
            chunks.append(chunk)
            on_chunk(spec.id, chunk)
    elapsed = time.monotonic() - t0
    _log.info("judge[%s]: complete in %.1fs", spec.id, elapsed)

    raw = "".join(chunks)
    judge_md_path = output_dir / f"{scenario_id}.{spec.id}.judge.md"
    judge_md_path.write_text(raw)

    trace_md_path = output_dir / f"{scenario_id}.{spec.id}.trace.md"
    # trace was already written by caller before this function was invoked

    scores, body = parse_judge_response(raw)
    return JudgeResult(
        raw_response=raw,
        body_md=body,
        scores=scores,
        rubric_path=str(rubric_path),
        model=judge_model,
        judge_id=spec.id,
        trace_md_path=str(trace_md_path),
        judge_md_path=str(judge_md_path),
        previous_scores=previous_scores,
    )


async def run_judges(
    events_path: Path,
    *,
    eval_cfg: "EvalConfig",
    output_dir: Path,
    scenario_id: str,
    on_judge_complete: Callable[[str, "JudgeResult"], None] | None = None,
    previous_run_dir: Path | None = None,
    game_config_path: Path | None = None,
) -> list["JudgeResult"]:
    """Fan-out to N domain judges in parallel, then run meta judge sequentially.

    Returns list of JudgeResult, one per spec in eval_cfg.judges.specs.
    Meta judge is always last in the returned list if present.
    on_judge_complete(judge_id, result) is called after each judge finishes.
    """
    from ccya.models import load_config

    if not eval_cfg.judges.specs:
        return []

    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    game_cfg = load_config(cfg_path)
    llm = game_cfg.get("llm", {})
    host = str(llm.get("host", "http://localhost:8080/v1"))

    events_lines = events_path.read_text().splitlines() if events_path.exists() else []
    events = [json.loads(line) for line in events_lines if line.strip()]

    options = TraceOptions(
        dedup_immutable_sections=eval_cfg.judges.trace.dedup_immutable_sections,
        state_as_diff=eval_cfg.judges.trace.state_as_diff,
    )

    # Build shared signals once
    metrics_rows = _build_metrics_rows(events)
    turn_events_for_check = [e for e in events if not e.get("__metadata__")]
    failures: list[dict[str, Any]] = []
    prev_ev: dict[str, Any] | None = None
    for ev in turn_events_for_check:
        for r in run_all_universal_asserts(ev, prev_ev):
            if not r.get("passed"):
                failures.append({
                    "turn": ev.get("turn", "?"),
                    "assertion": r["assertion"],
                    "detail": r.get("detail", ""),
                })
        prev_ev = ev

    try:
        from ccya.eval.redundancy import compute_redundancy_signals
        redundancy = compute_redundancy_signals(events)
    except ImportError:
        redundancy = None

    try:
        from ccya.eval.compaction_signals import compute_compaction_signals
        compaction = compute_compaction_signals(events)
    except ImportError:
        compaction = None

    try:
        from ccya.eval.architecture_context import load_architecture_context
        arch_context = load_architecture_context()
    except ImportError:
        arch_context = ""

    # Load previous scores per judge_id if previous run exists
    prev_scores_by_id: dict[str, dict[str, Any]] = {}
    if previous_run_dir is not None:
        for spec in eval_cfg.judges.specs:
            candidate = previous_run_dir / f"{scenario_id}.{spec.id}.judge.md"
            if candidate.exists():
                s, _ = parse_judge_response(candidate.read_text())
                if s:
                    prev_scores_by_id[spec.id] = s

    # Determine which specs are domain judges vs meta
    domain_specs = [s for s in eval_cfg.judges.specs if s.id != "meta"]
    meta_spec = next((s for s in eval_cfg.judges.specs if s.id == "meta"), None)

    # Build and write traces for domain judges
    domain_traces: dict[str, str] = {}
    for spec in domain_specs:
        trace = build_trace_for_judge(
            spec.id, events,
            options=options,
            auto_checker_failures=failures,
            metrics_rows=metrics_rows,
            redundancy_signals=redundancy,
            compaction_signals=compaction,
            arch_context=arch_context,
        )
        trace_md_path = output_dir / f"{scenario_id}.{spec.id}.trace.md"
        trace_md_path.write_text(trace)
        domain_traces[spec.id] = trace

    # Resolve model for each spec (fall back to engine model if not set)
    engine_model = str(llm.get("model", ""))
    for spec in eval_cfg.judges.specs:
        if not spec.model:
            object.__setattr__(spec, "model", engine_model)  # JudgeSpec is not frozen

    def _noop_chunk(judge_id: str, chunk: str) -> None:
        pass

    # Run domain judges in parallel
    async def _run_domain(spec: "JudgeSpec") -> "JudgeResult":
        result = await _run_single_judge(
            spec,
            domain_traces[spec.id],
            host=host,
            arch_context=arch_context,
            output_dir=output_dir,
            scenario_id=scenario_id,
            on_chunk=_noop_chunk,
            previous_scores=prev_scores_by_id.get(spec.id),
        )
        if on_judge_complete:
            on_judge_complete(spec.id, result)
        return result

    domain_results: list["JudgeResult"] = list(
        await asyncio.gather(*[_run_domain(spec) for spec in domain_specs])
    )

    all_results = list(domain_results)

    # Run meta judge sequentially after domain judges
    if meta_spec is not None:
        meta_input = _build_meta_judge_input(domain_results)
        meta_trace_path = output_dir / f"{scenario_id}.meta.trace.md"
        meta_trace_path.write_text(meta_input)
        meta_result = await _run_single_judge(
            meta_spec,
            meta_input,
            host=host,
            arch_context="",
            output_dir=output_dir,
            scenario_id=scenario_id,
            on_chunk=_noop_chunk,
            previous_scores=prev_scores_by_id.get("meta"),
        )
        if on_judge_complete:
            on_judge_complete("meta", meta_result)
        all_results.append(meta_result)

    return all_results


def merge_judge_scores(results: list["JudgeResult"]) -> dict[str, Any]:
    """Merge scores from multiple JudgeResults into one flat dict for report rendering.

    Meta judge scores take precedence. Domain judge scores fill in any gaps.
    pipeline_scores dict is taken from the prompt_pipeline judge.
    """
    merged: dict[str, Any] = {}
    # First pass: domain judges
    for jr in results:
        if jr.judge_id != "meta":
            for k, v in (jr.scores or {}).items():
                if k not in merged:
                    merged[k] = v
    # Second pass: meta judge overwrites
    meta = next((jr for jr in results if jr.judge_id == "meta"), None)
    if meta:
        for k, v in (meta.scores or {}).items():
            merged[k] = v
    return merged
```

**Validation:**
- With a real `events.jsonl`, call `run_judges(...)` and confirm 5 `JudgeResult` objects returned, each with the correct `judge_id`, and non-empty `scores`.
- Confirm 5 `*.trace.md` and 5 `*.judge.md` files written to `output_dir`.
- Confirm `merge_judge_scores` returns all 7 top-level score keys when meta judge emits all of them.

---

#### Step 4.2 — Keep `run_judge_streaming` as a back-compat wrapper

**File:** `ccya/eval/judge.py`

**What:** Update `run_judge_streaming` and `run_judge` to continue working with the legacy single

#### Step 4.2 — Keep `run_judge_streaming` as a back-compat wrapper

**File:** `ccya/eval/judge.py`

**What:** Update `run_judge_streaming` and `run_judge` to delegate to `run_judges` when the config has multiple specs, or fall back to original single-judge behavior when only one spec with `id="default"` is present. This preserves `judge-only` CLI behavior without a flag.

**Why:** `cli.py` currently calls `run_judge_streaming` directly. Changing that in Phase 06 is the clean path, but keeping a shim here means Phase 06 is not a hard dependency for correctness.

**Code Snippet**
```python
async def run_judge_streaming(
    events_path: Path,
    *,
    eval_cfg: "EvalConfig",
    output_dir: Path,
    scenario_id: str,
    on_chunk: Callable[[str], None] | None = None,
    previous_judge_md_path: Path | None = None,
) -> "JudgeResult":
    """Back-compat single-judge entry point.

    If eval_cfg.judges.specs has >1 spec or contains non-default ids,
    delegates to run_judges() and returns the meta judge result (or the
    last result if no meta spec is configured).

    If only a single 'default' spec is present, runs original single-judge path.
    """
    specs = eval_cfg.judges.specs
    is_multi = len(specs) > 1 or (len(specs) == 1 and specs[0].id != "default")

    if is_multi:
        results = await run_judges(
            events_path,
            eval_cfg=eval_cfg,
            output_dir=output_dir,
            scenario_id=scenario_id,
        )
        # Return meta judge result if present, else last result
        meta = next((r for r in results if r.judge_id == "meta"), None)
        return meta or results[-1]

    # Legacy single-judge path — original implementation unchanged below
    spec = specs[0] if specs else JudgeSpec(id="default", rubric_path="evals/rubrics/default.md")
    # ... (existing implementation body, unchanged)
```

**Validation:** `run_judge_streaming` with a legacy single-spec config still returns a single `JudgeResult` with `judge_id="default"`. With multi-spec config returns meta result.

### Tests to write or update
- `tests/test_eval.py`: `test_run_judges_fan_out` — mock `_run_single_judge` to return fixtures; assert 5 results, correct ids, meta is last.
- `tests/test_eval.py`: `test_merge_judge_scores_meta_wins` — meta score overwrites domain score for same key.
- `tests/test_eval.py`: `test_run_judge_streaming_backcompat` — single default spec routes to legacy path.

### Risks
1. `asyncio.gather` on 4 concurrent judge calls may hit the local LLM server's concurrency limit (most local servers process one request at a time). Mitigation: `asyncio.gather` will queue naturally since the HTTP client awaits each chunk. No change needed — effective serialization happens at the server without code changes. If true parallelism is wanted later, a semaphore can be added.
2. `object.__setattr__` on `JudgeSpec` to set `model` is fragile if `JudgeSpec` becomes a frozen dataclass. Mitigation: make `model` a `str` (not `str | None`) with empty string default, and resolve the engine model in `load_eval_config` itself when `model` is absent.

***

## Implementation — Phase 05: Report assembly

### Files to pull for context
- `ccya/eval/report.py` — full file (already reviewed)
- `ccya/eval/judge.py` — `JudgeResult` dataclass, `merge_judge_scores`

### Detailed steps

#### Step 5.1 — Update `_render_judge_summary` to accept list of results

**File:** `ccya/eval/report.py`

**What:** Change signature to `_render_judge_summary(judges: list[JudgeResult] | JudgeResult | None) -> str`. When a list is passed, call `merge_judge_scores` to get the merged flat dict for display. Add a per-judge score table below the merged summary showing each domain judge's individual scores.

**Why:** The report currently renders one flat score block. With 5 judges, the reader needs both the merged verdict (from meta) and the domain breakdown.

**Code Snippet**
```python
from ccya.eval.judge import JudgeResult, merge_judge_scores


def _render_judge_summary(
    judges: list[JudgeResult] | JudgeResult | None,
) -> str:
    if judges is None:
        return ""
    if isinstance(judges, JudgeResult):
        judges = [judges]
    if not judges:
        return ""

    merged = merge_judge_scores(judges)
    meta = next((j for j in judges if j.judge_id == "meta"), judges[-1])

    parts: list[str] = []

    # Merged scores block
    parts.append(f"**Mechanical:** {_fmt_score(merged.get('mechanical_score'))}/5  ")
    parts.append(f"**Narrative:** {_fmt_score(merged.get('narrative_score'))}/5  ")
    parts.append(f"**System Cohesion:** {_fmt_score(merged.get('system_cohesion_score'))}/5  ")
    parts.append(f"**Prompt Quality:** {_fmt_score(merged.get('prompt_quality_score'))}/5  ")
    parts.append(f"**Compaction:** {_fmt_score(merged.get('compaction_score'))}/5  ")
    parts.append(f"**State Fidelity:** {_fmt_rate(merged.get('state_fidelity_rate'))}  ")
    parts.append(f"**Prompt Adherence:** {_fmt_rate(merged.get('prompt_adherence_rate'))}")
    parts.append(f"**Judge model:** `{meta.model}`")
    ps = merged.get("pipeline_scores") or {}
    if ps:
        parts.append("")
        parts.append("**Pipeline scores:**")
        for k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress"):
            parts.append(f"- {k}: {_fmt_score(ps.get(k))}/5")
    parts.append("")

    # Domain judge breakdown table
    domain_judges = [j for j in judges if j.judge_id != "meta"]
    if len(domain_judges) > 1:
        parts.append("**Domain judge breakdown:**")
        parts.append("")
        parts.append("| Judge | Scores |")
        parts.append("|---|---|")
        for jr in domain_judges:
            score_items = []
            for k, v in (jr.scores or {}).items():
                if k == "pipeline_scores":
                    continue
                if isinstance(v, float):
                    score_items.append(f"{k}={_fmt_rate(v)}")
                else:
                    score_items.append(f"{k}={_fmt_score(v)}")
            parts.append(f"| `{jr.judge_id}` | {', '.join(score_items)} |")
        parts.append("")

    # Previous scores comparison (use meta or last judge)
    if meta.previous_scores:
        prev_mech = meta.previous_scores.get("mechanical_score")
        prev_narr = meta.previous_scores.get("narrative_score")
        if prev_mech is not None:
            parts.append(f"**Previous mechanical:** {prev_mech}/5")
        if prev_narr is not None:
            parts.append(f"**Previous narrative:** {prev_narr}/5")
        parts.append("")

    # Artifact links for all judges
    for jr in judges:
        label = jr.judge_id
        parts.append(
            f"**[{label} trace]({Path(jr.trace_md_path).name})** · "
            f"**[{label} verdict]({Path(jr.judge_md_path).name})**  "
        )
    parts.append("")
    return "\n".join(parts)
```

**Validation:** `_render_judge_summary([jr1, jr2, jr_meta])` produces markdown with merged scores block + domain breakdown table + artifact links for all 3 judges.

***

#### Step 5.2 — Update `_collect_flags` to handle list of JudgeResults

**File:** `ccya/eval/report.py`

**What:** Change `_collect_flags` signature: `judge: JudgeResult | list[JudgeResult] | None`. When a list is passed, find the meta judge (or last result) for the `judge_score_drop` check and use `merge_judge_scores` to get `mechanical_score`.

**Why:** The flag logic currently checks `judge.scores.get("mechanical_score")` from a single judge. With multi-judge, `mechanical_score` lives in the meta judge's scores.

**Code Snippet**
```python
def _collect_flags(
    cur: list[TurnMetrics],
    regressions: list[StreamRegression],
    run_result: RunResult,
    judge: JudgeResult | list[JudgeResult] | None,
) -> list[Flag]:
    flags: list[Flag] = []

    # ... existing tokens_regression, extraction_retries, extraction_failures,
    # rejected_deltas, runner_errors, parse_failures logic unchanged ...

    if judge is not None:
        if isinstance(judge, list):
            merged = merge_judge_scores(judge)
            representative = next((j for j in judge if j.judge_id == "meta"), judge[-1])
            prev_scores = representative.previous_scores or {}
        else:
            merged = judge.scores or {}
            prev_scores = judge.previous_scores or {}

        prev_score = prev_scores.get("mechanical_score")
        cur_score = merged.get("mechanical_score")
        if prev_score is not None and cur_score is not None and (prev_score - cur_score) >= 1:
            flags.append(
                Flag(
                    kind="judge_score_drop",
                    summary=f"judge mechanical {prev_score} → {cur_score} (-{prev_score - cur_score})",
                    detail="See judge verdict files for analysis.",
                ),
            )

    return flags
```

**Validation:** `_collect_flags` called with `judge=list_of_results` produces correct `judge_score_drop` flag when meta mechanical_score is lower than previous.

***

#### Step 5.3 — Update `finalize_report` to accept list of JudgeResults

**File:** `ccya/eval/report.py`

**What:** Change `finalize_report` signature: `judge_result: JudgeResult | list[JudgeResult]`. When a list is passed: use `merge_judge_scores` for the summary; render all judge body sections (one `## Judge Verdict — {id}` section per judge). `_collect_flags` gets the list. The `write_report_skeleton` streaming sentinel stays identical — it's always replaced wholesale.

**Why:** Callers in `cli.py` will pass the list returned by `run_judges`. The report needs to surface all 5 bodies, not just the meta's.

**Code Snippet**
```python
def finalize_report(
    report_path: Path,
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_result: JudgeResult | list[JudgeResult],
    runs_dir: Path | None = None,
) -> None:
    judges = judge_result if isinstance(judge_result, list) else [judge_result]

    output_dir = Path(run_result.output_dir)
    runs_dir = runs_dir or output_dir.parent
    cur_events = _read_events(Path(run_result.events_jsonl_path))
    cur_metrics = _summarize_events(cur_events)
    prev_metrics: list[TurnMetrics] = []
    prev_run_path: Path | None = None
    prev_json = find_previous_run(runs_dir, run_result.scenario_id, exclude=output_dir)
    if prev_json is not None:
        prev_run_path = prev_json.parent
        prev_run = load_run_result(prev_json)
        prev_events = _read_events(Path(prev_run.events_jsonl_path))
        prev_metrics = _summarize_events(prev_events)
    regressions = _compute_regressions(
        cur_metrics, prev_metrics,
        warn_pct=eval_cfg.report.token_warn_pct,
        fail_pct=eval_cfg.report.token_fail_pct,
    )
    flags = _collect_flags(cur_metrics, regressions, run_result, judges)

    parts: list[str] = []
    parts.append(f"# Eval Report — `{run_result.scenario_id}`\n")
    parts.append(
        f"**Pack:** `{run_result.pack}` · **Model:** `{run_result.model}` · "
        f"**Temp override:** `{run_result.temperature_override}`  "
    )
    parts.append(
        f"**Started:** {run_result.started_at} · **Finished:** {run_result.finished_at}  "
    )
    parts.append(f"**Output dir:** `{run_result.output_dir}`  ")
    parts.append(
        f"**Compared against:** `{prev_run_path}`" if prev_run_path is not None
        else "**Compared against:** _(no prior run found)_"
    )
    parts.append("")
    parts.append("## Judge Summary\n")
    parts.append(_render_judge_summary(judges))
    parts.append(_render_flag_block(flags, eval_cfg.report.flag_at_top))
    parts.append("")

    # One verdict section per judge, meta last
    domain_judges = [j for j in judges if j.judge_id != "meta"]
    meta_judge = next((j for j in judges if j.judge_id == "meta"), None)
    for jr in domain_judges:
        parts.append(f"## Judge Verdict — `{jr.judge_id}`\n")
        parts.append(jr.body_md)
        parts.append("")
    if meta_judge:
        parts.append("## Meta Judge Verdict\n")
        parts.append(meta_judge.body_md)
        parts.append("")

    auto_block = _render_auto_checker_block(run_result)
    if auto_block:
        parts.append("## Auto-Checker\n")
        parts.append(auto_block)
    assert_table = _render_assert_summary_table(run_result)
    if assert_table:
        parts.append(assert_table)
    pacing = _compute_pacing_metrics(cur_events)
    if pacing:
        parts.append(pacing)
    parts.append("## Turn Metrics\n")
    parts.append(_render_combined_table(cur_metrics, prev_metrics, run_result))
    if regressions:
        warns = [r for r in regressions if r.severity == "warn"]
        if warns:
            parts.append("\n## Warnings (≥ warn threshold but < fail threshold)\n")
            for r in warns:
                parts.append(
                    f"- `{r.stream}` turn {r.turn}: "
                    f"{r.prev_tokens_in} → {r.cur_tokens_in} (+{r.pct_change:.1f}%)"
                )

    tmp = report_path.with_suffix(".md.tmp")
    tmp.write_text("\n".join(parts) + "\n")
    tmp.replace(report_path)
```

**Validation:** `finalize_report` with a 5-element list produces a REPORT.md with 4 domain verdict sections + 1 meta section + correct merged summary block.

### Tests to write or update
- `tests/test_eval.py`: `test_render_judge_summary_multi` — assert domain breakdown table present, all artifact links present.
- `tests/test_eval.py`: `test_finalize_report_multi_judge` — mock `JudgeResult` list, assert REPORT.md contains all 5 `## Judge Verdict` headings and merged score keys.

### Risks
1. `generate_report` (back-compat entry point) still accepts `JudgeResult | None`. If callers pass a list it will type-error. Mitigation: update `generate_report` signature to `JudgeResult | list[JudgeResult] | None` and forward accordingly.

***

## Implementation — Phase 06: CLI wiring

### Files to pull for context
- `ccya/eval/cli.py` — full file (already reviewed)

### Detailed steps

#### Step 6.1 — Update `_run_one_scenario` to call `run_judges`

**File:** `ccya/eval/cli.py`

**What:** Replace the `run_judge_streaming` call in `_run_one_scenario` with `run_judges`. Wire `on_judge_complete` to stream each domain judge's output to the report skeleton via `append_judge_chunk`. Update the `finalize_report` call to pass the list.

**Why:** This is where the new parallel execution enters the run path.

**Code Snippet**
```python
from ccya.eval.judge import run_judges, merge_judge_scores, JudgeResult

# Replace the judge block in _run_one_scenario:

    judge_results: list[JudgeResult] = []
    if not args.no_judge and eval_cfg.judges.enabled:
        prev_json = find_previous_run(
            (REPO_ROOT / eval_cfg.runs_dir).resolve(),
            scenario.id,
            exclude=Path(rr.output_dir),
        )
        prev_run_dir: Path | None = None
        if prev_json is not None:
            prev_run_dir = prev_json.parent

        print("[eval] judges running (parallel domain + sequential meta)…", file=sys.stderr)

        def _on_judge_complete(judge_id: str, result: JudgeResult) -> None:
            print(f"[eval] judge[{judge_id}] complete: scores={result.scores}", file=sys.stderr)

        judge_results = await run_judges(
            Path(rr.events_jsonl_path),
            eval_cfg=eval_cfg,
            output_dir=Path(rr.output_dir),
            scenario_id=scenario.id,
            on_judge_complete=_on_judge_complete,
            previous_run_dir=prev_run_dir,
        )

        merged = merge_judge_scores(judge_results)
        mech = merged.get("mechanical_score", "?")
        print(f"[eval] judges done: mechanical_score={mech}", file=sys.stderr)

        # Update run result artifact paths (use meta or last judge)
        representative = next((r for r in judge_results if r.judge_id == "meta"), judge_results[-1])
        rr.trace_md_path = representative.trace_md_path
        rr.judge_md_path = representative.judge_md_path

        artifacts_dir = Path(rr.output_dir) / "artifacts"
        (artifacts_dir / f"{scenario.id}.run.json").write_text(
            json.dumps(asdict(rr), indent=2, default=str)
        )
        finalize_report(report_path, rr, eval_cfg=eval_cfg, judge_result=judge_results)
        print(f"[eval] report finalized: {report_path}", file=sys.stderr)
```

**Validation:** `python -m ccya.eval run` completes a scenario, writes 5 `*.judge.md` files to the output dir, and REPORT.md contains all verdict sections.

***

#### Step 6.2 — Update `_cmd_judge_only` to call `run_judges`

**File:** `ccya/eval/cli.py`

**What:** Replace the `run_judge` call in `_cmd_judge_only` with `run_judges`. Print per-judge scores on completion. Pass the list to `generate_report`.

**Code Snippet**
```python
async def _cmd_judge_only(args: argparse.Namespace) -> int:
    eval_cfg = load_eval_config()
    # ... logging setup unchanged ...

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"[eval] not a directory: {run_dir}", file=sys.stderr)
        return 1

    run_jsons = (
        sorted((run_dir / "artifacts").glob("*.run.json"))
        if (run_dir / "artifacts").is_dir()
        else sorted(run_dir.glob("*.run.json"))
    )
    if not run_jsons:
        print(f"[eval] no *.run.json found in {run_dir}/artifacts/", file=sys.stderr)
        return 1
    rr = load_run_result(run_jsons[0])

    events_path = Path(rr.events_jsonl_path)
    if not events_path.exists():
        print(f"[eval] events not found: {events_path}", file=sys.stderr)
        return 1

    runs_dir = run_dir.parent
    prev_json = find_previous_run(runs_dir, rr.scenario_id, exclude=run_dir)
    prev_run_dir: Path | None = prev_json.parent if prev_json is not None else None

    judge_results = await run_judges(
        events_path,
        eval_cfg=eval_cfg,
        output_dir=Path(rr.output_dir),
        scenario_id=rr.scenario_id,
        previous_run_dir=prev_run_dir,
    )

    from ccya.eval.judge import merge_judge_scores
    merged = merge_judge_scores(judge_results)
    mech = merged.get("mechanical_score", "?")
    report_path = generate_report(rr, eval_cfg=eval_cfg, judge_result=judge_results)
    print(f"[eval] re-judged: mechanical_score={mech}", file=sys.stderr)
    print(str(report_path))
    return 0
```

**Validation:** `python -m ccya.eval judge-only <run_dir>` produces updated REPORT.md with multi-judge output.

***

#### Step 6.3 — Update `_cmd_pack` to print new judges config

**File:** `ccya/eval/cli.py`

**What:** Replace the old `judge.*` prints with a loop over `cfg.judges.specs`.

**Code Snippet**
```python
def _cmd_pack(args: argparse.Namespace) -> int:
    cfg = load_eval_config()
    print("Eval config:")
    for k in ("default_pack", "default_scenario", "pack_dirs", "default_save_root", "runs_dir", "num_turns"):
        print(f"  {k}: {getattr(cfg, k)}")
    print(f"  logging.level: {cfg.logging.level}")
    print(f"  inference.temperature_override: {cfg.inference.temperature_override}")
    print(f"  inference.cache: {cfg.inference.cache}")
    print(f"  judges.enabled: {cfg.judges.enabled}")
    for spec in cfg.judges.specs:
        print(
            f"  judges.specs[{spec.id}]: rubric={spec.rubric_path} "
            f"model={spec.model} temp={spec.temperature} max_tokens={spec.max_tokens}"
        )
    print(f"  report.token_warn_pct: {cfg.report.token_warn_pct}")
    print(f"  report.token_fail_pct: {cfg.report.token_fail_pct}")
    print(f"  report.flag_at_top: {cfg.report.flag_at_top}")
    return 0
```

**Validation:** `python -m ccya.eval pack` prints one line per spec.

### Tests to write or update
- `tests/test_eval.py`: integration test `test_cmd_judge_only_multi` — provide a fixture run dir with known `events.jsonl`, mock `_run_single_judge`, assert REPORT.md contains 5 verdict sections.

### Risks
1. `append_judge_chunk` is currently called with a single string chunk during streaming. Multi-judge does not stream (all judges complete before report is finalized). The streaming sentinel in the report skeleton will remain open until `finalize_report` rewrites the file. This is acceptable — the skeleton says "streaming…" for the duration of all 5 judge calls. If live streaming per domain judge is desired, a Phase 06b can add a per-judge sentinel scheme.

***

## Implementation — Phase 07: Tests & REPOMAP

### Files to pull for context
- `tests/test_eval.py` — full file
- `docs/REPOMAP/eval.md` (if it exists)
- `AGENTS.md`

### Detailed steps

#### Step 7.1 — Audit and update all existing eval tests

**File:** `tests/test_eval.py`

**What:** Review every test that constructs `JudgeConfig`, calls `load_eval_config`, constructs `JudgeResult`, or calls `_render_judge_summary`. Update each to match the new types. Specifically:
- Any test building `JudgeConfig(...)` → replace with `JudgesConfig(specs=[JudgeSpec(...)])`.
- Any test passing `JudgeResult` without `judge_id` → still works (default `"default"`).
- Any test calling `_render_judge_summary(jr)` with a single `JudgeResult` → still works (list wrapping added).
- Any test checking `eval_cfg.judge.rubric_path` → update to `eval_cfg.judges.specs[0].rubric_path`.

**Why:** Dead code policy — tests that reference removed APIs must be updated, not left failing silently.

**Validation:** `make test` passes with no skipped tests. No `AttributeError: 'JudgesConfig' object has no attribute 'rubric_path'`.

***

#### Step 7.2 — Add new tests

**File:** `tests/test_eval.py`

**What:** Add the following tests (signatures and assertions listed):

```python
def test_load_eval_config_multi_judge():
    """Config with judges.specs parses correctly."""
    # Write a temp config with 5 specs; assert len(cfg.judges.specs) == 5
    # Assert each spec has correct id, rubric_path

def test_load_eval_config_legacy_single_judge():
    """Old flat judge: block still parses as single spec with id='default'."""
    # Write old-style config; assert len(cfg.judges.specs) == 1 and specs[0].id == "default"

def test_normalize_scores_new_keys():
    """New score keys coerced correctly."""
    result = _normalize_scores({
        "extraction_accuracy_score": "4",
        "mechanic_lifecycle_score": 2,
        "sanitization_fidelity_rate": "0.85",
    })
    assert result["extraction_accuracy_score"] == 4
    assert result["mechanic_lifecycle_score"] == 2
    assert abs(result["sanitization_fidelity_rate"] - 0.85) < 0.001

def test_normalize_scores_clamping():
    result = _normalize_scores({"extraction_accuracy_score": 7, "sanitization_fidelity_rate": 1.5})
    assert result["extraction_accuracy_score"] == 5
    assert result["sanitization_fidelity_rate"] == 1.0

def test_build_trace_for_judge_state_correctness(sample_events):
    trace = build_trace_for_judge("state_correctness", sample_events)
    assert "Narrate User Prompt" not in trace
    assert "State After" in trace or "Applied Deltas" in trace

def test_build_trace_for_judge_prompt_pipeline(sample_events_with_prompts):
    trace = build_trace_for_judge("prompt_pipeline", sample_events_with_prompts)
    assert "System Prompt" in trace or "rules_prompt" in trace.lower()

def test_build_trace_for_judge_compaction_no_compaction(sample_events):
    """When no compaction detected, all events returned."""
    trace = build_trace_for_judge("compaction", sample_events)
    assert trace  # non-empty

def test_build_meta_judge_input_structure():
    jr1 = JudgeResult(
        raw_response="", body_md="## Key Findings\n- foo",
        scores={"state_fidelity_rate": 0.9}, rubric_path="r.md",
        model="m", judge_id="state_correctness",
    )
    jr2 = JudgeResult(
        raw_response="", body_md="## Actionable Issues\n- bar",
        scores={"narrative_score": 3}, rubric_path="r.md",
        model="m", judge_id="narrative_interplay",
    )
    result = _build_meta_judge_input([jr1, jr2])
    assert "state_correctness" in result
    assert "Key Findings" in result
    assert "Actionable Issues" in result
    assert "state_fidelity_rate" in result

def test_merge_judge_scores_meta_wins():
    domain = JudgeResult(raw_response="", body_md="", scores={"mechanical_score": 2},
                         rubric_path="r.md", model="m", judge_id="state_correctness")
    meta = JudgeResult(raw_response="", body_md="", scores={"mechanical_score": 4},
                       rubric_path="r.md", model="m", judge_id="meta")
    merged = merge_judge_scores([domain, meta])
    assert merged["mechanical_score"] == 4

def test_merge_judge_scores_domain_fills_gaps():
    domain = JudgeResult(raw_response="", body_md="",
                         scores={"compaction_score": 3, "sanitization_fidelity_rate": 0.7},
                         rubric_path="r.md", model="m", judge_id="compaction")
    meta = JudgeResult(raw_response="", body_md="",
                       scores={"mechanical_score": 4},
                       rubric_path="r.md", model="m", judge_id="meta")
    merged = merge_judge_scores([domain, meta])
    assert merged["compaction_score"] == 3
    assert merged["mechanical_score"] == 4

def test_render_judge_summary_multi():
    jr1 = JudgeResult(raw_response="", body_md="",
                      scores={"state_fidelity_rate": 0.9, "extraction_accuracy_score": 4},
                      rubric_path="r.md", model="m", judge_id="state_correctness",
                      trace_md_path="sc.trace.md", judge_md_path="sc.judge.md")
    meta = JudgeResult(raw_response="", body_md="",
                       scores={"mechanical_score": 4, "narrative_score": 3},
                       rubric_path="r.md", model="m", judge_id="meta",
                       trace_md_path="meta.trace.md", judge_md_path="meta.judge.md")
    summary = _render_judge_summary([jr1, meta])
    assert "state_correctness" in summary
    assert "meta.judge.md" in summary
    assert "mechanical_score" not in summary  # rendered as **Mechanical:**, not raw key name
    assert "Mechanical:" in summary
```

**Validation:** `make test` green.

***

#### Step 7.3 — Update `docs/REPOMAP/eval.md`

**File:** `docs/REPOMAP/eval.md`

**What:** Add entries for:
- `build_trace_for_judge(judge_id, events, ...)` — returns filtered trace string for a given judge domain.
- `run_judges(events_path, *, eval_cfg, ...)` — parallel fan-out to domain judges + sequential meta judge; returns `list[JudgeResult]`.
- `merge_judge_scores(results)` — merges partial score dicts; meta wins conflicts.
- `_build_meta_judge_input(judge_results)` — assembles meta-judge user message from domain outputs.
- `JUDGE_SCORE_KEYS` — maps judge id to its expected score keys.
- `JudgeSpec` — per-judge config (id, rubric_path, model, temperature, max_tokens).
- `JudgesConfig` — replaces `JudgeConfig`; holds list of specs + shared trace config.
- New rubric files: `evals/rubrics/state_correctness.md`, `narrative_interplay.md`, `prompt_pipeline.md`, `compaction.md`, `meta.md`.

Update the existing `JudgeConfig` entry to note it is superseded by `JudgesConfig` and will be removed.

Update the `run_judge_streaming` entry to note it is a back-compat shim over `run_judges`.

**Validation:** No dead entries in REPOMAP pointing to renamed functions.

***

#### Step 7.4 — Final validation

**File:** N/A (make targets)

**What:** Run the full check and test suite.

```bash
make check && make test
```

Expected: all lint passes, all tests green. Address any type errors surfaced by mypy on the changed signatures.

### Risks
1. `make check` may flag the `object.__setattr__` call in Phase 04 as a mypy error. Mitigation: resolve in Phase 04 risk mitigation (non-optional `model` field).
2. If `docs/REPOMAP/eval.md` does not exist yet, create it with the entries above; do not add REPOMAP entries to the wrong file.

***

## Ambiguities requiring resolution before execution

1. **Local LLM concurrency**: `asyncio.gather` on 4 domain judges will issue 4 concurrent requests to the local LLM server. Does the server (llama.cpp or mlx_lm) queue them, reject with 429, or deadlock? Options: A) Accept natural serialization at server level (recommended — no code change). B) Add `asyncio.Semaphore(1)` to force strict serialization in the client. C) Add `asyncio.Semaphore(N)` for configurable parallelism.

2. **`redundancy_signals` and `compaction_signals` modules**: `ccya.eval.redundancy` and `ccya.eval.compaction_signals` are imported with `try/except ImportError` in `run_judges`. Do these modules exist? Options: A) They don't exist yet — the `try/except` stub is correct and they return `None` until implemented. B) They exist under different names — identify the actual module paths before Phase 04 execution.

3. **`_build_metrics_rows` function**: Phase 04 calls `_build_metrics_rows(events)` assuming it exists in `judge.py`. Verify the actual function name that produces the metrics table rows from events in the current codebase before Phase 04 execution.

4. **`run_all_universal_asserts` import**: Phase 04 calls `run_all_universal_asserts(ev, prev_ev)` inside `run_judges`. Verify the exact import path and function signature from the current codebase before Phase 04 execution.

5. **`JudgeSpec` mutability**: Phase 04 uses `object.__setattr__` to set `model` when it's `None`. If you prefer immutability, make `model` default to `""` (empty string) and resolve the engine model in `load_eval_config` by reading `config.yaml` at parse time. Options: A) Keep `model: str | None` with runtime fallback in `run_judges` (current plan). B) Resolve at config load time and make `model: str` required.

6. **Streaming sentinel during multi-judge run**: The `write_report_skeleton` writes a `## Judge (streaming…)` sentinel. With multi-judge, all judges complete before `finalize_report` rewrites the file, so the skeleton is only visible if you open the file mid-run. Is that acceptable? Options: A) Accept it — skeleton is transient (recommended). B) Write one sentinel per judge and stream each domain judge's chunks live as they complete.