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

from ccya.eval.config import EvalConfig, JudgeSpec
from ccya.eval.engine_mirror import constants_block
from ccya.eval.universal_asserts import run_all_universal_asserts
from ccya.llm_client import strip_thinking
from ccya.models import load_config

_log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class TraceOptions:
    """Dedup options for trace rendering."""
    dedup_immutable_sections: bool = True
    state_as_diff: bool = True


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
    """Structured result of one judge invocation.

    `body_md` is the raw markdown the judge returned (front matter stripped).
    `scores` is the parsed front matter dict. Missing scores are None.
    """
    raw_response: str
    body_md: str
    scores: dict[str, Any]
    rubric_path: str
    model: str
    judge_id: str = "default"
    trace_md_path: str = ""
    judge_md_path: str = ""
    previous_scores: dict[str, Any] | None = None


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
_NARRATIVE_SNAPSHOT_KEYS = {"meta", "scene", "pc", "location", "arc"}

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


# ---------------------------------------------------------------------------
# Meta judge input builder
# ---------------------------------------------------------------------------

_SECTION_HEADING_RE = re.compile(r"^#{1,3} .+", re.MULTILINE)


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
    return yaml.dump(d, default_flow_style=False, allow_unicode=True)


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
            auto_checker_failures, metrics_rows, turn_events, redundancy_signals, compaction_signals
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
    events: list[dict[str, Any]] | None = None,
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
        parts.append("| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |\n")
        parts.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for m in metrics:
            parts.append(
                f"| {m.get('turn','?')} | {m.get('rules_tok_in',0)} | "
                f"{m.get('narrate_tok_in',0)} | {m.get('scene_tok_in',0)} | "
                f"{m.get('state_tok_in',0)} | {m.get('progress_tok_in',0)} | "
                f"{m.get('parse_failures',0)} | {m.get('retries',0)} | "
                f"{m.get('momentum_after', '—')} |\n"
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

    # Scope fallback rate
    events_for_scope = events or []
    fallback_turns = sum(
        1 for e in events_for_scope
        if e.get("scope", {}).get("decided_by", "narrator") != "narrator"
    )
    scope_fallback_rate = fallback_turns / len(events_for_scope) if events_for_scope else 0.0
    parts.append(f"\n**Scope fallback rate:** {scope_fallback_rate:.0%} ({fallback_turns}/{len(events_for_scope)} turns)\n")

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
            "momentum_after": (ev.get("state_snapshot") or {}).get("meta", {}).get("momentum", "—"),
        })
    return rows


# ---------------------------------------------------------------------------
# Front matter parsing
# ---------------------------------------------------------------------------

_FM_RE = re.compile(
    r"^---\s*\n(.*?)\n^---\s*\n(.*)",
    re.DOTALL | re.MULTILINE,
)


def parse_judge_response(raw: str) -> tuple[dict[str, Any], str]:
    """Strip thinking tags, then split YAML front matter from markdown body.

    Returns (scores, body_md). If no front matter present, scores is empty dict
    and body_md is the entire (think-stripped) response.

    Tries two formats in order:
    1. ```yaml code fence
    2. `---` delimiter front matter (must be at start of response)
    3. Fallback: no scores, full text as body
    """
    s = strip_thinking(raw or "").strip()

    # Try extracting from ```yaml code fence first
    yaml_fence_re = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
    fence_match = yaml_fence_re.search(s)
    if fence_match:
        fm_text = fence_match.group(1).strip()
        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            fm = {}
        if isinstance(fm, dict):
            scores = _normalize_scores(fm)
            # Body is everything after the code fence
            body = s[fence_match.end():].strip()
            if scores:
                return scores, body

    # Tolerate optional leading code fence (generic ```)
    if s.startswith("```"):
        s = "\n".join(s.splitlines()[1:])
        if s.endswith("```"):
            s = "\n".join(s.splitlines()[:-1])
    m = _FM_RE.search(s)
    if not m:
        return {}, s
    fm_text = m.group(1)
    body = m.group(2).strip()
    # Strip markdown table rows (lines with |- separators or multiple | chars forming tables)
    # before YAML parsing. PyYAML treats leading '|' as a literal block scalar indicator.
    _table_row_re = re.compile(r"^\s*\|(.*)\|\s*$")
    fm_lines: list[str] = []
    in_table = False
    for line in fm_text.splitlines():
        if _table_row_re.match(line):
            # Detect table separator (---) or data row with multiple | chars
            stripped = line.strip()
            if "---" in stripped and all(c in "-| " for c in stripped.replace(" ", "")):
                continue  # skip column separators like |-|-|-
            elif stripped.count("|") >= 2:
                if not in_table:
                    in_table = True
                fm_lines.append("# [table row omitted]")
                continue
        else:
            in_table = False
        fm_lines.append(line)
    fm_text_sanitized = "\n".join(fm_lines)
    try:
        fm = yaml.safe_load(fm_text_sanitized) or {}
    except yaml.YAMLError as exc:
        _log.warning("judge front matter YAML parse failed: %s", exc)
        return {}, s
    if not isinstance(fm, dict):
        return {}, s
    return _normalize_scores(fm), body


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
    for k in ("mechanical_score", "narrative_score", "system_cohesion_score",
              "prompt_quality_score", "compaction_score",
              "extraction_accuracy_score", "mechanic_lifecycle_score"):
        if k in fm:
            out[k] = _coerce_int(fm[k])
    for k in ("state_fidelity_rate", "prompt_adherence_rate", "sanitization_fidelity_rate"):
        if k in fm:
            out[k] = _coerce_rate(fm[k])
    ps = fm.get("pipeline_scores") or {}
    if isinstance(ps, dict):
        out["pipeline_scores"] = {
            k: _coerce_int(v) for k, v in ps.items()
            if k in ("rules", "narrate", "extract_scene", "extract_state",
                     "extract_progress")
        }
    return out


