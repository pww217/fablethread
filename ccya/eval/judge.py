"""Single LLM judge over events.jsonl.

Renders a full structured-markdown trace containing static context (pack
style, seed state, engine constants, 5 system prompts) once at the top,
then per-turn blocks (user prompts, outputs, state, applied/rejected,
scope, telemetry). Saves trace.md to disk before the LLM call, and the
raw judge response to judge.md after. Parses only the YAML front matter
of the response for scores.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from ccya.eval.config import EvalConfig
from ccya.eval.engine_mirror import constants_block
from ccya.eval.universal_asserts import run_all_universal_asserts
from ccya.llm_client import strip_thinking
from ccya.models import load_config

_log = logging.getLogger("ccya.eval")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class TraceOptions:
    """Dedup options for trace rendering."""
    dedup_immutable_sections: bool = True
    state_as_diff: bool = True


@dataclass
class JudgeResult:
    """Structured result of one judge invocation.

    `body_md` is the raw markdown the judge returned (front matter stripped).
    `scores` is the parsed front matter dict. Missing scores are None.
    """
    raw_response: str
    body_md: str
    scores: dict[str, Any]
    rubric_path: str
    model: str
    trace_md_path: str = ""
    judge_md_path: str = ""
    previous_scores: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Dedup helpers
# ---------------------------------------------------------------------------

_IMMUTABLE_MARKER_RE = re.compile(
    r"<<<TRACE_IMMUTABLE_START>>>(.*?)<<<TRACE_IMMUTABLE_END>>>",
    re.DOTALL,
)

_IMMUTABLE_PLACEHOLDER = "_(immutable section omitted — see Static Context > Seed State)_"


def _strip_immutable_sections(text: str) -> str:
    """Replace marker-bracketed sections with a placeholder. No-op if no markers."""
    return _IMMUTABLE_MARKER_RE.sub(_IMMUTABLE_PLACEHOLDER, text)


def _strip_remaining_markers(text: str) -> str:
    """Strip bare sentinels so they don't appear in the rendered trace."""
    return text.replace("<<<TRACE_IMMUTABLE_START>>>", "").replace("<<<TRACE_IMMUTABLE_END>>>", "")


def _maybe_dedup_user_prompt(text: str, options: TraceOptions) -> str:
    if options.dedup_immutable_sections:
        return _strip_immutable_sections(text)
    return _strip_remaining_markers(text)


def _hashable(x: Any) -> Any:
    if isinstance(x, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in x.items()))
    if isinstance(x, list):
        return tuple(_hashable(v) for v in x)
    return x


def _diff_list(prev: list[Any], cur: list[Any]) -> dict[str, Any]:
    """Diff two lists. If items are dicts with 'id', use id as identity."""
    if all(isinstance(x, dict) and "id" in x for x in prev + cur):
        prev_by_id = {x["id"]: x for x in prev}
        cur_by_id = {x["id"]: x for x in cur}
        added = [v for k, v in cur_by_id.items() if k not in prev_by_id]
        removed = [v for k, v in prev_by_id.items() if k not in cur_by_id]
        changed = []
        for k, cv in cur_by_id.items():
            pv = prev_by_id.get(k)
            if pv is not None and pv != cv:
                changed.append({"from": pv, "to": cv})
        out: dict[str, Any] = {}
        if added:
            out["added"] = added
        if removed:
            out["removed"] = removed
        if changed:
            out["changed"] = changed
        return out
    # Fallback: set diff
    p = set(map(_hashable, prev))
    c = set(map(_hashable, cur))
    return {"added": list(c - p), "removed": list(p - c)} if (c - p) or (p - c) else {}


def _diff_state_snapshots(prev: dict[str, Any], cur: dict[str, Any]) -> dict[str, Any]:
    """Compute a diff between two state snapshots.

    For dict values: recurse. For list-of-dicts: emit {added, removed, changed}.
    For scalars: emit {from, to}. Unchanged keys are omitted.
    """
    out: dict[str, Any] = {}
    all_keys = set(prev.keys()) | set(cur.keys())
    for key in sorted(all_keys):
        pv = prev.get(key)
        cv = cur.get(key)
        if pv == cv:
            continue
        if isinstance(pv, dict) and isinstance(cv, dict):
            sub = _diff_state_snapshots(pv, cv)
            if sub:
                out[key] = sub
        elif isinstance(pv, list) and isinstance(cv, list):
            out[key] = _diff_list(pv, cv)
        else:
            out[key] = {"from": pv, "to": cv}
    return out


