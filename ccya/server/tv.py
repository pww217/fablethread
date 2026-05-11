"""Turn viewer data preparation and _tv_* helpers."""

from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any

from .metrics import _fmt_tokens_exact
from .tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested

_STATUS_CSS: dict[str, str] = {
    "ok": "tv-sts-ok",
    "skipped": "tv-sts-skipped",
    "retried": "tv-sts-retried",
    "rejected": "tv-sts-rejected",
    "error": "tv-sts-error",
}

_STAGE_CSS: dict[str, str] = {
    "rules": "tv-stage-rules",
    "narrate": "tv-stage-narrate",
    "scene": "tv-stage-scene",
    "state": "tv-stage-state",
    "progress": "tv-stage-progress",
}


def _tv_parse_json_blob(raw: Any) -> dict[str, Any] | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    try:
        out = _json.loads(s)
        return out if isinstance(out, dict) else None
    except _json.JSONDecodeError:
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = _json.loads(s[i : j + 1])
                return out if isinstance(out, dict) else None
            except _json.JSONDecodeError:
                return None
        return None


def _tv_dict_to_lines(
    d: dict[str, Any],
    skip_keys: tuple[str, ...] = (),
    max_str: int = 150,
) -> list[dict[str, Any]]:
    """Generic: render every top-level key of a dict as a KV line.

    Values are stringified with enough context to be useful:
    - empty list/None/empty string → "∅", dim=True
    - list of primitives (≤4) → comma-joined
    - list of dicts → "[N] id1, id2, …" using id/name/text heuristics
    - longer list → "[N items] first_item_summary"
    - dict → flat inline JSON (truncated)
    - bool → "true"/"false"
    - string → truncated to max_str
    """
    lines: list[dict[str, Any]] = []
    for k, v in d.items():
        if k in skip_keys:
            continue
        if v is None:
            lines.append({"k": k, "v": "null", "dim": True})
        elif isinstance(v, bool):
            lines.append({"k": k, "v": str(v).lower(), "dim": not v})
        elif isinstance(v, list):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            elif all(isinstance(x, (str, int, float)) for x in v):
                joined = ", ".join(str(x) for x in v)
                if len(joined) > max_str:
                    joined = joined[:max_str] + "\u2026"
                lines.append({"k": k, "v": joined, "dim": False})
            elif all(isinstance(x, dict) for x in v):
                def _label(x: dict[str, Any]) -> str:
                    for key in ("id", "name", "text", "label"):
                        val = x.get(key)
                        if val and isinstance(val, str):
                            return val[:60]
                    return str(list(x.values())[0])[:60] if x else ""
                labels = [_label(x) for x in v if x]
                summary = ", ".join(label for label in labels if label)
                if len(summary) > max_str:
                    summary = summary[:max_str] + "\u2026"
                display = f"[{len(v)}] {summary}" if summary else f"[{len(v)}]"
                lines.append({"k": k, "v": display, "dim": False})
            else:
                lines.append({"k": k, "v": f"[{len(v)} items]", "dim": False})
        elif isinstance(v, dict):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            else:
                for sk, sv in v.items():
                    sub_k = f"{k}.{sk}"
                    if sv is None:
                        lines.append({"k": sub_k, "v": "null", "dim": True})
                    elif isinstance(sv, bool):
                        lines.append({"k": sub_k, "v": str(sv).lower(), "dim": not sv})
                    elif isinstance(sv, list):
                        if not sv:
                            lines.append({"k": sub_k, "v": "\u2205", "dim": True})
                        elif all(isinstance(x, (str, int, float)) for x in sv):
                            joined = ", ".join(str(x) for x in sv)
                            if len(joined) > max_str:
                                joined = joined[:max_str] + "\u2026"
                            lines.append({"k": sub_k, "v": joined or "\u2205", "dim": not sv})
                        else:
                            lines.append({"k": sub_k, "v": f"[{len(sv)} items]", "dim": False})
                    elif isinstance(sv, str):
                        display = sv[:max_str] + ("\u2026" if len(sv) > max_str else "")
                        lines.append({"k": sub_k, "v": display or "\u2205", "dim": not sv})
                    else:
                        s = str(sv)
                        if len(s) > max_str:
                            s = s[:max_str] + "\u2026"
                        lines.append({"k": sub_k, "v": s, "dim": not sv})
        elif isinstance(v, str):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            else:
                display = v[:max_str] + ("\u2026" if len(v) > max_str else "")
                lines.append({"k": k, "v": display, "dim": False})
        else:
            lines.append({"k": k, "v": str(v), "dim": not v})
    return lines


def _tv_extract_stream_status(
    name: str,
    *,
    skipped: bool,
    error: str | None,
    attempts: int,
    rejected: list[Any],
) -> str:
    # NOTE: stream key "state" hardcoded here; see _STREAMS in tv_mirror.py
    if skipped:
        return "skipped"
    if error:
        return "error"
    if name == "state" and any(
        isinstance(r, dict) and r.get("field") == "inventory_remove" for r in rejected
    ):
        return "rejected"
    if int(attempts or 1) > 1:
        return "retried"
    return "ok"