def parse_previous_judge_md(path: Path) -> dict[str, Any] | None:
    """Load a prior judge.md and return its front matter scores, or None."""
    if not path.exists():
        return None
    txt = path.read_text()
    scores, _ = parse_judge_response(txt)
    return scores or None


# ---------------------------------------------------------------------------
# Parallel judge runner
# ---------------------------------------------------------------------------


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
            max_tokens=spec.max_tokens,  # type: ignore[call-arg]
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
    resume: bool = False,
) -> list["JudgeResult"]:
    """Run domain judges sequentially, then meta judge.

    If resume=True, skips judges whose judge.md already exists in output_dir.

    Returns list of JudgeResult, one per spec in eval_cfg.judges.specs.
    Meta judge is always last in the returned list if present.
    on_judge_complete(judge_id, result) is called after each judge finishes.
    """
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
            spec.model = engine_model

    def _noop_chunk(judge_id: str, chunk: str) -> None:
        pass

    # Run domain judges sequentially
    domain_results: list["JudgeResult"] = []
    for spec in domain_specs:
        judge_md_path = output_dir / f"{scenario_id}.{spec.id}.judge.md"
        if resume and judge_md_path.exists():
            _log.info("judge[%s]: skipping (already complete)", spec.id)
            scores, _ = parse_judge_response(judge_md_path.read_text())
            result = JudgeResult(
                raw_response=judge_md_path.read_text(),
                body_md="",
                scores=scores,
                rubric_path=str(REPO_ROOT / spec.rubric_path if not Path(spec.rubric_path).is_absolute() else spec.rubric_path),
                model=spec.model or engine_model,
                judge_id=spec.id,
                trace_md_path=str(output_dir / f"{scenario_id}.{spec.id}.trace.md"),
                judge_md_path=str(judge_md_path),
                previous_scores=prev_scores_by_id.get(spec.id),
            )
            domain_results.append(result)
            if on_judge_complete:
                on_judge_complete(spec.id, result)
            continue

        _log.info("judge[%s]: running", spec.id)
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
        domain_results.append(result)
        if on_judge_complete:
            on_judge_complete(spec.id, result)

    all_results = list(domain_results)

    # Run meta judge sequentially after domain judges
    if meta_spec is not None:
        meta_judge_md_path = output_dir / f"{scenario_id}.meta.judge.md"
        if resume and meta_judge_md_path.exists():
            _log.info("judge[meta]: skipping (already complete)")
            scores, _ = parse_judge_response(meta_judge_md_path.read_text())
            meta_result = JudgeResult(
                raw_response=meta_judge_md_path.read_text(),
                body_md="",
                scores=scores,
                rubric_path=str(REPO_ROOT / meta_spec.rubric_path if not Path(meta_spec.rubric_path).is_absolute() else meta_spec.rubric_path),
                model=meta_spec.model or engine_model,
                judge_id="meta",
                trace_md_path=str(output_dir / f"{scenario_id}.meta.trace.md"),
                judge_md_path=str(meta_judge_md_path),
                previous_scores=prev_scores_by_id.get("meta"),
            )
            all_results.append(meta_result)
            if on_judge_complete:
                on_judge_complete("meta", meta_result)
        else:
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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_judge_streaming(
    events_path: Path,
    *,
    eval_cfg: "EvalConfig",
    output_dir: Path,
    scenario_id: str,
    on_chunk: Callable[[str], None] | None = None,
    previous_judge_md_path: Path | None = None,
    game_config_path: Path | None = None,
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
            game_config_path=game_config_path,
        )
        # Return meta judge result if present, else last result
        meta = next((r for r in results if r.judge_id == "meta"), None)
        return meta or results[-1]

    # Legacy single-judge path — original implementation unchanged below
    spec = specs[0] if specs else JudgeSpec(id="default", rubric_path="evals/rubrics/default.md")

    from ccya.llm_client import chat_stream

    rubric_path = Path(spec.rubric_path)
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
    system_text = (rubric_text + "\n\n" + arch_context) if arch_context and spec.id != "meta" else rubric_text

    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    game_cfg = load_config(cfg_path)
    llm = game_cfg.get("llm", {})
    host = str(llm.get("host", "http://localhost:8080/v1"))
    judge_model = spec.model or str(llm.get("model", ""))
    if not judge_model:
        raise ValueError("judge model not set")

    events_lines = events_path.read_text().splitlines() if events_path.exists() else []
    events = [json.loads(line) for line in events_lines if line.strip()]
    options = TraceOptions(
        dedup_immutable_sections=eval_cfg.judges.trace.dedup_immutable_sections,
        state_as_diff=eval_cfg.judges.trace.state_as_diff,
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
            temperature=spec.temperature,
            timeout=spec.timeout_s or 180.0,
            max_tokens=spec.max_tokens,  # type: ignore[call-arg]
        ):
            chunks.append(chunk)
            if on_chunk:
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
            temperature=spec.temperature,
            timeout=spec.timeout_s or 180.0,
        ):
            chunks.append(chunk)
            if on_chunk:
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