# ---------------------------------------------------------------------------
# Trace builder
# ---------------------------------------------------------------------------


def build_trace(
    events: list[dict[str, Any]],
    *,
    options: TraceOptions | None = None,
    auto_checker_failures: list[dict[str, Any]] | None = None,
    metrics_rows: list[dict[str, Any]] | None = None,
    redundancy_signals: dict[str, Any] | None = None,
    compaction_signals: dict[str, Any] | None = None,
    arch_context: str = "",
) -> str:
    """Render the full markdown trace sent to the judge as the user message.

    Expects events[0] to be a metadata event ({"__metadata__": True, ...}).
    If absent, the static context block falls back to engine constants only.
    Subsequent events are per-turn events with rendered_system, rendered_user,
    output for rules, narrate, and each extraction stream.

    No truncation. No size enforcement. Caller is responsible for choosing
    a judge model with adequate context.

    auto_checker_failures: optional list of dicts with keys turn, assertion, detail.
                           Pass-through; render at the end of the trace.
    metrics_rows: optional list of per-turn dicts with keys turn, rules_tok_in,
                  narrate_tok_in, scene_tok_in, state_tok_in, progress_tok_in,
                  parse_failures, retries.
    """
    options = options or TraceOptions()
    metadata, turn_events = _split_metadata(events)
    parts: list[str] = []
    parts.append(_render_static_context(metadata, turn_events, arch_context))
    prev_snap: dict[str, Any] | None = None
    for i, ev in enumerate(turn_events):
        is_first = (i == 0)
        is_last = (i == len(turn_events) - 1)
        parts.append(_render_turn_context(
            ev,
            options=options,
            prev_state_snapshot=prev_snap,
            full_snapshot=is_first or is_last,
        ))
        prev_snap = ev.get("state_snapshot") or prev_snap
    if auto_checker_failures or metrics_rows or redundancy_signals or compaction_signals:
        parts.append(_render_deterministic_signals(
            auto_checker_failures, metrics_rows, redundancy_signals, compaction_signals
        ))
    return "\n".join(parts)