def _tv_narration_lines(narr: str) -> list[dict[str, Any]]:
    s = narr or ""
    lines: list[dict[str, Any]] = [
        {"k": "chars", "v": str(len(s)), "dim": not s, "full_width": False}
    ]
    if s:
        prev = s[:100] + ("\u2026" if len(s) > 100 else "")
        lines.append({"k": "text", "v": prev, "dim": False, "full_width": True})
    return lines


def _turn_viewer_data(save_dir: Path) -> tuple[list[dict[str, Any]], bool]:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return [], True
    raw = path.read_text().strip()
    if not raw:
        return [], True
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return [], True
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            ev = _json.loads(line)
        except _json.JSONDecodeError:
            continue

        def _fmt_ms(ms: Any) -> str:
            if ms is None:
                return "\u2014"
            try:
                return f"{float(ms) / 1000.0:.1f}s"
            except (TypeError, ValueError):
                return "\u2014"

        rej: list[Any] = ev.get("rejected") or []

        # Step 2.1: Stream metric collection from _STREAMS
        streams: dict[str, dict[str, Any]] = {}
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
            retry_errors: list[Any] = blob.get("retry_errors") or []
            status = _tv_extract_stream_status(
                sd.key,
                skipped=skipped,
                error=error_s,
                attempts=attempts,
                rejected=rej,
            )
            tok_in_display = "\u2014" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_in)
            tok_out_display = "\u2014" if (skipped and sd.skip_token_display) else _fmt_tokens_exact(t_out)
            streams[sd.key] = {
                "tt": "\u2014" if (skipped and sd.skip_token_display) else _fmt_ms(ms_val),
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

        # Step 2.2: Token bar calculation from _STREAMS
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

        # Totals from streams dict
        total_in = sum(int(streams[sd.key].get("tokens_in") or 0) for sd in _STREAMS)
        total_out = sum(int(streams[sd.key].get("tokens_out") or 0) for sd in _STREAMS)
        # total_tt: rules.total_ms + narrate.total_ms + extract.total_ms
        rules_ev = ev.get("rules") or {}
        narr_ev = ev.get("narrate") or {}
        extract_ev = ev.get("extract") or {}
        total_tt_ms = (
            (rules_ev.get("total_ms") or 0)
            + (narr_ev.get("total_ms") or 0)
            + (extract_ev.get("total_ms") or 0)
        )

        # Step 2.3: Prompts dict
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

        # Step 2.4: Connector generation from sd.inputs
        connectors: list[dict[str, Any]] = []
        for sd in _STREAMS:
            if not sd.inputs:
                continue
            segments: list[dict[str, Any]] = []
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

                segments.append({
                    "from": inp_key,
                    "label": f"{inp_key} \u2192 {sd.key}",
                    "lines": seg_lines,
                    "anchor": inp_key,
                    "upstream_status": streams[inp_key]["status"],
                    "upstream_status_class": streams[inp_key]["status_class"],
                })
            connectors.append({"before_stage": sd.key, "segments": segments})

        # Step 2.5: Scope block
        raw_scope: dict[str, Any] = ev.get("scope") or {}
        scope_block = {
            "active_domains": raw_scope.get("active_domains") or [],
        }

        # Derived flags from streams dict
        has_retries = any(streams[sd.key].get("attempts", 1) > 1 for sd in _STREAMS)
        has_errors = any(bool(streams[sd.key].get("error")) for sd in _STREAMS)
        has_skipped = any(streams[sd.key].get("skipped") for sd in _STREAMS)

        # rules_intent for template (parsed from rules_prompt.output)
        rules_intent = _tv_parse_json_blob(prompts["rules"]["output"])

        # state_rejections
        state_rej = [
            r
            for r in (rej if isinstance(rej, list) else [])
            if isinstance(r, dict) and r.get("field") == "inventory_remove"
        ]

        tid = str(ev.get("trace_id") or "")
        tid_short = tid[:8] if len(tid) >= 8 else tid

        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid_short,
                "trace_id_full": tid,
                "has_rejections": bool(rej),
                "has_retries": has_retries,
                "has_errors": has_errors,
                "has_skipped": has_skipped,
                "streams": streams,
                "connectors": connectors,
                "scope": scope_block,
                "total_tt": _fmt_ms(total_tt_ms),
                "total_tokens_in": total_in,
                "total_tokens_out": total_out,
                "total_tokens_in_display": _fmt_tokens_exact(total_in),
                "total_tokens_out_display": _fmt_tokens_exact(total_out),
                "user_input": ev.get("input", ""),
                "rules_intent": rules_intent,
                "state_rejections": state_rej,
                "prompts": prompts,
            }
        )
    rows.reverse()
    return rows, False