def _split_metadata(events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if events and events[0].get("__metadata__"):
        return events[0], events[1:]
    return None, list(events)


def _render_static_context(metadata: dict[str, Any] | None, turn_events: list[dict[str, Any]], arch_context: str = "") -> str:
    """Render: Engine Design Reference (optional), World Pack Style, Seed State, Engine Constants, 5 System Prompts.

    If metadata is None: render only constants_block().
    System prompts come from turn_events[0]'s rendered_system fields. If turn 1
    is a retry-only turn (rules_prompt empty), pull from the first turn that
    has the field populated.
    """
    sections: list[str] = []
    if arch_context:
        sections.append("# Engine Design Reference (EVAL_CONTEXT from ARCHITECTURE.md)\n")
        sections.append(arch_context + "\n")
    if metadata is not None:
        sections.append("# Static Context (immutable across all turns)\n")
        sections.append("## World Pack Style\n")
        sections.append("```\n" + (metadata.get("pack_style") or "(none)") + "\n```\n")
        if metadata.get("narrator_rules"):
            sections.append("## Narrator Rules\n")
            for rule in metadata["narrator_rules"]:
                sections.append(f"- {rule}\n")
        if metadata.get("world_factions"):
            sections.append("## World Factions\n")
            for f in metadata["world_factions"]:
                sections.append(f"- **{f.get('name', '')}** ({f.get('disposition', 'neutral')}): {f.get('description', '')}\n")
        if metadata.get("world_locations"):
            sections.append("## World Locations\n")
            for loc in metadata["world_locations"]:
                sections.append(f"- **{loc.get('name', '')}** ({loc.get('type', '')}): {loc.get('description', '')}\n")
        sections.append("## Seed State\n")
        sections.append("```json\n" + json.dumps(metadata.get("seed_state") or {}, indent=2, default=str) + "\n```\n")
        sections.append("## Engine Constants\n")
        sections.append("```json\n" + json.dumps(metadata.get("engine_constants") or {}, indent=2) + "\n```\n")
    else:
        sections.append("# Static Context\n")
        sections.append(constants_block())

    sections.append("## System Prompts (identical every turn)\n")
    sys_prompts = _collect_system_prompts(turn_events)
    for label, key in [
        ("Rules System Prompt", "rules"),
        ("Narrate System Prompt", "narrate"),
        ("Extract Scene System Prompt", "extract_scene"),
        ("Extract State System Prompt", "extract_state"),
        ("Extract Progress System Prompt", "extract_progress"),
    ]:
        sections.append(f"### {label}\n")
        sections.append("```\n" + (sys_prompts.get(key) or "(not captured this run)") + "\n```\n")

    return "\n".join(sections)


def _collect_system_prompts(turn_events: list[dict[str, Any]]) -> dict[str, str]:
    """Find the first event with each rendered_system populated.

    Returns dict with keys: rules, narrate, extract_scene, extract_state, extract_progress.
    """
    out: dict[str, str] = {}
    for ev in turn_events:
        if "rules" not in out:
            v = (ev.get("rules_prompt") or {}).get("rendered_system")
            if v:
                out["rules"] = v
        if "narrate" not in out:
            v = (ev.get("narrate_prompt") or {}).get("rendered_system")
            if v:
                out["narrate"] = v
        ext = ev.get("extraction") or {}
        for stream_key, out_key in [("scene", "extract_scene"), ("state", "extract_state"), ("progress", "extract_progress")]:
            if out_key not in out:
                v = (ext.get(stream_key) or {}).get("rendered_system")
                if v:
                    out[out_key] = v
        if all(k in out for k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress")):
            break
    return out


def _render_turn_context(
    event: dict[str, Any],
    *,
    options: TraceOptions,
    prev_state_snapshot: dict[str, Any] | None,
    full_snapshot: bool,
) -> str:
    """Render one TURN block: header, user prompts, engine outputs, state, telemetry."""
    turn = event.get("turn", "?")
    inp = event.get("input", "")
    parts: list[str] = []
    parts.append(f"\n---\n\n# TURN {turn}\n")
    parts.append(f"**Input:** `{inp}`\n")

    parts.append("## User Prompts\n")
    rules_user = (event.get("rules_prompt") or {}).get("rendered_user") or "(no rules call this turn)"
    narrate_user = (event.get("narrate_prompt") or {}).get("rendered_user") or "(no narrate call)"
    ext = event.get("extraction") or {}
    parts.append("### Rules User Prompt\n```\n" + _maybe_dedup_user_prompt(rules_user, options) + "\n```\n")
    parts.append("### Narrate User Prompt\n```\n" + _maybe_dedup_user_prompt(narrate_user, options) + "\n```\n")
    for stream_key, label in [("scene", "Extract Scene User Prompt"), ("state", "Extract State User Prompt"), ("progress", "Extract Progress User Prompt")]:
        s = ext.get(stream_key) or {}
        if s.get("skipped"):
            parts.append(f"### {label}\n*(skipped)*\n")
        else:
            v = s.get("rendered_user") or "(not captured)"
            parts.append(f"### {label}\n```\n" + _maybe_dedup_user_prompt(v, options) + "\n```\n")

    parts.append("## Engine Outputs\n")
    rules = event.get("rules") or {}
    rules_raw = (event.get("rules_prompt") or {}).get("output") or ""
    parts.append("### Rules\n")
    parts.append("**Parsed (engine):**\n```json\n" + json.dumps(rules, indent=2, default=str) + "\n```\n")
    parts.append("**Raw LLM output:**\n```\n" + rules_raw + "\n```\n")

    narrate_out = (event.get("narrate_prompt") or {}).get("output") or ""
    parts.append("### Narration\n")
    parts.append(narrate_out + "\n")

    for stream_key, label in [("scene", "Extract Scene"), ("state", "Extract State"), ("progress", "Extract Progress")]:
        s = ext.get(stream_key) or {}
        parts.append(f"### {label}\n")
        if s.get("skipped"):
            parts.append("*(skipped — domain not active this turn)*\n")
        else:
            out = s.get("output")
            parts.append("```json\n" + json.dumps(out or {}, indent=2, default=str) + "\n```\n")

    parts.append("### Applied Deltas\n")
    parts.append("```json\n" + json.dumps(event.get("applied") or {}, indent=2, default=str) + "\n```\n")
    rejected = event.get("rejected") or []
    parts.append("### Rejected Deltas\n")
    if rejected:
        parts.append("```json\n" + json.dumps(rejected, indent=2, default=str) + "\n```\n")
    else:
        parts.append("*(none)*\n")

    parts.append("### Suggested Actions\n")
    actions = event.get("actions") or []
    if actions:
        for a in actions:
            parts.append(f"- {a}\n")
    else:
        parts.append("*(none)*\n")

    parts.append("### Context Telemetry\n")
    parts.append(_render_context_telemetry(event))

    parts.append("### State After Turn\n")
    snap = event.get("state_snapshot") or {}
    if options.state_as_diff and not full_snapshot and prev_state_snapshot:
        diff = _diff_state_snapshots(prev_state_snapshot, snap)
        parts.append("*(diff vs previous turn — full snapshot only on first and last turns)*\n")
        parts.append("```json\n" + json.dumps(diff, indent=2, default=str) + "\n```\n")
    else:
        parts.append("```json\n" + json.dumps(snap, indent=2, default=str) + "\n```\n")

    return "\n".join(parts)


def _render_context_telemetry(event: dict[str, Any]) -> str:
    """One-line per-stream token estimate + trim status, for the judge."""
    rows: list[str] = []
    rules_meta = (event.get("rules_prompt") or {}).get("context_meta") or {}
    if rules_meta:
        rows.append(f"- rules: est={rules_meta.get('est_tokens', '?')}t trimmed={bool(rules_meta.get('trimmed'))}")
    narr_meta = (event.get("narrate_prompt") or {}).get("context_meta") or {}
    if narr_meta:
        rows.append(f"- narrate: est={narr_meta.get('est_tokens', '?')}t trimmed={bool(narr_meta.get('trimmed'))}")
    ext = event.get("extraction") or {}
    for stream in ("scene", "state", "progress"):
        s = ext.get(stream) or {}
        if s.get("skipped"):
            rows.append(f"- extract.{stream}: skipped")
            continue
        cm = s.get("context_meta") or {}
        if cm:
            rows.append(f"- extract.{stream}: est={cm.get('est_tokens', '?')}t trimmed={bool(cm.get('trimmed'))} attempts={s.get('attempts', 1)}")
    return "\n".join(rows) + "\n" if rows else "*(no telemetry)*\n"


def _render_deterministic_signals(
    failures: list[dict[str, Any]] | None,
    metrics: list[dict[str, Any]] | None,
    redundancy_signals: dict[str, Any] | None = None,
    compaction_signals: dict[str, Any] | None = None,
) -> str:
    parts: list[str] = ["\n---\n", "# Deterministic Signals\n"]
    parts.append("\n## Auto-Checker Failures\n")
    if failures:
        parts.append("| Turn | Assertion | Detail |\n|---|---|---|\n")
        for f in failures:
            t = f.get("turn", "?")
            a = f.get("assertion", "?")
            d = f.get("detail", "").replace("|", "&#124;")
            parts.append(f"| {t} | `{a}` | {d} |\n")
    else:
        parts.append("*(no failures)*\n")

    parts.append("\n## Metrics\n")
    if metrics:
        parts.append("| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |\n")
        parts.append("|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for m in metrics:
            parts.append(
                f"| {m.get('turn','?')} | {m.get('rules_tok_in',0)} | "
                f"{m.get('narrate_tok_in',0)} | {m.get('scene_tok_in',0)} | "
                f"{m.get('state_tok_in',0)} | {m.get('progress_tok_in',0)} | "
                f"{m.get('parse_failures',0)} | {m.get('retries',0)} |\n"
            )
        parse_details = [m.get("parse_error_details") for m in metrics if m.get("parse_error_details")]
        if parse_details:
            parts.append("\n### Parse Error Details\n")
            for m in metrics:
                errors = m.get("parse_error_details")
                if errors:
                    parts.append(f"**Turn {m.get('turn','?')}** ({len(errors)} error(s)):\n")
                    for err in errors:
                        parts.append(f"- `{err[:500]}`\n")
    else:
        parts.append("*(no metrics)*\n")

    if redundancy_signals is not None:
        from ccya.eval.redundancy import render_redundancy_section
        parts.append(render_redundancy_section(redundancy_signals))

    if compaction_signals is not None:
        from ccya.eval.compaction_signals import render_compaction_section
        parts.append(render_compaction_section(compaction_signals))

    return "".join(parts)


def _build_metrics_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ev in events:
        if ev.get("__metadata__"):
            continue
        rules_meta = (ev.get("rules_prompt") or {}).get("context_meta") or {}
        narr_meta = (ev.get("narrate_prompt") or {}).get("context_meta") or {}
        ext = ev.get("extraction") or {}
        retries = 0
        parse_errors: list[str] = []
        rules_error = (ev.get("rules_prompt") or {}).get("parse_error") or ""
        if rules_error:
            parse_errors.append(f"[rules] {rules_error}")
        for s in ("scene", "state", "progress"):
            sub = ext.get(s) or {}
            retries += max(0, int(sub.get("attempts") or 1) - 1)
            parse_errors.extend(sub.get("retry_errors") or [])
        rows.append({
            "turn": ev.get("turn", "?"),
            "rules_tok_in": int(rules_meta.get("est_tokens", 0) or 0),
            "narrate_tok_in": int(narr_meta.get("est_tokens", 0) or 0),
            "scene_tok_in": int((ext.get("scene") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "state_tok_in": int((ext.get("state") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "progress_tok_in": int((ext.get("progress") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "parse_failures": len(parse_errors),
            "retries": retries,
            "parse_error_details": parse_errors,
        })
    return rows


# ---------------------------------------------------------------------------
# Front matter parsing
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL | re.MULTILINE)


def parse_judge_response(raw: str) -> tuple[dict[str, Any], str]:
    """Strip thinking tags, then split YAML front matter from markdown body.

    Returns (scores, body_md). If no front matter present, scores is empty dict
    and body_md is the entire (think-stripped) response.
    """
    s = strip_thinking(raw or "").strip()
    # Tolerate optional leading code fence
    if s.startswith("```"):
        s = "\n".join(s.splitlines()[1:])
        if s.endswith("```"):
            s = "\n".join(s.splitlines()[:-1])
    m = _FM_RE.match(s)
    if not m:
        return {}, s
    fm_text = m.group(1)
    body = m.group(2)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        _log.warning("judge front matter YAML parse failed: %s", exc)
        return {}, s
    if not isinstance(fm, dict):
        return {}, s
    return _normalize_scores(fm), body


def _normalize_scores(fm: dict[str, Any]) -> dict[str, Any]:
    """Coerce score values to ints clamped 1-5. Pass through other fields untouched."""
    def _coerce(v: Any) -> int | None:
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return None
        return max(1, min(5, n))

    out: dict[str, Any] = {}
    for k in ("mechanical_score", "narrative_score"):
        if k in fm:
            out[k] = _coerce(fm[k])
    ps = fm.get("pipeline_scores") or {}
    if isinstance(ps, dict):
        out["pipeline_scores"] = {k: _coerce(v) for k, v in ps.items() if k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress")}
    return out


def parse_previous_judge_md(path: Path) -> dict[str, Any] | None:
    """Load a prior judge.md and return its front matter scores, or None."""
    if not path.exists():
        return None
    txt = path.read_text()
    scores, _ = parse_judge_response(txt)
    return scores or None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_judge_streaming(
    events_path: Path,
    *,
    eval_cfg: EvalConfig,
    output_dir: Path,
    scenario_id: str,
    on_chunk: Callable[[str], None],
    previous_judge_md_path: Path | None = None,
    game_config_path: Path | None = None,
) -> JudgeResult:
    """Same contract as run_judge() but uses chat_stream() and forwards each
    chunk to on_chunk() so callers can append to REPORT.md in flight.
    """
    from ccya.llm_client import chat_stream

    rubric_path = Path(eval_cfg.judge.rubric_path)
    if not rubric_path.is_absolute():
        rubric_path = REPO_ROOT / rubric_path
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")
    rubric_text = rubric_path.read_text()

    # Phase 06: prepend architecture context to system message
    try:
        from ccya.eval.architecture_context import load_architecture_context
        arch_context = load_architecture_context()
    except ImportError:
        arch_context = ""
    system_text = (rubric_text + "\n\n" + arch_context) if arch_context else rubric_text

    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    game_cfg = load_config(cfg_path)
    llm = game_cfg.get("llm", {})
    host = str(llm.get("host", "http://localhost:8080/v1"))
    judge_model = eval_cfg.judge.model or str(llm.get("model", ""))
    if not judge_model:
        raise ValueError("judge model not set")

    events_lines = events_path.read_text().splitlines() if events_path.exists() else []
    events = [json.loads(line) for line in events_lines if line.strip()]
    options = TraceOptions(
        dedup_immutable_sections=eval_cfg.judge.trace.dedup_immutable_sections,
        state_as_diff=eval_cfg.judge.trace.state_as_diff,
    )

    # Build per-turn metrics
    metrics_rows = _build_metrics_rows(events)

    # Auto-checker failures: derive from events using universal_asserts
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

    # Phase 07: prompt-redundancy signals
    try:
        from ccya.eval.redundancy import compute_redundancy_signals
        redundancy = compute_redundancy_signals(events)
    except ImportError:
        redundancy = None

    # Phase 08: compaction-feature signals
    try:
        from ccya.eval.compaction_signals import compute_compaction_signals
        compaction = compute_compaction_signals(events)
    except ImportError:
        compaction = None

    trace = build_trace(
        events,
        options=options,
        auto_checker_failures=failures,
        metrics_rows=metrics_rows,
        redundancy_signals=redundancy,
        compaction_signals=compaction,
        arch_context=arch_context,
    )

    trace_md_path = output_dir / f"{scenario_id}.trace.md"
    trace_md_path.write_text(trace)
    _log.info("wrote trace: %s", trace_md_path)

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": trace},
    ]
    _log.info("judge: streaming model=%s trace_chars=%d", judge_model, len(trace))
    t0 = time.monotonic()
    chunks: list[str] = []
    try:
        async for chunk in chat_stream(
            host=host,
            model=judge_model,
            messages=messages,
            temperature=eval_cfg.judge.temperature,
            timeout=eval_cfg.judge.timeout_s or 180.0,
            max_tokens=eval_cfg.judge.max_tokens,  # type: ignore[call-arg]
        ):
            chunks.append(chunk)
            on_chunk(chunk)
        elapsed = time.monotonic() - t0
        _log.info("judge: streaming complete in %.1fs", elapsed)
    except TypeError:
        # chat_stream() doesn't accept max_tokens yet (Phase 12 not implemented)
        # Fall back to the old signature
        async for chunk in chat_stream(
            host=host,
            model=judge_model,
            messages=messages,
            temperature=eval_cfg.judge.temperature,
            timeout=eval_cfg.judge.timeout_s or 180.0,
        ):
            chunks.append(chunk)
            on_chunk(chunk)
        elapsed = time.monotonic() - t0
        _log.info("judge: streaming complete (fallback) in %.1fs", elapsed)
    except Exception as exc:
        elapsed = time.monotonic() - t0
        _log.warning("judge: streaming failed after %.1fs: %s", elapsed, exc)
        raise

    raw = "".join(chunks)
    judge_md_path = output_dir / f"{scenario_id}.judge.md"
    judge_md_path.write_text(raw)

    scores, body = parse_judge_response(raw)
    previous_scores = parse_previous_judge_md(previous_judge_md_path) if previous_judge_md_path else None

    return JudgeResult(
        raw_response=raw,
        body_md=body,
        scores=scores,
        rubric_path=str(rubric_path),
        model=judge_model,
        trace_md_path=str(trace_md_path),
        judge_md_path=str(judge_md_path),
        previous_scores=previous_scores,
    )


async def run_judge(
    events_path: Path,
    *,
    eval_cfg: EvalConfig,
    output_dir: Path,
    scenario_id: str,
    previous_judge_md_path: Path | None = None,
    game_config_path: Path | None = None,
) -> JudgeResult:
    """Back-compat. New code should call run_judge_streaming with an on_chunk callback."""
    return await run_judge_streaming(
        events_path,
        eval_cfg=eval_cfg,
        output_dir=output_dir,
        scenario_id=scenario_id,
        on_chunk=lambda _c: None,
        previous_judge_md_path=previous_judge_md_path,
        game_config_path=game_config_path,
    )
